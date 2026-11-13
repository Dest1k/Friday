import ast
import datetime
import hashlib
import json
import os
import pathlib
import stat

B = pathlib.Path(__file__).resolve().parent.parent
F = pathlib.Path(__file__).resolve().parent
os.umask(0o077)
checks = []

def pin(path, expected=None, size=None):
    raw = path.read_bytes()
    info = path.stat()
    actual = hashlib.sha256(raw).hexdigest()
    passed = (expected is None or actual == expected) and (size is None or len(raw) == size)
    checks.append(dict(path=str(path), bytes=len(raw), sha256=actual,
                       expected_sha256=expected, match=passed, uid=info.st_uid,
                       mode=oct(stat.S_IMODE(info.st_mode)), nlink=info.st_nlink))
    assert passed, str(path)
    return raw

def all_nodes(tree):
    return {node.name: node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}

for rel, expected in [
    ('MANIFEST.json', '8f5581e4986074342aa21d91c897b11a29efee7346c997a81212c0f44595aed8'),
    ('ROOT-NEXT-RECIPE.json', '481f760b79129a407ef783f015f277eb5d37b9476214f87606213f2700922ee0'),
    ('ORIGINAL-COVERAGE.json', '806dca28eda6bf5b5bf1c88a39fe70f3576ae232367ebddbda85c1bfab4be141'),
]:
    pin(B / rel, expected)
manifest = json.loads((B / 'MANIFEST.json').read_text())
for entry in manifest['components'] + manifest['checks'] + [manifest['earlier_M1_artifact_issue']]:
    pin(pathlib.Path(entry['path']), entry['sha256'], entry['bytes'])
cas = json.loads((B / 'SOURCE209-CAS.json').read_text())
for entry in [cas['receipt'], cas['actual209_closed']] + cas['selected_sources']:
    pin(pathlib.Path(entry['path']), entry['sha256'], entry['bytes'])
textpins = json.loads((B / 'text-fixture/SOURCE-PINS.json').read_text())
for entry in textpins:
    raw = pin(pathlib.Path(entry['source']), entry['sha256'], entry['bytes'])
    if 'relative' in entry:
        pin(B / 'text-fixture/source' / entry['relative'], entry['sha256'], entry['bytes'])
    if 'selected_functions' in entry:
        basename = pathlib.Path(entry['source']).name
        selected_name = {'base.py': 'base_selected.py', 'run_startup.py': 'startup_selected.py',
                         'status.py': 'status_selected.py'}[basename]
        copied = B / 'text-fixture/source' / selected_name
        pin(copied)
        original_nodes = all_nodes(ast.parse(raw))
        selected_nodes = all_nodes(ast.parse(copied.read_bytes()))
        for name in entry['selected_functions']:
            assert ast.dump(original_nodes[name], include_attributes=False) == ast.dump(selected_nodes[name], include_attributes=False), name
            checks.append(dict(path=str(copied), label='complete selected AST ' + name, match=True))
filepins = json.loads((B / 'file-fixture/sourcepins.json').read_text())
for entry in filepins['files']:
    raw = pin(pathlib.Path(entry['source']), entry.get('source_sha256', entry.get('sha256')))
    copied = pin(pathlib.Path(entry['copy']), entry.get('copy_sha256', entry.get('sha256')))
    if 'spans' in entry:
        lines = raw.decode().splitlines(keepends=True)
        original_nodes, selected_nodes = all_nodes(ast.parse(raw)), all_nodes(ast.parse(copied))
        for span in entry['spans']:
            body = ''.join(lines[span['start_line'] - 1:span['end_line']]).encode()
            assert hashlib.sha256(body).hexdigest() == span['sha256'], span['symbol']
            name = span['symbol']
            assert ast.dump(original_nodes[name], include_attributes=False) == ast.dump(selected_nodes[name], include_attributes=False), name
            checks.append(dict(path=entry['copy'], label='complete selected AST ' + name, match=True))
for rel, expected in [
    ('original-binding/RESULT.json', '757746fc004413d4690c5bfd072161fc0afbe527e0ed98518023ad8dad911fee'),
    ('delivery-callgraph/RESULT.json', '6bb47a84a7d9a056a2422f8c4eb05ca50d9e91da2c5a861e58728a7bad16c87a'),
    ('M1-SUPERSEDED-REFS-DELTA.json', '8f7efe994f9b0c7985565fa7f31e85f577bf0806252aa3d54af974bfefadddf4'),
    ('file-fixture/INITIAL-ENVELOPE-CHECKER-ERROR-RESULT.json', None),
    ('file-fixture/INITIAL-HARNESS-ERROR-RESULT.json', None),
    ('file-fixture/initial-harness-error-observations.json', None),
    ('M1.json', 'b7d5548f6dfb0b338497676b90cf1dc3973b6aa524cbfb6c95a0800647a49e61'),
]:
    pin(B / rel, expected)
pin(pathlib.Path('/home/jericho/jericho/Friday_rework/docs/WORKING-RULES.md'))
output = F / 'PIN-CHECKS.json'
output.write_text(json.dumps(dict(
    at_moscow=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
    checks=checks, all_passed=True,
    first_checker_error='Inline initial pin checker mistakenly mapped status_selected.py to startup_selected.py; corrected selection only. No consumer execution or foreign writes occurred.',
    writes='final-review only', source_reads='source bytes/receipts only; no configuration/state/database/history read'
), indent=2) + '\n')
print(json.dumps(dict(pin_checks=len(checks), all_passed=True, output=str(output),
                      sha256=hashlib.sha256(output.read_bytes()).hexdigest())))
