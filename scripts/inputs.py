#!/usr/bin/env python3
"""Print one hash of everything the published repo is built from.

The Publish workflow compares it with the hash saved on the live site and
skips the build when they match. It covers:

- this repo's app list, icon, scripts, landing page, and workflow (not the
  README or other docs)
- every listed app's released APKs, the same ones collect.py downloads
- every listed app's store listing on its default branch

Each app is printed on its own line so the log shows what was looked at.
Set GITHUB_TOKEN to avoid the anonymous rate limit.
"""
import hashlib
import json
import subprocess
import sys
import urllib.error
from pathlib import Path

from collect import FDROID, get, github_repo

ROOT = FDROID.parent
# Everything here that changes what gets published
BUILT_FROM = ["fdroid/metadata", "fdroid/icon.png", "scripts", "site", ".github/workflows/publish.yml"]


def tree(path):
    """Git's hash of a file or folder as committed."""
    return subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


def released_apks(repo):
    try:
        releases = json.loads(get(f"https://api.github.com/repos/{repo}/releases?per_page=100"))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        return []
    return sorted(
        [release["tag_name"], asset["id"], asset["size"], asset["updated_at"]]
        for release in releases if not release["draft"] and not release["prerelease"]
        for asset in release["assets"] if asset["name"].endswith(".apk")
    )


def listing(repo):
    """Git's hash of fastlane/metadata/android on the default branch, or None without one."""
    try:
        entries = json.loads(get(f"https://api.github.com/repos/{repo}/contents/fastlane/metadata"))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        return None
    return next((e["sha"] for e in entries if e["name"] == "android"), None)


def main():
    inputs = {"repo": {path: tree(path) for path in BUILT_FROM}, "apps": {}}
    for metadata_file in sorted((FDROID / "metadata").glob("*.yml")):
        repo = github_repo(metadata_file)
        app = {"apks": released_apks(repo), "listing": listing(repo)}
        inputs["apps"][metadata_file.stem] = app
        print(f"{metadata_file.stem}: {len(app['apks'])} APK(s), listing {app['listing'] or 'none'}", file=sys.stderr)
    print(hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest())


if __name__ == "__main__":
    main()
