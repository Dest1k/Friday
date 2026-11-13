"""Read-only independent assessment of saved file observations and exact source receipt join."""
import hashlib
import json
import pathlib

F = pathlib.Path(__file__).resolve().parent
B = F.parent
cases = json.loads((B / 'file-fixture/observations.json').read_bytes())
published = json.loads((B / 'file-fixture/RESULT.json').read_bytes())
checks = []

def record(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))
    assert condition, name

def row(name, action='single', index=0):
    return [r for r in cases if r['case'] == name and r['action'] == action][index]

def unknown(r):
    states = r['observed']['states']
    return len(states) == 1 and bool(states[0]['ordinary']['files']) and all(
        f['state'] == 'UNKNOWN' for f in states[0]['ordinary']['files'].values())

def fenced(r, sends):
    returned = r['returned']
    guard = returned['actual_prior_history_guard']
    return (guard == dict(message='native_commit_UNKNOWN:LOCKED', primary='delivery_requires_reconciliation',
                          replaced=False, stage='LOCKED', type='NativeCommitUncertain')
            and returned['result']['error'] == 'gateway_document_preflight_rejected'
            and r['observed']['document_sends'] == sends)

for name, code, sends in [('before_transport', 71, 0), ('after_remote', 72, 1)]:
    cut, recovered = row(name), row(name, 'recover')
    record(name + '_durable_unknown_at_cut', cut['exit_code'] == code and unknown(cut)
           and len(cut['observed']['journals']) == 3 and cut['observed']['document_sends'] == sends)
    record(name + '_fresh_process_prior_guard_no_resend', recovered['exit_code'] == 0
           and recovered['pid'] != cut['pid'] and fenced(recovered, sends))
healthy = row('healthy', 'dispatch')
returned = healthy['returned']
record('real_dispatch_deduplicates_and_confirms_receipt', returned['handled'] is True
       and len(returned['results']) == 1 and returned['results'][0]['success'] is True
       and healthy['observed']['document_sends'] == 1 and len(healthy['observed']['journals']) == 4)
record('healthy_same_ingress_replay_fenced_without_resend', fenced(row('healthy', 'recover'), 1))
lost = row('after_remote', 'recover', -1)
record('lost_current_state_real_immutable_history_fences_replay', fenced(lost, 1) and not lost['observed']['states'])
marker = row('before_transport', 'single', -1)
record('lost_current_row_selection_marker_only_fences_replay', marker['returned']['result']['error'] == 'gateway_document_preflight_rejected'
       and marker['observed']['document_sends'] == 0 and not marker['observed']['states'] and len(marker['observed']['journals']) == 1)
for scenario in ('owner_mismatch', 'route_mismatch', 'unauthorized', 'cancelled'):
    r = row(scenario)
    record(scenario + '_preflight_no_effect', r['returned']['result']['error'] == 'gateway_document_preflight_rejected'
           and r['observed']['document_sends'] == 0 and not r['observed']['states'])
for scenario in ('cancel_after_reserve', 'owner_change_after_reserve', 'route_change_after_reserve'):
    r = row(scenario)
    record(scenario + '_retains_unknown_without_transport', unknown(r) and r['observed']['document_sends'] == 0
           and r['returned']['result']['success'] is False)
for scenario in ('missing_ack', 'bad_ack_route', 'cas_change_before_final'):
    r = row(scenario)
    record(scenario + '_remote_accepted_but_unknown', unknown(r) and r['observed']['document_sends'] == 1
           and r['returned']['result']['error'] == 'document_delivery_UNKNOWN')
    record(scenario + '_recovery_no_resend', fenced(row(scenario, 'recover'), 1))
assert len(checks) == 21
assert {c['name'] for c in checks} == {c['check'] for c in published['checks']}
initial = json.loads((B / 'file-fixture/INITIAL-ENVELOPE-CHECKER-ERROR-RESULT.json').read_bytes())
corrected_names = {c['check'] for c in published['checks'] if c.get('corrected_checker_accepts_actual_native_envelope')}
assert {c['assertion'] for c in initial['failures']} == corrected_names
assert published['checker_correction']['repeated_consumer_processes'] == published['checker_correction']['repeated_transport_effects'] == 0
assert hashlib.sha256((B / 'file-fixture/observations.json').read_bytes()).hexdigest() == published['checker_correction']['observations_unchanged_sha256']
assert len(cases) == len(published['cleanup']['children']) == 23
assert {(r['pid'], r['exit_code']) for r in cases} == {(r['pid'], r['exit_code']) for r in published['cleanup']['children']}
assert all(r['reaped'] for r in published['cleanup']['children'])
cas = json.loads((B / 'SOURCE209-CAS.json').read_bytes())
receipt_raw = pathlib.Path(cas['receipt']['path']).read_bytes()
assert hashlib.sha256(receipt_raw).hexdigest() == cas['receipt']['sha256']
receipt = json.loads(receipt_raw)
prefix = pathlib.Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
for entry in cas['selected_sources']:
    relative = str(pathlib.Path(entry['path']).relative_to(prefix))
    assert receipt['files'][relative] == entry['installed_receipt_entry']
assert len(receipt['layers']) == 209 and len(receipt['files']) == 17891 and receipt['source_file_count'] == 17730
assert receipt['commit'] == '781334eea4b9225a3e194faf0c241d9afe218634'
closed = json.loads(pathlib.Path(cas['actual209_closed']['path']).read_bytes())
assert closed['source_commit'] == '35c85be3a80999ee352a781d4990df3ba955e634'
assert closed['source_commit'] == json.loads((B / 'MANIFEST.json').read_bytes())['selected_installed_prefix']['source_commit']
extra = []
for rel, expected in [('TEXT-SEAMS.json', 'bd710a0731fbc6ca989f51369f7965fe63b01fca77ebda52b2274bef76d46d57')]:
    raw = (B / rel).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == expected
    extra.append(dict(path=str(B / rel), bytes=len(raw), sha256=actual))
result = dict(status='PASS', independent_saved_file_checks=checks,
              actual_consumer_runs=0, actual_transport_repeats=0,
              native_envelope_checker_correction='Seven original assertion failures match exactly seven corrected guards; all saved observations independently satisfy those conditions.',
              source_receipt_join=dict(selected_entries=15, layers=209, native_file_entries=17891,
                                       base_source_file_count=17730, native_vanilla_commit=receipt['commit'],
                                       project_source_commit=closed['source_commit'],
                                       scope='Exact selected source entries and receipt bytes only; not full installed tree readback or runtime config/admission.'),
              own_checker_correction='Initial checker assumed the project source commit must equal the native vanilla receipt commit. Existing pinned closure supplies the project source commit; the receipt correctly retains its distinct vanilla commit. Corrected only this pure assertion; no consumer/model/transport was run or repeated.',
              extra_pins=extra)
out = F / 'SAVED-OBSERVATION-CHECKS.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(status='PASS', file_checks=len(checks), source_entries=15, sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
