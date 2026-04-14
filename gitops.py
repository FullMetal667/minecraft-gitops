import subprocess

def run(cmd):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def create_or_checkout_branch(version):
    branch = f"bot/atm10-{version}"

    result = subprocess.run(
        f"git rev-parse --verify {branch}",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        run(f"git checkout {branch}")
    else:
        run(f"git checkout -b {branch}")

    return branch


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
        f"git diff --cached --name-only -- {file_path}",
        shell=True,
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


def commit_and_push(version):
    file_path = "build/params-atm10.env"

    if not has_changes(file_path):
        print(f"No changes detected in {file_path}. Skipping commit.")
        return

    run(f"git add {file_path}")

    if not has_staged_changes(file_path):
        print(f"No staged changes found in {file_path}. Skipping commit.")
        return

    run(f'git commit -m "ATM10 update to {version}"')
    run("git push -u origin HEAD")


if __name__ == "__main__":
    version = "6.6"
    branch = create_or_checkout_branch(version)
    commit_and_push(version)