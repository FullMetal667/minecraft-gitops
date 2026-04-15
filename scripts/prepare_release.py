#!/usr/bin/env python3
from __future__ import annotations
from curseforge import resolve_release

import json
import re
import subprocess
import sys
from pathlib import Path

from common import REPO_ROOT, params_file, overlay_kustomization, server_from_params_filename

release = resolve_release("all-the-mods-10", mc_version="1.20.1")

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("> " + " ".join(cmd), file=sys.stderr)
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=check,
    )


def git_stdout(args: list[str]) -> str:
    result = subprocess.run(
        args,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=True,
    )
    return result.stdout.strip()


def branch_exists(branch: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
    )
    return result.returncode == 0


def sanitize_branch_part(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def main() -> int:
    if len(sys.argv) < 4:
        print(
            "Usage: python3 scripts/prepare_release.py <server|params-file> <version> <server_file_id> [zip]",
            file=sys.stderr,
        )
        return 1

    raw_server = sys.argv[1]
    version = release["version"]
    server_file_id = release["server_file_id"]
    zip_name = sys.argv[4] if len(sys.argv) >= 5 else None

    server = server_from_params_filename(raw_server)
    branch_version = sanitize_branch_part(version)
    branch = f"bot/{server}-{branch_version}"

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=True,
    )

    if status.stdout.strip():
        print("Repository is not clean. Bitte erst committen oder staschen:")
        print(status.stdout)
        return 1

    # main aktualisieren
    run(["git", "checkout", "main"], check=True)
    run(["git", "pull", "origin", "main"], check=True)

    # Arbeitsbranch vorbereiten
    if branch_exists(branch):
        run(["git", "checkout", branch], check=True)
        run(["git", "rebase", "main"], check=True)
    else:
        run(["git", "checkout", "-b", branch], check=True)

    # Server-Dateien aktualisieren
    update_cmd = ["python3", "scripts/update_server.py", server, version, server_file_id]
    if zip_name:
        update_cmd.append(zip_name)

    update_result = run(update_cmd, check=False)
    if update_result.returncode != 0:
        print(update_result.stdout, file=sys.stderr)
        print(update_result.stderr, file=sys.stderr)
        return update_result.returncode

    changed_paths = [
        params_file(server),
        overlay_kustomization(server),
    ]
    changed_rel = [str(p.relative_to(REPO_ROOT)) for p in changed_paths]

    # Änderungen stagen
    run(["git", "add", *changed_rel], check=True)

    status = git_stdout(["git", "status", "--short", "--", *changed_rel])
    diff_cached = git_stdout(["git", "diff", "--cached", "--", *changed_rel])

    committed = False
    push_result = ""
    pr_url = None

    if status:
        run(
            ["git", "commit", "-m", f"chore({server}): update to {version}"],
            check=True,
        )
        push = run(["git", "push", "-u", "origin", branch], check=False)
        push_result = (push.stdout or "") + (push.stderr or "")
        if push.returncode != 0:
            print(push.stdout, file=sys.stderr)
            print(push.stderr, file=sys.stderr)
            return push.returncode
        committed = True

        # Optional: PR URL lesen, falls bereits vorhanden
        pr_view = subprocess.run(
            ["gh", "pr", "view", branch, "--json", "url"],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )
        if pr_view.returncode == 0:
            try:
                pr_url = json.loads(pr_view.stdout)["url"]
            except Exception:
                pr_url = None

    summary = {
        "server": server,
        "version": version,
        "server_file_id": server_file_id,
        "branch": branch,
        "changed_files": changed_rel,
        "status": status,
        "diff": diff_cached,
        "committed": committed,
        "pr_url": pr_url,
        "zip": zip_name,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())