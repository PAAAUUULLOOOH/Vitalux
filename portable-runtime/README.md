# Offline Linux x86-64 runtime

The checked-in `vitalux-linux-x86_64.tar.xz` contains CPython 3.12.16, PySide6/Qt 6.12.0, psutil 7.2.2, portable shared libraries, fio 3.43 and complete retained license notices. `SHA256SUMS` pins the archive. The launcher verifies and extracts it locally; no Python installation, pip download or administrator permission is required.

The runtime originates from the verified official Vitalux package. Unused Qt compiler/Lottie/vector-image modules and nonfunctional optional PDF/virtual-keyboard plugins have been removed. libaio 0.3.113 is rebuilt from the checksum-locked unmodified source documented in `third_party/sources.lock.json`. The runtime supports CPU and X11/OpenGL. The retired standalone OpenGL-widget binding/library and Wayland Vulkan plugin are removed; Qt Quick/QML remain required for X11/OpenGL, while native Wayland support remains available for CPU rendering.

License texts and the exact fio build source are extracted under `licenses/`. Other corresponding sources, source checksums and rebuild instructions are provided separately with each release; see [THIRD-PARTY.md](../THIRD-PARTY.md).

`mangohud-0.8.4-linux-x86.tar.xz` is a separate, checksum-locked 32/64-bit game-overlay runtime. `mangohud.json` pins its source, payload identity and archive digest. Packaging expands it into `mangohud-runtime/`; source launches install it locally on first game setup. No system MangoHud command, Flatpak extension or runtime download is needed. Build recipes are in `packaging/Dockerfile.mangohud`, `packaging/build-mangohud.sh` and `scripts/build-mangohud-archive.py`.

`desktop-libraries-linux-x86_64.tar.xz` adds the checksum-locked GLib/thread and actual Qt/Python desktop dependency closure. Its Ubuntu 22.04 packages avoid newer build-host ABI requirements in the formerly bundled X11 libraries. This does not bundle GPU drivers or replace the stated whole-application glibc requirement. Source launches also install the supplement over an already-extracted runtime. Libraries, binary-package URLs and hashes are recorded in `licenses/system-libraries/desktop-libraries.json`; the separate SHA-256 file verifies offline extraction.

Reproduce the supplement on a Debian/Ubuntu build host with `python3 scripts/build-desktop-libraries.py --output build/desktop-libraries-linux-x86_64.tar.xz`. Only locked runtime libraries and copyright notices are copied from the verified packages; development files and graphics-driver payloads are excluded. The source manifest lists the exact corresponding upstream archives, distribution patches and source descriptors for the separate release source download.

Systemd, OpenSSL, SQLite, Wayland client/cursor and DRM interfaces prefer the desktop’s installed libraries, preserving compatibility with newer graphics drivers. Verified offline copies are held separately under `fallback-libraries/` and selected only when the host interface is absent.

## Dependency maintenance

Each authorized Unstable release checks stable PyPI versions, the supported CPython 3.12 patch line, compiled upstream releases, and signed Ubuntu 22.04 update/security metadata. Compatible Python/Qt/psutil and baseline-library candidates are rebuilt with matching source locks, licenses and SHA-256 files before the complete package validation. Newly compiled upstream ABI families are reported for review; they are not substituted into a prebuilt Qt or AppImage runtime. Stable verifies currency without modifying Main. The build report records candidates and active PyPI advisories; unavailable metadata fails the check.

Run `python scripts/dependency_audit.py --ubuntu --output build/dependencies/audit.json`, then `python scripts/update_dependencies.py --report build/dependencies/audit.json` on an Ubuntu build host with Docker. CPython is built from its locked source using `packaging/Dockerfile.cpython`; the matching native dependency closure is recorded and included in the signed baseline supplement. `scripts/runtime_inventory.py` verifies the actual interpreter, Qt, bindings and psutil against the declared versions. Binary releases omit these development tools; rebuild recipes are included in the separate source download.

Source starts compare `.runtime/core-runtime.sha256` with the supplied archive lock. A changed verified archive replaces the old core; unchanged cores retain the fast path. Corrupt input leaves the previous working interpreter in place.
