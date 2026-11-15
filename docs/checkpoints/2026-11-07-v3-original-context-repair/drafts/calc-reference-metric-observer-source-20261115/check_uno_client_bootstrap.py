from pathlib import Path
import datetime, hashlib, json, os, resource, signal, subprocess, tempfile, time, types

os.umask(0o077)
Q=Path(__file__).parent
source=Q/'metric_namespace.py'
namespace=types.ModuleType('metric_namespace');namespace.__file__=str(source)
exec(compile(source.read_bytes(),str(source),'exec'),namespace.__dict__)
relocation=json.loads((Q/'PYUNO-LAUNCHER-RELOCATION.json').read_bytes())
paths=relocation['required_module_search_paths']
record=None;error=None;origin=time.monotonic()
probe='''import sys,json,os
sys.path[:0]='''+repr(paths)+'''
import uno
import pyuno
context=uno.getComponentContext()
assert context is not None
property_value=uno.createUnoStruct('com.sun.star.beans.PropertyValue')
font=uno.createUnoStruct('com.sun.star.awt.FontDescriptor')
assert property_value.Name=='' and font.Name==''
constants={name:uno.getConstantByName(name) for name in ['com.sun.star.document.MacroExecMode.NEVER_EXECUTE','com.sun.star.document.UpdateDocMode.NO_UPDATE']}
print(json.dumps({'UNO_context_bootstrap':True,'uno_module':uno.__file__,'pyuno_module':pyuno.__file__,'URE_BOOTSTRAP':os.getenv('URE_BOOTSTRAP'),'FontDescriptor_created':True,'PropertyValue_created':True,'load_policy_constants':constants,'Office_spawn_or_document_load_or_metric':False}))
'''

def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(10,10))
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

try:
    with tempfile.TemporaryDirectory(prefix='uno-client-bootstrap-',dir=Q) as tmp:
        work=Path(tmp)
        for name in ['tmp','cache','config','runtime','profile']:
            (work/name).mkdir(mode=0o700)
        argv=namespace.build_namespace(writable=work,readonly=[Path(paths[0])],
                 binding_root=Q/'python-uno-binding/root',
                 command=['/usr/bin/python3','-I','-B','-S','-c',probe])
        child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                               start_new_session=True,preexec_fn=limits)
        identity={'pid':child.pid,
                  'birth_ticks':int(Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19])}
        try:
            stdout,stderr=child.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL)
            stdout,stderr=child.communicate(timeout=5)
            raise
        record={'returncode':child.returncode,**identity,'reaped':True,
                'pid_absent':not Path('/proc',str(child.pid)).exists(),
                'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace')}
        if child.returncode==0:
            record['observations']=json.loads(stdout)
        assert child.returncode==0 and record['pid_absent'],record['stderr']
except BaseException as exc:
    error={'class':type(exc).__name__,'reason':str(exc)}

result={'schema':'frw.Root.calc-isolated-UNO-client-bootstrap-qualification.v1',
        'at_moscow':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
        'elapsed_seconds':time.monotonic()-origin,'record':record,'error':error,
        'namespace_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'relocation_record_sha256':hashlib.sha256((Q/'PYUNO-LAUNCHER-RELOCATION.json').read_bytes()).hexdigest(),
        'temporary_directory_removed':True,
        'allowed_effect':'One finite own isolated Python/UNO client bootstrap and native type reflection only. No Office child, document/model/source load, font metric, conversion/render, provider/model/user/send, H/globalconfig writes.',
        'actualM':None,'runtime_grant_for_Office':False}
with (Q/'UNO-CLIENT-BOOTSTRAP-QUALIFICATION.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps(result))
if error:
    raise SystemExit(1)
