"""Exact source-only v24 transplant into the captured actual221 private flavor.

Byte inputs only. No file, runtime, builder, installation, or authority operation.
The reviewed public transformation must reconstruct byte-for-byte; private edits
are limited to its same three shared seams and four groups of new v24 nodes.
"""
from __future__ import annotations
import ast
import hashlib

PUBLIC_BASE_SHA256 = 'a281dafffc509974ed6f40bfe5cef7e21f86838f00173f1c9227f05e5c4939a8'
PRIVATE_BASE_SHA256 = 'e4c4e33d07fd370c62ada08c67c6fafe42c64228a54c6b73fcb947d893b598d9'
PUBLIC_TEMPLATE_SHA256 = '3e6d5d522d8c0de1d69d0c68138810d088ab17fdde9eda430646996a9ee962c1'
SHARED_SEAMS = frozenset(('_current_source_twenty_third_successor_checked',
    'current_native_source_successor_checked', '_current_native_source_edge_checked'))
PRIVATE_CHANGED_FUNCTIONS = frozenset(('project_update_inputs', 'update', 'update_history', 'update_inputs'))
PRIVATE_ADDED_FUNCTIONS = frozenset(('v45_composition_checked', 'v45_composition_checked_previous',
    'v45_main', 'v45_manifest_checked'))
NEW_NAMES = frozenset(('CURRENT_SOURCE_TWENTY_FOURTH_SUCCESSOR_SCHEMA',
    'CURRENT_SOURCE_TWENTY_FOURTH_LAYER', 'CURRENT_SOURCE_TWENTY_FOURTH_MANIFEST',
    'CURRENT_SOURCE_TWENTY_FOURTH_PATCH', 'CURRENT_SOURCE_TWENTY_FOURTH_NATIVE',
    'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_REQUEST', 'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_INPUT',
    'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_RECEIPT', 'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_STAMP',
    'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_MARKER', 'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_INTENT',
    'CURRENT_SOURCE_TWENTY_FOURTH_PREVIOUS_COMMITTED', '_CURRENT_SOURCE_TWENTY_FOURTH_HISTORY_SEAL',
    '_CurrentSourceTwentyFourthHistory', '_current_source_twenty_fourth_source_bindings_checked',
    '_current_source_twenty_fourth_bindings_checked', '_current_source_twenty_fourth_successor_checked'))
class Refused(ValueError):
    pass
def require(condition, reason):
    if not condition:
        raise Refused(reason)
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def _key(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
        return ','.join(t.id for t in node.targets)
    return ast.dump(node, include_attributes=False)
def _nodes(raw):
    tree = ast.parse(raw)
    mapping = {_key(node): node for node in tree.body}
    require(len(mapping) == len(tree.body), 'duplicate_top_level_node')
    return tree.body, mapping

def compose_private_template(public_base_raw, private_base_raw, public_template_raw):
    """Return the exact UNBOUND private bytes plus provenance; never write them."""
    for label, raw, pin in (('public_base', public_base_raw, PUBLIC_BASE_SHA256),
            ('private_base', private_base_raw, PRIVATE_BASE_SHA256),
            ('public_template', public_template_raw, PUBLIC_TEMPLATE_SHA256)):
        require(type(raw) is bytes and sha(raw) == pin, label + '_origin_CAS_changed')
    _, public = _nodes(public_base_raw)
    private_order, private = _nodes(private_base_raw)
    template_order, template = _nodes(public_template_raw)
    dump = lambda node: ast.dump(node, include_attributes=False)
    require(set(public) <= set(private) and set(public) <= set(template), 'missing_baseline_node')
    require(set(template) - set(public) == NEW_NAMES, 'unreviewed_new_template_scope')
    require({key for key in public if dump(public[key]) != dump(template[key])} == SHARED_SEAMS,
        'unreviewed_changed_template_scope')
    require({key for key in public if dump(public[key]) != dump(private[key])} == PRIVATE_CHANGED_FUNCTIONS,
        'private_baseline_flavor_changed')
    old_functions = {node.name for node in public.values() if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    private_functions = {node.name for node in private.values() if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    require(private_functions - old_functions == PRIVATE_ADDED_FUNCTIONS, 'private_added_functions_changed')
    old_lines, private_lines, template_lines = [raw.splitlines(keepends=True)
        for raw in (public_base_raw, private_base_raw, public_template_raw)]
    operations = []
    for key in sorted(SHARED_SEAMS):
        old, prior, new = public[key], private[key], template[key]
        require(old_lines[old.lineno-1:old.end_lineno] == private_lines[prior.lineno-1:prior.end_lineno],
            'private_shared_seam_conflict_' + key)
        operations.append((key, old.lineno-1, old.end_lineno,
            prior.lineno-1, prior.end_lineno, template_lines[new.lineno-1:new.end_lineno]))
    index = 0
    while index < len(template_order):
        node = template_order[index]
        if _key(node) in public:
            index += 1
            continue
        end = index
        while end < len(template_order) and _key(template_order[end]) not in public:
            end += 1
        require(end < len(template_order), 'new_group_requires_existing_anchor')
        key = _key(template_order[end]); old, prior = public[key], private[key]
        require(dump(old) == dump(prior), 'private_insert_anchor_conflict_' + key)
        operations.append(('insert_before_' + key, old.lineno-1, old.lineno-1,
            prior.lineno-1, prior.lineno-1, template_lines[node.lineno-1:template_order[end].lineno-1]))
        index = end
    reconstructed = list(old_lines)
    composed = list(private_lines)
    for _, old_start, old_end, _, _, replacement in sorted(operations, key=lambda row: row[1], reverse=True):
        reconstructed[old_start:old_end] = replacement
    require(b''.join(reconstructed) == public_template_raw, 'public_delta_byte_reconstruction_failed')
    for _, _, _, start, end, replacement in sorted(operations, key=lambda row: row[3], reverse=True):
        composed[start:end] = replacement
    result = b''.join(composed)
    _, after = _nodes(result)
    require(set(after) == set(private) | NEW_NAMES, 'composed_node_inventory_changed')
    require({key for key in private if dump(private[key]) != dump(after[key])} == SHARED_SEAMS,
        'composed_unrelated_private_AST_changed')
    for key in PRIVATE_CHANGED_FUNCTIONS | PRIVATE_ADDED_FUNCTIONS:
        prior, final = private[key], after[key]
        require(private_lines[prior.lineno-1:prior.end_lineno] == composed[final.lineno-1:final.end_lineno],
            'private_flavor_function_bytes_changed_' + key)
    return result, {'schema': 'friday.source-only-private24-compose.v1',
        'public_base_sha256': PUBLIC_BASE_SHA256, 'private_base_sha256': PRIVATE_BASE_SHA256,
        'public_template_sha256': PUBLIC_TEMPLATE_SHA256, 'private_template_sha256': sha(result),
        'public_delta_exact_byte_reconstruction': True, 'unchanged_private_bytes_outside_operations': True,
        'operations': [{'name': name, 'private_start_line': start+1, 'private_end_line_exclusive': end+1,
            'replacement_lines': len(replacement)} for name, _, _, start, end, replacement in operations],
        'preserved_flavor_functions': sorted(PRIVATE_CHANGED_FUNCTIONS | PRIVATE_ADDED_FUNCTIONS),
        'changed_existing_functions': sorted(SHARED_SEAMS), 'added_top_level_nodes': sorted(NEW_NAMES),
        'authority_granted': False, 'effects_performed': False}
