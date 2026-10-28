# Vitalux – Changes

## [v0.9.6.4-unstable.12] - 2026-10-29

- Portable packages include the required GLib and other desktop runtime libraries. No separate GLib installation is needed to start the app.
- Steam restarts orderly and automatically when overlay setup requires it. Play game prepares the connection and then starts the game; running Steam games are not terminated. Existing connections and changes to metrics do not need a restart.
- Long game-session reports remain responsive while preserving recorded values and spikes.
- The game tile, current session and history update together after a game ends, without restarting Vitalux.
- Assessments use matching colors: green for Very good/Good, amber for Adequate and red for Needs improvement. Incomplete or short recordings remain neutral.
- Game covers fill the same compact tiles proportionally. Names and session details stay readable inside each tile.
- Removed RAM product pictures and picture lookups. Detected manufacturer, part number and module specifications remain visible.

## [v0.9.6.4-unstable.11] - 2026-10-28

- Aurora Bloom is now available through its own design preview tile. Buttons and selectors use asymmetric rounded corners; the inner header/sidebar junction is rounded.
- Designs with a collapsible sidebar: Settings search centers over the content and follows sidebar movement. Fixed the leftover strip below the top window outline.
- Glass, Obsidian Gold and Light: a small fixed gap between the Vitalux wordmark and navigation, including fullscreen.
- Compact game tiles place a centered title above fitted artwork, with the launcher and session status below. Steam artwork also supports current cache filenames and official image metadata.
- Play game verifies and prepares the actual overlay connection first. Missing launcher entries are detected; an enabled but disconnected overlay is no longer silently skipped. Native and Flatpak launchers are started explicitly.
- Overlay profiles close after saving only when setup succeeds. Errors stay visible and existing launch arguments are preserved.

## [v0.9.6.4-unstable.10] - 2026-10-28

- Less processing and bounded memory use when repeatedly changing designs and accent colors. Rendering, animations and measurement intervals are preserved.
- Animated backgrounds fully pause while the window is hidden and resume when shown.
- Open specification dialogs reliably display manufacturer data that finishes loading in the background.

## [v0.9.6.4-unstable.9] - 2026-10-28

- All designs: appearance changes without a bright flash or brightness jump, including interrupted transitions and fractional display scaling.
- All designs: calmer card surfaces, clearer measurement and label hierarchy, and balanced content gutters in narrow windows. Colors, backgrounds and distinctive design shapes remain individual.
- All designs: consistent available-update emphasis in sidebars, header navigation and the dock. The marker remains visible with reduced motion or animations disabled.
- All designs: coordinated hover, search and navigation transitions with clearer keyboard focus. Passive information cards no longer add a glow as the pointer passes over them.
- Specifications, details, game profiles and confirmations use matching design materials, shared spacing and consistent buttons.

## [v0.9.6.4-unstable.8] - 2026-10-27

- Game overlay: saving an enabled profile connects the game to its launcher and displays the actual connection state. The included MangoHud integration also works inside Steam’s runtime for OpenGL and Vulkan.
- Games library: wide, high-resolution Steam capsules with an offline cache. Titles, launchers and session status sit consistently below the artwork; unsuitable small or portrait images are not enlarged.
- All designs: direct, smooth appearance transitions without an intermediate design flashing. The top window contour remains intact while the sidebar expands and collapses.
- Designs with a header and sidebar: one continuous material without an overlapping seam. Crystal Atrium rounds the pane ends and inner junction.
- Nebula Prism: a floating, slightly translucent dock with an even rim. Cards scroll behind and beside it down to the bottom window edge.
- Settings: centered search in the top strip, sized to match the window controls. The magnifier and text remain aligned while opening and closing.

## [v0.9.6.4-unstable.7] - 2026-10-27

- MangoHud 0.8.4 is included for 32- and 64-bit OpenGL or Vulkan games, including Flatpak launchers. No separate MangoHud installation or extension is needed.
- Existing game connections automatically use the included overlay. Profiles and local reports are retained; connected games remain usable after closing or updating the app.

## [v0.9.6.4-unstable.6] - 2026-10-27

- New Games tab: automatically discover, search and launch installed Steam games (including Flatpak and additional libraries), Heroic and Lutris games. Previous reports remain available after uninstalling a game.
- Set up MangoHud per game: choose metrics, position, size, opacity, shortcuts and a target FPS. Existing launcher arguments are preserved and connections can be removed. The former MiniHUD remains available as Vitalux Overlay for the desktop.
- Automatically open a local post-game report with average FPS, 1% and 0.1% lows, selectable FPS/frametime history, available hardware peaks and past sessions. Target-relative assessments explain their criteria; incomplete or short recordings receive no overall grade.
- Less work for overview updates, chart hover, sensor discovery and closed network details; less retained memory from repeated context menus and experimental graphics backgrounds. Existing designs, animations and sampling intervals are preserved.

## [v0.9.6.4-unstable.5] - 2026-10-26

- All designs: removed the extra window-strip tint and duplicate distro/design captions from navigation. The distribution name remains in Overview.
- Sidebars meet the left and bottom window contour; designs without a header also meet the top edge. Materials and rounded corners follow each design.
- Existing headers fill the top window edge and contain layout and window controls. Sidebars join directly below, without an additional strip or floating gap.
- Cards use the recovered space and continue scrolling behind fixed navigation. Editing actions fit narrow headers while window controls and scrolling remain accessible.

## [v0.9.6.4-unstable.4] - 2026-10-26

- All designs: Sidebar expansion and collapse align with the frameless window, with clean transitions and straight edges.
- Compact window strip without the Vitalux caption. Layout editing sits left of Minimize, with matching controls and editing actions in the top strip.
- Overview cards start higher, use more width and resize automatically through to the grid's right edge.
- Cards remain visible while scrolling beneath the fixed translucent window strip; scrolling also works over the strip.

## [v0.9.6.4-unstable.3] - 2026-10-26

- All designs: Frameless main window with rounded outer corners, integrated window controls, dragging, resizing and maximization.
- The initialization card stays centered after opening and follows display geometry changes, including KDE/Wayland placement.

## [v0.9.6.4-unstable.2] - 2026-10-26

- Saved chart selections and time windows, plus a preferred GPU for the overview, MiniHUD and diagnostics.
- Reload individual components, reject incorrect pictures or choose local images; accessible error and data-source details.
- Complete sensor lists with distinct identities, explicit outdated readings and no false recovery when data disappears.
- Diagnostic reports and exports follow the app language; ChangeRadar saves its baseline without blocking the interface.
- Monotonic update progress when automatically switching to Stable.
- Less work for backgrounds, animations, tables and sensor queries with unchanged rendering quality.

## [v0.9.6.4-unstable.1] - 2026-10-26
- Unstable updates directly install and start Stable once it contains the test build. Parity is checked during preparation and before restarting; no separate channel-switch action is needed.
- Crystal Atrium design: the former Crystal Glass is renamed Crystal Atrium and uses the original static Atrium background. Glass surfaces, the overview layout editor and rounded design gallery remain. Personal colors and backgrounds are retained; Crystal Glass remains available as a color and background preset.

## [v0.9.6.3] - 2026-10-25
- The design gallery focuses on Obsidian Gold, Glass, Crystal Glass, Nebula Prism, Quantum Core and Light. Colors and backgrounds of several former designs remain named presets. All six designs remember independent accent/background settings and offer their own original/reset actions.
- Crystal Glass adds smooth glass on one static background and an editable overview. Nebula Prism adds prismatic instruments and a floating dock; Quantum Core adds angular neon panels and reactor instruments with a static factory background.
- Overview has a larger centered system header and roomier information chips. Component captions follow one centered order, with full long names available on hover. Updated design previews fit their rounded selection tiles.
- Additional Linux sensors expose supported component power and driver readings. Missing measurements remain unknown or hidden; real zeroes stay visible. Graphics groups utilization, video memory, current watts and power limit without a duplicate sensor card.
- Processor lists all available logical CPUs in numeric order and adapts meter sizes. One selectable history chart combines usage, temperature and clock speed with separate unit scales.
- CPU, graphics, memory modules and mainboard gain more precise manufacturer/model identification and optional matching product pictures with offline caching. Cutouts are preferred, with matching photographs as a fallback. CPU images must match the detected model variant.
- CPU, graphics and mainboard views show short specifications and a scrollable manufacturer datasheet with its source link. Manufacturer text follows the German or English app language and remains available offline after successful retrieval.
- An initialization window with actual rounded corners and centered screen placement reports real preparation stages. The interface, first measurements and cached product data are prepared before the main view opens. Disabling Ultra Eco restores the previous design.
- Vitalux runs once per user. Verified updates and channel switches restart automatically; slow downloads support cancellation/retry and clearer progress. The full running version stays visible; long release notes scroll in a bounded area.
- A fresh verified check that Stable contains the installed test changes automatically returns Unstable to Stable. Later test builds still require manually choosing Unstable.
- Restore defaults resets only the active channel profile, clears its cache and reopens the guide. Advanced settings and Maintenance remain permanently visible, without collapsing. Reset/restart wait for background work; AppImage activation and recovery share one transition owner.
- Settings search recognizes incomplete MiniHUD terms. Diagnostic Center shows the last five app events; unavailable measurements explain known causes. Click sounds and their settings are removed.
- With no new test changes, Unstable shows “No new updates · Switching to Unstable is unavailable”. Both channels share the published Stable baseline without creating another test build.

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
