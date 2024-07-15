# Gartenpumpensteuerung mit Shelly und Wetterdaten

Dieses Python-Skript steuert eine Gartenpumpe über ein Shelly 1-Relais basierend auf historischen und vorhergesagten Niederschlagsdaten. Die Pumpe wird nur aktiviert, wenn in den letzten drei Tagen kein Regen gefallen ist und in den nächsten zwei Tagen kein Regen erwartet wird. Das Skript kann als Cronjob auf einem Raspberry Pi ausgeführt werden.

## Voraussetzungen

### Hardware
- **Shelly 1 Relais** mit statischer IP-Adresse
- **Gartenpumpe (induktive Last: RC-Snubber nicht vergessen) oder Magnetventil **
- **Raspberry Pi** (oder Raspberry Pi Nano mit SIM-Karte und Relay, falls kein WLAN verfügbar ist)

### Software
- **Python 3.12**
- Python-Bibliotheken: `polars`, `requests`, `wetterdienst`


