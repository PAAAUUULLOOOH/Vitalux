#!/usr/bin/env python3
"""Exercise real TCP/UDP accounting and session blocks in an isolated Linux VM.

Run only in a disposable guest with VITALUX_NETWORK_TEST_VM=1. This must never
attach test filters to a developer's desktop or shared production host.
"""
import json,os,subprocess,sys,socket,threading,time
from pathlib import Path

if os.environ.get('VITALUX_NETWORK_TEST_VM')!='1' or os.geteuid()!=0:
    raise SystemExit('Run inside a disposable Linux VM with VITALUX_NETWORK_TEST_VM=1')
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'vitalux'))
sys.path.insert(0,'/')
import network_kernel
from network_kernel import NetworkSession,application,applications,socket_snapshot
TEST_UID=60123
assert not applications(TEST_UID),'Disposable test UID is already in use'

tcp=socket.socket();tcp.bind(('127.0.0.1',0));tcp.listen()
udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);udp.bind(('127.0.0.1',0))
tcp6=socket.socket(socket.AF_INET6);tcp6.bind(('::1',0));tcp6.listen()
udp6=socket.socket(socket.AF_INET6,socket.SOCK_DGRAM);udp6.bind(('::1',0))
received={'tcp':0,'udp':0}
server_connections=[]
def tcp_connection(connection):
    server_connections.append(connection)
    try:
        while True:
            data=connection.recv(65536)
            if not data:return
            received['tcp']+=len(data)
            connection.sendall(b'k'*len(data))
    except OSError:pass
def tcp_server(listener=tcp):
    while True:
        connection,_=listener.accept()
        threading.Thread(target=tcp_connection,args=(connection,),daemon=True).start()
def udp_server(listener=udp):
    while True:
        data,address=listener.recvfrom(65536)
        received['udp']+=len(data)
        listener.sendto(data,address)
threading.Thread(target=tcp_server,daemon=True).start()
threading.Thread(target=udp_server,daemon=True).start()
threading.Thread(target=tcp_server,args=(tcp6,),daemon=True).start()
threading.Thread(target=udp_server,args=(udp6,),daemon=True).start()

worker=r'''
import json,socket,sys,os
tcp=None;udps={}
print(json.dumps({'pid':os.getpid()}),flush=True)
for line in sys.stdin:
 req=json.loads(line)
 try:
  if 'cpu' in req:os.sched_setaffinity(0,{req['cpu']})
  family=socket.AF_INET6 if req.get('ipv6') else socket.AF_INET
  host='::1' if req.get('ipv6') else '127.0.0.1'
  op=req['op']
  if op=='connect':
   if tcp is not None:tcp.close()
   tcp=socket.socket(family);tcp.settimeout(.7);tcp.connect((host,req['port']));result='connected'
  elif op=='tcp':
   size=req.get('bytes',65536);tcp.sendall(b'x'*size);n=0
   while n<size:n+=len(tcp.recv(65536))
   result=n
  elif op=='udp':
   if family not in udps:
    udps[family]=socket.socket(family,socket.SOCK_DGRAM);udps[family].settimeout(.5)
   udp=udps[family];udp.sendto(b'u'*4096,(host,req['port']));result=len(udp.recv(65536))
  elif op=='receive':result=len(tcp.recv(65536))
  elif op=='probe':
   s=socket.socket(family);s.settimeout(.5);s.connect((host,req['port']));s.close();result='allowed'
  elif op=='private':
   import ctypes
   result=ctypes.CDLL(None).prctl(4,0,0,0,0)
   assert result==0
  elif op=='fork_probe':
   reader,writer=os.pipe();child=os.fork()
   if child==0:
    os.close(reader)
    try:
     s=socket.socket(family,socket.SOCK_DGRAM if req.get('udp') else socket.SOCK_STREAM);s.settimeout(.5)
     if req.get('udp'):s.sendto(b'child-probe',(host,req['port']));s.recv(65536)
     else:s.connect((host,req['port']))
     os.write(writer,b'escaped')
    except OSError:os.write(writer,b'blocked')
    os._exit(0)
   os.close(writer);result=os.read(reader,64).decode();os.close(reader);os.waitpid(child,0)
  elif op=='quit':break
  print(json.dumps({'ok':True,'result':result,'child':child if op=='fork_probe' else None}),flush=True)
 except OSError as exc:print(json.dumps({'ok':False,'error':str(exc)}),flush=True)
'''
def unprivileged():os.setgid(TEST_UID);os.setuid(TEST_UID)
client=subprocess.Popen([sys.executable,'-u','-c',worker],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,preexec_fn=unprivileged)
identity=json.loads(client.stdout.readline());pid=identity['pid']
def command(op,_process=client,**values):
    _process.stdin.write(json.dumps(dict(op=op,**values))+'\n');_process.stdin.flush()
    return json.loads(_process.stdout.readline())

other=subprocess.Popen([sys.executable,'-u','-c',worker+'\n# unrelated application'],
    stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,preexec_fn=unprivileged)
json.loads(other.stdout.readline())


def check_ipv6():
    assert command('connect',port=tcp6.getsockname()[1],ipv6=True)['ok']
    assert command('tcp',bytes=4096)['result']==4096
    assert command('udp',port=udp6.getsockname()[1],ipv6=True)['result']==4096
    protection=NetworkSession(TEST_UID)
    try:
        identity=application(pid,TEST_UID)
        protection.rule(dict(op='block',pid=pid,start=identity['start']))
        assert not command('probe',port=tcp6.getsockname()[1],ipv6=True)['ok']
        assert command('fork_probe',port=tcp6.getsockname()[1],ipv6=True)['result']=='blocked'
        assert command('fork_probe',port=udp6.getsockname()[1],ipv6=True,udp=True)['result']=='blocked'
        before=dict(received)
        connection=next(c for c in reversed(server_connections) if c.family==socket.AF_INET6)
        connection.sendall(b'inbound-v6')
        assert not command('receive')['ok'],'IPv6 inbound traffic escaped app block'
        assert not command('tcp',bytes=4096)['ok'],'IPv6 outbound TCP escaped app block'
        assert not command('udp',port=udp6.getsockname()[1],ipv6=True)['ok'],'IPv6 UDP escaped app block'
        assert before==received
        protection.rule(dict(op='allow',key=identity['key']))
        assert command('connect',port=tcp6.getsockname()[1],ipv6=True)['ok']
        assert command('tcp',bytes=4096)['result']==4096
        assert command('udp',port=udp6.getsockname()[1],ipv6=True)['result']==4096
        print('VITALUX_NETWORK_IPV6_OK '+json.dumps(dict(existing_tcp=True,existing_udp=True,
            new_sockets=True,new_subprocesses=True,bidirectional=True,allow=True)),flush=True)
    finally:protection.close()


def check_firefox(binary):
    """A real browser must stop fresh fetches and their responses, then recover."""
    import http.server,signal
    counts={'probe':0,'received':0}
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if path=='/':
                body=b'''<!doctype html><script>let n=0;setInterval(async()=>{try{
                let r=await fetch('/probe?n='+n++,{cache:'no-store'});let t=await r.text();
                if(t==='ok')await fetch('/received?n='+n,{cache:'no-store'});
                }catch(e){}},150);</script>Vitalux Firefox network test'''
            else:
                key=path.lstrip('/')
                if key in counts:counts[key]+=1
                body=b'ok'
            self.send_response(200);self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except OSError:pass
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    home=Path('/tmp/vitalux-firefox-home');home.mkdir(exist_ok=True)
    os.chown(home,TEST_UID,TEST_UID)
    profile=home/'profile';profile.mkdir(exist_ok=True);os.chown(profile,TEST_UID,TEST_UID)
    (profile/'user.js').write_text('''user_pref("network.captive-portal-service.enabled",false);
user_pref("network.connectivity-service.enabled",false);
user_pref("datareporting.policy.dataSubmissionEnabled",false);
user_pref("browser.shell.checkDefaultBrowser",false);
user_pref("browser.cache.disk.enable",false);
user_pref("network.trr.mode",5);
''')
    os.chown(profile/'user.js',TEST_UID,TEST_UID)
    environment=dict(os.environ,HOME=str(home),TMPDIR=str(home),MOZ_HEADLESS='1',MOZ_CRASHREPORTER_DISABLE='1')
    log=home/'browser.log';output=log.open('w')
    browser=subprocess.Popen([binary,'--headless','--no-remote','--profile',str(profile),
        f'http://127.0.0.1:{server.server_port}/'],stdout=output,stderr=output,
        env=environment,cwd=home,preexec_fn=unprivileged,start_new_session=True)
    protection=None
    def until(condition):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            assert browser.poll() is None,'Firefox exited before completing the network check'
            if condition():return
            time.sleep(.15)
        raise AssertionError('Firefox did not complete fresh requests: '+repr(counts))
    try:
        until(lambda:counts['probe']>=5 and counts['received']>=5)
        identity=application(browser.pid,TEST_UID);assert identity and identity['exe'],identity
        protection=NetworkSession(TEST_UID)
        protection.rule(dict(op='block',pid=browser.pid,start=identity['start']))
        time.sleep(.6)
        before=dict(counts);time.sleep(1.5)
        assert counts==before,('Firefox still communicated after Block',before,counts)
        protection.rule(dict(op='allow',key=identity['key']))
        until(lambda:all(counts[key]>=before[key]+3 for key in counts))
        print('VITALUX_NETWORK_FIREFOX_OK '+json.dumps(dict(real_browser=True,
            uncached_requests=True,outbound_block=True,response_receipts_block=True,
            explicit_allow=True,counts=counts)),flush=True)
    except BaseException:
        output.flush();print(log.read_text(errors='replace')[-6000:],flush=True);raise
    finally:
        if protection is not None:protection.close()
        try:os.killpg(browser.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:browser.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(browser.pid,signal.SIGKILL);browser.wait(timeout=5)
        output.close();server.shutdown();server.server_close()


session=None
try:
    assert command('connect',port=tcp.getsockname()[1])['ok']
    before=socket_snapshot(TEST_UID)
    assert not before['errors'],before['errors']
    old=sum(row['tx'] or 0 for row in before['connections'] if row.get('pid')==pid)
    assert command('tcp',bytes=262144)['result']==262144
    after=socket_snapshot(TEST_UID)
    sent=sum(row['tx'] or 0 for row in after['connections'] if row.get('pid')==pid)
    assert sent-old>=262144,(old,sent)
    session=NetworkSession(TEST_UID)
    assert command('tcp',bytes=131072)['result']==131072
    assert command('udp',port=udp.getsockname()[1])['result']==4096
    session.refresh()
    snapshot=session.snapshot()
    counters=[row for row in snapshot['counters'] if row['pid']==pid]
    assert sum(row['tx'] for row in counters)>=131072+4096,counters
    assert sum(row['rx'] for row in counters)>=131072+4096,counters
    tcp_row=next(row for row in session.base['connections'] if row.get('pid')==pid and row['protocol']=='TCP' and row['state']=='ESTABLISHED')
    session.connection_rule(dict(op='block_connection',cookie=tcp_row['cookie'],pid=pid,start=tcp_row['start']))
    assert command('probe',port=tcp.getsockname()[1])['ok'],'Connection rule blocked another socket'
    assert command('udp',port=udp.getsockname()[1])['ok'],'TCP connection rule blocked UDP'
    server_connections[0].sendall(b'inbound-probe')
    assert not command('receive')['ok'],'Inbound traffic escaped socket block'
    previous_tcp=received['tcp']
    assert not command('tcp',bytes=4096)['ok'],'Outbound traffic escaped socket block'
    assert received['tcp']==previous_tcp
    session.connection_rule(dict(op='allow_connection',cookie=tcp_row['cookie'],pid=pid,start=tcp_row['start']))
    assert command('connect',port=tcp.getsockname()[1])['ok']
    assert command('tcp',bytes=8192)['result']==8192
    session.refresh()
    udp_row=next(row for row in session.base['connections'] if row.get('pid')==pid and row['protocol']=='UDP')
    session.connection_rule(dict(op='block_connection',cookie=udp_row['cookie'],pid=pid,start=udp_row['start']))
    assert not command('udp',port=udp.getsockname()[1])['ok'],'UDP connection block failed'
    session.connection_rule(dict(op='allow_connection',cookie=udp_row['cookie'],pid=pid,start=udp_row['start']))
    assert command('udp',port=udp.getsockname()[1])['ok']
    assert command('private')['ok']
    identity=application(pid,TEST_UID)
    assert identity is not None,'A non-dumpable browser-style process disappeared from application ownership'
    try:session.rule(dict(op='block',pid=pid,start=identity['start']+1))
    except ValueError:pass
    else:raise AssertionError('Accepted a stale process identity')
    session.rule(dict(op='block',pid=pid,start=identity['start']))
    for cpu in sorted(os.sched_getaffinity(0)):
        assert command('fork_probe',port=tcp.getsockname()[1],cpu=cpu)['result']=='blocked','A newly forked app process escaped the network block before refresh'
        assert command('fork_probe',port=udp.getsockname()[1],udp=True,cpu=cpu)['result']=='blocked','A newly forked UDP process escaped the app block'
    inherited=command('fork_probe',port=tcp.getsockname()[1]);reused_pid=inherited['child']
    assert reused_pid in {pid for pid,_ in session.bpf.entries(session.blocked,8)}
    force_pid_reuse=os.environ.get('VITALUX_NETWORK_FORCE_PID_REUSE_TEST')=='1'
    if force_pid_reuse:Path('/proc/sys/kernel/ns_last_pid').write_text(str(reused_pid-1))
    replacement=subprocess.Popen([sys.executable,'-u','-c',worker+'\n# recycled PID, different application'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,preexec_fn=unprivileged)
    try:
        replacement_pid=json.loads(replacement.stdout.readline())['pid']
        if force_pid_reuse:assert replacement_pid==reused_pid,'Could not exercise PID reuse'
        assert command('probe',_process=replacement,port=tcp.getsockname()[1])['ok'],'An unrelated app inherited a stale PID block'
    finally:
        replacement.stdin.write('{"op":"quit"}\n');replacement.stdin.flush();replacement.wait(timeout=3)
    assert command('probe',_process=other,port=tcp.getsockname()[1])['ok'],'Blocking one interpreted app blocked an unrelated app'
    assert command('udp',_process=other,port=udp.getsockname()[1])['ok'],'An unrelated app lost UDP access'
    prior=dict(received)
    assert not command('probe',port=tcp.getsockname()[1])['ok'],'New socket escaped block'
    assert not command('udp',port=udp.getsockname()[1])['ok'],'Existing UDP socket escaped block'
    assert not command('tcp',bytes=4096)['ok'],'Existing TCP socket escaped block'
    assert received==prior,(received,prior)
    session.rule(dict(op='allow',key=identity['key']))
    assert command('fork_probe',port=tcp.getsockname()[1])['result']=='escaped','An inherited child block survived explicit Allow'
    assert command('probe',port=tcp.getsockname()[1])['ok']
    assert command('udp',port=udp.getsockname()[1])['ok']
    session.rule(dict(op='block',pid=pid,start=identity['start']))
    session.close();session=None
    assert command('probe',port=tcp.getsockname()[1])['ok'],'Closing BPF links did not release block'
    assert command('udp',port=udp.getsockname()[1])['ok'],'Closing BPF links did not release an existing socket'
    environment=os.environ.copy();environment['PKEXEC_UID']=str(TEST_UID)
    helper=subprocess.Popen([sys.executable,'-I',network_kernel.__file__,'--session'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=environment)
    ready=json.loads(helper.stdout.readline())
    assert ready['type']=='ready',ready
    helper.stdin.write(json.dumps(dict(op='block',pid=pid,start=identity['start']))+'\n');helper.stdin.flush()
    for _ in range(10):
        message=json.loads(helper.stdout.readline())
        if message['type']=='rules':break
    assert message['type']=='rules' and message['rules']
    assert not command('probe',port=tcp.getsockname()[1])['ok']
    helper.stdin.close();helper.wait(timeout=5)
    assert command('probe',port=tcp.getsockname()[1])['ok'],'Helper EOF retained a session block'
    check_ipv6()
    if os.environ.get('VITALUX_FIREFOX_BINARY'):check_firefox(os.environ['VITALUX_FIREFOX_BINARY'])
    print('VITALUX_NETWORK_KERNEL_OK '+json.dumps(dict(tcp_diag=True,bpf_tcp=True,bpf_udp=True,
        existing_tcp_block=True,existing_udp_block=True,new_socket_block=True,allow=True,
        automatic_cleanup=True,pid_reuse_guard=True,helper_protocol=True,helper_eof_cleanup=True,connection_tcp=True,connection_udp=True,bidirectional_socket_block=True,
        fork_tcp_block=True,fork_udp_block=True,all_cpu_fork_protection=True,unrelated_app_unaffected=True,recycled_pid_unaffected=force_pid_reuse)),flush=True)
finally:
    if session is not None:session.close()
    client.stdin.write('{"op":"quit"}\n');client.stdin.flush()
    client.wait(timeout=3)
    other.stdin.write('{"op":"quit"}\n');other.stdin.flush();other.wait(timeout=3)
