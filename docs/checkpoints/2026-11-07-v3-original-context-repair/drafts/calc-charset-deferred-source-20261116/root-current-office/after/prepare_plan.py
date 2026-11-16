"""Bind one future actual plan to reviewed static source; no grant or actor."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,os,secrets,importlib.util,sys,time,argparse
os.umask(0o077)
B=Path(__file__).resolve().parent
S=Path('/home/jericho/.cache/FRW-ASTRA-CHARSET-CURRENT-OFFICE-SOURCE-COMPOSITION-20261116')
F=Path('/home/jericho/.cache/FRW-ASTRA-MAPPED-BOOTSTRAP-OFFICE-M-ROOT-20261116')
L=Path('/home/jericho/.cache/FRW-ASTRA-OWNC-LOCALE-LANGUAGE-ACTUAL-20261116-887c410232d4')
A=Path('/home/jericho/.cache/FRW-ASTRA-MAPPED-BOOTSTRAP-ROOT-QUALIFICATION-20261116')
P=Path('/home/jericho/.cache/FRW-ASTRA-CURRENT-OFFICE-M-ROOT-20261116')
E=Path('/home/jericho/.cache/FRW-ASTRA-EXTRA-FORK-WORKER-ROOT-QUALIFICATION-20261116')
OLD_SOURCE=Path('/home/jericho/.cache/FRW-ASTRA-LOCALE-CONTRACT-FINAL-COMPOSITION-20261116')
NIL=Path('/home/jericho/.cache/FRW-ASTRA-CFB4-RETAINED-CONFIG-SOURCE-20261116')
OBSROOT=Path('/home/jericho/.cache/FRW-ASTRA-LOCALE-OFFICE-M-ROOT-20261116')
assert os.environ.get('FRW_CHARSET_FRESH_FORK_PID')==str(os.getpid()) and os.environ.get('FRW_CHARSET_FRESH_FORK_PARENT')==str(os.getppid()), 'fresh_non_tail_fork_launcher_required'
assert B != S, 'copy_callers_to_fresh_Root_target_not_frozen_Source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':str(p),'sha256':sha(p)}
def put(p,value):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:
  json.dump(value,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return ref(p)
parser=argparse.ArgumentParser(description='Root-only exact locale Source acceptance and OwnC closure pins; no default approval')
parser.add_argument('--root-source-accepted',required=True)
parser.add_argument('--root-source-accepted-sha256',required=True)
parser.add_argument('--root-locale-closed',required=True)
parser.add_argument('--root-locale-closed-sha256',required=True)
parser.add_argument('--root-nil-source-accepted',required=True)
parser.add_argument('--root-nil-source-accepted-sha256',required=True)
parser.add_argument('--root-charset-source-accepted',required=True)
parser.add_argument('--root-charset-source-accepted-sha256',required=True)
parser.add_argument('--decide-one-new-missing-m-operation',action='store_true',required=True)
args=parser.parse_args()
assert args.decide_one_new_missing_m_operation
for pin in (args.root_source_accepted_sha256,args.root_locale_closed_sha256):assert len(pin)==64 and all(c in '0123456789abcdef' for c in pin)
source_accepted=Path(args.root_source_accepted);locale_closed=Path(args.root_locale_closed)
assert sha(source_accepted)==args.root_source_accepted_sha256
assert sha(locale_closed)==args.root_locale_closed_sha256
nil_source_accepted=Path(args.root_nil_source_accepted)
assert len(args.root_nil_source_accepted_sha256)==64 and all(c in '0123456789abcdef' for c in args.root_nil_source_accepted_sha256)
assert sha(nil_source_accepted)==args.root_nil_source_accepted_sha256
charset_source_accepted=Path(args.root_charset_source_accepted)
assert len(args.root_charset_source_accepted_sha256)==64 and all(c in '0123456789abcdef' for c in args.root_charset_source_accepted_sha256)
assert sha(charset_source_accepted)==args.root_charset_source_accepted_sha256
assert ref(nil_source_accepted)=={'path':'/home/jericho/.cache/FRW-ASTRA-NIL-OFFICE-M-ROOT-20261116/ROOT-NIL-OFFICE-SOURCE-ACCEPTED.json','sha256':'69bcac5da74d126db039c45345ef1848c529f7bbb8e0beaad1e1b7b2e3edb4b9'}
def validate_charset_acceptance(value):
 assert value['schema']=='frw.Root.charset-current-office-source-composition-accepted.v1'
 assert value['state']=='ROOT_ACCEPTED_EXACT_COHERENT_SOURCE_ONLY'
 for key,name in [('candidate_freeze','CANDIDATE-FREEZE.json'),('composition','SOURCE-COMPOSITION.json'),('source_freeze','SOURCE-FREEZE.json'),('caller_input','source-inputs/FINAL-CALLER-SOURCE-INPUT-R2.json')]:assert value[key]==ref(S/name)
validate_charset_acceptance(json.loads(charset_source_accepted.read_text()))
prior_cfb4=OBSROOT/'ROOT-CURRENT-OFFICE-CFB4-FONT-QUALIFIER-REFUSAL-CLOSED.json'
observability_accepted=OBSROOT/'ROOT-CFB4-CONSTANT-CODE-OBSERVABILITY-SOURCE-ACCEPTED.json'
resolver_accepted=NIL/'ROOT-NIL-RESOLVER-SOURCE-ACCEPTED.json'
assert sha(prior_cfb4)=='2642ef74526e894c1e1aae2f1bb50e9b3573a5fdac49c14f36383aefb7e1a683'
assert sha(observability_accepted)=='96d6f88981d0c1d7267024b8b7a28dc98c9e4702e01fb49c187560eefd09857c'
assert sha(resolver_accepted)=='1f84f51f2d3260132ad02f650785378a67aaea4281be10bfbdf34e1d4bd854d0'
cfb4_closed=json.loads(prior_cfb4.read_text())
assert cfb4_closed['state']=='CONSUMED_CLOSED_REFUSED_QUALIFY_AND_QUERY_BEFORE_METRIC' and cfb4_closed['actual_M'] is None and cfb4_closed['ONCE_clock']=='CONSUMED_CLOSED_NEVER_REPLAY'
assert cfb4_closed['after_exact_unit']['Id']=='frw-calc-cfb470402bdda1ff49212f7280cb5973.service'
assert cfb4_closed['after_exact_unit']['LoadState']=='not-found' and cfb4_closed['after_exact_unit']['MainPID']=='0' and cfb4_closed['after_exact_unit']['ControlGroup']==''
prior_0b33=Path('/home/jericho/.cache/FRW-ASTRA-NIL-OFFICE-M-ROOT-20261116/ROOT-NIL-OFFICE-0B33-CHARSET-REFUSAL-CLOSED.json')
charset_twofile_accepted=Path('/home/jericho/.cache/FRW-ASTRA-CHARSET-ROUNDTRIP-SOURCE-GAP-20261116/ROOT-CHARSET-TWOFILE-SOURCE-ACCEPTED.json')
assert sha(prior_0b33)=='98b650bdd15c89c6b3d10915b377f8ca99696759b47689e4ee9d6693c81d46e3'
assert sha(charset_twofile_accepted)=='a27c60a8fbe21092b5f74efe3f576dbe73d2d589e7d61df7e5c82469fe6b70b2'
closed_0b33=json.loads(prior_0b33.read_text())
assert closed_0b33['state']=='CONSUMED_CLOSED_REFUSED_QUALIFY_AND_QUERY_BEFORE_METRIC' and closed_0b33['actual_M'] is None and closed_0b33['ONCE_clock']=='CONSUMED_CLOSED_NEVER_REPLAY'
assert closed_0b33['after_exact_unit']=={'Id':'frw-calc-0b33288a0038d5cdefb7291a5e1360b6.service','LoadState':'not-found','ActiveState':'inactive','SubState':'dead','InvocationID':'','RuntimeMaxUSec':'infinity','MainPID':'0','NRestarts':'0','ControlGroup':''}
assert sha(S/'SOURCE-COMPOSITION.json')=='dc694f13528c8a4086ee17f670135887357aa6c9f7ad97a61033b68e2a567b27'
assert sha(S/'SOURCE-FREEZE.json')=='fefe37045d56d63c0b6f6e37f18344119e0ce07f6a640e70e1c3fb5d69c82c4e'
assert sha(OLD_SOURCE/'RESULT.json')=='5bd9bad045317246ce5d684795169a68dd6e4a5511938ceb67a8c92d23851e13'
assert sha(OLD_SOURCE/'FINAL-FREEZE.json')=='4c8e9b3cc0edbd7c709b84f570085c5fe851c695ccc6e9a6be748df1bd082ff8'
prior_f59e=F/'ROOT-CURRENT-OFFICE-F59E-ENV-PROFILE-REFUSAL-CLOSED.json'
f59e_partial=F/'ROOT-F59E-PARTIAL-HELPER-EFFECT-CLARIFICATION.json'
locale_actual=L/'ROOT-RESULT.json'
assert sha(prior_f59e)=='57dcdd41503479a931a1dc4099cf81997695e1a609ac6e18ac9287891a265b29'
assert sha(f59e_partial)=='7c168805fbb6f7c44d9cdd0e6069d0baa0f893e4a00df1546223dc70a1a21033'
assert sha(locale_actual)=='5fe06a4b538a8c6a4ff7b333579c9e2e81606ed2bc38f23ccc4b2e9813d48187'
assert sha(A/'ROOT-PRODUCTION15-SOURCE-ACCEPTED.json')=='7e8b41e6e2ec48a9b6fa36268ef17849cef5de920c3cf0cedf1fd94a2927b23d'
qualified=A/'ROOT-MAPPED-POSTPAPER-OWNC-QUALIFIED-CLOSED.json'
assert sha(qualified)=='c6bc47e38964d65cb92b2a9f2582a2c04fda88bf9ed8934753b536531c533fd7'
prior_closed=P/'ROOT-CURRENT-OFFICE-LOAD-UNEXPECTED-FORK-50AA-CLOSED.json'
assert sha(prior_closed)=='0a5b0529f998d66ebb5728e86bd7d92be5f5727c1f2282ec9631438569b11bff'
assert sha(E/'ROOT-MISSING-POSTINIT-EXTRA-FORK-EXPECTED-NEGATIVE-ACCEPTED.json')=='f6b82e49fd667b686d4718a5015b3dfc79951c37ea39f3f6fc3cc499c451a672'
src=S/'source-inputs/FINAL-CALLER-SOURCE-INPUT-R2.json'
assert sha(src)=='6bd47619b5b06fc88fc2f57a19498e0dac467f0cece890d5e6a310b4aebc354d'
assert not (B/'PREPARED-ACTUAL-IDENTITY.json').exists(), 'stale_prepared_identity_refused'
v=json.loads(src.read_text())
assert v['plan']['operation_id']=='SOURCE_PREFLIGHT_ONLY_NOT_AN_OPERATION' and v['plan']['nonce']=='0'*32
nonce=secrets.token_hex(16)
op=B/('observation-'+nonce[:12]);op.mkdir(mode=0o700,exist_ok=False)
(op/'inputs').mkdir(mode=0o700);(op/'work').mkdir(mode=0o700)
operation='root-charset-current-calc-m-20261116-'+nonce[:12]
oldop=v['plan']['operation_dir'];oldid=v['plan']['operation_id'];oldnonce=v['plan']['nonce']
assert oldid=='SOURCE_PREFLIGHT_ONLY_NOT_AN_OPERATION' and oldnonce=='0'*32
def relocate(x):
 if isinstance(x,str):return x.replace(oldop,str(op)).replace(oldid,operation).replace(oldnonce,nonce)
 if isinstance(x,list):return [relocate(a) for a in x]
 if isinstance(x,dict):return {k:relocate(a) for k,a in x.items()}
 return x
plan=relocate(v['plan']);pre=relocate(v['preload'])
plan['preload']=put(op/'inputs/preload.json',pre)
plan['inner_input']['preload']=plan['preload']
assert plan['operation_dir']==str(op) and plan['work_dir']==str(op/'work')
assert plan['nonce']==nonce and plan['operation_id']==operation
assert plan['budgets']=={'cleanup_seconds':10,'cpu_seconds':120,'memory_bytes':2147483648,'startup_seconds':60,'tasks_max':128,'wall_seconds':240}
assert plan['inner_input']['load_dependency']['operation_deadline_monotonic'] is None
assert plan['inner_input']['gpgme_engine_init']['operation_deadline_monotonic'] is None
assert pre['load_policy']['read_only'] is True and pre['load_policy']['store_render_draw_conversion'] is False
assert pre['source']['sha256']=='a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
plan_ref=put(op/'inputs/plan.json',plan)
outer_ref=v['outer_ref'];assert sha(Path(outer_ref['path']))==outer_ref['sha256']=='8f162630ab2922a75a93c79476730a7a34e34e869aa4b1eaa587b6c8d01933a1'
spec=importlib.util.spec_from_file_location('root_currentM_static_inspection',outer_ref['path']);outer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=outer;spec.loader.exec_module(outer)
t=time.monotonic();inspected=outer.inspect_plan(plan);elapsed=time.monotonic()-t
assert inspected['status']=='SOURCE_INPUTS_INSPECTED_NO_GRANT' and inspected['actual_M'] is None and inspected['runtime_grant'] is False
assert not list((op/'work').iterdir()) and not(op/'consumed-once.json').exists()
inspection=put(op/'whole-actual-plan-preflight.json',{'at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'source_caller_input_ref':ref(src),'plan_ref':plan_ref,'outer_ref':outer_ref,'result':inspected,'elapsed_seconds':elapsed,'actual_new_operation_identity':True,'no_admission_clock_intent_ONCE_actor':True,'old_operations_effects_clocks_unchanged':True})
identity={'charset_source_accepted_ref':ref(charset_source_accepted),'charset_twofile_source_accepted_ref':ref(charset_twofile_accepted),'prior_0b33_closed_ref':ref(prior_0b33),'nil_source_accepted_ref':ref(nil_source_accepted),'charset_source_composition_ref':ref(S/'SOURCE-COMPOSITION.json'),'charset_source_freeze_ref':ref(S/'SOURCE-FREEZE.json'),'prior_cfb4_closed_ref':ref(prior_cfb4),'observability_accepted_ref':ref(observability_accepted),'resolver_accepted_ref':ref(resolver_accepted),'fresh_non_tail_fork':True,'at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'operation_id':operation,'nonce':nonce,'operation_dir':str(op),'plan_ref':plan_ref,'preload_ref':plan['preload'],'outer_ref':outer_ref,'whole_preflight_ref':inspection,'source_accepted_ref':ref(A/'ROOT-PRODUCTION15-SOURCE-ACCEPTED.json'),'locale_source_accepted_ref':ref(source_accepted),'locale_qualified_closed_ref':ref(locale_closed),'locale_source_result_ref':ref(OLD_SOURCE/'RESULT.json'),'locale_source_freeze_ref':ref(OLD_SOURCE/'FINAL-FREEZE.json'),'prior_f59e_closed_ref':ref(prior_f59e),'prior_f59e_partial_effect_ref':ref(f59e_partial),'locale_actual_ref':ref(locale_actual),'changed_boundary_qualification_ref':ref(qualified),'prior_50aa_closed_ref':ref(prior_closed),'helper_controls_accepted_ref':ref(E/'ROOT-MISSING-POSTINIT-EXTRA-FORK-EXPECTED-NEGATIVE-ACCEPTED.json'),'runtime_admitted':False,'actual_M':None,'repeat_basis':'All prior effects including0b33 and cfb4 remain CONSUMED CLOSED; no old nonce/identity/ONCE/clock may replay. Latest0b33 consumed13.139716652s with LOAD/five helper closures/three fontCAS/readOnlyclose; exact source_charset_roundtrip_unsupported beforeMSlookup, rawcharset/type UNKNOWN, nilbranch not reached, Mnull/zeroqueries, fourthfontCAS NOT_RUN and nativefinally NOT_CAPTURED; actor/outer identities reaped, cgroup absent, unit retired. Exact Source-supported UNOshort-1→RTL65535→Windows1→exportRTL0 resolver489c and nearest R2d0af are accepted as Source only; raw API source_font/observations and full reread equality preserved. This does not identify actual0b33 charset/type or prove its refusal repaired. Root separately decides only missing current metric on this exact frozen unchanged common15 plus new externalqualifier3 under a fresh operation and current guards/resources/wholecleanup; no prior futurePASS prerequisite. '+'All prior Root diagnostic/LOAD attempts including original50aa and f59e and their unknown effects/clocks remain consumed/closed; f59e included actual final gpgconf exec/entry/exitintent0 with final normalexit UNKNOWN, not no helper effect. No qualified M exists. Repeat only necessary readonly load/query to reach missing native metric, on exact locale-contract R2 common production15 after exact Root locale Source acceptance and separately Root-reviewed closed OwnC LANGUAGE qualification, with earlier mapped-bootstrap Source/qualification retained, plus preserved helper lifecycle/2negatives/postinitfork/c400 evidence and exact manifest/caller/preload/source joins. New OwnC LANGUAGE is fixture-only and does not identify the historical f59e offending ENV key/value or prove repair of its UNKNOWN selector/coverage. LANGUAGE is outside the15FONT join. StartupENV14 does not establish currentfullENV14 equality; current LANGUAGE/raw snapshot is not retained, only digests. LC_MESSAGES is a Source premise, not an observed runtime fact. Partial ENV15/font joining is distinct from full frozen effective parent/helper equality; no shared builder/ENV scrub/normalization or production ENV12 change. Earlier mapped changed-boundary qualification uses executed source-causal inference; bootstrap presence at new-method entry remains UNKNOWN and the absent-bootstrap branch is not separately runtime-qualified. It does not prequalify Office/native64/fontCAS/restore/readonlyclose/M or ordinary40wall35CPU; Office tasks128 and OwnC tasks64 remain separate. No user/model/producer/render/store/send/stop/App replay, no copied font/source rebaseline. Current authority/resources/cancel/slot/source/UID/hardware CAS required immediately before action; future native64/fontrestore/readonlyclose/M/cleanup not prepassed.'}
identity_ref=put(B/'PREPARED-ACTUAL-IDENTITY.json',identity)
print(json.dumps({'identity_ref':identity_ref,'operation_dir':str(op),'preflight':inspected['status'],'preflight_elapsed_seconds':elapsed,'runtime_admitted':False,'actor':False,'actual_M':None}))
