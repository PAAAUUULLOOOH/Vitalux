> **Experimentelle Glas-/Gold-Vorschau:** In diesem Branch funktioniert auch
> **Code → Download ZIP**. ZIP vollständig entpacken und `bash run.sh` starten.
> Python und Qt sind enthalten und werden beim ersten Start automatisch entpackt.
> Einzelheiten: [DESIGN-VORSCHAU.md](DESIGN-VORSCHAU.md).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/vitalux-readme-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/vitalux-readme-light.svg">
    <img src="assets/vitalux-readme-light.svg" alt="Vitalux – Linux-Systemmonitor" width="285">
  </picture>
</p>

<h3 align="center">Dein Linux-System. Alle wichtigen Informationen. Eine Anwendung.</h3>
<p align="center">Nativer Systemmonitor mit Live-Telemetrie, Hardwarediagnose, Leistungsanalysen und individuell gestaltbarem Dashboard.</p>

<p align="center">
  <a href="https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest"><img alt="Aktuelle Version" src="https://img.shields.io/github/v/release/PAAAUUULLOOOH/Vitalux?label=Version"></a>
  <img alt="Linux x86-64" src="https://img.shields.io/badge/Linux-x86__64-1793d1?logo=linux&logoColor=white">
  <img alt="Deutsch und Englisch" src="https://img.shields.io/badge/Sprache-DE%20%7C%20EN-5375bf">
  <img alt="Status: Entwicklung" src="https://img.shields.io/badge/Status-in%20Entwicklung-64748b">
</p>

<p align="center">
  <a href="https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest"><strong>Vitalux herunterladen</strong></a>
  &nbsp;·&nbsp; <a href="#funktionen">Funktionen</a>
  &nbsp;·&nbsp; <a href="#design-und-personalisierung">Design</a>
  &nbsp;·&nbsp; <a href="#installation">Installation</a>
  &nbsp;·&nbsp; <a href="#updates">Updates</a>
  &nbsp;·&nbsp; <a href="#hilfe-und-fehlerbehebung">Hilfe</a>
</p>

> [!NOTE]
> **Vitalux befindet sich in aktiver Entwicklung.** Die Anwendung liest reale Linux-Systemdaten aus. Welche Temperaturen, Takte, Spannungen oder SMART-Informationen verfügbar sind, hängt von Hardware, Kernel, Treibern und Zugriffsrechten ab. Nicht unterstützte Messwerte werden nicht erfunden.

<p align="center">
  <img src="assets/vitalux-dashboard-preview.png" alt="Vitalux – Dashboard-Vorschau" width="1080">
</p>
<p align="center"><sub>Beispielansicht des Dashboards. Darstellung und Messwerte unterscheiden sich je nach System und Einstellungen.</sub></p>

## Vitalux auf einen Blick

Vitalux ist ein **nativer Linux-Systemmonitor** mit PySide6 für **Wayland und X11**, ohne Browser oder Webserver.

| Bereich | Was du findest |
| --- | --- |
| **Übersicht** | Live-Kacheln und Systemzustand auf Basis von Auslastung, Speicherbelegung und verfügbaren SMART-Befunden |
| **Hardware** | CPU, GPU, RAM, Laufwerke, Netzwerke, Sensoren, Kernel, Mesa und Treiberdaten |
| **Laufwerke** | SMART und einstellbare fio-Benchmarks mit MB/s, IOPS und Latenz |
| **Diagnostic Center** | Drei getrennte Kacheln: Systemanalyse, Einzelprüfungen und Diagnoseberichte |
| **Einstellungen** | Glass-Suche, Farbdesigns, Warnwerte, MiniHUD, Ultra Eco und Grafik-Backends |
| **Info** | Versionsdetails und bebilderte Anleitung, die beim allerersten Start automatisch geöffnet wird |

### Darstellung und Bedienung

**Standard: Glass mit Vitalux-Blau.** Weitere Farbschemata: Black Glass, Black Glass Gold, Holographic, Dark, Light und Minimalistisch. Es gibt integrierte Hintergründe, eigene Bilder, Akzentfarben sowie einstellbare Animationen. Black Glass Gold verwendet einen festen Goldakzent.

Die **Einstellungssuche** öffnet und schließt weich animiert, zeigt auch den vollständigen Platzhaltertext und erweitert sich für längere Eingaben. Die geschlossene Lupe bleibt am Anfang der Seite, die geöffnete Suche bleibt beim Scrollen sichtbar.

Das **MiniHUD** ist ein separat verschiebbares Qt-Fenster mit drei Größen, auswählbaren Messwerten und **50–100 % Deckkraft**. Einen garantierten Vordergrundmodus gibt es nicht: KDE/KWin und andere Wayland-Compositoren bestimmen die Fensterreihenfolge.

### Diagnostik und Sicherheit

Im **Diagnostic Center** sind die vollständige Systemanalyse, gezielte Einzelprüfungen und lokale TXT-/JSON-Berichte deutlich voneinander getrennt. Netzwerk-Ping und Blackbox-Aufzeichnung werden nur nach ausdrücklicher Aktivierung gestartet. Eine eigenständige Insights-Oberfläche und die überflüssige Tray-Live-Vorschau werden nicht mehr angeboten; die Systeminformationen bleiben über die Tray-Tooltip-Anzeige erreichbar.

SMART-Werte hängen von Geräten und Berechtigungen ab. **fio-Schreibbenchmarks** erzeugen temporäre Daten, beanspruchen Laufwerke und sollten nur bei ausreichend freiem Speicher und vorhandener Datensicherung genutzt werden.

### Grafik-Backends

In **Einstellungen → Grafik-Rendering** lassen sich **CPU (Standard)**, OpenGL (GPU-Test), Wayland/OpenGL, Wayland/Vulkan und X11/OpenGL auswählen. GPU-Modi sind experimentell und besitzen eine separate Startprüfung mit CPU-Rückfall. Ein Wechsel wird mit **Jetzt neu starten** übernommen. Ultra Eco reduziert die Oberfläche auf schlichte CPU-Darstellung und verlängert das Messintervall auf zehn Sekunden.

```bash
# Notfallstart der portablen ZIP mit CPU-Rendering
VITALUX_RENDERER=software ./run.sh
```

## Download

Die offiziellen Pakete erscheinen unter **[GitHub Releases](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest)**.

| Release-Datei | Verwendung |
| --- | --- |
| `Vitalux-vVERSION-x86_64.AppImage` | **Empfohlen:** direkt starten oder benutzerlokal installieren |
| `Vitalux-vVERSION-linux-x86_64.zip` | Vollständige portable Version zum Entpacken und Starten |
| `Vitalux-vVERSION-Update-von-vVORVERSION.zip` | Differenzupdate **nur** für die ausdrücklich angegebene Vorgängerversion, nicht für AppImages |
| `Vitalux-vVERSION-SHA256SUMS.txt` | SHA-256-Prüfsummen der Release-Pakete |

Die vollständigen offiziellen Pakete enthalten die benötigte **Python-/Qt-Laufzeit**. Für Grafiktreiber, systemnahe Bibliotheken und einige Hardwarezugriffe ist Vitalux weiterhin auf das Linux-Hostsystem angewiesen. Ein reiner Quellcode-Download des GitHub-Repositories ist **kein** vollständig gebündeltes, direkt startbares Programm.

## Installation

### AppImage · empfohlen

1. Aktuelles AppImage aus den [Releases](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest) herunterladen.
2. In KDE Dolphin unter **Eigenschaften → Berechtigungen** als ausführbar markieren.
3. Die Datei doppelt anklicken.
4. Im Erststartdialog **Jetzt installieren** für die Integration ins Anwendungsmenü oder **Nur einmal starten** für den portablen Aufruf wählen.

Für die benutzerlokale Installation sind normalerweise **keine Administratorrechte** erforderlich. Alternativ ist der Start über ein Terminal möglich:

```bash
chmod +x ./Vitalux-v*-x86_64.AppImage
./Vitalux-v*-x86_64.AppImage
# Alternativ direkt integrieren:
./Vitalux-v*-x86_64.AppImage --install
# Oder ausdrücklich portabel starten:
./Vitalux-v*-x86_64.AppImage --portable
```

### Portable ZIP

1. Die **vollständige** Linux-ZIP herunterladen und **komplett entpacken**.
2. Im entpackten Vitalux-Ordner **run.sh** starten.
3. Bei fehlender Ausführungsberechtigung im Terminal:

```bash
chmod +x run.sh
./run.sh
```

**Wichtig:** Der Ordner `runtime/` und seine Dateien müssen vollständig vorhanden sein. Fehlt `runtime/bin/python3.12`, wurde in der Regel kein vollständiges Release-Paket verwendet oder unvollständig entpackt. **Portable-pruefen.sh** hilft bei der Diagnose.

<details>
<summary><strong>Installations- und Datenpfade</strong></summary>

| Bestandteil | Typischer Pfad |
| --- | --- |
| Installiertes AppImage | `~/.local/opt/vitalux/Vitalux.AppImage` |
| Desktop-Eintrag | `~/.local/share/applications/vitalux.desktop` |
| Startbefehl | `~/.local/bin/vitalux` |
| App-Symbol | `~/.local/share/icons/hicolor/scalable/apps/vitalux.svg` |
| Benutzereinstellungen | `~/.config/vitalux/settings.json` |
| Lokale Protokolle | `~/.local/state/vitalux/` |

Abweichende XDG-Umgebungsvariablen können die Speicherorte beeinflussen.
</details>

## Updates

Vitalux prüft **beim Start und ungefähr alle sechs Stunden** die offiziellen GitHub-Releases. Im **Updates-Reiter** erscheinen Versionsstatus, Neuerungen und eine manuelle Suche. **Installiert wird erst nach „Jetzt aktualisieren“**; Downloads werden mit SHA-256 geprüft. Je nach Paket stehen Sicherungs- und Wiederherstellungsmechanismen bereit.

Der **deutsch/englische Changelog** ist offline verfügbar. Nur die Release-Prüfung benötigt Internet – die Hardwareüberwachung funktioniert lokal und offline.

Der manuell gestartete GitHub-Workflow erstellt **AppImage, Vollversion, Differenzupdate und Prüfsummen**. Eine README-Änderung veröffentlicht **keinen Release**.

## Hilfe und Fehlerbehebung

<details>
<summary><strong>AppImage startet nicht oder fehlt im Anwendungsmenü</strong></summary>

Prüfe zunächst die Ausführungsberechtigung in Dolphin. Starte das AppImage testweise im Terminal, um Fehlermeldungen zu sehen. Mit `--install` kann die Menüintegration nachgeholt werden. Manche Distributionen benötigen geeignete **FUSE-Unterstützung**.
</details>

<details>
<summary><strong>Portable Version meldet eine fehlende Python-Laufzeit</strong></summary>

Verwende die **Linux-Vollversion aus GitHub Releases**, nicht die automatisch angebotene GitHub-Quellcode-ZIP. Entpacke das gesamte Archiv ohne Dateien oder Ordner auszulassen. Prüfe insbesondere `runtime/bin/python3.12`. Bei Bedarf `./Portable-pruefen.sh` ausführen.
</details>

<details>
<summary><strong>Rendering-Probleme oder Abstürze</strong></summary>

Nach problematischen OpenGL-/Qt-Quick-Starts versucht Vitalux die CPU-Ausgabe wiederherzustellen. Für die portable Version lässt sich das Software-Rendering auch direkt erzwingen:

```bash
VITALUX_RENDERER=software ./run.sh
```

Falls ein Grafiktreiber oder eine Bibliothek fehlt, helfen die lokalen Logs bei der Eingrenzung.
</details>

<details>
<summary><strong>Fehlerprotokolle und Diagnose</strong></summary>

Im Verzeichnis `~/.local/state/vitalux/` werden – je nach Vorgang – die folgenden Dateien angelegt:

| Datei | Inhalt |
| --- | --- |
| `vitalux.log` | Programmstart, Laufzeitmeldungen und Rückkehr nach einem Absturz |
| `errors.log` | Python-Ausnahmen und native Fehlerdiagnose |
| `installation.log` | Installations- und Integrationsvorgänge, sofern angelegt |
| `restart.log` | Neustart-/Update-Vorgänge, sofern angelegt |

Die Protokollierung kennzeichnet Ereignisse mit **Zeitstempeln, Zeitzonen- und Versionsinformationen**; rohe native Stackframes können zwischen solchen Markierungen stehen. Logs werden nicht automatisch hochgeladen. Diagnoseexporte bitte vor dem Teilen auf private Rechner- und Benutzerdaten prüfen.
</details>

<details>
<summary><strong>Sensor-, SMART- oder Benchmarkdaten fehlen</strong></summary>

Prüfe Hardwareunterstützung, Kernel/Grafiktreiber, Laufwerkscontroller und Berechtigungen. Für Benchmarks müssen das Ziel beschreibbar, genügend Speicher frei und die mitgelieferte fio-Engine verfügbar sein. Die portable Version kann mit `Portable-pruefen.sh` untersucht werden.
</details>

<details>
<summary><strong>Updateprüfung schlägt fehl</strong></summary>

Prüfe Internetverbindung, DNS, Systemzeit und die installierten CA-Zertifikate. Vitalux verwendet die offizielle GitHub-Releasequelle und verifiziert Downloads; unsichere Zertifikatsumgehungen sind nicht erforderlich.
</details>

<details>
<summary><strong>Release-Paket mit SHA-256 überprüfen</strong></summary>

Lade die Prüfsummendatei aus **demselben Release** und führe im Downloadordner aus:

```bash
sha256sum --ignore-missing -c Vitalux-v*-SHA256SUMS.txt
```
</details>

Fehlerberichte und Verbesserungsvorschläge können unter **[GitHub Issues](https://github.com/PAAAUUULLOOOH/Vitalux/issues)** eingereicht werden. Hilfreich sind Vitalux-Version, Distribution, Kernel, Desktop-Sitzung und eine Beschreibung der Schritte – **ohne sensible Systemdaten öffentlich zu posten**.

## Deinstallation

Nach einer benutzerlokalen AppImage-Installation:

```bash
~/.local/opt/vitalux/Vitalux.AppImage --uninstall
```

Der Desktop-Eintrag und die installierte Anwendung werden entfernt. **Persönliche Einstellungen bleiben erhalten.** Eine nur heruntergeladene, nicht integrierte AppImage-Datei kann einfach gelöscht werden; die portable ZIP-Version wird durch Entfernen ihres entpackten Ordners beseitigt.

## Systemanforderungen und Datenschutz

- **Linux x86-64**, Wayland oder X11; ausgelegt besonders für **KDE Plasma**. Ziel: aktuelle Distributionen mit **glibc 2.38+**; FUSE und weitere Systembibliotheken können erforderlich sein.
- **Vollständige Release-Pakete** enthalten Python und Qt; Sensorfunktionen erfordern passende Treiber und Berechtigungen.
- **Offline und lokal:** Monitoring und Anleitung benötigen keine Cloud. Gaming-Aufzeichnungen werden erst auf Wunsch exportiert; Vergleichssnapshots können lokal gespeichert werden. MangoHud-Dateien werden ausschließlich manuell ausgewählt.
- **Nur Überwachung:** Keine GPU-Übertaktung oder eigene Lüftersteuerung.

## Projekt, Mitwirkende und Lizenzen

**Entwicklung:** [PAAAUUULLOOOH](https://github.com/PAAAUUULLOOOH) · **Vitalux**

**Besonderer Dank an [TimBooH](https://github.com/TimBooH)** für die Unterstützung bei der Integration eigener Hintergrundbilder und der Grafikausgabe (OpenGL/CPU-Rendering).

Vitalux verwendet unter anderem **Python**, **Qt/PySide6**, **psutil**, **fio** und **libaio**. Lizenzinformationen zu mitgelieferten Drittkomponenten befinden sich in den offiziellen Paketen unter `licenses/`. Für den Vitalux-eigenen Projektcode liegt derzeit keine allgemeine Lizenzdatei im Repository vor; öffentliche Einsicht allein bedeutet daher keine allgemeine Nutzungserlaubnis.

---

<p align="center"><strong>Vitalux · Dein Linux-System im Blick.</strong></p>
