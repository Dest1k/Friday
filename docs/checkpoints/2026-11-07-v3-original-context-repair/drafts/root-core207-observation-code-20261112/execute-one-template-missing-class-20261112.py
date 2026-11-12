"""Root's one missing read-only metadata observation; no old18 replay or stores."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import stat
import sys
import time
import uuid

os.umask(0o077)
sys.dont_write_bytecode = True
B = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
T = Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112')
C = T / 'candidate'
P = C / 'root-proofs'
ROOT = B / 'F06-ONE-TEMPLATE-MISSING-CLASS-ROOT-20261112'
OLD = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TEMPLATES-OFFICE-SOURCE-PREPARE-20261112/candidate')
SOURCE_SHA = 'e3312f519505368666008ab264459ef2ccc90471a18addebf07cbbac98db8c76'

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_bytes())

def now():
    return datetime.datetime.now().astimezone().isoformat()

def save(p, value):
    p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def source():
    assert digest(C / 'SOURCE-PINS.json') == SOURCE_SHA
    assert digest(T / 'SOURCE-FREEZE-FINAL.json') == 'dc7eaf4385616ec5d4a6bd6b13e97a5795e34ccfbdc254943a1621b694db14b1'
    for row in load(T / 'SOURCE-FREEZE-FINAL.json')['files']:
        assert digest(row['path']) == row['sha256']
        assert Path(row['path']).stat().st_size == row['bytes']
    spec = importlib.util.spec_from_file_location('f06_contract', C / 'f06_contract.py')
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    c.recipe_check()
    return c

def full(c, p):
    return c.stable(p)[1]

def prepare(c):
    # Credential metadata/digest come from the already admitted old18 custody;
    # this preparation never opens that secret body.
    assert digest(OLD / 'operations/verify-native-edits-templates-r1/inputs/STAGED.json') == 'd0e5d001f50aed7300d19bdcef15ab08e3a8d19bb16bd5a04f9fd1542c24bcd3'
    old = load(OLD / 'TEMPLATE-MANIFEST.json')
    selected = next(row for row in old['fixtures'] if row['fixture_id'] == c.SELECTED_ID)
    wanted = set(load(C / 'ROOT-PROOFS.TEMPLATE.json')['selected_manifest']['fixtures'][0])
    row = {k: selected[k] for k in wanted}
    credential = load(OLD / 'operations/verify-native-edits-templates-r1/inputs/STAGED.json')['credential_source']
    c.credential_metadata(credential)
    assert full(c, row['path']) == {k: row[k] for k in ('path', 'bytes', 'sha256', 'identity')}
    selected_manifest = dict(schema='friday.f06.one-template-selected.v1',
        state='ROOT_BOUND_RETAINED_METADATA_NOT_EXECUTION_AUTHORITY', assignment=c.ASSIGNMENT,
        selected_count=1, selected_fixture_ids=[c.SELECTED_ID], expected_Office_stores=0,
        expected_Office_password_probes=1, whole_F06_accepted=False, as_template=False,
        credential=credential, fixtures=[row])
    c.manifest_contract(selected_manifest)
    save(P / 'SELECTED-MANIFEST.json', selected_manifest)
    old_review = B / 'SOL-TASK25-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json'
    assert digest(old_review) == '8c292c1da41049331caef6f69f83fa4e9514daf3201c44536fb6423007e2cdd1'
    review = dict(state='ROOT_ACCEPTED_ONE_TEMPLATE_DIAGNOSTIC_SOURCE', execution_authority=False,
        source_pins_sha256=SOURCE_SHA, task24_freeze_sha256=c.TASK24_FREEZE_SHA,
        findings_remaining=[], retained_Root_acceptance=full(c, old_review),
        source_freeze=full(c, T / 'SOURCE-FREEZE-FINAL.json'),
        actual_loads=0, scope='One missing class-only correct readonlyOTT/getRequest; no original18 replay')
    save(P / 'SOURCE-REVIEW.json', review)
    save(ROOT / 'PREPARATION.json', dict(at_moscow=now(), state='ROOT_PREPARED_METADATA_ONLY_NO_RUNTIME_GRANT',
        selected_manifest=full(c, P / 'SELECTED-MANIFEST.json'), source_review=full(c, P / 'SOURCE-REVIEW.json'),
        original18_closure=full(c, c.ORIGINAL18_PATH), credential_body_opened=False,
        source_pins_sha256=SOURCE_SHA, operation_clock_started=False))
    print(json.dumps(dict(state='ROOT_PREPARED_METADATA_ONLY_NO_RUNTIME_GRANT', ref=str(ROOT / 'PREPARATION.json'))))

def execute(c):
    assert not (P / 'ROOT-BINDINGS.json').exists(), 'No overwrite/retry of existing bindings'
    pre = load(ROOT / 'PREPARATION.json')
    assert full(c, P / 'SELECTED-MANIFEST.json') == pre['selected_manifest']
    assert full(c, P / 'SOURCE-REVIEW.json') == pre['source_review']
    old = load(c.ORIGINAL18_PATH)
    assert old['execution_closed'] and old['parent_absent_or_different_birth'] and old['original_and_staged_full_custody_verified']
    # Refuse conflict; never terminate someone else's Office process.
    conflicts = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal():
            continue
        try:
            if proc.stat().st_uid == os.getuid() and (proc / 'comm').read_text().strip() in ('soffice.bin', 'oosplash', 'python.bin'):
                conflicts.append(int(proc.name))
        except (FileNotFoundError, ProcessLookupError):
            pass
    assert not conflicts, 'Existing Office actor requires resource reconciliation'
    # Original finite future clock begins here; never resets or borrows old clocks.
    origin = time.monotonic()
    c.DEADLINE = origin + c.LIMITS['whole_wall_seconds']
    bank = c.bank_snapshot()
    assert digest(c.ORIGINAL18_PATH) == c.ORIGINAL18_SHA
    selected = load(P / 'SELECTED-MANIFEST.json')
    row = selected['fixtures'][0]
    assert full(c, row['path']) == {k: row[k] for k in ('path', 'bytes', 'sha256', 'identity')}
    c.credential_metadata(selected['credential'])
    slotfd = os.open(c.SLOT, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(slotfd)
        assert stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1 and stat.S_IMODE(s.st_mode) == 0o600 and s.st_size == 0
        fcntl.flock(slotfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        slot_identity = c.identity(s)
    finally:
        os.close(slotfd)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    nonce = uuid.uuid4().hex
    cpus = sorted(os.sched_getaffinity(0))
    assert len(cpus) >= 4
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    original18 = full(c, c.ORIGINAL18_PATH)
    fresh = dict(state='ROOT_FRESH_ONE_TEMPLATE_KERNEL_CUSTODY', boot_id=boot, uid=os.getuid(), nonce=nonce,
        slot_identity=slot_identity, original_operation_start_monotonic=origin, observed_at_moscow=now(),
        bank=bank, affinity_cpu_ids=cpus, memory_available_kib=int(mem['MemAvailable'].split()[0]),
        CPU_pressure_raw=Path('/proc/pressure/cpu').read_text(), IO_pressure_raw=Path('/proc/pressure/io').read_text(),
        prior_operation_closed=True, shared_slot_free_observed=True, original18_closure=original18,
        selected_ciphertext={k: row[k] for k in ('path', 'bytes', 'sha256', 'identity')},
        credential_metadata=selected['credential'], current_office_conflicts=conflicts)
    save(P / 'FRESH-BOUNDARY.json', fresh)
    key = 'one-template-diag-class1'
    authority = dict(state='ROOT_GRANTED_ONE_MISSING_CONVERSION_OBSERVATION', operation_key=key,
        source_pins_sha256=SOURCE_SHA, selected_manifest=pre['selected_manifest'], source_review=pre['source_review'],
        original18_closure=original18, fresh_boundary=full(c, P / 'FRESH-BOUNDARY.json'),
        original18_replayed=False, original_strict_all_pass=False, whole_F06_accepted=False,
        max_document_loads=1, max_getRequest_calls=1, stores=0, correct_password_only=True,
        limits=c.LIMITS, boot_id=boot, nonce=nonce, original_operation_start_monotonic=origin,
        actual_Root_basis='Missing callback type never observed in old18; accepted finite diagnostic source now observes exactly that metadata window, no old18/model/native/producer/send/store replay.')
    save(P / 'RUNTIME-AUTHORITY.json', authority)
    bindings = dict(schema='friday.f06.one-template-root-bindings.v1', state='ROOT_BOUND_NO_EFFECT_YET',
        assignment=c.ASSIGNMENT, operation_key=key, nonce=nonce, uid=os.getuid(), boot_id=boot,
        source_pins_sha256=SOURCE_SHA, limits=c.LIMITS, original_operation_start_monotonic=origin,
        actual_two_cpu_ids=cpus[-2:], slot_path=str(c.SLOT), slot_identity=slot_identity,
        source_review=pre['source_review'], runtime_authority=full(c, P / 'RUNTIME-AUTHORITY.json'),
        fresh_boundary=full(c, P / 'FRESH-BOUNDARY.json'), original18_closure=original18,
        output_manifest=pre['selected_manifest'], credential_source=selected['credential'], task_retention_root=str(T))
    save(P / 'ROOT-BINDINGS.json', bindings)
    save(ROOT / 'ROOT-DISPATCH-INTENT.json', dict(state='ROOT_ONE_NEW_MISSING_METADATA_OBSERVATION',
        at_moscow=now(), root_pid=os.getpid(), original_operation_start_monotonic=origin,
        bindings=full(c, P / 'ROOT-BINDINGS.json'), source_pins_sha256=SOURCE_SHA,
        original18_replayed=False, old_clocks_reset=False, no_model_nativeedit_producer_send_or_store=True))
    os.execv('/usr/bin/python3', ['/usr/bin/python3', '-I', '-B', '-S', str(C / 'root_entry.py'),
        '--root-reviewed-bind-admit-and-exec', '--source-pins-sha256', SOURCE_SHA,
        '--bindings', str(P / 'ROOT-BINDINGS.json'), '--bindings-sha256', digest(P / 'ROOT-BINDINGS.json')])

if __name__ == '__main__':
    c = source()
    if sys.argv[1:] == ['--prepare-only']:
        prepare(c)
    elif sys.argv[1:] == ['--execute-one-new-missing-class-observation']:
        execute(c)
    else:
        raise SystemExit('Exact Root preparation or execution flag required')
