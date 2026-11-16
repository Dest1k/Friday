"""Pure DOCX Unicode edit caller over qualified227 current/owned monitor.

No Root data is read or transferred. Default output is ROOT_UNBOUND and refuses
before helper IO; Root alone binds a genuinely eligible prospective operation.
"""
import ast
import hashlib
import re
from pathlib import Path

CURRENT_SHA = '1aae737aaf694677e1b1c133f8442a66ffc8e289847a1af16169e8889b5035f6'
ACTOR_SHA = '6c2a8a6b3e7c227b8373365406caf47304d217450cb805258ff57c4cf246db94'
PRODUCT = '0f098a354033317fe4cf20dd7a225ad5b2442361'
COUNTS = dict(layers=227,project=535,native=17895,plugins=52,base=17730)
WORD_ROLES = {
 'hermes_cli/friday_workspace_word_profiles.py': ('a31bd9b79b15ec8663d21199955d2d6600a1ccb3b400956ac79f74545c9aabe1',6558),
 'hermes_cli/friday_workspace_docx.py': ('0bc25b322c58c6a1aba5b4db2b6cf108b0b815b886d2e33f3c9cd2d02e881377',38137),
 'tools/scoped_word_profiles.py': ('4718c402bff018cb23544cc7d207755151c9ad93c327646ac1a84db90c34cf68',25594),
 'tools/scoped_word_stories.py': ('cf9760ecf984f5477047ad332832bd33a1b85be07c8e9ceca3a861a0ac43dc8f',14016),
 'tools/file_tools.py': ('cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1',191360)}
FUTURE = 'GENUINE_INGRESS_NATIVE_EDIT_RETURNED_BYTES_CUSTODY'
DECISIONS = (
 'original_docx_v03_Unicode_edit_preserve_genuinely_unexecuted_reconciled',
 'v01_accepted_v02_consumed_CREATE2251_old_effects_UNKNOWN_clocks_preserved',
 'exact_installed227_Word_roles_current_fresh_native_process_assessed',
 'one_prospective_input_and_natural_question_no_reset_or_hidden_oracle',
 'genuine_ingress_native_edit_returned_bytes_custody_are_postconditions',
 'current_permission_cancel_recovery_isolation_assessed',
 'private_oracle_excluded_from_model',
 'metadata_logging_source_unchanged_raw_retention_scoped')

def need(ok, why):
 if not ok:
  raise ValueError(why)

def checked(raw, sha):
 need(type(raw)is bytes and hashlib.sha256(raw).hexdigest()==sha,
      'DOCXUNI227_QUALIFIED_SOURCE_DRIFT')
 return raw.decode()

def path(value):
 need(type(value)is str and value.startswith('/') and not value.startswith('//')
      and str(Path(value))==value and all(p not in ('','.','..')for p in value.split('/')[1:])
      and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value),
      'DOCXUNI227_CANONICAL_PATH_REQUIRED')
 return value

def ref(value):
 need(type(value)is dict and set(value)=={'path','bytes','sha256'}
      and type(value['bytes'])is int and 0<value['bytes']<=24*1024**2
      and type(value['sha256'])is str and re.fullmatch('[a-f0-9]{64}',value['sha256']),
      'DOCXUNI227_EXACT_REF_REQUIRED')
 path(value['path'])
 return dict(value)

def assignment(source, name, value):
 found=[n for n in ast.parse(source).body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)]
 need(len(found)==1,'DOCXUNI227_EXACT_ASSIGNMENT_SEAM:'+name)
 node=found[0];lines=source.splitlines(keepends=True)
 lines[node.lineno-1:node.end_lineno]=[name+' = '+repr(value)+'\n']
 return ''.join(lines)

def function(source, name, replacement):
 found=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name==name]
 need(len(found)==1,'DOCXUNI227_EXACT_FUNCTION_SEAM:'+name)
 node=found[0];lines=source.splitlines(keepends=True)
 lines[node.lineno-1:node.end_lineno]=[replacement.rstrip()+'\n']
 return ''.join(lines)

def once(source, old, new):
 need(source.count(old)==1,'DOCXUNI227_EXACT_LITERAL_SEAM')
 return source.replace(old,new)

def contract_shape(contract):
 need(type(contract)is dict and all(k in contract for k in
  ('source_name','output_name','old_text','new_text','request','source')),
  'DOCXUNI227_EXACT_CONTRACT_REQUIRED')
 ref(contract['source'])
 need(contract['source_name'].endswith('.docx')and contract['output_name'].endswith('.docx')
      and contract['source_name']!=contract['output_name']
      and type(contract['old_text'])is type(contract['new_text'])is str
      and contract['old_text'] and contract['new_text'] and contract['old_text']!=contract['new_text']
      and type(contract['request'])is str and bool(contract['request']),
      'DOCXUNI227_SUBSTANTIVE_SAME_FORMAT_COPY_REQUIRED')
 return True

def current_source(parent_raw, *, contract, run_id='ROOT_UNBOUND', baseline_ref=None,
 eligibility_ref=None, installed227_ref=None, upload_input=None):
 contract_shape(contract)
 source=checked(parent_raw,CURRENT_SHA)
 bound=any(x is not None for x in (baseline_ref,eligibility_ref,installed227_ref,upload_input))
 expected=dict(contract['source'])
 if bound:
  need(type(run_id)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id)
       and 'UNBOUND'not in run_id,'DOCXUNI227_ROOT_UNUSED_RUN_REQUIRED')
  for value in (baseline_ref,eligibility_ref,installed227_ref):ref(value)
  need(type(upload_input)is dict and set(upload_input)=={'kind','path','sha256','stat','filename','mime_type','caption'},
       'DOCXUNI227_INITIAL_INPUT_REQUIRED')
  path(upload_input['path'])
  need(upload_input['kind']=='document'and upload_input['sha256']==expected['sha256']
       and upload_input['filename']==contract['source_name']
       and upload_input['mime_type']=='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
       and upload_input['caption']==contract['request'],'DOCXUNI227_EXACT_INPUT_REQUIRED')
  st=upload_input['stat']
  need(type(st)is dict and set(st)=={'device','inode','size_bytes','uid','mtime_ns','ctime_ns'}
       and all(type(v)is int and v>=0 for v in st.values())and st['inode']>0
       and st['size_bytes']==expected['bytes'],'DOCXUNI227_CURRENT_SOURCE_STAT_REQUIRED')
  expected['path']=upload_input['path']
 else:
  need(run_id=='ROOT_UNBOUND','DOCXUNI227_UNBOUND_RUN_REQUIRED')
 original=dict(case_id='F-03',case_index=164,original_fixture_ref='FX-FMT',
  extension='docx',variant_id='v03',variant_source_text='Unicode',
  edit_pointer='/operation_rows/16',preserve_pointer='/operation_rows/20',
  operation='initial_genuine_upload_single_BODY_fact_edit_preserve_return_DOCX',
  maximum_trials_per_operation=1,
  scope='DOCX_UNICODE_ONE_FACT_ONLY_NOT_FULL_WORD_APP_OR_OTHER_VARIANTS')
 for name,value in [('RUN',run_id),('BASE',baseline_ref),('ROOT_BOUND',bound),('FAMILY','docx'),
  ('EXPECTED_SOURCE',expected),('UPLOAD_INPUT',upload_input),('READ227_ROLES',WORD_ROLES),
  ('OPERATION','edit'),('ELIGIBILITY',eligibility_ref),('INSTALLED227',installed227_ref),
  ('RECEIVED_SOURCE',None),('DECISIONS',DECISIONS)]:
  source=assignment(source,name,value)
 source=once(source,'RECEIVED_SOURCE = None\n','RECEIVED_SOURCE = None\nVARIANT = \'v03\'\nORIGINAL_CASE = '+repr(original)+'\nFUTURE_POSTCONDITIONS = '+repr(FUTURE)+'\n')
 source=function(source,'validate_installed227_assessment','''def validate_installed227_assessment(value):
 need(type(value)is dict and set(value)=={'schema','operator','installed','project','native','plugins','base','product_source_commit','source_mode','family','variant','operation','baseline','word_roles','current_grant'},'DOCXUNI227_EXACT_ASSESSMENT_FIELDS_REQUIRED')
 need(value.get('schema')=='frw.Root.DOCX.UNICODE227.role-assessment.v1'and value.get('operator')=='Root'and (value.get('installed'),value.get('project'),value.get('native'),value.get('plugins'),value.get('base'))==(227,535,17895,52,17730)and all(type(value[k])is int for k in ('installed','project','native','plugins','base'))and value.get('product_source_commit')=='0f098a354033317fe4cf20dd7a225ad5b2442361'and value.get('source_mode')=='EXACT_INSTALLED227_WORD_UNICODE_EDIT'and value.get('family')==FAMILY and value.get('variant')==VARIANT and value.get('operation')==OPERATION and value.get('baseline')==BASE and value.get('word_roles')==expected_role_refs()and value.get('current_grant')is False,'DOCXUNI227_EXACT_WORD_ROLE_BASELINE_REQUIRED')
 return True
''')
 source=function(source,'validate_eligibility','''def validate_eligibility(value):
 need(type(value)is dict and set(value)=={'schema','operator','run_id','family','variant','operation','original_case','source','baseline','installed227_assessment','classification','old_effects_UNKNOWN_clocks_preserved','old_rows_modified','replay_authorized'},'DOCXUNI227_EXACT_ELIGIBILITY_FIELDS_REQUIRED')
 need(value.get('schema')=='frw.Root.DOCX.UNICODE227.effect-eligibility.v1'and value.get('operator')=='Root'and value.get('run_id')==RUN and value.get('family')==FAMILY and value.get('variant')==VARIANT and value.get('operation')==OPERATION and value.get('original_case')==ORIGINAL_CASE and value.get('source')==EXPECTED_SOURCE and value.get('baseline')==BASE and value.get('installed227_assessment')==INSTALLED227 and value.get('classification')=='GENUINELY_UNEXECUTED_ROOT_RECONCILED'and value.get('old_effects_UNKNOWN_clocks_preserved')is True and value.get('old_rows_modified')is False and value.get('replay_authorized')is False,'DOCXUNI227_UNEXECUTED_UNICODE_EDIT_REQUIRED')
 return True
''')
 source=once(source,"proof.get('received_source')==RECEIVED_SOURCE,", "proof.get('received_source')is None and proof.get('variant')==VARIANT and proof.get('original_case')==ORIGINAL_CASE and proof.get('future_postconditions')==FUTURE_POSTCONDITIONS,")
 source=once(source," for r in roles.values():h.readref(r,private=False)"," for name,r in roles.items():\n  row=values['source_receipt'].get('files',{}).get(name,{})\n  need(row.get('sha256')==r['sha256']and row.get('bytes')==r['bytes'],'DOCXUNI227_ACTUAL_RECEIPT_WORD_ROLE_CHANGED')\n  h.readref(r,private=False)")
 source=source.replace('frw.Root.ICSVCF.READ227.preintent-proof.v1','frw.Root.DOCX.UNICODE227.preintent-proof.v1')
 source=source.replace('Root\'s bounded preintent gate for one original F01/READ227 first upload.',
  'Root\'s qualified227 current guard specialized for one original DOCX Unicode edit.')
 ast.parse(source)
 return source.encode()

def actor_source(parent_raw, *, run_id='ROOT_UNBOUND', source_root, current_path, native_python=None):
 source=checked(parent_raw,ACTOR_SHA)
 if run_id=='ROOT_UNBOUND':
  need(native_python is None,'DOCXUNI227_UNBOUND_NATIVE_INTERPRETER_REQUIRED')
 else:
  need(type(run_id)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id)
       and 'UNBOUND'not in run_id,'DOCXUNI227_ROOT_UNUSED_RUN_REQUIRED')
  path(native_python)
 for name,value in [('RUN',run_id),('PYTHON',native_python or 'ROOT_UNBOUND_NATIVE227_INTERPRETER')]:
  source=assignment(source,name,value)
 for name,value in [('ROOT',source_root),('CURRENT',current_path)]:
  source=assignment(source,name,path(value))
  source=once(source,name+' = '+repr(value),name+' = Path('+repr(value)+')')
 source=once(source,"authority.get('icsvcf_read227_effect_eligibility')", "authority.get('docx_unicode227_effect_eligibility')")
 source=once(source,"authority.get('icsvcf_read227_installed227_assessment')", "authority.get('docx_unicode227_installed227_assessment')")
 source=once(source,"need(current.OPERATION=='read'and current.FAMILY=='vcf' and authority.get('icsvcf_read227_upload_input')==current.UPLOAD_INPUT,'READ227_ACTOR_EXACT_INITIAL_READ_REQUIRED')",
 "need(current.OPERATION=='edit'and current.FAMILY=='docx'and current.VARIANT=='v03'and authority.get('docx_unicode227_upload_input')==current.UPLOAD_INPUT and authority.get('docx_unicode227_original_case')==current.ORIGINAL_CASE and authority.get('docx_unicode227_future_postconditions')==current.FUTURE_POSTCONDITIONS,'DOCXUNI227_ACTOR_EXACT_UNICODE_EDIT_REQUIRED')")
 source=once(source,"received_source=current.RECEIVED_SOURCE,decisions=", "received_source=None,variant=current.VARIANT,original_case=current.ORIGINAL_CASE,future_postconditions=current.FUTURE_POSTCONDITIONS,decisions=")
 source=source.replace('frw.Root.ICSVCF.READ227.preintent-proof.v1','frw.Root.DOCX.UNICODE227.preintent-proof.v1')
 source=source.replace('One finite Root-owned original READ227 ordinary upload; no background loop/retry.',
  'One original DOCX Unicode edit, reusing the qualified227 owned monitor unchanged.')
 ast.parse(source)
 return source.encode()

if __name__=='__main__':
 raise SystemExit('REFUSED: pure Source binding only, Root actual eligibility/current required')
