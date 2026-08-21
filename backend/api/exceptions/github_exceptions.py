


class GitHubServiceError(Exception):
    """
    Base exception for all  GitHub API related errors.
    """
    pass

class GitHubNotFoundError(GitHubServiceError):
    """
    Raised when the requested GitHub resource
    does not exist.
    """
    pass

class GitHubRateLimitError(GitHubServiceError):
    """
    Raised when the GitHub API rate limit
    has been exceded.
    """
    pass

class GitHubAuthenticationError(GitHubServiceError):
    """
    Rased when authentication with GitHub
    fails or access is forbidden.
    """
    pass

class GitHubRequestError(GitHubServiceError):
    """
    Raised when a GitHub API request fails
    beacause of a network or unexpected HTTP error.
    """
    pass
