# Changelog

All notable changes to the **NAD C368** Home Assistant integration are documented here.
Alle væsentlige ændringer til **NAD C368**-integrationen er dokumenteret her.

The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses
semantic versioning: bigger features bump the minor (1.2.0 → 1.3.0), small fixes bump the
patch (1.2.0 → 1.2.1).

---

## [1.3.0] – 2026-06-27

### Added / Tilføjet
- **Settings as entities** – Minimum volume, Maximum volume, Volume step and Poll
  interval are now editable `number` entities, and the 8 input names are editable
  `text` entities (all under the device's "Configuration" section). This means the
  full configuration can be changed directly from a dashboard, not only from the
  Configure dialog.
  *Indstillinger som entiteter: min/maks-volumen, volumentrin, poll-interval og de 8
  kildenavne kan nu rettes direkte fra et dashboard – ikke kun i Configure-dialogen.*
- New `text` platform for the source names. */Ny `text`-platform til kildenavne.*
- **Logo** – an original "NAD C368 Control by MrStaLu" badge (`images/logo.png` and
  `images/icon.png`), ready for a dashboard header and for the Home Assistant brands
  repository. *Originalt logo til dashboard og brands-repoet.*

### Notes / Bemærkninger
- Changing one of these entities updates the integration's options and reloads it
  automatically. *Ændring genindlæser integrationen automatisk.*

---

## [1.2.0] – 2026-06-27

Mega-opdatering / major update. Baseline for fremtidige versioner.

### Added / Tilføjet
- **Options flow ("Configure" button)** – change IP address, TCP port, status poll
  interval, the volume %↔dB mapping and rename all 8 inputs directly in the Home
  Assistant UI, with no need to remove and re-add the integration. Changes apply live.
  *Konfigurer-knap i HA: ret IP, port, poll-interval, volumen-mapping og omdøb alle 8
  kilder direkte i GUI'en – uden at slette og tilføje integrationen igen. Ændringer
  træder i kraft med det samme.*
- **Universal services** `nad_c368.send_command` (variable=value) and `nad_c368.query`
  – reach every RS232 command the amplifier exposes from Developer Tools → Actions.
  *Universelle handlinger: send en hvilken som helst kommando og læs værdier tilbage.*
- **Danish + English translations** for the config flow, options flow and services.
  Home Assistant picks the language automatically per user.
  *Dansk + engelsk oversættelse; HA vælger sprog automatisk pr. bruger.*
- **Rename inputs** – the 8 source names set in the options flow are used everywhere
  in the source selector. *Omdøbte kilder bruges overalt i kildevælgeren.*

### Changed / Ændret
- **Instant (optimistic) UI feedback** for volume, mute, source, speakers A/B and tone
  controls – the interface updates immediately on tap instead of waiting for the next
  status poll. *Øjeblikkelig UI-respons på volume, mute, kilde, højttalere og tone.*
- **Faster status sync** – poll interval reduced from 15 s to 5 s and response timeout
  from 3 s to 1 s. *Hurtigere status-synkronisering.*
- **Default volume mapping** is now −80 dB (0 %) to +12 dB (100 %), the amplifier's full
  range. *Standard volumen-mapping er nu −80 dB (0 %) til +12 dB (100 %).*

### Fixed / Rettet
- Slow volume and mute response while the amplifier was powered on (caused by a full
  10-value re-poll after every command). *Langsom volume/mute-respons når forstærkeren
  var tændt.*

---

## [1.0.0] – Initial release / Første udgave

- HACS custom integration for the NAD C368 over a USR-TCP232-302 serial-to-Ethernet
  converter. *HACS-integration til NAD C368 via USR-TCP232-302-konverter.*
- Media player (power, volume, mute, 8 sources), Bass/Treble/Balance numbers, and
  Speaker A/B + Tone Defeat switches. *Media player, bas/diskant/balance og højttaler-
  samt tone-switches.*
