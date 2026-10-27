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
export MANGOHUD_OPENGL_LIBS=libVitaluxMangoHud_opengl.so
VITALUX_LAYER_PATH="$VITALUX_MANGO_ENGINE/layers"
if [ -n "${VK_LAYER_PATH-}" ]; then
    VITALUX_LAYER_PATH="$VITALUX_LAYER_PATH:$VK_LAYER_PATH"
else
    VITALUX_LAYER_PATH="$VITALUX_LAYER_PATH:${XDG_CONFIG_HOME:-$HOME/.config}/vulkan/explicit_layer.d:/etc/xdg/vulkan/explicit_layer.d:/etc/vulkan/explicit_layer.d"
    VITALUX_OLD_IFS=$IFS
    IFS=:
    for directory in "${XDG_DATA_HOME:-$HOME/.local/share}" ${XDG_DATA_DIRS:-/usr/local/share:/usr/share}; do
        VITALUX_LAYER_PATH="$VITALUX_LAYER_PATH:$directory/vulkan/explicit_layer.d"
    done
    IFS=$VITALUX_OLD_IFS
fi
export VK_LAYER_PATH="$VITALUX_LAYER_PATH"
case ":${VK_INSTANCE_LAYERS-}:" in
    *:VK_LAYER_VITALUX_MANGOHUD_overlay:*) ;;
    *) export VK_INSTANCE_LAYERS="${VK_INSTANCE_LAYERS:+$VK_INSTANCE_LAYERS:}VK_LAYER_VITALUX_MANGOHUD_overlay" ;;
esac
# The private explicit layer prevents duplicate activation of an installed HUD.
unset MANGOHUD
case "$*" in
    *cs2.sh*|*RiseOfTheTombRaider.sh*) ;;
    *) case ":${LD_PRELOAD-}:" in
           *:libVitaluxMangoHud_shim.so:*) ;;
           *) export LD_PRELOAD="${LD_PRELOAD:+$LD_PRELOAD:}libVitaluxMangoHud_shim.so" ;;
       esac ;;
esac
exec "$@"
