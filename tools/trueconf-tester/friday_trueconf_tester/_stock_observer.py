"""Stock custody and ordinary document verification used by TrueConf.

Reproduce from the owner-supplied verifier with packaging/extract_observer.py.
"""


import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import stat
import unicodedata


CANONICAL_STATE = Path(pwd.getpwuid(os.getuid()).pw_dir) / '.local/share/friday-telegram-bot-test'


MAX_JSON = 1024 * 1024


MAX_FILE = 8 * 1024 * 1024


MAX_UPLOAD = 1024 * 1024


UPLOAD_TYPES = {'': 'text/plain', '7z': 'application/x-7z-compressed', 'abw': 'application/x-abiword', 'accdb': 'application/octet-stream', 'arj': 'application/octet-stream', 'bmp': 'image/bmp', 'bz2': 'application/octet-stream', 'cab': 'application/vnd.ms-cab-compressed', 'csv': 'text/csv', 'dbf': 'application/vnd.dbf', 'dif': 'application/octet-stream', 'djv': 'image/vnd.djvu', 'djvu': 'image/vnd.djvu', 'doc': 'application/msword', 'docm': 'application/vnd.ms-word.document.macroEnabled.12', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'dot': 'application/msword', 'dotm': 'application/vnd.ms-word.template.macroEnabled.12', 'dotx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template', 'eml': 'message/rfc822', 'epub': 'application/epub+zip', 'fb2': 'application/octet-stream', 'fodg': 'application/octet-stream', 'fodp': 'application/vnd.oasis.opendocument.presentation', 'fods': 'application/octet-stream', 'fodt': 'application/octet-stream', 'gif': 'image/gif', 'gz': 'application/octet-stream', 'heic': 'image/heic', 'heif': 'image/heif', 'htm': 'text/html', 'html': 'text/html', 'ics': 'text/calendar', 'jpeg': 'image/jpeg', 'jpg': 'image/jpeg', 'json': 'application/json', 'key': 'application/vnd.apple.keynote', 'lzh': 'application/x-lzh', 'markdown': 'text/markdown', 'md': 'text/markdown', 'mdb': 'application/octet-stream', 'mht': 'message/rfc822', 'mhtml': 'message/rfc822', 'mpp': 'application/vnd.ms-project', 'mpt': 'application/vnd.ms-project', 'msg': 'application/octet-stream', 'numbers': 'application/vnd.apple.numbers', 'odb': 'application/vnd.oasis.opendocument.base', 'odf': 'application/vnd.oasis.opendocument.formula', 'odg': 'application/vnd.oasis.opendocument.graphics', 'odm': 'application/vnd.oasis.opendocument.text-master', 'odp': 'application/vnd.oasis.opendocument.presentation', 'ods': 'application/vnd.oasis.opendocument.spreadsheet', 'odt': 'application/vnd.oasis.opendocument.text', 'one': 'application/onenote', 'onepkg': 'application/onenote', 'otg': 'application/vnd.oasis.opendocument.graphics-template', 'otp': 'application/vnd.oasis.opendocument.presentation-template', 'ots': 'application/vnd.oasis.opendocument.spreadsheet-template', 'ott': 'application/vnd.oasis.opendocument.text-template', 'oxps': 'application/oxps', 'pages': 'application/vnd.apple.pages', 'pdf': 'application/pdf', 'png': 'image/png', 'pot': 'application/vnd.ms-powerpoint', 'potm': 'application/vnd.ms-powerpoint.template.macroEnabled.12', 'potx': 'application/vnd.openxmlformats-officedocument.presentationml.template', 'pps': 'application/vnd.ms-powerpoint', 'ppsm': 'application/vnd.ms-powerpoint.slideshow.macroEnabled.12', 'ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow', 'ppt': 'application/vnd.ms-powerpoint', 'pptm': 'application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'pub': 'application/octet-stream', 'rar': 'application/vnd.rar', 'rst': 'text/prs.fallenstein.rst', 'rtf': 'application/rtf', 'slk': 'application/octet-stream', 'stc': 'application/octet-stream', 'sti': 'application/vnd.sun.xml.impress.template', 'stw': 'application/octet-stream', 'svg': 'image/svg+xml', 'sxc': 'application/octet-stream', 'sxi': 'application/vnd.sun.xml.impress', 'sxw': 'application/octet-stream', 'tar': 'application/x-tar', 'tar.bz2': 'application/x-tar', 'tar.gz': 'application/x-tar', 'tar.xz': 'application/x-tar', 'tar.zst': 'application/zstd', 'tbz2': 'application/x-tar', 'tgz': 'application/x-tar', 'tif': 'image/tiff', 'tiff': 'image/tiff', 'tsv': 'text/tab-separated-values', 'txt': 'text/plain', 'txz': 'application/x-tar', 'tzst': 'application/octet-stream', 'vcf': 'text/vcard', 'vdx': 'application/octet-stream', 'vsd': 'application/vnd.visio', 'vsdx': 'application/octet-stream', 'vss': 'application/vnd.visio', 'vssx': 'application/octet-stream', 'vst': 'application/vnd.visio', 'vstx': 'application/octet-stream', 'webp': 'image/webp', 'wpd': 'application/vnd.wordperfect', 'wps': 'application/vnd.ms-works', 'xls': 'application/vnd.ms-excel', 'xlsb': 'application/vnd.ms-excel.sheet.binary.macroEnabled.12', 'xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12', 'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlt': 'application/vnd.ms-excel', 'xltm': 'application/vnd.ms-excel.template.macroEnabled.12', 'xltx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template', 'xml': 'application/xml', 'xps': 'application/vnd.ms-xpsdocument', 'xz': 'application/octet-stream', 'zip': 'application/zip', 'zst': 'application/zstd'}


INPUT_STAT_FIELDS = ('device', 'inode', 'size_bytes', 'uid', 'mtime_ns', 'ctime_ns')


class Refused(Exception):
    pass


class Uncertain(Refused):
    def __init__(self, *args, cause_code='TRANSPORT_OUTCOME_UNKNOWN', phase_code='SEND_API_CALL'):
        super().__init__(*args)
        # Only owned local deadline sites opt in; timing never establishes cause.
        self.cause_code = (cause_code if cause_code in (
            'LOCAL_HTTP_ALARM_DEADLINE', 'LOCAL_HTTP_BODY_DEADLINE',
            'TRANSPORT_TIMEOUT', 'TRANSPORT_URL_FAILURE', 'TRANSPORT_OS_FAILURE')
            else 'TRANSPORT_OUTCOME_UNKNOWN')
        self.phase_code = phase_code if phase_code in (
            'HTTP_WHOLE_CALL', 'HTTP_REQUEST_OR_HEADERS', 'HTTP_RESPONSE_BODY',
            'HTTP_RESPONSE_STATUS', 'HTTP_RESPONSE_ENVELOPE', 'SEND_API_CALL') else 'SEND_API_CALL'


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + '\n').encode()


def no_symlinks(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise Refused('Symlink path refused')
    return path


def secure_dir(path):
    path = no_symlinks(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    s = path.stat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o700:
        raise Refused('Private directory requires owner and mode 0700')
    return path


def safe_read(path, limit=MAX_JSON, private=True):
    path = no_symlinks(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        s = os.fstat(f.fileno())
        if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > limit:
            raise Refused('Unsafe file type, link count, or size')
        if private and (s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o600):
            raise Refused('Private file requires owner and mode 0600')
        data = f.read(limit + 1)
    if len(data) > limit:
        raise Refused('File too large')
    return data


def bounded_capture(value):
    return isinstance(value, dict) and value.get('mode') == 'bounded_capture'


def validate_capture(value):
    fields = {'mode', 'max_bytes', 'filename_equals', 'mime_type_equals', 'caption_equals'}
    if not isinstance(value, dict) or set(value) != fields or not bounded_capture(value):
        raise Refused('Bounded capture requires its exact explicit schema; no hash or wildcard')
    if type(value['max_bytes']) is not int or not 1 <= value['max_bytes'] <= MAX_FILE:
        raise Refused('Bounded capture requires the original finite byte cap')
    name = value['filename_equals']
    try:
        valid_name = (isinstance(name, str) and 1 <= len(name) <= 128
                      and len(name.encode('utf-8')) <= 512
                      and name == unicodedata.normalize('NFC', name)
                      and name == name.strip() and name not in ('.', '..')
                      and '..' not in name and '/' not in name and chr(92) not in name
                      and all(not unicodedata.category(c).startswith('C') for c in name))
    except UnicodeError:
        valid_name = False
    if not valid_name:
        raise Refused('Capture filename requires a safe bounded NFC Unicode basename')
    if (not isinstance(value['mime_type_equals'], str)
            or not re.fullmatch(r'[a-z0-9][a-z0-9!#$&^_.+-]{0,63}/[a-z0-9][a-z0-9!#$&^_.+-]{0,63}', value['mime_type_equals'])):
        raise Refused('Capture requires an exact bounded MIME selector')
    caption = value['caption_equals']
    try:
        valid_caption = (isinstance(caption, str) and len(caption) <= 1024
                         and len(caption.encode('utf-8')) <= 4096 and chr(0) not in caption)
    except UnicodeError:
        valid_caption = False
    if not valid_caption:
        raise Refused('Capture requires an exact bounded caption selector')
    return value


def verify_exact_document_bytes(data, sha, advertised_size, resolved_size, expectation):
    if len(data) != advertised_size or len(data) != resolved_size or sha != expectation['sha256']:
        raise Refused('Downloaded document size/hash mismatch; bytes retained')
    if 'contains_utf8' in expectation:
        try:
            valid = expectation['contains_utf8'] in data.decode('utf-8')
        except UnicodeError:
            valid = False
        if not valid:
            raise Refused('Downloaded document content mismatch')


def validate_document_input(value):
    fields = {'kind', 'path', 'sha256', 'stat', 'filename', 'mime_type', 'caption'}
    if not isinstance(value, dict) or set(value) != fields or value.get('kind') not in ('document', 'photo'):
        raise Refused('Local document/photo input requires the exact pinned schema')
    path = value['path']
    if (not isinstance(path, str) or not path.startswith('/') or path.startswith('//')
            or any(p in ('', '.', '..') for p in path.split('/')[1:])
            or any(ord(c) < 32 or ord(c) == 127 for c in path)):
        raise Refused('Document source requires a simple absolute local path')
    try:
        if len(path.encode('utf-8')) > 4096:
            raise Refused('Document source path is too long')
    except UnicodeError:
        raise Refused('Document source path must be valid UTF-8') from None
    # Operator-only state, oracles and control material are never upload inputs.
    components = path.casefold().split('/')
    if (Path(path).is_relative_to(CANONICAL_STATE) or '.jericho' in components
            or any(re.search(r'oracle|checklist|expected[_ -]?answer|(?:^|[-_])control(?:[-_.]|$)', p)
                   for p in components)
            or any(p in ('tester-token', 'cursor.json', 'cooldown.json', 'observer-stop.json')
                   or p.startswith('friday_user_journey_acceptance') for p in components)):
        raise Refused('Operator-private source material is not an upload input')
    pin = value['stat']
    if (not isinstance(pin, dict) or set(pin) != set(INPUT_STAT_FIELDS)
            or any(type(pin[k]) is not int or pin[k] < 0 for k in INPUT_STAT_FIELDS)
            or pin['uid'] != os.getuid() or pin['inode'] <= 0 or pin['size_bytes'] > MAX_UPLOAD
            or not isinstance(value['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', value['sha256'])):
        raise Refused('Document input requires owner, identity, timestamps, size and exact SHA256 pins')
    name = value['filename']
    try:
        valid_name = (isinstance(name, str) and 1 <= len(name) <= 128
                      and len(name.encode('utf-8')) <= 512
                      and name == unicodedata.normalize('NFC', name)
                      and name[0].isalnum()
                      and all(c.isalnum() or c in '_.-' for c in name)
                      and '..' not in name)
    except UnicodeError:
        valid_name = False
    if not valid_name:
        raise Refused('Multipart filename requires a bounded NFC Unicode alphanumeric basename')
    if (not isinstance(value['mime_type'], str)
            or not re.fullmatch(r'[a-z0-9][a-z0-9!#$&^_.+-]{0,63}/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,63}', value['mime_type'])):
        raise Refused('Multipart MIME type requires bounded ASCII type/subtype')
    extension = next((ext for ext in sorted(UPLOAD_TYPES, key=len, reverse=True) if ext and value['filename'].lower().endswith('.' + ext)), '')
    if (('.' in value['filename'] and not extension)
            or extension not in UPLOAD_TYPES
            or value['mime_type'] != UPLOAD_TYPES[extension]):
        raise Refused('Document input requires one exact pinned catalogue extension/MIME pair')
    if value['kind'] == 'photo' and (extension not in ('png', 'jpg', 'jpeg')
            or not 1 <= pin['size_bytes'] <= MAX_UPLOAD):
        raise Refused('Photo input requires bounded pinned PNG or JPEG bytes')
    caption = value['caption']
    if not isinstance(caption, str) or len(caption) > 1024 or '\x00' in caption:
        raise Refused('Plain caption requires 0-1024 Unicode characters')
    try:
        if len(caption.encode('utf-16-le')) // 2 > 1024:
            raise Refused('Caption UTF-16 unit bound exceeded')
        if len(caption.encode('utf-8')) > 4096:
            raise Refused('Caption UTF-8 bound exceeded')
    except UnicodeError:
        raise Refused('Caption must be valid UTF-8') from None
    return value


def input_stat(s):
    return dict(zip(INPUT_STAT_FIELDS, (s.st_dev, s.st_ino, s.st_size, s.st_uid,
                                       s.st_mtime_ns, s.st_ctime_ns)))


def read_document_input(value, guard):
    """Open every path component relative to its parent FD; never follow links.

    The same final FD supplies both reads and all before/after metadata. A second
    root-relative open checks that the pinned path still names that same file.
    """
    validate_document_input(value)
    def open_source():
        current = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            parts = value['path'].split('/')[1:]
            for part in parts[:-1]:
                following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                    dir_fd=current)
                os.close(current)
                current = following
            return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                           dir_fd=current)
        finally:
            os.close(current)
    def check(fd):
        s = os.fstat(fd)
        if (not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_uid != os.getuid()
                or input_stat(s) != value['stat']):
            raise Refused('Document source identity or metadata drift; nothing sent')
        return s
    def read(fd):
        chunks, total = [], 0
        while True:
            guard()
            part = os.read(fd, min(65536, MAX_UPLOAD + 1 - total))
            if not part:
                break
            chunks.append(part)
            total += len(part)
            if total > MAX_UPLOAD:
                raise Refused('Document input exceeds original byte cap')
        return b''.join(chunks)
    try:
        guard()
        fd = open_source()
        try:
            check(fd)
            data = read(fd)
            check(fd)
            if len(data) != value['stat']['size_bytes'] or digest(data) != value['sha256']:
                raise Refused('Document input size or hash drift; nothing sent')
            os.lseek(fd, 0, os.SEEK_SET)
            reread = read(fd)
            check(fd)
            if len(reread) != len(data) or digest(reread) != value['sha256']:
                raise Refused('Document input changed during verification; nothing sent')
            second = open_source()
            try:
                check(second)
            finally:
                os.close(second)
            guard()
            return data
        finally:
            os.close(fd)
    except OSError:
        raise Refused('Document source could not be safely opened; nothing sent') from None


class Store:
    def __init__(self, root):
        self.root = secure_dir(root)
        self.runs = secure_dir(self.root / 'runs')
        self.captures = secure_dir(self.root / 'updates')
        self.downloads = secure_dir(self.root / 'downloads')

    def write(self, path, data):
        path = no_symlinks(path)
        if path.exists():
            safe_read(path, max(MAX_JSON, MAX_FILE, len(data)))
        tmp = path.with_name(path.name + '.new')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            fd = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            if tmp.exists():
                tmp.unlink()

    def put(self, path, value):
        self.write(path, encoded(value))

    def get(self, path, default=None):
        return json.loads(safe_read(path), object_pairs_hook=unique_object) if path.exists() else default

    @contextlib.contextmanager
    def lock(self, path=None, create=True):
        path = no_symlinks(path or self.root / 'consumer.lock')
        fd = os.open(path, os.O_RDWR | (os.O_CREAT if create else 0) | os.O_NOFOLLOW, 0o600)
        try:
            s = os.fstat(fd)
            if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o600:
                raise Refused('Unsafe lock file')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refused('Another tester consumer is active') from None
            yield fd
        finally:
            os.close(fd)

    def run_path(self, name):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', name):
            raise Refused('Run ID requires 1-64 simple characters')
        return self.runs / (name + '.json')


def unique_object(pairs):
    """Reject ambiguous duplicate keys in operator proofs and rejected run bytes."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused('Duplicate JSON key in rejection evidence')
        result[key] = value
    return result


def validate_scenario_steps(scenario):
    """Validate plan structure after the caller validates its transport identity."""
    for field, low, high in [('deadline_seconds', 10, 1800), ('max_updates', 1, 200), ('pace_seconds', 1, 60)]:
        if type(scenario.get(field)) is not int or not low <= scenario[field] <= high:
            raise Refused('Scenario bound invalid: ' + field)
    steps = scenario.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
        raise Refused('Scenario requires 1-8 finite steps')
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise Refused('Scenario step requires an object')
        text = step.get('request')
        expected = step.get('observe', {})
        if 'input' in step:
            if set(step) != {'input', 'observe'}:
                raise Refused('Document step permits only input and operator-only observe')
            validate_document_input(step['input'])
        elif not isinstance(text, str) or not 1 <= len(text) <= 4000:
            raise Refused('Step request must be bounded text')
        if not isinstance(expected, dict):
            raise Refused('Unsupported observation schema')
        if 'mode' in expected:
            raise Refused('Unsupported observation schema')
        if set(expected) - {'text_equals', 'text_contains', 'documents'}:
            raise Refused('Unsupported observation schema')
        if 'text_equals' in expected and 'text_contains' in expected:
            raise Refused('Choose one precise text observation')
        if not any(expected.get(k) for k in ('text_equals', 'text_contains', 'documents')):
            raise Refused('First reply or quiet is not an oracle')
        for key in ('text_equals', 'text_contains'):
            if key in expected and (not isinstance(expected[key], str) or not 1 <= len(expected[key]) <= 8000):
                raise Refused('Text observation must be nonempty and bounded')
        docs = expected.get('documents', [])
        if not isinstance(docs, list) or len(docs) > 4:
            raise Refused('At most four expected documents per step')
        for doc in docs:
            if isinstance(doc, dict) and 'mode' in doc:
                raise Refused('Unsupported document observation schema')
            if not isinstance(doc, dict) or not isinstance(doc.get('sha256'), str) or not re.fullmatch('[a-f0-9]{64}', doc['sha256']) or type(doc.get('max_bytes')) is not int or not 1 <= doc['max_bytes'] <= MAX_FILE:
                raise Refused('Document requires exact hash and byte bound')
            if not isinstance(doc.get('caption_equals'), str) or len(doc['caption_equals']) > 1024:
                raise Refused('Document requires bounded exact caption')
            if 'contains_utf8' in doc and (not isinstance(doc['contains_utf8'], str) or len(doc['contains_utf8']) > 10000):
                raise Refused('Document content check invalid')
    return scenario


def ordinary_document_response_failures(output, observations):
    if (not isinstance(output, dict)
            or set(output) != {'filename', 'mime_type'}
            or output['mime_type'] not in UPLOAD_TYPES.values()):
        raise Refused('Declared catalogue document output required')
    if output['filename'] is not None:
        validate_capture(dict(mode='bounded_capture', max_bytes=MAX_FILE,
            filename_equals=output['filename'], mime_type_equals=output['mime_type'], caption_equals=''))
        extension = output['filename'].rsplit('.', 1)[-1].lower()
        if '.' not in output['filename'] or UPLOAD_TYPES.get(extension) != output['mime_type']:
            raise Refused('Declared output extension/MIME mismatch')

    documents = [o for o in observations if o.get('kind') == 'document']
    if len(documents) != 1:
        return ['EXPECTED_DOCUMENT_MISSING']
    actual = documents[0].get('advertised_document', {})
    return [] if (actual.get('mime_type') == output['mime_type']
                  and (output['filename'] is None
                       or actual.get('file_name') == output['filename'])) else ['EXPECTED_DOCUMENT_METADATA_MISMATCH']


def observation_ready(run):
    expected = run['scenario']['steps'][run['step']]['observe']
    return ((not any(k in expected for k in ('text_equals', 'text_contains')) or any(o['kind'] == 'text' for o in run['observations']))
            and sum(o['kind'] == 'document' for o in run['observations']) == len(expected.get('documents', [])))
