"""Own-workspace create-only EML/ICS/VCF operations with exact source custody."""
import hashlib
import json
import os
from pathlib import Path
import re

from hermes_cli.friday_user_scope import ScopeDenied, workspace_document
from hermes_cli.friday_workspace_docx import _check_parent, _create_bytes
from hermes_cli.friday_workspace_revision import check
from hermes_cli.friday_workspace_zip import _path as _attachment_path
from tools.scoped_communication import (
    CommunicationError, create_eml, create_ics, create_vcf, edit_communication,
    extract_eml_attachment,
)


_CREATE_SCHEMA_HINTS = {
    'eml': ('eml_create content must be a JSON string encoding exactly from:string, '
            'to:array[string] with 1-100 nonempty address strings, subject:string, text:string. '
            'from, subject and text must be nonempty; text is one string with JSON newline escapes, '
            'not an array. Use a NEW .eml path. Local file only; no mail is sent.'),
    'ics': ('ics_create content must be a JSON string encoding required uid,summary,start_date,dtstamp '
            'and optional end_date,description,location. All values are nonempty strings; '
            'dates are YYYY-MM-DD, dtstamp is YYYYMMDDTHHMMSSZ. Use a NEW .ics path. '
            'Local file only; no calendar import.'),
    'vcf': ('vcf_create content must be a JSON string encoding fn:string and optional '
            'uid,organization,title,note strings; all supplied scalar strings are nonempty. '
            'Optional emails/phones are arrays of strings or objects with value:string and '
            'optional types:array[string]. Use a NEW .vcf path. Local file only; no contact import.'),
}


def _object(content):
    if type(content) is not str or len(content.encode('utf-8')) > 100_000:
        raise ScopeDenied()
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ScopeDenied()
            result[key] = value
        return result
    try:
        value = json.loads(content, object_pairs_hook=pairs)
    except (ValueError, RecursionError):
        raise ScopeDenied() from None
    if type(value) is not dict:
        raise ScopeDenied()
    return value


def extract_attachment(cap, fd, leaf, path, content):
    _check_parent(cap, fd, path)
    _attachment_path(path)
    if Path(path).name != leaf:
        raise ScopeDenied()
    source = original = identity = relative = None
    try:
        check(cap)
        spec = _object(content)
        required = {'source', 'source_sha256', 'part_path', 'expected_decoded_sha256'}
        if set(spec) != required:
            raise CommunicationError('extract_schema')
        for key in ('source_sha256', 'expected_decoded_sha256'):
            if type(spec[key]) is not str or re.fullmatch(r'[0-9a-f]{64}', spec[key]) is None:
                raise CommunicationError('source_hash_required' if key == 'source_sha256' else 'decoded_hash_required')
        raw = spec['source']
        if type(raw) is not str or not raw or '\x00' in raw:
            raise ScopeDenied()
        root = cap.home / 'workspace'
        source = Path(raw)
        if not source.is_absolute():
            source = root / source
        try:
            relative = source.relative_to(root)
        except ValueError:
            raise ScopeDenied() from None
        if (source.suffix.lower() != '.eml' or not relative.parts
                or any(part in ('.', '..') or part.startswith('.') for part in relative.parts)
                or relative.as_posix() == path):
            raise ScopeDenied()
        original, actual, identity = workspace_document(str(source), max_bytes=1_000_000,
                                                        with_identity=True)
        if actual != relative.as_posix():
            raise ScopeDenied()
        source_sha256 = hashlib.sha256(original).hexdigest()
        if source_sha256 != spec['source_sha256']:
            return json.dumps({'success': False, 'error': 'eml_extract_attachment_refused',
                               'reason': 'source_hash_mismatch', 'effect_disposition': 'none'})
        rendered, selected = extract_eml_attachment(
            original, spec['part_path'], spec['expected_decoded_sha256'],
            checkpoint=lambda: check(cap))
        check(cap)
    except CommunicationError as error:
        return json.dumps({'success': False, 'error': 'eml_extract_attachment_refused',
                           'reason': error.code, 'effect_disposition': 'none'})

    def verify():
        check(cap)
        current, _, current_identity = workspace_document(str(source), max_bytes=1_000_000,
                                                          with_identity=True)
        if current != original or current_identity != identity:
            raise ScopeDenied()

    # Price the complete embedded JSON receipt before the create-only effect.
    # Metadata claims can be much larger than the publisher's small receipt.
    from agent.bounded_context import bounded_tool_result_budget, serialized_bytes
    budget = bounded_tool_result_budget()
    if budget is None:
        budget = 100_000
    receipt = dict(success=True, format='eml_attachment', path=path,
                   scope='own_user_workspace', create_only=True, verified=True,
                   bytes_written=len(rendered), sha256=hashlib.sha256(rendered).hexdigest(),
                   operation='eml_extract_attachment', source=relative.as_posix(),
                   source_sha256=source_sha256, source_unchanged=True,
                   part_path=selected['path'], decoded_sha256=selected['decoded_sha256'],
                   attachment={'claimed_filename': selected['filename'],
                               'claimed_content_type': selected['content_type'],
                               'disposition': selected['disposition'],
                               'attachment_context': selected['attachment_context'],
                               'transfer_encoding': selected['transfer_encoding']},
                   extraction_only=True, unselected_parts_published=False,
                   claimed_metadata_verified=False, document_interoperability='UNBOUND',
                   payload_executed=False, local_file_only=True, external_side_effects='none')
    encoded_receipt = json.dumps(receipt, ensure_ascii=False, separators=(',', ':'))
    if serialized_bytes(encoded_receipt) > budget:
        return json.dumps({'success': False, 'error': 'eml_extract_attachment_refused',
                           'reason': 'inline_result_capacity', 'effect_disposition': 'none'})

    result = json.loads(_create_bytes(cap, fd, leaf, path, rendered,
                                     output_format='eml_attachment', verify_source=verify))
    if result.get('success'):
        return encoded_receipt
    return json.dumps(result, ensure_ascii=False)


def execute(cap, fd, leaf, path, content, operation):
    _check_parent(cap, fd, path)
    if operation == 'eml_extract_attachment':
        if Path(path).name != leaf:
            raise ScopeDenied()
    else:
        match = re.fullmatch(r'(eml|ics|vcf)_(create|edit)', operation)
        if match is None or Path(path).name != leaf or Path(path).suffix.lower() != '.' + match.group(1):
            raise ScopeDenied()
        format, action = match.groups()
    try:
        os.stat(leaf, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        return json.dumps({'success': False, 'error': 'document_already_exists',
                           'effect_disposition': 'none'})
    if operation == 'eml_extract_attachment':
        return extract_attachment(cap, fd, leaf, path, content)
    source = original = identity = relative = None
    try:
        check(cap)
        spec = _object(content)
        if action == 'create':
            rendered = {'eml': create_eml, 'ics': create_ics, 'vcf': create_vcf}[format](
                spec, checkpoint=lambda: check(cap))
        else:
            edit_keys = {'old_value', 'new_value'} | ({'uid'} if format == 'ics' else set())
            if set(spec) != edit_keys | {'source', 'source_sha256'}:
                raise CommunicationError('edit_schema')
            expected = spec['source_sha256']
            if type(expected) is not str or re.fullmatch(r'[0-9a-f]{64}', expected) is None:
                raise CommunicationError('source_hash_required')
            raw = spec['source']
            if type(raw) is not str or not raw or '\x00' in raw:
                raise ScopeDenied()
            root = cap.home / 'workspace'
            source = Path(raw)
            if not source.is_absolute():
                source = root / source
            try:
                relative = source.relative_to(root)
            except ValueError:
                raise ScopeDenied() from None
            if (source.suffix.lower() != '.' + format or not relative.parts
                    or any(p in ('.', '..') or p.startswith('.') for p in relative.parts)
                    or relative.as_posix() == path):
                raise ScopeDenied()
            original, _, identity = workspace_document(str(source), max_bytes=1_000_000,
                                                       with_identity=True)
            if hashlib.sha256(original).hexdigest() != expected:
                return json.dumps({'success': False, 'error': 'communication_edit_refused',
                                   'reason': 'source_hash_mismatch', 'effect_disposition': 'none'})
            edit = {key: spec[key] for key in edit_keys}
            rendered = edit_communication(original, edit, format,
                                          checkpoint=lambda: check(cap))
        check(cap)
    except CommunicationError as error:
        refusal = {'success': False, 'error': 'communication_' + action + '_refused',
                   'reason': error.code, 'effect_disposition': 'none'}
        if action == 'create' and error.code == 'create_schema':
            refusal['hint'] = _CREATE_SCHEMA_HINTS[format]
        return json.dumps(refusal)
    verify = None
    if source is not None:
        def verify():
            check(cap)
            current, _, current_identity = workspace_document(str(source), max_bytes=1_000_000,
                                                              with_identity=True)
            if current != original or current_identity != identity:
                raise ScopeDenied()
    result = json.loads(_create_bytes(cap, fd, leaf, path, rendered,
                                     output_format=operation, verify_source=verify))
    if result.get('success'):
        result.update(local_file_only=True, external_side_effects='none')
        if source is not None:
            result.update(source=relative.as_posix(), source_sha256=hashlib.sha256(original).hexdigest(),
                          source_unchanged=True, replacements=1,
                          edit_mode={'eml': 'single_top_level_Subject',
                                     'ics': 'single_UID_selected_VEVENT_SUMMARY',
                                     'vcf': 'single_VCARD_FN'}[format],
                          unselected_bytes_preserved=True)
    return json.dumps(result, ensure_ascii=False)
