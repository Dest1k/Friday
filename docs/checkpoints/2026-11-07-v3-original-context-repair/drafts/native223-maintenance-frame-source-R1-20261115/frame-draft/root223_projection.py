'Pure source223 inventory/origin/projection joins. No IO or execution authority.'
import hashlib
import json

COMMIT = 'UNBOUND_NATIVE223_COMMIT'
LAYER = 'ordinary-f04-owned-ingress-stop-terminal-after-source222'
HELPER = 'scripts/friday_ordinary_install.py'
PAIR = {'patches/hermes/'+LAYER+'-manifest.json', 'patches/hermes/'+LAYER+'.patch'}
PRIVATE_HELPER = 'UNBOUND_NATIVE223_PRIVATE_HELPER'
PUBLIC_HELPER = 'UNBOUND_NATIVE223_PUBLIC_HELPER'
BEFORE_HELPER = '06fd2ab2ab96f9bced79a6d76a74fdc3f6886d468dcd8525a28422d89213ad43'

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()

def relative(name):
    require(type(name) is str and name and not name.startswith('/') and
            all(p not in ('','.','..') for p in name.split('/')), 'safe_project_relative_path_required')

def exact_delta(before, after):
    require(len(before)==525 and len(after)==527, 'exact_525_to527_inventory_required')
    require(set(after)-set(before)==PAIR and not set(before)-set(after), 'exact_new_pair_no_removal_required')
    require({p for p in before if before[p]!=after[p]}=={HELPER}, 'only_helper_changed_required')

def validate(*, predecessor, static_binding, request, private_input, public_input,
             before_public_input, public_origin, public_delta, spec, project_bytes,
             project_modes):
    'All byte maps are supplied by a source-pinned finite cache reader.'
    require(predecessor['complete_eight'] is True and predecessor['current_admission'] is False and
            predecessor['execution_grant'] is False, 'closed_actual8_not_current_required')
    previous=predecessor['values']['input']
    p, s, oldp, olds=(x['project_files'] for x in
                     (private_input,public_input,previous,before_public_input))
    exact_delta(oldp,p);exact_delta(olds,s)
    require(oldp[HELPER]==BEFORE_HELPER and p[HELPER]==PRIVATE_HELPER and
            s[HELPER]==PUBLIC_HELPER and PRIVATE_HELPER!=PUBLIC_HELPER,
            'genuine_private525_and_distinct527_flavors_required')
    require({k:v for k,v in private_input.items() if k!='project_files'}==
            {k:v for k,v in public_input.items() if k!='project_files'}, 'public_private_nonproject_inputs_unchanged')
    require({k:v for k,v in before_public_input.items() if k!='project_files'}==
            {k:v for k,v in public_input.items() if k!='project_files'}, 'public525_nonproject_inputs_unchanged')
    require(public_origin['schema']=='frw.Root.native223.public-origin-committed-project.v1' and
            public_origin['commit']==COMMIT and public_origin['origin']=='https://github.com/Dest1k/Friday.git' and
            public_origin['branch']=='main' and public_origin['file_count']==527 and
            public_origin['only_source_project_no_runtime_or_DB'] is True and
            public_origin['source_only_not_admission'] is True and public_origin['project_files']==s,
            'exact_Root_public527_capture_origin_required')
    require(set(public_origin['git_blob_ids'])==set(public_origin['git_modes'])==set(s),
            'exact_public_git_oid_modes_inventory_required')
    require(set(project_bytes)==set(project_modes)=={'private','public'}, 'two_explicit_project_sources_required')
    for flavor,inventory in (('private',p),('public',s)):
        require(set(project_bytes[flavor])==set(project_modes[flavor])==set(inventory),
                'exact_finite_project_source_set_required:'+flavor)
        for name, digest in inventory.items():
            relative(name);raw=project_bytes[flavor][name]
            require(type(raw) is bytes and sha(raw)==digest, 'project_source_sha_changed:'+flavor+':'+name)
            mode=project_modes[flavor][name]
            require(mode in ('100644','100755'), 'regular_project_git_mode_required')
            if flavor=='public':
                oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                require(oid==public_origin['git_blob_ids'][name] and mode==public_origin['git_modes'][name],
                        'Root_public_git_blob_or_mode_changed:'+name)
    require(sum(map(len,project_bytes['public'].values()))==public_origin['total_bytes'],
            'public_total_bytes_changed')
    differences=sorted(n for n in p if p[n]!=s[n])
    historical=sorted(n for n in oldp if oldp[n]!=olds[n])
    require(differences==historical and len(differences)==28 and
            sum(n.endswith('-manifest.json') for n in differences)==15,
            'retained_28_flavors_15metadata_13code_required')
    require(public_origin['public_private_differences']==
            [dict(path=n,public=s[n],private=p[n]) for n in differences],
            'exact_public_private_origin_rows_required')
    require(public_delta['schema']=='frw.Root.native223.public-counterpart-exact-delta.v1' and
            public_delta['changed']==[HELPER] and public_delta['added']==sorted(PAIR) and
            public_delta['removed']==[] and public_delta['private_public_different_paths']==28 and
            public_delta['metadata_manifests']==15 and public_delta['private_flavor_code_paths']==13 and
            public_delta['old_public_private_counterpart_differences_retained'] is True and
            public_delta['expected_only_new_delta'] is True and public_delta['execution_grant'] is False,
            'exact_public_delta_record_required')
    require(spec['schema']=='frw.f04223.pair-spec.v1' and spec['counts']==dict(added=static_binding['native_additions'],after_layers=223,after_native=static_binding['after_native'],after_project=527,base=17730,before_layers=222,before_native=17893,before_project=525,modified=static_binding['native_targets']-static_binding['native_additions'],plugins=52,retained=17893-(static_binding['native_targets']-static_binding['native_additions'])) and
            spec['selected_targets']==len(spec['native_files'])+6 and spec['layer']==LAYER and
            spec['outer_schema']=='friday.ordinary-telegram-source-update.v46' and
            spec['successor_schema']=='friday.current-source-native-successor.v25' and
            all(spec[k] is False for k in ('current_authority','execution_grant','installed223')) and
            spec['source_only'] is True and spec['native_files']==static_binding['native_files'],
            'exact_inert_source_spec223_required')
    require(spec['manifest']['sha256']==p[spec['manifest_rel']]==s[spec['manifest_rel']] and
            spec['patch']['sha256']==p['patches/hermes/'+LAYER+'.patch']==s['patches/hermes/'+LAYER+'.patch'],
            'source_spec_private_public_pair_join_required')
    require(request['candidate_project']==static_binding['candidate_project'] and
            static_binding['selected_target_count']==len(spec['native_files'])+6 and static_binding['current_admission'] is False and
            static_binding['execution_grant'] is False and static_binding['once']=='UNBOUND_ROOT' and
            static_binding['clock']=='UNBOUND_ROOT', 'exact_static223_not_current_required')
    return dict(schema='frw.root223.typed-source-origin-projection.v1', source_only=True,
                current_admission=False,execution_grant=False,public_origin_commit=COMMIT,
                public_origin_capture_verified=True,public_git_blob_oid_modes_verified=True,
                private_project=527,public_project=527,before_project=525,
                native=static_binding['after_native'],layers=223,plugins=52,base=17730,native_targets=static_binding['native_targets'],CAS_targets=static_binding['selected_target_count'],
                public_private_flavors=28,metadata_flavors=15,code_flavors=13,
                expected_receipt_sha256=static_binding['prospective_receipt_sha256'],
                fresh_current='UNBOUND_ROOT',source_acceptance='UNBOUND_ROOT',once='UNBOUND_ROOT',clock='UNBOUND_ROOT')
