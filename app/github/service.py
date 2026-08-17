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

    # fetch repositories of the user from github
    async def get_repositories(self):
        repositories = []
        page = 1

        async with httpx.AsyncClient() as client:

            while True:
                response = await client.get(
                    f"{GITHUB_API_URL}/user/repos",
                    headers=self._headers(),
                    params={
                        "per_page": 100,
                        "page": page,
                        "visibility": "all",
                        "affiliation": (
                            "owner,"
                            "collaborator,"
                            "organization_member"
                        ),
                        "sort": "updated",
                    }
                )

                response.raise_for_status()
                data = response.json()

                if not data:
                    break

                repositories.extend(data)

                if len(data) < 100:
                    break

                page += 1

        return repositories

    # fetch repository details from github
    async def get_repository(self, owner: str, name: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{name}",
                headers=self._headers()
            )

        return response