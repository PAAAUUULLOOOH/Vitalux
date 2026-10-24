"""Unit-aware component measurements and bounded histories, independent of Qt."""
from collections import deque
from .hardware_sensors import number
from .power_display import component_power, gpu_power, short_name, source_text


def gpu_scope(gpu,index=0):
    return 'gpu:'+str(gpu.get('id') or gpu.get('name') or index)


def describe(sample):
    groups={key:{} for key in ('cpu','ram','disks','network','system','sensors')}
    def add(scope,key,name,unit,value,default=False,source=''):
        value=number(value)
        if value is not None:
            groups.setdefault(scope,{})[key]=dict(key=key,name=name,unit=unit,value=value,default=default,source=source)
    def power(scope,record):
        if record:
            add(scope,'power','Leistung','W',record.get('value'),True,source_text(record))
            for title,value in record.get('limits',[]):
                add(scope,'limit:'+title,title,'W',value,False,record.get('limit_source') or source_text(record))
    cpu=sample.get('cpu') or {}
    for key,title,unit,default in (
        ('usage','Auslastung','%',True),('temp','Temperatur','°C',True),
        ('freq','Takt','MHz',False),('freq_max','Maximaler Takt','MHz',False)):
        add('cpu',key,title,unit,cpu.get(key),default)
    for index,value in enumerate(cpu.get('per_core') or []):
        add('cpu','thread:'+str(index),'Thread '+str(index),'%',value)
    for index,value in enumerate(cpu.get('load') or []):
        add('cpu','load:'+str(index),('Last · 1 Min','Last · 5 Min','Last · 15 Min')[index] if index<3 else 'Last','Last',value)
    ram=sample.get('ram') or {}
    add('ram','percent','RAM','%',ram.get('percent'),True)
    if number(ram.get('swap_total')) and ram['swap_total']>0:
        add('ram','swap_percent','Swap','%',ram.get('swap_percent'),True)
    for key,title in (('used','In Benutzung'),('available','Verfügbar'),('cached','Cache'),
                      ('buffers','Puffer'),('total','Gesamt'),('swap_used','Swap belegt'),('swap_total','Swap gesamt')):
        value=number(ram.get(key))
        if value is not None:
            add('ram',key,title,'GiB',value/2**30)
    records=sample.get('hardware') or []
    for component in ('cpu','ram'):
        power(component,component_power(records,component))
    for index,gpu in enumerate(sample.get('gpus') or []):
        scope=gpu_scope(gpu,index)
        record=gpu_power(gpu)
        power(scope,record)
        used,total=number(gpu.get('vram_used')),number(gpu.get('vram_total'))
        add(scope,'vram_pct','VRAM','%',100*used/total if used is not None and total is not None and total>0 else None,True)
        for key,title,unit,default in (
            ('usage','Auslastung','%',True),('temp','Temperatur','°C',True),
            ('hotspot','Hotspot','°C',False),('vram_temp','VRAM-Temperatur','°C',False),
            ('clock','GPU-Takt','MHz',False),('clock_mem','Speicher-Takt','MHz',False),
            ('fan_rpm','Lüfterdrehzahl','U/min',False),('fan','Lüfter','%',False),
            ('memory_busy','Speichercontroller','%',False),('video_busy','Video-Engine','%',False),
            ('encoder_busy','Encoder','%',False),('decoder_busy','Decoder','%',False)):
            add(scope,key,title,unit,gpu.get(key),default)
        voltage=number(gpu.get('voltage'))
        add(scope,'voltage','Spannung','V',voltage/1000 if voltage is not None else None)
        if used is not None:
            add(scope,'vram_used','VRAM belegt','GiB',used/2**30)
        if total is not None:
            add(scope,'vram_total','VRAM gesamt','GiB',total/2**30)
        if record and len(record.get('limits',[]))==1:
            key='limit:'+record['limits'][0][0]
            if key in groups[scope]:
                groups[scope][key]['name']='Leistungsgrenze'
    io=sample.get('io') or {}
    for key,title in (('read','Lesen'),('write','Schreiben')):
        add('disks',key,title,'B/s',io.get(key),True)
    for disk in sample.get('disks') or []:
        mount=disk.get('mount','')
        add('disks','used:'+mount,'Belegung · '+mount,'%',disk.get('percent'),mount=='/')
        for key,title in (('used','Belegt'),('total','Gesamt')):
            value=number(disk.get(key))
            if value is not None:
                add('disks',key+'_bytes:'+mount,title+' · '+mount,'GiB',value/2**30)
    net=sample.get('net') or {}
    for key,title in (('down','Download'),('up','Upload')):
        add('network',key,title,'B/s',net.get(key),True)
    for key,title in (('total_down','Empfangen gesamt'),('total_up','Gesendet gesamt')):
        value=number(net.get(key))
        if value is not None:
            add('network',key,title,'GiB',value/2**30)
    for interface in net.get('interfaces') or []:
        name=interface.get('name','')
        for key,title in (('bytes_recv','Empfangen gesamt'),('bytes_sent','Gesendet gesamt')):
            value=number(interface.get(key))
            if value is not None:
                add('network',key+':'+name,title+' · '+name,'GiB',value/2**30)
    resources=sample.get('app_resources') or {}
    add('system','app_cpu','Vitalux CPU','%',resources.get('cpu_percent'),True)
    memory=number(resources.get('rss_bytes'))
    add('system','app_ram','Vitalux RAM','MiB',memory/2**20 if memory is not None else None,True)

    represented={}
    for index,gpu in enumerate(sample.get('gpus') or []):
        scope=gpu_scope(gpu,index)
        own=gpu_power(gpu)
        represented[scope]=set(gpu.get('represented_sensors') or [])
        if own:
            represented[scope].add(own['id'])
    for component in ('cpu','ram'):
        main=component_power(records,component)
        represented[component]={main['id']} if main else set()
    defaults=set()
    for record in records:
        component=record.get('component','system')
        scope=component if component in groups or component.startswith('gpu:') else 'system'
        unit=record.get('unit') or {'temps':'°C','fans':'U/min','voltages':'V','powers':'W','frequencies':'MHz'}.get(record.get('kind'))
        if not unit:
            continue
        key='sensor:'+record['id']
        title=short_name(record)
        if record['id'] not in represented.get(scope,set()):
            default=(scope,record['kind']) not in defaults and scope in ('disks','network','system')
            add(scope,key,title,unit,record.get('value'),default,record.get('source',''))
            if number(record.get('value')) is not None:
                defaults.add((scope,record['kind']))
        add('sensors',key,title,unit,record.get('value'),('sensors',record['kind']) not in defaults,record.get('source',''))
        if number(record.get('value')) is not None:
            defaults.add(('sensors',record['kind']))
        for title,value in record.get('limits',[]):
            add('sensors',key+':'+title,short_name(record)+' · '+title,'W',value,False,record.get('source',''))
            if record['id'] not in represented.get(scope,set()):
                add(scope,key+':'+title,short_name(record)+' · '+title,'W',value,False,record.get('source',''))
    return groups


class MeasurementHistory:
    def __init__(self,maxlen=900):
        self.maxlen=maxlen
        self.times=deque(maxlen=maxlen)
        self.groups={}
        self.current={}

    def update(self,sample,stamp,interval=1):
        descriptions=describe(sample)
        self.current=descriptions
        if sample.get('_gap_before') and self.times:
            self._append(min(stamp-.001,self.times[-1]+max(1,interval)),{})
        self._append(stamp,descriptions)

    def _append(self,stamp,descriptions):
        self.times.append(stamp)
        for scope in self.groups.values():
            for metric in scope.values():
                metric['values'].append(None)
                metric['value']=None
        for name,scope in descriptions.items():
            target=self.groups.setdefault(name,{})
            for key,description in scope.items():
                if key not in target:
                    target[key]=dict(description,values=deque([None]*len(self.times),maxlen=self.maxlen))
                target[key].update(description)
                target[key]['values'][-1]=description['value']
