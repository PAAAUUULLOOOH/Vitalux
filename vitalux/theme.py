"""Vitalux themes with a shared, user-selectable accent palette."""
from . import DEFAULT_THEME
from string import Template
from PySide6.QtGui import QColor
from .premium import COLLECTIONS, KEYS as PREMIUM_MODES

WARN, CRIT, VIOLET, TEAL, CYAN = "#f5b84d", "#f26464", "#a78bfa", "#2dd4bf", "#52d3ff"
_THEMES = {
    "dark": {"bg":"#090f1a", "sidebar":"#0d1725", "card":"#162235", "border":"#2c4157", "track":"#26344a", "grid":"#26384d", "text":"#f0f6ff", "muted":"#adbed0"},
    "light":{"bg":"#f3f7fc", "sidebar":"#e9eff7", "card":"#ffffff", "border":"#c6d4e3", "track":"#dbe5ef", "grid":"#e2eaf3", "text":"#192c42", "muted":"#60728a"},
    "glass":{"bg":"#090f1b", "sidebar":"#101b2c", "card":"#18283c", "border":"#47718e", "track":"#27394f", "grid":"#2b405a", "text":"#f1f7ff", "muted":"#b3c5da"},
    "black_glass":{"bg":"#050506", "sidebar":"#0b0c0f", "card":"#141518", "border":"#454950", "track":"#25262b", "grid":"#303239", "text":"#f3f3f6", "muted":"#b9b9bf"},
    "black_glass_gold":{"bg":"#050504", "sidebar":"#100e0b", "card":"#16130f", "border":"#9a783a", "track":"#3d3120", "grid":"#574326", "text":"#fbe8b8", "muted":"#d0b984"},
    "holographic":{"bg":"#030b13", "sidebar":"#071421", "card":"#091826", "border":"#236282", "track":"#163144", "grid":"#1b4154", "text":"#e9faff", "muted":"#9cbdd1"},
    # Flat and opaque: the cheapest render path, with no atmospheric textures.
    "minimal":{"bg":"#111315", "sidebar":"#191b1d", "card":"#222528", "border":"#35393d", "track":"#373c41", "grid":"#32363a", "text":"#ecedef", "muted":"#b3b6ba"},
}
_THEMES.update({key: {name: pal[name] for name in (
    'bg', 'sidebar', 'card', 'border', 'track', 'grid', 'text', 'muted')}
    for key, pal in COLLECTIONS.items()})
CHOICES = (('dark', 'Dark'), ('light', 'Light'), ('glass', 'Glass'),
           ('black_glass', 'Black Glass'), ('black_glass_gold', 'Black Glass Gold'),
           ('holographic', 'Holographic'), ('minimal', 'Minimalistisch')) + tuple(
               (key, pal['title']) for key, pal in COLLECTIONS.items())
FIXED_MODES = (*PREMIUM_MODES, 'black_glass_gold')


def background_locked():
    from . import eco
    from .design_capabilities import capabilities
    return eco.enabled() or not capabilities(mode())['background']


_mode = DEFAULT_THEME
_accent = "#4f8cff"  # Replaced with the detected distro color at app startup.
BG, SIDEBAR, CARD, BORDER, TRACK, GRID, TEXT, MUTED = (_THEMES[_mode][key] for key in (
    "bg", "sidebar", "card", "border", "track", "grid", "text", "muted"))


def set_mode(value):
    global _mode, BG, SIDEBAR, CARD, BORDER, TRACK, GRID, TEXT, MUTED
    _mode = "dark" if value == "amoled" else value if value in _THEMES else DEFAULT_THEME
    a = _THEMES[_mode]
    BG, SIDEBAR, CARD, BORDER, TRACK, GRID, TEXT, MUTED = (a[x] for x in ("bg", "sidebar", "card", "border", "track", "grid", "text", "muted"))


def mode():
    return _mode


def source_accent():
    """Selected/detected hue before contrast adjustment, for authored assets."""
    return _accent


def set_accent(color):
    global _accent
    candidate = QColor(color)
    if candidate.isValid():
        _accent = candidate.name()


def _luminance(c):
    vals = []
    for v in (c.red(), c.green(), c.blue()):
        v /= 255.0
        vals.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return .2126 * vals[0] + .7152 * vals[1] + .0722 * vals[2]


def accent():
    """Keep user-selected hues readable against white/dark backgrounds."""
    if _mode in PREMIUM_MODES:
        return COLLECTIONS[_mode]['accent']
    if _mode == "black_glass_gold":
        return "#f3cd79"  # The gold theme ignores user and wallpaper accents.
    c = QColor("#52d3ff" if _mode == "holographic" and _accent == "#4f8cff" else _accent)
    if _mode == 'light':
        for _ in range(12):
            if (1.05 / (_luminance(c) + .05)) >= 4.0:
                break
            c = c.darker(113)
    else:
        for _ in range(12):
            if (_luminance(c) + .05) / (.020 + .05) >= 3.9:
                break
            c = c.lighter(116)
    return c.name()


def accent_qcolor(alpha=255):
    c = QColor(accent())
    c.setAlpha(alpha)
    return c


def secondary_accent():
    if _mode in PREMIUM_MODES:
        return COLLECTIONS[_mode]['secondary']
    if _mode == "black_glass_gold":
        return "#ffe4a2"
    c = QColor(accent())
    h, s, v, _ = c.getHsv()
    if h < 0:
        return "#a78bfa"
    return QColor.fromHsv((h + 88) % 360, max(105, min(175, s)), 184 if _mode == "light" else 248).name()


def level_color(pct):
    # Black Glass Gold does not inherit the default yellow/red load palette.
    # Warnings remain semantically distinguishable via their own labels.
    if _mode == "black_glass_gold":
        return "#bb8c45" if pct >= 90 else "#dfb963" if pct >= 75 else accent()
    return CRIT if pct >= 90 else WARN if pct >= 75 else accent()


def blend(foreground, background, strength):
    fg, bg = QColor(foreground), QColor(background)
    return QColor(round(fg.red()*strength + bg.red()*(1-strength)),
                  round(fg.green()*strength + bg.green()*(1-strength)),
                  round(fg.blue()*strength + bg.blue()*(1-strength))).name()


def combo_surface():
    if _mode in PREMIUM_MODES:
        return CARD
    if _mode == "black_glass_gold":
        return CARD
    if _mode == "holographic":
        return CARD
    if _mode == "glass":
        return blend(BORDER, CARD, .17)
    if _mode == "black_glass":
        return blend(CARD, SIDEBAR, .72)
    if _mode == "light":
        return blend(CARD, SIDEBAR, .82)
    return CARD if _mode == "minimal" else blend(CARD, SIDEBAR, .78)


_BLACK_GLASS_GOLD_QSS = Template(r"""
/* Special fixed-gold material; user-selected accents are intentionally ignored. */
#pageTitle, #heroTitle, #telemetryValue, #chipValue, #bigName { color: #ffebb5; }
#cardTitle, #chipTitle, #metricCaption, #overviewLive, #statusTag, #focusReading { color: $ACCENT; }
#pageSub, #metricDetail, #sidebarDistro, #sidebarVersion, #muted { color: #d0b984; }
QToolTip { background: #16130f; border: 1px solid #b99147; color: #ffe7af; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget,
QFrame#alertThresholdField { background: #17130e; color: #fbe8b8; border: 1px solid #9a783a; }
QComboBox::drop-down { background: #211a10; border-left: 1px solid #9a783a; }
QComboBox::drop-down:hover { background: #382913; }
QComboBox QAbstractItemView { background: #16120d; color: #ffe6a9; border: 1px solid #b99147;
    selection-background-color: #403019; selection-color: #fff0c9; }
QComboBox QAbstractItemView::item:selected { background: #403019; color: #fff0c9; }
QPushButton#ghostBtn, QPushButton#langBtn, QToolButton#layoutAction,
QPushButton#systemUpdatesDetails, QPushButton#systemUpdatesInstall {
    background: #211a11; color: #fbe8b8; border: 1px solid #8c703e;
}
QPushButton#ghostBtn:hover, QPushButton#langBtn:hover, QToolButton#layoutAction:hover,
QPushButton#systemUpdatesDetails:hover, QPushButton#systemUpdatesInstall:hover {
    border-color: $ACCENT; background: #382c17; color: #ffefb8;
}
QProgressBar { background: #17130c; border: 1px solid #9a783a; }
QProgressBar::chunk { background: $ACCENT; }
QGroupBox#insightGroup { background: #16120c; border-color: #9a783a; }
#primaryBtn { background: #f3cd79; border-color: #f3cd79; color: #160e03; }
QComboBox:disabled, QPushButton:disabled { color: #877858; border-color: #51432c; background: #16120e; }
""")

_HOLOGRAPHIC_QSS = Template(r"""
/* Entirely opaque, angular native HUD controls: no backdrop-filter or glass. */
QWidget { selection-background-color: $ACCENT; }
QToolTip { background: #081827; border: 1px solid $ACCENT; color: #e9faff; }
#cardTitle { color: $ACCENT; font-size: 11px; font-weight: 800; letter-spacing: 1.4px; }
#pageTitle { color: #e9faff; }
#chipTitle, #metricCaption, #systemUpdatesStatus { color: #9cbdd1; }
#telemetryValue, #chipValue { color: #eefeff; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget,
QFrame#alertThresholdField {
    background: #071b2a; color: #e9faff; border: 1px solid #236282;
    border-radius: 2px; padding: 8px 11px;
}
QComboBox { padding-right: 24px; }
QComboBox::drop-down { background: #0a2638; border: none; border-left: 1px solid #236282;
    border-radius: 0px; width: 21px; }
QComboBox QAbstractItemView { background: #061725; border: 1px solid $ACCENT;
    selection-background-color: #12384d; color: #e9faff; }
QComboBox QAbstractItemView::item:selected { background: #12384d; color: #ffffff; }
QPushButton#ghostBtn, QPushButton#langBtn, QToolButton#layoutAction,
QPushButton#systemUpdatesDetails, QPushButton#systemUpdatesInstall {
    background: #0a2436; border: 1px solid #236282; border-radius: 2px;
    color: #d9f9ff;
}
QPushButton#ghostBtn:hover, QPushButton#langBtn:hover, QToolButton#layoutAction:hover,
QPushButton#systemUpdatesDetails:hover, QPushButton#systemUpdatesInstall:hover {
    background: #113a4f; border: 1px solid $ACCENT; color: #ffffff;
}
QPushButton#langBtn:checked { background: #104155; border-color: $ACCENT; color: $ACCENT; }
QPushButton#primaryBtn { border-radius: 2px; background: $ACCENT;
    color: #041521; border: 1px solid $ACCENT; }
QProgressBar { background: #081e2e; border: 1px solid #236282;
    border-radius: 2px; min-height: 12px; }
QProgressBar::chunk { background: $ACCENT; border-radius: 1px; }
QGroupBox#insightGroup { background: #091b2a; border: 1px solid #236282; border-radius: 2px; }
QToolButton#customAccentRemove { border-radius: 2px; }
QLabel#benchmarkResultRead, QLabel#benchmarkResultWrite { border-radius: 3px; }
QScrollBar::handle:vertical { background: #236282; border-radius: 2px; }
""")

_QSS = Template(r"""
QWidget { background: transparent; color: $TEXT; font-family: "Inter", "Noto Sans", "Cantarell", "DejaVu Sans", sans-serif; font-size: 13px; }
QMainWindow { background: $BG; }
#root, QFrame#sidebar { background: transparent; border: none; }
#card, #heroCard, #chip { background: transparent; border: none; }
#cardTitle { color: $MUTED; font-size: 11px; font-weight: 750; letter-spacing: 1.2px; }
#pageTitle { font-size: 28px; font-weight: 800; }
#pageSub, #metricDetail, #sidebarDistro, #sidebarVersion, #muted { color: $MUTED; }
#bigName { font-size: 18px; font-weight: 800; }
#heroTitle { font-size: 22px; font-weight: 800; }
#heroUptime { color: $MUTED; font-size: 12px; font-weight: 650; }
#strong, #distroName, #gaugeTitle { font-weight: 700; }
#telemetryValue { font-size: 29px; font-weight: 900; }
#systemUpdatesTitle { color: $TEXT; font-size: 12px; font-weight: 800; }
#systemUpdatesStatus { color: $MUTED; font-size: 11px; }
QToolButton#updateCheckButton { background: transparent; border: none; color: $ACCENT; font-size: 22px; padding: 0px; min-width: 22px; max-width: 22px; }
QToolButton#updateCheckButton:hover { color: $TEXT; }
QPushButton#systemUpdatesDetails, QPushButton#systemUpdatesInstall {
    background: $BUTTON_BG; color: $TEXT; border: 1px solid $BORDER;
    border-radius: 6px; padding: 5px 9px; font-weight: 650; font-size: 11px;
}
QPushButton#systemUpdatesDetails:hover, QPushButton#systemUpdatesInstall:hover { border-color: $ACCENT; }
QPushButton#systemUpdatesInstall:enabled { color: $ACCENT; }
QPushButton#systemUpdatesInstall:disabled { color: $MUTED; }

#metricCaption { color: $MUTED; font-size: 11px; font-weight: 800; }
#overviewLive, #statusTag { color: $ACCENT; font-weight: 800; }
#sidebarDistro { font-size: 11px; }
#sidebarVersion { font-size: 10px; }
#navBtn { background: transparent; border: none; padding: 0; color: $TEXT; font-size: 13px; font-weight: 600; }
QScrollArea, QScrollArea#glassScroll, QScrollArea#glassScroll > QWidget,
QScrollArea#glassScroll QWidget#qt_scrollarea_viewport, QStackedWidget,
QFrame#glassNavRail { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $BORDER; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 9px; margin: 2px; }
QScrollBar::handle:horizontal { background: $BORDER; border-radius: 3px; min-width: 32px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
#madeBy { font-size: 32px; font-weight: 800; color: $ACCENT; }
#supportCredit { font-size: 14px; font-weight: 600; color: $ACCENT; }
#langBtn, #ghostBtn { background: $BUTTON_BG; border: 1px solid $BORDER; border-radius: 10px; color: $TEXT; padding: 9px 14px; font-weight: 700; }
#langBtn:checked { background: $ACTIVE_BG; border-color: $ACCENT; color: $ACCENT; }
#ghostBtn:hover, #langBtn:hover { border-color: $ACCENT; background: $ACTIVE_BG; }
QComboBox:hover, QSpinBox:hover, QListWidget:hover, QLineEdit:hover {
    border-color: $ACCENT_HOVER_BORDER;
}
QScrollBar::handle:vertical:hover { background: $ACCENT_HOVER_BORDER; }
#ghostBtn:disabled { color: $MUTED; }
#primaryBtn { background: $ACCENT; border: 1px solid $ACCENT; color: $BUTTON_TEXT; border-radius: 11px; padding: 10px 18px; font-weight: 800; }
#primaryBtn:hover { background: $ACCENT_HOVER; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget { background: $INPUT_BG; border: 1px solid $BORDER; border-radius: 9px; color: $TEXT; padding: 8px 12px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QListWidget:focus { border-color: $ACCENT; }
QComboBox { padding-right: 28px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right;
    width: 25px; border: none; border-left: 1px solid $BORDER;
    border-top-right-radius: 8px; border-bottom-right-radius: 8px;
    background: $BUTTON_BG; }
QComboBox::drop-down:hover { background: $ACTIVE_BG; }
QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
QComboBox QAbstractItemView { background: $INPUT_BG; color: $TEXT;
    border: 1px solid $BORDER; outline: none; padding: 0px;
    selection-background-color: $ACTIVE_BG; selection-color: $TEXT; }
QComboBox QAbstractItemView::item { background: transparent; color: $TEXT;
    border: none; padding: 7px 8px; min-height: 22px; }
QComboBox QAbstractItemView::item:selected { background: $ACTIVE_BG; color: $TEXT; }
/* Separate native line editor and unit: unlike QSpinBox the text never clips
   to a one-pixel strip when KDE/Qt uses a stylesheet without spin buttons. */
QFrame#alertThresholdField { background: $INPUT_BG; border: 1px solid $BORDER; border-radius: 9px; padding: 0px; }
QLineEdit#alertThresholdNumber, QLineEdit#alertThresholdNumber:focus {
    background: transparent; border: none; border-radius: 0px;
    margin: 0px; padding: 0px; min-width: 0px;
    color: $TEXT; font-size: 12px; font-weight: 650;
}
QLabel#alertThresholdUnit { background: transparent; border: none;
    padding: 0px; color: $TEXT; font-size: 12px; font-weight: 650; }
QTableWidget { background: $INPUT_BG; alternate-background-color: $CARD; color: $TEXT;
    border: 1px solid $BORDER; border-radius: 8px; gridline-color: $GRID; }
QHeaderView::section { background: $CARD; color: $MUTED; border: none;
    border-bottom: 1px solid $BORDER; padding: 8px; font-weight: 700; }
QTableWidget::item { padding: 6px; border-bottom: 1px solid $GRID; }
QTableWidget::item:selected { background: $ACTIVE_BG; color: $TEXT; }
QTableWidget QTableCornerButton::section { background: $CARD; border: none; }
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab { background: $INPUT_BG; color: $MUTED; border: 1px solid $BORDER;
    border-radius: 8px; margin: 0px 6px 10px 0px; padding: 10px 16px; }
QTabBar::tab:selected { background: $ACTIVE_BG; color: $ACCENT; border-color: $ACCENT; }
QListWidget::item { background: $INPUT_BG; color: $TEXT; }
QListWidget::item:selected { background: $ACTIVE_BG; color: $TEXT; }
QToolButton#customAccentRemove { background: $BUTTON_BG; border: 1px solid $BORDER;
    border-radius: 8px; color: $MUTED; font-size: 19px; padding: 0px; }
QToolButton#customAccentRemove:hover { color: $ACCENT; border-color: $ACCENT; background: $ACTIVE_BG; }
/* Vitalux Insights: nested cards follow the active native design. */
QGroupBox#insightGroup {
    background: $INPUT_BG;
    border: 1px solid $BORDER;
    border-radius: 12px;
    margin-top: 16px;
    padding: 12px 10px 10px 10px;
    color: $TEXT;
}
QGroupBox#insightGroup::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: $TEXT;
    font-weight: 750;
}
QLabel#focusReading { color: $ACCENT; font-size: 29px; font-weight: 800; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QCheckBox::indicator:checked { background: $ACCENT; border: 1px solid $ACCENT; border-radius: 4px; }
QToolTip { background: $CARD; border: 1px solid $BORDER; color: $TEXT; }
QToolButton#tileMoveHint, QToolButton#tileRemoveHint {
    background: transparent; border: none; border-radius: 0px;
    color: $MUTED; padding: 0px; font-size: 11px; font-weight: 600;
}
QToolButton#tileRemoveHint { font-size: 17px; font-weight: 500; }
QToolButton#tileMoveHint:hover, QToolButton#tileRemoveHint:hover { color: $ACCENT; }
QToolButton#layoutAction {
    background: $BUTTON_BG; border: 1px solid $BORDER;
    border-radius: 8px; padding: 2px 9px;
    color: $MUTED; font-size: 11px; font-weight: 600;
}
QToolButton#layoutAction:hover {
    color: $ACCENT; border-color: $ACCENT_HOVER_BORDER; background: $ACTIVE_BG;
}
QToolButton#layoutAction:disabled { color: $MUTED; }
QWidget#layoutActions { background: transparent; }
QWidget#dashboardToolbar { background: transparent; }
#chipValue { font-weight: 800; font-size: 16px; color: $TEXT; }
#chipTitle { color: $MUTED; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QProgressBar { background: $INPUT_BG; border: 1px solid $BORDER; border-radius: 8px; min-height: 12px; text-align: center; }
QProgressBar::chunk { background: $ACCENT; border-radius: 7px; }
QSlider::groove:horizontal { height: 4px; background: $TRACK; border-radius: 2px; }
QSlider::sub-page:horizontal { background: $ACCENT; border-radius: 2px; }
QSlider::handle:horizontal { width: 12px; margin: -5px 0; background: $CARD;
    border: 1px solid $ACCENT; border-radius: 6px; }
QSlider::handle:horizontal:hover { background: $ACCENT; }
QSlider::groove:vertical { width: 4px; background: $TRACK; border-radius: 2px; }
QSlider::add-page:vertical { background: $ACCENT; border-radius: 2px; }
QSlider::handle:vertical { height: 12px; margin: 0 -5px; background: $CARD;
    border: 1px solid $ACCENT; border-radius: 6px; }
QSlider::handle:vertical:hover { background: $ACCENT; }
QLabel#benchmarkResultRead, QLabel#benchmarkResultWrite { background: $RESULT_BG; border: 1px solid $RESULT_BORDER; border-radius: 14px; font-size: 24px; font-weight: 800; }
QLabel#benchmarkResultRead { color: $ACCENT; }
QLabel#benchmarkResultRead[resultState="running"], QLabel#benchmarkResultWrite[resultState="running"] { border: 2px solid $ACCENT; }
QLabel#benchmarkResultRead[resultState="pending"], QLabel#benchmarkResultWrite[resultState="pending"] { color: $MUTED; }
QLabel#benchmarkResultRead[resultState="done"] { border-color: $ACCENT; }
QLabel#benchmarkResultWrite[resultState="done"] { border-color: $SECONDARY; }
QLabel#benchmarkResultWrite { color: $SECONDARY; }
#wordmarkWrap { background: transparent; }
""")


def stylesheet():
    from . import eco
    base = accent()
    pal = _THEMES[_mode]
    light = _mode == "light"
    result_bg = blend(base, pal['card'], .055 if light else .10)
    active_bg = blend(base, pal['sidebar'], .18 if light else .22)
    qss = _QSS.substitute(
        BG=BG, TEXT=TEXT, MUTED=MUTED, CARD=CARD, BORDER=BORDER, TRACK=TRACK, GRID=GRID,
        ACCENT=base, ACCENT_HOVER=QColor(base).lighter(115).name() if light else QColor(base).lighter(128).name(),
        SECONDARY=secondary_accent(), BUTTON_TEXT="#07111b" if not light else "#ffffff",
        INPUT_BG=blend(base, pal['card'], .035 if light else .045),
        COMBO_BG=combo_surface(),
        BUTTON_BG=blend(base, pal['card'], .07 if light else .10),
        ACTIVE_BG=active_bg, RESULT_BG=result_bg,
        RESULT_BORDER=blend(base, pal['border'], .30),
        ACCENT_HOVER_BORDER=blend(base, pal['border'], .48 if light else .60),
    )
    # Settings-local search remains themed to the selected palette.
    qss += f"""
    QPushButton:focus, QToolButton:focus, QComboBox:focus, QLineEdit:focus {{
        border: 1px solid {base}; }}
    QPushButton:pressed, QToolButton:pressed {{
        background-color: {active_bg}; border-color: {base}; }}
    QPushButton:disabled, QToolButton:disabled {{
        color: {MUTED}; border-color: {GRID}; }}
    QLineEdit#settingsSearch {{
        background: {CARD}; color: {TEXT}; border: 1px solid {BORDER};
        padding: 9px 12px; border-radius: 7px;
    }}
    QListWidget#settingsSearchResults {{
        background: {CARD}; color: {TEXT}; border: 1px solid {BORDER};
    }}
    """
    if _mode in PREMIUM_MODES:
        from .premium import stylesheet as premium_stylesheet
        return qss + premium_stylesheet(_mode)
    if _mode == "black_glass_gold":
        return qss + _BLACK_GLASS_GOLD_QSS.substitute(ACCENT=base)
    if eco.enabled():
        # Intentionally primitive Qt widgets: no rounded cards, light effects,
        # shadow treatments or decorative surfaces. All selectors are native.
        qss += """
        QWidget#root, QFrame#glassNavRail, QScrollArea, QStackedWidget {
            background-color: #111315;
        }
        QPushButton, QComboBox, QLineEdit, QSpinBox, QTextEdit,
        QListWidget, QToolButton, QProgressBar, QFrame#alertThresholdField {
            border-radius: 0px; }
        QPushButton:hover, QToolButton:hover { background-color: #222528; }
        """
    return qss + (_HOLOGRAPHIC_QSS.substitute(ACCENT=base) if _mode == "holographic" else "")
