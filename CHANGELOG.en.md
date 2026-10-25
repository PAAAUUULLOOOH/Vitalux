# Vitalux – Changes


## [v0.9.6.3-unstable.21] - 2026-10-25
- Crystal Atrium joins the design gallery with clear glass surfaces, instruments, logo and wordmark, the familiar Obsidian layout and a static dark-blue/light-blue/violet background.
- Hardware identification uses a general PCI database, additional manufacturer aliases and available driver names. Picture lookup handles internal mainboard suffixes, structured product metadata and image CDNs.
- CPU, graphics, memory-module and mainboard headers show concise aligned specifications to the right of matching product pictures. RAM manufacturer/part numbers appear when firmware data is readable; different modules remain separate.
- Only cutout product pictures are displayed. Missing pictures remove the entire image area, without placeholders or gaps. Persistent offline caching is retained; the visible offline caption is removed.
- Eclipse Crystal puts CPU/GPU overview percentages and temperatures on separate, consistently aligned rows.
- Processor retains current measured watts, removes PL1/PL2 rows and realigns its remaining readings.

## [v0.9.6.3-unstable.20] - 2026-10-25
- Overview centers the GPU power reading to match the graphics-card name.
- Processor lists all present logical CPUs in numerical order, including offline entries. Its meter grid adapts its columns and height so every entry remains accessible on systems with many cores or threads.
- Graphics identifies board manufacturers and unambiguous retail models from PCI/subsystem IDs, including SAPPHIRE PURE RX 9070 XT. System shows mainboard manufacturer, model and available revision in a dedicated card.
- Graphics and mainboard cards find matching product pictures through manufacturer sources and online search. Pictures load in the background, are stored persistently and remain available offline. Missing or ambiguous pictures use a neutral placeholder.

## [v0.9.6.3-unstable.19] - 2026-10-24
- The component-tab chart changes have been reverted: load, temperatures, clocks and transfer rates return to their previous presentation and familiar curve selectors. Current GPU power and its limit are retained.


## [v0.9.6.3-unstable.18] - 2026-10-24
- Processor and Graphics use the same visible chart checkboxes as Overview. Measurements can be toggled directly; controls wrap into further rows on narrow windows and retain the active design palette.


## [v0.9.6.3-unstable.17] - 2026-10-24
- Overview tiles now show only current measured power in watts. Unavailable readings stay hidden; system-drive power requires an unambiguous sensor association.
- Each component tab combines available measurements in one chart with individually selectable curves and separate scales per unit. Sensor histories continue while visiting other tabs.
- Graphics shows current power and its limit with the live values. Separate watt charts and additional average/peak blocks have been removed.


## [v0.9.6.3-unstable.16] - 2026-10-24
- Components show genuinely available power readings with readable numeric limits, session average/peak and a watt history. CPU package, DRAM, GPU socket and other measurement domains remain separate.
- Additional driver sensors expose temperatures, GPU memory, fans, voltages and engine activity where supported. Missing or failed fields disappear without gaps; real zeroes remain visible.
- Updates shows the full running app version including its Unstable test number, independently of browsing versions or preparing an installation.
- Lumen Drift has been completely removed. Saved design selections return to Obsidian Gold; personal colors, images and other settings are preserved.


## [v0.9.6.3-unstable.14] - 2026-10-23
- Smaller installation packages by removing unnecessary development and test files.

## [v0.9.6.3-unstable.13] - 2026-10-23
- Long release notes scroll inside a bounded area in Updates. The scrollbar appears only on overflow; version selection, progress and installation controls stay outside. Selecting another version starts its notes at the top.
- Quantum Core uses a sharp, static circuitry background. Background motion is removed; animated logos and live instruments are retained.
- The Lumen Drift preview in Settings uses more consistent card shapes, spacing and a rounded rectangular outline.

## [v0.9.6.3-unstable.12] - 2026-10-23
- Lumen Drift joins the gallery as the 14th design, with warm pastel glass, softly rounded cards, calm ring instruments and floating navigation below the header.
- Lumen Drift includes matching animated circle and wordmark assets and a gently breathing backdrop. Its palette and background are fixed; turning animations off or enabling Ultra Eco stops the background motion.
- Lumen Drift navigation hints identify categories on hover and show the version of an available update. Design changes preserve live measurements and personal color and image choices.

## [v0.9.6.3-unstable.11] - 2026-10-23
- Quantum Core adds angular neon panels, distinct reactor ring instruments and an animated backdrop with a radar sweep, particles and a scanline to the design gallery.
- Quantum Core includes matching animated circle and wordmark assets, with a fixed palette and background. Turning animations off or enabling Ultra Eco stops its background motion.
- Aurora Gold is removed. Saved selections return to Obsidian Gold; personal colors, images and other preferences are preserved.

## [v0.9.6.3-unstable.10] - 2026-10-23
- Nebula Prism adds prismatic deep-space glass, spectral edges, distinct ring instruments and a floating bottom dock to the design gallery.
- The design includes matching animated circle and wordmark assets, with a fixed palette and background.
- Dock icons show category and available-update hints on hover; language and design changes preserve live measurements.

## [v0.9.6.3-unstable.9] - 2026-10-22
- Dashboard tiles stay stationary when layout editing opens; hold-to-move captions and X controls remain visible.
- The Diagnostic Center shows the five most recent app warnings, update failures and automatic renderer fallbacks.
- Unavailable CPU/GPU measurements show a short cause when confirmed by the data source.
- Settings search captions are fully translated; the renderer selector gives long names more space.
- Local log files rotate at approximately 5 MB and retain one backup, keeping complete error records and separate channel logs.

## [v0.9.6.3-unstable.8] - 2026-10-22
- Champagne Glass is removed completely; saved selections return to Obsidian Gold. Twelve standalone designs remain.
- Settings search recognizes partial MiniHUD names, distinguishes individual controls and scrolls smoothly to the matching section.
- Opening layout editing gently shakes movable tiles for two seconds. Hold-to-move captions and X controls remain visible throughout editing.
- Restore defaults under Advanced settings → Maintenance replaces the separate cache and personal reset actions. Its description and confirmation explain the complete active-profile reset, including imported image copies and cache, followed by restart and the guide. Original images and the other profile are preserved.
- Click sounds and their settings are removed.
- Update restart preparation automatically retries temporary failures and resumes verified saved preparations. An additional recovery button appears only after persistent failures.

## [v0.9.6.3-unstable.7] - 2026-10-22
- All thirteen designs return as separate choices, including Obsidian Gold, Black Glass, Black Glass Gold, Champagne Glass, Aurora Gold and Liquid Silver. Obsidian Gold remains the default.
- Each premium design again uses its own coordinated palette and background. Background and accent controls return to their compact selectors; fixed options are greyed out.
- Preferences from the combined-design builds return to the corresponding standalone designs with local backups, retaining personal images, saved colors and other settings.

## [v0.9.6.3-unstable.6] - 2026-10-22
- Leaving automatic accents from a personal wallpaper restores the previous Design colors selection. Obsidian returns to its original gold palette instead of Vitalux Blue.

## [v0.9.6.3-unstable.5] - 2026-10-21
- Design, Background and Accent colors are separate and freely combinable: use all previous backgrounds, personal images, background tint, preset accents and custom colors with any design.
- Obsidian Gold is renamed Obsidian and keeps its original gold appearance as the default. Black Glass Gold becomes Black Glass, replacing the former Black Glass. Champagne, Aurora and Liquid Silver remain available as backgrounds and accents instead of duplicate surface tiles.
- Existing preferences migrate with backups to their corresponding combination, retaining personal images, colors and dashboard settings.
- The update bar shows a centered percentage. Slow downloads report progress more often; stalled connections produce an error. Downloads can be cancelled and retried after failures.

## [v0.9.6.3-unstable.4] - 2026-10-21
- Liquid Silver now uses the Obsidian Gold interface with dark smoked glass and a coordinated satin-silver palette. The former light layout is replaced.
- Liquid Chrome is removed; saved selections move to the replacement Liquid Silver without resetting other preferences.
- Updates explains when an older Stable build still requires a manual restart for its subsequent updates; installations initiated by current Unstable restart automatically.

## [v0.9.6.3-unstable.3] - 2026-10-21
- Liquid Chrome adds a distinct dark graphite and smoked-glass design with sculpted silver/chrome surfaces, orbital instruments and an asymmetric dashboard. It has its own fixed palette and background.
- The existing light Liquid Silver design remains available separately; saved design choices are preserved.

## [v0.9.6.3-unstable.2] - 2026-10-21
- Liquid Silver adds light platinum, satin silver, crystal-glass panels, analog instruments and its own animated silver identity. Its coordinated palette and background are fixed.
- Deleting personal preferences in Unstable restores actual defaults and reopens the guide. An existing Stable profile is not imported again during a reset.
- Intentional restarts wait for an instance that is still shutting down, while genuine duplicate starts remain blocked.
- After a verified update or channel switch is prepared, Vitalux restarts automatically once background tasks finish. The immediate/later restart buttons are removed.
- Black Glass supports custom accent creation, editing and removal. Fixed palettes use consistently greyed-out color controls; fixed backgrounds only lock background selection.
- A shorter, softer click sound replaces the previous tone. The default volume remains 50 percent.
- The old placeholder test build is removed from the version selector, including cached release notes.

## [v0.9.6.3-unstable.1] - 2026-10-21
- Design tiles use smaller indicators without locks: available accent and background options are colored, while fixed options are grey.
- Release notes always remain visible in Updates. The version selector browses previous Stable or Unstable notes without changing the installation destination or channel.
- Vitalux allows one running instance per user and shows a notice on a second start. The protection remains active in the tray and releases automatically on exit or a crash.

## [v0.9.6.2] - 2026-10-21
- Updates presents the running version, Stable/Unstable and changelogs in two clear sections; channel browsing and installation remain separate actions within the tab.
- Duplicate version labels and the settings-import button are removed. Channel profiles are still created and preserved automatically.
- Smaller color-wheel and background indicators appear vertically stacked at the right center of design tiles, retaining their soft hover transitions.
- App network blocks immediately cover new subprocesses and their TCP/UDP sockets; allowing the app releases its inherited blocks together.
- Application and connection lists retain their selection and scroll position during refreshes, blocking and unblocking.

## [v0.9.6.1] - 2026-10-21
- Click Stable or Unstable to read its current changelog without switching channels or triggering an update notification; the running version and installation destination remain distinct.
- Switching to Unstable requires a verified, genuinely newer test build. Matching channel contents are clearly identified.
- Choose “Restart now” or “Later” after installation; “Restart required” remains visible without duplicate update offers.
- A notice explains when the installed test changes have reached Stable; a newer Unstable test build takes priority.
- Test profiles are created and preserved automatically. The separate fresh-profile button has been removed.
- Previously downloaded channel changelogs remain readable offline. Check times and connection errors are displayed clearly.

## [v0.9.6.0] - 2026-10-21
- Switch between Stable and Unstable from Updates, with separate settings profiles, backups and a return to the stable version that preserves each configuration.
- Block and unblock applications directly in the network list. Blocking requests necessary system authorization and explains failures visibly.
- Individually block or allow TCP/UDP sockets in smoothly expanding advanced connection details.
- Aether Glass and Eclipse Crystal now show the complete design-preview grid. Hovering reveals color-wheel and image indicators; fixed options carry a lock.
- Consistent on/off switches follow every design, while multiple selections retain checkmarks.
- A softer, damped click tone defaults to 50% volume and remains reliable for repeated clicks.

## [v0.9.5.9] - 2026-10-20
- Aether Glass and Eclipse Crystal add distinct glass/crystal materials, instruments and navigation layouts, with coordinated fixed palettes and backgrounds.
- The selected architectural VITALUX wordmark combines metal and smoked-glass facets, coordinated color variants and the existing moving reflection.
- Network → Apps & connections shows applications, connection destinations and recorded traffic, with configurable per-app usage warnings.
- Optional system authorization enables TCP/UDP accounting and network blocks for running applications. Session blocks are released automatically when authorization ends or Vitalux closes.
- The appearance selector is now named “Design”. Missing process or traffic data is explicitly shown as unavailable.
- Overlapping chart series retain their correct translucent fills without stray colored areas between the lines.

## [v0.9.5.8] - 2026-10-20
- Overview now always uses the compact system header; the previous toggle is removed while all system information remains available.
- A new circular logo with slimmer outer bands and a glass center is paired with a new Vitalux wordmark and coordinated metallic finish.
- A clearer heartbeat impulse, slow outer rotation and soft lettering reflection repeat without a visible cut; changing themes preserves their animation phase.
- Obsidian Gold, Black Glass Gold, Champagne Glass and Aurora Gold each have their own logo and wordmark colors. Custom accents look slightly richer on the circle without increasing saturation elsewhere in the interface.
- Smoother logo animation stays sharp at increased desktop scaling; reduced motion, disabled animation and Ultra Eco remain supported.

## [v0.9.5.7] - 2026-10-20
- Obsidian Gold is the default for new installations and appearance resets, with finer glass edges, softer reflections and clearer measurements; saved theme choices are preserved.
- The original central logo waveform now carries a soft heartbeat trace while the outer bands continue their slow rotation.
- A compact glass color swatch beside the accent selector replaces the stretched color bar.
- Reset buttons reveal and disappear smoothly. The full reset sits at the bottom of Settings and safely restarts Vitalux; section resets do not restart the app.
- Advanced settings scrolls into view as it expands. Returning to a category starts at the top of its page.
- Charts distinguish series with line patterns and show measurement names and times on hover. Missing readings and sampling interruptions remain visible as gaps.
- An optional compact Overview header leaves more room for measurements. Keyboard focus and pressed states are clearer.
- Closing and restarting remain responsive while background work finishes; full resets preserve settings when an active operation prevents restart.
- Updates check available disk space and report interrupted downloads. Click sounds reconnect to the current audio output after idle periods.

## [v0.9.5.6] - 2026-10-19
- Fixed theme palettes and backgrounds remain grey and disabled; scrolling over closed dropdowns no longer changes their selection.
- A softer crystal chime accompanies buttons, selections and dropdowns, with reliable repeated playback after idle periods and during rapid clicks.
- Settings search glides to recognized matches and stays visible for five seconds after selection before closing smoothly.
- Graphics renderers and Maintenance now live in the animated Advanced settings section at the bottom; matching searches expand it automatically.
- Theme previews gently enlarge on hover, and a clearer slow satin reflection moves across the original wordmark.
- Closing or restarting safely waits for slow sensor reads; Ultra Eco's sampling pause no longer delays exit.

## [v0.9.5.5] - 2026-10-19
- Choose ten themes through native preview tiles; Obsidian Gold, Champagne Glass and Aurora Gold are now included in the stable release.
- Fixed accent and background options explain their restrictions inside the open dropdown; unavailable choices stay grey and cannot change the design.
- Settings search now synchronizes its reveal and collapse, smoothly adapts its size, supports interrupted transitions and Escape, and closes after five idle seconds.
- Native-resolution transitions blend theme, accent and background changes while retaining live measurements, the selected page and scroll position.
- A coherent vector icon set replaces sidebar font symbols; captions, icons, logos and the original wordmark follow the effective palette.
- The original wordmark gains a subtle metallic reflection with quiet pauses; the outer logo bands continue their slow rotation.
- A short glass chime plays only when Vitalux buttons are activated, including keyboard activation; volume and mute controls are available.
- Logo/icon caches and paused invisible surfaces reduce file access and redundant redraws while preserving visual quality and measurement history.
- Fixed the small startup-window flash; CPU, OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan are validated with real framebuffers.
- Normal source ZIPs and stable packages start with release updates enabled; explicit design previews retain their isolated profile.
- German and English changelogs follow the selected language; refreshed the guide, missing translations and compact English README.

## [v0.9.5.4] - 2026-10-19
- Improved search animation and full placeholder visibility; smaller magnifier.
- Removed unreliable MiniHUD always-on-top option under KDE/Wayland.
- Diagnostic Center now separates system analysis, individual tests and reports into cards; removed Insights UI.
- Removed redundant tray preview; tooltip remains.
- First-run guide opens automatically. Improved initial X11 rendering setup and shortened README.

## [v0.9.5.3] - 2026-10-19
- Improved system score with CPU/GPU loads and temperatures, RAM, swap, VRAM, all mounted volume capacities, and actual SMART warnings; missing SMART data is never treated as healthy.
- Made settings search genuinely animated and text-responsive, with a smaller subtle magnifier that stays at the top of the page when closed.
- Restored the original DE/EN switch in the sidebar and removed the language setting.
- Consolidated Diagnostic Center into one card and removed the event timeline, interactive hardware map and before-after comparison.
- Separated renderer versus Ultra Eco restart notices; added Vitalux cache and personal settings maintenance actions.
- MiniHUD now paints transparent surfaces from 50–100% opacity and applies the topmost preference more consistently.

## [v0.9.5.2] - 2026-10-19
- Added a centered floating settings search with smooth theme-aware glass animation, adaptive width, instant suggestions and automatic close after five idle seconds or outside clicks.
- Added reset buttons for Appearance, MiniHUD and hardware alerts, visible only when the respective group differs from defaults.
- Kept the global reset at the end; imported wallpaper files and personal dashboard layouts are preserved.
- Made the DE/EN sidebar switch available even when the sidebar is collapsed.

## [v0.9.5.1] - 2026-10-19
- Restored the original compact sidebar with all pages in one uninterrupted list.
- Returned Settings to one scrollable page, with General directly after Appearance and Graphics rendering last.
- Settings-only search scrolls to the exact option and highlights it briefly.
- Diagnostic Center combines checks, performance insights, history and reports without extra category navigation.
- Removed Qt Raster from renderer choices; saved legacy settings safely migrate to standard CPU rendering.
- Added a subtle warning for custom wallpaper resource use and avoided redundant preview rendering.
- Preserved dashboard layouts, existing themes and GPU startup safety checks.

## [v0.9.5.0] - 2026-10-19
- Kept Settings and Diagnostic Center cards at their natural height instead of leaving oversized empty spaces.
- Made settings search results and diagnostic report selection more compact.
- Preserved the full v0.9.4.9 navigation, search, direct links and all existing functionality.

## [v0.9.4.9] - 2026-10-19
- Grouped the sidebar while keeping Settings, Updates and Info pinned at the bottom.
- Organized Settings into six sections: Appearance, MiniHUD & window, Monitoring & alerts, Performance & energy, General, and Graphics rendering last.
- Added search that navigates directly to settings options and remembers the last category.
- Organized Diagnostic Center into six categories; moved Vitalux Insights, gaming sessions and comparisons from Graphics to Performance & insights, with reports in their own area.
- Added contextual links from GPU and Network to their diagnostics; reorganized disk, network and sensor details.
- Updated the built-in guide, concise README and translations without removing existing features or saved preferences.

## [v0.9.4.8] - 2026-10-19
- Added Diagnostic Center with read-only system, crash, display, PCIe, thermal, network, process and change diagnostics, plus opt-in Blackbox.
- Moved existing system and error report exports out of Settings into Diagnostic Center.
- Added MiniHUD with three sizes, configurable metrics, opacity and system-tray controls.
- Preserved modern render settings and themes from v0.9.4.7.

## [v0.9.4.7] - 2026-10-19
- Black Glass Gold: fixed the RAM chart-series label, legends and load/status ring colors to use the gold palette from the initial frame.
- Ultra Eco: added a dedicated Restart now button for manual CPU/previous-GPU renderer switching instead of restarting automatically on toggle.
- Lower Eco overhead: 10-second sampling, no hidden-window chart repaints, and fewer logo updates.
- Updated the compact README, built-in guide and localized strings.

## [v0.9.4.6] - 2026-10-18
- Added an Ultra Eco on/off switch under Performance & energy with an extremely simple flat skin: no glass, shadows, wallpapers or animation.
- Ultra Eco uses CPU raster rendering, five-second monitoring and reduced redraw work.
- Turning it off restores the previous theme, accents, wallpapers, animations, polling interval and saved renderer.
- Updated the compact README, built-in guide and localized texts.

## [v0.9.4.5] - 2026-10-18
- Added power-saving Qt Raster CPU mode: cached static backgrounds and a slower optional Sparkle animation.
- Removed the standalone Qt Quick option; experimental Wayland/X11 GPU modes remain available.
- Black Glass disables personal accent colors and related controls without removing saved colors or built-in accents.
- Updated concise README, built-in guide, and English translations.

## [v0.9.4.4] - 2026-10-18
- Fixed the repeated “restart pending” state for Wayland/OpenGL, Wayland/Vulkan, and X11/OpenGL by reporting the active backend correctly.
- Graphics preflight no longer opens a visible small Qt Quick test window.
- Added explicit logging of display backend, rendering profile and GPU fallback details.
- Simplified Qt styling for the system-tray preview.

## [v0.9.4.3] - 2026-10-18
- Added experimental Wayland/OpenGL, Wayland/Vulkan and X11/OpenGL graphics profiles.
- Qt Quick now verifies its actual OpenGL or Vulkan scene graph in an isolated subprocess before starting.
- Improved safe CPU fallback for unsupported backends and native graphics crashes.
- Added quick restart-based switching with updated English strings and documentation.

## [v0.9.4.2] - 2026-10-18
- Dashboard tiles fill available space more reliably while keeping the same spacing.
- Qt Quick now checks graphics compatibility before activation and automatically returns to CPU rendering after graphics crashes.
- The author credit in the Info tab now links directly to the author's profile.

## [v0.9.4.1] - 2026-10-18
- Wallpaper-based accent is enabled only for a selected custom image; otherwise the option is greyed out.
- Switching away from a custom wallpaper restores the previous accent.
- Added system status tile with score and hints; refined theme visuals and controls.

## [v0.9.4.0] - 2026-10-18
- Black Glass Gold with a fixed gold accent and the separate Holographic HUD theme.
- Improved dashboard, charts, accent choices and monitoring.
