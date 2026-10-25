"""Exact manufacturer matching, complete tables/definitions/JSON and offline cache."""
import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import product_specs as specs
product=dict(kind='mainboard',vendor='MSI',model='MAG B650 TOMAHAWK WIFI (MS-7D75)',exact=True)
source='https://www.msi.com/Motherboard/MAG-B650-TOMAHAWK-WIFI/Specification'
raw='''<title>MAG B650 TOMAHAWK WIFI</title><div class="mega-menu"><h3>Memory</h3><p>wrong navigation data</p></div><table><tr><th>Chipset</th><td>AMD B650</td></tr><tr><td>Socket</td><td>AM5</td></tr><tr><td>Memory</td><td>DDR5, 4 DIMMs</td></tr></table><dl><dt>Form Factor</dt><dd>ATX</dd></dl><div><span class="TechSpecName">USB</span><div>USB-C</div></div>'''
data=specs.parse(product,raw,source);assert data
rows=[row for section in data['sections'] for row in section['rows']]
assert ['Socket','AM5'] in rows and ['Form Factor','ATX'] in rows
assert not any('wrong navigation' in value for _,value in rows)
assert specs.parse(dict(product,model='MAG B650M MORTAR WIFI'),raw,source) is None
assert specs.parse(product,raw,'https://retailer.invalid/specs') is None
with tempfile.TemporaryDirectory() as folder,patch.object(specs,'manufacturer_pages',return_value=[source]),patch.object(specs.ProductCache,'load',return_value=None):
 cache=specs.SpecCache(folder);calls=[]
 def download(url,*_):calls.append(url);return raw.encode()
 result=specs.resolve(product,cache,download);assert result and calls
 def offline(*_):raise AssertionError('Network call during offline read')
 assert specs.resolve(product,specs.SpecCache(folder),offline)==result
 assert specs.SpecCache(folder).load(dict(product,model='other')) is None
 p=cache.path(product);bad=json.loads(p.read_text());bad['key']='wrong';p.write_text(json.dumps(bad));assert cache.load(product) is None
print('Manufacturer tables, definitions and labeled fields, variant rejection, navigation exclusion and persistent offline cache PASS')

cpu=dict(kind='cpu',vendor='AMD',model='AMD Ryzen 7 9800X3D',exact=True)
raw='<title>AMD Ryzen 7 9800X3D</title><script type="application/ld+json">'+json.dumps({'@type':'Product','name':cpu['model'],'additionalProperty':[{'name':'Socket','value':'AM5'},{'name':'Cores','value':8}]})+'</script>'
data=specs.parse(cpu,raw,'https://www.amd.com/en/product');assert data
rows=[row for section in data['sections'] for row in section['rows']];assert ['Socket','AM5'] in rows
assert specs.parse(dict(cpu,model='Ryzen 7 9700X'),raw,'https://www.amd.com/en/product') is None

from vitalux.spec_ui import brief
sample={'sections':[{'rows':[['GPU','RX 9070 XT'],['Interface','PCIe 5.0'],['Engine Clock','Boost 3060 MHz'],['Video Memory','16 GB GDDR6'],['Marketing text','irrelevant']]}]}
summary=brief(sample,[('GPU','AMD')],'gpu')
assert summary[0][1]=='16 GB GDDR6' and len(summary)==4
