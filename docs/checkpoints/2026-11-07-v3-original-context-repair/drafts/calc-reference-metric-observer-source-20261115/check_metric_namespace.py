from pathlib import Path
import datetime, hashlib, json, os, resource, signal, subprocess, tempfile, time, types

os.umask(0o077)
Q=Path(__file__).parent
source=Q/'metric_namespace.py'
module=types.ModuleType('metric_namespace');module.__file__=str(source)
exec(compile(source.read_bytes(),str(source),'exec'),module.__dict__)
binding=Q/'python-uno-binding/root'
records=[];origin=time.monotonic();error=None

def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(15,15))
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

try:
    with tempfile.TemporaryDirectory(prefix='namespace-smoke-r2-',dir=Q) as tmp:
        root=Path(tmp);work=root/'work';ro=root/'source';work.mkdir();ro.mkdir()
        marker=ro/'marker';marker.write_text('namespace-smoke-marker\n')
        for name in ['tmp','cache','config','runtime','profile']:
            (work/name).mkdir(mode=0o700)
        probe='''from pathlib import Path
import os,json,hashlib,errno
assert not Path('/home/jericho/.codex').exists()
assert not Path('/home/jericho/jericho/Friday_rework').exists()
p=Path('''+repr(str(marker))+''');assert p.read_text()=='namespace-smoke-marker\\n'
try:p.write_text('forbidden')
except OSError as e:assert e.errno==errno.EROFS
else:raise AssertionError('source_mount_writable')
t=Path('''+repr(module.INNER_WORK+'/tmp/own-write')+''');t.write_text('temporary');t.unlink()
v=Path('/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/versionrc')
assert hashlib.sha256(v.read_bytes()).hexdigest()=='fb186292ec52c12eb15dd6f275f14291469d044c16a29199651d44a03e9fc159'
assert Path('''+repr(str(binding/'usr/lib/libreoffice/program/pyuno.so'))+''').is_file()
print(json.dumps({'home_masked':True,'exact_cache_source_readonly':True,'own_work_writable':True,'stock_component_metadata_unchanged':True,'matching_pyuno_files_visible_not_imported':True,'net_namespace_inode':os.stat('/proc/self/ns/net').st_ino,'pid_namespace_inode':os.stat('/proc/self/ns/pid').st_ino}))
'''
        commands=[('namespace_real_inputs',['/usr/bin/python3','-I','-B','-S','-c',probe]),
                  ('own_debugger_capability',['/usr/bin/gdb','-nx','-nh','--batch','-q',
                   '-ex','set startup-with-shell off','-ex','set disable-randomization off',
                   '-ex','set debuginfod enabled off','-ex','set auto-load off',
                   '-ex','run','--args','/usr/bin/true'])]
        for name,command in commands:
            argv=module.build_namespace(writable=work,readonly=[ro],binding_root=binding,command=command)
            start=time.monotonic()
            child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                   start_new_session=True,preexec_fn=limits)
            identity={'pid':child.pid,'birth_ticks':int(Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19])}
            timed_out=False
            try:
                out,err=child.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(child.pid,signal.SIGKILL)
                out,err=child.communicate(timeout=5)
            rec={'name':name,'returncode':child.returncode,**identity,'reaped':True,
                 'pid_absent':not Path('/proc',str(child.pid)).exists(),'timed_out':timed_out,
                 'elapsed_seconds':time.monotonic()-start,'stdout':out.decode(errors='replace'),
                 'stderr':err.decode(errors='replace'),'Office_UNO_or_document':False}
            records.append(rec)
            assert child.returncode==0 and rec['pid_absent'] and not timed_out,(name,rec['stderr'])
            if name=='namespace_real_inputs':
                rec['observations']=json.loads(out)
                assert rec['observations']['net_namespace_inode']!=os.stat('/proc/self/ns/net').st_ino
            assert marker.read_text()=='namespace-smoke-marker\n'
except BaseException as exc:
    error={'class':type(exc).__name__,'reason':str(exc)}
finally:
    result={'schema':'frw.Root.calc-observer-namespace-preparation-smoke-r2.v1',
            'at_moscow':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'records':records,'elapsed_seconds':time.monotonic()-origin,'error':error,
            'temporary_directory_removed':True,'UNO_import_Office_or_actualM':False,
            'scope':'Executor/dependency/mount/own-debugger capability only; no operation admission or user/application result.'}
    with (Q/'NAMESPACE-PREPARE-SMOKE-R2.json').open('x') as out:
        json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
    print(json.dumps(result))
if error:
    raise SystemExit(1)
