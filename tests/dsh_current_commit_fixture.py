"""Synthetic T1 journals with real typed/native construction consumers.

No StoppedOperator admission, lock acquisition, real native release, worker,
model or network runs. The release seam below is explicitly a fixture stub;
these files establish parser/consumer controls, never installed provenance.
"""
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace


def commit_pending_fixture(f):
    from friday_admin_controls import dsh_current_availability as cur
    existing=getattr(f,'_pending_transaction',None)
    if existing is not None and cur.read_json(existing)['dsh_current']['cycle']==f.c['current_availability']['cycle']:
        return copy.deepcopy(existing)
    from friday_admin_controls import worker_declarations as dec
    from friday_admin_controls import worker_declaration_writer as writer
    from friday_admin_controls import dsh_current_availability as cur
    from friday_admin_controls.stopped_operator import _encoded
    from hermes_cli.config import fast_safe_load
    from scripts import friday_ordinary_install as ordinary
    from test_dsh_current_availability import save
    from test_dsh_current_writer import build_writer_case, publish
    s=getattr(f,'_t1_journal_case',None) or getattr(f,'_writer_case',None)
    if s is None:
        parent=f.root/'synthetic-t1-fixture';parent.mkdir(mode=0o700)
        s=build_writer_case(f,parent)
    if not any(s.stage.iterdir()):
        outputs=writer.prepare_afterimages(s.view,s.plan,s.stage)
    else:
        outputs={name:ordinary.update_file_state(s.stage/name) for name in s.names}
        assert all(outputs.values())
    if not all(ordinary.update_file_state(f.e.home/name)['data']==state['data']
            for name,state in outputs.items()):
        owned,_=publish(s,outputs)
    else:
        owned={name:ordinary.update_file_state(f.e.home/name) for name in s.names}
    request={'schema':dec.DSH_CURRENT_APPLY_SCHEMA,'seconds':180,
        'home':str(f.e.home),'profile':f.h.name,
        'previous_input':s.view.request['current_input'],
        'current_input':s.view.request['current_input'],
        'native_unit':{'path':str(s.evidence/'not-run.service'),'sha256':'a'*64},
        'before':{name:{'path':str(f.e.home/name),
            'sha256':hashlib.sha256(state['data']).hexdigest()}
            for name,state in s.view.before.items()},
        'retained':{},'declaration_source':s.source,
        'launcher_source':s.view.request['launcher_source'],
        'clock':f.c['current_availability']['cycle'],'native_pm':{}}
    request_ref=save(s.evidence/'synthetic-t1-request.json',request)
    own_name=str(f.h.relative_to(f.e.home))+'/config.yaml'
    old_config=fast_safe_load(s.view.before[own_name]['data'].decode('utf-8-sig'))
    previous=dec._at(old_config,dec.profile_dsh_path(old_config)).get('current_availability')
    root_config=fast_safe_load(s.view.before['config.yaml']['data'].decode('utf-8-sig'))
    tx=f.e.home/'preparation'/dec.dsh_current_transaction_name(s.b,previous,
        before_configurations=(root_config,old_config))
    tx.parent.mkdir(mode=0o700,exist_ok=True);tx.mkdir(mode=0o700)
    for folder,states in (('before',s.view.before),('stage',outputs)):
        (tx/folder).mkdir(mode=0o700)
        for name,state in states.items():
            ordinary.private_parents(tx/folder,name)
            ordinary.write(tx/folder/name,state['data'],state['mode'])
    clock=cur.read_json(request['clock'])
    intent={'schema':writer.APPLY_SCHEMA,'state':'CONSUMED_NO_RETRY',
        'request_sha256':request_ref['sha256'],'request_reference':request_ref,
        'request_semantic_sha256':hashlib.sha256(_encoded(request)).hexdigest(),
        'clock':clock,'clock_reference':request['clock'],
        'previous_input':request['previous_input'],'current_input':request['current_input'],
        'before':request['before'],'ready':False,'retry_authorized':False,
        'consumers_started':False,'workers_enabled':False,'runtime_acceptance':'NOT_GRANTED'}
    ordinary.write(tx/'intent.json',_encoded(intent))
    result={'state':'WORKER_DECLARATIONS_REBOUND_CONSUMERS_STOPPED',
        'ready':False,'workers_enabled':False,'consumers_started':False,
        'database_changed':False,'native_migration':'IMPLEMENTED',
        'runtime_acceptance':'NOT_GRANTED','automatic_prepare':False,
        'request_sha256':request_ref['sha256'],'clock':request['clock'],
        'previous_input':request['previous_input'],'current_input':request['current_input'],
        'semantic_changes':s.plan['semantic_changes'],
        'after':{name:hashlib.sha256(state['data']).hexdigest() for name,state in outputs.items()},
        'original_attempt_consumed':True,
        'dsh_current':{'stage':dec.DSH_CURRENT_DECLARATION_SCHEMA,
            **copy.deepcopy(f.c['current_availability']),'runtime_sha256':f.d['runtime_sha256']}}
    state=writer._new_journal(tx/'committed.json',ordinary.encoded(result))
    fixture_authority=SimpleNamespace(home=f.e.home,tx=tx,declaration_bundle=s.b,
        clock=clock,request=request,request_reference=request_ref,prove_released=lambda:None)
    writer._dsh_completed(fixture_authority,result,state,owned)
    reference={'path':str(tx/'committed.json'),
        'sha256':hashlib.sha256(state['data']).hexdigest()}
    f._pending_transaction=reference
    return copy.deepcopy(reference)
