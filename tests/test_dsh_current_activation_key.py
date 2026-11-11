"""T2 consumes its signed pending D/cycle, independent of caller P or clock."""
import copy
import json
from pathlib import Path
import pytest
from test_dsh_current_availability import candidate, env, make_proof, save
from friday_admin_controls import worker_declarations as dec


@pytest.mark.parametrize('variation',['copy-path','json-format','different-proof','new-operation-clock'])
def test_t2_consumed_pending_edge_cannot_be_reopened_with_another_proof(candidate,variation):
    f=candidate;p=make_proof(f)
    active=copy.deepcopy(f.c);active['current_availability']['proof']=save(f.root/'activation-proof.json',p)
    bundle={'schema':dec.DSH_CURRENT_PROOF_SCHEMA,'runtime_after':active}
    name=dec.dsh_current_transaction_name(bundle)
    expected=dec.fingerprint({'schema':'friday.dsh-current-activation-key.v1',
        'declaration':active['current_availability']['declaration'],
        'cycle':active['current_availability']['cycle']})
    assert name=='ordinary-dsh-current-activation-'+expected
    consumed=f.root/name;consumed.mkdir(mode=0o700)
    changed=copy.deepcopy(bundle)
    if variation=='copy-path':
        changed['runtime_after']['current_availability']['proof']=save(f.root/'copied-proof.json',p)
    elif variation=='json-format':
        path=f.root/'reformatted-proof.json';path.write_text(json.dumps(p,indent=3));path.chmod(0o600)
        import hashlib
        changed['runtime_after']['current_availability']['proof']={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    elif variation=='different-proof':
        p['observed_mono']+=.00001
        changed['runtime_after']['current_availability']['proof']=save(f.root/'different-proof.json',p)
    else:
        # Real request.clock is outside the bundle/key; a new operation's
        # budget cannot reset the signed pending edge's consumption.
        changed['clock']={'path':str(f.root/'new-clock.json'),'sha256':'a'*64}
    assert dec.dsh_current_transaction_name(changed)==name
    assert (f.root/dec.dsh_current_transaction_name(changed)).is_dir()
