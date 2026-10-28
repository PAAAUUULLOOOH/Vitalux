#!/usr/bin/env bash
# Unpack the checked-in portable runtime locally. No Python or network needed.
set -euo pipefail
# A restart can inherit Vitalux's private libraries. Host tar/xz must use
# their matching system libraries while unpacking the next runtime.
unset LD_LIBRARY_PATH LD_PRELOAD
VITALUX_RUNTIME_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VITALUX_RUNTIME_ARCHIVE="$VITALUX_RUNTIME_ROOT/portable-runtime/vitalux-linux-x86_64.tar.xz"
cd -- "$VITALUX_RUNTIME_ROOT"

if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  printf 'Vitalux benötigt Linux x86-64.\n' >&2
  exit 1
fi

mkdir -p .runtime
if command -v flock >/dev/null 2>&1; then
  exec 9>.runtime/install.lock
  flock 9
fi
install_desktop_libraries() (
  set -euo pipefail
  local checksum="$VITALUX_RUNTIME_ROOT/portable-runtime/desktop-libraries.SHA256SUMS"
  local marker="$VITALUX_RUNTIME_ROOT/.runtime/desktop-libraries.sha256"
  [[ -f "$checksum" ]] || return 0
  if [[ -r lib/libgthread-2.0.so.0 ]] && cmp -s "$checksum" "$marker"; then return 0; fi
  if ! (cd portable-runtime && sha256sum --check desktop-libraries.SHA256SUMS); then
    printf 'Das Desktop-Laufzeitpaket ist beschädigt. Bitte die ZIP erneut vollständig entpacken.\n' >&2
    return 1
  fi
  local stage
  stage="$(mktemp -d "$VITALUX_RUNTIME_ROOT/.runtime/desktop.XXXXXX")"
  trap 'rm -rf -- "$stage"' EXIT
  tar --extract --xz --file portable-runtime/desktop-libraries-linux-x86_64.tar.xz --directory "$stage" --no-same-owner --no-same-permissions
  mkdir -p lib licenses/system-libraries
  cp --remove-destination -- "$stage"/lib/* lib/
  cp --recursive --remove-destination -- "$stage/fallback-libraries" .
  rm -f -- lib/libwayland-client.so.0 lib/libwayland-cursor.so.0 lib/libdrm.so.2
  cp --remove-destination -- "$stage"/licenses/system-libraries/* licenses/system-libraries/
  cp -- "$checksum" "$marker"
)
# Another launcher may have finished unpacking while this one waited.
if [ -f runtime/bin/python3.12 ]; then
  chmod u+x runtime/bin/python3.12
  install_desktop_libraries
  exit 0
fi

for VITALUX_RUNTIME_TOOL in tar xz sha256sum; do
  if ! command -v "$VITALUX_RUNTIME_TOOL" >/dev/null 2>&1; then
    printf 'Zum Entpacken der enthaltenen Laufzeit fehlt das Systemwerkzeug: %s\n' "$VITALUX_RUNTIME_TOOL" >&2
    exit 1
  fi
done

printf 'Enthaltene Python-/Qt-Laufzeit wird geprüft und einmalig entpackt …\n'
if ! (cd portable-runtime && sha256sum --check SHA256SUMS); then
  printf 'Das Laufzeitpaket ist beschädigt. Bitte die ZIP erneut vollständig entpacken.\n' >&2
  exit 1
fi
VITALUX_RUNTIME_STAGE="$(mktemp -d "$VITALUX_RUNTIME_ROOT/.runtime/extract.XXXXXX")"
trap 'rm -rf -- "$VITALUX_RUNTIME_STAGE"' EXIT
tar --extract --xz --file "$VITALUX_RUNTIME_ARCHIVE" \
  --exclude='*licenses/upstream/*/licensewizard*' \
  --exclude='*licenses/upstream/*/license_check.py' \
  --directory "$VITALUX_RUNTIME_STAGE" --no-same-owner --no-same-permissions
if [ ! -f "$VITALUX_RUNTIME_STAGE/runtime/bin/python3.12" ]; then
  printf 'Das Laufzeitpaket enthält kein Python.\n' >&2
  exit 1
fi
# Keep existing local files intact; publish Python last so a failed extraction
# cannot leave an apparently ready runtime behind.
for VITALUX_RUNTIME_PART in lib tools-lib licenses; do
  if [ ! -e "$VITALUX_RUNTIME_ROOT/$VITALUX_RUNTIME_PART" ]; then
    mv -- "$VITALUX_RUNTIME_STAGE/$VITALUX_RUNTIME_PART" "$VITALUX_RUNTIME_ROOT/$VITALUX_RUNTIME_PART"
  elif [ "$VITALUX_RUNTIME_PART" = licenses ]; then
    cp --recursive --no-clobber -- "$VITALUX_RUNTIME_STAGE/licenses/." "$VITALUX_RUNTIME_ROOT/licenses/"
  fi
done
mkdir -p bin
if [ ! -e bin/fio.real ]; then
  mv -- "$VITALUX_RUNTIME_STAGE/bin/fio.real" bin/fio.real
fi
if [ -e runtime ]; then
  printf 'Der vorhandene Ordner runtime ist unvollständig. Bitte die ZIP in einen neuen Ordner entpacken.\n' >&2
  exit 1
fi
mv -- "$VITALUX_RUNTIME_STAGE/runtime" runtime
chmod u+x runtime/bin/python3.12 bin/fio bin/fio.real
install_desktop_libraries
printf 'Python und Qt sind bereit. Vitalux startet.\n'
