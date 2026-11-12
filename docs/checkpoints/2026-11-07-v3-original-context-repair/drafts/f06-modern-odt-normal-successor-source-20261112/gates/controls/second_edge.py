"""Bounded second edge controls; never installs or executes the native source."""
import copy,json,os,shutil,stat,sys
from pathlib import Path


def run_second_edge(env):
    args=env['args'];O=env['O'];F=env['F'];P=env['P'];H=env['H'];N=env['N'];T=env['T']
    enc=env['enc'];sha=env['sha'];write=env['write'];ref=env['ref'];check=env['check'];refused=env['refused']
    native=env['native'];q1=env['q'];tx1=env['tx'];leaf1=env['leaf'];lp1=env['lp'];qr1=env['qr']
    assert_history=env['assert_history']
    # A genuine second publication uses a new project origin. Retained CP199
    # request/marker/operator metadata continue to name the original project.
    first_project=P;first_F=F;first_O=O
    P=T/'project200';shutil.copytree(first_project,P)
    first_validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for key in first_validation:del sys.modules[key]
    env['mod']('scripts',P/'scripts')
    F=env['load'](P/'scripts/friday_install.py','scripts.friday_install')
    O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for key in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY',
            'PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):
        setattr(O,key,copy.deepcopy(getattr(first_O,key)))
    F.native_packages=lambda source:None
    native.F=F;native.O=O
    name=O.CURRENT_SOURCE_SECOND_LAYER
    patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for relative in (patch,mn):
        source=args.second_layer_root/relative
        if not source.exists():source=args.second_layer_root/Path(relative).name
        write(P/relative,source.read_bytes())
        if relative==mn:original_manifest_ref=ref(source)
    manifest=json.loads((P/mn).read_bytes())
    # The actual source200 patch/rows are retained exactly. Synthetic fixture198
    # layers cannot provide production prerequisite names; this seam is explicit.
    manifest['prerequisites']={}
    write(P/mn,manifest)
    check('CP200_exact_layer_manifest_patch_pin',manifest['patch']==patch and manifest['patch_sha256']==ref(P/patch)['sha256'])
    check('CP200_exact_native_scope',set(row['path'] for row in manifest['files'])==set(O.CURRENT_SOURCE_SECOND_NATIVE))
    native_after={row['path']:(args.second_native_after/row['path']).read_bytes() for row in manifest['files']}
    for row in manifest['files']:
        n=row['path'];before,after=O.CURRENT_SOURCE_SECOND_NATIVE[n]
        check('CP200_real_before_and_after_'+n,ref(N/n)['sha256']==row['before_sha256']==before
            and sha(native_after[n])==row['sha256']==after and len(native_after[n])==row['bytes'])
    leaf2=copy.deepcopy(leaf1);leaf2['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()}
    lp2=T/'leaf481.json';write(lp2,leaf2)
    check('CP200_project481_plugins52',len(leaf2['project_files'])==481 and len([n for n in leaf2['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q2=copy.deepcopy(q1)
    q2.update(candidate_project=str(P),previous_input=ref(lp1),current_input=ref(lp2),candidate_input=ref(lp2),
        marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),
        target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),
        configuration=ref(H/'config.yaml'),installed_layers=199,project_inventory=leaf2['project_files'],
        project_inventory_sha256=sha(enc(leaf2['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=[],
        current_source_successor={'schema':O.CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA,
            'root_project_update':q1['current_source_successor']['root_project_update'],'previous_native_update':qr1})
    # The previously accepted R1 one-edge reader still refuses this genuinely
    # new v2 context. Replace only the whole dispatch function in memory and
    # preserve every other current validation function and source file.
    baseline=Path(__file__).resolve().with_name('r1_one_edge_function.py')
    assert sha(baseline.read_bytes())=='f6288b42da66c3d5f1d935b75d82461d6eaba5ee255921211b1792b3db7e8de6'
    selected_reader=O.current_native_source_successor_checked
    exec(compile(baseline.read_bytes(),str(baseline),'exec'),O.__dict__)
    try:
        try:F.spec_checked(leaf2,cli_only=True,source_update=q2)
        except ValueError as exc:check('old_R1_one_edge_reader_refuses_actual_v2_CP200','ordinary_current_successor_context_required' in str(exc))
        else:raise AssertionError('old R1 one-edge reader accepted v2')
    finally:O.current_native_source_successor_checked=selected_reader
    evidence_baseline={'old_r1_one_edge_function':ref(baseline),'swap':'IN_MEMORY_ONLY_EXACT_WHOLE_FUNCTION_RESTORED'}
    check('CP200_explicit_before_publication',F.spec_checked(leaf2,cli_only=True,source_update=q2)[0]==H)
    builder_path=args.publisher.resolve(strict=True).with_name('build-layer-publication-request.py')
    builder=env['load'](builder_path,'portable_actual_publication_request_builder')
    evidence={**evidence_baseline,'publisher':ref(args.publisher),'builder':ref(builder_path),'manifest_input':original_manifest_ref,
        'synthetic_manifest':ref(P/mn),'patch':ref(P/patch),'native_afterimages':{n:ref(args.second_native_after/n) for n in native_after},
        'seams':['synthetic198 layers/prerequisites={} in copied manifest only',
            'synthetic stopped gateway; no systemctl','distinct candidate199/candidate200 Python source origins, reset private validation namespace to emulate fresh process'],
        'rollback':args.publisher_rollback,'CP199_original_history':env['cp_immutable']}
    defaults=builder.parse_args([])
    check('builder_historical_default_four_unchanged',tuple(defaults.layer_names)==tuple(builder.LAYER_NAMES)
        and len(defaults.layer_names)==4 and name not in defaults.layer_names)
    built_args=builder.parse_args(['--layer',name,'--home',str(H),'--candidate-project',str(P),
        '--native-unit',q2['native_unit']['path'],'--previous-input',str(lp1),'--current-input',str(lp2),
        '--current-source-project-update',q2['current_source_successor']['root_project_update']['path'],
        '--current-source-native-predecessor',qr1['path'],'--output',str(T/'builder-request.json'),'--seconds','600'])
    generated=builder.build_request(built_args)
    check('CP200_actual_builder_exact_request',enc(generated)==enc(q2))
    assert_history('CP199_immutable_at_CP200_before')
    # Unchanged199/200 negatives reused; this is only canonical-chain preparation.
    raw=json.dumps(q2,sort_keys=False,separators=(',',':')).encode()+b'\n';qs=sha(raw)
    request_path=T/'CP200-request.json';write(request_path,raw)
    CP=env['load'](args.publisher.resolve(strict=True),'portable_actual_layer_publication')
    # Declared synthetic STOPPED gateway authority; no systemctl is invoked.
    CP.gateway_running=lambda *a,**kw:False
    observed=[];original_consumer=CP.current_source_consumer_checked
    class InjectedDefaultInspectFailure(CP.Refused):pass
    def tracked_consumer(value,request,candidate,*,committed=False,inspect=False):
        original_consumer(value,request,candidate,committed=committed,inspect=inspect)
        observed.append((committed,inspect))
        if args.publisher_rollback and committed and inspect:
            raise InjectedDefaultInspectFailure('portable final default inspect boundary failure')
    CP.current_source_consumer_checked=tracked_consumer
    affected=list(native_after)+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]
    affected=[n if n not in native_after else 'hermes-agent/'+n for n in affected]
    before_effect={n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if (H/n).exists() else None for n in affected}
    tx2=H/'preparation'/('ordinary-source-update-v45-'+qs[:16]);qr2={'path':str(tx2/'request.json'),'sha256':qs}
    if args.publisher_rollback:
        try:CP.run(q2,request_path,qs)
        except InjectedDefaultInspectFailure:pass
        else:raise AssertionError('missing final default inspect injected failure')
        check('CP200_actual_publisher_reaches_all_consumers_before_rollback',observed==[(False,False),(False,True),(True,True)])
        check('CP200_actual_publisher_rollback_metadata',json.loads((tx2/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        check('CP200_actual_publisher_rollback_all_effects',all(
            (((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode))==data if data is not None else not (H/n).exists()) for n,data in before_effect.items()))
        assert_history('CP199_immutable_after_real_CP200_rollback')
        # Return to the retained original199 source modules and project root;
        # the new candidate remains separate and is never mistaken for installed.
        for key in tuple(sys.modules):
            if key=='_friday_install_validation_plugins' or key.startswith('_friday_install_validation_plugins.'):del sys.modules[key]
        sys.modules.update(first_validation)
        env['mod']('scripts',first_project/'scripts')
        sys.modules['scripts.friday_install']=first_F
        sys.modules['scripts.friday_ordinary_install']=first_O
        native.F=first_F;native.O=first_O
        check('CP199_default_retained_origin_after_real_CP200_rollback',first_F.spec_checked(leaf1,cli_only=True)[0]==H)
        try:CP.run(q2,request_path,qs)
        except CP.Refused as exc:check('CP200_actual_publisher_consumed_after_rollback','already_consumed' in str(exc))
        else:raise AssertionError('closed effect replayed')
        return evidence
    result=CP.run(q2,request_path,qs)
    check('CP200_actual_publisher_success',result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED' and result['files']==2 and result['layers']==1)
    check('CP200_actual_publisher_default_join',observed==[(False,False),(False,True),(True,True)])
    check('CP200_actual_publisher_retains_exact_raw_request',(tx2/'request.json').read_bytes()==raw and ref(tx2/'request.json')==qr2)
    receipt2sha=ref(H/'hermes-agent.source.json')['sha256']
    for n,data in native_after.items():check('CP200_actual_publisher_afterimage_'+n,(N/n).read_bytes()==data)
    cp2_immutable={str(p.relative_to(tx2)):sha(p.read_bytes()) for p in tx2.rglob('*') if p.is_file()}
    check('CP200_default_after_commit',F.spec_checked(leaf2,cli_only=True)[0]==H)
    check('CP200_default_inspect_after_commit',F.inspect(leaf2,ref(lp2)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
    # Existing200 semantic/writer/tamper proofs reused; no duplicate counts.
    assert_history('CP199_immutable_after_CP200')
    check('CP200_original_history_immutable',cp2_immutable=={str(p.relative_to(tx2)):sha(p.read_bytes()) for p in tx2.rglob('*') if p.is_file()})
    archived_project=T/'retired-project199';first_project.rename(archived_project)
    check('CP200_historical_project199_not_reopened',F.spec_checked(leaf2,cli_only=True)[0]==H)
    from third_edge import run_third_edge
    evidence['third_edge']=run_third_edge(locals(),env)
    return evidence
