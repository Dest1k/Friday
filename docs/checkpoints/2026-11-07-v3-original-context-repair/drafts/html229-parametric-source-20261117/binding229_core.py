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
