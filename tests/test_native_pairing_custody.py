"""Own-layout controls with the actual Source198 readonly reader, never a fallback.

Only disposable fixture paths are written. Foreign-uid coverage injects a stat
observation because this unprivileged process cannot chown a file to another uid.
Foreign-gid coverage uses the actual permitted supplementary group on disk.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

import test_admin_foundation  # Native test package registration, as in existing source controls.
from friday_admin_controls import stopped_operator as stopped
from friday_admin_controls.worker_archive import _Directory
from scripts import friday_ordinary_install as ordinary
from scripts.install_containment import Budget
from gateway import pairing
import hermes_constants


REFUSED = (ValueError, PermissionError, RuntimeError, OSError)
BINDING = {'platform': 'telegram', 'user_id': 'fixture-user'}


def snapshot(root):
    result = {}
    for path in [root, *sorted(root.rglob('*'))]:
        info = path.lstat()
        row = [info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns]
        if stat.S_ISREG(info.st_mode):
            row.append(hashlib.sha256(path.read_bytes()).hexdigest())
        if stat.S_ISLNK(info.st_mode):
            row.append(os.readlink(path))
        result[str(path.relative_to(root))] = row
    return result


@pytest.fixture
def layout(tmp_path, monkeypatch):
    home = tmp_path / 'H'; home.mkdir(mode=0o700)
    platforms = home / 'platforms'; platforms.mkdir(mode=0o700); platforms.chmod(0o775)
    active = platforms / 'pairing'; active.mkdir(mode=0o700); active.chmod(0o775)
    for name, data in {
        'telegram-approved.json': {'fixture-user': {'user_name': 'OWN_FIXTURE', 'approved_at': 1}},
        'telegram-pending.json': {}, '_rate_limits.json': {}, '_rate_limits.json.lock': None,
    }.items():
        path = active / name
        path.write_bytes(b'' if data is None else (json.dumps(data) + '\n').encode())
        path.chmod(0o600)
    monkeypatch.setenv('HERMES_HOME', str(home))
    monkeypatch.setattr(hermes_constants, '_PINNED_PROCESS_HERMES_HOME', str(home))
    monkeypatch.setattr(pairing, 'PAIRING_DIR', None)
    token = hermes_constants.set_hermes_home_override(str(home))
    operator = stopped.StoppedOperator({}, Budget(90))
    operator.home = home; operator.ordinary = ordinary
    try:
        yield SimpleNamespace(home=home, platforms=platforms, active=active, operator=operator)
    finally:
        hermes_constants.reset_hermes_home_override(token)


def read_with_custody(layout):
    with layout.operator._pairing_custody(BINDING):
        return pairing.PairingStore.is_approved_storage_readonly('telegram', 'fixture-user')


def test_actual_0775_layout_uses_native_static_reader_and_anchored_inventory_without_writes(layout, monkeypatch):
    before = snapshot(layout.home)
    def forbidden(*args, **kwargs):
        pytest.fail('observer called a constructor, migration, or mkdir')
    original = ordinary.update_file_state
    descriptors = []
    def anchored(path, parent_fd=None):
        assert parent_fd is not None
        assert os.fstat(parent_fd).st_ino == layout.active.stat().st_ino
        descriptors.append(parent_fd)
        return original(path, parent_fd=parent_fd)
    with monkeypatch.context() as boundary:
        boundary.setattr(pairing.PairingStore, '__init__', forbidden)
        boundary.setattr(pairing, '_migrate_split_pairing_dirs', forbidden)
        boundary.setattr(Path, 'mkdir', forbidden)
        boundary.setattr(ordinary, 'update_file_state', anchored)
        assert read_with_custody(layout)
        with layout.operator._pairing_custody(BINDING):
            assert not pairing.PairingStore.is_approved_storage_readonly('telegram', 'unapproved')
    assert len(descriptors) == 16
    assert snapshot(layout.home) == before
    root_identity, children, ancestors = layout.operator._pairing_state[1]
    assert root_identity[:4] == (layout.home.stat().st_dev, layout.home.stat().st_ino,
        os.getuid(), os.getgid())
    assert [row[0] for row in children] == ['platforms', 'pairing']
    assert ancestors[-1] == ('H', root_identity)
    with pytest.raises(REFUSED):
        with _Directory(layout.active):
            pytest.fail('generic archive guard was relaxed')


@pytest.mark.parametrize('mode', [0o755, 0o770, 0o775, 0o702])
def test_exposed_root_is_refused_without_writes(layout, mode):
    layout.home.chmod(mode); before = snapshot(layout.home)
    with pytest.raises(REFUSED): read_with_custody(layout)
    with pytest.raises(REFUSED): pairing.PairingStore.is_approved_storage_readonly('telegram', 'fixture-user')
    assert snapshot(layout.home) == before


@pytest.mark.parametrize('member', ['platforms', 'active'])
@pytest.mark.parametrize('mode', [0o777, 0o702, 0o4775, 0o2775, 0o1775])
def test_worldwrite_or_special_child_bits_are_refused(layout, member, mode):
    getattr(layout, member).chmod(mode); before = snapshot(layout.home)
    with pytest.raises(REFUSED): read_with_custody(layout)
    with pytest.raises(REFUSED): pairing.PairingStore.is_approved_storage_readonly('telegram', 'fixture-user')
    assert snapshot(layout.home) == before


def test_actual_foreign_group_child_is_refused(layout):
    groups = [group for group in os.getgroups() if group != os.getgid()]
    assert groups, 'requires an existing supplementary group, never root'
    os.chown(layout.active, -1, groups[0])
    before = snapshot(layout.home)
    with pytest.raises(REFUSED): read_with_custody(layout)
    with pytest.raises(REFUSED): pairing.PairingStore.is_approved_storage_readonly('telegram', 'fixture-user')
    assert snapshot(layout.home) == before


def test_foreign_uid_stat_observation_is_refused(layout, monkeypatch):
    original = os.fstat; target = layout.active.stat().st_ino
    def observed(fd):
        info = original(fd)
        if info.st_ino == target:
            fields = list(info); fields[4] = os.getuid() + 1
            return os.stat_result(fields)
        return info
    with monkeypatch.context() as boundary:
        boundary.setattr(os, 'fstat', observed)
        with pytest.raises(REFUSED): read_with_custody(layout)


@pytest.mark.parametrize('member', ['platforms', 'active'])
def test_symlink_directory_is_refused(layout, member):
    path = getattr(layout, member); retained = path.with_name(path.name + '-retained')
    path.rename(retained); path.symlink_to(retained, target_is_directory=True)
    before = snapshot(layout.home)
    with pytest.raises(REFUSED): read_with_custody(layout)
    with pytest.raises(REFUSED): pairing.PairingStore.is_approved_storage_readonly('telegram', 'fixture-user')
    assert snapshot(layout.home) == before


@pytest.mark.parametrize('damage', ['symlink', 'hardlink', 'mode0400', 'mode0644', 'corrupt'])
def test_native_approval_file_safety_is_preserved(layout, damage):
    path = layout.active / 'telegram-approved.json'
    if damage == 'symlink':
        target = layout.home / 'own-approval'; path.rename(target); path.symlink_to(target)
    elif damage == 'hardlink': os.link(path, layout.home / 'own-hardlink')
    elif damage.startswith('mode'): path.chmod(int(damage[4:], 8))
    else: path.write_text('CORRUPT OWN FIXTURE')
    before = snapshot(layout.home)
    with pytest.raises(REFUSED): read_with_custody(layout)
    assert snapshot(layout.home) == before


@pytest.mark.parametrize('member', ['home', 'platforms', 'active'])
def test_directory_rename_away_and_restore_aba_is_refused(layout, member):
    path = getattr(layout, member)
    before_inode = path.stat().st_ino
    with pytest.raises(REFUSED):
        with layout.operator._pairing_custody(BINDING):
            assert pairing.PairingStore.is_approved_storage_readonly('telegram', 'fixture-user')
            retained = path.with_name(path.name + '-away')
            path.rename(retained); retained.rename(path)
            assert path.stat().st_ino == before_inode


def test_persistent_custody_rejects_replaced_ancestor_even_with_same_active_inode(layout):
    assert read_with_custody(layout)
    held = layout.platforms.with_name('held-platforms')
    layout.platforms.rename(held); layout.platforms.mkdir(mode=0o700); layout.platforms.chmod(0o775)
    (held / 'pairing').rename(layout.active)
    with pytest.raises(REFUSED): read_with_custody(layout)


def test_unrelated_completed_root_publication_does_not_poison_persistent_identity(layout):
    assert read_with_custody(layout)
    (layout.home / 'unrelated-publication').write_bytes(b'fixture completed outside custody')
    assert read_with_custody(layout)


def test_present_empty_alternate_directory_is_still_refused(layout):
    (layout.home / 'pairing').mkdir(mode=0o700)
    before = snapshot(layout.home)
    with pytest.raises(REFUSED): read_with_custody(layout)
    assert snapshot(layout.home) == before


def test_inventory_cannot_follow_a_replaced_active_path(layout, monkeypatch):
    original = ordinary.update_file_state; observed = []
    def redirect(path, parent_fd=None):
        if not observed:
            retained = layout.active.with_name('held-pairing')
            layout.active.rename(retained); layout.active.mkdir(mode=0o700)
            for member in retained.iterdir():
                (layout.active / member.name).write_bytes(b'PATH REDIRECTION CANARY')
                (layout.active / member.name).chmod(0o600)
        state = original(path, parent_fd=parent_fd)
        assert b'PATH REDIRECTION CANARY' not in state['data']
        observed.append(state)
        return state
    monkeypatch.setattr(ordinary, 'update_file_state', redirect)
    with pytest.raises(REFUSED): read_with_custody(layout)
    assert observed
