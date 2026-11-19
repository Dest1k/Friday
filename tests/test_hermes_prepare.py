"""Real local Git source/patch composition; no donor code or services execute."""
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

M = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/hermes_prepare.py'))
sha = M['sha']


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.donor = self.root / 'donor'; self.donor.mkdir()
        self.repo = self.root / 'product'; self.repo.mkdir()
        self.patches = self.repo / 'patches/hermes'; self.patches.mkdir(parents=True)
        self.dest = self.root / 'composed'
        self.git('init', '-q')
        self.git('remote', 'add', 'origin', 'https://github.com/NousResearch/hermes-agent.git')
        (self.donor / 'base.txt').write_text('original\n')
        (self.donor / 'untouched.txt').write_text('preserve complete donor\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid', 'commit', '-qm', 'fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()
        tree = self.git('rev-parse', 'HEAD^{tree}').strip()
        self.lock = {'repositories': [{'id': 'hermes', 'commit': self.commit, 'tree': tree,
                                     'clone_url': 'https://github.com/NousResearch/hermes-agent.git'}]}
        self.save_lock()
        self.first = self.layer('z-first', 'original', 'changed')
        self.second = self.layer('a-second', 'changed', 'final',
                                 {'z-first.patch': self.first['patch_sha256']})

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '--no-optional-locks', '-C', str(self.donor), *args],
                                       env=dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull),
                                       stderr=subprocess.PIPE, text=True, timeout=5)

    def save_lock(self):
        (self.repo / 'sources.lock.json').write_text(json.dumps(self.lock))

    def layer(self, name, before, after, requires=None):
        patch = (f'diff --git a/base.txt b/base.txt\n--- a/base.txt\n+++ b/base.txt\n'
                 f'@@ -1 +1 @@\n-{before}\n+{after}\n').encode()
        (self.patches / (name + '.patch')).write_bytes(patch)
        body = {'base_commit': self.commit, 'patch_file': name + '.patch', 'patch_sha256': sha(patch),
                'prerequisites': requires or {},
                'expected_base_files': {'base.txt': {'sha256': sha((before + '\n').encode())}},
                'expected_patched_files': {'base.txt': {'sha256': sha((after + '\n').encode()),
                                                      'bytes': len(after) + 1}}}
        self.save_layer(name, body)
        return body

    def save_layer(self, name, body):
        (self.patches / (name + '.json')).write_text(json.dumps(body))

    def prepare(self):
        return M['compose'](self.repo, self.donor, self.dest, seconds=10)

    def refuse(self, reason):
        with self.assertRaisesRegex(M['Refused'], '^' + reason + '$'):
            self.prepare()

    def test_complete_export_and_dependency_order_without_donor_changes(self):
        (self.donor / '.env').write_text('UNTRACKED_FIXTURE_DO_NOT_COPY=yes\n')
        before = self.git('status', '--porcelain=v1')
        result = self.prepare()
        self.assertEqual((self.dest / 'base.txt').read_text(), 'final\n')
        self.assertEqual((self.dest / 'untouched.txt').read_text(), 'preserve complete donor\n')
        self.assertFalse((self.dest / '.env').exists())
        self.assertFalse((self.dest / '.git').exists())
        self.assertEqual(result['source_file_count'], 2)
        self.assertEqual(result['layers'][0]['manifest'], 'patches/hermes/z-first.json')
        self.assertEqual(self.git('status', '--porcelain=v1'), before)
        self.assertEqual((self.donor / 'base.txt').read_text(), 'original\n')

    def test_existing_destination_never_adopted(self):
        self.dest.mkdir(); (self.dest / 'owner.txt').write_text('owner')
        self.refuse('fresh_destination_required')
        self.assertEqual((self.dest / 'owner.txt').read_text(), 'owner')

    def test_declared_crlf_checkout_exports_canonical_git_bytes(self):
        (self.donor / '.gitattributes').write_text('script.ps1 text eol=crlf\n')
        (self.donor / 'script.ps1').write_bytes(b'Write-Output fixture\r\n')
        self.git('add', '.gitattributes', 'script.ps1')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid', 'commit', '-qm', 'CRLF fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()
        self.lock['repositories'][0].update(commit=self.commit, tree=self.git('rev-parse', 'HEAD^{tree}').strip())
        self.save_lock()
        for name, body in (('z-first', self.first), ('a-second', self.second)):
            body['base_commit'] = self.commit
            self.save_layer(name, body)
        self.prepare()
        self.assertEqual((self.dest / 'script.ps1').read_bytes(), b'Write-Output fixture\n')
        self.assertEqual((self.donor / 'script.ps1').read_bytes(), b'Write-Output fixture\r\n')

    def test_unmanifested_layer_cannot_be_silently_omitted(self):
        (self.patches / 'forgotten.patch').write_text('unlisted')
        self.refuse('unmanifested_overlay'); self.assertFalse(self.dest.exists())

    def test_changed_patch_refused_before_export(self):
        (self.patches / 'z-first.patch').write_text('changed')
        self.refuse('overlay_hash_mismatch'); self.assertFalse(self.dest.exists())

    def test_missing_dependency_refused(self):
        self.second['prerequisites'] = {'missing.patch': '0' * 64}
        self.save_layer('a-second', self.second)
        self.refuse('overlay_prerequisite_mismatch')

    def test_manifest_reference_orders_its_owning_patch(self):
        (self.patches / 'z-first.json').rename(self.patches / 'legacy.json')
        self.second['prerequisites'] = {
            'patches/hermes/legacy.json': self.first['patch_sha256'],
        }
        self.save_layer('a-second', self.second)
        result = self.prepare()
        self.assertEqual([layer['manifest'] for layer in result['layers']],
                         ['patches/hermes/legacy.json', 'patches/hermes/a-second.json'])
        self.assertEqual((self.dest / 'base.txt').read_text(), 'final\n')

    def test_manifest_reference_must_pin_its_exact_owning_patch(self):
        patch_sha = self.first['patch_sha256']
        manifest_sha = sha((self.patches / 'z-first.json').read_bytes())
        for reference, pin in (
            ('missing.json', patch_sha),
            ('a-second.json', patch_sha),
            ('z-first.json', manifest_sha),
        ):
            with self.subTest(reference=reference):
                self.second['prerequisites'] = {'z-first.patch': patch_sha, reference: pin}
                self.save_layer('a-second', self.second)
                self.refuse('overlay_prerequisite_mismatch')
                self.assertFalse(self.dest.exists())

    def test_duplicate_patch_owner_refused_before_resolving_manifest_references(self):
        self.save_layer('alternate-owner', self.first)
        self.second['prerequisites'] = {'alternate-owner.json': self.first['patch_sha256']}
        self.save_layer('a-second', self.second)
        self.refuse('duplicate_overlay')
        self.assertFalse(self.dest.exists())

    def test_explicit_prerequisite_patch_field_requires_patch_path(self):
        self.second.update(prerequisite_patch='patches/hermes/z-first.json',
                           prerequisite_patch_sha256=self.first['patch_sha256'])
        self.save_layer('a-second', self.second)
        self.refuse('overlay_prerequisite_mismatch')
        self.assertFalse(self.dest.exists())

    def overlay_pins(self, *names):
        pins = {}
        for name in names:
            for suffix in ('.json', '.patch'):
                path = self.patches / (name + suffix)
                pins[str(path.relative_to(self.repo))] = sha(path.read_bytes())
        return pins

    def selection_cli(self, items):
        script = Path(__file__).resolve().parents[1] / 'scripts/hermes_prepare.py'
        argv = [sys.executable, '-B', str(script), '--repository', str(self.repo),
                '--donor', str(self.donor), '--destination', str(self.dest), '--seconds', '10']
        for name, digest in items:
            argv.extend(('--overlay-file', name, digest))
        return subprocess.run(argv, capture_output=True, text=True, timeout=12, check=False)

    def test_cli_selects_exact_pairs_leaving_inactive_sibling_intact(self):
        self.layer('inactive', 'changed', 'diverged', {'z-first.patch': self.first['patch_sha256']})
        self.refuse('overlay_input_changed')
        self.dest.rename(self.root / 'actual-default-partial')
        inactive = self.overlay_pins('inactive')
        selection = self.overlay_pins('z-first', 'a-second')
        result = self.selection_cli(selection.items())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / 'base.txt').read_text(), 'final\n')
        self.assertEqual(self.overlay_pins('inactive'), inactive)
        receipt = json.loads(self.dest.with_suffix('.source.json').read_text())
        self.assertEqual([row['manifest'] for row in receipt['layers']],
                         ['patches/hermes/z-first.json', 'patches/hermes/a-second.json'])

    def test_cli_refuses_changed_unpaired_duplicate_and_foreign_selection(self):
        valid = self.overlay_pins('z-first', 'a-second')
        manifest = 'patches/hermes/z-first.json'
        patch_name = 'patches/hermes/z-first.patch'
        cases = (
            (dict(valid, **{manifest: '0' * 64}).items(), 'overlay_selection_pair_changed'),
            (dict(valid, **{patch_name: '0' * 64}).items(), 'overlay_selection_pair_changed'),
            ([(name, pin) for name, pin in valid.items() if name != patch_name],
             'overlay_selection_pair_changed'),
            ([*valid.items(), (manifest, valid[manifest])], 'duplicate_overlay_selection'),
            ([*valid.items(), ('patches/hermes/unknown.patch', 'a' * 64)], 'unknown_overlay_selection'),
            ([*valid.items(), ('patches/hermes/../unknown.patch', 'a' * 64)], 'invalid_relative_path'),
        )
        for items, reason in cases:
            with self.subTest(reason=reason):
                result = self.selection_cli(items)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr, f'FRIDAY_SOURCE_REFUSED reason={reason}\n')
                self.assertFalse(self.dest.exists())
                self.assertFalse(self.dest.with_suffix('.source.json').exists())

    def test_cli_selection_cannot_omit_manifest_referenced_dependency(self):
        self.second['prerequisites'] = {'z-first.json': self.first['patch_sha256']}
        self.save_layer('a-second', self.second)
        result = self.selection_cli(self.overlay_pins('a-second').items())
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, 'FRIDAY_SOURCE_REFUSED reason=selected_overlay_dependency_missing\n')
        self.assertFalse(self.dest.exists())

    def test_explicit_empty_selection_cannot_mean_default(self):
        with self.assertRaisesRegex(M['Refused'], '^empty_overlay_selection$'):
            M['compose'](self.repo, self.donor, self.dest, seconds=10, overlay_pins={})
        self.assertFalse(self.dest.exists())

    def test_declared_absence_refuses_occupied_donor_path(self):
        self.first['expected_base_files']['base.txt'] = None
        self.save_layer('z-first', self.first)
        self.refuse('overlay_input_already_exists')
        self.assertEqual((self.dest / 'base.txt').read_text(), 'original\n')

    def test_dependency_cycle_refused(self):
        self.first['prerequisites'] = {'a-second.patch': self.second['patch_sha256']}
        self.save_layer('z-first', self.first)
        self.refuse('overlay_dependency_cycle')

    def test_unlisted_patch_target_refused(self):
        self.first['expected_patched_files']['extra.txt'] = {'sha256': '0' * 64, 'bytes': 0}
        self.save_layer('z-first', self.first)
        self.refuse('overlay_file_inventory_mismatch')

    def test_wrong_output_digest_cannot_produce_receipt(self):
        self.second['expected_patched_files']['base.txt']['sha256'] = '0' * 64
        self.save_layer('a-second', self.second)
        self.refuse('overlay_output_mismatch')
        self.assertTrue(self.dest.exists())  # retained partial output, never reused

    def test_wrong_before_digest_refused(self):
        self.first['expected_base_files']['base.txt']['sha256'] = '0' * 64
        self.save_layer('z-first', self.first)
        self.refuse('overlay_input_changed')
        self.assertEqual((self.dest / 'base.txt').read_text(), 'original\n')

    def test_dirty_owner_source_is_preserved_and_refused(self):
        (self.donor / 'base.txt').write_text('owner change\n')
        self.refuse('donor_blob_changed')
        self.assertEqual((self.donor / 'base.txt').read_text(), 'owner change\n')
        self.assertFalse(self.dest.exists())

    def test_repository_clean_filter_is_never_executed(self):
        marker = self.root / 'filter-executed'
        command = self.root / 'clean-filter.sh'
        command.write_text('#!/bin/sh\nprintf executed > ' + shlex.quote(str(marker)) + '\ncat\n')
        command.chmod(0o700)
        (self.donor / '.git/info/attributes').write_text('base.txt filter=fixture\n')
        self.git('config', 'filter.fixture.clean', shlex.quote(str(command)))
        target = self.donor / 'base.txt'
        changed = target.stat().st_mtime_ns + 10_000_000_000
        os.utime(target, ns=(changed, changed))
        result = self.prepare()
        self.assertEqual(result['status'], 'SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED')
        self.assertFalse(marker.exists())

    def test_staged_donor_change_refused_without_export(self):
        (self.donor / 'untouched.txt').write_text('owner staged edit\n')
        self.git('add', 'untouched.txt')
        self.refuse('dirty_donor_refused')
        self.assertFalse(self.dest.exists())
        self.assertEqual((self.donor / 'untouched.txt').read_text(), 'owner staged edit\n')

    def test_final_read_expiry_cannot_return_success(self):
        budget = M['preparation_budget'](10)
        namespace = M['_compose'].__globals__
        original = namespace['regular']
        def last_read(path):
            result = original(path)
            if path == self.dest / 'untouched.txt':
                budget.deadline = time.monotonic() - 1
            return result
        with patch.dict(namespace, regular=last_read):
            with self.assertRaisesRegex(M['Refused'], 'source_preparation_deadline'):
                M['_compose'](self.repo, self.donor, self.dest, budget)

    def test_receipt_serialization_keeps_original_deadline(self):
        budget = M['preparation_budget'](10)
        namespace = M['main'].__globals__
        dumps = json.dumps
        def slow_serialization(*args, **kwargs):
            result = dumps(*args, **kwargs)
            budget.deadline = time.monotonic() - 1
            return result
        argv = ['hermes_prepare', '--repository', str(self.repo), '--donor', str(self.donor),
                '--destination', str(self.dest)]
        with patch.dict(namespace, preparation_budget=lambda _: budget):
            with patch.object(sys, 'argv', argv), patch.object(json, 'dumps', slow_serialization):
                with self.assertRaisesRegex(M['Refused'], 'source_preparation_deadline'):
                    M['main']()
        self.assertFalse(self.dest.with_name(self.dest.name + '.source.json').exists())

    def test_success_serialization_expiry_cannot_print_success(self):
        budget = M['preparation_budget'](10)
        namespace = M['main'].__globals__
        dumps = json.dumps
        def slow_success(*args, **kwargs):
            result = dumps(*args, **kwargs)
            if isinstance(args[0], dict) and 'receipt' in args[0]:
                budget.deadline = time.monotonic() - 1
            return result
        argv = ['hermes_prepare', '--repository', str(self.repo), '--donor', str(self.donor),
                '--destination', str(self.dest)]
        with patch.dict(namespace, preparation_budget=lambda _: budget):
            with patch.object(sys, 'argv', argv), patch.object(json, 'dumps', slow_success):
                with patch('builtins.print') as output:
                    with self.assertRaisesRegex(M['Refused'], 'source_preparation_deadline'):
                        M['main']()
                    output.assert_not_called()

    def test_symlinked_donor_input_refused(self):
        alias = self.root / 'alias'; alias.symlink_to(self.donor, target_is_directory=True)
        with self.assertRaisesRegex(M['Refused'], 'canonical_donor_required'):
            M['compose'](self.repo, alias, self.dest)

    def test_duplicate_manifest_keys_refused(self):
        (self.patches / 'z-first.json').write_text('{"base_commit":"x","base_commit":"y"}')
        self.refuse('duplicate_json_key')

    def test_path_and_original_deadline_controls(self):
        for path in ('../escape', '.git/config', '/outside', '.', 'a//b', 'a/../b'):
            with self.subTest(path=path), self.assertRaises(M['Refused']): M['relative'](path)
        with self.assertRaisesRegex(M['Refused'], 'source_preparation_deadline'):
            M['Budget'](time.monotonic() - 1).remaining()


if __name__ == '__main__':
    unittest.main()
