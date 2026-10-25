# Vitalux – Änderungen

## [v0.9.6.3] - 2026-10-25
- Die Designauswahl konzentriert sich auf Obsidian Gold, Glass, Crystal Glass, Nebula Prism, Quantum Core und Light. Farben und Hintergründe vieler früherer Designs bleiben als benannte Vorlagen verfügbar. Alle sechs Designs unterstützen getrennt gespeicherte Akzentfarben und Hintergründe mit passenden Original- und Zurücksetzen-Aktionen.
- Crystal Glass erhält die Glasflächen auf einem durchgehenden statischen Hintergrund und unterstützt den Übersicht-Layouteditor. Nebula Prism ergänzt prismatische Instrumente und ein schwebendes Dock; Quantum Core kantige Neon-Panels und Reaktoranzeigen mit statischem Originalhintergrund.
- Die Übersicht zeigt einen größeren, mittig ausgerichteten Systemkopf und geräumigere Infokacheln. Komponententexte folgen einer einheitlichen mittigen Reihenfolge; lange Namen bleiben über den Mauszeiger vollständig lesbar. Designvorschauen passen in die abgerundeten Auswahlkacheln.
- Erweiterte Linux-Sensoren zeigen tatsächlich verfügbare Komponentenleistung und zusätzliche Treiberwerte. Fehlende Messwerte bleiben unbekannt oder ausgeblendet; echte Nullwerte bleiben sichtbar. Grafik bündelt aktuelle Werte einschließlich Auslastung, Videospeicher, Watt und Leistungsgrenze ohne doppelte Sensorenkachel.
- Der Prozessor-Reiter zeigt sämtliche vorhandenen logischen CPUs numerisch sortiert und passt die Kachelgrößen an. Ein gemeinsames Verlaufsdiagramm bietet auswählbare Auslastung, Temperatur und Takt mit eigenen Einheitenskalen.
- CPU, Grafikkarte, RAM-Module und Mainboard erhalten genauere Hersteller-/Modellangaben sowie passende, optional ausschaltbare Produktbilder mit Offline-Cache. Freigestellte Bilder werden bevorzugt; passende Fotos mit Hintergrund dienen als Ersatz. CPU-Bilder müssen zur erkannten Modellvariante passen.
- CPU-, Grafik- und Mainboard-Spezifikationen erscheinen kurz in der Komponentenansicht und ausführlich in einem scrollbaren Herstellerdatenfenster mit Quellenlink. Herstellertexte folgen Deutsch oder Englisch und bleiben nach erfolgreichem Laden offline verfügbar.
- Ein Initialisierungsfenster mit tatsächlich abgerundeten Ecken und mittiger Bildschirmplatzierung zeigt echte Vorbereitungsschritte; Oberfläche, erste Messwerte und vorhandene Produktdaten werden vor der Hauptansicht vorbereitet. Ultra Eco stellt beim Ausschalten das zuvor benutzte Design wieder her.
- Vitalux startet pro Benutzer nur einmal. Updates und Kanalwechsel starten nach erfolgreicher Vorbereitung automatisch neu; langsame Downloads lassen sich abbrechen oder wiederholen und melden ihren Fortschritt deutlicher. Die vollständige laufende Version bleibt sichtbar; lange Changelogs erhalten einen begrenzten Scrollbereich.
- Sobald eine frische Prüfung bestätigt, dass Stable den installierten Teststand vollständig enthält, kehrt Unstable automatisch zu Stable zurück. Spätere neue Teststände erfordern weiterhin einen bewussten Wechsel zu Unstable.
- Vollständiges Zurücksetzen betrifft nur das aktive Kanalprofil, entfernt auch dessen Cache und öffnet die Anleitung erneut. Erweiterte Einstellungen und Wartung bleiben dauerhaft sichtbar; es gibt keine Einklappfunktion. Reset/Neustart warten auf Hintergrundarbeiten; AppImage-Aktivierung und Wiederherstellung verwenden einen gemeinsamen Ablauf.
- Einstellungen finden MiniHUD auch bei unvollständigen Suchbegriffen. Das Diagnosezentrum zeigt die letzten fünf App-Ereignisse; fehlende Messungen erhalten bei bekannter Ursache einen Hinweis. Klickklänge und ihre Einstellungen entfallen.
- Ohne neue Teständerungen zeigt Unstable „Keine neuen Updates · Wechsel zu Unstable nicht möglich“. Beide Kanäle verwenden dann dieselbe veröffentlichte Stable-Basis ohne zusätzliche Testnummer.

## [v0.9.6.2] - 2026-10-21
- Der Updates-Reiter zeigt laufenden Stand, Stable/Unstable und Changelogs in zwei klaren Bereichen; Kanalwahl und Installation bleiben ohne zusätzliches Fenster getrennte Aktionen.
- Doppelte Versionsangaben und der Knopf zum Übernehmen von Einstellungen entfallen. Kanalprofile werden weiterhin automatisch erstellt und erhalten.
- Kleinere Farbkreis- und Hintergrundsymbole erscheinen rechts mittig untereinander auf den Designkacheln, weiterhin mit sanftem Ein- und Ausblenden.
- App-Netzwerksperren erfassen neue Unterprozesse sofort, einschließlich neuer TCP-/UDP-Verbindungen; Entsperren gibt die geerbten Sperren gemeinsam frei.
- Programm- und Verbindungslisten behalten beim Aktualisieren, Sperren und Entsperren ihre Auswahl und Scrollposition.

## [v0.9.6.1] - 2026-10-21
- Stable und Unstable lassen sich zum Lesen des aktuellen Changelogs anklicken, ohne dadurch den Kanal zu wechseln oder eine Update-Meldung auszulösen; aktueller Stand und Installationsziel werden getrennt angezeigt.
- Ein Wechsel zu Unstable ist nur mit einem geprüften, tatsächlich neueren Teststand möglich. Gleiche Stände werden verständlich gekennzeichnet.
- Nach einer Installation selbst zwischen „Jetzt neu starten“ und „Später“ wählen; bis dahin bleibt „Neustart erforderlich“ sichtbar, ohne doppelte Update-Angebote.
- Ein Hinweis zeigt, wenn die eigenen Teständerungen inzwischen in Stable enthalten sind; ein neuerer Unstable-Teststand bleibt vorrangig.
- Testprofile werden automatisch erstellt und erhalten. Der zusätzliche Knopf für ein frisches Testprofil entfällt.
- Bereits geladene Kanal-Changelogs bleiben offline lesbar. Prüfzeitpunkt und Verbindungsfehler werden klar angezeigt.

## [v0.9.6.0] - 2026-10-21
- Zwischen Stable und Unstable direkt unter Updates wechseln; getrennte Einstellungsprofile, Sicherungen und die Rückkehr zur stabilen Version erhalten die jeweilige Konfiguration.
- Apps direkt in der Netzwerkliste sperren und entsperren. Die erforderliche Systemfreigabe wird beim Sperren angefragt, Fehler werden sichtbar erklärt.
- Einzelne TCP-/UDP-Verbindungen lassen sich in den sanft aufklappbaren erweiterten Verbindungsdetails unabhängig sperren und freigeben.
- Alle Designs erscheinen auch in Aether Glass und Eclipse Crystal als vollständiges Vorschau-Raster. Beim Darüberfahren zeigen Farbkreis- und Bildsymbole die Anpassbarkeit; feste Optionen tragen ein Schloss.
- Einheitliche, zum Design passende Ein/Aus-Schalter; Mehrfachauswahlen behalten ihre Häkchen.
- Weicher, gedämpfter Klickton mit 50 % Standardlautstärke und zuverlässiger Wiedergabe bei wiederholten Klicks.

## [v0.9.5.9] - 2026-10-20
- Aether Glass und Eclipse Crystal ergänzen die Designauswahl mit eigenen Glas-/Kristallmaterialien, Instrumenten und Navigationslayouts. Ihre Paletten und Hintergründe sind fest abgestimmt.
- Der ausgewählte kantige VITALUX-Schriftzug erhält Metall- und Rauchglasfacetten, passende Farbvarianten und den bestehenden Lichtreflex.
- Unter Netzwerk → Programme & Verbindungen lassen sich Programme, Verbindungsziele und erfasster Datenverbrauch untersuchen; Verbrauchswarnungen sind pro App einstellbar.
- Eine optionale Systemfreigabe ermöglicht TCP-/UDP-Messung und Netzwerksperren für laufende Programme. Sitzungssperren werden beim Beenden der Freigabe oder der App automatisch aufgehoben.
- „Farbschema“ heißt jetzt „Design“. Fehlende Prozess- oder Verkehrsdaten werden ausdrücklich als nicht verfügbar angezeigt.
- Überlagerte Diagrammreihen behalten ihre korrekten transparenten Flächen ohne zusätzliche Farbflächen zwischen den Linien.

## [v0.9.5.8] - 2026-10-20
- Die Übersicht verwendet den kompakten Systemkopf dauerhaft; der bisherige Umschalter entfällt und alle Systeminformationen bleiben erhalten.
- Neues Kreislogo mit feineren Außenbögen und Glasmitte sowie neuer Vitalux-Schriftzug mit abgestimmtem Metallfinish.
- Deutlicher Herzschlagimpuls, langsame Außendrehung und weicher Schriftreflex laufen ohne sichtbaren Schnitt; beim Farbschemawechsel bleibt die Animationsphase erhalten.
- Obsidian Gold, Black Glass Gold, Champagne Glass und Aurora Gold besitzen jeweils eigene Logo- und Schriftfarben. Eigene Akzentfarben wirken am Kreislogo etwas satter, ohne die übrige Oberfläche stärker einzufärben.
- Flüssigere Logoanimation mit scharfer Darstellung bei vergrößerter Desktop-Skalierung; reduzierte Bewegung, ausgeschaltete Animationen und Ultra Eco bleiben berücksichtigt.

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
