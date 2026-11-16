"""Pure data/seam adaptation of the existing ordinary independent tester.

No filesystem reads/writes, run, authority issuance, nonce, clock, API or send.
Root separately authenticates current owned workspace source and admits the
genuinely distinct original F03 effect. The old F04 custody remains UNKNOWN.
"""
import ast
import hashlib
import json
import re
import types

SELECTED_TESTER_SHA = 'cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
HISTORY_COMPAT_SHA = '6eb474ec654cb789be3a70ce783fa3abb40a4c6528a1b06b3afe376d721f6cb6'
SOURCE_NAME = 'Mayak_v1_structured_original_converted.docx'
SOURCE_SHA = '1c95836b4d65b30488d8289c629bcea2835382136b85a324bde042198c900ebb'
SOURCE_BYTES = 8791
OUTPUT_NAME = 'Mayak_v1_structured_deadline_23.docx'
OLD_TEXT = 'Срок сдачи: 22 октября 2026 года.'
NEW_TEXT = 'Срок сдачи: 23 октября 2026 года.'
MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
REQUEST = (
    'В сохранённом файле Mayak_v1_structured_original_converted.docx исправь '
    'только один факт в основном тексте: «Срок сдачи: 22 октября 2026 года.» '
    'замени на «Срок сдачи: 23 октября 2026 года.». Исходный файл сохрани без '
    'изменений. Пришли отдельную редактируемую DOCX-копию '
    'Mayak_v1_structured_deadline_23.docx в эту беседу. Весь остальной текст, '
    'таблицу, списки, сноску, верхний и нижний колонтитулы и структуру сохрани. '
    'Кратко укажи фактические ограничения сохранения оформления. '
    'Не преобразовывай файл в другой формат и не создавай документ заново.'
)
TIMING = dict(operation_seconds=300, reply_window_seconds=180,
              ack_seconds=10, reserve_seconds=5, outer_seconds=600)
LIMITS = dict(cpu_seconds=120, max_rss_bytes=512 * 1024**2,
              disk_bytes=100 * 1024**2)


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def scenario_data(*, tester_id, peer_id, peer_username):
    """Prospective request-only schema; calling this cannot execute a scenario."""
    need(type(tester_id) is int and type(peer_id) is int
         and type(peer_username) is str and bool(peer_username), 'BOUND_SELECTORS_REQUIRED')
    return dict(tester_id=tester_id, peer_id=peer_id, peer_username=peer_username,
        deadline_seconds=300, max_updates=64, pace_seconds=1,
        steps=[dict(request=REQUEST, observe=dict(mode='bounded_reply_capture',
            window_seconds=180, max_messages=32, max_text_chars=8000,
            max_documents=1, document_max_bytes=8 * 1024**2))])


def compose_source(base_raw, history_compat_raw, *, scenario, run_id,
                   authority, authority_ref):
    """Bind only the four pre-existing independent-admission data seams.

    Root supplies already-issued existing-schema authority. This pure adapter
    does not authenticate its real custody/current validity or issue a grant.
    Actual current preintent and owned-executor binding remain Root's work.
    """
    need(type(base_raw) is bytes and digest(base_raw) == SELECTED_TESTER_SHA,
         'SELECTED_TESTER_CHANGED')
    need(type(history_compat_raw) is bytes
         and digest(history_compat_raw) == HISTORY_COMPAT_SHA, 'HISTORY_COMPAT_CHANGED')
    need(type(scenario) is dict and encoded(scenario) == encoded(scenario_data(
        tester_id=scenario.get('tester_id'), peer_id=scenario.get('peer_id'),
        peer_username=scenario.get('peer_username'))), 'EXACT_REQUEST_ONLY_SCENARIO_REQUIRED')
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', run_id)
         and run_id != 'UNBOUND', 'ROOT_SELECTED_UNUSED_RUN_REQUIRED')
    need(type(authority_ref) is dict and set(authority_ref) == {'path', 'bytes', 'sha256'}
         and type(authority_ref['path']) is str and authority_ref['path'].startswith('/')
         and authority_ref['bytes'] == len(encoded(authority))
         and authority_ref['sha256'] == digest(encoded(authority)), 'EXACT_AUTHORITY_REF_REQUIRED')
    need(type(authority) is dict
         and authority.get('schema') == 'frw.Root.ordinary-independent-history-admission.v1'
         and authority.get('operator') == 'Root' and authority.get('accepted') is True
         and type(authority.get('authority_id')) is str and bool(authority['authority_id'])
         and 'UNBOUND' not in authority['authority_id']
         and authority.get('run_scenarios') == {run_id: digest(encoded(scenario))}
         and type(authority.get('history')) is dict and len(authority['history']) >= 40
         and authority.get('ordered_predecessors', {}) == {}
         and all(authority.get(k) is False for k in ('unknown_effects_resolved',
             'old_rows_modified', 'new_trial_for_historical_task', 'product_or_B00_acceptance'))
         and authority.get('no_old_task_replay') is True
         and authority.get('new_independent_inputs_only') is True, 'EXISTING_ROOT_AUTHORITY_REQUIRED')
    helper = types.ModuleType('_exact_reused_history_compat')
    exec(compile(history_compat_raw, '<pinned-history-compat>', 'exec'), helper.__dict__)
    text = helper.apply_history_compat(base_raw).decode()
    tree = ast.parse(text)
    runner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner')
    lines = text.splitlines(keepends=True)
    changes = []
    for name, value in [('ORDINARY_INDEPENDENT_SCENARIOS', {run_id: digest(encoded(scenario))}),
                        ('ORDINARY_INDEPENDENT_AUTHORITY', authority_ref)]:
        nodes = [n for n in runner.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
        need(len(nodes) == 1, 'EXACT_ASSIGNMENT_SEAM_REQUIRED')
        n = nodes[0]
        changes.append((n.lineno, n.end_lineno, '    ' + name + ' = ' + repr(value) + '\n'))
    method = next(n for n in runner.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'ordinary_independent_admission')
    ids = [n for n in ast.walk(method) if isinstance(n, ast.Constant)
           and n.value == 'ordinary-independent-jarvis-activate-20261108-r44']
    counts = [n.comparators[0] for n in ast.walk(method) if isinstance(n, ast.Compare)
              and ast.unparse(n) == "len(document['history']) != 40"]
    need(len(ids) == len(counts) == 1, 'EXACT_AUTHORITY_AND_HISTORY_SEAMS_REQUIRED')
    for n, value in [(ids[0], authority['authority_id']), (counts[0], len(authority['history']))]:
        changes.append((n.lineno, n.end_lineno,
            lines[n.lineno - 1][:n.col_offset] + repr(value)
            + lines[n.lineno - 1][n.end_col_offset:]))
    need(len({lo for lo, _, _ in changes}) == 4, 'OVERLAPPING_SEAMS_REFUSED')
    for lo, hi, replacement in sorted(changes, reverse=True):
        lines[lo - 1:hi] = [replacement]
    result = ''.join(lines).encode()
    ast.parse(result)
    return result


if __name__ == '__main__':
    raise SystemExit('REFUSED: pure Source adapter only; no execution entry point')
