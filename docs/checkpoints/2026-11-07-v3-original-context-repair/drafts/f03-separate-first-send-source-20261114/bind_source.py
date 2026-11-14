"""Pure source binder. Returns bytes; no files, observations, decisions or effects.
Only the exact reviewed UNBOUND template and F03_CONTRACT literal can change.
"""
import ast,hashlib,json
TEMPLATE_SHA='63b85203f5b6574681c61cab05f7dc167af10fa2274e77d193dbade45c5cfc53'
ADAPTER={'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-MISSING-FIRST-SEND-CONTRACT-CANDIDATE-20261114/candidate/adapter.py', 'bytes': 12039, 'sha256': '0ed59a2f810c2f59aecdd0bb70d3e24f574e99e04171d73f2cb4bfb1b48b1d9a'}
CURRENT={'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-MISSING-FIRST-SEND-CONTRACT-CANDIDATE-20261114/candidate/current/current221.py', 'bytes': 43312, 'sha256': 'cc3af49e63f401e312c79009840fffcc5a6d42f1e425275532386737e883ddf0'}
def bind_source(raw,c):
    if type(raw)is not bytes or hashlib.sha256(raw).hexdigest()!=TEMPLATE_SHA:
        raise ValueError('F03_EXACT_REVIEWED_UNBOUND_TEMPLATE_REQUIRED')
    if type(c)is not dict or c.get('status')!='ROOT_BOUND_EXACT_F03' or c.get('adapter')!=ADAPTER or c.get('current_gate')!=CURRENT or c.get('run_id')!='f03-ods-formulas-original-221-20261114' or c.get('scenario_sha256')!='98c0c37105804e600a47eed83e6ba7504849333054e409c6af6080ed5496dd4f' or type(c.get('root_current_review'))is not dict:
        raise ValueError('F03_EXPLICIT_ROOT_BOUND_CURRENT_CONTRACT_REQUIRED')
    text=raw.decode();tree=ast.parse(text)
    nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='F03_CONTRACT'for t in n.targets)]
    if len(nodes)!=1:raise ValueError('F03_EXACT_SINGLE_BINDING_SEAM_REQUIRED')
    n=nodes[0];lines=text.splitlines(keepends=True);lines[n.lineno-1:n.end_lineno]=['F03_CONTRACT = '+repr(json.loads(json.dumps(c,allow_nan=False)))+'\n']
    bound=''.join(lines).encode();ast.parse(bound)
    return bound
