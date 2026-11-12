"""New fixed v4 changed-area controls. Authority is explicitly synthetic."""
import copy,json,sys,shutil,stat,os
from pathlib import Path

def run_fourth_edge(e,env):
    args=e['args'];P3=e['P'];F3=e['F'];O3=e['O'];H=e['H'];N=e['N'];T=e['T'];native=e['native']
    enc=e['enc'];sha=e['sha'];write=e['write'];ref=e['ref'];check=e['check'];refused=e['refused'];q3=e['q3'];tx3=e['tx3'];leaf3=e['leaf3'];lp3=e['lp3']
    start=len(env['checks']);P=T/'project202';shutil.copytree(P3,P)
    for helper in ('scripts/friday_install.py','scripts/friday_ordinary_install.py'):
        write(P/helper,(args.fourth_helpers_root/helper).read_bytes())
    validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for k in validation:del sys.modules[k]
    env['mod']('scripts',P/'scripts');F=env['load'](P/'scripts/friday_install.py','scripts.friday_install');O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for k in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY','PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):setattr(O,k,copy.deepcopy(getattr(O3,k)))
    F.native_packages=lambda source:None;native.F=F;native.O=O
    name=O.CURRENT_SOURCE_FOURTH_LAYER;patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for n in (patch,mn):write(P/n,(args.fourth_layer_root/n).read_bytes())
    rows=json.loads((P/mn).read_bytes())['files'];after={r['path']:(args.fourth_native_after/r['path']).read_bytes() for r in rows}
    check('CP202_exact_pair',ref(P/mn)['sha256']==O.CURRENT_SOURCE_FOURTH_MANIFEST and ref(P/patch)['sha256']==O.CURRENT_SOURCE_FOURTH_PATCH)
    check('CP202_exact_ten_rows_two_additions',len(rows)==10 and set(after)==set(O.CURRENT_SOURCE_FOURTH_NATIVE) and sum(r['new_file'] for r in rows)==2)
    check('CP202_exact_before_after',all((not (N/n).exists() if vals[3] else ref(N/n)['sha256']==vals[0]) and sha(after[n])==vals[1] and len(after[n])==vals[2] for n,vals in O.CURRENT_SOURCE_FOURTH_NATIVE.items()))
    leaf4=copy.deepcopy(leaf3);leaf4['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()};lp4=T/'leaf485.json';write(lp4,leaf4)
    check('CP202_project485_plugins52',len(leaf4['project_files'])==485 and len([n for n in leaf4['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q4=copy.deepcopy(q3);q4.update(candidate_project=str(P),previous_input=ref(lp3),current_input=ref(lp4),candidate_input=ref(lp4),marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),configuration=ref(H/'config.yaml'),installed_layers=201,project_inventory=leaf4['project_files'],project_inventory_sha256=sha(enc(leaf4['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=sorted(n for n in leaf3['project_files'] if leaf3['project_files'][n]!=leaf4['project_files'][n]),current_source_successor={'schema':O.CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA,'root_project_update':q3['current_source_successor']['root_project_update'],'previous_native_update':ref(tx3/'request.json')})
    check('CP202_actual_oldv3_to_finalv4_helper_delta',q4['project_file_updates']==['scripts/friday_ordinary_install.py'])
    def spec(q=None):return F.spec_checked(leaf4,cli_only=True,source_update=q4 if q is None else q)
    check('CP202_real_whole_spec_before',spec()[0]==H)
    builder=env['load'](args.publisher.with_name('build-layer-publication-request.py'),'v4_actual_builder')
    builderargs=['--layer',name,'--home',str(H),'--candidate-project',str(P),'--native-unit',q4['native_unit']['path'],'--previous-input',str(lp3),'--current-input',str(lp4),'--current-source-project-update',q4['current_source_successor']['root_project_update']['path'],'--current-source-native-predecessor',q4['current_source_successor']['previous_native_update']['path'],'--seconds','600']
    check('CP202_real_builder_exact_v4',enc(builder.build_request(builder.parse_args(builderargs)))==enc(q4))
    txs=[e['tx1'],e['tx2'],tx3]
    def history():return {str(p.relative_to(H/'preparation')):sha(p.read_bytes()) for tx in txs for p in tx.rglob('*') if p.is_file()}
    immutable=history()
    CP=env['load'](args.publisher.resolve(),'portable_fourth_publication');CP.gateway_running=lambda *a,**kw:False
    def pub_refused(label,fn):
        try:fn()
        except (CP.Refused,builder.publication().Refused,OSError,ValueError,TypeError,KeyError) as error:check(label,True,type(error).__name__+':'+str(error));return
        check(label,False,'accepted')
    if not args.fourth_rollback and not args.reuse_fourth_negatives:
        for label,mutate in [
            ('wrong_root_hash',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
            ('wrong_CP201_hash',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
            ('missing_CP201',lambda q:q['current_source_successor'].pop('previous_native_update')),
            ('extra_context',lambda q:q['current_source_successor'].update(allow=True)),
            ('arbitrary_list',lambda q:q['current_source_successor'].update(previous_native_update=[ref(tx3/'request.json')])),
            ('fifth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v5')),
            ('v3_not_v4',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA)),
            ('wrong_before_layers',lambda q:q.update(installed_layers=200)),('bool_before_layers',lambda q:q.update(installed_layers=True)),
            ('wrong_before_files',lambda q:q.update(installed_files=17890)),('wrong_layer',lambda q:q.update(layer_names=[O.CURRENT_SOURCE_THIRD_LAYER])),
            ('extra_layer',lambda q:q.update(layer_names=[name,O.CURRENT_SOURCE_THIRD_LAYER])),
            ('wrong_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),('wrong_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
            ('wrong_marker',lambda q:q['marker'].update(sha256='f'*64)),('plugin_claim',lambda q:q.update(plugin_set=['plugins/friday_rework/fixture0.py'])),
            ('reset_to_CP200',lambda q:q.update(previous_input=q3['previous_input'])),('foreign_origin',lambda q:q.update(candidate_project=str(P3))),
        ]:
            bad=copy.deepcopy(q4);mutate(bad);refused('CP202_'+label,lambda bad=bad:spec(bad))
        for tx,label in zip(txs,('CP199','CP200','CP201')):
            alias=T/(label+'-alias.json');write(alias,(tx/'request.json').read_bytes());bad=copy.deepcopy(q4);bad['current_source_successor']['previous_native_update']=ref(alias)
            refused('CP202_'+label+'_substitution_alias',lambda bad=bad:spec(bad))
        def corrupt(label,p,fn):
            saved=p.read_bytes();write(p,fn(saved))
            try:refused('CP202_'+label,spec)
            finally:write(p,saved)
        def j(raw,fn):d=json.loads(raw);fn(d);return enc(d)
        for tx,label in zip(txs,('CP199','CP200','CP201')):
            for rel in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
                corrupt(label+'_'+rel,tx/rel,(lambda raw:j(raw,lambda d:d.update(gateway_started=True))) if rel in ('intent.json','committed.json') else (lambda raw:raw+b' '))
            (tx/'request.json').chmod(0o644)
            try:refused('CP202_'+label+'_raw_mode',spec)
            finally:(tx/'request.json').chmod(0o600)
            saved=(tx/'committed.json').read_bytes();(tx/'committed.json').unlink()
            try:refused('CP202_'+label+'_partial_commit',spec)
            finally:write(tx/'committed.json',saved)
            write(tx/'rolled-back.json',{})
            try:refused('CP202_'+label+'_rolledback',spec)
            finally:(tx/'rolled-back.json').unlink()
        marker=json.loads((H/F.MARKER).read_bytes())
        refused('CP202_historical_third_without_proof',lambda:O._current_native_source_edge_checked(leaf3,cli_only=True,source_update=q3,historical_marker=marker,prior_edge={'request':e['q2']}))
        refused('CP202_historical_third_boolean_proof',lambda:O._current_native_source_edge_checked(leaf3,cli_only=True,source_update=q3,historical_marker=marker,prior_edge={'request':e['q2']},_fourth_history=True))
        duplicate=H/'preparation/ordinary-source-update-v45-duplicate';write(duplicate/'intent.json',{'current_input':{'path':str(lp3),'sha256':'f'*64}})
        try:refused('CP202_CP201_halfclaim_duplicate',spec)
        finally:shutil.rmtree(duplicate)
        partial=H/'preparation/ordinary-source-update-v45-halfclaim';write(partial/'request.json',{'current_input':{'path':'/foreign','sha256':ref(lp4)['sha256']}})
        try:refused('CP202_new_halfclaim_partial',spec)
        finally:shutil.rmtree(partial)
        corrupt('project_plugin_drift',P/'plugins/friday_rework/fixture0.py',lambda b:b+b' ')
        corrupt('physical_plugin_drift',H/'plugins/friday_rework/fixture0.py',lambda b:b+b' ')
        corrupt('physical_native_drift',N/'fixture/0.txt',lambda b:b+b' ')
        from hermes_yaml import safe_load,safe_dump
        def drift(raw):d=safe_load(raw);d['model']['default']='foreign';return safe_dump(d).encode()
        corrupt('semantic_config_drift',H/'config.yaml',drift)
        rawpath=T/'raw-v4.json'
        for label,raw in [('duplicate',b'{"seconds":600,'+enc(q4)[1:]),('nan',enc(q4).replace(b'"seconds": 600',b'"seconds": NaN')),('overflow',enc(q4).replace(b'"seconds": 600',b'"seconds": 1e999'))]:
            write(rawpath,raw);pub_refused('CP202_raw_'+label,lambda raw=raw:CP.current_source_request_bytes(q4,rawpath,sha(raw)))
        write(rawpath,enc(q4));rawpath.chmod(0o644)
        try:pub_refused('CP202_raw_mode644',lambda:CP.current_source_request_bytes(q4,rawpath,ref(rawpath)['sha256']))
        finally:rawpath.chmod(0o600)
        link=T/'raw-link.json';link.symlink_to(rawpath)
        try:pub_refused('CP202_raw_symlink',lambda:CP.current_source_request_bytes(q4,link,ref(rawpath)['sha256']))
        finally:link.unlink()
        os.link(rawpath,link)
        try:pub_refused('CP202_raw_hardlink',lambda:CP.current_source_request_bytes(q4,rawpath,ref(rawpath)['sha256']))
        finally:link.unlink()
        check('CP202_raw_exact_valid',CP.current_source_request_bytes(q4,rawpath,ref(rawpath)['sha256'])==enc(q4))
        for label,schema in [('v4','friday.current-source-native-successor.v4'),('unknown','unknown'),('missing',None)]:
            fake=T/('unsupported-'+label+'.json');write(fake,{'current_source_successor':{'schema':schema}})
            av=builderargs.copy();av[av.index('--current-source-native-predecessor')+1]=str(fake)
            pub_refused('CP202_builder_unsupported_'+label,lambda av=av:builder.build_request(builder.parse_args(av)))
    raw=json.dumps(q4,sort_keys=False,separators=(',',':')).encode()+b'\n';rp=T/'request202.json';write(rp,raw);qs=sha(raw);tx4=H/'preparation'/('ordinary-source-update-v45-'+qs[:16])
    observed=[];real=CP.current_source_consumer_checked
    class LateFailure(CP.Refused):pass
    def tracked(value,request,candidate,*,committed=False,inspect=False):
        real(value,request,candidate,committed=committed,inspect=inspect);observed.append((committed,inspect))
        if args.fourth_rollback and committed and inspect:raise LateFailure('injected_final_default_inspect')
    CP.current_source_consumer_checked=tracked
    paths=['hermes-agent/'+n for n in after]+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]+q4['project_file_updates']
    before={n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if (H/n).exists() else None for n in paths}
    if args.fourth_rollback:
        try:CP.run(q4,rp,qs)
        except LateFailure:pass
        else:raise AssertionError('missing late refusal')
        check('CP202_rollback_after_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP202_rollback_exact_bytes_modes_absences',all((((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode))==v if v is not None else not (H/n).exists()) for n,v in before.items()))
        check('CP202_rollback_two_new_native_files_removed',all(not (N/r['path']).exists() for r in rows if r['new_file']))
        check('CP202_rollback_journal',json.loads((tx4/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        for k in tuple(sys.modules):
            if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.'):del sys.modules[k]
        sys.modules.update(validation);env['mod']('scripts',P3/'scripts');sys.modules['scripts.friday_install']=F3;sys.modules['scripts.friday_ordinary_install']=O3;native.F=F3;native.O=O3
        check('CP202_rollback_oldv3_DEFAULT_retained',F3.spec_checked(leaf3,cli_only=True)[0]==H)
        pub_refused('CP202_rollback_consumed_no_replay',lambda:CP.run(q4,rp,qs))
    else:
        result=CP.run(q4,rp,qs)
        check('CP202_real_publisher_ten_files_one_layer',result['files']==10 and result['layers']==1 and result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
        check('CP202_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP202_exact_raw_retained',(tx4/'request.json').read_bytes()==raw)
        check('CP202_DEFAULT_current_leaf',F.spec_checked(leaf4,cli_only=True)[0]==H)
        check('CP202_DEFAULT_inspect',F.inspect(leaf4,ref(lp4)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        check('CP202_helper_published_exact',all((H/n).read_bytes()==(P/n).read_bytes() for n in q4['project_file_updates']))
        check('CP202_native_after_exact',all((N/n).read_bytes()==b for n,b in after.items()))
        rec=json.loads((H/'hermes-agent.source.json').read_bytes());oldrec=json.loads(before['hermes-agent.source.json'][0])
        check('CP202_17880_other_native_rows_unchanged',len(rec['files'])==17890 and rec['source_file_count']==17730 and all(v==rec['files'][n] for n,v in oldrec['files'].items() if n not in after))
        bad=copy.deepcopy(q4);bad.update(previous_input=ref(lp4),installed_layers=202);bad['current_source_successor']['previous_native_update']=ref(tx4/'request.json')
        refused('CP202_fifth_edge_with_v4_refused',lambda:F.spec_checked(leaf4,cli_only=True,source_update=bad))
        pub_refused('CP202_committed_replay_refused',lambda:CP.run(q4,rp,qs))
        P3.rename(T/'retired-project201')
        check('CP202_historical_project201_absent_DEFAULT_pass',F.spec_checked(leaf4,cli_only=True)[0]==H)
    check('CP202_all_three_original_journals_immutable',history()==immutable)
    v4_checks=len(env['checks'])-start
    from fifth_edge import run_fifth_edge
    fifth=run_fifth_edge(locals(),e,env)
    return {'fifth_edge':fifth,'state':'PASS','rollback':args.fourth_rollback,'new_v4_checks':v4_checks,'authority':'EXPLICIT_SYNTHETIC_FIXTURE_NO_NATIVE_GRANT','all_consumers':observed,'current_input':ref(lp4)}
