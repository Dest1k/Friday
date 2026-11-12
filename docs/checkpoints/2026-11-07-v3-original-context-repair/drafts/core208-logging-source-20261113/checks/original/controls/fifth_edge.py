"""Exact bounded v5 whole-consumer controls; authority is explicitly synthetic.

The fifth operation uses the final helper, real builder and real publisher bytes.
Ancestral operations remain the retained v1/v2/v3/v4 consumers.  The narrow
Journal probes below test the real new-source rollback guard separately from
whole CP.run late-inspect rollback; neither grants native or runtime authority.
"""
import copy,json,os,shutil,stat,sys
from pathlib import Path


def run_fifth_edge(e,parent,env):
    args=e['args'];P4=e['P'];F4=e['F'];O4=e['O'];H=e['H'];N=e['N'];T=e['T'];native=e['native']
    enc=e['enc'];sha=e['sha'];write=e['write'];ref=e['ref'];check=e['check'];refused=e['refused']
    q4=e['q4'];tx4=e['tx4'];leaf4=e['leaf4'];lp4=e['lp4']
    start=len(env['checks']);P=T/'project203';shutil.copytree(P4,P)
    for helper in ('scripts/friday_install.py','scripts/friday_ordinary_install.py'):
        write(P/helper,(args.fifth_helpers_root/helper).read_bytes())
    validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for k in validation:del sys.modules[k]
    env['mod']('scripts',P/'scripts')
    F=env['load'](P/'scripts/friday_install.py','scripts.friday_install')
    O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for k in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY','PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):
        setattr(O,k,copy.deepcopy(getattr(O4,k)))
    F.native_packages=lambda source:None;native.F=F;native.O=O
    name=O.CURRENT_SOURCE_FIFTH_LAYER;patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for n in (patch,mn):write(P/n,(args.fifth_layer_root/n).read_bytes())
    rows=json.loads((P/mn).read_bytes())['files']
    frozen=json.loads(args.fifth_native_spec.read_bytes())['native_files']
    after={r['path']:(args.fifth_native_after/r['path']).read_bytes() for r in rows}
    check('CP203_exact_new_core_layer',name=='core-file-readability-and-context-provenance-after-source202')
    check('CP203_exact_pair',ref(P/mn)['sha256']==O.CURRENT_SOURCE_FIFTH_MANIFEST and ref(P/patch)['sha256']==O.CURRENT_SOURCE_FIFTH_PATCH)
    keys=('path','before_sha256','sha256','bytes','mode','new_file')
    check('CP203_exact_frozen_seven_rows',sorted([{k:r[k] for k in keys} for r in rows],key=lambda r:r['path'])==sorted([{k:r[k] for k in keys} for r in frozen],key=lambda r:r['path']))
    check('CP203_exact_six_modifications_one_addition',len(rows)==7 and set(after)==set(O.CURRENT_SOURCE_FIFTH_NATIVE) and sum(r['new_file'] for r in rows)==1)
    check('CP203_exact_before_after_and_size',all((not os.path.lexists(N/n) if vals[3] else ref(N/n)['sha256']==vals[0]) and sha(after[n])==vals[1] and len(after[n])==vals[2] for n,vals in O.CURRENT_SOURCE_FIFTH_NATIVE.items()))
    leaf5=copy.deepcopy(leaf4)
    leaf5['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()}
    lp5=T/'leaf487.json';write(lp5,leaf5)
    check('CP203_project487_plugins52',len(leaf5['project_files'])==487 and len([n for n in leaf5['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q5=copy.deepcopy(q4)
    q5.update(candidate_project=str(P),previous_input=ref(lp4),current_input=ref(lp5),candidate_input=ref(lp5),marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),configuration=ref(H/'config.yaml'),installed_layers=202,installed_files=17890,project_inventory=leaf5['project_files'],project_inventory_sha256=sha(enc(leaf5['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=sorted(n for n in leaf4['project_files'] if leaf4['project_files'][n]!=leaf5['project_files'][n]),current_source_successor={'schema':O.CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA,'root_project_update':q4['current_source_successor']['root_project_update'],'previous_native_update':ref(tx4/'request.json')})
    check('CP203_exact_oldv4_to_finalv5_helper_delta',q5['project_file_updates']==['scripts/friday_ordinary_install.py'])
    def spec(q=None):return F.spec_checked(leaf5,cli_only=True,source_update=q5 if q is None else q)
    check('CP203_real_whole_spec_before',spec()[0]==H)
    builder=env['load'](args.publisher.with_name('build-layer-publication-request.py'),'v5_actual_builder')
    builderargs=['--layer',name,'--home',str(H),'--candidate-project',str(P),'--native-unit',q5['native_unit']['path'],'--previous-input',str(lp4),'--current-input',str(lp5),'--current-source-project-update',q5['current_source_successor']['root_project_update']['path'],'--current-source-native-predecessor',q5['current_source_successor']['previous_native_update']['path'],'--seconds','600']
    check('CP203_real_builder_exact_v5',enc(builder.build_request(builder.parse_args(builderargs)))==enc(q5))
    defaults=builder.parse_args([])
    check('CP203_builder_default_four_preserved',len(defaults.layer_names)==4 and tuple(defaults.layer_names)==tuple(builder.LAYER_NAMES) and name not in defaults.layer_names)
    txs=e['txs']+[tx4]
    def history():return {str(p.relative_to(H/'preparation')):(sha(p.read_bytes()),stat.S_IMODE(p.stat().st_mode)) for tx in txs for p in tx.rglob('*') if p.is_file()}
    immutable=history()
    CP=env['load'](args.publisher.resolve(),'portable_fifth_publication');CP.gateway_running=lambda *a,**kw:False
    def pub_refused(label,fn):
        try:fn()
        except (CP.Refused,builder.publication().Refused,OSError,ValueError,TypeError,KeyError) as error:
            check(label,True,type(error).__name__+':'+str(error));return
        check(label,False,'accepted')
    def corrupt(label,p,fn):
        saved=p.read_bytes();mode=stat.S_IMODE(p.stat().st_mode);write(p,fn(saved))
        try:refused('CP203_'+label,spec)
        finally:write(p,saved);p.chmod(mode)
    def j(raw,fn):d=json.loads(raw);fn(d);return enc(d)
    additions=[r['path'] for r in rows if r['new_file']]
    paths=['hermes-agent/'+n for n in after]+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]+q5['project_file_updates']
    def states():return {n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if os.path.lexists(H/n) else None for n in paths}
    if not args.fifth_rollback and not args.reuse_fifth_negatives:
        for label,mutate in [
            ('wrong_root_hash',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
            ('wrong_CP202_hash',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
            ('missing_CP202',lambda q:q['current_source_successor'].pop('previous_native_update')),
            ('extra_context',lambda q:q['current_source_successor'].update(allow=True)),
            ('arbitrary_list',lambda q:q['current_source_successor'].update(previous_native_update=[ref(tx4/'request.json')])),
            ('sixth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v6')),
            ('v4_not_v5',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA)),
            ('wrong_before_layers',lambda q:q.update(installed_layers=201)),
            ('bool_before_layers',lambda q:q.update(installed_layers=True)),
            ('wrong_before_files',lambda q:q.update(installed_files=17888)),
            ('wrong_layer',lambda q:q.update(layer_names=[O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('extra_layer',lambda q:q.update(layer_names=[name,O.CURRENT_SOURCE_FOURTH_LAYER])),
            ('wrong_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),
            ('wrong_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
            ('wrong_marker',lambda q:q['marker'].update(sha256='f'*64)),
            ('plugin_claim',lambda q:q.update(plugin_set=['plugins/friday_rework/fixture0.py'])),
            ('reset_to_CP201',lambda q:q.update(previous_input=q4['previous_input'])),
            ('foreign_origin',lambda q:q.update(candidate_project=str(P4))),
        ]:
            bad=copy.deepcopy(q5);mutate(bad);refused('CP203_'+label,lambda bad=bad:spec(bad))
        for tx,label in zip(txs,('CP199','CP200','CP201','CP202')):
            alias=T/(label+'-fifth-alias.json');write(alias,(tx/'request.json').read_bytes())
            bad=copy.deepcopy(q5);bad['current_source_successor']['previous_native_update']=ref(alias)
            refused('CP203_'+label+'_substitution_alias',lambda bad=bad:spec(bad))
            for rel in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
                corrupt(label+'_'+rel,tx/rel,(lambda raw:j(raw,lambda d:d.update(gateway_started=True))) if rel in ('intent.json','committed.json') else (lambda raw:raw+b' '))
            (tx/'request.json').chmod(0o644)
            try:refused('CP203_'+label+'_raw_mode',spec)
            finally:(tx/'request.json').chmod(0o600)
            saved=(tx/'committed.json').read_bytes();(tx/'committed.json').unlink()
            try:refused('CP203_'+label+'_partial_commit',spec)
            finally:write(tx/'committed.json',saved)
            write(tx/'rolled-back.json',{})
            try:refused('CP203_'+label+'_rolledback',spec)
            finally:(tx/'rolled-back.json').unlink()
        duplicate=H/'preparation/ordinary-source-update-v45-fifth-duplicate'
        write(duplicate/'intent.json',{'current_input':{'path':str(lp4),'sha256':'f'*64}})
        try:refused('CP203_CP202_halfclaim_duplicate',spec)
        finally:shutil.rmtree(duplicate)
        partial=H/'preparation/ordinary-source-update-v45-fifth-halfclaim'
        write(partial/'request.json',{'current_input':{'path':'/foreign','sha256':ref(lp5)['sha256']}})
        try:refused('CP203_new_halfclaim_partial',spec)
        finally:shutil.rmtree(partial)
        for target,label in [(P/'plugins/friday_rework/fixture0.py','project_plugin_drift'),(H/'plugins/friday_rework/fixture0.py','physical_plugin_drift'),(P/'scripts/friday_ordinary_install.py','candidate_helper_drift'),(P/patch,'exact_patch_hash'),(P/mn,'exact_manifest_hash'),(N/'fixture/0.txt','foreign_native_drift'),(N/'hermes_cli/friday_workspace_presentation_text.py','fifth_native_preimage_drift'),(N/'agent/context_compressor.py','compressor_native_preimage_drift')]:
            corrupt(label,target,lambda b:b+b' ')
        saved_file=O.__file__;O.__file__=str(T/'foreign-helper.py')
        try:pub_refused('CP203_publisher_loaded_helper_origin_drift',lambda:CP.current_source_consumer_checked(leaf5,q5,P))
        finally:O.__file__=saved_file
        saved_origin=F.__spec__.origin;F.__spec__.origin=str(T/'foreign-install.py')
        try:pub_refused('CP203_publisher_loaded_install_spec_origin_drift',lambda:CP.current_source_consumer_checked(leaf5,q5,P))
        finally:F.__spec__.origin=saved_origin
        for n in additions:
            write(N/n,b'foreign new-file collision\n')
            try:refused('CP203_new_file_collision',spec)
            finally:(N/n).unlink()
        rawpath=T/'raw-v5.json'
        for label,raw in [('duplicate',b'{"seconds":600,'+enc(q5)[1:]),('nan',enc(q5).replace(b'"seconds": 600',b'"seconds": NaN')),('overflow',enc(q5).replace(b'"seconds": 600',b'"seconds": 1e999'))]:
            write(rawpath,raw);pub_refused('CP203_raw_'+label,lambda raw=raw:CP.current_source_request_bytes(q5,rawpath,sha(raw)))
        write(rawpath,enc(q5));rawpath.chmod(0o644)
        try:pub_refused('CP203_raw_mode644',lambda:CP.current_source_request_bytes(q5,rawpath,ref(rawpath)['sha256']))
        finally:rawpath.chmod(0o600)
        link=T/'raw-v5-link.json';link.symlink_to(rawpath)
        try:pub_refused('CP203_raw_symlink',lambda:CP.current_source_request_bytes(q5,link,ref(rawpath)['sha256']))
        finally:link.unlink()
        os.link(rawpath,link)
        try:pub_refused('CP203_raw_hardlink',lambda:CP.current_source_request_bytes(q5,rawpath,ref(rawpath)['sha256']))
        finally:link.unlink()
        check('CP203_raw_exact_valid',CP.current_source_request_bytes(q5,rawpath,ref(rawpath)['sha256'])==enc(q5))
        for label,schema in [('v5','friday.current-source-native-successor.v5'),('v6','friday.current-source-native-successor.v6'),('unknown','unknown'),('missing',None)]:
            fake=T/('fifth-unsupported-'+label+'.json');write(fake,{'current_source_successor':{'schema':schema}})
            av=builderargs.copy();av[av.index('--current-source-native-predecessor')+1]=str(fake)
            pub_refused('CP203_builder_unsupported_'+label,lambda av=av:builder.build_request(builder.parse_args(av)))
        # A cancellation at the first real consumer occurs before the consuming
        # mkdir, intent, patch staging or publication. The valid operation then
        # uses its original unchanged request; no consumed effect is retried.
        cancellation=T/'cancel-before-effects.json';write(cancellation,enc(q5));cancelsha=ref(cancellation)['sha256']
        canceltx=H/'preparation'/('ordinary-source-update-v45-'+cancelsha[:16]);saved=states()
        original=CP.current_source_consumer_checked;cancel_observed=[]
        def cancelled(value,request,candidate,*,committed=False,inspect=False):
            original(value,request,candidate,committed=committed,inspect=inspect)
            cancel_observed.append((committed,inspect));raise KeyboardInterrupt('synthetic_before_effect_cancellation')
        CP.current_source_consumer_checked=cancelled
        try:
            try:CP.run(q5,cancellation,cancelsha)
            except KeyboardInterrupt:pass
            else:raise AssertionError('missing cancellation')
        finally:CP.current_source_consumer_checked=original
        check('CP203_cancelled_before_effects',cancel_observed==[(False,False)] and states()==saved and not os.path.lexists(canceltx) and history()==immutable)
        # Focused real Journal.restore probes: own exact afterimage is removed;
        # foreign bytes or mode is preserved and explicitly refused. These are
        # separate synthetic targets and carry no full-operation acceptance.
        JH=T/'journal-probes';JN=JH/'hermes-agent';JN.mkdir(mode=0o700,parents=True)
        for suffix,data,mode,expected in [('own',b'own-afterimage\n',0o600,False),('foreign-bytes',b'foreign-afterimage\n',0o600,True),('foreign-mode',b'own-afterimage\n',0o644,True)]:
            target=JN/(suffix+'.py');journal=CP.Journal(T/('journal-'+suffix),JH)
            journal.record_absent(target);journal.entries[str(target)]['published_after']={'sha256':sha(b'own-afterimage\n'),'bytes':len(b'own-afterimage\n'),'mode':0o600}
            write(target,data);target.chmod(mode)
            if expected:
                pub_refused('CP203_newfile_rollback_preserves_'+suffix,lambda journal=journal,target=target:journal.restore([target]))
                check('CP203_newfile_rollback_'+suffix+'_exact_retained',target.read_bytes()==data and stat.S_IMODE(target.stat().st_mode)==mode)
            else:
                journal.restore([target]);check('CP203_newfile_rollback_removes_only_own_afterimage',not os.path.lexists(target))
    raw=json.dumps(q5,sort_keys=False,separators=(',',':')).encode()+b'\n'
    rp=T/'request203.json';write(rp,raw);qs=sha(raw);tx5=H/'preparation'/('ordinary-source-update-v45-'+qs[:16])
    observed=[];real=CP.current_source_consumer_checked
    class LateFailure(CP.Refused):pass
    def tracked(value,request,candidate,*,committed=False,inspect=False):
        real(value,request,candidate,committed=committed,inspect=inspect);observed.append((committed,inspect))
        if args.fifth_rollback and committed and inspect:raise LateFailure('injected_final_default_inspect')
    CP.current_source_consumer_checked=tracked;before=states()
    if args.fifth_rollback:
        try:CP.run(q5,rp,qs)
        except LateFailure:pass
        else:raise AssertionError('missing late refusal')
        check('CP203_rollback_after_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP203_rollback_exact_bytes_modes_absence',states()==before)
        check('CP203_rollback_new_native_file_removed',all(not os.path.lexists(N/n) for n in additions))
        check('CP203_rollback_journal',json.loads((tx5/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        for k in tuple(sys.modules):
            if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.'):del sys.modules[k]
        sys.modules.update(validation);env['mod']('scripts',P4/'scripts')
        sys.modules['scripts.friday_install']=F4;sys.modules['scripts.friday_ordinary_install']=O4;native.F=F4;native.O=O4
        check('CP203_rollback_oldv4_DEFAULT_retained',F4.spec_checked(leaf4,cli_only=True)[0]==H)
        check('CP203_rollback_oldv4_DEFAULT_inspect',F4.inspect(leaf4,ref(lp4)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        pub_refused('CP203_rollback_consumed_no_replay',lambda:CP.run(q5,rp,qs))
    else:
        result=CP.run(q5,rp,qs)
        check('CP203_real_publisher_seven_files_one_layer',result['files']==7 and result['layers']==1 and result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
        check('CP203_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP203_exact_raw_retained',(tx5/'request.json').read_bytes()==raw)
        check('CP203_DEFAULT_current_leaf',F.spec_checked(leaf5,cli_only=True)[0]==H)
        check('CP203_DEFAULT_inspect',F.inspect(leaf5,ref(lp5)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        check('CP203_helper_published_exact',all((H/n).read_bytes()==(P/n).read_bytes() for n in q5['project_file_updates']))
        check('CP203_native_after_exact',all((N/n).read_bytes()==b for n,b in after.items()))
        rec=json.loads((H/'hermes-agent.source.json').read_bytes());oldrec=json.loads(before['hermes-agent.source.json'][0])
        check('CP203_17884_other_native_rows_unchanged',len(rec['files'])==17891 and len(rec['layers'])==203 and rec['source_file_count']==17730 and all(v==rec['files'][n] for n,v in oldrec['files'].items() if n not in after))
        bad=copy.deepcopy(q5);bad.update(previous_input=ref(lp5),installed_layers=203,installed_files=17891)
        bad['current_source_successor'].update(schema='friday.current-source-native-successor.v6',previous_native_update=ref(tx5/'request.json'))
        refused('CP203_sixth_edge_refused',lambda:F.spec_checked(leaf5,cli_only=True,source_update=bad))
        pub_refused('CP203_committed_replay_refused',lambda:CP.run(q5,rp,qs))
        P4.rename(T/'retired-project202')
        check('CP203_historical_project202_absent_DEFAULT_pass',F.spec_checked(leaf5,cli_only=True)[0]==H)
    check('CP203_all_four_original_journals_bytes_modes_immutable',history()==immutable)
    fifth_check_count=len(env['checks'])-start
    from sixth_edge import run_sixth_edge
    sixth=run_sixth_edge(locals(),e,env)
    return {'sixth_edge':sixth,'state':'PASS','rollback':args.fifth_rollback,'new_v5_checks':fifth_check_count,'authority':'EXPLICIT_SYNTHETIC_FIXTURE_NO_NATIVE_GRANT','all_consumers':observed,'current_input':ref(lp5),'publisher':ref(args.publisher),'builder':ref(args.publisher.with_name('build-layer-publication-request.py')),'pair':{n:ref(args.fifth_layer_root/n) for n in (patch,mn)},'native_spec':ref(args.fifth_native_spec),'native_after':{n:ref(args.fifth_native_after/n) for n in after},'retained_preimages':{'fourth':str(args.fourth_native_before),'fifth_only':str(args.fifth_native_before)},'negative_count_note':'Changed-area checks repeat independently per counterpart; repetitions are not unique coverage.'}
