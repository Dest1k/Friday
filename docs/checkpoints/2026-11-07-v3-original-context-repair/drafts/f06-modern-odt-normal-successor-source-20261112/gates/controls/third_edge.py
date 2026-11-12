"""Exact third-edge source fixtures; no production authority and no native process."""
import copy,json,sys,shutil,stat,os
from pathlib import Path

def run_third_edge(e,env):
    args=e['args'];P2=e['P'];F2=e['F'];O2=e['O'];H=e['H'];N=e['N'];T=e['T'];native=e['native']
    enc=e['enc'];sha=e['sha'];write=e['write'];ref=e['ref'];check=e['check'];refused=e['refused'];q2=e['q2'];tx2=e['tx2'];qr2=e['qr2'];leaf2=e['leaf2'];lp2=e['lp2']
    tx1=e['tx1'];q1=e['q1'];cp2_immutable=e['cp2_immutable']
    P=T/'project201';shutil.copytree(P2,P)
    # Exact oldv2 current200 -> finalv3+diagnostic helper change, not an already
    # upgraded helper seeded into all historical edges.
    for helper in ('scripts/friday_install.py','scripts/friday_ordinary_install.py'):
        write(H/helper,(P2/helper).read_bytes())
        write(P/helper,(args.third_helpers_root/helper).read_bytes())
    validation={k:v for k,v in tuple(sys.modules.items()) if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.')}
    for k in validation:del sys.modules[k]
    env['mod']('scripts',P/'scripts');F=env['load'](P/'scripts/friday_install.py','scripts.friday_install');O=env['load'](P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
    for k in ('PROJECT_DSH_CURRENT_INPUT','PROJECT_DSH_CURRENT_INVENTORY','PROJECT_DSH_CURRENT_RECEIPT','PROJECT_DSH_CURRENT_STAMP','PROJECT_DSH_CURRENT_ANCESTOR'):setattr(O,k,copy.deepcopy(getattr(O2,k)))
    F.native_packages=lambda source:None;native.F=F;native.O=O
    name=O.CURRENT_SOURCE_THIRD_LAYER;patch='patches/hermes/'+name+'.patch';mn='patches/hermes/'+name+'-manifest.json'
    for n in (patch,mn):write(P/n,(args.third_layer_root/n).read_bytes())
    manifest=json.loads((P/mn).read_bytes());rows=manifest['files'];assert len(rows)==1
    check('CP201_exact_unmodified_production_pair',ref(P/mn)['sha256']==O.CURRENT_SOURCE_THIRD_MANIFEST and ref(P/patch)['sha256']==O.CURRENT_SOURCE_THIRD_PATCH)
    after={r['path']:(args.third_native_after/r['path']).read_bytes() for r in rows}
    check('CP201_exact_one_native_before_after',set(after)==set(O.CURRENT_SOURCE_THIRD_NATIVE) and all(ref(N/n)['sha256']==O.CURRENT_SOURCE_THIRD_NATIVE[n][0] and sha(b)==O.CURRENT_SOURCE_THIRD_NATIVE[n][1] for n,b in after.items()))
    leaf3=copy.deepcopy(leaf2);leaf3['project_files']={str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()};lp3=T/'leaf483.json';write(lp3,leaf3)
    check('CP201_project483_plugins52',len(leaf3['project_files'])==483 and len([n for n in leaf3['project_files'] if n.startswith('plugins/friday_rework/')])==52)
    q3=copy.deepcopy(q2);q3.update(candidate_project=str(P),previous_input=ref(lp2),current_input=ref(lp3),candidate_input=ref(lp3),marker=ref(H/F.MARKER),source_receipt=ref(H/'hermes-agent.source.json'),target_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(N/'install-stamp.json'),configuration=ref(H/'config.yaml'),installed_layers=200,project_inventory=leaf3['project_files'],project_inventory_sha256=sha(enc(leaf3['project_files'])),layer_names=[name],layer_manifest_updates=[mn],project_file_updates=sorted(n for n in leaf2['project_files'] if leaf2['project_files'][n]!=leaf3['project_files'][n]),current_source_successor={'schema':O.CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA,'root_project_update':q1['current_source_successor']['root_project_update'],'previous_native_update':qr2})
    check('CP201_actual_oldv2_to_finalv3_helper_delta',q3['project_file_updates']==['scripts/friday_ordinary_install.py'])
    def spec(q=None):return F.spec_checked(leaf3,cli_only=True,source_update=q3 if q is None else q)
    check('CP201_real_whole_spec_before',spec()[0]==H)
    builder=e['builder'];built=builder.build_request(builder.parse_args(['--layer',name,'--home',str(H),'--candidate-project',str(P),'--native-unit',q3['native_unit']['path'],'--previous-input',str(lp2),'--current-input',str(lp3),'--current-source-project-update',q3['current_source_successor']['root_project_update']['path'],'--current-source-native-predecessor',qr2['path'],'--seconds','600']))
    check('CP201_real_builder_exact_v3',enc(built)==enc(q3))
    def history():return {str(p.relative_to(tx2)):sha(p.read_bytes()) for p in tx2.rglob('*') if p.is_file()}
    check('CP201_prior_CP200_unchanged',history()==cp2_immutable)
    CP=env['load'](args.publisher.resolve(),'portable_third_publication');CP.gateway_running=lambda *a,**kw:False
    def pub_refused(label,fn):
        try:fn()
        except (CP.Refused,OSError) as error:check(label,True,type(error).__name__+':'+str(error));return
        check(label,False,'accepted')
    if not args.third_rollback and not args.fourth_helpers_root:
        for label,mutate in [
            ('wrong_root_hash',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
            ('wrong_CP200_hash',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
            ('wrong_root_type',lambda q:q['current_source_successor'].update(root_project_update=True)),
            ('missing_CP200',lambda q:q['current_source_successor'].pop('previous_native_update')),
            ('extra_context',lambda q:q['current_source_successor'].update(allow=True)),
            ('arbitrary_list',lambda q:q['current_source_successor'].update(previous_native_update=[qr2])),
            ('fourth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v4')),
            ('v2_not_v3',lambda q:q['current_source_successor'].update(schema=O.CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA)),
            ('wrong_before_layers',lambda q:q.update(installed_layers=199)),
            ('bool_before_layers',lambda q:q.update(installed_layers=True)),
            ('wrong_before_files',lambda q:q.update(installed_files=17887)),
            ('wrong_layer',lambda q:q.update(layer_names=[O.CURRENT_SOURCE_SECOND_LAYER])),
            ('extra_layer',lambda q:q.update(layer_names=[name,O.CURRENT_SOURCE_SECOND_LAYER])),
            ('wrong_receipt',lambda q:q['source_receipt'].update(sha256='f'*64)),
            ('wrong_stamp',lambda q:q['stamp'].update(sha256='f'*64)),
            ('wrong_marker',lambda q:q['marker'].update(sha256='f'*64)),
            ('plugin_claim',lambda q:q.update(plugin_set=['plugins/friday_rework/fixture0.py'])),
            ('native_addition_claim',lambda q:q.update(staged_files=[{'path':'new'}])),
            ('reset_to_CP199',lambda q:q.update(previous_input=q2['previous_input'])),
            ('foreign_origin',lambda q:q.update(candidate_project=str(P2))),
        ]:
            bad=copy.deepcopy(q3);mutate(bad);refused('CP201_'+label,lambda bad=bad:spec(bad))
        alias=T/'CP200-noncanonical.json';write(alias,(tx2/'request.json').read_bytes());bad=copy.deepcopy(q3);bad['current_source_successor']['previous_native_update']=ref(alias)
        refused('CP201_CP200_canonical_path',lambda:spec(bad))
        root_alias=T/'root-alias.json';write(root_alias,Path(q3['current_source_successor']['root_project_update']['path']).read_bytes());bad=copy.deepcopy(q3);bad['current_source_successor']['root_project_update']=ref(root_alias)
        refused('CP201_root_canonical_path',lambda:spec(bad))
        def corrupt(label,p,fn):
            saved=p.read_bytes();write(p,fn(saved))
            try:refused('CP201_'+label,spec)
            finally:write(p,saved)
        def j(raw,fn):d=json.loads(raw);fn(d);return enc(d)
        for tx,label in ((tx1,'CP199'),(tx2,'CP200')):
            for rel in ('request.json','intent.json','committed.json','before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
                corrupt(label+'_'+rel,tx/rel,(lambda raw:j(raw,lambda d:d.update(gateway_started=True))) if rel in ('intent.json','committed.json') else (lambda raw:raw+b' '))
            (tx/'request.json').chmod(0o644)
            try:refused('CP201_'+label+'_raw_mode',spec)
            finally:(tx/'request.json').chmod(0o600)
            saved=(tx/'committed.json').read_bytes();(tx/'committed.json').unlink()
            try:refused('CP201_'+label+'_partial_commit',spec)
            finally:write(tx/'committed.json',saved)
            write(tx/'rolled-back.json',{})
            try:refused('CP201_'+label+'_rolledback',spec)
            finally:(tx/'rolled-back.json').unlink()
        duplicate=H/'preparation/ordinary-source-update-v45-duplicate';write(duplicate/'intent.json',{'current_input':{'path':str(lp2),'sha256':'f'*64}})
        try:refused('CP201_CP200_halfclaim_duplicate',spec)
        finally:shutil.rmtree(duplicate)
        partial=H/'preparation/ordinary-source-update-v45-halfclaim';write(partial/'request.json',{'current_input':{'path':'/foreign','sha256':ref(lp3)['sha256']}})
        try:refused('CP201_new_halfclaim_partial',spec)
        finally:shutil.rmtree(partial)
        corrupt('project_plugin_drift',P/'plugins/friday_rework/fixture0.py',lambda b:b+b' ')
        corrupt('physical_plugin_drift',H/'plugins/friday_rework/fixture0.py',lambda b:b+b' ')
        corrupt('physical_native_drift',N/'fixture/0.txt',lambda b:b+b' ')
        from hermes_yaml import safe_load,safe_dump
        def drift(raw):d=safe_load(raw);d['model']['default']='foreign';return safe_dump(d).encode()
        corrupt('semantic_config_drift',H/'config.yaml',drift)
        rawpath=T/'raw-v3.json'
        for label,raw in [('duplicate',b'{"seconds":600,'+enc(q3)[1:]),('nan',enc(q3).replace(b'"seconds": 600',b'"seconds": NaN')),('overflow',enc(q3).replace(b'"seconds": 600',b'"seconds": 1e999'))]:
            write(rawpath,raw);pub_refused('CP201_raw_'+label,lambda raw=raw:CP.current_source_request_bytes(q3,rawpath,sha(raw)))
        write(rawpath,enc(q3));rawpath.chmod(0o644)
        try:pub_refused('CP201_raw_mode644',lambda:CP.current_source_request_bytes(q3,rawpath,ref(rawpath)['sha256']))
        finally:rawpath.chmod(0o600)
        link=T/'raw-link.json';link.symlink_to(rawpath)
        try:pub_refused('CP201_raw_symlink',lambda:CP.current_source_request_bytes(q3,link,ref(rawpath)['sha256']))
        finally:link.unlink()
        os.link(rawpath,link)
        try:pub_refused('CP201_raw_hardlink',lambda:CP.current_source_request_bytes(q3,rawpath,ref(rawpath)['sha256']))
        finally:link.unlink()
        # Valid raw third context survives exact bytes/custody checking.
        check('CP201_raw_exact_valid',CP.current_source_request_bytes(q3,rawpath,ref(rawpath)['sha256'])==enc(q3))
    raw=json.dumps(q3,sort_keys=False,separators=(',',':')).encode()+b'\n';rp=T/'request201.json';write(rp,raw);qs=sha(raw);tx3=H/'preparation'/('ordinary-source-update-v45-'+qs[:16])
    observed=[];real=CP.current_source_consumer_checked
    class LateFailure(CP.Refused):pass
    def tracked(value,request,candidate,*,committed=False,inspect=False):
        real(value,request,candidate,committed=committed,inspect=inspect);observed.append((committed,inspect))
        if args.third_rollback and committed and inspect:raise LateFailure('injected_final_default_inspect')
    CP.current_source_consumer_checked=tracked
    paths=['hermes-agent/'+n for n in after]+['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json',patch,mn]+q3['project_file_updates']
    before={n:((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode)) if (H/n).exists() else None for n in paths}
    if args.third_rollback:
        try:CP.run(q3,rp,qs)
        except LateFailure:pass
        else:raise AssertionError('missing late refusal')
        check('CP201_rollback_after_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP201_rollback_exact_all_effects',all((((H/n).read_bytes(),stat.S_IMODE((H/n).stat().st_mode))==v if v is not None else not (H/n).exists()) for n,v in before.items()))
        check('CP201_rollback_journal',json.loads((tx3/'rolled-back.json').read_bytes())['state']=='ROLLED_BACK')
        for k in tuple(sys.modules):
            if k=='_friday_install_validation_plugins' or k.startswith('_friday_install_validation_plugins.'):del sys.modules[k]
        sys.modules.update(validation);env['mod']('scripts',P2/'scripts');sys.modules['scripts.friday_install']=F2;sys.modules['scripts.friday_ordinary_install']=O2;native.F=F2;native.O=O2
        check('CP201_rollback_source200_default_retained',F2.spec_checked(leaf2,cli_only=True)[0]==H)
        pub_refused('CP201_rollback_consumed_no_replay',lambda:CP.run(q3,rp,qs))
    else:
        result=CP.run(q3,rp,qs)
        check('CP201_real_publisher_one_file_one_layer',result['files']==1 and result['layers']==1 and result['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED')
        check('CP201_all_real_consumers',observed==[(False,False),(False,True),(True,True)])
        check('CP201_exact_raw_retained',(tx3/'request.json').read_bytes()==raw)
        check('CP201_default_current_leaf',F.spec_checked(leaf3,cli_only=True)[0]==H)
        check('CP201_default_inspect',F.inspect(leaf3,ref(lp3)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
        # Unchanged201 native semantic proof reused; no duplicate check for counts.
        check('CP201_helper_published_exact',all((H/n).read_bytes()==(P/n).read_bytes() for n in q3['project_file_updates']))
        check('CP201_native_after_exact',all((N/n).read_bytes()==b for n,b in after.items()))
        rec=json.loads((H/'hermes-agent.source.json').read_bytes());oldrec=json.loads(before['hermes-agent.source.json'][0])
        check('CP201_17887_other_receipt_rows_unchanged',len(rec['files'])==17888 and all(v==rec['files'][n] for n,v in oldrec['files'].items() if n not in after))
        bad=copy.deepcopy(q3);bad.update(previous_input=ref(lp3),installed_layers=201);bad['current_source_successor']['previous_native_update']=ref(tx3/'request.json')
        refused('CP201_fourth_edge_even_with_v3_refused',lambda:F.spec_checked(leaf3,cli_only=True,source_update=bad))
        # Remove both historical project trees: canonical journals, not retired
        # source/helper physical bytes, are the ancestral evidence.
        P2.rename(T/'retired-project200')
        check('CP201_historical_projects_absent_current_leaf_pass',F.spec_checked(leaf3,cli_only=True)[0]==H)
    check('CP201_CP200_original_journal_unchanged',history()==cp2_immutable)
    e['assert_history']('CP201_CP199_original_journal_unchanged')
    from fourth_edge import run_fourth_edge
    fourth=run_fourth_edge(locals(),env)
    return {'fourth_edge':fourth,'state':'PASS','rollback':args.third_rollback,'real_exact_pair':{n:ref(args.third_layer_root/n) for n in (patch,mn)},'authority':'EXPLICIT_SYNTHETIC_FIXTURE_NO_NATIVE_GRANT','native_after':{n:ref(args.third_native_after/n) for n in after},'all_consumers':observed,'current_input':ref(lp3)}
