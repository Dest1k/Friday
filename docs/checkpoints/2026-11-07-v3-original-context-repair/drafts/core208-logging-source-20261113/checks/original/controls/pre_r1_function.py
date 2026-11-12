def current_native_source_successor_checked(value, *, cli_only, source_update=None):
    """One immediate native198 -> native199 CP continuation; no old parser fallback."""
    f = api()
    if type(value) is not dict or type(value.get('home')) is not str:
        f.require(source_update is None,'ordinary_current_successor_value_required'); return None
    home = f.canonical(value['home']); tx_root = home/'preparation'/('ordinary-source-update-'+PROJECT_DSH_CURRENT_INPUT)
    if source_update is None and not os.path.lexists(tx_root): return None
    f.require(cli_only is True,'ordinary_project_current_source_cli_only_required'); f.directory(home)
    source = f.directory(home/'hermes-agent')
    leaf_ref = None; tx = None
    if source_update is None:
        root_intent = _current_source_json(tx_root/'intent.json')
        f.require(type(root_intent) is dict,'ordinary_current_successor_root_intent_required')
        root_ref = root_intent.get('request_reference')
        root_request,previous = _project_current_root_checked(home,root_ref)
        if encoded(value) == encoded(previous): return None
        leaf_ref = f.read_json(home/f.MARKER).get('ordinary_gateway',{}).get('operator_entry',{}).get('input')
        _current_source_reference(leaf_ref)
        tx = _current_source_cp_transactions(home,leaf_ref)
        f.require(tx is not None,'ordinary_current_successor_committed_edge_required')
        request = _current_source_json(tx/'request.json')
    else:
        request = source_update
    f.require(type(request) is dict and set(request) == CURRENT_SOURCE_CP_FIELDS
        and request['schema'] == 'friday.ordinary-telegram-source-update.v46'
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 7200
        and request['home'] == str(home),'ordinary_current_successor_explicit_request_required')
    context = request['current_source_successor']
    f.require(type(context) is dict and set(context) == {'schema','root_project_update'}
        and context['schema'] == CURRENT_SOURCE_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    root_request,previous = _project_current_root_checked(home,context['root_project_update'])
    _current_source_reference(request['previous_input']); _current_source_reference(request['current_input'])
    current = _current_source_json(Path(request['current_input']['path']))
    f.require(encoded(value) == encoded(current) and current.get('home') == str(home)
        and encoded(request['previous_input']) == encoded(root_request['current_input'])
        and request['previous_input']['sha256'] != request['current_input']['sha256']
        and request['previous_input']['path'] != request['current_input']['path']
        and encoded(request['candidate_input']) == encoded(request['current_input'])
        and request['candidate_project'] == str(f.ROOT)
        and encoded({k:v for k,v in previous.items() if k != 'project_files'}) ==
            encoded({k:v for k,v in current.items() if k != 'project_files'}),
        'ordinary_current_successor_input_join_changed')
    old_cp = _current_source_json(_current_source_reference(root_request['publication_ancestor']['request']))
    f.require(all(encoded(request[k]) == encoded(old_cp[k]) for k in
        ('predecessor_request','predecessor_current_input_sha256','predecessor_receipt_sha256','transaction_history')),
        'ordinary_current_successor_engineering_anchor_changed')
    for key,name in {'source_receipt':'hermes-agent.source.json','target_receipt':'hermes-agent.source.json',
            'marker':f.MARKER,'stamp':'hermes-agent/install-stamp.json'}.items():
        _current_source_reference_metadata = request[key]
        f.require(type(_current_source_reference_metadata) is dict
            and set(_current_source_reference_metadata) == {'path','sha256'}
            and _current_source_reference_metadata['path'] == str(home/name)
            and type(_current_source_reference_metadata['sha256']) is str
            and len(_current_source_reference_metadata['sha256']) == 64
            and all(c in '0123456789abcdef' for c in _current_source_reference_metadata['sha256']),
            'ordinary_current_successor_before_reference_changed')
    f.require(encoded(request['source_receipt']) == encoded(request['target_receipt'])
        and request['source_receipt']['sha256'] == PROJECT_DSH_CURRENT_RECEIPT
        and request['stamp']['sha256'] == PROJECT_DSH_CURRENT_STAMP
        and type(request['installed_layers']) is int and request['installed_layers'] == 198
        and type(request['installed_files']) is int and request['installed_files'] == 17888
        and encoded(request['plugin_set']) == encoded([]) and encoded(request['plugin_additions']) == encoded([])
        and encoded(request['staged_files']) == encoded([]),'ordinary_current_successor_exact_native198_required')
    for key,name in {'configuration':'config.yaml','profile':'FRIDAY-PROFILE.json',
            'launcher':'hermes-agent/.hermes/bin/hermes'}.items():
        _current_source_reference(request[key])
        f.require(request[key]['path'] == str(home/name),'ordinary_current_successor_current_pin_path_changed')
    _current_source_reference(request['native_unit'])
    f.require(request['native_unit']['path'] == root_request['native_unit']['path'],
        'ordinary_current_successor_native_unit_path_changed')
    names = request['layer_names']
    f.require(type(names) is list and len(names) == 1 and type(names[0]) is str
        and names[0] and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in names[0]),
        'ordinary_current_successor_one_layer_required')
    manifest_name = 'patches/hermes/'+names[0]+'-manifest.json'; patch_name = 'patches/hermes/'+names[0]+'.patch'
    old = previous['project_files']; files = current['project_files']
    f.require(type(old) is dict and type(files) is dict,'ordinary_current_successor_project_inventory_required')
    changes = {n for n in old if files.get(n) != old[n]}
    f.require(type(files) is dict and len(old) == 477 and len(files) == 479
        and set(files) == set(old) | {manifest_name,patch_name}
        and manifest_name not in old and patch_name not in old
        and changes <= PROJECT_DSH_CURRENT_HELPERS
        and encoded(request['project_file_updates']) == encoded(sorted(changes))
        and encoded(request['layer_manifest_updates']) == encoded([manifest_name])
        and encoded(request['project_inventory']) == encoded(files)
        and request['project_inventory_sha256'] == f.digest(encoded(files)),
        'ordinary_current_successor_exact_project_delta_required')
    for name,expected in files.items():
        path = Path(name)
        f.require(type(name) is str and not path.is_absolute() and name == path.as_posix()
            and not any(part in ('.','..') for part in path.parts)
            and type(expected) is str and len(expected) == 64 and all(c in '0123456789abcdef' for c in expected)
            and f.digest(f.owned_file(f.ROOT/name)) == expected,'ordinary_current_successor_project_pin_changed')
    f.require(Path(f.__file__).resolve() == f.ROOT/'scripts/friday_install.py'
        and Path(__file__).resolve() == f.ROOT/PROJECT_DSH_CURRENT_HELPER,
        'ordinary_current_successor_helper_origin_changed')
    required = {str(p.relative_to(f.ROOT)) for relative in ('plugins/friday_rework','patches/hermes')
        for p in (f.ROOT/relative).rglob('*') if p.is_file() or p.is_symlink()}
    f.require(required <= set(files),'ordinary_current_successor_extra_project_file')
    manifest = _current_source_json(f.ROOT/manifest_name,private=False)
    f.require(type(manifest) is dict and manifest.get('patch') == patch_name and manifest.get('patch_sha256') == files[patch_name]
        and type(manifest.get('files')) is list and manifest['files'],
        'ordinary_current_successor_manifest_required')
    rows = manifest['files']; touched = [r.get('path') for r in rows if type(r) is dict]
    f.require(len(touched) == len(rows) and len(touched) == len(set(touched))
        and all(type(n) is str and n and not Path(n).is_absolute() and n == Path(n).as_posix()
            and not any(p in ('.','..') for p in Path(n).parts) for n in touched),
        'ordinary_current_successor_manifest_paths_changed')
    marker = _current_source_json(home/f.MARKER); marker_raw = f.owned_file(home/f.MARKER,private=True)
    leaf = marker.get('input_sha256') == request['current_input']['sha256']
    if tx is None: tx = _current_source_cp_transactions(home,request['current_input'])
    intent = commit = None
    if tx is not None: intent,commit = _current_source_cp_proof(home,tx,request,committed=source_update is None)
    f.require(source_update is not None or leaf,'ordinary_current_successor_current_marker_required')
    f.require(not leaf or tx is not None,'ordinary_current_successor_leaf_journal_required')
    before_receipt = _current_source_json(tx/'before/hermes-agent.source.json') if leaf else _current_source_json(home/'hermes-agent.source.json')
    before_marker = _current_source_json(tx/'before'/f.MARKER) if leaf else marker
    before_stamp = _current_source_json(tx/'before/hermes-agent/install-stamp.json') if leaf else _current_source_json(source/'install-stamp.json')
    if not leaf:
        for key in ('source_receipt','marker','stamp'): _current_source_reference(request[key])
    f.require(len(before_receipt.get('layers',[])) == 198 and len(before_receipt.get('files',{})) == 17888
        and type(before_receipt.get('source_file_count')) is int and before_receipt['source_file_count'] == 17730
        and manifest.get('base_commit') == before_receipt.get('commit')
        and before_marker.get('input_sha256') == request['previous_input']['sha256']
        and before_marker.get('source_receipt_sha256') == PROJECT_DSH_CURRENT_RECEIPT
        and before_marker.get('ordinary_gateway',{}).get('source_receipt_sha256') == PROJECT_DSH_CURRENT_RECEIPT
        and encoded(before_marker.get('ordinary_gateway',{}).get('operator_entry',{}).get('input')) == encoded(request['previous_input'])
        and encoded(before_stamp.get('fridaySource')) == encoded({'baseTree':before_receipt['base_tree'],'layers':before_receipt['layers']})
        and encoded(before_stamp.get('commit')) == encoded(before_receipt['commit']) and before_stamp.get('dirty') is True,
        'ordinary_current_successor_before_native_join_changed')
    previous_script = before_marker['ordinary_gateway']['operator_entry'].get('script')
    f.require(type(previous_script) is dict and set(previous_script) == {'path','sha256'}
        and type(previous_script['path']) is str
        and str(f.canonical(previous_script['path'])) == previous_script['path']
        and Path(previous_script['path']).parts[-2:] == ('scripts','friday_native.py')
        and previous_script['sha256'] == old['scripts/friday_native.py'],
        'ordinary_current_successor_previous_operator_changed')
    if not leaf:
        _current_source_reference(previous_script)
    expected_receipt = json.loads(json.dumps(before_receipt)); expected_files = expected_receipt['files']
    for row in rows:
        name = row['path']; prior = expected_files.get(name)
        f.require(type(row.get('new_file')) is bool and row['new_file'] is (prior is None)
            and row.get('before_sha256') == (None if prior is None else prior['sha256'])
            and type(row.get('bytes')) is int and row['bytes'] >= 0 and row.get('mode') == '100644'
            and type(row.get('sha256')) is str and len(row['sha256']) == 64
            and all(c in '0123456789abcdef' for c in row['sha256']),
            'ordinary_current_successor_native_preimage_changed')
        after = dict(prior) if prior is not None else {}
        after.update({'sha256':row['sha256'],'bytes':row['bytes'],'mode':'100644'}); expected_files[name] = after
    expected_receipt['layers'].append({'manifest':manifest_name,'manifest_sha256':files[manifest_name],
        'patch_sha256':files[patch_name]})
    expected_receipt['sources_lock_sha256'] = current['sources_lock']['sha256']
    receipt = _current_source_json(home/'hermes-agent.source.json'); receipt_sha = f.digest(f.owned_file(home/'hermes-agent.source.json',private=True))
    stamp = _current_source_json(source/'install-stamp.json')
    expected_stamp = dict(before_stamp)
    expected_stamp['fridaySource'] = {'baseTree':expected_receipt['base_tree'],'layers':expected_receipt['layers']}
    selected = request['current_input'] if leaf else request['previous_input']; selected_files = files if leaf else old
    f.require(encoded(receipt) == encoded(expected_receipt if leaf else before_receipt)
        and encoded(stamp) == encoded(expected_stamp if leaf else before_stamp)
        and (not leaf or len(receipt['layers']) == 199)
        and (commit is None or commit['source_receipt_sha256'] == receipt_sha),
        'ordinary_current_successor_native_after_changed')
    if intent is not None:
        f.require(encoded(intent['layers']) == encoded([manifest_name]) and encoded(intent['files']) == encoded(touched)
            and (commit is None or encoded(commit['layers']) == encoded([manifest_name])
                and encoded(commit['files']) == encoded(touched)), 'ordinary_current_successor_journal_native_scope_changed')
    plugins = {n:h for n,h in selected_files.items() if n.startswith('plugins/friday_rework/')}
    f.require(len(plugins) == 52 and encoded(before_marker.get('plugin_files')) == encoded(plugins)
        and marker.get('schema') == f.SCHEMA and marker.get('home') == str(home) and marker.get('source') == str(source)
        and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE' and marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('runtime_ready') is False and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('input_sha256') == selected['sha256'] and marker.get('source_receipt_sha256') == receipt_sha
        and marker.get('ordinary_gateway',{}).get('source_receipt_sha256') == receipt_sha
        and encoded(marker.get('plugin_files')) == encoded(plugins), 'ordinary_current_successor_marker_changed')
    if leaf:
        expected_marker = json.loads(json.dumps(before_marker))
        expected_marker['input_sha256'] = request['current_input']['sha256']; expected_marker['source_receipt_sha256'] = receipt_sha
        expected_marker['ordinary_gateway']['source_receipt_sha256'] = receipt_sha
        expected_marker['ordinary_gateway']['operator_entry'] = {'input':request['current_input'],
            'script':{'path':str(f.ROOT/'scripts/friday_native.py'),'sha256':files['scripts/friday_native.py']}}
        f.require(encoded(marker) == encoded(expected_marker)
            and f.digest(f.owned_file(tx/'hermes-agent.source.json',private=True)) == receipt_sha
            and f.digest(f.owned_file(tx/'FRIDAY-INSTALL.json',private=True)) == f.digest(marker_raw)
            and f.digest(f.owned_file(tx/'install-stamp.json',private=True)) == f.digest(f.owned_file(source/'install-stamp.json',private=True)),
            'ordinary_current_successor_metadata_afterimage_changed')
    checked_plugin_inventory(home,plugins)
    lock = _current_source_json(_current_source_reference(current['sources_lock']))
    donors = {row['id']:row for row in lock['repositories']}
    f.require({'hermes','dsh','a0'} <= set(donors),'complete_donor_pins_required')
    f.composition_checked(current if leaf else previous,source,receipt,donors['hermes'])
    if 'tls' in current['product']['dashboard']:
        expected_tls = {relative:current['dashboard_tls'][key]['sha256'] for key,relative in current['product']['dashboard']['tls'].items()}
        f.require(encoded(marker.get('tls_files')) == encoded(expected_tls)
            and all(f.digest(f.owned_file(home/n,private=True)) == sha for n,sha in expected_tls.items()),'installed_dashboard_tls_changed')
    f.native_packages(source)
    from hermes_cli.friday_ordinary_gateway import check
    from hermes_cli.friday_user_scope import authority
    with authority(home): check(home,role=False)
    return home,donors
