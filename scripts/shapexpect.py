import hashlib
import random
import string
import pexpect

HOST = "guess-password-easy.2025-bq.ctfcompetition.com"
PORT = "1337"

def make_zero_hash_input():
    while True:
        s = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        h = hashlib.sha256(s.encode()).digest()
        if h[0] == 0:
            return s

child = pexpect.spawn(
    f"nc {HOST} {PORT}",
    encoding="utf-8",
    timeout=10
)

attempts = 0

while True:
    child.expect("Your guess:")

    guess = make_zero_hash_input()
    attempts += 1

    print(f"[{attempts}] trying: {guess}")

    child.sendline(guess)

    child.expect([
        "Wrong! Try again in a second...",
        "CTF\\{.*\\}",
        pexpect.EOF,
        pexpect.TIMEOUT
    ])

    output = child.before + child.after
    print(output)

    if "CTF{" in output:
        print("\nFLAG FOUND:")
        print(output)
        break
