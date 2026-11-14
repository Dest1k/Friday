SOURCE_BOUND = False
def require_source_bound():
    if not SOURCE_BOUND: raise ValueError('native223_source_inputs_UNBOUND_before_current_or_effect')
'Exact source223 finite cache data. Import inert; current admission stays Root-owned.'
from pathlib import Path
import hashlib
import json
import os
import stat
import types

B=Path(__file__).parent
FINAL_SPEC=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE223-MAINTENANCE-FRAME-SOURCE-PREP-20261115/frame-draft/SOURCE-SPEC223.json')
SCHEMA='frw.root223.coherent-after-actual222-source-pins.v1'
DESCRIPTOR_FIELDS={'schema','source_only','execution_grant','current_admission','future_root_authority',
                   'project_roots','dependencies','fixed','actual_rows','project_sources','native_after'}
FIXED_FIELDS={'native_spec','request','private_input','public_input','before_public_input',
              'public_origin','public_delta','static_binding','actual222_binding'}

def require(ok,reason):
    if not ok:
        raise ValueError(reason)

def digest(value):
    return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def cache_path(path):
    require(type(path) is str,'explicit_cache_path_string_required')
    p=Path(path)
    require(p.is_absolute() and str(p).startswith('/home/jericho/.cache/') and
            '/.runtime/' not in path and '..' not in p.parts and str(p)==path,
            'finite_absolute_cache_path_required')
    return p

def cache_raw(path):
    p=cache_path(str(path));a=p.lstat()
    require(stat.S_ISREG(a.st_mode) and a.st_uid==os.getuid() and a.st_nlink==1 and
            not any(q.is_symlink() for q in (p,*p.parents)), 'owned_singlelink_regular_cache_source_required')
    identity=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    raw=p.read_bytes();b=p.lstat()
    require(identity(a)==identity(b),'cache_source_identity_changed')
    return raw

def source_module(name,ref,raw_refs):
    m=types.ModuleType('Root223Data_'+name);m.__file__=ref['path']
    exec(compile(raw_refs[ref['path']],ref['path'],'exec'),m.__dict__)
    return m

def exact_project_inventory(root, expected):
    'Inventory only an explicitly selected 527-file source project, no cache discovery.'
    root=cache_path(root);seen=set()
    require(not root.is_symlink(),'source_project_symlink_root_rejected')
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:
            p=Path(parent)/name;s=p.lstat()
            require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid(),'owned_real_source_project_directory_required')
        for name in files:seen.add(str((Path(parent)/name).relative_to(root)))
    require(seen==set(expected),'exact_selected_527_source_project_inventory_required')

def validate_descriptor(value):
    require(type(value) is dict and set(value)==DESCRIPTOR_FIELDS,'exact_source223_descriptor_fields_required')
    require(value['schema']=='frw.root223.typed-origin-source-descriptor.v1' and
            value['source_only'] is True and value['execution_grant'] is False and
            value['current_admission'] is False and value['future_root_authority']==
            dict(source_acceptance='UNBOUND_ROOT',current='UNBOUND_ROOT',once='UNBOUND_ROOT',grant='UNBOUND_ROOT',clock='UNBOUND_ROOT'),
            'source_descriptor_never_current_authority_required')
    require(set(value['fixed'])==FIXED_FIELDS and set(value['dependencies'])=={'predecessor222','native223_binding'},
            'exact_finite_source_dependencies_required')
    require(set(value['project_roots'])=={'private','public','previous'} and
            set(value['project_sources'])=={'private','public','previous'},'exact_project_roots_required')
    for p in value['project_roots'].values():cache_path(p)
    require(set(value['actual_rows'])=={'request','intent','committed','closure','input','marker','receipt','stamp'},
            'exact_eight_actual_cache_refs_required')
    require(type(value['native_after'])is dict and value['native_after'] and all(type(n)is str and n and not n.startswith('/') and all(x not in ('','.','..')for x in n.split('/'))for n in value['native_after']),
            'exact_two_native_after_cache_sources_required')
    require(value['fixed']['native_spec']['path']==str(FINAL_SPEC),'single_exact_final_SOURCE_SPEC223_required')
    return value

def load(external_manifest_sha256,*,frame):
    require_source_bound()
    'Read explicit source-pinned cache bytes only. Canonical H refs remain opaque.'
    require(digest(external_manifest_sha256),'external_manifest_digest_required')
    require(Path(frame)==B,'exact_loaded_frame_required')
    manifest_raw=cache_raw(B/'SOURCE-PINS.json')
    require(hashlib.sha256(manifest_raw).hexdigest()==external_manifest_sha256,'external_source_manifest_changed')
    manifest=json.loads(manifest_raw)
    require(manifest['schema']==SCHEMA and manifest['runtime_grant'] is False,
            'exact_inert223_source_manifest_required')
    pins=manifest['source_refs'];require(type(pins) is dict,'source_refs_map_required')
    for p,h in pins.items():cache_path(p);require(digest(h),'source_pin_sha256_required')
    def pinned(path):
        path=str(path);require(path in pins,'followed_source_ref_not_in_external_pins')
        raw=cache_raw(path);require(hashlib.sha256(raw).hexdigest()==pins[path],'source_ref_bytes_changed')
        return raw
    for name in ('root223_data.py','root223_projection.py'):pinned(B/name)
    descriptor=json.loads(pinned(B/'ROOT223-DATA-BINDINGS.json'));validate_descriptor(descriptor)
    require(manifest.get('source_spec_ref')==descriptor['fixed']['native_spec'],
            'external_manifest_SOURCE_SPEC223_alias_required')
    refs=(list(descriptor['fixed'].values())+list(descriptor['dependencies'].values())+
          list(descriptor['actual_rows'].values())+list(descriptor['native_after'].values()))
    for flavor in ('private','public','previous'):
        exact_project_inventory(descriptor['project_roots'][flavor],descriptor['project_sources'][flavor])
        for name,r in descriptor['project_sources'][flavor].items():
            require(type(name) is str and name and not name.startswith('/') and
                    all(x not in ('','.','..') for x in name.split('/')),'safe_project_relative_required')
            require(r['path']==str(Path(descriptor['project_roots'][flavor])/name), 'project_ref_must_join_selected_root')
            refs.append(r)
    raw_refs={}
    for r in refs:
        require(type(r) is dict and set(r) in ({'path','sha256'},{'path','sha256','bytes'}), 'exact_source_reference_fields_required')
        require(digest(r['sha256']) and pins.get(r['path'])==r['sha256'],'followed_ref_requires_exact_external_source_pin')
        raw=pinned(r['path']);require('bytes' not in r or type(r['bytes']) is int and len(raw)==r['bytes'], 'source_ref_size_changed')
        raw_refs[r['path']]=raw
    fixed=descriptor['fixed']
    values={k:json.loads(raw_refs[r['path']]) for k,r in fixed.items()}
    binding=values['actual222_binding']
    for role,r in descriptor['actual_rows'].items():
        require(r==dict(path=binding[role]['cache_path'],sha256=binding[role]['sha256'],bytes=binding[role]['bytes']),
                'descriptor_actual_rows_must_join_typed_binding')
    actual_rows={k:raw_refs[r['path']] for k,r in descriptor['actual_rows'].items()}
    predecessor=source_module('predecessor222',descriptor['dependencies']['predecessor222'],raw_refs).validate_actual222(binding,actual_rows)
    require({n:r['sha256'] for n,r in descriptor['project_sources']['previous'].items()}==
            predecessor['values']['input']['project_files'],'genuine_previous525_project_source_pins_required')
    request=values['request'];spec=values['native_spec']
    require(request['current_input']==fixed['private_input'] and request['previous_input']==
            predecessor['current_input'],
            'exact_input_source_request_joins_required')
    require(request['candidate_project']==descriptor['project_roots']['private'] and
            values['public_origin']['project']==descriptor['project_roots']['public'], 'exact_private_public_project_roots_required')
    require(descriptor['project_roots']['previous']=='/home/jericho/.cache/FRW-ASTRA-NATIVE222-ACTUAL-CALLER-GATE-20261114/project',
            'exact_previous_private525_root_required')
    # The pair refs are finite source files within the selected private project.
    for role in ('manifest','patch'):
        r=spec[role];require(r['path'] in raw_refs and r['sha256']==pins.get(r['path']) and
                            len(raw_refs[r['path']])==r['bytes'],'spec_pair_must_be_authenticated_project_source')
    static=source_module('native223_binding',descriptor['dependencies']['native223_binding'],raw_refs).bind_static(
        request_raw=raw_refs[fixed['request']['path']],input_raw=raw_refs[fixed['private_input']['path']],
        manifest_raw=raw_refs[spec['manifest']['path']],patch_raw=raw_refs[spec['patch']['path']],
        predecessor_six=predecessor,actual_rows=actual_rows)
    require(static==values['static_binding'],'exact_STATIC_BINDING223_computed_bytes_join_required')
    require(set(descriptor['native_after'])=={r['path']for r in static['native_files']},'exact_finalmanifest_native_after_scope_required')
    for row in static['native_files']:
        r=descriptor['native_after'][row['path']]
        require(r['sha256']==row['sha256'] and r['bytes']==row['bytes'] and
                len(raw_refs[r['path']])==row['bytes'],'exact_native_after_source_row_required')
    require(values['public_delta']['before']==dict(path=fixed['before_public_input']['path'],
            bytes=len(raw_refs[fixed['before_public_input']['path']]),sha256=fixed['before_public_input']['sha256']) and
            values['public_delta']['after']==dict(path=fixed['public_origin']['path'],
            bytes=len(raw_refs[fixed['public_origin']['path']]),sha256=fixed['public_origin']['sha256']),
            'public_delta_exact_before_after_refs_required')
    project_bytes={f:{n:raw_refs[r['path']] for n,r in descriptor['project_sources'][f].items()} for f in ('private','public')}
    project_modes={f:{n:('100755' if Path(r['path']).lstat().st_mode&0o111 else '100644') for n,r in rows.items()}
                   for f,rows in descriptor['project_sources'].items() if f in ('private','public')}
    helper_ref=dict(path=str(B/'root223_projection.py'),sha256=pins[str(B/'root223_projection.py')])
    projection=source_module('projection',helper_ref,{helper_ref['path']:pinned(helper_ref['path'])}).validate(
        predecessor=predecessor,static_binding=static,request=request,private_input=values['private_input'],
        public_input=values['public_input'],before_public_input=values['before_public_input'],
        public_origin=values['public_origin'],public_delta=values['public_delta'],spec=spec,
        project_bytes=project_bytes,project_modes=project_modes)
    physical=dict(private_project_root=descriptor['project_roots']['private'],public_project_root=descriptor['project_roots']['public'],
                  previous_project_root=descriptor['project_roots']['previous'],private_input_ref=fixed['private_input'],
                  public_input_ref=fixed['public_input'],prospective_receipt_ref=dict(sha256=static['prospective_receipt_sha256'],
                  projection='PURE_PROJECTED_NOT_INSTALLED_METADATA'))
    return dict(descriptor=descriptor,predecessor=predecessor,static_binding=static,native_spec=fixed['native_spec'],
                source_refs=dict(pins),public_origin=values['public_origin'],private_input=values['private_input'],
                public_input=values['public_input'],before_public_input=values['before_public_input'],projection=projection,
                physical_binding=physical,fixed=fixed,request=request,native_spec_value=spec)

def bind_namespace(namespace,external_manifest_sha256):
    data=load(external_manifest_sha256,frame=B);roots=data['descriptor']['project_roots']
    namespace.update(C=Path(roots['private']),S=Path(roots['public']),P=Path(roots['previous']),
                     SPEC=Path(data['native_spec']['path']),AFTER=data['static_binding']['prospective_receipt_sha256'],
                     EXPECTED=data['static_binding']['prospective_receipt_sha256'])
    return data
