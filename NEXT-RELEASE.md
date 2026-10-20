# Release plan — v0.9.5.8

Approved by the owner on 2026-10-20. Baseline: v0.9.5.7.
Status: implemented in v0.9.5.8. Local validation passed; the stable-release workflow publishes packages only after its complete checks.

## Agreed application changes

- Make the compact Overview system header permanent and remove the preference/toggle. Preserve all system information and existing dashboard editing.
- Replace all Vitalux circle-logo SVGs with the selected slimmer outer-band design, a smoked-glass center and the approved waveform.
- Replace all wordmark SVGs with the approved title-case Vitalux outlines and coordinated metallic finish. No external font file.
- Preserve independent slow outer rotation, a clearly contrasting heartbeat impulse, and the wordmark's soft moving reflection. Keep all cycle boundaries continuous and preserve phase during theme changes.
- Provide independent vectors for eight accent colors, light-background lettering and each of Obsidian Gold, Black Glass Gold, Champagne Glass and Aurora Gold.
- Keep branding palettes and geometry in their own files and provide a reproducible standard-library SVG builder.
- Slightly enrich automatic custom/distribution accent tint only for the circle logo. Preserve the wordmark's existing tint calculation and avoid excessive saturation.
- Apply the identity consistently to the sidebar, app/window, desktop, tray and README.
- Preserve native SVG sharpness, full-density material detail, reduced/off motion, Ultra Eco and hidden-animation pausing. Optimize redundant work rather than removing visual detail.

## Documentation and release requirements

- Keep the professional README and user guide in English, with usable launch/help commands.
- Use a fresh English-interface Obsidian Gold screenshot and matching header artwork. Obsidian Gold remains the existing default; preserve saved themes.
- Maintain DE/EN interface, guide and release-note translations. Changelogs contain only relevant changes inside the app, excluding GitHub/README/screenshots, CI and internal housekeeping.
- Preserve the existing project licensing position, runtime/source notices and new build-tool attribution. No additional font or tracing dependency at runtime.
- Validate affected motion, palette selection, settings, scaling, update and shutdown paths before publication.
- Publish only with the GitHub identity PAAAUUULLOOOH; never use the owner's real name.

## Local validation

- All 51 regression scripts passed, including fixed palettes, custom tint scope, motion boundaries, reset/search flows and update/rollback behavior.
- CPU, OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan passed real-framebuffer startup checks using isolated Xvfb/Weston sessions and Mesa software drivers. No additional preflight window mapped.
- Native layouts passed at 100%, 125%, 150% and 200% desktop scaling, including the minimum settings-window size.
- Thirty theme/search/navigation cycles retained the same Qt object count (2343); RSS increased by about 4.1 MiB after warm-up. Hidden branding timers stopped; monitoring continued. These figures describe this test session.
- The actual native branding widgets produced a complete 48-second / 1200-frame capture with identical states at the cycle boundaries.
- Integrated SVG contours, authored colors and material gradients match all 74 approved local SVG assets.
- Repeated click audio, five-second idle recovery, rapid clicks and shutdown passed with a private audio server.
