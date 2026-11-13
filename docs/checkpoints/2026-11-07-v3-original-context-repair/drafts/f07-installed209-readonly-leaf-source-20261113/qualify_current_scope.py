"""Finite installed F07 read-only component; no scope/authority constructor.

Root calls run_current_scope only from an already admitted, fresh native
source/tool context in a bounded disposable process. Importing this file uses
stdlib only. It never sets native ContextVars, replaces modules or executes a
model, sender, Office process, write tool, installer or maintenance operation.
Standalone invocation deliberately refuses: genuine context is not CLI data.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import time

COMPLETE_SHA = '67d1aff2f27c8fbbb20303b0e2bcc1645ec4aa031cee2b26922726fd2acc6499'
TRUNCATED_SHA = '03bc974e86c81845b6d4d47bdb90eec7b21f66d750aa3319bc327149859a5a75'
TEXT_MARKER = 'Healthy follow-up marker: 2718.'
FIELDS = ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_uid', 'st_gid',
          'st_nlink', 'st_mtime_ns', 'st_ctime_ns')
REQUIRED_PINS = {
    'hermes_cli/friday_user_scope.py': '3dff39b51c8da112339ad5e2f5065a332fe102877303bf442a57624f07404474',
    'hermes_cli/friday_workspace_revision.py': 'a84959c7ddc6fec3a028e5b67b4af64b7ee5d7f462776b9a59150a1891b10dc4',
    'tools/file_tools.py': 'b834615c95438c2f1cb725247cc2ea0b6e1d5e1566cc3498fec2a069bc21a40f',
    'tools/binary_extensions.py': 'dce64d721d3541194d967f4b1edc9c4ae97e8e30fc64df20d606365ab70132de',
    'tools/read_extract.py': '8f3ad405263470eac948a9f14fa6c0af18144697cf5244c6c8c8a4f7d543b339',
    'tools/scoped_word_profiles.py': 'ef6767cdca7b761f6aa0da9ecfe81b44b66cc99b28af81de6f308b4180007e59',
    'tools/scoped_word_review.py': '050fafea426d2e5c5df584cbc1105549dfcaa55240552b80719db7f8bdeacb96',
    'tools/scoped_zip.py': 'fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127',
    'tools/scoped_ooxml_password.py': '59c65471582a30baf61ed8367925b477d00af70d6d1211e6044ecb2a3d35029c',
}


class QualificationRefused(RuntimeError):
    """Fixed metadata only; no source, document, credential or exception text."""


def require(condition, code):
    if not condition:
        raise QualificationRefused(code)


def pinned_read(path, *, private=True, limit=1_000_000):
    """Descriptor/named identity before/after; never follows the final symlink."""
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'noncanonical_path')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1 and before.st_size <= limit,
                'file_custody_refused')
        require(not private or not before.st_mode & 0o077, 'private_file_required')
        chunks = []
        size = 0
        while chunk := os.read(fd, min(65536, limit + 1 - size)):
            chunks.append(chunk)
            size += len(chunk)
            require(size <= limit, 'file_limit')
        after = os.fstat(fd)
        named = path.lstat()
        identity = tuple(getattr(before, name) for name in FIELDS)
        require(identity == tuple(getattr(after, name) for name in FIELDS)
                == tuple(getattr(named, name) for name in FIELDS)
                and size == before.st_size, 'file_changed')
        data = b''.join(chunks)
        return data, {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                      'stat': dict(zip(FIELDS, identity))}
    finally:
        os.close(fd)


def grade(case, observed):
    """Grade saved or actual read_file output; never claims its origin/stage."""
    require(isinstance(observed, dict), 'result_not_object')
    kind = case['kind']
    if kind in ('docx_noext', 'false_pdf', 'healthy_docx', 'ingress_bin'):
        require(observed.get('success') is True
                and observed.get('format') == 'docx'
                and observed.get('source_sha256') == COMPLETE_SHA
                and observed.get('extracted_document') is True
                and observed.get('partial') is False
                and TEXT_MARKER in observed.get('content', ''), 'docx_result_incomplete')
        metadata = observed.get('extraction', {})
        require(metadata.get('native_container') is True
                and metadata.get('macros_executed') is False
                and metadata.get('fields_evaluated') is False
                and 'images_layout' in observed.get('coverage', ''), 'inert_coverage_missing')
        if kind != 'healthy_docx':
            suffix = Path(case['tool_path']).suffix.lower()
            validation = metadata.get('format_validation', {})
            require(validation.get('claimed_format') == (suffix.lstrip('.') or 'none')
                    and validation.get('actual_format') == 'docx'
                    and validation.get('filename_mismatch') is True
                    and validation.get('filename_extension') == suffix
                    and validation.get('structure_validation') == 'SUPPORTED_DOCX_PROFILE_VALIDATED'
                    and validation.get('source_unchanged') is True,
                    'mismatch_not_truthful')
    elif kind == 'truncated_docx':
        require(observed == {'success': False, 'error': 'document_extraction_failed',
                             'format': 'docx', 'reason': 'malformed_package'},
                'truncated_not_fixed_refusal')
    elif kind == 'unknown_zip':
        require(observed.get('success') is False
                and observed.get('error') == 'document_extraction_failed'
                and observed.get('actual_format') == 'UNDETERMINED'
                and observed.get('structure_validation') == 'DOCX_PROFILE_NOT_VALIDATED'
                and observed.get('effect_disposition') == 'none', 'unknown_zip_misclassified')
    elif kind == 'literal_pk':
        require(observed.get('success') is True and not observed.get('extracted_document')
                and observed.get('content') == '1: PK\x03\x04 is inert UTF-8 text, not a ZIP package',
                'literal_pk_text_regression')
    else:
        raise QualificationRefused('unsupported_case')
    return {'id': case['id'], 'kind': kind, 'semantic_check': 'PASS'}


def validate_cases(cases):
    kinds = [case.get('kind') for case in cases]
    require(kinds == ['docx_noext', 'false_pdf', 'truncated_docx', 'healthy_docx', 'ingress_bin',
                      'unknown_zip', 'unknown_zip', 'literal_pk'], 'exact_case_sequence_required')
    require(len({case.get('id') for case in cases}) == len(cases), 'duplicate_case_id')
    for case in cases:
        path = Path(case.get('tool_path', ''))
        require(not path.is_absolute() and path.parts and not any(
            part in ('.', '..') or part.startswith('.') for part in path.parts), 'invalid_tool_path')
        require(len(case.get('sha256', '')) == 64 and type(case.get('bytes')) is int,
                'missing_input_pin')
    require(not Path(cases[0]['tool_path']).suffix
            and Path(cases[1]['tool_path']).suffix == '.pdf'
            and Path(cases[2]['tool_path']).suffix == '.docx'
            and Path(cases[3]['tool_path']).suffix == '.docx'
            and Path(cases[4]['tool_path']).suffix == '.bin'
            and Path(cases[5]['tool_path']).suffix == '.bin'
            and Path(cases[6]['tool_path']).suffix == '.pdf'
            and Path(cases[7]['tool_path']).suffix == '.txt', 'case_suffix_mismatch')
    require(all(cases[i]['sha256'] == COMPLETE_SHA and cases[i]['bytes'] == 1233
                for i in (0, 1, 3, 4)) and cases[2]['sha256'] == TRUNCATED_SHA
            and cases[2]['bytes'] == 64, 'original_prospective_pins_required')


def run_current_scope(native_root, cases, *, deadline_monotonic):
    """Read eight explicit prospective inputs inside Root's genuine context.

    No process/container/session is created. Root's actual executor must enforce
    its finite clock, source/permission/current/once/lease and no-write boundary.
    This local deadline can only shorten that clock. A healthy product is not
    stopped when this finite read qualification ends.
    """
    start = time.monotonic()
    require(type(deadline_monotonic) in (float, int)
            and start < deadline_monotonic <= start + 90, 'finite_deadline_required')
    validate_cases(cases)
    native_root = Path(native_root)
    require(native_root.is_absolute() and native_root.resolve() == native_root,
            'native_root_not_canonical')
    source_before = {}
    for relative, expected in REQUIRED_PINS.items():
        _, pin = pinned_read(native_root / relative, private=False)
        require(pin['sha256'] == expected, 'installed_source_pin_mismatch')
        source_before[relative] = pin
    scope = importlib.import_module('hermes_cli.friday_user_scope')
    tool = importlib.import_module('tools.file_tools')
    context = importlib.import_module('agent.web_call_context')
    loaded = [(importlib.import_module(relative[:-3].replace('/', '.')), relative)
              for relative in REQUIRED_PINS]
    loaded.append((context, 'agent/web_call_context.py'))
    for module, relative in loaded:
        require(Path(module.__file__).resolve() == native_root / relative,
                'module_origin_mismatch')
    cap = scope.current(required=True)
    require(type(cap) is scope.UserScope and cap.check() is cap, 'genuine_scope_required')
    call = context._current.get()
    require(call is not None and callable(getattr(call, 'check', None))
            and isinstance(getattr(call, 'task_id', None), str) and call.task_id,
            'existing_native_tool_context_required')
    call.check()
    workspace = cap.home / 'workspace'
    initial_read = getattr(call, '_workspace_read', None)
    initial_ready = getattr(call, '_workspace_read_ready', None)
    input_before = {}
    for case in cases:
        _, pin = pinned_read(workspace / case['tool_path'])
        require(pin['sha256'] == case['sha256'] and pin['stat']['st_size'] == case['bytes'],
                'prospective_input_pin_mismatch')
        input_before[case['id']] = pin
    observations = []
    for case in cases:
        require(time.monotonic() < deadline_monotonic, 'qualification_deadline')
        require(scope.current(required=True) is cap, 'scope_changed')
        call.check()
        raw = tool.read_file_tool(case['tool_path'], offset=1, limit=2000,
                                  char_offset=0, task_id=call.task_id)
        observed = json.loads(raw)
        assessment = grade(case, observed)
        _, after = pinned_read(workspace / case['tool_path'])
        require(after == input_before[case['id']], 'input_changed_by_read')
        if case['kind'] != 'literal_pk':
            require(getattr(call, '_workspace_read', None) is initial_read
                    and getattr(call, '_workspace_read_ready', None) is initial_ready,
                    'binary_read_coverage_changed')
        observations.append(dict(assessment, observed=observed))
    for relative, before in source_before.items():
        require(pinned_read(native_root / relative, private=False)[1] == before,
                'installed_source_changed')
    require(scope.current(required=True) is cap, 'final_scope_changed')
    call.check()
    require(time.monotonic() < deadline_monotonic, 'qualification_deadline')
    return {'schema': 'friday.F07.installed-current-scope-readonly-observation.v1',
            'state': 'PASS_INSTALLED_TOOL_PATH_ONLY', 'pid': os.getpid(),
            'elapsed_seconds': time.monotonic() - start,
            'same_process_same_scope': True, 'source_before_after': source_before,
            'input_before_after': input_before, 'observations': observations,
            'ordinary_Telegram_App_formal_F07_credit': False,
            'synthetic_scope_or_source_override': False,
            'resource_enforcement': 'Root actual bounded executor; local deadline <=90s'}


if __name__ == '__main__':
    raise SystemExit('REFUSED: invoke run_current_scope inside an existing genuine admitted native context')
