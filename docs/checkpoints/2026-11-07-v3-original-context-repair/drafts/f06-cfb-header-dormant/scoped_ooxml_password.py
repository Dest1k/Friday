"""Bounded read-only ECMA-376 Agile AES/CBC OOXML password envelope.

CFB allocation parser specialized from tools.scoped_doc (Source129); no
legacy Office profiles are changed. Crypto follows MS-OFFCRYPTO 2.3.4.10-15
using installed Cryptodome AES and stdlib hashlib/hmac. No crypto algorithm
implementation or third-party source is vendored. See OOXML-PASSWORD-NOTES.md.
This module has no filesystem, subprocess, network or package installation.
"""
from __future__ import annotations
import base64
import binascii
import hashlib
import hmac
import io
import re
import struct
import zipfile
import zlib
from xml.etree import ElementTree as ET

MAX_INPUT = 1_000_000
MAX_DIRECTORY = 256
MAX_DESCRIPTOR = 16_384
MAX_SPIN = 200_000
MAX_ZIP_TOTAL = 8_000_000
MAX_XML = 2_000_000
FREE = 0xFFFFFFFF
END = 0xFFFFFFFE
FAT = 0xFFFFFFFD
DIF = 0xFFFFFFFC
CFB_SIGNATURE = bytes.fromhex('d0cf11e0a1b11ae1')
FORMATS = frozenset(('docx', 'dotx', 'docm', 'dotm', 'xlsx', 'xltx', 'xlsm', 'xltm',
                     'xlsb', 'pptx', 'potx', 'ppsx', 'pptm', 'potm', 'ppsm'))
_DS = ('\x06DataSpaces',)
_STORAGES = frozenset((_DS, _DS + ('DataSpaceInfo',), _DS + ('TransformInfo',),
                      _DS + ('TransformInfo', 'StrongEncryptionTransform')))
_STREAMS = frozenset((('EncryptionInfo',), ('EncryptedPackage',),
    _DS + ('Version',), _DS + ('DataSpaceMap',),
    _DS + ('DataSpaceInfo', 'StrongEncryptionDataSpace'),
    _DS + ('TransformInfo', 'StrongEncryptionTransform', '\x06Primary')))

def _lp(value):
    raw = value.encode('utf-16le')
    return struct.pack('<I', len(raw)) + raw + bytes((-len(raw)) % 4)

def _dataspaces(streams, storages):
    # MS-OFFCRYPTO 2.1.5 and 2.3.4.1-3: the sole transform maps the
    # EncryptedPackage stream to the v1 strong-encryption transform.
    if set(streams) != _STREAMS or storages != _STORAGES:
        _fail('ooxml_dataspaces_structure')
    expected = {
        _DS + ('Version',): _lp('Microsoft.Container.DataSpaces') + struct.pack('<III', 1, 1, 1),
        _DS + ('DataSpaceMap',): struct.pack('<IIIII', 8, 1, 104, 1, 0) + _lp('EncryptedPackage') + _lp('StrongEncryptionDataSpace'),
        _DS + ('DataSpaceInfo', 'StrongEncryptionDataSpace'): struct.pack('<II', 8, 1) + _lp('StrongEncryptionTransform'),
        _DS + ('TransformInfo', 'StrongEncryptionTransform', '\x06Primary'): (
            struct.pack('<II', 88, 1) + _lp('{FF9A3F03-56EF-4613-BDD5-5A41C1D07246}')
            + _lp('Microsoft.Container.EncryptionTransform') + struct.pack('<IIIIIII', 1, 1, 1, 0, 0, 0, 4)),
    }
    if any(streams[name] != value for name, value in expected.items()):
        _fail('ooxml_dataspaces_unsupported')

class OOXMLPasswordError(ValueError):
    """Fixed, content-free refusal code."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def _fail(code):
    raise OOXMLPasswordError(code)

def _u16(data, at):
    return struct.unpack_from('<H', data, at)[0]

def _u32(data, at):
    return struct.unpack_from('<I', data, at)[0]

def _words(data):
    return struct.unpack('<' + 'I' * (len(data) // 4), data)

class _CFB:
    def __init__(self, data):
        if len(data) < 512 or data[:8] != bytes.fromhex('d0cf11e0a1b11ae1'):
            _fail('cfb_signature')
        self.data = data
        version = _u16(data, 26)
        shift = _u16(data, 30)
        # 0x003B/v3 is the legacy CFB header emitted by LibreOffice;
        # keep 0x003E for v3/v4 and reject every other minor/major pair.
        if (data[8:24] != b'\0' * 16
                or (_u16(data, 24), version) not in ((0x003B, 3), (0x003E, 3), (0x003E, 4))
                or _u16(data, 28) != 0xFFFE or shift != (9 if version == 3 else 12)
                or _u16(data, 32) != 6 or data[34:40] != b'\0' * 6
                or _u32(data, 56) != 4096):
            _fail('cfb_header')
        self.sector_size = 1 << shift
        if (len(data) % self.sector_size or len(data) < self.sector_size * 3
                or any(data[512:self.sector_size])):
            _fail('cfb_geometry')
        self.sectors = len(data) // self.sector_size - 1
        self.used = set()
        ndir, nfat = _u32(data, 40), _u32(data, 44)
        nmini, ndif = _u32(data, 64), _u32(data, 72)
        if ((version == 3 and ndir != 0) or not 1 <= nfat <= self.sectors
                or nmini > self.sectors or ndif > self.sectors):
            _fail('cfb_allocation_count')
        fat_ids = []
        saw_free = False

        def add_fat_ids(items):
            nonlocal saw_free
            for sid in items:
                if sid == FREE:
                    saw_free = True
                else:
                    if saw_free or len(fat_ids) >= nfat:
                        _fail('cfb_difat_count')
                    self._claim(sid)
                    fat_ids.append(sid)

        add_fat_ids(_words(data[76:512]))
        dif_ids = []
        sid = _u32(data, 68)
        for _ in range(ndif):
            self._claim(sid)
            dif_ids.append(sid)
            items = _words(self._sector(sid))
            add_fat_ids(items[:-1])
            sid = items[-1]
        if sid != END or len(fat_ids) != nfat:
            _fail('cfb_difat_count')
        self.fat = tuple(v for sid in fat_ids for v in _words(self._sector(sid)))
        if len(self.fat) < self.sectors:
            _fail('cfb_fat_coverage')
        for sid, value in enumerate(self.fat):
            if sid >= self.sectors:
                if value != FREE:
                    _fail('cfb_fat_padding')
            elif value not in (FREE, END, FAT, DIF) and value >= self.sectors:
                _fail('cfb_sector_bounds')
        if any(self.fat[sid] != FAT for sid in fat_ids) or any(
                self.fat[sid] != DIF for sid in dif_ids):
            _fail('cfb_allocation_marker')
        directory = self._chain(_u32(data, 48), self.fat, self.sector_size,
                                self.sectors, self.used, limit=MAX_DIRECTORY // (self.sector_size // 128))
        if version == 4 and len(directory) // self.sector_size != ndir:
            _fail('cfb_directory_count')
        if not directory:
            _fail('cfb_directory_missing')
        entries = []
        for at in range(0, len(directory), 128):
            row = directory[at:at + 128]
            kind = row[66]
            if kind == 0:
                entries.append(None)
                continue
            length = _u16(row, 64)
            if (kind not in (1, 2, 5) or length < 2 or length > 64 or length % 2
                    or row[length - 2:length] != b'\0\0' or row[67] not in (0, 1)):
                _fail('cfb_directory_entry')
            try:
                name = row[:length - 2].decode('utf-16le')
            except UnicodeError:
                _fail('cfb_directory_name')
            if not name or any(c in name for c in '\0/\\:!'):
                _fail('cfb_directory_name')
            if version == 3 and _u32(row, 124):
                _fail('cfb_v3_stream_size')
            size = _u32(row, 120) if version == 3 else struct.unpack_from('<Q', row, 120)[0]
            if size > MAX_INPUT:
                _fail('cfb_stream_limit')
            entries.append((name, kind, _u32(row, 68), _u32(row, 72),
                            _u32(row, 76), row[80:96], _u32(row, 116), size, row[67]))
        root = entries[0]
        if (root is None or root[0] != 'Root Entry' or root[1] != 5
                or root[2:4] != (FREE, FREE)):
            _fail('cfb_root')
        if root[5] != bytes(16):
            _fail('ooxml_cfb_clsid')
        # Each storage has its own CFB red-black sibling tree. Every active
        # entry must be reachable exactly once; storage cycles are forbidden.
        forests = [(root[4], ())]
        seen = {0}
        streams = []
        storages = set()
        while forests:
            first, parent_path = forests.pop()
            stack = [(first, None, None, False, 0)]
            leaf_depths = set()
            names = set()
            while stack:
                idx, low, high, parent_red, depth = stack.pop()
                if idx == FREE:
                    leaf_depths.add(depth)
                    continue
                if idx >= len(entries) or idx in seen or entries[idx] is None:
                    _fail('cfb_directory_cycle_or_bounds')
                seen.add(idx)
                row = entries[idx]
                name, kind, left, right, child, clsid, start, size, color = row
                key = (len(name), name.upper())
                if ((low is not None and key <= low) or (high is not None and key >= high)
                        or (parent_red and color == 0) or (idx == first and color != 1)):
                    _fail('cfb_directory_tree')
                if name.casefold() in names or clsid != bytes(16):
                    _fail('cfb_duplicate_or_clsid')
                names.add(name.casefold())
                path = parent_path + (name,)
                if kind == 1:
                    if path not in _STORAGES or size != 0:
                        _fail('unsupported_cfb_storage')
                    storages.add(path)
                    forests.append((child, path))
                elif kind == 2:
                    if child != FREE or path not in _STREAMS:
                        _fail('unsupported_cfb_stream')
                    streams.append((path, start, size))
                else:
                    _fail('cfb_nested_root')
                depth += color
                stack.extend(((left, low, key, color == 0, depth),
                              (right, key, high, color == 0, depth)))
            if len(leaf_depths) > 1:
                _fail('cfb_directory_tree')
        if seen != {i for i, row in enumerate(entries) if row is not None}:
            _fail('cfb_directory_orphan')
        mini_table = self._chain(_u32(data, 60), self.fat, self.sector_size,
                                 self.sectors, self.used, count=nmini)
        self.mini_fat = _words(mini_table)
        self.mini = self._chain(root[6], self.fat, self.sector_size,
                                self.sectors, self.used, size=root[7])
        if len(self.mini) % 64:
            _fail('cfb_ministream_geometry')
        mini_count = len(self.mini) // 64
        if len(self.mini_fat) < mini_count:
            _fail('cfb_minifat_coverage')
        for idx, value in enumerate(self.mini_fat):
            if value not in (FREE, END) and value >= mini_count:
                _fail('cfb_minisector_bounds')
            if idx >= mini_count and value != FREE:
                _fail('cfb_minifat_padding')
        mini_used = set()
        self.streams = {}
        for name, start, size in streams:
            if size < 4096:
                blob = self._chain(start, self.mini_fat, 64, mini_count, mini_used, size=size, mini=True)
            else:
                blob = self._chain(start, self.fat, self.sector_size, self.sectors, self.used, size=size)
            self.streams[name] = blob
        if any(value != FREE and idx not in self.used for idx, value in enumerate(self.fat[:self.sectors])):
            _fail('cfb_unowned_sector')
        if any(value != FREE and idx not in mini_used for idx, value in enumerate(self.mini_fat)):
            _fail('cfb_unowned_minisector')
        if not all((name,) in self.streams for name in ('EncryptionInfo', 'EncryptedPackage')):
            _fail('ooxml_encryption_stream_missing')
        _dataspaces(self.streams, storages)

    def _sector(self, sid):
        if not 0 <= sid < self.sectors:
            _fail('cfb_sector_bounds')
        at = (sid + 1) * self.sector_size
        return self.data[at:at + self.sector_size]

    def _claim(self, sid):
        if not 0 <= sid < self.sectors:
            _fail('cfb_sector_bounds')
        if sid in self.used:
            _fail('cfb_sector_overlap_or_cycle')
        self.used.add(sid)

    def _chain(self, start, table, unit, available, used, *, size=None, count=None,
               limit=None, mini=False):
        expected = (size + unit - 1) // unit if size is not None else count
        maximum = available if limit is None else min(available, limit)
        if expected is not None and expected > maximum:
            _fail('cfb_chain_limit')
        ids = []
        sid = start
        while sid != END:
            if not 0 <= sid < available or sid >= len(table):
                _fail('cfb_chain_bounds')
            if sid in used:
                _fail('cfb_sector_overlap_or_cycle')
            if len(ids) >= maximum or (expected is not None and len(ids) >= expected):
                _fail('cfb_chain_length')
            used.add(sid)
            ids.append(sid)
            sid = table[sid]
        if expected is not None and len(ids) != expected:
            _fail('cfb_chain_length')
        value = b''.join(self.mini[sid * unit:(sid + 1) * unit] if mini else self._sector(sid) for sid in ids)
        return value if size is None else value[:size]


_NS = 'http://schemas.microsoft.com/office/2006/encryption'
_PNS = 'http://schemas.microsoft.com/office/2006/keyEncryptor/password'
_HASHES = {'SHA256': ('sha256', 32),
           'SHA384': ('sha384', 48), 'SHA512': ('sha512', 64)}
_COMMON = frozenset(('saltSize', 'blockSize', 'keyBits', 'hashSize',
                     'cipherAlgorithm', 'cipherChaining', 'hashAlgorithm', 'saltValue'))
_PASSWORD = frozenset(('spinCount', 'encryptedVerifierHashInput',
                       'encryptedVerifierHashValue', 'encryptedKeyValue'))
_VERIFIER_INPUT = bytes.fromhex('fea7d2763b4b9e79')
_VERIFIER_VALUE = bytes.fromhex('d7aa0f6d3061344e')
_KEY_VALUE = bytes.fromhex('146e0be7abacd0d6')
_HMAC_KEY = bytes.fromhex('5fb2ad010cb9e1f6')
_HMAC_VALUE = bytes.fromhex('a0677f02b22c8433')


def _number(node, name, minimum, maximum):
    text = node.get(name, '')
    if not re.fullmatch(r'[0-9]{1,9}', text):
        _fail('ooxml_encryption_descriptor')
    value = int(text)
    if not minimum <= value <= maximum:
        _fail('ooxml_encryption_resource_limit')
    return value


def _base64(node, name, lengths):
    text = node.get(name, '')
    if not isinstance(text, str) or len(text) > 1024:
        _fail('ooxml_encryption_descriptor')
    try:
        value = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error):
        _fail('ooxml_encryption_descriptor')
    if len(value) not in lengths or base64.b64encode(value).decode('ascii') != text:
        _fail('ooxml_encryption_descriptor')
    return value


def _round_block(length):
    return (length + 15) // 16 * 16


def _params(node, password=False):
    if set(node.attrib) != _COMMON | (_PASSWORD if password else frozenset()):
        _fail('ooxml_encryption_descriptor')
    if (node.get('cipherAlgorithm') != 'AES'
            or node.get('cipherChaining') != 'ChainingModeCBC'
            or node.get('hashAlgorithm') not in _HASHES):
        _fail('ooxml_encryption_suite_unsupported')
    if (_number(node, 'saltSize', 1, 65536) != 16
            or _number(node, 'blockSize', 2, 4096) != 16):
        _fail('ooxml_encryption_suite_unsupported')
    key_bits = _number(node, 'keyBits', 8, 256)
    if key_bits not in (128, 256):
        _fail('ooxml_encryption_suite_unsupported')
    hash_name, hash_size = _HASHES[node.get('hashAlgorithm')]
    if _number(node, 'hashSize', 1, 65536) != hash_size:
        _fail('ooxml_encryption_descriptor')
    result = {'key_bytes': key_bits // 8, 'hash': hash_name,
              'hash_size': hash_size, 'salt': _base64(node, 'saltValue', (16,))}
    if password:
        result['spin'] = _number(node, 'spinCount', 0, MAX_SPIN)
        result['input'] = _base64(node, 'encryptedVerifierHashInput', (16,))
        result['value'] = _base64(node, 'encryptedVerifierHashValue', (_round_block(hash_size),))
    return result


def _descriptor(data):
    if len(data) < 9 or len(data) > MAX_DESCRIPTOR:
        _fail('ooxml_encryption_descriptor_limit')
    if data[:8] != struct.pack('<HHI', 4, 4, 0x40):
        _fail('ooxml_encryption_version_unsupported')
    # UTF-8 only. Refuse declarations and entities before a bounded tree parse.
    try:
        xml = data[8:].decode('utf-8-sig')
    except UnicodeError:
        _fail('ooxml_encryption_descriptor')
    if '<!' in xml or '\x00' in xml:
        _fail('ooxml_encryption_descriptor')
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        _fail('ooxml_encryption_descriptor')
    nodes = list(root.iter())
    if len(nodes) != 6 or any((n.text or '').strip() or (n.tail or '').strip() for n in nodes):
        _fail('ooxml_encryption_descriptor')
    expected = ['keyData', 'dataIntegrity', 'keyEncryptors']
    if (root.tag != '{' + _NS + '}encryption' or root.attrib
            or [n.tag for n in root] != ['{' + _NS + '}' + n for n in expected]):
        _fail('ooxml_encryption_descriptor')
    kd, integrity, encryptors = root
    if list(kd) or list(integrity) or encryptors.attrib or len(encryptors) != 1:
        _fail('ooxml_encryption_descriptor')
    encryptor = encryptors[0]
    if (encryptor.tag != '{' + _NS + '}keyEncryptor'
            or encryptor.attrib != {'uri': _PNS} or len(encryptor) != 1):
        _fail('ooxml_encryption_key_unsupported')
    encrypted_key = encryptor[0]
    if encrypted_key.tag != '{' + _PNS + '}encryptedKey' or list(encrypted_key):
        _fail('ooxml_encryption_key_unsupported')
    if set(integrity.attrib) != {'encryptedHmacKey', 'encryptedHmacValue'}:
        _fail('ooxml_encryption_integrity_required')
    keydata = _params(kd)
    password = _params(encrypted_key, password=True)
    password['key'] = _base64(encrypted_key, 'encryptedKeyValue',
                              (_round_block(keydata['key_bytes']),))
    # Office/msoffcrypto also use a hashSize-length HMAC key. Both encodings
    # are bounded; zero padding of a short HMAC key is equivalent in RFC2104.
    keydata['hmac_key'] = _base64(integrity, 'encryptedHmacKey',
                                  (16, _round_block(keydata['hash_size'])))
    keydata['hmac_value'] = _base64(integrity, 'encryptedHmacValue',
                                    (_round_block(keydata['hash_size']),))
    return keydata, password


def _aes_decrypt(data, key, iv):
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        _fail('ooxml_encryption_crypto_unavailable')
    return AES.new(key, AES.MODE_CBC, iv).decrypt(data)


def _key(iterated, block_key, params):
    value = hashlib.new(params['hash'], iterated + block_key).digest()
    return value.ljust(params['key_bytes'], b'\x36')[:params['key_bytes']]


def _iv(params, block_key):
    return hashlib.new(params['hash'], params['salt'] + block_key).digest()[:16]


def _zip_preflight(data, checkpoint):
    if not data.startswith(b'PK\x03\x04'):
        _fail('ooxml_decrypted_package_invalid')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 512:
                _fail('ooxml_decrypted_package_limit')
            names = set()
            total = 0
            for entry in entries:
                checkpoint()
                if (entry.filename in names or entry.flag_bits & 1
                        or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                        or entry.file_size < 0 or entry.compress_size < 0):
                    _fail('ooxml_decrypted_package_invalid')
                names.add(entry.filename)
                total += entry.file_size
                is_xml = entry.filename.lower().endswith(('.xml', '.rels'))
                if (total > MAX_ZIP_TOTAL or entry.file_size > MAX_ZIP_TOTAL
                        or (is_xml and entry.file_size > MAX_XML)
                        or entry.file_size > max(4096, entry.compress_size * 200)):
                    _fail('ooxml_decrypted_package_limit')
                # Read every member to enforce declared size, CRC and limits
                # before the ordinary exact-format parser can expose any text.
                with archive.open(entry) as member:
                    value = member.read(entry.file_size + 1)
                if len(value) != entry.file_size:
                    _fail('ooxml_decrypted_package_invalid')
            if '[Content_Types].xml' not in names or '_rels/.rels' not in names:
                _fail('ooxml_decrypted_package_invalid')
    except OOXMLPasswordError:
        raise
    except (zipfile.BadZipFile, RuntimeError, ValueError, EOFError, NotImplementedError, zlib.error):
        _fail('ooxml_decrypted_package_invalid')


def prepare_read(data, format, password=None, *, checkpoint=None):
    """Return immutable ZIP bytes and safe metadata, or refuse without text.

    Only a supplied password is attempted, once. An unencrypted ZIP passes
    through; its ordinary format parser remains authoritative. No password,
    derived key, verifier, plaintext or hash of plaintext is returned as metadata.
    """
    check = checkpoint if checkpoint is not None else lambda: None
    check()
    if not isinstance(data, bytes) or len(data) > MAX_INPUT:
        _fail('input_limit')
    if format not in FORMATS:
        _fail('ooxml_encryption_format_unsupported')
    if password is not None and (not isinstance(password, str) or len(password) > 1024):
        _fail('ooxml_password_invalid')
    if not data.startswith(CFB_SIGNATURE):
        return data, None
    streams = _CFB(data).streams
    params, pwd = _descriptor(streams[('EncryptionInfo',)])
    encrypted = streams[('EncryptedPackage',)]
    if len(encrypted) < 24 or (len(encrypted) - 8) % 16:
        _fail('ooxml_encrypted_package_invalid')
    size = struct.unpack_from('<Q', encrypted)[0]
    if not 1 <= size <= MAX_INPUT or len(encrypted) - 8 != _round_block(size):
        _fail('ooxml_encrypted_package_limit')
    if password is None:
        _fail('ooxml_password_required')
    try:
        encoded = password.encode('utf-16le')
    except UnicodeError:
        _fail('ooxml_password_invalid')
    iterated = hashlib.new(pwd['hash'], pwd['salt'] + encoded).digest()
    for iteration in range(pwd['spin']):
        if iteration % 1024 == 0:
            check()
        iterated = hashlib.new(pwd['hash'], struct.pack('<I', iteration) + iterated).digest()
    check()
    verifier = _aes_decrypt(pwd['input'], _key(iterated, _VERIFIER_INPUT, pwd), pwd['salt'])
    expected = _aes_decrypt(pwd['value'], _key(iterated, _VERIFIER_VALUE, pwd), pwd['salt'])
    actual = hashlib.new(pwd['hash'], verifier).digest()
    if not hmac.compare_digest(expected, actual.ljust(len(expected), b'\x00')):
        _fail('ooxml_password_incorrect')
    secret = _aes_decrypt(pwd['key'], _key(iterated, _KEY_VALUE, pwd), pwd['salt'])
    if any(secret[params['key_bytes']:]):
        _fail('ooxml_encrypted_key_invalid')
    secret = secret[:params['key_bytes']]
    hmac_key = _aes_decrypt(params['hmac_key'], secret, _iv(params, _HMAC_KEY))
    expected = _aes_decrypt(params['hmac_value'], secret, _iv(params, _HMAC_VALUE))
    actual = hmac.new(hmac_key, encrypted, params['hash']).digest()
    if not hmac.compare_digest(expected, actual.ljust(len(expected), b'\x00')):
        _fail('ooxml_encryption_integrity_failed')
    check()
    output = bytearray()
    for index, at in enumerate(range(8, len(encrypted), 4096)):
        check()
        output.extend(_aes_decrypt(encrypted[at:at + 4096], secret,
                                   _iv(params, struct.pack('<I', index))))
    clear = bytes(output[:size])
    _zip_preflight(clear, check)
    check()
    return clear, {'encrypted': True, 'encryption': 'ECMA-376-agile-AES-CBC',
                   'password_verified': True, 'data_integrity_verified': True,
                   'decrypted_output_published': False, 'read_only': True}


