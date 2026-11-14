#!/usr/bin/env python3
"""Finite SOURCE binding. Does not prepare a request, read H, install or admit effects."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT=Path(__file__).resolve().parent
CAPTURE=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE223-ACTUAL222-PREDECESSOR-CAPTURE-20261115/ACTUAL222-ROOT-CANONICAL-CAPTURE.json')
CAPTURE_SHA='32b80537a4e8c51246b21830b80b3fb48d8e3d6ffdc600006e660d9f7debca25'
LAYER='ordinary-f04-owned-ingress-stop-terminal-after-source222'
MANIFEST='patches/hermes/'+LAYER+'-manifest.json'
PATCH='patches/hermes/'+LAYER+'.patch'
TEMPLATE_PINS = {
    'private/scripts/friday_ordinary_install.py': '259d816daa6c9fa2a2a1b869118bfa0bdb77519a780993f53e77811cec4c8736',
    'public/scripts/friday_ordinary_install.py': '3fe220895b03f19bafe0fa9f0cf0e32d9299d772f48fd6834eaeef704e008db4',
    'publication/build-layer-publication-request.py': 'f09a8d75165463c3de1311137c8e533b0d4ed3746410b01c2cd82e9e7b7c29cd',
    'publication/friday_v3_layer_publication.py': '62e98b3ffd51dc24611ab93426b2083dda50ec4eed36cae507739835d5ef8931',
}

def require(ok,reason):
    if not ok: raise ValueError(reason)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def enc(value): return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def sha_pin(s): return type(s) is str and len(s)==64 and all(c in '0123456789abcdef' for c in s)
def unique(pairs):
    d={}
    for k,v in pairs:
        require(k not in d,'duplicate_json_key');d[k]=v
    return d

def relative(name):
    require(type(name) is str and bool(name),'relative_path_required')
    p=Path(name)
    require(bool(p.parts) and not p.is_absolute() and name==p.as_posix() and '\\' not in name
        and not any(x in ('.','..','.git') for x in p.parts),'unsafe_relative_path')
    return name

def source_bytes(ref):
    require(type(ref) is dict and set(ref)=={'path','sha256'} and type(ref['path']) is str and bool(ref['path']) and sha_pin(ref['sha256']), 'exact_source_reference_required')
    p=Path(ref['path'])
    require(p.is_absolute() and str(p)==ref['path'] and str(p)==os.path.normpath(str(p))
        and p.is_relative_to(Path('/home/jericho/.cache')), 'protected_cache_source_only')
    # Check ancestors from root down before touching a descendant through a link.
    for a in reversed((p,*p.parents)):
        require(not a.is_symlink(),'source_symlink_refused')
    st=p.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_uid==os.getuid() and st.st_nlink==1,'owned_regular_source_required')
    raw=p.read_bytes();end=p.lstat()
    require((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==
        (end.st_dev,end.st_ino,end.st_size,end.st_mtime_ns,end.st_ctime_ns), 'source_identity_changed')
    require(sha(raw)==ref['sha256'],'source_hash_changed')
    return raw,(st.st_dev,st.st_ino)

def predecessor():
    raw,_=source_bytes({'path':str(CAPTURE),'sha256':CAPTURE_SHA})
    cap=json.loads(raw,object_pairs_hook=unique)
    objects={}
    for role in ('request','input','receipt','stamp','marker','intent','committed'):
        ref=cap['roles'][role];p=Path(ref['cache_path'])
        require(p.is_relative_to(CAPTURE.parent/'actual222'),'genuine222_cache_role_changed')
        b,_=source_bytes({'path':str(p),'sha256':ref['sha256']});require(len(b)==ref['bytes'],'genuine222_role_bytes_changed')
        objects[role]=json.loads(b,object_pairs_hook=unique)
    require(len(objects['input']['project_files'])==525 and len(objects['receipt']['layers'])==222
        and len(objects['receipt']['files'])==17893,'genuine222_counts_changed')
    return cap,objects

def validate_record(record):
    """Pure validation after finite explicit cache leaves; never resolve canonical/H refs."""
    require(type(record) is dict and set(record)=={'schema','layer_name','manifest','patch','afterimages'},'exact_bind_record_required')
    require(record['schema']=='friday.source223.frozen-bind.v1' and record['layer_name']==LAYER,'selected_layer_required')
    cap,objects=predecessor()
    manifest_raw,manifest_id=source_bytes(record['manifest']);patch_raw,patch_id=source_bytes(record['patch'])
    manifest=json.loads(manifest_raw,object_pairs_hook=unique)
    require(type(manifest) is dict and manifest.get('patch')==PATCH and manifest.get('patch_sha256')==sha(patch_raw),'selected_patch_binding_changed')
    require(manifest.get('base_commit')==objects['receipt']['commit'],'native_base_commit_changed')
    require(type(manifest.get('files')) is list and bool(manifest['files']),'nonempty_native_scope_required')
    after=record['afterimages'];require(type(after) is dict,'exact_afterimages_required')
    native={};identities={manifest_id,patch_id};require(len(identities)==2,'source_alias_refused')
    for row in manifest['files']:
        require(type(row) is dict and set(row)=={'path','before_sha256','sha256','bytes','mode','new_file'},'exact_native_row_required')
        n=relative(row['path']);require(n not in native,'repeated_native_path')
        require(row['mode']=='100644' and type(row['new_file']) is bool and type(row['bytes']) is int and row['bytes']>=0
            and sha_pin(row['sha256']),'malformed_native_tuple')
        prior=objects['receipt']['files'].get(n)
        require(row['new_file'] is (prior is None) and row['before_sha256']==(prior['sha256'] if prior else None),'genuine222_native_before_changed')
        require(row['before_sha256']!=row['sha256'],'unchanged_native_row')
        require(n in after,'missing_native_afterimage')
        raw,identity=source_bytes(after[n]);require(identity not in identities,'source_alias_refused');identities.add(identity)
        require(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'native_afterimage_changed')
        native[n]=(row['before_sha256'],row['sha256'],row['bytes'],row['new_file'])
    require(set(after)==set(native),'foreign_native_afterimage')
    # Actual patch application and preimage validation remain the ordinary consumer's gate.
    diff_paths=[]
    for a,b in re.findall(rb'^diff --git a/(\S+) b/(\S+)$',patch_raw,re.M):
        require(a==b,'patch_rename_refused');diff_paths.append(relative(a.decode('utf-8')))
    require(len(diff_paths)==len(set(diff_paths)) and set(diff_paths)==set(native),'patch_native_scope_changed')
    expected_prereq={n:h for n,h in objects['input']['project_files'].items() if n.startswith('patches/hermes/') and n.endswith('.patch')}
    require(manifest.get('prerequisites')==expected_prereq,'genuine222_layer_prerequisites_changed')
    require(MANIFEST not in objects['input']['project_files'] and PATCH not in objects['input']['project_files'],'layer_already_installed')
    return {'manifest':sha(manifest_raw),'patch':sha(patch_raw),'native':native,'capture':cap}

def replace_constant(text,name,value,expected):
    tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
    require(len(nodes)==1,'single_bind_constant_required:'+name);node=nodes[0]
    require(ast.literal_eval(node.value)==expected,'draft_binding_changed:'+name)
    lines=text.splitlines(True);lines[node.lineno-1:node.end_lineno]=[name+' = '+repr(value)+'\n'];return ''.join(lines)

def bind(record,output):
    facts=validate_record(record)
    output=Path(output);require(output.is_absolute() and output.parent==ROOT and output.name.startswith('bound-source223-'), 'own_bound_output_required')
    require(not output.exists(),'bound_output_already_exists')
    templates={}
    for rel,pin in TEMPLATE_PINS.items():
        raw,_=source_bytes({'path':str(ROOT/rel),'sha256':pin});templates[rel]=raw
    prepared={}
    for kind in ('private','public'):
        rel=kind+'/scripts/friday_ordinary_install.py';text=templates[rel].decode()
        for suffix,key,old in [('MANIFEST','manifest','UNBOUND'),('PATCH','patch','UNBOUND'),('NATIVE','native',None)]:
            text=replace_constant(text,'CURRENT_SOURCE_TWENTY_FIFTH_'+suffix,facts[key],old)
        ast.parse(text);prepared[rel]=text.encode()
    rel='publication/friday_v3_layer_publication.py';text=templates[rel].decode()
    for suffix,key in [('MANIFEST','manifest'),('PATCH','patch')]:
        text=replace_constant(text,'CURRENT_SOURCE_TWENTY_FIFTH_'+suffix+'_SHA256',facts[key],'UNBOUND')
    ast.parse(text);prepared[rel]=text.encode()
    rel='publication/build-layer-publication-request.py';prepared[rel]=templates[rel]
    # All inputs validated before creating this strictly new source-only result tree.
    output.mkdir(mode=0o700)
    for rel,raw in prepared.items():
        p=output/rel;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(raw);p.chmod(0o600)
    result={'schema':'friday.source223.bound-source-result.v1','state':'BOUND_SOURCE_ONLY_NOT_PREFLIGHT_OR_ADMISSION',
        'input_record':record,'genuine222_capture_sha256':CAPTURE_SHA,'manifest_sha256':facts['manifest'],'patch_sha256':facts['patch'],
        'native':facts['native'],'expected_after_counts':{'base':17730,'layers':223,'native':17893+sum(int(r[3]) for r in facts['native'].values()),'plugins':52,'project':527},
        'journal_target_count':len(facts['native'])+6,'files':{rel:{'path':str(output/rel),'sha256':sha(raw)} for rel,raw in prepared.items()},
        'remaining':['Build exact private/public527 inventories without overwriting historical counterparts; private before helper remains06fd2.',
            'Generate final current input and request only after helper hashes settle; dynamic pins avoid self-reference.',
            'Run actual candidate builder+explicit/default ordinary consumers, negative controls and mandatory final gates/review.',
            'Root alone may recheck mutable actual CAS/admission/custody/quiescence/clocks and authorize later effect.']}
    (output/'BIND-RESULT.json').write_bytes(enc(result));(output/'BIND-RESULT.json').chmod(0o600)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--record',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rec=json.loads(a.record.read_bytes(),object_pairs_hook=unique)
    result=bind(rec,a.output);print(json.dumps({'state':result['state'],'output':str(a.output)},sort_keys=True))
