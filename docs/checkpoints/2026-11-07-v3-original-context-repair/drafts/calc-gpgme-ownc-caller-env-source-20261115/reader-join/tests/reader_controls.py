"""SOURCE-only real readers. Every created file is a synthetic purefixture.

No process/effect entry point is called. The reviewed namespace AST is loaded
in a separate in-memory module with only its WORK assignment changed before
execution; the production module, file and literal shared WORK are untouched.
"""
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import tempfile
import time
import types
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
REVIEWED=Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-REVIEWED-ROOT-20261115/candidate/outer/namespace_entry.py')
REVIEWED_SHA='398c3b883a4d0fcd31032709e71c8e15163cfeaeea4dc999262260047aa2e8bb'
ORIGINAL=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-ENV-DELTA-SOURCE-20261115')

def source(path, *, filename=None):
    module=types.ModuleType(path.stem)
    module.__file__=str(filename or path)
    exec(compile(path.read_bytes(),module.__file__,'exec'),module.__dict__)
    return module

host=source(BASE/'host/ownc_root_controller.py')
sup=source(BASE/'host/ownc_namespace_supervisor.py')
# Reuse original shape generator without copying source or invoking its tests.
shape=source(Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115/host/test_host_source.py'))

class GuardedRealReaderControls(unittest.TestCase):
    def setUp(self):
        os.umask(0o077)
        self.tmp=tempfile.TemporaryDirectory(prefix='purefixture-',dir=BASE/'tests')
        self.parent=Path(self.tmp.name);os.chmod(self.parent,0o700)
        self.work=self.parent/'synthetic-private-work';self.work.mkdir(mode=0o700)
        raw=REVIEWED.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),REVIEWED_SHA)
        tree=ast.parse(raw)
        original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='runtime_read')
        self.reader_ast=ast.dump(original,include_attributes=False)
        for n in tree.body:
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='WORK' for t in n.targets):
                n.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(self.work))],keywords=[])
        tree=ast.fix_missing_locations(tree)
        self.ns=types.ModuleType('purefixture_in_memory_namespace')
        self.ns.__file__='purefixture://reviewed-namespace-synthetic-WORK'
        exec(compile(tree,self.ns.__file__,'exec'),self.ns.__dict__)
        self.assertEqual(self.reader_ast,ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef)
            and n.name=='runtime_read'),include_attributes=False))
        self.scope=host.host_work_scope(self.work)
        self.deadline=time.monotonic()+60
        self.plan,self.ready,self.processes,self.unit,self.release=shape.PureHostSourceTests().data()
    def tearDown(self):
        self.tmp.cleanup()
    def file(self,name,value=None,*,raw=None):
        p=self.work/name
        p.write_bytes(raw if raw is not None else (json.dumps(value,sort_keys=True)+'\n').encode())
        p.chmod(0o600)
        return p
    def test_namespace_real_body_immutable_unit_and_office_release(self):
        for name,value in [('unit-release.json',self.unit),('office-release.json',self.release)]:
            p=self.file(name,value)
            self.assertEqual(sup.wait_file(self.ns,p,deadline=self.deadline),value)
    def test_namespace_real_body_mutable_trace_and_phase_original_deadline(self):
        for name in ('native-trace.json','phase.json'):
            p=self.file(name,{'nonce':self.plan['nonce'],'source':'synthetic'})
            self.assertEqual(json.loads(self.ns.runtime_read(p,deadline=self.deadline))['nonce'],self.plan['nonce'])
    def test_namespace_wrong_mode_refuses_existing_immutable_release(self):
        p=self.file('unit-release.json',self.unit)
        with self.assertRaisesRegex(self.ns.Refused,'^runtime_publication_deadline_or_path$'):
            self.ns.runtime_read(p,deadline=self.deadline)
    def test_namespace_wrong_path_scope_refuses_owned_host_path(self):
        p=self.parent/'office-ready.json';p.write_text('{}\n');p.chmod(0o600)
        with self.assertRaisesRegex(self.ns.Refused,'^exact_work_file_required$'):
            self.ns.runtime_read(p)
    def test_existing_immutable_release_expired_pre_read(self):
        p=self.file('unit-release.json',self.unit)
        with self.assertRaisesRegex(RuntimeError,'^fixture_existing_deadline_or_exit:unit-release.json$'):
            sup.wait_file(self.ns,p,deadline=time.monotonic()-1)
    def test_immutable_release_post_read_deadline_preserved(self):
        p=self.file('office-release.json',self.release)
        clock=types.SimpleNamespace(monotonic=iter([1.,3.]).__next__)
        with patch.object(sup,'time',clock),self.assertRaisesRegex(RuntimeError,
                '^fixture_existing_deadline_or_exit:office-release.json$'):
            sup.wait_file(self.ns,p,deadline=2.)
    def test_mutable_expired_deadline_refused(self):
        p=self.file('phase.json',{})
        with self.assertRaisesRegex(self.ns.Refused,'^runtime_publication_deadline$'):
            self.ns.runtime_read(p,deadline=time.monotonic()-1)
    def test_namespace_symlink_hardlink_groupwrite_refused(self):
        for kind in ('symlink','hardlink','groupwrite'):
            with self.subTest(kind=kind):
                p=self.file(kind+'.json',{})
                if kind=='symlink':
                    q=self.file('symlink-target.json',{});p.unlink();p.symlink_to(q)
                if kind=='hardlink':os.link(p,self.work/'extra-link.json')
                if kind=='groupwrite':p.chmod(0o620)
                with self.assertRaises((self.ns.Refused,OSError)):
                    self.ns.runtime_read(p)
    def test_namespace_immutable_rewritten_inode_refuses_cas(self):
        p=self.file('unit-release.json',self.unit)
        real_lstat=Path.lstat;once=[False]
        def replace_before_path_stat(path,*args,**kwargs):
            if path==p and not once[0]:
                once[0]=True
                replacement=self.file('replacement.json',self.unit);os.replace(replacement,p)
            return real_lstat(path,*args,**kwargs)
        with patch.object(Path,'lstat',replace_before_path_stat),self.assertRaisesRegex(self.ns.Refused,'^runtime_file_changed$'):
            self.ns.runtime_read(p)
        self.assertTrue(once[0])
    def test_namespace_immutable_duplicate_keys_refused_nearest_consumer(self):
        p=self.file('unit-release.json',raw=b'{"nonce":"first","nonce":"second"}\n')
        with self.assertRaisesRegex(RuntimeError,'^fixture_duplicate_json_key$'):
            sup.wait_file(self.ns,p,deadline=self.deadline)
    def test_font_real_reader_timed_and_duplicate_consumer(self):
        p=self.file('font-runtime-loaded-request.json',{'nonce':self.plan['nonce']})
        self.assertEqual(json.loads(sup.read_immutable(self.ns,p,deadline=self.deadline,font=True))['nonce'],self.plan['nonce'])
        p.write_bytes(b'{"nonce":1,"nonce":2}\n')
        with self.assertRaisesRegex(RuntimeError,'^fixture_duplicate_json_key$'):
            sup.read_immutable(self.ns,p,deadline=self.deadline,font=True)
    def test_host_real_reader_callback_ready_flow(self):
        self.file('office-ready.json',self.ready)
        ready,office,gdb=host.read_ready(self.scope,self.plan,self.processes,deadline=self.deadline)
        self.assertEqual(ready,self.ready);self.assertEqual((office,gdb),tuple(self.processes[:2]))
    def test_host_ready_nonce_mismatch_refused(self):
        self.ready['nonce']='f'*32;self.file('office-ready.json',self.ready)
        with self.assertRaisesRegex(RuntimeError,'^ownc_ready_operation_or_fixture_scope$'):
            host.read_ready(self.scope,self.plan,self.processes,deadline=self.deadline)
    def test_host_final_result_flow_only_after_actual_cgroup_empty(self):
        supervisor=dict(schema='frw.own-held-font-fixture-supervisor-result.v1',operation_id=self.plan['operation_id'],
            nonce=self.plan['nonce'],status='REFUSED_REQUIRES_ROOT_CGROUP_CLEANUP',actual_M=None)
        trace=dict(schema='frw.own-held-font-fixture-trace.v1',kind='OWN_POPEN_FIXTURE_ONLY',nonce=self.plan['nonce'],
            status='REFUSED',error='synthetic_expected_guard',actual_M=None)
        self.file('held-fixture-supervisor-result.json',supervisor);self.file('native-trace.json',trace)
        monitored=dict(status='REFUSED_OWNED_CGROUP_EMPTY',invocation_id='c'*32,cgroup_path='/owned',
            last_snapshot=({'ActiveState':'failed'},dict(populated=0,pids=[])),retirement_snapshot=None)
        self.assertEqual(host.read_terminal(self.scope,self.plan,monitored,deadline=self.deadline),
            dict(supervisor=supervisor,trace=trace))
        for mode in ('unknown','populated','pid','nonce'):
            m=copy.deepcopy(monitored)
            if mode=='unknown':m['status']='OWNED_CLEANUP_UNKNOWN'
            if mode=='populated':m['last_snapshot'][1]['populated']=1
            if mode=='pid':m['last_snapshot'][1]['pids']=[123]
            if mode=='nonce':
                trace['nonce']='e'*32;self.file('native-trace.json',trace)
            with self.subTest(mode=mode),self.assertRaises(RuntimeError):
                host.read_terminal(self.scope,self.plan,m,deadline=self.deadline)
    def test_host_expired_pre_and_post_read_deadline(self):
        self.file('office-ready.json',self.ready)
        with self.assertRaisesRegex(RuntimeError,'^ownc_host_original_deadline$'):
            host.host_record(self.scope,'office-ready.json',deadline=time.monotonic()-1)
        clock=types.SimpleNamespace(monotonic=iter([1.,3.]).__next__)
        with patch.object(host,'time',clock),self.assertRaisesRegex(RuntimeError,'^ownc_host_original_deadline$'):
            host.host_record(self.scope,'office-ready.json',deadline=2.)
    def test_host_expected_role_filenames_only(self):
        for name in ('unit-release.json','../office-ready.json','phase.json','output/office-ready.json'):
            with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'^ownc_host_record_role$'):
                host.host_record(self.scope,name,deadline=self.deadline)
    def test_host_symlink_hardlink_groupwrite_duplicate_bound_refused(self):
        for kind in ('symlink','hardlink','groupwrite','duplicate','bound'):
            with self.subTest(kind=kind):
                p=self.file('office-ready.json',self.ready)
                if kind=='symlink':
                    q=self.file('other.json',self.ready);p.unlink();p.symlink_to(q)
                if kind=='hardlink':os.link(p,self.work/'hardlink.json')
                if kind=='groupwrite':p.chmod(0o620)
                if kind=='duplicate':p.write_bytes(b'{"nonce":1,"nonce":2}\n')
                if kind=='bound':p.write_bytes(b' '*(1048576+1))
                with self.assertRaises((RuntimeError,OSError)):
                    host.host_record(self.scope,'office-ready.json',deadline=self.deadline)
                p.unlink()
    def test_host_rewritten_inode_during_actual_read_refused(self):
        p=self.file('office-ready.json',self.ready);real_read=os.read;once=[False]
        def read_and_replace(fd,size):
            raw=real_read(fd,size)
            if not once[0]:
                once[0]=True;q=self.file('replacement.json',self.ready);os.replace(q,p)
            return raw
        with patch.object(os,'read',read_and_replace),self.assertRaisesRegex(RuntimeError,'^ownc_host_record_changed$'):
            host.host_record(self.scope,'office-ready.json',deadline=self.deadline)
        self.assertTrue(once[0])
    def test_host_replaced_work_directory_refused(self):
        self.file('office-ready.json',self.ready)
        self.work.rename(self.parent/'retired-work');self.work.mkdir(mode=0o700)
        with self.assertRaisesRegex(RuntimeError,'^ownc_host_work_changed$'):
            host.host_record(self.scope,'office-ready.json',deadline=self.deadline)
    def test_current_four_real_metadata_namespace_validator_joins(self):
        for variant in ('worker_cached','extra_fork','forbidden_gpg_home','wrong_gpgconf_name'):
            with self.subTest(variant=variant):
                plan=json.loads((BASE/'inputs'/variant/'STATIC-PLAN.json').read_bytes())
                prepared=host.inspect_plan(plan)
                self.assertEqual(prepared['supervisor_ref'],plan['source_refs']['supervisor'])
                self.assertEqual(prepared['gdb_driver_ref']['sha256'],'a97cf8496f84416bce34e54b1af1dd6e4feda5cd8a7717dda392bdc438bf9541')
                self.assertEqual(plan['budgets'],dict(wall_seconds=240,cpu_seconds=120,memory_bytes=2147483648,
                    cleanup_seconds=10,startup_seconds=60,tasks_max=64))
    def test_preserved_infra_environment_launcher_and_changed_reader_call_inventory(self):
        old=ast.parse((ORIGINAL/'host/ownc_root_controller.py').read_bytes())
        new=ast.parse((BASE/'host/ownc_root_controller.py').read_bytes())
        named=lambda tree,name:ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef)
            and n.name==name),include_attributes=False)
        for name in ('namespace_argv','validate_budget','outside_cpu','outside_memory','map_ready','observe_stopped_target'):
            self.assertEqual(named(old,name),named(new,name))
        tree=ast.parse((BASE/'host/ownc_namespace_supervisor.py').read_bytes())
        runtime=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
            and n.func.attr=='runtime_read']
        self.assertGreater(len(runtime),5)
        immutable=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='read_immutable')
        immutable_calls={id(n) for n in ast.walk(immutable) if isinstance(n,ast.Call)}
        for call in runtime:
            if id(call) in immutable_calls:
                self.assertFalse(call.keywords)
            else:self.assertEqual([k.arg for k in call.keywords],['deadline'])
        old_sup=ast.parse((ORIGINAL/'host/ownc_namespace_supervisor.py').read_bytes())
        for name in ('environment_diagnostic','validate_supervisor_environment','native_refusal_trace','validate_release'):
            self.assertEqual(named(old_sup,name),named(tree,name))
        self.assertNotIn('ns.runtime_read',(BASE/'host/ownc_root_controller.py').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
