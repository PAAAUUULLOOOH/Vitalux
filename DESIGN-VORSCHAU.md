# Local design preview

For normal downloads and verified updates, use the [latest Stable release](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest) and follow the [README](README.md). Release ZIPs and AppImages include Python/Qt.

Test a design with separate local preferences:

```bash
bash Designs-testen.sh obsidian_gold
bash Quantum-Core.sh
```

Eight complete designs are available in **Settings → Appearance → Design**: Obsidian Gold, Glass, Crystal Atrium, Nebula Prism, Quantum Core, Light, Aurora Bloom and Eclipse Crystal. All support custom accents and backgrounds. Choices are remembered separately for each design. Original colors, Original background and Reset design restore the active design's factory choices. Retired design names remain available as color/background presets without transferring their effects or layouts.

Preview shortcuts use `design-test-data/` beside the extracted app. Normal Stable and Unstable profiles remain separate. Preview mode disables update checks and installation. Keep the complete runtime, libraries and assets together.

Animations and graphics controls remain available. CPU is the default renderer and works on X11 and Wayland. The optional X11/OpenGL renderer needs a suitable X server or XWayland and graphics driver.

Third-party notices and source offers remain in [THIRD-PARTY.md](THIRD-PARTY.md).

Crystal Atrium is available through `python -m vitalux.preview crystal_atrium`, with its original static Atrium background, the shared editable dashboard and the current rounded gallery previews.
