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
def tcp_server():
    while True:
        connection,_=tcp.accept()
        threading.Thread(target=tcp_connection,args=(connection,),daemon=True).start()
def udp_server():
    while True:
        data,address=udp.recvfrom(65536)
        received['udp']+=len(data)
        udp.sendto(data,address)
threading.Thread(target=tcp_server,daemon=True).start()
threading.Thread(target=udp_server,daemon=True).start()

worker=r'''
import json,socket,sys,os
tcp=None;udp=None
print(json.dumps({'pid':os.getpid()}),flush=True)
for line in sys.stdin:
 req=json.loads(line)
 try:
  op=req['op']
  if op=='connect':
   if tcp is not None:tcp.close()
   tcp=socket.socket();tcp.settimeout(.7);tcp.connect(('127.0.0.1',req['port']));result='connected'
  elif op=='tcp':
   size=req.get('bytes',65536);tcp.sendall(b'x'*size);n=0
   while n<size:n+=len(tcp.recv(65536))
   result=n
  elif op=='udp':
   if udp is None:
    udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);udp.settimeout(.5)
   udp.sendto(b'u'*4096,('127.0.0.1',req['port']));result=len(udp.recv(65536))
  elif op=='receive':result=len(tcp.recv(65536))
  elif op=='probe':
   s=socket.socket();s.settimeout(.5);s.connect(('127.0.0.1',req['port']));s.close();result='allowed'
  elif op=='quit':break
  print(json.dumps({'ok':True,'result':result}),flush=True)
 except OSError as exc:print(json.dumps({'ok':False,'error':str(exc)}),flush=True)
'''
def unprivileged():os.setgid(TEST_UID);os.setuid(TEST_UID)
client=subprocess.Popen([sys.executable,'-u','-c',worker],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,preexec_fn=unprivileged)
identity=json.loads(client.stdout.readline());pid=identity['pid']
def command(op,**values):
    client.stdin.write(json.dumps(dict(op=op,**values))+'\n');client.stdin.flush()
    return json.loads(client.stdout.readline())

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
    identity=application(pid,TEST_UID)
    try:session.rule(dict(op='block',pid=pid,start=identity['start']+1))
    except ValueError:pass
    else:raise AssertionError('Accepted a stale process identity')
    session.rule(dict(op='block',pid=pid,start=identity['start']))
    prior=dict(received)
    assert not command('probe',port=tcp.getsockname()[1])['ok'],'New socket escaped block'
    assert not command('udp',port=udp.getsockname()[1])['ok'],'Existing UDP socket escaped block'
    assert not command('tcp',bytes=4096)['ok'],'Existing TCP socket escaped block'
    assert received==prior,(received,prior)
    session.rule(dict(op='allow',key=identity['key']))
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
    print('VITALUX_NETWORK_KERNEL_OK '+json.dumps(dict(tcp_diag=True,bpf_tcp=True,bpf_udp=True,
        existing_tcp_block=True,existing_udp_block=True,new_socket_block=True,allow=True,
        automatic_cleanup=True,pid_reuse_guard=True,helper_protocol=True,helper_eof_cleanup=True,connection_tcp=True,connection_udp=True,bidirectional_socket_block=True)),flush=True)
finally:
    if session is not None:session.close()
    client.stdin.write('{"op":"quit"}\n');client.stdin.flush()
    client.wait(timeout=3)
