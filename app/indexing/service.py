import os
import shutil
import subprocess
import tempfile

from app.db.models import Repository, File
from app.indexing.scanner import scan_repository


class RepositoryIndexer:
    def __init__(self, repository: Repository, access_token: str):
        self.repository = repository
        self.access_token = access_token


    # CLONE REPOSITORY
    # GitHub repository ko temporary local directory me clone karega 
    def clone_repository(self, target_path: str):

        auth_header = (
            f"AUTHORIZATION: bearer {self.access_token}"
        )

        env = os.environ.copy()

        env["GIT_HTTP_EXTRAHEADER"] = auth_header

        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                self.repository.clone_url,
                target_path,
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Git clone failed: {result.stderr}"
            )

 
    # GET CURRENT COMMIT SHA
    def get_commit_sha(self, repo_path: str) -> str:
        result = subprocess.run(
            [
                "git",
                "-C",
                repo_path,
                "rev-parse",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()


    # INDEX REPOSITORY
    def index(self, db):
        temp_directory = tempfile.mkdtemp(
            prefix="codelens-"
        )

        try:

            # ------------------------------------------------
            # 1. Clone
            # ------------------------------------------------
            self.clone_repository(
                temp_directory
            )

            # ------------------------------------------------
            # 2. Get commit SHA
            # ------------------------------------------------
            commit_sha = self.get_commit_sha(
                temp_directory
            )

            # ------------------------------------------------
            # 3. Scan + ignore + language detection
            # ------------------------------------------------
            scanned_files = scan_repository(
                temp_directory
            )

            # ------------------------------------------------
            # 4. Remove old file records
            #
            # Phase 4 me full re-index kar rahe hain.
            # Incremental indexing later implement hoga.
            # ------------------------------------------------
            db.query(File).filter(
                File.repository_id
                == self.repository.id
            ).delete(
                synchronize_session=False
            )

            # ------------------------------------------------
            # 5. Save scanned files
            # ------------------------------------------------
            for file_data in scanned_files:

                db.add(
                    File(
                        repository_id=self.repository.id,
                        **file_data,
                    )
                )

            # ------------------------------------------------
            # 6. Update repository metadata
            # ------------------------------------------------
            self.repository.index_status = "indexed"

            self.repository.last_indexed_commit = (
                commit_sha
            )

            from datetime import datetime

            self.repository.last_indexed_at = (
                datetime.utcnow()
            )

            self.repository.file_count = (
                len(scanned_files)
            )

            # Phase 4 me AST nahi hai,
            # isliye symbols abhi 0 hain.
            self.repository.symbol_count = 0

            db.commit()

            return {
                "commit_sha": commit_sha,
                "files_scanned": len(scanned_files),
                "symbols_found": 0,
                "status": "indexed",
            }

        except Exception:

            db.rollback()

            self.repository.index_status = "failed"

            db.commit()

            raise

        finally:

            # Temporary clone delete kar do
            shutil.rmtree(
                temp_directory,
                ignore_errors=True
            )