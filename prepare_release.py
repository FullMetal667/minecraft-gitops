import subprocess
import sys


def run(cmd):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 prepare_release.py <version> <file_id>")
        sys.exit(1)

    version = sys.argv[1]
    file_id = sys.argv[2]

    run(f"python3 update_atm10.py {version} {file_id}")
    run(f"python3 gitops.py {version}")
    run(f"python3 create_pr.py {version} {file_id}")


if __name__ == "__main__":
    main()
