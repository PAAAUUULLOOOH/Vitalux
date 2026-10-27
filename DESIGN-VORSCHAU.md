# Local design preview

For normal downloads and verified updates, use the [latest Stable release](https://github.com/PAAAUUULLOOOH/Vitalux/releases/latest) and follow the [README](README.md). Release ZIPs and AppImages include Python/Qt.

Test a design with separate local preferences:

```bash
bash Designs-testen.sh obsidian_gold
bash Quantum-Core.sh
```

Six complete designs are available in **Settings → Appearance → Design**: Obsidian Gold, Glass, Crystal Atrium, Nebula Prism, Quantum Core and Light. All support custom accents and backgrounds. Choices are remembered separately for each design. Original colors, Original background and Reset design restore the active design's factory choices. Retired design names remain available as color/background presets without transferring their effects or layouts.

Preview shortcuts use `design-test-data/` beside the extracted app. Normal Stable and Unstable profiles remain separate. Preview mode disables update checks and installation. Keep the complete runtime, libraries and assets together.

Animations and graphics controls remain available. Software, OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan availability depends on the session and installed drivers.

Third-party notices and source offers remain in [THIRD-PARTY.md](THIRD-PARTY.md).

Crystal Atrium is available through `python -m vitalux.preview crystal_atrium`, with static blue/violet glass, the shared editable dashboard and the current rounded gallery previews.
