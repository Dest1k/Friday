"""Pure exact Source delta for existing ordinary Root current/owned actor.

No IO/import effects; no issuer, API, once, clock, process, runtime or install.
Unbound output fails before current reads. Root alone supplies real227 bindings.
"""
import ast,hashlib,re
from pathlib import Path
CURRENT_SHA='93f55acf28062fa941113c98e05fe67d95f2486cd46486be7e2bdbf304652411'
ACTOR_SHA='0719fbe5c589787998fa60df6ef1e2ac2f43f8c0cb5ff613652c5126886f869c'
DECISIONS=('original_EML_operation_genuinely_unexecuted_reconciled','old_effects_UNKNOWN_clocks_preserved','exact_installed227_current_and_fresh_native_process_accepted','single_natural_question_no_upload_reset_or_hidden_oracle','genuine_received_source_and_receipt_assessed_for_edit','native_write_output_custody_reply_are_postconditions','current_permission_cancel_recovery_isolation_assessed','private_oracle_excluded_from_model','metadata_logging_source_unchanged_raw_retention_scoped')
def need(ok,code):
 if not ok:raise ValueError(code)
def path(v):
 need(type(v)is str and v.startswith('/')and not v.startswith('//')and str(Path(v))==v and all(x not in('','.','..')for x in v.split('/')[1:])and all(ord(x)>=32 and not 127<=ord(x)<=159 for x in v),'EMLCE_CANONICAL_PATH_REQUIRED');return v
def ref(v):
 need(type(v)is dict and set(v)=={'path','bytes','sha256'}and type(v['bytes'])is int and 0<v['bytes']<=24*1024**2 and type(v['sha256'])is str and re.fullmatch('[a-f0-9]{64}',v['sha256']),'EMLCE_EXACT_REF_REQUIRED');path(v['path']);return dict(v)
def assignment(s,name,value):
 ns=[n for n in ast.parse(s).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)];need(len(ns)==1,'EMLCE_ASSIGNMENT_SEAM:'+name);n=ns[0];ls=s.splitlines(keepends=True);ls[n.lineno-1:n.end_lineno]=[name+' = '+repr(value)+'\n'];return ''.join(ls)
def once(s,old,new):
 need(s.count(old)==1,'EMLCE_EXACT_LITERAL_SEAM');return s.replace(old,new)
def checked(raw,sha):
 need(type(raw)is bytes and hashlib.sha256(raw).hexdigest()==sha,'EMLCE_REVIEWED_PARENT_DRIFT');return raw.decode()
def run(v):
 need(type(v)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',v)and 'UNBOUND'not in v,'EMLCE_ROOT_UNUSED_RUN_REQUIRED');return v

def current_source(parent_raw,*,run_id='ROOT_UNBOUND',operation='create',baseline_ref=None,eligibility_ref=None,installed227_ref=None,received_source_ref=None):
 need(operation in ('create','edit'),'EMLCE_SUPPORTED_OPERATION_REQUIRED')
 bound=baseline_ref is not None or eligibility_ref is not None or installed227_ref is not None or received_source_ref is not None
 if bound:
  run(run_id);baseline_ref=ref(baseline_ref);eligibility_ref=ref(eligibility_ref);installed227_ref=ref(installed227_ref)
  if operation=='edit':received_source_ref=ref(received_source_ref)
  else:need(received_source_ref is None,'EMLCE_CREATE_HAS_NO_SOURCE')
 else:need(run_id=='ROOT_UNBOUND','EMLCE_UNBOUND_RUN_REQUIRED')
 s=checked(parent_raw,CURRENT_SHA).replace('EML','EMLCE').replace('eml','emlce')
 s=assignment(s,'RUN',run_id);s=assignment(s,'BASE',baseline_ref);s=assignment(s,'DECISIONS',DECISIONS)
 s=once(s,'def need(ok,why):','ROOT_BOUND = '+repr(bound)+'\nOPERATION = '+repr(operation)+'\nELIGIBILITY = '+repr(eligibility_ref)+'\nINSTALLED227 = '+repr(installed227_ref)+'\nRECEIVED_SOURCE = '+repr(received_source_ref)+'\ndef need(ok,why):')
 s=s.replace('frw.Root.EMLCE-first-upload.preintent-proof.v1','frw.Root.EML-create-edit.preintent-proof.v1')
 s=once(s,"def validate_proof_shape(proof,run_id,scenario,stage):\n", "def validate_proof_shape(proof,run_id,scenario,stage):\n need(ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')\n")
 s=once(s,"need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False,'EMLCE_no_future_credit')", "need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False and proof.get('operation')==OPERATION and proof.get('effect_eligibility')==ELIGIBILITY and proof.get('installed227_assessment')==INSTALLED227 and proof.get('received_source')==RECEIVED_SOURCE,'EMLCE_exact_Root_bindings_no_future_credit')")
 s=once(s,"h,c,t=fixed_sources();proof=h.doc(proof_ref);validate_proof_shape(proof,run_id,scenario,stage)", "need(ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')\n h,c,t=fixed_sources();proof=h.doc(proof_ref);validate_proof_shape(proof,run_id,scenario,stage)")
 s=once(s,"base=h.doc(BASE)", "h.readref(ELIGIBILITY);assessment=h.doc(INSTALLED227)\n need(assessment.get('operator')=='Root'and assessment.get('installed')==227 and assessment.get('current_accepted')is True and assessment.get('fresh_native_process_after_change')is True and assessment.get('baseline')==BASE,'EMLCE_REAL_INSTALLED227_CURRENT_REQUIRED')\n if OPERATION=='edit':\n  received=h.doc(RECEIVED_SOURCE)\n  need(received.get('source_sha256')=='b308061ec10acc4d9b8f4bf45935da238b5ba851e1da9a5a64d4ec2a0e8b7928'and received.get('source_bytes')==1579 and received.get('genuine_previously_received')is True and received.get('source_unchanged')is True and received.get('original_first_read_preserved')is True,'EMLCE_REAL_RECEIVED_SOURCE_REQUIRED')\n  for key in ('received_artifact','receipt','native_ingress','native_original_read'):h.readref(received[key])\n  sp=Path(received['source_path']);st=sp.lstat();identity=lambda v:dict(device=v.st_dev,inode=v.st_ino,uid=v.st_uid,size_bytes=v.st_size,mtime_ns=v.st_mtime_ns,ctime_ns=v.st_ctime_ns)\n  need(not any(q.is_symlink()for q in(sp,*sp.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and identity(st)==received['source_identity'],'EMLCE_CURRENT_NATIVE_SOURCE_IDENTITY_REQUIRED')\n  h.readref(dict(path=str(sp),bytes=received['source_bytes'],sha256=received['source_sha256']))\n  need(identity(sp.lstat())==identity(st),'EMLCE_CURRENT_NATIVE_SOURCE_CAS_CHANGED')\n base=h.doc(BASE)")
 s=once(s,"clock['deadline_monotonic']-clock['started_monotonic']==600 and time.monotonic()+305<clock['deadline_monotonic']", "clock['deadline_monotonic']-clock['started_monotonic']==900 and time.monotonic()+605<clock['deadline_monotonic']")
 s=s.replace('Native admission supplies it after upload.','Native admission supplies it with a future ordinary event. No future write is preflight credit.')
 ast.parse(s);return s.encode()

def actor_source(parent_raw,*,run_id='ROOT_UNBOUND',source_root,current_path):
 # Parameterized only; current ROOT_BOUND and real Source/review/auth gates remain mandatory.
 if run_id!='ROOT_UNBOUND':run(run_id)
 s=checked(parent_raw,ACTOR_SHA).replace('EML','EMLCE').replace('eml','emlce')
 s=assignment(s,'RUN',run_id)
 for name,value in [('ROOT',source_root),('CURRENT',current_path)]:
  s=assignment(s,name,path(value));s=once(s,name+' = '+repr(value),name+' = Path('+repr(value)+')')
 s=s.replace('frw.Root.EMLCE-first-upload.preintent-proof.v1','frw.Root.EML-create-edit.preintent-proof.v1')
 s=once(s,"baseline=current.BASE,decisions={k:True for k in current.DECISIONS},", "baseline=current.BASE,operation=current.OPERATION,effect_eligibility=current.ELIGIBILITY,installed227_assessment=current.INSTALLED227,received_source=current.RECEIVED_SOURCE,decisions={k:True for k in current.DECISIONS},")
 s=once(s,"scenario=h.doc(v['scenario']);need(hashlib.sha256(h.encoded(scenario)).hexdigest()==v['scenario_sha256'],'EMLCE_scenario_drift')", "scenario=h.doc(v['scenario']);need(hashlib.sha256(h.encoded(scenario)).hexdigest()==v['scenario_sha256'],'EMLCE_scenario_drift')\n need(current.ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')\n prep.validate_scenario_data(scenario);need(prep.operation_of(scenario)==current.OPERATION,'EMLCE_EXACT_OPERATION_REQUIRED')\n authority=h.doc(v['authority']);prep.validate_authority_shape(authority,v['authority'],run_id=RUN,scenario=scenario)\n need(authority.get('eml_effect_eligibility_reconciliation')==current.ELIGIBILITY and authority.get('eml_installed227_current_assessment')==current.INSTALLED227,'EMLCE_ACTOR_EXACT_ROOT_BINDINGS_REQUIRED')\n if current.OPERATION=='edit':need(h.doc(current.RECEIVED_SOURCE)==authority.get('eml_received_source'),'EMLCE_ACTOR_EXACT_RECEIVED_SOURCE_REQUIRED')")
 s=once(s,'operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600','operation_seconds=600,reply_window_seconds=480,ack_seconds=10,reserve_seconds=5,outer_seconds=900')
 s=once(s,'need(h.remaining(clock)>305,','need(h.remaining(clock)>605,');s=once(s,'deadline_monotonic=start+600,','deadline_monotonic=start+900,');s=once(s,'ROOT-ORIGINAL-OUTER600-CLOCK.json','ROOT-ORIGINAL-OUTER900-CLOCK.json')
 s=once(s,"return load(raw,HELPER['path'],'RootEMLCEOwnedHelpers')","need(raw.count(b'F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED')==1,'EMLCE_exact_helper_diagnostic_seam_required');return load(raw.replace(b'F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED',b'EMLCE_STOP_UNCONFIRMED_ORIGINAL_OUTER900_EXPIRED'),HELPER['path'],'RootEMLCEOwnedHelpers')")
 ast.parse(s);return s.encode()
if __name__=='__main__':raise SystemExit('REFUSED: pure Source delta; Root bindings required')
