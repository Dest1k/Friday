import os,sys,subprocess,json,hashlib,datetime,time,shutil
from pathlib import Path
os.umask(0o077);b=Path(__file__).resolve().parent;s=b/'pure-stand';s.mkdir(mode=0o700)
for root,paths in [(b/'candidate',['agent/message_sanitization.py','agent/message_metadata.py']), (b/'dependencies',['agent/__init__.py','agent/jiter_preload.py','agent/conversation_compression_archive.py','agent/tool_dispatch_helpers.py','agent/compression_marker.py','agent/tool_result_classification.py','agent/lazy_forward.py','tools/__init__.py','tools/threat_patterns.py'])]:
 for name in paths:
  dst=s/name;dst.parent.mkdir(exist_ok=True,parents=True,mode=0o700);dst.write_bytes((root/name).read_bytes())
r=b/'checks/r1';r.mkdir(mode=0o700)
t=time.monotonic();p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(b/'pure_controls.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=b,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
try:out,err=p.communicate(timeout=90)
except subprocess.TimeoutExpired:
 os.killpg(p.pid,9);out,err=p.communicate();(r/'TIMEOUT').write_text('Original90wall consumed; no automatic retry\n')
(r/'stdout.json').write_bytes(out);(r/'stderr.txt').write_bytes(err)
(r/'RESULT.json').write_text(json.dumps({'started_moscow':datetime.datetime.now().astimezone().isoformat(),'pid':p.pid,'returncode':p.returncode,'waited_reaped':True,'wall_seconds':time.monotonic()-t,'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_bytes':len(err),'controls_source_sha256':hashlib.sha256((b/'pure_controls.py').read_bytes()).hexdigest(),'source_only':True},indent=2)+'\n')
print(json.dumps({'returncode':p.returncode,'stderr':err.decode()[:2500],'stdout_tail':out.decode()[-1300:]}))
