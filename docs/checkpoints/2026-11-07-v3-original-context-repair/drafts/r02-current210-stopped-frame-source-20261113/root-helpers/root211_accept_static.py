"""Root's source-only acceptance. No request, admission, clock or services."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json, hashlib, os, runpy, subprocess

D = Path(__file__).parent
F = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE211-STOPPED-SCOPE-FRAME-DELTA-20261113')
R = Path('/home/jericho/jericho/Friday_rework')
H = R / '.runtime/friday-normal-both-workers-frw032'
COMMIT = '5ac70db5bc0f137e166274e40351f62b1c5ec097'
FRAME = '113ca21f49155c1427969637dfc894154caca08d64e8084082018389ebeef820'
FRAME_REVIEW = 'ea22715fed25216ae35f57bb91e7f3843190cf03fd4203af2da98b918229159d'

def load(p): return json.loads(p.read_bytes())
def ref(p): return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.chmod(p, 0o600)
    fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
def template(name, state):
    j = load(F / (name + '-TEMPLATE.json'))
    for k in list(j):
        if k.startswith('required_state_after'): j.pop(k)
    j.update(state=state, template_only_no_execution_grant=False)
    return j

def main():
    os.umask(0o077)
    assert ref(F / 'SOURCE-PINS.json')['sha256'] == FRAME
    assert ref(F / 'review/RESULT.json')['sha256'] == FRAME_REVIEW
    fr = load(F / 'review/RESULT.json')
    assert fr['accepted'] is True and not fr['blocking_findings'] and fr['state'] == 'ACCEPT_SOURCE_ONLY_STOPPED_SCOPE_DELTA_NO_CURRENT_AUTHORITY_OR_RUNTIME_GRANT'
    assert fr['source_manifest'] == ref(F / 'SOURCE-PINS.json')
    assert subprocess.check_output(['git', '--no-optional-locks', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == COMMIT
    proof_path = D.parent / 'ROOT-COMMITTED503-PRIVATE28-PROVENANCE-BOUND.json'
    assert ref(proof_path)['sha256'] == '3b91d0044968f8f5704537799b8ef965f8690a58f96d2fa9bd17309d1421f558'
    proof = load(proof_path)
    assert proof['published_commit'] == COMMIT and proof['public503_raw_Git_blobs_match'] is True
    assert proof['private503_exact_disk_match'] is True and proof['private_counterparts'] == 28
    m = runpy.run_path(str(F / 'root211_metadata.py'))
    pred = template('ROOT-ACTUAL210-PREDECESSOR', 'ROOT_RECONCILED_GENUINE_INSTALLED210_NOT_EXPECTATION')
    m['validate_predecessor_record'](pred)
    closure = load(Path(pred['complete_closure']['path']))
    for key in ('marker', 'source_receipt', 'stamp', 'input'):
        row = closure['canonical4'][key]
        assert ref(Path(row['path'])) == row
    source = {
        'schema': 'friday.Root.core211.source-integration-acceptance.v1',
        'at_moscow': datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
        'state': 'ROOT_ACCEPTED_PUBLIC503_PRIVATE28_EXACT210_NEXT_SOURCE_ONLY',
        'source_commit': COMMIT, 'provenance_mode': 'local-committed-main',
        'source_delta': ref(D.parent / 'ROOT-FINAL211-PUBLIC5-APPLIED-SOURCE-ONLY.json'),
        'committed503_private28': ref(proof_path),
        'native_source_review': m['FIXED']['independent_source_review'],
        'independent_frame_review': ref(F / 'review/RESULT.json'),
        'frame': ref(F / 'SOURCE-PINS.json'), 'native_modified': 4, 'selected_CAS_targets': 10,
        'actual_installed210_canonical4_unchanged': True,
        'actual211_installation_or_runtime_accepted': False,
        'v13_full_transaction_defaultpostconsumer': 'NOT_RUN_REQUIRED_AFTER_SAME_ADMITTED_TRANSACTION',
        'recovery_ready': False, 'original_R02_controlled_live_formal_open': True,
        'source_only': True, 'execution_grant': False,
    }
    save(D / 'ROOT-SOURCE-INTEGRATION-ACCEPTANCE.json', source)
    si = ref(D / 'ROOT-SOURCE-INTEGRATION-ACCEPTANCE.json')
    policy = template('ROOT-211-PUBLIC-ORIGIN-POLICY', 'ROOT_ACCEPTED_EXACT_COMMITTED503_PRIVATE28_SOURCE_POLICY_NOT_EXECUTION')
    policy['source_commit'] = COMMIT
    save(F / 'ROOT-211-PUBLIC-ORIGIN-POLICY.json', policy)
    project = template('ROOT-211-PROJECT-SOURCE', 'ROOT_ACCEPTED_PRIVATE503_PUBLIC5_CONNECTED_NOT_INSTALLED_NOT_GRANTED')
    project.update(all503_origin_hashes_verified=True, installed210_canonical4_unchanged=True,
                   source_commit=COMMIT, source_integration_acceptance=si,
                   origin_policy=ref(F / 'ROOT-211-PUBLIC-ORIGIN-POLICY.json'))
    save(F / 'ROOT-211-PROJECT-SOURCE.json', project)
    save(F / 'ROOT-ACTUAL210-PREDECESSOR.json', pred)
    for name, refs in [
        ('ROOT-211-INDEPENDENT-ACTUAL-BULK-ACCEPTANCE', [m['FIXED']['independent_source_review'], m['FIXED']['recipe_supplement_review']]),
        ('ROOT-211-INDEPENDENT-FRAME-ACCEPTANCE', [ref(F / 'review/RESULT.json')]),
    ]:
        j = template(name, 'ROOT_ACCEPTED_INDEPENDENT_SOURCE_ONLY_NOT_RUNTIME')
        j.update(accepted=True, approved=True, review_evidence=refs)
        if 'frame_source_manifest' in j: j['frame_source_manifest'] = ref(F / 'SOURCE-PINS.json')
        save(F / (name + '.json'), j)
    a = template('ROOT-211-SOURCE-ACCEPTANCE', 'ROOT_ACCEPTED_EXACT211_R02_SOURCE_OFFLINE_NOT_RUNTIME')
    a.update(accepted=True, source_only_evidence_accepted=True,
             source_provenance={'mode': 'local-committed-main', 'commit': COMMIT}, public_main_sha=None,
             source_integration_acceptance=si, origin_policy=ref(F / 'ROOT-211-PUBLIC-ORIGIN-POLICY.json'),
             project_source_proof=ref(F / 'ROOT-211-PROJECT-SOURCE.json'),
             independent_actual_bulk_acceptance=ref(F / 'ROOT-211-INDEPENDENT-ACTUAL-BULK-ACCEPTANCE.json'),
             independent_frame_acceptance=ref(F / 'ROOT-211-INDEPENDENT-FRAME-ACCEPTANCE.json'),
             frame_source_manifest=ref(F / 'SOURCE-PINS.json'), frame_review_evidence=[ref(F / 'review/RESULT.json')],
             independent_review_evidence=[m['FIXED']['independent_source_review'], m['FIXED']['recipe_supplement_review']])
    save(F / 'ROOT-211-SOURCE-ACCEPTANCE.json', a)
    assert m['actual_predecessor']() == pred['request']
    m['validate_independent_acceptances'](a)
    m['validate_project_binding'](a)
    origin = m['source_origin'](COMMIT, None, provenance_mode='local-committed-main', acceptance=a)
    save(D / 'ROOT-STATIC-SIX-AND-EXACT-PROVENANCE-ACCEPTED.json', {
        'schema': 'friday.Root.core211.static-source-acceptance.v1',
        'state': 'ROOT_SOURCE_ONLY_ACCEPTED_EXACT_SIX_AND_REAL_PREDECESSOR',
        'source_manifest': ref(F / 'SOURCE-PINS.json'), 'independent_frame_review': ref(F / 'review/RESULT.json'),
        'source_origin': origin, 'actual_predecessor': pred['request'],
        'source_acceptance': ref(F / 'ROOT-211-SOURCE-ACCEPTANCE.json'),
        'current_service_anchor_or_admission': False, 'actual_whole_v13_transaction_defaultpostconsumer': False,
        'recovery_ready': False,
    })
    print(json.dumps({'state': 'ROOT_STATIC_SIX_SOURCE_ONLY_ACCEPTED', 'commit': COMMIT,
                      'project': 503, 'private_counterparts': 28, 'current_authority_or_installation': False}))

if __name__ == '__main__': main()
