"""Finite own-file atomic publication controls; no actor or namespace launch."""
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-CALC-FONT-ENV-REVIEWED-ROOT-20261115')
EVIDENCE = []


def load(name, path):
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), mod.__dict__)
    return mod


N = load('own_publication_namespace', BASE/'candidate/outer/namespace_entry.py')
OLD = load('own_original_namespace', ORIGINAL/'candidate/outer/namespace_entry.py')
FIX = load('own_publication_fixture', BASE/'fixture-source/held_fixture_supervisor.py')
OPEN, FSTAT = os.open, os.fstat


class ReaderControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=BASE, prefix='own-files-')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.path = self.work/'native-trace.json'
        self.end = time.monotonic()+10
        self.write(self.path, b'{"version":"old"}\n')
        self.patches = [patch.object(m, 'WORK', self.work) for m in (N, OLD, FIX)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def write(self, path, data, mode=0o600):
        path.write_bytes(data)
        path.chmod(mode)

    def replace_on_open(self, module, *, count=1, new=b'{"version":"new"}\n', transform=None):
        state = {'opens': 0, 'retired': []}
        def hooked(path, flags, *args, **kw):
            fd = OPEN(path, flags, *args, **kw)
            if Path(path) == self.path:
                state['opens'] += 1
                if state['opens'] <= count:
                    before = FSTAT(fd)
                    pending = self.work/('pending-'+str(state['opens']))
                    self.write(pending, new)
                    if transform:
                        transform(pending)
                    os.replace(pending, self.path)
                    after, current = FSTAT(fd), self.path.lstat()
                    state['retired'].append({'old_before_nlink': before.st_nlink,
                        'old_after_nlink': after.st_nlink,
                        'old_dev_ino': [after.st_dev, after.st_ino],
                        'current_dev_ino': [current.st_dev, current.st_ino],
                        'current_nlink': current.st_nlink})
            return fd
        return patch.object(module.os, 'open', hooked), state

    def test_actual_open_replace_proof_reproduces_original_refusal(self):
        hook, state = self.replace_on_open(OLD)
        with hook, self.assertRaisesRegex(OLD.Refused, '^runtime_file_rights$'):
            OLD.runtime_read(self.path)
        self.assertEqual(state['opens'], 1)
        row = state['retired'][0]
        self.assertEqual((row['old_before_nlink'], row['old_after_nlink'], row['current_nlink']), (1,0,1))
        self.assertNotEqual(row['old_dev_ino'], row['current_dev_ino'])
        EVIDENCE.append({'case': self._testMethodName, 'actual_kernel_metadata': row,
            'scope': 'CONTROLLED_OWN_FILE_NOT_OLD_FAILED_UNIT_METADATA'})

    def test_retired_before_fstat_reopens_and_returns_only_current(self):
        hook, state = self.replace_on_open(N)
        with hook:
            self.assertEqual(N.runtime_read(self.path, deadline=self.end), b'{"version":"new"}\n')
        self.assertEqual(state['opens'], 2)
        EVIDENCE.append({'case': self._testMethodName, **state})

    def test_retired_after_read_discards_old_bytes(self):
        calls = 0
        def changed(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                pending = self.work/'pending'
                self.write(pending,b'new')
                os.replace(pending,self.path)
            return FSTAT(fd)
        with patch.object(N.os,'fstat',changed):
            self.assertEqual(N.runtime_read(self.path,deadline=self.end),b'new')
        self.assertEqual(calls,5)

    def test_replacement_between_after_fstat_and_path_check_reopens(self):
        calls=0
        def changed(fd):
            nonlocal calls
            calls+=1
            observed=FSTAT(fd)
            if calls==2:
                pending=self.work/'pending';self.write(pending,b'new');os.replace(pending,self.path)
            return observed
        with patch.object(N.os,'fstat',changed):
            self.assertEqual(N.runtime_read(self.path,deadline=self.end),b'new')
        self.assertEqual(calls,5)

    def test_unlink_does_not_hide_descriptor_mode_change(self):
        calls=0
        def changed(fd):
            nonlocal calls
            calls+=1
            if calls==2:
                os.fchmod(fd,0o400)
                pending=self.work/'pending';self.write(pending,b'new');os.replace(pending,self.path)
            return FSTAT(fd)
        with patch.object(N.os,'fstat',changed),self.assertRaisesRegex(N.Refused,'runtime_file_changed'):
            N.runtime_read(self.path,deadline=self.end)
        self.assertEqual(calls,2)

    def test_phase_publication_is_also_explicitly_supported(self):
        self.path = self.work/'phase.json'
        self.write(self.path,b'old')
        hook,state = self.replace_on_open(N,new=b'newphase')
        with hook:
            self.assertEqual(N.runtime_read(self.path,deadline=self.end),b'newphase')
        self.assertEqual(state['opens'],2)

    def test_default_read_never_reopens_retired_descriptor(self):
        hook,state = self.replace_on_open(N)
        with hook,self.assertRaisesRegex(N.Refused,'^runtime_file_rights$'):
            N.runtime_read(self.path)
        self.assertEqual(state['opens'],1)

    def test_default_read_refuses_replacement_after_read(self):
        calls=0
        def changed(fd):
            nonlocal calls
            calls+=1
            if calls==2:
                pending=self.work/'pending';self.write(pending,b'new');os.replace(pending,self.path)
            return FSTAT(fd)
        with patch.object(N.os,'fstat',changed),self.assertRaisesRegex(N.Refused,'^runtime_file_changed$'):
            N.runtime_read(self.path)

    def test_churn_has_finite_eight_attempt_limit(self):
        hook,state = self.replace_on_open(N,count=20)
        with hook,self.assertRaisesRegex(N.Refused,'^runtime_publication_replacement_limit$'):
            N.runtime_read(self.path,deadline=self.end)
        self.assertEqual(state['opens'],8)

    def test_expired_and_nonfinite_deadlines_cannot_open(self):
        for end in (time.monotonic()-1, float('nan'), float('inf')):
            with self.subTest(end=end),patch.object(N.os,'open') as opened,self.assertRaises(N.Refused):
                N.runtime_read(self.path,deadline=end)
            opened.assert_not_called()

    def test_retry_keeps_same_deadline(self):
        hook,state = self.replace_on_open(N)
        with hook,patch.object(N.time,'monotonic',side_effect=[10.,12.]),self.assertRaisesRegex(N.Refused,'^runtime_publication_deadline$'):
            N.runtime_read(self.path,deadline=11.)
        self.assertEqual(state['opens'],1)

    def test_nonpublication_deadline_optin_refused(self):
        self.path=self.work/'grant.json';self.write(self.path,b'{}')
        with patch.object(N.os,'open') as opened,self.assertRaisesRegex(N.Refused,'^runtime_publication_deadline_or_path$'):
            N.runtime_read(self.path,deadline=self.end)
        opened.assert_not_called()

    def test_private_readonly_and_writable_records_remain_accepted(self):
        for mode in (0o400,0o600):
            self.path.chmod(mode)
            self.assertEqual(N.runtime_read(self.path),b'{"version":"old"}\n')
            self.assertEqual(N.runtime_read(self.path,deadline=self.end),b'{"version":"old"}\n')

    def test_wrong_mode_owner_hardlink_symlink_type_and_bound_refuse(self):
        self.path.chmod(0o640)
        with self.assertRaisesRegex(N.Refused,'runtime_file_rights'):N.runtime_read(self.path,deadline=self.end)
        self.path.chmod(0o600)
        with patch.object(N.os,'getuid',return_value=os.getuid()+1),self.assertRaisesRegex(N.Refused,'runtime_file_rights'):
            N.runtime_read(self.path,deadline=self.end)
        link=self.work/'hardlink';os.link(self.path,link)
        with self.assertRaisesRegex(N.Refused,'runtime_file_rights'):N.runtime_read(self.path,deadline=self.end)
        link.unlink();self.path.unlink();self.path.symlink_to(link)
        with self.assertRaisesRegex(N.Refused,'exact_work_file_required'):N.runtime_read(self.path,deadline=self.end)
        self.path.unlink();self.path.mkdir()
        with self.assertRaisesRegex(N.Refused,'runtime_file_rights'):N.runtime_read(self.path,deadline=self.end)
        self.path.rmdir();os.mkfifo(self.path,0o600)
        with self.assertRaisesRegex(N.Refused,'runtime_file_rights'):N.runtime_read(self.path,deadline=self.end)
        self.path.unlink();self.write(self.path,b'x'*1048577)
        with self.assertRaisesRegex(N.Refused,'runtime_file_rights'):N.runtime_read(self.path,deadline=self.end)

    def test_invalid_successor_is_not_retried(self):
        for kind in ('mode','hardlink','directory','symlink'):
            with self.subTest(kind=kind):
                if self.path.is_dir():self.path.rmdir()
                elif os.path.lexists(self.path):self.path.unlink()
                self.write(self.path,b'old')
                def transform(pending):
                    if kind=='mode':pending.chmod(0o640)
                    elif kind=='hardlink':os.link(pending,self.work/'successor-hardlink')
                    elif kind=='directory':pending.unlink();pending.mkdir()
                    else:pending.unlink();pending.symlink_to(self.work/'absent')
                hook,state=self.replace_on_open(N,transform=transform)
                # replace(file,directory) is invalid on Linux: replace an opened
                # file by directory via unlink+rename to test immediate type refusal.
                if kind=='directory':
                    def changed(path,flags,*a,**kw):
                        fd=OPEN(path,flags,*a,**kw)
                        if Path(path)==self.path:
                            state['opens']+=1;self.path.unlink();self.path.mkdir()
                        return fd
                    hook=patch.object(N.os,'open',changed)
                with hook,self.assertRaisesRegex(N.Refused,'runtime_file_rights'):
                    N.runtime_read(self.path,deadline=self.end)
                self.assertEqual(state['opens'],1)

    def test_truncation_and_inplace_change_never_trigger_reopen(self):
        for replacement in (b'',b'{"version":"bad"}\n'):
            with self.subTest(replacement=replacement):
                self.write(self.path,b'{"version":"old"}\n')
                calls=0
                def changed(fd):
                    nonlocal calls
                    calls+=1
                    if calls==2:self.write(self.path,replacement)
                    return FSTAT(fd)
                with patch.object(N.os,'fstat',changed),self.assertRaisesRegex(N.Refused,'runtime_file_changed'):
                    N.runtime_read(self.path,deadline=self.end)
                self.assertEqual(calls,2)

    def test_actual_fixture_wait_boundary_consumes_reopened_current_trace(self):
        trace={'error':None,'fixture_boundary':'AFTER_LOAD_BEFORE_QUERY','records':[],
               'record_semantics':'FIXTURE_MARKER_ONLY','process':{'pid':12,'start_ticks':34}}
        hook,state=self.replace_on_open(N,new=json.dumps(trace).encode())
        with hook:
            got=FIX.wait_boundary(N,types.SimpleNamespace(poll=lambda:None),'AFTER_LOAD_BEFORE_QUERY',self.end)
        self.assertEqual(got,trace['process']);self.assertEqual(state['opens'],2)

    def test_fixture_does_not_hide_reopened_observer_refusal(self):
        hook,state=self.replace_on_open(N,new=b'{"error":"refused"}')
        with hook,self.assertRaisesRegex(RuntimeError,'fixture_observer_refused_before_hold'):
            FIX.wait_boundary(N,types.SimpleNamespace(poll=lambda:None),'AFTER_LOAD_BEFORE_QUERY',self.end)
        self.assertEqual(state['opens'],2)

    def test_pinned_source_hash_refusal_is_unchanged(self):
        with self.assertRaisesRegex(N.Refused,'pinned_source_changed'):
            N.read_ref({'path':str(self.path),'sha256':'0'*64})


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReaderControls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (BASE/'NAMESPACE-TEST-RESULT.json').write_text(json.dumps({'tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'evidence':EVIDENCE,
        'live_actor_or_namespace_executed':False},sort_keys=True,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
