#!/bin/sh
# Variables above this body are quoted by Vitalux; the game command is argv.
umask 077
if [ ! -r "$VITALUX_OVERLAY_CONFIG" ] || [ ! -f "$VITALUX_OVERLAY_ENABLED" ]; then
    exec "$@"
fi
if [ "$VITALUX_OVERLAY_FLATPAK" != 1 ] && ! command -v mangohud >/dev/null 2>&1; then
    exec "$@"
fi
mkdir -p "$VITALUX_OVERLAY_SESSIONS" || exec "$@"
VITALUX_SESSION_DIR="$(mktemp -d "$VITALUX_OVERLAY_SESSIONS/session.XXXXXXXXXX")" || exec "$@"
cp "$VITALUX_OVERLAY_META" "$VITALUX_SESSION_DIR/game.json" || exec "$@"
cp "$VITALUX_OVERLAY_CONFIG" "$VITALUX_SESSION_DIR/overlay.conf" || exec "$@"
printf '\noutput_folder=%s\n' "$VITALUX_SESSION_DIR" >> "$VITALUX_SESSION_DIR/overlay.conf"
date +%s > "$VITALUX_SESSION_DIR/started"
printf '%s\n' "$$" > "$VITALUX_SESSION_DIR/owner.pid"
cp "/proc/$$/stat" "$VITALUX_SESSION_DIR/owner.stat" 2>/dev/null || :
export VITALUX_GAME_SESSION="$VITALUX_SESSION_DIR"
export MANGOHUD_CONFIGFILE="$VITALUX_SESSION_DIR/overlay.conf"
# A launcher's global string would override the dedicated profile file.
unset MANGOHUD_CONFIG
if command -v mangohud >/dev/null 2>&1; then
    mangohud --dlsym "$@"
else
    # Flatpak's Vulkan-layer extension is activated through its environment.
    MANGOHUD=1 "$@"
fi
VITALUX_GAME_EXIT="$?"
printf '%s\n' "$VITALUX_GAME_EXIT" > "$VITALUX_SESSION_DIR/exit-code"
date +%s > "$VITALUX_SESSION_DIR/finished"
exit "$VITALUX_GAME_EXIT"
