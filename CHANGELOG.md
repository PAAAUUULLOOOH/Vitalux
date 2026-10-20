# Vitalux – Änderungen

## [v0.9.5.8] - 2026-10-20
- Die Übersicht verwendet immer den kompakten Systemkopf mit kleinerem Distributionslogo und engeren Abständen. Dadurch bleibt mehr Platz für Messwerte und Diagramme; der bisherige Kompakt-Schalter entfällt, auch bestehende Installationen erhalten die kompakte Ansicht.

## [v0.9.5.7] - 2026-10-20
- Obsidian Gold ist der Standard für neue Installationen und das Zurücksetzen der Darstellung, mit feineren Glaskanten, weicheren Reflexionen und klareren Messwerten; gespeicherte Designauswahlen bleiben erhalten.
- Die originale Linie in der Logomitte erhält einen sanften Herzschlagimpuls, während sich die äußeren Streifen weiterhin langsam drehen.
- Eine kompakte Farbprobe mit Glaskante neben der Akzentfarbenauswahl ersetzt den langgezogenen Farbbalken.
- Zurücksetzen-Buttons erscheinen und verschwinden weich. Die vollständige Rücksetzung steht ganz unten und startet Vitalux sicher neu; einzelne Bereiche lösen keinen Neustart aus.
- Die Seite folgt beim Aufklappen der erweiterten Einstellungen. Erneut geöffnete Kategorien beginnen am Seitenanfang.
- Diagramme unterscheiden Reihen durch Linienmuster und zeigen Messnamen und Zeit beim Darüberfahren. Fehlende Werte und Messpausen bleiben als Lücken erkennbar.
- Ein optional kompakter Systemkopf schafft auf der Übersicht mehr Platz für Messwerte. Tastaturfokus und gedrückte Bedienelemente sind klarer erkennbar.
- Beenden und Neustarten bleiben während laufender Hintergrundarbeiten bedienbar; vollständige Rücksetzungen lassen Einstellungen unberührt, wenn ein aktiver Vorgang den Neustart verhindert.
- Updates prüfen freien Speicherplatz und melden unterbrochene Downloads. Klickklänge verbinden sich nach Pausen mit dem aktuellen Audioausgang.

## [v0.9.5.6] - 2026-10-19
- Feste Designpaletten und Hintergründe bleiben grau und deaktiviert; geschlossene Dropdowns ändern ihre Auswahl beim Scrollen nicht.
- Neuer weicher Kristallklang für Buttons, Auswahlen und Dropdowns; zuverlässige Wiederholung nach Pausen und bei schnellen Klicks.
- Die Einstellungssuche gleitet zu erkannten Treffern und bleibt nach der Auswahl fünf Sekunden sichtbar, bevor sie sanft schließt.
- Grafik-Renderer und Wartung liegen ganz unten im animiert auf- und zuklappbaren Bereich „Erweiterte Einstellungen“, den die Suche automatisch öffnet.
- Designvorschauen vergrößern sich beim Darüberfahren sanft; der originale Schriftzug erhält einen deutlicheren, langsam wandernden Lichtreflex.
- Beenden und Neustarten warten sicher auf langsame Sensorabfragen; die Messpause von Ultra Eco verzögert das Schließen nicht mehr.

## [v0.9.5.5] - 2026-10-19
- Zehn Farbschemata über native Vorschaukacheln auswählen; Obsidian Gold, Champagne Glass und Aurora Gold sind jetzt im stabilen Release enthalten.
- Feste Akzent- und Hintergrundoptionen werden direkt im geöffneten Dropdown erklärt; nicht verfügbare Einträge bleiben grau und unveränderbar.
- Einstellungssuche mit synchronisiertem Ein-/Ausblenden, weicher Größenanpassung, unterbrechbaren Übergängen, Escape und fünf Sekunden Inaktivitätszeit.
- Farbschema-, Akzent- und Hintergrundwechsel mit Überblendung in voller Auflösung; Messdaten, Seitenauswahl und Scrollposition bleiben erhalten.
- Neue einheitliche Vektorsymbole in der Seitenleiste; Schrift, Symbole, Logo und Originalschriftzug folgen der wirksamen Farbpalette.
- Originalschriftzug mit dezenter metallischer Lichtreflexion und ruhigen Pausen; äußere Logo-Streifen drehen sich weiterhin langsam.
- Kurzer Glasklang ausschließlich bei Vitalux-Buttons, auch per Tastatur; Lautstärke und Stummschaltung sind einstellbar.
- Weniger Dateizugriffe und unnötige Neuzeichnungen durch Logo-/Icon-Caches und pausierende, unsichtbare Oberflächen; Darstellungsqualität und Messhistorie bleiben erhalten.
- Kurz aufblinkendes Startfenster behoben; CPU, OpenGL, X11/OpenGL sowie Wayland/OpenGL und Wayland/Vulkan mit echten Framebuffern geprüft.
- Normale Quellcode-ZIPs und stabile Pakete starten mit aktiver Update-Funktion; explizite Designvorschauen behalten ihr isoliertes Profil.
- Deutsche und englische Changelogs folgen der ausgewählten Sprache; Anleitung, fehlende Übersetzungen und kompakte englische README aktualisiert.

## [v0.9.5.4] - 2026-10-19
- Einstellungssuche sanfter und breit genug für den vollständigen Platzhalter; Lupensymbol verkleinert.
- Unzuverlässige MiniHUD-Vordergrundoption entfernt, KDE/Wayland-Einschränkungen erläutert.
- Diagnostic Center in eigenständige Kacheln für Systemanalyse, Einzelprüfungen und Berichte gegliedert; Insights-Oberfläche entfernt.
- Überflüssige Live-Tray-Vorschau entfernt; Systeminformationen im Tooltip bleiben verfügbar.
- Erststart-Anleitung wird automatisch einmal geöffnet; X11-/GPU-Startvorbereitung verbessert.
- README deutlich kompakter und Anleitung aktualisiert.

## [v0.9.5.3] - 2026-10-19
- Systemzustand präziser: CPU-/GPU-Last, Temperaturen, RAM, Swap, VRAM, Belegung aller Laufwerke und tatsächliche SMART-Warnungen fließen ein. Fehlende SMART-Befunde werden nicht als gesund bewertet.
- Einstellungssuche mit kleinerer dezenter Lupe, sichtbarer Animation und dynamischer Feldbreite. Geschlossen bleibt die Lupe am Seitenanfang; nur die geöffnete Suche schwebt beim Scrollen mit.
- Originaler DE/EN-Umschalter unten in der Seitenleiste wiederhergestellt und Sprachauswahl aus den Einstellungen entfernt.
- Diagnostic Center in einer großen Kachel gebündelt; Ereignis-Timeline, interaktive Hardwareansicht und Vorher-Nachher-Vergleich entfernt.
- Grafik- und Ultra-Eco-Neustartanzeigen voneinander getrennt. Wartungsaktionen für Vitalux-Cache und persönliche Einstellungen ergänzt.
- MiniHUD: echte transparente Oberflächen mit Deckkraft bis 50 % und verbesserte Anwendung der Vordergrundeinstellung.

## [v0.9.5.2] - 2026-10-19
- Mittige, schwebende Einstellungssuche mit sanfter Glass-Animation, dynamischer Breite und Sofortvorschlägen. Beim Scrollen bleibt sie sichtbar und schließt nach fünf Sekunden Inaktivität oder Klick außerhalb.
- Darstellung, MiniHUD und Hardware-Warnungen lassen sich gezielt zurücksetzen; die Knöpfe erscheinen nur bei Abweichungen von den Standardwerten.
- Gesamtrücksetzung bleibt am Ende aller Einstellungen, importierte Bilder und persönliche Dashboard-Layouts bleiben erhalten.
- DE/EN-Umschalter unten in der Seitenleiste auch im kompakten Zustand erreichbar.

## [v0.9.5.1] - 2026-10-19
- Die ursprüngliche, kompakte Seitenleiste ist zurück: alle Reiter ohne zusätzliche Gruppen und feste Untermenüs.
- Einstellungen wieder auf einer scrollbaren Seite; Allgemein direkt nach Darstellung, Grafik-Rendering ganz unten.
- Die Suche arbeitet ausschließlich innerhalb der Einstellungen und springt mit kurzer Hervorhebung zur gefundenen Option.
- Diagnostic Center zeigt Diagnose, Performance-Analyse, Verlauf und Berichte ohne zusätzliche Unterkategorie-Navigation.
- Qt Raster aus der Backend-Auswahl entfernt; ältere gespeicherte Qt-Raster-Profile werden sicher auf CPU umgestellt.
- Eigene Hintergrundbilder zeigen einen dezenten Leistungshinweis; unveränderte Vorschauen werden nicht wiederholt berechnet.
- Dashboard-Kacheln, bestehende Farbschemata und GPU-Sicherheitsprüfungen bleiben erhalten.

## [v0.9.5.0] - 2026-10-19
- Unterkategorien in Einstellungen und Diagnostic Center optisch verdichtet: Karten bleiben in ihrer natürlichen Höhe statt große Leerflächen zu erzeugen.
- Einstellungssuche zeigt Treffer kompakt; der Berichtsexport nutzt eine passend breite Auswahl.
- Die in v0.9.4.9 eingeführte Neuordnung, Suche, Querverweise und sämtliche Funktionen bleiben unverändert erhalten.


## [v0.9.4.9] - 2026-10-19
- Seitenleiste logisch gruppiert; Einstellungen, Updates und Info bleiben unten fest erreichbar.
- Einstellungen in sechs Unterbereiche geteilt: Darstellung, MiniHUD & Fenster, Monitoring & Warnungen, Leistung & Energie, Allgemein und zuletzt Grafik-Rendering.
- Suche in den Einstellungen mit direkten Treffern ergänzt; zuletzt geöffnete Unterkategorie wird gespeichert.
- Diagnostic Center in sechs Themenbereiche gegliedert. Vitalux Insights mit Gaming Session Analyzer und Vergleichsmessungen aus Grafik dorthin verschoben; Berichte separat erreichbar.
- GPU- und Netzwerkansichten verlinken passende Diagnosewerkzeuge. Laufwerke, Netzwerk und Sensoren sinnvoller sortiert.
- Anleitung, README und Übersetzungen angepasst; bestehende Designs, Überwachung und Benutzeroptionen bleiben erhalten.


## [v0.9.4.8] - 2026-10-19
- Diagnostic Center als neuer Reiter: lokale Hardware-, Treiber- und Fehleranalysen inklusive optionaler Blackbox.
- Bestehende Systemberichte und Fehlerdiagnose aus den Einstellungen in das Diagnostic Center verschoben.
- MiniHUD mit drei Größen, Sensorwahl, Deckkraft und Systemleisten-Steuerung ergänzt.
- Die modernen Grafik-Rendering-Einstellungen und Designs aus v0.9.4.7 bleiben unverändert.


## [v0.9.4.7] - 2026-10-19
- Black Glass Gold: RAM-Beschriftung in der Auslastungsgrafik sowie weitere Diagramm-Legenden und Auslastungsringe direkt beim Aufbau an die Goldpalette angepasst.
- Ultra Eco: eigener Button „Jetzt neu starten“ zum bewussten Wechsel zwischen CPU- und vorherigem GPU-Renderer statt automatischem Neustart beim Umschalten.
- Ultra Eco sparsamer: Messintervall auf 10 Sekunden erhöht, unnötige Diagramm-Aktualisierungen bei verborgenem Fenster und Logo-Neuzeichnungen vermieden.
- Kompakte README, integrierte Anleitung und Übersetzungen auf den aktuellen Stand gebracht.


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
