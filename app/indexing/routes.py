from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Repository, RepositoryAccess
from app.indexing.service import RepositoryIndexer


router = APIRouter(
    prefix="/api/repositories",
    tags=["Indexing"]
)


@router.post("/{repository_id}/index")
def index_repository(repository_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # SECURITY CHECK
    # Sabse pehle verify karo ki current user ko repository access hai.

    access = (
        db.query(RepositoryAccess)
        .filter(
            RepositoryAccess.user_id == current_user.id,
            RepositoryAccess.repository_id == repository_id,
        )
        .first()
    )

    if not access:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this repository",
        )


    # Repository find karo
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )


    # GitHub token required
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub access token not available",
        )


    # INDEXING
    # Actual clone → scan → extract pipeline
    indexer = RepositoryIndexer(repository=repository, access_token=current_user.github_access_token)

    try:
        result = indexer.index(db)

        return {
            "message": "Repository indexed successfully",
            "repository_id": repository.id,
            **result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(error)}",
        )