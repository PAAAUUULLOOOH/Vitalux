# Release plan — v0.9.5.9

Owner-approved implementation. Baseline: v0.9.5.8.
Status: implemented and locally verified. The stable release workflow repeats the required checks before publishing packages.

## Application changes

- Use the selected architectural uppercase VITALUX wordmark, reconstructed as clean vector contours with authored metal/glass facets. Preserve the circle, slimmer rotating outer bands, traced heartbeat and continuous motion phases.
- Generate independent coordinated SVG variants for the existing accent colors and fixed collections, plus Aether Glass and Eclipse Crystal. Keep runtime dependencies unchanged.
- Add Aether Glass with floating navigation, optical platinum/violet/cyan surfaces and native instruments; add Eclipse Crystal with faceted black crystal, horizontal primary navigation and a secondary footer. Preserve original pages, sampler and dashboard editing.
- Give both designs coordinated fixed palettes/backgrounds, using the same disabled inline fields as existing fixed designs. Rename the selector to Design in German and English.
- Add Network → Apps & connections with process attribution, connection destinations, manual PTR lookup and per-app session usage warnings. Missing counters remain unknown.
- Offer explicit Polkit authorization for full TCP/UDP accounting and reversible blocks of running applications. The isolated root-owned helper imports no app code and retains no rules after its descriptors close. Describe its session scope and Linux requirements clearly.
- Correct stray chart fills between overlapping series.

## Documentation and publication

- Refresh the English README and user guide. Keep Obsidian Gold as the primary screenshot and include actual views of both new designs.
- Replace the static README identity with a complete, seamlessly looping animation of the actual circle and wordmark widgets.
- Preserve licenses and source notices. No new third-party Python or font dependency is shipped.
- Keep release notes limited to user-visible app changes. Exclude repository, artwork, documentation and CI maintenance.
- Publish on main with the GitHub identity PAAAUUULLOOOH only.

## Verification

- All 54 regression scripts passed.
- Thirty-six theme/search/navigation cycles retained stable memory use (RSS decreased by about 2.3 MiB after warm-up); Qt object count rose by eight. Live samples continued and hidden logo animations paused. These figures describe this session.
- Repeated click playback, five-second idle recovery, rapid notes and audio shutdown passed on an owned PulseAudio loopback.
- Actual native branding widgets produced 1200 frames over a full 48-second cycle with identical boundary states.

- Real Linux VM: TCP diagnostics, TCP/UDP BPF counters, existing/new socket blocks, allow, PID identity validation and automatic helper/EOF cleanup passed on Linux 6.12.107.
- Five native renderers passed with real framebuffers, live telemetry and no extra startup window.
- New designs passed 100%, 125%, 150% and 200% scaling and compact settings layouts.
- All 54 scripts also passed with the shipped Python/Qt runtime. Distribution notices and executable bits passed.
- The actual v0.9.5.8 updater rejected a corrupt checksum, installed v0.9.5.9, preserved settings and successfully restored the previous version.
- The English and German native screenshots use actual live readings; unavailable cloud GPU/drive counters remain unavailable.
- Regression, endurance, audio, portable-runtime and updater reports are retained in the release validation artifacts.
