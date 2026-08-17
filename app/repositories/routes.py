from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.github.service import GitHubService


router = APIRouter(
    prefix="/api/repositories",
    tags=["Repositories"]
)


@router.get("")
async def get_repositories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub access token not available"
        )

    github = GitHubService(current_user.github_access_token)

    repositories = await github.get_repositories()

    return repositories