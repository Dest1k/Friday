#!/usr/bin/env python3
"""Construct a bounded, inert Word228 sibling from the reviewed R2 Source.

This command writes Source Code and templates only. Root references are metadata:
the constructor never follows raw input/actual/current/authority/clock references.
"""
import argparse
import ast
import hashlib
import json
import os
import stat
from pathlib import Path

OWN = Path(__file__).parent
BASE = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE228-ROOT-FRAME-SOURCE-20261116/revision2/bound-source-frame228-c1cb63f7-5bb9f069')
BASE_PINS = 'cec8c97968dd1ec860eccf098868a1abfdf0962fc8a4424f8adf7dc4c40c83d1'
OBSERVER = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE227-ROOT-SOURCE-INTEGRATION-20261116/bound-source-frame227-0f098a35-r5/admission-retained/observe-current-retained-units.py')
OBSERVER_SHA = '211f4e00216ff8749782de4d44b0c9a2d872991ea42e9a53e9d0c0cb727ad148'
BANK = Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json')
BANK_SHA = 'cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'
COMMAND_SHA = 'ab55bf08dd9861d6c72b2c7a60c7cb3c1b33bd59ba251c5fe2dd9bcd99d1e45a'
PAIR = Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/drafts/word-output-visibility228-source-20261117')
LAYER = 'word-output-visibility-after-source227'
MANIFEST_SHA = 'f4e2806261378841508d000d485f613a9103b103fd0a19694af993990c0655ae'
PATCH_SHA = '73b4881b15d70aec053d0ff482a18141d95fdb6218b0e0a4cb6c41912097f024'
OLD_PRODUCT = '0f098a354033317fe4cf20dd7a225ad5b2442361'
OLD_COMM_PRODUCT = 'c1cb63f7ac7ed7c378d6638afeef7bb73c77080c'
KEYS = {'product_source_commit', 'execution_commit', 'new_request', 'private_input', 'public_input', 'before_public_input', 'actual227_binding', 'closed227_authentication', 'durable227_cutoff'}
SELECTION_KEYS = {'source_spec', 'source_spec_schema', 'private_helper_sha256', 'public_helper_sha256', 'after_project_map_sha256', 'product_source_commit', 'execution_commit', 'publication_builder', 'publication_consumer'}
CODE = ('actor_static_inputs228.py', 'bind_current_inputs228.py', 'boundary_contract.py', 'core228-first-actual-root.py', 'cutoff_contract.py', 'frame_source.py', 'native228_binding.py', 'native_scope_post228.py', 'native_scope_preflight227.py', 'predecessor227.py', 'prepare_root228.py', 'publication/build-layer-publication-request.py', 'publication/friday_v3_layer_publication.py', 'read_source_bound228.py', 'read_static_source_inputs228.py', 'recovery_scope.py', 'resume_native228_services.py', 'root228_data.py', 'root228_metadata.py', 'root228_projection.py', 'root228_source_seam.py', 'run_native228_once.py')
TEMPLATES = ('ROOT-228-CONSUMED-HISTORY-TEMPLATE.json', 'ROOT-228-CURRENT-SERVICE-ANCHOR-TEMPLATE.json', 'ROOT-228-FRESH-ADMISSION-TEMPLATE.json', 'ROOT-228-FRESH-READBACK-TEMPLATE.json', 'ROOT-228-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json', 'ROOT-228-NEW-OPERATION-PLAN-TEMPLATE.json', 'ROOT-228-RUNTIME-AUTHORITY-TEMPLATE.json')
COUNTS = dict(added=0, after_layers=228, after_project=537, base=17730, before_layers=227, before_project=535, modified=2, native=17895, plugins=52, retained=17893, selected_CAS=8)


def require(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(value, size=64):
    return type(value) is str and len(value) == size and all(c in '0123456789abcdef' for c in value)


def ref(value):
    return type(value) is dict and set(value) == {'path', 'sha256'} and type(value['path']) is str and value['path'].startswith('/home/jericho/.cache/') and '..' not in Path(value['path']).parts and digest(value['sha256'])


def checked(path, expected):
    p = Path(path)
    a = p.lstat()
    require(stat.S_ISREG(a.st_mode) and a.st_uid == os.getuid() and a.st_nlink == 1 and not any(q.is_symlink() for q in (p, *p.parents)), 'owned_regular_singlelink_Source_required')
    raw = p.read_bytes()
    b = p.lstat()
    fields = ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    require(all(getattr(a, k) == getattr(b, k) for k in fields) and sha(raw) == expected, 'exact_Source_identity_and_sha_required:' + str(p))
    return raw


def write(path, raw):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)


def word_preimages(rows, patch):
    # Exact textual patch byte delta; no current or cached native input is read.
    delta = {}
    current = None
    for line in patch.splitlines(keepends=True):
        require(not line.startswith(b'\\ No newline'), 'explicit_LF_patch_required')
        if line.startswith(b'+++ b/'):
            current = line[len(b'+++ b/'):].strip().decode()
            delta[current] = 0
        elif current is not None and line.startswith(b'+'):
            delta[current] += len(line) - 1
        elif current is not None and line.startswith(b'-') and not line.startswith(b'--- '):
            delta[current] -= len(line) - 1
    require(set(delta) == {r['path'] for r in rows}, 'exact_Word_patch_scope')
    return {r['path']: dict(sha256=r['before_sha256'], bytes=r['bytes'] - delta[r['path']], mode=r['mode']) for r in rows}


def selection_checked(value):
    require(type(value) is dict and set(value) == SELECTION_KEYS, 'exact_Word_Source_selection_keys')
    require(ref(value['source_spec']) and type(value['source_spec_schema']) is str and 'UNBOUND' not in value['source_spec_schema'], 'final_Word_Source_spec_required')
    require(ref(value['publication_builder']) and ref(value['publication_consumer']), 'exact_final_Sol_publication_Source_required')
    require(all(digest(value[k]) for k in ('private_helper_sha256', 'public_helper_sha256', 'after_project_map_sha256')), 'exact_final_Word_helper_and_map_pins_required')
    require(value['private_helper_sha256'] != value['public_helper_sha256'], 'genuine_private_public_helpers_required')
    require(digest(value['product_source_commit'], 40) and value['product_source_commit'] not in (OLD_PRODUCT, OLD_COMM_PRODUCT) and digest(value['execution_commit'], 40), 'distinct_Word_product_and_execution_selectors_required')
    return value


def gate_source(selectors, complete, product):
    return ast.parse('''def require_root_source_bindings():
    value = ROOT_SOURCE_BINDINGS
    if not WORD_SOURCE_SELECTION_COMPLETE or type(value) is not dict or set(value) != ROOT_BINDING_KEYS:
        raise ValueError('Root228_Word_Source_selectors_UNBOUND_before_runtime_IO')
    def digest(v, n=64):
        return type(v) is str and len(v) == n and all(c in '0123456789abcdef' for c in v)
    if not (digest(value['product_source_commit'], 40) and value['product_source_commit'] == WORD_PRODUCT_SOURCE_COMMIT and value['product_source_commit'] not in (''' + repr(OLD_PRODUCT) + ',' + repr(OLD_COMM_PRODUCT) + ''') and digest(value['execution_commit'], 40)):
        raise ValueError('Root228_Word_product_execution_UNBOUND_before_runtime_IO')
    for key in ROOT_BINDING_KEYS - {'product_source_commit', 'execution_commit'}:
        r = value[key]
        if not (type(r) is dict and set(r) == {'path', 'sha256'} and type(r['path']) is str and r['path'].startswith('/home/jericho/.cache/') and 'UNBOUND' not in r['path'] and '..' not in r['path'].split('/') and digest(r['sha256'])):
            raise ValueError('Root228_exact_Source_ref_UNBOUND_before_runtime_IO:' + key)
    return value
''').body[0]


class WordSelectors(ast.NodeTransformer):
    def __init__(self, name, substitutions, assignments, selectors, complete, product):
        self.name, self.substitutions, self.assignments = name, substitutions, assignments
        self.selectors, self.complete, self.product = selectors, complete, product
        self.function = None

    def visit_FunctionDef(self, node):
        if node.name == 'require_root_source_bindings':
            return gate_source(self.selectors, self.complete, self.product)
        old = self.function
        self.function = node.name
        self.generic_visit(node)
        self.function = old
        return node

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name == 'ROOT_SOURCE_BINDINGS':
                node.value = ast.parse(repr(self.selectors), mode='eval').body
                return node
            if name in self.assignments:
                node.value = ast.parse(repr(self.assignments[name]), mode='eval').body
                return node
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if type(node.value) is str:
            node.value = self.substitutions.get(node.value, node.value)
            if not digest(node.value) and not digest(node.value, 40):
                node.value = node.value.replace('COMMUNICATION_CREATE_CONTRACT', 'WORD_OUTPUT_VISIBILITY').replace('CAS9', 'CAS8').replace('17892', '17893').replace('three_MOD', 'two_MOD').replace('three_native', 'two_native').replace('three228 MOD', 'two228 MOD')
        count_functions = {
            'native228_binding.py': {'validate_native_rows', 'plan_native_projection', 'bind_static'},
            'root228_projection.py': {'validate', 'validate_candidate_source'},
            'root228_metadata.py': {'validate_candidate'},
            'root228_data.py': {'validate_descriptor'},
            'actor_static_inputs228.py': {'read_source_inputs'},
            'root228_source_seam.py': {'read_static_source_inputs', 'derive_static_binding', 'checked_native_settlement'},
            'read_source_bound228.py': {'main'},
        }
        if self.function in count_functions.get(self.name, set()) and type(node.value) is int:
            node.value = {3: 2, 9: 8, 17892: 17893}.get(node.value, node.value)
        return node


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, default=OWN / 'word228-unbound')
    parser.add_argument('--source-selection', type=Path)
    parser.add_argument('--root-bindings', type=Path)
    args = parser.parse_args()
    require(args.destination.parent == OWN and not args.destination.exists(), 'new_owned_Source_sibling_only')
    base_pins = json.loads(checked(BASE / 'SOURCE-PINS.json', BASE_PINS))
    manifest_raw = checked(PAIR / (LAYER + '-manifest.json'), MANIFEST_SHA)
    patch_raw = checked(PAIR / (LAYER + '.patch'), PATCH_SHA)
    rows = json.loads(manifest_raw)['files']
    require(len(rows) == 2 and all(r['new_file'] is False for r in rows), 'exact_Word_two_MOD_no_ADD')
    preimages = word_preimages(rows, patch_raw)
    selected = {k: 'UNBOUND_ROOT' for k in sorted(SELECTION_KEYS)}
    spec_raw = None
    if args.source_selection:
        # Only this explicit Source metadata file and its named Source spec are read.
        selected = selection_checked(json.loads(json.dumps(json.loads(args.source_selection.read_bytes()), sort_keys=True)))
        spec_raw = checked(selected['source_spec']['path'], selected['source_spec']['sha256'])
        spec = json.loads(spec_raw)
        require(spec['schema'] == selected['source_spec_schema'] and spec['layer'] == LAYER and spec['native_files'] == rows and spec['counts'] == COUNTS and spec['source_only'] is True and all(spec[k] is False for k in ('current_admission', 'execution_grant', 'install_ready')), 'exact_inert_final_Word_Source_spec')
        require(spec['ordinary_helpers']['private']['after']['sha256'] == selected['private_helper_sha256'] and spec['ordinary_helpers']['public']['after']['sha256'] == selected['public_helper_sha256'], 'selected_Word_helper_spec_join')
    selectors = {k: 'UNBOUND_ROOT' for k in sorted(KEYS)}
    extra = {}
    if args.root_bindings:
        require(spec_raw is not None, 'Source_selection_before_Root_binding')
        config = json.loads(json.dumps(json.loads(args.root_bindings.read_bytes()), sort_keys=True))
        require(set(config) == {'selectors', 'source_refs', 'historical_refs'}, 'exact_metadata_only_Root_binding_ABI')
        selectors, extra = config['selectors'], config
        scope = dict(ROOT_SOURCE_BINDINGS=selectors, ROOT_BINDING_KEYS=KEYS, WORD_SOURCE_SELECTION_COMPLETE=True, WORD_PRODUCT_SOURCE_COMMIT=selected['product_source_commit'])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[gate_source(selectors, True, selected['product_source_commit'])], type_ignores=[])), '<selector-only-gate>', 'exec'), scope)
        scope['require_root_source_bindings']()
        require(selectors['execution_commit'] == selected['execution_commit'], 'same_exact_execution_selector')
        for category in ('source_refs', 'historical_refs'):
            require(type(config[category]) is dict and all(ref(dict(path=p, sha256=h)) for p, h in config[category].items()), 'exact_cache_metadata_refs_only')
        require(set(config['source_refs']).isdisjoint(config['historical_refs']), 'source_historical_roles_distinct')
    complete = spec_raw is not None and args.root_bindings is not None
    substitutions = {
        'communication-create-contract-after-source227': LAYER,
        'patches/hermes/communication-create-contract-after-source227-manifest.json': 'patches/hermes/' + LAYER + '-manifest.json',
        'patches/hermes/communication-create-contract-after-source227.patch': 'patches/hermes/' + LAYER + '.patch',
        'frw.sol.communication228.final-integration-Source-spec.v1': selected['source_spec_schema'],
        'a7eff51998620b4af519c066e480af9895beb63451b188e7e26a2c9efb52edb0': selected['private_helper_sha256'],
        '26e0a0c574d915360e109cfc78156a0435f22e4ffef4f44858706065a7ade95d': selected['public_helper_sha256'],
        '4892163bc556e7d7dbf22b2d85a519eeae2a12c23252727f198dc3f0a45086f1': selected['after_project_map_sha256'],
        '7376080ed7b4c49bf2af9dd26d89e000e194d31ca110be553e1c57c8613df07e': MANIFEST_SHA,
        '36fff704a81cbce1098f81ce376eb5128264c8b35ea618accdab527acadb6a55': PATCH_SHA,
        OLD_COMM_PRODUCT: selected['product_source_commit'],
        'all_17892_retained_native_rows_exact': 'all_17893_retained_native_rows_exact',
        'exact_three_MOD_CAS9': 'exact_two_MOD_CAS8',
        'strict_three_MOD_zero_ADD': 'strict_two_MOD_zero_ADD',
    }
    for name in CODE + TEMPLATES + ('ROOT-FRESH-REQUEST.json', 'ROOT228-DATA-BINDINGS.json', 'SOURCE-SPEC228.json', 'STATIC-BINDING228.json', 'ACTUAL227-EIGHT-ROW-BINDING.json', 'SOURCE-PINS.json'):
        substitutions[str(BASE / name)] = str(args.destination / name)
    substitutions[str(BASE)] = str(args.destination)
    assignments = dict(SOURCE_BOUND=bool(complete), PRIVATE_HELPER=selected['private_helper_sha256'], PUBLIC_HELPER=selected['public_helper_sha256'], NATIVE_ROWS=rows, COUNTS=COUNTS, NATIVE_PREIMAGES=preimages, REQUEST_SHA=selectors['new_request']['sha256'] if complete else 'UNBOUND_ROOT', INPUT_SHA=selectors['private_input']['sha256'] if complete else 'UNBOUND_ROOT', AFTER_MAP_SHA=selected['after_project_map_sha256'], MANIFEST_SHA=MANIFEST_SHA, PATCH_SHA=PATCH_SHA, CONSUMER_SHA=selected['publication_consumer']['sha256'] if spec_raw is not None else 'UNBOUND_ROOT')
    args.destination.mkdir(mode=0o700)
    changes, reused, dependencies = {}, {}, {}
    for name in CODE:
        if name.startswith('publication/'):
            if spec_raw is None:
                continue  # Explicitly missing until Sol's selected Word Source is ready.
            role = 'publication_builder' if name.endswith('build-layer-publication-request.py') else 'publication_consumer'
            raw = checked(selected[role]['path'], selected[role]['sha256'])
            require(b'communication-create-contract-after-source227' not in raw and LAYER.encode() in raw, 'Word_publication_Source_not_deferred_comm228')
            compile(raw, name, 'exec')
            write(args.destination / name, raw)
            dependencies[selected[role]['path']] = selected[role]['sha256']
            continue
        original = checked(BASE / name, base_pins['source_refs'][str(BASE / name)]).decode()
        tree = WordSelectors(name, substitutions, assignments, selectors, complete, selected['product_source_commit']).visit(ast.parse(original))
        if name == 'read_static_source_inputs228.py':
            tree.body[0:0] = ast.parse('ROOT_SOURCE_BINDINGS = ' + repr(selectors) + '\nROOT_BINDING_KEYS = set(' + repr(tuple(sorted(KEYS))) + ')\nSOURCE_BOUND = ' + repr(bool(complete))).body + [gate_source(selectors, complete, selected['product_source_commit'])] + ast.parse("def require_source_bound():\n    require_root_source_bindings()\n    if SOURCE_BOUND is not True: raise ValueError('Root228_Word_Source_UNBOUND_before_IO')\n").body
            entry = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
            entry.body[0:0] = ast.parse('require_source_bound()').body
        if any(isinstance(n, ast.FunctionDef) and n.name == 'require_root_source_bindings' for n in tree.body):
            tree.body[0:0] = ast.parse('WORD_SOURCE_SELECTION_COMPLETE = ' + repr(bool(complete)) + '\nWORD_PRODUCT_SOURCE_COMMIT = ' + repr(selected['product_source_commit'])).body
        if name == 'root228_source_seam.py':
            settlement = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'checked_native_settlement')
            for node in ast.walk(settlement):
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'names' for t in node.targets) and isinstance(node.value, ast.Set):
                    node.value = ast.Set(elts=[ast.Constant(r['path']) for r in sorted(rows, key=lambda r: r['path'])])
        if name == 'frame_source.py':
            verifier = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_manifest')
            verifier.body[-1:-1] = ast.parse(
                "assert str(frame/'admission-retained/observe-current-retained-units.py') in value['source_refs'], 'retained_observer_Source_required_before_once'\n"
                "assert str(frame/'ROOT-FUTURE-COMMANDS.json') in value['source_refs'], 'exact_command_prefix_Source_required_before_once'\n"
                "assert value['source_refs'].get(" + repr(str(BANK)) + ") == " + repr(BANK_SHA) + ", 'exact_bank_manifest_Source_required_before_once'\n"
            ).body
        generated = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
        compile(generated, name, 'exec')
        write(args.destination / name, generated.encode())
        before = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(original).body if isinstance(n, ast.FunctionDef)}
        after = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(generated).body if isinstance(n, ast.FunctionDef)}
        reused[name] = [n for n in before if before[n] == after.get(n)]
        changes[name] = [n for n in before if before[n] != after.get(n)]
        dependencies[str(BASE / name)] = base_pins['source_refs'][str(BASE / name)]
    # Retained observer Code is byte-exact R5, never run by this constructor.
    write(args.destination / 'admission-retained/observe-current-retained-units.py', checked(OBSERVER, OBSERVER_SHA))
    checked(BANK, BANK_SHA)  # Source bank manifest metadata only, no bank contents.
    commands = json.loads(checked(BASE / 'ROOT-FUTURE-COMMANDS.json', COMMAND_SHA))
    commands.update(product_source_commit=selected['product_source_commit'], execution_commit=selected['execution_commit'])
    write(args.destination / 'ROOT-FUTURE-COMMANDS.json', encoded(commands))
    write(args.destination / 'WORD228-ROOT-BINDING-TEMPLATE.json', encoded(dict(selectors={k: 'UNBOUND_ROOT' for k in sorted(KEYS)}, source_refs={}, historical_refs={})))
    write(args.destination / 'WORD228-SOURCE-SELECTION-TEMPLATE.json', encoded({k: 'UNBOUND_ROOT' for k in sorted(SELECTION_KEYS)}))
    if spec_raw is not None:
        write(args.destination / 'SOURCE-SPEC228.json', spec_raw)
    code_pins = {str(args.destination / name): sha((args.destination / name).read_bytes()) for name in CODE + ('admission-retained/observe-current-retained-units.py', 'ROOT-FUTURE-COMMANDS.json') if (args.destination / name).exists()}
    code_pins[str(BANK)] = BANK_SHA
    for path, pin in extra.get('source_refs', {}).items():
        require(path not in code_pins or code_pins[path] == pin, 'Root_metadata_must_not_override_constructed_Code_or_bank_pin')
        code_pins[path] = pin
    if spec_raw is not None:
        code_pins[str(args.destination / 'SOURCE-SPEC228.json')] = sha(spec_raw)
    pins = dict(schema='frw.root228.coherent-after-actual227-source-pins.v1', source_only=True, runtime_grant=False, execution_grant=False, current_admission=False, source_refs=code_pins, historical_refs=extra.get('historical_refs', {}), source_spec_ref=dict(path=str(args.destination / 'SOURCE-SPEC228.json'), sha256=sha(spec_raw) if spec_raw is not None else 'UNBOUND_ROOT'), product_source_commit=selected['product_source_commit'], execution_commit=selected['execution_commit'], root_inputs_bound=bool(complete), counts=COUNTS)
    require(set(pins['source_refs']).isdisjoint(pins['historical_refs']), 'distinct_frozen_source_and_history_roles')
    write(args.destination / 'SOURCE-PINS.json', encoded(pins))
    write(args.destination / 'AST-REUSE-WORD228.json', encoded(dict(comparison='Exact R2 AST; only declared Word selector/count/Source gate changes. Operational guards, histories, clocks and budgets retain original AST.', reused=reused, changed=changes)))
    write(args.destination / 'CONSTRUCTION-DEPENDENCIES.json', encoded(dict(source_only=True, runtime=False, code=dependencies, observer=dict(path=str(OBSERVER), sha256=OBSERVER_SHA), bank=dict(path=str(BANK), sha256=BANK_SHA), command_prefix=dict(path=str(BASE / 'ROOT-FUTURE-COMMANDS.json'), sha256=COMMAND_SHA), manifest=dict(path=str(PAIR / (LAYER + '-manifest.json')), sha256=MANIFEST_SHA), patch=dict(path=str(PAIR / (LAYER + '.patch')), sha256=PATCH_SHA), native_preimages_derived_from_exact_patch=preimages, Root_descriptors_and_fresh_acceptance_remain_required=True)))
    print(json.dumps(dict(frame=str(args.destination), source_only=True, root_selectors_bound=bool(complete), operational_complete=False, install_ready=False, current_admission=False, execution_grant=False, source_pins_sha256=sha(encoded(pins)))))


if __name__ == '__main__':
    main()
