#!/usr/bin/env python3
"""Installed209 selective real ordinary-document consumer, synthetic no-network ingress.

Only this fixture's case homes are mutated. This is isolated fixture evidence,
not runtime/Telegram/product acceptance. See RESULT.json for exact boundaries.
"""
from __future__ import annotations
import argparse, ast, asyncio, copy, dataclasses, datetime, hashlib, importlib, json
import os, pathlib, resource, shutil, subprocess, sys, time, types

BASE = pathlib.Path(__file__).resolve().parent
PINNED_N = pathlib.Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
UTC = datetime.timezone.utc
MSK = datetime.timezone(datetime.timedelta(hours=3))
KEY = 'ordinary_documents.v1'
DATA = b'isolated installed209 ordinary file fixture 20261113\n'
ROUTE = {'transport_profile':'fixture-profile', 'runtime_profile':'fixture-profile', 'bot_id':'91001',
         'source':{'platform':'telegram','chat_id':'91002','chat_type':'dm','user_id':'91003',
                   'thread_id':None,'message_id':'91004'}}

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(path, 'w', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush(); os.fsync(f.fileno())
    os.chmod(path, 0o600)

def digest(raw): return hashlib.sha256(raw).hexdigest()
def stamp(): return datetime.datetime.now(MSK).isoformat()

def setup():
    pins = []
    for rel in ('gateway/run_plugin_delivery.py','hermes_cli/plugins_state.py','hermes_cli/friday_native_state.py'):
        source = PINNED_N / rel
        raw = source.read_bytes()
        dest = BASE / 'exact' / rel
        dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        dest.write_bytes(raw); dest.chmod(0o600)
        pins.append({'source':str(source),'copy':str(dest),'sha256':digest(raw),'bytes':len(raw),'mode':'whole exact file'})
    extracts = [
        ('gateway/platforms/base.py', ('_platform_name','_thread_metadata_for_source','SendResult'),
         'from dataclasses import dataclass\nfrom typing import Any, Optional\n'),
        ('hermes_cli/plugins_manifest.py', ('_portable_slug','_portable_skill_namespace'), 'import hashlib\n')]
    for rel, names, header in extracts:
        raw = (PINNED_N / rel).read_bytes(); text = raw.decode(); lines = text.splitlines(keepends=True)
        tree = ast.parse(text); parts = []; ranges=[]
        for name in names:
            node = next(n for n in tree.body if getattr(n,'name',None)==name)
            first = min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])
            part = ''.join(lines[first-1:node.end_lineno]); parts.append(part)
            ranges.append({'symbol':name,'start_line':first,'end_line':node.end_lineno,'sha256':digest(part.encode())})
        dest = BASE/'exact'/rel; dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        dest.write_text(header+'\n\n'.join(parts)+'\n'); dest.chmod(0o600)
        pins.append({'source':str(PINNED_N/rel),'source_sha256':digest(raw),'copy':str(dest),
                     'copy_sha256':digest(dest.read_bytes()),'mode':'exact AST-selected source spans plus imports', 'spans':ranges})
    dump(BASE/'sourcepins.json', {'read_at_msk':stamp(),'files':pins})

def module(name, **members):
    mod=types.ModuleType(name); mod.__dict__.update(members); sys.modules[name]=mod; return mod

def boot(case, scenario):
    """Explicit synthetic home, admission, session and transport seams only."""
    import enum
    sys.path.insert(0,str(BASE/'exact'))
    home=case/'home'; home.mkdir(mode=0o700, parents=True,exist_ok=True)
    work=home/'workspace'; work.mkdir(mode=0o700,exist_ok=True)
    document=work/'fixture.txt'
    if not document.exists(): document.write_bytes(DATA); document.chmod(0o600)
    def assert_home(path):
        if pathlib.Path(path)!=home or home.resolve()!=home:
            raise PermissionError('fixture_home_mismatch')
    module('hermes_constants', get_hermes_home=lambda:home,
           assert_named_profile_home_live=assert_home,
           hermes_home_key=lambda p:str(pathlib.Path(p).resolve()))
    class Platform(enum.Enum): TELEGRAM='telegram'
    module('gateway.config',Platform=Platform)
    class SessionSource(types.SimpleNamespace):
        @classmethod
        def from_dict(cls,row):
            row=dict(row); row['platform']=Platform(row['platform']); return cls(**row)
    module('gateway.session',SessionSource=SessionSource)
    identity=types.SimpleNamespace(transport_inferred=False,runtime_home=home,
                                   runtime_profile='fixture-profile',transport_profile='fixture-profile')
    module('gateway.session_identity',restore_identity=lambda *a,**k:identity,
           canonical_identity=lambda *a,**k:identity,identity_of=lambda s:getattr(s,'identity',identity))
    class Cap:
        key='fixture-principal-20261113'; profile='fixture-profile'
        principal=('telegram','fixture-profile','91001','91003')
        cancelled=False; checks=0
        def check(self):
            self.checks+=1
            if self.cancelled: raise PermissionError('fixture_cap_cancelled')
    cap=Cap(); cap.home=home
    source=SessionSource.from_dict({**ROUTE['source'],'profile':'fixture-profile'})
    source._friday_document_route=copy.deepcopy(ROUTE)
    source._friday_document_session_id='fixture-session'
    source._friday_user_scope=cap
    current_source=source
    def workspace_document(path):
        cap.check(); p=pathlib.Path(path)
        if not p.is_absolute(): p=work/p
        if p.resolve()!=document or p.is_symlink(): raise PermissionError('fixture_workspace_boundary')
        return p.read_bytes(), 'fixture.txt'
    module('hermes_cli.friday_user_scope',current=lambda **k:cap,
           ordinary_file_source=lambda:current_source,workspace_document=workspace_document,
           guard_gateway_reply=lambda s,c:(c,False))
    module('gateway.run_attachment_presentation',original_document_name=lambda *a:None)
    from gateway.platforms.base import SendResult
    def event(kind, **extra):
        path=case/'events.jsonl'
        with open(path,'a',encoding='utf8') as f:
            f.write(json.dumps({'event':kind,'pid':os.getpid(),**extra},sort_keys=True)+'\n')
            f.flush(); os.fsync(f.fileno())
        os.chmod(path,0o600)
        fd=os.open(case,os.O_RDONLY|os.O_DIRECTORY); os.fsync(fd); os.close(fd)
    class Store:
        async def append_to_transcript(self,session_id,row):
            observation=row['display_metadata']['friday_file_delivery_observation']
            event('transcript',state=observation.get('state'), outcome=observation.get('outcome'))
            if observation.get('state')=='UNKNOWN':
                if scenario=='cut_after_reserve':
                    event('controlled_cut',phase='after_real_UNKNOWN_commit_return_before_transport'); os._exit(71)
                if scenario=='cancel_after_reserve': cap.cancelled=True
                if scenario=='owner_change_after_reserve': runner.owner='other-profile'
                if scenario=='route_change_after_reserve': source._friday_document_route['source']['message_id']='91999'
                if scenario=='cas_change_before_final':
                    from hermes_cli.plugins_state import PluginState
                    from hermes_cli.friday_native_state import observe_commit_return,require_commit_return
                    other=PluginState('friday_rework'); prior=other.get(KEY)
                    next_value=copy.deepcopy(prior); next_value['fixture_current_cas']='other-writer'
                    witness=other.set_commit(KEY,next_value,expected_value=prior,compare=True)
                    require_commit_return(other,observe_commit_return(other,witness))
                    event('competing_real_cas_commit')
    class Adapter:
        is_connected=True
        _bot=types.SimpleNamespace(id=91001)
        async def send_document_bytes(self,chat_id,data,*,file_name,caption,reply_to,metadata):
            check,route=metadata['_friday_document_authority']; check()
            proof={'kind':'document','sha256':digest(data),'bytes':len(data),'file_name':file_name,
                   'bot_id':route['bot_id'],'chat_id':chat_id,'thread_id':source.thread_id,
                   'reply_to':reply_to,'message_id':'92001'}
            event('fake_remote_accepted',receipt=proof)
            if scenario=='cut_after_remote':
                event('controlled_cut',phase='after_fake_remote_accept_before_ACK_return'); os._exit(72)
            if scenario=='missing_ack': return SendResult(success=False,error='fixture_lost_ack')
            if scenario=='bad_ack_route': proof['chat_id']='91999'
            return SendResult(success=True,message_id='92001',raw_response=proof)
        async def send(self,*a,**k):
            # Only the synthetic outcome transport for the real dispatcher.
            check,route=k['metadata']['_friday_document_outcome']; check()
            event('fake_status_accepted'); return SendResult(success=True,message_id='92002')
    adapter=Adapter()
    class Runner:
        _primary_profile_name='fixture-profile'; owner='fixture-profile'; authorized=True
        async_session_store=Store()
        def _served_profile_for_home(self,p): return 'fixture-profile' if p==home else None
        def _adapters_for_profile(self,p): return {Platform.TELEGRAM:adapter}
        def _delivery_adapter_for(self,s): return adapter
        def _owning_profile(self,a,p): return True,self.owner
        def _is_user_authorized_for_source(self,s,**k): return self.authorized
    runner=Runner(); adapter.gateway_runner=runner
    if scenario=='owner_mismatch': runner.owner='other-profile'
    if scenario=='route_mismatch': source._friday_document_route['source']['user_id']='91999'
    if scenario=='unauthorized': runner.authorized=False
    if scenario=='cancelled': cap.cancelled=True
    # Only asyncio's internal unbound AF_UNIX socketpair is allowed; all
    # network families, bind/connect/DNS operations remain forbidden.
    def audit(name,args):
        if name.startswith('socket.') and not (name=='socket.__new__' and args[1]==1):
            raise PermissionError('fixture_network_forbidden')
        if name in ('subprocess.Popen','os.system','os.posix_spawn'): raise PermissionError('fixture_nested_process_forbidden')
    sys.addaudithook(audit)
    return cap,source,adapter,runner,document,event

def flatten_error(exc):
    return {'type':type(exc).__name__,'message':str(exc),'primary':str(getattr(exc,'primary','')),
            'stage':getattr(exc,'stage',None),'replaced':getattr(exc,'replaced',None)}

def worker(case,scenario,action):
    os.umask(0o077)
    cap,source,adapter,runner,document,event=boot(case,scenario)
    import gateway.run_plugin_delivery as delivery
    from hermes_cli.plugins_state import PluginState
    from hermes_cli.friday_native_state import encoded
    guard=None
    if action=='recover':
        selection=digest(encoded([cap.key,'fixture.txt']))
        try:
            delivery._ordinary_prior_attempt(PluginState('friday_rework'),cap,selection,'fixture.txt',ROUTE)
            guard={'returned':True}
        except Exception as e: guard=flatten_error(e)
    elif action=='lose_current':
        state=PluginState('friday_rework')
        os.unlink(state.path)
        event('fixture_deleted_current_state_only')
        return {'done':'lost_current'}
    elif action=='retain_marker_only':
        state=PluginState('friday_rework')
        for p in state.data_dir.glob('friday-*.json'):
            row=json.loads(p.read_bytes())
            if not (row.get('schema')=='friday.ordinary-document-attempt.v1' and set(row)=={'schema','selection'}):
                p.unlink()
        state.path.unlink()
        event('fixture_retained_only_immutable_selection_marker')
        return {'done':'marker_only'}
    async def invoke():
        if action=='dispatch':
            got=[]
            handled=await delivery.deliver_ordinary_files(adapter,source,[str(document),str(document)],record_delivery=got.append)
            return {'handled':handled,'results':[dataclasses.asdict(r) for r in got]}
        result=await delivery.deliver_ordinary_document(adapter,source,str(document))
        return {'result':dataclasses.asdict(result),'actual_prior_history_guard':guard}
    output=asyncio.run(invoke())
    output['cap_checks']=cap.checks
    event('worker_return',result=output)
    return output

def snapshot(case):
    home=case/'home'
    state_paths=list(home.glob('plugin-data/*/state.json')) if home.exists() else []
    states=[]; journals=[]
    for p in state_paths:
        raw=p.read_bytes(); data=json.loads(raw)
        states.append({'sha256':digest(raw),'bytes':len(raw),'mode':oct(p.stat().st_mode&0o777),
                       'generation':data.get('__friday_native_state_v1',{}).get('generation'),
                       'ordinary':data.get(KEY)})
    for p in sorted(home.glob('plugin-data/*/friday-*.json')) if home.exists() else []:
        raw=p.read_bytes(); row=json.loads(raw)
        journals.append({'name':p.name,'sha256':digest(raw),'bytes':len(raw),'mode':oct(p.stat().st_mode&0o777),
                         'schema':row.get('schema'),'state':row.get('state'),
                         'route_present':'route' in row,'receipt_present':'receipt' in row,
                         'body_schema_valid':p.name.endswith('-'+digest(raw)+'.json')})
    events=[json.loads(s) for s in (case/'events.jsonl').read_text().splitlines()] if (case/'events.jsonl').exists() else []
    return {'states':states,'journals':journals,'events':events,
            'document_sends':sum(e['event']=='fake_remote_accepted' for e in events),
            'status_sends':sum(e['event']=='fake_status_accepted' for e in events)}

def main():
    started=time.monotonic(); started_msk=stamp(); os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024*1024,100*1024*1024))
    setup(); cases=[]; children=[]; failures=[]
    live=BASE/'cases'; live.mkdir(mode=0o700,exist_ok=True)
    def run(case_name,scenario,action='single',expect_code=0):
        if time.monotonic()-started>=285: raise TimeoutError('fixture_total_wall_budget')
        case=live/case_name; case.mkdir(mode=0o700,exist_ok=True)
        proc=subprocess.Popen([sys.executable,'-B',str(BASE/'harness.py'),'worker',str(case),scenario,action],
                              cwd=case,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        try: out,err=proc.communicate(timeout=min(20,290-(time.monotonic()-started)))
        except subprocess.TimeoutExpired:
            proc.kill(); out,err=proc.communicate(); raise
        children.append({'pid':proc.pid,'exit_code':proc.returncode,'reaped':True})
        row={'case':case_name,'scenario':scenario,'action':action,'pid':proc.pid,'exit_code':proc.returncode,
             'stdout':out.decode(),'stderr':err.decode(),'observed':snapshot(case)}
        if proc.returncode!=expect_code: failures.append({'unexpected_process_exit':row})
        if out:
            try: row['returned']=json.loads(out)
            except Exception: failures.append({'bad_worker_output':row})
        cases.append(row); return row
    def check(label,condition):
        if not condition: failures.append({'assertion':label})
        return {'check':label,'passed':bool(condition)}
    checks=[]
    def unknown(row):
        return len(row['observed']['states'])==1 and all(
            f['state']=='UNKNOWN' for f in row['observed']['states'][0]['ordinary']['files'].values())
    def fenced(row,send_count):
        ret=row.get('returned',{}); guard=ret.get('actual_prior_history_guard') or {}
        return ('delivery_requires_reconciliation' in (guard.get('message'),guard.get('primary'))
                and ret.get('result',{}).get('error')=='gateway_document_preflight_rejected'
                and row['observed']['document_sends']==send_count)
    for name,scenario,code,sends in [('before_transport','cut_after_reserve',71,0),('after_remote','cut_after_remote',72,1)]:
        cut=run(name,scenario,expect_code=code)
        checks.append(check(name+'_durable_unknown_at_cut',unknown(cut) and len(cut['observed']['journals'])==3
                            and cut['observed']['document_sends']==sends))
        recovered=run(name,'healthy','recover')
        checks.append(check(name+'_fresh_process_prior_guard_no_resend',fenced(recovered,sends) and recovered['pid']!=cut['pid']))
    healthy=run('healthy','healthy','dispatch')
    hr=healthy.get('returned',{})
    checks.append(check('real_dispatch_deduplicates_and_confirms_receipt',hr.get('handled') is True
                        and len(hr.get('results',[]))==1 and hr['results'][0]['success'] is True
                        and healthy['observed']['document_sends']==1
                        and len(healthy['observed']['journals'])==4))
    replay=run('healthy','healthy','recover')
    checks.append(check('healthy_same_ingress_replay_fenced_without_resend',fenced(replay,1)))
    run('after_remote','healthy','lose_current')
    lost=run('after_remote','healthy','recover')
    checks.append(check('lost_current_state_real_immutable_history_fences_replay',fenced(lost,1) and not lost['observed']['states']))
    run('before_transport','healthy','retain_marker_only')
    marker=run('before_transport','healthy')
    checks.append(check('lost_current_row_selection_marker_only_fences_replay',
                        marker.get('returned',{}).get('result',{}).get('error')=='gateway_document_preflight_rejected'
                        and marker['observed']['document_sends']==0 and not marker['observed']['states']
                        and len(marker['observed']['journals'])==1))
    for scenario in ('owner_mismatch','route_mismatch','unauthorized','cancelled'):
        row=run(scenario,scenario)
        checks.append(check(scenario+'_preflight_no_effect',row.get('returned',{}).get('result',{}).get('error')=='gateway_document_preflight_rejected'
                            and row['observed']['document_sends']==0 and not row['observed']['states']))
    for scenario in ('cancel_after_reserve','owner_change_after_reserve','route_change_after_reserve'):
        row=run(scenario,scenario)
        checks.append(check(scenario+'_retains_unknown_without_transport',unknown(row) and row['observed']['document_sends']==0
                            and not row.get('returned',{}).get('result',{}).get('success')))
    for scenario in ('missing_ack','bad_ack_route','cas_change_before_final'):
        row=run(scenario,scenario)
        checks.append(check(scenario+'_remote_accepted_but_unknown',unknown(row) and row['observed']['document_sends']==1
                            and row.get('returned',{}).get('result',{}).get('error')=='document_delivery_UNKNOWN'))
        recovery=run(scenario,'healthy','recover')
        checks.append(check(scenario+'_recovery_no_resend',fenced(recovery,1)))
    # Preserve nonsensitive metadata and exact source/harness; remove own case state,
    # immutable journals, workspace bytes and fake transport files after capture.
    dump(BASE/'observations.json',cases)
    disk_before=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    shutil.rmtree(live)
    usage=resource.getrusage(resource.RUSAGE_CHILDREN); own=resource.getrusage(resource.RUSAGE_SELF)
    result={'assignment':'SOL-T40-R02-FILE-CONSUMER-FIXTURE-20261113#1',
            'status':'ISOLATED_REAL_FILE_CONSUMER_FIXTURE_PASS' if not failures else 'FAIL',
            'runtime_pass':False,'started_msk':started_msk,'finished_msk':stamp(),'elapsed_seconds':time.monotonic()-started,
            'checks':checks,'failures':failures,'sourcepins':'sourcepins.json','observations':'observations.json',
            'real_consumers':['complete installed gateway.run_plugin_delivery (unmodified selective file)',
                 'deliver_ordinary_files -> deliver_ordinary_document -> _ordinary_authority/resolve_document_route',
                 '_ordinary_prior_attempt -> RetainedStateTransaction -> immutable history',
                 '_begin_ordinary_document -> _ordinary_commit -> real PluginState/native set_commit',
                 'deliver_document and ACK proof checks -> final real CAS commit'],
            'synthetic_seams':['hermes home/config liveness constrained to unique fixture home',
                'Platform/SessionSource and identity lookup are in-process synthetic Telegram-shaped objects',
                'current/ordinary_file_source/workspace_document are declared synthetic admission/capability seams',
                'runner profile/owner/authorization/adapter registry and async_session_store are synthetic',
                'fake send_document_bytes records fsynced local remote-accepted event then returns exact synthetic ACK',
                'original_document_name returns None; actual extracted SendResult/thread metadata/portable namespace functions are exact source spans',
                'fault injection only in synthetic transcript/transport callbacks, no product code replaced'],
            'limitations':['No runtime HOME/API/Store/liveDB or service invoked; no network/model/Telegram/Office/producer/install/publication',
                'Initial harness blocked asyncio internal AF_UNIX socketpair before consumer execution; preserved INITIAL-HARNESS-ERROR-RESULT.json and initial-harness-error-observations.json; corrected audit permits only unbound AF_UNIX allocation',
                'SIGKILL/power loss and filesystem crash persistence are not tested: controlled os._exit occurs after real fsync/commit return',
                'Capability revocation and route registry changes are synthetic; actual file history/CAS/custody code executes',
                'No runtime managed-ingress or public fallback acceptance asserted'],
            'bounds':{'cpu_seconds_limit':120,'wall_seconds_limit':300,'address_space_bytes':512*1024*1024,
                'file_size_limit_bytes':100*1024*1024,'actual_total_cpu_seconds':usage.ru_utime+usage.ru_stime+own.ru_utime+own.ru_stime,
                'disk_before_cleanup_bytes':disk_before,'max_child_rss_kib':usage.ru_maxrss},
            'cleanup':{'case_trees_removed':not live.exists(),'children':children,'all_children_reaped':all(c['reaped'] for c in children),
                'kept':['harness.py','exact selective source copies','sourcepins.json','observations.json','RESULT.json']}}
    dump(BASE/'RESULT.json',result)
    print(json.dumps({'status':result['status'],'checks':len(checks),'failures':len(failures),
                      'elapsed_seconds':result['elapsed_seconds'],'result':str(BASE/'RESULT.json')}))
    return 0 if not failures else 1

def recheck_existing():
    """Correct only guard-envelope checker; no consumer, process, send or state effect."""
    original=json.loads((BASE/'RESULT.json').read_text())
    cases_raw=(BASE/'observations.json').read_bytes()
    cases=json.loads(cases_raw)
    if original['status']!='FAIL': raise ValueError('recheck_requires_original_failure')
    expected={
        'before_transport_fresh_process_prior_guard_no_resend':('before_transport',0),
        'after_remote_fresh_process_prior_guard_no_resend':('after_remote',1),
        'healthy_same_ingress_replay_fenced_without_resend':('healthy',1),
        'lost_current_state_real_immutable_history_fences_replay':('after_remote',1),
        'missing_ack_recovery_no_resend':('missing_ack',1),
        'bad_ack_route_recovery_no_resend':('bad_ack_route',1),
        'cas_change_before_final_recovery_no_resend':('cas_change_before_final',1)}
    failures=original['failures']
    if set(f.get('assertion') for f in failures)!=set(expected):
        raise ValueError('unexpected_failure_must_not_relabel')
    for entry in original['checks']:
        if entry['check'] not in expected: continue
        name,sends=expected[entry['check']]
        matches=[c for c in cases if c['case']==name and c['action']=='recover']
        if entry['check']=='lost_current_state_real_immutable_history_fences_replay':
            row=matches[-1]
            if row['observed']['states']: raise ValueError('lost_current_not_demonstrated')
        else: row=matches[0]
        ret=row['returned']; guard=ret['actual_prior_history_guard']
        if not (guard['type']=='NativeCommitUncertain' and guard['stage']=='LOCKED'
                and guard['replaced'] is False and guard['primary']=='delivery_requires_reconciliation'
                and ret['result']['error']=='gateway_document_preflight_rejected'
                and row['observed']['document_sends']==sends):
            raise ValueError('real_guard_or_no_resend_not_demonstrated')
        entry['passed']=True
        entry['corrected_checker_accepts_actual_native_envelope']=True
    (BASE/'RESULT.json').rename(BASE/'INITIAL-ENVELOPE-CHECKER-ERROR-RESULT.json')
    original['status']='ISOLATED_REAL_FILE_CONSUMER_FIXTURE_PASS'
    original['failures']=[]
    original['checker_correction']={
        'reason':'NativeCommitUncertain wraps the deliberate delivery_requires_reconciliation primary error under real native lock',
        'original_result':'INITIAL-ENVELOPE-CHECKER-ERROR-RESULT.json',
        'observations_unchanged_sha256':digest(cases_raw),
        'rechecked_msk':stamp(),'repeated_consumer_processes':0,'repeated_transport_effects':0,
        'method':'--recheck-existing'}
    original['finished_msk']=stamp()
    original['harness_sha256']=digest(pathlib.Path(__file__).read_bytes())
    dump(BASE/'RESULT.json',original)
    print(json.dumps({'status':original['status'],'checks':len(original['checks']),
                      'observations_sha256':digest(cases_raw),'repeated_transport_effects':0}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':
        try: print(json.dumps(worker(pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4]),sort_keys=True))
        except Exception as e:
            print(json.dumps({'unhandled':flatten_error(e)},sort_keys=True)); raise
    elif len(sys.argv)>1 and sys.argv[1]=='--recheck-existing': recheck_existing()
    else: sys.exit(main())
