"""Compatible update selection, signed metadata parsing and lock consistency."""
import hashlib,json,sys,tempfile
from pathlib import Path
from urllib.request import Request
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from dependency_audit import python_component,pypi_component,python_compatible,SafeRedirect
from update_dependencies import select_wheel,apply
from ubuntu_dependencies import paragraphs,verified_download
from runtime_inventory import expected

assert python_compatible('>=3.10,<3.13',(3,12,16))
assert not python_compatible('>=3.13',(3,12,16))
assert not python_compatible('!=3.12.*',(3,12,16))
try:python_compatible('unsupported constraint')
except ValueError:pass
else:raise AssertionError('Unknown compatibility requirement was accepted')
refs=[dict(ref='refs/tags/v'+v) for v in ('3.12.9','3.12.16','3.12.17rc1','3.13.0')]
assert python_component('3.12.7',lambda url:refs)['latest']=='3.12.16'
data=dict(info=dict(version='8.0.0'),releases={
    '7.2.2':[dict(requires_python='>=3.6')],
    '7.2.3':[dict(requires_python='>=3.12,<3.13')],
    '7.3.0':[dict(requires_python='>=3.13')],
    '7.9.0':[dict(yanked=True)],'7.10.0rc1':[{}],'8.0.0':[{}]})
def pypi(url):
    return dict(vulnerabilities=[dict(id='active'),dict(id='withdrawn',withdrawn='date')]) if url.endswith('/7.2.2/json') else data
result=pypi_component(('psutil','7.2.2'),pypi,(3,12,16))
assert result['latest']=='7.2.3' and result['update'] and len(result['vulnerabilities'])==1
def wheel(name):return dict(filename=name,packagetype='bdist_wheel')
files=[wheel('pkg-1.0-cp310-abi3-manylinux_2_34_x86_64.whl'),
       wheel('pkg-1.0-cp313-abi3-manylinux_2_34_x86_64.whl'),
       wheel('pkg-1.0-cp312-cp312-manylinux_2_41_x86_64.whl'),
       wheel('pkg-1.0-cp312-cp312-musllinux_1_2_x86_64.whl')]
assert select_wheel(dict(info=dict(name='pkg'),urls=files))==files[0]
request=Request('https://api.github.com/example',headers={'Authorization':'Bearer test-only'})
redirected=SafeRedirect().redirect_request(request,None,302,'',{},'https://example.com/')
assert redirected.get_header('Authorization') is None,'API credential leaked across hosts'
assert SafeRedirect().redirect_request(request,None,302,'',{},'http://api.github.com/example').get_header('Authorization') is None
record=list(paragraphs('Package: example\nVersion: 1\nChecksums-Sha256:\n abc 1 first\n def 2 second\n'))[0]
assert record['Checksums-Sha256'].splitlines()==['','abc 1 first','def 2 second']
with tempfile.TemporaryDirectory(prefix='vitalux-maintenance-') as folder:
    root=Path(folder);source=root/'source';source.write_bytes(b'verified payload')
    for name,kind,old,new in (('cpython','cpython','3.12.16','3.13.0'),('PySide6-Essentials','pypi','6.12.0','6.13.0')):
        try:apply(dict(updates=[dict(name=name,kind=kind,current=old,latest=new)]),root/'rejected','unused-keyring')
        except ValueError:pass
        else:raise AssertionError('Unreviewed ABI change accepted')
    assert not (root/'rejected').exists(),'Rejected ABI proposal mutated the build tree'
    target=root/'download';checksum=hashlib.sha256(source.read_bytes()).hexdigest()
    verified_download(source.as_uri(),target,checksum);assert target.read_bytes()==source.read_bytes()
    try:verified_download(source.as_uri(),root/'bad','0'*64)
    except ValueError:pass
    else:raise AssertionError('Unverified payload accepted')
    assert not (root/'bad').exists() and not (root/'bad.part').exists()
    (root/'third_party').mkdir()
    sources=[dict(name=name,version='6.12.0') for name in ('pyside-setup','qtbase','qtdeclarative','qtsvg','qtwayland','qtimageformats')]
    sources += [dict(name='cpython',version='3.12.16'),dict(name='psutil',version='7.2.2')]
    (root/'third_party/sources.lock.json').write_text(json.dumps(sources))
    requirements=root/'requirements-dev.txt';requirements.write_text('PySide6-Essentials==6.12.0\npsutil==7.2.2\n')
    assert expected(root)['python']=='3.12.16'
    requirements.write_text('PySide6-Essentials==6.12.1\npsutil==7.2.2\n')
    try:expected(root)
    except ValueError:pass
    else:raise AssertionError('Unrebuilt bindings/source mismatch permitted')
print('Stable/yanked/Python/ABI selection, advisory handling, checksums, token isolation and runtime/source version contract PASS')
