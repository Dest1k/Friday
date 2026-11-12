#!/usr/bin/env python3
"""Finite static source/config metadata collector; never imports installed code."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import yaml

os.umask(0o077)
OUT = Path('/home/jericho/.cache/FRW-ASTRA-F06-ORDINARY-CONSTRUCTOR-ROOTS-20261112')
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
N = H / 'hermes-agent'
U = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY207-ROOT-BINDING-SOURCE-20261112')
O = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
B = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
G6 = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112')
CRITERION = Path('/home/jericho/.cache/FRW-ASTRA-F06-FIRST-WRONGREAD-PRIVACY-CRITERION-20261112')
TZ = datetime.timezone(datetime.timedelta(hours=3))
def now():
    return datetime.datetime.now(TZ).isoformat()
def ref(p):
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
def meta(p):
    answer = dict(path=str(p), resolved=str(p.resolve()), exists=p.exists(), symlink=p.is_symlink())
    try:
        s = p.lstat()
        answer.update(mode=oct(stat.S_IMODE(s.st_mode)), uid=s.st_uid, gid=s.st_gid,
                      dev=s.st_dev, ino=s.st_ino, nlink=s.st_nlink,
                      directory=stat.S_ISDIR(s.st_mode))
    except FileNotFoundError:
        pass
    return answer
def write(name, obj):
    p=OUT/name
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.chmod(p, 0o600)
    return ref(p)
def field(cfg, path):
    parts=path.split('.')
    cur=cfg
    for k in parts:
        if not isinstance(cur, dict) or k not in cur:
            return {'present':False}
        cur=cur[k]
    # Only literal path/boolean/provider fields selected by the caller.
    if not isinstance(cur, (str, bool, int, float, type(None))):
        return {'present':True,'type':type(cur).__name__}
    return {'present':True,'value':cur}
def starttime(pid):
    return int(Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19])

collection_start=now()
pid=744387
birth_before=starttime(pid)
assert birth_before==6344413
raw_env=Path(f'/proc/{pid}/environ').read_bytes().split(b'\0')
env={k.decode():v.decode() for item in raw_env for k,sep,v in [item.partition(b'=')] if sep}
safe_keys=('HOME','HERMES_HOME','HERMES_MANAGED_DIR','HERMES_PROFILES_ROOT',
           'HERMES_CONFIG_PATH','HERMES_LOG_DIR','HERMES_STATE_DIR','HERMES_MEMORY_DIR',
           'HERMES_WORKSPACE_DIR','HERMES_SESSIONS_DIR','HERMES_CACHE_DIR',
           'HERMES_DATA_DIR_SUFFIX','TERMINAL_CWD','TMPDIR','TMP','TEMP')
safe_environment={k:{'present':k in env, **({'value':env[k]} if k in env else {})} for k in safe_keys}
process=dict(pid=pid,birth_start_ticks=birth_before,cwd=os.readlink(f'/proc/{pid}/cwd'),
             selected_nonsecret_environment=safe_environment,
             process_GATEWAY_PROXY_URL_nonempty=bool(env.get('GATEWAY_PROXY_URL','').strip()),
             stdout_stderr={fd:os.readlink(f'/proc/{pid}/fd/{fd}') for fd in ('1','2')})
del raw_env,env

profile_rel={'default':'config.yaml','dest':'profiles/dest_telegram/config.yaml',
             'tester':'profiles/telegram-bot-8812646969/config.yaml'}
selected=('memory.provider','memory.memory_enabled','memory.user_profile_enabled',
          'gateway.multiplex_profiles','gateway.sessions_dir','gateway.proxy_url',
          'terminal.cwd','compression.checkpoint_required')
prior_path=B/'F06-CURRENT206-MEMORY-MODE-METADATA-20261112.json'
prior=json.loads(prior_path.read_text())
configs={}
profiles={}
for label,rel in profile_rel.items():
    p=H/rel
    r=ref(p)
    cfg=yaml.safe_load(p.read_text())
    assert isinstance(cfg,dict)
    chosen={k:field(cfg,k) for k in selected if k!='gateway.proxy_url'}
    chosen['gateway.proxy_url']={'present':'proxy_url' in (cfg.get('gateway') or {}),
                                 'nonempty':bool((cfg.get('gateway') or {}).get('proxy_url'))}
    mem=cfg.get('memory') or {}
    assert mem.get('provider')=='' and mem.get('memory_enabled') is True and mem.get('user_profile_enabled') is True
    assert prior['profiles'][label]['sha256']==r['sha256']
    home=p.parent
    configs[label]=r
    profiles[label]=dict(config=r,selected_nonsecret_fields=chosen,config_stat=meta(p),
                         unchanged_since_prior206_metadata=True,
                         source_derived_memory_mode='builtin/core, both curated stores enabled',
                         external_provider_selected=False,
                         source_derived_paths={
                             'profile_home':str(home),'memory':str(home/'memories/MEMORY.md'),
                             'user_profile':str(home/'memories/USER.md'),
                             'state_database':str(home/'state.db'),
                             'transcripts_and_request_dumps':str(home/'sessions'),
                             'logs':str(home/'logs'),'scoped_file_read_workspace':str(home/'workspace')})
    del cfg

bulk_ref=ref(O/'OBSERVED-BULK-FACTS.json')
bulk=json.loads((O/'OBSERVED-BULK-FACTS.json').read_text())
assert bulk['profile_configs']==configs
del bulk

ranges={
 'gateway/run_turn.py':[(285,322),(2328,2348),(2713,2726),(2986,2993),(3129,3137),(3161,3171),(4412,4435),(4450,4463),(4490,4495)],
 'gateway/run_turn_runner.py':[(1111,1178),(1687,1727),(1946,1962)],
 'run_agent.py':[(295,318),(934,965)],
 'agent/agent_init.py':[(711,720),(1230,1250),(1344,1423),(2482,2491)],
 'agent/memory_provider.py':[(42,49)],
 'tools/memory_tool.py':[(38,44),(295,312)],
 'tools/memory_tool_store.py':[(141,160),(267,270)],
 'agent/turn_finalizer.py':[(682,694),(880,889)],
 'agent/codex_runtime.py':[(708,717)],
 'hermes_constants.py':[(26,48),(111,118),(1190,1197)],
 'hermes_cli/config.py':[(438,440),(2100,2120),(2300,2315),(2381,2405),(2420,2427)],
 'hermes_cli/managed_scope.py':[(45,62),(102,112)],
 'hermes_cli/friday_credential_admission.py':[(31,36),(3495,3505)],
 'gateway/config_loader.py':[(22,34)],
 'gateway/run.py':[(1821,1854),(2409,2421),(2967,2981),(3602,3610),(4365,4369),(4719,4742)],
 'gateway/run_config_loaders.py':[(48,82)],
 'gateway/config.py':[(583,592),(793,802)],
 'gateway/session.py':[(820,853)],
 'hermes_state.py':[(174,176),(196,199),(429,443)],
 'hermes_logging.py':[(326,344),(958,979)],
 'agent/session_persistence.py':[(590,598)],
 'agent/trajectory.py':[(37,55)],
 'tools/file_tools.py':[(780,802)],
 'hermes_cli/friday_user_scope.py':[(189,232),(300,323),(409,420),(487,499),(824,864),(940,952),(962,995)],
 'tools/scoped_ooxml_password.py':[(1,19),(580,655)],
}
sources={}
for name,spans in ranges.items():
    p=N/name
    ls=p.read_text().splitlines()
    sources[name]={'ref':ref(p),'ranges':[{'start':a,'end':min(b,len(ls)),
        'text':'\n'.join(f'{i+1}: {ls[i]}' for i in range(a-1,min(b,len(ls))))} for a,b in spans]}

template=json.loads((U/'ROOT-REVIEW-TEMPLATES.UNBOUND.json').read_text())
expected=template['runtime_privacy_review']['runtime_hashes']
runtime_hash_matches={name:dict(expected_sha256=sha,actual=ref(N/name),matches=ref(N/name)['sha256']==sha)
                      for name,sha in expected.items()}
assert all(x['matches'] for x in runtime_hash_matches.values())

tree=ast.parse((N/'gateway/run_turn_runner.py').read_text())
factory=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=='_build_fresh_agent')
call=next(x for x in ast.walk(factory) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='AIAgent')
explicit_kwargs=[k.arg for k in call.keywords if k.arg is not None]
assert 'memory_manager' not in explicit_kwargs and 'skip_memory' not in explicit_kwargs

private_roots=sorted(map(str,[U,O,B,G6,CRITERION,OUT]))
product_roots=[str(H)]
private_root_metadata=[meta(Path(p)) for p in private_roots]
disjoint=all(not (Path(p).resolve().is_relative_to(Path(r).resolve()) or
                   Path(r).resolve().is_relative_to(Path(p).resolve())) for p in private_roots for r in product_roots)
assert disjoint
root_meta=meta(H)
managed_overlay_observation={'etc_hermes_exists':Path('/etc/hermes').exists(),
                            'etc_hermes_config_exists':Path('/etc/hermes/config.yaml').exists(),
                            'managed_marker_metadata':[meta(p) for p in
                                (H/'FRIDAY-INSTALL.json',H/'FRIDAY-PROFILE.json',H/'hermes-agent.source.json')]}
legacy_gateway_metadata=meta(H/'gateway.json')
assert not legacy_gateway_metadata['exists'] and not legacy_gateway_metadata['symlink']
birth_after=starttime(pid)
assert birth_after==birth_before
head=subprocess.check_output(['git','--no-optional-locks','rev-parse','HEAD'],cwd=H.parent.parent,text=True).strip()

basis={
 'schema':'frw.Astra.F06.ordinary-constructor-root-source-basis.v1',
 'collected_at_moscow':now(),'collection_started_at_moscow':collection_start,
 'method':'Static AST/text/hash, safe YAML projections, path metadata and selected /proc metadata only; no installed module execution/import, database open, credentials or document bodies',
 'repo_head_observed':head,'repo_head_requested':'aef7541d558b9072370c748412b11757d7b8000c',
 'installed_source_root':str(N),'source_files':sources,
 'source_privacy_runtime_hashes_all12_match_207_template':runtime_hash_matches,
 'ordinary_constructor_ast':{'line':call.lineno,'end_line':call.end_lineno,
                             'explicit_keyword_names':explicit_kwargs,
                             'spread_expressions':[ast.unparse(k.value) for k in call.keywords if k.arg is None],
                             'explicit_memory_manager_handoff':False,'explicit_skip_memory_override':False,
                             'spread_keys_must_be_read_with_allowlists':'gateway/run_turn.py:292-300 and gateway/run.py:2977-2981'},
 'profile_configs':configs,'profiles':profiles,
 'same_profile_refs_as_root_bulk_observation':True,'root_bulk_observation_ref':bulk_ref,
 'prior206_memory_metadata_ref':ref(prior_path),'gateway_metadata':process,
 'managed_overlay_observation':managed_overlay_observation,
 'legacy_gateway_json_metadata':legacy_gateway_metadata,
 'effective_product_roots':product_roots,'product_root_metadata':root_meta,
 'private_roots':private_roots,'private_root_metadata':private_root_metadata,
 'private_vs_product_paths_currently_canonical_disjoint':disjoint,
 'collector_ref':ref(OUT/'collect_readonly.py')}
basis_ref=write('SOURCE-BASIS.json',basis)

result={
 'schema':'frw.Astra.F06.ordinary-constructor-memory-and-root-result.v1',
 'assignment':'ASTRA-NATIVE-F06-ORDINARY-CONSTRUCTOR-ROOTS-20261112','generation':1,
 'status':'READ_ONLY_SOURCE_AND_SELECTED_CONFIG_EVIDENCE_READY_FOR_ROOT_JUDGMENT',
 'completed_at_moscow':now(),'basis_ref':basis_ref,
 'effective_product_roots':product_roots,'effective_roots_profile_config_refs':configs,
 'effective_roots_source_basis':[basis_ref], 'private_roots':private_roots,
 'conclusions':[
  {'id':'ordinary_constructor','classification':'SOURCE_DERIVED',
   'finding':'The ordinary non-proxy gateway _run_agent path imports run_agent.AIAgent, puts it in TurnContext, and TurnRunner.run_sync resolves/reuses the session agent or calls _build_fresh_agent. That constructor does not supply memory_manager or skip_memory; its runtime and checkpoint kwargs are allowlisted without these keys. AIAgent defaults are memory_manager=None, skip_memory=False and forwards them to init_agent/_init_memory. No ordinary API-session memory-manager handback is present in this constructor.',
   'refs':['gateway/run_turn.py:2986-2993,4412-4463','gateway/run_turn_runner.py:1111-1178,1946-1962','gateway/run_turn.py:292-300','gateway/run.py:2967-2981','run_agent.py:295-318','agent/agent_init.py:2482-2490'],
   'live_agent_object_observed':False,'new_turn_executed':False},
  {'id':'core_memory_all3','classification':'OBSERVED_CONFIG_PLUS_SOURCE_INFERENCE',
   'finding':'All three exact config files still have memory.provider="", memory.memory_enabled=true and memory.user_profile_enabled=true, byte-identical to the prior206 metadata and the Root207 bulk observation. Empty string is a CORE_MEMORY_PROVIDER_SENTINEL; with the ordinary default manager=None, _init_memory retains _memory_manager=None instead of loading an external provider. Built-in MEMORY.md/USER.md remain enabled and are loaded from the routed profile home.',
   'refs':['agent/memory_provider.py:42-49','tools/memory_tool.py:295-312','agent/agent_init.py:1344-1423','tools/memory_tool.py:38-40','tools/memory_tool_store.py:267-270']},
  {'id':'raw_caption_external_sync','classification':'SOURCE_DERIVED_CONDITIONAL',
   'finding':'Completed ordinary turns call _sync_external_memory_for_turn with original_user_message. If an external manager exists and both texts are nonempty and the turn is not interrupted, the method flattens the original user content and calls sync_all and possibly queue_prefetch_all. For the demonstrated normal core-mode construction, _memory_manager=None makes the method return before this mirror. This establishes no external raw-caption synchronization along that source/config path; it does not establish absence of intentional user-row retention, logs, builtin memory tool writes/background review, summaries, outbound payloads or other consumers.',
   'refs':['agent/turn_finalizer.py:880-889','agent/codex_runtime.py:708-717','run_agent.py:934-965']},
  {'id':'effective_product_file_roots','classification':'SOURCE_DERIVED_WITH_SELECTED_ACTUAL_METADATA',
   'finding':'H is the canonical launch home and actual gateway cwd/HERMES_HOME. Scoped user runtime homes are H/profiles/<runtime_profile>; ordinary file reads use cap.home/workspace and descriptor/NOFOLLOW checks before generic file ops. Builtin memory, state DB, per-profile sessions/request dumps and logs resolve under those homes; launch sessions_dir is not overridden in the selected configs and legacy gateway.json is absent (also refused by the admitted channel_inputs path). Relative trajectory defaults resolve under actual gateway cwd=H. Thus [H] is the enclosing product-file/persistence root for this ordinary F06 source/config chain. It is not a global filesystem capability restriction.',
   'refs':['hermes_constants.py:111-118','gateway/run_config_loaders.py:48-82','gateway/run.py:1821-1854,4365-4369,4719-4742','hermes_cli/friday_user_scope.py:300-323,824-864','tools/file_tools.py:788-802','tools/memory_tool.py:38-40','hermes_state.py:196-199,429-443','agent/agent_init.py:1236-1249','hermes_logging.py:326-344','agent/trajectory.py:37-55']},
  {'id':'private_preparation_disjointness','classification':'PATH_METADATA_AND_CONSUMER_CONTRACT',
   'finding':'The five exact Root-declared private package/preparation/evidence roots plus this evidence directory are canonical and outside H; no product/source effects were made. This source result supplies enclosing roots and current all3 config refs. Root must still apply the existing current207 private_material proof coverage and exact private-path marker checks on final config/process/scenario/resources; this collector does not grant those judgments.',
   'refs':['current207.py:502-544 (Root package source)'],
   'source_ref':ref(U/'current207.py'),'currently_disjoint':disjoint}
 ],
 'limits':[
  'No installed native consumer, guarded product import, AIAgent construction, live manager accessor, model, Telegram, Office, DB connection, service/installation write or credential/document body read occurred.',
  'The constructor conclusion concerns the normal non-proxy ordinary gateway path; source includes a prior proxy branch and cached-agent reuse. No actual session agent object or Python in-process context/cache was introspected. Proxy URL in profile YAML/process env is empty/absent; profile secret content was deliberately not read, so the effective scoped-secret proxy decision is not independently observed here.',
  'Config YAML projections are not an executed effective loader. Source-managed deployments suppress the managed_scope overlay; additionally /etc/hermes and its config are absent and HERMES_MANAGED_DIR is absent in the observed process. Failures/fallbacks/mutation after this snapshot must be handled by Root current proof.',
  'stdout/stderr point at a socket, not a product-owned file. OS service journal storage, arbitrary generic terminal/file-tool capabilities outside ordinary cap, provider-side storage/network, and all unrelated product/plugin paths are not exhaustively inventoried. The [H] root claim is limited to the demonstrated ordinary F06 product-file chain.',
  'No global no-secret-persistence, external-memory audit, semantic wrong-password verdict, ingress-history absence, authority, once/clock admission, or full privacy/F06 PASS is supplied.',
  'Root bulk observation contains additional private facts; only its profile_configs were read for this comparison. It was not copied or semantically accepted wholesale.',
  'Private path disjointness does not by itself prove no product-visible marker/reference or user-prompt leakage; the final current207 marker checks and scoped post-effect criterion remain necessary.'
 ],
 'remaining_root_checks':[
  'Pin this RESULT and SOURCE-BASIS references and independently accept their exact narrow source/config scope. Confirm same installed207 receipt/input and pinned runtime source bytes; do not relabel prior206 consumer execution as207.',
  'Accept normal ordinary profile/route scope and retained current native-boundary observations; do not require a new memory-manager API accessor. Treat runtime manager=None as supported source/config inference unless genuinely observed through already-admitted current instrumentation.',
  'Keep sorted effective_product_roots=[H] for this scoped product-file chain and pin exact all3 profile config refs. Complete private_roots coverage for U/O/B/g6root/criterionchilddir/thisdir, every scenario/proof directory, future workdir and clock/wait evidence; independently perform current207 private_material exact marker checks against final configs and gateway cmdline/environ.',
  'Write actual Root runtime/privacy judgment incorporating narrow unchanged206 pure-leaf evidence, source207 consumer hashes, this constructor/core-mode/root derivation and the post-effect supplied-password criterion; preserve historical7/8 FAIL and runtime-wrapper WARN_NOT_RUN.',
  'Finish remaining real Root history/lineage/once/cursor/current207/resource/stop/slot checks and semantic reviews before new clock/grant. Reobserve final mutable identities/config/CAS/boundaries after refs settle using the existing workflow.',
  'After exactly one admitted new upload/wrong-password READ, grade the actual new reply and new technical copies/rows/logs against the supplied wrong password, exempt the intentional original private user request, and retain uncertainty/refusal truthfully without resend/replay.'
 ],
 'recommendation':'Use this finite evidence as source/config basis for Root’s existing narrow runtime-privacy/root judgment. Continue the already-reviewed ordinary207 binding workflow after final mutable checks; do not add a manager accessor, runtime import bypass or new global audit as a prerequisite.',
 'effects':{'product_writes':0,'native_consumer_executions':0,'guarded_product_imports':0,'database_connections':0,'telegram_model_office_calls':0,'authority_or_clock_created':False},
 'artifact_permissions':'directory0700/files0600'}
result_ref=write('RESULT.json',result)
print(json.dumps({'result':result_ref,'basis':basis_ref,'completed_at_moscow':result['completed_at_moscow'],
                  'all3_config_refs_equal_bulk':True,'all12_runtime_hashes_match':True,
                  'disjoint':disjoint,'source_files':len(sources)},ensure_ascii=False))
