"""Async TCP client for NAD C368 via USR-TCP232-302 serial-to-Ethernet converter."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5.0
RESPONSE_TIMEOUT = 1.0
RECONNECT_DELAY = 10.0  # seconds before reconnect attempt


class NADClient:
    """Maintains a persistent async TCP connection to the NAD C368."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._connected = False

    # ── Connection management ────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Open TCP connection. Returns True on success."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=CONNECT_TIMEOUT,
            )
            self._connected = True
            _LOGGER.debug("Connected to NAD C368 at %s:%s", self._host, self._port)
            return True
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Could not connect to NAD C368: %s", err)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def _ensure_connected(self) -> bool:
        if not self._connected:
            return await self.connect()
        return True

    # ── Send / Query ─────────────────────────────────────────────────────────

    async def send_command(self, variable: str, value: str) -> bool:
        """Send a set command: Main.Variable=Value"""
        async with self._lock:
            if not await self._ensure_connected():
                return False
            try:
                cmd = f"\r{variable}={value}\r"
                self._writer.write(cmd.encode("ascii"))
                await self._writer.drain()
                _LOGGER.debug("Sent: %s=%s", variable, value)
                return True
            except (OSError, ConnectionResetError) as err:
                _LOGGER.warning("Send failed (%s), will reconnect", err)
                await self.disconnect()
                return False

    async def query(self, variable: str) -> Optional[str]:
        """Send a query and return the value string, or None on failure."""
        async with self._lock:
            if not await self._ensure_connected():
                return None
            try:
                cmd = f"\r{variable}?\r"
                self._writer.write(cmd.encode("ascii"))
                await self._writer.drain()

                # Read lines until we find the response we care about
                deadline = asyncio.get_event_loop().time() + RESPONSE_TIMEOUT
                prefix = f"{variable}="

                while asyncio.get_event_loop().time() < deadline:
                    timeout_left = deadline - asyncio.get_event_loop().time()
                    try:
                        raw = await asyncio.wait_for(
                            self._reader.readuntil(b"\r"),
                            timeout=timeout_left,
                        )
                        line = raw.decode("ascii", errors="ignore").strip()
                        if line.startswith(prefix):
                            return line[len(prefix):]
                    except asyncio.TimeoutError:
                        break
                    except Exception:
                        break

                _LOGGER.debug("No response for query: %s", variable)
                return None

            except (OSError, ConnectionResetError) as err:
                _LOGGER.warning("Query failed (%s), will reconnect", err)
                await self.disconnect()
                return None

    # ── Convenience helpers ──────────────────────────────────────────────────

    async def get_power(self) -> Optional[bool]:
        val = await self.query("Main.Power")
        if val is None:
            return None
        return val.strip() == "On"

    async def set_power(self, on: bool) -> bool:
        return await self.send_command("Main.Power", "On" if on else "Off")

    async def get_volume(self) -> Optional[float]:
        val = await self.query("Main.Volume")
        try:
            return float(val) if val else None
        except ValueError:
            return None

    async def set_volume(self, db: float) -> bool:
        return await self.send_command("Main.Volume", str(int(db)))

    async def get_mute(self) -> Optional[bool]:
        val = await self.query("Main.Mute")
        return val.strip() == "On" if val else None

    async def set_mute(self, muted: bool) -> bool:
        return await self.send_command("Main.Mute", "On" if muted else "Off")

    async def get_source(self) -> Optional[str]:
        return await self.query("Main.Source")

    async def set_source(self, source_number: str) -> bool:
        return await self.send_command("Main.Source", source_number)

    async def get_bool_var(self, variable: str) -> Optional[bool]:
        val = await self.query(variable)
        return val.strip() == "On" if val else None

    async def set_bool_var(self, variable: str, on: bool) -> bool:
        return await self.send_command(variable, "On" if on else "Off")

    async def get_int_var(self, variable: str) -> Optional[int]:
        val = await self.query(variable)
        try:
            return int(val) if val else None
        except ValueError:
            return None

    async def set_int_var(self, variable: str, value: int) -> bool:
        return await self.send_command(variable, str(value))
