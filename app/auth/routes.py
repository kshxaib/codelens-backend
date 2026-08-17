from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.auth.dependencies import get_current_user


from app.core.config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    FRONTEND_URL,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.get("/github")
async def github_login():
    github_authorize_url = ("https://github.com/login/oauth/authorize"f"?client_id={GITHUB_CLIENT_ID}""&scope=user%20repo"
    )
    return RedirectResponse(url=github_authorize_url)



@router.get("/github/callback")
async def github_callback(request: Request, code: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:

        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={
                "Accept": "application/json"
            }
        )

        token_data = token_response.json()

        access_token = token_data.get("access_token")

        if not access_token:
            return {
                "error": "Failed to obtain GitHub access token"
            }

        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            }
        )

        github_user = user_response.json()

        github_id = github_user["id"]
        username = github_user["login"]
        avatar_url = github_user.get("avatar_url")
        
        user = db.query(User).filter(User.github_id == github_id).first()

        if not user:
            user = User(github_id=github_id, username=username, avatar_url=avatar_url)
            db.add(user)

        else:
            user.username = username
            user.avatar_url = avatar_url
        
        db.commit()
        db.refresh(user)
        
        # Create CodeLens session
        request.session["user_id"] = user.id
    
    return RedirectResponse(
        url=f"{FRONTEND_URL}/dashboard",
        status_code=303
    )



@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url
    }