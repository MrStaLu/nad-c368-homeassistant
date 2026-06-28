#!/usr/bin/env python3
"""
nad_send.py — Send a raw RS232 command to NAD C368 via USR-TCP232-302 converter.

Usage:
    python3 /config/nad_send.py "Main.Bass=-3"
    python3 /config/nad_send.py "Main.SpeakerA=On"

Place this file at /config/nad_send.py on your Home Assistant instance.
"""

import sys
import socket
import time

# ── Change these to match your converter ──────────────────────────────────────
HOST = "192.168.1.200"   # IP address of the USR-TCP232-302
PORT = 8234              # TCP port configured on the converter
# ─────────────────────────────────────────────────────────────────────────────

TIMEOUT = 3  # seconds


def send_command(command: str) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    try:
        s.connect((HOST, PORT))
        msg = f"\r{command}\r"
        s.send(msg.encode("ascii"))
        time.sleep(0.1)   # give the amp time to process
    finally:
        s.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: nad_send.py <command>", file=sys.stderr)
        sys.exit(1)
    send_command(sys.argv[1])
