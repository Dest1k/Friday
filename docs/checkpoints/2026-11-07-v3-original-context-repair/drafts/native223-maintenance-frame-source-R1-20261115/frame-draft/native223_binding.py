"""Pure source223 binding; final exact source constants deliberately UNBOUND."""
import copy,hashlib,json
REQUEST_SHA='UNBOUND_NATIVE223_REQUEST_SHA'
INPUT_SHA='UNBOUND_NATIVE223_INPUT_SHA'
PRIVATE_HELPER='UNBOUND_NATIVE223_PRIVATE_HELPER'
PUBLIC_HELPER='UNBOUND_NATIVE223_PUBLIC_HELPER'
CONSUMER_SHA='UNBOUND_NATIVE223_CONSUMER_SHA'
CONSUMER='UNBOUND_NATIVE223_CONSUMER'
REQUEST='UNBOUND_NATIVE223_REQUEST'
STATIC_BINDING_SHA256='UNBOUND_NATIVE223_STATIC_BINDING_SHA256'
LAYER='ordinary-f04-owned-ingress-stop-terminal-after-source222'
HOME='/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032'
PYTHON=HOME+'/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'
PREVIOUS_PROJECT='/home/jericho/.cache/FRW-ASTRA-NATIVE222-ACTUAL-CALLER-GATE-20261114/project'
BUDGETS=dict(operation=2700,forward=1200,external_rollback=300,terminal_cleanup=30,publisher_unit=1530,publisher_client=1560,publisher_CPU=3120,stop_each=45,postcheck=90,cold_gateway=180,cold_dashboard=180,cleanup_reserve=75)
def require(ok,why):
 if not ok:raise ValueError(why)
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def budget_checked(b):
 require(b==BUDGETS,'exact_new_finite_budgets_required');require(b['publisher_unit']>=b['forward']+b['external_rollback']+b['terminal_cleanup'] and b['publisher_client']>=b['publisher_unit']+30 and b['publisher_CPU']>=2*b['publisher_unit'],'publisher_family_budget_containment')
 require(b['operation']-b['postcheck']-b['cold_gateway']-b['cold_dashboard']-b['cleanup_reserve']>=2*b['stop_each']+135+b['publisher_client']+45,'operation_custody_service_reserves')
 return copy.deepcopy(b)
def validate_native_rows(rows,before):
 require(type(rows)is list and rows and len({r['path']for r in rows})==len(rows),'nonempty_exact_unique_native_scope')
 for r in rows:
  require(type(r)is dict and {'path','sha256','bytes','before_sha256','new_file'}<=set(r) and type(r['new_file'])is bool and type(r['bytes'])is int and r['bytes']>0,'strict_native_row_types')
  p=r['path'];require(type(p)is str and p and not p.startswith('/') and all(x not in ('','.','..')for x in p.split('/')),'safe_native_relative_path')
  require(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef'for c in r['sha256']),'native_after_sha256')
  require((r['new_file']is True and r['before_sha256']is None and p not in before)or(r['new_file']is False and p in before and before[p]['sha256']==r['before_sha256'] and r['sha256']!=r['before_sha256']),'native_beforetuple_newfile_join')
 return dict(touched=len(rows),added=sum(r['new_file']for r in rows),modified=sum(not r['new_file']for r in rows))
def bind_static(*,request_raw,input_raw,manifest_raw,patch_raw,predecessor_six,actual_rows):
 require(not REQUEST_SHA.startswith('UNBOUND') and not INPUT_SHA.startswith('UNBOUND'),'native223_final_source_UNBOUND')
 require(hashlib.sha256(request_raw).hexdigest()==REQUEST_SHA and hashlib.sha256(input_raw).hexdigest()==INPUT_SHA,'exact_final_request_input_required')
 q,current,layer=(json.loads(x)for x in (request_raw,input_raw,manifest_raw));oldq,previous,before,marker,stamp=(json.loads(actual_rows[k])for k in ('request','input','receipt','marker','stamp'))
 require(predecessor_six['complete_eight']is True and predecessor_six['installed']==dict(base=17730,layers=222,native=17893,plugins=52,project=525) and all(hashlib.sha256(v).hexdigest()==predecessor_six['authenticated_row_sha256'][k]for k,v in actual_rows.items()),'complete_genuine_actual222_basis')
 require(q['schema']=='friday.ordinary-telegram-source-update.v46' and q['current_source_successor']['schema']=='friday.current-source-native-successor.v25' and q['installed_layers']==222 and q['installed_files']==17893 and q['seconds']==1200,'exact_v25_request223_role')
 require(q['current_input']==q['candidate_input'] and q['current_input']['sha256']==INPUT_SHA and q['previous_input']==oldq['current_input'] and q['source_receipt']['sha256']==predecessor_six['receipt_sha256'],'actual222_before_and_private527_join')
 require(q['current_source_successor']['previous_native_update']==predecessor_six['request'] and q['current_source_successor']['root_project_update']==oldq['current_source_successor']['root_project_update'] and q['transaction_history']==oldq['transaction_history'] and q['predecessor_request']==oldq['predecessor_request'],'retained_history_exact_canonical222_context')
 require(len(previous['project_files'])==525 and len(current['project_files'])==527 and {k:v for k,v in previous.items()if k!='project_files'}=={k:v for k,v in current.items()if k!='project_files'},'525_to527_nonproject_unchanged')
 require(q['layer_names']==[LAYER] and q['project_file_updates']==['scripts/friday_ordinary_install.py'] and q['plugin_additions']==q['plugin_set']==[],'singleton223_helperonly_no_plugins')
 m='patches/hermes/'+LAYER+'-manifest.json';p='patches/hermes/'+LAYER+'.patch'
 require(q['layer_manifest_updates']==[m] and current['project_files'][m]==hashlib.sha256(manifest_raw).hexdigest() and current['project_files'][p]==hashlib.sha256(patch_raw).hexdigest() and current['project_files']['scripts/friday_ordinary_install.py']==PRIVATE_HELPER and PRIVATE_HELPER!=PUBLIC_HELPER,'exact_new_pair_and_private_helper')
 require(set(current['project_files'])-set(previous['project_files'])=={m,p} and not set(previous['project_files'])-set(current['project_files']) and {n for n in previous['project_files']if previous['project_files'][n]!=current['project_files'][n]}=={'scripts/friday_ordinary_install.py'},'no_historical_inventory_rewrite')
 rows=layer['files'];counts=validate_native_rows(rows,before['files']);future=copy.deepcopy(before);future['layers'].append(dict(manifest=m,manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),patch_sha256=hashlib.sha256(patch_raw).hexdigest()))
 for r in rows:future['files'][r['path']]=dict(sha256=r['sha256'],bytes=r['bytes'],mode='100644')
 require(len(future['layers'])==223 and len(future['files'])==17893+counts['added'] and len(marker['plugin_files'])==52 and stamp['fridaySource']['layers']==before['layers'],'derived_after_counts')
 targets={q[k]['path']:dict(before_sha256=q[k]['sha256'],metadata=True)for k in ('source_receipt','marker','stamp')}
 for r in rows:targets[q['home']+'/hermes-agent/'+r['path']]=dict(before_sha256=r['before_sha256'],after_sha256=r['sha256'],native_new=r['new_file'])
 for n in (m,p,'scripts/friday_ordinary_install.py'):targets[q['home']+'/'+n]=dict(before_sha256=previous['project_files'].get(n),after_sha256=current['project_files'][n],native_new=False)
 require(len(targets)==counts['touched']+6,'native_touched_plus_six_distinct_CAS_roles')
 return dict(schema='frw.root223.exact-static-frame-binding.v1',source_only=True,current_admission=False,execution_grant=False,once='UNBOUND_ROOT',clock='UNBOUND_ROOT',before_layers=222,after_layers=223,before_project=525,after_project=527,base=17730,native=17893+counts['added'],after_native=17893+counts['added'],plugins=52,native_targets=counts['touched'],native_additions=counts['added'],selected_target_count=len(targets),request_sha256=REQUEST_SHA,candidate_project=q['candidate_project'],current_input=q['current_input'],previous_input=q['previous_input'],genuine_actual222_predecessor=predecessor_six['request'],prospective_receipt_sha256=hashlib.sha256(encoded(future)).hexdigest(),prospective_receipt_is_not_installed_metadata=True,selected_targets=targets,route_inputs=dict(python=PYTHON,consumer=CONSUMER,request=REQUEST,previous_project=PREVIOUS_PROJECT,home=HOME),consumer_sha256=CONSUMER_SHA,native_files=copy.deepcopy(rows),budgets=budget_checked(BUDGETS),whole_consumer_and_default_aftercommit='NOT_RUN_POSTCONDITION_OF_FUTURE_OPERATION')
