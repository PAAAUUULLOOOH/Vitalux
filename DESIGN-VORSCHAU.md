# Local design preview

For normal Unstable downloads and verified updates, use the [rolling Unstable release](https://github.com/PAAAUUULLOOOH/Vitalux/releases/tag/unstable) and follow the [README](README.md). Release ZIPs and AppImages include Python/Qt.

To test appearance with separate local preferences:

```bash
bash Designs-testen.sh obsidian_gold
```

Other surface keys include `black_glass_gold`, `aether_glass` and `eclipse_crystal`. Internal legacy keys remain for saved-profile compatibility; the visible names are **Obsidian** and **Black Glass**.

Settings separates **Design**, **Background** and **Accent colors**. All backgrounds and preset/custom colors work with every surface. **Own image…** imports personal wallpapers within Background, alongside placement and optional tint. Obsidian defaults to its original gold appearance. Champagne, Aurora and Liquid Silver are background/color choices rather than duplicate surface tiles.

The older `Obsidian-Gold.sh`, `Champagne-Glass.sh` and `Aurora-Gold.sh` shortcuts still open the corresponding Obsidian background/color combination. They use `design-test-data/` beside the extracted app; normal Stable and Unstable profiles remain separate. Preview mode disables update checks and installation. Keep the complete runtime, libraries and assets together.

Animations, sound and graphics controls are documented in the [user guide](USER-GUIDE.md). Native renderer checks exercise software, OpenGL, X11/OpenGL, Wayland/OpenGL and Wayland/Vulkan with real frames and live samples; availability on physical hardware depends on installed drivers.

Third-party notices and source offers remain in [THIRD-PARTY.md](THIRD-PARTY.md).
