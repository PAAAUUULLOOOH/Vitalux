"""Manufacturer text translates both ways, preserves identifiers and works offline."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import spec_language
source=dict(model='Example mainboard',source='https://www.msi.com/specification',checked_at=10,
 sections=[dict(title='Technische Spezifikationen',rows=[['Memory','Supports DDR5-6000 memory modules.'],['Socket','AM5'],['CPU','AMD Ryzen 7 9800X3D']])])
calls=[]
def translate(text,language):
 calls.append(language)
 return text.replace('Supports ','Unterstützt ').replace(' memory modules.',' Speichermodule.') if language=='de' else text.replace('Unterstützt ','Supports ').replace(' Speichermodule.',' memory modules.')
with tempfile.TemporaryDirectory() as folder:
 de=spec_language.localize(source,'de',download=translate,root=folder)
 rows=dict(de['sections'][0]['rows']);assert rows['Speicher']=='Unterstützt DDR5-6000 Speichermodule.',rows
 assert 'AMD Ryzen 7 9800X3D' in rows.values() and 'AM5' in rows.values()
 before=len(calls)
 cached=spec_language.localize(source,'de',offline=True,root=folder)
 assert cached==de and len(calls)==before
 en=spec_language.localize(de,'en',download=translate,root=folder)
 assert any('Supports DDR5-6000 memory modules.'==v for g in en['sections'] for k,v in g['rows'])
 changed=dict(source,checked_at=11,sections=[dict(title='Technische Spezifikationen',rows=[['Memory','A new untranslated paragraph.']])])
 assert spec_language.localize(changed,'de',offline=True,root=folder) is None
 try:spec_language.localize(changed,'de',download=lambda *_:'Lost all identity markers',root=folder)
 except ValueError:pass
 else:raise AssertionError('Malformed translation accepted')
 assert source['sections'][0]['rows'][0][1]=='Supports DDR5-6000 memory modules.'
print('DE/EN specs, unchanged technical identifiers, offline cache, source invalidation and malformed-response rejection PASS')
