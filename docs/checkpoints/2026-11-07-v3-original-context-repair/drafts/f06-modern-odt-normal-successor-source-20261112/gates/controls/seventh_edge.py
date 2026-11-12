"""Exact bounded v7 whole-consumer controls; authority is explicitly synthetic.

The seventh operation uses the final helper, real builder and real publisher bytes.
Ancestral operations remain the retained v1/v2/v3/v4 consumers.  The narrow
Journal probes below test the real new-source rollback guard separately from
whole CP.run late-inspect rollback; neither grants native or runtime authority.
"""
import copy,json,os,shutil,stat,sys
from pathlib import Path


def run_seventh_edge(e,parent,env):
    args=e['args'];P6=e['P'];F6=e['F'];O6=e['O'];H=e['H'];N=e['N'];T=e['T'];native=e['native']
    enc=e['enc'];sha=e['sha'];write=e['write'];ref=e['ref'];check=e['check'];refused=e['refused']
    q6=e['q6'];tx6=e['tx6'];leaf6=e['leaf6'];lp6=e['lp6']
    start=len(env['checks']);P=T/'project205';shutil.copytree(P6,P)
    for helper in ('scripts/friday_install.py','scripts/friday_ordinary_install.py'):
        write(P/helper,(args.seventh_helpers_root/helper).read_bytes())
    validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for k in validation:del sys.modules[k]
    env['mod']('scripts',P/'scripts')
    F=env['load'](P/'scripts/friday_install.py','scripts.friday_install')
    O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for k in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY','PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):
        setattr(O,k,copy.deepcopy(getattr(O6,k)))
    F.native_packages=lambda source:None;native.F=F;native.O=O
    name=O.CURRENT_SOURCE_SEVENTH_LAYER;patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for n in (patch,mn):write(P/n,(args.seventh_layer_root/n).read_bytes())
    rows=json.loads((P/mn).read_bytes())['files']
    declared_spec=json.loads(args.seventh_native_spec.read_bytes());frozen=declared_spec['native_files'];native_count=len(frozen)
    after={r['path']:(args.seventh_native_after/r['path']).read_bytes() for r in rows}
    check('CP205_exact_new_core_layer',name==declared_spec['layer'])
    check('CP205_exact_pair',ref(P/mn)['sha256']==O.CURRENT_SOURCE_SEVENTH_MANIFEST and ref(P/patch)['sha256']==O.CURRENT_SOURCE_SEVENTH_PATCH)
    keys=('path','before_sha256','sha256','bytes','mode','new_file')
    check('CP205_exact_frozen_declared_rows',sorted([{k:r[k] for k in keys} for r in rows],key=lambda r:r['path'])==sorted([{k:r[k] for k in keys} for r in frozen],key=lambda r:r['path']))
    check('CP205_exact_declared_modifications_no_native_addition',len(rows)==native_count and set(after)==set(O.CURRENT_SOURCE_SEVENTH_NATIVE) and sum(r['new_file'] for r in rows)==0)
    check('CP205_exact_before_after_and_size',all((not os.path.lexists(N/n) if vals[3] else ref(N/n)['sha256']==vals[0]) and sha(after[n])==vals[1] and len(after[n])==vals[2] for n,vals in O.CURRENT_SOURCE_SEVENTH_NATIVE.items()))
    leaf7=copy.deepcopy(leaf6)
    leaf7['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()}
    lp7=T/'leaf491.json';write(lp7,leaf7)
    check('CP205_project491_plugins52',len(leaf7['project_files'])==491 and len([n for n in leaf7['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q7=copy.deepcopy(q6)
    q7.update(candidate_project=str(P),previous_input=ref(lp6),current_input=ref(lp7),candidate_input=ref(lp7),marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),configuration=ref(H/'config.yaml'),installed_layers=204,installed_files=17891,project_inventory=leaf7['project_files'],project_inventory_sha256=sha(enc(leaf7['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=sorted(n for n in leaf6['project_files'] if leaf6['project_files'][n]!=leaf7['project_files'][n]),current_source_successor={'schema':O.CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA,'root_project_update':q6['current_source_successor']['root_project_update'],'previous_native_update':ref(tx6/'request.json')})
    check('CP205_exact_oldv6_to_finalv7_helper_delta',q7['project_file_updates']==['scripts/friday_ordinary_install.py'])
    def spec(q=None):return F.spec_checked(leaf7,cli_only=True,source_update=q7 if q is None else q)
    check('CP205_real_whole_spec_before',spec()[0]==H)
    builder=env['load'](args.publisher.with_name('build-layer-publication-request.py'),'v7_actual_builder')
    builderargs=['--layer',name,'--home',str(H),'--candidate-project',str(P),'--native-unit',q7['native_unit']['path'],'--previous-input',str(lp6),'--current-input',str(lp7),'--current-source-project-update',q7['current_source_successor']['root_project_update']['path'],'--current-source-native-predecessor',q7['current_source_successor']['previous_native_update']['path'],'--seconds','600']
    check('CP205_real_builder_exact_v7',enc(builder.build_request(builder.parse_args(builderargs)))==enc(q7))
    defaults=builder.parse_args([])
    check('CP205_builder_default_four_preserved',len(defaults.layer_names)==4 and tuple(defaults.layer_names)==tuple(builder.LAYER_NAMES) and name not in defaults.layer_names)
    txs=e['txs']+[tx6]
    def history():return {str(p.relative_to(H/'preparation')):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for tx in txs for p in tx.rglob('*') if p.is_file()}
    immutable=history()
    schemas=['friday.current-source-native-successor.v'+str(i) for i in range(1,8)]
    def canonical_links(chain):
        if len(chain) not in (6,7):return False
        for i,tx in enumerate(chain):
            r=json.loads((tx/'request.json').read_bytes());ctx=r['current_source_successor']
            if tx.name!='ordinary-source-update-v45-'+ref(tx/'request.json')['sha256'][:16] or ctx['schema']!=schemas[i]:return False
            if i and ctx['previous_native_update']!=ref(chain[i-1]/'request.json'):return False
            if not (tx/'committed.json').is_file() or (tx/'rolled-back.json').exists():return False
        return True
    # Six physically completed operations exist before new seventh publication.
    check('CP205_six_real_predecessors_before_seventh',len(txs)==6 and canonical_links(txs))
    CP=env['load'](args.publisher.resolve(),'portable_seventh_publication');CP.gateway_running=lambda *a,**kw:False
    def pub_refused(label,fn):
        try:fn()
        except (CP.Refused,builder.publication().Refused,OSError,ValueError,TypeError,KeyError) as error:
            check(label,True,type(error).__name__+':'+str(error));return
        check(label,False,'accepted')
    def corrupt(label,p,fn):
        saved=p.read_bytes();mode=stat.S_IMODE(p.stat().st_mode);write(p,fn(saved))
        try:refused('CP205_'+label,spec)
        finally:write(p,saved);p.chmod(mode)
    def j(raw,fn):d=json.loads(raw);fn(d);return enc(d)
    additions=[r['path'] for r in rows if r['new_file']]
    paths=['hermes-agent/'+n for n in after]+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]+q7['project_file_updates']
    check('CP205_exact_declared_CAS_targets',len(paths)==len(set(paths))==declared_spec['selected_targets']==native_count+6 and paths.count(patch)==1 and paths.count(mn)==1)
    def states():return {n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if os.path.lexists(H/n) else None for n in paths}
    if not args.seventh_rollback and not args.reuse_seventh_negatives:
        for label,mutate in [
            ('wrong_root_hash',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
            ('wrong_CP204_hash',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
            ('missing_CP204',lambda q:q['current_source_successor'].pop('previous_native_update')),
            ('extra_context',lambda q:q['current_source_successor'].update(allow=True)),
            ('arbitrary_list',lambda q:q['current_source_successor'].update(previous_native_update=[ref(tx6/'request.json')])),
            ('eighth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v8')),
            ('v6_not_v7',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA)),
            ('wrong_before_layers',lambda q:q.update(installed_layers=202)),
            ('bool_before_layers',lambda q:q.update(installed_layers=True)),
            ('wrong_before_files',lambda q:q.update(installed_files=17888)),
            ('wrong_layer',lambda q:q.update(layer_names=[O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('extra_layer',lambda q:q.update(layer_names=[name,O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('wrong_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),
            ('wrong_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
            ('wrong_marker',lambda q:q['marker'].update(sha256='f'*64)),
            ('plugin_claim',lambda q:q.update(plugin_set=['plugins/friday_rework/fixture0.py'])),
            ('reset_to_CP201',lambda q:q.update(previous_input=q6['previous_input'])),
            ('foreign_origin',lambda q:q.update(candidate_project=str(P6))),
        ]:
            bad=copy.deepcopy(q7);mutate(bad);refused('CP205_'+label,lambda bad=bad:spec(bad))
        for tx,label in [(tx6,'CP204')]:
            alias=T/(label+'-seventh-alias.json');write(alias,(tx/'request.json').read_bytes())
            bad=copy.deepcopy(q7);bad['current_source_successor']['previous_native_update']=ref(alias)
            refused('CP205_'+label+'_substitution_alias',lambda bad=bad:spec(bad))
            for rel in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
                corrupt(label+'_'+rel,tx/rel,(lambda raw:j(raw,lambda d:d.update(gateway_started=True))) if rel in ('intent.json','committed.json') else (lambda raw:raw+b' '))
            (tx/'request.json').chmod(0o644)
            try:refused('CP205_'+label+'_raw_mode',spec)
            finally:(tx/'request.json').chmod(0o600)
            saved=(tx/'committed.json').read_bytes();(tx/'committed.json').unlink()
            try:refused('CP205_'+label+'_partial_commit',spec)
            finally:write(tx/'committed.json',saved)
            write(tx/'rolled-back.json',{})
            try:refused('CP205_'+label+'_rolledback',spec)
            finally:(tx/'rolled-back.json').unlink()
        duplicate=H/'preparation/ordinary-source-update-v45-seventh-duplicate'
        write(duplicate/'intent.json',{'current_input':{'path':str(lp6),'sha256':'f'*64}})
        try:refused('CP205_CP204_halfclaim_duplicate',spec)
        finally:shutil.rmtree(duplicate)
        partial=H/'preparation/ordinary-source-update-v45-seventh-halfclaim'
        write(partial/'request.json',{'current_input':{'path':'/foreign','sha256':ref(lp7)['sha256']}})
        try:refused('CP205_new_halfclaim_partial',spec)
        finally:shutil.rmtree(partial)
        for target,label in [(P/'plugins/friday_rework/fixture0.py','project_plugin_drift'),(H/'plugins/friday_rework/fixture0.py','physical_plugin_drift'),(P/'scripts/friday_ordinary_install.py','candidate_helper_drift'),(P/patch,'exact_patch_hash'),(P/mn,'exact_manifest_hash'),(N/'fixture/0.txt','foreign_native_drift'),*[(N/r['path'],'seventh_native_preimage_drift_'+r['path']) for r in rows]]:
            corrupt(label,target,lambda b:b+b' ')
        saved_file=O.__file__;O.__file__=str(T/'foreign-helper.py')
        try:pub_refused('CP205_publisher_loaded_helper_origin_drift',lambda:CP.current_source_consumer_checked(leaf7,q7,P))
        finally:O.__file__=saved_file
        saved_origin=F.__spec__.origin;F.__spec__.origin=str(T/'foreign-install.py')
        try:pub_refused('CP205_publisher_loaded_install_spec_origin_drift',lambda:CP.current_source_consumer_checked(leaf7,q7,P))
        finally:F.__spec__.origin=saved_origin
        for n in additions:
            write(N/n,b'foreign new-file collision\n')
            try:refused('CP205_new_file_collision',spec)
            finally:(N/n).unlink()
        rawpath=T/'raw-v7.json'
        for label,raw in [('duplicate',b'{"seconds":600,'+enc(q7)[1:]),('nan',enc(q7).replace(b'"seconds": 600',b'"seconds": NaN')),('overflow',enc(q7).replace(b'"seconds": 600',b'"seconds": 1e999'))]:
            write(rawpath,raw);pub_refused('CP205_raw_'+label,lambda raw=raw:CP.current_source_request_bytes(q7,rawpath,sha(raw)))
        write(rawpath,enc(q7));rawpath.chmod(0o644)
        try:pub_refused('CP205_raw_mode644',lambda:CP.current_source_request_bytes(q7,rawpath,ref(rawpath)['sha256']))
        finally:rawpath.chmod(0o600)
        link=T/'raw-v7-link.json';link.symlink_to(rawpath)
        try:pub_refused('CP205_raw_symlink',lambda:CP.current_source_request_bytes(q7,link,ref(rawpath)['sha256']))
        finally:link.unlink()
        os.link(rawpath,link)
        try:pub_refused('CP205_raw_hardlink',lambda:CP.current_source_request_bytes(q7,rawpath,ref(rawpath)['sha256']))
        finally:link.unlink()
        check('CP205_raw_exact_valid',CP.current_source_request_bytes(q7,rawpath,ref(rawpath)['sha256'])==enc(q7))
        for label,schema in [('v8','friday.current-source-native-successor.v8'),('v7','friday.current-source-native-successor.v7'),('unknown','unknown'),('missing',None)]:
            fake=T/('seventh-unsupported-'+label+'.json');write(fake,{'current_source_successor':{'schema':schema}})
            av=builderargs.copy();av[av.index('--current-source-native-predecessor')+1]=str(fake)
            pub_refused('CP205_builder_unsupported_'+label,lambda av=av:builder.build_request(builder.parse_args(av)))
        # A cancellation at the first real consumer occurs before the consuming
        # mkdir, intent, patch staging or publication. The valid operation then
        # uses its original unchanged request; no consumed effect is retried.
        cancellation=T/'cancel-before-effects.json';write(cancellation,enc(q7));cancelsha=ref(cancellation)['sha256']
        canceltx=H/'preparation'/('ordinary-source-update-v45-'+cancelsha[:16]);saved=states()
        original=CP.current_source_consumer_checked;cancel_observed=[]
        def cancelled(value,request,candidate,*,committed=False,inspect=False):
            original(value,request,candidate,committed=committed,inspect=inspect)
            cancel_observed.append((committed,inspect));raise KeyboardInterrupt('synthetic_before_effect_cancellation')
        CP.current_source_consumer_checked=cancelled
        try:
            try:CP.run(q7,cancellation,cancelsha)
            except KeyboardInterrupt:pass
            else:raise AssertionError('missing cancellation')
        finally:CP.current_source_consumer_checked=original
        check('CP205_cancelled_before_effects',cancel_observed==[(False,False)] and states()==saved and not os.path.lexists(canceltx) and history()==immutable)
        # Retained v6 guard implementation is reused for v7; these probes exercise
        # the actual guarded class and published inode bookkeeping, never CP.Journal.
        JH=T/'seventh-journal-probes';JN=JH/'hermes-agent';JN.mkdir(mode=0o700,parents=True)
        for suffix,foreign in [('own',None),('foreign-bytes',b'foreign'),('foreign-inode',b'own-afterimage\n')]:
            target=JN/(suffix+'.py');before_data=b'before\n';write(target,before_data)
            pins={target:{'sha256':sha(before_data),'bytes':len(before_data),'mode':0o600}}
            journal=CP._CurrentSourceV5Journal(T/('journal-'+suffix),JH,pins);journal.preflight();journal.record_existing(target,before_data)
            after_data=b'own-afterimage\n';callback=journal.prepare_publication(target,after_data,0o600)
            CP.publish(target,after_data,0o600,_before_replace=callback)
            check('CP205_guard_staged_inode_bound_'+suffix,bool(journal.after_states[str(target)]))
            if foreign is not None:
                replacement=JN/(suffix+'.foreign');write(replacement,foreign);os.replace(replacement,target)
                pub_refused('CP205_guard_foreign_preserved_'+suffix,lambda:journal.restore([target]))
                check('CP205_guard_foreign_retained_'+suffix,target.read_bytes()==foreign)
            else:
                journal.restore([target]);check('CP205_guard_own_exact_restore',target.read_bytes()==before_data)
    raw=json.dumps(q7,sort_keys=False,separators=(',',':')).encode()+b'\n'
    rp=T/'request205.json';write(rp,raw);qs=sha(raw);tx7=H/'preparation'/('ordinary-source-update-v45-'+qs[:16])
    observed=[];real=CP.current_source_consumer_checked
    class LateFailure(CP.Refused):pass
    def tracked(value,request,candidate,*,committed=False,inspect=False):
        real(value,request,candidate,committed=committed,inspect=inspect);observed.append((committed,inspect))
        if args.seventh_rollback and committed and inspect:raise LateFailure('injected_final_default_inspect')
    CP.current_source_consumer_checked=tracked;before=states()
    if args.seventh_rollback:
        try:CP.run(q7,rp,qs)
        except LateFailure:pass
        else:raise AssertionError('missing late refusal')
        check('CP205_rollback_after_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP205_rollback_exact_bytes_modes_absence',states()==before)
        check('CP205_rollback_existing_native_preimage_retained',not additions and all((N/r['path']).read_bytes()==before['hermes-agent/'+r['path']][0] for r in rows))
        check('CP205_rollback_journal',json.loads((tx7/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        for k in tuple(sys.modules):
            if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.'):del sys.modules[k]
        sys.modules.update(validation);env['mod']('scripts',P6/'scripts')
        sys.modules['scripts.friday_install']=F6;sys.modules['scripts.friday_ordinary_install']=O6;native.F=F6;native.O=O6
        check('CP205_rollback_oldv6_DEFAULT_retained',F6.spec_checked(leaf6,cli_only=True)[0]==H)
        check('CP205_rollback_oldv6_DEFAULT_inspect',F6.inspect(leaf6,ref(lp6)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        pub_refused('CP205_rollback_consumed_no_replay',lambda:CP.run(q7,rp,qs))
    else:
        result=CP.run(q7,rp,qs)
        check('CP205_real_publisher_declared_files_one_layer',result['files']==native_count and result['layers']==1 and result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
        check('CP205_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP205_all_seven_canonical_links',canonical_links(txs+[tx7]))
        check('CP205_exact_raw_retained',(tx7/'request.json').read_bytes()==raw)
        check('CP205_DEFAULT_current_leaf',F.spec_checked(leaf7,cli_only=True)[0]==H)
        check('CP205_DEFAULT_inspect',F.inspect(leaf7,ref(lp7)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        check('CP205_helper_published_exact',all((H/n).read_bytes()==(P/n).read_bytes() for n in q7['project_file_updates']))
        check('CP205_native_after_exact',all((N/n).read_bytes()==b for n,b in after.items()))
        rec=json.loads((H/'hermes-agent.source.json').read_bytes());oldrec=json.loads(before['hermes-agent.source.json'][0])
        check('CP205_declared_other_native_rows_unchanged',len(rec['files'])==17891 and declared_spec['untouched_native_rows']==17891-native_count and sum(v==rec['files'][n] for n,v in oldrec['files'].items())==17891-native_count and len(rec['layers'])==205 and rec['source_file_count']==17730 and all(v==rec['files'][n] for n,v in oldrec['files'].items() if n not in after))
        bad=copy.deepcopy(q7);bad.update(previous_input=ref(lp7),installed_layers=205,installed_files=17891)
        bad['current_source_successor'].update(schema='friday.current-source-native-successor.v8',previous_native_update=ref(tx7/'request.json'))
        refused('CP205_eighth_edge_refused',lambda:F.spec_checked(leaf7,cli_only=True,source_update=bad))
        pub_refused('CP205_committed_replay_refused',lambda:CP.run(q7,rp,qs))
        P6.rename(T/'retired-project204')
        check('CP205_historical_project204_absent_DEFAULT_pass',F.spec_checked(leaf7,cli_only=True)[0]==H)
    check('CP205_all_six_original_journals_bytes_modes_immutable',history()==immutable)
    seventh_check_count=len(env['checks'])-start
    from eighth_edge import run_eighth_edge
    eighth=run_eighth_edge(locals(),e,env)
    return {'eighth_edge':eighth,'state':'PASS','rollback':args.seventh_rollback,'new_v7_checks':seventh_check_count,'ancestral_negatives_reused':args.reuse_seventh_negatives,'authority':'EXPLICIT_SYNTHETIC_FIXTURE_NO_NATIVE_GRANT','all_consumers':observed,'current_input':ref(lp7),'publisher':ref(args.publisher),'builder':ref(args.publisher.with_name('build-layer-publication-request.py')),'pair':{n:ref(args.seventh_layer_root/n) for n in (patch,mn)},'native_spec':ref(args.seventh_native_spec),'native_after':{n:ref(args.seventh_native_after/n) for n in after},'retained_preimages':{'fourth':str(args.fourth_native_before),'seventh_only':str(args.seventh_native_before)},'native_modifications':native_count,'selected_targets':native_count+6,'untouched_native_rows':17891-native_count,'negative_count_note':'Changed-area checks repeat independently per counterpart; repetitions are not unique coverage.'}
