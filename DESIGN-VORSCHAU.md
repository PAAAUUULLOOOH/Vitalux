# Vitalux – lokale Glas- und Gold-Designs

Auf Basis von Vitalux **0.9.5.4**, im Branch **experimental/glass-gold-preview**.
Die vollständige Linux-x86-64-Test-ZIP enthält die Python-/Qt-Laufzeit der
offiziellen Version. Das ist eine Designvorschau, kein offizieller Release.

## Download auf GitHub

Der Workflow **Vitalux – Experimentelle Designvorschau** erstellt bei einem Push
auf diesen Branch nach bestandenen Tests ein herunterladbares Artifact namens
**Vitalux-v0.9.5.4-Designvorschau-linux-x86_64**. Der Build-Bericht enthält den
Download-Link. Für GitHub-Actions-Downloads ist eine GitHub-Anmeldung erforderlich.
Das Artifact enthält die vollständige Test-ZIP, Prüfsumme und Bildschirmaufnahmen.

**Code → Download ZIP funktioniert ebenfalls:** Dieser experimentelle Branch
enthält Python 3.12, Qt und die benötigten Bibliotheken als komprimiertes Paket
unter **portable-runtime/**. `run.sh` und `Designs-testen.sh` entpacken es beim
ersten Start automatisch. Dafür sind weder ein Download noch installiertes
Python oder pip nötig. Das Entpacken benötigt etwa 250 MB zusätzlichen Platz.

## Start

Das ZIP vollständig in einen **eigenen, beschreibbaren Ordner** entpacken.
Die installierte Version nicht überschreiben. Im entpackten Ordner starten:

```bash
bash run.sh
```

Oder ein Design direkt auswählen:

```bash
bash Obsidian-Gold.sh
bash Champagne-Glass.sh
bash Aurora-Gold.sh
```

In **Einstellungen → Erscheinungsbild** werden alle zehn Farbschemata als
anklickbare Vorschaukacheln angezeigt. Das Farbschema-Dropdown entfällt.
Ein Wechsel wirkt sofort auf die laufende Oberfläche.

**Obsidian Gold, Champagne Glass, Black Glass Gold und Aurora Gold** verwenden
feste Akzentpaletten und eigene Hintergründe. Die gesperrten Auswahlfelder
sind grau und werden direkt erklärt. Holographic verwendet ebenfalls seinen
festen HUD-Hintergrund. Persönliche Farben und Hintergründe bleiben für die
anderen Designs gespeichert und werden beim Wechsel dorthin wieder verwendet.

- **Obsidian Gold:** tiefes Rauchglas, polierte Goldkanten und dunkle Linsen.
- **Champagne Glass:** helleres Kristallglas, warme Metalle und seidige Reflexe.
- **Aurora Gold:** Petrol-/Violettlicht, irisierendes Glas und goldene Konturen.

Die äußeren Originalstreifen des Vitalux-Logos rotieren langsam im Uhrzeigersinn
(eine Umdrehung in 48 Sekunden). Pulssymbol und innere Linse bleiben stehen.
Unter **Animationen** lässt sich die Bewegung reduzieren oder abschalten.
Minimalistisch und Ultra Eco stoppen die dekorative Logo-Animation.
Auch die drei neuen Themes verwenden den originalen Vitalux-Vektorschriftzug.
Ein dezenter Lichtreflex läuft über seine Buchstaben. Logos und Icons folgen
der wirksamen Palette, einschließlich eigener Farben und Distributionsfarben.

**Glas-Klang bei Klicks** aktiviert einen kurzen, lokal erzeugten Glasklang.
Er lässt sich in den Einstellungen abschalten. Die Ausgabe verwendet den
PulseAudio-kompatiblen Desktop-Audioserver (auch PipeWire); Audioarbeit läuft
außerhalb des GUI-Threads. Es werden keine externen Samples geladen.

Die Einstellungssuche blendet weich ein, passt ihre Breite an den Suchtext und
die Fensterbreite an und schließt nach fünf Sekunden ohne Eingabe animiert.
Reduzierte oder abgeschaltete Animationen werden berücksichtigt.

## Getrennte Einstellungen

Der Vorschau-Starter speichert Einstellungen, eigene Hintergründe und Logs nur
im Unterordner **design-test-data/** neben der Testanwendung. Die Einstellungen
der normal installierten Version bleiben erhalten. Lösche diesen Unterordner
bei geschlossener Testanwendung, um die Vorschau zurückzusetzen.

Die automatische Release-Prüfung und Updateinstallation sind im Vorschau-Modus
deaktiviert, damit ein Update die lokalen Designs nicht überschreibt. Im
experimentellen Branch führt auch run.sh zum getrennten Vorschau-Starter.

## Voraussetzungen und Umfang

Linux x86-64 mit einer Wayland- oder X11-Sitzung und passenden Grafikbibliotheken.
Die Laufzeit stammt aus dem offiziellen Vitalux-Paket und hat dieselben
grundsätzlichen Host-Anforderungen (siehe README.md). Kein Python-/pip-Download
beim Start erforderlich. Die neuen Glasmaterialien funktionieren im CPU-Modus;
ein experimentelles GPU-Backend ist nicht nötig.

Die Anwendung zeigt reale Messwerte. In virtuellen Umgebungen können GPU-,
SMART- und Temperatursensoren fehlen. Durch die neuen Designs werden keine
Messwerte erfunden und keine Hardware-Stresstests automatisch gestartet.

Zum Testen sind native Qt-Aufnahmen der drei Oberflächen unter **Vorschauen/**
beigefügt. Sie zeigen den Cloud-Testrechner, nicht deinen Rechner.

Der experimentelle Branch ändert den offiziellen main-Branch nicht und erstellt
keine GitHub-Releases. Die Testpakete sind 14 Tage als Actions-Artifacts verfügbar.
Ein neuer Push baut die aktuelle Vorschau erneut.

## Grafik-Startprüfung

CPU, OpenGL, X11/OpenGL, Wayland/OpenGL und Wayland/Vulkan wurden mit echten
Fenstern, Framebuffern und Live-Messwerten unter Xvfb/Weston und Mesa geprüft.
Unter X11 wird nur das vollständige Hauptfenster eingeblendet. Der vorzeitig
als eigenes Fenster sichtbare Reset-Button und der GPU-Starttest sind korrigiert.
Die wiederholbare Prüfung steht in `scripts/check-graphics-startup.py`;
sie benötigt erreichbare X11- und Wayland-Testdisplays. Das prüft keine
physische GPU oder die individuellen Treiber eines anderen Rechners.
