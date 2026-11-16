"""Bounded inert EML/ICS/VCF reading and narrow new-file create/copy-edit.

All values are stored claims. No transport, import, resource lookup, recurrence
expansion, timezone conversion, HTML rendering or attachment execution occurs.
"""
from __future__ import annotations

import base64
import binascii
import codecs
from datetime import datetime
from email import policy
from email.errors import MessageError
from email.header import Header, decode_header
from email.message import EmailMessage
from email.parser import BytesParser
import hashlib
import json
import quopri
import re

MAX_BYTES = 1_000_000
MAX_PARTS = 128
MAX_DEPTH = 8
MAX_HEADERS = 200
MAX_HEADER_BYTES = 65_536
MAX_DECODED = 1_000_000
MAX_TEXT = 400_000
MAX_LINES = 4096
MAX_COMPONENTS = 256
FORMATS = frozenset({'eml', 'ics', 'vcf'})
CHARSETS = {
    'utf-8': 'utf-8', 'utf8': 'utf-8', 'us-ascii': 'ascii', 'ascii': 'ascii',
    'iso-8859-1': 'latin-1', 'latin1': 'latin-1', 'latin-1': 'latin-1',
    'windows-1252': 'cp1252', 'cp1252': 'cp1252',
    'windows-1251': 'cp1251', 'cp1251': 'cp1251', 'koi8-r': 'koi8-r',
    'iso-8859-2': 'iso8859-2',
}
HEADER_FIELDS = frozenset({
    'subject', 'from', 'to', 'cc', 'bcc', 'date', 'message-id',
    'in-reply-to', 'references', 'reply-to', 'mime-version',
})
DATE_PROPERTIES = frozenset({'DTSTART', 'DTEND', 'DUE', 'RECURRENCE-ID', 'DTSTAMP'})
TEXT_PROPERTIES = frozenset({
    'SUMMARY', 'DESCRIPTION', 'LOCATION', 'COMMENT', 'CATEGORIES', 'CONTACT',
    'FN', 'NICKNAME', 'ORG', 'TITLE', 'ROLE', 'NOTE', 'EMAIL', 'TEL', 'UID', 'URL', 'IMPP',
})
BINARY_PROPERTIES = frozenset({'PHOTO', 'LOGO', 'SOUND', 'KEY'})
TOKEN = re.compile(r'^[A-Za-z0-9-]+$')


class CommunicationError(ValueError):
    def __init__(self, code):
        self.code = code if isinstance(code, str) else 'malformed_input'
        super().__init__(self.code)


class DocumentText(str):
    def __new__(cls, value, metadata):
        result = super().__new__(cls, value)
        result.extraction_metadata = metadata
        result.scoped_metadata = metadata
        return result


def _fail(code):
    raise CommunicationError(code)


def _checkpoint(checkpoint):
    if checkpoint is not None:
        checkpoint()


def _input(data, format):
    if type(data) is not bytes or not data or len(data) > MAX_BYTES:
        _fail('input_limit')
    if format not in FORMATS:
        _fail('unsupported_format')


def _text(value, code='invalid_text', limit=100_000, newlines=False):
    if type(value) is not str or len(value.encode('utf-8')) > limit:
        _fail(code)
    if newlines and '\r' in value.replace('\r\n', ''):
        _fail(code)
    allowed = '\t\n\r' if newlines else '\t'
    for char in value:
        number = ord(char)
        if number == 127 or number < 32 and char not in allowed:
            _fail(code)
    if not newlines and ('\r' in value or '\n' in value):
        _fail(code)
    return value


def _decode_header(value):
    try:
        units = decode_header(value)
        result = ''
        for chunk, charset in units:
            if isinstance(chunk, str):
                result += chunk
                continue
            if charset is None:
                charset = 'ascii'
            try:
                codec = codecs.lookup(charset).name
            except (LookupError, TypeError):
                _fail('unsupported_header_charset')
            result += chunk.decode(codec, 'strict')
    except CommunicationError:
        raise
    except (UnicodeError, LookupError, MessageError, ValueError):
        _fail('malformed_header_encoding')
    return _text(result, 'malformed_header_encoding', 16_384)


def _header_separator(data):
    match = re.search(br'\r?\n\r?\n', data)
    if match is None or match.start() > MAX_HEADER_BYTES:
        _fail('malformed_mime_headers')
    raw = data[:match.start()]
    if b'\r' in raw.replace(b'\r\n', b'') or b'\x00' in raw:
        _fail('malformed_mime_headers')
    lines = raw.replace(b'\r\n', b'\n').split(b'\n')
    count = 0
    for line in lines:
        if not line or len(line) > 998 or any(c < 32 and c != 9 or c == 127 for c in line):
            _fail('malformed_mime_headers')
        if line[:1] in (b' ', b'\t'):
            if not count:
                _fail('malformed_mime_headers')
        else:
            name, colon, _ = line.partition(b':')
            if not colon or not re.fullmatch(br'[!-9;-~]+', name):
                _fail('malformed_mime_headers')
            count += 1
            if count > MAX_HEADERS:
                _fail('mime_header_limit')
    return match


def _transfer(part):
    encoding = (part.get('Content-Transfer-Encoding') or '7bit').lower().strip()
    if encoding not in ('7bit', '8bit', 'binary', 'base64', 'quoted-printable'):
        _fail('unsupported_transfer_encoding')
    if encoding in ('8bit', 'binary'):
        try:
            decoded = part.get_payload(decode=True)
        except (MessageError, UnicodeError, ValueError):
            _fail('malformed_mime_payload')
        if not isinstance(decoded, bytes):
            _fail('malformed_mime_payload')
        if len(decoded) > MAX_DECODED:
            _fail('decoded_payload_limit')
        return decoded, encoding
    try:
        raw = part.get_payload(decode=False)
        if not isinstance(raw, str):
            _fail('malformed_mime_payload')
        raw = raw.encode('ascii', 'surrogateescape')
    except (UnicodeError, ValueError):
        _fail('malformed_mime_payload')
    if encoding == '7bit' and any(c > 127 for c in raw):
        _fail('invalid_transfer_encoding')
    if encoding == 'base64':
        compact = re.sub(br'[ \t\r\n]', b'', raw)
        try:
            decoded = base64.b64decode(compact, validate=True)
        except (ValueError, binascii.Error):
            _fail('invalid_transfer_encoding')
    elif encoding == 'quoted-printable':
        if b'\r' in raw.replace(b'\r\n', b''):
            _fail('invalid_transfer_encoding')
        if re.search(br'=(?![0-9A-Fa-f]{2}|\r?\n)', raw):
            _fail('invalid_transfer_encoding')
        decoded = quopri.decodestring(raw)
    else:
        decoded = raw
    if len(decoded) > MAX_DECODED:
        _fail('decoded_payload_limit')
    return decoded, encoding


def _parse_eml(data, checkpoint=None):
    _input(data, 'eml')
    _header_separator(data)
    try:
        message = BytesParser(policy=policy.default).parsebytes(data)
    except (MessageError, UnicodeError, ValueError, IndexError, RecursionError):
        _fail('malformed_mime')
    headers = {}
    other = []
    for name, value in message.items():
        lower = name.lower()
        if getattr(value, 'defects', ()):
            _fail('malformed_mime_headers')
        if lower in HEADER_FIELDS:
            headers.setdefault(lower, []).append(_decode_header(str(value)))
        else:
            other.append({'name': lower, 'stored_value_suppressed': True})
    if message.defects:
        _fail('malformed_mime')
    state = {'parts': 0, 'decoded': 0, 'text': 0}
    records = []
    payloads = {}

    def visit(part, depth, path, attachment_ancestor=False):
        _checkpoint(checkpoint)
        state['parts'] += 1
        if state['parts'] > MAX_PARTS or depth > MAX_DEPTH:
            _fail('mime_structure_limit')
        if part.defects:
            _fail('malformed_mime')
        for name in ('Content-Type', 'Content-Transfer-Encoding', 'Content-Disposition'):
            if len(part.get_all(name, ())) > 1:
                _fail('duplicate_mime_header')
        content_type = part.get_content_type().lower()
        maintype, _, subtype = content_type.partition('/')
        try:
            filename = part.get_filename()
            if filename is not None:
                filename = _text(_decode_header(filename), 'invalid_attachment_name', 4096)
        except (MessageError, UnicodeError, ValueError):
            _fail('invalid_attachment_name')
        is_attachment = (attachment_ancestor or part.get_content_disposition() == 'attachment'
                         or filename is not None)
        item = {
            'part': len(records) + 1, 'path': list(path), 'depth': depth,
            'content_type': content_type, 'disposition': part.get_content_disposition(),
            'multipart': part.is_multipart(), 'payload_executed': False,
            'remote_resources_fetched': False,
            'filename': filename, 'attachment_context': is_attachment,
        }
        records.append(item)
        if part.is_multipart():
            children = list(part.iter_parts()) if hasattr(part, 'iter_parts') else list(part.get_payload())
            if not children or maintype not in ('multipart', 'message'):
                _fail('malformed_mime_structure')
            if is_attachment:
                item.update(text=None, text_status='multipart_attachment_metadata_only',
                            arbitrary_payload_emitted=False,
                            decoded_payload_metadata='not_available_for_container')
            for number, child in enumerate(children, 1):
                visit(child, depth + 1, path + [number], is_attachment)
            return
        decoded, transfer = _transfer(part)
        state['decoded'] += len(decoded)
        if state['decoded'] > MAX_DECODED:
            _fail('decoded_payload_limit')
        payloads[tuple(path)] = decoded
        item.update(decoded_bytes=len(decoded), decoded_sha256=hashlib.sha256(decoded).hexdigest(),
                    transfer_encoding=transfer, filename=filename, text=None,
                    arbitrary_payload_emitted=False)
        if maintype == 'text' and subtype != 'html' and not is_attachment:
            charset = part.get_content_charset()
            try:
                codec = CHARSETS.get((charset or 'us-ascii').lower())
                if codec is None:
                    raise LookupError()
                text = decoded.decode(codec, 'strict')
                _text(text, 'invalid_text_payload', MAX_BYTES + 1, newlines=True)
            except (LookupError, UnicodeError):
                item['text_status'] = 'unsupported_charset_or_strict_decode_failed'
                item['partial_semantics'] = True
                return
            state['text'] += len(text.encode('utf-8'))
            if state['text'] > MAX_TEXT:
                _fail('decoded_text_limit')
            item['text'] = text
            item['text_status'] = 'stored_text_decoded'
        elif subtype == 'html':
            item.update(text_status='html_not_rendered', active_material_retained_as_metadata=True)
        else:
            item['text_status'] = 'not_applicable_or_attachment_not_opened'
    visit(message, 0, [])
    attachment_part_numbers = [row['part'] for row in records
                               if row['disposition'] == 'attachment' or row.get('filename') is not None]
    result = {
        'format': 'eml', 'stored_claims_only': True, 'headers': headers,
        'other_header_metadata': other, 'parts': records,
        'body_part_numbers': [row['part'] for row in records if row.get('text') is not None],
        'attachments': attachment_part_numbers,
        'attachment_count': len(attachment_part_numbers),
        'attachment_part_numbers': attachment_part_numbers,
        'semantics': {
            'html_rendered': False, 'attachments_opened_or_extracted': False,
            'links_followed': False, 'message_sent': False,
            'unsupported_or_failed_text_decode_remains_in_part_metadata': True,
        },
    }
    coverage = 'stored_MIME_headers_text_bodies_and_attachment_metadata; HTML_not_rendered; attachment_payloads_not_emitted; no_transport_or_remote_fetch'
    return result, coverage, payloads


def _read_eml(data, checkpoint=None):
    result, coverage, _ = _parse_eml(data, checkpoint)
    return result, coverage


def extract_eml_attachment(data, part_path, expected_decoded_sha256, *, checkpoint=None):
    if (type(part_path) is not list or not 0 <= len(part_path) <= MAX_DEPTH
            or any(type(number) is not int or not 1 <= number <= MAX_PARTS for number in part_path)):
        _fail('part_path_invalid')
    if type(expected_decoded_sha256) is not str or re.fullmatch(r'[0-9a-f]{64}', expected_decoded_sha256) is None:
        _fail('decoded_hash_required')
    result, _, payloads = _parse_eml(data, checkpoint)
    selected = [row for row in result['parts'] if row['path'] == part_path]
    if not selected:
        _fail('attachment_not_found')
    row = selected[0]
    if row['multipart']:
        _fail('attachment_container_not_leaf')
    if not row['attachment_context']:
        _fail('not_an_attachment')
    if row['decoded_sha256'] != expected_decoded_sha256:
        _fail('decoded_hash_mismatch')
    payload = payloads[tuple(part_path)]
    if len(payload) != row['decoded_bytes'] or hashlib.sha256(payload).hexdigest() != expected_decoded_sha256:
        _fail('decoded_hash_mismatch')
    _checkpoint(checkpoint)
    metadata = {key: row[key] for key in (
        'part', 'path', 'depth', 'content_type', 'disposition', 'filename',
        'attachment_context', 'transfer_encoding', 'decoded_bytes', 'decoded_sha256',
    )}
    return payload, metadata


def _physical(data):
    if b'\x00' in data:
        _fail('malformed_lines')
    lines = []
    start = 0
    spans = [(match.start(), match.end(), match.group()) for match in re.finditer(br'\r\n|\r|\n', data)]
    if start < len(data) and (not spans or spans[-1][1] != len(data)):
        spans.append((len(data), len(data), b''))
    for end, stop, newline in spans:
        raw = data[start:end]
        if len(raw) > 4096:
            _fail('physical_line_limit')
        try:
            text = raw.decode('utf-8', 'strict')
        except UnicodeDecodeError:
            _fail('utf8_required')
        lines.append({'start': start, 'end': stop, 'text': text, 'newline': newline})
        start = stop
        if len(lines) > MAX_LINES:
            _fail('physical_line_limit')
    if not lines:
        _fail('empty_input')
    return lines


def _logical(data):
    result = []
    for line in _physical(data):
        text = line['text']
        if not text:
            continue
        if text[:1] in (' ', '\t'):
            if not result:
                _fail('orphan_fold')
            result[-1]['text'] += text[1:]
            result[-1]['end'] = line['end']
            result[-1]['newline'] = line['newline']
        else:
            result.append(dict(line))
        if len(result[-1]['text'].encode('utf-8')) > 65_536:
            _fail('logical_line_limit')
    return result


def _split_unquoted(value, delimiter):
    result = []
    start = 0
    quote = False
    for index, char in enumerate(value):
        if char == '"':
            quote = not quote
        elif char == delimiter and not quote:
            result.append(value[start:index])
            start = index + 1
    if quote:
        _fail('malformed_parameters')
    result.append(value[start:])
    return result


def _property(line):
    # Quoting applies to the name/parameter section only. Property values are
    # arbitrary stored text and may contain literal, unmatched double quotes.
    quote = False
    separator = None
    for index, char in enumerate(line['text']):
        if char == '"':
            quote = not quote
        elif char == ':' and not quote:
            separator = index
            break
    if separator is None:
        _fail('malformed_property')
    left = line['text'][:separator]
    value = line['text'][separator + 1:]
    fields = _split_unquoted(left, ';')
    full_name = fields.pop(0)
    group = ''
    name = full_name
    if '.' in full_name:
        group, name = full_name.rsplit('.', 1)
    if not TOKEN.fullmatch(name) or group and not TOKEN.fullmatch(group):
        _fail('malformed_property_name')
    params = []
    for field in fields:
        if '=' not in field:
            _fail('malformed_parameters')
        key, raw = field.split('=', 1)
        if not TOKEN.fullmatch(key) or not raw:
            _fail('malformed_parameters')
        values = []
        for item in _split_unquoted(raw, ','):
            if len(item) >= 2 and item[0] == item[-1] == '"':
                item = item[1:-1]
            if not item or any(ord(c) < 32 or ord(c) == 127 for c in item):
                _fail('malformed_parameters')
            values.append(item)
        params.append({'name': key.upper(), 'values': values})
    return dict(line, group=group.upper(), name=name.upper(), params=params, raw_value=value)


def _unescape(value):
    result = []
    index = 0
    while index < len(value):
        if value[index] != '\\':
            result.append(value[index])
            index += 1
            continue
        index += 1
        if index >= len(value):
            _fail('malformed_text_escape')
        char = value[index]
        if char in ('n', 'N'):
            result.append('\n')
        elif char in ('\\', ',', ';', ':', '"'):
            result.append(char)
        else:
            _fail('unsupported_text_escape')
        index += 1
    return ''.join(result)


def _params(prop, name):
    return [value for param in prop['params'] if param['name'] == name for value in param['values']]


def _public_property(prop):
    name = prop['name']
    row = {'name': name, 'group': prop['group'] or None, 'parameters': prop['params'],
           'raw_value': prop['raw_value']}
    encodings = [value.lower() for value in _params(prop, 'ENCODING')]
    value_types = [value.lower() for value in _params(prop, 'VALUE')]
    if name in BINARY_PROPERTIES or any(value in ('b', 'base64') for value in encodings) or 'binary' in value_types:
        row.update(raw_value=None, value=None, stored_value_suppressed=True,
                   stored_value_utf8_bytes=len(prop['raw_value'].encode('utf-8')))
    elif name in TEXT_PROPERTIES or name.startswith('X-'):
        row['value'] = _unescape(prop['raw_value'])
    else:
        row['value'] = prop['raw_value']
    if name in DATE_PROPERTIES:
        row['date_time'] = _date_value(prop)
    if name in ('RRULE', 'EXRULE'):
        row['recurrence'] = _recurrence(prop['raw_value'])
        row['occurrences_generated'] = False
    return row


def _date_value(prop):
    raw = prop['raw_value']
    tzids = _params(prop, 'TZID')
    values = _params(prop, 'VALUE')
    if len(tzids) > 1 or len(values) > 1:
        _fail('ambiguous_date_time')
    kind = None
    if re.fullmatch(r'[0-9]{8}', raw):
        fmt = '%Y%m%d'
        kind = 'date'
    elif re.fullmatch(r'[0-9]{8}T[0-9]{6}Z?', raw):
        fmt = '%Y%m%dT%H%M%SZ' if raw.endswith('Z') else '%Y%m%dT%H%M%S'
        kind = 'utc_datetime' if raw.endswith('Z') else ('named_timezone_datetime' if tzids else 'floating_datetime')
    else:
        _fail('invalid_date_time')
    try:
        datetime.strptime(raw, fmt)
    except ValueError:
        _fail('invalid_date_time')
    declared = values[0].upper() if values else None
    if (declared not in (None, 'DATE', 'DATE-TIME')
            or kind == 'date' and (tzids or declared == 'DATE-TIME')
            or kind != 'date' and declared == 'DATE'
            or kind == 'utc_datetime' and tzids):
        _fail('ambiguous_date_time')
    return {'kind': kind, 'stored_value': raw, 'tzid': tzids[0] if tzids else None,
            'utc_instant': None, 'timezone_conversion': 'not_performed',
            'semantics': 'explicit_Z_marker_retained_without_conversion' if kind == 'utc_datetime' else 'stored_local_or_date_value_only'}


def _recurrence(raw):
    rule = {}
    for field in raw.split(';'):
        if '=' not in field:
            _fail('invalid_recurrence')
        key, value = field.split('=', 1)
        if not TOKEN.fullmatch(key) or not value or key.upper() in rule:
            _fail('invalid_recurrence')
        rule[key.upper()] = value
    if rule.get('FREQ') not in ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'HOURLY', 'MINUTELY', 'SECONDLY'):
        _fail('invalid_recurrence')
    if 'COUNT' in rule and 'UNTIL' in rule:
        _fail('ambiguous_recurrence')
    return {'stored_rule': rule, 'expanded': False, 'occurrences': None}


def _components(lines, format):
    roots = []
    stack = []
    count = 0
    for index, line in enumerate(lines):
        prop = _property(line)
        prop['logical_index'] = index
        name = prop['name']
        if name in ('BEGIN', 'END'):
            if prop['params'] or prop['group']:
                _fail('malformed_component')
            value = prop['raw_value'].upper()
            if not TOKEN.fullmatch(value):
                _fail('malformed_component')
            if name == 'BEGIN':
                count += 1
                if count > MAX_COMPONENTS or len(stack) >= 16:
                    _fail('component_limit')
                node = {'type': value, 'properties': [], 'children': [], 'logical_index': index}
                if stack:
                    stack[-1]['children'].append(node)
                else:
                    roots.append(node)
                stack.append(node)
            else:
                if not stack or stack[-1]['type'] != value:
                    _fail('mismatched_component')
                stack.pop()
            continue
        if not stack:
            _fail('property_outside_component')
        stack[-1]['properties'].append(prop)
    if stack or not roots:
        _fail('unclosed_component')
    if format == 'ics' and (len(roots) != 1 or roots[0]['type'] != 'VCALENDAR'):
        _fail('calendar_required')
    if format == 'vcf' and (len(roots) > 32 or any(root['type'] != 'VCARD' for root in roots)):
        _fail('vcard_required')
    return roots


def _export_node(node):
    return {'type': node['type'],
            'properties': [_public_property(prop) for prop in node['properties']],
            'components': [_export_node(child) for child in node['children']]}


def _read_ics(data, checkpoint=None):
    _input(data, 'ics')
    lines = _logical(data)
    root = _components(lines, 'ics')[0]
    _checkpoint(checkpoint)
    versions = [p for p in root['properties'] if p['name'] == 'VERSION']
    if len(versions) != 1 or versions[0]['raw_value'] != '2.0':
        _fail('unsupported_calendar_version')
    tzids = set()
    events = []

    def walk(node):
        _checkpoint(checkpoint)
        if node['type'] == 'VTIMEZONE':
            for prop in node['properties']:
                if prop['name'] == 'TZID':
                    tzids.add(_unescape(prop['raw_value']))
        if node['type'] == 'VEVENT':
            event = {'uid': [], 'summary': [], 'date_time_properties': [], 'recurrence_properties': []}
            for prop in node['properties']:
                public = _public_property(prop)
                if prop['name'] in ('UID', 'SUMMARY'):
                    event[prop['name'].lower()].append(public['value'])
                if prop['name'] in DATE_PROPERTIES:
                    event['date_time_properties'].append({'name': prop['name'], **public['date_time']})
                if prop['name'] in ('RRULE', 'RDATE', 'EXDATE', 'EXRULE'):
                    event['recurrence_properties'].append({'name': prop['name'], 'stored_value': prop['raw_value'],
                                                           'occurrences_generated': False})
            events.append(event)
        for child in node['children']:
            walk(child)
    walk(root)
    for event in events:
        for row in event['date_time_properties']:
            if row['tzid'] is not None:
                row['timezone_definition_present'] = row['tzid'] in tzids
                row['timezone_resolution'] = 'TZID_retained_not_resolved'
    result = {
        'format': 'ics', 'stored_claims_only': True, 'calendar': _export_node(root),
        'events': events, 'declared_timezone_ids': sorted(tzids),
        'semantics': {'occurrences_generated': False, 'utc_instants_computed': False,
                      'timezones_resolved': False, 'calendar_imported': False,
                      'unknown_timezone_or_recurrence_semantics_not_guessed': True},
    }
    return result, 'stored_calendar_components_repeated_fields_dates_timezones_and_recurrence; no_occurrence_expansion_or_UTC_conversion; no_import'


def _read_vcf(data, checkpoint=None):
    _input(data, 'vcf')
    lines = _logical(data)
    roots = _components(lines, 'vcf')
    cards = []
    for root in roots:
        _checkpoint(checkpoint)
        for prop in root['properties']:
            encodings = [value.lower() for value in _params(prop, 'ENCODING')]
            if len(encodings) > 1 or any(value not in ('b', 'base64') for value in encodings):
                _fail('unsupported_vcard_encoding')
        versions = [p for p in root['properties'] if p['name'] == 'VERSION']
        names = [p for p in root['properties'] if p['name'] == 'FN']
        if len(versions) != 1 or versions[0]['raw_value'] not in ('3.0', '4.0'):
            _fail('unsupported_vcard_version')
        if len(names) != 1:
            _fail('formatted_name_required')
        cards.append(_export_node(root))
    result = {
        'format': 'vcf', 'stored_claims_only': True, 'contacts': cards,
        'semantics': {'repeated_and_typed_properties_preserved': True,
                      'binary_property_payloads_suppressed': True,
                      'uris_and_remote_resources_fetched': False, 'contacts_imported': False},
    }
    return result, 'stored_vCard_repeated_and_typed_properties; binary_payload_values_suppressed; no_URI_fetch_or_contact_import'


def extract_communication(data, format, *, checkpoint=None):
    if format == 'eml':
        result, coverage = _read_eml(data, checkpoint)
    elif format == 'ics':
        result, coverage = _read_ics(data, checkpoint)
    elif format == 'vcf':
        result, coverage = _read_vcf(data, checkpoint)
    else:
        _fail('unsupported_format')
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if len(text.encode('utf-8')) > MAX_BYTES:
        _fail('extracted_text_limit')
    return DocumentText(text, {'coverage': coverage, 'stored_claims_only': True,
                               'format': format, 'side_effects': 'none'})


def _escape(value):
    value = _text(value, 'invalid_text', 65_536, newlines=True)
    return value.replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def _fold(raw, newline=b'\r\n'):
    data = raw.encode('utf-8')
    lines = []
    current = b''
    limit = 75
    for char in raw:
        encoded = char.encode('utf-8')
        if len(current) + len(encoded) > limit:
            lines.append(current)
            current = b' ' + encoded
            limit = 74
        else:
            current += encoded
    lines.append(current)
    return newline.join(lines)


def _created(lines):
    output = b'\r\n'.join(lines) + b'\r\n'
    if len(output) > MAX_BYTES:
        _fail('output_limit')
    return output


def _field(spec, name, required=True):
    value = spec.get(name)
    if required and (type(value) is not str or not value):
        _fail('create_schema')
    if value is not None:
        _text(value, 'invalid_field', 65_536, newlines=name in ('text', 'description', 'note'))
    return value


def create_eml(spec, *, checkpoint=None):
    if type(spec) is not dict or set(spec) != {'from', 'to', 'subject', 'text'}:
        _fail('create_schema')
    sender = _field(spec, 'from')
    recipients = spec['to']
    if type(recipients) is not list or not 1 <= len(recipients) <= 100 or any(type(x) is not str or not x for x in recipients):
        _fail('create_schema')
    for value in [sender, *recipients]:
        _text(value, 'invalid_address', 4096)
    message = EmailMessage(policy=policy.SMTP)
    message['From'] = sender
    message['To'] = ', '.join(recipients)
    message['Subject'] = _field(spec, 'subject')
    message.set_content(_field(spec, 'text'), subtype='plain', charset='utf-8', cte='quoted-printable')
    _checkpoint(checkpoint)
    output = message.as_bytes()
    if len(output) > MAX_BYTES:
        _fail('output_limit')
    _read_eml(output, checkpoint)
    return output


def _iso_date(value, name):
    if type(value) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        _fail('invalid_' + name)
    try:
        parsed = datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        _fail('invalid_' + name)
    return parsed


def create_ics(spec, *, checkpoint=None):
    required = {'uid', 'summary', 'start_date', 'dtstamp'}
    optional = {'end_date', 'description', 'location'}
    if type(spec) is not dict or not required <= set(spec) or not set(spec) <= required | optional:
        _fail('create_schema')
    start = _iso_date(spec['start_date'], 'start_date')
    end = _iso_date(spec['end_date'], 'end_date') if 'end_date' in spec else None
    if end is not None and end <= start:
        _fail('invalid_end_date')
    stamp = spec['dtstamp']
    if type(stamp) is not str or not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z', stamp):
        _fail('invalid_dtstamp')
    try:
        datetime.strptime(stamp, '%Y%m%dT%H%M%SZ')
    except ValueError:
        _fail('invalid_dtstamp')
    lines = [b'BEGIN:VCALENDAR', b'VERSION:2.0', b'PRODID:-//Friday//Native Communication Files//EN', b'BEGIN:VEVENT']
    lines.append(_fold('UID:' + _escape(_field(spec, 'uid'))))
    lines.append(_fold('DTSTAMP:' + stamp))
    lines.append(_fold('DTSTART;VALUE=DATE:' + start.strftime('%Y%m%d')))
    if end is not None:
        lines.append(_fold('DTEND;VALUE=DATE:' + end.strftime('%Y%m%d')))
    lines.append(_fold('SUMMARY:' + _escape(_field(spec, 'summary'))))
    for name in ('description', 'location'):
        if name in spec:
            lines.append(_fold(name.upper() + ':' + _escape(_field(spec, name))))
    lines += [b'END:VEVENT', b'END:VCALENDAR']
    _checkpoint(checkpoint)
    return _created(lines)


def _typed_values(spec, name):
    rows = spec.get(name, [])
    if type(rows) is not list or len(rows) > 100:
        _fail('create_schema')
    result = []
    for row in rows:
        if type(row) is str:
            row = {'value': row}
        if type(row) is not dict or not set(row) <= {'value', 'types'} or type(row.get('value')) is not str or not row['value']:
            _fail('create_schema')
        types = row.get('types', [])
        if type(types) is not list or len(types) > 8 or any(type(x) is not str or not TOKEN.fullmatch(x) for x in types):
            _fail('invalid_type')
        result.append((_field(row, 'value'), [x.lower() for x in types]))
    return result


def create_vcf(spec, *, checkpoint=None):
    required = {'fn'}
    optional = {'uid', 'emails', 'phones', 'organization', 'title', 'note'}
    if type(spec) is not dict or not required <= set(spec) or not set(spec) <= required | optional:
        _fail('create_schema')
    lines = [b'BEGIN:VCARD', b'VERSION:4.0', _fold('FN:' + _escape(_field(spec, 'fn')))]
    if 'uid' in spec:
        lines.append(_fold('UID:' + _escape(_field(spec, 'uid'))))
    for key, prop in (('emails', 'EMAIL'), ('phones', 'TEL')):
        for value, types in _typed_values(spec, key):
            prefix = prop + ((';TYPE=' + ','.join(types)) if types else '')
            lines.append(_fold(prefix + ':' + _escape(value)))
    for key, prop in (('organization', 'ORG'), ('title', 'TITLE'), ('note', 'NOTE')):
        if key in spec:
            lines.append(_fold(prop + ':' + _escape(_field(spec, key))))
    lines.append(b'END:VCARD')
    _checkpoint(checkpoint)
    return _created(lines)


def _edit_header(data, spec):
    expected = spec['old_value']
    new = _text(spec['new_value'], 'invalid_new_value', 16_384)
    match = _header_separator(data)
    header = data[:match.start()]
    lines = _logical(header + (b'\n' if not header.endswith((b'\n', b'\r')) else b''))
    targets = []
    for line in lines:
        raw = line['text']
        name, colon, value = raw.partition(':')
        if colon and name.lower() == 'subject':
            targets.append((line, value))
    if len(targets) != 1:
        _fail('subject_target_not_unique')
    line, value = targets[0]
    # MIME unfolding retains the continuation whitespace; the ICS/VCF logical
    # line helper removes it. Compare against the same semantic header used by
    # the reader, including folded unencoded and encoded-word Subjects.
    parsed = BytesParser(policy=policy.default).parsebytes(data, headersonly=True)
    old = _decode_header(str(parsed['Subject']))
    if old != expected:
        _fail('precondition_mismatch')
    terminal = line['end'] > match.start()
    newline = ((b'\r\n' if match.group().startswith(b'\r\n') else b'\n') if terminal
               else line['newline'] or (b'\r\n' if b'\r\n' in header else b'\n'))
    encoded = Header(new, 'utf-8', header_name='Subject', maxlinelen=78).encode(linesep=newline.decode('ascii'))
    replacement = b'Subject: ' + encoded.encode('ascii') + (b'' if terminal else newline)
    end = line['end']
    if end > match.start():
        end = match.start()
    output = data[:line['start']] + replacement + data[end:]
    if len(output) > MAX_BYTES:
        _fail('output_limit')
    return output


def _edit_property(data, spec, format):
    lines = _logical(data)
    roots = _components(lines, format)
    if format == 'ics':
        selected = []

        def walk(node):
            if node['type'] == 'VEVENT':
                uids = [_unescape(p['raw_value']) for p in node['properties'] if p['name'] == 'UID']
                if spec['uid'] in uids:
                    selected.append(node)
            for child in node['children']:
                walk(child)
        walk(roots[0])
        target_name = 'SUMMARY'
    else:
        if len(roots) != 1:
            _fail('single_vcard_required')
        selected = roots
        target_name = 'FN'
    if len(selected) != 1:
        _fail('edit_target_not_unique')
    targets = [p for p in selected[0]['properties'] if p['name'] == target_name]
    if len(targets) != 1:
        _fail('edit_target_not_unique')
    target = targets[0]
    if target['params'] or target['group']:
        _fail('unsupported_edit_target')
    if _unescape(target['raw_value']) != spec['old_value']:
        _fail('precondition_mismatch')
    line = lines[target['logical_index']]
    newline = line['newline'] or (b'\r\n' if b'\r\n' in data else b'\n')
    replacement = _fold(target_name + ':' + _escape(spec['new_value']), newline) + newline
    output = data[:line['start']] + replacement + data[line['end']:]
    if len(output) > MAX_BYTES:
        _fail('output_limit')
    return output


def edit_communication(data, spec, format, *, checkpoint=None):
    _input(data, format)
    required = {'old_value', 'new_value'}
    if type(spec) is not dict or not required <= set(spec):
        _fail('edit_schema')
    if format == 'ics' and set(spec) != required | {'uid'}:
        _fail('edit_schema')
    if format != 'ics' and set(spec) != required:
        _fail('edit_schema')
    if type(spec['old_value']) is not str:
        _fail('invalid_old_value')
    _text(spec['new_value'], 'invalid_new_value', 65_536, newlines=format != 'eml')
    if format == 'ics':
        _field(spec, 'uid')
    extract_communication(data, format, checkpoint=checkpoint)
    _checkpoint(checkpoint)
    output = _edit_header(data, spec) if format == 'eml' else _edit_property(data, spec, format)
    extract_communication(output, format, checkpoint=checkpoint)
    return output
