"""Independent own tiny-file controls. No actors, namespaces or live effects."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parent

def load(name, filename):
    path=BASE/'source'/filename
    mod=types.ModuleType(name);mod.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),mod.__dict__)
    return mod

N=load('review_namespace','namespace_entry.py')
I=load('review_inner','inner_client.py')
F=load('review_fixture','held_fixture_supervisor.py')
OPEN,FSTAT=os.open,os.fstat
EVIDENCE=[]

class IndependentReview(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=BASE,prefix='own-case-')
        self.addCleanup(self.tmp.cleanup)
        self.work=Path(self.tmp.name);self.end=time.monotonic()+10
        for m,value in ((N,self.work),(I,str(self.work)),(F,self.work)):
            p=patch.object(m,'WORK',value);p.start();self.addCleanup(p.stop)
        self.opens=[]
    def write(self,path,raw):
        if not isinstance(raw,bytes):raw=json.dumps(raw,sort_keys=True,separators=(',',':')).encode()
        path.write_bytes(raw);path.chmod(0o600)
        return raw
    def replace_hook(self,path,replacement,*,keep_linked=False):
        def opened(p,flags,*a,**kw):
            fd=OPEN(p,flags,*a,**kw)
            if Path(p)==path:
                self.opens.append(fd)
                if len(self.opens)==1:
                    before=FSTAT(fd)
                    if keep_linked:path.rename(self.work/'kept-old')
                    pending=self.work/'pending';self.write(pending,replacement);os.replace(pending,path)
                    EVIDENCE.append({'case':self._testMethodName,'old_links_before':before.st_nlink,
                        'old_links_after':FSTAT(fd).st_nlink,'current_links':path.lstat().st_nlink,
                        'different_inode':FSTAT(fd).st_ino!=path.lstat().st_ino})
            return fd
        return patch.object(os,'open',opened)
    def test_namespace_renamed_old_linked_fd_is_not_retryable(self):
        p=self.work/'native-trace.json';self.write(p,b'old')
        with self.replace_hook(p,b'new',keep_linked=True),self.assertRaisesRegex(N.Refused,'runtime_file_changed'):
            N.runtime_read(p,deadline=self.end)
        self.assertEqual(len(self.opens),1)
    def test_namespace_missing_successor_is_not_retryable(self):
        p=self.work/'native-trace.json';self.write(p,b'old')
        def opened(path,flags,*a,**kw):
            fd=OPEN(path,flags,*a,**kw);self.opens.append(fd);p.unlink();return fd
        with patch.object(os,'open',opened),self.assertRaises(FileNotFoundError):
            N.runtime_read(p,deadline=self.end)
        self.assertEqual(len(self.opens),1)
    def test_namespace_stable_result_after_end_is_refused(self):
        p=self.work/'phase.json';self.write(p,b'{}')
        with patch.object(N.time,'monotonic',side_effect=[10.,12.]),self.assertRaisesRegex(N.Refused,'runtime_publication_deadline'):
            N.runtime_read(p,deadline=11.)
    def test_namespace_mutation_then_unlink_does_not_hide_content_change(self):
        p=self.work/'native-trace.json';self.write(p,b'old');before=p.stat();count=0
        def stat(fd):
            nonlocal count
            count+=1
            if count==2:
                self.write(p,b'bad');os.utime(p,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
                pending=self.work/'pending';self.write(pending,b'new');os.replace(pending,p)
            return FSTAT(fd)
        with patch.object(os,'fstat',stat),self.assertRaisesRegex(N.Refused,'runtime_file_changed'):
            N.runtime_read(p,deadline=self.end)
        self.assertEqual(count,2)
    def test_request_user_receipt_and_source_names_cannot_opt_in(self):
        for name in ('font-runtime-loaded-request.json','user-input.json','receipt.json','source.py'):
            p=self.work/name;self.write(p,b'{}')
            with self.subTest(name=name),patch.object(os,'open') as opened,self.assertRaisesRegex(N.Refused,'runtime_publication_deadline_or_path'):
                N.runtime_read(p,deadline=self.end)
            opened.assert_not_called()
    def test_nearest_acquire_both_phases_use_successor_before_effects(self):
        for boundary,phase in (('AFTER_LOAD_BEFORE_QUERY','IDLE'),('AFTER_READONLY_CLOSE','CLOSED')):
            with self.subTest(boundary=boundary):
                p=self.work/'phase.json';self.write(p,{'nonce':'WRONG','phase':'WRONG'})
                self.write(self.work/'helper-runtime.json',{'runtime':{'operation_id':'WRONG','nonce':'a'*32,
                    'operation_deadline_monotonic':self.end}})
                expected={'nonce':'a'*32,'phase':phase,'index':None,'digit':None}
                self.opens=[];services=N.LocalServices()
                with self.replace_hook(p,expected),patch.object(services,'process') as process, \
                    patch.object(os,'pidfd_open') as pidfd,patch.object(N.signal,'pidfd_send_signal') as send, \
                    self.assertRaisesRegex(N.Refused,'^font_runtime_request_original_deadline$'):
                    services.acquire_font_runtime({'operation_id':'own-review','nonce':'a'*32},{},
                        boundary=boundary,deadline=self.end,child=types.SimpleNamespace())
                self.assertEqual(len(self.opens),2);process.assert_not_called();pidfd.assert_not_called();send.assert_not_called()
                self.assertFalse(any(self.work.glob('font-runtime-*.json')))
    def test_nearest_acquire_reopened_wrong_phase_refuses_before_effects(self):
        p=self.work/'phase.json';self.write(p,b'{}');services=N.LocalServices()
        with self.replace_hook(p,{'nonce':'b'*32,'phase':'CLOSED','index':None,'digit':None}), \
            patch.object(os,'pidfd_open') as pidfd,patch.object(N.signal,'pidfd_send_signal') as send, \
            self.assertRaisesRegex(N.Refused,'^font_runtime_request_phase$'):
            services.acquire_font_runtime({'operation_id':'own-review','nonce':'a'*32},{},
                boundary='AFTER_READONLY_CLOSE',deadline=self.end,child=types.SimpleNamespace())
        self.assertEqual(len(self.opens),2);pidfd.assert_not_called();send.assert_not_called()
    def test_nearest_release_reopened_observer_error_preserves_strict_records(self):
        p=self.work/'native-trace.json';native={'pid':12,'start_ticks':23};office={'birth':'own-inert'}
        request={'operation_id':'own-review','nonce':'a'*32,'boundary':'AFTER_READONLY_CLOSE',
            'sequence':1,'process':native,'deadline_monotonic':self.end}
        paths=N.font_runtime_paths(request['boundary']);raw_request=self.write(paths['request'],request)
        raw_proof=self.write(paths['proof'],{'own':'inert-proof'});self.write(p,{'error':None,'process':native})
        held={'request':request,'request_ref':{'path':str(paths['request']),'sha256':N.sha(raw_request)},
            'proof_ref':{'path':str(paths['proof']),'sha256':N.sha(raw_proof)},'office_process':office}
        services=N.LocalServices()
        with self.replace_hook(p,{'error':'CONTROLLED_REFUSAL','process':native}), \
            patch.object(services,'process',return_value=office),self.assertRaisesRegex(N.Refused,'^font_runtime_release_observer_refused$'):
            services.release_font_runtime({},held,view_ref={'path':str(self.work/'view'),'sha256':'c'*64},deadline=self.end)
        self.assertEqual(len(self.opens),2);self.assertTrue(paths['release'].exists());self.assertFalse(paths['accepted'].exists())
        self.assertEqual(paths['request'].read_bytes(),raw_request);self.assertEqual(paths['proof'].read_bytes(),raw_proof)
    def test_nearest_fixture_lateclose_reopened_wrong_record_count_refuses(self):
        p=self.work/'native-trace.json';self.write(p,b'{}')
        replacement={'error':None,'fixture_boundary':'AFTER_READONLY_CLOSE','record_semantics':'FIXTURE_MARKER_ONLY',
            'records':[],'process':{'pid':12,'start_ticks':23}}
        with self.replace_hook(p,replacement),self.assertRaisesRegex(RuntimeError,'^fixture_boundary_marker_count$'):
            F.wait_boundary(N,types.SimpleNamespace(poll=lambda:None),'AFTER_READONLY_CLOSE',self.end)
        self.assertEqual(len(self.opens),2)
    def test_inner_wait_poll_and_reopen_retain_one_absolute_end(self):
        p=self.work/'native-trace.json';self.write(p,{'status':'STARTING'})
        clock=[100.];ends=[];reader=I.active_trace_bytes
        def read(path,*,deadline,**kw):
            ends.append(deadline);return reader(path,deadline=deadline,**kw)
        def sleep(duration):clock[0]+=duration
        with self.replace_hook(p,{'status':'STARTING'}),patch.object(I,'active_trace_bytes',read), \
            patch.object(I.time,'monotonic',side_effect=lambda:clock[0]),patch.object(I.time,'sleep',sleep), \
            self.assertRaisesRegex(I.Refused,'^bounded_metadata_wait_expired$'):
            I.wait_json(str(p),1,lambda v:v['status']=='READY',active_trace=True,deadline=100.06)
        self.assertEqual(set(ends),{100.06});self.assertAlmostEqual(clock[0],100.06)
        self.assertGreater(len(ends),1)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(IndependentReview)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'scope':'SOURCE_ONLY_OWN_TINY_FILES_AND_INERT_MOCKS','tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'successful':result.wasSuccessful(),'controlled_kernel_metadata':EVIDENCE}
    (BASE/'TEST-RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
