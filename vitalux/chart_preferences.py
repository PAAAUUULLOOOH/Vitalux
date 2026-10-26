"""Small, per-page and per-device chart preferences, independent of translations."""
from . import settings


def load(key):
    value = settings.get('chart_preferences', {})
    entry = value.get(key) if isinstance(value, dict) else None
    return entry if isinstance(entry, dict) else {}


def save(key, seconds, enabled):
    value = settings.get('chart_preferences', {})
    if not isinstance(value, dict):
        value = {}
    value[key] = dict(seconds=seconds, enabled=list(enabled))
    settings.set('chart_preferences', value)
