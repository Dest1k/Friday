"""Explicit continuation with fixture authority; no real installer execution."""
import copy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from scripts import friday_install as entry, install_containment as custody
from test_native_installer import install_input


def save(path, value, *, immutable=True):
    entry.publish(path, value)
    if immutable: path.chmod(0o400)
    return path


def setup(value, tmp_path, input_path=None):
    value['hermes_prepare'] = {'path': str(entry.ROOT / 'scripts/hermes_prepare.py'),
                              'sha256': value['project_files']['scripts/hermes_prepare.py']}
    old = copy.deepcopy(value)
    old['project_files']['scripts/friday_install.py'] = '1' * 64
    old_path = save(tmp_path / 'original-input.json', old)
    path = input_path or tmp_path / 'input.json'
    if path.exists(): path.write_text(json.dumps(value)); path.chmod(0o600)
    else: save(path, value, immutable=False)
    home = Path(value['home']); home.mkdir(mode=0o700)
    budget = custody.Budget(value['seconds'])
    claim = entry.partial_claim(entry.digest(old_path.read_bytes()), budget)
    save(home / entry.MARKER, claim, immutable=False)
    raw = (home / entry.MARKER).read_bytes()
    pins = lambda p: {'path': str(p), 'sha256': entry.digest(p.read_bytes())}
    census = save(tmp_path / 'census.json', {
        'schema': 'friday.readonly-namespace-init-census.v1', 'assignment': 'FRW032-INSTALL-CUSTODY-REVIEW#1',
        'boot_id': claim['boot_id'], 'boot_id_after': claim['boot_id'], 'original_boot_matches': True,
        'completed_msk': 'FIXTURE_ONLY', 'returned_sha256': '2'*64,
        'listed_count': 2, 'read_count': 2, 'read_errors': [], 'vanished_during_read': [],
        'candidate_processes': [], 'inclusive_candidate_starttime_ticks': [2, 5],
        'rows': [{'pid': 1, 'starttime_ticks': 1}, {'pid': 10, 'starttime_ticks': 10}]})
    cessation = save(tmp_path / 'cessation.json', {
        'assignment': 'FRW032-INSTALL-CUSTODY-REVIEW', 'generation': 1,
        'verdict': 'FIRST_ATTEMPT_CESSATION_ESTABLISHED_RETROSPECTIVELY_AT_CENSUS; GENERAL_CONTAINMENT_COMPLETION_BARRIER_INSUFFICIENT',
        'exact_refs': {'census': pins(census), 'marker': {'sha256': entry.digest(raw)}, 'returned': {'sha256': '2'*64}},
        'first_attempt': {'assignment': 'FRW032-NORMAL-INSTALL-FIRST-ATTEMPT#1',
                         'cessation_established': True, 'claim_preserved': claim,
                         'established_as_of_msk': 'FIXTURE_ONLY',
                         'original_installer_seconds': value['seconds'], 'resume_granted': False}})
    hashes = {'original_claim_sha256': entry.digest(raw),
              'original_input_sha256': entry.digest(old_path.read_bytes()),
              'current_input_sha256': entry.digest(path.read_bytes())}
    review = save(tmp_path / 'review.json', {
        'schema': 'friday.pre-compose-repair-review.v1', 'reviewer': 'Astra',
        'decision': 'ALLOW_PRECOMPOSE_CONTINUATION', 'stage': 'BEFORE_COMPOSE',
        **hashes, 'cessation_review_sha256': entry.digest(cessation.read_bytes()),
        'source_changes': {'scripts/friday_install.py':
                          {'before': '1' * 64, 'after': value['project_files']['scripts/friday_install.py']}}})
    auth = save(tmp_path / 'authorization.json', {'schema': 'friday.pre-compose-continuation.v1',
                **hashes, 'cessation_review': pins(cessation), 'repair_review': pins(review)})
    return {'path': path, 'old': old_path, 'auth': auth, 'sha': entry.digest(auth.read_bytes()),
            'home': home, 'raw': raw, 'claim': claim, 'review': review, 'cessation': cessation, 'census': census}


def continue_fixture(value, data):
    return entry.continue_install(value, data['path'], data['auth'], data['sha'], data['old'],
                                  started=time.monotonic())


def update_authority(data, target, mutation):
    body = entry.read_json(data[target]); mutation(body)
    data[target].chmod(0o600); data[target].write_text(json.dumps(body)); data[target].chmod(0o400)
    if target != 'auth':
        auth = entry.read_json(data['auth'])
        auth['repair_review' if target == 'review' else 'cessation_review']['sha256'] = entry.digest(data[target].read_bytes())
        data['auth'].chmod(0o600); data['auth'].write_text(json.dumps(auth)); data['auth'].chmod(0o400)
    data['sha'] = entry.digest(data['auth'].read_bytes())


@pytest.mark.parametrize('case', ['candidate', 'unreadable', 'vanished', 'count', 'duplicate', 'different_boot', 'interval'])
def test_review_label_cannot_substitute_for_complete_bound_census(install_input, tmp_path, case):
    data = setup(install_input, tmp_path)
    body = entry.read_json(data['census'])
    if case == 'candidate': body['rows'][1]['starttime_ticks'] = 3
    elif case == 'unreadable': body['read_errors'] = ['fixture-error']
    elif case == 'vanished': body['vanished_during_read'] = [10]
    elif case == 'count': body['listed_count'] += 1
    elif case == 'duplicate': body['rows'][1]['pid'] = 1
    elif case == 'different_boot': body['boot_id_after'] = 'other-boot'
    else: body['inclusive_candidate_starttime_ticks'] = [5, 2]
    data['census'].chmod(0o600); data['census'].write_text(json.dumps(body)); data['census'].chmod(0o400)
    update_authority(data, 'cessation', lambda b: b['exact_refs']['census'].update(sha256=entry.digest(data['census'].read_bytes())))
    with pytest.raises(ValueError, match='complete_reviewed_cessation_census_required'):
        continue_fixture(install_input, data)
    assert (data['home']/entry.MARKER).read_bytes() == data['raw']


def test_continuation_preserves_raw_history_and_original_clock_before_existing_loop(install_input, tmp_path, monkeypatch):
    data = setup(install_input, tmp_path); seen = []
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: seen.append('probe'))
    def loop(value, path, home, donors, argv, containment, budget, claim):
        assert budget.deadline == data['claim']['deadline_mono']
        assert claim['input_sha256'] == entry.digest(path.read_bytes())
        assert entry.active_claim_checked(value, claim['input_sha256'], budget) == claim
        assert (home / entry.HISTORY['claim']).read_bytes() == data['raw']
        assert (home / entry.HISTORY['input']).read_bytes() == data['old'].read_bytes()
        assert all((home / n).stat().st_mode & 0o777 == 0o400 for n in entry.HISTORY.values())
        seen.append('same_existing_loop')
        return {'state': 'FIXTURE_ONLY'}
    monkeypatch.setattr(entry, '_install_claimed', loop)
    result, budget = continue_fixture(install_input, data)
    assert result == {'state': 'FIXTURE_ONLY'} and seen == ['probe', 'same_existing_loop']
    assert budget.deadline == data['claim']['deadline_mono']
    with pytest.raises(ValueError): continue_fixture(install_input, data)
    assert seen == ['probe', 'same_existing_loop']


@pytest.mark.parametrize('case', ['expired', 'boot', 'new_home', 'pause', 'cancel', 'work', 'failure',
    'partial_history', 'changed_claim', 'input', 'auth_pin', 'mutable_auth', 'writer',
    'cessation_false', 'cessation_foreign', 'review_ready', 'review_foreign', 'review_stage',
    'review_delta', 'review_clock', 'mutable_review', 'auth_link', 'old_link'])
def test_ambiguous_or_unreviewed_continuation_refuses_before_effect(install_input, tmp_path, monkeypatch, case):
    data = setup(install_input, tmp_path); marker = data['home'] / entry.MARKER
    if case in ('expired', 'boot', 'changed_claim'):
        body = entry.read_json(marker)
        if case == 'expired': body['deadline_mono'] = time.monotonic() - 1
        elif case == 'boot': body['boot_id'] = 'another-boot'
        else: body['state'] = 'CANCELLED'
        marker.write_text(json.dumps(body))
    elif case == 'new_home': install_input['home'] = str(tmp_path / 'other')
    elif case in ('pause', 'cancel', 'work', 'failure', 'partial_history'):
        save(data['home'] / case, {'retain': True})
    elif case == 'input': data['path'].write_text('{}')
    elif case == 'auth_pin': data['sha'] = '0' * 64
    elif case == 'mutable_auth': data['auth'].chmod(0o600)
    elif case == 'cessation_false': update_authority(data, 'cessation', lambda b: b['first_attempt'].update(cessation_established=False))
    elif case == 'cessation_foreign': update_authority(data, 'cessation', lambda b: b['first_attempt']['claim_preserved'].update(input_sha256='0'*64))
    elif case == 'review_ready': update_authority(data, 'review', lambda b: b.update(decision='READY'))
    elif case == 'review_foreign': update_authority(data, 'review', lambda b: b.update(reviewer='Sol'))
    elif case == 'review_stage': update_authority(data, 'review', lambda b: b.update(stage='AFTER_PM'))
    elif case == 'review_delta': update_authority(data, 'review', lambda b: b.update(source_changes={}))
    elif case == 'review_clock': update_authority(data, 'review', lambda b: b.update(current_input_sha256='0'*64))
    elif case == 'mutable_review': data['review'].chmod(0o600)
    elif case in ('auth_link', 'old_link'):
        p = data['auth' if case == 'auth_link' else 'old']; retained = p.with_suffix('.saved')
        p.rename(retained); p.symlink_to(retained)
    lock = None
    if case == 'writer':
        lock = open(marker, 'rb'); fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    before = {p.name: p.read_bytes() for p in data['home'].iterdir()}
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: pytest.fail('refusal launched namespace'))
    monkeypatch.setattr(entry, '_install_claimed', lambda *a: pytest.fail('refusal entered installer'))
    try:
        with pytest.raises((ValueError, OSError)): continue_fixture(install_input, data)
    finally:
        if lock: lock.close()
    assert {p.name: p.read_bytes() for p in data['home'].iterdir()} == before


@pytest.mark.parametrize('key,change', [('home', 'different'), ('seconds', 3600),
    ('product', {'ready': True}), ('containment', {'path': '/fake', 'sha256': '0'*64}),
    ('hermes_donor', '/another'), ('dashboard_tls', {})])
def test_settings_and_grants_cannot_change_with_source_repair(install_input, tmp_path, key, change):
    data = setup(install_input, tmp_path); changed = copy.deepcopy(install_input); changed[key] = change
    with pytest.raises(ValueError, match='continuation_settings_changed'):
        entry.continuation_evidence(changed, entry.digest(data['path'].read_bytes()), data['auth'].read_bytes(),
                                    data['sha'], data['raw'], data['old'].read_bytes())


@pytest.mark.parametrize('change', ['deadline', 'boot', 'history', 'authority'])
def test_native_consumer_cannot_reset_or_forge_continued_lineage(install_input, tmp_path, monkeypatch, change):
    data = setup(install_input, tmp_path)
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: None)
    monkeypatch.setattr(entry, '_install_claimed', lambda *a: {})
    _, budget = continue_fixture(install_input, data)
    claim = entry.read_json(data['home'] / entry.MARKER)
    if change == 'deadline': budget.deadline += 1
    elif change == 'boot': claim['boot_id'] = 'other'; (data['home'] / entry.MARKER).write_text(json.dumps(claim))
    else:
        p = data['home'] / entry.HISTORY['claim' if change == 'history' else 'authorization']
        p.chmod(0o600); p.write_text('{}'); p.chmod(0o400)
    with pytest.raises(ValueError): entry.active_claim_checked(install_input, entry.digest(data['path'].read_bytes()), budget)


@pytest.mark.parametrize('case', ['missing_authority', 'expired', 'review_ready'])
def test_actual_cold_cli_refusals_preserve_partial(install_input, tmp_path, case):
    data = setup(install_input, tmp_path); marker = data['home'] / entry.MARKER
    if case == 'expired':
        body = entry.read_json(marker); body['deadline_mono'] = time.monotonic()-1; marker.write_text(json.dumps(body))
    if case == 'review_ready': update_authority(data, 'review', lambda b: b.update(decision='READY'))
    before = marker.read_bytes(); e = Path(os.environ['FRIDAY_FIXTURE_EVIDENCE'])
    args = [sys.executable, '-B', str(e/'cli_guard.py'), str(entry.ROOT/'scripts/friday_install.py'),
            'continue', '--input', str(data['path'])]
    if case != 'missing_authority':
        args += ['--continuation', str(data['auth']), '--continuation-sha256', data['sha'], '--original-input', str(data['old'])]
    result = subprocess.run(args, cwd=tmp_path, env={'PATH':os.defpath,'HOME':str(tmp_path),
                            'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=8)
    assert result.returncode == 2 and 'Friday entry refused:' in result.stderr and not result.stdout
    assert 'Traceback' not in result.stderr and marker.read_bytes() == before
    assert sorted(p.name for p in data['home'].iterdir()) == [entry.MARKER]


def test_whole_continuation_uses_actual_cli_existing_loop_and_completed_inspection(install_input, tmp_path, monkeypatch, capsys):
    from test_native_installer import test_whole_finite_composition_and_completed_idempotence_with_native_config as whole
    original_install = entry.install; captured = {}
    def redirected(value, path):
        if Path(value['home']).exists(): return original_install(value, path)
        data = setup(value, tmp_path, path); captured.update(data)
        with monkeypatch.context() as cli:
            cli.setattr(sys, 'argv', ['friday', 'continue', '--input', str(path),
                        '--continuation', str(data['auth']), '--continuation-sha256', data['sha'],
                        '--original-input', str(data['old'])])
            entry.main()
        result = json.loads(capsys.readouterr().out)
        assert result['original_attempt']['deadline_mono'] == data['claim']['deadline_mono']
        assert result['original_attempt']['continuation']['original_claim_sha256'] == entry.digest(data['raw'])
        return result
    monkeypatch.setattr(entry, 'install', redirected)
    whole(install_input, tmp_path, monkeypatch, 'exa-keyless')
    assert (captured['home'] / entry.HISTORY['claim']).read_bytes() == captured['raw']


def test_native_cli_consumes_continued_claim_before_any_native_import_or_effect(install_input, tmp_path, monkeypatch):
    from scripts import friday_native
    data = setup(install_input, tmp_path)
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: None)
    monkeypatch.setattr(entry, '_install_claimed', lambda *a: {})
    _, budget = continue_fixture(install_input, data)
    save(data['home'] / 'hermes-agent.source.json', {})
    def after_claim(*a): raise RuntimeError('AFTER_CONTINUED_CLAIM_BEFORE_NATIVE_EFFECT')
    monkeypatch.setattr(entry, 'composition_checked', after_claim)
    monkeypatch.setattr(sys, 'argv', ['friday-native', 'install', '--input', str(data['path']),
                                    '--deadline', str(budget.deadline)])
    with pytest.raises(RuntimeError, match='AFTER_CONTINUED_CLAIM_BEFORE_NATIVE_EFFECT'): friday_native.main()


def test_probe_failure_retains_exact_original_before_any_transition(install_input, tmp_path, monkeypatch):
    data = setup(install_input, tmp_path)
    def refuse(*a): raise ValueError('fixture_namespace_unavailable')
    monkeypatch.setattr(custody.Containment, 'probe', refuse)
    with pytest.raises(ValueError, match='fixture_namespace_unavailable'): continue_fixture(install_input, data)
    assert sorted(p.name for p in data['home'].iterdir()) == [entry.MARKER]
    assert (data['home'] / entry.MARKER).read_bytes() == data['raw']


@pytest.mark.parametrize('after', ['claim', 'input', 'authorization'])
def test_interrupted_history_publication_preserves_original_and_refuses_automatic_retry(install_input, tmp_path, monkeypatch, after):
    data = setup(install_input, tmp_path); original = entry.preserve_bytes
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: None)
    def interrupted(path, raw, budget):
        original(path, raw, budget)
        if path.name == entry.HISTORY[after]: raise ValueError('fixture_durable_publication_interrupted')
    monkeypatch.setattr(entry, 'preserve_bytes', interrupted)
    with pytest.raises(ValueError, match='fixture_durable_publication_interrupted'): continue_fixture(install_input, data)
    assert (data['home']/entry.MARKER).read_bytes() == data['raw']
    assert (data['home']/entry.HISTORY['claim']).read_bytes() == data['raw']
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: pytest.fail('retry ran capability'))
    with pytest.raises(ValueError, match='precompose_home_not_pristine'): continue_fixture(install_input, data)


def test_stop_record_arriving_during_probe_refuses_before_history_transition(install_input, tmp_path, monkeypatch):
    data = setup(install_input, tmp_path)
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: save(data['home']/'pause', {'intent': 'retain'}))
    with pytest.raises(ValueError, match='precompose_home_not_pristine'): continue_fixture(install_input, data)
    assert (data['home']/entry.MARKER).read_bytes() == data['raw']
    assert sorted(p.name for p in data['home'].iterdir()) == [entry.MARKER, 'pause']


def test_stop_record_during_history_publication_retains_original_and_history(install_input, tmp_path, monkeypatch):
    data = setup(install_input, tmp_path); original = entry.preserve_bytes
    monkeypatch.setattr(custody.Containment, 'probe', lambda *a: None)
    def paused(path, raw, budget):
        original(path, raw, budget)
        if path.name == entry.HISTORY['authorization']: save(data['home']/'cancel', {'intent': 'retain'})
    monkeypatch.setattr(entry, 'preserve_bytes', paused)
    monkeypatch.setattr(entry, '_install_claimed', lambda *a: pytest.fail('stop entered installer'))
    with pytest.raises(ValueError, match='precompose_home_changed_during_transition'): continue_fixture(install_input, data)
    assert (data['home']/entry.MARKER).read_bytes() == data['raw']
    assert (data['home']/entry.HISTORY['claim']).read_bytes() == data['raw']
    assert entry.read_json(data['home']/'cancel') == {'intent': 'retain'}
