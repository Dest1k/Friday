"""Pure simulated memory/adapter controls; no inferior or helper execution."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
DEPS = BASE / 'candidate/outer/deps'
spec = importlib.util.spec_from_file_location('runtime_env_adapter', DEPS / 'paper_helper_gdb.py')
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
MANIFEST = json.loads((DEPS / 'PAPER-HELPER-OFFICE-MANIFEST.json').read_text())
CRITICAL = {k.encode(): v.encode() for k, v in MANIFEST['environment'].items()}
spec = importlib.util.spec_from_file_location('runtime_env_namespace', BASE / 'candidate/outer/namespace_entry.py')
N = importlib.util.module_from_spec(spec); spec.loader.exec_module(N)


def wire(env):
    return b'\0'.join(k + b'=' + v for k, v in env.items()) + b'\0'


class MemoryFixture:
    """After-startup heap vector plus unchanged exec-time /proc environment."""
    base = 0x10000000
    heap = 0x40000000
    pid = 12
    def __init__(self, env=None):
        self.initial = dict(CRITICAL)
        self.effective = dict(self.initial, **{}) if env is None else dict(env)
        if env is None:
            self.effective[b'FRW_OWN_ENV_AFTER_STARTUP'] = b'OWN_HARMLESS_RUNTIME_VALUE'
        self.mem = {}
        self.reads = 0
        self.thread_stopped = True
        self.birth_calls = 0
        self.changed_birth = False
        self.a = A.Adapter.__new__(A.Adapter)
        a = self.a
        a.m = copy.deepcopy(MANIFEST)
        a.n = {'STATE': {'process': {'pid': self.pid, 'start_ticks': 100, 'gdb_pid': 2, 'inferior': 1}, 'error': None}, 'save': lambda: None}
        a.b = {'runtime': {'operation_id': 'OWN_MOCK', 'nonce': '0' * 32,
            'source_sha256': MANIFEST['source_sha256'], 'manifest_ref': {'path': str(DEPS/'PAPER-HELPER-OFFICE-MANIFEST.json'),
            'sha256': hashlib.sha256((DEPS/'PAPER-HELPER-OFFICE-MANIFEST.json').read_bytes()).hexdigest()}}}
        inf = types.SimpleNamespace(num=1, pid=self.pid,
            threads=lambda: [types.SimpleNamespace(is_valid=lambda: True, is_stopped=lambda: self.thread_stopped)])
        a.g = types.SimpleNamespace(selected_inferior=lambda: inf)
        a.original_check = self.birth
        a.pin = lambda image: None
        a.base = lambda pid, path: self.base
        a.memory = self.read
        a.bounded = self.bounded
        a.original_env = None
        a.original_stdin = a.original_stderr = a.pipe = None
        a.environment_proof = []
        self.maps = '\n'.join([
            f'{self.base:x}-{self.base+0x20e000:x} r-xp 00000000 00:01 1 {MANIFEST["images"]["libc"]["path"]}',
            f'{self.base+0x20e000:x}-{self.base+0x212000:x} r--p 0020e000 00:01 1 {MANIFEST["images"]["libc"]["path"]}',
            f'{self.base+0x212000:x}-{self.base+0x214000:x} rw-p 00212000 00:01 1 {MANIFEST["images"]["libc"]["path"]}',
            f'{self.base+0x214000:x}-{self.base+0x221000:x} rw-p 00000000 00:00 0',
            f'{self.heap:x}-{self.heap+0x50000:x} rw-p 00000000 00:00 0 [heap]',
        ]).encode()
        for name in ('load', 'dereference', 'call'):
            self.put(self.base + A.ENV_SOURCE[name+'_offset'], bytes.fromhex(A.ENV_SOURCE[name+'_bytes']))
        self.putint(self.base + A.ENV_SOURCE['got_offset'], self.base + A.ENV_SOURCE['storage_offset'])
        self.vector = self.heap + 0x100
        self.putint(self.base + A.ENV_SOURCE['storage_offset'], self.vector)
        self.fill_vector(self.effective)

    def fill_vector(self, env):
        location = self.heap + 0x2000
        for index, (key, value) in enumerate(env.items()):
            self.putint(self.vector + index * 8, location)
            item = key + b'=' + value + b'\0'
            self.put(location, item)
            location += len(item) + 8
        self.putint(self.vector + len(env) * 8, 0)

    def birth(self):
        self.birth_calls += 1
        return {'pid': self.pid, 'start_ticks': 101 if self.changed_birth and self.birth_calls > 1 else 100}

    def put(self, addr, raw):
        for i, byte in enumerate(raw): self.mem[addr+i] = byte

    def putint(self, addr, number): self.put(addr, number.to_bytes(8, 'little'))

    def read(self, addr, count):
        self.reads += 1
        try: return bytes(self.mem[addr+i] for i in range(count))
        except KeyError: raise RuntimeError('OWN_UNMAPPED_MOCK_READ')

    def bounded(self, path, limit):
        if str(path).endswith('/maps'): return self.maps
        if str(path).endswith('/environ'): return wire(self.initial)
        raise AssertionError('unexpected pure mock read')


class GetterTests(unittest.TestCase):
    def test_runtime_heap_vector_differs_from_proc_and_matches_child(self):
        f = MemoryFixture()
        self.assertNotIn(b'FRW_OWN_ENV_AFTER_STARTUP', f.a.parse_environment(wire(f.initial)))
        self.assertEqual(f.a.current_environment(12), f.effective)
        with patch.object(A.os, 'readlink', return_value='/tmp/friday-metric-work'), patch.object(A.os.path, 'lexists', return_value=False):
            f.a.environment(12, initial=True, expected_pointer=f.vector)
            f.a.bounded = lambda path, limit: wire(f.effective)
            f.a.environment(15)
            f.effective[b'PWD'] = b'/tmp/friday-metric-work'
            f.a.environment(16)
            f.effective[b'UNREVIEWED_NEW_CHILD_KEY'] = b'OWN'
            with self.assertRaisesRegex(RuntimeError, '^helper_inherited_environment_changed$'): f.a.environment(16)

    def test_proc_based_old_algorithm_would_refuse_same_child(self):
        f = MemoryFixture()
        self.assertNotEqual(f.initial, f.effective)
        self.assertEqual(f.a.current_environment(12, expected_pointer=f.vector), f.effective)

    def test_wrong_pid_or_inferior_refused_before_memory(self):
        f = MemoryFixture()
        for pid, number in ((13, 1), (12, 2)):
            f.a.g.selected_inferior().num = number
            with self.assertRaisesRegex(RuntimeError, 'original_only'): f.a.current_environment(pid)
        self.assertEqual(f.reads, 0)

    def test_running_thread_refused_before_memory(self):
        f = MemoryFixture(); f.thread_stopped = False
        with self.assertRaisesRegex(RuntimeError, 'all_stop'): f.a.current_environment(12)
        self.assertEqual(f.reads, 0)

    def test_source_pin_instruction_and_got_interposition_controls(self):
        f = MemoryFixture(); f.a.m['images']['libc']['sha256'] = '0'*64
        with self.assertRaisesRegex(RuntimeError, 'source_pin'): f.a.current_environment(12)
        for prefix in ('load', 'dereference', 'call'):
            f = MemoryFixture(); f.put(f.base+A.ENV_SOURCE[prefix+'_offset'], b'\x90')
            with self.subTest(prefix=prefix), self.assertRaisesRegex(RuntimeError, 'instruction'): f.a.current_environment(12)
        f = MemoryFixture(); f.putint(f.base+A.ENV_SOURCE['got_offset'], f.heap)
        with self.assertRaisesRegex(RuntimeError, 'symbol_interposition'): f.a.current_environment(12)

    def test_libc_bss_continuation_cannot_be_arbitrary_heap(self):
        f = MemoryFixture(); f.maps = f.maps.replace(b'rw-p 00000000 00:00 0\n', b'rw-p 00000000 00:00 0 [heap]\n')
        with self.assertRaisesRegex(RuntimeError, 'libc_zero_fill'): f.a.current_environment(12)

    def test_wrong_spawn_pointer_and_unreadable_pointer(self):
        f = MemoryFixture()
        with self.assertRaisesRegex(RuntimeError, 'spawn_pointer'): f.a.current_environment(12, expected_pointer=f.vector+8)
        f.putint(f.base+A.ENV_SOURCE['storage_offset'], 0x50000000)
        with self.assertRaisesRegex(RuntimeError, 'readable_mapping'): f.a.current_environment(12)

    def test_double_snapshot_and_stale_birth_controls(self):
        f = MemoryFixture(); original_read = f.a.memory; calls = 0
        def unstable(addr, count):
            nonlocal calls
            if addr == f.base+A.ENV_SOURCE['storage_offset']:
                calls += 1
                if calls == 2: return (f.vector+8).to_bytes(8, 'little')
            return original_read(addr,count)
        f.a.memory = unstable
        with self.assertRaisesRegex(RuntimeError, 'snapshot_changed'): f.a.current_environment(12)
        f = MemoryFixture(); f.changed_birth = True
        with self.assertRaisesRegex(RuntimeError, 'snapshot_changed'): f.a.current_environment(12)

    def test_duplicate_missing_nul_vector_and_string_bounds(self):
        f = MemoryFixture()
        with self.assertRaisesRegex(RuntimeError, 'duplicates'): f.a.parse_environment(b'A=1\0A=2\0')
        with self.assertRaisesRegex(RuntimeError, 'termination'): f.a.parse_environment(b'A=1')
        with self.assertRaisesRegex(RuntimeError, 'encoding'): f.a.parse_environment(b'=1\0')
        for i in range(513): f.putint(f.vector+i*8,f.heap+0x2000)
        with self.assertRaisesRegex(RuntimeError, 'vector_bound'): f.a.current_environment(12)
        f = MemoryFixture(); f.put(f.heap+0x2000,b'X'*32769)
        with self.assertRaisesRegex(RuntimeError, 'item_bound'): f.a.current_environment(12)

    def test_critical_override_and_font_projection_controls(self):
        for key,value,reason in ((b'PATH',b'/OWN','environment_changed'),(b'LC_ALL',b'OWN','environment_changed'),
                (b'PAPERSIZE',b'OWN','environment_override'),(b'LC_PAPER',b'OWN','environment_override'),
                (b'LD_PRELOAD',b'OWN','environment_override'),(b'LD_AUDIT',b'OWN','environment_override'),
                (b'ENV',b'OWN','environment_override'),(b'BASH_ENV',b'OWN','environment_override'),
                (b'FC_LANG',b'OWN','font_runtime_environment_changed')):
            f = MemoryFixture(dict(CRITICAL, **{})); f.effective[key]=value; f.fill_vector(f.effective)
            with self.subTest(key=key), patch.object(A.os,'readlink',return_value='/tmp/friday-metric-work'), \
                    patch.object(A.os.path,'lexists',return_value=False), self.assertRaisesRegex(RuntimeError,reason):
                f.a.environment(12, initial=True)
        f = MemoryFixture()
        with patch.object(A.os,'readlink',return_value='/tmp/friday-metric-work'), patch.object(A.os.path,'lexists',return_value=True), \
                self.assertRaisesRegex(RuntimeError,'paper_config_present'): f.a.environment(12,initial=True)

    def test_spawn_callsite_order_and_r9_binding(self):
        f = MemoryFixture(); a = f.a; actions=[]
        a.window=lambda: None; a.tid=lambda: [12,12,0]; a.c=types.SimpleNamespace(thread=[12,12,0],e={'state':'ARMED'})
        a.spawn_env_verified=False
        a.g.newest_frame=lambda: types.SimpleNamespace(pc=lambda:f.base+A.ENV_SOURCE['call_offset'])
        a.offset=lambda frame,image:A.ENV_SOURCE['call_offset']; a.register=lambda name:f.vector
        a.custody_boundary=lambda pid,stage,role,**kw: actions.append((pid,stage,role,kw))
        a.spawn_environment(); self.assertTrue(a.spawn_env_verified)
        self.assertEqual(actions,[(12,'spawn','parent',{'initial':True,'expected_pointer':f.vector})])
        with self.assertRaisesRegex(RuntimeError,'order'): a.spawn_environment()
        a.spawn_env_verified=False; a.offset=lambda frame,image:1
        with self.assertRaisesRegex(RuntimeError,'callsite'): a.spawn_environment()

    def test_install_preserves_persistent_popen_and_adds_one_shot_spawn(self):
        f=MemoryFixture(); a=f.a; calls=[]
        a.installed=False; a.ensure=lambda: None
        a.breakpoint=lambda address,fn,**kw: calls.append((address,fn.__name__,kw))
        a.install()
        self.assertTrue(a.installed)
        self.assertIn((f.base+MANIFEST['images']['libc']['entry'],'popen',{'one_shot':False}),calls)
        self.assertIn((f.base+A.ENV_SOURCE['call_offset'],'spawn_environment',{}),calls)
        count=len(calls); a.install(); self.assertEqual(len(calls),count)

    def test_birth_without_exact_spawn_snapshot_refuses_before_child_discovery(self):
        f=MemoryFixture(); a=f.a
        a.window=lambda: None; a.proc=lambda pid:{'pid':12,'start_ticks':100}
        a.c=types.SimpleNamespace(e={'children':[]},thread=[12,12,0]); a.tid=lambda:[12,12,0]
        a.spawn_env_verified=False
        with self.assertRaisesRegex(RuntimeError,'^helper_spawn_environment_unbound$'): a.birth()


class DiagnosticTests(unittest.TestCase):
    def test_consolidated_refusal_retains_first_and_collects_fds_without_resuming(self):
        f=MemoryFixture(); a=f.a; calls=[]
        a.environment=lambda *args,**kw: (_ for _ in ()).throw(RuntimeError('helper_environment_override'))
        a.fds=lambda *args,**kw: calls.append('validation_must_not_run')
        a.boundary_metadata=lambda pid,stage,role,**kw: calls.append((pid,stage,role,kw))
        with self.assertRaisesRegex(RuntimeError,'^helper_environment_override$'): a.custody_boundary(15,'dash_exec','dash')
        self.assertEqual(calls,[(15,'dash_exec','dash',{'refusal':'helper_environment_override'})])
        a.boundary_metadata=lambda *args,**kw: (_ for _ in ()).throw(OSError('OWN diagnostic write refusal'))
        with self.assertRaisesRegex(RuntimeError,'^helper_environment_override$'): a.custody_boundary(15,'dash_exec','dash')

    def test_sanitized_sidecar_current_and_expected_hashes_fd_metadata_and_limits(self):
        f=MemoryFixture(); a=f.a
        a.audit_actual_env=dict(f.effective); a.audit_expected_env=dict(f.initial); a.audit_font_initial=dict(f.initial)
        a.audit_actual_env[b'NOT_A_VALID/SECRET_KEY']=b'PRIVATE_VALUE_MUST_NEVER_APPEAR'
        a.fd=lambda pid,n:dict(dev=1,ino=100+n,type=stat.S_IFCHR,rdev=259,access=n%3,cloexec=False)
        real_path=Path
        with tempfile.TemporaryDirectory(dir=BASE) as d:
            root=Path(d); (root/'proc/12/fd').mkdir(parents=True)
            for n in range(12): (root/f'proc/12/fd/{n}').touch()
            def mapped(path):
                if str(path)=='/proc': return root/'proc'
                if str(path).startswith('/tmp/friday-metric-work/'): return root/real_path(path).name
                return real_path(path)
            with patch.object(A,'Path',mapped):
                a.boundary_metadata(12,'popen','parent')
                a.boundary_metadata(12,'spawn','parent',refusal='helper_inherited_environment_changed')
                out=root/'paper-helper-boundary.json'; raw=out.read_bytes(); value=json.loads(raw)
                self.assertEqual(out.stat().st_mode&0o777,0o600)
                self.assertNotIn(b'PRIVATE_VALUE_MUST_NEVER_APPEAR',raw)
                self.assertNotIn(b'OWN_HARMLESS_RUNTIME_VALUE',raw)
                self.assertNotIn(b'NOT_A_VALID/SECRET_KEY',raw)
                self.assertNotIn(MANIFEST['images']['libc']['path'].encode(),raw)
                s=value['stages'][-1]
                self.assertEqual(s['fd_count'],12); self.assertTrue(s['fds_truncated']); self.assertEqual(len(s['fds']),8)
                self.assertEqual(s['environment_key_count'],7)
                row=next(r for r in s['environment'] if r.get('key')=='FRW_OWN_ENV_AFTER_STARTUP')
                self.assertEqual(row['actual_value_sha256'],hashlib.sha256(b'OWN_HARMLESS_RUNTIME_VALUE').hexdigest())
                self.assertIsNone(row['expected_value_sha256'])
                self.assertEqual(s['font_runtime_equals_initial'],True)
                self.assertIn('NOT_FONT_CAS_POSTCONDITION',s['font_scope'])
                a.environment_proof=[{}]*8
                with self.assertRaisesRegex(RuntimeError,'stage_bound'): a.boundary_metadata(12,'spawn','parent')

    def test_parent_custody_does_not_replace_changed_originals(self):
        f=MemoryFixture(); a=f.a
        a.original_stdin=dict(dev=1,ino=2,type=stat.S_IFCHR,rdev=259,access=os.O_RDONLY)
        a.original_stderr=dict(dev=1,ino=3,type=stat.S_IFREG,rdev=0,access=os.O_WRONLY)
        old=copy.deepcopy(a.original_stdin)
        a.fd=lambda pid,n: dict(a.original_stdin,ino=999) if n==0 else dict(a.original_stderr)
        with self.assertRaisesRegex(RuntimeError,'parent_stdin_changed'): a.parent_fds(12)
        self.assertEqual(a.original_stdin,old)

    def test_key_diagnostic_limit_and_total_output_refusal(self):
        f=MemoryFixture(); a=f.a
        a.audit_actual_env={('OWN_KEY_%02d'%i).encode():b'OWN_SECRET_VALUE' for i in range(70)}
        a.audit_expected_env={}; a.audit_font_initial=None
        real_path=Path
        with tempfile.TemporaryDirectory(dir=BASE) as d:
            root=Path(d)
            def mapped(path):
                if str(path)=='/proc': return root/'no_proc'
                if str(path).startswith('/tmp/friday-metric-work/'): return root/real_path(path).name
                return real_path(path)
            with patch.object(A,'Path',mapped):
                a.boundary_metadata(12,'spawn','parent',refusal='helper_environment_changed')
                value=json.loads((root/'paper-helper-boundary.json').read_text())['stages'][0]
                self.assertEqual(len(value['environment']),49); self.assertTrue(value['environment_keys_truncated'])
                self.assertEqual(value['environment_key_count'],70)
                a.environment_proof=[{'bounded_control':'X'*32768}]
                with self.assertRaisesRegex(RuntimeError,'output_bound'): a.boundary_metadata(12,'spawn','parent')


class StaticBindingTests(unittest.TestCase):
    def test_exact_installed_elf_instruction_relocation_symbol_and_zero_fill(self):
        image=MANIFEST['images']['libc']; raw=Path(image['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),A.ENV_SOURCE['libc_sha256'])
        h=struct.unpack_from('<16sHHIQQQIHHHHHH',raw); loads=[]
        for i in range(h[10]):
            t,flags,off,va,_,size,mem,_=struct.unpack_from('<IIQQQQQQ',raw,h[5]+i*h[9])
            if t==1: loads.append((off,va,size,mem,flags))
        for name in ('load','dereference','call'):
            va=A.ENV_SOURCE[name+'_offset']; data=bytes.fromhex(A.ENV_SOURCE[name+'_bytes'])
            entries=[r for r in loads if r[1]<=va and va+len(data)<=r[1]+r[2]]
            self.assertEqual(len(entries),1); r=entries[0]
            self.assertEqual(raw[r[0]+va-r[1]:r[0]+va-r[1]+len(data)],data)
        displacement=int.from_bytes(bytes.fromhex(A.ENV_SOURCE['load_bytes'])[3:7],'little',signed=True)
        self.assertEqual(A.ENV_SOURCE['load_offset']+7+displacement,A.ENV_SOURCE['got_offset'])
        data=[r for r in loads if r[1]+r[2]<=A.ENV_SOURCE['storage_offset']<r[1]+r[3]]
        self.assertEqual(len(data),1); r=data[0]
        self.assertEqual((r[1]+r[2]+4095)&~4095,A.ENV_SOURCE['zero_fill_start'])
        self.assertEqual(r[1]+r[3],A.ENV_SOURCE['data_memory_end'])
        symbols=subprocess.check_output(['/usr/bin/readelf','-Ws',image['path']],text=True)
        self.assertIn('0000000000219de8     8 OBJECT  GLOBAL DEFAULT   32 __environ@@GLIBC_2.2.5',symbols)
        reloc=subprocess.check_output(['/usr/bin/readelf','-Wr',image['path']],text=True)
        self.assertIn('0000000000211fb0  00000b3500000006 R_X86_64_GLOB_DAT      0000000000219de8 __environ@@GLIBC_2.2.5 + 0',reloc)

    def test_font_keys_equal_existing_consumer_without_broad_scope_change(self):
        tree=__import__('ast').parse((BASE/'candidate/outer/font_view/font_view.py').read_text())
        keys=next(__import__('ast').literal_eval(n.value) for n in tree.body if isinstance(n,__import__('ast').Assign)
            and any(getattr(t,'id',None)=='ENV_KEYS' for t in n.targets))
        self.assertEqual(tuple(k.decode() for k in A.FONT_ENV_KEYS),keys)
        for rel in ('paper_helper_policy.py','native_return_observer.py','check_native_trace.py','PAPER-HELPER-OFFICE-MANIFEST.json'):
            self.assertEqual((DEPS/rel).read_bytes(),(BASE/'before/outer/deps'/rel).read_bytes())


class NamespaceConsumerTests(unittest.TestCase):
    def make_metadata(self, root):
        f=MemoryFixture(); a=f.a
        a.audit_actual_env=dict(f.effective); a.audit_expected_env=dict(CRITICAL); a.audit_font_initial=dict(CRITICAL)
        real_path=Path
        def mapped(path):
            if str(path)=='/proc': return root/'absent_proc'
            if str(path).startswith('/tmp/friday-metric-work/'): return root/real_path(path).name
            return real_path(path)
        with patch.object(A,'Path',mapped):
            a.boundary_metadata(12,'popen','parent')
            a.boundary_metadata(12,'spawn','parent')
        return a,root/'paper-helper-boundary.json'

    def test_exact_new_sidecar_inventory_schema_context_and_hash(self):
        with tempfile.TemporaryDirectory(dir=BASE) as d:
            root=Path(d); a,path=self.make_metadata(root)
            with patch.object(N,'WORK',root):
                result=N.output_inventory(helper_runtime=a.b['runtime'],original=a.n['STATE']['process'])
                self.assertEqual(len(result),1)
                self.assertEqual(result[0]['path'],'paper-helper-boundary.json')
                self.assertEqual(result[0]['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
                with self.assertRaisesRegex(N.Refused,'unexpected_writable_output'): N.output_inventory()
                wrong=dict(a.b['runtime'],nonce='f'*32)
                with self.assertRaisesRegex(N.Refused,'binding'): N.output_inventory(helper_runtime=wrong,original=a.n['STATE']['process'])
                path.unlink()
                with self.assertRaisesRegex(N.Refused,'missing'): N.output_inventory(helper_runtime=a.b['runtime'],original=a.n['STATE']['process'])

    def test_metadata_raw_values_bounds_and_birth_forgery_refused(self):
        with tempfile.TemporaryDirectory(dir=BASE) as d:
            a,path=self.make_metadata(Path(d)); raw=path.read_bytes(); value=json.loads(raw)
            for mutate,reason in (
                (lambda v:v['stages'][0].update(raw_value='OWN_PRIVATE'), 'stage_schema'),
                (lambda v:v['stages'][0]['font_environment'][0].update(runtime_value_sha256='OWN_PRIVATE'), 'value_hash'),
                (lambda v:v['stages'][0].update(pid=13), 'parent_identity'),
                (lambda v:v['stages'][0].update(environment_source_class='ARBITRARY_RAW_MAPPING'), 'mapping_class'),
                (lambda v:v.update(stages=[v['stages'][0]]*9), 'stage_bound')):
                changed=copy.deepcopy(value); mutate(changed)
                with self.subTest(reason=reason),self.assertRaisesRegex(N.Refused,reason):
                    N.validate_helper_boundary_metadata(json.dumps(changed).encode(),a.b['runtime'],a.n['STATE']['process'])
            with self.assertRaisesRegex(N.Refused,'metadata_bound'):
                N.validate_helper_boundary_metadata(b'X'*32769,a.b['runtime'],a.n['STATE']['process'])

    def test_metadata_link_rights_unknown_output_guards_preserved(self):
        with tempfile.TemporaryDirectory(dir=BASE) as d:
            root=Path(d); a,path=self.make_metadata(root)
            with patch.object(N,'WORK',root):
                path.chmod(0o640)
                with self.assertRaisesRegex(N.Refused,'private_output_rights'): N.output_inventory(helper_runtime=a.b['runtime'],original=a.n['STATE']['process'])
                path.chmod(0o600); link=root.parent/(root.name+'-owned_hardlink'); os.link(path,link)
                try:
                    with self.assertRaisesRegex(N.Refused,'rights_bound'): N.output_inventory(helper_runtime=a.b['runtime'],original=a.n['STATE']['process'])
                finally:
                    link.unlink()
                (root/'UNKNOWN_OUTPUT').touch(mode=0o600)
                with self.assertRaisesRegex(N.Refused,'unexpected_writable_output'): N.output_inventory(helper_runtime=a.b['runtime'],original=a.n['STATE']['process'])
                (root/'UNKNOWN_OUTPUT').unlink(); path.unlink(); path.symlink_to(root/'missing')
                with self.assertRaises(N.Refused): N.output_inventory(helper_runtime=a.b['runtime'],original=a.n['STATE']['process'])


if __name__=='__main__': unittest.main(verbosity=2)
