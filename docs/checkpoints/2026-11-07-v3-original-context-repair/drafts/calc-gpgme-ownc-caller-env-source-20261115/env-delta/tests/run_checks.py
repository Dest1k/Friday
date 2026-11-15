"""Finite source suites only; unchanged evidence stays by exact original refs."""
from pathlib import Path
import datetime
import hashlib
import io
import json
import os
import types
import unittest

BASE=Path(__file__).resolve().parents[1]
ORIGINAL=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115')


def execute_suite(source, synthetic_file, name):
    namespace={'__file__':str(synthetic_file),'__name__':name}
    exec(compile(source.read_bytes(),str(source),'exec'),namespace)
    module=types.ModuleType(name);module.__dict__.update(namespace)
    suite=unittest.defaultTestLoader.loadTestsFromModule(module)
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    output=BASE/'tests'/(name+'.log')
    output.write_text(stream.getvalue());output.chmod(0o600)
    assert result.wasSuccessful(),stream.getvalue()
    return dict(tests=result.testsRun,status='PASS_PURE_SOURCE_ONLY',
        source_ref=dict(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest()),
        source_file_context=str(synthetic_file),log_ref=dict(path=str(output),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest()))


def main():
    os.umask(0o077)
    checks={}
    checks['changed_delta']=execute_suite(BASE/'tests/env_delta_controls.py',
        BASE/'tests/env_delta_controls.py','changed_delta_controls')
    checks['nearest_host_consumers']=execute_suite(ORIGINAL/'host/test_host_source.py',
        BASE/'host/test_host_source.py','retained_host_consumers')
    checks['nearest_real_metadata_consumers']=execute_suite(ORIGINAL/'host/test_actual_joins.py',
        BASE/'host/test_actual_joins.py','retained_real_metadata_consumers')
    files=list(BASE.rglob('*.py'))
    for path in files:compile(path.read_bytes(),str(path),'exec')
    result=dict(schema='frw.ownc.environment-source-delta-checks.v1',
        at_moscow=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
        checks=checks,in_memory_compilation=len(files),actor_execution=False,
        actual_GDB_compatibility=False,actual_namespace_compatibility=False,
        reused_only_for_unchanged_parts=dict(original_driver21='9e97d537cb986a621efafcf27ef0b4f46f4f2b2889fa401934b2754d3c855854',
            original_pure10='1289619bd86b091df6a465153431778e9d39a55bc41ed4a66bacba5bde55633e'))
    out=BASE/'tests/CHECKS.json'
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');out.chmod(0o600)
    print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest()),sort_keys=True))


if __name__=='__main__':main()
