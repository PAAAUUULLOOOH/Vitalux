# Vitalux user guide

## Start

Use the latest AppImage or extract the complete Linux ZIP and run `bash run.sh`. The source ZIP includes a compressed runtime too. Run `bash Portable-pruefen.sh` if a component cannot load. Keep the extracted program in its own writable folder.

## Monitor your system

Current Vitalux editions allow one running instance per user, shared across ZIP/AppImage copies and Stable/Unstable profiles. A genuine second start shows “Vitalux is already running.” During a marked restart, a short overlap waits for the old process to finish; a prolonged restart shows a restart-specific notice. Closing to the tray keeps that instance active; use **Exit** to quit. The lock is released automatically when the process exits or crashes, and normal renderer/update restarts remain supported. Older editions without this protection must be closed before opening another edition.

Reopening a sidebar category returns to its page start. The sidebar opens Overview, Processor, Graphics, Memory, Drives, Network, Sensors, Diagnostic Center, System, Settings, Updates and About. The new vector symbols remain recognizable when the sidebar is collapsed. Charts distinguish series by line pattern and identify measurements and timestamps on hover. Sampling interruptions appear as gaps; missing sensors are never replaced with invented readings.

Use **Edit layout** on Overview to arrange cards. Tiles stay stationary when editing opens. Their **Hold to move** captions and X controls stay visible throughout edit mode. Drives loads SMART data asynchronously. Start disk benchmarks or external diagnostics only when needed; writing tests temporarily create files on the selected drive.

## Designs and backgrounds

**Obsidian Gold is the default** for new profiles and restored appearance defaults; saved designs are retained. Choose one of thirteen preview tiles under **Settings → Appearance → Design**. The transition preserves your page, scroll position and running measurements. Logos, sidebar text and symbols share the effective palette.

Obsidian Gold, Black Glass Gold, Aurora Gold, **Aether Glass**, **Eclipse Crystal**, **Liquid Silver** and **Nebula Prism** use fixed palettes and backgrounds. Their grey **Fixed design palette** and **Fixed background** fields cannot be opened. Aether Glass combines platinum and violet/cyan optical glass with floating navigation. Eclipse Crystal uses faceted black crystal, champagne edges, top category navigation and a bottom bar for System, Settings, Updates, About and language. Its top navigation scrolls on narrow windows. Holographic also has a fixed HUD background. Personal accent and background selections remain saved for compatible themes.

Nebula Prism uses prismatic deep-space glass, cyan/magenta spectral edges, its own ring instruments and matching animated logos. Its centered bottom dock opens all existing categories; hover identifies each icon, and the Updates icon includes the available version in its hint. Language controls stay in the header. Palette and background are fixed. Switching away restores the previous navigation layout and keeps sampling and saved customization choices.

Liquid Silver uses the same layout, smoked-glass panels and instrument geometry as Obsidian Gold, with a coordinated satin-silver palette. Its circle and wordmark retain continuous animations. Palette and background are fixed. The previous light Liquid Silver and Liquid Chrome are removed; saved Liquid Chrome selections migrate to the replacement without discarding accent, image or layout preferences.

The accent selector has a compact glass color swatch. Overview uses a compact system header by default, keeping system details visible while leaving more room for charts. Theme previews gently enlarge on hover without moving surrounding tiles. The sculpted uppercase **VITALUX** wordmark has coordinated metal and smoked-glass facets with a moving reflection. Slimmer outer logo bands rotate slowly around a clear heartbeat impulse on a darker base line. Rotation, heartbeat and lettering reflections repeat continuously and keep their phase when the theme changes. Each gold collection has its own coordinated logo and wordmark; preset and custom accent colors remain supported, with a modestly richer finish on the circle for custom colors. **Animations** provides smooth, reduced and off profiles. **Ultra Eco** uses a simple skin, CPU rendering and a ten-second sampling interval, preserving the previous appearance settings for later.

Profiles from the combined appearance builds return to standalone designs with a local backup. Matching Aurora and Liquid Silver combinations select their original design again. Retired Champagne Glass selections return to Obsidian Gold. The previous combined selection is retained in migration metadata; personal images, saved custom colors and unrelated preferences remain intact. Stable and Unstable profiles stay separate.

## Apps and network connections

Open **Network → Apps & connections** to start the session monitor. Select an application to inspect its process IDs, executable path and TCP/UDP destinations. Running applications without current connections are also listed. Filter by name or path and sort by transfer rate or recorded usage. Connection details remain collapsed until needed. Totals cover the observed measurement session, not historical usage before Vitalux started. **Reset measurement** resets totals and warnings without changing active blocks.

The normal view uses Linux TCP diagnostics. UDP counters, inaccessible processes and unavailable kernel data remain unknown rather than being inferred from interface totals. Some containers expose connections but no per-socket byte counters. **Partial** means not all of an application's traffic could be measured. Live updates retain your selected app/connection and scroll position, including after a block or unblock.

**Authorize full measurement** sets up an isolated root-owned helper through Polkit, then requests authorization to use it. This optional feature needs cgroup v2, Linux cgroup BPF, process-fork tracepoints/perf events, Polkit (`pkexec`) and `/usr/bin/python3` on the host. If tracefs is not mounted, the helper accesses it in a private mount namespace without changing desktop mounts or global tracing settings. Missing kernel support or denied authorization is reported explicitly. The portable app itself still includes Python and runs without a system Python installation. Full mode measures TCP/UDP IP bytes, including protocol headers; changing measurement modes starts new totals because TCP payload and IP-byte counters are different measurements. No packet payload is captured.

Use **Block** or **Unblock** directly beside an application, or select it and use **Block network access** / **Allow network access**. Blocking requests Polkit authorization directly when needed; the status shows pending actions and errors. Select an application and expand **Advanced connections** to inspect its sockets. Select a TCP/UDP socket and use **Block connection** / **Unblock connection** to control that socket in both directions. An application-wide block takes priority over an individual socket rule. It covers running app processes and is inherited by their new subprocesses before they can open a connection. Python/Node script identities are kept distinct. Allowing an app releases its inherited blocks together. Rules last for the authorized session: **Release all blocks**, **End authorization**, closing Vitalux, or helper termination releases them. This is session traffic control, not a persistent firewall policy across reboots. Independently launched instances are discovered as the helper refreshes; treat blocks as controls for running processes, not as a security boundary against hostile software. Cached pages can remain visible in a blocked browser; verify with a fresh request.

**Usage warning** sets an observed-traffic threshold in MiB for each application (0 disables it). Vitalux shows the warning once per measurement session; reset measurement to start again. **Look up hostnames** explicitly asks the system resolver for PTR records. A PTR hostname does not verify who operates a destination.

## Settings search

Click the magnifier in Settings. Search grows with the text, adapts to the available width and shows matching settings. Clear predictions glide to the control automatically while you keep typing. Choose a result to focus its control; the search field then remains visible for five seconds and closes smoothly. Open, close and interrupted transitions remain smooth. Escape, an outside click or five idle seconds closes the field.

Partial names such as **Mini**, **MiniH**, **MiniHU** and **MiniHUD** predict the same section. Layout and opacity results have distinct labels; adding those words selects the specific control. Tied matches for one subject no longer suppress automatic navigation. Predictions preserve input focus and the selected language. A closed dropdown ignores the mouse wheel, so page scrolling cannot accidentally change a setting. Click sounds and their controls have been removed.

## Graphics and MiniHUD

**Advanced settings** is near the bottom of Settings, and contains the full **Restore defaults** action under Maintenance. Click its header to expand or collapse it smoothly; the page follows expansion so the revealed controls become visible. It contains graphics rendering and **Maintenance** (full active-profile reset). Searching for these controls opens the card automatically.

CPU rendering is the stable default. Experimental OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan profiles depend on working drivers and a suitable session. Apply a renderer change with **Restart now**. Closing and restarting retain a responsive window until background work finishes safely. A failed startup falls back to CPU. X11 and Wayland select a window-system plugin; they do not change your desktop login session.

MiniHUD reuses the main sensor stream and offers three layouts and adjustable opacity. Your desktop compositor determines its placement relative to fullscreen applications.

## Reset settings

Section reset buttons softly appear when values differ from defaults and apply only to their group without restarting Vitalux.

The single full **Restore defaults** action is under **Advanced settings → Maintenance**. Its description and confirmation list the consequences: reset all active-profile preferences, including design, accents, layouts, language, warning thresholds and graphics renderer; delete saved custom colors, imported background copies, profile cache and its automatic profile backups; restart Vitalux and reopen the introductory guide. Original image files outside Vitalux and the other channel's profile/cache remain intact. Image-directory symlinks do not cause source images to be followed and deleted.

An active benchmark, diagnostic or update prevents the reset until it finishes. A failed defaults write restores the staged files. Fresh reset profiles remain initialized so Unstable does not copy Stable's preferences again. The separate cache and personal-preferences buttons are removed.

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

After a verified update or channel switch is prepared, Vitalux automatically finishes background work and restarts into the selected build. The prepared destination remains fixed; browsing other notes cannot change it or offer the package twice. The previous process fully exits before an external helper activates the ZIP/AppImage and reopens it once. If helper preparation fails, monitoring resumes and preparation retries automatically, with up to three attempts. Only a persistent failure shows **Retry restart**. A valid saved preparation resumes automatically on a later launch. The verified destination remains fixed, and an activated helper is never launched twice. Restart outcomes are recorded in `restart-events.jsonl` beside the pending-update state for local diagnosis. Stable v0.9.6.2 has the older updater: Stable → Unstable still asks for **Restart now** after installation. The new build can only control updates initiated by that build; returning to this older Stable also returns to its manual updater. Updates shows an inline explanation before that return. A Stable release is required to change the older Stable updater itself.

Stable keeps its existing preferences. Unstable automatically creates a separate profile on first launch using Stable's preferences and imported backgrounds. Subsequent launches, updates and switches preserve each profile; migrations receive local backups (the latest five per channel). Profile handling is automatic: there is no import or fresh-profile button, and switching back never overwrites the other channel's preferences.

When your test changes reach Stable, Vitalux offers a notice and lets you view the Stable destination. A newer eligible Unstable build takes precedence. A single rolling prerelease supplies test packages; when it has caught up with Stable it is marked **Unstable — based on Stable v…**, without creating another mirror build or consuming another test number. GitHub's **Latest** download always remains Stable. Technical test versions are retained internally for correct ordering and recovery.

Channel changelogs are cached for offline reading with their check time. Offline or failed checks are reported explicitly; cached information alone cannot authorize an installation.

On/off controls use themed switches throughout the interface. Multiple-selection controls retain checkmarks. Design previews form the same multi-row grid in every design; hover or keyboard focus softly reveals a small color wheel for accents and an image indicator for backgrounds, stacked at the right edge and vertically centered on the tile. Available options use colored symbols; unavailable options use grey symbols, without lock overlays. Black Glass supports both preset and custom accent colors, including editing and removing saved custom colors. Fixed-palette designs disable and consistently grey out the custom-color buttons. Background support is independent: Holographic allows accents but retains its fixed background. Ultra Eco can temporarily restrict customization. Controls no longer produce click sounds.

**Recent events:** the Diagnostic Center shows the latest five app warnings, update failures and automatic renderer fallbacks. Entries remain local and follow DE/EN. Repeated identical events are grouped briefly; the optional Blackbox remains separate. Known causes of missing CPU/GPU readings appear as short labels; unknown causes remain unavailable.

**Logs:** Vitalux keeps an active file and one previous file per log, rotating at about 5 MB (roughly 10 MB combined, allowing complete error records). This includes launcher, crash, installation, restart and local event logs. Stable and Unstable use separate directories. Crash recording and automatic version recovery remain active.
