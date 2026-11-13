"""Pure, bounded Task43 tool-argument and saved-byte preparation.

No ordinary operation is admitted or executed here. The original directed
ODT->DOCX operation already has accepted R97 evidence; its max1 is consumed.
R93 is a distinct edited source. Root alone may identify/admit a genuinely
missing original branch. This module never opens a path or sends a tool call.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath

R93_SHA256 = '74e80fdfe95d330509a589a9620f1b8e0ab3e4cc54f40e2a8caf34991173a132'
R93_BYTES = 2061
R97_SOURCE_SHA256 = '61226529fa1c8568a5bef2e144bf98857073f3043cb275c4bf16d8bfc389ad81'
R97_SOURCE_BYTES = 2022


class PreparationRefused(ValueError):
    """Fixed codes only; no arguments, source prose or exception diagnostics."""


def _path(value, suffix):
    if type(value) is not str:
        raise PreparationRefused('invalid_relative_tool_path')
    try:
        encoded_size = len(value.encode('utf-8'))
    except UnicodeEncodeError:
        raise PreparationRefused('invalid_relative_tool_path') from None
    if (not 1 <= encoded_size <= 4096
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise PreparationRefused('invalid_relative_tool_path')
    path = PurePosixPath(value)
    if (path.is_absolute() or path.as_posix() != value or not path.parts
            or any(p in ('.', '..') or p.startswith('.') for p in path.parts)
            or path.suffix.lower() != suffix):
        raise PreparationRefused('invalid_relative_tool_path')
    return value


def r93_tool_call(source_relative, new_destination_relative):
    """Return ordinary write_file's actual schema; data, never permission.

    Root must bind a genuine current own-workspace R93 source unit and prove
    destination absence, unchanged source, owner/route/session, permission,
    cancel/CAS/history/once/budget and a separate missing-branch basis before
    any eventual dispatch. No historical R97 allowance transfers to R93.
    """
    source = _path(source_relative, '.odt')
    target = _path(new_destination_relative, '.docx')
    return {'name': 'write_file', 'arguments': {
        'path': target, 'format': 'odt_docx',
        'content': json.dumps({'source': source, 'source_sha256': R93_SHA256},
                              ensure_ascii=False, separators=(',', ':'))}}


def assess_native_bytes(source, output):
    """Run the selected product validator on supplied RAM bytes, not Office.

    The caller authenticates module origin and retained/received custody.
    This result gives no transport, original full180, runtime, App or formal
    acceptance. Cross-format equality concerns semantic blocks, not ZIP bytes.
    """
    if type(source) is not bytes or type(output) is not bytes:
        raise PreparationRefused('native_bytes_required')
    identity = (len(source), hashlib.sha256(source).hexdigest())
    if identity not in {(R93_BYTES, R93_SHA256),
                        (R97_SOURCE_BYTES, R97_SOURCE_SHA256)}:
        raise PreparationRefused('unbound_source_bytes')
    from tools.scoped_word_conversion import validate_conversion
    details = validate_conversion(source, 'odt', output, 'docx')
    return {'state': 'CURRENT_PARSER_SEMANTICS_ONLY',
            'source_bytes': len(source), 'source_sha256': identity[1],
            'output_bytes': len(output),
            'output_sha256': hashlib.sha256(output).hexdigest(),
            'details': details, 'ordinary_or_custody_or_App_or_formal': False}


if __name__ == '__main__':
    raise SystemExit('REFUSED: preparation only; no operation entry point')
