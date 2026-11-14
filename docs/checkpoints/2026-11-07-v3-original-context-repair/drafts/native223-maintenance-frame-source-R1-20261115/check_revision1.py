"""Finite baseline dependency/R1 relocation SOURCE controls; no final inputs."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import ast,copy,hashlib,json,types
R=Path(__file__).parent;B=R.parent;results=[]
def require(ok,why='check_failed'):
 if not ok:raise AssertionError(why)
def check(name,fn):
 try:fn();results.append(dict(name=name,passed=True))
 except BaseException as e:results.append(dict(name=name,passed=False,error_class=type(e).__name__,reason=str(e)))
def module(path):
 m=types.ModuleType('R1_'+path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def sha(raw):return hashlib.sha256(raw).hexdigest()
m=module(R/'construct_frame223.py');baseline=m.refraw(m.BASELINE_SOURCE_PINS_REF);expected='5e358ccfc80558741e1c34e152d7297b8c733b1490d37d27831a6749cf5b6d00'
check('exact_accepted5e_constant_and_current_cached_bytes',lambda:require(m.BASELINE_SOURCE_PINS_REF==dict(path='/home/jericho/.cache/FRW-ASTRA-NATIVE222-INSTALL-FRAME-PREP-20261114/frame/SOURCE-PINS.json',sha256=expected) and sha(baseline)==expected))
added={};oldpins=m.accepted_baseline_source(lambda p,r:added.setdefault(p,r))
check('genuine5e_helper_retains_exact_source_provenance',lambda:require(added=={m.BASELINE_SOURCE_PINS_REF['path']:baseline} and oldpins==json.loads(baseline)))
bank='/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json'
check('bank_lookup_only_from_authenticated_genuine5e',lambda:require(oldpins['source_refs'][bank]=='cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'))
def changed_baseline_refuses_before_parse_or_add(raw):
 c=module(R/'construct_frame223.py');reads=[];parsed=[];inserted=[];real_read=c.read
 def changed_read(path):
  reads.append(str(path));return raw if str(path)==c.BASELINE_SOURCE_PINS_REF['path'] else real_read(path)
 c.read=changed_read
 c.json=types.SimpleNamespace(loads=lambda value:parsed.append(True))
 try:c.accepted_baseline_source(lambda p,r:inserted.append((p,r)))
 except ValueError as e:require(str(e)=='source_ref_changed','wrong_refusal');require(reads==[c.BASELINE_SOURCE_PINS_REF['path']] and not parsed and not inserted,'unverified_baseline_was_parsed_or_added');return
 raise AssertionError('changed_baseline_not_refused')
check('valid_JSON_whitespace_drift_refuses_before_parse_provenance_or_output',lambda:changed_baseline_refuses_before_parse_or_add(baseline+b' '))
wrong=json.loads(baseline);wrong['source_refs'][bank]='0'*64
check('valid_JSON_changed_bank_pin_refuses_before_any_lookup_or_output',lambda:changed_baseline_refuses_before_parse_or_add((json.dumps(wrong,sort_keys=True,indent=2)+'\n').encode()))
# Check actual constructor integration ordering without inventing a final native223 record.
tree=ast.parse((R/'construct_frame223.py').read_bytes());construct=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='construct');call_nodes=list(ast.walk(construct))
baseline_calls=[n for n in call_nodes if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='accepted_baseline_source']
writes=[n for n in call_nodes if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('mkdir','open')]
lookups=[n for n in call_nodes if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='oldpins']
check('accepted5e_actual_constructor_call_precedes_bank_lookup_and_first_output',lambda:require(len(baseline_calls)==1 and writes and lookups and baseline_calls[0].lineno<min(n.lineno for n in writes+lookups)))
# The nearest unchanged source-pin validator loop is evaluated independently on
# ONLY this actual source row; this is not a full manifest/frame acceptance.
p=R/'frame-draft/source_pins_producer.py';producer=module(p);ptree=ast.parse(p.read_bytes());validate=next(n for n in ptree.body if isinstance(n,ast.FunctionDef)and n.name=='validate_source_pins');loop=next(n for n in validate.body if isinstance(n,ast.For))
args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='value'),ast.arg(arg='source_bytes'),ast.arg(arg='frame')],kwonlyargs=[],kw_defaults=[],defaults=[]);fn=ast.FunctionDef(name='check_actual_source_pin_row_only',args=args,body=[copy.deepcopy(loop)],decorator_list=[]);unit=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));ns=dict(producer.__dict__);exec(compile(unit,'actual_source_pin_row_only','exec'),ns)
row_value=dict(source_refs={m.BASELINE_SOURCE_PINS_REF['path']:expected},historical_refs={});pinloop=ns['check_actual_source_pin_row_only'];source_map={m.BASELINE_SOURCE_PINS_REF['path']:baseline}
check('nearest_source_pin_loop_accepts_actual_authenticated5e_row_only',lambda:pinloop(row_value,source_map,str(R/'not-created-bound-source-control')))
def rejects_bad_pinrow():
 try:pinloop(row_value,{m.BASELINE_SOURCE_PINS_REF['path']:baseline+b' '},str(R/'not-created-bound-source-control'))
 except ValueError as e:require(str(e).startswith('source_pin_changed:'));return
 raise AssertionError('nearest_pin_loop_accepted_drift')
check('nearest_source_pin_loop_rejects_changed_baseline_row',rejects_bad_pinrow)
# All original frame source/templates remain byte-identical; only constructor
# rebases their old own-frame logical prefix when future genuine inputs arrive.
r0s_raw=(B/'DRAFT-SNAPSHOT.json').read_bytes();r0s=json.loads(r0s_raw)
check('R0_snapshot35_still_frozen',lambda:require(sha(r0s_raw)=='2fde33f9000e536b4a8feac6f2db3b6eafe8de9bb724e466a7abaa05050da2de' and all(sha((B/n).read_bytes())==h for n,h in r0s['files'].items())))
check('R0_RESULT_and_review_preserved',lambda:require(sha((B/'RESULT.json').read_bytes())=='8f991ca480384e9a97d4185f215a01f835b2703c5d9f6309384decc2a4c602f5' and sha((B/'review/FINAL-DRAFT-REVIEW.json').read_bytes())=='b15fb7b00aee3f7ee4a39f2111eb0a31dc2536d3a9e8b592dccfd6eca94b3594'))
framefiles=sorted(p for p in (R/'frame-draft').rglob('*')if p.is_file())
check('R1_frame28_bytes_unchanged_from_R0',lambda:require(len(framefiles)==28 and all(sha(p.read_bytes())==r0s['files'][str(p.relative_to(R))]for p in framefiles)))
planned_out=R/'bound-source-frame223-UNBOUND_SOURCE_CONTROL_NOT_CREATED';rendered={str(p.relative_to(R/'frame-draft')):m.rebase_frame_text(p.read_text(),planned_out)for p in framefiles}
for n,raw in rendered.items():
 if n.endswith('.py'):check('relocated_compile:'+n,lambda raw=raw:ast.parse(raw))
 else:check('relocated_JSON:'+n,lambda raw=raw:json.loads(raw))
check('R1_relocation_no_old_own_frame_prefix_left',lambda:require(all(m.DRAFT_LOGICAL_FRAME_PREFIX not in raw and str(m.D)not in raw for raw in rendered.values())))
data_tree=ast.parse(rendered['root223_data.py']);spec=next(n.value.args[0].value for n in data_tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='FINAL_SPEC'for x in n.targets))
check('nearest_planned_data_FINAL_SPEC_rebases_to_new_output',lambda:require(spec==str(planned_out/'SOURCE-SPEC223.json')))
check('R1_relocation_retains_genuine_historical_private525_path',lambda:require(m.PRIVATE525 in rendered['native223_binding.py'] and m.PRIVATE525 in rendered['run_native223_once.py']))
recipe=json.loads((R/'ROOT-223-FILL-EXECUTE-RECOVERY-RECIPE.json').read_bytes());argv=recipe['steps'][1]['argv']
check('R1_Root_recipe_constructor_and_output_join_revision',lambda:require(argv[3]==str(R/'construct_frame223.py') and argv[-1].startswith(str(R)+'/bound-source-frame223-') and 'revision1/DRAFT-SNAPSHOT.json'in recipe['constructor_input_schema']['draft_snapshot']))
check('no_final_bound_frame_or_dynamic_Root_once_created',lambda:require(not planned_out.exists() and not list(R.glob('bound-source-frame223-*')) and not(R/'frame-draft/SOURCE-PINS.json').exists() and not(R/'frame-draft/FUTURE-EXECUTION').exists() and not [p for p in (R/'frame-draft').glob('ROOT-223-*.json')if not p.name.endswith('-TEMPLATE.json')]))
result=dict(schema='frw.native223.maintenance-source-R1-baseline-pin-controls.v1',at_moscow=datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),source_only=True,current_admission=False,execution_grant=False,controls=results,passed=sum(x['passed']for x in results),failed=sum(not x['passed']for x in results),actual_genuine_baseline_ref=m.BASELINE_SOURCE_PINS_REF,not_run=['Full constructor with final native223/source527/request/commit inputs remains UNBOUND.','Full planned loader/producer/frame acceptance and actual builder/consumer remain NOT_RUN.','No H/current/native/service/DB/Office/model/Telegram/Git/once/grant/operation-clock effects.'],reuse=dict(R0_controls59='Unchanged28 frame source/template files and unchanged pure semantics; byte hashes verified. R1 constructor dependency and package relocation checked separately here.',R0_review16='Retained accepted R0 snapshot/review bytes; R1 delta review still separately required.'))
(R/'R1-CONTROLS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ('controls','reuse','not_run')}));raise SystemExit(bool(result['failed']))
