SOURCE_BOUND = False
def require_source_bound():
    if not SOURCE_BOUND: raise ValueError('native223_source_inputs_UNBOUND_before_current_or_effect')
"Future Root-only current metadata binder; import inert; no execution grant.\n\nNot invoked during source assembly. It consumes Root's actual new acceptance and\nreadback, validates current leaves through the exact metadata consumer, and\ncreates only the new BOUND-INPUTS record. It never starts maintenance/services.\n"
from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import sys
import time
import types

B=Path(__file__).parent


def module(path):
    m=types.ModuleType('Root223CurrentMetadata');m.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    return m


def main():
    require_source_bound()
    if not (__debug__ and sys.flags.isolated and sys.dont_write_bytecode):
        raise RuntimeError('isolated_nonoptimized_no_bytecode_required')
    p=argparse.ArgumentParser()
    p.add_argument('--validate-root-current-and-bind',action='store_true',required=True)
    p.add_argument('--source-pins-sha256',required=True)
    args=p.parse_args()
    os.umask(0o077)
    pins_raw=(B/'SOURCE-PINS.json').read_bytes()
    assert hashlib.sha256(pins_raw).hexdigest()==args.source_pins_sha256,'external_source_manifest_changed'
    pins=json.loads(pins_raw)
    verifier=B/'frame_source.py'
    assert hashlib.sha256(verifier.read_bytes()).hexdigest()==pins['source_refs'][str(verifier)]
    module(verifier).verify_manifest(args.source_pins_sha256,frame=B)
    path=B/'root223_metadata.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==pins['source_refs'][str(path)]
    metadata=module(path)
    metadata.require_bound_data(args.source_pins_sha256)
    names=dict(request='ROOT-FRESH-REQUEST.json',source_acceptance='ROOT-223-SOURCE-ACCEPTANCE.json',
               fresh_readback='ROOT-223-FRESH-READBACK.json')
    refs={key:metadata.reference(B/name)for key,name in names.items()}
    records={key:metadata.readref(ref)for key,ref in refs.items()}
    value=metadata.validate_join(records['request'],records['source_acceptance'],records['fresh_readback'],
        now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    result=dict(schema='frw.root.native223-bound-inputs.v1',
        state='ROOT_CURRENT_BOUND_INPUTS_NOT_EXECUTION_GRANT',template_only_no_execution_grant=False,
        binding=value,**refs)
    assert all(metadata.reference(B/names[key])==ref for key,ref in refs.items()),'Root_current_records_changed_during_binding'
    target=B/'ROOT-223-BOUND-INPUTS.json'
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w')as out:
        json.dump(result,out,sort_keys=True,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
    parent=os.open(B,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(parent)
    finally:os.close(parent)
    print(json.dumps(dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),execution_grant=False)))


if __name__=='__main__':main()
