#!/usr/bin/env python3
"""Fetch every listed app's released APKs and store listing from GitHub.

Each fdroid/metadata/<app id>.yml names the app's GitHub repo in SourceCode.
The APKs of all its releases go to fdroid/repo, and the fastlane listing on
its default branch goes to fdroid/metadata/<app id>/, where fdroid update
picks both up.

An APK is only kept if GitHub holds an attestation that it was built by a
workflow in that repo (checked with gh attestation verify). Anything else is
deleted again and left out of the store.

A repo with no releases yet is skipped, so an app can be listed before its
first release. Set GITHUB_TOKEN to avoid the anonymous rate limit. Pass
--skip-verify to try things out on a computer without gh.
"""
import calendar
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

FDROID = Path(__file__).resolve().parent.parent / "fdroid"
LISTING = "fastlane/metadata/android/"


def get(url, accept="application/vnd.github+json"):
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "nextcolor-apps"})
    token = os.environ.get("GITHUB_TOKEN")
    # urllib drops this header again when GitHub redirects a download elsewhere
    if token and url.startswith("https://api.github.com/"):
        request.add_unredirected_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def github_repo(metadata_file):
    match = re.search(r"^SourceCode:\s*https://github\.com/([\w.-]+/[\w.-]+?)/?\s*$",
                      metadata_file.read_text(), re.MULTILINE)
    if not match:
        sys.exit(f"{metadata_file.name}: SourceCode must be a https://github.com/<owner>/<repo> address")
    return match.group(1)


def verified(apk, repo):
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    # Ask GitHub first whether any attestation exists. A plain "no" drops the
    # APK, while an outage raises and stops the run, so a bad day at GitHub
    # never takes apps out of the store.
    try:
        found = json.loads(get(f"https://api.github.com/repos/{repo}/attestations/sha256:{digest}"))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        return False
    if not found.get("attestations"):
        return False
    env = dict(os.environ)
    if "GITHUB_TOKEN" in env:
        env.setdefault("GH_TOKEN", env["GITHUB_TOKEN"])
    result = subprocess.run(["gh", "attestation", "verify", str(apk), "--repo", repo],
                            env=env, capture_output=True, text=True)
    return result.returncode == 0


def fetch_apks(app_id, repo, taken, verify):
    try:
        releases = json.loads(get(f"https://api.github.com/repos/{repo}/releases?per_page=100"))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        releases = []
    count = 0
    for release in releases:
        if release["draft"] or release["prerelease"]:
            continue
        for asset in release["assets"]:
            if not asset["name"].endswith(".apk"):
                continue
            # Two apps may both call their file app-release.apk
            name = asset["name"] if asset["name"] not in taken else f"{app_id}_{asset['name']}"
            taken.add(name)
            target = FDROID / "repo" / name
            target.write_bytes(get(asset["url"], accept="application/octet-stream"))
            if verify and not verified(target, repo):
                target.unlink()
                # Shows up as a warning on the workflow run's summary page
                print(f"::warning::{app_id}: {asset['name']} from {release['tag_name']} has no attestation "
                      f"from github.com/{repo} and was left out")
                continue
            # fdroid update --use-date-from-apk reads this as the day the
            # version was added, so dates stay the same from one run to the next
            published = calendar.timegm(time.strptime(asset["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
            os.utime(target, (published, published))
            count += 1
    return count


def fetch_listing(app_id, repo):
    target = FDROID / "metadata" / app_id
    shutil.rmtree(target, ignore_errors=True)
    archive = tarfile.open(fileobj=io.BytesIO(get(f"https://api.github.com/repos/{repo}/tarball")))
    found = False
    for member in archive:
        # Paths look like <owner>-<repo>-<commit>/fastlane/metadata/android/en-US/title.txt
        path = member.name.split("/", 1)[-1]
        if not member.isfile() or not path.startswith(LISTING):
            continue
        out = target / path[len(LISTING):]
        if target not in out.resolve().parents:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(archive.extractfile(member).read())
        found = True
    return found


def main():
    (FDROID / "repo").mkdir(exist_ok=True)
    taken = set()
    verify = "--skip-verify" not in sys.argv
    if verify and not shutil.which("gh"):
        sys.exit("gh is needed to check attestations. Install it or pass --skip-verify.")
    for metadata_file in sorted((FDROID / "metadata").glob("*.yml")):
        app_id = metadata_file.stem
        repo = github_repo(metadata_file)
        count = fetch_apks(app_id, repo, taken, verify)
        if count == 0:
            print(f"{app_id}: nothing to publish from github.com/{repo}, left out")
            continue
        listing = fetch_listing(app_id, repo)
        print(f"{app_id}: {count} APK(s) from github.com/{repo}" + ("" if listing else ", no store listing found"))


if __name__ == "__main__":
    main()
