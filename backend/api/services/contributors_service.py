from api.services.github_service import GitHubService



class ContributorsService:

    @classmethod
    def get_contributors(cls, owner, repository):

        endpoint = f"/repos/{owner}/{repository}/contributors"

        try: 
            contributors = GitHubService.request(endpoint)

        except Exception:
            return[]

        if not isinstance(contributors, list):
            return []
        
        return contributors



    @staticmethod
    def summarize(contributors):

        if not contributors:
            return {
                "total_contributors": 0,
                "top_contributor": None,
                "top_contributions": 0,
                "contributors":[],
            }

        sorted_contributors = sorted(
            contributors,
            key=lambda contributor: contributor.get(
                "contributions",
                0,
            ),
            reverse = True,
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

        return{
            "total_contributors": len(contributors),
            "top_contributor":top_contributor.get("login"),
            "top_contributions": top_contributor.get("contributions", 0,),
            "contributors": contributors_summary
        }