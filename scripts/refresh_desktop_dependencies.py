#!/usr/bin/env python3
"""Refresh the signed Ubuntu ABI baseline, corresponding sources and licenses."""
import argparse,hashlib,importlib.util,json,re,subprocess,tempfile
from pathlib import Path
from ubuntu_dependencies import UbuntuArchive,BASE,verified_download

ROOT=Path(__file__).resolve().parents[1]


def refresh(archive,work,core=None):
    path=ROOT/'licenses/system-libraries/desktop-libraries.json'
    metadata=json.loads(path.read_text());libraries={entry['name']:entry for entry in metadata['libraries']}
    if core:
        for entry in json.loads(Path(core).read_text()):
            if entry['name'] not in libraries:libraries[entry['name']]=entry
    archive.cache_packages(entry['package'] for entry in libraries.values())
    packages={};sources={};updated=[]
    with tempfile.TemporaryDirectory(prefix='vitalux-baseline-') as folder:
        extracted=Path(folder)
        for name in sorted({entry['package'].split(':')[0] for entry in libraries.values()}):
            record=archive.package(name)
            package=dict(url=BASE+record['Filename'],filename=Path(record['Filename']).name,
                         size=int(record['Size']),sha256=record['SHA256'])
            binary=verified_download(package['url'],work/'packages'/package['filename'],package['sha256'])
            subprocess.run(['dpkg-deb','--extract',str(binary),str(extracted)],check=True)
            packages[name]=package
            source=record.get('Source',name);match=re.fullmatch(r'([^\s]+)(?: \(([^)]+)\))?',source)
            if not match:raise ValueError('Unexpected signed source field: '+source)
            sources[match.group(1)]=match.group(2) or record['Version']
        for entry in libraries.values():
            matches=list(extracted.rglob(entry['name']))
            matches=[candidate for candidate in matches if candidate.is_file() and candidate.resolve().is_relative_to(extracted)]
            if not matches:raise ValueError('Updated baseline lost required SONAME '+entry['name'])
            library=matches[0].resolve();record=archive.package(entry['package'])
            item=dict(name=entry['name'],sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
                package=record['Package']+':amd64',source=record.get('Source',record['Package']).split()[0],
                version=record['Version'],file=str(library.relative_to(extracted)))
            if 'path' in entry:item['path']=entry['path']
            if entry['name'] in ('libssl.so.3','libcrypto.so.3','libsqlite3.so.0'):
                item['path']='fallback-libraries/'+entry['name']+'/'+entry['name']
            updated.append(item)
    archive.cache_sources(sources)
    locked_sources=[]
    for name,version in sorted(sources.items()):locked_sources+=archive.source(name,version)
    lock=ROOT/'third_party/sources.lock.json';records=json.loads(lock.read_text())
    records=[entry for entry in records if not any(domain in entry.get('url','') for domain in ('archive.ubuntu.com/ubuntu/pool/','security.ubuntu.com/ubuntu/pool/'))]
    records+=locked_sources
    metadata['libraries']=sorted(updated,key=lambda entry:entry['name'])
    metadata['packages']=list(packages.values());path.write_text(json.dumps(metadata,indent=2)+'\n')
    lock.write_text(json.dumps(records,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('desktop_builder',ROOT/'scripts/build-desktop-libraries.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    destination=ROOT/'portable-runtime'/metadata['archive']
    builder.build(destination,work/'packages',update_lock=True)
    with __import__('tarfile').open(destination) as payload:
        for member in payload.getmembers():
            if member.isfile() and member.name.startswith('licenses/system-libraries/'):
                target=ROOT/member.name;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(payload.extractfile(member).read())
    print('Updated signed Ubuntu baseline:',len(updated),'libraries and',len(locked_sources),'corresponding source files')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=ROOT/'build/dependencies/desktop')
    parser.add_argument('--keyring',type=Path,default=Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg'))
    parser.add_argument('--python-core',type=Path)
    args=parser.parse_args();archive=UbuntuArchive(args.work/'apt',args.keyring);archive.refresh()
    refresh(archive,args.work,args.python_core)
