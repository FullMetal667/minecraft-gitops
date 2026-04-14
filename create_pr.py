import json
import os
import sys
import urllib.error
import urllib.request


def create_pull_request(owner: str, repo: str, head: str, base: str, version: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set.")

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    payload = {
        "title": f"ATM10 update to {version}",
        "head": head,
        "base": base,
        "body": (
            f"Automatisch erstellter Update-PR für ATM10.\n\n"
            f"- Version: `{version}`\n"
            f"- Source branch: `{head}`\n"
            f"- Target branch: `{base}`\n\n"
            f"Bitte params, Build-Verhalten und Rollout prüfen."
        ),
        "maintainer_can_modify": True,
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "minecraft-gitops-agent",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
            return response_data["html_url"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {e.code}: {body}") from e


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python3 create_pr.py <owner> <repo> <head_branch> <base_branch> <version>")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    head = sys.argv[3]
    base = sys.argv[4]
    version = sys.argv[5]

    pr_url = create_pull_request(owner, repo, head, base, version)
    print(f"PR created: {pr_url}")

