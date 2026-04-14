import re
from pathlib import Path

FILE = Path("build/params-atm10.env")

def update_env(version: str, file_id: str):
    content = FILE.read_text()

    content = re.sub(r"IMAGE_TAG=.*", f"IMAGE_TAG={version}", content)
    content = re.sub(r"FILE_ID=.*", f"FILE_ID={file_id}", content)

    FILE.write_text(content)

    print("Updated params-atm10.env:")
    print(content)


if __name__ == "__main__":
    update_env("6.6", "7892979")
