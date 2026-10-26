"""Stages of a verified update; transfer progress is separate from overall progress."""
from enum import Enum


class UpdatePhase(str, Enum):
    DOWNLOAD = 'Paket herunterladen …'
    VERIFY = 'Paket prüfen …'
    PREPARE = 'Installation vorbereiten …'
    PARITY = 'Stable-Verfügbarkeit prüfen …'
    STABLE = 'Stable-Paket herunterladen …'
    READY = 'Neustart vorbereiten …'
