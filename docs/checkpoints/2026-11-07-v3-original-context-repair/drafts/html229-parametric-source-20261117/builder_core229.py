"""PRIVATE parametric Source constructor. build(spec) performs no I/O or writes.

FROZEN is injected by the local assembly step from exact permitted Source pins.
The envelope holds a plain Root document, its exact bytes/ref, and the needed
baseline Source projection. No envelope or generated ROOT_BOUND literal grants
admission. Root materialization/qualification/review/current/issuance are separate.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import types

ROOT_DIRECTORY='/home/jericho/.cache/FRW-ASTRA-HTML-V01-EDIT229-ROOT-20261117'
INPUT_SPEC_PATH=ROOT_DIRECTORY+'/ROOT-HTML-EXACT-BINDING-INPUT-SPEC.json'
H='/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032'
STATE='/home/jericho/.local/share/friday-telegram-bot-test'
RUN='f03-html-v01-encoding-original-01-20261117'
SPEC_FIELDS={'schema','Root_directory','baseline','protected_input','native_python','history_count','unknowns','source_roles','run_id','naming_decision','HTML_operation_started','authority_issued','current_admission'}
STAT_FIELDS={'device','inode','uid','size_bytes','mtime_ns','ctime_ns'}
RESOURCES=dict(operation_seconds=600,reply_window_seconds=480,ack_seconds=10,reserve_seconds=5,outer_seconds=900,cpu_seconds=120,max_rss_bytes=536870912,disk_bytes=104857600)


def need(condition,code):
    if not condition:raise ValueError(code)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def encoded(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def canonical_path(value):
    return type(value)is str and value.startswith('/')and not value.startswith('//')and str(Path(value))==value and all(part not in ('','.','..')for part in value.split('/')[1:])and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value)


def reference_shape(value):
    return type(value)is dict and set(value)=={'path','bytes','sha256'}and canonical_path(value['path'])and type(value['bytes'])is int and 0<value['bytes']<=24*1024**2 and type(value['sha256'])is str and len(value['sha256'])==64 and all(c in '0123456789abcdef'for c in value['sha256'])


def reference(path,raw):
    return dict(path=path,bytes=len(raw),sha256=digest(raw))


def _unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'HTML_BUILD_DUPLICATE_JSON_KEY')
        result[key]=value
    return result


def _bad_constant(_value):raise ValueError('HTML_BUILD_NONSTANDARD_JSON_CONSTANT')


def _json(raw):
    return json.loads(raw,object_pairs_hook=_unique,parse_constant=_bad_constant)


def validate_document(document):
    need(type(document)is dict and set(document)==SPEC_FIELDS,'HTML_BUILD_EXACT_ROOT_DOCUMENT_FIELDS')
    need(document['schema']=='frw.Root.HTMLv01.actual-Source-binding-inputs.v1'and document['Root_directory']==ROOT_DIRECTORY and document['run_id']==RUN and document['naming_decision']=='mayak-html-edited.html','HTML_BUILD_EXACT_ROOT_NAMESPACE_CASE_REQUIRED')
    need(all(document[k]is False for k in ('HTML_operation_started','authority_issued','current_admission')),'HTML_BUILD_UNISSUED_SOURCE_ONLY_REQUIRED')
    need(type(document['history_count'])is int and 40<=document['history_count']<=1000000 and type(document['unknowns'])is int and 0<=document['unknowns']<=document['history_count'],'HTML_BUILD_DYNAMIC_HISTORY_COUNTS_REQUIRED')
    need(type(document['source_roles'])is int and document['source_roles']==23,'HTML_BUILD_TWENTYTHREE_SOURCE_ROLES_REQUIRED')
    baseline=document['baseline']
    need(reference_shape(baseline)and not Path(baseline['path']).is_relative_to(H)and not Path(baseline['path']).is_relative_to(STATE),'HTML_BUILD_BASELINE_MUST_BE_PINNED_SOURCE_METADATA')
    python=document['native_python']
    need(canonical_path(python)and python.startswith(H+'/installs/')and python.endswith('/venv/bin/python'),'HTML_BUILD_EXACT_NATIVE_NAMESPACE_PATH_REQUIRED')
    source=document['protected_input']
    need(type(source)is dict and set(source)=={'path','bytes','sha256','stat'}and {k:source[k]for k in ('path','bytes','sha256')}==dict(path=ROOT_DIRECTORY+'/fixtures/mayak-html-v01.html',bytes=1079,sha256='729dc8a2c4800b6039d2f74cc4333f74621473dedd7ae266bf046ae3eabb7294')and type(source['bytes'])is int,'HTML_BUILD_EXACT_PROSPECTIVE_HTML_COPY_REQUIRED')
    st=source['stat']
    need(type(st)is dict and set(st)==STAT_FIELDS and all(type(st[k])is int for k in st)and st['device']>0 and st['inode']>0 and st['uid']==1000 and st['size_bytes']==1079 and st['mtime_ns']>=0 and st['ctime_ns']>=0,'HTML_BUILD_CURRENT_PROSPECTIVE_STAT_SHAPE_REQUIRED')
    return True


def validate_envelope(spec):
    need(type(spec)is dict and set(spec)=={'document','document_ref','document_bytes','baseline_source','installation_ref','installation_bytes'},'HTML_BUILD_EXACT_SOURCE_ENVELOPE_REQUIRED')
    document=spec['document'];validate_document(document)
    raw=spec['document_bytes'];r=spec['document_ref']
    need(type(raw)is bytes and reference_shape(r)and r['path']==INPUT_SPEC_PATH and reference(r['path'],raw)==r,'HTML_BUILD_EXACT_DOCUMENT_BYTES_AND_REF_REQUIRED')
    parsed=_json(raw);validate_document(parsed)
    need(encoded(parsed)==encoded(document),'HTML_BUILD_EXACT_DOCUMENT_BYTES_AND_REF_REQUIRED')
    source=spec['baseline_source']
    need(type(source)is dict and encoded(source)==encoded(FROZEN['baseline_source23'])and len(source)==23,'HTML_BUILD_ACTUAL_BASELINE_TWENTYTHREE_TEXT_DELIVERY_CLOSURE_REQUIRED')
    need(all(source.get(k)==value for k,value in FROZEN['required_delivery_roles'].items())and len(FROZEN['required_delivery_roles'])==7,'HTML_BUILD_REQUIRED_DELIVERY7_CLOSURE')
    _installation(spec)
    return True


def _assignments(raw,values):
    lines=raw.decode().splitlines(keepends=True)
    nodes={n.targets[0].id:n for n in ast.parse(raw).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
    for name,value in sorted(values.items(),key=lambda item:nodes[item[0]].lineno,reverse=True):
        node=nodes[name];lines[node.lineno-1:node.end_lineno]=[name+' = '+value+'\n']
    return ''.join(lines).encode()


def _current(raw,document,data_refs,scenario,metadata_ref,basis):
    raw=_assignments(raw,dict(RUN=repr(document['run_id']),BASE=repr(document['baseline']),ROOT_BOUND='True',EXPECTED_SOURCE=repr({k:document['protected_input'][k]for k in ('path','bytes','sha256')}),UPLOAD_INPUT=repr(scenario['steps'][0]['input']),ELIGIBILITY=repr(data_refs['bindings/ROOT-ORIGINAL-HTMLV01-EDIT-ELIGIBILITY.json']),INSTALLED229=repr(data_refs['ROOT-INSTALLED229-HTML-ROLE-ASSESSMENT.Source-only.json']),CHECKER=repr(metadata_ref),EXPECTED_PRODUCT_SOURCE_COMMIT=repr(basis['product_source_commit']),EXPECTED_NATIVE_RECEIPT_SHA=repr(basis['canonical']['receipt']['sha256'])))
    anchor=b"OPERATION = 'edit'\n";need(raw.count(anchor)==1,'HTML_BUILD_CURRENT_OPERATION_SEAM')
    delivery={role:[r['sha256'],r['bytes']]for role,r in FROZEN['baseline_source23'].items()}
    raw=raw.replace(anchor,('EXPECTED_SOURCE_ROLE_COUNT = 23\nMETADATA_BASIS_REF = '+repr(data_refs['metadata_basis'])+'\nDELIVERY229_ROLES = '+repr(delivery)+'\n').encode()+anchor)
    anchor=b'def validate_installed229_assessment(value):\n';need(raw.count(anchor)==1,'HTML_BUILD_CURRENT_ROLE_FUNCTION_SEAM')
    functions=b'''def expected_delivery_role_refs():
 return {name:dict(path=str(H/'hermes-agent'/name),sha256=sha,bytes=size)for name,(sha,size)in DELIVERY229_ROLES.items()}
def validate_required_source_roles(base):
 # Exact Source closure is mandatory; actual receipt/bytes are checked below.
 roles={**expected_role_refs(),**expected_delivery_role_refs()}
 need(type(base)is dict and type(base.get('source'))is dict and len(base['source'])==EXPECTED_SOURCE_ROLE_COUNT and all(base['source'].get(k)==r for k,r in roles.items()),'HTMLV01_EXACT229_BASELINE_TEXT_AND_DELIVERY7_ROLES_REQUIRED')
 return roles
'''
    raw=raw.replace(anchor,functions+anchor)
    seam=b" roles=expected_role_refs()\n need(type(base.get('source'))is dict and all(base['source'].get(k)==r for k,r in roles.items()),'HTML229_EXACT229_BASELINE_READ_ROLES_REQUIRED')\n"
    need(raw.count(seam)==1,'HTML_BUILD_CURRENT_RECEIPT_ROLE_SEAM')
    raw=raw.replace(seam,b' roles=validate_required_source_roles(base)\n')
    raw=raw.replace(b"'HTMLV01_ACTUAL_RECEIPT_TEXT_ROLE_CHANGED'",b"'HTMLV01_ACTUAL_RECEIPT_REQUIRED_ROLE_CHANGED'")
    return raw


def _verify_frozen():
    for role,raw in FROZEN['templates'].items():
        need(type(raw)is bytes and digest(raw)==FROZEN['template_pins'][role]['sha256']and len(raw)==FROZEN['template_pins'][role]['bytes'],'HTML_BUILD_EXACT_FROZEN_SOURCE_PIN:'+role)
    need(FROZEN['predecessor']['sha256']=='8396368a55160b91e688894ec28fc3ce2e8efd241ab2f833cd3fc0ddef62413c','HTML_BUILD_EXACT_PREDECESSOR')
    return True


COUNTS229=dict(layers=229,project=539,native=17896,plugins=52,base=17730)
DELTA229=dict(modified=6,added=1,CAS=13,retained=17889)
BASIS_FIELDS={'Root_authenticated_closure','Source_eight_capture','at_moscow','canonical','counts','current_admission','dated_normal_services_infinity','default_same_transaction_postconsumer_returncode','event_or_read_capability','execution_commit','execution_grant','fresh_default_spec_inspect','full_native_readback','future_user_semantics','native_delta','native_seven','poststart_optional_Source_custody','product_source_commit','publisher_returncode','schema','scope','source_acceptance','state'}


def _sha40(value):
    return type(value)is str and len(value)==40 and all(c in '0123456789abcdef'for c in value)


def _installation(spec):
    """Authenticate exact supplied Source metadata, never infer installation.

    Root alone supplies a genuine dated actual229 basis after installation.
    Typed bytes/pins do not establish that its statements are true/current.
    There is no default228, predicted receipt, fabricated future Source capture,
    live I/O, current observation or admission here.
    """
    r=spec.get('installation_ref');raw=spec.get('installation_bytes')
    need(reference_shape(r)and r['path']==ROOT_DIRECTORY+'/ROOT-ACTUAL229-INSTALLATION-METADATA-SOURCE.json'and type(raw)is bytes and reference(r['path'],raw)==r,'HTML229_ACTUAL_INSTALLATION_UNBOUND_OR_PIN_CHANGED')
    basis=_json(raw)
    need(type(basis)is dict and set(basis)==BASIS_FIELDS,'HTML229_EXACT_ACTUAL_BASIS_FIELDS_REQUIRED')
    need(basis['schema']=='frw.Root.actual229.readonly-installation-metadata-basis.v1'and basis['state']=='DATED_CLOSED229_SOURCE_METADATA_ONLY','HTML229_ACTUAL229_BASIS_REQUIRED_NO_LEGACY_FALLBACK')
    need(encoded(basis['counts'])==encoded(COUNTS229)and encoded(basis['native_delta'])==encoded(DELTA229),'HTML229_EXACT_COUNTS_AND_NATIVE7_DELTA_REQUIRED')
    need(_sha40(basis['product_source_commit'])and _sha40(basis['execution_commit']),'HTML229_ACTUAL_PRODUCT_EXECUTION_COMMITS_UNBOUND')
    canonical=basis['canonical']
    need(type(canonical)is dict and set(canonical)=={'input','receipt','marker','stamp'}and all(reference_shape(v)for v in canonical.values()),'HTML229_ACTUAL_CANONICAL4_UNBOUND')
    paths=dict(receipt=H+'/hermes-agent.source.json',marker=H+'/FRIDAY-INSTALL.json',stamp=H+'/hermes-agent/install-stamp.json')
    need(all(canonical[k]['path']==p for k,p in paths.items()),'HTML229_ACTUAL_CANONICAL_NAMESPACES_REQUIRED')
    need(encoded(canonical['input'])==encoded(FROZEN['candidate_input229']),'HTML229_EXACT_REVIEWED_CORE229_INPUT_SOURCE_REQUIRED')
    need(canonical['receipt']['sha256']!='07bd8594911397405c5b222e2421cab2b0ad07e733f016877eb4e9f77655c0c9','HTML229_LEGACY228_RECEIPT_REFUSED')
    need(encoded(basis['native_seven'])==encoded(FROZEN['native7']),'HTML229_EXACT_NATIVE7_AFTER_PINS_REQUIRED')
    for key in ('source_acceptance','Root_authenticated_closure'):
        rr=basis[key]
        need(reference_shape(rr)and Path(rr['path']).is_relative_to('/home/jericho/.cache')and not Path(rr['path']).is_relative_to(H)and not Path(rr['path']).is_relative_to(STATE),'HTML229_ACTUAL_DATED_SOURCE_REF_UNBOUND:'+key)
    need(type(basis['at_moscow'])is str and basis['at_moscow'].endswith('+03:00')and type(basis['scope'])is str and basis['scope'],'HTML229_DATED_BASIS_SCOPE_REQUIRED')
    need(all(basis[k]is False for k in ('current_admission','execution_grant','event_or_read_capability','future_user_semantics')),'HTML229_SOURCE_BASIS_NEVER_CURRENT_AUTHORITY')
    # These are supplied dated installation observations, not preconditions on
    # the installation operation, not old/future booleans silently made True.
    need(all(basis[k]is True for k in ('full_native_readback','fresh_default_spec_inspect','dated_normal_services_infinity'))and all(type(basis[k])is int and basis[k]==0 for k in ('publisher_returncode','default_same_transaction_postconsumer_returncode')),'HTML229_ACTUAL_DATED_INSTALLATION_OBSERVATIONS_REQUIRED')
    need(type(basis['Source_eight_capture'])is dict and type(basis['poststart_optional_Source_custody'])is dict,'HTML229_CAPTURE_OBSERVATIONS_REQUIRED_NO_COMPLETENESS_ASSUMPTION')
    return basis


def _metadata_source(spec,basis):
    canonical=basis['canonical']
    return _assignments(FROZEN['templates']['metadata'],dict(NATIVE_PYTHON=repr(spec['document']['native_python']),SOURCE_BOUND='True',CLOSURE=repr(spec['installation_ref']),ACCEPTANCE=repr(basis['source_acceptance']),SOURCE_COMMIT=repr(basis['product_source_commit']),EXECUTION_COMMIT=repr(basis['execution_commit']),RECEIPT_SHA=repr(canonical['receipt']['sha256']),INPUT_SHA=repr(canonical['input']['sha256']),CANONICAL_REFS=repr(canonical),CANONICAL_PINS=repr({k:(v['sha256'],v['bytes'])for k,v in canonical.items()}),METADATA_BASIS=repr(basis)))


def build(spec):
    """Pure: source-envelope -> ten byte strings/manifest/recipe; no I/O.

    Envelope metadata is not authority. read_build_input may produce it after
    exact metadata reads; Root may use its own authorized reader for another
    authentic baseline location. All actual rows/current/CAS remain futureRoot.
    """
    _verify_frozen();validate_envelope(spec)
    document=spec['document'];root=document['Root_directory']
    basis=_installation(spec)
    data_module=_frozen_module(FROZEN['templates']['data_renderer'],'Parametric229DataRenderer')
    data_module.SOURCE_COMMIT=basis['product_source_commit'];data_module.NATIVE_RECEIPT_SHA256=basis['canonical']['receipt']['sha256']
    data=data_module.render_data(copy.deepcopy(document),copy.deepcopy(FROZEN['text_roles']))
    metadata=_metadata_source(spec,basis)
    metadata_ref=reference(root+'/fixed229_metadata_source.py',metadata)
    need(type(data)is dict and set(data)=={'bindings/scenario.json','bindings/ROOT-ORIGINAL-HTMLV01-EDIT-ELIGIBILITY.json','ROOT-INSTALLED229-HTML-ROLE-ASSESSMENT.Source-only.json','ROOT-HTMLV01-PREPARATION-RECONCILED.json'}and all(type(raw)is bytes for raw in data.values()),'HTML_BUILD_EXACT_FOUR_DATA_FILES')
    refs={name:reference(root+'/'+name,raw)for name,raw in data.items()}
    scenario=_json(data['bindings/scenario.json'])
    actor=_assignments(FROZEN['templates']['actor'],dict(ROOT='Path('+repr(root)+')',CURRENT='Path('+repr(root+'/root_html_v01_edit229_current.py')+')',PYTHON=repr(document['native_python']),RUN=repr(document['run_id'])))
    refs['metadata_basis']=spec['installation_ref']
    current=_current(FROZEN['templates']['current'],document,refs,scenario,metadata_ref,basis)
    issuer=_ISSUER_MODULE.render_issuer(copy.deepcopy(spec['document_ref']),document['history_count'],document['unknowns'])
    files={**data,'root_html_v01_edit229_once.py':actor,'root_html_v01_edit229_current.py':current,'issue_reviewed_html_v01_edit229.py':issuer,'html_v01_edit229_source.py':FROZEN['templates']['preparation'],'fixed229_metadata_source.py':metadata}
    for name,raw in files.items():
        if name.endswith('.py'):compile(raw,root+'/'+name,'exec')
    refs={name:reference(root+'/'+name,raw)for name,raw in files.items()}
    deps=copy.deepcopy(FROZEN['static_dependencies'])
    deps.update(fixed229_metadata=refs['fixed229_metadata_source.py'],metadata_basis=copy.deepcopy(spec['installation_ref']),preparation=refs['html_v01_edit229_source.py'])
    sources=dict(actor=refs['root_html_v01_edit229_once.py'],current_checker=refs['root_html_v01_edit229_current.py'],preparation=deps['preparation'],scenario=refs['bindings/scenario.json'],issuer=refs['issue_reviewed_html_v01_edit229.py'],baseline=copy.deepcopy(document['baseline']),eligibility=refs['bindings/ROOT-ORIGINAL-HTMLV01-EDIT-ELIGIBILITY.json'],installed229=refs['ROOT-INSTALLED229-HTML-ROLE-ASSESSMENT.Source-only.json'])
    bundle=dict(schema='frw.Root.HTMLV01EDIT229.exact-bound-Source-only.v1',operator='Root',run_id=document['run_id'],binding_input_spec=copy.deepcopy(spec['document_ref']),native_python=document['native_python'],sources=sources,reconciliation=refs['ROOT-HTMLV01-PREPARATION-RECONCILED.json'],static_dependencies=deps,required_delivery_roles=copy.deepcopy(FROZEN['baseline_source23']),resources=copy.deepcopy(RESOURCES),Source_acceptance='PENDING_ROOT_BOUND_INDEPENDENT_REVIEW',authority_issued=False,current_admission=False,execution_grant=False,once_or_clock=False)
    files['ROOT-HTMLV01-EXACT-SOURCE-BINDINGS.json']=encoded(bundle)
    rows=[dict(relative_path=name,final_path=root+'/'+name,bytes=len(raw),sha256=digest(raw))for name,raw in sorted(files.items())]
    manifest=dict(schema='frw.Sol.HTMLv01.parametric-materialization-manifest.v1',files=rows,input_spec=copy.deepcopy(spec['document_ref']),baseline=copy.deepcopy(document['baseline']),history_count=document['history_count'],unknowns=document['unknowns'],source_roles=23,predecessor=copy.deepcopy(FROZEN['predecessor']),template_pins=copy.deepcopy(FROZEN['template_pins']),current_admission=False,execution_grant=False,Root_materialized=False)
    recipe=dict(schema='frw.Sol.HTMLv01.parametric-Root-recipe.v1',materialization='Root alone copies ten exact bytes to manifest.final_path as new protected0600 Source files with exclusive writes/readback. Resolve existing different targets explicitly; no blind overwrite/chmod. Inputspec/baseline/prospectivecopy are separate existing Root inputs.',never_during_Source_materialization=['operation directory','authority','descriptor','proof','ONCE','clock','API or model request'],remaining=['actual native229 pure closest-caller qualification','independent final bound review of exact5refs with required decision','fresh current/history/permissions/cancel/locks/sourceCAS/fresh destination','separate Root explicit issuance/admission/operation','genuine observed native read_file; auto-inlineHTML is not equivalent','full480 and ownedstop/reap; actual savedbytes/filename/MIME/delivery/custody and two private assessors'],limits='Source ROOT_BOUND=True and dynamic counts are not authority; no future results pre-PASS. Only1079B UTF8BOM20CRLF one-date profile; not all encoding/HTML. Existing900/600/480/10/5/120/512MiB-AS/100MiBmonitored budgets unchanged. Separate authority/descriptor writes remain nontransactional.',current_admission=False,execution_grant=False)
    return dict(files=files,manifest=manifest,materialization_recipe=recipe)


def _metadata_read(r):
    """Optional Root read-only adapter; never called by build or module import."""
    need(reference_shape(r)and Path(r['path']).is_relative_to('/home/jericho/.cache'),'HTML_BUILD_ADAPTER_ONLY_EXPLICIT_PRIVATE_CACHED_METADATA')
    p=Path(r['path']);need(not any(q.is_symlink()for q in(p,*p.parents)),'HTML_BUILD_METADATA_PATH_LINK')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb')as stream:
        before=os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode)and before.st_uid==os.getuid()and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600,'HTML_BUILD_METADATA_OWNER_MODE')
        raw=stream.read(r['bytes']+1);after=os.fstat(stream.fileno())
    identity=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    need(identity(before)==identity(after)==identity(p.lstat())and reference(r['path'],raw)==r,'HTML_BUILD_METADATA_IDENTITY_HASH_DRIFT')
    return raw


def read_build_input(input_spec_ref,installation_basis_ref,*,reader=None):
    """Read exact Source metadata only; extract source map, never history.

    read adapter and pure constructor are distinct. For another authentic Root
    metadata location, Root may supply its own authorized exact reader. No file
    writes, current checks, operation, credential or runtime are performed here.
    """
    reader=_metadata_read if reader is None else reader
    need(reference_shape(input_spec_ref)and input_spec_ref['path']==INPUT_SPEC_PATH,'HTML_BUILD_EXACT_INPUT_SPEC_PATH')
    raw=reader(input_spec_ref);need(type(raw)is bytes and reference(input_spec_ref['path'],raw)==input_spec_ref,'HTML_BUILD_INPUT_READER_PIN')
    document=_json(raw);validate_document(document)
    baseline_raw=reader(document['baseline'])
    need(type(baseline_raw)is bytes and reference(document['baseline']['path'],baseline_raw)==document['baseline'],'HTML_BUILD_BASELINE_READER_PIN')
    baseline=_json(baseline_raw)
    need(type(baseline)is dict and type(baseline.get('source'))is dict,'HTML_BUILD_BASELINE_SOURCE_MAP_REQUIRED')
    need(reference_shape(installation_basis_ref),'HTML229_ACTUAL_INSTALLATION_UNBOUND')
    installation_raw=reader(installation_basis_ref)
    result=dict(document=document,document_ref=copy.deepcopy(input_spec_ref),document_bytes=raw,baseline_source=copy.deepcopy(baseline['source']),installation_ref=copy.deepcopy(installation_basis_ref),installation_bytes=installation_raw)
    # No baseline history/body is exposed, counted, iterated or returned.
    validate_envelope(result)
    return result


def _frozen_module(raw,name):
    module=types.ModuleType(name);module.__file__='<frozen permitted Source '+name+'>'
    exec(compile(raw,module.__file__,'exec'),module.__dict__)
    return module


def _initialize_frozen():
    global _ISSUER_MODULE,_DATA_MODULE
    _verify_frozen()
    _ISSUER_MODULE=_frozen_module(FROZEN['templates']['issuer_renderer'],'ParametricHTMLIssuerRenderer')
    _DATA_MODULE=_frozen_module(FROZEN['templates']['data_renderer'],'ParametricHTMLDataRenderer')
