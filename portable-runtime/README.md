# Offline Linux x86-64 runtime

The checked-in `vitalux-linux-x86_64.tar.xz` contains CPython 3.12.7, PySide6/Qt 6.12.0, psutil 7.2.2, portable shared libraries, fio 3.43 and complete retained license notices. `SHA256SUMS` pins the archive. The launcher verifies and extracts it locally; no Python installation, pip download or administrator permission is required.

The runtime originates from the verified official Vitalux package. Unused Qt compiler/Lottie/vector-image modules and nonfunctional optional PDF/virtual-keyboard plugins have been removed. libaio 0.3.113 is rebuilt from the checksum-locked unmodified source documented in `third_party/sources.lock.json`. These changes preserve the supported desktop rendering modes.

License texts and the exact fio build source are extracted under `licenses/`. Other corresponding sources, source checksums and rebuild instructions are provided separately with each release; see [THIRD-PARTY.md](../THIRD-PARTY.md).
