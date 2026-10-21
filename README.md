<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/vitalux-readme-dark-animated.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/vitalux-readme-light-animated.svg">
    <img src="assets/vitalux-readme-light-animated.svg" alt="Vitalux — rotating gold circle, traced heartbeat and shimmering VITALUX lettering" width="285">
  </picture>
</p>

<p align="center"><strong>Your Linux system, clearly in view.</strong><br>A native desktop monitor with live telemetry, glass interfaces and practical hardware diagnostics.</p>
<p align="center"><a href="https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest"><strong>Download</strong></a> · <a href="USER-GUIDE.md">User guide</a> · <a href="CHANGELOG.en.md">Changelog</a> · <a href="https://github.com/PAAAUUULLOOOH/Vitalux/issues">Support</a> · <a href="THIRD-PARTY.md">Licenses</a></p>

![Vitalux running in English with Obsidian Gold and real system measurements](assets/vitalux-dashboard-preview.png)

## What Vitalux offers

- **Live system monitoring:** CPU, GPU, memory, storage, networking and Linux hardware sensors, with charts and local history.
- **A configurable workspace:** rearrange dashboard cards, choose twelve visual designs, or keep essential measurements visible in MiniHUD.
- **Application networking:** inspect per-app connections and observed traffic, set usage warnings, and authorize TCP/UDP accounting and reversible session blocks.
- **Two signature designs:** Aether Glass uses platinum and violet/cyan optical glass; Eclipse Crystal combines faceted black crystal with horizontal navigation. Both have coordinated fixed palettes and backgrounds.
- **Thoughtful interactions:** animated theme previews, a coordinated animated logo and wordmark, predictive settings search and optional crystal feedback sounds.
- **Useful diagnostics:** SMART information, configurable alerts, disk benchmarks and local diagnostic reports.
- **German and English:** switch the interface, guide and release history without interrupting monitoring.
- **Local operation:** monitoring works offline. Hostname resolution runs only on request. Update checks contact the official GitHub release service; installation requires your action.

Vitalux focuses on monitoring and diagnostics, with optional session network controls. It does not provide GPU overclocking or fan control. Missing sensor readings remain unavailable rather than being estimated.

## Requirements

Use **Linux x86-64** with an X11 or Wayland desktop. The portable packages target current distributions with **glibc 2.38 or newer**. Python 3.12 and Qt are included; running a release does not require pip or a system Python installation.

CPU rendering is the default. Optional GPU renderers require suitable drivers and session support. Sensor and SMART availability depends on your hardware, kernel, drivers and permissions; some diagnostic tools are supplied by your distribution.

**Optional full app networking:** requires cgroup v2 with cgroup BPF support, Polkit (`pkexec`) and `/usr/bin/python3` on the host. The normal portable app still needs no system Python. Authorization is requested from **Network → Apps & connections**. Basic TCP counters and connection inspection remain available where the kernel exposes them. See the [network guide](USER-GUIDE.md#apps-and-network-connections) for measurement scope and session-block behavior.

## Get started

### AppImage

Download the `.AppImage` from [the latest release](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest). For v0.9.6.1:

```bash
chmod +x Vitalux-v0.9.6.1-x86_64.AppImage
./Vitalux-v0.9.6.1-x86_64.AppImage
```

The first-run dialog offers installation in your user account, including an application-menu entry. Administrator rights are not required. You can also choose **Run once**, or run explicitly without integration:

```bash
./Vitalux-v0.9.6.1-x86_64.AppImage --portable
```

To add or remove desktop integration later, use `--install` or `--uninstall`. Uninstalling keeps personal preferences.

### Portable ZIP or source ZIP

Download **`Vitalux-v0.9.6.1-linux-x86_64.zip`**, extract the entire archive into its own writable folder, and run:

```bash
cd Vitalux-v0.9.6.1
bash run.sh
```

Keep `runtime/`, `lib/`, `tools-lib/`, `assets/` and the launcher together. **Code → Download ZIP** works too: its checked-in runtime is verified and extracted offline on first launch. That initial extraction requires `tar`, `xz` and `sha256sum`.

The `Update-von-...zip` download is a manual overlay for the immediately preceding ZIP edition. Use the full ZIP for a fresh installation; AppImages use their own update path.

## Make it yours

**Obsidian Gold is the default appearance.** Open **Settings → Appearance** to select a design. Existing installations retain their saved choice. Preview tiles grow gently on hover. Their color-wheel and image indicators fade in to show accent/background customization; a grey lock marks fixed options. All designs use the same complete preview grid. **Obsidian Gold, Champagne Glass, Black Glass Gold, Aurora Gold, Aether Glass and Eclipse Crystal** use coordinated fixed palettes and backgrounds; their grey fields are disabled. Holographic also has a fixed background. Compatible designs retain your personal accent colors and images.

A compact glass swatch previews the current accent. Overview uses a **compact system header by default**, leaving more space for measurements and charts. The slimmer circular logo rotates around a clearly traced heartbeat, while a soft metallic reflection travels across the new **VITALUX** wordmark. Both follow the selected palette; each collection has its own coordinated identity. Custom accents give the circle a slightly richer finish. The animated SVG header above uses the same vector geometry, materials and seamless motion periods as the app, and stays sharp at every size.

<details>
<summary><strong>Explore the two signature designs</strong></summary>

**Aether Glass** — floating navigation, platinum glass and violet/cyan optical surfaces.

![Aether Glass with floating navigation and native system instruments](assets/vitalux-aether-glass-preview.png)

**Eclipse Crystal** — horizontal navigation, champagne highlights and faceted black crystal.

![Eclipse Crystal with horizontal navigation and faceted instruments](assets/vitalux-eclipse-crystal-preview.png)

</details>

The settings magnifier predicts matches and glides to their controls. After selecting a result, the search remains visible for five seconds, then closes softly. **Advanced settings** expands for graphics renderers and Maintenance, with the page following its reveal; relevant searches open it automatically. The full **Restore defaults** action sits below it, at the very bottom. Reset buttons appear and disappear smoothly. A full reset restarts Vitalux; individual section resets apply in place. Reopening a sidebar category starts at the top.

A soft, damped tone accompanies Vitalux buttons, selections and dropdowns at 50% default volume. On/off settings use coordinated switches; chart and other multiple selections retain checkmarks. Adjust volume or disable them in Settings. Scrolling over a closed dropdown never changes its selection. Animation profiles and Ultra Eco remain available. Charts identify hovered measurements and times; missing readings and sampling interruptions remain gaps.

## Stable and Unstable channels

Click **Stable** or **Unstable** under **Updates → Browse channel** to read the current changelog. Clicking a tab only changes the view. A separate action prepares the installation and shows the running version alongside its destination. Switching to Unstable is available only when a verified test build contains real application changes beyond the current Stable baseline; a larger build number or a Stable mirror does not qualify. Returning to Stable remains possible.

After installation, choose **Restart now** or **Later**. A prepared installation stays marked **Restart required**, even while browsing the other channel. It cannot generate another update offer or be installed twice. With Later, the prepared ZIP or AppImage is activated on normal exit without reopening Vitalux. On your next launch the new version uses its own profile.

Stable keeps its existing preferences. Unstable automatically creates a separate profile on first launch using Stable's preferences and imported backgrounds. Subsequent launches, updates and switches preserve each profile; migrations receive local backups (the latest five per channel). **Import settings** explicitly transfers compatible preferences with a backup and CPU-rendered restart. No fresh-profile button is needed.

When your test changes reach Stable, Vitalux offers a notice and lets you view the Stable destination. A newer eligible Unstable build takes precedence. A single rolling prerelease supplies test packages; when it has caught up with Stable it is marked **Unstable — based on Stable v…**, without creating another mirror build or consuming another test number. GitHub's **Latest** download always remains Stable. Technical test versions are retained internally for correct ordering and recovery.

Channel changelogs are cached for offline reading with their check time. Offline or failed checks are reported explicitly; cached information alone cannot authorize an installation.

## Updates and verification

Vitalux checks official GitHub releases at startup and approximately every six hours. **Updates** provides a manual check and release notes in the selected language. Installation verifies the download's SHA-256 digest, retains a recovery copy and preserves personal preferences. The changelog remains available offline.

To check a manually downloaded package, download its release's `SHA256SUMS.txt` file into the same directory and run:

```bash
sha256sum --ignore-missing -c Vitalux-v0.9.6.1-SHA256SUMS.txt
```

A matching checksum confirms consistency with that manifest; it is not an independent digital signature.

## Help and troubleshooting

<details>
<summary><strong>The application does not start, or Python appears to be missing</strong></summary>

Extract the complete ZIP rather than launching a file inside the archive. In its extracted folder, run:

```bash
bash Portable-pruefen.sh
bash run.sh
```

The source ZIP includes its runtime as well. Re-extract into a new folder if the existing runtime is incomplete.
</details>

<details>
<summary><strong>Graphics problems or an AppImage/FUSE error</strong></summary>

For the ZIP edition, force the default CPU renderer:

```bash
VITALUX_RENDERER=software bash run.sh
```

For an AppImage that cannot mount through FUSE, extract its payload instead:

```bash
./Vitalux-v0.9.6.1-x86_64.AppImage --appimage-extract
VITALUX_RENDERER=software bash squashfs-root/AppRun --portable
```

GPU modes are experimental. Select them under **Settings → Advanced settings** and use **Restart now** to apply a change. Closing or restarting waits asynchronously for active work to finish; the window remains responsive.
</details>

<details>
<summary><strong>Logs, settings and reporting an issue</strong></summary>

| Item | Default location |
| --- | --- |
| Preferences | `~/.config/vitalux/settings.json` |
| Runtime and error logs | `~/.local/state/vitalux/` |
| Installed AppImage | `~/.local/opt/vitalux/Vitalux.AppImage` |
| Desktop entry | `~/.local/share/applications/vitalux.desktop` |
| Local launch command | `~/.local/bin/vitalux` |

XDG environment variables can change these locations. To inspect the latest startup messages:

```bash
tail -n 80 "${XDG_STATE_HOME:-$HOME/.local/state}/vitalux/vitalux.log"
```

Reports and logs remain local unless you share them. For [bug reports](https://github.com/PAAAUUULLOOOH/Vitalux/issues), include the Vitalux version, distribution, desktop/session, renderer and reproduction steps. Review exported logs for personal system details before posting them.

Explicit `Designs-testen.sh` previews use a separate `design-test-data/` profile and disable updates. Use normal `run.sh` or the AppImage for release updates.
</details>

See the [user guide](USER-GUIDE.md) or **About → Guide** for more help. Write benchmarks create temporary data on the selected drive and start only when requested.

## Development

Use Python 3.12. A typical isolated development setup is:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m vitalux
.venv/bin/python scripts/run-regressions.py
```

Branding uses outlined SVG geometry and the separate `assets/brand/palettes.json` configuration. After editing a palette, regenerate assets with `.venv/bin/python scripts/build-brand-assets.py` and README artwork with `.venv/bin/python scripts/build-readme-brand.py`; no external fonts or tracing tools are needed.

Native renderer checks use `scripts/run-graphics-checks.py` with Xvfb, Weston and Mesa. `scripts/check-ui-audio.py` tests repeated sound playback through a private PulseAudio sink. CI also validates offline startup, AppImage integration, update/rollback and release checksums. Releases advance from `.0` through `.9`, then increment the preceding component: `0.9.5.9 → 0.9.6.1`.

## Credits and licenses

Developed by **[PAAAUUULLOOOH](https://github.com/PAAAUUULLOOOH)**. Special thanks to **[TimBooH](https://github.com/TimBooH)** for help with custom backgrounds and graphics integration.

Vitalux includes CPython, Qt/PySide6, Shiboken, psutil, fio, libaio and supporting libraries. Full notices, versions, source references and LGPL replacement instructions are in **[THIRD-PARTY.md](THIRD-PARTY.md)** and **[licenses/](licenses/README.md)**. AppImage runtime dependencies are listed there too. Each release supplies a separate **ThirdPartySources ZIP**, so source access does not enlarge the normal application download.

The original Vitalux code and branding currently have no general public license; see **[LICENSE-NOTICE.md](LICENSE-NOTICE.md)**. Third-party rights, warranty disclaimers and trademark rules remain independent. This documentation does not claim legal clearance for original artwork or third-party trademarks.
