#!/usr/bin/python3
"""Finite independent R2 delta controls. No product reads or operational calls."""
import ast, copy, datetime, difflib, hashlib, importlib.util, json, os
from pathlib import Path
import stat, sys, time, types

W=Path(__file__).resolve().parent
B=W.parent
R1=Path(str(B).removesuffix('-R2')+'-R1')
ORIGINAL=Path(str(B).removesuffix('-R2'))
CACHE=Path('/home/jericho/.cache')
START=time.monotonic()
rows=[]

def check(name, value, **details):
    if not value:
        raise AssertionError(name)
    rows.append(dict(name=name,state='PASS',**details))

def data(path):
    p=Path(path)
    assert p.is_absolute() and p.is_relative_to(CACHE), str(p)
    return p.read_bytes()

def sha(path): return hashlib.sha256(data(path)).hexdigest()
def load(path): return json.loads(data(path))
def ref(path): return dict(path=str(path),sha256=sha(path))
def dump(name, value):
    p=W/name
    assert p.parent == W
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
    return ref(p)

def audit(event,args):
    if event in {'subprocess.Popen','socket.connect','socket.bind','sqlite3.connect'}:
        raise AssertionError('forbidden_operation:'+event)
    if event=='open':
        p,mode,flags=args
        if isinstance(p,(str,bytes)):
            path=os.fsdecode(p)
            if path.startswith('/home/jericho/jericho/Friday_rework/.runtime/'):
                raise AssertionError('forbidden_current_H_read')
            if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
                assert Path(path).is_relative_to(W), 'outside_review_write:'+path

def funcs(tree):
    return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

def reject(label, fn, reason=None):
    try:
        fn()
    except m.InvalidBinding as e:
        check(label, reason is None or reason in str(e),reason=str(e))
        return
    raise AssertionError('accepted_negative:'+label)

def main():
    global m
    check('isolated_no_bytecode',sys.flags.isolated and sys.dont_write_bytecode)
    sys.addaudithook(audit)
    pins=load(B/'SOURCE-PINS.json');old=load(R1/'SOURCE-PINS.json')
    check('exact_R2_manifest',sha(B/'SOURCE-PINS.json')=='79faafa439202f0183bf5bda9ae45a96d47c18a92310ef69f8e27ed852b95c7f')
    check('R1_and_b9_manifest_seals_unchanged',sha(R1/'SOURCE-PINS.json')=='cc66b9cb42ec75f5a8af6e1133842976cce1949b030905b1b70590f6e873f90b' and sha(ORIGINAL/'SOURCE-PINS.json')=='b9b388de63d7afd04c0da345275573bffdc7a15b95fbc147a1f421493a5e3368')
    check('all43_historical_refs_unchanged',pins['historical_refs']==old['historical_refs'] and len(pins['historical_refs'])==43)
    manifest=load(B/'R2-DIFF-MANIFEST.json')
    relocated_paths={row['before']['path'] for row in manifest['relocated']}
    retained={p:h for p,h in old['source_refs'].items() if p not in relocated_paths}
    local={p:h for p,h in pins['source_refs'].items() if Path(p).is_relative_to(B)}
    check('manifest_exact_retained1502_local29_total1531',len(retained)==1502 and len(local)==29 and len(pins['source_refs'])==1531 and {p:h for p,h in pins['source_refs'].items() if p not in local}==retained)
    check('all29_local_source_hashes',all(sha(p)==h for p,h in local.items()))
    check('diff_manifest_joins_exact_R1_R2',manifest['original_manifest']==ref(R1/'SOURCE-PINS.json') and manifest['final_manifest']==ref(B/'SOURCE-PINS.json') and manifest['retained_source_refs']==1502 and manifest['historical_refs_unchanged'] is True)
    relocated={str(Path(p).relative_to(R1)):(p,h) for p,h in old['source_refs'].items() if p in relocated_paths}
    expected_paths={p for p in old['source_refs'] if Path(p).is_relative_to(R1) and p!=str(R1/'controls-work/focused_controls.py')}
    check('exact28_relocations',len(relocated)==28 and len(manifest['relocated'])==28 and relocated_paths==expected_paths)
    for row in manifest['relocated']:
        name=Path(row['before']['path']).relative_to(R1)
        check('relocated_pin/'+str(name),row['before']==dict(path=str(R1/name),sha256=old['source_refs'][str(R1/name)]) and row['after']==dict(path=str(B/name),sha256=local[str(B/name)]))
    changed=[]
    for name in relocated:
        if data(B/name)!=data(R1/name): changed.append(name)
    check('only_new_frozen_source_is_saved_shape_controls',set(local)-{str(B/n) for n in relocated}=={str(B/'saved-shape-work/saved_shape_controls.py')})
    check('diff_manifest_exact_changed_files',set(changed)=={Path(x['after']['path']).name for x in manifest['changed']} and len(changed)==11)
    for row in manifest['changed']:
        name=Path(row['after']['path']).relative_to(B)
        expected=''.join(difflib.unified_diff(data(R1/name).decode().splitlines(True),data(B/name).decode().splitlines(True),fromfile='consumed-R1/'+str(name),tofile='source-R2/'+str(name)))
        check('exact_saved_diff/'+str(name),row['before']==ref(R1/name) and row['after']==ref(B/name) and row['diff']==ref(B/(str(name)+'.diff')) and data(row['diff']['path']).decode()==expected)
    oldtree=ast.parse(data(R1/'root209_metadata.py'));newtree=ast.parse(data(B/'root209_metadata.py'))
    before,after=funcs(oldtree),funcs(newtree)
    check('only_added_definition_sized_reader',set(after)-set(before)=={'read_sized_source_ref'} and not(set(before)-set(after)))
    for name in before:
        target=copy.deepcopy(after[name])
        if name=='validate_join':
            calls=[n for n in ast.walk(target) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read_sized_source_ref']
            check('exact_two_gate_calls',len(calls)==2 and {ast.unparse(n.args[0]) for n in calls}=={"row['result']","row['process_record']"})
            for call in calls:call.func.id='readref'
        check('existing_definition_unchanged/'+name,ast.dump(target)==ast.dump(before[name]))
    stripped=copy.deepcopy(newtree)
    stripped.body=[n for n in stripped.body if not(isinstance(n,ast.FunctionDef) and n.name=='read_sized_source_ref')]
    for n in ast.walk(stripped):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read_sized_source_ref':n.func.id='readref'
    check('entire_metadata_AST_only_adapter_delta',ast.dump(stripped)==ast.dump(oldtree))
    oldactor=data(R1/'run_native209_once.py').decode().replace(str(R1),str(B))
    check('actor_only_metadata_pin',data(B/'run_native209_once.py').decode()==oldactor.replace(sha(R1/'root209_metadata.py'),sha(B/'root209_metadata.py')))
    for name in relocated:
        if name.endswith('.py') and name not in ('root209_metadata.py','run_native209_once.py','frame_controls.py'):
            check('unchanged_operational_source/'+name,data(B/name).decode()==data(R1/name).decode().replace(str(R1),str(B)))
    for p in B.glob('*TEMPLATE.json'):
        expected=json.loads(json.dumps(load(R1/p.name)).replace(str(R1),str(B)))
        actual=load(p)
        if p.name=='ROOT-209-FRESH-ADMISSION-TEMPLATE.json':
            expected['actor']=ref(B/'run_native209_once.py')
        check('template_exact_relocation_policy_retained/'+p.name,actual==expected)
    commands=load(B/'ROOT-FUTURE-COMMANDS.json')
    check('command_binder_and_actor_target_R2',commands['commands']['metadata_binder'][-2:]==[str(B/'root209_metadata.py'),'--validate-and-bind'] and commands['commands']['once_actor'][-2:]==[str(B/'run_native209_once.py'),'--execute-once-root-accepted-209'])
    spec=importlib.util.spec_from_file_location('independentR2metadata',B/'root209_metadata.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    fixture=W/'fixture.json';fixture.write_bytes(b'{"n":1}\n');fixture.chmod(0o600)
    first={**ref(fixture),'bytes':len(data(fixture))}
    check('own_positive_sized_ref',m.read_sized_source_ref(first)=={'n':1})
    check('general_readref_still_strict2',m.readref({k:v for k,v in first.items() if k!='bytes'})=={'n':1})
    reject('general_reader_rejects_sized3',lambda:m.readref(first),'exact_reference_fields_required')
    variants=[('not_dict',None),('dict_subclass',type('Subclass',(dict,),{})(first)),('extra',dict(first,grant=False)),('no_bytes',{k:v for k,v in first.items() if k!='bytes'})]
    variants += [('bytes_'+name,dict(first,bytes=x)) for name,x in [('false',False),('true',True),('zero',0),('negative',-1),('float',8.0),('string','8'),('null',None),('int_subclass',type('IntSubclass',(int,),{})(8)),('wrong_positive',len(data(fixture))+1),('huge',2**128)]]
    variants += [('relative',dict(first,path='fixture.json')),('path_wrong_type',dict(first,path=fixture)),('hash_wrong_type',dict(first,sha256=1)),('hash_invalid',dict(first,sha256='f'*63)),('hash_uppercase',dict(first,sha256='A'*64)),('hash_changed',dict(first,sha256='0'*64))]
    for name,row in variants:reject('helper_negative/'+name,lambda row=row:m.read_sized_source_ref(row))
    symlink=W/'link.json';symlink.symlink_to(fixture)
    reject('helper_rejects_file_symlink',lambda:m.read_sized_source_ref(dict(first,path=str(symlink))),'owned_regular_singlelink_required')
    symlink.unlink()
    directory=W/'real-parent';directory.mkdir(mode=0o700);inner=directory/'inner.json';inner.write_bytes(data(fixture));inner.chmod(0o600)
    linkparent=W/'linked-parent';linkparent.symlink_to(directory,target_is_directory=True)
    reject('helper_rejects_parent_symlink',lambda:m.read_sized_source_ref(dict(first,path=str(linkparent/'inner.json'))),'real_parent_required')
    linkparent.unlink();inner.unlink();directory.rmdir()
    hard=W/'hard.json';os.link(fixture,hard)
    reject('helper_rejects_hardlink',lambda:m.read_sized_source_ref(first),'owned_regular_singlelink_required')
    hard.unlink()
    original_os=m.os;m.os=types.SimpleNamespace(getuid=lambda:os.getuid()+1)
    try:reject('helper_rejects_owner_mismatch',lambda:m.read_sized_source_ref(first),'owned_regular_singlelink_required')
    finally:m.os=original_os
    original_read=m.readref
    def change_after_strict(row):
        value=original_read(row);fixture.write_bytes(b'{"n":2}\n');return value
    m.readref=change_after_strict
    try:reject('second_read_hash_rechecked_after_strict_reader',lambda:m.read_sized_source_ref(first),'sized_source_reference_hash_changed')
    finally:m.readref=original_read;fixture.write_bytes(b'{"n":1}\n')
    def resize_after_strict(row):
        value=original_read(row);fixture.write_bytes(b'{"n":2,"more":true}\n');return value
    m.readref=resize_after_strict
    try:reject('actual_raw_size_rechecked_after_strict_reader',lambda:m.read_sized_source_ref(first),'sized_source_reference_byte_length_changed')
    finally:m.readref=original_read;fixture.write_bytes(b'{"n":1}\n')
    gates=m.readref(m.FIXED['gates_summary']);gate_rows=[]
    for kind in ('operational-success','operational-rollback'):
        for slot in ('result','process_record'):
            row=gates['runs'][kind][slot];gate_rows.append(row)
            check('genuine_producer_sized3/'+kind+'/'+slot,set(row)=={'path','sha256','bytes'} and type(row['bytes']) is int and row['bytes']>0 and len(data(row['path']))==row['bytes'] and sha(row['path'])==row['sha256'] and m.read_sized_source_ref(row)==load(row['path']),actual_bytes=row['bytes'])
    q=load(R1/'ROOT-FRESH-REQUEST.json');acceptance=load(R1/'ROOT-209-SOURCE-ACCEPTANCE.json');snapshot=load(R1/'ROOT-209-FRESH-READBACK.json')
    slots='marker source_receipt stamp configuration profile launcher native_unit previous_input current_input predecessor_request target_receipt candidate_input'.split()
    check('all12_saved_builder_request_ref_shapes_strict2',all(type(q[k]) is dict and set(q[k])=={'path','sha256'} for k in slots))
    m.B=R1
    for kind in ('operational-success','operational-rollback'):
        for slot in ('result','process_record'):
            mutated=copy.deepcopy(gates);mutated['runs'][kind][slot]['bytes']+=1
            seen=[]
            def inject_gate(row):
                if row==m.FIXED['gates_summary']:return copy.deepcopy(mutated)
                assert Path(row['path']).is_relative_to(CACHE)
                seen.append(row)
                return original_read(row)
            m.readref=inject_gate
            try:reject('actual_validate_join_rejects_size_drift/'+kind+'/'+slot,lambda:m.validate_join(q,acceptance,snapshot,now=0,boot_id='UNUSED'),'sized_source_reference_byte_length_changed')
            finally:m.readref=original_read
            check('negative_join_never_reads_H/'+kind+'/'+slot,all(Path(row['path']).is_relative_to(CACHE) for row in seen))
    proof=load(B/'saved-shape-work/RESULT.json')
    check('saved_connected_proof_hashes',sha(B/'saved-shape-work/RESULT.json')=='7b965979e12bbeb0a36fd2e0b0cd0808c02f7e7b662f868c3f7905cff7dff3a9' and all(ref(proof[k]['path'])==proof[k] for k in ('metadata','script','matrix','focused_controls','connected_saved_probe')))
    probe=load(proof['connected_saved_probe']['path']);strict=probe['strict_reference_reads'];shape_matrix=load(proof['matrix']['path'])
    check('saved_positive_real_join_binder_loader_is_explicitly_historical',probe['direct_join_equals_memory_binder_equals_actor_loader'] is True and probe['R2_output_binding']=='UNBOUND' and probe['Root_verdict_files_created']==0 and probe['actual_current_or_runtime_or_admission_credit'] is False and probe['current_time_or_boot_read'] is False and probe['sized_read_total']==12 and probe['sized_refs_per_entry']==4 and len(strict)==133)
    distinct={row['reference']['path']:row['reference'] for row in strict if row['kind']=='strict2'}
    check('saved_trace_all_strict2_shapes',all(set(row)=={'path','sha256'} and type(row['path']) is str and type(row['sha256']) is str and Path(row['path']).is_relative_to(CACHE) for row in distinct.values()))
    check('saved_trace_cached_refs_hashes',all(ref(row['path'])==row for row in distinct.values()),distinct_cached_refs=len(distinct))
    check('saved_matrix_all10_documents_authentic',len(shape_matrix['documents'])==10 and all(ref(row['file']['path'])==row['file'] for row in shape_matrix['documents']) and shape_matrix['additional_discoverable_saved_shape_mismatches']==[])
    evidence=load(B/'CONSUMED-R1-ROOT-EVIDENCE.json')
    check('consumed_R1_reconciliation_cached_refs_authentic',all(ref(v['path'])==v for v in evidence.values() if type(v) is dict and set(v)=={'path','sha256'}))
    root_files=['FUTURE-EXECUTION','ROOT-FRESH-REQUEST.json','ROOT-209-SOURCE-ACCEPTANCE.json','ROOT-209-RUNTIME-AUTHORITY.json','ROOT-209-FRESH-ADMISSION.json','ROOT-209-BOUND-INPUTS.json','ROOT-NATIVE209-LIVE-OPERATION.json']
    check('R2_Root_outputs_remain_UNBOUND',all(not (B/n).exists() for n in root_files) and pins['runtime_grant'] is False)
    fixture.unlink()
    return dump('INDEPENDENT-CONTROLS.json',dict(state='PASS_INDEPENDENT_R2_CONNECTED_SOURCE_DELTA',controls_count=len(rows),rows=rows,elapsed_seconds=time.monotonic()-START,manifest=ref(B/'SOURCE-PINS.json'),metadata=ref(B/'root209_metadata.py'),read_scope='cached saved source/metadata and owned disposable fixtures only',saved_positive_probe_reused_not_rerun=True,own_current_H_or_operational_effects=0,source_gates_reexecuted=False,R2_Root_binding='UNBOUND'))

if __name__=='__main__':
    os.umask(0o077)
    print(json.dumps(main(),sort_keys=True))
