# Vitalux user guide

## Start

Use the latest AppImage or extract the complete Linux ZIP and run `bash run.sh`. The source ZIP includes a compressed runtime too. Run `bash Portable-pruefen.sh` if a component cannot load. Keep the extracted program in its own writable folder.

## Monitor your system

Reopening a sidebar category returns to its page start. The sidebar opens Overview, Processor, Graphics, Memory, Drives, Network, Sensors, Diagnostic Center, System, Settings, Updates and About. The new vector symbols remain recognizable when the sidebar is collapsed. Charts distinguish series by line pattern and identify measurements and timestamps on hover. Sampling interruptions appear as gaps; missing sensors are never replaced with invented readings.

Use **Edit layout** on Overview to arrange cards. Drives loads SMART data asynchronously. Start disk benchmarks or external diagnostics only when needed; writing tests temporarily create files on the selected drive.

## Designs and backgrounds

**Obsidian Gold is the default** for new profiles and restored appearance defaults; saved designs are retained. Choose one of twelve preview tiles under **Settings → Appearance → Design**. The transition preserves your page, scroll position and running measurements. Logos, sidebar text and symbols share the effective palette.

Obsidian Gold, Champagne Glass, Black Glass Gold, Aurora Gold, **Aether Glass** and **Eclipse Crystal** use fixed palettes and backgrounds. Their grey **Fixed design palette** and **Fixed background** fields cannot be opened. Aether Glass combines platinum and violet/cyan optical glass with floating navigation. Eclipse Crystal uses faceted black crystal, champagne edges, top category navigation and a bottom bar for System, Settings, Updates, About and language. Its top navigation scrolls on narrow windows. Holographic also has a fixed HUD background. Personal accent and background selections remain saved for compatible themes.

The accent selector has a compact glass color swatch. Overview uses a compact system header by default, keeping system details visible while leaving more room for charts. Theme previews gently enlarge on hover without moving surrounding tiles. The sculpted uppercase **VITALUX** wordmark has coordinated metal and smoked-glass facets with a moving reflection. Slimmer outer logo bands rotate slowly around a clear heartbeat impulse on a darker base line. Rotation, heartbeat and lettering reflections repeat continuously and keep their phase when the theme changes. Each gold collection has its own coordinated logo and wordmark; preset and custom accent colors remain supported, with a modestly richer finish on the circle for custom colors. **Animations** provides smooth, reduced and off profiles. **Ultra Eco** uses a simple skin, CPU rendering and a ten-second sampling interval, preserving the previous appearance settings for later.

## Apps and network connections

Open **Network → Apps & connections** to start the session monitor. Select an application to inspect its process IDs, executable path and TCP/UDP destinations. Running applications without current connections are also listed. Filter by name or path and sort by transfer rate or recorded usage. Connection details remain collapsed until needed. Totals cover the observed measurement session, not historical usage before Vitalux started. **Reset measurement** resets totals and warnings without changing active blocks.

The normal view uses Linux TCP diagnostics. UDP counters, inaccessible processes and unavailable kernel data remain unknown rather than being inferred from interface totals. Some containers expose connections but no per-socket byte counters. **Partial** means not all of an application's traffic could be measured.

**Authorize full measurement** sets up an isolated root-owned helper through Polkit, then requests authorization to use it. This optional feature needs cgroup v2, Linux cgroup BPF support, Polkit (`pkexec`) and `/usr/bin/python3` on the host. The portable app itself still includes Python and runs without a system Python installation. Full mode measures TCP/UDP IP bytes, including protocol headers; changing measurement modes starts new totals because TCP payload and IP-byte counters are different measurements. No packet payload is captured.

Use **Block** or **Unblock** directly beside an application, or select it and use **Block network access** / **Allow network access**. Blocking requests Polkit authorization directly when needed; the status shows pending actions and errors. Select an application and expand **Advanced connections** to inspect its sockets. Select a TCP/UDP socket and use **Block connection** / **Unblock connection** to control that socket in both directions. An application-wide block takes priority over an individual socket rule. Blocks cover its running processes, grouped by executable; programs using the same interpreter can share an executable. They last for the authorized session. **Release all blocks**, **End authorization**, closing Vitalux, or helper termination releases them. This is session traffic control, not a persistent firewall policy across reboots. Newly launched instances are discovered as the helper refreshes; treat blocks as controls for the running processes, not as a security boundary against hostile software.

**Usage warning** sets an observed-traffic threshold in MiB for each application (0 disables it). Vitalux shows the warning once per measurement session; reset measurement to start again. **Look up hostnames** explicitly asks the system resolver for PTR records. A PTR hostname does not verify who operates a destination.

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

Use **DE / EN** in the navigation area (bottom bar in Eclipse Crystal). Labels, the native guide, update notes and offline changelog follow the selected language without interrupting monitoring.

Vitalux checks the official release at startup and about every six hours. Read the current-language notes in **Updates**, then choose **Install update**. The full archive/AppImage and checksum must be available. AppImage replacement is atomic; a ZIP installation keeps its previous version for rollback. Personal data and settings are retained. Updates check free space before staging files and report interrupted downloads; a failed download does not replace the installed application.

The full release ZIP includes Python/Qt. Manual delta ZIPs are only for overlaying the immediately preceding portable ZIP version, never for AppImages. Keep a backup before a manual overlay.

## Troubleshooting

Normal settings: `${XDG_CONFIG_HOME:-~/.config}/vitalux`. Logs: `${XDG_STATE_HOME:-~/.local/state}/vitalux`. Diagnostic Center exports local reports; **About → Guide** opens the translated tour.

Explicit `Designs-testen.sh` previews keep their separate `design-test-data/` profile and disable releases. Use the normal stable `run.sh` or AppImage for update-enabled operation.

## Update channels and profiles

Open **Updates → Update channel** and select **Stable** or **Unstable**. The installed version and active channel remain visible. Review the destination version and its changes, then use **Switch to Unstable** or **Return to Stable**. Switching verifies the package, backs up profiles and restarts Vitalux; returning to an older stable package is supported.

Stable retains your existing preferences. Unstable creates its own settings profile on first launch by copying Stable's preferences and imported backgrounds. Later switches retain each channel's configuration, caches and diagnostic data. **Import settings** transfers compatible preferences with a backup and CPU-rendered restart. **Fresh test profile** resets only the test profile. Backups precede format migrations and are kept locally (the latest five per channel).

Test versions use names such as `v0.9.6.1-unstable.1`. A single rolling **Unstable — current test build** prerelease supplies the latest test package across development cycles. GitHub's **Latest** download remains Stable. Test packages can change frequently; the previous test package in the rolling entry is replaced. Download the full ZIP or AppImage from that entry when installing manually.

On/off controls use themed switches throughout the interface. Multiple-selection controls retain checkmarks. Design previews form the same multi-row grid in every design; hover or keyboard focus reveals a color wheel for accents and an image indicator for backgrounds. Grey locks mark fixed options; Black Glass allows accent presets but locks custom colors. Ultra Eco can temporarily restrict customization. The softer click sound defaults to 50% and can be adjusted or muted in Settings.
