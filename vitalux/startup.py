"""A real startup pipeline: worker-side discovery, cached products and GUI warmup."""
import time
from PySide6.QtCore import QObject,QThread,Signal,Slot,Qt,QTimer,QPropertyAnimation,QEasingCurve,QRectF
from PySide6.QtGui import QPainter,QColor,QPen,QLinearGradient
from PySide6.QtWidgets import QWidget,QVBoxLayout,QApplication,QGraphicsOpacityEffect
from . import settings,theme,motion,eco
from .i18n import tr
from .widgets import label

class StartupWorker(QThread):
    stage=Signal(str)
    prepared=Signal(object)
    failed=Signal(str)
    def run(self):
        try:
            from . import sensors
            self.stage.emit('Hardware erkennen …')
            static=sensors.system_static()
            if self.isInterruptionRequested():return
            self.stage.emit('Sensorwerte einlesen …')
            sensors.prime();sample=sensors.collect();sample['timestamp']=time.time()
            if self.isInterruptionRequested():return
            self.stage.emit('Komponentenbilder und Spezifikationen laden …')
            from .product_images import ProductCache,lookup_key
            from .product_specs import SpecCache,product_key
            products=[sample['cpu'].get('product'),static.get('board_product')]
            products += [item.get('product') for item in sample.get('gpus',[])]
            products += [item.get('product') for item in sample.get('ram',{}).get('modules',[])]
            images={};specs={}
            for product in products:
                if not product:continue
                if settings.get('component_images',True) is not False:
                    cached=ProductCache(include_image=True).load(product)
                    if cached:images[lookup_key(product)]=cached
                cached=SpecCache().load(product)
                if cached:specs[product_key(product)]=cached
            self.stage.emit('Installierte Spiele erkennen …')
            from .game_library import discover
            games=discover()
            if self.isInterruptionRequested():return
            self.prepared.emit(dict(sample=sample,images=images,specs=specs,games=games))
        except Exception as exc:
            from .diagnostics import log_exception
            log_exception(type(exc),exc,exc.__traceback__)
            self.failed.emit(str(exc))

class ActivityLine(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setFixedHeight(4);self.phase=0.
        self.timer=QTimer(self);self.timer.setInterval(40);self.timer.timeout.connect(self.advance)
    def advance(self):self.phase=(self.phase+.025)%1;self.update()
    def showEvent(self,event):
        super().showEvent(event)
        if motion.enabled() and not eco.enabled():self.timer.start()
    def hideEvent(self,event):self.timer.stop();super().hideEvent(event)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen);p.setBrush(QColor(theme.TRACK));p.drawRoundedRect(self.rect(),2,2)
        if self.timer.isActive():
            width=self.width()*.3;x=(self.width()+width)*self.phase-width
        else:width=self.width();x=0
        gradient=QLinearGradient(x,0,x+width,0);gradient.setColorAt(0,QColor(theme.secondary_accent()));gradient.setColorAt(1,QColor(theme.accent()))
        p.setBrush(gradient);p.drawRoundedRect(QRectF(x,0,width,4),2,2);p.end()

class StartupCard(QWidget):
    def paintEvent(self,event):
        from .window_frame import CORNER_RADIUS
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        fill=QLinearGradient(0,0,self.width(),self.height());fill.setColorAt(0,QColor(theme.CARD));fill.setColorAt(1,QColor(theme.BG))
        p.setBrush(fill);p.setPen(QPen(QColor(theme.BORDER),1))
        p.drawRoundedRect(self.rect().adjusted(1,1,-1,-1),CORNER_RADIUS,CORNER_RADIUS);p.end()


class StartupWindow(QWidget):
    def __init__(self):
        # Wayland owns top-level positions. A transparent maximized surface
        # supplies a stable screen-sized coordinate system; only the small
        # centered card is painted and accepts input. There is no extra window.
        self._centered_surface=QApplication.platformName().startswith('wayland')
        kind=Qt.Window if self._centered_surface else Qt.Dialog
        super().__init__(None,kind|Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowRole('vitalux-initialization')
        self.setAttribute(Qt.WA_QuitOnClose,False)
        self.setAttribute(Qt.WA_TranslucentBackground,True)
        self.setWindowTitle('Vitalux');self.ready=False
        self.card=StartupCard(self);self.card.setFixedSize(460,400)
        if self._centered_surface:self.setMinimumSize(460,400)
        else:self.setFixedSize(460,400)
        from .brand import PulseCore,Wordmark
        layout=QVBoxLayout(self.card);layout.setContentsMargins(44,24,44,28);layout.setSpacing(12)
        self.logo=PulseCore(160);self.wordmark=Wordmark();self.wordmark.setFixedSize(210,44)
        layout.addWidget(self.logo,0,Qt.AlignHCenter);layout.addWidget(self.wordmark,0,Qt.AlignHCenter)
        self.caption=label('Dein System wird vorbereitet …','strong',Qt.AlignCenter,wrap=True);layout.addWidget(self.caption)
        self.activity=ActivityLine(self.card);layout.addWidget(self.activity)
        self.status=label('Hardware erkennen …','muted',Qt.AlignCenter,wrap=True);self.status.setMinimumHeight(36);layout.addWidget(self.status)
        self._placement_attempts=0
        self._placement_timer=QTimer(self);self._placement_timer.setInterval(150)
        self._placement_timer.timeout.connect(self._settle_position)
        self._screen=None
        QApplication.instance().primaryScreenChanged.connect(self._watch_screen)
        self._watch_screen(QApplication.primaryScreen())
        self._position_card()

    def _position_card(self):
        self.card.move((self.width()-self.card.width())//2,(self.height()-self.card.height())//2)
        handle=self.windowHandle()
        if self._centered_surface and handle:
            from .window_frame import CORNER_RADIUS
            from PySide6.QtGui import QPainterPath,QRegion
            path=QPainterPath()
            path.addRoundedRect(QRectF(self.card.geometry()).adjusted(-2,-2,2,2),CORNER_RADIUS,CORNER_RADIUS)
            handle.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _watch_screen(self,screen):
        if self.ready and not self.isVisible():return
        if self._screen is not None:
            for name in ('availableGeometryChanged','geometryChanged','logicalDotsPerInchChanged'):
                try:getattr(self._screen,name).disconnect(self._center)
                except (RuntimeError,TypeError):pass
        self._screen=screen
        if screen is not None:
            self.setScreen(screen)
            for signal in (screen.availableGeometryChanged,screen.geometryChanged,screen.logicalDotsPerInchChanged):
                signal.connect(self._center)
            self._center()

    def _center(self,*_):
        if self.ready and not self.isVisible():return
        if self._centered_surface:
            self._position_card()
            return
        screen=self._screen or self.screen() or QApplication.primaryScreen()
        if screen is not None:
            frame=self.frameGeometry();frame.moveCenter(screen.availableGeometry().center())
            self.move(frame.topLeft())

    def _settle_position(self):
        self._center();self._placement_attempts+=1
        if self._placement_attempts==3:self._placement_timer.setInterval(500)
        if not self.isVisible():self._placement_timer.stop()

    def show(self):
        if self._centered_surface:super().showMaximized()
        else:super().show()

    def showEvent(self,event):
        super().showEvent(event)
        self._placement_attempts=0
        QTimer.singleShot(0,self._center)
        if not self._centered_surface:
            self._placement_timer.setInterval(150);self._placement_timer.start()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'card'):self._position_card()

    def hideEvent(self,event):
        self._placement_timer.stop();super().hideEvent(event)
        if self._centered_surface and self.ready:
            QTimer.singleShot(0,self._release_surface)

    def _release_surface(self):
        if not self.isVisible():self.destroy()

    def paintEvent(self,event):
        painter=QPainter(self);painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(),Qt.transparent);painter.end()

    def closeEvent(self,event):
        if not self.ready:event.ignore()
        else:super().closeEvent(event)

    def set_stage(self,text):self.status.setText(tr(text));self.status.setAccessibleName(tr(text))

class StartupController(QObject):
    def __init__(self,app,info,logo,instance,on_ready):
        super().__init__(app)
        self.app,self.info,self.logo,self.instance,self.on_ready=app,info,logo,instance,on_ready
        self.splash=StartupWindow();self.worker=StartupWorker(app);self.window=None
        self.worker.stage.connect(self.splash.set_stage)
        self.worker.prepared.connect(self.build)
        self.worker.failed.connect(self.failed)
        self.splash.show();QTimer.singleShot(0,self.worker.start)
    @Slot(str)
    def failed(self,error):
        self.build(dict(sample=None,images={},specs={},error=error))
    @Slot(object)
    def build(self,bundle):
        try:self._build(bundle)
        except Exception as exc:
            from .diagnostics import log_exception
            log_exception(type(exc),exc,exc.__traceback__)
            self.splash.ready=True;self.splash.close();self.app.exit(1)

    def _build(self,bundle):
        self.splash.set_stage('Oberfläche vorbereiten …')
        from .product_ui import loader as images
        from .spec_ui import loader as specifications
        images().results.update(bundle['images']);specifications().results.update(bundle['specs'])
        from .update_manager import UpdateManager
        from .window import MainWindow
        manager=UpdateManager();manager._restart_timer.stop()
        self.app.aboutToQuit.connect(manager.finalize_exit)
        def progress():
            # Only already-built widgets process events; sampling starts after warmup.
            self.app.processEvents()
        self.window=MainWindow(self.info,self.logo,manager,startup_sample=bundle['sample'],startup_games=bundle.get('games'),preparing=progress)
        self.app.aboutToQuit.connect(lambda:self.instance.mark_restarting() if self.window.restart_requested or manager.pending_restart else None)
        self.window.ensurePolished();self.window.centralWidget().ensurePolished();self.window.layout().activate()
        self.window.grab()  # Populate real painter/backdrop caches before the first map.
        if bundle.get('error'):self.window.statusBar().showMessage(tr('Einige Startdaten konnten nicht geladen werden.'),12000)
        self.splash.ready=True
        self.window.show()
        if settings.get('mini_hud_enabled',False):self.window.set_mini_hud_enabled(True)
        if motion.enabled() and not eco.enabled():
            effect=QGraphicsOpacityEffect(self.splash);self.splash.card.setGraphicsEffect(effect)
            self.fade=QPropertyAnimation(effect,b'opacity',self.splash);self.fade.setDuration(motion.duration(180))
            self.fade.setStartValue(1.);self.fade.setEndValue(0.);self.fade.setEasingCurve(QEasingCurve.OutCubic)
            self.fade.finished.connect(self.splash.close);self.fade.start()
        else:self.splash.close()
        self.on_ready(self.window,manager)
        if manager.pending_restart:manager._restart_timer.start(200)
