#!/usr/bin/env python3
"""Verify real manufacturer datasheets, exact model matching and offline reuse."""
import argparse,json,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux.product_specs import resolve,SpecCache,product_key,fetch,parse
PRODUCTS=(('gpu','SAPPHIRE','SAPPHIRE PURE Radeon RX 9070 XT'),('gpu','ASUS','ASUS TUF Gaming Radeon RX 9060 XT'),('cpu','Intel','13th Gen Intel(R) Core(TM) i7-13700K'),('cpu','AMD','AMD Ryzen 7 9800X3D 8-Core Processor'),('mainboard','MSI','MAG B650 TOMAHAWK WIFI (MS-7D75)'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('build/product-spec-check'));p.add_argument('--require-all-components',action='store_true');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 def check(item):
  kind,vendor,model=item;product=dict(kind=kind,vendor=vendor,model=model,revision='',exact=True)
  path=args.output/product_key(product);path.mkdir(parents=True,exist_ok=True)
  calls=[]
  def download(url,limit,hosts):
   try:
    raw=fetch(url,limit,hosts)
    if 'bing.com' not in url and 'duckduckgo' not in url:
     filename=str(len(calls))+'.html';(path/filename).write_bytes(raw);calls.append(dict(url=url,file=filename,bytes=len(raw)))
    return raw
   except Exception as exc:calls.append(dict(url=url,error=type(exc).__name__));raise
  result=resolve(product,SpecCache(path/'cache'),download=download)
  record=dict(kind=kind,vendor=vendor,model=model,found=bool(result),requests=calls)
  if result:
   def offline(*_):raise AssertionError('Cached specifications used the network')
   cached=resolve(product,SpecCache(path/'cache'),download=offline)
   assert cached==result
   record.update(source=result['source'],rows=sum(len(s['rows']) for s in result['sections']),offline=True,fields=[row[0] for s in result['sections'] for row in s['rows']][:12])
   assert record['rows']>=10
  print(json.dumps(record),flush=True)
  return record
 with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(check,PRODUCTS))
 # Render the actual retrieved datasheets and verify the full scrollable dialog.
 import os
 os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['VITALUX_SPEC_OFFLINE']='1'
 from PySide6.QtWidgets import QApplication,QLabel
 from vitalux import settings,theme
 from vitalux.product_ui import ProductHeader
 from vitalux.spec_ui import loader as specification_loader,SpecificationDialog
 from vitalux.widgets import label
 app=QApplication.instance() or QApplication([])
 settings.set('component_images',False);app.setStyleSheet(theme.stylesheet())
 for item,record in zip(PRODUCTS,records):
  if not record['found']:continue
  kind,vendor,model=item;product=dict(kind=kind,vendor=vendor,model=model,revision='',exact=True)
  data=SpecCache(args.output/product_key(product)/'cache').load(product)
  specification_loader().results[product_key(product)]=data
  header=ProductHeader(label(model,'bigName',wrap=True),label(vendor,'muted'),kind)
  header.set_product(product);header.resize(800,260);header.show();app.processEvents()
  assert not header.picture.isVisible()
  assert abs(header.details.geometry().center().x()-header.rect().center().x())<=2
  dialog=SpecificationDialog(header);dialog.resize(720,600);dialog.show();app.processEvents()
  expected=[value for section in data['sections'] for _,value in section['rows']]
  displayed=[widget.text() for widget in dialog.scroll.findChildren(QLabel)]
  assert all(value in displayed for value in expected)
  assert dialog.scroll.horizontalScrollBar().maximum()==0
  assert dialog.source_button.isVisible()
  assert dialog.grab().save(str(args.output/(kind+'-'+product_key(product)[:8]+'.png')))
  record['ui_display']=True;dialog.close();header.close();app.processEvents()
 (args.output/'results.json').write_text(json.dumps(records,indent=2))
 missing={'cpu','gpu','mainboard'}-{r['kind'] for r in records if r['found']}
 if args.require_all_components and missing:raise SystemExit('No manufacturer datasheet found for: '+', '.join(sorted(missing)))
if __name__=='__main__':main()
