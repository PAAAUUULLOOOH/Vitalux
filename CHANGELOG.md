# Vitalux – Änderungen


## [v0.9.6.4] - 2026-10-30

- Neues Spiele-Center: installierte Steam-, Heroic- und Lutris-Spiele erkennen, durchsuchen und starten; kompakte Cover-Kacheln mit aktueller Sitzungsanzeige und Offline-Bildern.
- MangoHud ist für 32-/64-Bit-Spiele mit OpenGL und Vulkan enthalten, einschließlich Steam-Laufzeit und Flatpak. Metriken, Position, Größe, Deckkraft, Tastenkürzel und FPS-Ziel lassen sich pro Spiel einstellen; vorhandene Startargumente bleiben erhalten.
- Die Overlay-Einrichtung prüft die tatsächlichen Launcher-Einträge und das aktive Steam-Konto. Ein nötiger Steam-Neustart erfolgt automatisch; laufende Spiele werden geschützt. Einrichtung und Spielstart melden Fehler sichtbar.
- Nach Spielende erscheinen lokale Auswertungen mit Durchschnitts-FPS, 1%-/0,1%-Low, FPS-/Frametime-Verlauf, Hardware-Spitzen und Sitzungshistorie. Zielabhängige Bewertungen erhalten passende Farben; unvollständige Messungen bleiben neutral. Lange Auswertungen bleiben flüssig bedienbar.
- Rahmenloses Hauptfenster mit abgerundeten Außenecken, eigenen Fensterknöpfen, Verschieben, Größenänderung und Maximieren. Layout-Bearbeitung und Fenstersteuerung teilen sich die obere Leiste.
- Alle Designs: bündige Navigation ohne doppelte Distro-/Designnamen, mehr nutzbare Kachelfläche, sauberes Ein-/Ausklappen und Scrollen hinter festen Leisten. Kopf- und Seitenleiste bilden bei entsprechenden Designs eine gemeinsame abgerundete Oberfläche; Nebula Prism nutzt ein freistehendes transparentes Dock.
- Alle Designs: weichere unterbrechbare Designwechsel ohne Aufblitzen, gut sichtbare Update-Hinweise, klare Tastaturfokusse sowie abgestimmte Suche, Dialoge und Innenabstände. Die Einstellungssuche folgt der Mitte des Inhaltsbereichs.
- Crystal Glass heißt wieder Crystal Atrium und nutzt den ursprünglichen statischen Atrium-Hintergrund. Gespeicherte Farben und Hintergründe werden übernommen. Aurora Bloom ergänzt die reguläre Designauswahl mit eigener Vorschau und asymmetrisch abgerundeten Bedienelementen.
- Diagrammauswahl und Zeitfenster bleiben gespeichert. Eine bevorzugte Grafikkarte kann für Übersicht, Desktop-Overlay und Diagnosen gewählt werden.
- Komponenten lassen sich einzeln neu laden; falsche Produktbilder können verworfen oder durch eigene ersetzt werden. Nachgeladene Spezifikationen aktualisieren sich auch im geöffneten Fenster. RAM-Bildabfragen entfallen; Hersteller, Teilenummer und Spezifikationen bleiben erhalten.
- Vollständige Sensorlisten unterscheiden fehlende und veraltete Messwerte. Diagnoseberichte und Exporte folgen der App-Sprache; der Vergleich mit einer Diagnosebasis blockiert die Oberfläche nicht.
- Grafik-Renderer auf CPU und X11/OpenGL konzentriert; entfernte Einstellungen wechseln auf CPU. Das Initialisierungsfenster richtet sich auch nach Bildschirmänderungen mittig aus.
- Updates, Rendererwechsel und bestätigtes Zurücksetzen verwenden einen kontrollierten automatischen Neustart. Offene Spiele-Launcher blockieren ihn nicht; App-Menü-Starts verlieren keine installierte Zielkopie durch übernommene AppImage-Kennungen. Vorbereitete Updates werden vor dem Neustart erneut geprüft.
- Enthält Stable den Teststand vollständig, führt das normale Unstable-Update direkt zu Stable – auch wenn der Gleichstand während Download oder Vorbereitung entsteht. Gleiche Stände bieten keinen Wechsel zu Unstable; neue Tests erfordern wieder eine ausdrückliche Auswahl.
- Geringerer Rechenaufwand und begrenzte Caches bei Designs, Hintergründen, Diagrammen, Sensorabfragen und Netzwerkdetails, bei unveränderten Animationen, Darstellungsqualität und Messintervallen. Benötigte Desktop-Bibliotheken sind enthalten; eine separate GLib-Installation entfällt.

## [v0.9.6.4-unstable.15] - 2026-10-30

- Automatische Neustarts nach Updates, Rendererwechseln und dem Zurücksetzen bleiben nicht mehr an weiterhin geöffneten Spiele-Launchern hängen.
- Spiele-Launcher werden gezielt und unabhängig geöffnet. Die Overlay-Einrichtung ruft durch übernommene AppImage-Kennungen nicht mehr versehentlich Vitalux erneut auf.

## [v0.9.6.4-unstable.14] - 2026-10-29

- Steam-Kontoerkennung unterstützt aktuelle Kontodaten ohne MostRecent, einschließlich AutoLogin und Kontonamen aus der Steam-Registry. Gemeinsame Datenordner werden nicht als zusätzliches Konto gezählt.
- Rendererwechsel und bestätigtes Zurücksetzen starten Vitalux zuverlässig neu. Laufende Vorgänge werden abgewartet; vorbereitete Neustarts bleiben bei einem Fehler während des Beendens erhalten.
- Renderer-Auswahl auf CPU und X11/OpenGL reduziert. Einstellungen entfernter Renderer wechseln sicher auf CPU.

## [v0.9.6.4-unstable.13] - 2026-10-29

- Steam-Anbindung berücksichtigt die laufende native oder Flatpak-Installation und das aktive Konto. Ungültige Kontodaten werden vor einem Neustart erkannt.
- Overlay-Startoptionen werden nach dem Schreiben und nach einem nötigen Steam-Neustart erneut geprüft. Bei verlorenen Optionen startet das Spiel nicht ohne sein aktiviertes Overlay.
- Fehler im Overlay-Profil bleiben auch nach einer Aktualisierung sichtbar. Laufende Einrichtung sperrt weitere Start- und Speicheraktionen.

## [v0.9.6.4-unstable.12] - 2026-10-29

- Portable-Pakete enthalten die benötigten GLib- und weiteren Desktop-Laufzeitbibliotheken. Der Start erfordert keine separate GLib-Nachinstallation.
- Steam wird bei nötiger Overlay-Einrichtung geordnet automatisch neu gestartet. „Spiel starten“ richtet die Verbindung ein und startet anschließend das Spiel; laufende Steam-Spiele werden nicht beendet. Bestehende Verbindungen und reine Metrikänderungen benötigen keinen Neustart.
- Spiele-Auswertungen bleiben auch bei langen Sitzungen flüssig bedienbar. Messwerte und Spitzen bleiben erhalten.
- Spielkachel, aktuelle Sitzung und Historie aktualisieren sich nach Spielende gemeinsam, ohne Vitalux-Neustart.
- Bewertungen verwenden passende Farben: Grün für sehr gut/gut, Gelb für ausreichend und Rot für Verbesserungsbedarf. Unvollständige oder zu kurze Messungen bleiben neutral.
- Spielcover füllen die gleich großen Kacheln proportional aus. Namen und Sitzungsangaben bleiben lesbar innerhalb der Kachel.
- RAM-Produktbilder und deren Abfragen entfernt. Erkannter Hersteller, Teilenummer und Modulspezifikationen bleiben sichtbar.

## [v0.9.6.4-unstable.11] - 2026-10-28

- Aurora Bloom ist regulär mit eigener Vorschaukachel auswählbar. Buttons und Auswahlfelder erhalten die asymmetrischen Rundungen; die innere Verbindungsecke von Kopf- und Seitenleiste ist abgerundet.
- Designs mit einklappbarer Seitenleiste: Die Einstellungssuche sitzt mittig über dem Inhaltsbereich und folgt der Seitenleistenbewegung. Der Reststreifen unter der oberen Fensterkontur ist behoben.
- Glass, Obsidian Gold und Light: etwas mehr fester Abstand zwischen Vitalux-Schriftzug und Navigationsreitern, auch im Vollbild.
- Kompakte Spielkacheln mit mittigem Namen oben, passend skaliertem Bild und Launcher sowie Sitzungsanzeige darunter. Steam-Bilder berücksichtigen auch aktuelle Cache-Dateien und offizielle Bildadressen.
- „Spiel starten“ prüft und bereitet die tatsächliche Overlay-Verbindung vor. Verlorene Launcher-Einträge werden erkannt; ein nicht verbundenes aktiviertes Overlay wird nicht mehr beim Start übergangen. Native und Flatpak-Launcher werden gezielt gestartet.
- Overlay-Profile schließen nach dem Speichern erst bei erfolgreicher Einrichtung. Fehler bleiben sichtbar; vorhandene Startargumente bleiben erhalten.

## [v0.9.6.4-unstable.10] - 2026-10-28

- Weniger Rechenaufwand und begrenzter Speicherbedarf beim wiederholten Wechseln von Designs und Akzentfarben. Darstellung, Animationen und Messintervalle bleiben erhalten.
- Animierte Hintergründe pausieren bei ausgeblendetem Fenster vollständig und laufen beim Öffnen weiter.
- Bereits geöffnete Spezifikationsfenster zeigen nachgeladene Herstellerangaben zuverlässig an.

## [v0.9.6.4-unstable.9] - 2026-10-28

- Alle Designs: Designwechsel ohne Aufblitzen oder Helligkeitssprung; auch bei unterbrochenen Übergängen und vergrößerter Bildschirmdarstellung.
- Alle Designs: ruhigere Kachelflächen, klarer abgestufte Messwerte und Beschriftungen sowie ausgewogene Innenabstände für schmale Fenster. Farben, Hintergründe und besondere Designformen bleiben individuell.
- Alle Designs: einheitliche Hervorhebung verfügbarer Updates in Seitenleiste, Kopf-Navigation und Dock. Die Markierung bleibt auch bei reduzierten oder ausgeschalteten Animationen sichtbar.
- Alle Designs: abgestimmte Hover-, Such- und Navigationsübergänge sowie klarer Tastaturfokus. Reine Informationskacheln leuchten beim Überfahren nicht mehr zusätzlich auf.
- Spezifikationen, Details, Spielprofile und Bestätigungen verwenden passende Designmaterialien, gemeinsame Abstände und einheitliche Schaltflächen.

## [v0.9.6.4-unstable.8] - 2026-10-27

- Spiel-Overlay: Aktivierte Profile verbinden das Spiel beim Speichern mit dem Launcher. Der tatsächliche Verbindungsstatus wird angezeigt. Die mitgelieferte MangoHud-Anbindung funktioniert auch innerhalb der Steam-Laufzeit für OpenGL und Vulkan.
- Spielebibliothek: breite, hochauflösende Steam-Kapselbilder mit Offline-Cache. Titel, Launcher und Sitzungsstatus stehen einheitlich darunter; ungeeignete kleine oder hochkantige Bilder werden nicht vergrößert.
- Alle Designs: direkter, weicher Designwechsel ohne zwischendurch aufblinkendes Design. Die obere Fensterkontur bleibt beim Ein- und Ausklappen der Seitenleiste erhalten.
- Designs mit Kopf- und Seitenleiste: zusammenhängendes Material ohne überlappende Naht. Crystal Atrium erhält passende Rundungen an den Leistenenden und der inneren Verbindung.
- Nebula Prism: freistehendes, leicht transparentes Dock mit gleichmäßiger Kontur. Kacheln scrollen dahinter und seitlich bis zum unteren Fensterrand.
- Einstellungen: mittige Suche in der oberen Leiste, passend zu den Fensterknöpfen. Lupe und Text bleiben beim Öffnen und Schließen sauber ausgerichtet.

## [v0.9.6.4-unstable.7] - 2026-10-27

- MangoHud 0.8.4 ist für 32- und 64-Bit-Spiele mit OpenGL oder Vulkan direkt enthalten, auch für Flatpak-Launcher. Keine separate MangoHud-Installation oder Erweiterung nötig.
- Bestehende Spielverbindungen nutzen das mitgelieferte Overlay automatisch. Profile und lokale Auswertungen bleiben erhalten; die Spielanbindung bleibt auch nach dem Schließen oder Aktualisieren der App verfügbar.

## [v0.9.6.4-unstable.6] - 2026-10-27

- Neuer Reiter Spiele: installierte Spiele aus Steam (auch Flatpak und zusätzliche Bibliotheken), Heroic und Lutris automatisch erkennen, durchsuchen und starten. Bisherige Auswertungen bleiben auch nach der Deinstallation erhalten.
- MangoHud pro Spiel einrichten: auswählbare Metriken, Position, Größe, Deckkraft, Tastenkürzel und FPS-Ziel. Bestehende Launcher-Startargumente bleiben erhalten; die Verbindung lässt sich entfernen. Das bisherige MiniHUD bleibt als Vitalux Overlay für den Desktop verfügbar.
- Nach Spielende automatisch eine lokale Auswertung mit Durchschnitts-FPS, 1%- und 0,1%-Low, auswählbarem FPS-/Frametime-Verlauf, verfügbaren Hardware-Spitzenwerten und Sitzungshistorie anzeigen. Zielabhängige Bewertungen erläutern ihre Kriterien; unvollständige oder zu kurze Messungen erhalten keine Gesamtnote.
- Geringerer Aufwand bei Übersicht, Diagramm-Hover, Sensorerkennung und geschlossenen Netzwerkdetails; weniger Speicherbedarf bei wiederholt geöffneten Kontextmenüs und experimentellen Grafik-Hintergründen. Vorhandene Designs, Animationen und Messintervalle bleiben erhalten.

## [v0.9.6.4-unstable.5] - 2026-10-26

- Alle Designs: zusätzliche Abdunklung der Fensterleiste und doppelte Distro-/Designnamen aus den Navigationsleisten entfernt. Der Distributionsname bleibt in der Übersicht.
- Seitenleisten reichen bündig bis an die linke und untere Fensterkontur; Designs ohne Kopfleiste schließen auch oben am Fensterrand ab. Material und Rundungen folgen dem jeweiligen Design.
- Vorhandene Kopfleisten füllen den oberen Fensterrand und enthalten die Layout- und Fensterknöpfe. Seitenleisten docken direkt darunter an, ohne zusätzliche Leiste oder schwebenden Abstand.
- Kacheln nutzen die gewonnene Fläche und scrollen hinter der festen Navigation weiter. Bearbeitungsaktionen passen auch in schmale Kopfleisten; Fensterknöpfe und Scrollen bleiben bedienbar.

## [v0.9.6.4-unstable.4] - 2026-10-26

- Alle Designs: Seitenleiste beim Ein-/Ausklappen korrekt am rahmenlosen Fenster ausgerichtet; saubere Übergänge und gerade Anschlüsse.
- Kompakte Fensterleiste ohne Vitalux-Schriftzug. Layout-Bearbeitung links neben Minimieren, mit einheitlichen Knöpfen und Bearbeitungsaktionen in der oberen Leiste.
- Übersichtskacheln weiter oben, mehr nutzbare Breite und automatisch angepasste Kachelgrößen bis zum rechten Rasterrand.
- Kacheln bleiben beim Scrollen unter der feststehenden, halbtransparenten Fensterleiste sichtbar; Scrollen funktioniert auch über der Leiste.

## [v0.9.6.4-unstable.3] - 2026-10-26

- Alle Designs: Rahmenloses Hauptfenster mit echten runden Außenecken, eigenen Fensterknöpfen sowie Verschieben, Größenänderung und Maximieren.
- Initialisierungskarte nach dem Anzeigen und bei Bildschirmänderungen mittig ausgerichtet, auch unter KDE/Wayland.

## [v0.9.6.4-unstable.2] - 2026-10-26

- Gespeicherte Diagrammauswahl und Zeitfenster sowie eine bevorzugte Grafikkarte für Übersicht, MiniHUD und Diagnosen.
- Komponenten einzeln neu laden, falsche Bilder verwerfen oder eigene Bilder auswählen; abrufbare Fehler- und Datenquellendetails.
- Vollständige Sensorlisten mit eindeutigen Sensoren, erkennbare veraltete Messwerte und keine falsche Entwarnung bei fehlenden Daten.
- Diagnoseberichte und Exporte in der gewählten App-Sprache; ChangeRadar-Vergleichsbasis ohne Blockieren der Oberfläche.
- Gleichmäßiger Updatefortschritt beim automatischen Wechsel zu Stable.
- Geringerer Aufwand für Hintergründe, Animationen, Tabellen und Sensorabfragen bei unveränderter Darstellungsqualität.

## [v0.9.6.4-unstable.1] - 2026-10-26
- Unstable-Updates wechseln direkt zu Stable, sobald Stable den Teststand enthält. Der Gleichstand wird auch während der Vorbereitung und vor dem Neustart geprüft; ein zusätzlicher Kanalwechsel ist nicht nötig.
- Design Crystal Atrium: Das bisherige Crystal Glass trägt wieder den Namen Crystal Atrium und nutzt den ursprünglichen statischen Atrium-Hintergrund. Glasflächen, Übersicht-Layouteditor und abgerundete Designauswahl bleiben erhalten. Persönliche Farben und Hintergründe werden übernommen; Crystal Glass bleibt als Farb- und Hintergrundvorlage verfügbar.

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
