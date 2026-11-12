"""Independent isolated source-only F06 leaf review; no candidate module import."""
import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

HERE = Path(__file__).absolute().parent
R = HERE.parent
T = Path('/home/jericho/.cache/FRW-SOL-V3-F06-CANONICAL-BINDING-LAUNCH-PROTOCOL-CORE-20261112/candidate')
W = Path('/home/jericho/.cache/FRW-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112/candidate')
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', type=Path, default=R/'candidate')
parser.add_argument('--freeze', type=Path, default=R/'SOURCE-FREEZE.json')
parser.add_argument('--expected-freeze', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert args.output.absolute().parent == HERE
os.umask(0o077)
checks, observations = [], []
sha = lambda raw: hashlib.sha256(raw).hexdigest()
def good(name, value=True):
    assert value, name
    checks.append(name)
def refuses(name, operation):
    try:
        operation()
    except Exception:
        checks.append(name)
        return
    raise AssertionError(name)
def defs(raw):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
def leaf_ns(raw, names, namespace=None):
    ns = dict(Path=Path, hashlib=hashlib, re=re, os=os, stat=stat, MAX_JSON=1048576)
    if namespace:
        ns.update(namespace)
    chosen = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in chosen} == set(names)
    exec(compile(ast.Module(body=chosen, type_ignores=[]), '<review-only-selected-inert-source-defs>', 'exec'), ns)
    return ns
freeze_raw = args.freeze.read_bytes()
good('source_freeze_pin', sha(freeze_raw) == args.expected_freeze)
freeze = json.loads(freeze_raw)
raws = {}
for relative, pin in freeze['files'].items():
    raw = (args.candidate/relative).read_bytes()
    good(relative+':byte_and_sha_pin', len(raw) == pin['bytes'] and sha(raw) == pin['sha256'])
    raws[relative] = raw
changed = []
for relative, raw in raws.items():
    branch, filename = relative.split('/')
    before = ((W/filename) if branch == 'wrong-edit' else (T/branch/filename)).read_bytes()
    if raw == before:
        good(relative+':baseline_byte_identical')
        continue
    changed.append(relative)
    if filename != 'f06_footer.py.txt':
        a, b = ast.parse(before), ast.parse(raw)
        a.body = [n for n in a.body if not isinstance(n, ast.FunctionDef) or n.name != 'readref']
        b.body = [n for n in b.body if not isinstance(n, ast.FunctionDef) or n.name != 'readref']
        good(relative+':all_other_module_AST_exact', ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False))
good('exact_eight_changed_files', sorted(changed) == sorted(freeze['changed_files']) and len(changed) == 8)

payload = b'REVIEW-SYNTHETIC-ONLY\n' + b'Q'*1250000
reference = dict(path=str(HERE/'NEVER-OPENED'), bytes=len(payload), sha256=sha(payload))
leaves = [name for name in raws if name.endswith(('f06_source.py', 'first_ingress.py'))]
good('five_exact_reference_leaves', len(leaves) == 5)
for name in leaves:
    ingress = name.endswith('first_ingress.py')
    ns = leaf_ns(raws[name], {'need','digest','sha','path','reference','readref'} if ingress else {'need','digest','sha','canonical_path','ref','readref'})
    readref = ns['readref']
    calls = []
    def fallback(path, *, private=True):
        calls.append(('path', str(path), private))
        return payload
    good(name+':absent_callback_original_ABI', readref(reference, fallback) == payload and calls == [('path', reference['path'], True)])
    for bad in (None, False, 0, '', {}):
        calls.clear()
        fallback.f06_read_reference = bad
        if bad is None:
            try:
                result = readref(reference, fallback)
            except Exception:
                good(name+':present_None_refused_no_fallback', not calls)
            else:
                good(name+':original_None_gap_reproduced', result == payload and len(calls) == 1)
                observations.append(dict(code='EXPLICIT_NONE_FALLS_BACK', source=name, original_readref=defs(raws[name])['readref']))
        else:
            refuses(name+':present_noncallable_'+type(bad).__name__, lambda: readref(reference, fallback))
            good(name+':present_noncallable_no_fallback_'+type(bad).__name__, not calls)
    calls.clear()
    def callback(ref):
        calls.append(('callback', ref is reference))
        return payload
    fallback.f06_read_reference = callback
    good(name+':callback_gets_exact_leaf_only', readref(reference, fallback) == payload and calls == [('callback', True)])
    def throws(ref):
        calls.append(('throw',))
        raise RuntimeError('SYNTHETIC_CALLBACK_ERROR')
    calls.clear()
    fallback.f06_read_reference = throws
    refuses(name+':callback_exception_propagates', lambda: readref(reference, fallback))
    good(name+':exception_no_retry_or_fallback', calls == [('throw',)])
    for label, returned in [('wrong_hash', b'Z'*len(payload)), ('wrong_size', payload[:-1]), ('wrong_type', bytearray(payload))]:
        calls.clear()
        fallback.f06_read_reference = lambda r, v=returned: v
        refuses(name+':callback_revalidated_'+label, lambda: readref(reference, fallback))
        good(name+':callback_bad_value_no_path_'+label, not calls)
    fallback.f06_read_reference = callback
    invalid = [('bool', dict(reference, bytes=True)), ('over_cap', dict(reference, bytes=24*1024**2+1)), ('zero', dict(reference, bytes=0)), ('alias', dict(reference, path=str(HERE)+'/./NEVER-OPENED')), ('extra_key', dict(reference, extra=True))]
    for label, ref in invalid:
        calls.clear()
        refuses(name+':reference_validated_before_callback_'+label, lambda r=ref: readref(r, fallback))
        good(name+':invalid_ref_no_reader_'+label, not calls)

class Refused(Exception):
    pass
full = (R/'checks/first/SYNTHETIC-full-consumer.py').read_bytes()
reader_ns = leaf_ns(full, {'safe_read','no_symlinks'}, {'Refused':Refused})
helpers = []
for branch in ('first','correct','wrong-edit'):
    footer = raws[branch+'/f06_footer.py.txt']
    ns = leaf_ns(footer, {'_f06_need','_f06_path','_f06_reference_read','_f06_bounded_reference_read'}, {**reader_ns, 'digest':sha})
    helpers.append(tuple(defs(footer)[n] for n in ('_f06_reference_read','_f06_bounded_reference_read')))
    with tempfile.TemporaryDirectory(prefix='synthetic-leaf-', dir=HERE) as tmp:
        p = Path(tmp)/'SYNTHETIC-large.bin'
        p.write_bytes(payload)
        p.chmod(0o600)
        ref = dict(path=str(p), bytes=len(payload), sha256=sha(payload))
        bounded, direct = ns['_f06_bounded_reference_read'], ns['_f06_reference_read']
        good(branch+':real_bounded_reader_gt1MiB', bounded(ref) == payload)
        refuses(branch+':direct_path_default_stays1MiB', lambda:direct(p))
        refuses(branch+':declared_short_refused', lambda:bounded(dict(ref, bytes=len(payload)-1)))
        refuses(branch+':declared_long_refused', lambda:bounded(dict(ref, bytes=len(payload)+1)))
        refuses(branch+':declared_wrong_sha_refused', lambda:bounded(dict(ref, sha256='0'*64)))
        p.chmod(0o640)
        refuses(branch+':private0640_refused', lambda:bounded(ref))
        p.chmod(0o600)
        linked = p.with_name('SYNTHETIC-hardlink')
        os.link(p, linked)
        refuses(branch+':hardlink_refused', lambda:bounded(ref))
        linked.unlink()
        alias = p.with_name('SYNTHETIC-symlink')
        alias.symlink_to(p)
        refuses(branch+':symlink_refused', lambda:bounded(dict(ref, path=str(alias))))
good('shared_footer_reader_AST_identical', len(set(helpers)) == 1)
result = dict(schema='frw.F06.R2.independent-leaf-review.v1', source_freeze_sha256=args.expected_freeze, candidate_root=str(args.candidate), controls=checks, count=len(checks), observations=observations, extracted_functions_only=True, actual_checker_main_caller_api_model_office_telegram=False, actual_payload_reads=False, timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat())
args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
args.output.chmod(0o600)
print(json.dumps(dict(path=str(args.output), sha256=sha(args.output.read_bytes()), controls=len(checks), observations=len(observations))))
