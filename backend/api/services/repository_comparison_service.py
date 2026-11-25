import math

from api.exceptions.github_exceptions import GitHubNotFoundError
from api.services.analyzer_service import AnalyzerService


class RepositoryComparisonService:
    """
    Compares several repositories using their analysis scores.

    Every repository is analyzed with AnalyzerService (so it uses the
    same score version, the same GitHub data cache and is saved in the
    user's history) and the scores are then compared dimension by
    dimension.

    For each dimension the result says:
      - leaders:  the repositories with the highest score
      - winner:   the leader, or None when there is a tie
      - margin:   points between the leader and the second best
      - verdict:  "clear" (margin >= CLEAR_MARGIN), "close", "tie" or
                  "unknown" (fewer than two scores to compare)
    """

    MIN_REPOSITORIES = 2
    MAX_REPOSITORIES = 4

    # A difference below this many points is treated as noise.
    CLEAR_MARGIN = 5

    DIMENSIONS = (
        ("popularity", "popularity"),
        ("activity", "development activity"),
        ("documentation", "documentation"),
        ("maintainability", "maintainability"),
        ("code_quality", "code quality"),
        ("community", "community"),
    )

    @classmethod
    def analyze_and_compare(cls, repository_urls, user=None):
        """Analyze every repository and return their comparison."""
        valid_count = (
            isinstance(repository_urls, (list, tuple))
            and cls.MIN_REPOSITORIES
            <= len(repository_urls)
            <= cls.MAX_REPOSITORIES
        )

        if not valid_count:
            raise ValueError(
                f"Between {cls.MIN_REPOSITORIES} and "
                f"{cls.MAX_REPOSITORIES} repositories are required."
            )

        results = []

        for repository_url in repository_urls:
            try:
                results.append(
                    AnalyzerService.analyze_repository(
                        repository_url,
                        user=user,
                    )
                )
            except GitHubNotFoundError as error:
                # Tell the client which of the repositories was not found.
                error.repository_url = repository_url
                raise

        return cls.compare(results)

    @staticmethod
    def _score(value):
        """Return a valid score (0 to 100) or None."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None

        if not math.isfinite(value) or not 0 <= value <= 100:
            return None

        return value

    @staticmethod
    def _section(value):
        """Return value when it is a dict, otherwise an empty dict."""
        return value if isinstance(value, dict) else {}

    @classmethod
    def _entry(cls, result):
        """Summarize the analysis of one repository."""
        result = cls._section(result)

        repository = cls._section(result.get("repository"))
        analysis = cls._section(result.get("analysis"))
        classification = cls._section(result.get("classification"))
        quality = cls._section(result.get("data_quality"))
        overall = cls._section(
            cls._section(result.get("analysis_result")).get("overall")
        )

        names = [key for key, _ in cls.DIMENSIONS] + ["overall"]

        return {
            "repository_id": repository.get("id"),
            "full_name": repository.get("full_name"),
            "html_url": repository.get("html_url"),
            "description": repository.get("description"),
            "language": repository.get("language"),
            "stars": repository.get("stars"),
            "forks": repository.get("forks"),
            "project_type": classification.get("project_type"),
            "analysis_id": analysis.get("id"),
            "score_version": analysis.get("score_version"),
            "level": overall.get("level"),
            "scores": {
                name: cls._score(analysis.get(f"{name}_score"))
                for name in names
            },
            "data_complete": quality.get("complete") is not False,
            "missing_data": (
                [str(item) for item in quality.get("missing")]
                if isinstance(quality.get("missing"), (list, tuple))
                else []
            ),
        }

    @classmethod
    def _rank(cls, entries, dimension):
        """Compare the scores of one dimension."""
        scores = [
            {
                "repository": entry["full_name"],
                "score": entry["scores"][dimension],
            }
            for entry in entries
        ]

        valid = [item["score"] for item in scores if item["score"] is not None]

        if len(valid) < 2:
            return {
                "scores": scores,
                "winner": None,
                "leaders": [],
                "margin": 0,
                "verdict": "unknown",
            }

        top = max(valid)

        leaders = [
            item["repository"] for item in scores if item["score"] == top
        ]

        if len(leaders) > 1:
            return {
                "scores": scores,
                "winner": None,
                "leaders": leaders,
                "margin": 0,
                "verdict": "tie",
            }

        margin = top - max(score for score in valid if score < top)

        return {
            "scores": scores,
            "winner": leaders[0],
            "leaders": leaders,
            "margin": margin,
            "verdict": "clear" if margin >= cls.CLEAR_MARGIN else "close",
        }

    @staticmethod
    def _points(margin):
        return f"{margin:g} point" + ("" if margin == 1 else "s")

    @classmethod
    def _highlights(cls, dimensions, overall):
        """Short sentences about the clear differences."""
        highlights = []

        if overall["verdict"] == "clear":
            highlights.append(
                f"{overall['winner']} has the highest overall score, "
                f"{cls._points(overall['margin'])} ahead."
            )
        elif overall["verdict"] == "close":
            highlights.append(
                f"{overall['winner']} is slightly ahead overall "
                f"({cls._points(overall['margin'])})."
            )
        elif overall["verdict"] == "tie":
            highlights.append("The repositories are tied overall.")

        for key, label in cls.DIMENSIONS:
            ranking = dimensions[key]

            if ranking["verdict"] == "clear":
                highlights.append(
                    f"{ranking['winner']} leads in {label} by "
                    f"{cls._points(ranking['margin'])}."
                )

        return highlights

    @staticmethod
    def _warnings(entries):
        warnings = []

        for entry in entries:
            if not entry["data_complete"]:
                missing = ", ".join(entry["missing_data"]) or "some data"

                warnings.append(
                    f"GitHub could not provide {missing} for "
                    f"{entry['full_name']}: its scores may not be fully "
                    "comparable."
                )

        project_types = sorted(
            {
                entry["project_type"]
                for entry in entries
                if isinstance(entry["project_type"], str)
            }
        )

        if len(project_types) > 1:
            warnings.append(
                "The repositories have different project types "
                f"({', '.join(project_types)}), so the comparison may be "
                "less meaningful."
            )

        versions = {entry["score_version"] for entry in entries}

        if len(versions) > 1:
            warnings.append(
                "The analyses use different score versions and cannot be "
                "compared reliably."
            )

        return warnings

    @classmethod
    def compare(cls, results):
        """
        Build the comparison from the results of AnalyzerService.

        Only needs the analysis results, so it makes no requests.
        """
        entries = [cls._entry(result) for result in results]

        dimensions = {
            key: cls._rank(entries, key) for key, _ in cls.DIMENSIONS
        }

        overall = cls._rank(entries, "overall")

        wins = {entry["full_name"]: 0 for entry in entries}

        for ranking in dimensions.values():
            winner = ranking["winner"]

            if winner is not None and winner in wins:
                wins[winner] += 1

        versions = {entry["score_version"] for entry in entries}

        return {
            "score_version": (
                versions.pop() if len(versions) == 1 else None
            ),
            "repositories": entries,
            "dimensions": dimensions,
            "overall": overall,
            "summary": {
                "best_overall": overall["winner"],
                "overall_verdict": overall["verdict"],
                "wins": wins,
            },
            "highlights": cls._highlights(dimensions, overall),
            "warnings": cls._warnings(entries),
        }
