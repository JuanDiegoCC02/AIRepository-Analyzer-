class GitHubServiceError(Exception):
    """
    Base exception for all GitHub API related errors.
    """
    pass


class GitHubNotFoundError(GitHubServiceError):
    """
    Raised when the requested GitHub resource
    does not exist.

    `repository_url` is set when several repositories are processed
    together (comparison), so the API can say which one was not found.
    """

    def __init__(self, *args, repository_url=None):
        super().__init__(*args)
        self.repository_url = repository_url


class GitHubRateLimitError(GitHubServiceError):
    """
    Raised when the GitHub API rate limit
    has been exceeded.

    `retry_after` is the number of seconds to wait before trying again
    when GitHub told us (None when it did not).
    """

    def __init__(
        self,
        message="GitHub API rate limit exceeded.",
        retry_after=None,
    ):
        super().__init__(message)
        self.retry_after = retry_after


class GitHubAuthenticationError(GitHubServiceError):
    """
    Raised when authentication with GitHub
    fails or access is forbidden.
    """
    pass


class GitHubRequestError(GitHubServiceError):
    """
    Raised when a GitHub API request fails
    because of a network or unexpected HTTP error.
    """
    pass


class InvalidRepositoryURLError(ValueError):
    """
    Raised when a repository URL is not a valid HTTPS GitHub repository
    URL. It is a ValueError, so code that already catches ValueError
    keeps working.
    """
    pass
