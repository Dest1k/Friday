#!/usr/bin/env python3
"""Small real-CP publication/rollback bench, with explicit synthetic authority seams.

No installed home is read. The real publisher, git patch application, beforeimage
journal, metadata publication and rollback execute against ~KB synthetic fixtures.
ONLY the layer-name allowlist and native/common source authority are fixture seams.
This does not establish native authority, installed acceptance, or user behavior.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time


HERE = Path(__file__).resolve().parent
BASELINE = Path(__file__).resolve().parents[2] / 'docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py'
LAYER = 'TEST-ONLY-controlled-native-successor'
NATIVE = 'hermes_cli/bench_native.py'
PLUGIN = 'plugins/friday_rework/bench_existing.py'
ADDED = 'plugins/friday_rework/bench_added.py'
SCRIPT = 'scripts/friday_native.py'
STAGED = 'native/bench_native.py'
MANIFEST = f'patches/hermes/{LAYER}-manifest.json'
PATCH = f'patches/hermes/{LAYER}.patch'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(data)
    path.chmod(mode)
    return {'path': str(path), 'sha256': digest(data)}


def snapshot(home, names):
    out = {}
    for name in names:
        path = home / name
        if not os.path.lexists(path):
            out[name] = {'state': 'ABSENT'}
        else:
            info = path.lstat()
            data = path.read_bytes()
            out[name] = {'state': 'EXISTED', 'sha256': digest(data),
                         'bytes': len(data), 'mode': stat.S_IMODE(info.st_mode)}
    return out


# Explicit test authority boundary. Actual production source authority is tested
# separately by the parent/common child. These stand-ins check fixture file pins,
# publication joins and call ordering; they NEVER return native acceptance.
STANDIN = r'''"""TEST ONLY synthetic source-authority seam; never install this file."""
import hashlib
import json
from pathlib import Path
import stat
Path(__file__).resolve().parent.parent.joinpath('TOP_LEVEL_SENTINEL').write_text('TEST_ONLY_imported')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def record(value, kind, source_update=None, **extra):
    cfg = value['_test_only_bench']
    phase = 'DEFAULT' if source_update is None else 'PROSPECTIVE'
    row = {'kind': kind, 'phase': phase, **extra}
    with Path(cfg['events']).open('a') as out:
        out.write(json.dumps(row, sort_keys=True) + '\n')
    return cfg

def composition_checked(value, source, receipt, donor, proven_cache=None):
    record(value, 'composition_checked')
    for name, row in receipt['files'].items():
        data = (Path(source) / name).read_bytes()
        assert sha(data) == row['sha256'] and len(data) == row['bytes']
    assert donor['id'] == 'hermes'
    return receipt

def spec_checked(value, cli_only=False, source_update=None):
    cfg = record(value, 'spec_checked', source_update, cli_only=cli_only)
    assert cli_only is True
    candidate = Path(cfg['candidate'])
    for name, pin in value['project_files'].items():
        assert sha((candidate / name).read_bytes()) == pin
    if source_update is not None:
        assert source_update['current_source_successor']['schema'] == 'friday.current-source-native-successor.v2'
    return value

def inspect(value, current_sha, source_update=None):
    cfg = record(value, 'inspect', source_update, input_sha256=current_sha)
    home = Path(cfg['home'])
    receipt_raw = (home / 'hermes-agent.source.json').read_bytes()
    receipt = json.loads(receipt_raw)
    marker = json.loads((home / 'FRIDAY-INSTALL.json').read_bytes())
    stamp = json.loads((home / 'hermes-agent/install-stamp.json').read_bytes())
    assert marker['input_sha256'] == current_sha
    assert marker['source_receipt_sha256'] == sha(receipt_raw)
    assert marker['ordinary_gateway']['source_receipt_sha256'] == sha(receipt_raw)
    assert stamp['fridaySource']['layers'] == receipt['layers']
    for name, row in receipt['files'].items():
        assert sha((home / 'hermes-agent' / name).read_bytes()) == row['sha256']
    for name, pin in marker['plugin_files'].items():
        assert sha((home / name).read_bytes()) == pin
    if source_update is None and cfg.get('fail_default_inspect'):
        states = {}
        for name in cfg['watched']:
            p = home / name
            states[name] = ({'state': 'EXISTED', 'sha256': sha(p.read_bytes()),
                'mode': stat.S_IMODE(p.stat().st_mode)} if p.exists() else {'state': 'ABSENT'})
        Path(cfg['final_snapshot']).write_text(json.dumps(states, sort_keys=True))
        raise RuntimeError('TEST_ONLY_final_default_inspect_failure')
    return {'state': 'TEST_ONLY_SYNTHETIC_INSPECT', 'native_authority': False}
'''


class Fixture:
    def __init__(self, root, *, successor=False, final_failure=False, native_addition=False):
        self.root = root
        self.home = root / 'home'
        self.home.mkdir(parents=True, mode=0o700)
        self.candidate = root / 'candidate'
        self.candidate.mkdir(mode=0o700)
        self.events = root / 'consumer-events.jsonl'
        self.source_before = b'def bench_native():\n    return "before"\n'
        self.source_after = b'def bench_native():\n    return "after"\n'
        self.watched = ('hermes-agent/' + NATIVE, SCRIPT, STAGED, PLUGIN, ADDED,
                        MANIFEST, PATCH, 'hermes-agent.source.json',
                        'FRIDAY-INSTALL.json', 'hermes-agent/install-stamp.json')
        source = self.home / 'hermes-agent'
        if not native_addition:
            write(source / NATIVE, self.source_before, 0o640)
        else:
            (source / Path(NATIVE).parent).mkdir(parents=True, mode=0o700)
        lock = write(root / 'sources.lock.json', encoded({'repositories': [{'id': 'hermes'}]}))
        before_files = {
            SCRIPT: b'# synthetic native operator before\n',
            PLUGIN: b'VALUE = "plugin before"\n',
            'scripts/friday_install.py': STANDIN.encode(),
            'scripts/friday_ordinary_install.py': b'# TEST ONLY inert adjacent common helper\n',
        }
        after_files = {**before_files,
            SCRIPT: b'# synthetic native operator after\n',
            PLUGIN: b'VALUE = "plugin after"\n',
            ADDED: b'VALUE = "added plugin"\n',
        }
        patch = (f'diff --git a/{NATIVE} b/{NATIVE}\n'
                 f'--- a/{NATIVE}\n+++ b/{NATIVE}\n@@ -1,2 +1,2 @@\n'
                 ' def bench_native():\n-    return "before"\n+    return "after"\n').encode()
        if native_addition:
            patch = (f'diff --git a/{NATIVE} b/{NATIVE}\nnew file mode 100644\n'
                     f'--- /dev/null\n+++ b/{NATIVE}\n@@ -0,0 +1,2 @@\n'
                     '+def bench_native():\n+    return \"after\"\n').encode()
        manifest = {'patch': PATCH, 'patch_sha256': digest(patch),
                    'base_commit': 'a' * 40, 'prerequisites': {},
                    'files': [{'path': NATIVE, 'before_sha256': None if native_addition else digest(self.source_before),
                               'sha256': digest(self.source_after),
                               'bytes': len(self.source_after), 'new_file': native_addition}]}
        after_files.update({PATCH: patch, MANIFEST: encoded(manifest)})
        for name, data in before_files.items():
            write(self.home / name, data, 0o640 if name == SCRIPT else 0o600)
        for name, data in after_files.items():
            write(self.candidate / name, data)
        bench_cfg = {'events': str(self.events), 'home': str(self.home),
                     'candidate': str(self.candidate), 'watched': self.watched,
                     'final_snapshot': str(root / 'final-consumer-state.json'),
                     'fail_default_inspect': final_failure}
        previous = {'project_files': {n: digest(d) for n, d in before_files.items()},
                    'sources_lock': lock}
        current = {'project_files': {n: digest(d) for n, d in after_files.items()},
                   'sources_lock': lock, '_test_only_bench': bench_cfg}
        self.previous = write(root / 'previous-input.json', encoded(previous))
        self.current = write(root / 'current-input.json', encoded(current))
        self.current_value = current
        receipt = {'commit': 'a' * 40, 'base_tree': 'b' * 40, 'layers': [],
                   'sources_lock_sha256': lock['sha256'],
                   'files': {NATIVE: {'sha256': digest(self.source_before),
                       'bytes': len(self.source_before), 'mode': '100644'}}}
        if native_addition:
            receipt['files'] = {}
        source_receipt = write(self.home / 'hermes-agent.source.json', encoded(receipt), 0o640)
        stamp = write(source / 'install-stamp.json', encoded({
            'fridaySource': {'baseTree': receipt['base_tree'], 'layers': []}}), 0o640)
        # This engineering152 anchor is synthetic authority but its real raw bytes,
        # source receipt pin, custody and unchanged before/after state are exercised.
        predecessor_value = {'schema': 'frw.root.engineering152-successor-request.v1',
                             'home': str(self.home), 'current_input': self.previous,
                             '_test_only': 'SYNTHETIC engineering152 anchor'}
        predecessor_raw = encoded(predecessor_value)
        anchor_dir = self.home / 'preparation' / ('ordinary-source-update-successor-' + digest(predecessor_raw))
        self.anchor_request = write(anchor_dir / 'request.json', predecessor_raw)
        self.anchor_commit = write(anchor_dir / 'committed.json', encoded({
            'state': 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED', 'gateway_started': False,
            'workers_enabled': False, 'source_receipt_sha256': source_receipt['sha256']}))
        marker_value = {'completion_stage': 'TELEGRAM_ORDINARY', 'runtime_ready': False,
            'worker_state': 'BOTH_WORKERS_PREPARATION_PENDING',
            'source_receipt_sha256': source_receipt['sha256'],
            'input_sha256': self.previous['sha256'],
            'plugin_files': {PLUGIN: previous['project_files'][PLUGIN]},
            'ordinary_gateway': {'source_receipt_sha256': source_receipt['sha256']}}
        marker = write(self.home / 'FRIDAY-INSTALL.json', encoded(marker_value), 0o640)
        refs = {'marker': marker, 'source_receipt': source_receipt, 'stamp': stamp}
        for key, rel in (('configuration', 'config.yaml'), ('profile', 'FRIDAY-PROFILE.json'),
                         ('launcher', 'hermes-agent/.hermes/bin/hermes')):
            refs[key] = write(self.home / rel, b'TEST ONLY harmless fixture\n')
        refs['native_unit'] = write(root / 'bench.service', b'# TEST ONLY never started\n')
        target_receipt = write(root / 'target-receipt.json', encoded(receipt))
        inventory = current['project_files']
        self.request = {'schema': 'friday.ordinary-telegram-source-update.v46',
            'home': str(self.home), 'bench_home': str(self.home),
            'candidate_project': str(self.candidate), 'seconds': 30,
            **refs, 'current_input': self.current, 'candidate_input': self.current,
            'previous_input': self.previous, 'predecessor_request': self.anchor_request,
            'predecessor_current_input_sha256': self.previous['sha256'],
            'predecessor_receipt_sha256': source_receipt['sha256'],
            'target_receipt': target_receipt, 'transaction_history': {},
            'installed_layers': 0, 'installed_files': 0 if native_addition else 1, 'layer_names': [LAYER],
            'project_inventory': inventory, 'project_inventory_sha256': digest(encoded(inventory)),
            'plugin_set': [PLUGIN], 'plugin_additions': [ADDED],
            'project_file_updates': [SCRIPT], 'layer_manifest_updates': [MANIFEST],
            'staged_files': [{'path': STAGED, 'source': SCRIPT}]}
        if successor:
            root_update = write(root / 'root-project-update.json', encoded({
                'schema': 'TEST_ONLY-root-project-update', 'home': str(self.home),
                'current_input': self.previous}))
            self.request['current_source_successor'] = {
                'schema': 'friday.current-source-native-successor.v2',
                'root_project_update': root_update,
                'previous_native_update': self.anchor_request}
        self.request_path = root / 'input-request.json'
        self.before = snapshot(self.home, self.watched)
        self.anchor_before = snapshot(self.home, (str(anchor_dir.relative_to(self.home) / 'request.json'),
                                                   str(anchor_dir.relative_to(self.home) / 'committed.json')))

    def anchor_unchanged(self):
        return self.anchor_before == snapshot(self.home, self.anchor_before)

    def run(self, cp, updates=None, *, bad_sha=False, raw_mutation=False,
            raw_prefix_member=None, ownership_fault=None):
        request = copy.deepcopy(self.request)
        request.update(updates or {})
        raw = encoded(request)
        if raw_prefix_member is not None:
            raw = b'{' + raw_prefix_member.encode() + raw[1:]
        write(self.request_path, raw)
        if raw_mutation:
            write(self.request_path, raw + b' ')
        if ownership_fault == 'mode':
            self.request_path.chmod(0o640)
        elif ownership_fault == 'hardlink':
            os.link(self.request_path, self.root / 'other-request-link')
        elif ownership_fault == 'symlink':
            actual = self.request_path.with_name('actual-request.json')
            self.request_path.rename(actual)
            self.request_path.symlink_to(actual)
        sha = '0' * 64 if bad_sha else digest(raw)
        os.environ['HERMES_HOME'] = str(self.home)
        # Each case represents a fresh CLI invocation. Removing ONLY the explicit
        # fixture package prevents cross-case module caching from fabricating a
        # foreign-consumer refusal before the requested publication phase.
        for name in list(sys.modules):
            if name == 'scripts' or name.startswith('scripts.'):
                del sys.modules[name]
        try:
            outcome = cp.run(request, self.request_path, sha)
            result = {'state': 'RETURNED', 'outcome': outcome}
        except BaseException as exc:
            result = {'state': 'RAISED', 'exception': type(exc).__name__, 'reason': str(exc)}
        result.update({'request_sha256': sha,
            'restored': snapshot(self.home, self.watched) == self.before,
            'anchor_unchanged': self.anchor_unchanged(),
            'events': [json.loads(x) for x in self.events.read_text().splitlines()] if self.events.exists() else []})
        self.stage = self.home / 'preparation' / ('ordinary-source-update-v45-' + sha[:16])
        result['stage'] = str(self.stage)
        result['journal_files'] = sorted(p.name for p in self.stage.iterdir()) if self.stage.exists() else []
        write(self.root / 'case-result.json', encoded(result))
        return result


def load(path):
    name = 'cp_controlled_offline_bench'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # FINITE TEST-ONLY allowlist injection. All remaining inventory/manifest/patch,
    # preimage and output validation remains the real publisher implementation.
    module.LAYER_NAMES = (*module.LAYER_NAMES, LAYER)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument('--publisher', type=Path, default=BASELINE)
    parser.add_argument('--mode', choices=('baseline', 'candidate'), default='candidate')
    parser.add_argument('--evidence-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    started = time.monotonic()
    destination = args.evidence_dir.resolve()
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    checks, cases = [], {}
    cp = load(args.publisher.resolve())
    successor = args.mode == 'candidate'

    def check(name, condition, detail=None):
        checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

    def fixture(name, **kw):
        return Fixture(destination / name, successor=successor, **kw)

    for name, kind in (('raw_hash_mismatch', 'bad_sha'), ('raw_bytes_mismatch', 'raw_mutation')):
        f = fixture(name)
        r = f.run(cp, **{kind: True})
        cases[name] = r
        rejected = r['state'] == 'RAISED' and r['restored'] and not f.stage.exists()
        check(name + '_before_effects', rejected if successor else not rejected,
              'candidate must refuse; legacy baseline is expected unsupported')
        check(name + '_anchor_immutable', r['anchor_unchanged'])

    f = fixture('success')
    r = f.run(cp)
    cases['success'] = r
    check('genuine_native_source_update', r['state'] == 'RETURNED'
          and (f.home / 'hermes-agent' / NATIVE).read_bytes() == f.source_after
          and f.source_before != f.source_after, r)
    check('success_anchor_immutable', r['anchor_unchanged'])
    if r['state'] == 'RETURNED':
        check('success_plugin_and_added_file', (f.home / PLUGIN).read_bytes() == b'VALUE = "plugin after"\n'
              and (f.home / ADDED).is_file() and (f.home / MANIFEST).is_file())
        journal_request = f.stage / 'request.json'
        intent = json.loads((f.stage / 'intent.json').read_bytes())
        committed = json.loads((f.stage / 'committed.json').read_bytes())
        if successor:
            actual_ref = {'path': str(journal_request), 'sha256': r['request_sha256']}
            check('owned_rawrequest_exact', journal_request.read_bytes() == f.request_path.read_bytes()
                  and stat.S_IMODE(journal_request.stat().st_mode) == 0o600
                  and journal_request.stat().st_uid == os.getuid() and journal_request.stat().st_nlink == 1)
            check('intent_commit_rawrequest_reference', intent.get('request_reference') == actual_ref
                  and committed.get('request_reference') == actual_ref)
            check('intent_commit_context', intent.get('current_source_successor') == f.request['current_source_successor']
                  and committed.get('current_source_successor') == f.request['current_source_successor'])
            events = [(e['kind'], e['phase']) for e in r['events'] if e['kind'] != 'composition_checked']
            check('prospective_and_default_consumer_calls', events == [
                ('spec_checked', 'PROSPECTIVE'), ('spec_checked', 'PROSPECTIVE'),
                ('inspect', 'PROSPECTIVE'), ('spec_checked', 'DEFAULT'), ('inspect', 'DEFAULT')], events)
            installed = snapshot(f.home, f.watched)
            second = f.run(cp)
            check('existing_canonical_transaction_refused', second['state'] == 'RAISED'
                  and second['reason'] == 'transaction_current_source_already_consumed'
                  and snapshot(f.home, f.watched) == installed, second)
        else:
            check('baseline_has_no_rawrequest_reference', not journal_request.exists()
                  and 'request_reference' not in intent and 'request_reference' not in committed)

    # Every injection is inside real publish() AFTER the target rename, with a
    # CP-owned durable snapshot proving changed live bytes reached this exact phase.
    boundaries = [('source', 'hermes-agent/' + NATIVE), ('native_project', SCRIPT),
                  ('plugin_addition', ADDED), ('receipt', 'hermes-agent.source.json'),
                  ('marker', 'FRIDAY-INSTALL.json'), ('stamp', 'hermes-agent/install-stamp.json')]
    for boundary_index, (name, target) in enumerate(boundaries):
        f = fixture('rollback_' + name)
        snap_dir = f.root / 'after-rename-snapshot'
        # CP's snapshot contract requires named files to exist at that phase.
        snapshot_names = [n for n in f.watched if f.before[n]['state'] == 'EXISTED']
        if boundary_index >= 1:
            snapshot_names.extend([STAGED, MANIFEST, PATCH])
        if boundary_index >= 2:
            snapshot_names.append(ADDED)
        r = f.run(cp, {'inject_after_rename': True, 'inject_target': str(f.home / target),
                      'inject_snapshot_dir': str(snap_dir), 'inject_snapshot_files': snapshot_names})
        cases['rollback_' + name] = r
        snapshots = list(snap_dir.glob('*.json')) if snap_dir.exists() else []
        state = json.loads(snapshots[0].read_bytes()) if len(snapshots) == 1 else {}
        check(name + '_failure_reached_after_rename', r['state'] == 'RAISED'
              and r.get('exception') == 'OSError' and state.get('at_target') == str(f.home / target), r)
        at_files = state.get('files', {})
        changed_source = at_files.get(str(f.home / 'hermes-agent' / NATIVE), {}).get('sha256') == digest(f.source_after)
        changed_target = at_files.get(str(f.home / target), {}).get('sha256') != f.before[target].get('sha256')
        check(name + '_snapshot_proves_changed_source_and_target', changed_source and changed_target)
        # Snapshot format belongs to actual CP, so also persist exact state for review.
        check(name + '_all_before_bytes_modes_absences_restored', r['restored'] and r['anchor_unchanged'])
        check(name + '_rollback_record_written', (f.stage / 'rolled-back.json').is_file())

    if successor:
        f = fixture('rollback_final_consumer', final_failure=True)
        r = f.run(cp)
        cases['rollback_final_consumer'] = r
        final_snapshot = f.root / 'final-consumer-state.json'
        reached = final_snapshot.exists() and r.get('reason') == 'TEST_ONLY_final_default_inspect_failure'
        check('final_default_inspect_failure_reached', reached, r)
        if reached:
            changed = json.loads(final_snapshot.read_bytes())
            check('final_inspect_saw_published_source_plugins_metadata',
                changed['hermes-agent/' + NATIVE]['sha256'] == digest(f.source_after)
                and changed[ADDED]['state'] == 'EXISTED'
                and changed['FRIDAY-INSTALL.json']['sha256'] != f.before['FRIDAY-INSTALL.json']['sha256']
                and changed['hermes-agent/install-stamp.json']['sha256'] != f.before['hermes-agent/install-stamp.json']['sha256'])
        check('final_consumer_failure_restores_exact_before', r['restored'] and r['anchor_unchanged'])
        rollback_path = f.stage / 'rolled-back.json'
        retained_commit = f.stage / 'committed.json'
        check('final_consumer_failure_durable_tombstone_and_retained_observation',
              r['state'] == 'RAISED' and rollback_path.is_file() and retained_commit.is_file()
              and json.loads(rollback_path.read_bytes())['state'] == 'ROLLED_BACK'
              and json.loads(retained_commit.read_bytes())['request_sha256'] == r['request_sha256'])

        for helper in ('scripts/friday_install.py', 'scripts/friday_ordinary_install.py'):
            f = fixture('preimport_drift_' + Path(helper).stem)
            sentinel = f.candidate / 'TOP_LEVEL_SENTINEL'
            write(f.candidate / helper, (f.candidate / helper).read_bytes() + b'\n# unauthorized helper drift\n')
            r = f.run(cp)
            cases['preimport_drift_' + Path(helper).stem] = r
            check('preimport_drift_' + Path(helper).stem + '_refused_before_top_level',
                  r['state'] == 'RAISED' and r['restored'] and not sentinel.exists()
                  and not f.stage.exists() and not r['events'], r)

        for fault in ('restore_failure', 'rollback_tombstone_failure', 'keyboard_interrupt'):
            f = fixture('rollback_' + fault)
            original_restore, original_atomic, original_publish = cp.Journal.restore, cp.write_atomic, cp.publish
            reached = {'calls': 0}

            def restore_failure(journal, paths):
                reached['calls'] += 1
                reached['state_at_failure'] = snapshot(f.home, f.watched)
                raise OSError('TEST_ONLY_actual_restore_failure')

            def tombstone_failure(path, data, mode=0o600):
                if Path(path).name == 'rolled-back.json':
                    reached['calls'] += 1
                    reached['state_at_failure'] = snapshot(f.home, f.watched)
                    raise OSError('TEST_ONLY_actual_rollback_tombstone_failure')
                return original_atomic(path, data, mode)

            def interrupt_after_native(target, data, mode=0o600):
                result = original_publish(target, data, mode)
                if Path(target) == f.home / 'hermes-agent' / NATIVE and not reached['calls']:
                    reached['calls'] += 1
                    reached['state_at_failure'] = snapshot(f.home, f.watched)
                    raise KeyboardInterrupt('TEST_ONLY_interrupt_after_real_native_publication')
                return result

            try:
                if fault == 'restore_failure':
                    cp.Journal.restore = restore_failure
                elif fault == 'rollback_tombstone_failure':
                    cp.write_atomic = tombstone_failure
                else:
                    cp.publish = interrupt_after_native
                r = f.run(cp, {} if fault == 'keyboard_interrupt' else {'fail_after_publish': True})
            finally:
                cp.Journal.restore, cp.write_atomic, cp.publish = original_restore, original_atomic, original_publish
            cases['rollback_' + fault] = {**r, 'fault': reached}
            if fault == 'keyboard_interrupt':
                check('keyboard_interrupt_after_real_effect_restores', reached['calls'] == 1
                      and reached['state_at_failure']['hermes-agent/' + NATIVE]['sha256'] == digest(f.source_after)
                      and r.get('exception') == 'KeyboardInterrupt' and r['restored']
                      and (f.stage / 'rolled-back.json').is_file(), r)
            else:
                check(fault + '_returns_stop_unconfirmed', reached['calls'] == 1
                      and r.get('exception') == 'StopUnconfirmed', r)
                check(fault + '_not_claimed_rolled_back', not (f.stage / 'rolled-back.json').exists())
                if fault == 'restore_failure':
                    check('restore_failure_retains_observed_changed_bytes', not r['restored']
                          and reached['state_at_failure']['hermes-agent/' + NATIVE]['sha256'] == digest(f.source_after))

        # Shape/type rejection is the real CP contract. Source generation/receipt/
        # root authority negatives belong to the real common-consumer suite, since
        # this fixture deliberately does not impersonate that authority.
        valid_context = copy.deepcopy(f.request['current_source_successor'])
        bad_contexts = {
            'null': None, 'bool': True, 'list': [], 'schema': {**valid_context, 'schema': 'wrong'},
            'extra': {**valid_context, 'future_exemption': True},
            'ref_bool_hash': {**valid_context, 'root_project_update': {'path': '/synthetic', 'sha256': True}},
            'ref_bool_path': {**valid_context, 'root_project_update': {'path': True, 'sha256': '0' * 64}},
            'ref_extra': {**valid_context, 'root_project_update': {**valid_context['root_project_update'], 'extra': 1}},
        }
        for name, context in bad_contexts.items():
            f = fixture('typed_context_' + name)
            r = f.run(cp, {'current_source_successor': context})
            cases['typed_context_' + name] = r
            check('typed_context_' + name + '_before_effects', r['state'] == 'RAISED'
                  and r['restored'] and not f.stage.exists() and not r['events'], r)

        for name, member, reason in (
            ('duplicate_key', '"schema":"duplicate",', 'transaction_current_source_duplicate_json_key'),
            ('nan', '"_test_float":NaN,', 'transaction_current_source_nonfinite_json'),
            ('infinity', '"_test_float":Infinity,', 'transaction_current_source_nonfinite_json'),
            ('overflow_float', '"_test_float":1e400,', 'transaction_current_source_nonfinite_json')):
            f = fixture('raw_json_' + name)
            r = f.run(cp, raw_prefix_member=member)
            cases['raw_json_' + name] = r
            check('raw_json_' + name + '_before_effects', r['state'] == 'RAISED'
                  and r.get('reason') == reason and r['restored']
                  and not f.stage.exists() and not r['events'], r)

        for name in ('mode', 'hardlink', 'symlink'):
            f = fixture('raw_custody_' + name)
            r = f.run(cp, ownership_fault=name)
            cases['raw_custody_' + name] = r
            check('raw_custody_' + name + '_before_effects', r['state'] == 'RAISED'
                  and r['restored'] and not f.stage.exists() and not r['events'], r)

        for fault in ('short_writes', 'zero_write', 'oversized_write', 'parent_fsync', 'file_fsync', 'directory_fsync'):
            f = fixture('raw_io_' + fault)
            original_write, original_fsync = cp.os.write, cp.os.fsync
            original_publish = cp.publish
            reached = {'calls': 0, 'sequence': []}

            def raw_fd(fd):
                try:
                    path = Path(os.readlink('/proc/self/fd/' + str(fd)))
                    return path.name == 'request.json' and path.parent.name.startswith('ordinary-source-update-v45-')
                except OSError:
                    return False

            def write_fault(fd, data):
                if raw_fd(fd):
                    reached['calls'] += 1
                    reached['sequence'].append('raw_write')
                    if fault == 'zero_write':
                        return 0
                    if fault == 'oversized_write':
                        return len(data) + 1
                    if fault == 'short_writes':
                        return original_write(fd, data[:7])
                return original_write(fd, data)

            def fsync_fault(fd):
                target = Path(os.readlink('/proc/self/fd/' + str(fd)))
                parent_directory = target == f.home / 'preparation'
                if parent_directory:
                    reached['sequence'].append('parent_fsync')
                directory = target.name.startswith('ordinary-source-update-v45-') and (target / 'request.json').is_file()
                if ((fault == 'parent_fsync' and parent_directory)
                    or (fault == 'file_fsync' and raw_fd(fd))
                    or (fault == 'directory_fsync' and directory)):
                    reached['calls'] += 1
                    raise OSError('TEST_ONLY_rawrequest_' + fault)
                return original_fsync(fd)

            def publish_trace(target, data, mode=0o600):
                reached['sequence'].append('publish:' + str(target))
                return original_publish(target, data, mode)

            try:
                cp.os.write = write_fault
                cp.os.fsync = fsync_fault
                cp.publish = publish_trace
                r = f.run(cp)
            finally:
                cp.os.write, cp.os.fsync = original_write, original_fsync
                cp.publish = original_publish
            cases['raw_io_' + fault] = {**r, 'fault_calls': reached['calls'], 'sequence': reached['sequence']}
            if fault == 'short_writes':
                check('rawrequest_short_writes_complete', reached['calls'] > 1 and r['state'] == 'RETURNED'
                      and (f.stage / 'request.json').read_bytes() == f.request_path.read_bytes(), r)
                sequence = reached['sequence']
                first_publish = next((i for i, item in enumerate(sequence) if item.startswith('publish:')), -1)
                check('transaction_parent_durable_before_raw_and_publication', 'parent_fsync' in sequence
                      and sequence.index('parent_fsync') < sequence.index('raw_write') < first_publish,
                      sequence[:5] + ['...'] + sequence[-5:])
            else:
                check('rawrequest_' + fault + '_before_effects', reached['calls'] > 0
                      and r['state'] == 'RAISED' and r['restored'] and r['anchor_unchanged']
                      and not (f.stage / 'intent.json').exists()
                      and not (f.stage / 'committed.json').exists(), r)
                retry = f.run(cp)
                check('rawrequest_' + fault + '_consumed_no_retry', retry['state'] == 'RAISED'
                      and retry['reason'] == 'transaction_current_source_already_consumed'
                      and retry['restored'], retry)
                if fault == 'parent_fsync':
                    check('parent_fsync_failure_before_raw_and_first_publish', reached['sequence'] == ['parent_fsync']
                          and not (f.stage / 'request.json').exists(), reached['sequence'])

    # Real new native-file staging/journalling: absent beforeimage, success and
    # final committed DEFAULT refusal, then consumed replay. No installed home.
    for label, final_failure in [('native_addition_success', False), ('native_addition_late_rollback', True)]:
        f = fixture(label, native_addition=True, final_failure=final_failure)
        r = f.run(cp); cases[label] = r
        absent_before = f.before['hermes-agent/' + NATIVE]['state'] == 'ABSENT'
        check(label + '_genuine_absent_before', absent_before, r)
        if final_failure:
            check(label + '_late_default_reached', r['state'] == 'RAISED'
                  and 'final_default_inspect_failure' in r.get('reason', '')
                  and f.root.joinpath('final-consumer-state.json').exists(), r)
            check(label + '_exact_restoration_and_new_file_removed', r['restored']
                  and not (f.home / 'hermes-agent' / NATIVE).exists(), r)
            check(label + '_rolled_back', (f.stage / 'rolled-back.json').exists(), r)
        else:
            check(label + '_published_exact', r['state'] == 'RETURNED'
                  and (f.home / 'hermes-agent' / NATIVE).read_bytes() == f.source_after, r)
            receipt = json.loads((f.home / 'hermes-agent.source.json').read_bytes())
            check(label + '_one_new_receipt_row', len(receipt['files']) == 1
                  and receipt['files'][NATIVE]['sha256'] == digest(f.source_after), r)
        check(label + '_historical_anchor_immutable', r['anchor_unchanged'], r)
        replay = f.run(cp); cases[label + '_replay'] = replay
        check(label + '_consumed_replay_refused', replay['state'] == 'RAISED'
              and replay['reason'] == 'transaction_current_source_already_consumed', replay)

    for fault in ('occupied', 'symlink', 'parent_link', 'missing_parent'):
        f = fixture('native_addition_refuse_' + fault, native_addition=True)
        target = f.home / 'hermes-agent' / NATIVE
        if fault == 'occupied':
            write(target, b'TEST_ONLY_foreign_existing')
        elif fault == 'symlink':
            foreign = f.root / 'foreign.txt'; write(foreign, b'TEST_ONLY_foreign')
            target.symlink_to(foreign)
        elif fault == 'parent_link':
            foreign = f.root / 'foreign-directory'; foreign.mkdir()
            target.parent.rmdir(); target.parent.symlink_to(foreign)
        else:
            target.parent.rmdir()
        f.before = snapshot(f.home, f.watched)
        r = f.run(cp); cases['native_addition_refuse_' + fault] = r
        check('native_addition_' + fault + '_refused_before_staging', r['state'] == 'RAISED'
              and not f.stage.exists() and r['restored'] and r['anchor_unchanged'], r)

    for fault in ('hash', 'mode'):
        f = fixture('native_addition_rollback_foreign_' + fault, native_addition=True)
        real_consumer = cp.current_source_consumer_checked
        def changed_before_refusal(value, request, candidate, *, committed=False, inspect=False):
            real_consumer(value, request, candidate, committed=committed, inspect=inspect)
            if committed and inspect:
                target = f.home / 'hermes-agent' / NATIVE
                if fault == 'hash':
                    target.write_bytes(b'TEST_ONLY_foreign_afterimage')
                else:
                    target.chmod(0o640)
                raise RuntimeError('TEST_ONLY_late_foreign_afterimage')
        cp.current_source_consumer_checked = changed_before_refusal
        try:
            r = f.run(cp)
        finally:
            cp.current_source_consumer_checked = real_consumer
        cases['native_addition_rollback_foreign_' + fault] = r
        target = f.home / 'hermes-agent' / NATIVE
        check('native_addition_foreign_' + fault + '_STOP_UNCONFIRMED', r['state'] == 'RAISED'
              and r.get('exception') == 'StopUnconfirmed' and target.exists()
              and not (f.stage / 'rolled-back.json').exists(), r)
        check('native_addition_foreign_' + fault + '_preserved',
              target.read_bytes() == b'TEST_ONLY_foreign_afterimage' if fault == 'hash'
              else stat.S_IMODE(target.stat().st_mode) == 0o640, r)

    for fault in ('broken_symlink', 'directory', 'permission_error'):
        f = fixture('native_addition_absence_' + fault, native_addition=True)
        source = f.home / 'hermes-agent'; target = source / NATIVE
        if fault == 'broken_symlink':
            target.symlink_to(f.root / 'does-not-exist')
        elif fault == 'directory':
            target.mkdir()
        original_lstat = Path.lstat
        if fault == 'permission_error':
            def denied(path, *args, **kw):
                if path == target:
                    raise PermissionError('TEST_ONLY_source_absence_permission_error')
                return original_lstat(path, *args, **kw)
            Path.lstat = denied
        try:
            try:
                cp.new_source_absence_checked(source, NATIVE)
            except (cp.Refused, PermissionError):
                check('native_addition_' + fault + '_never_absent', True)
            else:
                check('native_addition_' + fault + '_never_absent', False)
        finally:
            Path.lstat = original_lstat

    result = {'schema': 'TEST_ONLY-real-cp-offline-bench.v1',
              'result': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'mode': args.mode, 'publisher': str(args.publisher.resolve()),
              'publisher_sha256': digest(args.publisher.read_bytes()),
              'test_sha256': digest(Path(__file__).read_bytes()),
              'checks': checks, 'cases': cases, 'elapsed_seconds': round(time.monotonic() - started, 3),
              'limits': ['SYNTHETIC authority and composition boundary, not native PASS',
                         'TEST-ONLY finite layer-name allowlist injection',
                         'No installed-home data, model/network/service/native execution',
                         'Actual CP.run, git apply, journal, publish and rollback execute']}
    write(destination / 'RESULT.json', encoded(result))
    print(json.dumps({'result': result['result'], 'checks': len(checks),
                      'failed': [c['name'] for c in checks if not c['passed']],
                      'evidence': str(destination / 'RESULT.json')}))
    return 0 if result['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
