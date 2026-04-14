import subprocess

def run(cmd):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def create_branch(version):
    branch = f"bot/atm10-{version}"
    run(f"git checkout -b {branch}")
    return branch

def commit_and_push(version):
    run("git add build/params-atm10.env")
    run(f'git commit -m "ATM10 update to {version}"')
    run("git push origin HEAD")

if __name__ == "__main__":
    branch = create_branch("6.6")
    commit_and_push("6.6")
