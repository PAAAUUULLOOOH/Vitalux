#!/bin/sh
# Relocatable engine; no host mangohud command, no global Vulkan installation.
set -eu
if [ "$#" -eq 0 ]; then exit 2; fi
if [ "$1" = --version ]; then printf '%s\n' 'Vitalux bundled MangoHud 0.8.4'; exit 0; fi
if [ "$1" = --dlsym ]; then shift; fi
VITALUX_MANGO_ENGINE=$(CDPATH= cd -- "${0%/*}" && pwd)
# Only MangoHud and uniquely named private helpers live in these directories.
# ld.so selects the matching ELF architecture; game/driver libraries are untouched.
export LD_LIBRARY_PATH="$VITALUX_MANGO_ENGINE/lib64:$VITALUX_MANGO_ENGINE/lib32${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export MANGOHUD_OPENGL_LIBS="$VITALUX_MANGO_ENGINE/lib64/libVitaluxMangoHud_opengl.so:$VITALUX_MANGO_ENGINE/lib32/libVitaluxMangoHud_opengl.so"
# Steam's pressure-vessel imports implicit Vulkan layers, then replaces the
# host's VK_LAYER_PATH and LD_LIBRARY_PATH. Publish only this game's private
# implicit layer through XDG instead of depending on those discarded paths.
export XDG_DATA_DIRS="$VITALUX_MANGO_ENGINE:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export VITALUX_MANGOHUD=1
export PRESSURE_VESSEL_FILESYSTEMS_RO="${PRESSURE_VESSEL_FILESYSTEMS_RO:+$PRESSURE_VESSEL_FILESYSTEMS_RO:}$VITALUX_MANGO_ENGINE"
# Keep an installed system MangoHud from activating beside our private layer.
unset MANGOHUD
case "$*" in
    *cs2.sh*|*RiseOfTheTombRaider.sh*) ;;
    *) VITALUX_MANGO_SHIM="$VITALUX_MANGO_ENGINE/\${LIB}/libVitaluxMangoHud_shim.so"
       case ":${LD_PRELOAD-}:" in
           *:"$VITALUX_MANGO_SHIM":*) ;;
           *) export LD_PRELOAD="${LD_PRELOAD:+$LD_PRELOAD:}$VITALUX_MANGO_SHIM" ;;
       esac ;;
esac
exec "$@"
