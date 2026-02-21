# `pyproject.toml` — Project & Build Configuration

## Role in the project

This file is the single source of truth for the project's metadata, build system, versioning strategy, and release tooling. It follows the [PEP 517/518](https://peps.python.org/pep-0518/) standard.

---

## Project metadata (`[project]`)

```toml
[project]
name = "my-data-project"
dynamic = ["version"]
description = "My data project wheel"
requires-python = ">=3.10"
```

Defines the package name, Python version requirement, and marks `version` as **dynamic** — meaning it will not be hardcoded here but computed at build time by the custom hook.

`commitizen` is listed as a runtime dependency because it is used in CI to compute and bump versions.

---

## Build system (`[build-system]`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

[Hatchling](https://hatch.pypa.io/) is the build backend. It is responsible for packaging the project into a wheel (`.whl`) or source distribution (`.tar.gz`) when `uv build` is called in CI.

---

## Custom version hook (`[tool.hatch.version]`)

```toml
[tool.hatch.version]
source     = "code"
path       = "hatch_build.py"
expression = "get_version()"
```

Instead of reading the version from a static string or a VCS tag directly, Hatchling is instructed to call `get_version()` from `hatch_build.py`. This allows **context-aware versioning**:

| Context | Version format |
|---|---|
| Tag pipeline (`CI_COMMIT_TAG`) | `1.2.3` (the tag itself) |
| `main` branch | `1.2.3` (read from `__init__.py`) |
| `develop` branch | `1.2.3rc2` (RC incremented from tag registry) |
| Feature / dev branch | `1.2.3.dev0+feat-my-feature.a1b2c3d` |
| Local (no git) | `1.2.3.dev0` |

---

## Commitizen configuration (`[tool.commitizen]`)

```toml
[tool.commitizen]
name                     = "cz_conventional_commits"
tag_format               = "$version"
version_files            = ["my-data-project/__init__.py:__version__"]
update_changelog_on_bump = false
```

[Commitizen](https://commitizen-tools.github.io/commitizen/) automates semantic versioning based on [Conventional Commits](https://www.conventionalcommits.org/).

- **`tag_format = "$version"`** — tags are plain semver (`1.2.3`), without a `v` prefix.
- **`version_files`** — when `cz bump` runs on `main`, it automatically rewrites `__version__` in `__init__.py` with the new version, keeping the source file in sync.
- **`update_changelog_on_bump = false`** — changelog generation is disabled; only tagging and version bumping are used.

---

## Summary

```
pyproject.toml
├── Declares package name, Python requirement, dependencies
├── Delegates versioning to hatch_build.py (dynamic, context-aware)
└── Configures Commitizen to bump __init__.py and push semver tags on main
```
