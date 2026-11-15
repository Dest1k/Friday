"""Pure changed-source checks. Never imports GDB or calls a process/effect leaf."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import types
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
ORIGINAL=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115')


def source(path):
    module=types.ModuleType(path.stem)
    module.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
    return module


host=source(BASE/'host/ownc_root_controller.py')
sup=source(BASE/'host/ownc_namespace_supervisor.py')
driver=source(BASE/'driver/ownc_gdb.py')
driver.require=lambda ok,code: None if ok else (_ for _ in ()).throw(RuntimeError(code))


class FakeDebugger:
    def __init__(self,env):
        self.environment=dict(env);self.commands=[]
    def execute(self,command,to_string=False):
        self.commands.append(command)
        if command=='set confirm off':return ''
        if command=='unset environment':self.environment.clear();return ''
        if command.startswith('set environment '):
            key,value=command[len('set environment '):].split('=',1)
            self.environment[key]=value;return ''
        raise AssertionError('unexpected debugger operation')


class EnvironmentDeltaControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads((BASE/'inputs/worker_cached/STATIC-PLAN.json').read_bytes())
        cls.expected=cls.plan['target_environment']

    def test_real_four_metadata_namespace_validator_joins(self):
        for variant in ('worker_cached','extra_fork','forbidden_gpg_home','wrong_gpgconf_name'):
            with self.subTest(variant=variant):
                plan=json.loads((BASE/'inputs'/variant/'STATIC-PLAN.json').read_bytes())
                prepared=host.inspect_plan(plan)
                self.assertEqual(prepared['target_environment'],plan['target_environment'])
                self.assertEqual(plan['budgets'],dict(wall_seconds=240,cpu_seconds=120,
                    memory_bytes=2147483648,cleanup_seconds=10,startup_seconds=60,tasks_max=64))

    def test_namespace_exact_execve_without_ambient_and_builder_preserved(self):
        builder=host.load_module(self.plan['source_refs']['metric_namespace'],'pure_builder')
        # Avoid operation directories: only source argv construction is exercised.
        builder.owned_directory=Path
        plan=copy.deepcopy(self.plan)
        argv=host.namespace_argv(plan,builder,work=Path('/source-only-argv-placeholder'),job_ref={})
        launcher=ast.parse(argv[-1])
        call=launcher.body[-1].value
        self.assertEqual(ast.unparse(call.func),'os.execve')
        self.assertEqual(ast.literal_eval(call.args[2]),self.expected)
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr=='environ' for n in ast.walk(launcher)))
        calls=[]
        fake=types.SimpleNamespace(execve=lambda *args:calls.append(args))
        expression=ast.fix_missing_locations(ast.Module(body=[launcher.body[-1]],type_ignores=[]))
        exec(compile(expression,'source-execve-only-expression','exec'),{'os':fake})
        self.assertEqual(calls[0][2],self.expected)
        legacy=source(ORIGINAL/'host/ownc_root_controller.py').namespace_argv(
            plan,builder,work=Path('/source-only-argv-placeholder'),job_ref={})
        self.assertEqual(argv[:argv.index('--')],legacy[:legacy.index('--')])
        self.assertIn('--unshare-all',argv);self.assertIn('--die-with-parent',argv)

    def test_builder_extra_missing_changed_and_duplicate_still_refused(self):
        expected={k:v for k,v in self.expected.items() if k!='DEBUGINFOD_URLS'}
        for mode in ('extra','missing','changed','duplicate'):
            env=list(expected.items())
            if mode=='extra':env.append(('AMBIENT','private'))
            if mode=='missing':env=env[1:]
            if mode=='changed':env[0]=(env[0][0],'wrong')
            if mode=='duplicate':env.append(env[0])
            class Builder:
                def build_namespace(self,**kwargs):
                    return ['bwrap','--clearenv',*[p for kv in env for p in ('--setenv',*kv)],'--',*kwargs['command']]
            with self.subTest(mode=mode),self.assertRaises(RuntimeError):
                host.namespace_argv(self.plan,Builder(),work=Path('/placeholder'),job_ref={})

    def test_gdb_construction_clears_ambient_preserves_python_env_all_controls_debugger_only(self):
        before=dict(os.environ)
        ambient=dict(self.expected,AMBIENT='secret',**{k:'debugger-ref' for k in driver.CONTROLS})
        fake=FakeDebugger(ambient)
        driver.construct_inferior_environment(fake,self.expected)
        self.assertEqual(fake.commands[:2],['set confirm off','unset environment'])
        self.assertEqual(fake.environment,self.expected)
        self.assertEqual(len(fake.commands),2+len(self.expected))
        self.assertEqual(dict(os.environ),before)
        self.assertFalse(set(driver.CONTROLS)&set(fake.environment))
        observed='\n'.join(k+'='+v for k,v in sorted(fake.environment.items()))
        self.assertEqual(driver.validate_inferior_environment(observed,self.expected),self.expected)

    def test_unsafe_command_encodings_refused_before_debugger_commands(self):
        for key,value in [('BAD\nunset environment','x'),('BAD=NAME','x'),('A-B','x'),('','x'),
                ('A\0','x'),('A','x\ncontinue'),('A','x\rcontinue'),('A','x\0'),('A',' x'),('A','x ')]:
            fake=FakeDebugger({})
            with self.subTest(key=repr(key),value=repr(value)),self.assertRaisesRegex(
                    RuntimeError,'^fixture_declared_target_environment$'):
                driver.construct_inferior_environment(fake,{key:value})
            self.assertEqual(fake.commands,[])
        for control in driver.CONTROLS:
            fake=FakeDebugger({})
            with self.assertRaisesRegex(RuntimeError,'^fixture_no_debug_controls_in_target_environment$'):
                driver.construct_inferior_environment(fake,{control:'x'})
            self.assertEqual(fake.commands,[])

    def test_single_line_shell_metacharacters_are_passed_literally_no_shell(self):
        fake=FakeDebugger({})
        env={'VALUE':'$(never-run);`never-run`#literal=still-value','EMPTY':''}
        driver.construct_inferior_environment(fake,env)
        self.assertEqual(fake.environment,env)
        self.assertEqual(driver.validate_inferior_environment('\n'.join(k+'='+v for k,v in env.items()),env),env)

    def test_complete_gdb_comparator_rejects_every_final_difference(self):
        expected={'A':'same','EMPTY':''}
        for actual in ('A=same\nEMPTY=\nEXTRA=x','A=same','A=changed\nEMPTY=',
                'A=same\nA=same\nEMPTY=','not-an-environment-line'):
            with self.subTest(actual=actual),self.assertRaises(RuntimeError):
                driver.validate_inferior_environment(actual,expected)

    def test_supervisor_and_gdb_diagnostics_metadata_only_and_bounded(self):
        actual={'CHANGED':'ACTUAL_PRIVATE_VALUE','EXTRA':'EXTRA_PRIVATE_VALUE',**{
            'K'+str(i)+'x'*200:'PRIVATE'+str(i) for i in range(300)}}
        expected={'CHANGED':'EXPECTED_PRIVATE_VALUE','MISSING':'MISSING_PRIVATE_VALUE'}
        for module in (sup,driver):
            value=module.environment_diagnostic(actual,expected,phase='PURE',nonce='a'*32,exception_class='RuntimeError')
            raw=json.dumps(value,sort_keys=True)
            self.assertNotIn('PRIVATE',raw)
            self.assertLess(len(raw),18000)
            self.assertEqual(value['extra_count'],301);self.assertEqual(value['missing_keys'],['MISSING'])
            self.assertEqual(value['changed_keys'],['CHANGED']);self.assertLessEqual(len(value['extra_keys']),32)
            self.assertNotEqual(value['actual_sha256'],value['expected_sha256'])
        self.assertEqual(sup.environment_diagnostic(actual,expected,phase='PURE',nonce='a'*32,exception_class=None),
            driver.environment_diagnostic(actual,expected,phase='PURE',nonce='a'*32,exception_class=None))

    def test_supervisor_strict_refusal_and_first_error_survive_diagnostic_oserror(self):
        with patch.object(sup,'new_json',side_effect=OSError('PRIVATE_EXCEPTION_VALUE')):
            with self.assertRaisesRegex(RuntimeError,'^fixture_supervisor_complete_environment$'):
                sup.validate_supervisor_environment({'A':'actual'},{'A':'expected'},'a'*32)
            with self.assertRaises(OSError):
                sup.validate_supervisor_environment({'A':'same'},{'A':'same'},'a'*32)
        values=[]
        with patch.object(sup,'new_json',side_effect=lambda p,v:values.append((p,v))):
            sup.validate_supervisor_environment(self.expected,self.expected,'a'*32)
        self.assertEqual(values[0][0],sup.WORK/'ownc-namespace-environment-check.json')
        self.assertIsNone(values[0][1]['exception_class'])

    def test_gdb_first_comparison_or_parse_refusal_survives_diagnostic_oserror(self):
        def refuse(value):raise OSError('PRIVATE_EXCEPTION_VALUE')
        for actual,code in [('A=actual','fixture_complete_startup_environment_mismatch'),
                ('A=expected\nA=expected','fixture_inferior_environment_duplicate'),
                ('unparseable','fixture_inferior_environment_encoding')]:
            with self.subTest(code=code),self.assertRaisesRegex(RuntimeError,'^'+code+'$'):
                driver.validate_inferior_environment(actual,{'A':'expected'},publish=refuse,nonce='a'*32)
        with self.assertRaises(OSError):
            driver.validate_inferior_environment('A=expected',{'A':'expected'},publish=refuse,nonce='a'*32)

    def test_diagnostic_construction_failure_cannot_replace_first_refusal(self):
        for module,invoke,code in (
                (sup,lambda:sup.validate_supervisor_environment({'A':'actual'},{'A':'expected'},'a'*32),
                 'fixture_supervisor_complete_environment'),
                (driver,lambda:driver.validate_inferior_environment('A=actual',{'A':'expected'},
                 publish=lambda value:None,nonce='a'*32),'fixture_complete_startup_environment_mismatch')):
            with patch.object(module,'environment_diagnostic',side_effect=OSError('PRIVATE')):
                with self.assertRaisesRegex(RuntimeError,'^'+code+'$'):invoke()
        values=[]
        with self.assertRaisesRegex(RuntimeError,'^fixture_complete_startup_environment_mismatch$'):
            driver.validate_inferior_environment('A=\udcff',{'A':'expected'},publish=values.append,nonce='a'*32)
        self.assertEqual(len(values),1)

    def test_source_order_and_native_finally_unchanged(self):
        new=ast.parse((BASE/'driver/ownc_gdb.py').read_bytes());old=ast.parse((ORIGINAL/'driver/ownc_gdb.py').read_bytes())
        newrun=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        oldrun=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        newtry=next(n for n in newrun.body if isinstance(n,ast.Try));oldtry=next(n for n in oldrun.body if isinstance(n,ast.Try))
        self.assertEqual(ast.dump(ast.Module(body=newtry.finalbody,type_ignores=[])),
            ast.dump(ast.Module(body=oldtry.finalbody,type_ignores=[])))
        body=ast.unparse(newtry)
        self.assertLess(body.index('construct_inferior_environment('),body.index('validate_inferior_environment('))
        self.assertLess(body.index('validate_inferior_environment('),body.index("gdb.execute('starti'"))
        self.assertIn('capture_refusal_stop()',body)
        self.assertIn("exec(compile(final, CFG['native_observer_ref']['path'], 'exec'), globals())",body)
        # The fixed full ENV consumer, kernel/current/child checks remain in exact immutable refs.
        for variant in ('worker_cached','extra_fork','forbidden_gpg_home','wrong_gpgconf_name'):
            before=json.loads((ORIGINAL/'inputs'/variant/'PREPARED.json').read_bytes())
            after=json.loads((BASE/'inputs'/variant/'PREPARED.json').read_bytes())
            for key in before:
                if key not in ('gdb_driver_ref','supervisor_ref'):self.assertEqual(before[key],after[key])

    def test_fresh_fork_wrapper_binds_new_controller_only(self):
        before=(ORIGINAL/'host/root_fresh_fork.sh').read_text()
        after=(BASE/'host/root_fresh_fork.sh').read_text()
        self.assertEqual(after,before.replace(str(ORIGINAL/'host/ownc_root_controller.py'),
            str(BASE/'host/ownc_root_controller.py')))
        self.assertTrue(after.endswith('status=$?\nexit "$status"\n'))
        self.assertNotIn('exec /usr/bin/python3',after)

    def test_exact_source_mutation_current_pin_refused(self):
        mutated=dict(self.plan['source_refs']['supervisor'],sha256='0'*64)
        with self.assertRaisesRegex(RuntimeError,'^ownc_ref_pin$'):host.read_ref(mutated)


if __name__=='__main__':unittest.main(verbosity=2)
