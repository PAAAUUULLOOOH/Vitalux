"""Visible designs, internal render modes and independent color/background data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS = json.loads((ROOT/'assets/design-presets.json').read_text())['presets']
VISIBLE = ('obsidian_gold','glass','crystal_atrium','nebula_prism','quantum_core','sculpt','aurora_bloom','eclipse_crystal')
INTERNAL = ('minimal','nexus')
AVAILABLE = (*VISIBLE,*INTERNAL)
CHOICES = tuple((key,{'aurora_bloom':'Aurora Bloom','sculpt':'Sculpt'}.get(key) or PRESETS[key]['title']) for key in VISIBLE)
RETIRED = {'dark':'obsidian_gold','black_glass':'glass',
           'black_glass_gold':'obsidian_gold','holographic':'quantum_core',
           'aether_glass':'glass','liquid_silver':'obsidian_gold','crystal_glass':'crystal_atrium','light':'sculpt'}
FIELDS = ('accent','background_style','custom_background_selected','custom_background_fit')


def factory(key):
    if key=='nexus':
        from .nexus import PALETTE
        return dict(PALETTE)
    if key=='sculpt':
        from .sculpt import PALETTE
        return dict(PALETTE)
    if key=='aurora_bloom':
        from .aurora_bloom import PALETTE
        return dict(PALETTE)
    return dict(PRESETS.get(key,PRESETS['obsidian_gold'])['palette'])


def accent_preset(value):
    if isinstance(value,str) and value.startswith('palette:'):
        return PRESETS.get(value[8:])
    return None


def defaults():
    return dict(accent='design_default',background_style='theme_default',
                custom_background_selected='',custom_background_fit='cover')


def _finish_migration(result):
    """Retire only the skin choice; retain personal colors and imported data."""
    if result.get('theme')=='light':result['theme']='sculpt'
    result['_design_catalog_revision']=4
    return result


def migrate(data):
    """Retain personal colors and the appearance of discontinued selections."""
    result=dict(data)
    revision=result.get('_design_catalog_revision',0)
    if revision in (3,4):return _finish_migration(result)
    if result.get('accent')=='palette:crystal_atrium':result['accent']='palette:crystal_atrium_original'
    if isinstance(result.get('design_settings'),dict):
        result['design_settings']={key:dict(value,accent='palette:crystal_atrium_original')
            if isinstance(value,dict) and value.get('accent')=='palette:crystal_atrium' else value
            for key,value in result['design_settings'].items()}
    if revision in (1,2):
        if result.get('theme')=='crystal_glass':result['theme']='crystal_atrium'
        saved=dict(result.get('design_settings') or {})
        if 'crystal_glass' in saved:
            previous=saved.pop('crystal_glass')
            saved['crystal_atrium']=previous
            result['design_settings']=saved
        return _finish_migration(result)
    if 'theme' not in result:return result
    selected=result.get('theme','obsidian_gold')
    if not isinstance(selected,str):selected='obsidian_gold';result['theme']=selected
    old_fixed={'obsidian_gold','aether_glass','eclipse_crystal','liquid_silver',
               'nebula_prism','quantum_core','crystal_atrium','crystal_glass','black_glass_gold'}
    if selected in RETIRED:
        result['theme']=RETIRED[selected]
        if selected!='crystal_glass' and result.get('background_style','theme_default')=='theme_default':
            result['background_style']=selected
        if selected in old_fixed and selected!='crystal_glass':result['accent']='palette:'+selected
    elif selected=='minimal':
        result['theme']='obsidian_gold'
    elif selected in old_fixed:
        result['accent']='design_default'
    result['_crystal_design_revision']=2
    return _finish_migration(result)


def switch(key):
    from . import settings
    if key not in AVAILABLE:return False
    data=settings._load();saved=dict(data.get('design_settings') or {})
    old=data.get('theme','obsidian_gold')
    saved[old]={field:data.get(field,default) for field,default in defaults().items()}
    incoming=saved.get(key,defaults())
    values={field:incoming.get(field,default) for field,default in defaults().items()}
    return settings.set_many(dict(values,theme=key,design_settings=saved,_design_catalog_revision=4,_crystal_design_revision=2))



def remember():
    from . import settings
    data=settings._load();selected=data.get('theme','obsidian_gold')
    saved=dict(data.get('design_settings') or {})
    values={field:data.get(field,default) for field,default in defaults().items()}
    if saved.get(selected)==values and data.get('_design_catalog_revision')==4:return
    saved[selected]=values
    settings.set_many(dict(design_settings=saved,_design_catalog_revision=4,_crystal_design_revision=2))
