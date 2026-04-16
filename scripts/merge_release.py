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
    def __init__(self, path: str):
        self.path = path
        self.fd = None

    def __enter__(self):
        self.fd = open(self.path, "w")
        try:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(
                "Ein anderer Git-Lauf arbeitet bereits im Repository."
            ) from exc
        self.fd.write(str(os.getpid()))
        self.fd.flush()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.fd:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            self.fd.close()


def run(
    cmd: list[str],
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    print("> " + " ".join(cmd), file=sys.stderr)
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
        env=env,
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    return result


def run_stdout(cmd: list[str], check: bool = True) -> str:
    return run(cmd, check=check).stdout.strip()


def sanitize_branch_part(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def branch_exists_local(branch: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0


def remote_branch_exists(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def is_rebase_in_progress() -> bool:
    git_dir = REPO_ROOT / ".git"
    return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()


def abort_rebase_if_needed() -> None:
    if is_rebase_in_progress():
        run(["git", "rebase", "--abort"], check=False)


def ensure_clean_repo() -> None:
    result = run(["git", "status", "--porcelain"], check=True)
    if result.stdout.strip():
        raise RuntimeError(
            "Repository ist nicht sauber. Bitte vorher laufende Änderungen oder Konflikte bereinigen."
        )


def push_branch_with_auth(branch: str, force_with_lease: bool = False) -> None:
    github_user = os.environ.get("GITHUB_USER")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO", "FullMetal667/minecraft-gitops")

    if not github_user or not github_token:
        raise RuntimeError("GITHUB_USER oder GITHUB_TOKEN fehlt")

    push_url = f"https://{github_user}:{github_token}@github.com/{repo}.git"

    cmd = ["git", "push"]
    if force_with_lease:
        cmd.append("--force-with-lease")
    cmd.extend([push_url, f"{branch}:{branch}"])

    print(
        f"> {' '.join(['git', 'push'] + (['--force-with-lease'] if force_with_lease else []) + [f'https://{github_user}:***@github.com/{repo}.git', f'{branch}:{branch}'])}",
        file=sys.stderr,
    )

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )


def ensure_pr(branch: str, server: str, version: str) -> str:
    view = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "url"],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if view.returncode == 0:
        return json.loads(view.stdout)["url"]

    run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            f"chore({server}): update to {version}",
            "--body",
            f"Automatisches Update für {server} auf Version {version}.",
        ],
        check=True,
    )

    return json.loads(run_stdout(["gh", "pr", "view", branch, "--json", "url"]))["url"]


def checkout_branch(branch: str) -> None:
    run(["git", "fetch", "origin"], check=True)

    if branch_exists_local(branch):
        run(["git", "checkout", branch], check=True)
        run(["git", "reset", "--hard", f"origin/{branch}"], check=True)
        return

    if remote_branch_exists(branch):
        run(["git", "checkout", "-b", branch, f"origin/{branch}"], check=True)
        return

    raise RuntimeError(f"Branch {branch} wurde weder lokal noch auf origin gefunden.")


def conflicted_files() -> list[str]:
    result = run(["git", "diff", "--name-only", "--diff-filter=U"], check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def auto_resolve_known_conflicts(server: str) -> bool:
    expected = {
        f"build/params-{server}.env",
        f"clusters/overlays/{server}/kustomization.yaml",
    }

    conflicts = set(conflicted_files())
    if not conflicts:
        return False

    if not conflicts.issubset(expected):
        return False

    for path in sorted(conflicts):
        run(["git", "checkout", "--theirs", "--", path], check=True)
        run(["git", "add", "--", path], check=True)

    return True


def rebase_branch_onto_main(server: str, branch: str) -> None:
    try:
        run(["git", "rebase", "main"], check=True)
        return
    except subprocess.CalledProcessError as exc:
        if not auto_resolve_known_conflicts(server):
            run(["git", "rebase", "--abort"], check=False)
            raise RuntimeError(
                f"Rebase von {branch} auf main fehlgeschlagen. "
                f"Nicht automatisch auflösbare Konflikte.\n"
                f"stdout:\n{exc.output or ''}\n"
                f"stderr:\n{exc.stderr or ''}"
            ) from exc

    continue_result = run(["git", "rebase", "--continue"], check=False)
    if continue_result.returncode != 0:
        run(["git", "rebase", "--abort"], check=False)
        raise RuntimeError(
            f"Rebase von {branch} auf main konnte trotz Auto-Resolve nicht fortgesetzt werden.\n"
            f"stdout:\n{continue_result.stdout or ''}\n"
            f"stderr:\n{continue_result.stderr or ''}"
        )


def main() -> int:
    args = [arg for arg in sys.argv[1:] if arg != "--yes"]
    auto_yes = "--yes" in sys.argv[1:]

    if len(args) < 2:
        print(
            "Usage: python3 scripts/merge_release.py <server|params-file> <version> [--yes]",
            file=sys.stderr,
        )
        return 1

    server = server_from_params_filename(args[0])
    version = args[1]
    branch_version = sanitize_branch_part(version)
    branch = f"bot/{server}-{branch_version}"

    try:
        with RepoLock(LOCK_PATH):
            abort_rebase_if_needed()
            ensure_clean_repo()

            pr_url = ensure_pr(branch, server, version)

            if not auto_yes:
                answer = input(f"PR {pr_url} jetzt mergen? [y/N]: ").strip().lower()
                if answer not in {"y", "yes", "j", "ja"}:
                    print("Merge abgebrochen.")
                    return 0

            run(["git", "checkout", "main"], check=True)
            run(["git", "pull", "--ff-only", "origin", "main"], check=True)

            checkout_branch(branch)
            rebase_branch_onto_main(server, branch)

            push_branch_with_auth(branch, force_with_lease=True)

            merge_result = run(
                ["gh", "pr", "merge", pr_url, "--squash", "--delete-branch"],
                check=False,
            )
            if merge_result.returncode != 0:
                raise RuntimeError(
                    f"GitHub PR-Merge fehlgeschlagen.\n"
                    f"stdout:\n{merge_result.stdout or ''}\n"
                    f"stderr:\n{merge_result.stderr or ''}"
                )

            print(
                json.dumps(
                    {
                        "server": server,
                        "version": version,
                        "branch": branch,
                        "pr_url": pr_url,
                        "merged": True,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0

    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        if exc.output:
            print(exc.output, file=sys.stderr, end="")
        if exc.stderr:
            print(exc.stderr, file=sys.stderr, end="")
        return exc.returncode
    finally:
        try:
            if is_rebase_in_progress():
                run(["git", "rebase", "--abort"], check=False)
            run(["git", "checkout", "main"], check=False)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())