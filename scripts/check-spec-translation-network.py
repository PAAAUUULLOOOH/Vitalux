#!/usr/bin/env python3
"""Exercise real DE/EN translation, technical identifiers, cached UI and offline reuse."""
import json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from vitalux import spec_language,i18n,settings
from vitalux.product_specs import SpecCache,product_key,resolve
from PySide6.QtWidgets import QApplication,QLabel
from vitalux.product_ui import ProductHeader
from vitalux.widgets import label
from vitalux.spec_ui import loader,SpecificationDialog
output=Path('build/spec-language-check');output.mkdir(parents=True,exist_ok=True)
root=output/'cache'
def translate(text,language):
 for attempt in range(3):
  try:return spec_language.network_translate(text,language)
  except OSError:
   if attempt==2:raise
   print('Translation transport retry '+str(attempt+1),flush=True)
   time.sleep(attempt+1)

probe=dict(source='https://www.msi.com/',checked_at=1,sections=[dict(title='Technische Spezifikationen',rows=[['Memory','Supports DDR5-6000 memory modules and Intel Core i5-14600KF processors.']])])
de=spec_language.localize(probe,'de',root=root,download=translate)
value=de['sections'][0]['rows'][0][1]
assert 'DDR5-6000' in value and 'Intel Core i5-14600KF' in value and 'Supports ' not in value,value
en=spec_language.localize(de,'en',root=root,download=translate)
assert any('Supports ' in v for g in en['sections'] for _,v in g['rows']),en
product=dict(kind='mainboard',vendor='MSI',model='MAG B650 TOMAHAWK WIFI (MS-7D75)',revision='',exact=True)
key=product_key(product)
source=SpecCache(Path('build/product-spec-check')/key/'cache').load(product) or resolve(product)
assert source,'Missing real mainboard datasheet'
app=QApplication.instance() or QApplication([]);settings.set('component_images',False)
records=[]
for language in ('de','en'):
 localized=spec_language.localize(source,language,root=root,download=translate)
 assert localized and localized['language']==language
 def offline(*_):raise AssertionError('Translation cache accessed the network')
 assert spec_language.localize(source,language,download=offline,offline=True,root=root)==localized
 i18n.set_lang(language)
 loader()._ready(key,dict(source=source,localized=localized,language=language))
 header=ProductHeader(label(product['model'],'bigName'),label('MSI','muted'),'mainboard')
 header.set_product(product);header.resize(800,400);header.show();app.processEvents()
 dialog=SpecificationDialog(header);dialog.show();app.processEvents()
 displayed=[item.text() for item in dialog.scroll.findChildren(QLabel)]
 expected=[value for group in localized['sections'] for _,value in group['rows']]
 assert all(value in displayed for value in expected)
 assert dialog.source_button.isVisible() and dialog.scroll.horizontalScrollBar().maximum()==0
 dialog.grab().save(str(output/(language+'.png')))
 records.append(dict(language=language,rows=len(expected),offline_cache=True,native_dialog=True))
 print(json.dumps(records[-1]),flush=True)
 dialog.close();header.close()
(output/'results.json').write_text(json.dumps(records,indent=2))
print('Real DE/EN manufacturer translation, preserved CPU identifiers and cached native dialogs PASS',flush=True)
