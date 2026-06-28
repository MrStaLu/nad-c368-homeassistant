<p align="center">
  <img src="images/logo.png" alt="NAD C368 Control by MrStaLu" width="520">
</p>

<h1 align="center">NAD C368 Control</h1>

<p align="center">
  Styr din <b>NAD C368</b>-forstærker fra Home Assistant — og fra Apple HomeKit/Siri —
  via en USR-TCP232-302 seriel-til-Ethernet-konverter.<br>
  <i>Control your NAD C368 amplifier from Home Assistant via RS232 over Ethernet.</i><br>
  En original integration af <b>MrStaLu</b>.
</p>

---

## ✨ Funktioner (v1.3.0)

| Entitet | Type | Hvad |
|---|---|---|
| NAD C368 | `media_player` | Tænd/sluk, volumen, mute, kildevalg (8 indgange) |
| Bas / Diskant | `number` | −7 til +7 dB |
| Balance | `number` | −18 til +18 |
| Højttaler A / B | `switch` | Til/fra |
| Tone-bypass | `switch` | Forbi bas/diskant-EQ |
| Min/Max volumen, trin, poll | `number` | Indstillinger — redigerbare direkte fra dashboardet |
| Kilde 1–8 navn | `text` | Omdøb indgange fra dashboardet |

Derudover: **volumen vist som 0–100 %** (lineær dB-mapping), **universelle handlinger** til alle RS232-kommandoer, og **dansk + engelsk** UI (Home Assistant vælger sprog automatisk).

---

## 🛒 Hardware — og hvor du køber den

Du skal bruge:

- **NAD C368**-forstærker (RS232-port på bagsiden, DB9 hun)
- **USR-TCP232-302** seriel-til-Ethernet-konverter — kan bl.a. købes hos
  **[CDON](https://cdon.dk/hjemme-elektronik/usr-tcp232-302-rs232-till-tcp-ip-omvandlare-serial-till-ethernet-support-dns-dhcp-inbyggd-webbplats-c105000015476055)**
  (alternativt [Fruugo](https://www.fruugo.dk/mini-seriel-portserver-seriel-til-ethernet-modulkonverter-usr-tcp232-302/p-400318900-851897763?language=da),
  [eBay](https://www.ebay.com/itm/334411000168) eller [Amazon](https://www.amazon.de/dp/B01GPGPEBM))
- **DB9 han-han null modem-kabel** (ben 2 og 3 krydset)
- Et **Ethernet-kabel**
- En **Raspberry Pi** med Home Assistant (eller anden HA-installation)

<p align="center"><img src="images/setup.png" alt="Opsætning" width="760"></p>

---

## 🔌 Trin 1 — Konverteren (USR-TCP232-302)

Konverteren har som standard IP **192.168.0.7** og login **admin / admin**. Sæt din computer
midlertidigt på samme net (fx 192.168.0.10), åbn `http://192.168.0.7` i en browser, log ind og indstil:

| Indstilling | Værdi |
|---|---|
| Baud rate | 115200 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |
| Work mode | **TCP Server** |
| Local port | 8234 |
| Device IP | fast IP på dit net, fx 192.168.1.200 |

Lav en DHCP-reservation på din router, så IP'en ikke skifter. Forbind: **NAD C368 → null modem DB9 → konverter → Ethernet → netværk**.

---

## 📦 Trin 2 — Installation i Home Assistant (HACS)

1. Åbn **HACS → Integrations → ⋮ (øverst til højre) → Custom repositories**
2. Indsæt `https://github.com/MrStaLu/NAD-C368-homeassistant` og vælg type **Integration** → **Add**
3. Søg efter **NAD C368** på listen → **Download**
4. **Genstart Home Assistant**

<details>
<summary>Manuel installation (uden HACS)</summary>

1. Kopiér mappen `custom_components/nad_c368` ind i din HA's `config/custom_components/`
2. Genstart Home Assistant
</details>

---

## ⚙️ Trin 3 — Tilføj enheden

1. **Indstillinger → Enheder & tjenester → Tilføj integration**
2. Søg **NAD C368**
3. Indtast konverterens **IP-adresse** og **port** (fx 192.168.1.200 / 8234) → **Send**

Entiteterne oprettes automatisk. Lægger du dem på et dashboard (eller opretter et "NAD C368"-dashboard), får du et fast punkt i sidebaren.

---

## 🎚️ Trin 4 — Justér indstillinger og omdøb kilder

Alle indstillinger er **entiteter**, så du retter dem direkte fra dashboardet eller enhedssiden —
ingen genstart nødvendig.

<p align="center"><img src="images/settings.png" alt="Fremgangsmåde" width="760"></p>

- **Volumen-mapping:** sæt `Minimum volume` (= 0 %) og `Maximum volume` (= 100 %) i dB.
  Standard er −80 → +12 dB. 10 % ≈ −71 dB.
- **Omdøb en kilde:** ret fx tekstfeltet `Input 5 name` fra *Phono* til *Pladespiller* — navnet
  bruges med det samme i kildevælgeren.
- Du kan også bruge **Indstillinger → Enheder & tjenester → NAD C368 → Konfigurer** til det samme.

### Kilder (standard)

| Nr. | Indgang | | Nr. | Indgang |
|---|---|---|---|---|
| 1 | Optical 1 | | 5 | Phono |
| 2 | Optical 2 | | 6 | Line 1 |
| 3 | Coaxial 1 | | 7 | Line 2 |
| 4 | Coaxial 2 | | 8 | Bluetooth |

---

## 🍎 Apple HomeKit / Siri

Tilføj **HomeKit Bridge** (Indstillinger → Enheder & tjenester → Tilføj integration → HomeKit Bridge)
og vælg `media_player.nad_c368`. Så kan du styre tænd/sluk, volumen, mute og kilde fra Apple Home og Siri.
Bas/diskant/balance findes kun i HA-appen (HomeKit har ingen tilsvarende).

---

## 🛠️ Alle kommandoer (avanceret)

To handlinger gør **enhver** RS232-kommando tilgængelig fra HA (Udviklerværktøjer → Handlinger):

- **`nad_c368.send_command`** — `command` + `value`, fx `Source5.Enabled` = `No`
- **`nad_c368.query`** — læs en hvilken som helst værdi tilbage

---

<p align="center"><i>NAD C368 Control — by MrStaLu</i></p>
