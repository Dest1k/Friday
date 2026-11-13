from pathlib import Path
import ast,copy,hashlib,json,textwrap,difflib
D=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113')
P=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT-HARNESS-ORDINARY-PHASE-PREP-20261113/source/f07_phase_prepare.py')
V=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
B=Path('/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py')
C=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT209-CONFIG-BOUND-DELTA-20261113/source/current209.py')
R=C.with_name('root_caller.py')
F=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-FINITE-ROOT-ONCE-SOURCE-20261113/source/root_f07_once.py')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(p,raw):
 if isinstance(raw,str):raw=raw.encode()
 p.write_bytes(raw);p.chmod(0o600);return dict(path=str(p),bytes=len(raw),sha256=sha(raw))
b=B.read_bytes();v=V.read_bytes();assert sha(b)=='cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b';assert sha(v)=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
def runner(raw):return next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Runner')
def nodes(raw):return {getattr(n,'name',next((getattr(t,'id','') for t in getattr(n,'targets',[])),'')):n for n in runner(raw).body}
bn,vn=nodes(b),nodes(v)
def segment(raw,n):return ''.join(raw.decode().splitlines(keepends=True)[n.lineno-1:n.end_lineno])
# Every new absent-document fallback is bound before returning unavailable metadata.
# These canonical hashes pre-exist the F07 operation and cannot admit other rows.
pins={
 'root-m03-missing-1a223c04a13c':('96285219817f17f85ceee4d800615c3eccbbc883ed598e9b263a58fc8ec65cce','STOPPED'),
 'root-settings-restarted-e109244e1a93':('f25bf6cdd5d45764ebaf61cbb764cfd747b97bdf7c66ab8126b3b8ab5453cce9','STOPPED'),
 'root-m12-upload-305fa49d4a48':('a95f79820ab4fb31e360320a8224964cb08e2aef60d74251ff08cfcbb11d3961','STOPPED'),
 'root-w03-fulltext-5db764f4a3fe':('29ec939758d449688c08288e1df0870982652a56df1814686a0e539dd44e1c60','STOPPED'),
 'root-source102-a02-414cee111784':('5492f9813a6a5ee0477701aca5abc69de8c4d97615c0b37f598870be1fcb9d3c','RECOVERED_PARTIAL_CAPTURE'),
 'root-s05-d745ac09dcf2':('aa410300fef9fed685c2de67acf309b67082fa67bca54c670d30b54b0db5efae','OBSERVING')}
# Extract only accepted readonly-contract methods. Do not import any F06 footer,
# authority, request/password, runtime208 or product proof.
methods={}
specs={
 'm03_stopped1754_history':('root-m03-missing-1a223c04a13c','not Path(PROOF_PATH).exists()',None),
 'settings_stopped1667_history':('root-settings-restarted-e109244e1a93',"not Path('/home/jericho/.cache/FRW-ROOT-SETTINGS-ORDINARY-SAME-SID-BINDER-20261029/disabled_after_restart/ROOT-ORDINARY-OBSERVATION.json').exists()",None),
 'm12_r02_local_history':('root-m12-upload-305fa49d4a48',"not (Path('/home/jericho/.cache/FRW-ROOT-M12-R02-FALSE-REFUSAL-REPAIR-20261030') / 'PREPARED-LOCAL-RECONCILIATION.json').exists()",'root_acceptance is True'),
 'w03_stopped_local_history':('root-w03-fulltext-5db764f4a3fe',"not Path(W03_STOPPED_PREPARED['path']).exists()",None),
 'a02_terminal_partial':('root-source102-a02-414cee111784',"not Path(A02_PARTIAL_BINDING['path']).exists()",'check_custody is True'),
 's05_settled_partial':('root-s05-d745ac09dcf2',"not Path('/home/jericho/.cache/FRW-ROOT-S05-SOURCE109-ACTUAL-20261030').exists()",None)}
for name,(rid,absent,extra) in specs.items():
 n=bn[name];lines=segment(b,n).splitlines(keepends=True)
 # Insert after any true function docstring, retaining the original body unchanged.
 body0=n.body[1] if isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant) and isinstance(n.body[0].value.value,str) else n.body[0]
 at=body0.lineno-n.lineno
 branch=("        self._f07_exact_history_row(run, "+repr(rid)+")\n"
         "        if "+absent.replace("not Path(", "self._f07_history_document_absent(Path(").replace("not (Path(", "self._f07_history_document_absent((Path(").replace(".exists()", ")")+":\n"
         "            if previous_plan is not None"+(" or not ("+extra+")" if extra else '')+":\n"
         "                raise Refused('Unavailable historical Root proof cannot admit a continuation')\n"
         "            return {'schema': 'frw.F07.exact-retained-history-unavailable.v1',\n"
         "                    'run_id': "+repr(rid)+", 'canonical_sha256': "+repr(pins[rid][0])+",\n"
         "                    'root_document': 'UNAVAILABLE_REMOVED_BY_DISK_CLEANUP_2026-11-08',\n"
         "                    'resource_outcome': 'UNAVAILABLE', 'terminal_complete': False,\n"
         "                    'full180': False, 'semantic_acceptance': 'NOT_ESTABLISHED',\n"
         "                    'replay_authorized': False}\n")
 lines[at:at]=[branch];methods[name]=''.join(lines)
# B00 obligation map is identical to v42, including exact m03 partial and only
# four recorded deleted closure references. No new run/closure is manufactured.
methods['B00_CLOSED_PARTIAL_HISTORY']=segment(v,vn['B00_CLOSED_PARTIAL_HISTORY'])
# Rewrite the v42 deleted-closure branch: validate immutable run first, represent
# unavailable facts explicitly, keep present-document contract and pending raw ACK join.
base_method=segment(b,bn['b00_closed_partial_history'])
start=base_method.index("        closure_raw = safe_read(Path(reference['path']))")
end=base_method.index("        pending = expected['pending_update']")
original=base_method[start:end]
# Keep original full validation only when the actual original closure exists.
run_checks="""        if (digest(raw) != expected['run_sha256'] or encoded(run) != raw
                or run.get('status') != expected['status'] or run.get('send_state') != 'sent'
                or run.get('send_attempts') != 1
                or run.get('stop_phase') != expected['stop_phase']
                or run.get('stop_reason_code') != expected['stop_reason_code']
                or self.clock() < run['deadline']):
            raise Refused('Exact immutable Root-closed B00 history row required')
        closure_path = Path(reference['path'])
        if self._f07_history_document_absent(closure_path):
            if expected.get('closure_deleted_by_disk_cleanup') is not True:
                raise Refused('Closed B00 closure missing without recorded deletion')
            # These are unavailable Root-document facts. terminal_complete in
            # expected remains a receipt-chain OBLIGATION checked by inventory.
            expected = dict(expected, closure_facts_unavailable=True,
                            root_resource_outcome='UNAVAILABLE', root_full180='UNAVAILABLE')
        else:
"""
methods['b00_closed_partial_history']=base_method[:start]+run_checks+textwrap.indent(original,'    ')+base_method[end:]
for name in ('verify_reply_custody','check_reply_text_receipt'):
 methods[name]=segment(v,vn[name])
methods['_f07_history_document_absent']='''    def _f07_history_document_absent(self, path):
        path = no_symlinks(path)
        try:
            path.stat()
        except FileNotFoundError:
            return True
        return False
'''
methods['_f07_exact_history_row']='''    def _f07_exact_history_row(self, run, expected_id):
        pins = '''+repr(pins)+'''
        expected = pins.get(expected_id)
        if expected is None or not isinstance(run, dict) or run.get('id') != expected_id:
            raise Refused('Exact F07 retained history identity required')
        raw = safe_read(self.store.run_path(expected_id))
        if (encoded(run) != raw or digest(raw) != expected[0]
                or run.get('status') != expected[1] or run.get('send_state') != 'sent'
                or run.get('send_attempts') != 1 or self.clock() <= run['deadline']):
            raise Refused('Exact F07 retained history canonical bytes required')
        return expected[0]
'''
# Exact original prefix ends before constructing the new row (stamp/deadline/save).
n=bn['new'];cut=[i for i,x in enumerate(n.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='run' for t in x.targets)]
assert cut==[10]
q=copy.deepcopy(n);q.name='_f07_qualify_new_prefix_readonly';q.args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='name'),ast.arg(arg='scenario')],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[])
q.body=[ast.parse("if self.api is not None: raise Refused('F07 readonly qualifier requires api=None')").body[0],ast.parse('continuation = None').body[0]]+copy.deepcopy(n.body[:cut[0]])+ast.parse("return dict(state='WHOLE_ORIGINAL_NEW_PREFIX_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION', run_id=name, scenario_sha256=digest(encoded(scenario)), continuation=None, new_called=False, run_constructed=False, save_called=False, send_called=False, operation_clock_created=False)").body
ast.fix_missing_locations(q);methods[q.name]=textwrap.indent(ast.unparse(q),'    ')+'\n'
# Source template functions are inert; composition is pure and checks exact base.
addition='\n\n# Exact accepted v42/F06 readonly historical compatibility; guarded absent facts.\nHISTORY_COMPAT_PROVENANCE = '+repr({'accepted_v42_source':dict(path=str(V),bytes=len(v),sha256=sha(v)),'accepted_F06_consumer':dict(path='/home/jericho/.cache/FRW-ASTRA-V3-F06-CORRECTREAD208-ROOT-20261113/work/bot_tester.f06.root-bound.py',sha256='30b7e9183fe70837d5e6bccc5f6317eeb0449ccb057590ee05f995aeef2829da'),'W03_pin_metadata':dict(path='/home/jericho/.cache/FRW-ASTRA-V3-F07-ORDINARY209-ROOT-20261113/CURRENT-CANONICAL-HISTORY-METADATA-ROOT-PREPARATION.json',sha256='3a2798db180ba7be2d74ec02070596ba7fe634b6a4749176b1b8d14125bc958b')})+'\nHISTORY_COMPAT_METHODS = '+repr(methods)+'''\n\ndef apply_history_compat(base_raw):
    """Pure exact cc36→accepted immutable history contracts, no reads/effects."""
    need(type(base_raw) is bytes and digest(base_raw)==SELECTED_SHA,'F07_SELECTED_TESTER_CHANGED')
    text=base_raw.decode();tree=ast.parse(text)
    runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
    existing={getattr(n,'name',next((getattr(t,'id','') for t in getattr(n,'targets',[])),'')):n for n in runner.body}
    lines=text.splitlines(keepends=True);changes=[];added=[]
    for name,source in HISTORY_COMPAT_METHODS.items():
        ast.parse('class Runner:\\n'+source)
        if name in existing:
            node=existing[name];changes.append((node.lineno,node.end_lineno,source))
        else:added.append(source)
    # New private methods are added after the original class body, before its next
    # top-level declaration. Existing consumer functions remain byte-for-byte.
    changes.append((runner.end_lineno+1,runner.end_lineno,'\\n'+''.join(added)))
    for lo,hi,replacement in sorted(changes,reverse=True):lines[lo-1:hi]=[replacement]
    result=''.join(lines).encode();ast.parse(result);return result
'''
prep=P.read_text();needle="    text=base_raw.decode('utf-8');tree=ast.parse(text);lines=text.splitlines(keepends=True)";assert prep.count(needle)==1;prep=prep.replace(needle,"    base_raw=apply_history_compat(base_raw)\n"+needle)
# Append source helpers before optional CLI (none here); runtime lookup is safe.
prep+=addition
pr=write(D/'source/f07_phase_prepare.py',prep)
current=C.read_text();tree=ast.parse(current);n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='PREP' for t in n.targets));lines=current.splitlines(keepends=True);lines[n.lineno-1:n.end_lineno]=['PREP = '+repr(pr)+'\n'];cr=write(D/'source/current209.py',''.join(lines))
caller=R.read_text();start=caller.index('def qualify_selected_ordinary_readonly(');end=caller.index('\n\ndef assemble_root_proof',start)
caller=caller[:start]+'''def qualify_selected_ordinary_readonly(genuine_runner,*,run_id,phase):
    """FUTURE ROOT locked call: original new prefix through every pre-row check.

    Exact composition contains AST-derived original Runner.new checks, truncated
    immediately before row construction. No new/save/stamp/deadline/API/send or
    operation clock is invoked. Historical expiry reads remain original checks.
    This qualifies no current209 proof, operation eligibility or user effect.
    """
    need(genuine_runner.api is None,'F07_READONLY_RUNNER_MUST_HAVE_NO_API')
    result=genuine_runner._f07_qualify_new_prefix_readonly(run_id,phase['scenario'])
    admission=genuine_runner.ordinary_independent_admission(run_id,phase['scenario'])
    need(admission is not None,'F07_EXACT_SELECTED_ORDINARY_ADMISSION_REQUIRED')
    genuine_runner.ordinary_independent_current_rows(admission,run_id)
    need(result['scenario_sha256']==phase['scenario_sha256'],'F07_EXACT_READONLY_PREFIX_SCENARIO_REQUIRED')
    return result
'''+caller[end:]
rr=write(D/'source/root_caller.py',caller)
# Driver: before any once claim or user clock, qualify the same actual prefix
# under all three locks. Revalidate again at existing child boundary as before.
driver=F.read_text();needle='def execute(v,*,binding_ref):';assert driver.count(needle)==1
helper='''def qualify_before_clock(v,caller,checker,ordinary,phase):
    """ROOT ONLY read-only actual history call. No file/claim/clock/API creation.

    Caller holds the shared slot; take existing consumer+credential locks without
    creating them. Store construction is allowed only for pre-existing checked
    directories and must preserve their exact metadata. No child invokes this on
    actual inputs. Refusal propagates before spending a new operation lifecycle.
    """
    genuine=load_raw(ordinary,v['selected_tester']['path'],'_Root_F07_preclock_ordinary')
    paths=[STATE,STATE/'runs',STATE/'updates',STATE/'downloads']
    before={str(p):protected_directory(p) for p in paths};store=genuine.Store(STATE)
    need({str(p):protected_directory(p) for p in paths}==before,'F07_STORE_CONSTRUCTOR_MUTATED_DIRS')
    with store.lock(create=False),store.lock(STATE/'tester-token',create=False):
        me=kernel(os.getpid())
        checker.lock_held(SLOT,me);checker.lock_held(STATE/'consumer.lock',me);checker.lock_held(STATE/'tester-token',me)
        return caller.qualify_selected_ordinary_readonly(genuine.Runner(store,None),run_id=v['run_id'],phase=phase)


DIAGNOSTIC_PHASES=('NEW','SEND','OBSERVE')
DIAGNOSTIC_CALLS=('new','validate_scenario','cursor_offsets','receive_inventory','legacy_receive_inventory',
    'b00_closed_partial_history','_f07_exact_history_row','ordinary_independent_admission',
    'ordinary_independent_history_row','ordinary_independent_current_rows','ordinary_independent_predecessor_checked',
    'verify_reply_custody','check_reply_text_receipt','verify_capture_context','verify_window',
    'a02_terminal_partial','s05_settled_partial','m03_stopped1754_history','settings_stopped1667_history',
    'm12_r02_local_history','w03_stopped_local_history','check','decisions','send','_send','observe')


def enum_failure_frames(exc,stage):
    """No paths, dynamic names, exception text, locals or user payloads."""
    need(stage in DIAGNOSTIC_PHASES,'F07_ENUM_DIAGNOSTIC_PHASE_REQUIRED')
    frames=[];tb=exc.__traceback__
    while tb is not None:
        name=tb.tb_frame.f_code.co_name
        if name in DIAGNOSTIC_CALLS and len(frames)<24:
            frames.append(dict(call=name,line=tb.tb_lineno))
        tb=tb.tb_next
    return frames


'''
driver=driver.replace(needle,helper+needle)
needle="        baseline=scan_scope(v['disk_scope'],deadline=time.monotonic()+30)";assert driver.count(needle)==1;driver=driver.replace(needle,"        readonly_qualification=qualify_before_clock(v,caller,checker,ordinary,phase)\n"+needle)
needle="binding=binding_ref,run_id=v['run_id'],no_retry=True,parent=kernel(os.getpid()))))";assert driver.count(needle)==1;driver=driver.replace(needle,"binding=binding_ref,run_id=v['run_id'],no_retry=True,parent=kernel(os.getpid()),\n            readonly_preclock_qualification=readonly_qualification)))")
needle="exception_class=type(exc).__name__,no_retry=True,product_cancelled=False,semantic='NOT_ESTABLISHED')))";assert driver.count(needle)==1;driver=driver.replace(needle,"exception_class=type(exc).__name__,frames=enum_failure_frames(exc,stage),no_retry=True,\n                product_cancelled=False,semantic='NOT_ESTABLISHED')))")
fr=write(D/'source/root_f07_once.py',driver)
for p in D.joinpath('source').glob('*.py'):compile(p.read_bytes(),str(p),'exec')
write(D/'BASIS.json',json.dumps({'schema':'frw.F07.exact-history-caller-delta-basis.v1','source_only':True,'base':dict(path=str(B),bytes=len(b),sha256=sha(b)),'accepted_v42':dict(path=str(V),bytes=len(v),sha256=sha(v)),'original_preparation':dict(path=str(P),sha256=sha(P.read_bytes())),'previous_checker':dict(path=str(C),sha256=sha(C.read_bytes())),'previous_caller':dict(path=str(R),sha256=sha(R.read_bytes())),'previous_driver':dict(path=str(F),sha256=sha(F.read_bytes())),'new_sources':[pr,cr,rr,fr],'guarded_history_pins':pins,'changed_history_methods':list(methods),'prefix_statement_count':cut[0]},sort_keys=True,indent=2)+'\n')
for old,new,name in [(P,D/'source/f07_phase_prepare.py','PREP'),(C,D/'source/current209.py','CHECKER'),(R,D/'source/root_caller.py','CALLER'),(F,D/'source/root_f07_once.py','DRIVER')]:
 write(D/(name+'-DELTA.patch'),''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new))))
print(json.dumps({'new_sources':[pr,cr,rr,fr],'source_only':True},indent=2))
