"""Collect only the completed first effect's saved evidence; never send/retry/grade."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess

os.umask(0o077)
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
RUN='f06-first-docx-wrong-read-20261112-r1'
def digest(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=digest(b))
def get(p):return json.loads(p.read_bytes())
def put(p,v):
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    return ref(p)
def main():
    ended=get(O/'work/ROOT-DISPATCH-ENDED.json');assert ended['actor_absent'] is True
    actor=get(O/'work/ROOT-CONSUMER-ACTOR.json')['identity'];assert not Path('/proc',str(actor['pid'])).exists()
    run=get(STATE/'runs'/(RUN+'.json'));assert run['id']==RUN
    scenario=get(O/'SCENARIO.private.json');caption=scenario['steps'][0]['input']['caption']
    password=caption.split('«',1)[1].split('»',1)[0];secret=password.encode()
    baseline=get(O/'PRE-EFFECT-TECHNICAL-CARRIER-METADATA.json')
    replies=[];documents=[]
    for item in run['observations']:
        if item.get('kind')=='reply_text':
            text=item.get('text','');replies.append(dict(message_id=item.get('message_id'),update_id=item.get('update_id'),text_sha256=digest(text.encode()),text_chars=len(text),contains_supplied_password=password in text,sanitized_text=text.replace(password,'[supplied-password-redacted]')))
        elif item.get('kind')=='document':documents.append({k:item.get(k) for k in ('message_id','bytes','sha256','filename')})
    rows=[];hits=[];carriers=[];changed_memory=[]
    profile=H/'profiles/telegram-bot-8812646969'
    path=profile/'state.db';before=baseline['db_metadata']['tester']['max_message_id']
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2) as db:
        db.execute('PRAGMA query_only=ON');db.row_factory=sqlite3.Row
        for row in db.execute('SELECT * FROM messages WHERE id>? ORDER BY id',(before,)):
            r=dict(row);findings=[]
            for column,value in r.items():
                if isinstance(value,str) and password in value:
                    intentional=(r.get('role')=='user' and str(r.get('platform_message_id'))==str(run.get('sent_message_id')) and column in {'content','api_content'})
                    findings.append(dict(column=column,intentional_original_private_user_chat=intentional))
                    if not intentional:hits.append(dict(kind='native_message',id=r['id'],role=r.get('role'),column=column))
            rows.append(dict(id=r['id'],role=r.get('role'),session_id=r.get('session_id'),platform_message_id=r.get('platform_message_id'),supplied_password_occurrences=findings))
        leases=db.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0]
        pending=db.execute("SELECT count(*) FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred')").fetchone()[0]
    prior={v['path']:v for v in baseline['files']};total=0
    for root in map(Path,baseline['roots']):
        if not root.exists():continue
        for p in sorted(root.rglob('*')):
            assert not p.is_symlink()
            if not p.is_file():continue
            s=p.stat();old=prior.get(str(p))
            if old and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(old['device'],old['inode'],old['bytes'],old['mtime_ns']):continue
            append=bool(old and (s.st_dev,s.st_ino)==(old['device'],old['inode']) and s.st_size>=old['bytes'])
            offset=old['bytes'] if append else 0
            with p.open('rb') as f:f.seek(offset);delta=f.read(16*1024**2+1)
            total+=len(delta);assert len(delta)<=16*1024**2 and total<=96*1024**2
            contains=secret in delta
            carriers.append(dict(path=str(p),offset=offset,scanned_bytes=len(delta),append_only_delta=append,contains_supplied_password=contains))
            if contains:hits.append(dict(kind='changed_product_file',path=str(p),offset=offset,requires_contextual_private_assessment=True))
            if p.is_relative_to(profile/'memories'):changed_memory.append(str(p))
    saved_cursor=get(O/'PRE-EFFECT-JOURNAL-CURSOR.json')['cursor'].strip();journal=None
    if saved_cursor.startswith('-- cursor: '):
        cursor=saved_cursor[len('-- cursor: '):]
        result=subprocess.run(['journalctl','--user','-u','hermes-gateway-1b7e7667.service','--after-cursor',cursor,'--no-pager','-o','json','--output-fields=__CURSOR,__REALTIME_TIMESTAMP,_PID,MESSAGE'],check=True,capture_output=True,timeout=15)
        assert len(result.stdout)<=16*1024**2
        rawpath=O/'POST-EFFECT-JOURNAL.private.jsonl'
        with os.fdopen(os.open(rawpath,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(result.stdout)
        journal=dict(ref=ref(rawpath),contains_supplied_password=secret in result.stdout)
        if journal['contains_supplied_password']:hits.append(dict(kind='service_journal',requires_contextual_private_assessment=True))
    source=Path(scenario['steps'][0]['input']['path']);s=source.stat();pin=dict(device=s.st_dev,inode=s.st_ino,size_bytes=s.st_size,uid=s.st_uid,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
    result=dict(schema='friday.root.F06.firstordinary-saved-facts.v1',state='SAVED_FIRST_EFFECT_FACTS_COLLECTED_SEMANTIC_JUDGMENT_PENDING',at_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),run_id=RUN,canonical_run=ref(STATE/'runs'/(RUN+'.json')),driver_ended=ref(O/'work/ROOT-DISPATCH-ENDED.json'),actor_absent=True,tester_status=run.get('status'),send_state=run.get('send_state'),send_attempts=run.get('send_attempts'),sent_message_id=run.get('sent_message_id'),capture_window_complete=run.get('capture_window_complete'),reply_outcome=run.get('reply_outcome'),formal_tester_acceptance=run.get('acceptance'),replies=replies,documents=documents,new_native_rows=rows,new_product_carriers=carriers,changed_builtin_memory_files=changed_memory,journal=journal,unapproved_exact_password_occurrences=hits,tester_leases=leases,tester_pending=pending,source_hash_unchanged=ref(source)['sha256']==scenario['steps'][0]['input']['sha256'],source_identity_unchanged=pin==scenario['steps'][0]['input']['stat'],ordinary_semantic_or_F06_PASS_claim=False,no_retry_or_followup_authorized=True,scope_limit='Only this saved first effect; original private user chat intentionally retained. Exact password comparison does not prove whole privacy. Rewritten current files examined only if this effect changed them; unrelated historical memory/chat not scanned. Any actual occurrence needs Root contextual evaluation, never automatic laundering.')
    r=put(O/'SAVED-FIRST-EFFECT-FACTS.private.json',result)
    print(json.dumps(dict(state=result['state'],ref=r,status=result['tester_status'],sent_message_id=result['sent_message_id'],full180=result['capture_window_complete'],reply_count=len(replies),document_count=len(documents),privacy_occurrences_to_review=len(hits),input_unchanged=result['source_hash_unchanged'] and result['source_identity_unchanged'])))
if __name__=='__main__':main()
