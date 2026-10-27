#!/bin/bash
# Isolated CI probe app: existing platform/graphics runtimes, no MangoHud extension.
set -euo pipefail
MANGO_TEST_OUTPUT="$(realpath "$1")"
MANGO_TEST_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANGO_TEST_APP=io.github.vitalux.OverlayProbe
MANGO_TEST_PLATFORM=26.08
mkdir -p "$MANGO_TEST_OUTPUT"
flatpak --user remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak --user install --noninteractive -y flathub \
    "org.freedesktop.Platform//$MANGO_TEST_PLATFORM" \
    "org.freedesktop.Platform.Compat.i386//$MANGO_TEST_PLATFORM" \
    "org.freedesktop.Platform.GL32.default//$MANGO_TEST_PLATFORM"
flatpak --user list --runtime --columns=application > "$MANGO_TEST_OUTPUT/runtime-list.txt"
if grep -i MangoHud "$MANGO_TEST_OUTPUT/runtime-list.txt"; then
    echo 'The sandbox test must not have a MangoHud extension installed' >&2
    exit 1
fi
MANGO_TEST_BUILD="$MANGO_TEST_OUTPUT/app"
mkdir -p "$MANGO_TEST_BUILD/files/bin" "$MANGO_TEST_BUILD/files/etc" \
    "$MANGO_TEST_BUILD/files/lib/i386-linux-gnu/GL"
cp "$MANGO_TEST_ROOT/build/game-recording/graphics-probe64" "$MANGO_TEST_BUILD/files/bin/overlay-probe64"
cp "$MANGO_TEST_ROOT/build/game-recording/graphics-probe32" "$MANGO_TEST_BUILD/files/bin/overlay-probe32"
cat > "$MANGO_TEST_BUILD/files/bin/with-compat" <<'COMPAT'
#!/bin/sh
export LD_LIBRARY_PATH="/app/lib/i386-linux-gnu:/app/lib/i386-linux-gnu/GL/default/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$@"
COMPAT
chmod 755 "$MANGO_TEST_BUILD/files/bin/with-compat"
printf '%s\n' '/app/lib/i386-linux-gnu' '/app/lib/i386-linux-gnu/GL/default/lib' > "$MANGO_TEST_BUILD/files/etc/ld.so.conf"
cat > "$MANGO_TEST_BUILD/metadata" <<META
[Application]
name=$MANGO_TEST_APP
runtime=org.freedesktop.Platform/x86_64/$MANGO_TEST_PLATFORM
sdk=org.freedesktop.Platform/x86_64/$MANGO_TEST_PLATFORM
command=overlay-probe64

[Context]
shared=ipc;
sockets=x11;
devices=dri;

[Extension org.freedesktop.Platform.Compat.i386]
directory=lib/i386-linux-gnu
version=$MANGO_TEST_PLATFORM

[Extension org.freedesktop.Platform.GL32]
directory=lib/i386-linux-gnu/GL
version=1.4
versions=$MANGO_TEST_PLATFORM;$MANGO_TEST_PLATFORM-extra;1.4;
subdirectories=true
no-autodownload=true
add-ld-path=lib
merge-dirs=vulkan/icd.d;glvnd/egl_vendor.d;lib/dri;
download-if=active-gl-driver
META
flatpak build-finish --allow=multiarch "$MANGO_TEST_BUILD"
flatpak build-export "$MANGO_TEST_OUTPUT/repo" "$MANGO_TEST_BUILD"
flatpak --user remote-add --if-not-exists --no-gpg-verify vitalux-overlay-probe "file://$MANGO_TEST_OUTPUT/repo"
flatpak --user install --noninteractive -y vitalux-overlay-probe "$MANGO_TEST_APP"
python "$MANGO_TEST_ROOT/scripts/check-game-recording.py" --output "$MANGO_TEST_OUTPUT/recording" \
    --probe64 /app/bin/overlay-probe64 --probe32 /app/bin/overlay-probe32 \
    --loader32 /app/lib/i386-linux-gnu/ld-linux.so.2 --flatpak-app "$MANGO_TEST_APP" --short
