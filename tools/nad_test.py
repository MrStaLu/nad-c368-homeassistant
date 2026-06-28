#!/usr/bin/env python3
"""
nad_test.py — Test tovejs-forbindelse til NAD C368 via USR-TCP232-302.

Sender en forespørgsel og udskriver svaret fra forstærkeren.
Kør fra din Mac (samme netværk som konverteren):

    python3 nad_test.py

Hvis du ser fx "Main.Power=On" tilbage, virker hele kæden.
"""

import socket
import time

HOST = "192.168.1.200"   # USR-TCP232-302 IP
PORT = 8234              # TCP-port på konverteren
TIMEOUT = 3


def query(sock, command: str) -> str:
    sock.send(f"\r{command}\r".encode("ascii"))
    time.sleep(0.3)
    try:
        data = sock.recv(1024)
    except socket.timeout:
        return ""
    return data.decode("ascii", errors="replace").replace("\r", " ").strip()


def main() -> None:
    print(f"Forbinder til {HOST}:{PORT} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print(f"❌ Kunne ikke forbinde: {e}")
        print("   Tjek: konverterens IP/port, at den er i TCP Server-mode,")
        print("   og at din Mac er på samme netværk (192.168.1.x).")
        return

    print("✅ TCP-forbindelse oprettet. Spørger forstærkeren ...\n")
    for cmd in ("Main.Power?", "Main.Model?", "Main.Volume?", "Main.Source?"):
        resp = query(s, cmd)
        print(f"  → {cmd:14s} svar: {resp or '(intet svar)'}")
    s.close()

    print("\nHvis du ser rigtige svar ovenfor (fx Main.Power=On), er hardwaren klar.")
    print("Hvis alt er '(intet svar)': forbindelsen når konverteren, men ikke")
    print("NAD'en — tjek null modem-kablet, baud 115200/8N1, og at NAD er tændt.")


if __name__ == "__main__":
    main()
