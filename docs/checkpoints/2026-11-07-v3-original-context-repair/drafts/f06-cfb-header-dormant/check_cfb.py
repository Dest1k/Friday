"""Task20 parser-only controls; real ciphertext is never decrypted or copied.

Synthetic fixed-envelope packages below contain inert bytes, not encryption
results. Real-file observations are reported separately from synthetic PASS.
"""
import ast
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import stat
import struct
import sys
import time
import types

B = Path(__file__).resolve().parents[1]
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024 * 1024, 4 * 1024 * 1024))
START = time.monotonic()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load(B / 'baseline/tools/scoped_ooxml_password.py', 'baseline_read')
new = load(B / 'candidate/tools/scoped_ooxml_password.py', 'candidate_read')
package = types.ModuleType('tools')
package.scoped_ooxml_password = new
sys.modules['tools'] = package
writer = load(B / 'baseline/tools/scoped_ooxml_password_edit.py', 'unchanged_writer')
checks = []
decrypt_calls = []


def forbidden_decrypt(*args, **kwargs):
    decrypt_calls.append(True)
    raise AssertionError('decryption forbidden in Task20')


old._aes_decrypt = new._aes_decrypt = forbidden_decrypt


def check(name, condition, **details):
    checks.append({'name': name, 'pass': bool(condition), **details})
    if not condition:
        raise AssertionError(name)


def outcome(module, blob):
    try:
        return 'PARSED', module._CFB(blob).streams
    except module.OOXMLPasswordError as error:
        return error.code, None


def w16(blob, at, value):
    data = bytearray(blob)
    struct.pack_into('<H', data, at, value)
    return bytes(data)


def w32(blob, at, value):
    data = bytearray(blob)
    struct.pack_into('<I', data, at, value)
    return bytes(data)


def byte(blob, at, value):
    data = bytearray(blob)
    data[at] = value
    return bytes(data)


def synthetic_streams(large=False):
    # Exact fixed DataSpaces strings, with an inert Agile-shaped descriptor.
    ds = new._DS
    lp = new._lp
    common = {'saltSize': '16', 'blockSize': '16', 'keyBits': '256',
              'hashSize': '64', 'cipherAlgorithm': 'AES',
              'cipherChaining': 'ChainingModeCBC', 'hashAlgorithm': 'SHA512',
              'saltValue': base64.b64encode(bytes(16)).decode()}
    enc = lambda n: base64.b64encode(bytes(n)).decode()
    root = new.ET.Element('{' + new._NS + '}encryption')
    new.ET.SubElement(root, '{' + new._NS + '}keyData', common)
    new.ET.SubElement(root, '{' + new._NS + '}dataIntegrity', {
        'encryptedHmacKey': enc(64), 'encryptedHmacValue': enc(64)})
    encryptors = new.ET.SubElement(root, '{' + new._NS + '}keyEncryptors')
    encryptor = new.ET.SubElement(encryptors, '{' + new._NS + '}keyEncryptor', {'uri': new._PNS})
    password = dict(common, spinCount='1', encryptedVerifierHashInput=enc(16),
                    encryptedVerifierHashValue=enc(64), encryptedKeyValue=enc(32))
    new.ET.SubElement(encryptor, '{' + new._PNS + '}encryptedKey', password)
    size = 4096 if large else 1
    return {
        ('EncryptionInfo',): struct.pack('<HHI', 4, 4, 0x40) + new.ET.tostring(root),
        ('EncryptedPackage',): struct.pack('<Q', size) + bytes(new._round_block(size)),
        ds + ('Version',): lp('Microsoft.Container.DataSpaces') + struct.pack('<III', 1, 1, 1),
        ds + ('DataSpaceMap',): struct.pack('<IIIII', 8, 1, 104, 1, 0) + lp('EncryptedPackage') + lp('StrongEncryptionDataSpace'),
        ds + ('DataSpaceInfo', 'StrongEncryptionDataSpace'): struct.pack('<II', 8, 1) + lp('StrongEncryptionTransform'),
        ds + ('TransformInfo', 'StrongEncryptionTransform', '\x06Primary'): (
            struct.pack('<II', 88, 1) + lp('{FF9A3F03-56EF-4613-BDD5-5A41C1D07246}')
            + lp('Microsoft.Container.EncryptionTransform') + struct.pack('<IIIIIII', 1, 1, 1, 0, 0, 0, 4))}


def to_v4(v3):
    # Repack this SMALL synthetic writer fixture into four v4 sectors.
    # Stream mini-sector indexes and directory trees remain byte-for-byte.
    cfb = new._CFB(v3)
    assert all(len(value) < 4096 for value in cfb.streams.values())
    directory = bytearray(cfb._chain(new._u32(v3, 48), cfb.fat, 512,
                                   cfb.sectors, set(), limit=64))
    struct.pack_into('<I', directory, 116, 1)  # root mini stream is v4 SID1
    assert len(cfb.mini) <= 4096
    mini = cfb.mini.ljust(4096, b'\0')
    mini_fat = struct.pack('<' + 'I' * len(cfb.mini_fat), *cfb.mini_fat)
    mini_fat = mini_fat.ljust(4096, b'\xff')
    fat = struct.pack('<' + 'I' * 1024, new.END, new.END, new.END,
                      new.FAT, *([new.FREE] * 1020))
    header = bytearray(4096)
    header[:512] = v3[:512]
    struct.pack_into('<HH', header, 26, 4, 0xFFFE)
    struct.pack_into('<H', header, 30, 12)
    struct.pack_into('<IIIIIIIII', header, 40, 1, 1, 0, 0, 4096, 2, 1, new.END, 0)
    struct.pack_into('<' + 'I' * 109, header, 76, 3, *([new.FREE] * 108))
    return bytes(header) + bytes(directory).ljust(4096, b'\0') + mini + mini_fat + fat


def dir_offsets(blob):
    cfb = new._CFB(blob)
    sid = new._u32(blob, 48)
    result = {}
    while sid != new.END:
        start = (sid + 1) * cfb.sector_size
        for at in range(start, start + cfb.sector_size, 128):
            row = blob[at:at + 128]
            if row[66]:
                name = row[:new._u16(row, 64) - 2].decode('utf-16le')
                result[name] = at
        sid = cfb.fat[sid]
    return result


def synthetic_controls():
    # The rest of the entire product AST is unchanged, not just sample errors.
    a = ast.parse((B / 'baseline/tools/scoped_ooxml_password.py').read_text())
    b = ast.parse((B / 'candidate/tools/scoped_ooxml_password.py').read_text())
    def header(tree):
        return next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                    and len(n.body) == 1 and isinstance(n.body[0], ast.Expr)
                    and isinstance(n.body[0].value, ast.Call)
                    and n.body[0].value.args and isinstance(n.body[0].value.args[0], ast.Constant)
                    and n.body[0].value.args[0].value == 'cfb_header')
    header(b).test = copy.deepcopy(header(a).test)
    check('whole_product_AST_unchanged_except_header_predicate', ast.dump(a) == ast.dump(b))

    fixtures = {'writer-small-v3': writer._cfb(synthetic_streams(), lambda: None),
                'writer-large-v3': writer._cfb(synthetic_streams(True), lambda: None)}
    fixtures['synthetic-v4'] = to_v4(fixtures['writer-small-v3'])
    for label, blob in fixtures.items():
        expected = synthetic_streams(label == 'writer-large-v3')
        major = new._u16(blob, 26)
        check(label + '_canonical003E', new._u16(blob, 24) == 0x3E)
        check(label + '_baseline_and_candidate_same_streams',
              outcome(old, blob) == outcome(new, blob) == ('PARSED', expected))
        if major == 3:
            legacy = w16(blob, 24, 0x3B)
            check(label + '_003B_valid_streams', outcome(new, legacy) == ('PARSED', expected))
            check(label + '_003B_old_refusal_reproduced', outcome(old, legacy)[0] == 'cfb_header')
        else:
            check('v4_003B_still_refused', outcome(new, w16(blob, 24, 0x3B))[0] == 'cfb_header')
        for minor in (0, 0x3A, 0x3C, 0x3D, 0x3F, 0xFFFF):
            check(label + '_invalidminor_' + hex(minor),
                  outcome(new, w16(blob, 24, minor))[0] == 'cfb_header')
        for format in ('docx', 'xlsx', 'pptx'):
            try:
                new.prepare_read(blob, format, password=None)
                code = 'UNEXPECTED_RETURN'
            except new.OOXMLPasswordError as error:
                code = error.code
            check(label + '_no_password_' + format, code == 'ooxml_password_required', observed=code)

    blob = fixtures['writer-large-v3']
    rows = dir_offsets(blob)
    root = rows['Root Entry']
    info = rows['EncryptionInfo']
    package = rows['EncryptedPackage']
    fat_sid = new._u32(blob, 76)
    fat_at = (fat_sid + 1) * 512
    mini_fat_at = (new._u32(blob, 60) + 1) * 512
    package_sid = new._u32(blob, package + 116)
    mutations = {
        'signature': (byte(blob, 0, 0), 'cfb_signature'),
        'short_header': (blob[:511], 'cfb_signature'),
        'header_CLSID': (byte(blob, 8, 1), 'cfb_header'),
        'bad_major': (w16(blob, 26, 5), 'cfb_header'),
        'bad_endian': (w16(blob, 28, 0xFEFF), 'cfb_header'),
        'wrong_v3_shift': (w16(blob, 30, 12), 'cfb_header'),
        'wrong_mini_shift': (w16(blob, 32, 5), 'cfb_header'),
        'reserved': (byte(blob, 34, 1), 'cfb_header'),
        'cutoff': (w32(blob, 56, 2048), 'cfb_header'),
        'truncated_sector': (blob[:-1], 'cfb_geometry'),
        'v3_directory_count': (w32(blob, 40, 1), 'cfb_allocation_count'),
        'fat_count_zero': (w32(blob, 44, 0), 'cfb_allocation_count'),
        'mini_count_bounds': (w32(blob, 64, len(blob)), 'cfb_allocation_count'),
        'DIFAT_unexpected_head': (w32(blob, 68, 0), 'cfb_difat_count'),
        'DIFAT_duplicate_fat': (w32(w32(blob, 44, 2), 80, fat_sid), 'cfb_sector_overlap_or_cycle'),
        'DIFAT_FAT_id_out_of_bounds': (w32(blob, 76, len(blob)), 'cfb_sector_bounds'),
        'FAT_marker': (w32(blob, fat_at + fat_sid * 4, new.END), 'cfb_allocation_marker'),
        'FAT_sector_out_of_bounds': (w32(blob, fat_at + package_sid * 4, len(blob)), 'cfb_sector_bounds'),
        'FAT_padding': (w32(blob, fat_at + (len(blob) // 512 - 1) * 4, new.END), 'cfb_fat_padding'),
        'directory_FAT_cycle': (w32(blob, fat_at + new._u32(blob, 48) * 4, new._u32(blob, 48)), 'cfb_sector_overlap_or_cycle'),
        'root_CLSID': (byte(blob, root + 80, 1), 'ooxml_cfb_clsid'),
        'root_kind': (byte(blob, root + 66, 2), 'cfb_root'),
        'invalid_color': (byte(blob, info + 67, 2), 'cfb_directory_entry'),
        'first_sibling_red': (byte(blob, (new._u32(blob, 48) + 1) * 512 + new._u32(blob, root + 76) * 128 + 67, 0), 'cfb_directory_tree'),
        'unowned_sector': (w32(blob + bytes(512), fat_at + (len(blob) // 512 - 1) * 4, new.END), 'cfb_unowned_sector'),
        'unowned_minisector': (w32(w32(blob, root + 120, new._u32(blob, root + 120) + 64), mini_fat_at + new._u32(blob, root + 120) // 64 * 4, new.END), 'cfb_unowned_minisector'),
        'stream_child': (w32(blob, package + 76, 1), 'unsupported_cfb_stream'),
        'stream_size_limit': (w32(blob, package + 120, new.MAX_INPUT + 1), 'cfb_stream_limit'),
        'v3_stream_highword': (w32(blob, package + 124, 1), 'cfb_v3_stream_size'),
        'directory_cycle': (w32(blob, info + 68, (info - (new._u32(blob, 48) + 1) * 512) // 128), 'cfb_directory_cycle_or_bounds'),
        'directory_orphan': (w32(blob, root + 76, new.FREE), 'cfb_directory_orphan'),
        'unknown_stream': (byte(blob, package, ord('X')), 'unsupported_cfb_stream'),
        'mini_chain_cycle': (w32(blob, mini_fat_at + new._u32(blob, info + 116) * 4, new._u32(blob, info + 116)), 'cfb_sector_overlap_or_cycle'),
        'large_stream_chain_short': (w32(blob, fat_at + package_sid * 4, new.END), 'cfb_chain_length'),
    }
    v4 = fixtures['synthetic-v4']
    mutations.update({
        'wrong_v4_shift': (w16(v4, 30, 9), 'cfb_header'),
        'v4_padding': (byte(v4, 512, 1), 'cfb_geometry'),
        'v4_directory_count': (w32(v4, 40, 2), 'cfb_directory_count'),
    })
    for label, (bad, expected) in mutations.items():
        observed_old = outcome(old, bad)[0]
        observed_new = outcome(new, bad)[0]
        check('negative_' + label, observed_new == observed_old == expected,
              observed=observed_new, expected=expected)
        if new._u16(bad, 26) == 3 and label not in ('short_header', 'signature'):
            # Header compatibility must not disable any downstream refusal.
            legacy_bad = w16(bad, 24, 0x3B)
            check('legacy_negative_' + label, outcome(new, legacy_bad)[0] == expected)
    check('no_decryption_called_synthetic', not decrypt_calls)
    return {'fixtures': [{'name': name, 'bytes': len(value),
                          'sha256': hashlib.sha256(value).hexdigest()}
                         for name, value in fixtures.items()]}


def identity(s):
    return [s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def real_controls():
    base = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112/operations/generate-g6/work/encrypted-inputs')
    expected = {
        'docx': (23040, '22b0dcb3fed3d979b37ff701af42b00d3756d76a863e8f8c736405acc9c33fd5'),
        'xlsx': (8704, '041432418a341a058661aac4ca8659ebabf2c5c04cd716a6e8ed1020dbb256e6'),
        'pptx': (19456, '552a636f0bd052b90189763ccb0731060e8510679c730aa65e6fb6fbecf3da98'),
    }
    rows = []
    for ext, (size, sha) in expected.items():
        path = base / ('f06-new-encrypted.' + ext)
        before = identity(path.lstat())
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            assert identity(os.fstat(fd)) == before
            assert stat.S_ISREG(before[2]) and before[5] == 1 and before[3] == os.getuid()
            raw = os.read(fd, size + 1)
            assert len(raw) == size and hashlib.sha256(raw).hexdigest() == sha
            baseline = outcome(old, raw)[0]
            candidate = outcome(new, raw)[0]
            check(ext + '_header_only_then_tree_refusal', baseline == 'cfb_header'
                  and candidate == 'cfb_directory_tree', baseline=baseline, candidate=candidate)
            assert identity(os.fstat(fd)) == before
            rows.append({'format': ext, 'path': str(path), 'bytes': size, 'sha256': sha,
                         'before_identity': before, 'after_identity': identity(path.lstat()),
                         'baseline': baseline, 'candidate': candidate,
                         'valid_package_claim': False, 'decryption': False})
            assert rows[-1]['after_identity'] == before
        finally:
            os.close(fd)
    check('no_decryption_called_real', not decrypt_calls)
    return rows


def main():
    result = {'scope': 'PARSER_ONLY_SYNTHETIC_AND_EXACT_REAL3_NO_DECRYPT',
              'python': sys.version, 'executable': sys.executable}
    try:
        result['synthetic'] = synthetic_controls()
        result['real3'] = real_controls()
        result['state'] = 'CONTROLS_PASS_REAL3_REMAIN_REFUSED_TREE'
    except BaseException as error:
        result['state'] = 'FAILED'
        result['failure_class'] = type(error).__name__
        result['failure_control'] = str(error) if isinstance(error, AssertionError) else 'fixed_control_failure'
        raise
    finally:
        result.update(checks=checks, pass_count=sum(row['pass'] for row in checks),
                      elapsed_seconds=time.monotonic() - START, decrypt_calls=len(decrypt_calls),
                      usage={'cpu_seconds': resource.getrusage(resource.RUSAGE_SELF).ru_utime
                             + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                             'maxrss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        target = B / 'evidence' / sys.argv[1]
        with target.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        print(json.dumps({'state': result['state'], 'checks': len(checks),
                          'pass_count': result['pass_count'], 'seconds': result['elapsed_seconds']}))


if __name__ == '__main__':
    main()
