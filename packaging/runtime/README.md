# Pinned AppImage runtime

`runtime-x86_64` is the unmodified 944,632-byte type-2 runtime from AppImage commit `fedfad51acc2860b2916a1eef32ba4a500ff31ef`. It was extracted from the SHA-256-verified official Vitalux v0.9.5.5 AppImage. `SHA256SUMS` pins its exact bytes; the build verifies this file before embedding it.

License and statically linked component notices: [THIRD-PARTY.md](../../THIRD-PARTY.md). Exact source/build scripts and the matching libfuse/squashfuse sources are supplied in the release's third-party source download. The runtime's version can be checked with `./runtime-x86_64 --appimage-version`.
