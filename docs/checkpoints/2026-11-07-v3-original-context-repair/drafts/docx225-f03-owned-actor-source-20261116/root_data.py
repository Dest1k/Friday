"""Pure F03 record packaging. No IO, CLI, defaults, grant or clock issuance.

All statuses, accepted flags, current observations and Root decisions are caller
inputs. Source-only fixtures may exercise shapes; they are never live evidence.
Actual custody/current validation remains in the selected reviewed actor.
"""
import hashlib
import json
from pathlib import PurePosixPath
import re


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       allow_nan=False) + '\n').encode('utf-8')


def clone(value):
    return json.loads(encoded(value))


def path(value):
    need(type(value) is str and value.startswith('/')
         and not value.startswith('//') and str(PurePosixPath(value)) == value
         and all(x not in ('', '.', '..') for x in value.split('/')[1:])
         and all(ord(c) >= 32 and not 127 <= ord(c) <= 159 for c in value),
         'CANONICAL_PATH_REQUIRED')
    value.encode('utf-8')
    return value


def reference(location, value):
    raw = encoded(value)
    need(0 < len(raw) <= 24 * 1024**2, 'EXACT_REFERENCE_BOUND_REQUIRED')
    return dict(path=path(location), bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())


def reference_shape(value):
    return (type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
            and path(value['path']) == value['path']
            and type(value['bytes']) is int and 0 < value['bytes'] <= 24 * 1024**2
            and type(value['sha256']) is str
            and re.fullmatch('[a-f0-9]{64}', value['sha256']) is not None)


def bind(document, key, value):
    need(key not in document or document[key] == value,
         'CALLER_BINDING_CONFLICT_' + key)
    document[key] = clone(value)


def history_projection(rows, *, historical_replay_authorized):
    """Metadata only. Caller separately checks canonical rows/current deadlines.

    unknown_retained is the existing consumer's exact send_state rule, not an
    inference that an effect is resolved. No current or absence claim is made.
    """
    need(historical_replay_authorized is False, 'NO_HISTORICAL_REPLAY_REQUIRED')
    result = {}
    for row in rows:
        name = row['id']
        need(type(name) is str and name not in result, 'UNIQUE_HISTORY_ID_REQUIRED')
        need(type(row['deadline']) in (int, float)
             and type(row['sha256']) is str
             and re.fullmatch('[a-f0-9]{64}', row['sha256']) is not None,
             'EXACT_HISTORY_METADATA_REQUIRED')
        result[name] = {k: clone(row[k]) for k in
                        ('sha256', 'status', 'send_state', 'deadline')}
        result[name].update(new_effect_replay_authorized=historical_replay_authorized,
                            unknown_retained=row['send_state'] == 'unknown')
    return result


def pack(*, locations, phase, obligation, source_review, authority,
         acceptance, descriptor, selected_sources):
    """Return canonical bytes + sized refs, without reading or writing anything.

    Source review, authority and acceptance are explicit Root inputs, including
    their status/accepted/decision fields. This only fills reference bindings.
    Final driver/checker/PREP/LEAF/SHARED/TRANSPORT are mandatory parameters.
    """
    names = ('scenario', 'source_review', 'preparation', 'authority',
             'Root_acceptance', 'descriptor')
    need(set(locations) == set(names), 'EXACT_DOCUMENT_LOCATIONS_REQUIRED')
    need(len(set(locations.values())) == len(names), 'DISTINCT_LOCATIONS_REQUIRED')
    for location in locations.values():
        path(location)
    required_sources = {'driver', 'checker', 'prep', 'leaf', 'shared', 'transport',
                        'selected_tester', 'installation_closure', 'source_acceptance'}
    need(set(selected_sources) == required_sources, 'EXACT_SELECTED_SOURCE_CHAIN_REQUIRED')
    need(all(reference_shape(r) for r in selected_sources.values()),
         'SIZED_SELECTED_SOURCE_REFERENCES_REQUIRED')
    # The packager never upgrades omitted/negative decisions to accepted ones.
    need(all(k in authority for k in ('accepted', 'operator', 'authority_id',
         'created_at', 'expires_at', 'boot_id', 'gateway', 'history',
         'unknown_effects_resolved', 'old_rows_modified',
         'new_trial_for_historical_task', 'product_or_B00_acceptance',
         'no_old_task_replay', 'new_independent_inputs_only', 'ordered_predecessors')),
         'EXPLICIT_AUTHORITY_INPUTS_REQUIRED')
    need(all(k in acceptance for k in ('schema', 'status', 'operator',
         'Root_authorizes_observed_hash_binding_only', 'original_F03_BODYedit_decision',
         'privacy_preflight', 'aggregate_disk_monitor_limitations_accepted',
         'accepted_current_facts')), 'EXPLICIT_ROOT_DECISIONS_REQUIRED')
    need(all(k in source_review for k in ('decision', 'open_critical_defects',
                                         'reviewed_sources')), 'EXPLICIT_SOURCE_REVIEW_REQUIRED')
    if source_review['decision'] == 'SOURCE_ONLY_READY_UNBOUND':
        need(source_review['open_critical_defects'] == []
             and all(selected_sources[k] in source_review['reviewed_sources']
                     for k in ('driver', 'checker', 'prep', 'leaf', 'shared', 'transport')),
             'EXACT_SIX_REVIEWED_SOURCES_REQUIRED')
    documents = {}

    def add(name, value):
        value = clone(value)
        documents[name] = dict(value=value, raw=encoded(value),
                               reference=reference(locations[name], value))
        return documents[name]['reference']

    scenario_ref = add('scenario', phase['scenario'])
    need(phase['scenario_sha256'] == scenario_ref['sha256'], 'SCENARIO_DIGEST_MISMATCH')
    review_ref = add('source_review', source_review)
    phase_ref = add('preparation', phase)
    run_id = descriptor['run_id']
    authority = clone(authority)
    for key, value in dict(run_scenarios={run_id: scenario_ref['sha256']},
          word_scenario=scenario_ref, docx_original_case=obligation,
          docx_input_original=phase['input_original'],
          docx_source_scope=phase['source_scope']).items():
        bind(authority, key, value)
    authority_ref = add('authority', authority)
    bindings = {k: selected_sources[k] for k in
                ('driver', 'checker', 'selected_tester',
                 'installation_closure', 'source_acceptance')}
    bindings.update(source_review=review_ref, preparation=phase_ref,
                    authority=authority_ref)
    acceptance = clone(acceptance)
    for key, value in dict(run_id=run_id, scenario_sha256=scenario_ref['sha256'],
                           bindings=bindings).items():
        bind(acceptance, key, value)
    acceptance_ref = add('Root_acceptance', acceptance)
    descriptor = clone(descriptor)
    for key, value in dict(bindings, Root_acceptance=acceptance_ref).items():
        bind(descriptor, key, value)
    add('descriptor', descriptor)
    return documents
