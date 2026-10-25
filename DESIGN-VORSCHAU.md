# Local design preview

For normal Unstable downloads and verified updates, use the [rolling Unstable release](https://github.com/PAAAUUULLOOOH/Vitalux/releases/tag/unstable) and follow the [README](README.md). Release ZIPs and AppImages include Python/Qt.

Test a design with separate local preferences:

```bash
bash Designs-testen.sh obsidian_gold
bash Quantum-Core.sh
```

All fifteen standalone designs are available in **Settings → Appearance → Design**. **Obsidian Gold** is the default. **Quantum Core** has a neon reactor HUD; **Nebula Prism** has a floating bottom dock. **Black Glass**, **Black Glass Gold** and **Liquid Silver** retain their separate tiles. Aurora Gold is removed.

Premium palettes/backgrounds remain fixed. Grey selectors explain these restrictions directly; adjustable designs support built-in backgrounds, personal images and preset/custom accents. Personal selections remain saved when a fixed design is active. See the [user guide](USER-GUIDE.md) for the full capability list and image controls.

Preview shortcuts use `design-test-data/` beside the extracted app. Normal Stable and Unstable profiles remain separate. Preview mode disables update checks and installation. Keep the complete runtime, libraries and assets together.

Animations and graphics controls remain available. Software, OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan availability depends on the session and installed drivers.

Third-party notices and source offers remain in [THIRD-PARTY.md](THIRD-PARTY.md).

Crystal Atrium is available through `python -m vitalux.preview crystal_atrium`: the original liquid-glass dashboard from the supplied archive, with its background frozen. `python -m vitalux.preview crystal_glass` selects the previous clear-glass Obsidian composition under its new Crystal Glass name. Both have normal design-gallery tiles.
