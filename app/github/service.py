import httpx

GITHUB_API_URL = "https://api.github.com"

class GitHubService:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def _headers(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.access_token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }

    async def get_repositories(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/user/repos",
                headers=self._headers(),
                params={
                    "per_page": 100,
                    "sort": "updated",
                }
            )

        response.raise_for_status()

        return response.json()