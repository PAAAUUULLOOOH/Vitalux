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

Vitalux vereint Systemüberwachung, Live-Diagramme, Datenträgeranalyse und eine anpassbare Oberfläche in einer **eigenständigen Linux-Desktopanwendung mit Qt/PySide6**. Die Benutzeroberfläche läuft nativ unter **Wayland und X11**; ein Browser oder Webserver ist nicht erforderlich.

| Bereich | Funktionsumfang |
| --- | --- |
| **Übersicht** | Live-Dashboard, Systemzustand, CPU-/GPU-/RAM-Auslastung, Laufwerke, Netzwerk und Systemlaufzeit |
| **Prozessor** | Kerne, Threads, aktuelle Auslastung und Taktraten, verfügbare Temperaturen und Verläufe |
| **Grafik** | GPU-/VRAM-Telemetrie, Taktraten, Sensoren, PCIe-/Treiberinformationen und Vitalux Insights |
| **Arbeitsspeicher** | Auslastung, belegter und verfügbarer Speicher sowie zeitlicher Verlauf |
| **Netzwerk** | Schnittstellen, IP-Adressen, aktuelle Up-/Downloadraten und Datenverkehr |
| **Laufwerke** | Datenträger, Partitionen, Belegung, SMART-Diagnose und fio-Benchmarks |
| **Sensoren** | Verfügbare Temperaturen, Lüfterdrehzahlen, Spannungen, Leistungsaufnahme und Frequenzen |
| **System** | Distribution, Kernel, Desktop-/Sitzungsinformationen, Mesa, Treiber und Hardwaredetails |
| **Einstellungen** | Farbschemata, Akzentfarben, Hintergründe, Animationen, Rendering, Warnungen und Datenexport |
| **Updates** | Offizielle GitHub-Releases prüfen, Neuerungen anzeigen und Aktualisierungen bestätigen |
| **Info** | Versionsinformationen, Mitwirkende und integrierte, bebilderte Anleitung |

### Dashboard und Live-Anzeigen

Das Dashboard vereint Systemzustand, CPU-, GPU-, RAM- und Laufwerksauslastung, Netzwerkverkehr, Live-Diagramme und Systemlaufzeit.

- **Layout bearbeiten:** Kacheln verschieben, ein- oder ausblenden; Änderungen speichern, verwerfen oder zurücksetzen. Größere Lücken werden bei unverändertem **14-px-Kachelabstand** aufgefüllt.
- **Systemzustand:** Messwertbasierte Statusbewertung mit Hinweisen – keine umfassende Hardwarediagnose.
- **Systemdetails:** Distribution, Kernel, KDE, Mesa, Treiber, Architektur und Sitzung.
- **Bedienung:** Einklappbare linke Navigation, anpassbares Abfrageintervall (Standard: eine Sekunde) und Unterstützung unterschiedlicher Fenstergrößen und Skalierungen.

### CPU, GPU und Systemdiagnose

**CPU:** Auslastung, Kerne und Threads, Taktraten, verfügbare Temperaturen, Verlaufsdiagramme sowie Min-/Max-Werte der laufenden Sitzung.

**GPU:** Auslastung, VRAM, Taktraten, Temperatur/Hotspot, Spannung, Leistung, Lüfter, PCIe, Mesa, Treiber und Sensorquelle – jeweils soweit verfügbar.

**Sensoren:** Eigener Reiter für auslesbare Temperaturen, Lüfterdrehzahlen, Spannungen, Leistung und Frequenzen.

**Diagnose:** Systemberichte als **TXT/JSON**, Fehlerdiagnosen als **JSON** unter **Einstellungen → Diagnose & Berichte**. Exporte erfolgen nur auf ausdrücklichen Wunsch und können private Systemdaten enthalten.

### Vitalux Insights

Im Reiter **Grafik** stehen zusätzlich ausklappbare Analysewerkzeuge zur Verfügung:

| Werkzeug | Beschreibung |
| --- | --- |
| **Performance Detective** | Messwertbasierte Hinweise auf auffällige Auslastungen und mögliche Engpässe; unterscheidet Beobachtungen von Vermutungen |
| **Performance-Verlauf** | Gemeinsame grafische Betrachtung von CPU-, GPU- und VRAM-Auslastung |
| **Gaming Session Analyzer** | Gaming-Sitzungen manuell aufzeichnen, auswerten und bei Bedarf als JSON speichern |
| **MangoHud-Import** | Lokal ausgewählte CSV-Dateien einlesen und enthaltene FPS-Daten auswerten; ungefähre 1%-Lows nur aus geeigneten Daten |
| **Vorher-/Nachher-Vergleich** | Zwei Messzeitpunkte speichern und deren vorhandene Werte gegenüberstellen |
| **Ereignis-Timeline** | Aufgezeichnete Ereignisse mit zugehörigen Telemetriedaten nachvollziehen |
| **Interaktive Hardware-Übersicht** | Schematische Komponentenansicht mit anklickbaren Hardwareinformationen |
| **Fokusmodus** | Eigenständiges, verschiebbares Live-Fenster, beispielsweise für einen zweiten Monitor; Messgrößen auswählbar |

> [!IMPORTANT]
> Vitalux Insights ist eine **experimentelle, lesende Analysefunktion**. Einzelschnappschüsse sind kein reproduzierbarer Benchmark. FPS und 1%-Lows werden nicht aus gewöhnlicher GPU-Auslastung errechnet. **Vitalux nimmt keine GPU-Übertaktung vor und steuert keine eigenen Lüfterkurven.**

## Laufwerke, SMART und Benchmarks

Der Reiter **Laufwerke** zeigt Datenträger, Partitionen, Dateisysteme, Kapazitäten und verfügbare SMART-Werte. Beim ersten Öffnen wird eine SMART-Prüfung im Hintergrund angestoßen; sie kann manuell wiederholt werden.

Der integrierte **fio-Benchmark** bietet **Standard-, Peak-, Real-World- und benutzerdefinierte Tests** mit sequenziellen bzw. zufälligen Zugriffen. Testgröße, Durchläufe, Messdauer, Blockgröße, Queue Depth und Threads sind einstellbar. Die Auswertung zeigt **MB/s, IOPS und Latenz**, soweit vom Test geliefert.

> [!CAUTION]
> **Schreibbenchmarks belasten den Datenträger und erzeugen temporäre Testdateien.** Vitalux schreibt nicht direkt auf bestehende Dateien oder rohe Blockgeräte. Vor dem Start Laufwerk, freien Speicherplatz und Datensicherung prüfen.

## Design und Personalisierung

**Standarddesign: Glass mit Vitalux Blau.** Vitalux bietet sieben eigenständige Farbschemata:

| Farbschema | Charakter |
| --- | --- |
| **Glass** · Standard | Halbtransparente Glasflächen, weiche Hintergrundunschärfe und Reflexionen |
| **Black Glass** | Tiefschwarze Glasoptik mit zurückhaltenden Licht- und Kanteneffekten |
| **Black Glass Gold** | Schwarzes Premiumdesign mit **festem hellgoldenem Akzent** für Logo, Symbole, Anzeigen und Diagramme |
| **Holographic** | Technisches, vollständig deckendes HUD-Design mit leuchtenden Konturen – **kein Glasmodus** |
| **Dark** | Kontrastreiche dunkle Oberflächen ohne Glasunschärfe |
| **Light** | Helle Oberfläche mit gut lesbaren Karten und Bedienelementen |
| **Minimalistisch** | Reduzierte Darstellung mit geringeren dekorativen Effekten |

In **Black Glass Gold** sind die Auswahl und Bearbeitung von Akzentfarben bewusst deaktiviert. Für alle anderen Farbschemata stehen die regulären Akzentoptionen zur Verfügung.

### Hintergründe, Farben und Animationen

- **14 integrierte Hintergründe:** darunter Glass, Black Glass, Morgenlicht, Prisma, Tiefsee, Mitternacht, Samt, Graphit und Adaptiv. Nur **Funkeln** ist animiert.
- **Eigene Bilder:** PNG, JPEG, WebP und BMP; Füllen, Einpassen, Strecken, Zentrieren oder Kacheln.
- **Akzente:** Acht geschützte Standardfarben, Distributionsfarbe und eigene, bearbeitbare/löschbare Farben. **Hintergrundfarbe automatisch** funktioniert nur bei ausgewähltem eigenen Bild.
- **Animationen:** Flüssig, Reduziert oder Aus.

**Black Glass Gold** verwendet ausschließlich seinen festen Goldakzent; dessen Farbauswahl ist deaktiviert. Eigene Bilder und Akzente ermöglichen zahlreiche weitere Designs, aber nicht jede theoretische Kombination ist gleichzeitig wählbar.

### Grafik-Rendering

Unter **Einstellungen → Grafik-Rendering** stehen drei Varianten bereit:

| Render-Methode | Einsatz |
| --- | --- |
| **CPU · Standard** | Voreingestellte, auf Stabilität ausgerichtete Grafikausgabe |
| **OpenGL · GPU-Test** | Experimentelle GPU-Unterstützung für Hintergrund und grafische Komposition |
| **Qt Quick · GPU-Test** | Experimenteller Hintergrund über den Qt-Quick-Scene-Graph |

Ein Wechsel wird mit **Jetzt neu starten** übernommen. Die Qt-Widgets, Bedienelemente und Diagramme werden dadurch **nicht automatisch vollständig auf GPU-Rendering umgestellt**. Die experimentellen Modi sind nicht auf jeder Hardware schneller.

**Wiederherstellung:** Ein fehlgeschlagener oder inkompatibler GPU-Start kann auf das CPU-Rendering zurückgesetzt werden. Für einen erzwungenen Softwarestart der entpackten ZIP-Version:

```bash
VITALUX_RENDERER=software ./run.sh
```

## Warnungen, Systemleiste und Bedienung

- **Hardware-Warnungen:** Individuelle Grenzwerte für CPU-/GPU-Temperatur, RAM und Systemlaufwerk. Neue Meldungen erst nach zwischenzeitlicher Entwarnung.
- **Systemleiste:** Weiterlaufen beim Schließen, Tooltip und kompakte Live-Vorschau. Updates können durch pulsierendes Logo, hervorgehobenen Reiter und Benachrichtigung angezeigt werden.
- **Sprachen:** **Deutsch / Englisch** ohne Neustart, einschließlich lokalisiertem Changelog.
- **Anleitung:** Unter **Info → Anleitung öffnen** steht eine bebilderte, neunteilige Einführung bereit; beim Erststart optional.

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
