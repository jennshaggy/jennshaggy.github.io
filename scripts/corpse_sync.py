#!/usr/bin/env python3

import re
import sys
from pathlib import Path

REGION_INDEX = {
    "WORLD": 0,
    "NORTH_AMERICA": 1,
    "LATIN_AMERICA": 2,
    "EUROPE": 3,
    "EU_EASTERN": 4,
    "ASIA": 8,
    "EAST_ASIA": 9,
    "SUB_SAHARAN_AFRICA": 16,
    "AFRICA_EAST": 17,
    "AFRICA_WEST": 18,
    "AFRICA_SOUTH": 20,
    "RUSSIA": 21,
    "OCEANIA": 24,
}

WEEKDAY_KEY = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}

ENV_KEY = bytes.fromhex("f07ec6a4")

PATTERN = re.compile(
    r"^([^,]+), "
    r"(\d+)/(\d+)/(\d+) "
    r"(\d+):(\d+):(\d+) "
    r"(\S+) (\S+) \| Region=(\S+)$"
)


def decode_record(match):
    weekday = match.group(1)
    day, month, year = map(int, match.group(2, 3, 4))
    hour, minute, second = map(int, match.group(5, 6, 7))
    _ampm = match.group(8)
    timezone = match.group(9)
    region = match.group(10)

    # FUN_14000314a
    if timezone == "GMT":
        old_minute = minute
        pivot = int((minute + hour - second) / 2)
        hour -= pivot
        minute = pivot
        second = old_minute - pivot

    region_index = REGION_INDEX[region]

    # FUN_140003117: each region bit controls one field XOR.
    if region_index & 0x10:
        hour ^= 0x0C
    if region_index & 0x08:
        minute ^= 0x1E
    if region_index & 0x04:
        second ^= 0x1E
    if region_index & 0x02:
        day ^= 0x10
    if region_index & 0x01:
        month ^= 0x06

    # FUN_140003215: pack the fields into one 32-bit value.
    packed = (
        (hour << 27)
        | (minute << 21)
        | (second << 15)
        | (day << 10)
        | (month << 6)
        | (year - 1990)
    ) & 0xFFFFFFFF

    weekday_xor = WEEKDAY_KEY.get(weekday, 1)
    raw = packed.to_bytes(4, "big")

    return bytes(
        raw[i] ^ weekday_xor ^ ENV_KEY[i]
        for i in range(4)
    )


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} suspicious.log")

    payload = bytearray()
    decoded_records = 0

    for line in Path(sys.argv[1]).read_text().splitlines():
        match = PATTERN.match(line)

        if not match:
            continue

        payload.extend(decode_record(match))
        decoded_records += 1

    Path("payload.bin").write_bytes(payload)

    print(f"decoded_records={decoded_records}")
    print(f"payload_size={len(payload)}")
    print(f"first_32_bytes={payload[:32].hex()}")
    print("saved=payload.bin")


if __name__ == "__main__":
    main()
