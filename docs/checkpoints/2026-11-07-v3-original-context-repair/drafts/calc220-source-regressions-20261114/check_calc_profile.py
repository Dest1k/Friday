#!/usr/bin/env python3
"""Small offline source regressions, using public inputs and labelled synthetic vectors.

No Office producer, runtime adapter, provider, user scope, or publication is run.
Invoke with python3 -I -B and three explicit roots; see README.md.
"""
import argparse
import ast
from dataclasses import replace
from decimal import Decimal
import hashlib
import importlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
import sys
import types
import zipfile
from xml.etree import ElementTree as ET


PUBLIC_INPUTS = {
    'S-01-orders_base.xlsx': (5660, '714bdf80668250af362d607f24c5bf4c054f35094215f005b3631f90a67e7dd1'),
    'S-11-orders_complex_features.xlsx': (8926, 'f805315c82d40bb220b52dbe709063c2dbfc08b5c5a746bf0daae0916c9c9497'),
}


class CheckFailure(Exception):
    pass


def require(condition, code):
    if not condition:
        raise CheckFailure(code)


def plain_path(raw, directory=False):
    require(bool(str(raw)), 'empty_root_refused')
    path = Path(os.path.abspath(raw))
    require(path.resolve(strict=True) == path, 'pathlink_refused')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'file_type_refused')
    if not directory:
        require(info.st_nlink == 1, 'file_link_refused')
    return path


def protected_work(raw, native, fixtures):
    require(bool(raw), 'empty_root_refused')
    path = Path(os.path.abspath(raw))
    require(path.parent.resolve(strict=True) == path.parent, 'work_parent_pathlink_refused')
    require(not path.is_relative_to(native) and not path.is_relative_to(fixtures), 'work_source_overlap_refused')
    if not path.exists():
        path.mkdir(mode=0o700)
    path = plain_path(path, directory=True)
    info = path.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'work_owner_mode_refused')
    require(not any(path.iterdir()), 'work_not_empty_refused')
    return path


def source_file(root, relative):
    path = plain_path(root / relative)
    require(path.is_relative_to(root), 'source_origin_refused')
    return path


def load_pure(native):
    # Namespace containers locate real source modules without executing the full
    # runtime's package __init__. No parser or primitive module is substituted.
    require('tools' not in sys.modules, 'tools_already_imported')
    package = types.ModuleType('tools')
    package.__path__ = [str(native / 'tools')]
    package.__package__ = 'tools'
    sys.modules['tools'] = package
    g = importlib.import_module('tools.scoped_spreadsheet_conversion')
    r = importlib.import_module('tools.scoped_spreadsheet_rich')
    origins = {}
    for name, module in tuple(sys.modules.items()):
        if not name.startswith('tools.'):
            continue
        path = plain_path(module.__file__)
        require(path.is_relative_to(native), 'module_origin_refused')
        relative = path.relative_to(native).as_posix()
        origins[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return g, r, origins


def independently_evaluate(inventory):
    """Independent DAG walk; uses parsed public formula objects, no oracle totals."""
    cells = {(name, row, col): cell for name, rows in inventory.sheets for row, col, cell in rows}
    computed, visiting = {}, set()

    def visit(key):
        require(key in cells and cells[key].kind == 'number', 'independent_dependency_type')
        if key in computed:
            return computed[key]
        require(key not in visiting, 'independent_cycle')
        visiting.add(key)
        cell = cells[key]
        if cell.formula is None:
            result = Decimal(str(cell.value))
        else:
            f = cell.formula
            if f.operation == 'product':
                left, right = f.refs
                result = visit((left.sheet, left.row, left.column)) * visit((right.sheet, right.row, right.column))
            else:
                require(f.operation == 'sum', 'independent_operation')
                first, last = f.refs
                require(first.sheet == last.sheet, 'independent_sheet_range')
                result = sum((visit((first.sheet, row, col))
                              for row in range(first.row, last.row + 1)
                              for col in range(first.column, last.column + 1)), Decimal(0))
        visiting.remove(key)
        computed[key] = result
        return result

    for key, cell in cells.items():
        if cell.kind == 'number':
            visit(key)
    return computed


def rewrite_xml(data, member, change):
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(data)) as original, zipfile.ZipFile(output, 'w') as changed:
        found = False
        for info in original.infolist():
            raw = original.read(info)
            if info.filename == member:
                root = ET.fromstring(raw)
                change(root)
                raw = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                found = True
            changed.writestr(info, raw)
    require(found, 'mutation_member_missing')
    return output.getvalue()


def source_tree(native, relative, origins):
    raw = source_file(native, relative).read_bytes()
    origins[relative] = hashlib.sha256(raw).hexdigest()
    return ast.parse(raw)


def function(tree, name):
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(found) == 1, 'transport_definition_changed')
    return found[0]


def snippet(name, arguments, statements, environment):
    definition = ast.FunctionDef(name=name,
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=arg) for arg in arguments],
                           kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=statements, decorator_list=[])
    tree = ast.fix_missing_locations(ast.Module(body=[definition], type_ignores=[]))
    exec(compile(tree, '<native-transport-ast>', 'exec'), environment)
    return environment[name]


def transport_checks(native, origins):
    """Compile unchanged pure source branches; all effectful statements omitted."""
    publish = function(source_tree(native, 'hermes_cli/friday_workspace_presentation.py', origins), '_publish')
    start = next((i for i, node in enumerate(publish.body)
                  if isinstance(node, ast.If) and 'result.get' in ast.unparse(node.test)), None)
    require(start is not None and isinstance(publish.body[-1], ast.Return), 'publish_transport_changed')
    merge = snippet('merge', ['result', 'extra', 'output_format'], publish.body[start:], {'json': json})
    writer = function(source_tree(native, 'tools/file_tools.py', origins), 'write_file_tool')
    branches = [node for node in ast.walk(writer) if isinstance(node, ast.If)
                and ast.unparse(node.test) == 'scoped is not None']
    require(len(branches) == 1 and len(branches[0].body) == 1
            and isinstance(branches[0].body[0], ast.Return)
            and ast.unparse(branches[0].body[0].value) == 'scoped', 'opaque_transport_changed')
    passthrough = snippet('passthrough', ['scoped'], branches, {})
    # Deliberately synthetic opaque metadata, not a native destination inventory
    # or a projection of any retained Office output.
    fidelity = {'declared_losses': ['synthetic_loss'], 'unassessed': ['synthetic_unknown'],
                'dimension_metadata': [{'side': 'synthetic', 'unit': 'synthetic', 'data': [1, 2]}],
                'synthetic_extension': {'nested': [False, None, 'opaque']}}
    extra = {'fidelity': fidelity, 'declared_losses': fidelity['declared_losses'],
             'rich_spreadsheet_profile_preserved': False, 'runtime_qualified': False}
    returned = merge({'success': True}, extra, 'xlsx')
    require(passthrough(returned) == returned, 'opaque_transport_changed_bytes')
    require(json.loads(returned) == dict(success=True, **extra), 'fidelity_transport_changed')
    require(json.loads(merge({'success': False}, extra, 'xlsx')) == {'success': False}, 'failure_extra_leaked')
    return {'source_ast_only': True, 'effectful_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-root', required=True, help='Explicit isolated native source root')
    parser.add_argument('--public-evidence', required=True, help='Directory containing the two original public XLSX files')
    parser.add_argument('--work-root', required=True, help='Owned empty directory, mode 0700, outside the source/input roots')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode, 'require_python_I_B')
    os.umask(0o077)
    native = plain_path(args.native_root, directory=True)
    fixtures = plain_path(args.public_evidence, directory=True)
    work = protected_work(args.work_root, native, fixtures)
    g, r, origins = load_pure(native)
    ast_origins = {}
    checks, input_facts = [], {}

    def check(name, action, reason=None):
        observed = 'PASS'
        try:
            detail = action()
        except (g.ODSError, g.ODTError, CheckFailure) as error:
            observed = str(error)
            detail = None
        matched = observed == (reason or 'PASS')
        # Only fixed reason codes and counts are written. Never persist cell data.
        if not re.fullmatch(r'[A-Za-z0-9_]+', observed):
            observed = 'unexpected_noncode_exception'
            matched = False
        row = {'check': name, 'expected': reason or 'PASS', 'observed': observed, 'matched': matched}
        if isinstance(detail, dict):
            row['facts'] = detail
        checks.append(row)

    originals, inventories = {}, {}
    for filename, (size, digest) in PUBLIC_INPUTS.items():
        path = plain_path(fixtures / filename)
        data = path.read_bytes()
        require(len(data) == size and hashlib.sha256(data).hexdigest() == digest, 'public_input_pin_mismatch')
        originals[filename] = data
        input_facts[filename] = {'bytes': size, 'sha256': digest}

        def public_inventory(filename=filename, data=data):
            inv = g.inventory(data, 'xlsx')
            snapshots = tuple((name, row, col, cell.value) for name, rows in inv.sheets
                              for row, col, cell in rows if cell.formula)
            independent = independently_evaluate(inv)
            require(g.evaluate(inv) == independent, 'independent_formula_mismatch')
            require(snapshots == tuple((name, row, col, cell.value) for name, rows in inv.sheets
                    for row, col, cell in rows if cell.formula), 'source_cache_mutated')
            require(any(value is None for _, _, _, value in snapshots), 'expected_missing_source_cache_absent')
            inventories[filename] = inv
            return dict(inv.counts(), missing_source_caches=sum(value is None for _, _, _, value in snapshots),
                        independent_formula_check=True, source_cache_unchanged=True)
        check('public_' + filename[:4].replace('-', '') + '_inventory', public_inventory)

    require(len(inventories) == 2, 'public_inventory_failed')
    base = originals['S-01-orders_base.xlsx']
    rich = inventories['S-11-orders_complex_features.xlsx']

    def mutation(name, member, action, reason):
        data = rewrite_xml(base, member, action)
        path = work / (name + '.synthetic.xlsx')
        path.write_bytes(data)
        path.chmod(0o600)
        check(name, lambda: g.inventory(path.read_bytes(), 'xlsx'), reason)
        path.unlink()

    def first_formula(root):
        return next(cell for cell in root.iter(g.q(g.S, 'c')) if cell.find(g.q(g.S, 'f')) is not None)

    mutation('synthetic_unknown_root_attribute', 'xl/worksheets/sheet1.xml',
             lambda root: root.set('unrepresented', '1'), 'conversion_unsupported_attributes')
    mutation('synthetic_active_formula', 'xl/worksheets/sheet1.xml',
             lambda root: setattr(first_formula(root).find(g.q(g.S, 'f')), 'text', 'WEBSERVICE("https://invalid.example/")'),
             'rich_active_or_external')
    mutation('synthetic_unknown_formula', 'xl/worksheets/sheet1.xml',
             lambda root: setattr(first_formula(root).find(g.q(g.S, 'f')), 'text', 'AVERAGE(A1:A2)'),
             'conversion_formula_unsupported')

    def stale_cache(root):
        cell = first_formula(root)
        node = cell.find(g.q(g.S, 'v'))
        if node is None:
            node = ET.SubElement(cell, g.q(g.S, 'v'))
        node.text = '-987654321'
    mutation('synthetic_stale_present_cache', 'xl/worksheets/sheet1.xml', stale_cache,
             'conversion_formula_cache_mismatch')
    check('public_missing_cache_not_destination_credit',
          lambda: g.evaluate(inventories['S-01-orders_base.xlsx'], check_cache=True),
          'conversion_formula_cache_missing')

    def missing_dependency():
        formula = g.parse_formula('A1*Z99', 'xlsx', 'Synthetic')
        inv = g.Inventory((('Synthetic', ((1, 1, g.Cell('number', Decimal(2))),
                                         (1, 2, g.Cell('number', None, formula)))),))
        return g.evaluate(inv)
    check('synthetic_missing_formula_dependency', missing_dependency,
          'conversion_formula_nonnumeric_or_missing_dependency')

    def digest_vectors():
        def signature(value, vendor=(), geometry=(), cache=()):
            result = r.RichSignature((('synthetic', 'Synthetic', (value,)),), cache)
            result.vendor_styles = vendor
            result.native_geometry = geometry
            return result
        def digest(sig):
            return g.Inventory((), rich_signature=sig).digest()
        require(digest(signature(Decimal('1.0'))) == digest(signature(Decimal('1.00'))), 'digest_decimal_scale_changed')
        require(digest(signature(False)) != digest(signature(0)), 'digest_bool_int_collapsed')
        require(digest(signature('1')) != digest(signature(1)), 'digest_text_int_collapsed')
        require(digest(signature(1)) != digest(signature(1, vendor=('synthetic_vendor',))), 'digest_vendor_ignored')
        require(digest(signature(1)) != digest(signature(1, geometry=('synthetic_geometry',))), 'digest_geometry_ignored')
        require(digest(signature(1)) == digest(signature(1, cache=('synthetic_cache_probe',))), 'digest_probe_polluted')
        return {'synthetic_typed_atoms': True, 'private_outputs_used': 0}
    check('synthetic_digest_identity', digest_vectors)
    check('synthetic_digest_nonfinite_refused', lambda: g._rich_digest_atom((Decimal('NaN'),)), 'conversion_rich_digest_nonfinite')
    check('synthetic_digest_unknown_type_refused', lambda: g._rich_digest_atom((object(),)), 'conversion_rich_digest_unsupported')

    def reference_positive():
        parsed = r._native_reference_list("$'Synthetic O''Brien'.$A$1:.$A$2 $'Synthetic O''Brien'.$B$1")
        require(len(parsed) == 2 and parsed[0] == ("Synthetic O'Brien", 1, 1, 2, 1), 'reference_quote_changed')
        require(r.validate_references(rich.rich_signature, rich), 'public_reference_validation_failed')
    check('public_references_and_synthetic_quoted_list', reference_positive)
    check('synthetic_unclosed_reference_refused', lambda: r._native_reference_list("$'Synthetic.$A$1"), 'rich_chart_update_reference_unsupported')
    check('synthetic_reference_count_bound', lambda: r._native_reference_list(' '.join(['$Synthetic.$A$1'] * 7)), 'rich_chart_update_reference_unsupported')
    check('synthetic_reference_outside_inventory',
          lambda: r.validate_references(r.RichSignature((('chart', 'Synthetic',
                ('bar', '', '', 'none', True, ('Synthetic', 1, 1, 1, 1),
                 ((('Synthetic', 1, 1, 1, 1), ('Synthetic', 2, 1, 2, 1)),), (), ())),)), rich),
          'rich_chart_reference_bounds')

    def changed_heading():
        table = next(row for row in rich.rich_signature if row[0] == 'table')
        _, area, headings, _ = table[2]
        sheet, row, col, _, _ = area
        sheets = tuple((name, tuple((rr, cc, replace(cell, value='synthetic_changed_heading')
            if (name, rr, cc) == (sheet, row, col) else cell) for rr, cc, cell in cells))
            for name, cells in rich.sheets)
        return r.validate_references(rich.rich_signature, replace(rich, sheets=sheets))
    check('synthetic_table_binding_changed', changed_heading, 'rich_table_header_mismatch')

    def public_same_source_fidelity():
        report = r.fidelity_report(rich.rich_signature, rich.rich_signature,
                                   source_kind='xlsx', target_kind='xlsx')
        require(report['declared_losses'] == [] and report['unassessed'] == [], 'same_source_fidelity_changed')
        require(bool(report['dimension_metadata']), 'public_dimensions_not_captured')
        return {'metadata_count': len(report['dimension_metadata']), 'same_source_only': True}
    check('public_same_source_fidelity_metadata', public_same_source_fidelity)

    def safe_namespace():
        raw = ('<root xmlns:t="' + g.TB + '" xmlns:of="' + g.OF + '" t:formula="of:=SUM([.A1:.A2])"/>').encode()
        require(r._formula_namespace_bindings(raw) == {'of': g.OF}, 'formula_namespace_binding_changed')
    check('synthetic_formula_namespace', safe_namespace)
    check('synthetic_foreign_formula_namespace_refused',
          lambda: r._formula_namespace_bindings(('<root xmlns:t="' + g.TB + '" xmlns:of="urn:synthetic:unknown" t:formula="of:=SUM([.A1:.A2])"/>').encode()),
          'rich_formula_namespace_unsupported')
    check('synthetic_original_xml_literal', lambda: r._native_original_xml_guard({'content.xml': b'<root>&lt;!--literal--&gt;</root>'}))
    check('synthetic_original_xml_dtd_refused', lambda: r._native_original_xml_guard({'content.xml': b'<!DOCTYPE root><root/>'}), 'rich_native_original_xml_unsupported')
    check('synthetic_original_xml_depth_refused', lambda: r._native_original_xml_guard({'content.xml': b'<a>' * 65 + b'</a>' * 65}), 'rich_native_original_xml_limit')
    check('synthetic_opaque_cli_fidelity_transport', lambda: transport_checks(native, ast_origins))

    for filename, data in originals.items():
        require((fixtures / filename).read_bytes() == data, 'public_input_changed')
    for relative, digest in (origins | ast_origins).items():
        require(hashlib.sha256(source_file(native, relative).read_bytes()).hexdigest() == digest, 'source_changed_during_check')
    report = {'scope': 'offline_source_only', 'all_expected': all(row['matched'] for row in checks),
              'checks': checks, 'public_inputs': input_facts, 'native_module_origins': origins,
              'native_transport_ast_origins': ast_origins,
              'runtime_adapter_imports': 0, 'office_model_provider_publication_calls': 0,
              'retained_office_outputs_used': 0, 'real_output_qualification': False,
              'synthetic_files_remaining': 0, 'input_files_unchanged': True}
    (work / 'CHECKS.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (work / 'CHECKS.json').chmod(0o600)
    passed = sum(row['matched'] for row in checks)
    print(json.dumps({'passed': passed, 'failed': len(checks) - passed, 'type': 'source_only'}))
    return 0 if report['all_expected'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except CheckFailure as error:
        # Never print paths, formula text, cell values, or native exception dumps.
        print(json.dumps({'reason': str(error), 'type': 'source_check_refused'}))
        raise SystemExit(2)
    except Exception:
        print(json.dumps({'reason': 'unexpected_check_failure', 'type': 'source_check_refused'}))
        raise SystemExit(2)
