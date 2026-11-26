from rest_framework.throttling import UserRateThrottle


class CompareRateThrottle(UserRateThrottle):
    """
    Limits how often a user can compare repositories.

    A comparison analyzes several repositories and can use dozens of
    GitHub requests, so it has its own, lower limit. The rate is defined
    here (and not in settings) so the endpoint is protected out of the box.
    """

    scope = "compare"
    rate = "20/hour"
