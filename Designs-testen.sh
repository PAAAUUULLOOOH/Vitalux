#!/usr/bin/env bash
# Local-only UI preview. Does not install or overwrite the installed Vitalux.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
VITALUX_PREVIEW_ROOT="$PWD"
export PATH="$VITALUX_PREVIEW_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$VITALUX_PREVIEW_ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
unset PYTHONHOME PYTHONPATH PYTHONUSERBASE
VITALUX_PREVIEW_PY="$VITALUX_PREVIEW_ROOT/runtime/bin/python3.12"
if [ ! -f "$VITALUX_PREVIEW_PY" ] && [ -f "$VITALUX_PREVIEW_ROOT/portable-runtime/vitalux-linux-x86_64.tar.xz" ]; then
  bash "$VITALUX_PREVIEW_ROOT/scripts/ensure-runtime.sh"
fi
if [ -f "$VITALUX_PREVIEW_PY" ] && [ ! -x "$VITALUX_PREVIEW_PY" ]; then
  chmod u+x "$VITALUX_PREVIEW_PY"
fi
if [ ! -x "$VITALUX_PREVIEW_PY" ]; then
  if [ -x "$VITALUX_PREVIEW_ROOT/.venv/bin/python" ]; then
    VITALUX_PREVIEW_PY="$VITALUX_PREVIEW_ROOT/.venv/bin/python"
  else
    printf 'Die Python-Laufzeit fehlt. Bitte die vollständige Test-ZIP entpacken.\n' >&2
    exit 1
  fi
fi
mkdir -p design-test-data/state
while true; do
  set +e
  "$VITALUX_PREVIEW_PY" -u -m vitalux.preview "$@" 2>&1 \
    | tee -a design-test-data/state/design-preview.log
  VITALUX_PREVIEW_STATUS=${PIPESTATUS[0]}
  set -e
  if [ "$VITALUX_PREVIEW_STATUS" -ne 42 ]; then
    exit "$VITALUX_PREVIEW_STATUS"
  fi
  # Preserve the latest UI choice across a renderer-triggered restart.
  set --
done
