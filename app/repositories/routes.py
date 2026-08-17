from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Repository, RepositoryAccess
from app.github.service import GitHubService


router = APIRouter(
    prefix="/api/repositories",
    tags=["Repositories"]
)


# Jab user manually GitHub repository URL add karega, frontend se request me URL aayega.
# Example: {"url": "https://github.com/kshxaib/codelens"} 
class RepositoryURLRequest(BaseModel):
    url: str

# Database/GitHub se repository ka data milne ke baad frontend ko sirf required information bhejenge.
def repository_response(repository: Repository, permission: str = "read" ):
    return {
        "id": repository.id,
        "github_id": repository.github_id,
        "owner": repository.owner,
        "name": repository.name,
        "full_name": repository.full_name,
        "html_url": repository.html_url,
        "private": repository.private,
        "default_branch": repository.default_branch,
        "description": repository.description,
        "permission": permission,
        "index_status": repository.index_status,
        "last_indexed_commit": repository.last_indexed_commit,
        "last_indexed_at": repository.last_indexed_at,
        "file_count": repository.file_count,
        "symbol_count": repository.symbol_count,
    }


# GET ALL ACCESSIBLE REPOSITORIES
# Is endpoint ka kaam:
# 1. Check karo user logged in hai
# 2. User ka GitHub access token lo
# 3. GitHub API se accessible repositories lao
# 4. Repository ko local DB me save/update karo
# 5. User <-> Repository ka access record banao
# 6. Frontend ko repositories return karo
@router.get("")
async def list_repositories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub access token not available"
        )

    github = GitHubService(current_user.github_access_token)

    github_repositories = await github.get_repositories()

    results = []

    # GitHub se aayi har repository ko process karenge
    for repo_data in github_repositories:
        # Check repository already local DB me hai ya nahi
        repository = (
            db.query(Repository)
            .filter(Repository.github_id == repo_data["id"])
            .first()
        )

        # Repository DB me nahi hai → create karo
        if not repository:
            repository = Repository(
                github_id=repo_data["id"],
                owner=repo_data["owner"]["login"],
                name=repo_data["name"],
                full_name=repo_data["full_name"],
                html_url=repo_data["html_url"],
                clone_url=repo_data["clone_url"],
                private=repo_data["private"],
                default_branch=repo_data.get("default_branch"),
                description=repo_data.get("description"),
            )

            db.add(repository)
            db.flush()

        # Repository already DB me hai → information update karo
        else:
            repository.owner = repo_data["owner"]["login"]
            repository.name = repo_data["name"]
            repository.full_name = repo_data["full_name"]
            repository.html_url = repo_data["html_url"]
            repository.clone_url = repo_data["clone_url"]
            repository.private = repo_data["private"]
            repository.default_branch = repo_data.get("default_branch")
            repository.description = repo_data.get("description")

        # Same repository multiple users access kar sakte hain.
        # User-Repo pair exist karta hai ya nahi check karo
        access = (
            db.query(RepositoryAccess)
            .filter(
                RepositoryAccess.user_id == current_user.id,
                RepositoryAccess.repository_id == repository.id
            )
            .first()
        )

        permission = "read" # Default permission

        if repo_data.get("permissions"):
            permissions = repo_data["permissions"]

            if permissions.get("admin"):
                permission = "admin"
            elif permissions.get("push"):
                permission = "write"
            elif permissions.get("pull"):
                permission = "read"

        # Access record nahi hai → create karo
        if not access:
            access = RepositoryAccess(
                user_id=current_user.id,
                repository_id=repository.id,
                permission=permission
            )

            db.add(access)

        # Access already exists → permission update karo
        else:
            access.permission = permission

        # Frontend response list me repository add karo
        results.append(repository_response(repository, permission))

    # Final results ko database me save karo
    db.commit()

    # return repositories to frontend
    return {
        "repositories": results
    }
