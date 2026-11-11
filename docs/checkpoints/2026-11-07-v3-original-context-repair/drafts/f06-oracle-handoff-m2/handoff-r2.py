"""Dormant retained-ciphertext metadata adapter. No Office, credentials or staging copy."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

BASE = Path(__file__).resolve().parent
TASK = BASE.parent
ASSIGNMENT = 'ASTRA-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111#1'
HARNESS_SHA = 'ad02621e5d9c2b5760430fe1d5da0f0e324fcf5722ef7227bf337969b4a2bf93'
NATIVE_PINS_SHA = '53edc7bc3d76766fe3a6c22662d902d5aa78cba63c9c62f65901c0aa7974ea69'
QUALIFICATION_ROOT = TASK / 'native-harness/revision3/qualification'
FORMATS = ('docx', 'xlsx', 'pptx', 'odt', 'ods', 'odp', 'odt')
REF_KEYS = {'path', 'sha256', 'bytes', 'uid', 'gid', 'mode', 'dev', 'ino', 'nlink', 'mtime_ns', 'ctime_ns'}
INTENT_KEYS = ('assignment', 'operation_id', 'root_generation_operation_id',
               'harness_sha256', 'native_source_pins_sha256', 'limits', 'effect_scope',
               'root_generation_result', 'independent_input_oracle', 'credential',
               'credential_keys', 'fixtures')
HEX = re.compile(r'[0-9a-f]{64}')


class HandoffError(ValueError):
    """Fixed diagnostic code only; never serialize input/error/credential values."""


def need(ok, code):
    if not ok:
        raise HandoffError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(raw):
    p = Path(raw)
    need(type(raw) is str and str(p) == raw and p.is_absolute() and '..' not in p.parts
         and p.resolve(strict=True) == p, 'canonical_path')
    return p


def private_parents(p):
    for parent in (p.parent, *p.parent.parents):
        s = parent.lstat()
        need(stat.S_ISDIR(s.st_mode), 'parent_type')
        if parent == Path('/home/jericho/.cache'):
            return
        need(s.st_uid == os.getuid() and stat.S_IMODE(s.st_mode) == 0o700, 'parent_custody')
    raise HandoffError('private_cache_anchor_required')


def credential_metadata(ref):
    need(type(ref) is dict and {'path', 'sha256', 'bytes'} <= set(ref) <= REF_KEYS, 'credential_metadata_only')
    need(type(ref['path']) is str and type(ref['sha256']) is str and HEX.fullmatch(ref['sha256'])
         and type(ref['bytes']) is int and 0 < ref['bytes'] < 16384, 'credential_ref')
    # Metadata only: neither open(), read(), nor hash the credential file.
    p = canonical(ref['path']); private_parents(p); s = p.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1
         and stat.S_IMODE(s.st_mode) == 0o600 and s.st_size == ref['bytes'], 'credential_custody')
    actual = dict(uid=s.st_uid, gid=s.st_gid, dev=s.st_dev, ino=s.st_ino, mode='0600',
                  nlink=s.st_nlink, mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)
    need(all(k not in ref or ref[k] == value for k, value in actual.items()), 'credential_identity_cas')
    return dict(ref)


def read_ref(ref, forbidden=(), limit=2 * 1024**2):
    need(type(ref) is dict and {'path', 'sha256', 'bytes'} <= set(ref) <= REF_KEYS, 'reference_shape')
    need(type(ref['sha256']) is str and HEX.fullmatch(ref['sha256']) and type(ref['bytes']) is int, 'reference_digest')
    p = canonical(ref['path']); need(str(p) not in forbidden, 'credential_content_read_forbidden')
    # Every ancestor under the task/private proof root must be owned/private.
    private_parents(p)
    before = p.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
         and stat.S_IMODE(before.st_mode) == 0o600 and 0 <= before.st_size == ref['bytes'] <= limit, 'file_custody')
    fields = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode, s.st_nlink,
                        s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        held = os.fstat(f.fileno()); raw = f.read(limit + 1); after = os.fstat(f.fileno())
    need(fields(before) == fields(held) == fields(after) == fields(p.lstat()), 'file_identity_cas')
    need(len(raw) == ref['bytes'] and sha(raw) == ref['sha256'], 'file_hash_cas')
    actual = dict(path=str(p), bytes=len(raw), sha256=sha(raw), uid=held.st_uid, gid=held.st_gid,
                  mode='0600', dev=held.st_dev, ino=held.st_ino, nlink=held.st_nlink,
                  mtime_ns=held.st_mtime_ns, ctime_ns=held.st_ctime_ns)
    need(all(k not in ref or ref[k] == actual[k] for k in REF_KEYS), 'declared_custody_cas')
    return raw, actual


def decode(raw):
    def pairs(items):
        d = {}
        for key, value in items:
            need(key not in d, 'duplicate_json_key'); d[key] = value
        return d
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(HandoffError('json_constant')))


def edit_for(fmt):
    old, new = 'F06 SYNTHETIC ALPHA 11 NOV', 'F06 SYNTHETIC BRAVO 11 NOV'
    if fmt in ('docx', 'odt'):
        return {'old_text': old, 'new_text': new}
    if fmt in ('pptx', 'odp'):
        return {'slide': 1, 'role': 'slide', 'old_text': old, 'new_text': new}
    return {'sheet': 'F06Data', 'cell': 'B2', 'expected': 17 if fmt == 'xlsx' else '17',
            'value': 23 if fmt == 'xlsx' else '23'}


def exact_json(a, b):
    # JSON numeric/bool equality must not silently accept true as slide=1.
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def build(req):
    """Read exact non-secret refs/ciphertext; emit plan only, never execute Office."""
    need(req.get('schema') == 'friday.f06.output-handoff-request.v1'
         and req.get('state') == 'BOUND_METADATA_ONLY' and req.get('assignment') == ASSIGNMENT, 'unbound_request')
    cred = credential_metadata(req['credential']); forbidden = {cred['path']}
    proofs = {}
    def load(key, optional=False):
        ref = req.get(key)
        if optional and ref is None:
            return None
        raw, actual = read_ref(ref, forbidden); proofs[key] = actual
        return decode(raw)
    binding = load('native_binding'); grant = load('native_root_grant'); once = load('native_once')
    need(binding.get('schema') == 'friday.f06.native-binding.v2' and binding.get('assignment') == ASSIGNMENT
         and binding.get('root_authorized_native_run') is True, 'native_binding')
    need(binding.get('harness_sha256') == HARNESS_SHA and binding.get('native_source_pins_sha256') == NATIVE_PINS_SHA, 'native_source_origin')
    need(exact_json(binding.get('credential'), cred)
         and binding.get('credential_keys') == {'correct': 'password', 'wrong': 'wrong_password'}, 'credential_lineage')
    need(grant.get('schema') == 'friday.f06.root-native-grant.v2' and grant.get('assignment') == ASSIGNMENT
         and grant.get('native_qualification_authorized') is True
         and grant.get('manifest_sha256') == proofs['native_binding']['sha256']
         and exact_json(grant.get('intent'), {k: binding[k] for k in INTENT_KEYS}), 'native_grant_join')
    need(once.get('effect') == 'BOUND_NATIVE_QUALIFICATION' and once.get('automatic_retry') is False
         and once.get('manifest_sha256') == proofs['native_binding']['sha256']
         and once.get('root_grant_sha256') == proofs['native_root_grant']['sha256'], 'native_once_join')
    fixtures = binding['fixtures']
    need(type(fixtures) is list and len(fixtures) == 7, 'binding_seven')
    byid = {}
    for i, f in enumerate(fixtures):
        ident, fmt = 'f06-' + str(i + 1), FORMATS[i]
        need(f.get('id') == ident and f.get('format') == fmt
             and f.get('profile') == ('compatible' if i < 6 else 'current_latest')
             and exact_json(f.get('edit'), edit_for(fmt)), 'binding_fixture_profile_or_edit')
        byid[ident] = f
    records = load('records'); observations = load('observations', True); summary = load('summary', True)
    kind = req.get('records_kind')
    need(kind in ('r3_output_request', 'Root_readonly_reconciliation'), 'records_kind')
    if kind == 'r3_output_request':
        need(records.get('stage') == 'NOT_RUN' and exact_json(records.get('credential'), cred), 'native_request_pending_oracle')
        items = records['outputs']
    else:
        need(records.get('schema') == 'friday.f06.reconciled-native-outputs.v1'
             and records.get('assignment') == ASSIGNMENT and records.get('read_only_reconciliation') is True
             and records.get('native_success_credit') is False
             and records.get('native_binding_sha256') == proofs['native_binding']['sha256']
             and records.get('native_root_grant_sha256') == proofs['native_root_grant']['sha256']
             and records.get('native_once_sha256') == proofs['native_once']['sha256'], 'Root_reconciliation_join')
        items = records['outputs']
    need(type(items) is list and 0 < len(items) <= 7, 'retained_outputs_required')
    output_map = {}
    for item in items:
        ident = item['fixture_id']; need(ident in byid and ident not in output_map, 'duplicate_or_unknown_output')
        need(item.get('format') == byid[ident]['format'], 'output_profile_mismatch'); output_map[ident] = item
    selected = req['selected_fixture_ids']
    need(type(selected) is list and selected and selected == sorted(set(selected), key=lambda n: int(n.split('-')[-1]))
         and all(n in output_map for n in selected), 'selected_retained_subset')
    obsmap = {}
    if observations is not None:
        need(type(observations) is list, 'observations_shape')
        for row in observations:
            ident = row['id']; need(ident in byid and ident not in obsmap, 'observations_identity'); obsmap[ident] = row
    rows, snapshots = [], []
    for ident in selected:
        f, item = byid[ident], output_map[ident]; fmt = f['format']; index = int(ident[4:])
        output_ref = {k: item[k] for k in ('path', 'sha256', 'bytes')}
        opath = canonical(output_ref['path'])
        need(opath.is_relative_to(QUALIFICATION_ROOT) and opath.name == ident + '-edited.' + fmt, 'native_output_slot')
        source_raw, source_actual = read_ref(f['input'], forbidden, 1_000_000)
        output_raw, output_actual = read_ref(output_ref, forbidden, 1_000_000)
        need(source_actual['path'] != output_actual['path'] and source_actual['sha256'] != output_actual['sha256'], 'output_not_edited_source_copy')
        row = obsmap.get(ident)
        if kind == 'r3_output_request':
            need(row is not None and row.get('format') == fmt and row.get('profile') == f['profile']
                 and row.get('checks', {}).get('correct_edit') is True, 'recorded_native_edit_join')
            receipt = row.get('receipts', {}).get('correct_edit', {})
            need(receipt.get('success') is True and receipt.get('sha256') == item['sha256']
                 and receipt.get('source_sha256') == f['input']['sha256'], 'native_receipt_output_source_join')
        elif row is not None:
            need(row.get('format') == fmt and row.get('profile') == f['profile'], 'reconciled_observation_profile')
        name = 'f06-native-edited.' + fmt if index <= 6 else 'f06-native-edited-default-latest.odt'
        rows.append({'fixture_id': ident, 'format': fmt,
                     'fixture_profile': 'compatible1.3_or_Agile' if index <= 6 else 'current_default_latest_odt_negative',
                     'path': output_actual['path'], 'sha256': output_actual['sha256'], 'bytes': output_actual['bytes'],
                     'staged_name': name, 'semantic': 'BRAVO23', 'native_source_ciphertext': source_actual,
                     'native_output_custody': output_actual, 'native_edit_intent': edit_for(fmt),
                     'native_case_status': row.get('status', 'UNKNOWN_AFTER_CREATE') if row else 'UNKNOWN_AFTER_CREATE',
                     'lineage': kind, 'native_success_inferred_from_oracle': False,
                     'staging': 'COPY_SAME_BYTES_MODE0600_UNDER_ROOT_PRIVATE_NATIVE_OUTPUTS; no store/decrypt/re-encrypt',
                     'independent_oracle': 'NOT_GRANTED_BY_THIS_MANIFEST'})
        snapshots += [(f['input'], source_actual), (output_ref, output_actual)]
    # Independent second physical read catches concurrent source/output drift while building the plan.
    for ref, expected in snapshots:
        _, actual = read_ref(ref, forbidden, 1_000_000)
        need(actual == expected, 'handoff_source_or_output_cas')
    return {'schema': 'friday.f06.retained-native-edit-oracle.v1',
            'state': 'BOUND_RETAINED_BYTES_NOT_EXECUTION_AUTHORITY', 'assignment': ASSIGNMENT,
            'semantic': 'BRAVO23', 'native_operation_id': binding['operation_id'],
            'credential': cred, 'proofs': proofs, 'records_kind': kind,
            'native_operation_summary_status': summary.get('status') if summary else 'PARTIAL_OR_UNKNOWN',
            'selected_fixture_ids': selected, 'selected_count': len(rows), 'fixtures': rows,
            'retained_but_not_selected': [n for n in output_map if n not in selected],
            'not_present_in_retained_records': [n for n in byid if n not in output_map],
            'expected_Office_stores': 0, 'expected_Office_password_probes': 3 * len(rows),
            'full_compatible_six_selected': all('f06-' + str(i) in selected for i in range(1, 7)),
            'modern_seventh_selected': 'f06-7' in selected, 'whole_F06_accepted': False,
            'authority': 'ROOT_FRESH_FINITE_READONLY_ORACLE_ADMISSION_AND_EFFECT_RECONCILIATION_REQUIRED',
            'credential_content_status': 'NOT_OPENED_OR_REHASHED; Root must verify exact upstream digest before private staging',
            'no_credential_values_read_or_written': True, 'no_output_regeneration': True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--request', required=True); ap.add_argument('--request-sha256', required=True)
    ap.add_argument('--output', required=True); args = ap.parse_args(); os.umask(0o077)
    p = Path(args.request); need(p.is_file(), 'request_absent')
    raw, _ = read_ref({'path': str(p), 'sha256': args.request_sha256, 'bytes': p.stat().st_size})
    result = build(decode(raw)); out = Path(args.output)
    need(out.is_absolute() and out.parent.resolve() == out.parent and out.parent.is_relative_to(BASE), 'own_output_only')
    need(stat.S_IMODE(out.parent.stat().st_mode) == 0o700, 'output_parent_custody')
    payload = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    need(sum(q.stat().st_size for q in TASK.rglob('*') if q.is_file() and not q.is_symlink()) + len(payload) < 192 * 1024**2, 'own192MiB_cap')
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(payload); f.flush(); os.fsync(f.fileno())
    print(json.dumps({'state': 'RETAINED_METADATA_ONLY_NO_OFFICE_AUTHORITY', 'selected_count': len(result['fixtures']), 'sha256': sha(payload)}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('F06_HANDOFF_REFUSED:' + (str(error) if isinstance(error, HandoffError) else type(error).__name__))
        raise SystemExit(2)
