# hatch_build.py
import os
import re
import subprocess


def _run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError:
        return ""


def _slugify(branch):
    slug = branch.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:40] or "unknown"


def _read_version_init():
    path = os.path.join("my-data-project", "__init__.py")
    with open(path, "r") as f:
        for line in f:
            if "__version__" in line:
                match = re.search(r'__version__\s*=\s*["\'](.+)["\']', line)
                if match:
                    return match.group(1)
    return "0.0.0"


def get_version():
    # Tag pipeline → use tag directly as version
    tag = os.environ.get("CI_COMMIT_TAG")
    if tag:
        return tag

    # Forced override
    forced = os.environ.get("PACKAGE_VERSION")
    if forced:
        return forced

    # Determine branch
    branch = (
        os.environ.get("CI_COMMIT_BRANCH")
        or os.environ.get("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME")  # MR source branch
        or _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        or "unknown"
    )

    # MR target branch (if needed)
    mr_target = os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")

    base_version = _read_version_init()

    # -------- main = main package : x.y.z --------
    if branch == "main":
        return base_version

    # -------- develop = RC package : x.y.zrc<number> --------
    elif branch == "develop":
        _run(["git", "fetch", "origin", "develop", "--tags"])
        rc_tags = _run(["git", "tag", "--list", f"{base_version}rc*"])
        if not rc_tags:
            rc_number = 1
        else:
            rc_number = max(int(re.search(r"rc(\d+)", t).group(1)) for t in rc_tags.splitlines())
        return f"{base_version}rc{rc_number}"

    # -------- feature branches package : x.y.z.dev0+<commit SHA> --------
    else:
        # dev/* branches → PEP 440 compliant dev version
        commit_sha = _run(["git", "rev-parse", "--short", "HEAD"])
        slug = _slugify(branch)
 
        # Always include a dev number (required by PEP 440)
        dev_number = 0
 
        if commit_sha:
            return f"{base_version}.dev{dev_number}+{slug}.{commit_sha}"
        else:
            # fallback if git is unavailable (lint job / shallow clone)
            return f"{base_version}.dev{dev_number}"