#!/usr/bin/env python3
"""Root-only one finite known PPTX -> PDF export qualifier; source-only until explicitly run."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time

HERE = Path(__file__).resolve().parent
UTILITY = HERE.parent / 'base' / 'qualify_office.py'
UTILITY_SHA = 'df1e37b50eb5216506f345c9e64c18aedd03883a91964dad5161824703a45588'
CONTRACT = __import__('runpy').run_path(str(HERE / 'pptx_pdf_contract.py'))
PPTX_MIME, EXPORT_FILTER = CONTRACT['PPTX_MIME'], CONTRACT['EXPORT_FILTER']
PDFTOTEXT = CONTRACT['PDFTOTEXT']
SOURCES = {'qualify_pptx_pdf.py', 'pptx_pdf_contract.py', 'pdf_pages.py', 'presentation_contract.py',
           'scoped_presentation.py', 'read_extract.py'}
FIELDS = {'schema', 'operator', 'format', 'operation_id', 'input', 'expectation', 'sources', 'source_manifest',
          'current', 'toolchain', 'kernel', 'operation_clock', 'output', 'deadline_utc', 'scope', 'budgets', 'once_intent'}
BUDGETS = {'wall_seconds': 90, 'cpu_seconds': 180, 'memory_bytes': 1073741824, 'swap_bytes': 0,
           'tasks': 96, 'helper_tasks': 48, 'cleanup_reserve_seconds': 12}
IMPORT_SETTINGS = {'encoding': 'OOXML-per-part-declaration', 'delimiter': 'not-applicable', 'locale': 'C.UTF-8',
                   'other_declared_options': {'profile': 'fresh-default', 'filter': EXPORT_FILTER,
                       'column_types': 'not-applicable', 'formula_evaluation': 'not-evaluated', 'input_extension': 'pptx'}}


def need(value, why):
    if not value:
        raise ValueError(why)


def read_private_file(path, expected, cap):
    need(path.is_absolute() and path.resolve() == path, 'CANONICAL_PROTECTED_FILE_REQUIRED')
    protected = False
    for parent in path.parents:
        info = parent.lstat()
        need(stat.S_ISDIR(info.st_mode) and not parent.is_symlink(), 'CANONICAL_DIRECTORY_ANCESTRY_REQUIRED')
        protected = protected or (info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o077)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode, s.st_nlink,
                          s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    before = path.lstat()
    need(protected and stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
         and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600, 'OWNED0600_SINGLE_LINK_FILE_REQUIRED')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        need(identity(info) == identity(before) and 0 < info.st_size <= cap, 'PINNED_FILE_CAP_OR_IDENTITY')
        raw = stream.read(cap + 1)
        need(len(raw) == info.st_size and identity(os.fstat(stream.fileno())) == identity(info)
             and identity(path.lstat()) == identity(info), 'PINNED_FILE_CHANGED_DURING_READ')
    need(hashlib.sha256(raw).hexdigest() == expected, 'PINNED_FILE_HASH_MISMATCH')
    return raw


def read_ref(ref, cap=2 * 1024 * 1024):
    need(type(ref) is dict and set(ref) in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'}), 'EXACT_PINNED_REF_REQUIRED')
    raw = read_private_file(Path(ref['path']), ref['sha256'], cap)
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'PINNED_REF_BYTE_MISMATCH')
    return raw


def _tool(value, path):
    need(type(value) is dict and set(value) == {'executable', 'version'}
         and CONTRACT['reference'](value['executable']) and value['executable']['path'] == path
         and type(value['version']) is str and 0 < len(value['version']) <= 128, 'EXACT_TOOL_PIN_REQUIRED')


def _reader(value):
    need(type(value) is dict and set(value) == {'source', 'executable', 'version'}
         and CONTRACT['reference'](value['source']) and CONTRACT['reference'](value['executable'])
         and value['executable']['path'] == PDFTOTEXT and type(value['version']) is str
         and 0 < len(value['version']) <= 128, 'EXACT_READER_PIN_REQUIRED')


def validate_plan(plan):
    need(type(plan) is dict and set(plan) == FIELDS, 'EXACT_PPTX_PDF_PLAN_FIELDS')
    CONTRACT['reject_interfaces'](plan)
    need(plan['schema'] == 'frw.Root.presentation-pdf-native-qualification-plan.v1'
         and plan['operator'] == 'Root' and plan['format'] == 'pptx', 'ROOT_PPTX_PDF_PLAN_REQUIRED')
    need(type(plan['operation_id']) is str and 0 < len(plan['operation_id']) <= 96, 'FINITE_OPERATION_ID_REQUIRED')
    need(type(plan['input']) is dict and set(plan['input']) == {'path', 'sha256', 'bytes', 'mime'}
         and plan['input']['mime'] == PPTX_MIME and CONTRACT['reference']({k: plan['input'][k] for k in ('path', 'sha256')})
         and type(plan['input']['bytes']) is int and 0 < plan['input']['bytes'] <= CONTRACT['MAX_PPTX_BYTES'], 'EXACT_KNOWN_PPTX_INPUT_REQUIRED')
    input_raw = read_private_file(Path(plan['input']['path']), plan['input']['sha256'], CONTRACT['MAX_PPTX_BYTES'])
    need(len(input_raw) == plan['input']['bytes'], 'KNOWN_PLAN_INPUT_BYTE_MISMATCH')
    need(CONTRACT['reference'](plan['expectation']) and CONTRACT['reference'](plan['source_manifest'])
         and CONTRACT['reference'](plan['current']) and CONTRACT['reference'](plan['once_intent']), 'PINNED_PLAN_REFS_REQUIRED')
    need(type(plan['sources']) is dict and set(plan['sources']) == SOURCES
         and all(type(v) is str and len(v) == 64 and all(c in '0123456789abcdef' for c in v)
                 for v in plan['sources'].values()), 'EXACT_QUALIFIER_SOURCE_SET_REQUIRED')
    toolchain = plan['toolchain']
    need(type(toolchain) is dict and set(toolchain) == {'consumer', 'strace', 'pdf_reader', 'wrapper'}, 'EXACT_TOOLCHAIN_FIELDS')
    _tool(toolchain['consumer'], CONTRACT['ENGINE'])
    _tool(toolchain['strace'], CONTRACT['STRACE'])
    _reader(toolchain['pdf_reader'])
    need(CONTRACT['reference'](toolchain['wrapper']) and toolchain['wrapper']['path'] == '/opt/friday-archive/bin/libreoffice',
         'FIXED_WRAPPER_PIN_REQUIRED')
    need(type(plan['kernel']) is dict and set(plan['kernel']) == {'release', 'boot_id'}
         and all(type(v) is str and 0 < len(v) <= 128 for v in plan['kernel'].values()), 'ACTUAL_KERNEL_BOOT_REQUIRED')
    CONTRACT['finite_clock'](plan['operation_clock'], 90)
    need(plan['operation_clock']['boot_id'] == plan['kernel']['boot_id'], 'PLAN_CLOCK_BOOT_MISMATCH')
    deadline = datetime.fromisoformat(plan['deadline_utc'].replace('Z', '+00:00'))
    need(deadline.tzinfo is not None and 18 < (deadline - datetime.now(timezone.utc)).total_seconds() <= 90,
         'FINITE_FUTURE_QUALIFICATION_DEADLINE_REQUIRED')
    need(plan['scope'] == 'frw-pptx-pdf-qualification-1.scope' and plan['budgets'] == BUDGETS, 'EXACT_PDF_QUALIFICATION_BUDGET_REQUIRED')
    output = Path(plan['output'])
    need(output.is_absolute() and output.parent.resolve() == output.parent and not output.exists(), 'NEW_CANONICAL_OUTPUT_REQUIRED')
    info = output.parent.stat()
    need(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'OWNED0700_OUTPUT_PARENT_REQUIRED')
    return output


def _check_plan_records(plan):
    manifest = json.loads(read_ref(plan['source_manifest']))
    leaves = {row.get('path'): row.get('sha256') for row in manifest.get('files', []) if type(row) is dict}
    need(all(leaves.get('code/' + name) == sha for name, sha in plan['sources'].items()), 'SOURCE_MANIFEST_PLAN_HASH_JOIN')
    current = json.loads(read_ref(plan['current']))
    need(current.get('schema') == 'frw.Root.pptx-pdf-known-export-current.v1' and current.get('operator') == 'Root'
         and current.get('whole_case_acceptance') is False and current.get('original_effect_closed') is True,
         'FRESH_ROOT_KNOWN_CURRENT_REQUIRED')
    intent = json.loads(read_ref(plan['once_intent']))
    need(intent.get('schema') == 'frw.Root.pptx-pdf-export-once-intent.v1' and intent.get('operator') == 'Root'
         and intent.get('operation_id') == plan['operation_id'] and intent.get('output') == plan['output']
         and intent.get('state') == 'INTENT_BEFORE_CGROUP_MOVE' and intent.get('consumed') is False,
         'EXACT_ONCE_INTENT_REQUIRED')
    need(current.get('source_manifest') == plan['source_manifest']
         and current.get('source_directory') == str(HERE) and current.get('source_only_accepted') is True
         and current.get('kernel') == plan['kernel'] and current.get('toolchain') == plan['toolchain'],
         'KNOWN_CURRENT_EXACT_SOURCE_TOOL_KERNEL_JOIN')
    need(all(intent.get(n) == plan[n] for n in ('current', 'operation_clock', 'input', 'expectation', 'source_manifest')),
         'ONCE_INTENT_EXACT_PLAN_CAS_JOIN')
    fixture = HERE.parent / 'fixtures/known-visible-label.pptx'
    expectation = HERE.parent / 'fixtures/KNOWN-PPTX-PDF-EXPECTATION.json'
    need(plan['input']['path'] == str(fixture) and plan['expectation']['path'] == str(expectation)
         and leaves.get('fixtures/known-visible-label.pptx') == plan['input']['sha256']
         and leaves.get('fixtures/KNOWN-PPTX-PDF-EXPECTATION.json') == plan['expectation']['sha256'],
         'KNOWN_ACCEPTED_FIXTURE_MANIFEST_JOIN')
    for name in ('base/qualify_office.py', *['code/' + n for n in SOURCES]):
        raw = (HERE.parent / name).read_bytes()
        need(leaves.get(name) == hashlib.sha256(raw).hexdigest(), 'KNOWN_COMPLETE_MANIFEST_GRAPH_JOIN')
    return current, intent


def check_actual(plan, utility):
    need(plan['kernel'] == {'release': os.uname().release,
         'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}, 'ACTUAL_KERNEL_BOOT_MISMATCH')
    now = time.monotonic()
    need(plan['operation_clock']['origin_monotonic'] <= now
         < plan['operation_clock']['deadline_monotonic'] - 12, 'ACTUAL_CLOCK_EXPIRED_OR_FUTURE')
    for name, path in (('consumer', CONTRACT['ENGINE']), ('strace', CONTRACT['STRACE'])):
        need(plan['toolchain'][name]['executable']['sha256'] == utility['PINS'][path], 'ACTUAL_TOOL_DECLARATION_PIN_MISMATCH')
    need(plan['toolchain']['wrapper']['sha256'] == utility['PINS'][utility['WRAPPER']], 'ACTUAL_WRAPPER_DECLARATION_PIN_MISMATCH')
    need(plan['toolchain']['pdf_reader']['source'] == {'path': str(HERE / 'read_extract.py'),
         'sha256': CONTRACT['READER_SHA256']}, 'ACTUAL_READER_SOURCE_DECLARATION_PIN_MISMATCH')


def execute(plan, output):
    start = time.monotonic()
    wall_end = datetime.fromisoformat(plan['deadline_utc'].replace('Z', '+00:00'))
    end = min(start + 88, time.monotonic() + max(0, (wall_end - datetime.now(timezone.utc)).total_seconds()),
              plan['operation_clock']['deadline_monotonic'])
    for name, expected in plan['sources'].items():
        read_private_file(HERE / name, expected, 256 * 1024)
    utility_raw = read_private_file(UTILITY, UTILITY_SHA, 256 * 1024)
    utility = {'__name__': 'Root_reviewed_qualification_utilities', '__file__': str(UTILITY)}
    exec(compile(utility_raw, str(UTILITY), 'exec'), utility)
    current, intent = _check_plan_records(plan)
    check_actual(plan, utility)
    original = read_private_file(Path(plan['input']['path']), plan['input']['sha256'], CONTRACT['MAX_PPTX_BYTES'])
    need(len(original) == plan['input']['bytes'], 'KNOWN_INPUT_BYTE_MISMATCH')
    expected = json.loads(read_ref(plan['expectation'], 1_000_000))
    CONTRACT['validate_source_expectation'](original, expected)
    observed = CONTRACT['observe_pptx'](original)
    need(observed['bounded_native_admission'] is True and observed['semantic_sha256'] == expected['pptx_semantic_sha256'],
         'KNOWN_PPTX_ADMISSION_OR_SEMANTIC_MISMATCH')
    utility['owned'](HERE, 0o700)
    need(end - time.monotonic() > 12, 'QUALIFICATION_FORWARD_OR_CLEANUP_DEADLINE')
    base = utility['own_cgroup']()
    utility['prepare_scope'](base, plan['scope'])
    affinity = sorted(os.sched_getaffinity(0))[:2]
    need(len(affinity) == 2, 'TWO_CPUS_UNAVAILABLE')
    os.sched_setaffinity(0, affinity)
    output.mkdir(mode=0o700, exist_ok=False)
    utility['OUTPUT'] = output
    toolchain = plan['toolchain']
    result = {'schema': 'frw.Root.pptx-pdf-native-qualification-observation.v1', 'operator': 'Root', 'format': 'pptx',
              'state': 'INCOMPLETE', 'commands': [], 'phases': [], 'pins': {}, 'scope': str(base), 'affinity': affinity,
              'started_monotonic': start, 'deadline_monotonic': end, 'qualifier_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'sources': plan['sources'], 'source_manifest': plan['source_manifest'], 'current': plan['current'],
              'operation_clock': plan['operation_clock'], 'once_intent': plan['once_intent'], 'operation_id': plan['operation_id'],
              'qualification_input': {k: plan['input'][k] for k in ('path', 'sha256')},
              'expectation': plan['expectation'], 'kernel': plan['kernel'], 'consumer': toolchain['consumer'],
              'strace': toolchain['strace'], 'pdf_reader': toolchain['pdf_reader'], 'import_settings': IMPORT_SETTINGS,
              'export_filter': EXPORT_FILTER, 'whole_case_acceptance': False, 'full_format_acceptance': False,
              'editable_preservation': 'FAIL_RETAINED', 'user_case_PASS': False, 'no_retry': True}
    work = []
    try:
        for name, expected_pin in utility['PINS'].items():
            raw = utility['pinned_wrapper'](expected_pin) if name == utility['WRAPPER'] else Path(name).read_bytes()
            need(hashlib.sha256(raw).hexdigest() == expected_pin, 'TOOL_HASH_CHANGED')
            result['pins'][name] = {'sha256': expected_pin, 'bytes': len(raw)}
        pdf_pin = toolchain['pdf_reader']['executable']['sha256']
        need(hashlib.sha256(Path(PDFTOTEXT).read_bytes()).hexdigest() == pdf_pin, 'PDFTOTEXT_HASH_CHANGED')
        common = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
        tracer = utility['fixed_command']([CONTRACT['STRACE'], '--version'], common, base, end, 'strace-version', result)
        home = Path(tempfile.mkdtemp(prefix='friday-office-pptx-pdf-version-', dir='/tmp'))
        work.append(home)
        office = utility['fixed_command']([utility['WRAPPER'], '--version'], dict(common, HOME=str(home), TMPDIR=str(home)), base, end, 'office-version', result)
        pdf_version = utility['fixed_command']([PDFTOTEXT, '-v'], common, base, end, 'pdftotext-version', result)
        versions = {}
        for key, raw in (('strace', tracer), ('consumer', office), ('pdf_reader', pdf_version)):
            lines = raw.decode('utf-8', 'strict').splitlines()
            need(lines and 0 < len(lines[0]) <= 128, 'BOUNDED_ACTUAL_VERSION_LINE_REQUIRED')
            versions[key] = lines[0]
        need(versions['consumer'] == toolchain['consumer']['version'] and versions['strace'] == toolchain['strace']['version']
             and versions['pdf_reader'] == toolchain['pdf_reader']['version'], 'ACTUAL_TOOL_VERSION_JOIN_MISMATCH')
        result['consumer']['version'] = versions['consumer']
        result['strace']['version'] = versions['strace']
        result['pdf_reader']['version'] = versions['pdf_reader']
        result['input_observation'] = utility['write_new'](output / 'ORIGINAL-PPTX-STRUCTURAL.json', CONTRACT['json_bytes'](observed))
        result['input_comparison'] = {'status': 'MATCH', 'pptx_semantic_sha256': observed['semantic_sha256']}
        home = Path(tempfile.mkdtemp(prefix='friday-office-pptx-pdf-export-', dir='/tmp'))
        work.append(home)
        source = home / 'known.pptx'
        source.write_bytes(original)
        source.chmod(0o400)
        out = home / 'output'
        out.mkdir(mode=0o700)
        profile = home / 'profile'
        argv = CONTRACT['fixed_engine_argv'](utility['WRAPPER'], str(profile), str(out), str(source))
        phase = {'stage': 'export', 'input_path': str(source), 'input_sha256': hashlib.sha256(original).hexdigest(),
                 'output_path': str(out / 'known.pdf'), 'started_monotonic': time.monotonic(), 'deadline_monotonic': end,
                 'declared_import_settings': IMPORT_SETTINGS, 'qualified': False}
        result['phases'].append(phase)
        returned_zero = False
        try:
            utility['fixed_command'](argv, dict(common, HOME=str(home), TMPDIR=str(home)), base, end, 'export', result)
            returned_zero = True
        finally:
            phase['input_unchanged'] = source.read_bytes() == original
        produced = out / 'known.pdf'
        need(list(out.iterdir()) == [produced] and produced.is_file() and not produced.is_symlink()
             and produced.stat().st_nlink == 1, 'ONE_SEPARATE_PDF_OUTPUT_REQUIRED')
        need(0 < produced.stat().st_size <= CONTRACT['MAX_PDF_BYTES'], 'PDF_OUTPUT_BYTE_CAP')
        raw = produced.read_bytes()
        need(0 < len(raw) <= CONTRACT['MAX_PDF_BYTES'], 'PDF_OUTPUT_BYTE_CAP')
        pages = __import__('runpy').run_path(str(HERE / 'pdf_pages.py'))
        reader_tool = pages['authenticate_tool'](None, PDFTOTEXT, pdf_pin, versions['pdf_reader'])
        page_result = pages['read_pages'](raw, produced, deadline_monotonic=end - 12, tool=reader_tool)
        pdf_observation = CONTRACT['pdf_observation'](raw, page_result['pages'], expected, page_result['reader'], output / 'known.pdf')
        phase['output_observation'] = utility['write_new'](output / 'EXPORTED-PDF-OBSERVATION.json', CONTRACT['json_bytes'](pdf_observation))
        phase['output_comparison'] = pdf_observation['comparison']
        phase['output_artifact'] = utility['write_new'](output / 'known.pdf', raw)
        phase['qualified'] = returned_zero and phase['input_unchanged'] and phase['output_comparison']['status'] == 'MATCH'
        result['state'] = 'ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED'
    except BaseException as exc:
        result['error_class'] = type(exc).__name__
        result['error_detail'] = str(exc)[:256]
    finally:
        result['own_processes_zero'] = (not any(p.is_dir() and p.name != 'supervisor' for p in base.iterdir())
            and (base / 'cgroup.procs').read_text().split() == []
            and (base / 'supervisor' / 'cgroup.procs').read_text().split() == [str(os.getpid())])
        result['temporary_homes'] = [str(p) for p in work]
        if result['own_processes_zero']:
            for path in work:
                try:
                    shutil.rmtree(path)
                except Exception as exc:
                    result.setdefault('temporary_cleanup_errors', []).append({'path': str(path), 'class': type(exc).__name__})
        result['temporary_homes_removed'] = all(not p.exists() for p in work)
        result['ended_monotonic'] = time.monotonic()
        observation = utility['write_new'](output / 'OBSERVATION.json', utility['data'](result))
        qualified = (CONTRACT['qualification_gate'](result['state'], result['commands'],
                         result['own_processes_zero'], result['temporary_homes_removed'],
                         bool(result['phases']) and result['phases'][0].get('input_unchanged') is True,
                         [result.get('input_comparison', {}), *[p.get('output_comparison', {}) for p in result['phases']]])
                     and result['state'] == 'ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED'
                     and len(result['phases']) == 1 and result['phases'][0]['qualified']
                     and result['own_processes_zero'] and result['temporary_homes_removed'] and result['ended_monotonic'] <= end)
        if qualified:
            qualifier = {'schema': 'frw.Root.pptx-pdf-native-consumer-qualification.v1', 'operator': 'Root', 'format': 'pptx',
                         'consumer': result['consumer'], 'strace': result['strace'], 'kernel': result['kernel'],
                         'pdf_reader': result['pdf_reader'], 'source_manifest': result['source_manifest'],
                         'import_settings': IMPORT_SETTINGS, 'export_filter': EXPORT_FILTER,
                         'actual_observation': {k: observation[k] for k in ('path', 'sha256')},
                         'full_format_acceptance': False, 'editable_preservation': 'FAIL_RETAINED'}
            utility['write_new'](output / 'CONSUMER-QUALIFICATION.json', utility['data'](qualifier))
    return 0 if qualified else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--execute-once', action='store_true')
    args = parser.parse_args()
    need(args.execute_once, 'SOURCE_ONLY_DEFAULT_EXPLICIT_ROOT_EXECUTION_REQUIRED')
    os.umask(0o077)
    plan = json.loads(read_private_file(Path(args.plan), args.plan_sha256, 32768))
    output = validate_plan(plan)
    raise SystemExit(execute(plan, output))


if __name__ == '__main__':
    raise SystemExit(main())
