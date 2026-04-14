import subprocess
import sys


FILE_PATH = "../build/params-atm10.env"


def run(cmd):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def has_changes(file_path):
    result = subprocess.run(
        f"git status --porcelain -- {file_path}",
        shell=True,
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


def has_staged_changes(file_path):
    result = subprocess.run(
        f"git diff --cached --quiet -- {file_path}",
        shell=True
    )
    return result.returncode != 0


def branch_exists_remote(branch):
    result = subprocess.run(
        f"git ls-remote --heads origin {branch}",
        shell=True,
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


def ensure_worktree_safe():
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True
    )

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    allowed = {f"M {FILE_PATH}", f"?? {FILE_PATH}"}

    disallowed = [line for line in lines if line not in allowed]

    if disallowed:
        print("Working tree is not clean. Please commit, stash, or discard these changes first:")
        for line in disallowed:
            print(f"  {line}")
        sys.exit(1)


def checkout_fresh_main():
    run("git checkout main")
    run("git pull origin main")


def create_branch(branch):
    run(f"git checkout -b {branch}")


def run_update(version, file_id):
    run(f"python3 update_atm10.py {version} {file_id}")


def commit_and_push(version):
    run(f"git add {FILE_PATH}")

    if not has_staged_changes(FILE_PATH):
        print(f"No staged changes found in {FILE_PATH}. Skipping commit.")
        return False

    run(f'git commit -m "ATM10 update to {version}"')
    run("git push -u origin HEAD")
    return True


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 gitops.py <version> <file_id>")
        sys.exit(1)

    version = sys.argv[1]
    file_id = sys.argv[2]
    branch = f"bot/atm10-{version}"

    print(f"Running GitOps for version {version} with FILE_ID {file_id}")

    if branch_exists_remote(branch):
        print(f"Remote branch {branch} already exists. Nothing to do.")
        sys.exit(2)

    ensure_worktree_safe()
    checkout_fresh_main()
    create_branch(branch)
    run_update(version, file_id)

    if not has_changes(FILE_PATH):
        print(f"No changes detected in {FILE_PATH}. Skipping.")
        sys.exit(2)

    changed = commit_and_push(version)
    if not changed:
        sys.exit(2)


if __name__ == "__main__":
    main()