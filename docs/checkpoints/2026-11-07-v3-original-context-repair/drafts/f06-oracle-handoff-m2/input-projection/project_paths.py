"""Dormant F06 target-path projection. Reads pinned metadata/ciphertext only.

Projection success is neither encryption validation, oracle acceptance nor authority.
No source_path/credential_ref is opened or rewritten. No raw document is modified.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat

BASE = Path(__file__).absolute().parent
ANCHOR = Path('/home/jericho/.cache')
TASK = BASE.parent.parent
ASSIGNMENT = 'ASTRA-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111#1'
FORMATS = ('docx', 'xlsx', 'pptx', 'odt', 'ods', 'odp', 'odt')
PROFILES = ('compatible1.3_or_Agile',) * 6 + ('current_default_latest_odt_negative',)
PREFIXES = {'/work/encrypted-inputs'}
HEX = re.compile('[0-9a-f]{64}')
REF_KEYS = {'path', 'sha256', 'bytes', 'uid', 'gid', 'mode', 'dev', 'ino', 'nlink', 'mtime_ns', 'ctime_ns'}


class Refused(ValueError):
    """Fixed public code only: never serialize caller text or exception contents."""


def need(ok, code):
    if not ok:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def lexical(raw):
    # Reject aliases before pathlib can erase // or /./ (including trailing /).
    need(type(raw) is str and raw.startswith('/') and '\\' not in raw
         and '\x00' not in raw and all(p not in ('', '.', '..') for p in raw.split('/')[1:]), 'lexical_path')
    return Path(raw)


def file_state(s):
    return (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def dir_state(s):
    return (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode, s.st_nlink)


def open_parent(path):
    """Open the whole chain without following symlinks; hold it through file read."""
    need(path.is_relative_to(ANCHOR) and path != ANCHOR, 'private_cache_path')
    chain = []
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    chain.append((None, '/', fd, os.fstat(fd)))
    current = Path('/')
    try:
        for part in path.parts[1:-1]:
            parentfd = fd
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parentfd)
            current = current / part
            s = os.fstat(fd)
            need(stat.S_ISDIR(s.st_mode), 'parent_type')
            if current == ANCHOR or current.is_relative_to(ANCHOR):
                need(s.st_uid == os.getuid() and stat.S_IMODE(s.st_mode) == 0o700, 'parent_custody')
            chain.append((parentfd, part, fd, s))
        return chain
    except BaseException:
        for _, _, held, _ in reversed(chain):
            os.close(held)
        # If custody failed before appending the most recently opened fd.
        if fd not in [item[2] for item in chain]:
            os.close(fd)
        raise


def check_chain(chain):
    for parentfd, name, fd, before in chain:
        now = os.stat(name, dir_fd=parentfd, follow_symlinks=False) if parentfd is not None else os.stat('/')
        need(dir_state(before) == dir_state(os.fstat(fd)) == dir_state(now), 'parent_cas')


def ref_shape(ref):
    need(type(ref) is dict and {'path', 'sha256', 'bytes'} <= set(ref) <= REF_KEYS, 'reference_shape')
    need(type(ref['sha256']) is str and HEX.fullmatch(ref['sha256']) is not None
         and type(ref['bytes']) is int and ref['bytes'] >= 0, 'reference_pin')
    return lexical(ref['path'])


def read_ref(ref, limit=2 * 1024**2):
    path = ref_shape(ref)
    chain = open_parent(path)
    try:
        parentfd = chain[-1][2]
        before = os.stat(path.name, dir_fd=parentfd, follow_symlinks=False)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
             and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600
             and 0 <= before.st_size == ref['bytes'] <= limit, 'file_custody')
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parentfd)
        with os.fdopen(fd, 'rb') as stream:
            held = os.fstat(stream.fileno())
            need(file_state(before) == file_state(held), 'opened_file_cas_before_read')
            check_chain(chain)
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        now = os.stat(path.name, dir_fd=parentfd, follow_symlinks=False)
        need(file_state(before) == file_state(held) == file_state(after) == file_state(now), 'file_cas')
        check_chain(chain)
        digest = sha(raw)
        need(len(raw) == ref['bytes'] and digest == ref['sha256'], 'file_hash')
        actual = dict(path=str(path), sha256=digest, bytes=len(raw), uid=held.st_uid,
                      gid=held.st_gid, mode='0600', dev=held.st_dev, ino=held.st_ino,
                      nlink=held.st_nlink, mtime_ns=held.st_mtime_ns, ctime_ns=held.st_ctime_ns)
        need(all(k not in ref or type(ref[k]) is type(actual[k]) and ref[k] == actual[k]
                 for k in REF_KEYS), 'declared_cas')
        return raw, actual
    finally:
        for _, _, fd, _ in reversed(chain):
            os.close(fd)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def finite(value):
        parsed = float(value)
        need(math.isfinite(parsed), 'json_nonfinite')
        return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_float=finite,
                      parse_constant=lambda _: (_ for _ in ()).throw(Refused('json_constant')))


def target_name(index):
    return ('f06-new-encrypted.' if index < 6 else 'f06-new-default-latest.') + FORMATS[index]


def namespace_target(raw, prefixes, name):
    lexical(raw)
    need(any(raw == prefix + '/' + name for prefix in prefixes), 'namespace_target')
    return raw


def project(req):
    # First guard precedes all file operations, including reading any declared ref.
    need(type(req) is dict and req.get('schema') == 'friday.f06.host-path-projection-request.v1'
         and req.get('state') == 'BOUND_READONLY_PROJECTION' and req.get('assignment') == ASSIGNMENT, 'unbound_request')
    need(set(req) == {'schema', 'state', 'assignment', 'namespace_prefixes', 'host_root',
                      'raw_custody', 'raw_result', 'expected_fixtures'}, 'request_keys')
    prefixes = req['namespace_prefixes']
    need(type(prefixes) is list and len(prefixes) == 1
         and all(type(p) is str and p in PREFIXES for p in prefixes), 'explicit_fixed_prefixes')
    host = lexical(req['host_root'])
    need(host.is_relative_to(ANCHOR) and host.name == 'encrypted-inputs', 'host_root_slot')
    expected = req['expected_fixtures']
    need(type(expected) is list and 1 <= len(expected) <= 7, 'expected_prefix')
    for i, row in enumerate(expected):
        need(type(row) is dict and set(row) == {'name', 'format', 'fixture_profile', 'sha256', 'bytes',
                                               'custody_path', 'result_path', 'source_path', 'source_sha256'}, 'expected_row_keys')
        need(row['name'] == target_name(i) and row['format'] == FORMATS[i]
             and row['fixture_profile'] == PROFILES[i], 'expected_family_profile_name')
        namespace_target(row['custody_path'], prefixes, row['name'])
        namespace_target(row['result_path'], prefixes, row['name'])
        lexical(row['source_path'])  # Historical metadata only, never resolved/opened.
        need(type(row['source_sha256']) is str and HEX.fullmatch(row['source_sha256']) is not None, 'expected_source_hash')
        ref_shape({'path': str(host / row['name']), 'sha256': row['sha256'], 'bytes': row['bytes']})
        need(0 < row['bytes'] <= 1_000_000, 'ciphertext_limit')
    cp = ref_shape(req['raw_custody'])
    need(cp.name == 'CUSTODY.json', 'raw_custody_slot')
    if req['raw_result'] is not None:
        rp = ref_shape(req['raw_result'])
        need(rp.name == 'RESULT.json' and rp != cp, 'raw_result_slot')
    custody_raw, custody_ref = read_ref(req['raw_custody'])
    custody = decode(custody_raw)
    need(type(custody) is dict and custody.get('mode') == 'produce'
         and type(custody.get('planned_rows')) is int and len(expected) <= custody['planned_rows'] <= 7
         and type(custody.get('known_prefix_count')) is int and custody['known_prefix_count'] == len(expected)
         and type(custody.get('fixtures')) is list and len(custody['fixtures']) == len(expected), 'custody_prefix_contract')
    result, result_ref = None, None
    if req['raw_result'] is not None:
        raw, result_ref = read_ref(req['raw_result'])
        result = decode(raw)
        need(type(result) is dict and result.get('mode') == 'produce'
             and type(result.get('rows')) is list and 1 <= len(result['rows']) <= len(expected)
             and type(result.get('planned_rows')) is int and len(result['rows']) <= result['planned_rows'] <= 7
             and type(result.get('whole_seven_covered')) is bool and type(result.get('all_pass')) is bool, 'result_prefix_contract')
    projected_custody, projected_result = copy.deepcopy(custody), copy.deepcopy(result)
    snapshots, provenance = [(req['raw_custody'], custody_ref)], []
    if result_ref is not None:
        snapshots.append((req['raw_result'], result_ref))
    for i, row in enumerate(expected):
        c = custody['fixtures'][i]
        need(type(c) is dict and all(type(c.get(k)) is type(row[k]) and c.get(k) == row[k]
             for k in ('name', 'format', 'fixture_profile', 'sha256', 'bytes'))
             and c.get('path') == row['custody_path'], 'custody_expected_join')
        host_ref = {'path': str(host / row['name']), 'sha256': row['sha256'], 'bytes': row['bytes']}
        _, physical = read_ref(host_ref, 1_000_000)
        snapshots.append((host_ref, physical))
        projected_custody['fixtures'][i]['path'] = physical['path']
        joined = {'index': i, 'raw_custody_path': c['path'], 'host_ciphertext': physical}
        if result is not None and i < len(result['rows']):
            r = result['rows'][i]
            need(type(r) is dict and all(type(r.get(k)) is type(row[k]) and r.get(k) == row[k]
                 for k in ('format', 'fixture_profile', 'sha256', 'bytes', 'source_path', 'source_sha256'))
                 and r.get('path') == row['result_path'], 'result_expected_source_join')
            projected_result['rows'][i]['path'] = physical['path']
            joined['raw_result_path'] = r['path']
        provenance.append(joined)
    # Re-read all pinned raw records and ciphertexts to reject whole-build drift.
    for ref, original in snapshots:
        _, current = read_ref(ref, 1_000_000 if Path(ref['path']).suffix != '.json' else 2 * 1024**2)
        need(current == original, 'projection_cas')
    record = {'schema': 'friday.f06.host-path-projection-provenance.v1',
              'state': 'DERIVED_METADATA_NO_ORACLE_OR_EXECUTION_AUTHORITY', 'assignment': ASSIGNMENT,
              'namespace_prefixes': list(prefixes), 'host_root': str(host),
              'raw_custody': custody_ref, 'raw_result': result_ref, 'rows': provenance,
              'only_changed_fields': ['fixtures[*].path', 'rows[*].path'],
              'source_and_credential_paths': 'UNCHANGED_HISTORICAL_METADATA_NOT_OPENED',
              'ciphertext_validation': 'CUSTODY_HASH_SIZE_IDENTITY_ONLY_NOT_ENCRYPTION_OR_PASSWORD_PROOF',
              'root_native_binding_and_grant': 'UNBOUND_NOT_CREATED_BY_PROJECTION'}
    return {'custody': projected_custody, 'result': projected_result, 'provenance': record}


def dump_exclusive(path, obj, dirfd):
    raw = (json.dumps(obj, ensure_ascii=True, indent=2, allow_nan=False) + '\n').encode()
    need(len(raw) < 4 * 1024**2, 'output_limit')
    fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dirfd)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return {'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--request-bytes', required=True, type=int)
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--output-name', required=True)
    a = parser.parse_args()
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(Refused('wall_limit')))
    signal.alarm(300)
    need(re.fullmatch('[A-Za-z0-9_-]{1,80}', a.output_name) is not None, 'output_name')
    need(HEX.fullmatch(a.helper_sha256) is not None, 'helper_pin_required')
    need(sum(p.lstat().st_size for p in TASK.rglob('*') if p.is_file() and not p.is_symlink()) < 192 * 1024**2 - 12 * 1024**2, 'task_disk_cap')
    helper = Path(__file__).absolute()
    _, helper_ref = read_ref({'path': str(helper), 'sha256': a.helper_sha256, 'bytes': helper.stat().st_size})
    raw, request_ref = read_ref({'path': a.request, 'sha256': a.request_sha256, 'bytes': a.request_bytes})
    projected = project(decode(raw))
    # All validation/reads precede output creation. Never overwrite a prior run.
    out = BASE / a.output_name
    chain = open_parent(BASE / 'directory-anchor')
    outfd = None
    try:
        basefd = chain[-1][2]
        check_chain(chain)
        os.mkdir(a.output_name, 0o700, dir_fd=basefd)
        # Our mkdir changes BASE.nlink; preserve the other directory identity fields.
        parent, name, held, before = chain[-1]
        after = os.fstat(basefd)
        need(dir_state(before)[:-1] == dir_state(after)[:-1], 'output_parent_cas')
        chain[-1] = (parent, name, held, after)
        outfd = os.open(a.output_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=basefd)
        outstat = os.fstat(outfd)
        need(stat.S_ISDIR(outstat.st_mode) and outstat.st_uid == os.getuid()
             and stat.S_IMODE(outstat.st_mode) == 0o700, 'output_directory_custody')
        outstate = dir_state(outstat)
        def output_cas():
            check_chain(chain)
            need(dir_state(os.stat(a.output_name, dir_fd=basefd, follow_symlinks=False))
                 == dir_state(os.fstat(outfd)) == outstate, 'output_directory_cas')
        output_cas()
        refs = {'custody': dump_exclusive(out / 'CUSTODY.HOST.json', projected['custody'], outfd)}
        if projected['result'] is not None:
            refs['result'] = dump_exclusive(out / 'RESULT.HOST.json', projected['result'], outfd)
        projected['provenance']['projection_request'] = request_ref
        projected['provenance']['projection_helper'] = helper_ref
        projected['provenance']['derived'] = dict(refs)
        output_cas()
        refs['provenance'] = dump_exclusive(out / 'PROJECTION.json', projected['provenance'], outfd)
        os.fsync(outfd)
        output_cas()
    finally:
        if outfd is not None:
            os.close(outfd)
        for _, _, fd, _ in reversed(chain):
            os.close(fd)
    print(json.dumps({'status': 'PROJECTED_METADATA_ONLY', 'refs': refs}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status': 'REFUSED', 'code': str(exc) if isinstance(exc, Refused) else type(exc).__name__}))
        raise SystemExit(2)
