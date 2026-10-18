# Vitalux – Änderungen

## [v0.9.4.6] - 2026-10-18
- Ultra Eco als Ein-/Aus-Schalter unter „Leistung & Energie“ ergänzt: besonders primitiver, flacher Skin ohne Glas, Schatten, Hintergrundbilder und Animationen.
- CPU-Rendering statt GPU, 5 Sekunden Abfrageintervall und reduzierte Zeichenarbeit im Ultra-Eco-Modus.
- Nach dem Ausschalten kehren das zuvor gewählte Design, die Farben, Hintergründe, Animationen, das Messintervall und der gespeicherte Renderer zurück.
- Kompakte README, integrierte Anleitung sowie deutsche und englische Texte angepasst.


## [v0.9.4.5] - 2026-10-18
- Qt Raster als sparsamen CPU-Render-Modus ergänzt: statische Hintergründe bleiben zwischengespeichert; die optionale Funkeln-Animation zeichnet seltener neu.
- Eigenständigen Qt-Quick-Modus aus der Auswahl entfernt. Die experimentellen Wayland-/X11-GPU-Modi bleiben erhalten.
- Im Farbschema Black Glass sind eigene Akzentfarben und deren Aktionen ausgegraut; Standardfarben und gespeicherte eigene Farben bleiben erhalten.
- Kompakte README, integrierte Anleitung und englische Übersetzungen aktualisiert.


## [v0.9.4.4] - 2026-10-18
- Endlosschleife bei „Neustart vorgemerkt“ für Wayland-OpenGL, Wayland-Vulkan und X11-OpenGL behoben: Vitalux erkennt nun das tatsächlich aktive Rendering-Profil.
- Qt-Quick-Kompatibilitätstest öffnet kein sichtbares kleines Testfenster mehr.
- Ursache eines GPU-Fallbacks und der aktive Fenster-/Grafikmodus werden im Vitalux-Log ausgegeben.
- Systemleisten-Vorschau verwendet ein vereinfachtes Qt-Stylesheet.


## [v0.9.4.3] - 2026-10-18
- Experimentelle Grafik-Backends für Wayland mit OpenGL oder Vulkan sowie X11 mit OpenGL ergänzt.
- Qt-Quick-Teststart prüft jetzt das tatsächliche OpenGL-/Vulkan-Scene-Graph-Rendering isoliert vor dem App-Start.
- Sichere Rückkehr zum CPU-Modus bei inkompatiblen Backends oder nativen Grafikabstürzen verbessert.
- Auswahl, englische Übersetzungen und Anleitung für schnellen Wechsel per Neustart erweitert.

## [v0.9.4.2] - 2026-10-18
- Dashboard-Kacheln füllen freie Bereiche zuverlässiger aus, ohne den gewohnten Abstand zu verändern.
- Qt Quick wird vor der Aktivierung auf Grafikkompatibilität geprüft; nach Grafikabstürzen kehrt Vitalux automatisch zum CPU-Rendering zurück.
- Der Entwicklername im Info-Reiter ist jetzt anklickbar und führt zum GitHub-Profil.

## [v0.9.4.1] - 2026-10-18
- Hintergrundbasierte Akzentfarbe ist nur bei ausgewähltem eigenen Bild verfügbar, sonst ausgegraut.
- Beim Wechsel des Hintergrunds wird die vorherige Akzentfarbe wiederhergestellt.
- Systemzustand-Kachel mit Score und Hinweisen ergänzt; Farbschemata und Oberfläche vereinheitlicht.

## [v0.9.4.0] - 2026-10-18
- Black Glass Gold mit festem Goldakzent sowie separates Holographic-HUD hinzugefügt.
- Dashboard, Diagramme, Akzentfarben und Monitoring verbessert.
