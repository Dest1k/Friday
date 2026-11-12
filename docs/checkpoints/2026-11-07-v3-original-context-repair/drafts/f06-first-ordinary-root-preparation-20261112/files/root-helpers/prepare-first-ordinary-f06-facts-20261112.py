"""Root private bulk preparation, readonly observation; no grant/clock/send."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import types

os.umask(0o077)
U=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY207-ROOT-BINDING-SOURCE-20261112')
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
G6=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112/operations/generate-g6')
RUN='f06-first-docx-wrong-read-20261112-r1'
def raw(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def ref(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def put(p,v):
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:
        f.write(raw(v));f.flush();os.fsync(f.fileno())
    return ref(p)
def load(p,name):
    m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
    O.mkdir(mode=0o700);(O/'work').mkdir(mode=0o700);(O/'bootstrap').mkdir(mode=0o700)
    a=load(U/'f06_source.py','f06_bulk_source');check=load(U/'current207.py','f06_bulk_current')
    assert not (check.STATE/'runs'/(RUN+'.json')).exists()
    source=Path(a.SOURCE['path']);assert ref(source)==a.SOURCE
    st=source.stat();assert st.st_uid==os.getuid() and st.st_nlink==1 and stat.S_ISREG(st.st_mode)
    pin=dict(device=st.st_dev,inode=st.st_ino,size_bytes=st.st_size,uid=st.st_uid,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns)
    credential=G6/'inputs/credential.private.json';before=ref(credential)
    assert stat.S_IMODE(credential.stat().st_mode)==0o600
    correct=json.loads(credential.read_bytes())['password']
    wrong='f06-wrong-'+secrets.token_hex(12)
    assert wrong!=correct and wrong not in correct and correct not in wrong
    scenario=a.construct_scenario(supplied_password=wrong,input_pin=dict(a.SOURCE,stat=pin,filename=source.name,mime_type=a.MIME,kind='document'))
    # SOURCE uses bytes for provenance, scenario input intentionally has no bytes key.
    scenario['steps'][0]['input'].pop('bytes',None);a.scenario_shape(scenario)
    sref=put(O/'SCENARIO.private.json',scenario)
    assert ref(credential)==before
    put(O/'CREDENTIAL-SELECTION.json',dict(schema='friday.root.F06.wrong-private-selection.v1',operator='Root',selected_wrong_compared_privately_to_retained_correct=True,credential_ref=before,values_exported=False,source=a.SOURCE,scenario=sref))
    closure=json.loads(check.CLOSURE.read_bytes())
    placeholders={k:put(O/'bootstrap'/(k+'.json'),{'status':'UNBOUND_OBSERVATION_ONLY','proof_key':k}) for k in sorted(a.PROOFS)}
    clock=put(O/'bootstrap/CLOCK.NOT_STARTED.json',dict(schema='frw.Root.F06.original-finite-clock.v1',status='NOT_STARTED_NO_EXECUTION_RIGHT'))
    wait=put(O/'bootstrap/WAIT.NOT_GRANTED.json',{'status':'UNBOUND_NO_ACTOR'})
    c=a.unbound();c.update(run_id=RUN,scenario_ref=sref,scenario_sha256=sref['sha256'],adapter=ref(U/'f06_source.py'),footer=ref(U/'f06_footer.py.txt'),actual_root_B_checker=ref(U/'current207.py'),product=check.EXPECTED,root_proofs=placeholders)
    c['resources']=dict(a.TIMING,cpu_seconds=120,max_rss_bytes=1024**3,disk_bytes=32*1024**2,clock=clock,owned_parent_wait_cleanup=wait)
    c['boundary']={k:'0'*64 for k in a.BOUNDARY};c['boundary'].update(gateway={},B=dict(profile='telegram-bot-8812646969',session_id=check.SID,session_key=check.KEY,native_max_id=0),phase_unconsumed=True,uploads_this_operation=1,producer_calls=0,restarts=0)
    p=check.unbound_proof();p.update(contract_effect=a.effect(c),whole_effect_sha256=a.digest(a.encoded(a.effect(c))),installation_closure=ref(check.CLOSURE),installation_acceptance=closure['source_acceptance'])
    obs=check.observe(p)
    oref=put(O/'OBSERVED-BULK-FACTS.json',obs)
    historical=[];matching=[];protected=[]
    for run_id in obs['history']['run_ids']:
        row=json.loads((check.STATE/'runs'/(run_id+'.json')).read_bytes())
        created=dt.datetime.fromisoformat(row['created_at']).timestamp()
        steps=row.get('scenario',{}).get('steps',[])
        files=[{'filename':step.get('input',{}).get('filename'),'sha256':step.get('input',{}).get('sha256'),'kind':step.get('input',{}).get('kind')} for step in steps if step.get('input')]
        # Full captions are examined only in this private process and never copied.
        has_selected_name=any(source.name in str(step.get('request','')) or source.name in str(step.get('input',{}).get('caption','')) for step in steps)
        same_sha=any(f['sha256']==a.SOURCE['sha256'] for f in files)
        if same_sha or has_selected_name:matching.append(run_id)
        if 'f06' in run_id.lower() or any(str(f['filename']).lower().endswith(('.docx','.xlsx','.pptx','.odt','.ods','.odp')) for f in files):
            protected.append(dict(id=run_id,created=row['created_at'],status=row.get('status'),files=files))
        historical.append(dict(id=run_id,created_at=row['created_at'],created_epoch=created,status=row.get('status'),predates_source=created<st.st_mtime_ns/1e9))
    database_times={}
    for label,path in check.DATABASES.items():
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
        count,maximum,last=db.execute('SELECT count(*),max(id),max(timestamp) FROM messages').fetchone();db.close()
        database_times[label]=dict(count=count,max_id=maximum,last_timestamp=last,last_before_g6=last<st.st_mtime_ns/1e9)
    assert len(historical)==512 and matching==[] and all(v['predates_source'] for v in historical) and all(v['last_before_g6'] for v in database_times.values())
    put(O/'HISTORY-LINEAGE-BULK-FACTS.json',dict(schema='friday.root.F06.retained-g6-history-bulk.v1',observed=oref,source=a.SOURCE,source_identity=pin,source_file_created_mtime_epoch=st.st_mtime_ns/1e9,all_512=historical,source_exact_or_selected_filename_matches=matching,office_or_f06_candidates=protected,all_three_database_metadata=database_times,no_global_unlogged_absence_claim=True,projection_limit=check.LIMIT,prior_history_basis=ref(B/'F06-ORDINARY-DOCX-ROOT-PREPARATION-20261112/RESULT.json'),g6_original_custody=ref(G6/'ROOT-G6-SEVEN-CIPHERTEXT-AND-CLOSURE.json')))
    put(O/'BULK-CONTRACT-UNBOUND.json',c)
    print(json.dumps(dict(state='BULK_FACTS_COLLECTED_NO_GRANT_NO_CLOCK_NO_SEND',source=a.SOURCE,observation=oref,canonical_runs=len(historical),matching_sources=matching,all3_last_ingress_before_g6=True,office_or_f06_candidate_count=len(protected),ordinary_operations_started=0)))
if __name__=='__main__':main()
