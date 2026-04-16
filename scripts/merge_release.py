#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys

from common import REPO_ROOT, server_from_params_filename


LOCK_PATH = "/tmp/minecraft-gitops-repo.lock"


class RepoLock:
    def __enter__(self):
        self.fd = open(LOCK_PATH, "w")
        try:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Ein anderer Git-Prozess läuft bereits.")
        return self

    def __exit__(self, *args):
        fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
        self.fd.close()


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("> " + " ".join(cmd), file=sys.stderr)

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env={**os.environ, "GIT_EDITOR": "true"},
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )

    return result


def sanitize_branch_part(value: str) -> str:
    value = re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-")
    return value or "unknown"


def ensure_pr(branch: str, server: str, version: str) -> str:
    view = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "url"],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
    )

    if view.returncode == 0:
        return json.loads(view.stdout)["url"]

    run([
        "gh", "pr", "create",
        "--base", "main",
        "--head", branch,
        "--title", f"chore({server}): update to {version}",
        "--body", f"Automatisches Update für {server} auf Version {version}.",
    ])

    out = run(["gh", "pr", "view", branch, "--json", "url"])
    return json.loads(out.stdout)["url"]


def checkout_branch(branch: str):
    run(["git", "fetch", "origin"])
    run(["git", "checkout", branch])
    run(["git", "reset", "--hard", f"origin/{branch}"])


def auto_resolve(server: str):
    conflicts = run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        check=False,
    ).stdout.splitlines()

    allowed = {
        f"build/params-{server}.env",
        f"clusters/overlays/{server}/kustomization.yaml",
    }

    conflicts = {c.strip() for c in conflicts if c.strip()}

    if not conflicts:
        return False

    if not conflicts.issubset(allowed):
        return False

    for f in conflicts:
        run(["git", "checkout", "--theirs", f])
        run(["git", "add", f])

    return True


def rebase(server: str):
    r = run(["git", "rebase", "main"], check=False)
    if r.returncode == 0:
        return

    if not auto_resolve(server):
        run(["git", "rebase", "--abort"], check=False)
        raise RuntimeError("Nicht automatisch lösbarer Konflikt")

    r = run(["git", "rebase", "--continue"], check=False)
    if r.returncode != 0:
        run(["git", "rebase", "--abort"], check=False)
        raise RuntimeError("Rebase konnte nicht fortgesetzt werden")


def push(branch: str):
    user = os.environ["GITHUB_USER"]
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ.get("GITHUB_REPO", "FullMetal667/minecraft-gitops")

    url = f"https://{user}:{token}@github.com/{repo}.git"

    run([
        "git", "push", "--force-with-lease",
        url, f"{branch}:{branch}"
    ])


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: merge_release.py <server> <version> --yes", file=sys.stderr)
        return 1

    if "--yes" not in sys.argv:
        print("Merge nur mit --yes erlaubt (Bot-Safety).")
        return 0

    server = server_from_params_filename(sys.argv[1])
    version = sys.argv[2]

    branch = f"bot/{server}-{sanitize_branch_part(version)}"

    try:
        with RepoLock():
            pr_url = ensure_pr(branch, server, version)

            run(["git", "checkout", "main"])
            run(["git", "pull", "--ff-only", "origin", "main"])

            checkout_branch(branch)
            rebase(server)
            push(branch)

            merge = run(
                ["gh", "pr", "merge", pr_url, "--squash", "--delete-branch"],
                check=False,
            )

            if merge.returncode != 0:
                raise RuntimeError(
                    f"Merge fehlgeschlagen:\n{merge.stderr}"
                )

            print(json.dumps({
                "server": server,
                "version": version,
                "merged": True,
                "pr": pr_url
            }, indent=2))

            return 0

    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())