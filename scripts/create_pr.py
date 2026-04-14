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


def branch_exists_remote(branch):
    result = subprocess.run(
        f"git ls-remote --heads origin {branch}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    return bool(result.stdout.strip())


def pr_already_exists(branch):
    result = subprocess.run(
        f'gh pr list --head "{branch}" --state open --json number',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("Fehler beim Prüfen vorhandener PRs.")
        print(result.stderr.strip())
        sys.exit(1)

    return result.stdout.strip() not in ("[]", "")


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


def create_pr(version, file_id):
    branch = f"bot/atm10-{version}"
    title = f"ATM10 update to {version}"
    body = (
        f"Automated ATM10 update to version {version}.\n\n"
        f"- IMAGE_TAG={version}\n"
        f"- FILE_ID={file_id}\n"
        f"- Branch={branch}"
    )

    if not branch_exists_remote(branch):
        print(f"Remote-Branch {branch} existiert nicht. Bitte zuerst gitops.py ausführen.")
        sys.exit(1)

    if pr_already_exists(branch):
        print(f"Für {branch} existiert bereits ein offener PR. Abbruch.")
        return

    run(
        f'gh pr create '
        f'--base main '
        f'--head "{branch}" '
        f'--title "{title}" '
        f'--body "{body}"'
    )


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 create_pr.py <version> <file_id>")
        sys.exit(1)

    version = sys.argv[1]
    file_id = sys.argv[2]

    ensure_gh_available()
    ensure_gh_auth()

    print(f"Erstelle PR für ATM10-Version {version} mit FILE_ID {file_id}")
    create_pr(version, file_id)


if __name__ == "__main__":
    main()