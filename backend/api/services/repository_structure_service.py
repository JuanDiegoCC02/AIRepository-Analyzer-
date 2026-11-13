from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubServiceError,
)
from api.services.github_service import GitHubService


class RepositoryStructureService:
    """
    Reads the top-level structure of a repository from GitHub.

    It makes at most two requests per analysis:
      1. the list of files and folders in the repository root;
      2. the workflow files in .github/workflows (only when the root
         contains a .github folder).

    The result only keeps lowercase file names and their type. Nothing
    from GitHub is ever used to build a URL or a path: the names are only
    compared against fixed lists by CodeQualityService.
    """

    # GitHub never lists more than 1000 entries for a folder.
    MAX_ENTRIES = 1000
    MAX_NAME_LENGTH = 255

    WORKFLOWS_PATH = ".github/workflows"
    WORKFLOW_EXTENSIONS = (".yml", ".yaml")

    @classmethod
    def unavailable(cls):
        """Result returned when the structure could not be retrieved."""
        return {
            "available": False,
            "entries": {},
            "workflows": None,
        }

    @classmethod
    def _normalize(cls, items):
        """
        Convert a GitHub folder listing into {lowercase name: type}.

        Anything that is not a dictionary with text name and type is
        ignored, and the amount of entries is bounded.
        """
        entries = {}

        for item in items[: cls.MAX_ENTRIES]:
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            item_type = item.get("type")

            if not isinstance(name, str) or not isinstance(item_type, str):
                continue

            name = name.strip().lower()

            if not name or len(name) > cls.MAX_NAME_LENGTH:
                continue

            entries[name] = item_type

        return entries

    @classmethod
    def get_root_entries(cls, owner, repository):
        """
        Return {name: type} for the repository root.

        An empty repository (GitHub answers 404 for its contents, even
        though the repository itself exists) returns an empty dictionary.
        None means GitHub could not provide the data.
        """
        endpoint = f"/repos/{owner}/{repository}/contents"

        try:
            items = GitHubService.request(endpoint)
        except GitHubNotFoundError:
            return {}
        except GitHubServiceError:
            return None

        if not isinstance(items, list):
            return None

        return cls._normalize(items)

    @classmethod
    def get_workflow_files(cls, owner, repository):
        """
        Return the lowercase names of the workflow files.

        A missing folder means the repository has no workflows ([]).
        None means GitHub could not provide the data.
        """
        endpoint = f"/repos/{owner}/{repository}/contents/{cls.WORKFLOWS_PATH}"

        try:
            items = GitHubService.request(endpoint)
        except GitHubNotFoundError:
            return []
        except GitHubServiceError:
            return None

        if not isinstance(items, list):
            return None

        entries = cls._normalize(items)

        return [
            name
            for name, item_type in entries.items()
            if item_type == "file"
            and name.endswith(cls.WORKFLOW_EXTENSIONS)
        ]

    @classmethod
    def analyze(cls, owner, repository):
        """
        Retrieve the structure needed to evaluate engineering practices.

        'workflows' is None when it could not be checked, and a list
        (possibly empty) when it was.
        """
        entries = cls.get_root_entries(owner, repository)

        if entries is None:
            return cls.unavailable()

        workflows = []

        if entries.get(".github") == "dir":
            workflows = cls.get_workflow_files(owner, repository)

        return {
            "available": True,
            "entries": entries,
            "workflows": workflows,
        }