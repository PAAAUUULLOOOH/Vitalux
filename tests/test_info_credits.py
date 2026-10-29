"""Author and contributor attribution stays accessible in both interface languages."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from vitalux import i18n,theme
from vitalux.pages_extra import InfoPage,AUTHOR_URL,CREDIT_URL,CREDIT_TEXT
from vitalux.ui_locale import retranslate_widgets
app=QApplication([]);theme.set_mode('glass');app.setStyleSheet(theme.stylesheet());page=InfoPage({'name':'openSUSE'});page.show();app.processEvents()
for language,prefix in (('de','<b>Danke an:</b> '),('en','<b>Thanks to:</b> ')):
    i18n.set_lang(language);retranslate_widgets(page)
    assert AUTHOR_URL in page.author_credit.text() and page.author_credit.openExternalLinks()
    credit=page.support_credit
    assert credit.textFormat()==Qt.RichText and credit.openExternalLinks()
    assert credit.textInteractionFlags()&Qt.LinksAccessibleByMouse
    assert credit.text().startswith(prefix) and CREDIT_URL in credit.text() and 'TimBooH</a>' in credit.text()
    assert credit.accessibleName()==i18n.tr(CREDIT_TEXT)
    assert credit.font().pixelSize()<page.author_credit.font().pixelSize()
page.close()
print('DE/EN author/contributor links and accessibility PASS')
