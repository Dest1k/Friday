"""Pure/static caller checks. Synthetic runtime joins are not execution proof."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import types
import unittest

BASE=Path(__file__).resolve().parents[1]

def load(path):
    m=types.ModuleType('frw_ownc_source_test');m.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m

I=load(BASE/'inputs/ownc_inputs.py');D=load(BASE/'driver/ownc_gdb.py')
P=load(I.DEPS/'paper_helper_policy.py');G=load(I.DEPS/'gpgme_engine_bundle.py')


def runtime(prepared):
    p=copy.deepcopy(prepared['runtime_template']);g=copy.deepcopy(prepared['gpgme_runtime_template'])
    for r in (p,g):r.update(operation_id='SOURCE_SCHEMA_CHECK_ONLY',nonce='0'*32,operation_deadline_monotonic=1.0)
    return p,g


class SourceChecks(unittest.TestCase):
    def variants(self):
        return [(v,json.loads((BASE/'inputs'/v/'PREPARED.json').read_bytes())) for v in
                ('worker_cached','extra_fork','forbidden_gpg_home','wrong_gpgconf_name')]

    def test_all_reviewed_selected_sources_still_exact(self):
        c=json.loads((I.REVIEWED/'ROOT-COMPOSITION.json').read_bytes())
        self.assertEqual(len(c['files']),16)
        for item in c['files']:
            self.assertEqual(I.ref(Path(item['selected']['path']))['sha256'],item['selected']['sha256'])
        for _,p in self.variants():
            for key in ('source_ref','target_ref','manifest_ref','adapter_ref','policy_ref','native_observer_ref',
                        'namespace_ref','gdb_driver_ref','supervisor_ref'):
                self.assertEqual(I.ref(Path(p[key]['path'])),p[key])

    def test_real_elf_calls_and_normalized_nonpie_marker_sites(self):
        for _,p in self.variants():
            e=I.ELF(Path(p['target_ref']['path']));m=json.loads(Path(p['manifest_ref']['path']).read_bytes())
            self.assertEqual(e.etype,2);self.assertEqual(e.origin,0x400000)
            self.assertEqual(m['caller'],e.paper_caller())
            for name,offset in p['marker_offsets'].items():
                self.assertEqual(offset+e.origin,e.symbols[name][0])
                self.assertEqual(e.get(offset+e.origin,len(bytes.fromhex(p['marker_entry_bytes'][name]))).hex(),
                                 p['marker_entry_bytes'][name])
            with self.assertRaises(ValueError):e.get(0,16)

    def test_fixture_paper_policy_own_target_not_office(self):
        for _,p in self.variants():
            m=json.loads(Path(p['manifest_ref']['path']).read_bytes())
            P.validate_manifest(m,fixture=True)
            with self.assertRaisesRegex(RuntimeError,'helper_manifest_kind'):P.validate_manifest(m)
            bad=copy.deepcopy(m);bad['caller']['sites']['popen_return']['offset']=bad['caller']['function_offset']
            with self.assertRaisesRegex(RuntimeError,'helper_call_site_range'):P.validate_manifest(bad,fixture=True)

    def test_only_exact_one_fixture_validator_pin_changes(self):
        old=(I.DEPS/'gpgme_engine_bundle.py').read_bytes()
        for _,p in self.variants():
            b=p['gpgme_binding'];fixture=Path(b['validator']['path']).read_bytes()
            self.assertEqual(fixture,old.replace(G.PAPER_MANIFEST_SHA256.encode(),p['manifest_ref']['sha256'].encode(),1))
            self.assertEqual(Path(b['validator']['path']).name,'gpgme_engine_bundle.py')
        self.assertEqual(I.ref(I.DEPS/'gpgme_engine_bundle.py')['sha256'],
                         '72f0126e4fffcdba7d43f76a92bf2c03555ad86f8738c315cf41f389052efa15')

    def test_real_runtime_validator_manifest_clock_and_paper_joins(self):
        for _,p in self.variants():
            b=p['gpgme_binding'];v=load(Path(b['validator']['path']))
            modules=v.load_sources(b,lambda r:Path(r['path']).read_bytes())
            m=json.loads(Path(b['manifest']['path']).read_bytes());paper,gpg=runtime(p)
            P.validate_runtime(paper,json.loads(Path(p['manifest_ref']['path']).read_bytes()))
            v.validate_runtime(gpg,manifest_ref=b['manifest'],paper_runtime=paper)
            bundle=dict(schema=v.SCHEMA,manifest_ref=b['manifest'],runtime=gpg,evidence_path=v.EVIDENCE_PATH,
                        **{role+'_ref':b[role] for role in v.MODULES})
            v.validate_bundle(bundle,m,modules['policy'],modules['collector'])
            with self.assertRaisesRegex(G.Refused,'gpgme_exact_paper_window_and_outputs'):G.validate_runtime(gpg)
            bad=copy.deepcopy(gpg);bad['operation_deadline_monotonic']=2.0
            with self.assertRaisesRegex(v.Refused,'gpgme_same_paper_load_window'):v.validate_runtime(bad,paper_runtime=paper)
            bad=copy.deepcopy(m);bad['collector_pins']['future_exit_code']=0
            with self.assertRaisesRegex(RuntimeError,'gpgme_collector_pins_schema'):
                v.validate_manifest(bad,modules['policy'],modules['collector'])

    def test_real_dependencies_full_declared_environment_and_no_future_facts(self):
        p=self.variants()[0][1];b=p['gpgme_binding'];v=load(Path(b['validator']['path']))
        modules=v.load_sources(b,lambda r:Path(r['path']).read_bytes());m=json.loads(Path(b['manifest']['path']).read_bytes())
        v.validate_manifest(m,modules['policy'],modules['collector'])
        pins=m['collector_pins'];self.assertEqual(pins['environment'],I.ENV)
        self.assertEqual(len(m['profile']['branches']),6);self.assertEqual(set(m['helpers']),{'gpgconf','gpg','gpgsm'})
        for k in ('operation','original','reaper','private_roots','cgroup','uid_projection'):self.assertIsNone(pins[k])
        images={x['path']:x for arr in pins['dependencies'].values() for x in arr}
        for path,image in images.items():
            self.assertEqual(I.ref(Path(path))['sha256'],image['sha256'])
            self.assertEqual(I.host_stamp(path),image['host_stamp'])
        bad=copy.deepcopy(m);bad['collector_pins']['environment']['GNUPGHOME']='/tmp/forbidden'
        with self.assertRaisesRegex(RuntimeError,'gpgme_environment_isolation_or_override'):
            v.validate_manifest(bad,modules['policy'],modules['collector'])

    def test_complete_startup_environment_refuses_unpinned_extra_keys(self):
        D.require=lambda ok,reason:None if ok else (_ for _ in ()).throw(RuntimeError(reason))
        text='\n'.join(k+'='+v for k,v in I.ENV.items())
        self.assertEqual(D.validate_inferior_environment(text,I.ENV),I.ENV)
        for extra in ('\nGNUPGHOME=/tmp/keyring','\nFRW_HELD_FIXTURE_CONFIG=/tmp/config','\nCOLUMNS=80'):
            with self.assertRaisesRegex(RuntimeError,'fixture_complete_startup_environment_mismatch'):
                D.validate_inferior_environment(text+extra,I.ENV)
        with self.assertRaisesRegex(RuntimeError,'fixture_inferior_environment_duplicate'):
            D.validate_inferior_environment(text+'\nHOME=/tmp/other',I.ENV)
        self.assertEqual(set(D.CONTROLS),{'FRW_NATIVE_OBSERVER_CONFIG','FRW_NATIVE_LOAD_DEPENDENCY_REF',
            'FRW_NATIVE_GPGME_ENGINE_INIT_REF','FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE','FRW_HELD_FIXTURE_CONFIG'})

    def test_native_unknownfork_helpers_and_finally_are_exact_selected_ast(self):
        raw=(I.DEPS/'native_return_observer.py').read_bytes();tree=ast.parse(raw)
        definitions,final=D.exact_native(tree)
        originals={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        for n in definitions.body:self.assertEqual(ast.dump(n),ast.dump(originals[n.name]))
        self.assertTrue({'process_boundary_snapshot','boundary_symbol','boundary_proc_identity'}<=D.NATIVE_NAMES)
        original_final=[n.finalbody for n in tree.body if isinstance(n,ast.Try)][-1]
        self.assertEqual(ast.dump(final),ast.dump(ast.Module(body=original_final,type_ignores=[])))
        self.assertNotIn('cleanup_inferiors',ast.unparse(final))
        bad=copy.deepcopy(tree);bad.body=[n for n in bad.body if not(isinstance(n,ast.FunctionDef) and n.name=='boundary_symbol')]
        with self.assertRaisesRegex(RuntimeError,'fixture_native_definitions'):D.exact_native(bad)

    def test_single_window_callback_order_and_pending_drain_path_static(self):
        tree=ast.parse((BASE/'driver/ownc_gdb.py').read_bytes());defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        calls=lambda name:[ast.unparse(n) for n in ast.walk(defs[name]) if isinstance(n,ast.Call)]
        self.assertIn("load_window('LOAD_OPEN')",calls('ready'))
        self.assertNotIn("load_window('LOAD_CLOSED')",calls('paper_done'))
        after=ast.unparse(defs['after_load'])
        self.assertLess(after.index('helper.gpgme.metric_ready()'),after.index("load_window('LOAD_CLOSED')"))
        self.assertLess(after.index("load_window('LOAD_CLOSED')"),after.index('helper.metric_ready()'))
        source=ast.unparse(defs['run'])
        self.assertIn('helper.paper.catchpoints = dict(catchpoints)',source)
        self.assertIn('helper.gpgme.catchpoints = dict(catchpoints)',source)
        self.assertIn('helper.gpgme.drain()',source)
        self.assertNotIn('helper.catchpoints =',source)
        self.assertNotIn('cleanup_inferiors(',source)

    def test_fixture_refusal_diagnostic_never_asserts_future_release_or_negative_pass(self):
        tree=ast.parse((BASE/'driver/ownc_gdb.py').read_bytes());defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        source=ast.unparse(defs['capture_refusal_stop'])
        self.assertIn('helper.gpgme.paper_closed()',source)
        self.assertIn('helper.proc(inf.pid) == before',source)
        self.assertNotIn('affected_child_released',source)
        self.assertNotIn('PASS',source)
        for _,p in self.variants():
            if p['expected_refusal'] is not None:
                self.assertFalse(p['expected_refusal']['affected_child_released'])
                self.assertIn(p['expected_refusal']['stage'],('boundary:fork','bootstrap_entry','dirs_entry'))


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SourceChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
