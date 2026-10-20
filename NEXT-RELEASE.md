# Release plan — v0.9.6.0 with a permanent Unstable channel

Baseline: published stable v0.9.5.9. Status: implemented and locally verified; release package validation is repeated before publication. The owner requests the current changes as a Stable release on main, alongside a working permanent Unstable channel.

## Stable and Unstable updates

- Keep one permanent `unstable` development branch. Work explicitly requested as Unstable targets that branch. Stable releases come from `main`.
- Prepare the next stable version with `v0.9.6.0-unstable.1`, `.2`, and subsequent test build numbers. The finished stable version is `v0.9.6.0`; the following cycle can start at `v0.9.6.1-unstable.1`. Preserve the owner's four-part release numbering and rollover from v0.9.5.9 to v0.9.6.0.
- Publish test packages through ONE continuously updated prerelease entry, "Unstable — current test build". Keep that entry across stable publications and future test cycles. Use a fixed test tag and explicit build-version metadata; update packages and notes rather than creating a release entry for every test build. Verify assets/checksums before advertising a new build, and handle interrupted publication safely.
- GitHub's Latest label and latest-release download remain Stable. The repository release count includes the single Unstable entry; replacing that entry's packages does not add releases. Each new Stable release adds its own entry.
- After EVERY stable publication, merge the released main changes back into unstable, preserve ongoing work and history, then build and update the SAME rolling test prerelease. Never silently discard test work to resolve a merge conflict.
- Put a themed `Stable | Unstable` segmented selector in Updates → Vitalux version status, beneath the installed version and above the update-check action. Show the actual installed channel independently of the selected destination.
- Show the destination version and localized changes before installation. Use explicit "Switch to Unstable" / "Return to Stable" actions, backed by verified downloads, backups and restart. Returning to Stable must also work when its version is older than the installed test build.
- Keep Stable's existing settings and a separate Unstable profile. Copy settings and profile-owned resources on the first test launch; retain each profile on later switches. Separate caches and internal app data as well. Store channel-selection state independently where necessary for reliable switching.
- Version settings/data schemas, validate values and back up before migrations, including migrations between successive test builds. Offer explicit import of compatible settings from the other channel and a fresh test profile when needed. Preserve a usable stable configuration and validate renderer availability with CPU fallback.

## Consistent themed switches

- Use themed animated switches for immediate on/off settings in every design, extending the existing signature-design switches.
- Keep interaction, focus/keyboard behavior and sizing consistent; adapt materials, accent/fixed-palette colors, edges and reflections to each design. Respect reduced/off motion and Ultra Eco.
- Retain checkmarks for multiple selections, such as CPU/GPU/RAM chart series.

## Design gallery and customization indicators

- In Aether Glass and Eclipse Crystal, replace the horizontal design-preview strip/slider with the same multi-row preview grid used by the other designs. Show every design tile in the gallery without horizontal scrolling; retain normal vertical page scrolling and readable tile sizes on compact windows. Preserve hover/selection animations and the distinct designs themselves.
- Add two well-visible, theme-coordinated vector indicators to every preview tile: palette/accent customization and custom-background support. The accent indicator should be a colorful circular color wheel, replacing the outlined artist-palette proposal. Use a contrasting glass backing and readable icon sizes (approximately 20–24 logical pixels); fixed options remain muted with a visible lock, and limited capabilities have an accurate indication. Preserve names, selected markers and sharpness at fractional scaling.
- Reveal these indicators on tile hover with a soft opacity/position transition (approximately 180–240 ms), and fade them out smoothly on leave. Also reveal them on keyboard focus and provide an equivalent discoverable interaction on touch. Respect reduced/off motion and avoid moving the surrounding grid. The idle tile remains uncluttered.
- Show concise DE/EN tooltips and accessible descriptions, such as "Accent colors adjustable", "Fixed design palette", "Background adjustable" and "Fixed background". Match the existing disabled-control explanations.
- Derive indicators and actual control availability from shared per-design capability data, never from whichever design is currently active. Obsidian Gold, Champagne Glass, Aurora Gold, Black Glass Gold, Aether Glass and Eclipse Crystal have fixed palettes and backgrounds. Holographic supports accent changes but has a fixed background. Black Glass currently permits preset accent choices and backgrounds but disallows custom accent creation/editing; represent this limited capability accurately. Keep temporary Ultra Eco restrictions distinct from the design's inherent capabilities.
- Verify agreement between every tile's indicators and the settings it actually permits, including Black Glass's partial restriction, DE/EN, all existing designs, minimum window sizes and scaling.

## Simple application network controls and advanced connections

- Reported defect: "Block network access" remains grey for the user. Current source gates the action on `client.active`, a selected application and known processes/rules (`NetworkWatch._selection`). Full authorization is currently requested through a separate measurement button; this source check alone does not establish why authorization is missing or failing on the user's machine.
- Make blocking directly discoverable from each recognizable running application, including applications with no current connection. Provide clear "Block network access" and "Allow network access" actions and an acknowledged active/blocked/pending/error state.
- Request necessary Polkit authorization from the block action itself, then apply the intended validated rule. Explain cancellation, unsupported kernels, unavailable helpers or missing prerequisites in the interface rather than leaving an unexplained permanently disabled control. Do not bypass Linux authorization.
- Whole-app blocks must cover both inbound and outbound IPv4/IPv6 traffic, TCP and UDP, existing connections and new traffic from the application's associated processes. Validate application/process attribution, particularly browser worker processes, sandboxed apps and shared interpreters; do not silently block unrelated apps.
- Keep the default view simple: application name, useful traffic/status information and whole-app block/unblock. Clicking an application reveals its details, with individual TCP/UDP connections inside an animated Advanced section.
- In Advanced, allow blocking and unblocking an individual connection in both directions. Validate socket/process ownership and identity; make app-wide and connection-specific rules distinct and show when an app-wide rule still blocks a connection. Prevent stale identities from affecting a reused PID/socket.
- Keep the existing session-scoped lifetime for now and state it clearly. Retain a discoverable release-all action and automatic cleanup when authorization or Vitalux ends.
- Verify actual block/unblock behavior using real bidirectional TCP/UDP traffic, existing/new sockets, helper authorization/failure paths and process lifecycle changes. Check compact layouts, translated labels, theme transitions and shutdown.

## Current release verification

- Stable and Unstable each pass all 56 regression scripts using the shipped Python/Qt runtime, including channel downgrades, manifest integrity, profile isolation, migration and rollback.
- Real Linux 6.12.107 VM checks pass app-wide and individual TCP/UDP block/unblock, both directions, existing/new sockets, process identity validation and automatic helper/EOF cleanup.
- All five native renderers pass with live samples and a single X11 startup map. Repeated audio, five-second idle recovery and rapid notes pass through an owned PulseAudio loopback.
- Thirty-six live navigation/design/search cycles complete with hidden animations paused; Qt object count increases by eight and RSS by approximately 20 MiB after warm-up.
- Native settings captures pass fractional scaling. Updated screenshots show the actual design grid, readable network actions and selected update channel.
- The predecessor's actual updater rejects corrupt checksums, installs v0.9.6.0, preserves settings and rolls back successfully. AppImage extraction, user installation, desktop integration and removal pass.

## Documentation and publication conventions

- Refresh the English README and user guide when these features are implemented. Keep changelogs limited to relevant changes inside the app; omit repository, CI and README maintenance.
- Preserve license/source notices, verified portable runtimes and the GitHub identity PAAAUUULLOOOH.

---

# Completed release plan — v0.9.5.9

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
