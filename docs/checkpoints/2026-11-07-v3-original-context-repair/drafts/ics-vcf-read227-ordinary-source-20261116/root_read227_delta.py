"""Pure exact READ227 caller specialization. No IO or runtime grant at import."""
import ast,hashlib,types
DELTA_SHA='94706f69fe3c9a578f63e35b39b405eeee3fff0eb1a7e32ad73248d7c1379726'
PROFILE_SHA='4d4c1c4ee56f937804011068d54d9a88818bfdc75df4018eb1e706e429e1e8da'
ROLES={
 'tools/scoped_communication.py':('bdba918298bd5f187bc18f5baa887ef1bb07736a7f4887dae39b77dee35df73f',35712),
 'tools/read_extract.py':('8f3ad405263470eac948a9f14fa6c0af18144697cf5244c6c8c8a4f7d543b339',74912),
 'tools/file_tools.py':('cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1',191360),
 'hermes_cli/friday_user_scope.py':('abad3f299d1099914455781176ac0a3e09b4d40d4a2afd14b342dcb990087dba',149634)}
PROFILES={'ics': {'format_index': 110, 'input_filename': 'maple_schedule.ics', 'mime_type': 'text/calendar', 'request': 'Прочитай приложенный календарь maple_schedule.ics целиком. Перечисли все события с названиями, датами и временем так, как они записаны, местами и важными примечаниями. Если есть часовой пояс или повторение, объясни именно записанные условия, не вычисляя новые даты. В конце укажи последнюю содержательную заметку и где она находится в файле.', 'request_ref': {'bytes': 610, 'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/ordinary/REQUEST-ICS-READ.txt', 'sha256': 'b30e4c0707daa0d694b23f19e556881c38537eabcf352146f8f7ed63d1588cb2'}, 'source': {'bytes': 2075, 'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/native/fixtures/maple_schedule.ics', 'sha256': 'ae16ca56024a1f5949552c773764cf9d8d6ca9b8332a2c182220741d3331db46'}}, 'vcf': {'format_index': 111, 'input_filename': 'maple_contacts.vcf', 'mime_type': 'text/vcard', 'request': 'Прочитай приложенный файл контактов maple_contacts.vcf целиком. Перечисли все контакты с именами, организациями, должностями, адресами электронной почты, телефонами и примечаниями. Сохрани различия между рабочими и другими адресами. В конце укажи последнюю содержательную заметку и где она находится в файле.', 'request_ref': {'bytes': 554, 'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/ordinary/REQUEST-VCF-READ.txt', 'sha256': '544cf0e3f0b40d74d185cc663526ec5ae764d01fa454a7dadfe3d3318a77c9f6'}, 'source': {'bytes': 2194, 'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/native/fixtures/maple_contacts.vcf', 'sha256': '301538a40aa3c00b0eff445b6b15f7a9e7dd338b55b109782942a890de69ad41'}}}
def need(ok,why):
 if not ok:raise ValueError(why)
def accepted(raw):
 need(type(raw)is bytes and hashlib.sha256(raw).hexdigest()==DELTA_SHA,'READ227_ACCEPTED_DELTA_DRIFT')
 m=types.ModuleType('_accepted_ordinary_delta');exec(compile(raw,'<accepted-Source>','exec'),m.__dict__);return m
def once(s,old,new):
 need(s.count(old)==1,'READ227_EXACT_SOURCE_SEAM');return s.replace(old,new)
def current_source(delta_raw,parent_raw,*,family,run_id='ROOT_UNBOUND',baseline_ref=None,eligibility_ref=None,installed227_ref=None,upload_input=None,metadata_checker_ref=None,metadata_checker_raw=None):
 need(family in PROFILES,'READ227_EXACT_FAMILY_REQUIRED');profile=PROFILES[family];d=accepted(delta_raw)
 bound=any(v is not None for v in (baseline_ref,eligibility_ref,installed227_ref,upload_input))
 if bound:
  d.ref(metadata_checker_ref);validate_metadata_checker(metadata_checker_raw)
  need(metadata_checker_ref['bytes']==len(metadata_checker_raw) and metadata_checker_ref['sha256']==hashlib.sha256(metadata_checker_raw).hexdigest(),'READ227_EXACT_METADATA_CHECKER_REF_REQUIRED')
  need(type(upload_input)is dict and set(upload_input)=={'kind','path','sha256','stat','filename','mime_type','caption'},'READ227_INITIAL_INPUT_REQUIRED')
  need(all(upload_input[k]==v for k,v in dict(kind='document',path=profile['source']['path'],sha256=profile['source']['sha256'],filename=profile['input_filename'],mime_type=profile['mime_type'],caption=profile['request']).items()),'READ227_EXACT_INITIAL_INPUT_REQUIRED')
  st=upload_input['stat'];need(type(st)is dict and set(st)=={'device','inode','size_bytes','uid','mtime_ns','ctime_ns'} and all(type(v)is int and v>=0 for v in st.values()) and st['inode']>0 and st['size_bytes']==profile['source']['bytes'],'READ227_INITIAL_STAT_REQUIRED')
 else:need(upload_input is None and metadata_checker_ref is None and metadata_checker_raw is None,'READ227_UNBOUND_NO_SOURCE_IDENTITY_OR_METADATA')
 s=d.current_source(parent_raw,run_id=run_id,operation='create',baseline_ref=baseline_ref,eligibility_ref=eligibility_ref,installed227_ref=installed227_ref).decode()
 s=d.assignment(s,'OPERATION','read')
 s=d.assignment(s,'CHECKER',metadata_checker_ref)
 s=once(s,'ROOT_BOUND = '+repr(bound)+'\n','ROOT_BOUND = '+repr(bound)+'\nFAMILY = '+repr(family)+'\nEXPECTED_SOURCE = '+repr(profile['source'])+'\nUPLOAD_INPUT = '+repr(upload_input)+'\nREAD227_ROLES = '+repr(ROLES)+'\n')
 s=once(s,"proof.get('operation')==OPERATION", "proof.get('operation')==OPERATION and proof.get('family')==FAMILY and proof.get('upload_input')==UPLOAD_INPUT")
 # Replace only the accepted exact CREATE/EDIT preamble. No dynamic version path.
 start=s.index(' h.readref(ELIGIBILITY);assessment=h.doc(INSTALLED227)')
 end=s.index(' base=h.doc(BASE)',start)
 s=s[:start]+''' eligibility=h.doc(ELIGIBILITY);assessment=h.doc(INSTALLED227)
 validate_eligibility(eligibility)
 validate_installed227_assessment(assessment)
 source=Path(UPLOAD_INPUT['path']);st=source.lstat();identity=lambda v:dict(device=v.st_dev,inode=v.st_ino,uid=v.st_uid,size_bytes=v.st_size,mtime_ns=v.st_mtime_ns,ctime_ns=v.st_ctime_ns)
 need(not any(q.is_symlink()for q in(source,*source.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and identity(st)==UPLOAD_INPUT['stat'],'EMLCE_CURRENT_UPLOAD_SOURCE_IDENTITY_REQUIRED')
 h.readref(EXPECTED_SOURCE)
 need(identity(source.lstat())==identity(st),'EMLCE_CURRENT_UPLOAD_SOURCE_CAS_CHANGED')
''' +s[end:]
 s=once(s,' base=h.doc(BASE)\n', ''' base=h.doc(BASE)
 # The fixed227 metadata consumer authenticates genuine canonical values now;
 # an assessment boolean or Source-written code-role map is never authority.
 closure=h.doc(c.CLOSURE);metadata=c.installation_metadata(closure)
 values={k:c.doc(r,private=False)for k,r in metadata['canonical4'].items()}
 c.installation_shapes(closure,values['source_receipt'],values['marker'],values['stamp'],values['input'])
 canonical=dict(metadata['canonical4']);canonical['receipt']=canonical.pop('source_receipt')
 need(type(base.get('canonical'))is dict and set(base['canonical'])=={'receipt','marker','stamp'}and all(base['canonical'][k]==canonical[k]for k in base['canonical']),'EMLCE_EXACT227_BASELINE_CANONICAL_REQUIRED')
 roles=expected_role_refs()
 need(type(base.get('source'))is dict and all(base['source'].get(k)==r for k,r in roles.items()),'EMLCE_EXACT227_BASELINE_READ_ROLES_REQUIRED')
 for r in roles.values():h.readref(r,private=False)
''')
 extra='''def expected_role_refs():
 return {name:dict(path=str(H/'hermes-agent'/name),sha256=sha,bytes=size)for name,(sha,size)in READ227_ROLES.items()}
def validate_installed227_assessment(assessment):
 need(type(assessment)is dict and set(assessment)=={'schema','operator','installed','project','product_source_commit','source_mode','family','operation','baseline','read_roles','current_grant'},'EMLCE_EXACT227_ASSESSMENT_FIELDS_REQUIRED')
 need(assessment.get('schema')=='frw.Root.ICSVCF.READ227.role-assessment.v1' and assessment.get('operator')=='Root'and assessment.get('installed')==227 and type(assessment.get('installed'))is int and assessment.get('project')==535 and assessment.get('product_source_commit')=='0f098a354033317fe4cf20dd7a225ad5b2442361'and assessment.get('source_mode')=='EXACT_INSTALLED227_READ_ONLY'and assessment.get('family')==FAMILY and assessment.get('operation')=='read'and assessment.get('baseline')==BASE and assessment.get('read_roles')==expected_role_refs()and assessment.get('current_grant')is False,'EMLCE_EXACT227_ROLE_BASELINE_REQUIRED')
 return True
def validate_eligibility(value):
 need(type(value)is dict and set(value)=={'schema','operator','run_id','family','operation','source','baseline','installed227_assessment','classification','old_effects_UNKNOWN_clocks_preserved','old_rows_modified','replay_authorized'},'EMLCE_EXACT_ELIGIBILITY_FIELDS_REQUIRED')
 need(value.get('schema')=='frw.Root.ICSVCF.READ227.effect-eligibility.v1'and value.get('operator')=='Root'and value.get('run_id')==RUN and value.get('family')==FAMILY and value.get('operation')=='read'and value.get('source')==EXPECTED_SOURCE and value.get('baseline')==BASE and value.get('installed227_assessment')==INSTALLED227 and value.get('classification')=='GENUINELY_UNEXECUTED_ROOT_RECONCILED'and value.get('old_effects_UNKNOWN_clocks_preserved')is True and value.get('old_rows_modified')is False and value.get('replay_authorized')is False,'EMLCE_UNEXECUTED_ELIGIBILITY_REQUIRED')
 return True

'''
 s=once(s,'def validate_proof_shape(',extra+'def validate_proof_shape(')
 s=s.replace('INSTALLED227','INSTALLED227').replace('installed227_assessment','installed227_assessment')
 s=s.replace('frw.Root.EML-create-edit.preintent-proof.v1','frw.Root.ICSVCF.READ227.preintent-proof.v1').replace('EMLCE','READ227').replace('emlce','read227')
 decisions=('original_ICSVCF_initial_READ_genuinely_unexecuted_reconciled','old_effects_UNKNOWN_clocks_preserved','exact_installed227_role_baseline_current_and_fresh_native_process_assessed','single_natural_request_new_upload_no_reset_or_hidden_oracle','native_ingress_actual_read_reply_and_custody_are_postconditions','current_permission_cancel_recovery_isolation_assessed','private_oracle_excluded_from_model','metadata_logging_source_unchanged_raw_retention_scoped')
 s=d.assignment(s,'DECISIONS',decisions);ast.parse(s);return s.encode()
def actor_source(delta_raw,parent_raw,*,family,run_id='ROOT_UNBOUND',source_root,current_path,native_python=None):
 need(family in PROFILES,'READ227_EXACT_FAMILY_REQUIRED');d=accepted(delta_raw)
 if run_id=='ROOT_UNBOUND':need(native_python is None,'READ227_UNBOUND_INTERPRETER_REQUIRED')
 else:d.path(native_python)
 s=d.actor_source(parent_raw,run_id=run_id,source_root=source_root,current_path=current_path).decode()
 s=d.assignment(s,'PYTHON',native_python or 'ROOT_UNBOUND_NATIVE227_INTERPRETER')
 s=once(s,'operation=current.OPERATION,','family=current.FAMILY,operation=current.OPERATION,upload_input=current.UPLOAD_INPUT,')
 s=once(s,"prep.operation_of(scenario)==current.OPERATION", "prep.operation_of(scenario)==current.OPERATION and prep.family_of(scenario)==current.FAMILY")
 s=once(s,"authority.get('eml_effect_eligibility_reconciliation')", "authority.get('icsvcf_read227_effect_eligibility')")
 s=once(s,"authority.get('eml_installed227_current_assessment')", "authority.get('icsvcf_read227_installed227_assessment')")
 s=once(s,"if current.OPERATION=='edit':need(h.doc(current.RECEIVED_SOURCE)==authority.get('eml_received_source'),'EMLCE_ACTOR_EXACT_RECEIVED_SOURCE_REQUIRED')", "need(current.OPERATION=='read'and current.FAMILY=="+repr(family)+" and authority.get('icsvcf_read227_upload_input')==current.UPLOAD_INPUT,'EMLCE_ACTOR_EXACT_INITIAL_READ_REQUIRED')\n need(v.get('native_python')==PYTHON==sys.executable,'EMLCE_EXACT_ROOT_NATIVE227_INTERPRETER_REQUIRED')")
 s=s.replace('INSTALLED227','INSTALLED227').replace('installed227_assessment','installed227_assessment')
 s=once(s,'def main():\n h=helper();',"def main():\n need(RUN!='ROOT_UNBOUND'and PYTHON!='ROOT_UNBOUND_NATIVE227_INTERPRETER','EMLCE_ROOT_UNBOUND_FAILCLOSED_BEFORE_IO')\n h=helper();")
 s=s.replace('frw.Root.EML-create-edit.preintent-proof.v1','frw.Root.ICSVCF.READ227.preintent-proof.v1').replace('EMLCE','READ227').replace('emlce','read227')
 s=s.replace('bot_tester.read227.current226.py','bot_tester.read227.current227.py')
 ast.parse(s);return s.encode()

COUNTS227 = dict(layers=227,project=535,native=17895,plugins=52,base=17730)
PRODUCT227 = '0f098a354033317fe4cf20dd7a225ad5b2442361'
RECEIPT227 = 'e47010a840e2eee2c6c47acb4a5bcd97362ea5575e2f25a5a33887b387890d84'
ACTUAL227_CANONICAL3 = {'receipt': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent.source.json', 'bytes': 3469015, 'sha256': 'e47010a840e2eee2c6c47acb4a5bcd97362ea5575e2f25a5a33887b387890d84'}, 'marker': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/FRIDAY-INSTALL.json', 'bytes': 29573, 'sha256': 'e4900b96adbee30fb6dd27cd5df48abbb160f2b5d251dbb8dd5c61f4a1f2647a'}, 'stamp': {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/install-stamp.json', 'bytes': 66485, 'sha256': '01444eb155a99ca34fda354898a8f2548307797fa1b721715c0f4a32b9b40f00'}}
INSTALLATION_SHAPES_AST_SHA = '7237e7d9eeb0fdf6b4a1bbfc1d98434385ff33e44ef2a8d938abf33e39523b2c'
def validate_metadata_checker(raw):
 """Static exact227 consumer contract only. Root authenticates actual bindings.

 No document is read here. The existing pure installation_shapes body must be
 retained exactly except fixed227 names and the227/535 tuple; actual canonical
 metadata and permission-interpreter bindings remain Root's missing input.
 """
 need(type(raw)is bytes and 0<len(raw)<=1024**2,'READ227_ACTUAL_METADATA_CHECKER_CODE_REQUIRED')
 tree=ast.parse(raw);constants={}
 for n in tree.body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:constants[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 need(constants.get('COUNTS')==COUNTS227 and constants.get('SOURCE_COMMIT')==PRODUCT227 and constants.get('RECEIPT_SHA')==RECEIPT227,'READ227_EXACT_METADATA_PROFILE_REQUIRED')
 need(type(constants.get('LEAF_PINS'))is dict and all(constants['LEAF_PINS'].get(k)==v[0] for k,v in ROLES.items()),'READ227_EXACT_METADATA_READ_ROLES_REQUIRED')
 methods=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='installation_shapes']
 need(len(methods)==1 and hashlib.sha256(ast.dump(methods[0],include_attributes=False).encode()).hexdigest()==INSTALLATION_SHAPES_AST_SHA,'READ227_EXISTING_INSTALLATION_SHAPES_REQUIRED')
 for name in ('installation_metadata','permission_current','databases','services','profile_config_refs'):
  need(len([n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name])==1,'READ227_REQUIRED_EXISTING_METADATA_CONSUMER:'+name)
 canonical=constants.get('CANONICAL_REFS')
 need(type(canonical)is dict and set(canonical)=={'receipt','marker','stamp','input'},'READ227_ACTUAL_CANONICAL_REFS_REQUIRED')
 for r in canonical.values():accepted_ref_shape(r)
 need({k:canonical[k]for k in ACTUAL227_CANONICAL3}==ACTUAL227_CANONICAL3,'READ227_ACTUAL_DATED_CANONICAL3_REQUIRED')
 root='/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032'
 need(all(canonical[k]['path']==root+'/'+v for k,v in {'receipt':'hermes-agent.source.json','marker':'FRIDAY-INSTALL.json','stamp':'hermes-agent/install-stamp.json'}.items())and canonical['receipt']['sha256']==RECEIPT227,'READ227_ACTUAL_CANONICAL_PATHS_AND_RECEIPT_REQUIRED')
 need(constants.get('CANONICAL_PINS')=={k:(v['sha256'],v['bytes'])for k,v in canonical.items()},'READ227_ACTUAL_CANONICAL_PINS_REQUIRED')
 for name in ('CLOSURE','ACCEPTANCE'):accepted_ref_shape(constants.get(name))
 need(constants.get('SOURCE_BOUND')is True and type(constants.get('NATIVE_PYTHON'))is str and 'UNBOUND'not in constants['NATIVE_PYTHON'],'READ227_ACTUAL_METADATA_RUNTIME_BINDINGS_REQUIRED')
 return True

def accepted_ref_shape(v):
 need(type(v)is dict and set(v)=={'path','bytes','sha256'}and type(v['path'])is str and v['path'].startswith('/')and type(v['bytes'])is int and 0<v['bytes']<=24*1024**2 and type(v['sha256'])is str and len(v['sha256'])==64 and all(x in 'abcdef0123456789'for x in v['sha256']),'READ227_EXACT_METADATA_REF_REQUIRED')
 return True

if __name__=='__main__':raise SystemExit('REFUSED: pure Source generator, Root bindings required')
