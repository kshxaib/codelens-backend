from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import httpx

from app.core.config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
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
async def github_callback(code: str):
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

    return {
        "message": "GitHub login successful",
        "github_user": github_user,
    }