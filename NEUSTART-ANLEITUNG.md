# Vitalux – Neustart v0.9.4.0

**Dieses Archiv enthält nur den vorbereiteten Vitalux-Quellcode.**
Die ältere Commit-Historie, Releases und Runtime-Dateien sind absichtlich nicht enthalten.

## Bevor du etwas auf GitHub löscht

1. Behalte `Vitalux-Sicherung.zip` und prüfe, ob du den Inhalt wieder öffnen kannst.
2. Im **alten** Repository: Settings → General → Repository name → von `Vitalux` auf **`Vitalux-Archiv`** umbenennen. **Nicht löschen.**
3. Auf GitHub ein neues, **leeres** öffentliches Repository `PAAAUUULLOOOH/Vitalux` erstellen. Keine GitHub-README, keine Lizenz und keine `.gitignore` automatisch hinzufügen.
4. **Erst jetzt** diesen Quellcode als neuen ersten Commit hochladen. Mit der Archiv-ZIP selbst kein `git add` ausführen.

## Erster Commit – in einem Terminal im ENTPACKTEN Ordner

```bash
git init -b main
git add .
git commit -m "Initial commit: Vitalux v0.9.4.0"
git remote add origin https://github.com/PAAAUUULLOOOH/Vitalux.git
git push -u origin main
```

GitHub darf vorher keine Branches/Commits enthalten. Der Quellcode hat keine `.git`-Historie.

## Einmaliger erster Release

- Sicherstellen, dass das **alte** `Vitalux-Archiv` und dort der vollständige Release **v0.9.3.82** weiterhin erreichbar sind.
- Auf der **neuen** Repo-Seite **Actions → Vitalux – Manuelle Veröffentlichung → Run workflow → main** starten (nur wenn du wirklich veröffentlichen willst).
- Der Workflow prüft die Version, lädt die bereits geprüfte Laufzeit aus `Vitalux-Archiv`, verpackt das aktuelle Programm, testet die native Qt-Oberfläche und stellt GitHub **v0.9.4.0** bereit: AppImage, komplette Linux-ZIP, Update-von-v0.9.3.82-ZIP und SHA256SUMS-Datei.
- **Erst wenn alle Action-Schritte und die Downloads funktionieren**, kannst du über das endgültige Löschen von `Vitalux-Archiv` entscheiden. Die Sicherungs-ZIP unbedingt aufbewahren.

## Künftige Releases

- Änderungen und Fehlerkorrekturen dürfen auf `main` gesammelt werden. Das löst **keinen** Release aus.
- Wenn ein Release ausdrücklich freigegeben ist, `vitalux/__init__.py` und DE/EN-Changelog aktualisieren. Der letzte Nummernblock läuft **0…9**, danach wird die vorherige Stelle erhöht.
- Auf GitHub **Actions → Vitalux – Manuelle Veröffentlichung → Run workflow → main** ausführen.
- Die nächsten Versionen verwenden die vorherige **Vollversion aus dem neuen Repository**; `Vitalux-Archiv` ist nur für den **allerersten** Release nötig.
- Für jeden veröffentlichten Release erstellt GitHub automatisch AppImage, vollständige ZIP, Differenzupdate und Prüfsummen. Normaler Code-Push erstellt keine Releases mehr.

## Wichtige Einschränkungen

- Ein neues Repository enthält weder die bisherigen Sterne, Issues noch die frühere Commit-/Release-Historie. Alte URLs können ungültig werden.
- Diese Quellcode-ZIP allein enthält **keine gebündelte Linux-Laufzeit**. Für den direkten Linux-Test weiter deine gesicherte Vollversions-ZIP verwenden oder einen offiziellen Release-Build ausführen.
- Die bestehenden Einstellungen auf dem Linux-PC unter `~/.config/vitalux/` werden beim Repo-Neustart nicht gelöscht.
- Die reale Grafik-/Sensorhardware lässt sich nicht allein durch die GitHub-Buildtests abdecken.
