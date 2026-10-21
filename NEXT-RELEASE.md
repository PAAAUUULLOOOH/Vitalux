# Unstable follow-up — v0.9.6.3-unstable.6

Final verification of the authorized appearance/update release found that the existing wallpaper-auto fallback did not recognize the new `design_default` choice and fell back to blue. Preserve that choice alongside manual/distribution colors. Extend the real PreferencesPage test through image selection, automatic accent selection and background deselection; retain all v0.9.6.3-unstable.5 changes and isolated profiles. Publish this small follow-up on the same rolling Unstable entry; Main remains unchanged. English docs and app-only DE/EN notes are updated.

---

# Unstable plan — v0.9.6.3-unstable.5

Owner authorizes implementation and publication on Unstable. Main remains at v0.9.6.2.

Validation: all 68 scripts pass using the shipped runtime, including real slow/stalled and size-header-free HTTPS transfers, actual install-worker cancel/retry, appearance migration, default-image equality and all-design image/palette compatibility. All five native renderers and scale factors 1/1.25/1.5/2 pass. The candidate updater downloaded and SHA-256-verified the public Stable AppImage, activated it after shutdown and reopened it once. The original-container backup remains intact.

- Keep original Obsidian Gold appearance as the default, renaming its visible design to Obsidian. Rename Black Glass Gold to Black Glass and remove the former Black Glass surface. Combine Champagne Glass, Aurora Gold and Liquid Silver into Obsidian; retain all backgrounds and authored colors.
- Separate Design, Background and Accent colors into clear cards. Every retained design supports every built-in background, imported image, preset/custom accent and independent background tint. Responsive native preview grids, protected presets, coherent materials/identity and accessible color selection.
- Back up and migrate old profiles once while preserving visible combinations, dormant choices, custom resources, dashboard settings and Stable isolation. Resets retain original gold defaults.
- Center update preparation percentage inside the bar. Investigate reported hangs with real slow/stalled HTTPS transfers. Read available smaller chunks, bound idle waits, support cancellation and retry while preserving verification, frozen destinations and automatic restart.
- Refresh compact English docs, DE/EN guide, translations and actual screenshots. Changelogs contain only app-visible changes. Keep licenses and source offers.
- Platinum Atelier remains deferred; this does not authorize implementing that concept.

---

# Unstable plan — v0.9.6.3-unstable.4

Owner explicitly requests publication on Unstable. Main remains at v0.9.6.2.

Validated with the shipped runtime: 67 regression scripts, all five native renderers and four scale factors. The actual published Unstable AppImage downloaded, SHA-256-verified and activated the real Stable AppImage, reopened it once automatically and retained its previous-image backup. Separate regression coverage compiles the same updater behavior as the future Stable version and exercises both destinations through the real install worker.

- Remove Liquid Chrome and replace the original light Liquid Silver with Obsidian Gold geometry/materials in satin silver and dark smoked glass; retain the Liquid Silver name, fixed palette/background, coordinated icons/graphs and continuously animated identity. Migrate saved Liquid Chrome selections safely to the replacement.
- The reported Restart now button occurs specifically on Stable → Unstable. Published Stable v0.9.6.2 contains the old manual updater, verified directly in the actual release ZIP. Current Unstable does not contain that Updates button and already restarts automatically. Do not claim an Unstable-only release can modify the updater in an already running older Stable. Test a real install worker and actual AppImage activation; explain the legacy behavior inline when returning to the older Stable and in the guide.
- Refresh compact English README/user guide and DE/EN native help; changelogs contain app-visible changes only.

## Deferred: Platinum Atelier

Keep the concept for a later release; do not implement or publish its PNG yet. Original design study uses a horizontal workspace navigation, large typographic readings and charts instead of repeated round dials, a right status inspector and a slim bottom status shelf. Palette: ink blue/graphite with platinum/silver edges, petrol and restrained iris accents. The preview uses demo data. Approved only for keeping as a plan, not for implementation.

---

# Unstable plan — v0.9.6.3-unstable.3

Owner requested an additional, entirely distinct dark silver/chrome premium design and explicitly retained the existing light Liquid Silver. Add Liquid Chrome with graphite/smoked-glass surfaces, sculpted mercury ribbons, orbital instruments and an asymmetric responsive dashboard; fixed palette/background and existing customization explanations. Preserve all reset, guide, update, sound and profile fixes from Unstable .2. Update English docs, DE/EN guide and app-only notes; publish on the same rolling Unstable entry. Main remains unchanged.

---

# Unstable plan — v0.9.6.3-unstable.2 (implementation authorized)

Implemented for the rolling Unstable update. Local validation: all 66 regression scripts pass with the shipped Python/Qt runtime, including real launcher resets and guide reopening, both automatic update destinations and actual ZIP/AppImage activation helpers. Native audio and all five renderers pass, including Liquid Silver transitions. Main remains unchanged.

- Remove the placeholder build `v0.9.6.1-unstable.2` from the visible release history: delete any dedicated GitHub release/tag/downloads for that placeholder and remove its DE/EN app changelog entry. Ensure cached release notes cannot make it reappear in the updated app's version selector.
- Preserve the permanent `unstable` branch, the rolling `unstable` release/tag and its genuine current test build (`v0.9.6.3-unstable.1`). Inspect the actual GitHub records before deleting anything; the request concerns the old placeholder, not the active rolling release.
- For designs with their own fixed palette, disable **Custom color… / Eigene Farbe …** as well as the accent selector, using the same greyed-out visual treatment as the other disabled controls for a uniform appearance. A fixed background separately locks the background selector; derive each restriction from its corresponding design capability. Editable properties remain usable, including custom colors in Black Glass. The disabled color button must not open a dialog; retain saved custom accents for compatible designs.
- Fix the reported unavailable **Custom color… / Eigene Farbe …** action in **Black Glass**: remove its legacy preset-only restriction so designs with adjustable accent colors also allow creating, applying, editing and deleting custom accents. Audit all adjustable designs for the same mismatch, and align capability data, actual controls, preview indicators and DE/EN descriptions. Fixed-palette designs remain disabled; background support is an independent capability. This explicitly supersedes older plans describing Black Glass as preset-only.
- Replace the current click sound with a more pleasant, softer and less intrusive sound. Keep the 50% default volume, volume/mute controls and Vitalux-only scope; retain reliable repeated playback for buttons, dropdown opening and selection.
- Add the approved **Liquid Silver** design: a distinct light platinum/pearl interface with satin-silver and cut-crystal materials, floating glass panels, subtly curved edges, precise silver contours and soft directional lighting. Use a slim floating navigation rail on the left with engraved-looking icons, large graphite readings, silver instrument scales and restrained ice-blue activity accents. Adapt the existing animated logo to brushed silver with a moving highlight and a clearly contrasting dark heartbeat. Preserve the logo's continuous outer-ring animation. Give panels gentle hover lift and moving reflections, with smooth layered-glass page transitions. Preserve legibility, responsive layouts, reduced/off motion and rendering quality/performance. Owner selected a fixed silver palette and fixed background; use the same disabled-control explanations and capability indicators as the other fixed premium designs.
- Fix deleting personal preferences in Unstable: a deliberate reset must restore actual defaults and reopen the introductory guide, without copying the Stable profile again. Keep automatic Stable-to-Unstable copying for the genuine first test launch only. Preserve Stable settings and separate channel profiles.
- Investigate the reported **Vitalux is already running** notice during intentional reset/restart. The existing launcher reset and the published AppImage under X11 did not reproduce it during review; do not assume a proven timing cause. Synchronize authorized restarts with the previous process fully exiting while retaining protection against genuine duplicate launches.
- Automatically restart after a successfully verified and prepared Stable/Unstable update, and remove the **Restart now / Later** buttons. Finish background tasks safely, retain pending-target/recovery protections, and ensure exactly one relaunch. This behavior begins with the updated Unstable application; an older unchanged Stable retains its existing updater UI until promotion.
- Review findings: Stable v0.9.6.2 is included in the current test build. The placeholder has no dedicated public GitHub release/tag/download remaining, but appears in both app changelog histories. Fixed-palette custom-color buttons are already functionally disabled; their muted appearance needs to communicate this more clearly. Verify repeated resets, first-run guide behavior, actual AppImage restart, and Stable → Unstable → Stable before publishing.
- Owner approved all collected changes with “okay setz alles um”. Implement, validate and publish only on Unstable; Main remains at v0.9.6.2.

---

# Unstable plan — v0.9.6.3-unstable.1 (published)

Approved for the next Unstable update; Main remains at published v0.9.6.2.

- Remove design capability lock overlays. Use smaller, colored/grey icons at the right center, vertically stacked, with existing hover/focus motion.
- Always show the selected channel’s localized changelog and offer its version history. Browsing historical notes must not change the installation target, pending state, saved channel or update notifications.
- Enforce one instance per user before profile initialization or renderer probing. Share the lock between current package copies/channels, keep it in tray mode, release on process death, and preserve restart behavior. Show a localized notice on a second start.
- Update the compact English README, user guide and native DE/EN help. Changelogs describe app-visible changes only; retain third-party notices.
- Validate process contention/crash/restart, version browsing, full regressions, portable packages and native graphics; capture the changed interface before publishing the rolling test package.

---

# Release plan — v0.9.6.2: focused inline updates and effective app blocks

Owner approved implementation on main, including Firefox/app network blocking and the scroll regression.

- Keep all channel, notes and installation controls inside Updates. No popup or separate channel window.
- Two clear sections: running installation/check status, then channel browsing with inline notes and one applicable installation/restart action. Show the target only when meaningful; preserve the prepared target while browsing.
- Remove the settings-import button and unused transfer function. Keep automatic isolated profiles and migrations/backups.
- Keep Unstable gated by verified newer app changes; retain readable notes and the compact Stable promotion notice.
- Put smaller capability indicators at the right edge of each design tile, vertically centered and stacked; preserve hover/focus motion and accurate locks.
- Fix live application/connection selection updates so they retain scrolling rather than repeatedly scrolling to the selected row.
- Kernel fork protection immediately inherits active app blocks; atomic active-group switches release all inherited members together. Reject stale process identities and clear inherited PID entries at birth to protect unrelated reused PIDs.
- Verify existing/new TCP and UDP traffic, both directions, all CPUs, unrelated applications, PID reuse, cleanup and a real Firefox session in the isolated Linux VM.
- Keep the English README compact; update the English user guide and native DE/EN guide. Changelogs contain app-visible changes only. Preserve licenses and source offers.

---

# Release plan — v0.9.6.1: clear, deliberate channel updates

Owner approved implementation of the collected update changes. Previous discussion-only instructions are superseded by “ja setz das mal umalles”.

- Channel clicks display the channel's latest localized notes without changing preferences, authorizing an install or producing cross-channel update alerts.
- Require a verified test manifest, a newer test version, the current Stable baseline, application differences and inclusion of main. Version labels, README images and documentation alone never qualify.
- Before a genuine Unstable build, prepend its actual DE/EN test changes to both changelogs; use `python scripts/prepare-unstable-build.py --next` for the next internal version. Never copy Stable notes as new test changes.
- Keep technical test build identifiers for comparison/recovery; present a caught-up release as “Unstable — based on Stable v…”. No mirror packaging or test-number increase when no application changes remain.
- Preserve actual running version/channel, browsed channel and pending installation target independently. Freeze prepared installations until restart; suppress repeated offers and stale check replies.
- Provide Restart now / Later. On normal exit activate a deferred AppImage without reopening it; persist pending state per installation and clear it only in the newly running version.
- Automatically initialize/preserve/migrate isolated test profiles with backups; remove the manual fresh-profile button/function.
- Show when an installed test's changes reached Stable; prefer a newer eligible Unstable build when one exists. Returning to Stable remains possible.
- Cache notes for reading offline only, show successful check times and failures honestly, and never authorize downloads from stale cached metadata.
- Update English instructions and DE/EN app translations. Changelogs describe only app-visible changes.

---

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
