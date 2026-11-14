"""Pure genuine closed222 captured-byte join. Canonical paths stay opaque."""
import copy, hashlib, json
SOURCE_COMMIT='199405849b62edb926a234f119b5a62d2adcf3b5'
INSTALLED=dict(base=17730,layers=222,native=17893,plugins=52,project=525)
ROWS=('request','intent','committed','closure','input','marker','receipt','stamp')
SHA={'request':'cf861c5e90a81973896eb478e1d49481ed13f1af434b1d5d029eb639361b9468','intent':'5e57eca25828c952e32c95011a4d89b3ee617ca5a41db021405cc3d245b907bc','committed':'b30edcd3b49f64b1124466c4a88e1d39513e405ceff25c4a8ebb12df930227a5','closure':'c36e719394a3f1e311dcd9996b59f09dada34869e9f1319ee397b18524403619','input':'6ce2378edfb4f2e39fbac58f987ce7d66eaee0b7975c5bdffd0e210b46106951','marker':'927160312baa77b0e95455bf2328a8946dd438bdb5d2e9a101fef3a679db072e','receipt':'b9bbf62464a86621b654f4034480a7e7ac2c280f19ab55b1d7908bd09ae06721','stamp':'41a900c5c4f44de221bd90e74be6d44b58a07eed83dabd36c8d0de5ce5b6396d'}
def require(ok,why):
 if not ok:raise ValueError(why)
def validate_actual222(binding,raw_rows):
 require(binding['schema']=='frw.Root.actual222.eight-row-binding.v1' and binding['source_commit']==SOURCE_COMMIT and binding['installed']==INSTALLED and binding['not_fresh_future_precondition']is True and binding['no_new_effect_or_admission']is True,'genuine_closed222_binding_required')
 require(set(raw_rows)==set(ROWS),'complete_eight_supplied_rows_required');v={}
 for k in ROWS:
  row=binding[k];raw=raw_rows[k]
  require(set(row)=={'cache_path','canonical_path','sha256','bytes'} and row['sha256']==SHA[k] and type(raw)is bytes and len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==SHA[k],'actual222_raw_changed:'+k)
  require(row['cache_path'].startswith('/home/jericho/.cache/') and '/.runtime/'not in row['cache_path'] and '..'not in row['cache_path'].split('/'),'cache_only_actual222_row')
  v[k]=json.loads(raw)
 q,i,c,z,x,m,r,s=(v[k]for k in ROWS)
 canonical={'path':binding['request']['canonical_path'],'sha256':SHA['request']}
 require(q['schema']=='friday.ordinary-telegram-source-update.v46' and q['current_source_successor']['schema']=='friday.current-source-native-successor.v24' and q['installed_layers']==221 and q['installed_files']==17893,'genuine_pre222_request_required')
 require(q['current_input']=={'path':binding['input']['canonical_path'],'sha256':SHA['input']} and len(x['project_files'])==525,'actual222_input525_required')
 require(z['state']=='ROOT_VERIFIED_NATIVE222_INSTALLED_SERVICES_PERMANENT_OPERATION_CLOSED' and z['installed']==INSTALLED and z['actor_reaped']is True and z['publisher_closed']is True and z['recovery_ready']is False,'actual222_closed_not_semantic_credit')
 for role in ('input','marker','receipt','stamp'):require(z[role]=={'path':binding[role]['canonical_path'],'sha256':SHA[role]},'actual222_canonical_role_join:'+role)
 require(z['request']['sha256']==SHA['request'] and m['input_sha256']==SHA['input'] and m['source_receipt_sha256']==SHA['receipt'],'actual222_request_marker_join')
 require(len(r['layers'])==222 and len(r['files'])==17893 and r['source_file_count']==17730 and len(m['plugin_files'])==52,'full_actual222_counts')
 require(all(type(t)is dict and set(t)=={'bytes','mode','sha256'} for t in r['files'].values()),'typed_full_actual222_inventory')
 require(s['fridaySource']['layers']==r['layers'] and s['fridaySource']['baseTree']==r['base_tree'],'actual222_stamp_join')
 require(i['state']=='SOURCE_UPDATE_INTENT' and c['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED' and i['request_reference']==c['request_reference']==canonical and i['request_sha256']==c['request_sha256']==SHA['request'] and i['current_input']==c['current_input']==q['current_input'] and i['current_source_successor']==c['current_source_successor']==q['current_source_successor'] and c['source_receipt_sha256']==SHA['receipt'],'actual222_intent_committed_join')
 require(all(t[k]is False for t in (i,c)for k in ('gateway_started','workers_enabled')),'commit_not_service_authority')
 cut=z['candidate_startup_cutoff'];require(cut['no_DB_restore']is True and all(cut['preserve_current_data_no_old%d_delivery_or_resume'%n]is True for n in range(210,222)),'actual222_retained_cutoff')
 return dict(schema='frw.root223.supplied-actual222-metadata-join.v1',state='SUPPLIED_BYTES_JOINED_NOT_FRESH_CANONICAL_OR_CAS_ADMISSION',complete_eight=True,authenticated_row_sha256=dict(SHA),request=canonical,current_input=q['current_input'],receipt_sha256=SHA['receipt'],installed=copy.deepcopy(INSTALLED),current_source_successor=q['current_source_successor'],canonical4={k:copy.deepcopy(z[n])for k,n in (('input','input'),('marker','marker'),('source_receipt','receipt'),('stamp','stamp'))},source_commit=SOURCE_COMMIT,embedded_runtime_references_followed=False,current_admission=False,execution_grant=False,recovery_ready=False,CASE147='OPEN',values=v)
