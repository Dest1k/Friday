#!/usr/bin/env python3
"""Project the original Friday V3 requirements into a read-only CORE queue.

The default output is a summary. Use --case and --format for indexed source
references and use --all for the full projection. A source reference is a
source name from the output's `sources` object followed by a JSON pointer.
Each B00 phase references its pinned planning row, including fixture and
predecessor requirements. Historical wave evidence is projected separately.
Use --b00-wave-root to join historical B00 scenarios from a local wave archive.
The joined archive also reports recorded observation and deadline ranges for
one scenario per phase on the shared serial slot.
With --b00-fixture, match explicit copies to the fixture pins.
Use --prepared-result, --prepared-plan and --prepared-r4 to verify selected
passive plans from an already pinned private preparation result for one case.
The original requests and oracles stay in their source files. The projection
carries no current admission or dispatch state.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
from zipfile import BadZipFile, ZipFile


CHECKPOINT = Path(__file__).resolve().parent
CASE_ANCHORS = 'evidence/astra-20261112/remaining-core-original-criteria-review.json'
PACKAGE_ANCHORS = 'evidence/sol-20261110/conditional-archive-links-root-review.json'
PREPARED_R4_SHA256 = '44577894f0669d305d2cd713048928c7ccbce265a40f1f6d09080b1fb62228bd'
B00_PLANNING_KEY = 'b219_finite_executable_expansion'
WORKER_CASES = {
    'W-13': 'DSH', 'R-11': 'DSH', 'W-14': 'A0', 'R-12': 'A0', 'R-13': 'DSH/A0 handoff',
}
FORMAT_OPERATIONS = {'read', 'create', 'edit', 'extract', 'summarize', 'recall', 'preserve'}
TRIAL_POLICY = {
    'source': 'original_directive:75',
    'default': 'one baseline trial per applicable instance',
    'critical_non_dangerous': ['nominal', 'paraphrase', 'retained-history'],
    'controlled_fault_exception': 'Predeclare one controlled observation and deterministic negatives where sufficient.',
}
# These retained records establish phase order within a shared catalogue clause.
B00_DOCUMENT_PHASE_ORDER = {
    'D-03-02': ('D-03-01', 'evidence/astra-20261120/d03-exact-staged-owned-predecessor-offline.json#/pairs/0'),
    'D-03-03': ('D-03-02', 'evidence/astra-20261120/d03-exact-staged-owned-predecessor-offline.json#/pairs/1'),
    'D-07-02': ('D-07-01', 'TWENTYSECOND-WAVE.json#/results'),
    'D-08-02': ('D-08-01', 'TWENTYTHIRD-WAVE.json#/results'),
    'D-14-02': ('D-14-01',
                'evidence/astra-20261120/d14-b00-exact-clauses-and-ordered-passive-continuation.json#/phase_summary/1/predecessor'),
    'D-14-03': ('D-14-02',
                'evidence/astra-20261120/d14-b00-exact-clauses-and-ordered-passive-continuation.json#/phase_summary/2/predecessor'),
    'D-15-02': ('D-15-01', 'THIRTEENTH-WAVE.json#/admission/scope'),
}


class ProjectionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProjectionError(message)


def verified_bytes(raw, pin, source):
    sha256 = hashlib.sha256(raw).hexdigest()
    require(len(raw) == pin.get('bytes', len(raw)) and sha256 == pin['sha256'],
            f'{source} bytes or SHA-256 differ from the checkpoint pin')
    return raw


def read_pinned(path, pin, source):
    with path.open('rb') as stream:
        return verified_bytes(stream.read(pin.get('bytes', 65536) + 1), pin, source)


def catalog_fixture_members(archive, member_directory):
    fixtures = defaultdict(list)
    fixture_directory = f'{member_directory}/fixtures'
    for info in archive.infolist():
        name = info.filename
        if not info.is_dir() and Path(name).parent.as_posix() == fixture_directory:
            data = archive.read(info)
            fixtures[hashlib.sha256(data).hexdigest()].append({'zip_member': name, 'bytes': len(data)})
    return fixtures


def load_inputs(args):
    anchors = json.loads((CHECKPOINT / CASE_ANCHORS).read_bytes())['original_anchors']
    package = json.loads((CHECKPOINT / PACKAGE_ANCHORS).read_bytes())['original_contract']
    sums = [line.partition('  ') for line in (CHECKPOINT / 'SHA256SUMS').read_text().splitlines()]
    b00_pins = [checksum for checksum, _, name in sums if name == 'B00-COVERAGE-MAP.json']
    require(len(b00_pins) == 1, 'expected one B00 pin in SHA256SUMS')
    pins = {
        'case_catalog': anchors['original_catalogue'],
        'format_catalog': package['format_catalog'],
        'case_ledger': anchors['immutable_case_ledger'],
        'extension_ledger': anchors['immutable_extension_ledger'],
        'b00': {'sha256': b00_pins[0]},
    }
    require(pins['case_catalog']['sha256'] == package['case_catalog']['sha256']
            and pins['case_catalog']['member'] == package['case_catalog']['zip_entry'],
            'existing case catalogue pins disagree')
    archive_bytes = read_pinned(args.catalog_zip, package['zip'], 'original archive')
    case_member = pins['case_catalog']['member']
    format_member = pins['format_catalog']['zip_entry']
    member_directory = case_member.rsplit('/', 1)[0]
    fixture_member = f'{member_directory}/04_FIXTURES_AND_ORACLES_EN.md'
    with ZipFile(io.BytesIO(archive_bytes)) as archive:
        cases = json.loads(verified_bytes(archive.read(case_member), pins['case_catalog'], 'case catalogue'))
        formats = json.loads(verified_bytes(archive.read(format_member), pins['format_catalog'], 'format catalogue'))
        fixture_headings = re.findall(r'^### (FX-[A-Z]+(?: / FX-[A-Z]+)*):',
                                      archive.read(fixture_member).decode('utf-8'), re.MULTILINE)
        catalog_fixtures = catalog_fixture_members(archive, member_directory)
    fixture_families = set(' / '.join(fixture_headings).split(' / '))
    case_ledger = json.loads(read_pinned(args.case_ledger, pins['case_ledger'], 'case ledger'))
    require(case_ledger['schema'] == 'private.user-journey.case-ledger.v1', 'unexpected case ledger schema')
    extension_ledger = json.loads(read_pinned(args.extension_ledger, pins['extension_ledger'], 'extension ledger'))
    require(extension_ledger['schema'] == 'private.user-journey.format-operation-ledger.v1',
            'unexpected extension ledger schema')
    b00 = json.loads(read_pinned(args.b00, pins['b00'], 'B00 map'))
    require(b00['schema'] == 'frw.public.v3.b00-coverage-map.v1', 'unexpected B00 map schema')
    sources = {name: {'sha256': pin['sha256']} for name, pin in pins.items()}
    sources['case_catalog']['zip_member'] = case_member
    sources['format_catalog']['zip_member'] = format_member
    sources['catalogue_archive'] = {'sha256': package['zip']['sha256']}
    sources['original_directive'] = {'zip_member': f'{member_directory}/01_ASTRA_DIRECTIVE_EN.md'}
    sources['original_fixture_families'] = {'zip_member': fixture_member}
    return cases, formats, case_ledger, extension_ledger, b00, fixture_families, sources, catalog_fixtures


def indexed_rows(rows, key, count, label):
    indexed = {row[key]: (index, row) for index, row in enumerate(rows)}
    require(len(rows) == len(indexed) == count, f'{label} count or identity mismatch')
    return indexed


def list_references(row, reference, fields):
    return {field: {'count': len(row[field]), 'ref': f'{reference}/{field}'}
            for field in fields if row.get(field)}


def archive_directory(path):
    return not path.is_symlink() and path.is_dir()


def unique_object(pairs):
    value = dict(pairs)
    require(len(value) == len(pairs), 'duplicate key in B00 wave JSON')
    return value


def read_wave_object(path):
    require(stat.S_ISREG(path.lstat().st_mode), 'expected a regular B00 wave file')
    limit = 256 * 1024
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, 'B00 wave file exceeds size limit')
    value = json.loads(data, object_pairs_hook=unique_object)
    require(isinstance(value, dict), 'expected a B00 wave JSON object')
    return value


def matches_b00_scenario(scenario, expected):
    steps = scenario.get('steps') if isinstance(scenario, dict) else None
    if not isinstance(steps, list) or not steps or not all(isinstance(step, dict) for step in steps):
        return False
    encoded = json.dumps(scenario, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n'
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest() == expected


def b00_capsule(wave, scenario_path, run_id, expected, stores):
    local_scenarios = wave / 'scenarios'
    if scenario_path.parent.name == 'scenarios' and scenario_path.parent.parent.name == wave.name:
        path = local_scenarios / scenario_path.name
        if archive_directory(local_scenarios) and path.is_file():
            scenario = read_wave_object(path)
            if matches_b00_scenario(scenario, expected):
                return 'scenario_file', path, '', scenario
    for store in stores:
        path = store / f'{run_id}.json'
        if not path.is_file():
            continue
        record = read_wave_object(path)
        if (record.get('id') == run_id and record.get('scenario_sha256') == expected
                and matches_b00_scenario(record.get('scenario'), expected)):
            return 'run_record', path, '/scenario', record['scenario']
    return None


def b00_fixture_pins(paths):
    pins = {}
    for index, path in enumerate(paths, 1):
        # Only read explicit CLI inputs. Never follow an old scenario's input path.
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'expected a regular B00 fixture copy')
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = os.fstat(stream.fileno())
        identities = {(item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
                      for item in (before, after, path.lstat())}
        require(len(identities) == 1, 'B00 fixture copy changed during read')
        pins.setdefault((before.st_size, digest), []).append(index)
    return pins


def b00_capsule_details(capsule, root, fixture_pins):
    kind, path, pointer, scenario = capsule
    deadline = scenario.get('deadline_seconds')
    require(type(deadline) is int and deadline > 0, 'invalid B00 scenario deadline')
    steps = []
    for index, step in enumerate(scenario['steps']):
        projected = {'source': f'{pointer}/steps/{index}'}
        observation = step.get('observe')
        if isinstance(observation, dict) and 'window_seconds' in observation:
            window = observation['window_seconds']
            require(type(window) is int and 0 < window <= deadline, 'invalid B00 observation window')
            projected['recorded_observation_seconds'] = window
        attachment = step.get('input')
        if isinstance(attachment, dict) and attachment.get('kind') == 'document':
            filename, size, digest = attachment['filename'], attachment['stat']['size_bytes'], attachment['sha256']
            require(type(size) is int and size >= 0 and isinstance(digest, str)
                    and re.fullmatch(r'[a-f0-9]{64}', digest), 'invalid B00 attachment size or hash')
            require(isinstance(filename, str) and 1 <= len(filename) <= 128 and filename[0].isalnum()
                    and '..' not in filename and all(c.isalnum() or c in '_.-' for c in filename),
                    'invalid B00 attachment filename')
            projected['document'] = {
                'filename': filename, 'bytes': size, 'sha256': digest,
                'matching_fixture_arguments': fixture_pins.get((size, digest), []),
            }
        steps.append(projected)
    return {
        'capsule': kind,
        'capsule_ref': {'relative_to_wave_root': path.relative_to(root).as_posix(), 'pointer': pointer},
        'recorded_deadline_seconds': deadline,
        'steps': steps,
    }


def project_b00_wave_history(b00, root, fixture_pins):
    require(archive_directory(root), 'expected a B00 wave root directory')
    registry = Path(b00['source_registry'])
    phases = {phase: [] for row in b00['cases'] for phase in row['step_ids']}
    waves = [path for path in sorted(root.iterdir())
             if re.fullmatch(r'FRW-KIMI-B00-[A-Z0-9-]+-[0-9]{8}', path.name) and archive_directory(path)]
    stores = [child / 'store' / 'runs' for wave in waves for child in sorted(wave.iterdir())
              if archive_directory(child) and archive_directory(child / 'store')
              and archive_directory(child / 'store' / 'runs')]
    for wave in waves:
        for path in sorted(wave.glob('INDEPENDENT-AUTHORITY-R*.json')):
            if not re.fullmatch(r'INDEPENDENT-AUTHORITY-R[0-9]+\.json', path.name):
                continue
            authority = read_wave_object(path)
            bindings = authority.get('phase_id_bindings', {})
            hashes = authority.get('run_scenarios', {})
            require(isinstance(bindings, dict) and isinstance(hashes, dict), 'invalid B00 wave bindings')
            for run_id, binding in bindings.items():
                require(isinstance(binding, dict), 'invalid B00 phase binding')
                scenario_path = Path(binding['scenario_path'])
                phase = scenario_path.stem.removesuffix('-long')
                if phase not in phases:
                    continue
                require(scenario_path.is_absolute() and '..' not in scenario_path.parts
                        and scenario_path.suffix == '.json' and '\x00' not in str(scenario_path)
                        and re.fullmatch(r'root-b00-[a-z0-9-]{1,120}', run_id), 'invalid B00 phase identity')
                expected = hashes.get(run_id)
                registry_sha = binding.get('canonical_sha256', expected)
                require(all(isinstance(digest, str) and re.fullmatch(r'[a-f0-9]{64}', digest)
                            for digest in (expected, registry_sha))
                        and binding.get('tester_sha256', expected) == expected, 'invalid B00 scenario pin')
                original = scenario_path.parent == registry and registry_sha == expected
                capsule = b00_capsule(wave, scenario_path, run_id, expected, stores)
                phases[phase].append({
                    'wave': wave.name.removeprefix('FRW-KIMI-B00-'),
                    'authority': path.stem.removeprefix('INDEPENDENT-AUTHORITY-'),
                    'run_id': run_id,
                    'scenario_sha256': expected,
                    'source_scenario_sha256': registry_sha,
                    'source': 'original_registry' if original else 'separately_pinned_variant',
                    **(b00_capsule_details(capsule, root, fixture_pins) if capsule else {'capsule': None}),
                })
    return {phase: {'availability': b00_availability(bindings), 'bindings': bindings}
            for phase, bindings in phases.items()}


def b00_availability(bindings):
    if any(binding['capsule'] and binding['source'] == 'original_registry' for binding in bindings):
        return 'original_registry_exact'
    if any(binding['capsule'] for binding in bindings):
        return 'separately_pinned_variant_exact'
    return 'missing_capsule' if bindings else 'missing_authority'


def b00_historical_timing(history):
    observation = []
    deadlines = []
    for row in history.values():
        capsules = [binding for binding in row['bindings'] if binding['capsule']]
        if capsules:
            deadlines.append([binding['recorded_deadline_seconds'] for binding in capsules])
        windows = []
        for binding in capsules:
            parts = [step.get('recorded_observation_seconds') for step in binding['steps']]
            if None not in parts:
                seconds = sum(parts)
                if seconds <= binding['recorded_deadline_seconds']:
                    windows.append(seconds)
        if windows:
            observation.append(windows)

    def serial_envelope(per_phase):
        return {
            'phases_with_recorded_bounds': len(per_phase),
            'phases_without_recorded_bounds': len(history) - len(per_phase),
            'minimum_seconds': sum(map(min, per_phase)) if per_phase else None,
            'maximum_seconds': sum(map(max, per_phase)) if per_phase else None,
        }

    return {
        'scope': 'One archived scenario per covered phase, including separately pinned variants. '
                 'These are declared slot bounds. Current eligibility, endpoint latency, '
                 'preparation and independent grading time are unmeasured.',
        'observation_windows': serial_envelope(observation),
        'deadline_envelopes': serial_envelope(deadlines),
    }


def project_b00_planning(case_ledger, catalog, b00, catalog_fixtures, fixture_pins):
    expanded = case_ledger[B00_PLANNING_KEY]
    require(expanded['schema'] == 'frw.Kimi.b219-finite-case-instances.v1', 'unexpected B00 planning schema')
    planned = indexed_rows(expanded['cases'], 'case_id', 170, 'expanded cases')
    definitions = indexed_rows(catalog['cases'], 'id', 170, 'original cases')
    copies = defaultdict(list)
    for (size, digest), arguments in fixture_pins.items():
        copies[digest].extend({'argument': index, 'bytes': size} for index in arguments)

    result = {}
    for row in b00['cases']:
        case_id = row['case']
        case_index, case_plan = planned[case_id]
        catalog_index, definition = definitions[case_id]
        clauses = definition['steps_ru']
        operations = case_plan['operations']
        require(len(row['step_ids']) == len(operations), f'B00 planning phase count differs for {case_id}')
        phases = []
        for ordinal, (phase, op) in enumerate(zip(row['step_ids'], operations, strict=True)):
            label = f'{case_id} {phase}'
            ref = f'case_ledger#/{B00_PLANNING_KEY}/cases/{case_index}/operations/{ordinal}'
            index = op['original_step_index']
            require(op['operation_id'] == f'{case_id}/OP-{ordinal + 1:03}'
                    and type(index) is int and 0 <= index < len(clauses)
                    and op['exact_original_clause'] == clauses[index]
                    and op['oracle']['text'] == definition['oracle_en']
                    and op['new_execution_credit'] == 0, f'invalid B00 planning operation for {label}')
            request = op['request']
            require(isinstance(request['text'], str)
                    and hashlib.sha256(request['text'].encode('utf-8')).hexdigest() == request['sha256'],
                    f'invalid B00 planning request pin for {label}')
            inputs = op['inputs']
            scenario = op['scenario']
            case_input = op['case_input']
            if scenario is None:
                require(op['phase'] == f'original_step_{ordinal + 1}' and index == ordinal
                        and request['binding'] == 'ORIGINAL_CLAUSE_FUTURE_PLANNED_REQUEST_NOT_SCENARIO_ACCEPTED'
                        and request['text'] == clauses[index] and case_input is None and not inputs,
                        f'invalid B00 clause-only operation for {label}')
                source = 'original_clause_only'
            else:
                require(op['phase'] == phase and request['binding'] == 'PINNED_ACCEPTED_SCENARIO'
                        and Path(scenario['path']).name == f'{phase}.json'
                        and all(isinstance(pin, str) and re.fullmatch(r'[a-f0-9]{64}', pin)
                                for pin in (scenario['sha256'], case_input['sha256'])),
                        f'invalid B00 planning scenario pin for {label}')
                source = 'pinned_planning_scenario'

            dependencies = op['dependencies']
            needed = dependencies['required_original_step_indices']
            require(all(type(step) is int and 0 <= step < index for step in needed)
                    and len(set(needed)) == len(needed), f'invalid B00 planning dependency for {label}')
            prior_clauses = []
            for step in needed:
                earlier_phases = [previous_phase for previous_phase, previous_op
                                  in zip(row['step_ids'][:ordinal], operations[:ordinal], strict=True)
                                  if previous_op['original_step_index'] == step]
                prior_clauses.append({
                    'original_step_ref': f'case_catalog#/cases/{catalog_index}/steps_ru/{step}',
                    'earlier_phase_candidates': earlier_phases,
                    'mapping': 'unique_candidate' if len(earlier_phases) == 1 else 'exact_phase_mapping_open',
                })
            documents = []
            for input_index, attachment in enumerate(inputs):
                digest = attachment['sha256']
                require(attachment['kind'] == 'document' and isinstance(digest, str)
                        and re.fullmatch(r'[a-f0-9]{64}', digest),
                        f'invalid B00 planning document pin for {label}')
                documents.append({
                    'ref': f'{ref}/inputs/{input_index}', 'filename': attachment['filename'],
                    'mime_type': attachment['mime_type'], 'sha256': digest,
                    'catalogue_members': catalog_fixtures.get(digest, []),
                    'matching_fixture_arguments': copies.get(digest, []),
                })
            projected = {
                'phase': phase, 'source': source, 'operation_ref': ref,
                'original_step_ref': f'case_catalog#/cases/{catalog_index}/steps_ru/{index}',
                'request_ref': f'{ref}/request/text', 'request_sha256': request['sha256'],
                'scenario_pin': {'ref': f'{ref}/scenario', 'sha256': scenario['sha256']} if scenario else None,
                'case_input_pin': {'ref': f'{ref}/case_input', 'sha256': case_input['sha256']} if case_input else None,
                'dependencies': dependencies, 'missing_bindings': op['missing_bindings'],
                'prior_clause_phases': prior_clauses,
                'documents': documents,
            }
            sequence = B00_DOCUMENT_PHASE_ORDER.get(phase)
            if sequence:
                previous_phase, evidence = sequence
                earlier = row['step_ids'][:ordinal]
                require(previous_phase in earlier
                        and operations[earlier.index(previous_phase)]['original_step_index'] == index,
                        f'invalid documented B00 phase order for {label}')
                projected['same_clause_predecessor'] = {'phase': previous_phase, 'evidence': evidence}
            phases.append(projected)
        result[case_id] = phases
    return result


def prepared_file(path, pin, limit, label):
    """Hold exactly the bytes verified from one explicit protected input."""
    path = Path(path).absolute()
    require(re.fullmatch(r'[a-f0-9]{64}', pin['sha256']) is not None, f'invalid SHA-256 for {label}')
    try:
        require(path.resolve(strict=True) == path, f'canonical non-symlink path required for {label}')
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
                    and not stat.S_IMODE(before.st_mode) & 0o077 and 0 < before.st_size <= limit,
                    f'bounded private regular file required for {label}')
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        identities = {(info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                      for info in (before, after, path.lstat())}
        require(len(identities) == 1 and len(raw) == before.st_size and path.resolve(strict=True) == path,
                f'{label} changed while reading')
    except OSError as error:
        raise ProjectionError(f'could not read {label} ({type(error).__name__})') from error
    return verified_bytes(raw, pin, label), {'path': str(path), 'bytes': len(raw), 'sha256': pin['sha256']}


def prepared_pointer(document, pointer):
    require(pointer.startswith('/') and not re.search(r'~(?![01])', pointer), 'invalid preparation JSON pointer')
    node = document
    for part in pointer.split('/')[1:]:
        token = part.replace('~1', '/').replace('~0', '~')
        if type(node) is dict and token in node:
            node = node[token]
        elif type(node) is list and re.fullmatch(r'(0|[1-9][0-9]*)', token) and int(token) < len(node):
            node = node[int(token)]
        else:
            raise ProjectionError(f'preparation pointer does not resolve: {pointer}')
    return node


def prepared_reference(record, pointer):
    ref = prepared_pointer(record, pointer)
    require(type(ref) is dict and {'path', 'bytes', 'sha256'} <= ref.keys()
            and type(ref['path']) is str and Path(ref['path']).is_absolute()
            and type(ref['bytes']) is int and ref['bytes'] > 0 and type(ref['sha256']) is str,
            'exact sized artifact reference required in the preparation result')
    return ref


def prepared_plan_reference(record, pointer, result_ref):
    value = prepared_pointer(record, pointer)
    # Earlier passive results retain the plan basename and its adjacent raw hash.
    if pointer.endswith('/scenario') and type(value) is str and Path(value).name == value:
        checksum = prepared_pointer(record, pointer + '_file_sha256')
        require(type(checksum) is str, 'raw scenario file SHA-256 required')
        return {'path': str(Path(result_ref['path']).with_name(value)), 'sha256': checksum}
    return prepared_reference(record, pointer)


def prepared_case_reference(record, case_id):
    for field in ('case', 'assignment', 'state'):
        value = record.get(field)
        if type(value) is not str:
            continue
        pattern = r'^([A-Z])-?([0-9]{2})(?:_|$)' if field == 'state' else r'(?<![A-Z0-9])([A-Z])-?([0-9]{2})(?![A-Z0-9])'
        cases = {f'{prefix}-{number}' for prefix, number in re.findall(pattern, value)}
        if cases:
            require(cases == {case_id}, 'preparation result case differs from the selected catalogue case')
            return '/' + field
    raise ProjectionError('preparation result is missing a case identity')


def prepared_label(label, seen):
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', label) is not None and label not in seen,
            'duplicate or invalid preparation label')
    seen.add(label)


def project_prepared(args, output, selected_cases):
    if not (args.prepared_result or args.prepared_r4 or args.prepared_plan
            or args.prepared_artifact or args.prepared_dependency):
        return
    require(len(selected_cases) == 1 and args.prepared_result and args.prepared_r4 and args.prepared_plan,
            'prepared projection requires one --case, a pinned result, selected R4 and at least one plan')
    result_path, result_sha = args.prepared_result
    raw, result_ref = prepared_file(result_path, {'sha256': result_sha}, 2_000_000, 'preparation result')
    record = json.loads(raw, object_pairs_hook=unique_object)
    require(type(record) is dict, 'preparation result must be an object')
    case_id = next(iter(selected_cases))
    case_ref = prepared_case_reference(record, case_id)
    observer_raw, observer_ref = prepared_file(args.prepared_r4, {'sha256': PREPARED_R4_SHA256}, 2_000_000, 'selected R4')
    observer = {'__file__': observer_ref['path'], '__name__': '_pinned_core_prepared_r4'}
    exec(compile(observer_raw, observer_ref['path'], 'exec'), observer)
    plans, artifacts, labels = [], {}, set()
    for label, pointer, scenario_pointer in args.prepared_plan:
        prepared_label(label, labels)
        raw_ref = prepared_plan_reference(record, pointer, result_ref)
        plan_bytes, plan_ref = prepared_file(raw_ref['path'], raw_ref, 2_000_000, label)
        expected = prepared_pointer(record, scenario_pointer)
        require(type(expected) is str and re.fullmatch(r'[a-f0-9]{64}', expected), 'normalized scenario SHA-256 required')
        try:
            scenario = observer['validate_scenario'](json.loads(plan_bytes, object_pairs_hook=unique_object))
            require(hashlib.sha256(observer['encoded'](scenario)).hexdigest() == expected,
                    f'normalized scenario does not match selected preparation for {label}')
            inputs = []
            for step_index, step in enumerate(scenario['steps']):
                upload = step.get('input')
                if upload is not None:
                    data = observer['read_document_input'](upload, lambda: None)
                    inputs.append({'step': step_index, 'path': upload['path'], 'bytes': len(data), 'sha256': upload['sha256']})
        except observer['Refused'] as error:
            raise ProjectionError(f'selected passive plan or attachment refused by exact R4 for {label}') from error
        plans.append({'label': label, 'plan': plan_ref, 'plan_ref': pointer, 'scenario_sha256': expected,
                      'scenario_ref': scenario_pointer, 'steps': len(scenario['steps']), 'uploads': inputs})

    for role, pointer in args.prepared_artifact:
        prepared_label(role, labels)
        ref = prepared_reference(record, pointer)
        _, artifact = prepared_file(ref['path'], ref, 8_388_608, role)
        artifacts[role] = {**artifact, 'result_ref': pointer}
    for role, path, checksum in args.prepared_dependency:
        prepared_label(role, labels)
        _, artifact = prepared_file(path, {'sha256': checksum}, 8_388_608, role)
        artifacts[role] = {**artifact, 'externally_pinned': True}
    case = next(row for row in output['cases'] if row['id'] == case_id)
    case['selected_preparation'] = {
        'state': 'PASSIVE_PLANS_AND_REFERENCES_VERIFIED', 'result': result_ref, 'case_ref': case_ref, 'r4': observer_ref,
        'plans': plans, 'artifacts': artifacts, 'order': 'explicit selection order',
        'admission': 'UNBOUND', 'historical_effects_reconciled': False,
    }


def project_cases(catalog, ledger, b00, fixture_families, catalog_sha):
    definitions = indexed_rows(catalog['cases'], 'id', 170, 'original cases')
    retained = indexed_rows(ledger['rows'], 'case_id', 170, 'case ledger')
    require(catalog['case_count'] == 170 and definitions.keys() == retained.keys(),
            'case definitions and ledger IDs do not join')
    worker_ids = {case_id for case_id, (_, row) in definitions.items()
                  if row['evidence_required'] == 'LIVE_BOT_WITH_WORKER'}
    require(worker_ids == WORKER_CASES.keys(), 'original worker case set changed')
    phases = indexed_rows(b00['cases'], 'case', 31, 'B00 cases')
    require(phases.keys() <= definitions.keys() - worker_ids and b00['cases_total'] == 31,
            'B00 cases do not join to CORE cases')

    b00_steps = 0
    b00_sent = 0
    for case_id, (_, row) in phases.items():
        count = row['scenarios']
        required = [f'{case_id}-{number:02}' for number in range(1, count + 1)]
        sent = set(row['sent_steps'])
        require(required and row['step_ids'] == required and sent <= set(required)
                and len(sent) == row['sent'] == len(row['sent_steps']), f'invalid B00 phase join for {case_id}')
        b00_steps += count
        b00_sent += len(sent)
    require(b00_steps == b00['steps_total'] == 62 and b00_sent == b00['steps_sent'],
            'B00 phase totals differ from the map')

    core = {}
    for case_id, (index, definition) in definitions.items():
        ledger_index, row = retained[case_id]
        refs = definition['fixture_refs']
        require(refs and len(refs) == len(set(refs)) and set(refs) <= fixture_families
                and refs == row['fixture_families'], f'fixture family join differs for {case_id}')
        require(all(re.fullmatch(r'[a-f0-9]{64}', fixture['sha256'])
                    for fixture in row['fixture_instances']), f'invalid fixture pin for {case_id}')
        require(row['catalogue']['sha256'] == catalog_sha
                and row['category'] == definition['category'] and row['priority'] == definition['priority']
                and row['required_evidence'] == definition['evidence_required']
                and definition['steps_ru'] and all(isinstance(step, str) and step for step in definition['steps_ru']),
                f'original case definition differs from ledger for {case_id}')
        if case_id in worker_ids:
            continue
        source = f'case_catalog#/cases/{index}'
        history = f'case_ledger#/rows/{ledger_index}'
        known_preparation = [f'{history}/{field}' for field in (
            'continuation_preparation', 'source_free_exact_preparation', 'nominal_actual_ingress',
            'last_technical_closure', 'active_original_nominal', 'active_original_paraphrase', 'active_retained_setup',
        ) if row.get(field)]
        projected = {
            'id': case_id,
            'category': definition['category'],
            'priority': definition['priority'],
            'steps_ref': f'{source}/steps_ru',
            'step_count': len(definition['steps_ru']),
            'criteria_refs': [f'{source}/oracle_en', f'{source}/common_evidence'],
            'required_evidence': definition['evidence_required'],
            'fixture_families': refs,
            'fixture_ref': f'{source}/fixture_refs',
            'fixture_instances': [
                {'sha256': fixture['sha256'], 'ref': f'{history}/fixture_instances/{position}'}
                for position, fixture in enumerate(row['fixture_instances'])
            ],
            'historical': {
                'source': history,
                'candidate': row['candidate'],
                'execution_status': row['execution_status'],
                'capability_status': row['capability_status'],
                'whole_case_accepted': row.get('whole_case_accepted'),
                'live_admission_disposition': row['live_admission'],
                'recorded_budget_seconds': row['budget_seconds'],
                'gap_ids': row['gap_ids'],
                **list_references(row, history, ('attempts', 'technical_attempts', 'evidence', 'retained_first_failure_refs')),
            },
            'known_preparation_refs': known_preparation,
            'trial_plan': 'Resolve applicable trial IDs, prerequisites, and exact inputs against the original steps and retained evidence.',
            'missing_current_bindings': ['candidate', 'physical scenario and execution route', 'historical effect reconciliation'],
        }
        if not row['fixture_instances']:
            projected['missing_current_bindings'].append('fixture instance absent from case ledger row')
        if case_id in phases:
            phase_index, b00_row = phases[case_id]
            ids = b00_row['step_ids']
            projected['b00'] = {
                'source': f'b00#/cases/{phase_index}',
                'listed_order': ids,
                'sent_exact_hash_in_snapshot': b00_row['sent_steps'],
                'binding_needed': 'Resolve each phase to its exact scenario and qualify same-conversation predecessors where required.',
            }
        core[case_id] = projected
    return core


def project_operation(row, reference, criteria_ref):
    projected = {
        'id': row['id'],
        'source': reference,
        'criteria_ref': criteria_ref,
        'applicability': row['applicability'],
        'historical_status': row['status'],
        'historical_candidate': row['candidate'],
        'case_templates': row['case_templates'],
        'gap_ids': row['gap_ids'],
        **list_references(row, reference, ('attempts', 'evidence')),
    }
    missing = ['current candidate and physical execution binding']
    if row['applicability'] == 'UNRESOLVED_REVIEW_REQUIRED':
        missing.append('applicability disposition')
    if row['fixture'] is None:
        missing.append('fixture instance absent from ledger row')
    else:
        projected['fixture_ref'] = f'{reference}/fixture'
    projected['missing_current_bindings'] = missing
    if row.get('not_applicable_rationale') or row.get('not_applicable_reviewer'):
        projected['applicability_decision_ref'] = reference
    if row.get('first_failure'):
        projected['first_failure_ref'] = f'{reference}/first_failure'
    return projected


def project_formats(catalog, ledger, case_ids, conversion_criteria):
    definitions = indexed_rows(catalog['formats'], 'extension', 120, 'original formats')
    retained = indexed_rows(ledger['extensions'], 'extension', 120, 'extension ledger')
    require(catalog['extension_count'] == 120 and definitions.keys() == retained.keys(),
            'format definitions and ledger extensions do not join')
    formats = {}
    variants = {}
    for extension, (index, definition) in definitions.items():
        ledger_index, row = retained[extension]
        clauses = [clause.strip() for clause in definition['variants'].split(';')]
        ids = row['variant_ids']
        require(row['family'] == definition['family'] and row['priority'] == definition['priority']
                and row['variant_source'] == definition['variants'] and all(clauses)
                and ids == [f'v{number:02}' for number in range(1, len(clauses) + 1)]
                and set(row['operations']) == FORMAT_OPERATIONS, f'variant definition differs for {extension}')
        variants.update({(extension, variant): clause for variant, clause in zip(ids, clauses, strict=True)})
        source = f'format_catalog#/formats/{index}'
        formats[extension] = {
            'extension': extension,
            'family': definition['family'],
            'priority': definition['priority'],
            'source': source,
            'variant_ref': f'{source}/variants',
            'historical_coverage': {
                'source': f'extension_ledger#/extensions/{ledger_index}',
                'status': row['status'], 'backend': row['backend'],
                'capability_status': row['capability_status'], 'fixtures': row['fixture_coverage'],
            },
            'variants': [{'id': variant, 'clause': clause, 'operations': [], 'directed_conversions': []}
                         for variant, clause in zip(ids, clauses, strict=True)],
        }
    require(len(variants) == 404, 'original format variant count differs')
    variant_output = {(extension, variant['id']): variant
                      for extension, row in formats.items() for variant in row['variants']}
    operations = indexed_rows(ledger['operation_rows'], 'id', 2828, 'format operations')
    seen = defaultdict(set)
    for row_id, (index, row) in operations.items():
        key = (row['extension'], row['variant_id'])
        operation = row['operation']
        require(key in variants and variants[key] == row['variant_source_text']
                and operation in FORMAT_OPERATIONS and operation not in seen[key]
                and row_id == '/'.join((*key, operation, row['candidate'] or 'UNBOUND')),
                'operation ID, candidate, or literal variant join differs')
        links = row['candidate_family_case_links']
        require(set(row['case_templates'] + links) <= case_ids, 'format operation case link is missing')
        seen[key].add(operation)
        source = formats[key[0]]['source']
        criteria_field = operation if operation in {'read', 'create', 'edit'} else 'checks'
        projected = project_operation(row, f'extension_ledger#/operation_rows/{index}', f'{source}/{criteria_field}')
        projected['operation'] = operation
        projected['candidate_family_case_links'] = links
        variant_output[key]['operations'].append(projected)
    require(seen.keys() == variants.keys() and all(ops == FORMAT_OPERATIONS for ops in seen.values()),
            'format operation grid is incomplete')

    conversions = indexed_rows(ledger['explicit_conversion_variant_rows'], 'id', 82, 'directed conversion variants')
    pairs = set()
    for row_id, (index, row) in conversions.items():
        extension, destination = row['source_extension'], row['destination_extension']
        key = (extension, row['source_variant_id'])
        operation = f'convert_to_{destination}'
        require(key in variants and variants[key] == row['source_variant_text'] and destination in formats
                and row['operation'] == operation and row_id == '/'.join((*key, operation, row['candidate'] or 'UNBOUND'))
                and set(row['case_templates']) <= case_ids,
                'directed conversion ID, case link, or literal variant join differs')
        pairs.add((extension, destination))
        projected = project_operation(row, f'extension_ledger#/explicit_conversion_variant_rows/{index}',
                                      conversion_criteria)
        projected['destination_extension'] = destination
        variant_output[key]['directed_conversions'].append(projected)
    require(len(pairs) == 16, 'directed conversion pair count differs')
    return formats


def format_conditions(ledger, formats, case_ids):
    conditional = indexed_rows(ledger['conditional_pdf_family_obligations'], 'obligation_id', 20, 'conditional PDF rows')
    require(len(ledger['open_directed_conversion_obligations']) == 4, 'open conversion rule count differs')
    require({row['template'] for row in ledger['cross_cut_requirements']} == {'F-05', 'F-06', 'F-07', 'F-08'},
            'format cross-cutting case template set differs')
    for _, row in conditional.values():
        extensions = row['candidate_source_extensions']
        expected = {key for key, item in formats.items() if item['family'] == row['source_family']}
        require(set(extensions) == expected and len(extensions) == row['candidate_extension_count']
                and row['destination_extension'] in formats and set(row['case_templates']) <= case_ids,
                'conditional conversion family, destination, or case link differs')
    require(all(set(row['case_templates']) <= case_ids for row in ledger['open_directed_conversion_obligations']),
            'open conversion case link is missing')
    return {
        'conditional_pdf_families': [
            {**row, 'source': f'extension_ledger#/conditional_pdf_family_obligations/{index}'}
            for index, row in conditional.values()
        ],
        'open_directed_conversions': [
            {**row, 'source': f'extension_ledger#/open_directed_conversion_obligations/{index}'}
            for index, row in enumerate(ledger['open_directed_conversion_obligations'])
        ],
        'cross_cut_requirements': ledger['cross_cut_requirements'],
    }


def build_projection(inputs, selected_cases, selected_formats, select_all, b00_wave_root=None, b00_fixtures=()):
    case_catalog, format_catalog, case_ledger, extension_ledger, b00, fixture_families, sources, catalog_fixtures = inputs
    cases = project_cases(case_catalog, case_ledger, b00, fixture_families, sources['case_catalog']['sha256'])
    fixture_pins = b00_fixture_pins(b00_fixtures)
    b00_plans = project_b00_planning(case_ledger, case_catalog, b00, catalog_fixtures, fixture_pins)
    planned_phases = [phase for phases in b00_plans.values() for phase in phases]
    planned_documents = [doc for phase in planned_phases for doc in phase['documents']]
    original_ids = cases.keys() | WORKER_CASES.keys()
    conversion_criteria = cases['F-04']['criteria_refs'][0]
    formats = project_formats(format_catalog, extension_ledger, original_ids, conversion_criteria)
    conditions = format_conditions(extension_ledger, formats, original_ids)
    require(selected_cases <= cases.keys(), 'case selection contains an unknown or out-of-scope case ID')
    require(selected_formats <= formats.keys(), 'format selection contains an unknown extension')
    operations = extension_ledger['operation_rows']
    output = {
        'sources': sources,
        'summary': {
            'original_cases': len(original_ids), 'core_cases': len(cases), 'worker_cases_out_of_scope': WORKER_CASES,
            'b00_cases': b00['cases_total'], 'b00_phases': b00['steps_total'],
            'b00_sent_exact_hash_in_snapshot': b00['steps_sent'],
            'b00_planning': {
                'phases_by_source': dict(Counter(phase['source'] for phase in planned_phases)),
                'attachment_references': len(planned_documents),
                'attachment_references_with_verified_bytes': sum(
                    bool(doc['catalogue_members'] or doc['matching_fixture_arguments']) for doc in planned_documents),
            },
            'formats': len(formats), 'variants': sum(len(row['variants']) for row in formats.values()),
            'format_operation_rows': len(operations),
            'format_operations_by_applicability': dict(Counter(row['applicability'] for row in operations)),
            'format_operations_by_historical_status': dict(Counter(row['status'] for row in operations)),
            'directed_conversion_variants': len(extension_ledger['explicit_conversion_variant_rows']),
            'conditional_pdf_families': len(conditions['conditional_pdf_families']),
            'open_directed_conversion_rules': len(conditions['open_directed_conversions']),
            'physical_execution_count': None,
        },
        'order': ['documents, texts and tables', 'images and archives', 'remaining CORE'],
        'trial_policy': TRIAL_POLICY,
        'execution_boundary': 'Resolve fixtures, applicability, dependencies and physical plans. Bind fresh clocks and admission separately.',
    }
    if select_all or selected_cases:
        output['cases'] = [row for case_id, row in cases.items() if select_all or case_id in selected_cases]
        for case in output['cases']:
            if 'b00' in case:
                case['b00']['planning_operations'] = b00_plans[case['id']]
    if b00_wave_root is not None:
        history = project_b00_wave_history(b00, b00_wave_root, fixture_pins)
        availability = Counter(row['availability'] for row in history.values())
        output['summary']['b00_historical_scenarios'] = {
            status: availability[status] for status in (
                'original_registry_exact', 'separately_pinned_variant_exact', 'missing_capsule', 'missing_authority')}
        output['summary']['b00_archived_serial_timing'] = b00_historical_timing(history)
        for case in output.get('cases', []):
            if 'b00' in case:
                case['b00']['historical_scenarios'] = [
                    {'phase': phase, **history[phase]} for phase in case['b00']['listed_order']]
    format_cases_selected = bool(selected_cases & {'F-04', 'F-05', 'F-06', 'F-07', 'F-08'})
    if select_all or selected_formats or format_cases_selected:
        output['format_conditions'] = conditions
        if selected_formats and not (select_all or format_cases_selected):
            output['format_conditions']['conditional_pdf_families'] = [
                row for row in conditions['conditional_pdf_families']
                if selected_formats.intersection(row['candidate_source_extensions'])
                or row['destination_extension'] in selected_formats
            ]
    if select_all or selected_formats:
        output['formats'] = [row for extension, row in formats.items() if select_all or extension in selected_formats]
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('--catalog-zip', '--case-ledger', '--extension-ledger', '--b00'):
        parser.add_argument(option, required=True, type=Path)
    parser.add_argument('--case', action='append', default=[], metavar='ID', help='include an indexed CORE case')
    parser.add_argument('--format', action='append', default=[], metavar='EXT', help='include an indexed extension')
    parser.add_argument('--all', action='store_true', help='include every CORE case, extension and format rule')
    parser.add_argument('--b00-wave-root', type=Path,
                        help='join historical B00 scenario hashes from retained wave directories')
    parser.add_argument('--b00-fixture', type=Path, action='append', default=[],
                        help='match an explicit local copy against planning or historical attachment pins; repeatable')
    parser.add_argument('--prepared-result', nargs=2, metavar=('FILE', 'SHA256'),
                        help='read the exact already accepted private RESULT for one selected case')
    parser.add_argument('--prepared-r4', type=Path, help='exact composed passive R4 used to validate selected plans')
    parser.add_argument('--prepared-plan', nargs=3, action='append', default=[],
                        metavar=('LABEL', 'PLAN_POINTER', 'SCENARIO_SHA_POINTER'),
                        help='select a plan reference and its recorded normalized hash; repeat for exact phases')
    parser.add_argument('--prepared-artifact', nargs=2, action='append', default=[], metavar=('ROLE', 'POINTER'),
                        help='verify the exact artifact reference for a reply checker, prerequisite or other input')
    parser.add_argument('--prepared-dependency', nargs=3, action='append', default=[], metavar=('ROLE', 'FILE', 'SHA256'),
                        help='verify a dependency pinned by existing evidence outside the prepared result')
    args = parser.parse_args(argv)
    try:
        selected_cases = {case.upper() for case in args.case}
        output = build_projection(load_inputs(args), selected_cases,
                                  {fmt.lower().removeprefix('.') for fmt in args.format}, args.all,
                                  args.b00_wave_root, args.b00_fixture)
        project_prepared(args, output, selected_cases)
    except ProjectionError as error:
        print(f'CORE projection refused: {error}', file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError, BadZipFile) as error:
        print(f'CORE projection refused: could not load or join inputs ({type(error).__name__})', file=sys.stderr)
        return 1
    json.dump(output, sys.stdout, ensure_ascii=False, separators=(',', ':'))
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
