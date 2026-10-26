"""Local report translation; captured command output remains byte-for-byte intact."""
from contextvars import ContextVar
import re
from . import i18n

TRANSLATIONS = {'nicht verfügbar': 'not available',
 'unbekannt': 'unknown',
 'vorhanden': 'present',
 'nicht festgestellt': 'not detected',
 'aktiv': 'active',
 'inaktiv': 'inactive',
 'aktiviert': 'enabled',
 'deaktiviert': 'disabled',
 ' nicht installiert': ' not installed',
 'SYSTEMCHECK · ': 'SYSTEM CHECK · ',
 'Messwerte beschreiben den aktuellen Zustand, keine vollständige Hardwareprüfung.': 'Readings '
                                                                                     'describe the '
                                                                                     'current '
                                                                                     'state, not a '
                                                                                     'complete '
                                                                                     'hardware '
                                                                                     'test.',
 'Betriebssystem: ': 'Operating system: ',
 'CPU-Auslastung: ': 'CPU load: ',
 'GPU-Auslastung: ': 'GPU load: ',
 'RAM-Auslastung: ': 'RAM usage: ',
 'CPU-Temperatur': 'CPU temperature',
 'GPU-Temperatur': 'GPU temperature',
 'Systemlaufwerk': 'System drive',
 '-Belegung: ': ' usage: ',
 ' ≥ Warnwert ': ' ≥ warning threshold ',
 'ÜBERSCHRITTENE KONFIGURIERTE WARNWERTE': 'CONFIGURED WARNING THRESHOLDS EXCEEDED',
 'Keine Überschreitung in den verfügbaren Messwerten festgestellt.': 'No exceeded thresholds found '
                                                                     'in the available readings.',
 'Das ist ausdrücklich keine Freigabe oder Garantie für die Hardware.': 'This is not a hardware '
                                                                        'clearance or guarantee.',
 'CRASH INVESTIGATOR\nSystemjournal nicht auswertbar: ': 'CRASH INVESTIGATOR\n'
                                                         'System journal unavailable: ',
 '\nJe nach Distribution fehlen Leserechte.': '\n'
                                              'Read permissions may be missing on this '
                                              'distribution.',
 'CRASH INVESTIGATOR\nKeine kritischen Journalmeldungen im verfügbaren Bootprotokoll.\nNicht alle Abstürze erscheinen zwangsläufig im Journal.': 'CRASH '
                                                                                                                                                 'INVESTIGATOR\n'
                                                                                                                                                 'No '
                                                                                                                                                 'critical '
                                                                                                                                                 'journal '
                                                                                                                                                 'entries '
                                                                                                                                                 'in '
                                                                                                                                                 'the '
                                                                                                                                                 'available '
                                                                                                                                                 'boot '
                                                                                                                                                 'log.\n'
                                                                                                                                                 'Some '
                                                                                                                                                 'crashes '
                                                                                                                                                 'may '
                                                                                                                                                 'not '
                                                                                                                                                 'appear '
                                                                                                                                                 'in '
                                                                                                                                                 'the '
                                                                                                                                                 'journal.',
 'CRASH INVESTIGATOR · aktueller Boot': 'CRASH INVESTIGATOR · current boot',
 'Journalmeldungen (Priorität Fehler und kritischer). Keine automatische Ursachenfeststellung.': 'Journal '
                                                                                                 'entries '
                                                                                                 '(error '
                                                                                                 'priority '
                                                                                                 'and '
                                                                                                 'above). '
                                                                                                 'Causes '
                                                                                                 'are '
                                                                                                 'not '
                                                                                                 'determined '
                                                                                                 'automatically.',
 'MÖGLICHE HARDWARE-/TREIBERHINWEISE:': 'POSSIBLE HARDWARE/DRIVER INDICATIONS:',
 'Keine der gesuchten Signaturen gefunden.': 'None of the searched signatures found.',
 'WEITERE FEHLERMELDUNGEN:': 'OTHER ERROR MESSAGES:',
 'Sitzung: ': 'Session: ',
 ': verbunden': ': connected',
 '  Unterstützte DRM-Modi (Auswahl): ': '  Supported DRM modes (selection): ',
 'Kein angeschlossener DRM-Connector auslesbar. (Container/VM oder eingeschränkte Rechte möglich.)': 'No '
                                                                                                     'connected '
                                                                                                     'DRM '
                                                                                                     'connector '
                                                                                                     'readable. '
                                                                                                     '(A '
                                                                                                     'container/VM '
                                                                                                     'or '
                                                                                                     'restricted '
                                                                                                     'permissions '
                                                                                                     'may '
                                                                                                     'be '
                                                                                                     'the '
                                                                                                     'cause.)',
 'KSCREEN-DOCTOR (Anzeigezustand):': 'KSCREEN-DOCTOR (display state):',
 'KScreen-Auskunft: ': 'KScreen information: ',
 'HDR, VRR, Bildfarbtiefe und die tatsächliche XWayland-Bildausgabe sind': 'HDR, VRR, color depth '
                                                                           'and actual XWayland '
                                                                           'output',
 'nicht mit einem allgemeinen DRM-Status allein verlässlich nachweisbar.': 'cannot be reliably '
                                                                           'established from a '
                                                                           'general DRM status '
                                                                           'alone.',
 'Der aktive Spiel-Renderingpfad muss separat im Spiel/Compositor geprüft werden.': 'The active '
                                                                                    'game '
                                                                                    'rendering '
                                                                                    'path must be '
                                                                                    'checked '
                                                                                    'separately in '
                                                                                    'the '
                                                                                    'game/compositor.',
 'Link-Zustände können im Leerlauf durch Energiesparen abweichen.\n': 'Link states may differ at '
                                                                      'idle due to power saving.\n',
 'GPU-Auslastung zum Messzeitpunkt: ': 'GPU load when sampled: ',
 'Keine GPU-PCIe-Verbindungsdaten verfügbar.': 'No GPU PCIe link data available.',
 '  Aktuell: ': '  Current: ',
 '  Maximal laut Gerät: ': '  Device maximum: ',
 '  HINWEIS: Geringere Linkbreite bei hoher GPU-Last – erneut prüfen.': '  NOTE: Reduced link '
                                                                        'width under high GPU load '
                                                                        '– check again.',
 '  HINWEIS: Geringere Linkbreite kann bei Leerlauf normal sein.': '  NOTE: Reduced link width may '
                                                                   'be normal at idle.',
 '\nPCIe-Generation wird aus der vom Kernel gemeldeten Linkgeschwindigkeit abgeleitet, nicht aus dem Mainboardnamen.': '\n'
                                                                                                                       'PCIe '
                                                                                                                       'generation '
                                                                                                                       'is '
                                                                                                                       'derived '
                                                                                                                       'from '
                                                                                                                       'the '
                                                                                                                       'link '
                                                                                                                       'speed '
                                                                                                                       'reported '
                                                                                                                       'by '
                                                                                                                       'the '
                                                                                                                       'kernel, '
                                                                                                                       'not '
                                                                                                                       'the '
                                                                                                                       'motherboard '
                                                                                                                       'name.',
 'Abstand zu selbst festgelegten Warnwerten ist keine Hersteller-Throttling-Grenze.': 'The margin '
                                                                                      'to your '
                                                                                      'configured '
                                                                                      'warning '
                                                                                      'thresholds '
                                                                                      'is not a '
                                                                                      'manufacturer '
                                                                                      'throttling '
                                                                                      'limit.',
 ': nicht verfügbar': ': not available',
 ' · Herstellergrenzwert nicht bekannt': ' · manufacturer limit unknown',
 ' · Abstand zum Warnwert: ': ' · margin to warning threshold: ',
 'Weitere hwmon-Temperatursensoren: nicht verfügbar': 'Additional hwmon temperature sensors: not '
                                                      'available',
 'NETWORKPULSE · lokaler Check': 'NETWORKPULSE · local check',
 'Kein Ping und keine externen Verbindungen bei diesem Test.': 'This test sends no pings or '
                                                               'external connections.',
 'Netzwerkinformationen nicht verfügbar: ': 'Network information unavailable: ',
 '  Bytes gesendet / empfangen: ': '  Bytes sent / received: ',
 'Paketverlust und Latenz lassen sich nur durch einen ausdrücklich gestarteten Netzwerktest messen.': 'Packet '
                                                                                                      'loss '
                                                                                                      'and '
                                                                                                      'latency '
                                                                                                      'require '
                                                                                                      'an '
                                                                                                      'explicitly '
                                                                                                      'started '
                                                                                                      'network '
                                                                                                      'test.',
 'NETWORKPULSE · manueller Verbindungstest': 'NETWORKPULSE · manual connection test',
 'Ziel: 1.1.1.1; drei ICMP-Echoanfragen (nur nach Klick).': 'Target: 1.1.1.1; three ICMP echo '
                                                            'requests (only after clicking).',
 'Ping nicht ausführbar: ': 'Unable to run ping: ',
 '\nHinweis: ICMP kann durch Netzwerke blockiert werden, ohne dass die Internetverbindung ausfällt.': '\n'
                                                                                                      'Note: '
                                                                                                      'Networks '
                                                                                                      'may '
                                                                                                      'block '
                                                                                                      'ICMP '
                                                                                                      'while '
                                                                                                      'internet '
                                                                                                      'connectivity '
                                                                                                      'still '
                                                                                                      'works.',
 'Kurze CPU-Stichprobe (~0,4 Sekunden); Werte sind Momentaufnahmen.': 'Short CPU sample (~0.4 '
                                                                      'seconds); readings are '
                                                                      'snapshots.',
 '\nCPU-Prozent kann bei Mehrkernprozessen über 100 % liegen.': '\n'
                                                                'CPU percentages can exceed 100% '
                                                                'for multithreaded processes.',
 'Prozessinformationen nicht verfügbar: ': 'Process information unavailable: ',
 'Vergleichsbasis lokal gespeichert: ': 'Baseline saved locally: ',
 '\nStand: ': '\nCaptured: ',
 'CHANGERADAR\nNoch keine Vergleichsbasis vorhanden. Mit „Aktuellen Stand merken“ anlegen.': 'CHANGERADAR\n'
                                                                                             'No '
                                                                                             'baseline '
                                                                                             'yet. '
                                                                                             'Create '
                                                                                             'one '
                                                                                             'with '
                                                                                             '“Remember '
                                                                                             'current '
                                                                                             'state”.',
 'CHANGERADAR\nGespeicherte Vergleichsbasis nicht auswertbar: ': 'CHANGERADAR\n'
                                                                 'Saved baseline unreadable: ',
 'Vergleich mit: ': 'Compared with: ',
 'Änderungen belegen noch keinen ursächlichen Zusammenhang mit einem Fehler.': 'Changes do not '
                                                                               'establish a causal '
                                                                               'link to an error.',
 'GEÄNDERT: ': 'CHANGED: ',
 '  Alt: ': '  Before: ',
 '  Neu: ': '  After: ',
 'Keine Unterschiede in den unterstützten Vergleichsfeldern festgestellt.': 'No differences found '
                                                                            'in the supported '
                                                                            'comparison fields.',
 'BLACKBOX · lokales Ereignisprotokoll': 'BLACKBOX · local event log',
 'Langzeitaufzeichnung: ': 'Long-term recording: ',
 'Datei: ': 'File: ',
 'Nur Warnwert-Übergänge, keine kontinuierliche Speicherung von Rohmessungen.': 'Only warning '
                                                                                'threshold '
                                                                                'transitions; raw '
                                                                                'readings are not '
                                                                                'stored '
                                                                                'continuously.',
 'Noch keine gespeicherten Ereignisse vorhanden.': 'No saved events yet.',
 ' (Schwelle ': ' (threshold ',
 'Blackbox-Daten gelöscht.': 'Blackbox data deleted.',
 'Blackbox konnte nicht gelöscht werden: ': 'Unable to delete Blackbox: ',
 'Warnwert erreicht': 'Warning threshold reached',
 'Entwarnung': 'Back below warning threshold',
 'Messwert nicht verfügbar': 'Reading unavailable',
 ': nicht verfügbar (': ': unavailable ('}
TRANSLATIONS['Warnwert überschritten'] = 'Warning threshold exceeded'
_TEMPLATE_PATTERN = re.compile('|'.join(map(re.escape, sorted(TRANSLATIONS, key=len, reverse=True))))
_capture = ContextVar('diagnostic_report', default=None)

def _translate(template):
    return _TEMPLATE_PATTERN.sub(lambda match: TRANSLATIONS[match[0]], template)

def report_text(template, *values):
    german = template.format(*values) if values else template
    english_template = _translate(template)
    english_values = tuple(TRANSLATIONS.get(value, value) if isinstance(value, str) else value for value in values)
    english = english_template.format(*english_values) if values else english_template
    context = _capture.get()
    if context is not None:
        context[0][german] = english
    return german

def protect_output(text):
    context = _capture.get()
    if context is not None and text:
        context[1].append(text)
    return text

class Report(str):
    def __new__(cls, text, translations=None, protected=None):
        result = super().__new__(cls, text)
        result.translations = translations or {}
        result.protected = protected or []
        return result

    def localized(self, language=None):
        if (language or i18n.lang()) != 'en':
            return str(self)
        if hasattr(self, '_english'):return self._english
        # A single substitution avoids translating inserted values a second time.
        translations = {k:v for k,v in self.translations.items() if k and k != v}
        translations.update({value:value for value in self.protected if value})
        if not translations:
            return str(self)
        pattern = '|'.join(map(re.escape, sorted(translations, key=len, reverse=True)))
        self._english = re.sub(pattern, lambda match: translations[match[0]], str(self))
        return self._english

def capture_report(action):
    context = ({}, [])
    token = _capture.set(context)
    try:
        return Report(action(), *context)
    finally:
        _capture.reset(token)
