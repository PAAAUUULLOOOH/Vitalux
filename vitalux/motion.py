"""User-selectable, low-overhead motion profiles.

All durations are resolved at animation start, so changes take effect without
rebuilding pages or restarting live measurements.
"""
from . import DEFAULT_THEME
from . import settings, eco

MODES = ("smooth", "reduced", "off")
TIMINGS = dict(hover=160, transition=300, search=300, reflow=300)


def timing(action):
    """One rhythm for navigation, galleries and fixed header controls."""
    return duration(TIMINGS[action])


def level():
    if eco.enabled():
        return 'off'
    value = settings.observed("motion", "smooth")
    return value if value in MODES else "smooth"


def duration(milliseconds):
    base = max(0, int(milliseconds))
    profile = level()
    if profile == "off" or eco.enabled() or settings.observed("theme", DEFAULT_THEME) == "minimal":
        return 0
    if profile == "reduced":
        return max(50, min(110, round(base * .43)))
    return base


def enabled():
    return not eco.enabled() and level() != "off" and settings.observed("theme", DEFAULT_THEME) != "minimal"
