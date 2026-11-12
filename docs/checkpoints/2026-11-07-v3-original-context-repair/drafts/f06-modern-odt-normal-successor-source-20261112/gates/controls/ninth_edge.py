"""Exact bounded v9 whole-consumer controls; authority is explicitly synthetic.

The ninth operation uses the final helper, real builder and real publisher bytes.
All eight ancestral source operations remain genuine synthetic consumers.
CP.run late-inspect rollback checks all 7 declared CAS targets. No native
or runtime authority is granted.
"""
import copy,json,os,shutil,stat,sys
from pathlib import Path


def run_ninth_edge(e,parent,env):
    args=e['args'];P8=e['P'];F8=e['F'];O8=e['O'];H=e['H'];N=e['N'];T=e['T'];native=e['native']
    enc=e['enc'];sha=e['sha'];write=e['write'];ref=e['ref'];check=e['check'];refused=e['refused']
    q8=e['q8'];tx8=e['tx8'];leaf8=e['leaf8'];lp8=e['lp8']
    start=len(env['checks']);P=T/'project207';shutil.copytree(P8,P)
    for helper in ('scripts/friday_install.py','scripts/friday_ordinary_install.py'):
        write(P/helper,(args.ninth_helpers_root/helper).read_bytes())
    validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for k in validation:del sys.modules[k]
    env['mod']('scripts',P/'scripts')
    F=env['load'](P/'scripts/friday_install.py','scripts.friday_install')
    O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for k in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY','PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):
        setattr(O,k,copy.deepcopy(getattr(O8,k)))
    F.native_packages=lambda source:None;native.F=F;native.O=O
    name=O.CURRENT_SOURCE_NINTH_LAYER;patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for n in (patch,mn):write(P/n,(args.ninth_layer_root/n).read_bytes())
    rows=json.loads((P/mn).read_bytes())['files']
    declared_spec=json.loads(args.ninth_native_spec.read_bytes());frozen=declared_spec['native_files'];native_count=len(frozen)
    after={r['path']:(args.ninth_native_after/r['path']).read_bytes() for r in rows}
    check('CP207_exact_new_core_layer',name==declared_spec['layer'])
    check('CP207_exact_pair',ref(P/mn)['sha256']==O.CURRENT_SOURCE_NINTH_MANIFEST and ref(P/patch)['sha256']==O.CURRENT_SOURCE_NINTH_PATCH)
    keys=('path','before_sha256','sha256','bytes','mode','new_file')
    check('CP207_exact_frozen_declared_rows',sorted([{k:r[k] for k in keys} for r in rows],key=lambda r:r['path'])==sorted([{k:r[k] for k in keys} for r in frozen],key=lambda r:r['path']))
    check('CP207_exact_declared_modifications_no_native_addition',len(rows)==native_count==1 and set(after)==set(O.CURRENT_SOURCE_NINTH_NATIVE) and sum(r['new_file'] for r in rows)==0)
    check('CP207_exact_before_after_and_size',all((not os.path.lexists(N/n) if vals[3] else ref(N/n)['sha256']==vals[0]) and sha(after[n])==vals[1] and len(after[n])==vals[2] for n,vals in O.CURRENT_SOURCE_NINTH_NATIVE.items()))
    leaf9=copy.deepcopy(leaf8)
    leaf9['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()}
    lp9=T/'leaf495.json';write(lp9,leaf9)
    check('CP207_project495_plugins52',len(leaf9['project_files'])==495 and len([n for n in leaf9['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q9=copy.deepcopy(q8)
    q9.update(candidate_project=str(P),previous_input=ref(lp8),current_input=ref(lp9),candidate_input=ref(lp9),marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),configuration=ref(H/'config.yaml'),installed_layers=206,installed_files=17891,project_inventory=leaf9['project_files'],project_inventory_sha256=sha(enc(leaf9['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=sorted(n for n in leaf8['project_files'] if leaf8['project_files'][n]!=leaf9['project_files'][n]),current_source_successor={'schema':O.CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,'root_project_update':q8['current_source_successor']['root_project_update'],'previous_native_update':ref(tx8/'request.json')})
    check('CP207_exact_oldv8_to_finalv9_helper_delta',q9['project_file_updates']==['scripts/friday_ordinary_install.py'])
    def spec(q=None):return F.spec_checked(leaf9,cli_only=True,source_update=q9 if q is None else q)
    check('CP207_real_whole_spec_before',spec()[0]==H)
    builder=env['load'](args.publisher.with_name('build-layer-publication-request.py'),'v8_actual_builder')
    builderargs=['--layer',name,'--home',str(H),'--candidate-project',str(P),'--native-unit',q9['native_unit']['path'],'--previous-input',str(lp8),'--current-input',str(lp9),'--current-source-project-update',q9['current_source_successor']['root_project_update']['path'],'--current-source-native-predecessor',q9['current_source_successor']['previous_native_update']['path'],'--seconds','600']
    check('CP207_real_builder_exact_v9',enc(builder.build_request(builder.parse_args(builderargs)))==enc(q9))
    defaults=builder.parse_args([])
    check('CP207_builder_default_four_preserved',len(defaults.layer_names)==4 and tuple(defaults.layer_names)==tuple(builder.LAYER_NAMES) and name not in defaults.layer_names)
    txs=e['txs']+[tx8]
    def history():return {str(p.relative_to(H/'preparation')):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for tx in txs for p in tx.rglob('*') if p.is_file()}
    immutable=history()
    check('CP207_current_CP206_exact_canonical_provenance',json.loads((tx8/'request.json').read_bytes())==q8 and json.loads((tx8/'committed.json').read_bytes())['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
    schemas=['friday.current-source-native-successor.v'+str(i) for i in range(1,10)]
    def canonical_links(chain):
        if len(chain) not in (8,9):return False
        for i,tx in enumerate(chain):
            r=json.loads((tx/'request.json').read_bytes());ctx=r['current_source_successor']
            if tx.name!='ordinary-source-update-v45-'+ref(tx/'request.json')['sha256'][:16] or ctx['schema']!=schemas[i]:return False
            if i and ctx['previous_native_update']!=ref(chain[i-1]/'request.json'):return False
            if not (tx/'committed.json').is_file() or (tx/'rolled-back.json').exists():return False
        return True
    # Seven physically completed operations exist before new ninth publication.
    check('CP207_eight_real_predecessors_before_ninth',len(txs)==8 and canonical_links(txs))
    CP=env['load'](args.publisher.resolve(),'portable_ninth_publication');CP.gateway_running=lambda *a,**kw:False
    def pub_refused(label,fn):
        try:fn()
        except (CP.Refused,builder.publication().Refused,OSError,ValueError,TypeError,KeyError) as error:
            check(label,True,type(error).__name__+':'+str(error));return
        check(label,False,'accepted')
    def corrupt(label,p,fn):
        saved=p.read_bytes();mode=stat.S_IMODE(p.stat().st_mode);write(p,fn(saved))
        try:refused('CP207_'+label,spec)
        finally:write(p,saved);p.chmod(mode)
    def j(raw,fn):d=json.loads(raw);fn(d);return enc(d)
    additions=[r['path'] for r in rows if r['new_file']]
    paths=['hermes-agent/'+n for n in after]+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]+q9['project_file_updates']
    check('CP207_exact_declared_CAS_targets',len(paths)==len(set(paths))==declared_spec['selected_targets']==native_count+6==7 and paths.count(patch)==1 and paths.count(mn)==1)
    def states():return {n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if os.path.lexists(H/n) else None for n in paths}
    if not args.ninth_rollback:
        for label,mutate in [
            ('wrong_root_hash',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
            ('wrong_CP206_hash',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
            ('missing_CP206',lambda q:q['current_source_successor'].pop('previous_native_update')),
            ('extra_context',lambda q:q['current_source_successor'].update(allow=True)),
            ('arbitrary_list',lambda q:q['current_source_successor'].update(previous_native_update=[ref(tx8/'request.json')])),
            ('ninth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v10')),
            ('v7_not_v8',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA)),
            ('wrong_before_layers',lambda q:q.update(installed_layers=202)),
            ('bool_before_layers',lambda q:q.update(installed_layers=True)),
            ('wrong_before_files',lambda q:q.update(installed_files=17888)),
            ('wrong_layer',lambda q:q.update(layer_names=[O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('extra_layer',lambda q:q.update(layer_names=[name,O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('wrong_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),
            ('wrong_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
            ('wrong_marker',lambda q:q['marker'].update(sha256='f'*64)),
            ('plugin_claim',lambda q:q.update(plugin_set=['plugins/friday_rework/fixture0.py'])),
            ('reset_to_CP201',lambda q:q.update(previous_input=q8['previous_input'])),
            ('foreign_origin',lambda q:q.update(candidate_project=str(P8))),
        ]:
            bad=copy.deepcopy(q9);mutate(bad);refused('CP207_'+label,lambda bad=bad:spec(bad))
        for tx,label in [(tx8,'CP206'),(txs[0],'CP199-root-native')]:
            alias=T/(label+'-ninth-alias.json');write(alias,(tx/'request.json').read_bytes())
            bad=copy.deepcopy(q9);bad['current_source_successor']['previous_native_update']=ref(alias)
            refused('CP207_'+label+'_substitution_alias',lambda bad=bad:spec(bad))
            for rel in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
                corrupt(label+'_'+rel,tx/rel,(lambda raw:j(raw,lambda d:d.update(gateway_started=True))) if rel in ('intent.json','committed.json') else (lambda raw:raw+b' '))
            (tx/'request.json').chmod(0o644)
            try:refused('CP207_'+label+'_raw_mode',spec)
            finally:(tx/'request.json').chmod(0o600)
            saved=(tx/'committed.json').read_bytes();(tx/'committed.json').unlink()
            try:refused('CP207_'+label+'_partial_commit',spec)
            finally:write(tx/'committed.json',saved)
            write(tx/'rolled-back.json',{})
            try:refused('CP207_'+label+'_rolledback',spec)
            finally:(tx/'rolled-back.json').unlink()
        duplicate=H/'preparation/ordinary-source-update-v45-ninth-duplicate'
        write(duplicate/'intent.json',{'current_input':{'path':str(lp8),'sha256':'f'*64}})
        try:refused('CP207_CP206_halfclaim_duplicate',spec)
        finally:shutil.rmtree(duplicate)
        partial=H/'preparation/ordinary-source-update-v45-ninth-halfclaim'
        write(partial/'request.json',{'current_input':{'path':'/foreign','sha256':ref(lp9)['sha256']}})
        try:refused('CP207_new_halfclaim_partial',spec)
        finally:shutil.rmtree(partial)
        for target,label in [(P/'plugins/friday_rework/fixture0.py','project_plugin_drift'),(H/'plugins/friday_rework/fixture0.py','physical_plugin_drift'),(P/'scripts/friday_ordinary_install.py','candidate_helper_drift'),(P/patch,'exact_patch_hash'),(P/mn,'exact_manifest_hash'),(N/'fixture/0.txt','foreign_native_drift'),*[(N/r['path'],'ninth_native_preimage_drift_'+r['path']) for r in rows]]:
            corrupt(label,target,lambda b:b+b' ')
        saved_file=O.__file__;O.__file__=str(T/'foreign-helper.py')
        try:pub_refused('CP207_publisher_loaded_helper_origin_drift',lambda:CP.current_source_consumer_checked(leaf9,q9,P))
        finally:O.__file__=saved_file
        saved_origin=F.__spec__.origin;F.__spec__.origin=str(T/'foreign-install.py')
        try:pub_refused('CP207_publisher_loaded_install_spec_origin_drift',lambda:CP.current_source_consumer_checked(leaf9,q9,P))
        finally:F.__spec__.origin=saved_origin
        for n in additions:
            write(N/n,b'foreign new-file collision\n')
            try:refused('CP207_new_file_collision',spec)
            finally:(N/n).unlink()
        rawpath=T/'raw-v8.json'
        for label,raw in [('duplicate',b'{"seconds":600,'+enc(q9)[1:]),('nan',enc(q9).replace(b'"seconds": 600',b'"seconds": NaN')),('overflow',enc(q9).replace(b'"seconds": 600',b'"seconds": 1e999'))]:
            write(rawpath,raw);pub_refused('CP207_raw_'+label,lambda raw=raw:CP.current_source_request_bytes(q9,rawpath,sha(raw)))
        write(rawpath,enc(q9));rawpath.chmod(0o644)
        try:pub_refused('CP207_raw_mode644',lambda:CP.current_source_request_bytes(q9,rawpath,ref(rawpath)['sha256']))
        finally:rawpath.chmod(0o600)
        link=T/'raw-v8-link.json';link.symlink_to(rawpath)
        try:pub_refused('CP207_raw_symlink',lambda:CP.current_source_request_bytes(q9,link,ref(rawpath)['sha256']))
        finally:link.unlink()
        os.link(rawpath,link)
        try:pub_refused('CP207_raw_hardlink',lambda:CP.current_source_request_bytes(q9,rawpath,ref(rawpath)['sha256']))
        finally:link.unlink()
        check('CP207_raw_exact_valid',CP.current_source_request_bytes(q9,rawpath,ref(rawpath)['sha256'])==enc(q9))
        for label,schema in [('v10','friday.current-source-native-successor.v10'),('v9','friday.current-source-native-successor.v9'),('unknown','unknown'),('missing',None)]:
            fake=T/('ninth-unsupported-'+label+'.json');write(fake,{'current_source_successor':{'schema':schema}})
            av=builderargs.copy();av[av.index('--current-source-native-predecessor')+1]=str(fake)
            pub_refused('CP207_builder_unsupported_'+label,lambda av=av:builder.build_request(builder.parse_args(av)))
        # A cancellation at the first real consumer occurs before the consuming
        # mkdir, intent, patch staging or publication. The valid operation then
        # uses its original unchanged request; no consumed effect is retried.
        cancellation=T/'cancel-before-effects.json';write(cancellation,enc(q9));cancelsha=ref(cancellation)['sha256']
        canceltx=H/'preparation'/('ordinary-source-update-v45-'+cancelsha[:16]);saved=states()
        original=CP.current_source_consumer_checked;cancel_observed=[]
        def cancelled(value,request,candidate,*,committed=False,inspect=False):
            original(value,request,candidate,committed=committed,inspect=inspect)
            cancel_observed.append((committed,inspect));raise KeyboardInterrupt('synthetic_before_effect_cancellation')
        CP.current_source_consumer_checked=cancelled
        try:
            try:CP.run(q9,cancellation,cancelsha)
            except KeyboardInterrupt:pass
            else:raise AssertionError('missing cancellation')
        finally:CP.current_source_consumer_checked=original
        check('CP207_cancelled_before_effects',cancel_observed==[(False,False)] and states()==saved and not os.path.lexists(canceltx) and history()==immutable)
    raw=json.dumps(q9,sort_keys=False,separators=(',',':')).encode()+b'\n'
    rp=T/'request207.json';write(rp,raw);qs=sha(raw);tx9=H/'preparation'/('ordinary-source-update-v45-'+qs[:16])
    observed=[];real=CP.current_source_consumer_checked
    class LateFailure(CP.Refused):pass
    def tracked(value,request,candidate,*,committed=False,inspect=False):
        real(value,request,candidate,committed=committed,inspect=inspect);observed.append((committed,inspect))
        if args.ninth_rollback and committed and inspect:raise LateFailure('injected_final_default_inspect')
    CP.current_source_consumer_checked=tracked;before=states()
    if args.ninth_rollback:
        try:CP.run(q9,rp,qs)
        except LateFailure:pass
        else:raise AssertionError('missing late refusal')
        check('CP207_rollback_after_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP207_rollback_exact_bytes_modes_absence',states()==before)
        check('CP207_rollback_existing_native_preimage_retained',not additions and all((N/r['path']).read_bytes()==before['hermes-agent/'+r['path']][0] for r in rows))
        check('CP207_rollback_journal',json.loads((tx9/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        for k in tuple(sys.modules):
            if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.'):del sys.modules[k]
        sys.modules.update(validation);env['mod']('scripts',P8/'scripts')
        sys.modules['scripts.friday_install']=F8;sys.modules['scripts.friday_ordinary_install']=O8;native.F=F8;native.O=O8
        check('CP207_rollback_oldv8_DEFAULT_retained',F8.spec_checked(leaf8,cli_only=True)[0]==H)
        check('CP207_rollback_oldv8_DEFAULT_inspect',F8.inspect(leaf8,ref(lp8)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        pub_refused('CP207_rollback_consumed_no_replay',lambda:CP.run(q9,rp,qs))
    else:
        result=CP.run(q9,rp,qs)
        check('CP207_real_publisher_declared_files_one_layer',result['files']==native_count and result['layers']==1 and result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
        check('CP207_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP207_all_nine_canonical_links',canonical_links(txs+[tx9]))
        check('CP207_exact_raw_retained',(tx9/'request.json').read_bytes()==raw)
        check('CP207_DEFAULT_current_leaf',F.spec_checked(leaf9,cli_only=True)[0]==H)
        check('CP207_DEFAULT_inspect',F.inspect(leaf9,ref(lp9)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        check('CP207_helper_published_exact',all((H/n).read_bytes()==(P/n).read_bytes() for n in q9['project_file_updates']))
        check('CP207_native_after_exact',all((N/n).read_bytes()==b for n,b in after.items()))
        rec=json.loads((H/'hermes-agent.source.json').read_bytes());oldrec=json.loads(before['hermes-agent.source.json'][0])
        check('CP207_declared_other_native_rows_unchanged',len(rec['files'])==17891 and declared_spec['untouched_native_rows']==17891-native_count and sum(v==rec['files'][n] for n,v in oldrec['files'].items())==17891-native_count and len(rec['layers'])==207 and rec['source_file_count']==17730 and all(v==rec['files'][n] for n,v in oldrec['files'].items() if n not in after))
        bad=copy.deepcopy(q9);bad.update(previous_input=ref(lp9),installed_layers=207,installed_files=17891)
        bad['current_source_successor'].update(schema='friday.current-source-native-successor.v10',previous_native_update=ref(tx9/'request.json'))
        refused('CP207_ninth_edge_refused',lambda:F.spec_checked(leaf9,cli_only=True,source_update=bad))
        pub_refused('CP207_committed_replay_refused',lambda:CP.run(q9,rp,qs))
        # Recheck the retained R1/T1/T2 seam on the current committed v8 leaf.
        # These genuine writer afterimages carry synthetic authority only.
        current_cp={str(p.relative_to(tx9)):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for p in tx9.rglob('*') if p.is_file()}
        for phase,runtime in [('T1',env['pending']),('T2',env['active'])]:
            changes=native.afterimages(leaf9,ref(lp9),runtime,T/('ninth-'+phase+'-stage'))
            check('CP207_'+phase+'_five_genuine_writer_afterimages',len(changes)==5)
            for n,value in changes.items():write(H/n,value['data'])
            check('CP207_'+phase+'_native_semantic_readers',native.check() is None)
            check('CP207_'+phase+'_current_DEFAULT_spec',F.spec_checked(leaf9,cli_only=True)[0]==H)
            check('CP207_'+phase+'_current_DEFAULT_inspect',F.inspect(leaf9,ref(lp9)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
            check('CP207_'+phase+'_original_current_CP_immutable',{str(p.relative_to(tx9)):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for p in tx9.rglob('*') if p.is_file()}==current_cp)
        P8.rename(T/'retired-project206')
        check('CP207_historical_project206_absent_DEFAULT_pass',F.spec_checked(leaf9,cli_only=True)[0]==H)
    check('CP207_all_eight_original_journals_bytes_modes_immutable',history()==immutable)
    return {'state':'PASS','rollback':args.ninth_rollback,'new_v9_checks':len(env['checks'])-start,'authority':'EXPLICIT_SYNTHETIC_FIXTURE_NO_NATIVE_GRANT','all_consumers':observed,'current_input':ref(lp9),'publisher':ref(args.publisher),'builder':ref(args.publisher.with_name('build-layer-publication-request.py')),'pair':{n:ref(args.ninth_layer_root/n) for n in (patch,mn)},'native_spec':ref(args.ninth_native_spec),'native_after':{n:ref(args.ninth_native_after/n) for n in after},'retained_preimages':{'fourth':str(args.fourth_native_before),'ninth_only':str(args.ninth_native_before)},'native_modifications':native_count,'ancestral_negative_matrices':'REUSED_PINNED_PRIOR_RESULTS_NOT_RERUN','selected_targets':native_count+6,'untouched_native_rows':17891-native_count,'negative_count_note':'Changed-area checks repeat independently per counterpart; repetitions are not unique coverage.'}
