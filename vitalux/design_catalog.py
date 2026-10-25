"""Visible designs, internal render modes and independent color/background data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS = json.loads((ROOT/'assets/design-presets.json').read_text())['presets']
VISIBLE = ('obsidian_gold','glass','crystal_glass','nebula_prism','quantum_core','light')
INTERNAL = ('eclipse_crystal','minimal')
AVAILABLE = (*VISIBLE,*INTERNAL)
CHOICES = tuple((key,PRESETS[key]['title']) for key in VISIBLE)
RETIRED = {'dark':'obsidian_gold','black_glass':'glass',
           'black_glass_gold':'obsidian_gold','holographic':'quantum_core',
           'aether_glass':'glass','liquid_silver':'obsidian_gold','crystal_atrium':'crystal_glass'}
FIELDS = ('accent','background_style','custom_background_selected','custom_background_fit')


def factory(key):
    return dict(PRESETS.get(key,PRESETS['obsidian_gold'])['palette'])


def accent_preset(value):
    if isinstance(value,str) and value.startswith('palette:'):
        return PRESETS.get(value[8:])
    return None


def defaults():
    return dict(accent='design_default',background_style='theme_default',
                custom_background_selected='',custom_background_fit='cover')


def migrate(data):
    """Retain personal colors and the appearance of discontinued selections."""
    result=dict(data)
    if result.get('_design_catalog_revision')==2:return result
    if result.get('_design_catalog_revision')==1:
        if result.get('theme')=='crystal_atrium':result['theme']='crystal_glass'
        saved=dict(result.get('design_settings') or {})
        if 'crystal_atrium' in saved:
            previous=saved.pop('crystal_atrium')
            saved.setdefault('crystal_glass',previous)
            result['design_settings']=saved
        result['_design_catalog_revision']=2
        return result
    if 'theme' not in result:return result
    selected=result.get('theme','obsidian_gold')
    if not isinstance(selected,str):selected='obsidian_gold';result['theme']=selected
    old_fixed={'obsidian_gold','aether_glass','eclipse_crystal','liquid_silver',
               'nebula_prism','quantum_core','crystal_atrium','crystal_glass','black_glass_gold'}
    if selected in RETIRED:
        result['theme']=RETIRED[selected]
        if result.get('background_style','theme_default')=='theme_default':
            result['background_style']=selected
        if selected in old_fixed:result['accent']='palette:'+selected
    elif selected=='minimal':
        result['theme']='obsidian_gold'
    elif selected in old_fixed:
        result['accent']='design_default'
    result['_crystal_design_revision']=2
    result['_design_catalog_revision']=2
    return result


def switch(key):
    from . import settings
    if key not in AVAILABLE:return False
    data=settings._load();saved=dict(data.get('design_settings') or {})
    old=data.get('theme','obsidian_gold')
    saved[old]={field:data.get(field,default) for field,default in defaults().items()}
    incoming=saved.get(key,defaults())
    values={field:incoming.get(field,default) for field,default in defaults().items()}
    return settings.set_many(dict(values,theme=key,design_settings=saved,_design_catalog_revision=2,_crystal_design_revision=2))



def remember():
    from . import settings
    data=settings._load();selected=data.get('theme','obsidian_gold')
    saved=dict(data.get('design_settings') or {})
    values={field:data.get(field,default) for field,default in defaults().items()}
    if saved.get(selected)==values and data.get('_design_catalog_revision')==1:return
    saved[selected]=values
    settings.set_many(dict(design_settings=saved,_design_catalog_revision=2,_crystal_design_revision=2))
