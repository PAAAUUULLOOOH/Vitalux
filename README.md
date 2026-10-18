<p align="center"><img src="assets/vitalux-readme-dark.svg" alt="Vitalux" width="285"></p>

<h3 align="center">Dein Linux-System auf einen Blick.</h3>
<p align="center">Native Systemüberwachung mit Live-Dashboard, Analysen und Laufwerksdiagnose.</p>
<p align="center"><a href="https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest"><strong>Vitalux herunterladen</strong></a> · <a href="#funktionen">Funktionen</a> · <a href="#installation">Installation</a> · <a href="#hilfe">Hilfe</a></p>

<p align="center"><img src="assets/vitalux-dashboard-preview.png" alt="Vitalux im Glass-Design" width="1000"></p>

## Funktionen

| Bereich | Möglichkeiten |
| --- | --- |
| **Übersicht** | Verschiebbare Live-Kacheln, **Systemzustand** mit Score und Hinweisen |
| **CPU / GPU / RAM** | Auslastung, Takt, Temperaturen, VRAM, Verlaufsdiagramme |
| **Netzwerk / Laufwerke** | Datenraten, SMART, Partitionen und Laufwerks-Benchmarks |
| **System / Sensoren** | Distribution, Kernel, Mesa, Treiber und verfügbare Messwerte |
| **Vitalux Insights** | Performance-Hinweise, Gaming-Sessions, Vergleiche und Ereignisverlauf |
| **Einstellungen** | Designs, Akzentfarben, Hintergrundbilder, Warnungen und Render-Modus |

### Design und Personalisierung

Standard ist **Glass mit Vitalux-Blau**. Zusätzlich stehen **Black Glass**, **Black Glass Gold** (fester Goldakzent), **Holographic** (undurchsichtiges HUD ohne Glas), **Dark**, **Light** und **Minimalistisch** zur Auswahl.

Eigene Bilder, Farben und der animierte Hintergrund **Funkeln** lassen sich konfigurieren. **„Hintergrundfarbe automatisch“** ist ausschließlich bei einem ausgewählten **eigenen Hintergrundbild** aktiv, sonst ausgegraut. Beim Hintergrundwechsel kehrt die vorherige Akzentfarbe zurück. Black Glass Gold sperrt die Akzentfarben unabhängig davon.

## Installation

Unter [Releases](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest) gibt es **AppImage**, **portable Vollversions-ZIP** und **Update-ZIP**, inklusive gebündelter Python-/Qt-Laufzeit.

- **AppImage:** ausführbar machen und starten; optional benutzerweit installieren.
- **ZIP:** vollständig entpacken und `run.sh` starten. Kein separates Python nötig.

Zielplattform ist aktuelles **Linux x86-64** mit Wayland oder X11. Nicht jeder Treiber und Sensor wird unterstützt; einige Systembibliotheken und gegebenenfalls FUSE müssen vorhanden sein. CPU-Rendering ist der Standard; OpenGL und Qt Quick sind optional.

## Hilfe

Die interaktive Anleitung findest du unter **Info → Anleitung**. Fehlerprotokolle liegen unter `~/.local/state/vitalux/`; bei Startproblemen hilft `Portable-pruefen.sh`. Benchmarks können temporär Daten schreiben.

**Made by PAAAUUULLOOOH.** Danke an [TimBooH](https://github.com/TimBooH) für Unterstützung bei Hintergrundbildern und der Grafikausgabe. [Fehler melden](https://github.com/PAAAUUULLOOOH/Vitalux/issues).
