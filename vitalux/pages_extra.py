from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout,QButtonGroup

from . import APP_NAME, __version__, changelog, settings, theme, profiles
from .i18n import tr
from .pages import Page
from .ui_locale import QLabel, QPushButton, QMessageBox
from .widgets import Bar, Card, KeyValue, label

AUTHOR_URL = "https://github.com/PAAAUUULLOOOH"
CREDIT_URL = "https://github.com/TimBooH"
CREDIT_TEXT = "Danke an: TimBooH für die Unterstützung bei der Integration eigener Hintergrundbilder und der Grafikausgabe (OpenGL/CPU-Rendering)."

STATUS_TEXT = {
    'preview': 'Lokale Designvorschau · Updates sind deaktiviert.',
    "idle": "Die Updateprüfung startet automatisch.",
    "checking": "Prüfe GitHub auf eine neue Vitalux-Version …",
    "uptodate": "Vitalux ist auf dem neuesten Stand.",
    "available": "Eine neue Vitalux-Version ist verfügbar!",
    "installing": "Update wird heruntergeladen und geprüft …",
    "installed": "Update wird installiert. Vitalux startet anschließend neu …",
}

class UpdatePage(Page):
    """Browse channel notes independently from preparing a verified installation."""

    def __init__(self, manager):
        super().__init__("Updates", "Vitalux automatisch über GitHub aktualisieren")
        self.m=manager
        overview=Card("Vitalux – Versionsstatus")
        self.current=KeyValue("Installierte Version")
        self.current.set(self._installed_name())
        overview.body.addWidget(self.current)
        self.installed_channel=KeyValue('Aktiver Kanal')
        self.installed_channel.set('Unstable' if profiles.installed()=='unstable' else 'Stable')
        overview.body.addWidget(self.installed_channel)
        overview.body.addWidget(label('Kanal ansehen','strong'))
        self.channel_group=QButtonGroup(self);self.channel_buttons={}
        row=QHBoxLayout()
        for key,title in (('stable','Stable'),('unstable','Unstable')):
            button=QPushButton(title,self);button.setCheckable(True);button.setObjectName('langBtn')
            self.channel_group.addButton(button)
            button.clicked.connect(lambda checked=False,key=key:self._channel(key))
            self.channel_buttons[key]=button;row.addWidget(button)
        row.addStretch(1);overview.body.addLayout(row)
        overview.body.addWidget(label('Ein Klick zeigt den Changelog. Ein Kanalwechsel wird separat vorbereitet und erst nach dem Neustart aktiv.','muted',wrap=True))
        self.status=label('', 'strong',wrap=True);self.status.setTextFormat(Qt.PlainText)
        self.checked_at=label('', 'muted',wrap=True)
        self.check_error=label('', 'muted',wrap=True);self.check_error.setTextFormat(Qt.PlainText)
        self.stable_notice=label('Deine Teständerungen sind jetzt in Stable verfügbar.','strong',wrap=True)
        self.return_stable=QPushButton('Stable ansehen',self);self.return_stable.setObjectName('ghostBtn')
        self.return_stable.clicked.connect(lambda:self._channel('stable'))
        for widget in (self.status,self.checked_at,self.check_error,self.stable_notice,self.return_stable):overview.body.addWidget(widget)
        self.check_button=QPushButton('Erneut nach Updates suchen',self);self.check_button.setObjectName('ghostBtn')
        self.check_button.clicked.connect(self.m.check);overview.body.addWidget(self.check_button,0,Qt.AlignLeft)
        self.import_profile=QPushButton('Einstellungen übernehmen …',self);self.import_profile.setObjectName('ghostBtn')
        self.import_profile.clicked.connect(self._profile);overview.body.addWidget(self.import_profile,0,Qt.AlignLeft)
        self.content.addWidget(overview)

        self.update_card=Card('Installation')
        self.source=KeyValue('Aktuell');self.source.set(self._installed_name())
        self.latest=KeyValue('Zielstand')
        self.update_card.body.addWidget(self.source);self.update_card.body.addWidget(self.latest)
        self.install_button=QPushButton('Jetzt aktualisieren',self);self.install_button.setObjectName('primaryBtn')
        self.install_button.clicked.connect(self.m.install);self.update_card.body.addWidget(self.install_button,0,Qt.AlignLeft)
        self.progress_bar=Bar();self.progress_bar.flat=True
        self.phase=label('', 'muted',wrap=True)
        self.update_card.body.addWidget(self.progress_bar);self.update_card.body.addWidget(self.phase)
        self.restart_hint=label('Neustart erforderlich. Du kannst Vitalux bis dahin weiterverwenden.','strong',wrap=True)
        self.update_card.body.addWidget(self.restart_hint)
        restart_row=QHBoxLayout()
        self.restart_button=QPushButton('Jetzt neu starten',self);self.restart_button.setObjectName('primaryBtn')
        self.later_button=QPushButton('Später',self);self.later_button.setObjectName('ghostBtn')
        self.restart_button.clicked.connect(self.m._restart)
        self.later_button.clicked.connect(self.m.defer_restart)
        restart_row.addWidget(self.restart_button);restart_row.addWidget(self.later_button);restart_row.addStretch(1)
        self.update_card.body.addLayout(restart_row)
        self.content.addWidget(self.update_card)

        self.changelog_card=Card('Changelog')
        self.changelog_heading=label('', 'strong',wrap=True)
        self.changelog_summary=label('', 'muted',wrap=True)
        self.changelog_details=label('', 'muted',wrap=True)
        self.changelog_details.setTextFormat(Qt.PlainText)
        self.changelog_details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        for widget in (self.changelog_heading,self.changelog_summary,self.changelog_details):self.changelog_card.body.addWidget(widget)
        self.content.addWidget(self.changelog_card)
        self.m.changed.connect(self.sync);self.m.progress.connect(self._progress)
        self.sync()

    @staticmethod
    def _installed_name():
        if profiles.installed()=='stable':return 'Stable · v'+__version__
        from .versions import parse
        base,_=parse(__version__)
        return tr('Unstable · Teststand für v{version}').format(version='.'.join(map(str,base)))

    def _channel(self,channel):self.m.set_channel(channel)

    def _profile(self):
        text='Kompatible Einstellungen und Hintergrundbilder aus dem anderen Kanal übernehmen? Das aktuelle Profil wird gesichert. Vitalux startet mit CPU-Rendering neu.'
        if QMessageBox.question(self,tr('Einstellungsprofile'),tr(text),QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        restart=getattr(self.window(),'restart_for_renderer',None)
        if not restart or not restart(commit=profiles.import_other):
            QMessageBox.information(self,tr('Einstellungsprofile'),tr('Ein aktiver Vorgang verhindert den Neustart. Bitte später erneut versuchen.'))

    def _name(self,channel,record):
        if channel=='stable':return 'Stable · v'+record.get('latest','–')
        if not record or record.get('stale') or not record.get('ok',True):
            return tr('Unstable · Verfügbarkeit nicht bestätigt')
        if not record.get('eligible',False):
            version=record.get('stable_version') or self.m.records.get('stable',{}).get('latest','')
            if version and record.get('same_as_stable',False):return tr('Unstable · entspricht Stable v{version}').format(version=version)
            return tr('Unstable · derzeit kein neuerer Teststand')
        from .versions import parse
        try:base='.'.join(map(str,parse(record.get('latest',''))[0]))
        except ValueError:base=record.get('latest','–')
        return tr('Unstable · Teststand für v{version}').format(version=base)

    def _progress(self,value):
        self.progress_bar.set_value(value)
        text='Paket herunterladen …' if value<80 else 'Paket prüfen …' if value<85 else 'Installation vorbereiten …'
        self.phase.setText(tr(text))

    def retranslate(self):self.sync()

    def sync(self):
        from datetime import datetime
        from .i18n import lang
        m=self.m;record=m.records.get(m.channel,{})
        pending=m.pending_restart or m.status=='installed'
        busy=m.status=='installing'
        for key,button in self.channel_buttons.items():
            button.setChecked(key==m.channel);button.setEnabled(not busy)
        self.current.set(self._installed_name());self.source.set(self._installed_name())
        self.import_profile.setEnabled(not busy and not m.checking and not pending)
        self.check_button.setEnabled(not busy and not m.checking and not pending and m.status!='preview')
        messages=dict(STATUS_TEXT,unavailable='Derzeit gibt es keinen neueren Unstable-Teststand.',
                      switch_available='Der gewählte Kanal kann separat installiert werden.',
                      installed='Neustart erforderlich.',error='Prüfung nicht möglich.')
        message=tr(messages.get(m.status,''))
        if m.status=='error' and m.error:
            if m.error_kind!='check':message=tr('Vorgang fehlgeschlagen.')
            message+=' '+tr(m.error)
        self.status.setText(message)
        self.check_error.setText(tr('Hinweis: {reason}').format(reason=tr(m.error)) if m.error and m.status!='error' else '')
        self.check_error.setVisible(bool(self.check_error.text()))
        stamp=record.get('checked_at',m.last_checked)
        if stamp:
            pattern='%d.%m.%Y %H:%M' if lang()=='de' else '%Y-%m-%d %H:%M'
            text=tr('Zuletzt geprüft: {time}').format(time=datetime.fromtimestamp(stamp).strftime(pattern))
        else:text=tr('Noch nicht geprüft.')
        if record.get('stale'):text+=' · '+tr('Gespeicherter Stand; offline lesbar.')
        self.checked_at.setText(text)
        self.stable_notice.setVisible(bool(m.stable_has_test_changes) and not pending)
        self.return_stable.setVisible(bool(m.stable_has_test_changes) and not pending)
        destination=m.pending if pending else record
        target_channel=destination.get('channel',m.channel)
        if pending:destination=dict(destination,latest=destination.get('version',''),eligible=True)
        self.latest.set(self._name(target_channel,destination))
        switching=m.channel!=profiles.installed()
        self.install_button.setText(tr(('Zu Unstable wechseln' if m.channel=='unstable' else 'Zu Stable zurückkehren') if switching else 'Jetzt aktualisieren'))
        show_disabled=(m.notes_open and m.channel=='unstable' and not record.get('eligible',False))
        self.install_button.setVisible(not pending and (m.can_install or show_disabled))
        self.install_button.setEnabled(m.can_install)
        self.install_button.setStyleSheet(f'QPushButton#primaryBtn:disabled {{ background: {theme.CARD}; color: {theme.MUTED}; border: 1px solid {theme.BORDER}; }}')
        self.install_button.setToolTip(tr('Ein Wechsel ist nur mit einem geprüften, neueren Teststand möglich.') if show_disabled else '')
        self.progress_bar.setVisible(busy);self.phase.setVisible(busy)
        self.restart_hint.setVisible(pending);self.restart_button.setVisible(pending)
        self.later_button.setVisible(pending and not m.restart_deferred)
        self.update_card.setVisible(pending or busy or m.can_install or show_disabled)
        self.changelog_card.setVisible(m.notes_open)
        self.changelog_heading.setText(self._name(m.channel,record))
        same=(m.channel=='unstable' and record.get('ok') and not record.get('stale') and not record.get('eligible',False))
        self.changelog_summary.setText(tr('Keine zusätzlichen Teständerungen. Es gilt der aktuelle Stable-Changelog.') if same else '')
        self.changelog_summary.setVisible(same)
        body=changelog.localized_release_notes(m.notes)
        if not body:
            version=m.latest if not same else record.get('stable_version','')
            changes=changelog.version_notes(version)
            if not changes and not version:
                from .versions import channel
                changes=next((notes for ident,notes in changelog.entries() if channel(ident)==('stable' if same else m.channel)),[])
            body=changelog.displayed_changes(changes)
        lines=[]
        for line in body.splitlines():
            if line.startswith('[Changelog '):continue
            line=line.lstrip('#').strip()
            if line.startswith('- '):line='• '+line[2:]
            lines.append(line)
        self.changelog_details.setText('\n'.join(lines).strip()[:10000] or tr('Für diesen Kanal ist noch kein Changelog verfügbar.'))


class AuthorCredit(QLabel):
    """Theme-aware, accessible hyperlink to the developer's profile."""

    def __init__(self):
        super().__init__()
        self.setObjectName('madeBy')
        self.setAlignment(Qt.AlignHCenter)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByMouse)
        self.setOpenExternalLinks(True)
        self.retranslate()

    def retranslate(self):
        self.setText(f'Made by <a href="{AUTHOR_URL}" style="color: {theme.accent()}; '
                     f'text-decoration: underline;">PAAAUUULLOOOH</a>')
        self.setAccessibleName('Made by PAAAUUULLOOOH')


class SupportCredit(QLabel):
    """Translated acknowledgement linking only to the fixed GitHub profile."""

    def __init__(self):
        super().__init__()
        self.setObjectName("supportCredit")
        self.setAlignment(Qt.AlignHCenter)
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByMouse)
        self.setOpenExternalLinks(True)
        self.retranslate()

    def retranslate(self):
        # Translated content is escaped; only this fixed URL becomes HTML.
        heading, separator, remainder = tr(CREDIT_TEXT).partition(":")
        before, name, after = remainder.partition("TimBooH")
        if not separator or not name:
            raise ValueError("Invalid TimBooH credit translation")
        self.setText(
            f"<b>{escape(heading)}:</b>{escape(before)}"
            f'<a href="{CREDIT_URL}" style="color: {theme.accent()}; '
            f'text-decoration: underline;">TimBooH</a>{escape(after)}'
        )
        self.setAccessibleName(tr(CREDIT_TEXT))


class InfoPage(Page):
    def __init__(self, distro):
        super().__init__("Info", "Über diese App")
        c = Card(hero=True)
        c.body.addSpacing(10)
        self.author_credit = AuthorCredit()
        c.body.addWidget(self.author_credit)
        self.support_credit = SupportCredit()
        c.body.addWidget(self.support_credit)
        c.body.addWidget(label(f"{APP_NAME} {__version__}", "muted", Qt.AlignHCenter))
        c.body.addSpacing(10)
        self.content.addWidget(c)
        help_card = Card("Anleitung und Hilfe")
        help_card.body.addWidget(label(
            "Entdecke Vitalux in einer bebilderten Schritt-für-Schritt-Anleitung mit Pfeilen und Beispielen.",
            "muted", wrap=True))
        self.guide_button = QPushButton("Anleitung öffnen")
        self.guide_button.setObjectName("primaryBtn")
        self.guide_button.setCursor(Qt.PointingHandCursor)
        self.guide_button.clicked.connect(self.open_guide)
        help_card.body.addWidget(self.guide_button)
        self.content.addWidget(help_card)
        d = Card("Details")
        for k, v in (("Version", __version__), ("Erkannte Distribution", distro["name"]),
                     ("Einstellungsdatei", settings.PATH)):
            kv = KeyValue(k)
            kv.set(v)
            d.body.addWidget(kv)
        self.content.addWidget(d)

    def open_guide(self):
        from .guide import GuideDialog
        # Visiting the guide counts as opt-in; do not prompt again on next launch.
        settings.set("guide_intro_choice", "completed")
        dlg = GuideDialog(self.window())
        dlg.exec()
