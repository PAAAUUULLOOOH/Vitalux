#!/bin/sh
# Run in Dockerfile.mangohud; source is the checksum-locked complete upstream tar.
set -eu
export SOURCE_DATE_EPOCH=1760000000
# GCC 9 predates __has_builtin. Meson already probes the actual intrinsic;
# the fallback only makes the vendored Mesa preprocessor guard portable.
python3 - <<'PYCOMPAT'
from pathlib import Path
path=Path('src/mesa/util/macros.h')
text=path.read_text()
needle='#include "../c11_compat.h"\n'
assert needle in text
text=text.replace(needle,needle+'#ifndef __has_builtin\n#define __has_builtin(x) 0\n#endif\n',1)
path.write_text(text)
PYCOMPAT
for bits in 64 32; do
    cross=''
    if [ "$bits" = 32 ]; then
        export CC='gcc -m32' CXX='g++ -m32'
        export PKG_CONFIG_LIBDIR=/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig
        machine=i386-linux-gnu
        cross=--cross-file=/src/vitalux-i386.ini
    else
        export CC=gcc CXX=g++
        export PKG_CONFIG_LIBDIR=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig
        machine=x86_64-linux-gnu
    fi
    reconfigure=''
    if [ -f "build$bits/build.ninja" ]; then reconfigure=--reconfigure; fi
    meson setup $reconfigure $cross "build$bits" --prefix=/usr --libdir="lib$bits" \
        -Dappend_libdir_mangohud=false -Dinclude_doc=false -Dmangoplot=disabled \
        -Dmangoapp=false -Dmangohudctl=false -Dtests=disabled \
        -Dcpp_link_args=-static-libgcc -Dc_link_args=-static-libgcc
    ninja -C "build$bits" -j2
    directory="/out/mangohud-runtime/lib$bits"
    mkdir -p "$directory"
    for library in "build$bits"/src/libMangoHud*.so; do
        name=${library##*/}
        private="libVitalux${name#lib}"
        cp "$library" "$directory/$private"
        strip --strip-unneeded "$directory/$private"
        patchelf --set-soname "$private" "$directory/$private"
    done
    for name in xkbcommon wayland-client ffi; do
        case "$name" in ffi) soname=libffi.so.7;; *) soname="lib$name.so.0";; esac
        private="libvitalux-mango-$name.so"
        cp -L "/usr/lib/$machine/$soname" "$directory/$private"
        strip --strip-unneeded "$directory/$private"
        patchelf --set-soname "$private" "$directory/$private"
        for library in "$directory"/*.so; do
            if patchelf --print-needed "$library" | grep -qx "$soname"; then
                patchelf --replace-needed "$soname" "$private" "$library"
            fi
        done
    done
    for library in "$directory"/*.so; do
        patchelf --set-rpath '$ORIGIN' "$library"
    done
done
mkdir -p /out/mangohud-runtime/licenses /out/mangohud-runtime/layers
cp LICENSE /out/mangohud-runtime/licenses/MangoHud-MIT.txt
mkdir -p /out/mangohud-runtime/licenses/mesa-utilities
cp -R src/mesa/. /out/mangohud-runtime/licenses/mesa-utilities/
# The NVML interface header carries a separate NVIDIA redistribution notice.
sed -n '1,/^ \*\//p' include/nvml.h > /out/mangohud-runtime/licenses/NVIDIA-NVML-interface.txt
for package in libxkbcommon0 libwayland-client0 libffi7 gcc-9-base; do
    cp -L "/usr/share/doc/$package/copyright" "/out/mangohud-runtime/licenses/$package-copyright.txt"
done
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /out/mangohud-runtime/build-packages.txt
find subprojects -type f \( -iname 'license*' -o -iname 'copying*' -o -iname 'ofl*' -o -iname '*.license.*' -o -path '*/LICENSES/*' \) \
    -exec sh -c 'for path do destination="/out/mangohud-runtime/licenses/upstream/$path"; mkdir -p "${destination%/*}"; cp "$path" "$destination"; done' sh {} +

# Validate ELF mappings for both architectures and load the 64-bit payload on
# this older glibc. The build host may not execute i386 binaries.
python3 - <<'PYABI'
import ctypes
from pathlib import Path
import struct
for path in Path('/out/mangohud-runtime').glob('lib*/*.so'):
    data=path.read_bytes()
    wide=data[4]==2
    offset=struct.unpack_from('<Q' if wide else '<I',data,32 if wide else 28)[0]
    size,count=struct.unpack_from('<HH',data,54 if wide else 42)
    for index in range(count):
        header=struct.unpack_from('<IIQQQQQQ' if wide else '<IIIIIIII',data,offset+index*size)
        if header[0]!=1:continue
        file_offset,address,alignment=(header[2],header[3],header[7]) if wide else (header[1],header[2],header[7])
        assert not alignment or file_offset%alignment==address%alignment,(path,header)
for name in ('libVitaluxMangoHud_shim.so','libVitaluxMangoHud_opengl.so','libVitaluxMangoHud.so'):
    ctypes.CDLL('/out/mangohud-runtime/lib64/'+name)
print('Both ELF architectures align; complete 64-bit overlay loads on glibc 2.31')
PYABI
