"""Dormant Root-only entry for one missing conversion observation.

Consumes independently created fresh Root proofs. Does not create observations,
accept its own source, infer permission from history or fall back to old frames.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def require(value, code):
    if not value:
        raise ValueError(code)


def assemble(bindings, source_sha, *, uid, boot, now, monotonic_now):
    """Pure field assembly; its inputs must be authenticated by main first."""
    require(type(bindings) is dict and bindings.get('schema') == 'friday.f06.one-template-root-bindings.v1' and bindings.get('state') == 'ROOT_BOUND_NO_EFFECT_YET', 'BOUND_ROOT_PROOFS_REQUIRED')
    fields = {'schema', 'state', 'assignment', 'operation_key', 'nonce', 'uid', 'boot_id', 'source_pins_sha256', 'limits', 'original_operation_start_monotonic', 'actual_two_cpu_ids', 'slot_path', 'slot_identity', 'source_review', 'runtime_authority', 'fresh_boundary', 'original18_closure', 'output_manifest', 'credential_source', 'task_retention_root'}
    require(set(bindings) == fields, 'ROOT_BINDINGS_FIELDS')
    require(bindings['uid'] == uid and type(bindings['uid']) is int and bindings['boot_id'] == boot, 'ROOT_CURRENT_UID_BOOT')
    origin = bindings['original_operation_start_monotonic']
    require(type(origin) in (int, float) and 0 <= monotonic_now-origin <= 120, 'ROOT_ORIGINAL_CLOCK_REQUIRED')
    require(bindings['source_pins_sha256'] == source_sha, 'ROOT_EXACT_SOURCE')
    require(all(type(bindings[k]) is dict for k in ('source_review', 'runtime_authority', 'fresh_boundary', 'original18_closure', 'output_manifest', 'credential_source')), 'ROOT_UNBOUND_REFERENCE')
    from f06_contract import ASSIGNMENT, MODE, SELECTED_ID, LIMITS
    require(bindings['assignment'] == ASSIGNMENT and bindings['limits'] == LIMITS, 'ROOT_ASSIGNMENT_LIMITS')
    return dict(bindings, schema='friday.f06.one-template-admission.v1', state='ROOT_FRESH_ONCE_ADMITTED', mode=MODE, admitted_at_moscow=now, credential_source_identity=bindings['credential_source']['identity'], selected_count=1, selected_fixture_ids=[SELECTED_ID], expected_probes=1, expected_stores=0)


def main():
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, 'ISOLATED_ROOT_FLAGS')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-reviewed-bind-admit-and-exec', action='store_true', required=True)
    parser.add_argument('--source-pins-sha256', required=True)
    parser.add_argument('--bindings', required=True)
    parser.add_argument('--bindings-sha256', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    candidate = Path(__file__).resolve().parent
    # The Root invokes this accepted entry by its separately reviewed exact SHA;
    # no candidate Python imports before every source hash is checked.
    raw = (candidate/'SOURCE-PINS.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == args.source_pins_sha256, 'SOURCE_PINS_CAS')
    pins = json.loads(raw)
    require(pins.get('schema') == 'friday.f06.one-template-diagnostic-source.v1' and pins.get('state') == 'SOURCE_ONLY_DORMANT', 'SOURCE_SCHEMA')
    for row in pins['files']:
        name = row['name']
        require(type(name) is str and Path(name).name == name and name != 'SOURCE-PINS.json', 'SOURCE_LOCAL_NAME')
        body = (candidate/name).read_bytes()
        require(len(body) == row['bytes'] and hashlib.sha256(body).hexdigest() == row['sha256'], 'SOURCE_BODY_CAS')
    sys.path.insert(0, str(candidate))
    import f06_contract as c
    c.recipe_check()
    # Lexical spelling before private predicate prevents alias/root namespace
    # confusion; .json proof is not a payload/credential selector.
    bpath = c.canonical(str(args.bindings))
    require(bpath == candidate/'root-proofs'/'ROOT-BINDINGS.json', 'EXACT_ROOT_METADATA_BINDINGS_PATH')
    raw, bpin = c.private(bpath, bpath.parent)
    require(bpin['sha256'] == args.bindings_sha256 and bpath.suffix == '.json', 'BINDINGS_CAS')
    bindings = c.decode(raw)
    admission = assemble(bindings, args.source_pins_sha256, uid=os.getuid(), boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), now=c.utcmoscow(), monotonic_now=time.monotonic())
    c.operation(admission['operation_key'], c.MODE)
    c.credential_metadata(admission['credential_source'])
    # All nonsecret full-pin proof/CAS/type/identity joins and resources are
    # validated before any once admission file or unit intent is created.
    from root_frame import validate_fields
    validate_fields(admission)
    path = candidate/(admission['operation_key']+'.ADMISSION.json')
    require(not os.path.lexists(c.operation(admission['operation_key'], c.MODE)), 'OPERATION_EXISTS_NO_REPLAY')
    c.save(path, admission)  # O_EXCL, consumed on publication; no overwrite/reset.
    apin = c.private(path, candidate)[1]
    from root_frame import validate_admission
    validate_admission(path, apin['sha256'])
    c.save(candidate/(admission['operation_key']+'.ENTRY-INTENT.json'), dict(state='ROOT_BOUND_EXACT_SOURCE_CONSUMER_READBACK_EXEC_SAME_ADMISSION', bindings=bpin, admission=apin, original_operation_start_monotonic=admission['original_operation_start_monotonic'], planned_document_loads=1, planned_getRequest_calls=1, planned_stores=0))
    os.execv('/usr/bin/python3', ['/usr/bin/python3', '-I', '-B', '-S', str(candidate/'root_frame.py'), '--execute-once-root-accepted', '--admission', str(path), '--admission-sha256', apin['sha256']])


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print(json.dumps({'state':'ROOT_ENTRY_REFUSED_PRESERVE_NO_REPLAY', 'exception_class':type(error).__name__}), flush=True)
        raise SystemExit(2)
