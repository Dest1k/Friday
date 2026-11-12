"""Connect reviewed source five, materialize finite495 source; no installation."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import stat
import subprocess

R = Path('/home/jericho/jericho/Friday_rework')
W = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112')
B = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
D = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112')
H = R / '.runtime/friday-normal-both-workers-frw032'
os.umask(0o077)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_bytes())

def ref(p):
    return dict(path=str(p), sha256=sha(p))

def main():
    review = B / 'F06-MODERN207-FINAL-EXECUTION-ROOT-ACCEPTANCE-20261112.json'
    assert sha(review) == 'c73c762908b563efafd6f49c7652f3f7ef0f2be2cb9f89964eb6763c0bc23c33'
    assert load(review)['state'] == 'ROOT_ACCEPTED_EXACT_SOURCE_AND_ALL_FOUR_SYNTHETIC_EXECUTIONS_NOT_LIVE_GRANT'
    oldproof = load(B / 'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json')
    for pin in oldproof['installed']['canonical4'].values():
        assert ref(pin['path']) == pin
    oldinput = load(oldproof['installed']['canonical4']['current_input']['path'])
    proposed = W / 'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json'
    assert sha(proposed) == 'c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'
    newinput = load(proposed)
    assert {k:v for k,v in oldinput.items() if k != 'project_files'} == {k:v for k,v in newinput.items() if k != 'project_files'}
    assert len(oldinput['project_files']) == 493 and len(newinput['project_files']) == 495
    assert set(newinput['project_files']) - set(oldinput['project_files']) == {
        'patches/hermes/f06-modern-odt-authenticated-profile-after-source206-manifest.json',
        'patches/hermes/f06-modern-odt-authenticated-profile-after-source206.patch'}
    assert [k for k,v in oldinput['project_files'].items() if newinput['project_files'][k] != v] == ['scripts/friday_ordinary_install.py']
    origins = load(W / 'PROJECT495-ORIGINS.json')['rows']
    public = load(W / 'PUBLIC495-ORIGINS.json')['rows']
    assert set(origins) == set(public) == set(newinput['project_files'])
    for name, pin in origins.items():
        p = Path(pin['path'])
        assert Path(name).is_absolute() is False and '..' not in Path(name).parts
        assert p.resolve(strict=True) == p and p.is_file() and p.stat().st_uid == os.getuid() and p.stat().st_nlink == 1
        assert sha(p) == pin['sha256'] == newinput['project_files'][name]
    for name, digest in oldinput['project_files'].items():
        p = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112/project493') / name
        assert sha(p) == digest
    assert sha(H / 'hermes-agent/tools/scoped_odf_password.py') == 'ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae'
    changes = [
        'scripts/friday_ordinary_install.py',
        'docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py',
        'docs/checkpoints/2026-11-07-v3-original-context-repair/build-layer-publication-request.py',
        'patches/hermes/f06-modern-odt-authenticated-profile-after-source206-manifest.json',
        'patches/hermes/f06-modern-odt-authenticated-profile-after-source206.patch',
    ]
    patch = W / 'PUBLIC-INTEGRATION.patch'
    assert sha(patch) == 'ecf0383c310c09dfbb0120f69e4e4329959d7bb17934827809e4831e42b848f0'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '68e0ecf0b23d4fdb97e3234a06aadd6f98f05c15'
    assert subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R) == b''
    for name in changes[:3]:
        assert subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=R) == (R/name).read_bytes()
    for name in changes[3:]:
        assert not (R/name).exists()
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=R, check=True)
    # Reversible source-only integration; accepted public bytes, no H writes.
    subprocess.run(['git', 'apply', str(patch)], cwd=R, check=True)
    for name, pin in public.items():
        assert sha(R/name) == pin['sha256']
    cp = R / 'docs/checkpoints/2026-11-07-v3-original-context-repair'
    assert sha(cp/'friday_v3_layer_publication.py') == sha(W/'publication/friday_v3_layer_publication.py')
    assert sha(cp/'build-layer-publication-request.py') == sha(W/'publication/build-layer-publication-request.py')
    counterparts = sorted(name for name in origins if origins[name]['sha256'] != public[name]['sha256'])
    assert counterparts == load(W/'COUNTERPART-INVARIANTS.json')['private_difference_names'] and len(counterparts) == 28
    D.mkdir(mode=0o700)
    project = D / 'project495'
    project.mkdir(mode=0o700)
    total = 0
    for name, pin in origins.items():
        target = project/name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        src = Path(pin['path'])
        shutil.copyfile(src, target)
        os.chmod(target, stat.S_IMODE(src.stat().st_mode))
        assert sha(target) == pin['sha256'] and target.stat().st_nlink == 1
        assert (target.stat().st_dev, target.stat().st_ino) != (src.stat().st_dev, src.stat().st_ino)
        total += target.stat().st_size
    files = {str(p.relative_to(project)) for p in project.rglob('*') if p.is_file()}
    assert files == set(origins) and total < 64*1024**2
    shutil.copyfile(proposed, D/'INPUT-SOURCE207.json')
    assert sha(D/'INPUT-SOURCE207.json') == sha(proposed)
    for pin in oldproof['installed']['canonical4'].values():
        assert ref(pin['path']) == pin
    proof = dict(schema='friday.root.future207.project-source.v1',
        state='ROOT_MATERIALIZED_PRIVATE495_PUBLIC5_CONNECTED_NOT_INSTALLED_NOT_GRANTED',
        at_moscow=datetime.datetime.now().astimezone().isoformat(),
        installed206_canonical4_unchanged=True, native207_installed=False,
        main_source_baseline='68e0ecf0b23d4fdb97e3234a06aadd6f98f05c15', execution_commit='UNBOUND_CURRENT_COMMITTED_MAIN',
        private_project=str(project), project_files=495, project_bytes=total,
        current_input=ref(D/'INPUT-SOURCE207.json'), previous_input=oldproof['installed']['canonical4']['current_input'],
        all495_origin_hashes_verified=True, private_public28=counterparts,
        public_source_changes={name:ref(R/name) for name in changes},
        native_existing_preimage='ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae',
        native_candidate='b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d',
        independent_four_execution_acceptance=ref(review),
        runtime_grant=False, actual_request_or_UUID_or_admission_created=False)
    p = D/'ROOT-207-PROJECT-SOURCE.json'
    with p.open('x') as f:
        json.dump(proof,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write('\n')
    print(json.dumps(dict(state=proof['state'], proof=ref(p), project_bytes=total, project_files=495)))

if __name__ == '__main__':
    main()
