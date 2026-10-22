"""Real HTTPS: slow reads, socket timeout, cancellation, retry and centered percent."""
import hashlib,os,ssl,subprocess,sys,tempfile,threading,time,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from vitalux import profiles,settings,updater,theme
from vitalux.update_manager import UpdateManager
from vitalux.pages_extra import UpdatePage

app=QApplication.instance() or QApplication([])
body=b'\x7fELF'+b'\x00'*4+b'AI\x02'+bytes(range(256))*256
sha=hashlib.sha256(body).hexdigest()
class Server(ThreadingHTTPServer):daemon_threads=True
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        self.send_response(200)
        if self.path!='/no-length':self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        try:
            for i in range(0,len(body),4096):
                self.wfile.write(body[i:i+4096]);self.wfile.flush()
                if self.path=='/stall' and i==0:time.sleep(.8)
                else:time.sleep(.04)
        except (BrokenPipeError,ConnectionResetError,ssl.SSLError):pass

def settle(condition,seconds=5):
    end=time.monotonic()+seconds
    while not condition() and time.monotonic()<end:app.processEvents();time.sleep(.01)
    assert condition(),'Transfer did not settle within its expected bound'

with tempfile.TemporaryDirectory(prefix='vitalux-transfer-') as folder:
    root=Path(folder);cert=root/'cert.pem';key=root/'key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    server=Server(('127.0.0.1',0),Handler)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
    server.socket=context.wrap_socket(server.socket,server_side=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    trusted=ssl.create_default_context(cafile=str(cert))
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=trusted))
    base=f'https://127.0.0.1:{server.server_port}'
    calls=[]
    def request(req,timeout):
        calls.append(timeout)
        return opener.open(req,timeout=.25 if req.full_url.endswith('/stall') else timeout)
    try:
        with patch.object(updater,'_github_request',side_effect=request):
            progress=[];start=time.monotonic()
            updater._download_verified(base+'/slow',root/'verified.AppImage',sha,lambda p:progress.append((p,time.monotonic()-start)),len(body)+1)
            assert (root/'verified.AppImage').read_bytes()==body
            assert any(0<p<80 for p,_ in progress),progress
            assert all(p<=q for (p,_),(q,__) in zip(progress,progress[1:]))
            assert calls[-1]==15
            unknown=[]
            updater._download_verified(base+'/no-length',root/'without-header',sha,unknown.append,len(body)+1,expected_size=len(body))
            assert any(0<p<80 for p in unknown),unknown
            assert (root/'without-header').read_bytes()==body
            start=time.monotonic()
            try:
                updater._download_verified(base+'/stall',root/'partial',sha,lambda _:None,len(body)+1)
                raise AssertionError('A stalled HTTPS transfer was accepted')
            except TimeoutError:pass
            assert time.monotonic()-start<1.2
            owned=root/'Vitalux.AppImage';owned.write_bytes(b'old image')
            env={f'XDG_{kind.upper()}_HOME':str(root/kind) for kind in profiles.KINDS}
            env['APPIMAGE']=str(owned)
            with patch.dict(os.environ,env),patch.object(settings,'PATH',str(root/'settings.json')):
                profiles.select('stable')
                manager=UpdateManager();manager._timer.stop()
                record=dict(ok=True,eligible=True,newer=True,latest='0.9.6.3-unstable.5',channel='unstable',url=base+'/slow',sha256=sha,bytes=len(body),notes='Test changes')
                manager._on_checked(dict(unstable=record));manager.set_channel('unstable')
                page=UpdatePage(manager);page.resize(700,800);page.show()
                manager.install();settle(lambda:manager.progress_value>0)
                page.cancel_button.click();assert manager.cancelling
                settle(lambda:manager.status=='error')
                settle(lambda:not any(w.isRunning() for w in manager._active_threads))
                assert 'abgebrochen' in manager.error.lower() and profiles.selected()=='stable'
                assert not manager.pending_restart and owned.read_bytes()==b'old image'
                assert not list(root.glob('.vitalux-next-*'))
                assert not page.install_retry.isHidden()
                restarted=[];manager.restart.connect(lambda:restarted.append(manager.pending.copy()))
                page.install_retry.click();settle(lambda:manager.pending_restart)
                settle(lambda:bool(restarted))
                assert len(restarted)==1 and restarted[0]['version']==record['latest']
                assert Path(manager.pending_path).read_bytes()==body
                assert owned.read_bytes()==b'old image'
                assert profiles.selected()=='unstable' and manager.progress_value==100
                for mode,_ in theme.CHOICES:
                    theme.set_mode(mode);theme.set_accent('#4f8cff');app.setStyleSheet(theme.stylesheet())
                    for value in (0,27,50,81,100):
                        page._progress(value);assert page.progress_bar.value==value
                        assert page.progress_bar.accessibleDescription()==f'{value}%'
                        assert not page.progress_bar.grab().isNull()
                assert manager.shutdown();page.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
print('Real slow HTTPS progress, bounded idle timeout, actual install-worker cancel/retry, verified bytes and all-design centered percentages PASS')
