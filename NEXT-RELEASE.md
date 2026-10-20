# Release plan — v0.9.5.7

Agreed with the owner on 2026-10-20. Baseline: v0.9.5.6.
Target: v0.9.5.7. Status: implemented in v0.9.5.7.

## Agreed improvements

1. **Refine glass and gold materials — priority.** Use finer gold edges,
   softer reflections and clearer depth between the background, cards and
   controls. Give active elements a restrained highlight. Preserve rendering
   quality and responsiveness.
2. **Strengthen measurement typography and hierarchy.** Use clearer numeric
   sizing and tabular digits to prevent visual jumping. Offer an optional
   compact system header to leave more room for measurements and charts.
3. **Improve chart readability — priority.** Distinguish series in gold themes
   through coordinated brightness and line patterns. Extend the existing hover
   readout with measurement names and the corresponding time.
4. **Explain unavailable measurements consistently.** Apply coherent empty
   states to GPU, system-drive and other measurements. Explain the reason when
   it is known; do not infer unsupported causes or invent readings.
5. **Unify interaction states.** Make hover, pressed, keyboard focus, disabled
   and busy states clearly distinguishable and consistent with each theme's
   materials.
6. **Make closing and restarting fully asynchronous — priority.** Replace GUI
   thread waits for sensor and update workers with safe asynchronous completion.
   Keep the window responsive, retain worker ownership until completion and
   preserve explicit quit and renderer-restart intent.
7. **Replace the stretched accent-color preview.** Replace the full-card-width
   color bar with a small rounded color swatch directly beside the accent-color
   selector. Give it a subtle glass edge and a smooth transition when the color
   changes. The owner approved this design for the next release on 2026-10-20.
8. **Restart Vitalux after a complete settings reset.** Automatically restart
   the application after every successful application-wide reset to defaults,
   including deletion of all personal preferences, so the reset graphics
   renderer is applied at startup. Use the safe asynchronous shutdown/restart
   path. This applies only to actions that reset all settings: individual
   section resets (such as Appearance, MiniHUD or alert thresholds) must not
   trigger an automatic restart. The owner explicitly clarified this scope on
   2026-10-20.
9. **Open revisited categories at the page start.** When a user leaves a
   category and opens it again through the sidebar, show the top of that page
   rather than its previous scroll position. Apply this consistently to all
   categories and set the position before displaying the page. Cancel stale
   scroll animations or focus-driven restoration that could move it back down.
   Explicit search-result navigation should still reach the requested control;
   saved preferences, live readings and measurement history are preserved.
10. **Animate the central heartbeat waveform in the logo.** Add a calm,
    heartbeat-like light impulse travelling from left to right along the
    original central waveform, with a short soft trail, a brief highlight at
    its peaks and a gentle fade between beats. Preserve the recognizable
    waveform and the outer bands' independent slow rotation. Follow the
    effective theme palette, respect reduced/off motion and Ultra Eco, and
    pause hidden animations. Reuse the logo's animation timing without adding
    sensor polling or expensive full-window redraws.
11. **Place the global reset button at the very bottom of Settings.** The
    application-wide restore-defaults action must be the final element, after
    Advanced settings and outside its collapsible content. Keep the automatic
    restart requirement from item 8 scoped to complete resets.
12. **Follow Advanced settings expansion with smooth scrolling.** Animate the
    page's scroll position together with the expanding card so newly revealed
    controls enter the viewport without an initial manual scroll. Keep the
    section header visible when space allows. Coordinate this behavior with
    search-result navigation, respect reduced/off motion, and yield to manual
    scrolling rather than fighting the user's input.
13. **Animate reset-button appearance and disappearance.** Both section reset
    buttons and the global restore-defaults button should softly fade in when
    their associated settings differ from defaults, and fade out after a
    successful reset leaves those settings at defaults. Animate the occupied
    layout space together with opacity to avoid abrupt jumps. Support smooth
    reversals if settings change mid-animation, respect motion preferences,
    and coordinate the global button's exit with the planned safe restart.
14. **Make Obsidian Gold the default theme.** Use `obsidian_gold` for new
    installations, startup without a saved theme and restoration of appearance
    defaults. Keep default and reset entry points consistent while preserving
    existing users' explicitly saved theme choices. Include the new default
    theme in both German and English user-facing release notes.
15. **Match the GitHub README presentation to Obsidian Gold.** At the next
    README update, replace the Black Glass Gold screenshot with a real
    Obsidian Gold screenshot of the English interface and update its caption
    and capture script. Adapt the README header logo and original wordmark to
    Obsidian Gold's palette, including readable variants for GitHub's light and
    dark backgrounds. This replaces the earlier Black Glass Gold screenshot
    preference.

## Release requirements

- Keep the README and user guide current and in English.
- Use Obsidian Gold for the README screenshot and matching header branding.
- Maintain German and English interface translations and user-facing changelogs.
  Changelogs must contain only user-relevant changes inside Vitalux: app
  features, interaction changes and bug fixes. Do not mention GitHub or
  repository changes, README updates, README logos/screenshots, CI/pipeline
  work, or internal housekeeping. Describe improvements through their actual
  effect in the app. The Obsidian Gold default-theme change is relevant;
  matching GitHub presentation changes are not.
- Validate affected interactions, rendering, worker shutdown and update paths
  without reducing visual quality or responsiveness.
- Keep dependency notices and license documentation current.
- Use the GitHub identity **PAAAUUULLOOOH** for uploaded work, never the owner's
  real name.

## Additional quality checks

- Busy diagnostics prevent preference deletion; failed reset commits retain a
  responsive app and restore its reset action.
- Native Qt layouts checked at 100%, 125%, 150% and 200%, including the minimum
  window size and wrapped Advanced settings text.
- Sampling pauses reset rate baselines and preserve chart gaps.
- Low disk space, read-only installation, truncated downloads and interrupted
  installation retain the existing application and preferences.
- Idle audio streams reconnect to the current default output.
- 180 theme/search/navigation cycles completed in about five minutes with no
  Qt object growth and approximately 1 MiB RSS growth after cache warm-up;
  hidden logo animations pause. These measurements describe the test session.
