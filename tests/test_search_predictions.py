"""Partial-name predictions scroll to real controls, retaining focus in DE/EN."""
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QScrollArea,QWidget
from vitalux import settings,theme,i18n
from vitalux.control import PreferencesPage

app=QApplication.instance() or QApplication([])
def wait(ms):
    end=time.monotonic()+ms/1000
    while time.monotonic()<end:app.processEvents();time.sleep(.01)
class Host(QWidget):
    _tray=None
    render_backend_active='software'
    def apply_appearance(self):theme.set_mode(settings.get('theme','obsidian_gold'))
    def set_interval(self,value):pass

with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    settings.set_many(dict(theme='obsidian_gold',motion='smooth'))
    host=Host();page=PreferencesPage(host)
    scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page)
    scroll.resize(1000,650);page.install_search_overlay(scroll);scroll.show();wait(100)
    for language in ('de','en'):
        i18n.set_lang(language);page.retranslate()
        scroll.verticalScrollBar().setValue(0)
        page.search_overlay.open_search();wait(360)
        for query in ('min','mini','minih','minihu','minihud','MINIHUD','mini hud','minihdu'):
            page.search.setText(query)
            assert page.search_navigation.target is page.hud_on,(language,query)
            assert page.search_results.count()>=3
        wait(750)
        assert scroll.verticalScrollBar().value()>0
        assert page.search.hasFocus() and page.search_overlay.expanded
        queries=(('minihud layout',page.hud_size),('minihud opacity',page.hud_opacity),
                 ('accent',page.accent_combo),('hinterg',page.background_combo),
                 ('vulk',page.render_combo),('warnung',page.alert_toggle),
                 ('interval',page.interval),('ultra eco',page.eco_toggle),
                 ('wartung',page._maintenance_card),('reset',page.restore_button))
        for query,target in queries:
            page.search.setText(query)
            assert page.search_navigation.target is target,(language,query)
        wait(800)
        assert page.advanced.expanded
        assert page.advanced.isAncestorOf(page.restore_button)
        assert not hasattr(page,'clear_cache_btn') and not hasattr(page,'clear_preferences_btn')
        assert not hasattr(page,'sound_toggle') and not hasattr(page,'sound_volume')
        assert len(page.design_tiles)== 14 and all(t.key!='champagne_glass' for t in page.design_tiles)
        assert page.search.hasFocus()
        if language == 'en':
            assert page.search_results.item(0).text().startswith('Restore defaults')
        page.choose_search_result(page.search_results.item(0))
        assert page.search_overlay.idle_timer.remainingTime()>=4700
        page.search_overlay.close_search();wait(360)
    scroll.close();host.close()
print('Mini/MiniH/MiniHU/MiniHUD and typo predictions, DE/EN controls, real smooth scroll and unified reset PASS')
