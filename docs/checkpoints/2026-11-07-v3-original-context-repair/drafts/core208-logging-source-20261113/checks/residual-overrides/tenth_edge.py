"""Exact bounded v9 whole-consumer controls; authority is explicitly synthetic.

The tenth operation uses the final helper, real builder and real publisher bytes.
All nine ancestral source operations remain genuine synthetic consumers.
CP.run late-inspect rollback checks all 8 declared CAS targets. No native
or runtime authority is granted.
"""
import copy,json,os,shutil,stat,sys
from pathlib import Path


def run_tenth_edge(e,parent,env):
    args=e['args'];P9=e['P'];F9=e['F'];O9=e['O'];H=e['H'];N=e['N'];T=e['T'];native=e['native']
    enc=e['enc'];sha=e['sha'];write=e['write'];ref=e['ref'];check=e['check'];refused=e['refused']
    q9=e['q9'];tx9=e['tx9'];leaf9=e['leaf9'];lp9=e['lp9']
    start=len(env['checks']);P=T/'project208';shutil.copytree(P9,P)
    for helper in ('scripts/friday_install.py','scripts/friday_ordinary_install.py'):
        write(P/helper,(args.tenth_helpers_root/helper).read_bytes())
    validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for k in validation:del sys.modules[k]
    env['mod']('scripts',P/'scripts')
    F=env['load'](P/'scripts/friday_install.py','scripts.friday_install')
    O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for k in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY','PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):
        setattr(O,k,copy.deepcopy(getattr(O9,k)))
    F.native_packages=lambda source:None;native.F=F;native.O=O
    name=O.CURRENT_SOURCE_TENTH_LAYER;patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for n in (patch,mn):write(P/n,(args.tenth_layer_root/n).read_bytes())
    rows=json.loads((P/mn).read_bytes())['files']
    declared_spec=json.loads(args.tenth_native_spec.read_bytes());frozen=declared_spec['native_files'];native_count=len(frozen)
    after={r['path']:(args.tenth_native_after/r['path']).read_bytes() for r in rows}
    check('CP208_exact_new_core_layer',name==declared_spec['layer'])
    check('CP208_exact_pair',ref(P/mn)['sha256']==O.CURRENT_SOURCE_TENTH_MANIFEST and ref(P/patch)['sha256']==O.CURRENT_SOURCE_TENTH_PATCH)
    keys=('path','before_sha256','sha256','bytes','mode','new_file')
    check('CP208_exact_frozen_declared_rows',sorted([{k:r[k] for k in keys} for r in rows],key=lambda r:r['path'])==sorted([{k:r[k] for k in keys} for r in frozen],key=lambda r:r['path']))
    check('CP208_exact_declared_modifications_no_native_addition',len(rows)==native_count==2 and set(after)==set(O.CURRENT_SOURCE_TENTH_NATIVE) and sum(r['new_file'] for r in rows)==0)
    check('CP208_exact_before_after_and_size',all((not os.path.lexists(N/n) if vals[3] else ref(N/n)['sha256']==vals[0]) and sha(after[n])==vals[1] and len(after[n])==vals[2] for n,vals in O.CURRENT_SOURCE_TENTH_NATIVE.items()))
    leaf10=copy.deepcopy(leaf9)
    leaf10['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()}
    lp10=T/'leaf497.json';write(lp10,leaf10)
    check('CP208_project497_plugins52',len(leaf10['project_files'])==497 and len([n for n in leaf10['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q10=copy.deepcopy(q9)
    q10.update(candidate_project=str(P),previous_input=ref(lp9),current_input=ref(lp10),candidate_input=ref(lp10),marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),configuration=ref(H/'config.yaml'),installed_layers=207,installed_files=17891,project_inventory=leaf10['project_files'],project_inventory_sha256=sha(enc(leaf10['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=sorted(n for n in leaf9['project_files'] if leaf9['project_files'][n]!=leaf10['project_files'][n]),current_source_successor={'schema':O.CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA,'root_project_update':q9['current_source_successor']['root_project_update'],'previous_native_update':ref(tx9/'request.json')})
    check('CP208_exact_oldv9_to_finalv10_helper_delta',q10['project_file_updates']==['scripts/friday_ordinary_install.py'])
    def spec(q=None):return F.spec_checked(leaf10,cli_only=True,source_update=q10 if q is None else q)
    check('CP208_real_whole_spec_before',spec()[0]==H)
    builder=env['load'](args.publisher.with_name('build-layer-publication-request.py'),'v8_actual_builder')
    builderargs=['--layer',name,'--home',str(H),'--candidate-project',str(P),'--native-unit',q10['native_unit']['path'],'--previous-input',str(lp9),'--current-input',str(lp10),'--current-source-project-update',q10['current_source_successor']['root_project_update']['path'],'--current-source-native-predecessor',q10['current_source_successor']['previous_native_update']['path'],'--seconds','600']
    check('CP208_real_builder_exact_v10',enc(builder.build_request(builder.parse_args(builderargs)))==enc(q10))
    defaults=builder.parse_args([])
    check('CP208_builder_default_four_preserved',len(defaults.layer_names)==4 and tuple(defaults.layer_names)==tuple(builder.LAYER_NAMES) and name not in defaults.layer_names)
    txs=e['txs']+[tx9]
    def history():return {str(p.relative_to(H/'preparation')):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for tx in txs for p in tx.rglob('*') if p.is_file()}
    immutable=history()
    check('CP208_current_CP207_exact_canonical_provenance',json.loads((tx9/'request.json').read_bytes())==q9 and json.loads((tx9/'committed.json').read_bytes())['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
    schemas=['friday.current-source-native-successor.v'+str(i) for i in range(1,11)]
    def canonical_links(chain):
        if len(chain) not in (9,10):return False
        for i,tx in enumerate(chain):
            r=json.loads((tx/'request.json').read_bytes());ctx=r['current_source_successor']
            if tx.name!='ordinary-source-update-v45-'+ref(tx/'request.json')['sha256'][:16] or ctx['schema']!=schemas[i]:return False
            if i and ctx['previous_native_update']!=ref(chain[i-1]/'request.json'):return False
            if not (tx/'committed.json').is_file() or (tx/'rolled-back.json').exists():return False
        return True
    # Seven physically completed operations exist before new tenth publication.
    check('CP208_nine_real_predecessors_before_tenth',len(txs)==9 and canonical_links(txs))
    CP=env['load'](args.publisher.resolve(),'portable_tenth_publication');CP.gateway_running=lambda *a,**kw:False
    def pub_refused(label,fn):
        try:fn()
        except (CP.Refused,builder.publication().Refused,OSError,ValueError,TypeError,KeyError) as error:
            check(label,True,type(error).__name__+':'+str(error));return
        check(label,False,'accepted')
    def corrupt(label,p,fn):
        saved=p.read_bytes();mode=stat.S_IMODE(p.stat().st_mode);write(p,fn(saved))
        try:refused('CP208_'+label,spec)
        finally:write(p,saved);p.chmod(mode)
    def j(raw,fn):d=json.loads(raw);fn(d);return enc(d)
    additions=[r['path'] for r in rows if r['new_file']]
    paths=['hermes-agent/'+n for n in after]+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]+q10['project_file_updates']
    check('CP208_exact_declared_CAS_targets',len(paths)==len(set(paths))==declared_spec['selected_targets']==native_count+6==8 and paths.count(patch)==1 and paths.count(mn)==1)
    def states():return {n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if os.path.lexists(H/n) else None for n in paths}
    if not args.tenth_rollback and not args.reuse_tenth_negatives:
        for label,mutate in [
            ('wrong_root_hash',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
            ('wrong_CP207_hash',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
            ('missing_CP207',lambda q:q['current_source_successor'].pop('previous_native_update')),
            ('extra_context',lambda q:q['current_source_successor'].update(allow=True)),
            ('arbitrary_list',lambda q:q['current_source_successor'].update(previous_native_update=[ref(tx9/'request.json')])),
            ('tenth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v11')),
            ('v7_not_v8',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA)),
            ('wrong_before_layers',lambda q:q.update(installed_layers=202)),
            ('bool_before_layers',lambda q:q.update(installed_layers=True)),
            ('wrong_before_files',lambda q:q.update(installed_files=17888)),
            ('wrong_layer',lambda q:q.update(layer_names=[O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('extra_layer',lambda q:q.update(layer_names=[name,O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('wrong_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),
            ('wrong_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
            ('wrong_marker',lambda q:q['marker'].update(sha256='f'*64)),
            ('plugin_claim',lambda q:q.update(plugin_set=['plugins/friday_rework/fixture0.py'])),
            ('reset_to_CP201',lambda q:q.update(previous_input=q9['previous_input'])),
            ('foreign_origin',lambda q:q.update(candidate_project=str(P9))),
        ]:
            bad=copy.deepcopy(q10);mutate(bad);refused('CP208_'+label,lambda bad=bad:spec(bad))
        for tx,label in [(tx9,'CP207'),(txs[0],'CP199-root-native')]:
            alias=T/(label+'-tenth-alias.json');write(alias,(tx/'request.json').read_bytes())
            bad=copy.deepcopy(q10);bad['current_source_successor']['previous_native_update']=ref(alias)
            refused('CP208_'+label+'_substitution_alias',lambda bad=bad:spec(bad))
            for rel in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
                corrupt(label+'_'+rel,tx/rel,(lambda raw:j(raw,lambda d:d.update(gateway_started=True))) if rel in ('intent.json','committed.json') else (lambda raw:raw+b' '))
            (tx/'request.json').chmod(0o644)
            try:refused('CP208_'+label+'_raw_mode',spec)
            finally:(tx/'request.json').chmod(0o600)
            saved=(tx/'committed.json').read_bytes();(tx/'committed.json').unlink()
            try:refused('CP208_'+label+'_partial_commit',spec)
            finally:write(tx/'committed.json',saved)
            write(tx/'rolled-back.json',{})
            try:refused('CP208_'+label+'_rolledback',spec)
            finally:(tx/'rolled-back.json').unlink()
        duplicate=H/'preparation/ordinary-source-update-v45-tenth-duplicate'
        write(duplicate/'intent.json',{'current_input':{'path':str(lp9),'sha256':'f'*64}})
        try:refused('CP208_CP207_halfclaim_duplicate',spec)
        finally:shutil.rmtree(duplicate)
        partial=H/'preparation/ordinary-source-update-v45-tenth-halfclaim'
        write(partial/'request.json',{'current_input':{'path':'/foreign','sha256':ref(lp10)['sha256']}})
        try:refused('CP208_new_halfclaim_partial',spec)
        finally:shutil.rmtree(partial)
        for target,label in [(P/'plugins/friday_rework/fixture0.py','project_plugin_drift'),(H/'plugins/friday_rework/fixture0.py','physical_plugin_drift'),(P/'scripts/friday_ordinary_install.py','candidate_helper_drift'),(P/patch,'exact_patch_hash'),(P/mn,'exact_manifest_hash'),(N/'fixture/0.txt','foreign_native_drift'),*[(N/r['path'],'tenth_native_preimage_drift_'+r['path']) for r in rows]]:
            corrupt(label,target,lambda b:b+b' ')
        saved_file=O.__file__;O.__file__=str(T/'foreign-helper.py')
        try:pub_refused('CP208_publisher_loaded_helper_origin_drift',lambda:CP.current_source_consumer_checked(leaf10,q10,P))
        finally:O.__file__=saved_file
        saved_origin=F.__spec__.origin;F.__spec__.origin=str(T/'foreign-install.py')
        try:pub_refused('CP208_publisher_loaded_install_spec_origin_drift',lambda:CP.current_source_consumer_checked(leaf10,q10,P))
        finally:F.__spec__.origin=saved_origin
        for n in additions:
            write(N/n,b'foreign new-file collision\n')
            try:refused('CP208_new_file_collision',spec)
            finally:(N/n).unlink()
        rawpath=T/'raw-v8.json'
        for label,raw in [('duplicate',b'{"seconds":600,'+enc(q10)[1:]),('nan',enc(q10).replace(b'"seconds": 600',b'"seconds": NaN')),('overflow',enc(q10).replace(b'"seconds": 600',b'"seconds": 1e999'))]:
            write(rawpath,raw);pub_refused('CP208_raw_'+label,lambda raw=raw:CP.current_source_request_bytes(q10,rawpath,sha(raw)))
        write(rawpath,enc(q10));rawpath.chmod(0o644)
        try:pub_refused('CP208_raw_mode644',lambda:CP.current_source_request_bytes(q10,rawpath,ref(rawpath)['sha256']))
        finally:rawpath.chmod(0o600)
        link=T/'raw-v8-link.json';link.symlink_to(rawpath)
        try:pub_refused('CP208_raw_symlink',lambda:CP.current_source_request_bytes(q10,link,ref(rawpath)['sha256']))
        finally:link.unlink()
        os.link(rawpath,link)
        try:pub_refused('CP208_raw_hardlink',lambda:CP.current_source_request_bytes(q10,rawpath,ref(rawpath)['sha256']))
        finally:link.unlink()
        check('CP208_raw_exact_valid',CP.current_source_request_bytes(q10,rawpath,ref(rawpath)['sha256'])==enc(q10))
        for label,schema in [('v11','friday.current-source-native-successor.v11'),('v10','friday.current-source-native-successor.v10'),('unknown','unknown'),('missing',None)]:
            fake=T/('tenth-unsupported-'+label+'.json');write(fake,{'current_source_successor':{'schema':schema}})
            av=builderargs.copy();av[av.index('--current-source-native-predecessor')+1]=str(fake)
            pub_refused('CP208_builder_unsupported_'+label,lambda av=av:builder.build_request(builder.parse_args(av)))
        # A cancellation at the first real consumer occurs before the consuming
        # mkdir, intent, patch staging or publication. The valid operation then
        # uses its original unchanged request; no consumed effect is retried.
        cancellation=T/'cancel-before-effects.json';write(cancellation,enc(q10));cancelsha=ref(cancellation)['sha256']
        canceltx=H/'preparation'/('ordinary-source-update-v45-'+cancelsha[:16]);saved=states()
        original=CP.current_source_consumer_checked;cancel_observed=[]
        def cancelled(value,request,candidate,*,committed=False,inspect=False):
            original(value,request,candidate,committed=committed,inspect=inspect)
            cancel_observed.append((committed,inspect));raise KeyboardInterrupt('synthetic_before_effect_cancellation')
        CP.current_source_consumer_checked=cancelled
        try:
            try:CP.run(q10,cancellation,cancelsha)
            except KeyboardInterrupt:pass
            else:raise AssertionError('missing cancellation')
        finally:CP.current_source_consumer_checked=original
        check('CP208_cancelled_before_effects',cancel_observed==[(False,False)] and states()==saved and not os.path.lexists(canceltx) and history()==immutable)
    raw=json.dumps(q10,sort_keys=False,separators=(',',':')).encode()+b'\n'
    rp=T/'request208.json';write(rp,raw);qs=sha(raw);tx10=H/'preparation'/('ordinary-source-update-v45-'+qs[:16])
    observed=[];real=CP.current_source_consumer_checked
    class LateFailure(CP.Refused):pass
    def tracked(value,request,candidate,*,committed=False,inspect=False):
        real(value,request,candidate,committed=committed,inspect=inspect);observed.append((committed,inspect))
        if args.tenth_rollback and committed and inspect:raise LateFailure('injected_final_default_inspect')
    CP.current_source_consumer_checked=tracked;before=states()
    if args.tenth_rollback:
        try:CP.run(q10,rp,qs)
        except LateFailure:pass
        else:raise AssertionError('missing late refusal')
        check('CP208_rollback_after_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP208_rollback_exact_bytes_modes_absence',states()==before)
        check('CP208_rollback_existing_native_preimage_retained',not additions and all((N/r['path']).read_bytes()==before['hermes-agent/'+r['path']][0] for r in rows))
        check('CP208_rollback_journal',json.loads((tx10/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        for k in tuple(sys.modules):
            if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.'):del sys.modules[k]
        sys.modules.update(validation);env['mod']('scripts',P9/'scripts')
        sys.modules['scripts.friday_install']=F9;sys.modules['scripts.friday_ordinary_install']=O9;native.F=F9;native.O=O9
        check('CP208_rollback_oldv9_DEFAULT_retained',F9.spec_checked(leaf9,cli_only=True)[0]==H)
        check('CP208_rollback_oldv9_DEFAULT_inspect',F9.inspect(leaf9,ref(lp9)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        pub_refused('CP208_rollback_consumed_no_replay',lambda:CP.run(q10,rp,qs))
    else:
        result=CP.run(q10,rp,qs)
        check('CP208_real_publisher_declared_files_one_layer',result['files']==native_count and result['layers']==1 and result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
        check('CP208_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP208_all_ten_canonical_links',canonical_links(txs+[tx10]))
        check('CP208_exact_raw_retained',(tx10/'request.json').read_bytes()==raw)
        check('CP208_DEFAULT_current_leaf',F.spec_checked(leaf10,cli_only=True)[0]==H)
        check('CP208_DEFAULT_inspect',F.inspect(leaf10,ref(lp10)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        check('CP208_helper_published_exact',all((H/n).read_bytes()==(P/n).read_bytes() for n in q10['project_file_updates']))
        check('CP208_native_after_exact',all((N/n).read_bytes()==b for n,b in after.items()))
        rec=json.loads((H/'hermes-agent.source.json').read_bytes());oldrec=json.loads(before['hermes-agent.source.json'][0])
        check('CP208_declared_other_native_rows_unchanged',len(rec['files'])==17891 and declared_spec['untouched_native_rows']==17891-native_count and sum(v==rec['files'][n] for n,v in oldrec['files'].items())==17891-native_count and len(rec['layers'])==208 and rec['source_file_count']==17730 and all(v==rec['files'][n] for n,v in oldrec['files'].items() if n not in after))
        bad=copy.deepcopy(q10);bad.update(previous_input=ref(lp10),installed_layers=208,installed_files=17891)
        bad['current_source_successor'].update(schema='friday.current-source-native-successor.v11',previous_native_update=ref(tx10/'request.json'))
        refused('CP208_tenth_edge_refused',lambda:F.spec_checked(leaf10,cli_only=True,source_update=bad))
        pub_refused('CP208_committed_replay_refused',lambda:CP.run(q10,rp,qs))
        # Recheck the retained R1/T1/T2 seam on the current committed v8 leaf.
        # These genuine writer afterimages carry synthetic authority only.
        current_cp={str(p.relative_to(tx10)):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for p in tx10.rglob('*') if p.is_file()}
        for phase,runtime in [('T1',env['pending']),('T2',env['active'])]:
            changes=native.afterimages(leaf10,ref(lp10),runtime,T/('tenth-'+phase+'-stage'))
            check('CP208_'+phase+'_five_genuine_writer_afterimages',len(changes)==5)
            for n,value in changes.items():write(H/n,value['data'])
            check('CP208_'+phase+'_native_semantic_readers',native.check() is None)
            check('CP208_'+phase+'_current_DEFAULT_spec',F.spec_checked(leaf10,cli_only=True)[0]==H)
            check('CP208_'+phase+'_current_DEFAULT_inspect',F.inspect(leaf10,ref(lp10)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
            check('CP208_'+phase+'_original_current_CP_immutable',{str(p.relative_to(tx10)):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for p in tx10.rglob('*') if p.is_file()}==current_cp)
        P9.rename(T/'retired-project207')
        check('CP208_historical_project206_absent_DEFAULT_pass',F.spec_checked(leaf10,cli_only=True)[0]==H)
    check('CP208_all_nine_original_journals_bytes_modes_immutable',history()==immutable)
    return {'state':'PASS','rollback':args.tenth_rollback,'new_v10_checks':len(env['checks'])-start,'authority':'EXPLICIT_SYNTHETIC_FIXTURE_NO_NATIVE_GRANT','all_consumers':observed,'current_input':ref(lp10),'publisher':ref(args.publisher),'builder':ref(args.publisher.with_name('build-layer-publication-request.py')),'pair':{n:ref(args.tenth_layer_root/n) for n in (patch,mn)},'native_spec':ref(args.tenth_native_spec),'native_after':{n:ref(args.tenth_native_after/n) for n in after},'retained_preimages':{'fourth':str(args.fourth_native_before),'tenth_only':str(args.tenth_native_before)},'native_modifications':native_count,'ancestral_negative_matrices':'REUSED_PINNED_PRIOR_RESULTS_NOT_RERUN','selected_targets':native_count+6,'untouched_native_rows':17891-native_count,'negative_count_note':'Changed-area checks repeat independently per counterpart; repetitions are not unique coverage.'}
