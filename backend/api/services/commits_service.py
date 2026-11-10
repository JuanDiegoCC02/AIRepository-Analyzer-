from datetime import datetime, timedelta, timezone

from api.exceptions.github_exceptions import GitHubServiceError
from api.services.github_service import GitHubService


class CommitsService:
    """
    Summarizes the recent commit activity of a repository.

    It performs a single GitHub request (the latest 100 commits of the
    last WINDOW_DAYS days), so it is cheap enough to run on every analysis.
    """

    WINDOW_DAYS = 90
    PAGE_SIZE = 100

    @classmethod
    def empty_summary(cls):
        """Summary returned when commit data could not be retrieved."""
        return {
            "available": False,
            "window_days": cls.WINDOW_DAYS,
            "commits": 0,
            "bot_commits": 0,
            "capped": False,
            "active_authors": 0,
            "last_commit_at": None,
        }

    @staticmethod
    def _parse_date(value):
        """Parse an ISO 8601 string into an aware UTC datetime."""
        if not isinstance(value, str) or not value:
            return None

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    @classmethod
    def _commit_date(cls, commit):
        """Return the date of a commit (committer date, then author date)."""
        details = commit.get("commit")

        if not isinstance(details, dict):
            return None

        for role in ("committer", "author"):
            person = details.get(role)

            if isinstance(person, dict):
                parsed = cls._parse_date(person.get("date"))

                if parsed is not None:
                    return parsed

        return None

    @staticmethod
    def _identify_author(commit):
        """
        Return (identifier, is_bot) for a commit.

        The GitHub login is preferred. When the commit is not linked to a
        GitHub account, the git author name is used. E-mail addresses are
        deliberately never read or stored.
        """
        author = commit.get("author")

        if isinstance(author, dict):
            login = author.get("login")

            if isinstance(login, str) and login:
                is_bot = (
                    author.get("type") == "Bot"
                    or login.lower().endswith("[bot]")
                )
                return login, is_bot

        details = commit.get("commit")

        if isinstance(details, dict):
            git_author = details.get("author")

            if isinstance(git_author, dict):
                name = git_author.get("name")

                if isinstance(name, str) and name.strip():
                    name = name.strip()
                    return name, name.lower().endswith("[bot]")

        return None, False

    @classmethod
    def get_recent_commits(cls, owner, repository, now=None):
        """
        Fetch the latest commits inside the analysis window.

        Returns None when GitHub cannot provide the data (rate limit,
        empty repository, network error...), so callers can tell
        "no data" apart from "zero commits".
        """
        now = now or datetime.now(timezone.utc)

        since = (
            now - timedelta(days=cls.WINDOW_DAYS)
        ).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        endpoint = f"/repos/{owner}/{repository}/commits"

        try:
            commits = GitHubService.request(
                endpoint,
                params={
                    "since": since,
                    "per_page": cls.PAGE_SIZE,
                },
            )
        except GitHubServiceError:
            return None

        if not isinstance(commits, list):
            return None

        return [
            commit
            for commit in commits
            if isinstance(commit, dict)
        ]

    @classmethod
    def summarize(cls, commits):
        """Build the commit activity summary from a list of commits."""
        if commits is None:
            return cls.empty_summary()

        human_commits = 0
        bot_commits = 0
        authors = set()
        latest = None

        for commit in commits:
            identifier, is_bot = cls._identify_author(commit)

            if is_bot:
                bot_commits += 1
            else:
                human_commits += 1

                if identifier:
                    authors.add(identifier)

            moment = cls._commit_date(commit)

            if moment is not None and (latest is None or moment > latest):
                latest = moment

        return {
            "available": True,
            "window_days": cls.WINDOW_DAYS,
            "commits": human_commits,
            "bot_commits": bot_commits,
            # With 100 results there may be more commits than we can see.
            "capped": len(commits) >= cls.PAGE_SIZE,
            "active_authors": len(authors),
            "last_commit_at": (
                latest.strftime("%Y-%m-%dT%H:%M:%SZ")
                if latest is not None
                else None
            ),
        }

    @classmethod
    def analyze(cls, owner, repository, now=None):
        """Fetch and summarize the recent commit activity."""
        commits = cls.get_recent_commits(
            owner,
            repository,
            now=now,
        )

        return cls.summarize(commits)