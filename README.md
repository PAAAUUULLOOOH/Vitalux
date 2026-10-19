<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/vitalux-readme-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/vitalux-readme-light.svg">
    <img src="assets/vitalux-readme-light.svg" alt="Vitalux — Linux system monitor" width="285">
  </picture>
</p>

<p align="center">A native Linux system monitor with live telemetry, glass themes and hardware diagnostics.</p>
<p align="center"><a href="https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest"><strong>Download the latest release</strong></a> · <a href="USER-GUIDE.md">User guide</a> · <a href="CHANGELOG.en.md">Changelog</a></p>

![Vitalux: a real Qt dashboard with live measurements](assets/vitalux-dashboard-preview.png)

### Features

- Live CPU, GPU, RAM, disks, network and Linux hardware sensors.
- Ten theme previews, frosted glass, coordinated palettes and animated original branding.
- Smooth appearance transitions, adaptive settings search and optional glass button sounds.
- Rearrange dashboard cards; use MiniHUD, alerts, SMART information and the Diagnostic Center.
- German and English UI, guide and release history; switch language in the sidebar.
- CPU rendering by default, optional OpenGL/X11/Wayland/Vulkan profiles and Ultra Eco.
- Verified release updates, installation backup and rollback support.

### Install or run

**Linux x86-64**, a Wayland or X11 desktop and working system graphics drivers are required. Python and Qt are bundled; no pip installation is needed.

**AppImage:** download the `.AppImage` from [Releases](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest), then:

```bash
chmod +x Vitalux-*.AppImage
./Vitalux-*.AppImage
```

The first-run dialog can add Vitalux to your application menu. Use `--portable` to run without integration. If AppImage/FUSE is unavailable, use the full ZIP.

**Full ZIP:** extract the entire `linux-x86_64.zip` into its own writable folder, then run:

```bash
bash run.sh
```

**Code → Download ZIP also works:** its included runtime is verified and unpacked on first launch. Keep all files together. `Portable-pruefen.sh` reports missing components or libraries.

### Appearance and controls

Select themes directly from **Settings → Appearance**. Obsidian Gold, Champagne Glass, Black Glass Gold and Aurora Gold have fixed palettes and backgrounds. Open their grey dropdowns to read the restriction. Holographic has its own fixed HUD background. Other themes retain your personal colors and images.

Search settings with the magnifier: the field expands to fit the text, remains above scrolling content and closes after five idle seconds, Escape or a click outside. Reduced/off animation settings and Ultra Eco are respected. Button sounds stay inside Vitalux and have volume/mute controls.

### Updates, data and diagnostics

Vitalux checks its official GitHub releases at startup and every six hours. **Updates** shows release notes in the current UI language before installation. AppImages are replaced atomically; ZIP installations keep a backup for recovery. Checksums are verified before applying an update.

Normal preferences use XDG locations under `~/.config/vitalux`; logs use `~/.local/state/vitalux`. Explicit `Designs-testen.sh` previews use `design-test-data/` beside the app and disable updates.

Sensor availability depends on hardware, kernel, drivers and permissions. Unavailable readings remain unavailable. Stress tests and external diagnostics require an explicit action. See the [user guide](USER-GUIDE.md) and the in-app **About → Guide**.

### Development and releases

Use Python 3.12 with `PySide6==6.12.0` and `psutil==7.2.2`. Run standalone checks with `python scripts/run-regressions.py`. `scripts/check-graphics-startup.py` additionally needs reachable X11 and Wayland test displays.

Release versions advance from `.0` through `.9`, then increment the preceding component: `0.9.5.9 → 0.9.6.0`. A release requires matching German/English changelogs and a successful guarded build on `main`.
