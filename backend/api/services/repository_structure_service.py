from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubServiceError,
)
from api.services.github_service import GitHubService


class RepositoryStructureService:

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