# `hatch_build.py` — Dynamic Version Hook

## Role in the project

This file is a **custom Hatchling version hook**. It is called by the build backend every time a package is built (locally or in CI) to determine what version string to stamp into the wheel.

It is referenced in `pyproject.toml`:

```toml
[tool.hatch.version]
source     = "code"
path       = "hatch_build.py"
expression = "get_version()"
```

---

## Why a custom hook?

The project needs **different version formats depending on where and on which branch the build runs**. A static file or a simple VCS tag would not cover all cases. This hook centralises all version logic in one place, making both local development and CI pipelines work seamlessly without extra environment setup.

---

## Helper functions

### `_run(cmd)`
Runs a shell command and returns its stdout, silently returning an empty string on failure. Used to call `git` without crashing when git is unavailable (e.g. shallow CI clones or lint jobs).

### `_slugify(branch)`
Converts a branch name into a PEP 440–safe local identifier (lowercase, alphanumeric + hyphens, max 40 chars). Example: `feature/my-new-api` → `feature-my-new-api`.

### `_read_version_init()`
Reads `__version__` from `my-data-project/__init__.py`. This is the **base version** — the last version that was officially released on `main` and written there by Commitizen.

---

## `get_version()` — Decision tree

```
CI_COMMIT_TAG set?
  └─ yes → return the tag as-is             (e.g. 1.2.3 or 1.2.3rc2)

PACKAGE_VERSION env var set?
  └─ yes → return it (manual override)

Determine branch from:
  CI_COMMIT_BRANCH → CI_MERGE_REQUEST_SOURCE_BRANCH_NAME → git rev-parse

branch == "main"
  └─ return base_version from __init__.py   (e.g. 1.2.3)

branch == "develop"
  └─ fetch RC tags for base_version
     └─ find highest rc<N>, increment by 1  (e.g. 1.2.3rc3)

any other branch (feature/*, dev/*, hotfix/*, …)
  └─ return base_version.dev0+<slug>.<sha>  (e.g. 1.2.3.dev0+feat-login.a1b2c3d)
     └─ fallback if no git: base_version.dev0
```

---

## Version formats per context

| Trigger | Example output | PEP 440 compliant |
|---|---|---|
| Tag pipeline | `1.2.3` | ✅ |
| `main` branch build | `1.2.3` | ✅ |
| `develop` branch build | `1.2.3rc3` | ✅ |
| Feature branch build | `1.2.3.dev0+feat-login.a1b2c3` | ✅ |
| Local, no git | `1.2.3.dev0` | ✅ |

---

## Key design decisions

- **No bump logic here.** This hook is read-only: it never writes to `__init__.py`. Bumping is the sole responsibility of Commitizen in the `create-tag` CI job.
- **`develop` RC number is derived from git tags**, not from a file, so multiple pipelines running in parallel will not conflict.
- **Feature branch versions use the commit SHA** as a local identifier, making each build uniquely traceable without polluting the tag registry.
- **Graceful degradation**: every `git` call is wrapped in `_run()` so lint jobs or pre-commit hooks that trigger a build in a shallow or tag-only clone will still produce a valid version string.

---

## Summary

```
hatch_build.py
├── Called by Hatchling at build time to resolve the package version
├── Reads base version from __init__.py (written by Commitizen on main)
├── Applies branch-specific logic: stable / RC / dev+local
└── Never writes files — version bumping is handled by CI (create-tag job)
```
