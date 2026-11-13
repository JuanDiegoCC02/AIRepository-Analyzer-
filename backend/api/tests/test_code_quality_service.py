from django.test import SimpleTestCase

from api.services.code_quality_service import CodeQualityService


def structure(names=(), dirs=(), workflows=(), available=True):
    """Build a structure like RepositoryStructureService returns."""
    entries = {name.lower(): "file" for name in names}
    entries.update({name.lower(): "dir" for name in dirs})

    return {
        "available": available,
        "entries": entries,
        "workflows": list(workflows),
    }


# Real top-level structure of pallets/flask.
FLASK = structure(
    names=[
        ".editorconfig", ".gitignore", ".pre-commit-config.yaml",
        ".readthedocs.yaml", "CHANGES.rst", "LICENSE.txt", "README.md",
        "pyproject.toml", "uv.lock",
    ],
    dirs=[".devcontainer", ".github", "docs", "examples", "src", "tests"],
    workflows=[
        "lock.yaml", "pre-commit.yaml", "publish.yaml", "tests.yaml",
        "zizmor.yaml",
    ],
)

FULL = structure(
    names=[
        ".pre-commit-config.yaml", ".editorconfig", "pyproject.toml",
        "uv.lock", "CONTRIBUTING.md", "SECURITY.md",
    ],
    dirs=["tests", ".github"],
    workflows=["ci.yml"],
)


class CodeQualityServiceTests(SimpleTestCase):

    def test_flask_structure_scores_95(self):
        # tests 30 + CI 25 + lint 20 + dependencies 15 + one document 5.
        # The old formula (wiki, projects, discussions) gave Flask 70.
        score = CodeQualityService.calculate({}, structure=FLASK)

        self.assertEqual(score, 95)

    def test_complete_repository_scores_100(self):
        self.assertEqual(
            CodeQualityService.calculate({}, structure=FULL),
            100,
        )

    def test_repository_with_nothing_scores_zero(self):
        score = CodeQualityService.calculate(
            {},
            structure=structure(names=["README.md", "main.py"]),
        )

        self.assertEqual(score, 0)

    def test_empty_repository_scores_zero(self):
        self.assertEqual(
            CodeQualityService.calculate({}, structure=structure()),
            0,
        )

    def test_unavailable_structure_returns_the_neutral_score(self):
        for value in (None, {}, "text", {"available": False},
                      {"available": True, "entries": "bad"}):
            with self.subTest(structure=value):
                self.assertEqual(
                    CodeQualityService.calculate({}, structure=value),
                    CodeQualityService.NEUTRAL_SCORE,
                )

    def test_calculate_works_with_only_the_repository_argument(self):
        self.assertEqual(
            CodeQualityService.calculate({"stargazers_count": 5}),
            CodeQualityService.NEUTRAL_SCORE,
        )

    def test_invalid_repository_returns_zero(self):
        self.assertEqual(CodeQualityService.calculate(None), 0)
        self.assertEqual(CodeQualityService.calculate("text"), 0)

    def test_metadata_that_said_nothing_about_quality_is_ignored(self):
        base = CodeQualityService.calculate({}, structure=FLASK)
        noisy = CodeQualityService.calculate(
            {
                "has_wiki": True,
                "has_projects": True,
                "has_discussions": True,
                "open_issues_count": 0,
                "default_branch": "main",
                "license": {"name": "MIT"},
                "stargazers_count": 900000,
            },
            structure=FLASK,
        )

        self.assertEqual(base, noisy)

    def test_tests_signal_accepts_common_layouts(self):
        for name in ("tests", "test", "spec", "__tests__"):
            with self.subTest(name=name):
                result = CodeQualityService.breakdown(
                    structure(dirs=[name])
                )

                self.assertEqual(result["tests"]["points"], 30)

    def test_tests_signal_is_case_insensitive_through_normalization(self):
        result = CodeQualityService.breakdown(structure(dirs=["Tests"]))

        self.assertEqual(result["tests"]["points"], 30)

    def test_ci_accepts_github_workflows(self):
        result = CodeQualityService.breakdown(
            structure(dirs=[".github"], workflows=["build.yml"])
        )

        self.assertEqual(result["ci"]["points"], 25)

    def test_ci_accepts_other_providers(self):
        for name in (".gitlab-ci.yml", ".travis.yml", "Jenkinsfile"):
            with self.subTest(name=name):
                result = CodeQualityService.breakdown(
                    structure(names=[name])
                )

                self.assertEqual(result["ci"]["points"], 25)

    def test_github_folder_without_workflows_has_no_ci(self):
        result = CodeQualityService.breakdown(
            structure(dirs=[".github"], workflows=[])
        )

        self.assertEqual(result["ci"]["points"], 0)

    def test_unreadable_workflows_make_ci_unknown_not_zero(self):
        data = structure(dirs=[".github"])
        data["workflows"] = None

        result = CodeQualityService.breakdown(data)

        self.assertIsNone(result["ci"]["points"])

    def test_unknown_signal_is_left_out_and_the_score_rescaled(self):
        data = structure(
            names=["pyproject.toml", "uv.lock", ".flake8", ".editorconfig"],
            dirs=["tests", ".github"],
        )
        data["workflows"] = None

        # tests 30 + lint 20 + dependencies 15 = 65 of the 75 checkable.
        self.assertEqual(
            CodeQualityService.calculate({}, structure=data),
            87,
        )

    def test_lint_points_depend_on_the_number_of_tools(self):
        none = CodeQualityService.breakdown(structure())
        one = CodeQualityService.breakdown(structure(names=[".flake8"]))
        two = CodeQualityService.breakdown(
            structure(names=[".flake8", ".editorconfig"])
        )

        self.assertEqual(none["lint_format"]["points"], 0)
        self.assertEqual(one["lint_format"]["points"], 12)
        self.assertEqual(two["lint_format"]["points"], 20)

    def test_dependencies_manifest_and_lockfile(self):
        manifest = CodeQualityService.breakdown(
            structure(names=["package.json"])
        )
        both = CodeQualityService.breakdown(
            structure(names=["package.json", "package-lock.json"])
        )
        lock_only = CodeQualityService.breakdown(
            structure(names=["yarn.lock"])
        )

        self.assertEqual(manifest["dependencies"]["points"], 10)
        self.assertEqual(both["dependencies"]["points"], 15)
        self.assertEqual(lock_only["dependencies"]["points"], 5)

    def test_project_documents_ignore_code_files_with_the_same_name(self):
        result = CodeQualityService.breakdown(
            structure(names=["security.py", "history.js", "news.json"])
        )

        self.assertEqual(result["project_docs"]["points"], 0)

    def test_project_documents_accept_common_formats(self):
        result = CodeQualityService.breakdown(
            structure(names=["CHANGES.rst", "CONTRIBUTING", "security.md"])
        )

        self.assertEqual(result["project_docs"]["points"], 10)
        self.assertEqual(
            result["project_docs"]["evidence"],
            ["changes", "contributing", "security"],
        )

    def test_folders_named_like_documents_do_not_count(self):
        result = CodeQualityService.breakdown(
            structure(dirs=["changelog", "security"])
        )

        self.assertEqual(result["project_docs"]["points"], 0)

    def test_evidence_only_lists_known_names_and_is_bounded(self):
        data = structure(
            names=[
                "malicious<script>.txt", "../../etc/passwd",
                ".flake8", ".pylintrc", "ruff.toml", ".editorconfig",
                "mypy.ini", ".eslintrc", ".prettierrc",
            ],
        )

        evidence = CodeQualityService.breakdown(data)[
            "lint_format"
        ]["evidence"]

        self.assertLessEqual(len(evidence), CodeQualityService.MAX_EVIDENCE)
        self.assertTrue(
            set(evidence) <= CodeQualityService.LINT_ENTRIES
        )

    def test_breakdown_of_unavailable_structure_has_no_points(self):
        result = CodeQualityService.breakdown(None)

        self.assertEqual(
            set(result),
            {"tests", "ci", "lint_format", "dependencies", "project_docs"},
        )

        for signal in result.values():
            self.assertIsNone(signal["points"])

    def test_maximum_points_add_up_to_100(self):
        result = CodeQualityService.breakdown(FULL)

        self.assertEqual(
            sum(signal["max"] for signal in result.values()),
            100,
        )