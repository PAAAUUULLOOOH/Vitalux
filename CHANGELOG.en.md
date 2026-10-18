# Vitalux – Changelog

The new GitHub repository starts at **v0.9.4.0**. Older release history
is intentionally not imported. All previously implemented features remain.

## [v0.9.4.0] - 2026-10-18
- New GitHub repository with a fresh commit and release history while preserving the complete Vitalux application and design.
- New version policy: v0.9.4.0 through v0.9.4.9, then v0.9.5.0. Official releases require manual approval.
- Preserved the overview of key components and detailed CPU, graphics, memory, storage, network and sensor pages.
- Preserved Vitalux Insights: Performance Detective, Gaming Session Analyzer, event timeline, before/after comparison, clickable hardware overview and focus mode.
- GPU monitoring remains read-only; compact accent dropdown, themes, translations and local reports remain available.
- Kept crash logs, optimized telemetry history, the native Qt interface and existing recovery mechanisms.
- Updated GitHub workflow for initial release from an archived runtime and subsequent releases; no automatic release on ordinary code changes.

### In development – Holographic
- New native **Holographic** theme with opaque custom-drawn HUD cards, technical sidebar, grid backdrop, custom charts, gauges, navigation and controls.
- No glass or frosted blur effects in Holographic, including OpenGL and Qt Quick. Glass with Vitalux Blue remains the default.

- Restored separate **Black Glass Gold** theme with fixed light gold styling for widgets, graphs, icons and logo; accent selection disabled while active.
- Prevent duplicated options and repeated release entries in tab selectors; bundled Qt/Python runtime retained for portable ZIP and AppImage.
