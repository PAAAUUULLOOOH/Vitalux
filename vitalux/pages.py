"""Overview dashboard and its layout editor."""
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
from PySide6.QtWidgets import QHBoxLayout, QWidget, QMenu, QToolButton, QGraphicsOpacityEffect, QStackedWidget

from . import theme, motion
from .dashboard import DashboardBoard, TITLES
from .i18n import tr
from .sensors import fmt_bytes, fmt_duration, fmt_rate, system_static
from PySide6.QtWidgets import QLabel, QSizePolicy
from .widgets import Card, ChipsGrid, GaugeCard, label, SidebarToggle
from .charts import ChartPanel
from .sensor_ui import power_text
from .power_display import component_power, disk_power, gpu_power, source_text


from .page_base import Page, _temp_freq, _vram_text, _system_state


# ------------------------------------------------------------------ Übersicht
class OverviewPage(Page):
    def __init__(self, distro, logo):
        super().__init__("Übersicht", "Live-Status deines Systems")
        self.static = system_static()
        self.distro_version = distro.get("version") or "–"

        # Auf der Übersicht steht nur die erkannte Distribution. Der App-Name
        # bleibt in der Seitenleiste; Systemversionen stehen ausschließlich in
        # den Kacheln direkt unter dem Distro-Kopf.
        head = Card(hero=True)
        # A compact system header leaves more room for the telemetry below.
        # Keep all eight system-info chips and the original title typography.
        head.layout().setContentsMargins(20, 14, 20, 14)
        head.body.setSpacing(10)
        row = QHBoxLayout()
        row.setContentsMargins(4, 0, 4, 2)
        row.setSpacing(20)
        # The distribution logo is an independent visibility option *inside*
        # the hero tile: its name and system-information chips stay intact.
        self.distro_logo_host = QWidget(head)
        self.distro_logo_host.setFixedSize(76, 76)
        pic = label()
        pic.setParent(self.distro_logo_host)
        self.distro_pic=pic
        pic.setGeometry(0, 0, 76, 76)
        pic.setAlignment(Qt.AlignCenter)
        pic.setPixmap(logo.scaled(round(76*max(1.,logo.devicePixelRatioF())), round(76*max(1.,logo.devicePixelRatioF())), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.distro_logo_remove = QToolButton(self.distro_logo_host)
        self.distro_logo_remove.setObjectName('tileRemoveHint')
        self.distro_logo_remove.setProperty('distroLogoRemove', True)
        self.distro_logo_remove.setText('×')
        self.distro_logo_remove.setToolTip(tr('Distributionslogo ausblenden'))
        self.distro_logo_remove.setCursor(Qt.PointingHandCursor)
        self.distro_logo_remove.setFixedSize(25, 25)
        self.distro_logo_remove.move(50, 1)
        self.distro_logo_remove.raise_()
        row.addWidget(self.distro_logo_host, 0, Qt.AlignVCenter)
        from .overview_text import ElidedLabel
        distro_name = ElidedLabel(distro["name"]);distro_name.setObjectName("heroTitle")
        self.distro_name=distro_name
        distro_name.setAlignment(Qt.AlignCenter)
        row.addWidget(distro_name, 1, Qt.AlignVCenter)
        self.distro_balance=QWidget();self.distro_balance.setFixedWidth(76)
        row.addWidget(self.distro_balance)
        # Equal side widths keep the name centered on the whole card.
        head.body.addLayout(row)

        # Restored 0.9.3.30 chip sizing: natural text/layout height and
        # standard Qt grid column sizing, without any fixed 80px tiles.
        # Uptime stays in the last small tile; the OS updater is gone.
        self.chips = ChipsGrid(["Kernel", "KDE", "Mesa", "Distributionsversion", "Sitzung", "Architektur", "Treiber", "Laufzeit"], columns=4)
        for chip in self.chips.chips.values():
            old=chip.value;chip.value=ElidedLabel(old.text());chip.value.setObjectName('chipValue')
            chip.layout().replaceWidget(old,chip.value);old.hide();old.deleteLater()
            chip.layout().setContentsMargins(14, 10, 14, 10)
            chip.setMinimumHeight(58)
        self.chips.grid.setVerticalSpacing(10)
        head.body.addWidget(self.chips)
        self.hero_card = head
        # Restore the ORIGINAL centered telemetry cards (v0.9.3.29).
        # Wrap the full GPU model; keep all four load instruments the same size.
        self.g_cpu, self.g_gpu = GaugeCard("Prozessor"), GaugeCard("Grafik", compact_caption=True)
        self.g_ram, self.g_disk = GaugeCard("Arbeitsspeicher"), GaugeCard("System-Laufwerk")
        for card in (self.g_cpu,self.g_gpu,self.g_ram,self.g_disk):
            card.box.gauge.setFixedHeight(180)
            card.box.layout().setAlignment(Qt.AlignTop)
            card.body.setAlignment(Qt.AlignTop)
        self.g_health = GaugeCard("Systemzustand", gauge_semantic='score')
        self.g_health.box.gauge.setFixedHeight(180)
        c1, c2 = Card("Auslastung"), Card("Netzwerk-Verlauf")
        self.graph_load = ChartPanel(['CPU', 'GPU', 'RAM'], [theme.accent(), theme.secondary_accent(), theme.TEAL])
        self.graph_net = ChartPanel(['Download', 'Upload'], [theme.accent(), theme.secondary_accent()], mode='rate')
        c1.body.addWidget(self.graph_load)
        c2.body.addWidget(self.graph_net)

        net = Card("Netzwerk")
        from .overview_text import OverviewValue
        self.net_name = OverviewValue("Aktive Schnittstelle")
        self.net_down, self.net_up = OverviewValue("Download"), OverviewValue("Upload")
        self.net_total = OverviewValue("Daten gesamt")
        net.body.addWidget(self.net_name)
        net.body.addWidget(self.net_down)
        net.body.addWidget(self.net_up)
        net.body.addWidget(self.net_total)
        self.disks_card = Card("Laufwerke")
        self.disk_meters = {}

        # Standalone previews keep the page-local editor. The main window
        # installs its grid button and editing actions in the fixed top strip.
        self.root.setContentsMargins(30,45,30,30)
        self.layout_toggle = SidebarToggle(self, orientation='horizontal')
        self.layout_toggle.setToolTip(tr('Dashboard-Layout'))
        self.layout_toggle.setAccessibleName(tr('Dashboard-Layout'))

        self.layout_actions = QWidget(self)
        self.layout_actions.setObjectName('layoutActions')
        self.layout_actions.setAttribute(Qt.WA_TranslucentBackground, True)
        strip = QHBoxLayout(self.layout_actions)
        strip.setContentsMargins(0,0,0,0)
        strip.setSpacing(5)
        self._editor_buttons = []
        for key, icon, text, handler, width in (
            ('add', '+', 'Kacheln hinzufügen', self._show_hidden_tiles, 156),
            ('undo', '↶', 'Rückgängig', self._undo_layout, 109),
            ('reset', '↺', 'Standardlayout', self.reset_editor, 123),
            ('discard', '×', 'Verwerfen', self.discard_edit, 108),
            ('save', '✓', 'Speichern', self.save_editor, 105),
        ):
            action = QToolButton(self.layout_actions)
            action.setObjectName('layoutAction')
            action.setFixedSize(width,30)
            action.setCursor(Qt.PointingHandCursor)
            action.setFocusPolicy(Qt.StrongFocus)
            action.setProperty('layoutName',key)
            action.setProperty('layoutBaseWidth',width)
            action.setProperty('layoutWideWidth',width)
            action.setText(f'{icon}  {tr(text)}')
            action.clicked.connect(handler)
            strip.addWidget(action)
            self._editor_buttons.append((key,icon,text,action))
        self._strip_width = sum(item[3].width() for item in self._editor_buttons) + strip.spacing()*4
        self.layout_actions.setFixedSize(self._strip_width,30)
        self._strip_open = False
        self._strip_anim = None
        self._strip_fraction = 0.0
        self._strip_effect = QGraphicsOpacityEffect(self.layout_actions)
        self._strip_effect.setOpacity(0.0)
        self.layout_actions.setGraphicsEffect(self._strip_effect)
        self.layout_actions.hide()
        self.board = DashboardBoard(self)
        from .signature_designs import Metric
        self.design_metrics={}
        self.design_metric_hosts={}
        from .overview_text import OverviewInfo
        self.power_labels={}
        self.overview_info={}
        def metric_host(key,classic):
            host=QStackedWidget()
            host.addWidget(classic)
            classic.box.sub.hide()
            classic.box.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
            face=Card(TITLES[key])
            face.layout().setContentsMargins(20,16,20,18)
            instrument=Metric(TITLES[key],key)
            face.body.addWidget(instrument)
            self.overview_info[key]=[]
            for card in (classic,face):
                card.layout().setAlignment(Qt.AlignTop)
                card.body.setAlignment(Qt.AlignTop)
                for heading in card.findChildren(QLabel):
                    if heading.objectName()=='cardTitle':heading.setAlignment(Qt.AlignCenter)
                info=OverviewInfo();card.body.addWidget(info)
                self.overview_info[key].append(info)
                if key in ('cpu','ram','disk'):self.power_labels.setdefault(key,[]).append(info.power)
            host.addWidget(face)
            self.design_metrics[key]=instrument
            self.design_metric_hosts[key]=host
            return host
        for key, widget in (
            ('hero',head), ('cpu',metric_host('cpu',self.g_cpu)), ('gpu',metric_host('gpu',self.g_gpu)),
            ('ram',metric_host('ram',self.g_ram)), ('disk',metric_host('disk',self.g_disk)),
            ('graph_load',c1), ('graph_net',c2),
            ('health',metric_host('health',self.g_health)), ('network',net), ('drives',self.disks_card),
        ):
            self.board.register(key,widget)
        for card in (head,c1,c2,net,self.disks_card):
            card.layout().setAlignment(Qt.AlignTop)
            for text in card.findChildren(QLabel):
                if text.objectName() in ('cardTitle','chipTitle','chipValue'):text.setAlignment(Qt.AlignCenter)
        self.content.addWidget(self.board)
        self.layout_toggle.clicked.connect(self.toggle_editor)
        self.board.changed.connect(self._refresh_editor_actions)
        self.board.changed.connect(self._sync_distro_logo)
        self.distro_logo_remove.clicked.connect(self.board.hide_distro_logo)
        self._sync_distro_logo()
        self._position_editor_controls()
        self.refresh_design()
        QTimer.singleShot(0,self.board.refresh_geometry)

    def refresh_design(self):
        from .signature_designs import active
        selected=active()
        changed=any(host.currentIndex()!=(1 if selected else 0) for host in self.design_metric_hosts.values())
        if changed and hasattr(self,'_last_overview_sample'):
            self.refresh(*self._last_overview_sample,_variant=1 if selected else 0)
        for host in self.design_metric_hosts.values():
            host.setCurrentIndex(1 if selected else 0)
        top = getattr(self, '_frame_top_margin', 24) if getattr(self, '_window_layout_toggle', False) else 45
        horizontal = 16 if selected or getattr(self, '_window_layout_toggle', False) else 30
        self.root.setContentsMargins(horizontal,top,horizontal,24 if selected else 30)
        self.root.setStretch(0,0)
        self.root.setStretch(1,1)
        self.board.show()
        if not getattr(self, '_window_layout_toggle', False):self.layout_toggle.show()
        self._sync_distro_logo()
        self.distro_logo_host.setFixedSize(76,76)
        for chip in self.chips.chips.values():
            chip.layout().setContentsMargins(14,10,14,10)
        self.chips.grid.setVerticalSpacing(10)
        self.board.refresh_geometry(animate=False)
        for panel in (self.graph_load,self.graph_net):
            panel.graph.setMinimumHeight(110 if selected else 185)
            panel.graph.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self,'layout_actions'):
            self._position_editor_controls()

    def set_window_layout_toggle(self, button):
        """Use accessible frame controls and their shared editing-action row."""
        self.layout_toggle.hide()
        self.layout_toggle.deleteLater()
        self.layout_toggle = button
        self._window_layout_toggle = True
        self.layout_actions.setFixedHeight(button.height())
        for _,_,_,action in self._editor_buttons:action.setFixedHeight(button.height())
        button.set_collapsed(self.board.editing)
        self._position_editor_controls()

    def _editor_strip_x(self):
        return self.width()-self._strip_width-self.layout_toggle.width()-12

    def set_frame_editor_compact(self, compact):
        for _,_,_,action in self._editor_buttons:action.ensurePolished()
        key=(compact,theme.mode(),tr('Kacheln hinzufügen'),
             tuple(action.font().toString() for _,_,_,action in self._editor_buttons))
        if getattr(self,'_editor_size_key',None)==key:return
        self._editor_size_key=key
        self._editor_compact=compact
        for _,icon,source,action in self._editor_buttons:
            action.setText(f'{icon}  {tr(source)}')
            width=max(action.property('layoutBaseWidth'),action.sizeHint().width())
            action.setProperty('layoutWideWidth',width)
            action.setFixedWidth(28 if compact else width)
            if compact:action.setText(icon)
            action.setToolTip(tr(source));action.setAccessibleName(tr(source))
        strip=self.layout_actions.layout()
        self._strip_width=sum(a.width() for _,_,_,a in self._editor_buttons)+strip.spacing()*4
        self.layout_actions.setFixedWidth(self._strip_width)

    def _position_editor_controls(self):
        if getattr(self, '_window_layout_toggle', False):return
        self.layout_toggle.move(self.width()-self.layout_toggle.width()-5,13)
        # Shift just the small action strip, not its children or an animated
        # clipping mask. Widgets retain their full width throughout movement.
        target_x = self._editor_strip_x()
        if self._strip_anim is None:
            self.layout_actions.move(target_x+round(22*(1-self._strip_fraction)),13)
        self.layout_toggle.raise_()
        if self._strip_open:
            self.layout_actions.raise_()
            self.layout_toggle.raise_()

    def _reveal_strip(self, opening):
        """Slide one lightweight action row; never clip/repaint its text.

        The old QRegion mask was rebuilt on every frame and visibly sheared
        button labels, especially at fractional scaling on KDE/Wayland.
        Here button geometries never change. We animate only the containing
        QWidget's position and opacity with one synchronized animation group.
        """
        previous = self._strip_anim
        if previous is not None:
            previous.stop()
            previous.deleteLater()
            self._strip_anim = None
        start = self._strip_fraction
        finish = 1.0 if opening else 0.0
        if opening:
            self.layout_actions.show()
            self.layout_actions.raise_()
            self.layout_toggle.raise_()
        if getattr(self,'_window_layout_toggle',False):self.layout_toggle.frame.sync_controls()
        if not motion.enabled() or abs(finish-start) < .001:
            self._strip_fraction = finish
            self._strip_effect.setOpacity(finish)
            self._position_editor_controls()
            if not opening:
                self.layout_actions.hide()
                if getattr(self,'_window_layout_toggle',False):self.layout_toggle.frame.sync_controls()
            return
        # Keep the strip in one row with stable letter spacing. A property
        # animation on the opacity effect avoids a per-frame pixel mask.
        fade = QPropertyAnimation(self._strip_effect, b'opacity', self)
        fade.setStartValue(self._strip_effect.opacity())
        fade.setEndValue(finish)
        group=QParallelAnimationGroup(self)
        animations = [fade]
        if not getattr(self, '_window_layout_toggle', False):
            travel = QPropertyAnimation(self.layout_actions, b'pos', self)
            travel.setStartValue(self.layout_actions.pos())
            target=self._editor_strip_x()
            travel.setEndValue(QPoint(target+round(22*(1-finish)),13))
            animations.append(travel)
        for animation in animations:
            animation.setDuration(motion.duration(round(235*abs(finish-start))))
            animation.setEasingCurve(QEasingCurve.InOutCubic)
            group.addAnimation(animation)
        self._strip_anim=group
        fade.valueChanged.connect(lambda opacity: setattr(self, '_strip_fraction', float(opacity)))
        def completed():
            if self._strip_anim is not group:return
            self._strip_anim=None
            self._strip_fraction=finish
            if not opening:
                self.layout_actions.hide()
                if getattr(self,'_window_layout_toggle',False):self.layout_toggle.frame.sync_controls()
            self._position_editor_controls()
            group.deleteLater()
        group.finished.connect(completed)
        group.start()

    def _sync_distro_logo(self):
        visible = self.board.distro_logo_visible
        self.distro_logo_host.setVisible(visible)
        self.distro_balance.setVisible(visible)
        self.distro_logo_remove.setVisible(visible and self.board.editing)

    def _refresh_editor_actions(self):
        for key, _icon, _txt, action in self._editor_buttons:
            if key=='undo':action.setEnabled(bool(self.board.history))
            if key=='add':action.setEnabled(bool(self.board.available_hidden()))

    def _show_hidden_tiles(self):
        menu = QMenu(self)
        hidden=self.board.available_hidden()
        for key,title in hidden:
            item=menu.addAction(title)
            item.triggered.connect(lambda _=False,k=key:self.board.show_tile(k))
        if not hidden:
            item=menu.addAction(tr('Alle Kacheln sind bereits sichtbar'))
            item.setEnabled(False)
        add = next(a for k,_,_,a in self._editor_buttons if k=='add')
        try:menu.exec(add.mapToGlobal(QPoint(0,add.height())))
        finally:menu.deleteLater()
        self._refresh_editor_actions()

    def _undo_layout(self):
        self.board.undo()
        self._refresh_editor_actions()

    def toggle_editor(self):
        # A second arrow click commits the edited arrangement, closes the
        # actions AND exits edit mode (same semantics as the Save control).
        if self.board.editing:
            self.save_editor()
            return
        self.board.begin_edit()
        self._sync_distro_logo()
        self._refresh_editor_actions()
        self._strip_open = True
        self.layout_toggle.set_collapsed(True)
        self.layout_toggle.setToolTip(tr('Dashboard-Layout'))
        self._reveal_strip(True)

    def _finish_editor(self, save):
        if not self.board.editing:return
        self.board.finish_edit(save=save)
        self._sync_distro_logo()
        self._strip_open=False
        self.layout_toggle.set_collapsed(False)
        self.layout_toggle.reset_highlight()
        self.layout_toggle.setToolTip(tr('Dashboard-Layout'))
        self._reveal_strip(False)

    def save_editor(self):
        self._finish_editor(True)

    def discard_edit(self):
        self._finish_editor(False)

    def reset_editor(self):
        if not self.board.editing:return
        self.board.reset()
        self._finish_editor(True)

    def retranslate(self):
        self.layout_toggle.setToolTip(tr('Dashboard-Layout'))
        self.layout_toggle.setAccessibleName(tr('Dashboard-Layout'))
        for _,icon,source,action in self._editor_buttons:
            action.setText(icon if getattr(self,'_editor_compact',False) else f'{icon}  {tr(source)}')
            action.setToolTip(tr(source));action.setAccessibleName(tr(source))
        if getattr(self,'_window_layout_toggle',False):self.layout_toggle.frame.sync_controls()
        for tile in self.board.tiles.values():
            tile.drag.setText(tr('Zum Verschieben halten'))
            tile.drag.setToolTip(tr('Kachel verschieben'))
            tile.remove.setToolTip(tr('Kachel ausblenden'))
        self.distro_logo_remove.setToolTip(tr('Distributionslogo ausblenden'))


    def refresh(self, d, h, _variant=None):
        initial=not hasattr(self,'_last_overview_sample')
        self._last_overview_sample=(d,h)
        variant=next(iter(self.design_metric_hosts.values())).currentIndex() if _variant is None else _variant
        c, r, gpus, disks = d["cpu"], d["ram"], d["gpus"], d["disks"]
        records=d.get('hardware') or []
        root = next((x for x in disks if x['mount']=='/'),disks[0] if disks else None)
        readings={'cpu':component_power(records,'cpu'),'ram':component_power(records,'ram'),
                  'gpu':gpu_power(gpus[0]) if gpus else None,'disk':disk_power(records,root)}
        for key,widgets in self.power_labels.items():
            record=readings[key]
            text=power_text(record)
            for widget in widgets if initial or not text else widgets[variant:variant+1]:
                widget.setText(text);widget.setVisible(bool(text))
                widget.setToolTip(source_text(record) if text else '')
        net = d["net"]
        primary = net.get("primary") or {}
        driver = next((g.get("driver") for g in gpus if g.get("driver")), "amdgpu / drm" if gpus and gpus[0]["vendor"] == "AMD" else "–")
        self.chips.set("Kernel", self.static["kernel"])
        self.chips.set("KDE", f"Plasma {self.static['plasma']}")
        self.chips.set("Mesa", self.static["mesa"])
        self.chips.set("Distributionsversion", self.distro_version)
        self.chips.set("Sitzung", self.static["session"])
        self.chips.set("Architektur", self.static["arch"])
        self.chips.set("Treiber", driver)
        self.chips.set("Laufzeit", fmt_duration(d['uptime']))

        gpu=gpus[0] if gpus else {}
        score, state, detail = _system_state(d)
        if initial or variant==0:
            self.g_cpu.set(c["usage"], _temp_freq(c))
            if gpus:
                g = gpus[0]
                vt = _vram_text(g)
                self.g_gpu.set(g["usage"], g["name"] + (f"\nVRAM {vt}" if vt else ""))
                self.g_gpu.box.sub.setToolTip(g["name"] + (f"\nVRAM {vt}" if vt else ""))
            else:
                self.g_gpu.set(None, "Keine GPU-Daten verfügbar")
            self.g_ram.set(r["percent"], f"{fmt_bytes(r['used'])} / {fmt_bytes(r['total'])}")
            root = next((x for x in disks if x["mount"] == "/"), disks[0] if disks else None)
            if root:
                self.g_disk.set(root["percent"], f"{fmt_bytes(root['used'])} / {fmt_bytes(root['total'])}")
            else:
                self.g_disk.set(None, 'Keine Laufwerksdaten verfügbar')

            score, state, detail = _system_state(d)
            self.g_health.set(score, f"{state}\n{detail}",
                              text=f"{score:.0f}" if score is not None else "–")
        if initial or variant==1:
            self.design_metrics['cpu'].set(c['usage'],_temp_freq(c),extra=c.get('model',''),history=h['cpu'])
            gpu=gpus[0] if gpus else {}
            self.design_metrics['gpu'].set(gpu.get('usage'),
                f"{gpu['temp']:.0f} °C" if gpu.get('temp') is not None else tr('Keine GPU-Daten verfügbar'),
                extra=gpu.get('name',tr('Keine GPU-Daten verfügbar')),history=h['gpu'])
            self.design_metrics['ram'].set(r['percent'],f"{fmt_bytes(r['used'])} / {fmt_bytes(r['total'])}")
            self.design_metrics['disk'].set(root['percent'] if root else None,
                f"{fmt_bytes(root['used'])} / {fmt_bytes(root['total'])}" if root else tr('Keine Laufwerksdaten verfügbar'))
            self.design_metrics['health'].set(score,f'{state} · {detail}')

        captions={
            'cpu':(c.get('model',''),_temp_freq(c)),
            'gpu':(gpu.get('name',''),(' · '.join(x for x in (
                f"{gpu['temp']:.0f} °C" if gpu.get('temp') is not None else '',
                f"VRAM {_vram_text(gpu)}" if _vram_text(gpu) else '') if x)) if gpu else tr('Keine GPU-Daten verfügbar')),
            'ram':('',f"{fmt_bytes(r['used'])} / {fmt_bytes(r['total'])}"),
            'disk':('',f"{fmt_bytes(root['used'])} / {fmt_bytes(root['total'])}" if root else tr('Keine Laufwerksdaten verfügbar')),
            'health':(tr(state),detail),
        }
        for key,infos in self.overview_info.items():
            name,details=captions[key]
            for info in infos if initial else infos[variant:variant+1]:info.set(name,details,power_text(readings.get(key)) if key in self.power_labels else '')

        self.graph_load.set_series([(h["cpu"], theme.accent()), (h["gpu"], theme.secondary_accent()), (h["ram"], theme.TEAL)])
        self.graph_net.set_series([(h["net_down"], theme.accent()), (h["net_up"], theme.secondary_accent())])
        self.net_name.set(primary.get("name", "–") + (f"  ·  {primary.get('speed', 0)} Mbit/s" if primary.get("speed") else ""))
        self.net_down.set(fmt_rate(net["down"]))
        self.net_up.set(fmt_rate(net["up"]))
        self.net_total.set(f"↓ {fmt_bytes(net['total_down'])}   ·   ↑ {fmt_bytes(net['total_up'])}")
        for x in disks[:6]:
            m = self.disk_meters.get(x["mount"])
            if m is None:
                from .overview_text import OverviewMeter
                m = self.disk_meters[x["mount"]] = OverviewMeter(x["mount"])
                self.disks_card.body.addWidget(m)
            m.set(x["percent"], f"{fmt_bytes(x['used'])} / {fmt_bytes(x['total'])}")


# ------------------------------------------------------------------ Prozessor


# ------------------------------------------------------------------ Grafik (schreibgeschützt)


# ------------------------------------------------------------------ Speicher


# ------------------------------------------------------------------ Laufwerke


# ------------------------------------------------------------------ Netzwerk


# ------------------------------------------------------------------ System
