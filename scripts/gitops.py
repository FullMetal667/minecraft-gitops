#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from common import (
    REPO_ROOT,
    ensure_server_exists,
    params_file,
    overlay_kustomization,
    run,
    server_from_params_filename,
)


def branch_exists(branch: str) -> bool:
    result = subprocess.run(
        f"git rev-parse --verify {branch}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return result.returncode == 0


def has_changes(paths: list[Path]) -> bool:
    quoted = " ".join(str(p) for p in paths)
    result = subprocess.run(
        f"git status --porcelain -- {quoted}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return bool(result.stdout.strip())


def checkout_main_and_update() -> None:
    run("git checkout main")
    run("git pull origin main")


def create_or_checkout_branch(server: str, version: str) -> str:
    branch = f"bot/{server}-{version}"

    if branch_exists(branch):
        run(f"git checkout {branch}")
        run("git rebase main")
    else:
        run(f"git checkout -b {branch}")

    return branch


def commit_and_push(server: str, version: str, changed_paths: list[Path], branch: str) -> None:
    quoted = " ".join(str(p) for p in changed_paths)

    run(f"git add {quoted}")

    if not has_changes(changed_paths):
        print("Keine Änderungen erkannt. Kein Commit notwendig.")
        return

    run(f'git commit -m "chore({server}): update to {version}"')

    github_user = os.environ.get("GITHUB_USER")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO", "FullMetal667/minecraft-gitops")

    if not github_user or not github_token:
        raise RuntimeError("GITHUB_USER oder GITHUB_TOKEN fehlt")

    push_url = f"https://{github_user}:{github_token}@github.com/{repo}.git"

    print(f"> git push https://{github_user}:***@github.com/{repo}.git {branch}:{branch}")
    subprocess.run(
        ["git", "push", push_url, f"{branch}:{branch}"],
        check=True,
        cwd=REPO_ROOT,
    )


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: python3 gitops.py <server|params-file> <version> <file_id> [zip]")
        return 1

    server = server_from_params_filename(sys.argv[1])
    version = sys.argv[2]
    file_id = sys.argv[3]
    zip_name = sys.argv[4] if len(sys.argv) >= 5 else None

    ensure_server_exists(server)

    print(f"Running GitOps for server={server}, version={version}, file_id={file_id}")

    checkout_main_and_update()
    branch = create_or_checkout_branch(server, version)

    cmd = f"python3 scripts/update_server.py {server} {version} {file_id}"
    if zip_name:
        cmd += f" {zip_name}"
    run(cmd)

    changed_paths = [
        params_file(server),
        overlay_kustomization(server),
    ]

    commit_and_push(server, version, changed_paths, branch)

    print(f"Fertig. Branch: {branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())