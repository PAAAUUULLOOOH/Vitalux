#!/usr/bin/env python3
"""Download real pictures for all component kinds and verify offline UI reuse."""
import argparse,json,os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from vitalux.product_images import ProductCache,resolve,valid_image,product_key
from vitalux.product_ui import ProductHeader
from vitalux.widgets import label

PRODUCTS=(
 ('gpu','SAPPHIRE','SAPPHIRE PURE Radeon RX 9070 XT'),
 ('gpu','ASUS','ASUS TUF Gaming Radeon RX 9060 XT'),
 ('cpu','AMD','AMD Ryzen 7 9800X3D 8-Core Processor'),
 ('cpu','Intel','13th Gen Intel(R) Core(TM) i7-13700K'),
 ('mainboard','MSI','MAG B650 TOMAHAWK WIFI (MS-7D75)'),
 ('ram','Kingston','KF560C30BB-16'),
)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--require-all-components',action='store_true')
 parser.add_argument('--output',type=Path,default=Path('build/product-image-check'))
 args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 app=QApplication.instance() or QApplication([])
 def check(item):
  kind,vendor,model=item;product=dict(kind=kind,vendor=vendor,model=model,revision='',exact=True)
  cache=ProductCache(args.output/'cache'/product_key(product));result=resolve(product,cache)
  record=dict(kind=kind,vendor=vendor,model=model,found=bool(result))
  if result:
   def offline(*_):raise AssertionError('Cached product picture used the network')
   restored=resolve(product,ProductCache(cache.root),download=offline)
   assert restored and restored['cached'] and restored['sha256']==result['sha256']
   assert valid_image(Path(restored['path']).read_bytes())
   record.update(offline_reuse=True,cutout=result['cutout'],bytes=Path(result['path']).stat().st_size,source=result['source'])
  else:
   report=cache.root/(product_key(product)+'.lookup.json')
   if report.exists():record['diagnostic']=json.loads(report.read_text())
  print(json.dumps(record),flush=True)
  return product,result,record
 with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(check,PRODUCTS))
 for product,result,record in outcomes:
  header=ProductHeader(label(product['model'],'bigName',wrap=True),label(product['vendor'],'muted'),product['kind'])
  header.set_specs([('Model',product['model'])]);header.key=product_key(product)
  header._ready(header.key,result);header.resize(800,240);header.show();app.processEvents()
  if result:
   assert header.picture.isVisible() and not header.picture.pixmap.isNull()
   assert header.picture.geometry().right()<header.details.geometry().left()
  else:
   assert header.picture.isHidden() and header.details.geometry().left()<5
  assert header.grab().save(str(args.output/(product['kind']+'-'+product_key(product)[:8]+'.png')))
  record['ui_display']=bool(result);header.close()
 records=[record for _,_,record in outcomes]
 found={record['kind'] for record in records if record['found']}
 summary=dict(real_product_downloads=records,component_kinds_found=sorted(found),missing_component_kinds=sorted({'cpu','gpu','ram','mainboard'}-found))
 (args.output/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({key:value for key,value in summary.items() if key!='real_product_downloads'}),flush=True)
 if args.require_all_components and summary['missing_component_kinds']:
  raise SystemExit('No actual online picture found for: '+', '.join(summary['missing_component_kinds']))
 return 0

if __name__=='__main__':raise SystemExit(main())
