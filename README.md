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

Die Startseite bündelt die wichtigsten Messwerte in einem individuell anpassbaren Dashboard:

- **Frei anordenbare Kacheln:** Im Modus **Layout bearbeiten** Kacheln verschieben, ausblenden oder wieder hinzufügen; Änderungen speichern, verwerfen oder zurücksetzen.
- **Intelligente Flächennutzung:** Größere freie Bereiche werden beim Anordnen möglichst geschlossen, während der gewohnte **14-px-Abstand** zwischen den Kacheln erhalten bleibt. Die vorhandenen Kachelformate bleiben grundsätzlich bestehen.
- **Systemzustand:** Eine kompakte, aus verfügbaren Messwerten abgeleitete Statusbewertung mit Hinweisen. **Kein Ersatz für eine Hardwarediagnose.**
- **Live-Diagramme:** Auslastung und Netzwerkaktivität direkt auf der Übersicht; weitere Verläufe in den jeweiligen Hardware-Reitern.
- **Systeminformationen:** Distribution, Kernel, KDE, Mesa, Architektur, Grafiktreiber, Sitzung, Distributionsversion und **Systemlaufzeit**.
- **Anpassbare Navigation:** Die Seitenleiste bleibt links, kann platzsparend eingeklappt werden und bietet einen direkten Sprachwechsel.

Die Anzeige aktualisiert sich standardmäßig im Sekundentakt. Das Abfrageintervall lässt sich in den Einstellungen ändern. Die Oberfläche berücksichtigt unterschiedliche Fenstergrößen und KDE-Skalierungen.

### CPU, GPU und Systemdiagnose

**CPU:** Gesamtauslastung, vorhandene Kern-/Thread- und Taktinformationen sowie CPU-Temperaturen, soweit vom System bereitgestellt. Verfügbare Min-/Max-Messwerte werden für die laufende Sitzung erfasst.

**GPU:** Auslastung, VRAM-Belegung, aktuelle Taktraten, Temperaturen einschließlich Hotspot sowie – wenn vom Treiber geliefert – Spannung, Leistungsaufnahme und Lüfterwerte. Ergänzende Angaben umfassen unter anderem Grafiktreiber, Mesa, PCIe-Verbindung und Sensorquelle. Verlaufskurven helfen, Laständerungen einzuordnen.

**Sensoren:** Ein eigener Reiter fasst Messwerte aus Linux-Schnittstellen wie hwmon zusammen. Kategorien ohne auslesbare Werte bleiben verborgen; fehlende Kennzahlen werden als nicht verfügbar gekennzeichnet.

**Berichte:** Über **Einstellungen → Diagnose & Berichte** lassen sich Systemberichte als **TXT oder JSON** sowie separate Fehlerdiagnosen als JSON exportieren. Die Berichte können Hardwaredetails und persönliche Systeminformationen enthalten und werden **nur auf ausdrücklichen Wunsch lokal gespeichert**.

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

Unter **Laufwerke** werden erkannte Speichergeräte, Partitionen, Dateisysteme und Kapazitäten angezeigt. Beim ersten Öffnen startet die verfügbare **SMART-Prüfung im Hintergrund**; eine manuelle Wiederholung ist möglich. Welche Gesundheitsdaten erscheinen, hängt vom Laufwerk, Controller und den erforderlichen Berechtigungen ab.

Der integrierte **fio-Benchmark** bietet unter anderem:

- **Standard-, Peak- und Real-World-Profile** sowie anpassbare Testmuster.
- Einstellungen für sequenzielle und zufällige Zugriffe, Blockgröße, Queue Depth und Threads.
- Wählbare Testgröße, Durchläufe und Messzeit sowie auf die Geräteklasse abgestimmte Vorgaben.
- Ergebnisse für **MB/s**, **IOPS** und **Latenz**, soweit der jeweilige Test sie liefert.

> [!CAUTION]
> **Benchmarks belasten Datenträger und können vorübergehend Daten schreiben.** Vitalux verwendet temporäre Testdateien, keinen direkten Schreibtest auf bestehende Dateien oder rohe Blockgeräte. Wähle das Ziel sorgfältig aus, achte auf freien Speicherplatz und sichere wichtige Daten vor intensiven Schreibtests.

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

- **14 integrierte Hintergrundoptionen:** vom farbschemaabhängigen Standard über Glass, Black Glass, Dark und Light bis zu Morgenlicht, Prisma, Tiefsee, Mitternacht, Samt, Graphit und einem adaptiven Hintergrund.
- **Funkeln** ist der einzige verbliebene **animierte Hintergrund**; die übrigen integrierten Hintergründe sind statisch.
- **Eigene Bilder:** PNG, JPEG, WebP und BMP importieren, auswählen und wieder entfernen. Unterstützte Ausrichtungen sind **Bildschirmfüllend, Einpassen, Strecken, Zentrieren und Kacheln**.
- **Akzentfarben:** **acht feste Vitalux-Farben** (Blau, Cyan, Violett, Grün, Orange, Gelb, Rot und Rosa), die Farbe der Linux-Distribution sowie individuell benannte Farben. Eigene Farben lassen sich erstellen, bearbeiten und löschen; Standardfarben bleiben geschützt.
- **Hintergrundfarbe automatisch:** Die Akzentfarbe kann aus dem **ausgewählten eigenen Hintergrundbild** abgeleitet werden. Ohne eigenes Bild ist diese Option nicht verfügbar; beim Verlassen der Funktion wird die vorherige Akzentwahl berücksichtigt.
- **Bewegung:** **Flüssig**, **Reduziert** oder **Aus** für Übergänge und dekorative Animationen.

Die Farb- und Hintergrundauswahl eröffnet zahlreiche Kombinationen. Da **Black Glass Gold** einen festen Akzent verwendet und die automatische Bildfarbe ein eigenes Hintergrundbild voraussetzt, ist nicht jede mathematisch denkbare Auswahl tatsächlich kombinierbar. Eigene Farben und Bilder erweitern die Möglichkeiten zusätzlich.

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

- **Hardware-Warnungen:** Konfigurierbare Grenzwerte für CPU- und GPU-Temperatur, RAM-Auslastung und Belegung des Systemlaufwerks. Wiederholte Meldungen erfolgen erst nach zwischenzeitlicher Entwarnung.
- **Systemleiste (Tray):** Vitalux kann beim Schließen im Hintergrund weiterlaufen. Tooltip und optionale kompakte Live-Vorschau zeigen verfügbare Hardwarewerte.
- **Update-Hinweise:** Bei einer neuen Vitalux-Version können das App-Logo und das Tray-Symbol leuchten bzw. pulsieren, der Updates-Reiter wird hervorgehoben und eine Systembenachrichtigung angezeigt.
- **DE / EN:** Deutsch und Englisch lassen sich **ohne Neustart** wechseln. Der lokale Changelog folgt der gewählten Sprache.
- **Integrierte Anleitung:** Über **Info → Anleitung öffnen** startet eine bebilderte, neunteilige Einführung zu Navigation, Monitoring, Benchmarks, Einstellungen und Updates. Beim Erststart wird sie optional angeboten.

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

Vitalux sucht **beim Start und ungefähr alle sechs Stunden** nach offiziellen Veröffentlichungen auf GitHub. Im **Updates-Reiter** lassen sich die installierte Version, eine verfügbare neue Version und deren Neuerungen einsehen. Die Suche kann manuell wiederholt werden.

**Ein Update wird nicht ungefragt installiert:** Erst **Jetzt aktualisieren** startet die Aktualisierung. Downloads werden über **SHA-256** geprüft. Die Anwendung unterstützt – abhängig vom verwendeten Paket – den Austausch des AppImages beziehungsweise die Aktualisierung der portablen Version mit Sicherungs- und Wiederherstellungsmechanismen.

Der **lokale Changelog** bleibt auch ohne Internet einsehbar und zeigt die Einträge in der aktuell ausgewählten Sprache. Die automatische Versionsprüfung benötigt eine Verbindung zu GitHub; die eigentliche Hardwareüberwachung funktioniert offline.

Für Veröffentlichungen erstellt der manuell angestoßene GitHub-Workflow **AppImage, Vollversion, passendes Differenzupdate und Prüfsummen**. Ein normaler README- oder Code-Commit veröffentlicht **keine neue Version**.

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

- **Betriebssystem:** Aktuelle **GNU/Linux-x86-64**-Distribution; **Wayland oder X11**.
- **Kompatibilität:** Derzeitiges Ziel sind moderne Systeme mit **glibc 2.38 oder neuer**; weitere Laufzeitbibliotheken und Grafikunterstützung hängen von der Distribution ab.
- **Desktop:** Besonders auf KDE Plasma ausgelegt, ohne auf KDE beschränkt zu sein.
- **Pakete:** Offizielle Vollversionen bündeln Python/Qt; AppImages benötigen abhängig von der Distribution FUSE.
- **Offline-Nutzung:** Hardwaremonitoring, lokale Verläufe und die integrierte Anleitung benötigen keinen Cloud-Dienst.
- **Datenschutz:** Messwerte werden lokal verarbeitet. Gaming-Sitzungen bleiben bis zum ausdrücklichen Export im Arbeitsspeicher; Vergleichs-Snapshots können in der Benutzerkonfiguration liegen. MangoHud-Dateien werden nur nach manueller Auswahl eingelesen.
- **Keine Fernsteuerung:** Vitalux ist ein Monitor- und Analysewerkzeug, kein Übertaktungs- oder Lüftersteuerungsdienst.

## Projekt, Mitwirkende und Lizenzen

**Entwicklung:** [PAAAUUULLOOOH](https://github.com/PAAAUUULLOOOH) · **Vitalux**

**Besonderer Dank an [TimBooH](https://github.com/TimBooH)** für die Unterstützung bei der Integration eigener Hintergrundbilder und der Grafikausgabe (OpenGL/CPU-Rendering). Der Hinweis ist auch im Info-Reiter der App zu finden.

Vitalux verwendet unter anderem **Python**, **Qt/PySide6**, **psutil**, **fio** und **libaio**. Lizenzinformationen zu mitgelieferten Drittkomponenten befinden sich in den offiziellen Paketen unter `licenses/`. Für den Vitalux-eigenen Projektcode liegt derzeit keine allgemeine Lizenzdatei im Repository vor; öffentliche Einsicht allein bedeutet daher keine allgemeine Nutzungserlaubnis.

---

<p align="center"><strong>Vitalux · Dein Linux-System im Blick.</strong></p>
