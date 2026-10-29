#!/usr/bin/env bash
# One-version recovery guard for installed/portable Vitalux AppImages.
# The .previous AppImage is preserved on healthy exits and replaced by the
# immediate predecessor on the next update. No user downloads are touched.
set -u
BASE="${1:?AppDir}"
TARGET="${2:?AppImage}"
shift 2
PREVIOUS="${TARGET}.previous"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/vitalux"
# The running mount identifies the exact version that failed.
VERSION="$(sed -n 's/^__version__ = "\([^"]*\)".*/\1/p' "$BASE/vitalux/__init__.py" 2>/dev/null)"
case "$VERSION" in *-unstable.*) STATE="$STATE/profiles/unstable" ;; esac
mkdir -p -- "$STATE"
LOG="$STATE/restart.log"
if [[ -r "$BASE/packaging/logging.sh" ]]; then source "$BASE/packaging/logging.sh"; fi
log_line() {
  if declare -F vitalux_log_line >/dev/null; then
    vitalux_log_line "$LOG" "$VERSION" "$*"
    return
  fi
  printf '[%s] [Vitalux v%s] %s\n' "$(date -Is)" "${VERSION:-unknown}" "$*" >> "$LOG"
}
log_child() {
  while IFS= read -r line || [[ -n "$line" ]]; do
    log_line "$line"
  done
}

# Never trust or follow an unrelated/symlinked rollback file.
if [[ ! -f "$TARGET" || -L "$TARGET" ]]; then
  exec bash "$BASE/run.sh" "$@"
fi

REQUEST="$(mktemp "$STATE/.appimage-launch-XXXXXXXX")" || exit 1
trap 'rm -f -- "$REQUEST"' EXIT
log_line "Starting Vitalux with one owner for update and recovery."
# The mailbox is unique to this launch and remains on disk through a reset.
VITALUX_GUARDED=1 VITALUX_APPIMAGE_REQUEST_FILE="$REQUEST" VITALUX_APPIMAGE_TARGET="$TARGET" bash "$BASE/run.sh" "$@"
status=$?
if [[ -s "$REQUEST" && ! -L "$REQUEST" ]]; then
  "$BASE/runtime/bin/python3.12" -I "$BASE/packaging/appimage-activate.py" "$REQUEST" "$TARGET" "$VERSION" >>"$LOG" 2>&1
  activation=$?
  if [[ "$activation" == 0 || "$activation" == 10 || "$activation" == 20 ]]; then
    if [[ "$activation" == 20 ]]; then
      log_line "Requested restart retained the current version; recovery of the exiting process is skipped."
    else
      log_line "Prepared update activated; recovery of the exiting version is skipped."
    fi
    if [[ "$activation" == 0 || "$activation" == 20 ]]; then
      unset APPDIR APPIMAGE LD_LIBRARY_PATH LD_PRELOAD PYTHONHOME PYTHONPATH PYTHONUSERBASE VITALUX_GUARDED VITALUX_APPIMAGE_REQUEST_FILE VITALUX_APPIMAGE_TARGET
      exec "$TARGET" --launch "$@" > >(log_child) 2>&1
    fi
    exit 0
  fi
  log_line "Prepared update activation failed (status $activation); previous files retained."
  if [[ "$status" == 0 ]]; then exit 1; fi
fi
case "$status" in
  0|129|130|143)
    # Normal exit, terminal interrupt or a typical session-shutdown signal.
    # Retain previous until the NEXT successful update replaces it.
    exit "$status"
    ;;
esac

log_line "Vitalux exited unexpectedly (status $status). Attempting rollback."
if [[ ! -f "$PREVIOUS" || -L "$PREVIOUS" || ! -f "$TARGET" || -L "$TARGET" ]]; then
  log_line "Rollback skipped: valid previous AppImage no longer present."
  exit "$status"
fi
TMP="$(mktemp "${TARGET}.rollback-XXXXXXXX")" || exit "$status"
trap 'rm -f -- "$TMP" "$REQUEST"' EXIT
if ! cp -p -- "$PREVIOUS" "$TMP"; then
  log_line "Rollback copy failed."
  exit "$status"
fi
chmod u+x "$TMP" || exit "$status"
if ! mv -f -- "$TMP" "$TARGET"; then
  log_line "Rollback swap failed."
  exit "$status"
fi
trap - EXIT
rm -f -- "$PREVIOUS" "$REQUEST"
log_line "Recovered previous Vitalux version. Restarting it."
# Launch the restored version once, without inheriting the failed AppImage mount.
unset APPDIR APPIMAGE LD_LIBRARY_PATH LD_PRELOAD PYTHONHOME PYTHONPATH PYTHONUSERBASE VITALUX_GUARDED VITALUX_APPIMAGE_REQUEST_FILE VITALUX_APPIMAGE_TARGET
exec "$TARGET" --launch "$@" > >(log_child) 2>&1
