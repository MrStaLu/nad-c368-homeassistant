# NAD C368 Home Assistant Integration

Control your **NAD C368 amplifier** from Home Assistant via a [USR-TCP232-302](https://www.pusr.com) serial-to-Ethernet converter. Full support for Apple HomeKit via the built-in HA HomeKit Bridge.

## What you get

| Entity | Type | Description |
|---|---|---|
| NAD C368 | `media_player` | Power, volume, mute, source selection |
| Bass | `number` | −7 to +7 dB slider |
| Treble | `number` | −7 to +7 dB slider |
| Balance | `number` | −18 to +18 slider |
| Speaker A | `switch` | On/Off |
| Speaker B | `switch` | On/Off |
| Tone Defeat | `switch` | Bypasses bass/treble EQ |

---

## Hardware required

- NAD C368 amplifier
- [USR-TCP232-302](https://www.pusr.com/products/1-port-rs232-serial-ethernet-converter.html) serial-to-Ethernet converter
- DB9 male-to-male **null modem cable**
- Ethernet patch cable

### Wiring

```
NAD C368 (RS232, DB9 female)
        ↕  null modem DB9 cable
USR-TCP232-302 (DB9 female)
        ↕  Ethernet patch cable
Your network switch / router
```

---

## Installation via HACS

1. In Home Assistant, go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/MrStaLu/NAD-C368-homeassistant` as type **Integration**
3. Search for **NAD C368** and install
4. Restart Home Assistant

## Manual installation

1. Copy the `custom_components/nad_c368` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **NAD C368**
3. Enter the IP address of your USR-TCP232-302 and the TCP port you configured on it

### USR-TCP232-302 converter setup

Configure the converter via its web interface (`http://192.168.0.7` by default):

| Setting | Value |
|---|---|
| Baud rate | 115200 |
| Data bits | 8 |
| Stop bits | 1 |
| Parity | None |
| Work mode | TCP Server |
| Local port | 8234 (or your choice) |

Assign a static IP to the converter in your router's DHCP settings.

---

## Apple HomeKit

Once the integration is running:

1. Go to **Settings → Devices & Services → Add Integration → HomeKit Bridge**
2. The NAD C368 media player will be available to add
3. Scan the HomeKit QR code with your iPhone

The amp will appear in **Apple Home** as a receiver — you can control power, volume, and source from the Home app or Siri.

> Note: Bass/treble/balance sliders are not exposed to HomeKit (HomeKit has no equivalent). They remain available in the HA app and dashboard.

---

## Sources (default mapping)

| Number | Input |
|---|---|
| 1 | Optical 1 |
| 2 | Optical 2 |
| 3 | Coaxial 1 |
| 4 | Coaxial 2 |
| 5 | Phono |
| 6 | Line 1 |
| 7 | Line 2 |
| 8 | Bluetooth |
