"""New source refs only; preserve all original metadata and target afterimages."""
from pathlib import Path
import copy
import hashlib
import json
import os

BASE = Path(__file__).resolve().parents[1]
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115')
SELECTED_SHA = '1b6ed0f0c0574afebd2619d97fe31f4a7172ce5413fd32b35b8f8f72604e47f1'


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def put(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return ref(path)


def rebind():
    os.umask(0o077)
    original_selected = ORIGINAL / 'inputs/SELECTED-INPUTS.json'
    assert ref(original_selected)['sha256'] == SELECTED_SHA
    selected = json.loads(original_selected.read_bytes())
    result = copy.deepcopy(selected)
    for variant, refs in selected['variants'].items():
        for source in refs.values():
            assert ref(Path(source['path'])) == source
        plan = json.loads(Path(refs['plan_ref']['path']).read_bytes())
        prepared = json.loads(Path(refs['prepared_ref']['path']).read_bytes())
        prepared['supervisor_ref'] = ref(BASE / 'host/ownc_namespace_supervisor.py')
        prepared['gdb_driver_ref'] = ref(BASE / 'driver/ownc_gdb.py')
        out = BASE / 'inputs' / variant
        out.mkdir(mode=0o700)
        pref = put(out / 'PREPARED.json', prepared)
        plan['prepared_ref'] = pref
        plan['source_refs']['supervisor'] = prepared['supervisor_ref']
        plan['source_refs']['gdb_driver'] = prepared['gdb_driver_ref']
        plan['readonly_roots'] = [str(BASE), *plan['readonly_roots']]
        result['variants'][variant] = dict(prepared_ref=pref,
            plan_ref=put(out / 'STATIC-PLAN.json', plan))
    return put(BASE / 'inputs/SELECTED-INPUTS.json', result)


if __name__ == '__main__':
    print(json.dumps(rebind(), sort_keys=True))
