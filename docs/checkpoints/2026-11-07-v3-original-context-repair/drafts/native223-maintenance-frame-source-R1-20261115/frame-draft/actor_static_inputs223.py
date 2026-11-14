'Shared exact actor SOURCE inputs, checked before once and before maintenance.\n\nImport is inert. read_source_inputs performs bounded caller-selected exact readonly\nreads only; it never imports product packages, collects live authority, writes,\nlaunches a process, or grants admission. Runtime custody remains with Root.\n'
from pathlib import Path
import hashlib,json,os
EXPECTED_HISTORY={'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da.json': '775f18761a37495ded7a1a2b5212bf2fc1cd712051433a710f0ba90d16182160', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/FRIDAY-INSTALL.json': '1f4deb3655b526986c697a2ffba7e6907b898534ba3a403c78ea880b136fd031', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/config.yaml': 'a7bde4c9f1498a1f9d003fbdf4bdb6b9629c7e2f6b6b581a23a523a08249531c', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/hermes-agent.source.json': '403c8b989cb63d4b7aed1a663f4c6e9ee4a03a9eb45d7a43dc21c0c3e42c4402', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/hermes-agent/gateway/authz_mixin.py': '04eb0e1452711d03eb5af20b36cfbe21a1046b7d8c830a41b456f7608403c866', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/hermes-agent/hermes_cli/friday_credential_admission.py': '2ea01026d881aef9b476842add88edefb6e1acc8f40c13496fba9533c3066874', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/hermes-agent/hermes_cli/friday_dashboard_owner.py': 'c6953a787e6645fcf11b16a194db4d50ad500d755c99c0073602f919c424f7f7', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/hermes-agent/hermes_cli/friday_gateway_owner.py': 'cc0ba3eda37e330af6d2ec62e1c9672572a3eac087d070e32d66ff86c2da7682', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/hermes-agent/install-stamp.json': '1cf2bfaa41bd308dc7f389a997ea0795a9748dd21d10735919ebbd8d780d6b53', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/before/plugins/friday_rework/onboarding.py': 'fad47378ae82904d974f78bd489a7f8653c8c0910320aebe25b4b1383bf6fcc9', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/intent.json': '9f0a9a45b4e5dc58bff33712bc350f245b61585c68f248ddcbee132445464b0b', 'preparation/ordinary-gateway-archive/5f42623e9bdc0d6e30a61eb08a06769de128c2c2a1fd0c6838e1f6290ec997da/rolled-back.json': 'ca03657df8e907886ef1d95ca8057a086d544f9980d59187d1cb33702538ddf0', 'preparation/ordinary-gateway/before/FRIDAY-INSTALL.json': '1f4deb3655b526986c697a2ffba7e6907b898534ba3a403c78ea880b136fd031', 'preparation/ordinary-gateway/before/config.yaml': 'a7bde4c9f1498a1f9d003fbdf4bdb6b9629c7e2f6b6b581a23a523a08249531c', 'preparation/ordinary-gateway/before/hermes-agent.source.json': '403c8b989cb63d4b7aed1a663f4c6e9ee4a03a9eb45d7a43dc21c0c3e42c4402', 'preparation/ordinary-gateway/before/hermes-agent/gateway/authz_mixin.py': '04eb0e1452711d03eb5af20b36cfbe21a1046b7d8c830a41b456f7608403c866', 'preparation/ordinary-gateway/before/hermes-agent/hermes_cli/friday_credential_admission.py': '2ea01026d881aef9b476842add88edefb6e1acc8f40c13496fba9533c3066874', 'preparation/ordinary-gateway/before/hermes-agent/hermes_cli/friday_dashboard_owner.py': 'c6953a787e6645fcf11b16a194db4d50ad500d755c99c0073602f919c424f7f7', 'preparation/ordinary-gateway/before/hermes-agent/hermes_cli/friday_gateway_owner.py': 'cc0ba3eda37e330af6d2ec62e1c9672572a3eac087d070e32d66ff86c2da7682', 'preparation/ordinary-gateway/before/hermes-agent/install-stamp.json': '1cf2bfaa41bd308dc7f389a997ea0795a9748dd21d10735919ebbd8d780d6b53', 'preparation/ordinary-gateway/before/plugins/friday_rework/onboarding.py': 'fad47378ae82904d974f78bd489a7f8653c8c0910320aebe25b4b1383bf6fcc9', 'preparation/ordinary-gateway/committed.json': '6ee0e604c4a4223bd376b5d9db2c54138848e189ccb3df696abc94279ce20954', 'preparation/ordinary-gateway/intent.json': '91395401da5a89b7a52c626f099bd4ec1a22e69dfa4c96b842ae16990ef81f4d'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def validate_source_schema(q):
    assert type(q) is dict, 'exact_source_request_object_required'
    assert type(q['seconds']) is int and q['seconds']==1200, 'exact_forward600_required'
    assert type(q['installed_layers']) is int and q['installed_layers']==222, 'actual218_not_future220_required'
    assert type(q['installed_files']) is int and q['installed_files']==17893, 'actual_native17893_required'
    history=q['transaction_history']
    assert type(history) is dict and history==EXPECTED_HISTORY, 'actual_current_history_mapping23_required'
    for name,digest in history.items():
        assert type(name) is str and not name.startswith('/') and '..' not in Path(name).parts, 'relative_current_history_path_required'
        assert type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest), 'current_history_sha256_required'

def selected_source_reference(*, manifest, bound, native_spec):
    'Keep selected-current role, category, hash and metadata joins distinct.'
    SPEC=Path(native_spec)
    assert type(manifest['source_refs']) is dict and str(SPEC) in manifest['source_refs'], 'native_spec_must_be_in_typed_source_refs'
    reference={'path':str(SPEC),'sha256':manifest['source_refs'][str(SPEC)]}
    assert manifest['source_spec_ref'] == reference, 'native_spec_source_category_join_required'
    assert sha(SPEC) == reference['sha256'], 'native_spec_source_pin_changed'
    assert bound['native_spec'] == reference, 'actor_selected_source_bound_join_required'
    return reference

def validate_selection_aliases(*, source_spec_ref, q, bound, admission, qualification):
    'Readonly joins only; a template never grants admission or qualification.'
    assert bound['current_input'] == q['current_input'] and bound['previous_input'] == q['previous_input'], 'actor_request_bound_input_join_required'
    assert admission['native_spec'] == source_spec_ref, 'actor_admission_selected_source_join_required'
    assert qualification['native_spec'] == source_spec_ref, 'actor_qualification_selected_source_join_required'
    assert qualification['operational_input'] == q['current_input'], 'actor_qualification_current_input_join_required'

def read_source_inputs(*, manifest, bound, request_path, home, previous_project, candidate_project, native_spec):
    REQ=Path(request_path);H=Path(home);P=Path(previous_project);C=Path(candidate_project);N=H/'hermes-agent';SPEC=Path(native_spec)
    source_spec_ref=selected_source_reference(manifest=manifest,bound=bound,native_spec=SPEC)
    q = json.loads(REQ.read_bytes())
    validate_source_schema(q)
    assert bound['current_input'] == q['current_input'] and bound['previous_input'] == q['previous_input'], 'actor_request_bound_input_join_required'
    for name,digest in q['transaction_history'].items():
        assert sha(H/name)==digest, 'actual_current_history_pin_changed'

    cur = json.loads(Path(q['current_input']['path']).read_bytes())

    previous = json.loads(Path(q['previous_input']['path']).read_bytes())

    assert len(cur['project_files']) == 527

    assert len(previous['project_files']) == 525

    assert q['home'] == str(H) and q['candidate_project'] == str(C) and q['seconds'] == 1200

    assert q['layer_names'] == ['ordinary-f04-owned-ingress-stop-terminal-after-source222']

    tx = H / 'preparation' / ('ordinary-source-update-v45-' + sha(REQ)[:16])

    assert not os.path.lexists(tx)

    for name, expected in cur['project_files'].items():
        assert sha(C / name) == expected, name

    for name, expected in previous['project_files'].items():
        assert sha(P / name) == expected, name

    for name in ['marker', 'source_receipt', 'stamp', 'configuration', 'profile', 'launcher', 'native_unit',
            'previous_input', 'current_input', 'predecessor_request', 'target_receipt', 'candidate_input']:
        assert sha(q[name]['path']) == q[name]['sha256'], name

    before_receipt = json.loads((H / 'hermes-agent.source.json').read_bytes())

    before_marker = json.loads((H / 'FRIDAY-INSTALL.json').read_bytes())

    assert len(before_receipt['layers']) == 222 and len(before_marker['plugin_files']) == 52

    assert sha(H / 'hermes-agent.source.json') == 'b9bbf62464a86621b654f4034480a7e7ac2c280f19ab55b1d7908bd09ae06721'

    layer = json.loads((C / 'patches/hermes/ordinary-f04-owned-ingress-stop-terminal-after-source222-manifest.json').read_bytes())

    targets = {x['path']: x['sha256'] for x in layer['files']}

    spec = json.loads(SPEC.read_bytes())

    assert spec['schema'] == 'frw.f04223.pair-spec.v1' and spec['source_only'] is True, 'selected_current220_pair_spec_role_required'
    assert spec['layer'] == q['layer_names'][0] and spec['outer_schema'] == q['schema'] and spec['successor_schema'] == q['current_source_successor']['schema'], 'selected_current220_pair_spec_request_join_required'

    assert layer['files'] == spec['native_files']

    assert len(targets) == len(layer['files']) == len(spec['native_files']) and len(targets)>0

    assert bound['selected_target_count'] == len(targets)+6

    native_additions = {row['path'] for row in layer['files'] if row['new_file']}

    assert len(native_additions) == spec['counts']['added'] and all(type(row['new_file']) is bool for row in layer['files'])

    assert set(before_receipt['files']) & native_additions == set()

    assert len(before_receipt['files']) == 17893

    assert before_marker['input_sha256'] == q['previous_input']['sha256']

    assert q['schema'] == 'friday.ordinary-telegram-source-update.v46'

    assert q['current_source_successor']['schema'] == 'friday.current-source-native-successor.v25'

    assert q['current_source_successor']['previous_native_update'] == bound['genuine_actual222_predecessor']

    assert sha(q['current_source_successor']['previous_native_update']['path']) == q['current_source_successor']['previous_native_update']['sha256']

    assert q['project_file_updates'] == ['scripts/friday_ordinary_install.py']

    for row in layer['files']:
        path = N / row['path']
        assert not os.path.lexists(path) if row['new_file'] else sha(path) == row['before_sha256'], row['path']

    project_targets = set(q['project_file_updates'] + q['layer_manifest_updates'] + [f'patches/hermes/{name}.patch' for name in q['layer_names']])

    return dict(q=q,cur=cur,previous=previous,tx=tx,before_receipt=before_receipt,before_marker=before_marker,source_spec_ref=source_spec_ref,
                layer=layer,targets=targets,spec=spec,native_additions=native_additions,project_targets=project_targets)
