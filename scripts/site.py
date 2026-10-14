#!/usr/bin/env python3
"""Build the landing page and the folder that goes to GitHub Pages.

Run after fdroid update. Reads the app list from fdroid/repo/index-v2.json,
so the page always shows what F-Droid shows.

usage: site.py <site url> <repo key fingerprint>
"""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def text(value):
    """Localized fields are {locale: value}. English first, then whatever is there."""
    if isinstance(value, dict):
        return value.get("en-US") or next(iter(value.values()), "")
    return value or ""


def app_entry(package):
    meta = package["metadata"]
    latest = max(package["versions"].values(), key=lambda v: v["manifest"]["versionCode"])
    e = html.escape
    icon = text(meta.get("icon"))
    icon_html = f'<img src="fdroid/repo{e(icon["name"])}" alt="">' if icon else '<span class="noicon"></span>'
    author = e(meta.get("authorName", ""))
    if author and meta.get("authorWebSite"):
        author = f'<a href="{e(meta["authorWebSite"])}">{author}</a>'
    links = []
    if meta.get("sourceCode"):
        links.append(f'<a href="{e(meta["sourceCode"])}">Source code</a>')
    links.append(f'<a href="fdroid/repo{e(latest["file"]["name"])}">Download APK</a>'
                 f' ({e(latest["manifest"]["versionName"])})')
    return (
        f'<li>{icon_html}<div>'
        f'<h3>{e(text(meta.get("name")))}</h3>'
        + (f'<p class="by">by {author}</p>' if author else '')
        + f'<p>{e(text(meta.get("summary")))}</p>'
        f'<p class="links">{" · ".join(links)}</p>'
        f'</div></li>'
    )


def main():
    site_url, fingerprint = sys.argv[1].rstrip("/"), sys.argv[2]
    index = json.loads((ROOT / "fdroid/repo/index-v2.json").read_text())
    packages = sorted(index["packages"].values(), key=lambda p: text(p["metadata"].get("name")).lower())

    repo_url = f"{site_url}/fdroid/repo"
    page = (ROOT / "site/index.html").read_text()
    for placeholder, value in {
        "@APPS@": "\n".join(app_entry(p) for p in packages),
        "@REPO_URL@": repo_url,
        "@ADD_URL@": f"fdroidrepos://{repo_url.split('://', 1)[1]}?fingerprint={fingerprint}",
        "@FINGERPRINT@": fingerprint,
    }.items():
        page = page.replace(placeholder, value)

    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "fdroid").mkdir(parents=True)
    shutil.copytree(ROOT / "fdroid/repo", OUT / "fdroid/repo")
    (OUT / "index.html").write_text(page)
    shutil.copy(ROOT / "site/favicon.ico", OUT)
    print(f"{len(packages)} app(s) on the page")


if __name__ == "__main__":
    main()
