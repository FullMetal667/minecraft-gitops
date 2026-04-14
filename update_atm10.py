import re
from pathlib import Path
import sys

FILE = Path("build/params-atm10.env")


def update_env(version: str, file_id: str):
    content = FILE.read_text()

    content = re.sub(r"^IMAGE_TAG=.*$", f"IMAGE_TAG={version}", content, flags=re.MULTILINE)
    content = re.sub(r"^FILE_ID=.*$", f"FILE_ID={file_id}", content, flags=re.MULTILINE)

    FILE.write_text(content)

    print("Updated params-atm10.env:")
    print(content)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 update_atm10.py <image_tag> <file_id>")
        sys.exit(1)

    image_tag = sys.argv[1]
    file_id = sys.argv[2]

    print(f"Using IMAGE_TAG={image_tag}")
    print(f"Using FILE_ID={file_id}")

    update_env(image_tag, file_id)