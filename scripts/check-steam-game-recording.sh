#!/bin/bash
# Exercise Valve's actual pressure-vessel import path, without installing Steam.
set -euo pipefail
STEAM_PROBE_OUTPUT="$(realpath "$1")"
STEAM_PROBE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STEAM_PROBE_VERSION=3.0.20261021.266025
STEAM_PROBE_SOURCE="https://repo.steampowered.com/steamrt3/images/$STEAM_PROBE_VERSION"
mkdir -p "$STEAM_PROBE_OUTPUT/source"
curl -fL --retry 2 --max-time 180 "$STEAM_PROBE_SOURCE/SteamLinuxRuntime_sniper.tar.xz" -o "$STEAM_PROBE_OUTPUT/source/runtime.tar.xz"
curl -fL --retry 2 --max-time 40 "$STEAM_PROBE_SOURCE/SHA256SUMS" -o "$STEAM_PROBE_OUTPUT/source/SHA256SUMS"
python - "$STEAM_PROBE_OUTPUT" <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
root=Path(sys.argv[1]);source=root/'source'
rows=(source/'SHA256SUMS').read_text().splitlines()
expected=next(row.split()[0] for row in rows if row.split()[-1].lstrip('*')=='SteamLinuxRuntime_sniper.tar.xz')
with (source/'runtime.tar.xz').open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
assert expected==actual,'Steam runtime checksum mismatch'
with tarfile.open(source/'runtime.tar.xz') as archive:archive.extractall(source,filter='data')
(root/'runtime-source.json').write_text(json.dumps(dict(version='3.0.20261021.266025',sha256=actual),indent=2)+'\n')
PY
python "$STEAM_PROBE_ROOT/scripts/check-game-recording.py" --output "$STEAM_PROBE_OUTPUT/recording" \
    --probe64 "$STEAM_PROBE_ROOT/build/game-recording/graphics-probe64" \
    --probe32 "$STEAM_PROBE_ROOT/build/game-recording/graphics-probe32" \
    --steam-runtime "$STEAM_PROBE_OUTPUT/source/SteamLinuxRuntime_sniper" --short
