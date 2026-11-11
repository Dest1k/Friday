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
    for label,mutate in [
        ('missing_predecessor',lambda q:q['current_source_successor'].pop('previous_native_update')),
        ('wrong_predecessor_digest',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
        ('wrong_predecessor_context',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_SUCCESSOR_SCHEMA)),
        ('reset_to_root477',lambda q:q.update(previous_input=q1['previous_input'])),
        ('native198_count',lambda q:q.update(installed_layers=198)),
        ('bool_native199_count',lambda q:q.update(installed_layers=True)),
        ('wrong_layer',lambda q:q.update(layer_names=['foreign-layer'])),
        ('wrong_source199_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),
        ('wrong_source199_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
        ('extra_context_key',lambda q:q['current_source_successor'].update(accept=True)),
    ]:
        bad=copy.deepcopy(q2);mutate(bad)
        refused('CP200_before_'+label,lambda bad=bad:F.spec_checked(leaf2,cli_only=True,source_update=bad))
    alias=T/'noncanonical-CP199-request.json';write(alias,(tx1/'request.json').read_bytes())
    noncanonical=copy.deepcopy(q2);noncanonical['current_source_successor']['previous_native_update']=ref(alias)
    refused('CP200_prior_canonical_path_required',lambda:F.spec_checked(leaf2,cli_only=True,source_update=noncanonical))
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
    check('CP200_actual_native_semantic_check',native.check() is None)
    # Actual whole default start path stops before containment/process selection.
    class Boundary(RuntimeError):pass
    class Budget:
        def __init__(self):self.seen=[]
        def call(self,fn,*a,**kw):
            result=fn(*a,**kw);self.seen.append((fn.__name__,kw));return result
        def check(self,**kw):return 30
    containment=env['mod']('scripts.install_containment')
    class StopBeforeContainment:
        def __init__(self,*a,**kw):raise Boundary()
    containment.Containment=StopBeforeContainment
    budget=Budget()
    try:O.start(leaf2,lp2,ref(lp2)['sha256'],budget)
    except Boundary:pass
    else:raise AssertionError('start crossed test boundary')
    check('CP200_actual_start_default_consumer',budget.seen[0]==('spec_checked',{'cli_only':True}) and len(budget.seen)==2)
    # A further declared CP successor cannot turn this bounded v2 into a chain.
    q3=copy.deepcopy(q2);q3.update(previous_input=ref(lp2),installed_layers=200)
    q3['current_source_successor']['previous_native_update']=qr2
    refused('CP201_third_edge_refused',lambda:F.spec_checked(leaf2,cli_only=True,source_update=q3))
    # Legitimate later five-file writer afterimages keep both CP histories frozen.
    for stage,runtime in [('CP200-T1',native.runtime()),('CP200-T2',native.runtime(proof=True))]:
        afterimages=native.afterimages(leaf2,ref(lp2),runtime,T/stage)
        check(stage+'_exact_five_writer_afterimages',len(afterimages)==5)
        for n,state in afterimages.items():write(H/n,state['data'])
        check(stage+'_actual_native_semantics',native.check() is None)
        check(stage+'_default_consumer',F.spec_checked(leaf2,cli_only=True)[0]==H)
    def corrupt(label,path,mutate):
        before=path.read_bytes();write(path,mutate(before))
        try:refused(label,lambda:F.spec_checked(leaf2,cli_only=True))
        finally:write(path,before)
    def json_change(b,fn):
        value=json.loads(b);fn(value);return enc(value)
    # CP199 remains an authenticated original edge even after native200 changes
    # its two files. Every retained request/journal/image class remains guarded.
    for tx,label in ((tx1,'original199'),(tx2,'current200')):
        for n in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json',
                'before/hermes-agent.source.json','before/hermes-agent/install-stamp.json',
                'FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
            corrupt(label+'_'+n,tx/n,lambda b:b+b' ' if n not in ('intent.json','committed.json') else json_change(b,lambda d:d.update(gateway_started=True)))
        write(tx/'rolled-back.json',{})
        try:refused(label+'_rolledback',lambda:F.spec_checked(leaf2,cli_only=True))
        finally:(tx/'rolled-back.json').unlink()
    corrupt('CP200_raw_request_duplicate_key',tx2/'request.json',lambda b:b.replace(b'"seconds":600',b'"seconds":600,"seconds":600'))
    corrupt('CP200_raw_request_nonfinite',tx2/'request.json',lambda b:b.replace(b'"seconds":600',b'"seconds":NaN'))
    duplicate=H/'preparation/ordinary-source-update-v45-duplicate';shutil.copytree(tx1,duplicate)
    try:refused('CP199_duplicate_matching_edge',lambda:F.spec_checked(leaf2,cli_only=True))
    finally:shutil.rmtree(duplicate)
    for n in native_after:corrupt('CP200_native_afterimage_'+n,N/n,lambda b:b+b' ')
    corrupt('CP200_old_native_prefix_reordered',H/'hermes-agent.source.json',lambda b:json_change(b,lambda d:d['layers'].reverse()))
    saved_config=(H/'config.yaml').read_bytes();saved_marker=(H/F.MARKER).read_bytes()
    from hermes_yaml import safe_load,safe_dump
    config=safe_load(saved_config);config['model']['default']='foreign-after200'
    write(H/'config.yaml',safe_dump(config).encode())
    forged=json.loads(saved_marker);forged['profile_files']['config.yaml']=ref(H/'config.yaml')['sha256']
    forged['ordinary_gateway']['configuration_sha256']=native.gw.normalized_configuration(config)
    write(H/F.MARKER,forged)
    try:refused('CP200_semantic_config_and_phase_seal_forgery',lambda:F.spec_checked(leaf2,cli_only=True))
    finally:write(H/'config.yaml',saved_config);write(H/F.MARKER,saved_marker)
    corrupt('CP200_original_semantic_phase_seal',H/F.MARKER,lambda b:json_change(b,lambda d:d['ordinary_gateway'].update(configuration_sha256='f'*64)))
    assert_history('CP199_immutable_after_CP200')
    check('CP200_original_history_immutable',cp2_immutable=={str(p.relative_to(tx2)):sha(p.read_bytes()) for p in tx2.rglob('*') if p.is_file()})
    archived_project=T/'retired-project199';first_project.rename(archived_project)
    check('CP200_historical_project199_not_reopened',F.spec_checked(leaf2,cli_only=True)[0]==H)
    return evidence
