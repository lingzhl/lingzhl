#!/usr/bin/env python3
"""Update the combined repository star count shown in the profile SVG."""

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "assets" / "profile-details.svg"
USERNAME = os.environ.get("GITHUB_USERNAME", "lingzhl")
EXTRA_REPOS = os.environ.get(
    "CONTRIBUTED_REPOS", "limouren2000/YYGlobal"
).split(",")


def github_get(url: str, token: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "lingzhl-profile-stats",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def owned_repositories(token: str) -> list[dict]:
    repositories = []
    for page in range(1, 11):
        query = urllib.parse.urlencode(
            {"type": "owner", "per_page": 100, "page": page}
        )
        batch = github_get(
            f"https://api.github.com/users/{USERNAME}/repos?{query}", token
        )
        if not isinstance(batch, list):
            raise RuntimeError("GitHub returned an unexpected repository response")
        repositories.extend(batch)
        if len(batch) < 100:
            break
    return repositories


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    repositories = {
        repo["full_name"]: repo
        for repo in owned_repositories(token)
        if repo.get("full_name") and isinstance(repo.get("stargazers_count"), int)
    }
    for full_name in (repo.strip() for repo in EXTRA_REPOS):
        if not full_name:
            continue
        repo = github_get(f"https://api.github.com/repos/{full_name}", token)
        if not isinstance(repo, dict) or not isinstance(repo.get("stargazers_count"), int):
            raise RuntimeError(f"GitHub returned an unexpected response for {full_name}")
        repositories[full_name] = repo

    stars = sum(repo["stargazers_count"] for repo in repositories.values())
    svg = SVG_PATH.read_text(encoding="utf-8")
    updated, replacements = re.subn(
        r"(<text x=\"24\" y=\"97\" class=\"label\">Stars: )\d+(</text>)",
        rf"\g<1>{stars}\g<2>",
        svg,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError("Could not find the Stars value in the profile SVG")
    SVG_PATH.write_text(updated, encoding="utf-8")
    print(f"Updated combined stars for {len(repositories)} repositories: {stars}")


if __name__ == "__main__":
    main()
