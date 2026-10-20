# Vitalux user guide

## Start

Use the latest AppImage or extract the complete Linux ZIP and run `bash run.sh`. The source ZIP includes a compressed runtime too. Run `bash Portable-pruefen.sh` if a component cannot load. Keep the extracted program in its own writable folder.

## Monitor your system

Reopening a sidebar category returns to its page start. The sidebar opens Overview, Processor, Graphics, Memory, Drives, Network, Sensors, Diagnostic Center, System, Settings, Updates and About. The new vector symbols remain recognizable when the sidebar is collapsed. Charts distinguish series by line pattern and identify measurements and timestamps on hover. Sampling interruptions appear as gaps; missing sensors are never replaced with invented readings.

Use **Edit layout** on Overview to arrange cards. Drives loads SMART data asynchronously. Start disk benchmarks or external diagnostics only when needed; writing tests temporarily create files on the selected drive.

## Themes and backgrounds

**Obsidian Gold is the default** for new profiles and restored appearance defaults; saved themes are retained. Choose one of ten preview tiles in **Settings → Appearance**. The transition preserves your page, scroll position and running measurements. Logos, sidebar text and symbols share the effective palette.

Obsidian Gold, Champagne Glass, Black Glass Gold and Aurora Gold use fixed palettes and backgrounds. Their grey fields are disabled and cannot be opened. Holographic also has a fixed HUD background. Personal accent and background selections remain saved for compatible themes.

The accent selector has a compact glass color swatch. Enable **Compact system header on Overview** to leave more room for charts. Theme previews gently enlarge on hover without moving surrounding tiles. The original wordmark has a slow, clearly visible satin reflection; outer logo bands rotate slowly around a softly traced heartbeat waveform. **Animations** provides smooth, reduced and off profiles. **Ultra Eco** uses a simple skin, CPU rendering and a ten-second sampling interval, preserving the previous appearance settings for later.

## Search and sound

Click the magnifier in Settings. Search grows with the text, adapts to the available width and shows matching settings. Clear predictions glide to the control automatically while you keep typing. Choose a result to focus its control; the search field then remains visible for five seconds and closes smoothly. Open, close and interrupted transitions remain smooth. Escape, an outside click or five idle seconds closes the field.

**Glass sound on clicks** gives buttons, selections and opening dropdowns a short crystal sound, including keyboard activation. Adjust **Volume** or switch it off. It stays within Vitalux. A closed dropdown ignores the mouse wheel, so page scrolling cannot accidentally change a setting. Desktop audio uses PulseAudio or PipeWire's PulseAudio-compatible service.

## Graphics and MiniHUD

**Advanced settings** is near the bottom of Settings, directly above the full **Restore defaults** button. Click its header to expand or collapse it smoothly; the page follows expansion so the revealed controls become visible. It contains graphics rendering and **Maintenance** (clear Vitalux caches or reset personal preferences). Searching for these controls opens the card automatically.

CPU rendering is the stable default. Experimental OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan profiles depend on working drivers and a suitable session. Apply a renderer change with **Restart now**. Closing and restarting retain a responsive window until background work finishes safely. A failed startup falls back to CPU. X11 and Wayland select a window-system plugin; they do not change your desktop login session.

MiniHUD reuses the main sensor stream and offers three layouts and adjustable opacity. Your desktop compositor determines its placement relative to fullscreen applications.

## Reset settings

Section reset buttons softly appear when values differ from defaults and softly disappear after a reset. They apply only to their own section and do not restart Vitalux. The full **Restore defaults** button is the final item in Settings and restarts the app so graphics defaults take effect. A running benchmark, diagnostic or update prevents a full reset until it finishes; settings are not deleted in that case. **Delete personal preferences** in Maintenance also restarts the app after a successful deletion.

## Language and updates

Use **DE / EN** at the bottom of the sidebar. Labels, the native guide, update notes and offline changelog follow the selected language without interrupting monitoring.

Vitalux checks the official release at startup and about every six hours. Read the current-language notes in **Updates**, then choose **Install update**. The full archive/AppImage and checksum must be available. AppImage replacement is atomic; a ZIP installation keeps its previous version for rollback. Personal data and settings are retained. Updates check free space before staging files and report interrupted downloads; a failed download does not replace the installed application.

The full release ZIP includes Python/Qt. Manual delta ZIPs are only for overlaying the immediately preceding portable ZIP version, never for AppImages. Keep a backup before a manual overlay.

## Troubleshooting

Normal settings: `${XDG_CONFIG_HOME:-~/.config}/vitalux`. Logs: `${XDG_STATE_HOME:-~/.local/state}/vitalux`. Diagnostic Center exports local reports; **About → Guide** opens the translated tour.

Explicit `Designs-testen.sh` previews keep their separate `design-test-data/` profile and disable releases. Use the normal stable `run.sh` or AppImage for update-enabled operation.
