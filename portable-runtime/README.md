# Offline Linux x86-64 runtime

The checked-in `vitalux-linux-x86_64.tar.xz` contains CPython 3.12.7, PySide6/Qt 6.12.0, psutil 7.2.2, portable shared libraries, fio 3.43 and complete retained license notices. `SHA256SUMS` pins the archive. The launcher verifies and extracts it locally; no Python installation, pip download or administrator permission is required.

The runtime originates from the verified official Vitalux package. Unused Qt compiler/Lottie/vector-image modules and nonfunctional optional PDF/virtual-keyboard plugins have been removed. libaio 0.3.113 is rebuilt from the checksum-locked unmodified source documented in `third_party/sources.lock.json`. These changes preserve the supported desktop rendering modes.

License texts and the exact fio build source are extracted under `licenses/`. Other corresponding sources, source checksums and rebuild instructions are provided separately with each release; see [THIRD-PARTY.md](../THIRD-PARTY.md).

`mangohud-0.8.4-linux-x86.tar.xz` is a separate, checksum-locked 32/64-bit game-overlay runtime. `mangohud.json` pins its source, payload identity and archive digest. Packaging expands it into `mangohud-runtime/`; source launches install it locally on first game setup. No system MangoHud command, Flatpak extension or runtime download is needed. Build recipes are in `packaging/Dockerfile.mangohud`, `packaging/build-mangohud.sh` and `scripts/build-mangohud-archive.py`.

`desktop-libraries-linux-x86_64.tar.xz` adds the checksum-locked GLib/thread and actual Qt/Python desktop dependency closure. Its Ubuntu 22.04 packages avoid newer build-host ABI requirements in the formerly bundled X11 libraries. This does not bundle GPU drivers or replace the stated whole-application glibc requirement. Source launches also install the supplement over an already-extracted runtime. Libraries, binary-package URLs and hashes are recorded in `licenses/system-libraries/desktop-libraries.json`; the separate SHA-256 file verifies offline extraction.

Reproduce the supplement on a Debian/Ubuntu build host with `python3 scripts/build-desktop-libraries.py --output build/desktop-libraries-linux-x86_64.tar.xz`. Only locked runtime libraries and copyright notices are copied from the verified packages; development files and graphics-driver payloads are excluded. The source manifest lists the exact corresponding upstream archives, distribution patches and source descriptors for the separate release source download.
