#!/usr/bin/env python3
"""
nad_probe.py — Find ud af HVILKE setup-indstillinger din NAD C368 svarer på
over RS232. Sender en masse forespørgsler og viser svarene.

Kør fra din Mac (samme netværk som konverteren), med NAD'en TÆNDT:

    python3 ~/Claude/"NAD368 styring"/nad_probe.py

Alt der får et svar (fx "Source1.Enabled=Yes") kan vi styre fra Home Assistant.
Linjer med "(intet svar)" understøttes sandsynligvis ikke over RS232.
"""

import socket
import time

HOST = "192.168.1.200"   # USR-TCP232-302 IP
PORT = 8234              # TCP-port på konverteren
READ_WINDOW = 0.4        # sek. der lyttes efter svar pr. forespørgsel

# Hovedindstillinger (setup-menu + status)
MAIN_VARS = [
    "Main.Model", "Main.Version",
    "Main.Power", "Main.Volume", "Main.Mute", "Main.Source",
    "Main.Balance", "Main.Bass", "Main.Treble", "Main.ToneDefeat",
    "Main.SpeakerA", "Main.SpeakerB",
    "Main.Brightness", "Main.AutoStandby", "Main.AutoSense",
    "Main.ControlStandby", "Main.Standby", "Main.Dimmer",
    "Main.IRChannel", "Main.AnalogGain", "Main.DigitalAudio",
    "Main.Trigger", "Main.TriggerIn", "Main.TriggerOut",
]

# Pr. kilde (1-10): aktivér/deaktivér, navn, gain, trigger osv.
SOURCE_FIELDS = ["Enabled", "Name", "Gain", "Trigger", "VolumeFixed",
                 "VolumeControl", "AudioInput", "TriggerOut", "Visible"]


def build_queries():
    qs = list(MAIN_VARS)
    for n in range(1, 11):
        for f in SOURCE_FIELDS:
            qs.append(f"Source{n}.{f}")
    return qs


def main() -> None:
    print(f"Forbinder til {HOST}:{PORT} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(READ_WINDOW)
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print(f"❌ Kunne ikke forbinde: {e}")
        return
    print("✅ Forbundet. Prober (kan tage ~30 sek.) ...\n")

    supported, unsupported = [], []
    for var in build_queries():
        s.send(f"\r{var}?\r".encode("ascii"))
        time.sleep(0.1)
        buf = b""
        end = time.time() + READ_WINDOW
        while time.time() < end:
            try:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
            except socket.timeout:
                break
        text = buf.decode("ascii", errors="replace")
        # find en linje der starter med variabelnavnet
        answer = ""
        for line in text.replace("\r", "\n").split("\n"):
            line = line.strip()
            if line.lower().startswith(var.lower().split("?")[0]):
                answer = line
                break
        if answer:
            supported.append(answer)
            print(f"  ✅ {answer}")
        else:
            unsupported.append(var)
    s.close()

    print("\n──────── OPSUMMERING ────────")
    print(f"Understøttet ({len(supported)}):")
    for a in supported:
        print(f"   {a}")
    print(f"\nIkke understøttet / intet svar ({len(unsupported)}):")
    print("   " + ", ".join(unsupported))
    print("\nKopiér hele dette output ind i chatten, så bygger jeg HA-kontroller for de understøttede.")


if __name__ == "__main__":
    main()
