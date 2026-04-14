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


def pr_exists(pr_number):
    result = subprocess.run(
        f"gh pr view {pr_number}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def show_pr_summary(pr_number):
    result = run(
        f'gh pr view {pr_number} --json number,title,headRefName,baseRefName,state,mergeable,url',
        capture_output=True
    )
    print(result.stdout)


def merge_pr(pr_number):
    run(f"gh pr merge {pr_number} --merge --delete-branch")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 merge_pr.py <pr_number>")
        sys.exit(1)

    pr_number = sys.argv[1]

    ensure_gh_available()
    ensure_gh_auth()

    if not pr_exists(pr_number):
        print(f"PR #{pr_number} existiert nicht oder ist nicht erreichbar.")
        sys.exit(1)

    print(f"Merge PR #{pr_number}")
    show_pr_summary(pr_number)
    merge_pr(pr_number)


if __name__ == "__main__":
    main()