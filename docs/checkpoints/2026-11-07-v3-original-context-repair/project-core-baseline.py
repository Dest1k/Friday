#!/usr/bin/env python3
"""Project the original Friday V3 requirements into a read-only CORE queue.

The default output is a summary. Use --case and --format for indexed source
references and use --all for the full projection. A source reference is a
source name from the output's `sources` object followed by a JSON pointer.
Use --b00-wave-root to join historical B00 scenarios from a local wave archive.
With --b00-fixture, match operator-supplied copies by size and SHA-256.
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
    return cases, formats, case_ledger, extension_ledger, b00, fixture_families, sources


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


def project_b00_wave_history(b00, root, fixture_paths=()):
    require(archive_directory(root), 'expected a B00 wave root directory')
    fixture_pins = b00_fixture_pins(fixture_paths)
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
    case_catalog, format_catalog, case_ledger, extension_ledger, b00, fixture_families, sources = inputs
    cases = project_cases(case_catalog, case_ledger, b00, fixture_families, sources['case_catalog']['sha256'])
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
    if b00_wave_root is not None:
        history = project_b00_wave_history(b00, b00_wave_root, b00_fixtures)
        availability = Counter(row['availability'] for row in history.values())
        output['summary']['b00_historical_scenarios'] = {
            status: availability[status] for status in (
                'original_registry_exact', 'separately_pinned_variant_exact', 'missing_capsule', 'missing_authority')}
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
                        help='match an explicit local copy against historical attachment pins; repeatable')
    args = parser.parse_args(argv)
    if args.b00_fixture and args.b00_wave_root is None:
        parser.error('--b00-fixture requires --b00-wave-root')
    try:
        output = build_projection(load_inputs(args), {case.upper() for case in args.case},
                                  {fmt.lower().removeprefix('.') for fmt in args.format}, args.all,
                                  args.b00_wave_root, args.b00_fixture)
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
