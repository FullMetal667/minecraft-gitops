#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys

from common import REPO_ROOT, server_from_params_filename


def run_capture(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, text=True, capture_output=True, cwd=REPO_ROOT, check=check)
    return result.stdout.strip()


def ensure_pr(branch: str, server: str, version: str) -> str:
    view = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "url"],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
    )
    if view.returncode == 0:
        return json.loads(view.stdout)["url"]

    subprocess.run(
        [
            "gh", "pr", "create",
            "--base", "main",
            "--head", branch,
            "--title", f"chore({server}): update to {version}",
            "--body", f"Automatisches Update für {server} auf Version {version}.",
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    return json.loads(run_capture(["gh", "pr", "view", branch, "--json", "url"]))["url"]


def main() -> int:
    args = [arg for arg in sys.argv[1:] if arg != "--yes"]
    auto_yes = "--yes" in sys.argv[1:]

    if len(args) < 2:
        print("Usage: python3 scripts/merge_release.py <server|params-file> <version> [--yes]")
        return 1

    server = server_from_params_filename(args[0])
    version = args[1]
    branch = f"bot/{server}-{version}"

    pr_url = ensure_pr(branch, server, version)

    if not auto_yes:
        answer = input(f"PR {pr_url} jetzt mergen? [y/N]: ").strip().lower()
        if answer not in {"y", "yes", "j", "ja"}:
            print("Merge abgebrochen.")
            return 0

    subprocess.run(["gh", "pr", "merge", branch, "--squash", "--delete-branch"], cwd=REPO_ROOT, check=True)
    print(json.dumps({
        "server": server,
        "version": version,
        "branch": branch,
        "pr_url": pr_url,
        "merged": True,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())