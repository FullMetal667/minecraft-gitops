import subprocess
import sys


def run(cmd):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def branch_exists_remote(branch):
    result = subprocess.run(
        f"git ls-remote --heads origin {branch}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    return bool(result.stdout.strip())


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
    return result.returncode != 0  # 0 = no changes


def create_branch(branch):
    run(f"git checkout -b {branch}")


def commit_and_push(version, branch):
    file_path = "build/params-atm10.env"

    # 🔍 1. Prüfen ob überhaupt Änderungen existieren
    if not has_changes(file_path):
        print(f"No changes detected in {file_path}. Skipping.")
        return

    # 🔍 2. Prüfen ob Branch schon remote existiert
    if branch_exists_remote(branch):
        print(f"Branch {branch} already exists on origin → skipping to avoid duplicate commits.")
        return

    # 🌱 3. Branch erstellen
    create_branch(branch)

    # ➕ 4. Datei adden
    run(f"git add {file_path}")

    # 🔍 5. Prüfen ob staged changes vorhanden sind
    if not has_staged_changes(file_path):
        print(f"No staged changes found in {file_path}. Skipping commit.")
        return

    # 💾 6. Commit
    run(f'git commit -m "ATM10 update to {version}"')

    # 🚀 7. Push
    run("git push -u origin HEAD")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gitops.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    branch = f"bot/atm10-{version}"

    print(f"Running GitOps for version {version}")
    commit_and_push(version, branch)


if __name__ == "__main__":
    main()