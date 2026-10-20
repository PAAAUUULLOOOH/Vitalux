"""App traffic, socket details and explicit session network controls."""
from PySide6.QtCore import Qt,Signal
import ipaddress
from PySide6.QtNetwork import QDnsLookup
from PySide6.QtWidgets import (QAbstractItemView,QHeaderView,QHBoxLayout,QInputDialog,
    QLineEdit,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget)
from . import settings,theme
from .i18n import tr
from .ui_locale import QPushButton
from .widgets import Card,label
from .sensors import fmt_bytes,fmt_rate
from .network_monitor import TrafficLedger,NetworkSampler,HelperClient


class NumberItem(QTableWidgetItem):
    def __init__(self,text,value=None):
        super().__init__(text)
        self.setData(Qt.UserRole,-1 if value is None else value)

    def __lt__(self,other):
        return (self.data(Qt.UserRole) or 0)<(other.data(Qt.UserRole) or 0)


class NetworkWatch(QWidget):
    alert=Signal(str,str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.ledger=TrafficLedger()
        self.worker=None
        self.client=HelperClient(self)
        self.client.sample.connect(self._helper_sample)
        self.client.state.connect(self._helper_state)
        self.client.error.connect(self._error)
        self.client.rules.connect(self._rules_changed)
        self._closing=False
        self._last_notice=''
        self._key=None
        self._names={}
        self._lookups={}
        self._limits=self._read_limits()
        layout=QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(14)
        controls=Card('Programme & Verbindungen')
        self.state_label=label('Messung wird beim Öffnen gestartet.','strong',wrap=True)
        self.state_label.setTextFormat(Qt.PlainText)
        self.scope=label('Ohne Freigabe: TCP-Nutzdaten der erkennbaren Verbindungen. UDP-Verbrauch ist nicht verfügbar. Werte gelten ab Messbeginn.','muted',wrap=True)
        controls.body.addWidget(self.state_label)
        controls.body.addWidget(self.scope)
        buttons=QHBoxLayout()
        self.full=QPushButton('Vollständige Messung freigeben')
        self.full.setObjectName('ghostBtn')
        self.full.clicked.connect(self._toggle_helper)
        self.clear=QPushButton('Alle Sperren aufheben')
        self.clear.setObjectName('ghostBtn')
        self.clear.clicked.connect(lambda:self.client.command('clear'))
        self.clear.setEnabled(False)
        self.reset=QPushButton('Messung zurücksetzen')
        self.reset.setObjectName('ghostBtn')
        self.reset.clicked.connect(self._reset)
        for button in (self.full,self.clear,self.reset):buttons.addWidget(button)
        buttons.addStretch(1)
        controls.body.addLayout(buttons)
        self.filter=QLineEdit()
        self.filter.setPlaceholderText(tr('Programme oder Pfade filtern'))
        self.filter.textChanged.connect(self._render)
        controls.body.addWidget(self.filter)
        self.table=QTableWidget(0,6)
        self.table.setObjectName('networkApplications')
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(245)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        for column in range(1,6):self.table.horizontalHeader().setSectionResizeMode(column,QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._selection)
        controls.body.addWidget(self.table)
        self.empty=label('Noch keine zuordenbaren Netzwerkverbindungen. Öffne eine Anwendung mit Netzwerkzugriff.','muted',wrap=True)
        controls.body.addWidget(self.empty)
        layout.addWidget(controls)
        details=Card('Verbindungsdetails')
        self.application=label('Programm auswählen','strong',wrap=True)
        self.application.setTextFormat(Qt.PlainText)
        self.path=label('','muted',wrap=True)
        self.path.setTextFormat(Qt.PlainText)
        self.path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        details.body.addWidget(self.application)
        details.body.addWidget(self.path)
        actions=QHBoxLayout()
        self.block=QPushButton('Netzwerk sperren')
        self.block.setObjectName('ghostBtn')
        self.block.clicked.connect(self._block)
        self.budget=QPushButton('Verbrauchswarnung …')
        self.budget.setObjectName('ghostBtn')
        self.budget.clicked.connect(self._budget)
        self.resolve=QPushButton('Hostnamen ermitteln')
        self.resolve.setObjectName('ghostBtn')
        self.resolve.clicked.connect(self._resolve)
        for button in (self.block,self.budget,self.resolve):actions.addWidget(button)
        actions.addStretch(1)
        details.body.addLayout(actions)
        self.limit_label=label('','muted',wrap=True)
        details.body.addWidget(self.limit_label)
        self.connections=QTableWidget(0,5)
        self.connections.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.connections.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.connections.setShowGrid(False)
        self.connections.verticalHeader().hide()
        self.connections.setMinimumHeight(180)
        self.connections.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.connections.horizontalHeader().setSectionResizeMode(3,QHeaderView.Stretch)
        details.body.addWidget(self.connections)
        details.body.addWidget(label('Sperren betreffen die laufenden Prozesse dieses Programms und gelten nur während der freigegebenen Vitalux-Sitzung. Hostnamen werden erst auf Klick über die Systemauflösung angefragt; ein PTR-Name bestätigt nicht die Identität eines Ziels.','muted',wrap=True))
        layout.addWidget(details)
        self.retranslate()
        self._selection()

    @staticmethod
    def _read_limits():
        value=settings.get('network_app_limits',{})
        if not isinstance(value,dict):return {}
        return {key:limit for key,limit in list(value.items())[:4096]
                if isinstance(key,str) and len(key)<=4096 and type(limit) is int and 0<limit<=1024**5}

    def showEvent(self,event):
        super().showEvent(event)
        self._start_sampler()

    def _start_sampler(self):
        if not self._closing and self.worker is None:
            self.worker=NetworkSampler(self)
            self.worker.sampled.connect(self._normal_sample)
            self.worker.failed.connect(self._error)
            self.worker.start()
            self.state_label.setText(tr('TCP-Messung aktiv · nur Programme des aktuellen Benutzers'))

    def resume_after_shutdown(self):
        had_worker=self.worker is not None
        if had_worker:
            self.worker.deleteLater()
            self.worker=None
        self._closing=False
        self.full.setEnabled(True)
        if had_worker:self._start_sampler()

    def _normal_sample(self,sample):
        if not self.client.active and not self._closing:self._ingest(sample)

    def _helper_sample(self,sample):
        if not self._closing:self._ingest(sample)

    def _ingest(self,sample):
        try:notifications=self.ledger.ingest(sample,self._limits)
        except (ValueError,TypeError,KeyError) as exc:
            self._error(str(exc))
            return
        for key,total,limit in notifications:
            app=self.ledger.apps[key]
            name=app['name'] or app['exe'] or tr('Nicht zugeordnet')
            self.alert.emit(tr('Verbrauchswarnung'),f'{name}: {fmt_bytes(total)} / {fmt_bytes(limit)}')
        self._render()
        self.clear.setEnabled(bool(self.ledger.rules) and self.client.active)
        if self.ledger.errors:
            self.state_label.setText(tr('Messung teilweise verfügbar. Details stehen im Hinweis.'))
            self.state_label.setToolTip('\n'.join(self.ledger.errors))

    def _render(self,*_):
        needle=self.filter.text().casefold()
        rows=[row for row in self.ledger.apps.values() if not needle or needle in
              (row['name']+' '+row['exe']).casefold()]
        rows.sort(key=lambda row:row['total_down']+row['total_up'],reverse=True)
        selected=self._key
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        selected_row=-1
        for index,row in enumerate(rows):
            name=row['name'] or (row['exe'].rsplit('/',1)[-1] if row['exe'] else tr('Nicht zugeordnet'))
            item=QTableWidgetItem(name)
            item.setData(Qt.UserRole,row['key'])
            item.setToolTip(row['exe'] or tr('Prozess konnte nicht zugeordnet werden.'))
            self.table.setItem(index,0,item)
            for column,key in ((1,'down'),(2,'up')):
                value=row.get(key)
                shown='–' if value is None else fmt_rate(value)
                self.table.setItem(index,column,NumberItem(shown,value))
            total=row['total_down']+row['total_up']
            self.table.setItem(index,3,NumberItem(fmt_bytes(total) if row['measured'] or total else '–',total))
            self.table.setItem(index,4,NumberItem(str(row['connections']),row['connections']))
            state=tr('Gesperrt') if row['blocked'] else tr('Teilweise') if row['partial'] else tr('Aktiv') if row['connections'] else tr('Beendet')
            self.table.setItem(index,5,QTableWidgetItem(state))
            if row['key']==selected:selected_row=index
        if selected_row>=0:self.table.selectRow(selected_row)
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
        self.empty.setVisible(not rows)
        self._selection()

    def _selection(self):
        selected=self.table.selectionModel().selectedRows()
        item=self.table.item(selected[0].row(),0) if selected else None
        self._key=item.data(Qt.UserRole) if item else None
        row=self.ledger.apps.get(self._key)
        self.budget.setEnabled(bool(row) and self._key!='@unassigned')
        self.resolve.setEnabled(bool(row and row['connections']))
        self.block.setEnabled(bool(row and self.client.active and (row['pids'] or row['blocked'])))
        self.block.setText(tr('Netzwerk freigeben' if row and row['blocked'] else 'Netzwerk sperren'))
        self.block.setToolTip('' if self.client.active else tr('Vollständige Messung freigeben, um laufende Programme zu sperren.'))
        self.application.setText((row['name'] or row['exe'] or tr('Nicht zugeordnet')) if row else tr('Programm auswählen'))
        self.path.setText(row['exe'] if row else '')
        limit=self._limits.get(self._key)
        self.limit_label.setText((tr('Verbrauchswarnung')+': '+fmt_bytes(limit)+tr(' pro Messsitzung')) if limit else tr('Keine Verbrauchswarnung für dieses Programm.'))
        self._render_connections()

    def _render_connections(self):
        rows=[row for row in self.ledger.connections if row.get('key')==self._key]
        self.connections.setRowCount(len(rows))
        for index,row in enumerate(rows):
            address=row['remote']
            remote=f"[{address}]:{row['remote_port']}" if ':' in address else f"{address}:{row['remote_port']}"
            local=f"{row['local']}:{row['local_port']}"
            name=self._names.get(address,tr('Nicht aufgelöst'))
            values=(row['protocol'],str(row.get('pid') or '–'),remote,name,row['state'])
            for column,value in enumerate(values):
                item=QTableWidgetItem(value)
                item.setToolTip(local if column==2 else value)
                self.connections.setItem(index,column,item)

    def _toggle_helper(self):
        self._last_notice=''
        if self.client.active:self.client.stop()
        else:self.client.start()

    def _helper_state(self,state):
        if self.worker is not None:self.worker.paused=state=='ready'
        busy=state in ('installing','authenticating')
        self.full.setEnabled(not busy and not self._closing)
        self.full.setText(tr('Freigabe beenden' if state=='ready' else 'Vollständige Messung freigeben'))
        texts=dict(installing='Netzwerk-Helfer wird eingerichtet · Systemfreigabe erforderlich',
            authenticating='Systemfreigabe für die Netzwerkmessung wird angefragt …',
            ready='Vollständige Messung aktiv · TCP und UDP · IP-Bytes einschließlich Protokoll-Header',
            stopped='TCP-Messung aktiv · nur Programme des aktuellen Benutzers')
        self.state_label.setText(tr(texts.get(state,'')))
        self.scope.setText(tr('Session-Sperren werden beim Beenden der Freigabe oder von Vitalux aufgehoben. Verbrauch gilt ab Beginn dieser Messung.' if state=='ready' else
            'Ohne Freigabe: TCP-Nutzdaten der erkennbaren Verbindungen. UDP-Verbrauch ist nicht verfügbar. Werte gelten ab Messbeginn.'))
        if state=='stopped':
            self.ledger.rules.clear()
            self.clear.setEnabled(False)
            if self._last_notice:self._error(self._last_notice)
        self._selection()

    def _rules_changed(self,rules):
        self.ledger.rules=set(rules)
        for key,row in self.ledger.apps.items():row['blocked']=key in self.ledger.rules
        self.clear.setEnabled(bool(rules))
        self._render()

    def _error(self,message):
        self._last_notice=message
        short=tr('Der Netzwerk-Helfer konnte nicht gestartet werden. Die Basisansicht bleibt verfügbar.') if len(message)>160 or '\n' in message else tr(message)
        self.state_label.setText(tr('Netzwerk-Hinweis')+': '+short)
        self.state_label.setToolTip(message)

    def _block(self):
        row=self.ledger.apps.get(self._key)
        if not row or not self.client.active:return
        if row['blocked']:
            self.client.command('allow',key=row['key'])
        elif row['pids']:
            pid,start=next(iter(row['pids'].items()))
            if type(start) is int:self.client.command('block',pid=pid,start=start)

    def _budget(self):
        if not self._key or self._key=='@unassigned':return
        value,ok=QInputDialog.getInt(self,tr('Verbrauchswarnung'),
            tr('Warnung ab MiB pro Messsitzung (0 = aus):'),self._limits.get(self._key,0)//(1024**2),0,1000000,1)
        if not ok:return
        if value:self._limits[self._key]=value*1024**2
        else:self._limits.pop(self._key,None)
        settings.set('network_app_limits',self._limits)
        window=self.window()
        if hasattr(window,'pages'):
            preferences=next((page for title,page in window.pages if title=='Einstellungen'),None)
            if preferences is not None:preferences._refresh_restore_button()
        self._selection()

    def _resolve(self):
        addresses={row['remote'] for row in self.ledger.connections if row.get('key')==self._key
                   and row.get('remote') not in ('0.0.0.0','::')}
        for address in sorted(addresses)[:32]:
            if len(self._lookups)>=32:break
            if address in self._lookups or address in self._names:continue
            lookup=QDnsLookup(QDnsLookup.PTR,ipaddress.ip_address(address).reverse_pointer,self)
            self._lookups[address]=lookup
            def result(address=address,lookup=lookup):
                self._lookups.pop(address,None)
                if self._closing:return
                if len(self._names)>=512:self._names.pop(next(iter(self._names)))
                records=lookup.pointerRecords() if lookup.error()==QDnsLookup.NoError else []
                self._names[address]=records[0].value().rstrip('.') if records else tr('Unbekannt')
                lookup.deleteLater()
                self._render_connections()
            lookup.finished.connect(result)
            lookup.lookup()

    def _reset(self):
        rules=set(self.ledger.rules)
        self.ledger.reset()
        self.ledger.rules=rules
        self._render()

    def retranslate(self):
        self.table.setHorizontalHeaderLabels([tr(value) for value in
            ('Programm','Download','Upload','Erfasst','Verbindungen','Status')])
        self.connections.setHorizontalHeaderLabels([tr(value) for value in
            ('Protokoll','PID','Zieladresse','PTR-Hostname','Zustand')])
        self.filter.setPlaceholderText(tr('Programme oder Pfade filtern'))
        if self.worker is not None:self._helper_state('ready' if self.client.active else 'stopped')
        self._render()

    def shutdown(self):
        if not self._closing:
            self._closing=True
            if self.worker is not None:self.worker.stop()
            self.client.stop()
            for lookup in list(self._lookups.values()):
                lookup.abort()
                lookup.deleteLater()
            self._lookups.clear()
        return (self.worker is None or not self.worker.isRunning()) and self.client.is_stopped()
