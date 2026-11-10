#!/usr/bin/env python3
"""Offline contract/extraction regression; never a model or user-acceptance test.

Run with the selected product Python, --source-root the installed hermes-agent
(either the exact preimage or the exact installed postimage),
--temp-root a private disk directory, and --fixture the retained ambiguous PDF.
Only three pinned source files are copied. Product imports use installed read-only
dependencies. Real local PDF extraction runs in its existing networkless sandbox.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def readable_pdf():
    text = b'BT /F1 12 Tf 72 720 Td (Readable amount 1234.56 and complete source text) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
               b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(text)).encode() + b' >>\nstream\n' + text + b'\nendstream']
    data, offsets = b'%PDF-1.4\n', [0]
    for index, value in enumerate(objects, 1):
        offsets.append(len(data))
        data += str(index).encode() + b' 0 obj\n' + value + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 6\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return data + b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + str(start).encode() + b'\n%%EOF\n'


def worker(args):
    sys.path.insert(0, str(args.source_root))
    os.environ['HERMES_HOME'] = str(args.home)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    tempfile.tempdir = str(args.home)
    scope = load('p04_scope', args.stage / 'hermes_cli/friday_prompt_scope.py')
    prompt = load('p04_prompt', args.stage / 'agent/prompt_builder.py')
    ocr = load('tools.scoped_pdf_ocr', args.stage / 'tools/scoped_pdf_ocr.py')
    from tools.read_extract import extract_scoped_document_bytes

    cap = SimpleNamespace(binding={'tools': ['read_file']}, key='offline-principal',
                          admission_generation='offline-generation', home=args.home,
                          directory_identity=(1, 2), check=lambda: None)
    agent = SimpleNamespace(_session_db=None, session_id='offline-session')
    with patch.object(scope, 'current', return_value=cap), patch.object(scope, 'check_agent'):
        parts = scope.dialogue_parts(agent)
        assert scope.DOCUMENT_GROUNDING_GUIDANCE in parts
        cap.binding['tools'] = []
        assert scope.DOCUMENT_GROUNDING_GUIDANCE not in scope.dialogue_parts(agent)
        cap.binding['tools'] = ['read_file']
        stamp = scope._stamp(cap, agent.session_id, '\n'.join(parts))
        row = {'model_config': json.dumps({scope.FIELD: stamp})}
        assert scope.matches(agent, '\n'.join(parts), row)
        old = dict(stamp, dialogue_revision='old-unrelated-revision')
        assert not scope.matches(agent, '\n'.join(parts), {'model_config': json.dumps({scope.FIELD: old})})
    with patch.object(scope, 'current', return_value=None):
        assert scope.dialogue_parts(agent) == []

    rendered = '\n'.join(parts)
    guidance = prompt.execution_guidance_text({'read_file'})
    guidance_no_tools = prompt.execution_guidance_text(set())
    needed = 'задай в ответе один конкретный необходимый вопрос'
    assert (needed in rendered) == args.changed
    assert ('even when the tool choice is unchanged' in guidance) == args.changed
    assert ('even when the tool choice is unchanged' in guidance_no_tools) == args.changed
    if args.changed:
        for clause in ['только с доступной точностью', 'не требуй уточнения каждого OCR-токена',
                       'не используй неполное значение как точное', 'Не выдумывай точность распознавания']:
            assert clause in rendered, clause
    rows = [((1, 1, 1), 'Readable', 99), ((1, 1, 1), '1234.56', 99),
            ((1, 1, 2), 'faint', 31), ((1, 1, 2), '12?', 31)]
    tokens, uncertain, numbers = ocr._recognized(rows)
    assert uncertain == 2 and numbers == 2
    assert '[unverified OCR numeric token: 1234.56]' in tokens
    assert '[unverified OCR numeric token: 12?]' in tokens
    assert '[uncertain OCR token: faint]' in tokens
    assert 'Readable' in tokens

    # Actual ordinary byte consumer: OCR fallback for the immutable retained file.
    ambiguous = extract_scoped_document_bytes(args.fixture.read_bytes(), 'pdf')
    meta = dict(ambiguous.extraction_metadata)
    warning = meta.pop('warning')
    assert meta['numeric_values_verified'] is False and meta['ocr_exact'] is False
    assert 'UNVERIFIED' in warning
    assert ('a conditional recommendation' in warning) == args.changed
    assert str(ambiguous).startswith('[PDF extraction warning: ' + warning + ']\n\n')
    content = str(ambiguous).split('\n\n', 1)[1]
    assert '[unverified OCR numeric token:' in content

    # Real native-text extraction control bypasses OCR and stays fully readable.
    readable = extract_scoped_document_bytes(readable_pdf(), 'pdf')
    assert 'Readable amount 1234.56 and complete source text' in readable
    assert '[unverified OCR numeric token:' not in readable
    assert 'UNVERIFIED' not in readable
    assert not getattr(readable, 'extraction_metadata', {}).get('method') == 'local_pdf_ocr'
    return {'changed': args.changed, 'dialogue_revision': scope.DIALOGUE_REVISION,
            'rendered_prompt_sha256': sha(rendered.encode()),
            'execution_guidance_sha256': sha(guidance.encode()),
            'warning_sha256': sha(warning.encode()), 'warning_bytes': len(warning.encode()),
            'ocr_content_sha256': sha(content.encode()), 'ocr_metadata_without_warning': meta,
            'recognized_control_sha256': sha(tokens.encode()),
            'native_text_sha256': sha(str(readable).encode()),
            'checks': ['admitted_read_contract', 'nonread_and_unscoped_exclusion',
                       'persisted_prompt_revision_guard', 'execution_guidance_tool_filter',
                       'numeric_and_low_confidence_controls', 'real_retained_pdf_ocr',
                       'real_fully_readable_native_pdf']}


def main(args):
    here = Path(__file__).resolve().parent
    manifest_path = here / 'necessary-document-clarification-p04-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    patch_path = here / 'necessary-document-clarification-p04.patch'
    assert sha(patch_path.read_bytes()) == manifest['patch_sha256']
    fixture_before = sha(args.fixture.read_bytes())
    source_hashes = {item['path']: sha((args.source_root / item['path']).read_bytes())
                     for item in manifest['files']}
    before_source = all(source_hashes[item['path']] == item['before_sha256']
                        for item in manifest['files'])
    after_source = all(source_hashes[item['path']] == item['sha256']
                       for item in manifest['files'])
    assert before_source != after_source, 'Require one complete pinned preimage or postimage; mixed/unknown source refused'
    args.temp_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sol-v3-p04-20261110-check-', dir=args.temp_root) as tmp:
        root = Path(tmp)
        for kind in ['before', 'after']:
            for item in manifest['files']:
                data = (args.source_root / item['path']).read_bytes()
                assert sha(data) == source_hashes[item['path']], item['path']
                target = root / kind / item['path']
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                target.write_bytes(data)
        direction = ['--reverse'] if after_source else []
        subprocess.run(['patch', '--batch', '--fuzz=0', *direction, '-p1', '-i', str(patch_path)],
                       cwd=root / ('before' if after_source else 'after'), check=True, capture_output=True)
        for item in manifest['files']:
            assert sha((root / 'before' / item['path']).read_bytes()) == item['before_sha256']
            data = (root / 'after' / item['path']).read_bytes()
            assert sha(data) == item['sha256'] and len(data) == item['bytes']
            compile(data, item['path'], 'exec')
        result = []
        for kind in ['before', 'after']:
            home = root / (kind + '-home')
            home.mkdir(mode=0o700)
            command = [sys.executable, '-B', str(Path(__file__).resolve()), '--source-root', str(args.source_root),
                       '--fixture', str(args.fixture), '--worker', '--stage', str(root / kind), '--home', str(home)]
            if kind == 'after':
                command += ['--changed']
            env = dict(os.environ, HERMES_HOME=str(home), TMPDIR=str(home), PYTHONDONTWRITEBYTECODE='1')
            completed = subprocess.run(command, env=env, check=True, capture_output=True, text=True, timeout=160)
            result.append(json.loads(completed.stdout))
        before, after = result
        for key in ['ocr_content_sha256', 'ocr_metadata_without_warning', 'recognized_control_sha256', 'native_text_sha256']:
            assert before[key] == after[key], key
        assert before['dialogue_revision'] != after['dialogue_revision']
        assert before['warning_sha256'] != after['warning_sha256']
    assert sha(args.fixture.read_bytes()) == fixture_before
    for item in manifest['files']:
        assert sha((args.source_root / item['path']).read_bytes()) == source_hashes[item['path']]
    return {'status': 'PASS_OFFLINE_CONTRACT_AND_EXTRACTION_ONLY', 'fixture_sha256': fixture_before,
            'manifest_sha256': sha(manifest_path.read_bytes()), 'observations': result,
            'source_basis': 'postimage' if after_source else 'preimage',
            'source_and_fixture_unchanged': True, 'temporary_stage_removed': True,
            'limits': 'No model/API/Telegram call; admission mocked for prompt delivery only. '
                      'No demonstrated user clarification behavior, installation or live acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--temp-root', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--stage', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--home', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--changed', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.worker and args.temp_root is None:
        parser.error('--temp-root is required')
    print(json.dumps(worker(args) if args.worker else main(args), ensure_ascii=False, sort_keys=True))
