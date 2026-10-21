# Vitalux user guide

## Start

Use the latest AppImage or extract the complete Linux ZIP and run `bash run.sh`. The source ZIP includes a compressed runtime too. Run `bash Portable-pruefen.sh` if a component cannot load. Keep the extracted program in its own writable folder.

## Monitor your system

Current Vitalux editions allow one running instance per user, shared across ZIP/AppImage copies and Stable/Unstable profiles. A genuine second start shows “Vitalux is already running.” During a marked restart, a short overlap waits for the old process to finish; a prolonged restart shows a restart-specific notice. Closing to the tray keeps that instance active; use **Exit** to quit. The lock is released automatically when the process exits or crashes, and normal renderer/update restarts remain supported. Older editions without this protection must be closed before opening another edition.

Reopening a sidebar category returns to its page start. The sidebar opens Overview, Processor, Graphics, Memory, Drives, Network, Sensors, Diagnostic Center, System, Settings, Updates and About. The new vector symbols remain recognizable when the sidebar is collapsed. Charts distinguish series by line pattern and identify measurements and timestamps on hover. Sampling interruptions appear as gaps; missing sensors are never replaced with invented readings.

Use **Edit layout** on Overview to arrange cards. Drives loads SMART data asynchronously. Start disk benchmarks or external diagnostics only when needed; writing tests temporarily create files on the selected drive.

## Designs and backgrounds

**Obsidian is the default**, with the original Obsidian Gold colors, smoked-glass materials, background and continuously animated logo. The change is a name change; new profiles and appearance resets retain its gold look. Choose among nine actual surface designs in **Settings → Design**. Black Glass Gold is renamed **Black Glass** and replaces the former Black Glass surface. Champagne Glass, Aurora Gold and Liquid Silver are combined into Obsidian; their backgrounds and colors remain available separately.

The controls are separated into three cards:

- **Design:** surface geometry and materials. Aether Glass retains floating navigation and optical instruments; Eclipse Crystal retains faceted surfaces, top navigation and a bottom utility bar. The remaining surface styles preserve their own layouts.
- **Background:** preview tiles for all 22 built-in options, including every retained design background, plus **Own image…**. All options work with all designs. Import, select and remove personal images here; the original file is never deleted. Choose cover, contain, stretch, center or tile. **Tint background…** and **Remove tint** affect the background independently of accents. Sparkle retains its animation; other backgrounds are static, and Adaptive follows the accent.
- **Accent colors:** named preset swatches, including the original Gold, Champagne, Liquid Silver and Aurora accents, plus **Custom color…**. Select a saved personal color to edit or delete it. Presets remain protected. **Design colors** uses the native palette of the selected surface. When automatic wallpaper accents are deselected, the previous manual choice—including Design colors—is restored. Foreground materials, reflections, icons, text, charts and the animated identity coordinate with the selected colors while remaining legible on light surfaces.

For example, combine Obsidian with the Aurora background and Liquid Silver accents. Changing the design retains your explicit background and accent selection. Resetting Appearance restores Obsidian’s original gold combination. Theme, accent and background transitions preserve the active page, scroll position and live measurements. Previews wrap into fewer columns on small windows.

Existing profiles migrate once with a local backup. Previously fixed designs retain their effective visible palette and backdrop as an explicit combination. Dormant accent and background choices are also retained in migration metadata; personal images, custom colors and dashboard preferences are not removed. Stable and Unstable remain isolated.

The sculpted VITALUX wordmark, rotating outer logo bands, heartbeat and moving reflection remain continuously animated. **Animations** offers smooth, reduced and off profiles. **Ultra Eco** temporarily uses a simple surface, CPU rendering and a ten-second sampling interval; saved design, background, tint and accent choices return when disabled.

## Apps and network connections

Open **Network → Apps & connections** to start the session monitor. Select an application to inspect its process IDs, executable path and TCP/UDP destinations. Running applications without current connections are also listed. Filter by name or path and sort by transfer rate or recorded usage. Connection details remain collapsed until needed. Totals cover the observed measurement session, not historical usage before Vitalux started. **Reset measurement** resets totals and warnings without changing active blocks.

The normal view uses Linux TCP diagnostics. UDP counters, inaccessible processes and unavailable kernel data remain unknown rather than being inferred from interface totals. Some containers expose connections but no per-socket byte counters. **Partial** means not all of an application's traffic could be measured. Live updates retain your selected app/connection and scroll position, including after a block or unblock.

**Authorize full measurement** sets up an isolated root-owned helper through Polkit, then requests authorization to use it. This optional feature needs cgroup v2, Linux cgroup BPF, process-fork tracepoints/perf events, Polkit (`pkexec`) and `/usr/bin/python3` on the host. If tracefs is not mounted, the helper accesses it in a private mount namespace without changing desktop mounts or global tracing settings. Missing kernel support or denied authorization is reported explicitly. The portable app itself still includes Python and runs without a system Python installation. Full mode measures TCP/UDP IP bytes, including protocol headers; changing measurement modes starts new totals because TCP payload and IP-byte counters are different measurements. No packet payload is captured.

Use **Block** or **Unblock** directly beside an application, or select it and use **Block network access** / **Allow network access**. Blocking requests Polkit authorization directly when needed; the status shows pending actions and errors. Select an application and expand **Advanced connections** to inspect its sockets. Select a TCP/UDP socket and use **Block connection** / **Unblock connection** to control that socket in both directions. An application-wide block takes priority over an individual socket rule. It covers running app processes and is inherited by their new subprocesses before they can open a connection. Python/Node script identities are kept distinct. Allowing an app releases its inherited blocks together. Rules last for the authorized session: **Release all blocks**, **End authorization**, closing Vitalux, or helper termination releases them. This is session traffic control, not a persistent firewall policy across reboots. Independently launched instances are discovered as the helper refreshes; treat blocks as controls for running processes, not as a security boundary against hostile software. Cached pages can remain visible in a blocked browser; verify with a fresh request.

**Usage warning** sets an observed-traffic threshold in MiB for each application (0 disables it). Vitalux shows the warning once per measurement session; reset measurement to start again. **Look up hostnames** explicitly asks the system resolver for PTR records. A PTR hostname does not verify who operates a destination.

## Search and sound

Click the magnifier in Settings. Search grows with the text, adapts to the available width and shows matching settings. Clear predictions glide to the control automatically while you keep typing. Choose a result to focus its control; the search field then remains visible for five seconds and closes smoothly. Open, close and interrupted transitions remain smooth. Escape, an outside click or five idle seconds closes the field.

**Glass sound on clicks** gives buttons, selections and opening dropdowns a short, softly damped glass tap (115 ms, lower pitch), including keyboard activation. Adjust **Volume** or switch it off. It stays within Vitalux. A closed dropdown ignores the mouse wheel, so page scrolling cannot accidentally change a setting. Desktop audio uses PulseAudio or PipeWire's PulseAudio-compatible service.

## Graphics and MiniHUD

**Advanced settings** is near the bottom of Settings, directly above the full **Restore defaults** button. Click its header to expand or collapse it smoothly; the page follows expansion so the revealed controls become visible. It contains graphics rendering and **Maintenance** (clear Vitalux caches or reset personal preferences). Searching for these controls opens the card automatically.

CPU rendering is the stable default. Experimental OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan profiles depend on working drivers and a suitable session. Apply a renderer change with **Restart now**. Closing and restarting retain a responsive window until background work finishes safely. A failed startup falls back to CPU. X11 and Wayland select a window-system plugin; they do not change your desktop login session.

MiniHUD reuses the main sensor stream and offers three layouts and adjustable opacity. Your desktop compositor determines its placement relative to fullscreen applications.

## Reset settings

Section reset buttons softly appear when values differ from defaults and softly disappear after a reset. They apply only to their own section and do not restart Vitalux. The full **Restore defaults** button is the final item in Settings and restarts the app so graphics defaults take effect. A running benchmark, diagnostic or update prevents a full reset until it finishes; settings are not deleted in that case. **Delete personal preferences** in Maintenance restores actual defaults, restarts the app and reopens the introductory guide. Only the active profile is reset; imported image files and the other channel’s profile are retained. Stable settings are copied only on the genuine first Unstable launch, not after an intentional reset. A reset profile also remains compatible with older builds when switching channels.

## Language and updates

Use **DE / EN** in the navigation area (bottom bar in Eclipse Crystal). Labels, the native guide, update notes and offline changelog follow the selected language without interrupting monitoring.

Vitalux checks the official release at startup and about every six hours. Read the current-language notes in **Updates**, then choose **Update now**. The full archive/AppImage and checksum must be available. AppImage replacement is atomic; a ZIP installation keeps its previous version for rollback. Personal data and settings are retained. Updates check free space before staging files and report interrupted downloads; a failed download does not replace the installed application. A centered percentage shows total preparation progress: downloading uses 0–80%, followed by verification and staging up to 100%. Slow connections report smaller received chunks. An idle socket times out after 15 seconds, subject to DNS and connection setup. When the server omits its size header, the official asset size or verified test manifest supplies the total. Progress stays at 0 until reception finishes only if neither source provides a size. **Cancel download** stops a transfer without activating the destination; a blocked read can take until its timeout to finish. **Retry download** starts a fresh verified transfer after a failure. Cancellation is unavailable once verification/preparation begins.

The full release ZIP includes Python/Qt. Manual delta ZIPs are only for overlaying the immediately preceding portable ZIP version, never for AppImages. Keep a backup before a manual overlay.

## Troubleshooting

Normal settings: `${XDG_CONFIG_HOME:-~/.config}/vitalux`. Logs: `${XDG_STATE_HOME:-~/.local/state}/vitalux`. Diagnostic Center exports local reports; **About → Guide** opens the translated tour.

Explicit `Designs-testen.sh` previews keep their separate `design-test-data/` profile and disable releases. Use the normal stable `run.sh` or AppImage for update-enabled operation.

## Update channels and profiles

Everything stays in the **Updates** tab, without a channel-switch popup. The first card shows the installed channel/version once, its running status and **Check for updates**. The second card, **Update channels**, holds Stable/Unstable, their availability and release notes that always remain visible. Its **Version** selector browses the selected channel’s release history, including offline notes. Older notes never change the installation destination or enable a downgrade; only the separate installation action prepares the latest verified destination.

Browsing does not alter your installed channel or create an update notification. A separate **Update now**, **Switch to Unstable** or **Return to Stable** action shows the target version and prepares the installation. The target appears only when installation is available, in progress or awaiting restart. Switching to Unstable requires a verified test build with real application changes beyond the current Stable baseline; otherwise its action is disabled with an inline explanation and its notes remain readable. Returning to Stable remains possible.

After a verified update or channel switch is prepared, Vitalux automatically finishes background work and restarts into the selected build. The prepared destination remains fixed; browsing other notes cannot change it or offer the package twice. The previous process fully exits before an external helper activates the ZIP/AppImage and reopens it once. If helper preparation fails, monitoring resumes with the package retained and **Retry** in Updates. Stable v0.9.6.2 has the older updater: Stable → Unstable still asks for **Restart now** after installation. The new build can only control updates initiated by that build; returning to this older Stable also returns to its manual updater. Updates shows an inline explanation before that return. A Stable release is required to change the older Stable updater itself.

Stable keeps its existing preferences. Unstable automatically creates a separate profile on first launch using Stable's preferences and imported backgrounds. Subsequent launches, updates and switches preserve each profile; migrations receive local backups (the latest five per channel). Profile handling is automatic: there is no import or fresh-profile button, and switching back never overwrites the other channel's preferences.

When your test changes reach Stable, Vitalux offers a notice and lets you view the Stable destination. A newer eligible Unstable build takes precedence. A single rolling prerelease supplies test packages; when it has caught up with Stable it is marked **Unstable — based on Stable v…**, without creating another mirror build or consuming another test number. GitHub's **Latest** download always remains Stable. Technical test versions are retained internally for correct ordering and recovery.

Channel changelogs are cached for offline reading with their check time. Offline or failed checks are reported explicitly; cached information alone cannot authorize an installation.

On/off controls use themed switches throughout the interface. Multiple-selection controls retain checkmarks. Surface previews softly zoom on hover, with small palette/background hints at the right edge; all surface styles now support both. Background and accent controls occupy their own cards. Ultra Eco temporarily restricts customization. The soft click sound defaults to 50% and can be adjusted or muted in Settings.
