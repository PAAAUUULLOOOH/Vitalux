# Vitalux – Changes

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
