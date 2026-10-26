"""Shared page layout and formatting for component and overview pages."""
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .i18n import tr
from .sensors import fmt_bytes


class Page(QWidget):
    def refresh(self, d, h):
        pass

    def __init__(self, title, sub=""):
        super().__init__()
        self.setProperty('page_key', title)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(30, 24, 30, 30)
        self.root.setSpacing(16)
        # Die linke Navigation zeigt bereits klar den aktuellen Bereich an.
        # Zusätzliche Seitenüberschriften oben würden nur Fläche verbrauchen
        # und die Oberfläche unnötig wiederholen.
        self.content = QVBoxLayout()
        self.content.setSpacing(16)
        self.root.addLayout(self.content)
        self.root.addStretch(1)


def _row(*widgets):
    lay = QHBoxLayout()
    lay.setSpacing(16)
    for w in widgets:
        lay.addWidget(w, 1)
    return lay


def _temp_freq(c):
    parts = []
    if c["temp"] is not None:
        parts.append(f"{c['temp']:.0f} °C")
    if c["freq"]:
        parts.append(f"{c['freq'] / 1000:.2f} GHz")
    return " · ".join(parts) or f"{c['cores']} {tr('Kerne')} / {c['threads']} {tr('Threads')}"


def _vram_text(g):
    if g["vram_total"]:
        return f"{fmt_bytes(g['vram_used'])} / {fmt_bytes(g['vram_total'])}"
    return None


def _system_state(sample):
    """Resource-pressure score using *observed* signals only, not a benchmark rank.

    100 represents no identified pressure amongst the available measurements,
    rather than a warranty of hardware health. SMART is evaluated only after a
    real disk scan, and benchmark throughput is never assigned a fabricated
    expected speed (HDD/SSD, cache, controller and workload differ).
    """
    from .monitoring import valid_number

    sample = sample or {}
    cpu = sample.get("cpu") or {}
    ram = sample.get("ram") or {}
    gpu = next(iter(sample.get("gpus") or ()), {}) or {}
    disks = sample.get("disks") or []
    smart = sample.get("smart_reports") or []
    score = 100.0
    issues = []
    observed = 0

    def severity(value, low, high, limit, description):
        nonlocal score, observed
        if not valid_number(value):
            return
        observed += 1
        if value <= low:
            return
        impact = limit * min(1.0, max(0.0, (value - low) / max(1, high-low)))
        score -= impact
        if impact >= 1:
            issues.append((impact, description))

    severity(cpu.get('temp'), 72, 94, 24,
             f"CPU {cpu['temp']:.0f} °C" if valid_number(cpu.get('temp')) else "")
    severity(cpu.get('usage'), 84, 100, 8,
             f"CPU-Auslastung {cpu['usage']:.0f} %" if valid_number(cpu.get('usage')) else "")
    severity(gpu.get('temp'), 72, 92, 22,
             f"GPU {gpu['temp']:.0f} °C" if valid_number(gpu.get('temp')) else "")
    severity(gpu.get('hotspot'), 88, 108, 13,
             f"GPU-Hotspot {gpu['hotspot']:.0f} °C" if valid_number(gpu.get('hotspot')) else "")
    # Sustained GPU load in a game is normal; penalize primarily thermal / memory pressure.
    severity(gpu.get('usage'), 96, 100, 3,
             f"GPU-Auslastung {gpu['usage']:.0f} %" if valid_number(gpu.get('usage')) else "")
    severity(ram.get('percent'), 76, 97, 22,
             f"RAM {ram['percent']:.0f} %" if valid_number(ram.get('percent')) else "")
    severity(ram.get('swap_percent'), 45, 95, 9,
             f"Swap {ram['swap_percent']:.0f} %" if valid_number(ram.get('swap_percent')) else "")
    if valid_number(gpu.get('vram_used')) and valid_number(gpu.get('vram_total')) and gpu['vram_total'] > 0:
        vram = 100 * gpu['vram_used'] / gpu['vram_total']
        severity(vram, 83, 98, 12, f"VRAM {vram:.0f} %")

    # Include every mounted disk, not only /. Bound the combined contribution:
    # ten similarly full mountpoints should not create tenfold punishment.
    disk_penalties = []
    for disk in disks:
        pct = disk.get('percent')
        if not valid_number(pct):
            continue
        observed += 1
        penalty = 16 * min(1., max(0., (pct - 80) / 18))
        if penalty >= 1:
            disk_penalties.append((penalty, f"Laufwerk {disk.get('mount') or disk.get('device') or '?'}: {pct:.0f} % belegt"))
    if disk_penalties:
        disk_penalties.sort(reverse=True)
        score -= min(22, disk_penalties[0][0] + sum(p[0] for p in disk_penalties[1:]) * .25)
        issues.extend(disk_penalties[:2])

    seen_drives = set()
    for drive in smart:
        name = drive.get('name')
        if not name or name in seen_drives or drive.get('_pending'):
            continue
        seen_drives.add(name)
        health = drive.get('health', 'Unbekannt')
        remaining = drive.get('health_percent')
        if health == 'Warnung':
            observed += 1
            score -= 32
            issues.append((32, f"SMART-Warnung {name}"))
        elif health == 'Gut':
            observed += 1
        if valid_number(remaining):
            observed += 1
            penalty = 20 * min(1., max(0., (30 - remaining) / 25))
            if penalty >= 1:
                score -= penalty
                issues.append((penalty, f"SMART {name}: {remaining:.0f} % Restlebensdauer"))
        # Failed SMART attributes are actual evidence even if the generic status says OK.
        attributes = drive.get('attributes') or []
        if any(isinstance(attr, dict) and attr.get('failed') for attr in attributes):
            score -= 23
            issues.append((23, f"SMART-Attributfehler {name}"))
            observed += 1

    if not observed:
        return None, tr('Beobachten'), tr('Noch nicht genügend Sensordaten')
    score = max(0, min(100, round(score)))
    issue = max(issues, key=lambda row: row[0])[1] if issues else ""
    # A missing SMART scan does not mean that disks were checked and are good.
    if not smart and score > 89:
        score = 89
    if not smart and not issue:
        issue = tr('SMART noch nicht geprüft')
    if score >= 90:
        return score, tr('Sehr gut'), issue or tr('Alles im grünen Bereich')
    if score >= 76:
        return score, tr('Stabil'), issue or tr('Leichte Last, aber unkritisch')
    if score >= 58:
        return score, tr('Beobachten'), issue or tr('Einzelne Werte im Blick behalten')
    return score, tr('Auffällig'), issue or tr('Mehrere Werte prüfen')
