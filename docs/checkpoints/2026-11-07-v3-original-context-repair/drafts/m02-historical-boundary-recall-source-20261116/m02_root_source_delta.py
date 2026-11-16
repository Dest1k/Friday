"""Pure, exact delta for existing Root current gate and finite owned actor.

Returns Source bytes only. It reads nothing, issues nothing and executes nothing.
No installed-code change or new transport/projection is required. Root supplies
fresh protected references after its own effect/principal/permission assessment.
"""
import ast,hashlib,re
from pathlib import Path

CURRENT_SHA='93f55acf28062fa941113c98e05fe67d95f2486cd46486be7e2bdbf304652411'
ACTOR_SHA='0719fbe5c589787998fa60df6ef1e2ac2f43f8c0cb5ff613652c5126886f869c'
DECISIONS=('original_M02_effect_eligibility_reconciled',
 'old_effects_UNKNOWN_clocks_preserved','actual_prior_original_source_and_standard_same_tester_boundary_accepted',
 'single_natural_question_no_reupload_no_reset_no_hidden_facts',
 'installed_session_search_predecessor_route_source_unchanged',
 'session_search_original_source_and_reply_are_postconditions',
 'current_permission_cancel_recovery_isolation_assessed',
 'private_oracle_excluded_from_model','metadata_logging_source_unchanged_raw_retention_scoped')


def need(ok,code):
 if not ok:raise ValueError(code)


def path(value):
 need(type(value)is str and value.startswith('/')and not value.startswith('//')and str(Path(value))==value
  and all(x not in('','.','..')for x in value.split('/')[1:])and all(ord(x)>=32 and not 127<=ord(x)<=159 for x in value),'M02_EXACT_CANONICAL_PATH_REQUIRED')
 return value


def ref(value):
 need(type(value)is dict and set(value)=={'path','bytes','sha256'}and type(value['bytes'])is int
  and 0<value['bytes']<=24*1024**2 and type(value['sha256'])is str and re.fullmatch('[a-f0-9]{64}',value['sha256']),'M02_EXACT_SIZED_ROOT_REF_REQUIRED')
 path(value['path']);return dict(path=value['path'],bytes=value['bytes'],sha256=value['sha256'])


def replace_assignment(source,name,value):
 tree=ast.parse(source);nodes=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)]
 need(len(nodes)==1,'M02_EXACT_ASSIGNMENT_SEAM_REQUIRED:'+name);node=nodes[0]
 lines=source.splitlines(keepends=True);lines[node.lineno-1:node.end_lineno]=[name+' = '+repr(value)+'\n'];return ''.join(lines)


def replace_once(source,old,new):
 need(source.count(old)==1,'M02_EXACT_LITERAL_SEAM_REQUIRED');return source.replace(old,new)


def checked(raw,sha):
 need(type(raw)is bytes and hashlib.sha256(raw).hexdigest()==sha,'M02_REVIEWED_PARENT_SOURCE_CHANGED');return raw.decode()


def run_shape(run_id):
 need(type(run_id)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id)and 'UNBOUND'not in run_id,'M02_ROOT_UNUSED_RUN_REQUIRED')
 return run_id


def current_source(parent_raw,*,run_id,baseline_ref,historical_boundary_ref,eligibility_ref):
 """No current data reads. Exact baseline/old-source/eligibility remain Root-owned.

 The generic current checker retains current metadata, three-principal database,
 policy namespace, ordinary projection, configs, lock, cancel, clock, and old-row
 guards. Historical references are pinned Root assessments, never future credits.
 """
 source=checked(parent_raw,CURRENT_SHA).replace('EML','M02').replace('eml','m02')
 source=replace_once(source,'Root\'s bounded preintent gate for one original F01/M02 first upload.',"Root's bounded preintent gate for one original historical M02 recall.")
 source=replace_assignment(source,'RUN',run_shape(run_id))
 source=replace_assignment(source,'BASE',ref(baseline_ref))
 source=replace_assignment(source,'DECISIONS',DECISIONS)
 source=replace_once(source,"def need(ok,why):",'HISTORICAL_BINDING = '+repr(ref(historical_boundary_ref))+'\nELIGIBILITY = '+repr(ref(eligibility_ref))+'\ndef need(ok,why):')
 source=source.replace('frw.Root.M02-first-upload.preintent-proof.v1','frw.Root.M02-historical-recall.preintent-proof.v1')
 source=replace_once(source,'Native admission supplies it after upload.','Native admission supplies it with the future ordinary text event.')
 source=replace_once(source,"need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False,'M02_no_future_credit')",
  "need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False\n      and proof.get('historical_source_boundary')==HISTORICAL_BINDING\n      and proof.get('effect_eligibility')==ELIGIBILITY,'M02_exact_historical_bindings_no_future_credit')")
 source=replace_once(source,"base=h.doc(BASE)","h.readref(HISTORICAL_BINDING);h.readref(ELIGIBILITY)\n base=h.doc(BASE)")
 source=replace_once(source,"clock['deadline_monotonic']-clock['started_monotonic']==600 and time.monotonic()+305<clock['deadline_monotonic']",
  "clock['deadline_monotonic']-clock['started_monotonic']==900 and time.monotonic()+605<clock['deadline_monotonic']")
 ast.parse(source);return source.encode()


def actor_source(parent_raw,*,run_id,source_root,current_path):
 """Same finite once actor/locks/cleanup/resource consumers; no effect is run."""
 source=checked(parent_raw,ACTOR_SHA).replace('EML','M02').replace('eml','m02')
 source=replace_once(source,'One finite Root-owned original M02 ordinary upload; no background loop/retry.',
  'One finite Root-owned original M02 history recall; no background loop/retry.')
 source=replace_assignment(source,'ROOT',Path(path(source_root)))
 # repr(Path) is not a standalone Source literal; use Path of the exact string.
 source=replace_once(source,'ROOT = '+repr(Path(source_root)), 'ROOT = Path('+repr(source_root)+')')
 source=replace_assignment(source,'CURRENT',Path(path(current_path)))
 source=replace_once(source,'CURRENT = '+repr(Path(current_path)), 'CURRENT = Path('+repr(current_path)+')')
 source=replace_assignment(source,'RUN',run_shape(run_id))
 source=source.replace('frw.Root.M02-first-upload.preintent-proof.v1','frw.Root.M02-historical-recall.preintent-proof.v1')
 source=replace_once(source,"baseline=current.BASE,decisions={k:True for k in current.DECISIONS},",
  "baseline=current.BASE,historical_source_boundary=current.HISTORICAL_BINDING,effect_eligibility=current.ELIGIBILITY,decisions={k:True for k in current.DECISIONS},")
 source=replace_once(source,"need(hashlib.sha256(h.encoded(scenario)).hexdigest()==v['scenario_sha256'],'M02_scenario_drift')",
  "need(hashlib.sha256(h.encoded(scenario)).hexdigest()==v['scenario_sha256'],'M02_scenario_drift')\n authority=h.doc(v['authority'])\n need(authority.get('m02_original_source_boundary')==current.HISTORICAL_BINDING and authority.get('m02_effect_eligibility_reconciliation')==current.ELIGIBILITY,'M02_actor_exact_historical_bindings_required')")
 source=replace_once(source,'operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600',
  'operation_seconds=600,reply_window_seconds=480,ack_seconds=10,reserve_seconds=5,outer_seconds=900')
 source=replace_once(source,'need(h.remaining(clock)>305,','need(h.remaining(clock)>605,')
 source=replace_once(source,'deadline_monotonic=start+600,','deadline_monotonic=start+900,')
 source=replace_once(source,'ROOT-ORIGINAL-OUTER600-CLOCK.json','ROOT-ORIGINAL-OUTER900-CLOCK.json')
 # The pinned f172 helper already uses the supplied clock deadline for wait and
 # stop. Only its inherited diagnostic literal needs an M02-local900 adaptation;
 # authenticate original raw bytes first, and never change the parent file.
 source=replace_once(source,"return load(raw,HELPER['path'],'RootM02OwnedHelpers')",
  "need(raw.count(b'F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED')==1,'M02_exact_helper_diagnostic_seam_required');return load(raw.replace(b'F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED',b'M02_STOP_UNCONFIRMED_ORIGINAL_OUTER900_EXPIRED'),HELPER['path'],'RootM02OwnedHelpers')")
 ast.parse(source);return source.encode()


if __name__=='__main__':raise SystemExit('REFUSED: pure Source delta only; Root bindings required')
