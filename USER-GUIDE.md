# Vitalux user guide

## Start

Use the latest AppImage or extract the complete Linux ZIP and run `bash run.sh`. The source ZIP includes a compressed runtime too. Run `bash Portable-pruefen.sh` if a component cannot load. Keep the extracted program in its own writable folder.

## Monitor your system

The sidebar opens Overview, Processor, Graphics, Memory, Drives, Network, Sensors, Diagnostic Center, System, Settings, Updates and About. The new vector symbols remain recognizable when the sidebar is collapsed. Charts show real history; missing sensors are never replaced with invented readings.

Use **Edit layout** on Overview to arrange cards. Drives loads SMART data asynchronously. Start disk benchmarks or external diagnostics only when needed; writing tests temporarily create files on the selected drive.

## Themes and backgrounds

Choose one of ten preview tiles in **Settings → Appearance**. The transition preserves your page, scroll position and running measurements. Logos, sidebar text and symbols share the effective palette.

Obsidian Gold, Champagne Glass, Black Glass Gold and Aurora Gold use fixed palettes and backgrounds. Their grey dropdowns remain openable: the explanation appears inside, above unavailable options. Holographic also has a fixed HUD background. Personal accent and background selections remain saved for compatible themes.

The original wordmark has a subtle metallic reflection; outer logo bands rotate slowly. **Animations** provides smooth, reduced and off profiles. **Ultra Eco** uses a simple skin, CPU rendering and a ten-second sampling interval, preserving the previous appearance settings for later.

## Search and sound

Click the magnifier in Settings. Search grows with the text, adapts to the available width and shows matching settings. Choose a result to jump to its control. Open, close and interrupted transitions remain smooth. Escape, an outside click or five idle seconds closes the field.

**Glass sound on clicks** applies only to Vitalux buttons, including keyboard activation. Adjust **Volume** or switch it off. It does not monitor other applications or make empty-space clicks audible. Desktop audio uses PulseAudio or PipeWire's PulseAudio-compatible service.

## Graphics and MiniHUD

CPU rendering is the stable default. Experimental OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan profiles depend on working drivers and a suitable session. Apply a renderer change with **Restart now**. A failed startup falls back to CPU. X11 and Wayland select a window-system plugin; they do not change your desktop login session.

MiniHUD reuses the main sensor stream and offers three layouts and adjustable opacity. Your desktop compositor determines its placement relative to fullscreen applications.

## Language and updates

Use **DE / EN** at the bottom of the sidebar. Labels, the native guide, update notes and offline changelog follow the selected language without interrupting monitoring.

Vitalux checks the official release at startup and about every six hours. Read the current-language notes in **Updates**, then choose **Install update**. The full archive/AppImage and checksum must be available. AppImage replacement is atomic; a ZIP installation keeps its previous version for rollback. Personal data and settings are retained.

The full release ZIP includes Python/Qt. Manual delta ZIPs are only for overlaying the immediately preceding portable ZIP version, never for AppImages. Keep a backup before a manual overlay.

## Troubleshooting

Normal settings: `${XDG_CONFIG_HOME:-~/.config}/vitalux`. Logs: `${XDG_STATE_HOME:-~/.local/state}/vitalux`. Diagnostic Center exports local reports; **About → Guide** opens the translated tour.

Explicit `Designs-testen.sh` previews keep their separate `design-test-data/` profile and disable releases. Use the normal stable `run.sh` or AppImage for update-enabled operation.
