"""Pure exact installed227 ICS READ Source binder; never calls a runtime entrypoint.

Only explicit accepted Code and an explicit Root Source-input manifest are read.
Baseline/eligibility/assessment references are never dereferenced. Root authenticates
those values, original unexecuted eligibility and mutable state at its own boundary.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import types

SOURCE_REFS = {
    'read_constructor': {'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-READ227-EXACT-PROFILE-DELTA-CORE-20261116/ordinary/root_read227_delta.py', 'bytes': 16555, 'sha256': '37ccb093c78b6ced2dd36fccbd6db2f0e9653b4f65c5d407bc7dfe01bcc51572'},
    'common_constructor': {'path': '/home/jericho/.cache/FRW-ASTRA-EML-CREATE-EDIT-ORDINARY-SOURCE-20261116/root_source_delta.py', 'bytes': 9076, 'sha256': '94706f69fe3c9a578f63e35b39b405eeee3fff0eb1a7e32ad73248d7c1379726'},
    'current_parent': {'path': '/home/jericho/.cache/FRW-ASTRA-EML-FIRST-READ-PREPARATION-20261116/root_eml_current.py', 'bytes': 6913, 'sha256': '93f55acf28062fa941113c98e05fe67d95f2486cd46486be7e2bdbf304652411'},
    'actor_parent': {'path': '/home/jericho/.cache/FRW-ASTRA-EML-FIRST-READ-PREPARATION-20261116/root_eml_once.py', 'bytes': 11231, 'sha256': '0719fbe5c589787998fa60df6ef1e2ac2f43f8c0cb5ff613652c5126886f869c'},
    'preparation': {'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-READ227-EXACT-PROFILE-DELTA-CORE-20261116/ordinary/ics_vcf_read227_source.py', 'bytes': 18093, 'sha256': 'b57f229a9bdcfd7e1ba48f968941c76778e10df278746af4523ccfd9c1b69f2d'},
    'metadata': {'path': '/home/jericho/.cache/FRW-ASTRA-FIXED227-METADATA-SIBLING-SOURCE-20261116/fixed227_metadata_source.py', 'bytes': 37670, 'sha256': '787cdfdfa5e8150f4f472767002438a39951c5bac89ff95fbfa2d64d214c7a8e'},
}
RESOURCES = dict(operation_seconds=600, reply_window_seconds=480, ack_seconds=10,
                 reserve_seconds=5, outer_seconds=900, cpu_seconds=120,
                 max_rss_bytes=536870912, disk_bytes=104857600)
NAMES = dict(current_checker='root_ics227_current.py', actor='root_ics227_once.py',
             preparation='ics_vcf_read227_source.py', scenario='bindings/scenario.json',
             source_preparation='ICS227-BOUND-PREPARATION.json')


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ref_for(path, raw):
    return dict(path=path, bytes=len(raw), sha256=digest(raw))


def literals(raw):
    result = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result


def load_pure(raw, reference, name):
    need(type(raw) is bytes and len(raw) == reference['bytes'] and digest(raw) == reference['sha256'],
         'ICS227_EXACT_ACCEPTED_CODE_REQUIRED:'+name)
    module = types.ModuleType(name)
    module.__file__ = '<exact-accepted-pure-Source>'
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def generate(inputs, *, input_ref, source_bytes):
    """Return bound Source bytes and pins. No filesystem/runtime observation."""
    need(type(source_bytes) is dict and set(source_bytes) == set(SOURCE_REFS),
         'ICS227_EXACT_CODE_SET_REQUIRED')
    for key, reference in SOURCE_REFS.items():
        raw = source_bytes[key]
        need(type(raw) is bytes and len(raw) == reference['bytes'] and digest(raw) == reference['sha256'],
             'ICS227_EXACT_ACCEPTED_CODE_REQUIRED:'+key)
    delta = load_pure(source_bytes['read_constructor'], SOURCE_REFS['read_constructor'], '_ICS227ReadConstructor')
    common = delta.accepted(source_bytes['common_constructor'])
    prep = load_pure(source_bytes['preparation'], SOURCE_REFS['preparation'], '_ICS227Preparation')
    common.ref(input_ref)
    need(type(inputs) is dict and set(inputs) == {'schema','baseline','family','history_rows','matching_rows','native_python','no_effect','old_unknown_count','reconciliation','role_assessment','root_dir','run_id','selectors','source_stat','eligibility'},
         'ICS227_EXACT_ROOT_MANIFEST_FIELDS_REQUIRED')
    need(input_ref['bytes'] == len(encoded(inputs)) and input_ref['sha256'] == digest(encoded(inputs)),
         'ICS227_EXACT_ROOT_MANIFEST_REF_REQUIRED')
    need(inputs['schema'] == 'frw.Root.ICS227.Source-binding-inputs.v1' and inputs['family'] == 'ics'
         and inputs['no_effect'] is True and inputs['matching_rows'] == []
         and type(inputs['history_rows']) is int and inputs['history_rows'] >= 40
         and type(inputs['old_unknown_count']) is int and inputs['old_unknown_count'] >= 0,
         'ICS227_ROOT_ICS_SOURCE_MANIFEST_REQUIRED')
    common.run(inputs['run_id'])
    root_dir = inputs['root_dir']
    native_python = inputs['native_python']
    eligibility_ref = inputs['eligibility']
    role_assessment_ref = inputs['role_assessment']
    common.ref(inputs['reconciliation'])
    common.path(root_dir)
    need(root_dir != '/' and not Path(root_dir).is_relative_to('/home/jericho/jericho/Friday_rework/.runtime')
         and not Path(root_dir).is_relative_to('/home/jericho/.local/share/friday-telegram-bot-test'),
         'ICS227_PRIVATE_SOURCE_ROOT_REQUIRED')
    common.path(native_python)
    metadata = literals(source_bytes['metadata'])
    need(native_python == metadata['NATIVE_PYTHON'], 'ICS227_EXACT_METADATA_NATIVE_PYTHON_REQUIRED')
    delta.validate_metadata_checker(source_bytes['metadata'])
    baseline_ref = common.ref(inputs['baseline'])
    eligibility_ref = common.ref(eligibility_ref)
    role_assessment_ref = common.ref(role_assessment_ref)
    need(len({input_ref['path'], baseline_ref['path'], eligibility_ref['path'], role_assessment_ref['path']}) == 4,
         'ICS227_SEPARATE_ROOT_INPUT_REFS_REQUIRED')
    need(type(inputs['selectors']) is dict and set(inputs['selectors']) == {'tester_id','peer_id','peer_username'},
         'ICS227_EXACT_EXPLICIT_SELECTORS_REQUIRED')
    upload = prep.input_data('ics', inputs['source_stat'])
    scenario = prep.scenario_data(upload, **inputs['selectors'])
    prep.validate_scenario_data(scenario)
    preparation = prep.preparation(scenario)
    current_path = str(Path(root_dir)/NAMES['current_checker'])
    current_raw = delta.current_source(source_bytes['common_constructor'], source_bytes['current_parent'],
        family='ics', run_id=inputs['run_id'], baseline_ref=baseline_ref,
        eligibility_ref=eligibility_ref, installed227_ref=role_assessment_ref,
        upload_input=upload, metadata_checker_ref=SOURCE_REFS['metadata'], metadata_checker_raw=source_bytes['metadata'])
    actor_raw = delta.actor_source(source_bytes['common_constructor'], source_bytes['actor_parent'],
        family='ics', run_id=inputs['run_id'], source_root=root_dir,
        current_path=current_path, native_python=native_python)
    # Inspect generated Code as AST only. Never import/call current or actor.
    current = literals(current_raw)
    need(current['ROOT_BOUND'] is True and current['RUN'] == inputs['run_id']
         and current['FAMILY'] == 'ics' and current['OPERATION'] == 'read'
         and current['BASE'] == baseline_ref and current['ELIGIBILITY'] == eligibility_ref
         and current['INSTALLED227'] == role_assessment_ref and current['UPLOAD_INPUT'] == upload
         and current['CHECKER'] == SOURCE_REFS['metadata'] and current['RECEIVED_SOURCE'] is None,
         'ICS227_BOUND_CURRENT_AST_JOIN_REQUIRED')
    actor = literals(actor_raw)
    need(actor['RUN'] == inputs['run_id'] and actor['PYTHON'] == native_python,
         'ICS227_BOUND_ACTOR_AST_JOIN_REQUIRED')
    files = {NAMES['current_checker']: current_raw, NAMES['actor']: actor_raw,
             NAMES['preparation']: source_bytes['preparation'],
             NAMES['scenario']: encoded(scenario), NAMES['source_preparation']: encoded(preparation)}
    output_refs = {key: ref_for(str(Path(root_dir)/name), files[name]) for key,name in NAMES.items()}
    need(not {r['path'] for r in output_refs.values()} & {input_ref['path'],baseline_ref['path'],eligibility_ref['path'],role_assessment_ref['path']},
         'ICS227_INPUT_OUTPUT_ALIAS_REFUSED')
    bindings = dict(schema='frw.Root.ICS227.bound-Source-pins.v1', source_only=True,
        state='EXACT_BOUND_SOURCE_RUNTIME_UNOBSERVED', operator='Root', run_id=inputs['run_id'],
        root_dir=root_dir, family='ics', operation='read', native_python=native_python,
        Root_inputs=dict(manifest=input_ref, baseline=baseline_ref, eligibility=eligibility_ref,
                         installed227_assessment=role_assessment_ref, selectors=inputs['selectors'], source_stat=inputs['source_stat']),
        accepted_Code=SOURCE_REFS, sources=output_refs, scenario_sha256=digest(encoded(scenario)),
        guards=dict(helper=current['HELPER'], transport=current['TRANSPORT'], metadata=current['CHECKER'],
                    metadata_basis=metadata['CLOSURE'], metadata_acceptance=metadata['ACCEPTANCE']),
        resources=RESOURCES, current_admission=False, execution_grant=False,
        authority_issued=False, proof_created=False, once_created=False, operation_clock_created=False,
        future_ingress_read_reply_custody='POSTCONDITIONS_ONLY',
        old_effects_UNKNOWN_clocks='PRESERVED_NOT_REPLAY_AUTHORITY',
        remaining_Root_inputs=['Authenticate baseline, genuine unexecuted eligibility, role-assessment and current mutable state at the proper Root boundary.',
            'Independent review of these exact bound bytes and exact Source/review references.',
            'Root ordinary authority and descriptor with genuine existing locks/ONCE/finite clock at their proper boundary.',
            'After admitted single operation only: genuine ingress, ordered complete same-source read pages, answer semantics and custody.'],
        not_read=['baseline','eligibility','role_assessment','H','history','private_oracle','credentials'])
    files['ROOT-ICS227-BOUND-SOURCE-PINS.json'] = encoded(bindings)
    bundle_sources = dict(output_refs, baseline=baseline_ref, eligibility=eligibility_ref, installed227=role_assessment_ref, emitters=SOURCE_REFS['read_constructor'], metadata_checker=SOURCE_REFS['metadata'])
    bundle = dict(schema='frw.Root.ICS227.exact-bound-Source-only.v1', operator='Root', run_id=inputs['run_id'], sources=bundle_sources, resources=RESOURCES, native_python=native_python, scenario_sha256=bindings['scenario_sha256'], Root_inputs=input_ref, reconciliation=inputs['reconciliation'], authority_issued=False, proof_created=False, once_or_operation_clock_created=False, API_or_model_or_send=False, current_admission=False, execution_grant=False, remaining=bindings['remaining_Root_inputs'])
    files['ROOT-ICS227-EXACT-SOURCE-BINDINGS.json'] = encoded(bundle)
    return files, bindings


def read_explicit(path, *, maximum):
    p = Path(path)
    need(str(p) == path and p.is_absolute() and not any(q.is_symlink() for q in (p,*p.parents)),
         'ICS227_EXPLICIT_CANONICAL_INPUT_PATH_REQUIRED')
    with p.open('rb') as stream:
        raw = stream.read(maximum+1)
    need(0 < len(raw) <= maximum, 'ICS227_SOURCE_INPUT_BOUND_REQUIRED')
    return raw


def write_new(root_dir, files):
    root = Path(root_dir)
    need(root.is_dir() and not any(q.is_symlink() for q in (root,*root.parents)),
         'ICS227_EXISTING_PRIVATE_ROOT_REQUIRED')
    st = root.lstat()
    need(st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o700,
         'ICS227_PRIVATE_ROOT_IDENTITY_REQUIRED')
    for name in files:
        parent = (root/name).parent
        need(parent.is_dir() and not any(q.is_symlink() for q in (parent,*parent.parents)) and parent.stat().st_uid == os.getuid() and stat.S_IMODE(parent.stat().st_mode) == 0o700, 'ICS227_EXISTING_PRIVATE_OUTPUT_PARENT_REQUIRED')
    need(all(not os.path.lexists(root/name) for name in files), 'ICS227_OUTPUT_EXISTS_NO_OVERWRITE')
    for name,raw in files.items():
        fd = os.open(root/name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    return {name:ref_for(str(root/name),raw) for name,raw in files.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--inputs-sha256', required=True)
    args = parser.parse_args(argv)
    raw = read_explicit(args.inputs, maximum=1024**2)
    need(digest(raw) == args.inputs_sha256, 'ICS227_ROOT_INPUT_MANIFEST_CHANGED')
    sources = {key:read_explicit(ref['path'],maximum=ref['bytes']) for key,ref in SOURCE_REFS.items()}
    files, bindings = generate(json.loads(raw), input_ref=ref_for(args.inputs,raw), source_bytes=sources)
    written = write_new(bindings['root_dir'],files)
    print(json.dumps(dict(state=bindings['state'],sources=written,current_admission=False,execution_grant=False)))


if __name__ == '__main__':
    main()
