"""Inert Root caller: --prepare metadata; --execute-once one NEW post-args operation.

This source package creates no actual proof or clock. Root alone may invoke it.
No old18/class1 replay, regrade, grant, clock or admission is reused.
"""
from pathlib import Path
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import stat
import sys
import time
import uuid

os.umask(0o077)
sys.dont_write_bytecode = True
B = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
T = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112')
C = T / 'candidate'
P = C / 'root-proofs'
ROOT = Path('/home/jericho/.cache/FRW-ASTRA-PREPARE-POST-ARGS-ROOT-OFFICE-CALLER-20261112') / 'future-root-operation'
OLD = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TEMPLATES-OFFICE-SOURCE-PREPARE-20261112/candidate')
SOURCE_SHA = '89a003927b226f6d185af4954a34ead5c991bb74ccc88cccec6f6cbeed8d681f'
FREEZE_SHA = 'f3b0f3055ddfc0be08bcc90040aa8a090a409d2c0a99c99b35a3a9a821f4d070'
ACCEPT = B / 'F06-POST-ARGS-COMPAT-OFFICE-FRAME-ROOT-SOURCE-ACCEPTANCE-20261112.json'
ACCEPT_SHA = 'd0a2dd28bdd09e20861c664f623a37ccbc3bbe61b89db6ffc1fec08700a04a34'
PREVIOUS = T / 'reference-metadata/F06-ONE-TEMPLATE-MISSING-CLASS-OBSERVED-PARTIAL-CLOSED-20261112.json'
KEY = 'one-template-post-args-compat1'
PIN_KEYS = ('path', 'bytes', 'sha256', 'identity')

def require(value, code):
    if not value:
        raise ValueError(code)

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_bytes())

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()

def budget(origin):
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    require(time.monotonic() < origin + 300 - 15, 'WHOLE_OPERATION_WALL_WITH_CLEANUP')
    require(time.process_time() + child.ru_utime + child.ru_stime < 180, 'WHOLE_OPERATION_CPU')

def save(p, value):
    # Deterministic sorted JSON bytes; O_EXCL never overwrites a prior proof.
    p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode()
    require(len(raw) <= 4*1024**2, 'REPORT_LIMIT')
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def source(origin=None):
    # Authenticate the complete accepted frame before importing any candidate.
    require(digest(C / 'SOURCE-PINS.json') == SOURCE_SHA, 'SOURCE_PINS_CAS')
    require(digest(T / 'SOURCE-FREEZE.json') == FREEZE_SHA, 'SOURCE_FREEZE_CAS')
    freeze = load(T / 'SOURCE-FREEZE.json')
    require(len(freeze['files']) == 60, 'SOURCE_FREEZE_INVENTORY')
    for row in freeze['files']:
        path = Path(row['path'])
        require(path.is_relative_to(T) and path.resolve(strict=True) == path, 'FROZEN_LOCAL_PATH')
        require(digest(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'FROZEN_SOURCE_CAS')
        if origin is not None:
            budget(origin)
    require(digest(ACCEPT) == ACCEPT_SHA, 'RETAINED_ROOT_SOURCE_ACCEPTANCE_CAS')
    spec = importlib.util.spec_from_file_location('f06_contract', C / 'f06_contract.py')
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    c.recipe_check()
    require(c.OPERATION_KEY == KEY, 'ONLY_NEW_OPERATION_KEY')
    return c

def full(c, p):
    return c.stable(p)[1]

def history(c):
    original = load(c.ORIGINAL18_PATH)
    require(digest(c.ORIGINAL18_PATH) == c.ORIGINAL18_SHA, 'OLD18_CLOSURE_CAS')
    require(original['execution_closed'] is True and original['parent_absent_or_different_birth'] is True and original['original_and_staged_full_custody_verified'] is True, 'OLD18_CLOSED')
    require(digest(PREVIOUS) == c.PREVIOUS_CLASS1_SUMMARY_SHA, 'CLASS1_CLOSED_SUMMARY_CAS')
    previous = load(PREVIOUS)
    require(previous['state'] == 'ONE_DIAGNOSTIC_COMPLETED_NEW_OBSERVED_SETTER_FAILURE_PARTIAL_CLOSED' and previous['owned_actor_namespace_unit_and_parent_closed'] is True and previous['slot_free'] is True and previous['full_original_staged_bank_source_admission_CAS_after_closure'] is True, 'CLASS1_CLOSED')
    return full(c, c.ORIGINAL18_PATH)

def accepted_review(c):
    require(digest(ACCEPT) == ACCEPT_SHA, 'RETAINED_ROOT_SOURCE_ACCEPTANCE_CAS')
    review = load(ACCEPT)
    require(review['state'] == 'ROOT_ACCEPTED_POST_ARGS_COMPAT_ONE_TEMPLATE_SOURCE' and review['execution_authority'] is False and review['source_pins_sha256'] == SOURCE_SHA and review['task24_freeze_sha256'] == c.TASK24_FREEZE_SHA and review['task25_sourcefreeze_sha256'] == c.TASK25_FREEZE_SHA and review['task27_sourcefreeze_sha256'] == c.TASK27_FREEZE_SHA and review['previous_class1_summary_sha256'] == c.PREVIOUS_CLASS1_SUMMARY_SHA and review['postchange_purpose'] == c.POSTCHANGE_PURPOSE and review['findings_remaining'] == [], 'EXACT_ROOT_SOURCE_REVIEW')
    require(review['source_freeze']['sha256'] == FREEZE_SHA and review['source_freeze']['path'] == str(T / 'SOURCE-FREEZE.json'), 'ROOT_REVIEW_FREEZE_JOIN')
    return review  # Actual Root acceptance copied verbatim as data; never template booleans.

def prepare(c):
    # Future Root metadata work only: no secret body, runtime grant or clock.
    require(not P.exists() and not ROOT.exists(), 'NO_EXISTING_PREPARATION_REUSE')
    original18 = history(c)
    review = accepted_review(c)
    staged = OLD / 'operations/verify-native-edits-templates-r1/inputs/STAGED.json'
    require(digest(staged) == 'd0e5d001f50aed7300d19bdcef15ab08e3a8d19bb16bd5a04f9fd1542c24bcd3', 'RETAINED_CREDENTIAL_METADATA_CAS')
    old = load(OLD / 'TEMPLATE-MANIFEST.json')
    selected = next(row for row in old['fixtures'] if row['fixture_id'] == c.SELECTED_ID)
    wanted = list(load(C / 'ROOT-PROOFS.TEMPLATE.json')['selected_manifest']['fixtures'][0])
    row = {k: selected[k] for k in wanted}
    credential = load(staged)['credential_source']
    c.credential_metadata(credential)
    require(full(c, row['path']) == {k: row[k] for k in PIN_KEYS}, 'RETAINED_SELECTED_CIPHERTEXT_CAS')
    selected_manifest = dict(schema='friday.f06.one-template-selected.v1', state='ROOT_BOUND_RETAINED_METADATA_NOT_EXECUTION_AUTHORITY', assignment=c.ASSIGNMENT,
        selected_count=1, selected_fixture_ids=[c.SELECTED_ID], expected_Office_stores=0, expected_Office_password_probes=1, whole_F06_accepted=False, as_template=False,
        credential=credential, fixtures=[row])
    c.manifest_contract(selected_manifest)
    save(P / 'SELECTED-MANIFEST.json', selected_manifest)
    save(P / 'SOURCE-REVIEW.json', review)
    save(ROOT / 'PREPARATION.json', dict(at_moscow=now(), state='ROOT_PREPARED_POST_ARGS_METADATA_ONLY_NO_RUNTIME_GRANT',
        selected_manifest=full(c, P / 'SELECTED-MANIFEST.json'), source_review=full(c, P / 'SOURCE-REVIEW.json'), retained_Root_acceptance=full(c, ACCEPT),
        original18_closure=original18, previous_class1_summary_sha256=c.PREVIOUS_CLASS1_SUMMARY_SHA, postchange_purpose=c.POSTCHANGE_PURPOSE,
        source_pins_sha256=SOURCE_SHA, source_freeze_sha256=FREEZE_SHA, credential_body_opened=False, operation_clock_started=False))
    print(json.dumps(dict(state='ROOT_PREPARED_POST_ARGS_METADATA_ONLY_NO_RUNTIME_GRANT', ref=str(ROOT / 'PREPARATION.json'))))

def execute(c, origin):
    c.DEADLINE = origin + c.LIMITS['whole_wall_seconds']
    c.CPU_GUARD = lambda: budget(origin)
    budget(origin)
    # Any partial publication remains consumed/manual-reconciliation, never retry.
    for path in (P / 'ROOT-BINDINGS.json', P / 'FRESH-BOUNDARY.json', P / 'RUNTIME-AUTHORITY.json', ROOT / 'ROOT-DISPATCH-INTENT.json', C / (KEY + '.ADMISSION.json'), C / (KEY + '.ENTRY-INTENT.json'), c.operation(KEY, c.MODE)):
        require(not os.path.lexists(path), 'NEW_OPERATION_ALREADY_STARTED_NO_REPLAY')
    pre = load(ROOT / 'PREPARATION.json')
    require(pre['state'] == 'ROOT_PREPARED_POST_ARGS_METADATA_ONLY_NO_RUNTIME_GRANT' and pre['source_pins_sha256'] == SOURCE_SHA and pre['source_freeze_sha256'] == FREEZE_SHA and pre['operation_clock_started'] is False, 'PREPARATION_SOURCE_SCOPE')
    require(full(c, P / 'SELECTED-MANIFEST.json') == pre['selected_manifest'] and full(c, P / 'SOURCE-REVIEW.json') == pre['source_review'] and full(c, ACCEPT) == pre['retained_Root_acceptance'], 'PREPARATION_FULL_CAS')
    require(load(P / 'SOURCE-REVIEW.json') == accepted_review(c), 'COPIED_ACTUAL_ROOT_REVIEW')
    original18 = history(c)
    require(original18 == pre['original18_closure'] and pre['previous_class1_summary_sha256'] == c.PREVIOUS_CLASS1_SUMMARY_SHA and pre['postchange_purpose'] == c.POSTCHANGE_PURPOSE, 'PREPARATION_HISTORY_PURPOSE_JOIN')
    conflicts = []
    scan_end = min(origin + 120, time.monotonic() + 2)
    for count, proc in enumerate(Path('/proc').iterdir(), 1):
        require(count <= 65536 and time.monotonic() < scan_end, 'OFFICE_ACTOR_SCAN_BOUND')
        if not proc.name.isdecimal():
            continue
        try:
            if proc.stat().st_uid == os.getuid() and (proc / 'comm').read_text().strip() in ('soffice.bin', 'oosplash', 'python.bin'):
                conflicts.append(int(proc.name))
        except (FileNotFoundError, ProcessLookupError):
            pass
    require(not conflicts, 'EXISTING_OFFICE_ACTOR_REQUIRES_RECONCILIATION')
    bank = c.bank_snapshot()
    selected = load(P / 'SELECTED-MANIFEST.json')
    row = c.manifest_contract(selected)
    require(full(c, row['path']) == {k: row[k] for k in PIN_KEYS}, 'CURRENT_CIPHERTEXT_CAS')
    c.credential_metadata(selected['credential'])
    slotfd = os.open(c.SLOT, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(slotfd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1 and stat.S_IMODE(s.st_mode) == 0o600 and s.st_size == 0, 'SLOT_CUSTODY')
        fcntl.flock(slotfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        slot_identity = c.identity(s)
        require(slot_identity == c.identity(c.SLOT.lstat()), 'SLOT_CURRENT_CAS')
    finally:
        os.close(slotfd)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    nonce = uuid.uuid4().hex
    cpus = sorted(os.sched_getaffinity(0))
    require(len(cpus) >= 4, 'AVAILABLE_CPU_AFFINITY')
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    require(int(mem['MemAvailable'].split()[0]) >= 3*1024*1024, 'AVAILABLE_MEMORY')
    fresh = dict(state='ROOT_FRESH_POST_ARGS_COMPAT_ONE_TEMPLATE_KERNEL_CUSTODY', boot_id=boot, uid=os.getuid(), nonce=nonce,
        slot_identity=slot_identity, original_operation_start_monotonic=origin, observed_at_moscow=now(), bank=bank,
        affinity_cpu_ids=cpus, memory_available_kib=int(mem['MemAvailable'].split()[0]), CPU_pressure_raw=Path('/proc/pressure/cpu').read_text(), IO_pressure_raw=Path('/proc/pressure/io').read_text(),
        prior_operation_closed=True, shared_slot_free_observed=True, original18_closure=original18,
        selected_ciphertext={k: row[k] for k in PIN_KEYS}, credential_metadata=selected['credential'], current_office_conflicts=conflicts)
    budget(origin)
    save(P / 'FRESH-BOUNDARY.json', fresh)
    authority = dict(state='ROOT_GRANTED_ONE_POST_ARGS_COMPAT_QUALIFICATION', assignment=c.ASSIGNMENT, operation_key=KEY,
        source_pins_sha256=SOURCE_SHA, task27_sourcefreeze_sha256=c.TASK27_FREEZE_SHA, previous_class1_summary_sha256=c.PREVIOUS_CLASS1_SUMMARY_SHA, postchange_purpose=c.POSTCHANGE_PURPOSE,
        selected_manifest=pre['selected_manifest'], source_review=pre['source_review'], original18_closure=original18, fresh_boundary=full(c, P / 'FRESH-BOUNDARY.json'),
        original18_replayed=False, previous_class1_replayed=False, actual_normal_payload_type_before='UNKNOWN', original_strict_all_pass=False, whole_F06_accepted=False,
        max_document_loads=1, max_getRequest_calls=1, stores=0, correct_password_only=True, limits=c.LIMITS,
        boot_id=boot, nonce=nonce, original_operation_start_monotonic=origin,
        actual_Root_basis='One distinct missing post-args normal payload and supported readonly OTT load; closed class1/old18 unchanged, no replay or regrade.')
    save(P / 'RUNTIME-AUTHORITY.json', authority)
    bindings = dict(schema='friday.f06.one-template-post-args-root-bindings.v1', state='ROOT_BOUND_NO_EFFECT_YET', assignment=c.ASSIGNMENT, operation_key=KEY,
        nonce=nonce, uid=os.getuid(), boot_id=boot, source_pins_sha256=SOURCE_SHA, limits=c.LIMITS, original_operation_start_monotonic=origin,
        actual_two_cpu_ids=cpus[-2:], slot_path=str(c.SLOT), slot_identity=slot_identity, source_review=pre['source_review'], runtime_authority=full(c, P / 'RUNTIME-AUTHORITY.json'),
        fresh_boundary=full(c, P / 'FRESH-BOUNDARY.json'), original18_closure=original18, output_manifest=pre['selected_manifest'], credential_source=selected['credential'], task_retention_root=str(T))
    save(P / 'ROOT-BINDINGS.json', bindings)
    save(ROOT / 'ROOT-DISPATCH-INTENT.json', dict(state='ROOT_ONE_NEW_POST_ARGS_METADATA_OBSERVATION', at_moscow=now(), root_pid=os.getpid(), original_operation_start_monotonic=origin,
        bindings=full(c, P / 'ROOT-BINDINGS.json'), source_pins_sha256=SOURCE_SHA, original18_replayed=False, previous_class1_replayed=False, old_clocks_reset=False, no_model_nativeedit_producer_send_or_store=True))
    budget(origin)
    require(time.monotonic() - origin <= 120, 'ROOT_BOUNDARY_FRESH_BEFORE_ENTRY')
    require(digest(C / 'root_entry.py') == 'a054d39aa563359a6b1e3069d56f7f75c134caaf0d40861f5235752f860b0daa', 'EXACT_ENTRY_BEFORE_EXEC')
    os.execv('/usr/bin/python3', ['/usr/bin/python3', '-I', '-B', '-S', str(C / 'root_entry.py'), '--root-reviewed-bind-admit-and-exec', '--source-pins-sha256', SOURCE_SHA,
        '--bindings', str(P / 'ROOT-BINDINGS.json'), '--bindings-sha256', digest(P / 'ROOT-BINDINGS.json')])

if __name__ == '__main__':
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, 'ISOLATED_ROOT_FLAGS')
    require(sys.argv[1:] in (['--prepare'], ['--execute-once']), 'EXACT_ROOT_FLAG_REQUIRED')
    origin = time.monotonic() if sys.argv[1:] == ['--execute-once'] else None
    c = source(origin)
    if origin is None:
        prepare(c)
    else:
        execute(c, origin)
