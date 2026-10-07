"""Parser controls are synthetic; they do not claim an actual executed owner PASS."""
import base64
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]/'plugins/friday_rework'
spec=importlib.util.spec_from_file_location('fixture_parser_test',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
package=importlib.util.module_from_spec(spec);sys.modules[spec.name]=package;spec.loader.exec_module(package)
from fixture_parser_test.goal_checks import verdict,strict_json


def make(good=True):
    stderr='test_add (test_calculator.CalculatorTest.test_add) ... '+('ok' if good else 'FAIL')+'\n\n----------------------------------------------------------------------\nRan 1 test in 0.000s\n\n'+('OK' if good else 'FAILED (failures=1)')+'\n'
    value=dict(accepted=good,returncode=0 if good else 1,executed=True,child_returncode=0 if good else 1,
               status='completed',elapsed_seconds=.05,artifact_sha256='a'*64,
               owner_sha256='3046b45b0b2c2702ac686ef1e946a6601c67d456a4e49b895566310674b33995',
               stdout='',stderr=stderr,stdout_base64='',stderr_base64=base64.b64encode(stderr.encode()).decode(),cleanup_completed=True)
    artifacts=[dict(reference='r',sha256='a'*64,size_bytes=32)]
    return value,artifacts


def envelope(value,code=0,**kw):
    return json.dumps(dict(output=json.dumps(value),exit_code=code,error=None,**kw))


@pytest.mark.parametrize('good',[True,False])
def test_synthetic_exact_shape_classification(good):
    value,artifacts=make(good)
    assert verdict(envelope(value,0 if good else 1),'coding_add',artifacts)==('PASS' if good else 'FAIL')


@pytest.mark.parametrize('change',['accepted_only','no_tests','wrong_count','wrong_owner','wrong_artifact','cleanup','executed','status','raw_mismatch','elapsed','type','extra','native_extra','oversized','truncated'])
def test_synthetic_unproven_or_changed_fields_stay_unknown(change):
    value,artifacts=make();terminal={}
    if change=='accepted_only':value={'accepted':True}
    if change=='no_tests':value['stderr']='OK\n';value['stderr_base64']=base64.b64encode(b'OK\n').decode()
    if change=='wrong_count':value['stderr']=value['stderr'].replace('Ran 1 test','Ran 2 tests');value['stderr_base64']=base64.b64encode(value['stderr'].encode()).decode()
    if change=='wrong_owner':value['owner_sha256']='b'*64
    if change=='wrong_artifact':value['artifact_sha256']='b'*64
    if change=='cleanup':value['cleanup_completed']=False
    if change=='executed':value['executed']=False
    if change=='status':value['status']='timeout'
    if change=='raw_mismatch':value['stderr_base64']=base64.b64encode(b'other').decode()
    if change=='elapsed':value['elapsed_seconds']=100
    if change=='type':value['returncode']=True
    if change=='extra':value['worker_claim']='PASS'
    if change=='native_extra':terminal['session_id']='yielded'
    if change=='oversized':value['stdout']='a'*33000
    raw=envelope(value,**terminal)
    if change=='truncated':raw=raw[:-1]
    assert verdict(raw,'coding_add',artifacts)=='UNKNOWN'


@pytest.mark.parametrize('raw',['{"x":1,"x":2}','{"x":NaN}','{"x":1e999}','[]','{}x'])
def test_strict_observation_json_rejects_incomplete_or_ambiguous(raw):
    with pytest.raises((ValueError,TypeError)):strict_json(raw)


def test_reversible_native_json_escaping_is_complete_but_redaction_is_not():
    value,artifacts=make()
    output=json.dumps(json.dumps(value))[1:-1]
    raw=json.dumps(dict(output=output,exit_code=0,error=None))
    assert verdict(raw,'coding_add',artifacts)=='PASS'
    value['stderr']=value['stderr'].replace('test_add','[REDACTED]')
    raw=json.dumps(dict(output=json.dumps(json.dumps(value))[1:-1],exit_code=0,error=None))
    assert verdict(raw,'coding_add',artifacts)=='UNKNOWN'
