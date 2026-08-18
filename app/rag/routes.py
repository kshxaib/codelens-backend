from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Repository, RepositoryAccess

from app.rag.service import ask_repository


router = APIRouter(
    prefix="/api/repositories",
    tags=["RAG"],
)


# REQUEST MODEL

class AskRepositoryRequest(BaseModel):
    question: str


# ============================================================
# ASK REPOSITORY
# ============================================================

@router.post("/{repository_id}/ask")
def ask_repository_endpoint(
    repository_id: int,

    request: AskRepositoryRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):

    # ========================================================
    # STEP 1 — CHECK USER ACCESS
    # ========================================================
    # Sirf wahi user repository ke code ke baare me question
    # pooch sakta hai jiske paas repository access hai.

    access = (
        db.query(RepositoryAccess)
        .filter(
            RepositoryAccess.user_id
            == current_user.id,

            RepositoryAccess.repository_id
            == repository_id,
        )
        .first()
    )

    if not access:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this repository"
            ),
        )


    # ========================================================
    # STEP 2 — CHECK REPOSITORY
    # ========================================================

    repository = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id
        )
        .first()
    )

    if not repository:

        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )


    # ========================================================
    # STEP 3 — CHECK INDEXING
    # ========================================================
    # RAG tabhi useful hoga jab repository indexed ho.

    if repository.index_status != "indexed":

        raise HTTPException(
            status_code=400,
            detail=(
                "Repository has not been indexed yet"
            ),
        )


    # ========================================================
    # STEP 4 — VALIDATE QUESTION
    # ========================================================

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )


    # ========================================================
    # STEP 5 — RUN RAG
    # ========================================================

    try:

        result = ask_repository(
            question=question,
            repository_id=repository_id,
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail="Failed to answer repository question",
        )