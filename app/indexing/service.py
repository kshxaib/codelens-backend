import os
import shutil
import subprocess
import tempfile
import uuid

from app.db.models import Repository, File
from app.indexing.scanner import scan_repository,detect_symbol
from app.rag.chunker import chunk_code
from app.rag.embeddings import create_embedding
from app.rag.vector_store import create_collection, store_chunks, delete_repository_chunks


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

        # 1. Ensure Qdrant collection exists
        create_collection()    

        temp_directory = tempfile.mkdtemp(
            prefix="codelens-"
        )

        try:

            # 2. Clone repository
            self.clone_repository(temp_directory)


            # 3. Get commit SHA
            commit_sha = self.get_commit_sha(temp_directory)


            # 4. Scan repository
            scanned_files = scan_repository(temp_directory)


            # 5. Remove old PostgreSQL file records and Qdrant chunks for full re-index
            db.query(File).filter(
                File.repository_id == self.repository.id
            ).delete(
                synchronize_session=False
            )
            db.flush()   # Database me changes save

            delete_repository_chunks(self.repository.id)


            # 6. Save scanned files in PostgreSQL
            file_records = []

            for file_data in scanned_files:
                file_record = File(repository_id=self.repository.id, **file_data)
                db.add(file_record)
                file_records.append(file_record)
            db.flush()  # Database IDs generate karwao


            # 7. Create chunks for Qdrant
            chunks_for_qdrant = []
            for file_record in file_records:
                chunks = chunk_code(file_record.content)

                for chunk in chunks:
                    symbol = detect_symbol(
                        content=chunk["content"],
                        start_line=chunk["start_line"],
                        end_line=chunk["end_line"],
                        language=file_record.language,
                    )

                    chunks_for_qdrant.append({
                        "id": str(uuid.uuid4()),
                        "repository_id": self.repository.id,
                        "file_id": file_record.id,
                        "file_path": file_record.file_path,
                        "language": file_record.language,
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                        "content": chunk["content"],
                        "symbol": symbol,
                    })

            
            # 8. Create embedding for every chunk
            for chunk in chunks_for_qdrant:
                chunk["embedding"] = create_embedding(chunk["content"])
                

            # 9. Store chunks + embeddings in Qdrant
            if chunks_for_qdrant:
                store_chunks(chunks_for_qdrant)


            # 10. Update repository metadata
            self.repository.index_status = "indexed"

            self.repository.last_indexed_commit = commit_sha

            from datetime import datetime
            self.repository.last_indexed_at = datetime.utcnow()

            self.repository.file_count = len(scanned_files)

            # Phase 4 me AST nahi hai, isliye symbols abhi 0 hain.
            self.repository.symbol_count = 0

            # 11. Save PostgreSQL changes
            db.commit()

            return {
                "commit_sha": commit_sha,
                "files_scanned": len(scanned_files),
                "chunks_created": len(chunks_for_qdrant),
                "symbols_found": 0,
                "status": "indexed",
            }

        except Exception:
            db.rollback()
            raise

        finally:
            # Temporary clone delete kar do
            shutil.rmtree(temp_directory, ignore_errors=True)


