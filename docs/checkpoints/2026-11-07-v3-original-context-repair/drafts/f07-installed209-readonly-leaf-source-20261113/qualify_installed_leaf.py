"""One fresh-process, read-only installed snapshot/DOCX leaf qualification.

This is not source/current admission, scoped_file routing, Telegram or formal
F07 acceptance. Root supplies the separately accepted installed209 closure and
launches with its existing finite source/current/slot/resource boundary. No
synthetic native modules, capabilities, context or installation overrides.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

HELPER_SHA = '5cde9a8c164bd06b788176cd3dd6f3821515d5764d9a77056e12a6be7503998d'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-root', required=True)
    parser.add_argument('--installation-evidence', required=True)
    parser.add_argument('--installation-evidence-sha256', required=True)
    parser.add_argument('--input-manifest', required=True)
    parser.add_argument('--input-manifest-sha256', required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    affinity = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, affinity)
    signal.alarm(90)
    start = time.monotonic()
    deadline = start + 85
    helper_path = Path(__file__).with_name('qualify_current_scope.py')
    if hashlib.sha256(helper_path.read_bytes()).hexdigest() != HELPER_SHA:
        raise SystemExit('REFUSED: helper_source_changed')
    spec = importlib.util.spec_from_file_location('_f07_preparation_helpers', helper_path)
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)

    def tick():
        q.require(time.monotonic() < deadline, 'leaf_deadline')

    root = Path(args.native_root)
    q.require(root.is_absolute() and root.resolve() == root, 'native_root_not_canonical')
    _, install_pin = q.pinned_read(args.installation_evidence)
    q.require(install_pin['sha256'] == args.installation_evidence_sha256,
              'installation_evidence_changed')
    raw_manifest, manifest_pin = q.pinned_read(args.input_manifest)
    q.require(manifest_pin['sha256'] == args.input_manifest_sha256,
              'input_manifest_changed')
    cases = json.loads(raw_manifest)['cases']
    q.validate_cases(cases)
    source_before = {}
    for relative, expected in q.REQUIRED_PINS.items():
        _, pin = q.pinned_read(root / relative, private=False)
        q.require(pin['sha256'] == expected, 'installed209_source_pin_mismatch')
        source_before[relative] = pin
    # The actual installed package is the import root, with no copied sources.
    sys.path.insert(0, str(root))
    revision = importlib.import_module('hermes_cli.friday_workspace_revision')
    extraction = importlib.import_module('tools.read_extract')
    for module, relative in ((revision, 'hermes_cli/friday_workspace_revision.py'),
                             (extraction, 'tools/read_extract.py')):
        q.require(Path(module.__file__).resolve() == root / relative,
                  'installed_module_origin_mismatch')
    observations = []
    input_before = {}
    # Suffix-specific ingress.bin/unknown.pdf checks belong to scoped_file,
    # whose genuine-context entry remains separate and NOT_RUN. Explicit DOCX
    # leaf probing would not add coverage by repeating their identical bytes.
    leaf_cases = [case for case in cases if case['id'] not in ('ingress-bin', 'unknown-pdf')]
    for case in leaf_cases:
        tick()
        data, before = q.pinned_read(case['source_path'])
        q.require(before['sha256'] == case['sha256'] and len(data) == case['bytes'],
                  'input_pin_mismatch')
        input_before[case['id']] = before
        path = Path(case['source_path'])
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if case['kind'] != 'literal_pk':
                try:
                    revision.snapshot(fd, path.name)
                except revision.NonTextSnapshotError:
                    default_snapshot = 'TEXT_ONLY_REFUSED_BINARY'
                else:
                    raise q.QualificationRefused('default_snapshot_binary_regression')
            else:
                default, _ = revision.snapshot(fd, path.name)
                q.require(default == data, 'literal_pk_snapshot_regression')
                default_snapshot = 'UTF8_TEXT_PRESERVED'
            explicit, _ = revision.snapshot(fd, path.name, require_utf8=False)
            q.require(explicit == data, 'readonly_snapshot_bytes_mismatch')
        finally:
            os.close(fd)
        record = {'id': case['id'], 'kind': case['kind'],
                  'default_snapshot': default_snapshot,
                  'explicit_readonly_snapshot': 'EXACT_BYTES'}
        if case['kind'] != 'literal_pk':
            try:
                text = extraction.extract_scoped_document_bytes(data, 'docx', checkpoint=tick)
            except extraction.ScopedExtractionError as error:
                q.require(case['kind'] in ('truncated_docx', 'unknown_zip'),
                          'supported_docx_rejected')
                if case['kind'] == 'truncated_docx':
                    q.require(error.code == 'malformed_package', 'truncated_refusal_changed')
                record['fixed_refusal_code'] = error.code
            else:
                q.require(case['kind'] not in ('truncated_docx', 'unknown_zip'),
                          'invalid_zip_accepted_as_docx')
                metadata = text.extraction_metadata
                q.require(q.TEXT_MARKER in text and metadata['native_container'] is True
                          and metadata['macros_executed'] is False
                          and metadata['fields_evaluated'] is False,
                          'inert_docx_semantics_missing')
                record['extraction_metadata'] = metadata
                record['synthetic_text_marker_present'] = True
            record['explicit_probe_format'] = 'docx'
            record['filename_routing_or_mismatch_metadata_credit'] = False
        q.require(q.pinned_read(path)[1] == before, 'source_input_changed')
        observations.append(record)
    for module_name in ('hermes_cli.friday_user_scope', 'tools.scoped_word_profiles',
                        'tools.scoped_word_review', 'tools.scoped_zip'):
        module = importlib.import_module(module_name)
        relative = module_name.replace('.', '/') + '.py'
        q.require(Path(module.__file__).resolve() == root / relative,
                  'dependency_origin_mismatch')
    for relative, before in source_before.items():
        q.require(q.pinned_read(root / relative, private=False)[1] == before,
                  'installed_source_changed')
    q.require(q.pinned_read(args.installation_evidence)[1] == install_pin,
              'installation_evidence_changed')
    tick()
    signal.alarm(0)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print(json.dumps({'schema': 'friday.F07.installed209.readonly-leaf.v1',
          'state': 'PASS_INSTALLED_PATH_LEAVES_ONLY',
          'installation_evidence': install_pin, 'input_manifest': manifest_pin,
          'source_before_after': source_before, 'input_before_after': input_before,
          'observations': observations, 'same_fresh_process': True,
          'tool_route_only_case_ids_not_executed': ['ingress-bin', 'unknown-pdf'],
          'scope_context_constructor_or_override': False,
          'product_tool_routing_current_admission_ordinary_App_formal_F07_credit': False,
          'limits': {'execution_wall_seconds': 90, 'local_work_deadline_seconds': 85,
                     'CPU_seconds': 90, 'AS_bytes': 512 * 1024**2,
                     'FSIZE_bytes': 16 * 1024**2, 'NOFILE': 128, 'affinity': affinity},
          'resources': {'elapsed_seconds': time.monotonic() - start,
                        'CPU_seconds': usage.ru_utime + usage.ru_stime,
                        'maxrss_kib': usage.ru_maxrss},
          'limit_scope': 'Per-process limits; Root outer120s stop/reap plus existing source/current/slot boundary. No aggregate-cgroup or total-disk quota claim.'}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Retain class/location without serializing an upstream parser message.
        frame = error.__traceback__
        while frame is not None and frame.tb_next is not None:
            frame = frame.tb_next
        result = {'schema': 'friday.F07.installed209.readonly-leaf-refusal.v1',
                  'state': 'NOT_QUALIFIED_NO_AUTOMATIC_RETRY',
                  'exception_class': type(error).__name__,
                  'exception_module': type(error).__module__,
                  'location': None if frame is None else {
                      'file': Path(frame.tb_frame.f_code.co_filename).name,
                      'function': frame.tb_frame.f_code.co_name,
                      'line': frame.tb_lineno},
                  'upstream_message_serialized': False}
        if type(error).__module__ == '_f07_preparation_helpers':
            result['fixed_local_refusal'] = error.args[0]
        print(json.dumps(result))
        raise SystemExit(1) from None
