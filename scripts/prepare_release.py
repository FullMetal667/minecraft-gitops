import subprocess
import sys

from detect_latest_atm10 import get_latest_server_file


def run(cmd: str) -> None:
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def run_result(cmd: str) -> subprocess.CompletedProcess:
    print(f"> {cmd}")
    return subprocess.run(cmd, shell=True, text=True)


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "latest":
        version, file_id = get_latest_server_file()
        print(f"Detected latest ATM10 release: version={version}, file_id={file_id}")
    elif len(sys.argv) == 3:
        version = sys.argv[1]
        file_id = sys.argv[2]
    else:
        print("Usage:")
        print("  python3 prepare_release.py <version> <file_id>")
        print("  python3 prepare_release.py latest")
        sys.exit(1)

    result = run_result(f"python3 gitops.py {version} {file_id}")

    if result.returncode == 2:
        print(f"Release for ATM10 {version} already exists or nothing changed. Nothing more to do.")
        sys.exit(0)

    if result.returncode != 0:
        print(f"gitops.py failed for ATM10 {version}.")
        sys.exit(result.returncode)

    run(f"python3 create_pr.py {version} {file_id}")


if __name__ == "__main__":
    main()