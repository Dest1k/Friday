"""F04 Root source adapter. Import and all constructors are effect free.

Only bind_full_v42 changes tester source: exactly its three existing ordinary
independent-admission seams. Current, clocks, single use and native closure are
owned by root_f04.py/current_stop, never by an F03 footer or timeout override.
"""
import ast
import copy
import hashlib
import json
import re

BASE = {
    'path': '/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py',
    'bytes': 1136988,
    'sha256': 'f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3',
}
ISSUER = {
    'path': '/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py',
    'bytes': 29781,
    'sha256': 'ae6f2631eb6b053d1463a15665eaef7354b622756cee76c69b582ae8eb70d518',
}
SOURCE = {
    'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/input/orders-formulas-original.ods',
    'bytes': 16538,
    'sha256': 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58',
}
ROOT_SCOPE = 'case165/F04/format27_to26/original_required_rich_formula'
CAPTION = ('Преобразуй приложенный ODS в настоящий XLSX и пришли полученный файл в эту беседу. '
           'Сохрани все листы, их порядок, строки, типы данных, строковые идентификаторы, исходные числа, '
           'формулы произведений и межлистовую итоговую формулу; не заменяй формулы значениями. '
           'Сохрани поддерживаемые имена, диаграммы, фильтр, проверки данных, объединения и текущее скрытое '
           'состояние. Исходник не изменяй. Перечисли все реальные потери и непроверенные аспекты, а также '
           'ограничения кэшей и пересчёта. Не называй преобразование полностью без потерь или эквивалентным '
           'по внешнему виду и физической разметке.')
STAT_FIELDS = {'device', 'inode', 'size_bytes', 'uid', 'mtime_ns', 'ctime_ns'}
OLD_AUTHORITY = 'ordinary-independent-jarvis-activate-20261109-r68'


def need(condition, code):
    if not condition:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def is_sha(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def path_shape(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and not any(part in ('', '.', '..') for part in value.split('/')[1:])
         and not any(ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in value),
         'F04_ABSOLUTE_CANONICAL_PATH_REQUIRED')
    value.encode('utf-8')
    return value


def reference(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
         and type(value['bytes']) is int and value['bytes'] > 0
         and is_sha(value['sha256']), 'F04_EXACT_REFERENCE_REQUIRED')
    path_shape(value['path'])
    return value


def stat_shape(value):
    need(type(value) is dict and set(value) == STAT_FIELDS
         and all(type(v) is int and v >= 0 for v in value.values())
         and value['inode'] > 0 and value['size_bytes'] == SOURCE['bytes'],
         'F04_FRESH_EXACT_SOURCE_STAT_REQUIRED')
    return value


def construct_scenario(source_stat):
    """Root supplies fresh metadata later. This creates no file or admission."""
    stat_shape(source_stat)
    return {
        'tester_id': 8812646969, 'peer_id': 8751854128, 'peer_username': '@jerichodevbot',
        'deadline_seconds': 300, 'max_updates': 64, 'pace_seconds': 2,
        'steps': [{
            'input': {'kind': 'document', 'path': SOURCE['path'], 'sha256': SOURCE['sha256'],
                      'stat': dict(source_stat), 'filename': 'orders-formulas-original.ods',
                      'mime_type': 'application/vnd.oasis.opendocument.spreadsheet', 'caption': CAPTION},
            'observe': {'mode': 'bounded_reply_capture', 'window_seconds': 180,
                        'document_max_bytes': 1048576, 'max_documents': 1,
                        'max_messages': 4, 'max_text_chars': 8000},
        }],
    }


def scenario_shape(value):
    need(type(value) is dict and type(value.get('steps')) is list
         and len(value['steps']) == 1, 'F04_EXACT_SINGLETON_SCENARIO_REQUIRED')
    try:
        pin = value['steps'][0]['input']['stat']
    except (KeyError, IndexError, TypeError):
        raise ValueError('F04_SOURCE_STAT_UNBOUND') from None
    need(value == construct_scenario(pin), 'F04_ORIGINAL_SOURCE_CAPTION_OR_BOUNDS_CHANGED')
    return value


def _seams(tree):
    runners = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner']
    need(len(runners) == 1, 'F04_SINGLE_RUNNER_REQUIRED')
    runner = runners[0]
    nodes = []
    for name in ('ORDINARY_INDEPENDENT_SCENARIOS', 'ORDINARY_INDEPENDENT_AUTHORITY'):
        hits = [n for n in runner.body if isinstance(n, ast.Assign)
                and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == name]
        need(len(hits) == 1, 'F04_UNIQUE_SOURCE_SEAM_REQUIRED')
        nodes.append(hits[0])
    methods = [n for n in runner.body if isinstance(n, ast.FunctionDef)
               and n.name == 'ordinary_independent_admission']
    need(len(methods) == 1, 'F04_UNIQUE_ADMISSION_METHOD_REQUIRED')
    ids = [n for n in ast.walk(methods[0]) if isinstance(n, ast.Constant)
           and n.value == OLD_AUTHORITY]
    need(len(ids) == 1, 'F04_UNIQUE_AUTHORITY_ID_SEAM_REQUIRED')
    return nodes + ids


def _normalized(tree, authority_id):
    tree = copy.deepcopy(tree)
    runner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner')
    for node in runner.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {
                'ORDINARY_INDEPENDENT_SCENARIOS', 'ORDINARY_INDEPENDENT_AUTHORITY'} for t in node.targets):
            node.value = ast.Constant(value='EXACT_EXISTING_SEAM')
        if isinstance(node, ast.FunctionDef) and node.name == 'ordinary_independent_admission':
            hits = [n for n in ast.walk(node) if isinstance(n, ast.Constant) and n.value == authority_id]
            need(len(hits) == 1, 'F04_BOUND_AUTHORITY_LITERAL_NOT_UNIQUE')
            hits[0].value = 'EXACT_AUTHORITY_ID_SEAM'
    return ast.dump(tree, include_attributes=False)


def bind_full_v42(base_raw, run_id, scenario_sha256, authority, authority_id):
    """Pure exact three-seam successor; full remaining AST must be identical."""
    need(type(base_raw) is bytes and len(base_raw) == BASE['bytes']
         and digest(base_raw) == BASE['sha256'], 'F04_PINNED_FULL_V42_REQUIRED')
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', run_id)
         and 'UNBOUND' not in run_id and is_sha(scenario_sha256), 'F04_ACTUAL_RUN_SCENARIO_REQUIRED')
    reference(authority)
    need(type(authority_id) is str and authority_id and authority_id != OLD_AUTHORITY
         and 'UNBOUND' not in authority_id, 'F04_ACTUAL_NEW_AUTHORITY_REQUIRED')
    text = base_raw.decode('utf-8')
    before = ast.parse(text)
    nodes = _seams(before)
    lines = text.splitlines(keepends=True)
    values = ({run_id: scenario_sha256}, authority)
    edits = []
    for node, value in zip(nodes[:2], values):
        name = node.targets[0].id
        edits.append((node.lineno, node.end_lineno, '    ' + name + ' = ' + repr(value) + '\n'))
    node = nodes[2]
    need(node.lineno == node.end_lineno, 'F04_AUTHORITY_LITERAL_SINGLE_LINE_REQUIRED')
    line = lines[node.lineno - 1]
    # Source columns are UTF-8 bytes; this existing comparison line is ASCII.
    need(line.isascii(), 'F04_LITERAL_LINE_ENCODING_CHANGED')
    edits.append((node.lineno, node.end_lineno,
                  line[:node.col_offset] + repr(authority_id) + line[node.end_col_offset:]))
    for first, last, replacement in sorted(edits, reverse=True):
        lines[first - 1:last] = [replacement]
    bound = ''.join(lines).encode()
    after = ast.parse(bound)
    need(_normalized(before, OLD_AUTHORITY) == _normalized(after, authority_id),
         'F04_NON_SEAM_TESTER_AST_CHANGED')
    return bound


def verify_issued(document, root, authority_id):
    """Additional singleton/scope check; generic v42 rechecks its full admission."""
    need(type(document) is dict and document.get('schema') ==
         'frw.Root.ordinary-independent-history-admission.v1'
         and document.get('authority_id') == authority_id
         and document.get('operator') == 'Root' and document.get('accepted') is True
         and document.get('run_scenarios') == {root['run_id']: root['scenario_sha256']}
         and document.get('scope') == root['authority_scope']
         and document.get('product_or_B00_acceptance') is False
         and document.get('new_trial_for_historical_task') is False
         and document.get('unknown_effects_resolved') is False,
         'F04_ISSUED_SINGLETON_ORIGINAL_SCOPE_REQUIRED')
    return True
