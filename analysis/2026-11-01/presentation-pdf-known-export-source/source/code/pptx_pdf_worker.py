"""One sealed original PPTX -> PDF export and same-created delivered-PDF reader."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import time

ENGINE = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/soffice'
PROGRAM = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
PRIVATE = '/opt/friday-document-toolchain'
PYTHON = '/opt/friday-archive/python'
TRACE_FILTER = '%process,%network,%file,write,writev,pwrite64,pwritev,pwritev2,fsync,fdatasync'
COMPLETE = 'PPTX_PDF_EXPORT_RAW_RUNTIME_OBSERVATIONS_REVIEW_REQUIRED'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def reap(process, phase, end):
    if process is None:
        phase['process_reaped'] = False
        return False
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=max(.01, min(1, end - time.monotonic())))
    except subprocess.TimeoutExpired:
        pass
    phase['process_reaped'] = process.returncode is not None
    return phase['process_reaped']


def run(args, binding, suffix, received, delivered, scratch, end, emit_data):
    contract = runpy.run_path('/mnt/observer/pptx_pdf_contract.py')
    pages = runpy.run_path('/mnt/observer/pdf_pages.py')
    trace_module = runpy.run_path('/mnt/observer/trace_capture.py')
    expected = json.loads(Path('/mnt/input/expectation.json').read_bytes())
    original_raw = received.read_bytes()
    delivered_raw = delivered.read_bytes()
    contract['validate_source_expectation'](original_raw, expected)
    contract['need'](digest(delivered_raw) == args.delivered_sha256 and len(delivered_raw) == binding['delivered_pdf_bytes'],
                     'DELIVERED_PDF_SNAPSHOT_DRIFT')
    original_observation = contract['observe_pptx'](original_raw)
    contract['need'](original_observation['bounded_native_admission'] is True
                     and original_observation['semantic_sha256'] == expected['pptx_semantic_sha256'],
                     'ORIGINAL_PPTX_STATIC_ADMISSION_OR_SEMANTICS_REFUSED')
    original_structural = contract['json_bytes'](original_observation)
    emit_data('ORIGINAL-PPTX-STRUCTURAL.json', original_structural)
    original_ref = {'path': str(Path(args.export_path) / 'ORIGINAL-PPTX-STRUCTURAL.json'),
                    'sha256': digest(original_structural), 'bytes': len(original_structural)}
    env = dict(os.environ, LD_LIBRARY_PATH=PROGRAM + ':' + PRIVATE + '/root/usr/lib/x86_64-linux-gnu',
               SAL_USE_VCLPLUGIN='svp', MAX_CONCURRENCY='2')
    record = {'schema': 'frw.Root.pptx-pdf-finite-native-consumer-draft.v1',
              'invocation_id': binding['invocation_id'], 'binding_sha256': args.custody_sha256,
              'received_sha256': args.received_sha256, 'delivered_pdf_sha256': args.delivered_sha256,
              'format': suffix, 'export_filter': contract['EXPORT_FILTER'], 'state': 'INTENT_BEFORE_POPEN',
              'started_monotonic': time.monotonic(), 'internal_phase_timestamps': 'NOT_OBSERVED',
              'phases': [], 'consumer_safety': 'UNKNOWN', 'full_format_acceptance': False,
              'editable_preservation': 'FAIL_RETAINED'}
    (scratch / 'out').mkdir(mode=0o700, exist_ok=True)
    try:
        contract['need'](time.monotonic() < end - 3, 'SHARED_PDF_WORKER_DEADLINE_EXHAUSTED')
        input_path = received
        output_dir = scratch / 'out'
        before = input_path.read_bytes()
        phase_profile = scratch / 'profile-export'
        phase_profile.mkdir(mode=0o700)
        engine_argv = contract['fixed_engine_argv'](ENGINE, str(phase_profile), str(output_dir), str(input_path))
        trace_read, trace_write = os.pipe2(os.O_CLOEXEC)
        close_fds = 'import os,sys;fds=[int(x) for x in os.listdir("/proc/self/fd") if int(x)>2];[(os.close(fd) if os.path.exists("/proc/self/fd/"+str(fd)) else None) for fd in fds];os.execv(sys.argv[2],sys.argv[2:])'
        argv = ['/usr/bin/strace', '-f', '-ttt', '-T', '-yy', '-s', '256', '-e', 'trace=' + TRACE_FILTER,
                '-o', '/dev/fd/' + str(trace_write), '--', PYTHON, '-I', '-B', '-c', close_fds,
                str(trace_write), *engine_argv]
        phase = {'stage': 'export', 'format': suffix, 'input_path': str(input_path), 'input_sha256': digest(before),
                 'output_path': str(output_dir / 'received.pdf'), 'started_monotonic': time.monotonic(),
                 'deadline_monotonic': end, 'trace_filter': TRACE_FILTER,
                 'declared_import_settings': binding['import_settings'], 'state': 'INTENT_BEFORE_POPEN',
                 'input_observation': original_ref}
        record['phases'].append(phase)
        process = None
        try:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, pass_fds=(trace_write,), env=env, start_new_session=True)
            phase.update(tracer_pid=process.pid, state='STARTED_EFFECT_UNKNOWN_UNTIL_RECONCILED')
            os.close(trace_write)
            trace_write = None
            captured = trace_module['pump_capture'](process, trace_read, max(.01, min(30, end - time.monotonic() - 3)),
                                                    trace_cap=4 * 1024 * 1024, log_cap=65536)
            trace_read = None
            trace = bytes(captured['trace'].prefix)
            log = bytes(captured['out'].prefix)
            phase.update(exit_code=captured['returncode'], trace_complete=captured['streams_eof'],
                         timed_out=captured['timed_out'], overflow=captured['overflow'],
                         trace_reference={'path': str(Path(args.export_path) / 'EXPORT-SYSCALLS-PRIVATE.log'), 'sha256': digest(trace)},
                         trace_bytes=len(trace),
                         log_reference={'path': str(Path(args.export_path) / 'EXPORT-CONSUMER-PRIVATE.log'), 'sha256': digest(log)})
            emit_data('EXPORT-SYSCALLS-PRIVATE.log', trace)
            emit_data('EXPORT-CONSUMER-PRIVATE.log', log)
            out = output_dir / 'received.pdf'
            contract['need'](out.is_file() and not out.is_symlink() and out.stat().st_nlink == 1, 'SEPARATE_PDF_EXPORT_ABSENT')
            contract['need'](0 < out.stat().st_size <= contract['MAX_PDF_BYTES'], 'PDF_OUTPUT_BYTE_CAP')
            data = out.read_bytes()
            contract['need'](0 < len(data) <= contract['MAX_PDF_BYTES'], 'PDF_OUTPUT_BYTE_CAP')
            reader_tool = pages['authenticate_tool'](None, contract['PDFTOTEXT'],
                                                       binding['pdf_reader']['executable']['sha256'], binding['pdf_reader']['version'])
            exported_pages = pages['read_pages'](data, out, deadline_monotonic=end, tool=reader_tool)
            exported_reader = dict(exported_pages['reader'])
            exported_reader['source'] = binding['pdf_reader']['source']
            exported_observation = contract['pdf_observation'](data, exported_pages['pages'], expected,
                                                                exported_reader, Path(args.export_path) / 'received-exported.pdf')
            exported_structural = contract['json_bytes'](exported_observation)
            emit_data('EXPORTED-PDF-OBSERVATION.json', exported_structural)
            phase['output_observation'] = {'path': str(Path(args.export_path) / 'EXPORTED-PDF-OBSERVATION.json'),
                                           'sha256': digest(exported_structural), 'bytes': len(exported_structural)}
            phase['output_comparison'] = exported_observation['comparison']
            emit_data('received-exported.pdf', data)
            phase['output_artifact'] = {'path': str(Path(args.export_path) / 'received-exported.pdf'),
                                        'sha256': digest(data), 'bytes': len(data)}
            delivered_pages = pages['read_pages'](delivered_raw, delivered, deadline_monotonic=end, tool=reader_tool)
            delivered_reader = dict(delivered_pages['reader'])
            delivered_reader['source'] = binding['pdf_reader']['source']
            delivered_observation = contract['pdf_observation'](delivered_raw, delivered_pages['pages'], expected,
                                                                delivered_reader, Path(binding['delivered_pdf']['path']))
            delivered_structural = contract['json_bytes'](delivered_observation)
            emit_data('DELIVERED-PDF-OBSERVATION.json', delivered_structural)
            record['delivered_observation'] = {'path': str(Path(args.export_path) / 'DELIVERED-PDF-OBSERVATION.json'),
                                               'sha256': digest(delivered_structural), 'bytes': len(delivered_structural)}
            record['delivered_comparison'] = delivered_observation['comparison']
            phase['input_unchanged'] = digest(input_path.read_bytes()) == digest(before)
            record['delivered_snapshot_unchanged'] = digest(delivered.read_bytes()) == args.delivered_sha256
            contract['need'](phase['input_unchanged'] and record['delivered_snapshot_unchanged']
                             and captured['returncode'] == 0 and captured['streams_eof'],
                             'CONTAINED_FAILURE_OR_INCOMPLETE_CAPTURE')
            phase['state'] = 'ACTUAL_OUTPUT_RETAINED_RUNTIME_REVIEW_REQUIRED'
        finally:
            for fd in (trace_write, trace_read):
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            reap(process, phase, end)
            phase['ended_monotonic'] = time.monotonic()
        record['bounded_projection_match'] = (record['phases'][0].get('output_comparison', {}).get('status') == 'MATCH'
                                               and record.get('delivered_comparison', {}).get('status') == 'MATCH')
        record['state'] = COMPLETE
    except BaseException as exc:
        record.update(exception_class=type(exc).__name__, state='PPTX_PDF_CONTAINED_FAILURE_OR_INCOMPLETE_UNKNOWN')
    finally:
        record['ended_monotonic'] = time.monotonic()
        record['process_reaped'] = bool(record['phases']) and all(p.get('process_reaped') is True for p in record['phases'])
        record['received_snapshot_unchanged'] = digest(received.read_bytes()) == args.received_sha256
        record['delivered_snapshot_unchanged'] = digest(delivered.read_bytes()) == args.delivered_sha256
        emit_data('WORKER-RESULT.json', json_bytes(record), diagnostic=True)
    return 0 if record['state'] == COMPLETE else 2
