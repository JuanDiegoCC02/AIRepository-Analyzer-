from api.services.github_service import GitHubService


class ContributorsService:
    """Retrieves and summarizes the contributors of a repository."""

    # GitHub returns only 30 items per page unless asked otherwise, which
    # silently truncated every total. 100 is the maximum GitHub allows.
    PAGE_SIZE = 100

    @classmethod
    def get_contributors(cls, owner, repository):

        endpoint = f"/repos/{owner}/{repository}/contributors"

        try:
            contributors = GitHubService.request(
                endpoint,
                params={"per_page": cls.PAGE_SIZE},
            )

        except Exception:
            return []

        if not isinstance(contributors, list):
            return []

        return [
            contributor
            for contributor in contributors
            if isinstance(contributor, dict)
        ]

    @classmethod
    def summarize(cls, contributors):

        if not contributors:
            return {
                "total_contributors": 0,
                "capped": False,
                "top_contributor": None,
                "top_contributions": 0,
                "contributors": [],
            }

        sorted_contributors = sorted(
            contributors,
            key=lambda contributor: contributor.get(
                "contributions",
                0,
            ),
            reverse=True,
        )

        top_contributor = sorted_contributors[0]

        contributors_summary = []

        for contributor in sorted_contributors:
            contributors_summary.append(
                {
                    "login": contributor.get("login"),
                    "contributions": contributor.get("contributions", 0),
                    "avatar_url": contributor.get("avatar_url"),
                    "html_url": contributor.get("html_url"),
                }
            )

        return {
            "total_contributors": len(contributors),
            # True when the list hit the page limit: the repository may
            # have more contributors than the ones counted here.
            "capped": len(contributors) >= cls.PAGE_SIZE,
            "top_contributor": top_contributor.get("login"),
            "top_contributions": top_contributor.get("contributions", 0),
            "contributors": contributors_summary,
        }