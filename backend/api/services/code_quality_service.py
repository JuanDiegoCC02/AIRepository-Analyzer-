import os


class CodeQualityService:

    TESTS_MAX = 30
    CI_MAX = 25
    LINT_MAX = 20
    DEPENDENCIES_MAX = 15
    PROJECT_DOCS_MAX = 10

    NEUTRAL_SCORE = 50

    TEST_ENTRIES = frozenset({
        "test", "tests", "spec", "specs", "__tests__", "testing", "e2e",
        "cypress", "conftest.py", "pytest.ini", "tox.ini", ".rspec",
        "jest.config.js", "jest.config.ts", "jest.config.mjs",
        "jest.config.cjs", "vitest.config.js", "vitest.config.ts",
        "karma.conf.js", "phpunit.xml", "phpunit.xml.dist",
    })

    CI_ENTRIES = frozenset({
        ".gitlab-ci.yml", ".travis.yml", ".circleci", ".drone.yml",
        "azure-pipelines.yml", "appveyor.yml", ".appveyor.yml",
        "bitbucket-pipelines.yml", "jenkinsfile", ".buildkite",
        "cloudbuild.yaml", "cloudbuild.yml",
    })

    LINT_ENTRIES = frozenset({
        ".pre-commit-config.yaml", ".editorconfig", ".flake8", ".pylintrc",
        "ruff.toml", ".ruff.toml", "mypy.ini", ".mypy.ini",
        ".prettierrc", ".prettierrc.json", ".prettierrc.js",
        ".prettierrc.yaml", ".prettierrc.yml",
        ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json",
        ".eslintrc.yml", ".eslintrc.yaml",
        "eslint.config.js", "eslint.config.mjs", "eslint.config.cjs",
        "eslint.config.ts", "biome.json", "biome.jsonc",
        ".stylelintrc", "stylelint.config.js",
        ".rubocop.yml", ".golangci.yml", ".golangci.yaml",
        ".clang-format", ".clang-tidy", "rustfmt.toml", ".rustfmt.toml",
        "clippy.toml", "checkstyle.xml", "phpcs.xml", "phpstan.neon",
        ".scalafmt.conf",
    })

    DEPENDENCY_MANIFESTS = frozenset({
        "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
        "pipfile", "environment.yml", "package.json", "cargo.toml",
        "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
        "gemfile", "composer.json", "mix.exs", "pubspec.yaml",
        "package.swift", "build.sbt", "deno.json", "project.clj",
    })

    DEPENDENCY_LOCKFILES = frozenset({
        "uv.lock", "poetry.lock", "pipfile.lock", "pdm.lock",
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
        "cargo.lock", "go.sum", "gemfile.lock", "composer.lock",
        "mix.lock", "pubspec.lock",
    })

    PROJECT_DOC_STEMS = frozenset({
        "contributing", "security", "code_of_conduct", "changelog",
        "changes", "history", "news",
    })

    PROJECT_DOC_EXTENSIONS = frozenset({
        "", ".md", ".rst", ".txt", ".markdown", ".adoc",
    })

    # Maximum names listed as evidence for each signal.
    MAX_EVIDENCE = 5

    @staticmethod
    def _entries(structure):
        """The {name: type} dictionary of a structure, or None."""
        if not isinstance(structure, dict):
            return None

        if structure.get("available") is not True:
            return None

        entries = structure.get("entries")

        if not isinstance(entries, dict):
            return None

        return entries

    @classmethod
    def _matching(cls, entries, known_names):
        """Sorted names from 'entries' that are in 'known_names'."""
        return sorted(name for name in entries if name in known_names)

    @classmethod
    def _project_docs(cls, entries):
        """Sorted document stems (contributing, changelog...) found."""
        found = set()

        for name, item_type in entries.items():
            if item_type != "file":
                continue

            # "changes.rst" -> ("changes", ".rst"); "security.py" is
            # rejected because ".py" is not a documentation extension.
            stem, extension = os.path.splitext(name)

            if (
                stem in cls.PROJECT_DOC_STEMS
                and extension in cls.PROJECT_DOC_EXTENSIONS
            ):
                found.add(stem)

        return sorted(found)

    @classmethod
    def _signal(cls, points, maximum, evidence=None):
        return {
            "points": None if points is None else round(points, 2),
            "max": maximum,
            "evidence": (evidence or [])[: cls.MAX_EVIDENCE],
        }

    @classmethod
    def breakdown(cls, structure):

        entries = cls._entries(structure)

        if entries is None:
            return {
                "tests": cls._signal(None, cls.TESTS_MAX),
                "ci": cls._signal(None, cls.CI_MAX),
                "lint_format": cls._signal(None, cls.LINT_MAX),
                "dependencies": cls._signal(None, cls.DEPENDENCIES_MAX),
                "project_docs": cls._signal(None, cls.PROJECT_DOCS_MAX),
            }

        # --- tests ---
        test_entries = cls._matching(entries, cls.TEST_ENTRIES)
        tests = cls._signal(
            cls.TESTS_MAX if test_entries else 0,
            cls.TESTS_MAX,
            test_entries,
        )

        # --- continuous integration ---
        workflows = structure.get("workflows")
        ci_entries = cls._matching(entries, cls.CI_ENTRIES)

        if ci_entries or (isinstance(workflows, list) and workflows):
            evidence = ci_entries + (
                [f"{len(workflows)} workflow(s)"]
                if isinstance(workflows, list) and workflows
                else []
            )
            ci = cls._signal(cls.CI_MAX, cls.CI_MAX, evidence)
        elif workflows is None and entries.get(".github") == "dir":
            # There is a .github folder but its workflows could not be
            # read: the answer is unknown, not "no CI".
            ci = cls._signal(None, cls.CI_MAX)
        else:
            ci = cls._signal(0, cls.CI_MAX)

        # --- linters and formatters ---
        lint_entries = cls._matching(entries, cls.LINT_ENTRIES)

        if len(lint_entries) >= 2:
            lint_points = cls.LINT_MAX
        elif len(lint_entries) == 1:
            lint_points = cls.LINT_MAX * 0.6
        else:
            lint_points = 0

        lint_format = cls._signal(lint_points, cls.LINT_MAX, lint_entries)

        # --- dependency management ---
        manifests = cls._matching(entries, cls.DEPENDENCY_MANIFESTS)
        lockfiles = cls._matching(entries, cls.DEPENDENCY_LOCKFILES)

        dependency_points = (10 if manifests else 0) + (
            5 if lockfiles else 0
        )
        dependencies = cls._signal(
            dependency_points,
            cls.DEPENDENCIES_MAX,
            manifests + lockfiles,
        )

        # --- project documents ---
        docs = cls._project_docs(entries)

        if len(docs) >= 2:
            docs_points = cls.PROJECT_DOCS_MAX
        elif len(docs) == 1:
            docs_points = cls.PROJECT_DOCS_MAX / 2
        else:
            docs_points = 0

        project_docs = cls._signal(
            docs_points,
            cls.PROJECT_DOCS_MAX,
            docs,
        )

        return {
            "tests": tests,
            "ci": ci,
            "lint_format": lint_format,
            "dependencies": dependencies,
            "project_docs": project_docs,
        }

    @classmethod
    def calculate(cls, repository, structure=None):
 
        if not isinstance(repository, dict):
            return 0

        signals = cls.breakdown(structure)

        earned = 0.0
        possible = 0

        for signal in signals.values():
            if signal["points"] is None:
                continue

            earned += signal["points"]
            possible += signal["max"]

        if possible == 0:
            return cls.NEUTRAL_SCORE

        return max(0, min(100, round(earned / possible * 100)))