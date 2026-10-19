# Vitalux release and recovery guide

The current repository is already initialized. Normal updates do not require deleting or renaming any repository.

- User instructions: [USER-GUIDE.md](USER-GUIDE.md).
- Run the complete ZIP with `bash run.sh`, or use the release AppImage.
- Graphics changes use the explicit **Restart now** control; failed GPU startup returns to CPU rendering.
- Release versions advance `.0` through `.9`, then carry into the preceding component.
- Update both changelogs and `vitalux/__init__.py` before an authorized release.
- The guarded publication workflow validates the next version, runtime checksum, regressions, package startup and installation before creating release assets.
- The built-in updater uses verified complete archives or atomic AppImage replacement. ZIP backups support recovery without deleting user data.
