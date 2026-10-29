"""Real per-game UI: attribution, history, own timelines, themes and minimum size."""
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['VITALUX_SPEC_OFFLINE']='1'
os.environ['VITALUX_LOCAL_PREVIEW']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from vitalux import settings, theme, distro, sensors, i18n
from vitalux.game_service import GameService
from vitalux.games_page import GamesPage, OverlayProfile
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow, Sampler

app=QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms=30):
    deadline=time.monotonic()+ms/1000
    while time.monotonic()<deadline:app.processEvents();time.sleep(.003)

output=Path(os.environ['VITALUX_GAMES_EVIDENCE']) if os.environ.get('VITALUX_GAMES_EVIDENCE') else None
if output:output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',folder+'/settings.json'),\
        patch.object(Sampler,'start',lambda self:None),patch.object(GameService,'start',lambda self:None),\
        patch.object(MainWindow,'_start_background_smart',lambda self:None):
    settings.set_many(dict(theme='obsidian_gold',motion='off',component_images=False,close_to_tray=False))
    theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet());i18n.set_lang('de')
    info=distro.info();window=MainWindow(info,load_logo(info,96),UpdateManager())
    window.resize(1500,1100);window.show();wait(70)
    page=window.pages[12][1]
    assert isinstance(page,GamesPage) and len(window.pages)==13
    assert window.navigation_indices()[8:11]==[8,12,9]
    report=dict(id='a'*32,game_id='steam:42',game_name='Cyberpunk 2077',started=1793100000,
                duration=2820,average_fps=132.,low_1=108.,low_01=74.,target_fps=120.,grade='good',
                plot=[[i*3,132+(i%7)-3,7.5+(i%5)*.2] for i in range(941)],
                maxima=dict(cpu_temp=69.,gpu_temp=72.,gpu_vram_used=11.2,gpu_power=224.),
                frames=300000,complete=True,per_frame=True)
    summary={key:value for key,value in report.items() if key!='plot'}
    previous=dict(summary,id='b'*32,started=1793013600,average_fps=128.,low_1=102.)
    games=[dict(id='steam:42',store='steam',appid='42',name='Cyberpunk 2077',installed=True,
                launcher_uri='steam://rungameid/42',cover='',latest=summary,connected=True,mangohud_available=True),
           dict(id='steam:43',store='steam',appid='43',name='Counter-Strike 2',installed=True,
                launcher_uri='steam://rungameid/43',cover='',latest=None,connected=False,mangohud_available=True),
           dict(id='heroic-gog:99',store='heroic',appid='99',name='Baldur’s Gate 3',installed=False,
                cover='',latest=None,connected=False,mangohud_available=False)]
    try:
        page._catalog(dict(games=games,sessions=[summary,previous]))
        window._switch_page(12);wait(40);page._report(report);wait(40)
        assert page.values[0].text()=='132' and page.values[3].text()=='Gut'
        assert page.history.rowCount()==2
        assert page.chart.time_range.currentData()==-1
        assert page.chart.graph.horizon_seconds>=2819
        timeline=list(page.chart._timestamps)
        sensors.prime();sample=sensors.collect();window.on_sample(sample);wait(30)
        assert page.chart._timestamps==timeline,'Live system samples overwrote the recorded game timeline'
        page.select_game('steam:43');assert page.current_report is None
        page._report(report);assert page.current_report is None,'Displayed another game’s report'
        page.select_game('steam:42');page.selected_report=report['id'];page._report(report)
        page._history_selected(1,0);assert page.selected_report=='b'*32
        page._report(report);assert page.current_report['id']=='a'*32
        page.selected_report=report['id'];page._report(report)
        for design in [key for key,_ in theme.CHOICES]+['eclipse_crystal','minimal']:
            settings.set_many(dict(theme='obsidian_gold' if design=='minimal' else design,ultra_eco=design=='minimal'))
            window.apply_appearance();wait(30)
            page._report(report)
            for width,height in ((1500,1100),(800,560)):
                window.resize(width,height);wait(30)
                scroll=window.stack.widget(12)
                assert page.width()<=scroll.viewport().width()+2,(design,page.width(),scroll.viewport().width())
                assert page.values[0].text()=='132'
                assert sum(tile.isVisible() for tile in page.tiles)<=3
                for tile in page.tiles:
                    if not tile.isVisible():continue
                    assert tile.height()==128 and tile.name.alignment()==Qt.AlignCenter
                    assert tile.cover.geometry()==tile.rect().adjusted(4,4,-4,-4)
                    assert tile.name.geometry().bottom()<tile.source.geometry().top()
                    assert tile.source.geometry().bottom()<tile.result.geometry().top()
                    assert all(tile.rect().contains(widget.geometry()) for widget in (tile.name,tile.cover,tile.source,tile.result)),design
                if output:window.grab().save(str(output/(design+'-'+str(width)+'.png')))
        window.resize(1500,1100);window.set_language('en');wait(30)
        page._report(report)
        assert window.nav_buttons[12].text().endswith('Games')
        assert page.values[3].text()=='Good'
        assert page.history.horizontalHeaderItem(4).text()=='Assessment'
        page.search.setText('counter');assert page.tiles[0].game_id=='steam:43'
        page.search.clear();page.select_game('steam:42')
        QTest.keyClick(page.tiles[1],Qt.Key_Return)
        assert page.selected_id=='steam:43'
        page.select_game('steam:42')
        with patch.object(page.service,'submit') as submitted,patch('vitalux.game_launch.start',return_value=True) as opened:
            page.start_game();assert submitted.call_args.args[0]=='launch'
            assert not opened.called and not page.start_button.isEnabled()
            page._launch_ready(games[0]);assert opened.call_args.args[0]['id']=='steam:42'
        dialog=OverlayProfile(page,games[0]);dialog.target.setValue(144)
        assert dialog._save()
        from vitalux import game_profiles
        assert game_profiles.load('steam:42')['target_fps']==144
        assert game_profiles.load('steam:43')['target_fps']==60
        finished=[];dialog.finished.connect(finished.append)
        dialog._save_close();assert not finished,'Profile closed before its worker succeeded'
        page.service.profile_saved.emit('unrelated');assert not finished
        page.service.profile_saved.emit('steam:42');assert finished==[QDialog.DialogCode.Accepted]
        wait(20)
        page._busy(False);page.open_profile();dialog=page._dialog
        error='Steam hat die Overlay-Startoptionen nicht übernommen. Das Spiel wurde nicht gestartet. Bitte prüfe das aktive Steam-Konto und die Zugriffsrechte.'
        page._error(error);visible=dialog.notice.text()
        page._catalog(dict(games=games,sessions=[summary,previous]))
        assert dialog.notice.text()==visible,'Catalog refresh discarded the setup failure'
        page._progress('Steam wird wieder geöffnet …')
        assert dialog.notice.text()==visible and page.notice.text()==visible
        page._busy(True);page._catalog(dict(games=games,sessions=[summary,previous]))
        assert not page.start_button.isEnabled() and not dialog.save_button.isEnabled()
        with patch.object(page.service,'submit') as submitted:
            page._busy(False);dialog._save()
            assert submitted.called and not dialog._operation_error and not page._operation_error
        page._busy(False);dialog.close();wait(20)
        window._switch_page(0);page._finished(report);wait(30)
        assert window.stack.currentIndex()==12 and page.current_report['game_id']=='steam:42'
        assert window.nav_buttons[12].isChecked()
        # Completion must update a previously empty catalog immediately, even
        # before a worker catalog snapshot arrives or the app restarts.
        page._catalog(dict(games=[dict(games[0],latest=None)],sessions=[]))
        page._finished(report);wait(20)
        assert page.tiles[0].result.text()=='Good' and page.history.rowCount()==1
        assert page.games[0]['latest']['id']==report['id']
        assert 'No session' not in page.session_name.text()
        from vitalux.games_page import grade_color
        assert page.history.item(0,4).foreground().color().name()==grade_color('good')
        assert grade_color('good') in page.values[3].styleSheet()
    finally:
        window._force_quit=True;window.close();wait(60)
print('Per-game reports/history, automatic page opening, isolated profiles, DE/EN and all eight minimum-width layouts PASS')
