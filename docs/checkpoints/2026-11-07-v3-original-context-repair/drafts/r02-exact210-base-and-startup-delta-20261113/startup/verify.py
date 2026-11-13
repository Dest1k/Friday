"""Evaluate saved observations, without repeating their synthetic effects."""
import ast, hashlib, json
from pathlib import Path
R=Path(__file__).resolve().parent
before=json.loads((R/'PROBES-before.json').read_text())
after=json.loads((R/'PROBES-after.json').read_text())
b={s['scenario']:s for s in before['scenarios']}
a={s['scenario']:s for s in after['scenarios']}
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
    assert value,name
key='own:telegram:answered'
for name in ['open_failure','commit_failure']:
    x,y=b[name],a[name]
    check(name+' original linked regeneration and second identical accepted payload',
          len(x['startup_generations'])==1 and len(x['effects'])==2
          and x['effects'][0]==x['effects'][1] and len(x['after_start'])==2
          and len({r['id'] for r in x['after_start']})==2)
    check(name+' fixed no regeneration/no second send/no replacement',
          not y['startup_generations'] and len(y['effects'])==1
          and y['after_start']==y['before'])
    check(name+' fixed marker and unknown fence retained/reconnect still withheld',
          y['session_flags_after_start'][key] and y['fence_failed']
          and not y['clears'] and y['reconnect_scheduled']==0)
for name in ['healthy_uncertain','terminal']:
    check(name+' unchanged terminal/uncertainty no regeneration no resend',
          len(a[name]['effects'])==len(b[name]['effects'])==1
          and not a[name]['startup_generations'] and not b[name]['startup_generations'])
for name in ['pending','proved_unsent']:
    check(name+' both variants send original exactly once without model',
          len(a[name]['effects'])==len(b[name]['effects'])==1
          and not a[name]['startup_generations'] and not b[name]['startup_generations']
          and a[name]['after'][0]['state']==b[name]['after'][0]['state']=='delivered'
          and a[name]['after'][0]['attempts']==b[name]['after'][0]['attempts']==1)
    check(name+' original route/profile/body retained',all(a[name]['after'][0][k]==a[name]['before'][0][k]
          for k in ['id','session','platform','chat','thread','profile','content']))
x,y=b['pending_open_failure'],a['pending_open_failure']
check('pending fault did not fake an unsent proof or clear resume marker',
      len(x['effects'])==1 and not y['effects'] and y['after']==y['before']
      and y['after'][0]['state']=='pending' and y['session_flags_after_start'][key]
      and y['fence_failed'] and not y['clears'])
for name in ['unrelated_unanswered','ledger_disabled']:
    check(name+' fresh unchanged automatic normal path',
          len(a[name]['effects'])==len(b[name]['effects'])==1
          and len(a[name]['startup_generations'])==len(b[name]['startup_generations'])==1
          and not a[name]['fence_failed'])
check('fresh explicit-off really used actual disabled ledger gate',
      a['ledger_disabled']['before']==a['ledger_disabled']['after']==[])
y=a['unrelated']
check('failed sweep leaves unrelated Slack auto-resume and new ordinary Telegram final operational',
      y['startup_generations']==[{'platform':'slack','session':'own:slack:unanswered'}]
      and y['ordinary_new_final_success'] and len(y['effects'])==3
      and y['session_flags_after_start'][key] and y['fence_failed'])
y=a['open_failure_recovered']
check('only later successful full recovery clears failed latch and suppresses answered generation',
      y['recovery']=={'claimed':1,'scheduled':1,'fence_failed':False}
      and y['all_generations']==[{'platform':'telegram','session':'own:telegram:independent'}]
      and not y['session_flags_final'][key] and len(y['effects'])==2)
y=a['explicit_off_after_fault']
check('explicit off cannot clear previously established recovery uncertainty',
      y['explicit_off_after_fault']=={'fence_failed':True,'scheduled':0}
      and len(y['effects'])==1 and y['session_flags_final'][key])
check('all raw observations integral DELETE journal with own DB removed',
      all(s['db']=={'journal_mode':'delete','integrity':'ok'} and s['own_db_removed']
          for s in before['scenarios']+after['scenarios']))
changed=[]; pins=[]
for old in sorted((R/'before').rglob('*.py')):
    rel=old.relative_to(R/'before');new=R/'after'/rel
    if old.read_bytes()!=new.read_bytes():changed.append(str(rel))
    for v,path in [('before',old),('after',new)]:
        ast.parse(path.read_text())
        pins.append({'variant':v,'path':str(rel),'bytes':path.stat().st_size,
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
check('only run_startup source changed',changed==['gateway/run_startup.py'])
trees=[ast.parse((R/v/'gateway/run_startup.py').read_text()) for v in ['before','after']]
methods=[]
for tree in trees:
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GatewayStartupMixin')
    methods.append({n.name:ast.dump(n,include_attributes=False) for n in cls.body
                    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))})
changed_methods=[name for name in methods[0] if methods[0][name]!=methods[1][name]]
check('only claim and schedule methods changed',set(changed_methods)=={
      '_claim_pending_obligations','_schedule_resume_pending_sessions'})
result={'schema':'frw.r02.startup-sweep-focused-controls.v1','checks':checks,
        'source_pins':pins,'changed_methods':changed_methods,
        'credit':'Source-only saved observation evaluation; no live/product/global PASS',
        'journal_mode':'delete; original WAL description corrected in EVIDENCE-DESCRIPTION-CORRECTION.json',
        'terminal_limit':'Normal terminal has resume_pending=False; stale terminal marker is not qualified.'}
(R/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'all_passed':all(c['passed'] for c in checks),
                 'changed_source':changed,'changed_methods':changed_methods}))
