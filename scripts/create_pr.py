#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

from common import run, server_from_params_filename


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 create_pr.py <server|params-file> <version>")
        return 1

    server = server_from_params_filename(sys.argv[1])
    version = sys.argv[2]
    branch = f"bot/{server}-{version}"

    run(
        f'gh pr create '
        f'--base main '
        f'--head {branch} '
        f'--title "chore({server}): update to {version}" '
        f'--body "Automatisches Update für {server} auf Version {version}."'
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())