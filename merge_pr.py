import json
import subprocess
import sys


def run(cmd, capture_output=False):
    print(f"> {cmd}")
    return subprocess.run(
        cmd,
        shell=True,
        check=True,
        text=True,
        capture_output=capture_output
    )


def ensure_gh_available():
    result = subprocess.run(
        "gh --version",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode != 0:
        print("GitHub CLI 'gh' ist nicht installiert oder nicht im PATH.")
        sys.exit(1)


def ensure_gh_auth():
    result = subprocess.run(
        "gh auth status",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode != 0:
        print("GitHub CLI ist nicht eingeloggt. Bitte zuerst 'gh auth login' ausführen.")
        sys.exit(1)


def get_pr_info(pr_number):
    result = run(
        f'gh pr view {pr_number} --json number,title,headRefName,baseRefName,state,mergeable,url',
        capture_output=True
    )
    return json.loads(result.stdout)


def merge_pr(pr_number):
    run(f"gh pr merge {pr_number} --merge --delete-branch")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 merge_pr.py <pr_number>")
        sys.exit(1)

    pr_number = sys.argv[1]

    ensure_gh_available()
    ensure_gh_auth()

    try:
        pr = get_pr_info(pr_number)
    except subprocess.CalledProcessError:
        print(f"PR #{pr_number} existiert nicht oder ist nicht erreichbar.")
        sys.exit(1)

    print(pr)

    if pr["state"] != "OPEN":
        print(f"PR #{pr_number} ist bereits {pr['state']}. Kein Merge nötig.")
        return

    merge_pr(pr_number)
    print("PR merged successfully.")


if __name__ == "__main__":
    main()