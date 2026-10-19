# Vitalux – Changes

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
