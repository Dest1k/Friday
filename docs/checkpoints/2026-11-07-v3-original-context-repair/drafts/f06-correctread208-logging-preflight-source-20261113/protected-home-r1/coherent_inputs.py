"""Inert input-assembly helpers for the unchanged accepted5 Root F06 driver.

Import and no arguments perform no file/process/network/current-state access.
All constructors below are pure. Explicit read/load/write functions only touch
caller-selected files. There is no observe/check/issuer/clock/once/execute call.
Root owns every factual/semantic judgment and every future live effect.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import types

ROOT = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-CORRECTREAD208-ROOT-20261113')
SOURCE = ROOT/'source-protected-home-r1'
PACKAGE = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F06-COHERENT-CORRECTREAD208-CALLER-PREP-20261113')
FREEZE = {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-CORRECTREAD208-ROOT-20261113/source-protected-home-r1/SOURCE-FREEZE.json', 'bytes': 822, 'sha256': '60496cf92f5241bf8d77d4c10c650863e0f644526db064869f3566599233d394'}
SOURCE5 = {
 'current_root.py': {'bytes':56008,'sha256':'6bd5fe52cdb005651dde83c004d1cb79bb51d147a224ae4d1a6346618b8f07db'},
 'first_ingress.py': {'bytes':26519,'sha256':'6d813bb5ed3f4ddc5c5bf0f55539ef36c7e6578e3bedff791d7a9132306e26ea'},
 'f06_source.py': {'bytes':19110,'sha256':'1acef7dabc4221aa1e85ab38af47578b9e2d37e76f3e078a3a331a943fa80c21'},
 'f06_footer.py.txt': {'bytes':8042,'sha256':'f73f5a4af5bdfb8d82b41aa87ca831a52513f3f3e6dbb25464f46e15a1012e29'},
 'root_bind_dispatch_once.py': {'bytes':19526,'sha256':'7d69fd12f7239028e9857edcafbefdce0d4db22d01f4ed7055b0d1ed4f2f4526'},
}
DEFAULT_LIMIT = 1024**2
EXACT_LIMIT = 24*1024**2
DRIVER_FIELDS = {'schema','status','contract','source_freeze','independent_review','workdir','slot_identity','expected_binding_sha256'}
TIMING = {'operation_seconds':300,'reply_window_seconds':180,'ack_seconds':10,'reserve_seconds':5,'outer_seconds':600}
LIMITS = {'cpu_seconds':120,'max_rss_bytes':1073741824,'disk_bytes':33554432}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(v):
    return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def clone(v):
    return json.loads(encoded(v))


def unique(pairs):
    out = {}
    for k,v in pairs:
        need(k not in out,'ASSEMBLY_DUPLICATE_JSON_KEY')
        out[k] = v
    return out


def canonical_path(v):
    text = str(v) if isinstance(v,Path) else v
    need(type(text) is str and text.startswith('/') and not text.startswith('//')
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in text)
         and (text=='/' or all(p not in ('','.','..') for p in text.split('/')[1:]))
         and str(Path(text))==text,'ASSEMBLY_CANONICAL_PATH_REQUIRED')
    text.encode('utf-8')
    return Path(text)


def reference_shape(r):
    return (type(r) is dict and set(r)=={'path','bytes','sha256'}
            and type(r['path']) is str and canonical_path(r['path']).is_absolute() and type(r['bytes']) is int
            and 0<r['bytes']<=EXACT_LIMIT and type(r['sha256']) is str
            and re.fullmatch('[a-f0-9]{64}',r['sha256']) is not None)


def identity(s):
    return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def _read_bounded(path, limit, private):
    p = canonical_path(path)
    need(type(limit) is int and 0<limit<=EXACT_LIMIT,'ASSEMBLY_EXACT_READ_BOUND_REQUIRED')
    need(not any(q.is_symlink() for q in (p,*p.parents)),'ASSEMBLY_NO_SYMLINKS_REQUIRED')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        before = os.fstat(f.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
             and not stat.S_IMODE(before.st_mode)&0o002
             and (not private or stat.S_IMODE(before.st_mode)==0o600),'ASSEMBLY_UNSAFE_INPUT')
        raw = f.read(limit+1)
        after = os.fstat(f.fileno())
    need(len(raw)<=limit and identity(before)==identity(after)==identity(p.stat()),'ASSEMBLY_INPUT_CAS_OR_SIZE_CHANGED')
    return raw


def read(path, *, private=True):
    """Path ABI deliberately has the original 1 MiB default and no limit kwarg."""
    return _read_bounded(path,DEFAULT_LIMIT,private)


def read_reference(r, *, private=True):
    """Only an explicit exact leaf may opt into its <=24 MiB declared bound."""
    need(reference_shape(r),'ASSEMBLY_EXACT_REFERENCE_REQUIRED')
    raw = _read_bounded(r['path'],r['bytes'],private)
    need(len(raw)==r['bytes'] and digest(raw)==r['sha256'],'ASSEMBLY_PIN_CHANGED')
    return raw


# Both adapter and first-validator discover this exact callback for nested refs.
read.f06_read_reference = read_reference


def doc(r, *, private=True):
    return json.loads(read_reference(r,private=private),object_pairs_hook=unique)


def ref(path, *, private=True):
    raw = read(path,private=private)
    return {'path':str(canonical_path(path)),'bytes':len(raw),'sha256':digest(raw)}


def put_new(path, value):
    """Explicit Root artifact write only; never overwrites or creates parents."""
    path = canonical_path(path)
    parent = path.parent
    st = parent.stat()
    need(not any(q.is_symlink() for q in (parent,*parent.parents)) and stat.S_ISDIR(st.st_mode)
         and st.st_uid==os.getuid() and stat.S_IMODE(st.st_mode)==0o700,'ASSEMBLY_PRIVATE_PARENT_REQUIRED')
    raw = encoded(value)
    need(0<len(raw)<=EXACT_LIMIT,'ASSEMBLY_ARTIFACT_SIZE_BOUND')
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return {'path':str(path),'bytes':len(raw),'sha256':digest(raw)}


def source_refs():
    return {leaf:dict(path=str(SOURCE/leaf),**want) for leaf,want in SOURCE5.items()}


def checked_sources():
    """Explicit static-only loader; imports only these four inert Python files."""
    freeze = doc(FREEZE)
    need(freeze.get('schema')=='frw.F06.ordinary-singleton.source-freeze.v1'
         and freeze.get('files')==SOURCE5,'ASSEMBLY_SOURCE_FREEZE_CHANGED')
    refs = source_refs()
    for r in refs.values(): read_reference(r)
    modules = {}
    for leaf in ('f06_source.py','first_ingress.py','current_root.py','root_bind_dispatch_once.py'):
        r = refs[leaf]
        m = types.ModuleType('_Root208_'+leaf.replace('.','_'))
        m.__file__ = r['path']
        exec(compile(read_reference(r),r['path'],'exec'),m.__dict__)
        modules[leaf] = m
    return modules


def source_review_shape(review):
    """Actual unchanged driver's exact header; does not issue the Root decision."""
    need(type(review) is dict and review.get('decision')=='SOURCE_ONLY_READY_UNBOUND'
         and review.get('source_freeze_sha256')==FREEZE['sha256']
         and review.get('open_critical_defects')==[],'ASSEMBLY_DRIVER_REVIEW_HEADER_UNBOUND')
    return True


def unbound_inputs(adapter, *, installation):
    """Pure full eight-key mapping. Static pins do not establish installed/current."""
    c = adapter.unbound()
    refs = source_refs()
    c.update(adapter=refs['f06_source.py'],footer=refs['f06_footer.py.txt'],
             actual_root_B_checker=refs['current_root.py'],first_validator=refs['first_ingress.py'],
             product=clone(adapter.SUPPORTED208_PRODUCT),installation=clone(installation),
             source_reference=clone(adapter.EXPECTED_FIRST_SOURCE_REFERENCE),
             resources=dict(TIMING,**LIMITS,clock=None,owned_parent_wait_cleanup=None))
    return dict(schema='frw.Root.F06.same-upload-correctread-driver.v1',status='UNBOUND_NOT_GRANTED',
                contract=adapter.canonical_contract(c),source_freeze=clone(FREEZE),independent_review=None,
                workdir=None,slot_identity=None,expected_binding_sha256=None)


def prepare_contract(adapter, inputs, *, run_id, scenario_ref, first_ref, first,
                     proofs, boundary, clock_ref, owned_wait_ref, root_current_proof=None):
    """Pure exact correctREAD contract join. Accepts Root decisions, invents none."""
    need(set(inputs)==DRIVER_FIELDS and inputs['status']=='UNBOUND_NOT_GRANTED',
         'ASSEMBLY_UNBOUND_INPUT_TEMPLATE_REQUIRED')
    need(type(first) is dict and first.get('schema')=='frw.Root.F06.closed-first-upload.v1'
         and first.get('status')=='ROOT_BOUND_CLOSED_RECONCILED'
         and first.get('source_reference')==adapter.EXPECTED_FIRST_SOURCE_REFERENCE,
         'ASSEMBLY_ROOT_ACCEPTED_FIRST_REQUIRED')
    need(type(proofs) is dict and set(proofs)==adapter.PROOFS
         and all(reference_shape(r) for r in proofs.values()),'ASSEMBLY_ALL12_ROOT_PROOF_REFS_REQUIRED')
    need(all(reference_shape(r) for r in (scenario_ref,first_ref,clock_ref,owned_wait_ref)),
         'ASSEMBLY_TYPED_FUTURE_REFERENCES_REQUIRED')
    need(proofs['first_upload_reconciliation']==first['root_reconciliation'],
         'ASSEMBLY_TYPED_FIRST_RECONCILIATION_JOIN_REQUIRED')
    c = clone(inputs['contract'])
    c.update(run_id=run_id,scenario_ref=clone(scenario_ref),scenario_sha256=scenario_ref['sha256'],
             first_ingress=clone(first_ref),source_reference=clone(first['source_reference']),
             root_proofs=clone(proofs),boundary=clone(boundary),root_current_proof=clone(root_current_proof))
    c['resources'] = dict(TIMING,**LIMITS,clock=clone(clock_ref),owned_parent_wait_cleanup=clone(owned_wait_ref))
    adapter.contract_shape(c,bound=False)
    return adapter.canonical_contract(c)


def history_fact_fields(c, observed):
    """Only current join fields; Root supplies semantic classifications separately."""
    b = observed['f06_mutable_boundary']
    return dict(phase=c['phase'],source=clone(c['source']),source_reference=clone(c['source_reference']),
        first_ingress=clone(c['first_ingress']),history_manifest_sha256=observed['history']['manifest_sha256'],
        classified_run_ids=clone(observed['history']['run_ids']),native_boundary_sha256=b['native_boundary_sha256'],
        once_sha256=b['once_sha256'],ingress_lineage_sha256=b['ingress_lineage_sha256'])


def lineage_fact_fields(c, observed):
    return dict(phase=c['phase'],source=clone(c['source']),source_identity=clone(observed['source_identity']),
        current_ingress_lineage_sha256=observed['f06_mutable_boundary']['ingress_lineage_sha256'],
        source_reference=clone(c['source_reference']),first_ingress=clone(c['first_ingress']),
        native_qualification=clone(c['root_proofs']['actual_native_qualification']))


def logging_preflight_fact_fields(c, observed, plan):
    return dict(installed_product=clone(c['product']),installation_closure=clone(c['installation']['closure']),
        gateway=clone(observed['gateway']),B={k:c['boundary']['B'][k] for k in ('profile','session_id','session_key')},
        logging_sites=['agent/turn_context.py','gateway/run_turn.py'],runtime_hashes=clone(c['installation']['runtime_hashes']),
        technical_log_cursor=clone(observed['technical_log_cursor']),postcondition_plan=clone(plan))


def privacy_fact_fields(c, observed, *, private_roots, preflight_ref):
    need(reference_shape(preflight_ref),'ASSEMBLY_PREFLIGHT_REFERENCE_REQUIRED')
    return dict(installed_product=clone(c['product']),runtime_hashes=clone(c['installation']['runtime_hashes']),
        effective_roots_profile_config_refs=clone(observed['profile_configs']),
        private_roots=clone(private_roots),metadata_logging_preflight=clone(preflight_ref))


def scenario(adapter, *, supplied_password, accepted_first):
    """Pure private constructor; returned text must remain in Root protected RAM/file."""
    value = adapter.construct_scenario(supplied_password=supplied_password,first_dependency=accepted_first)
    adapter.scenario_shape(value)
    return value


def collect_technical_carrier_baseline(checker, *, databases, technical_log_cursor):
    """EXPLICIT FUTURE ROOT READ-ONLY CALL, ported from existing Y collector.
    Never invoked at import/noarg/preparation tests. No log/file body is opened.
    Returns one value containing the original ten-root metadata inventory, existing
    journal cursor, database metadata, and both sink metadata cursors.
    Root calls while holding the ordinary shared slot; stores with put_new().
    """
    need(type(databases) is dict and type(technical_log_cursor) is dict,
         'ASSEMBLY_ROOT_METADATA_BASIS_REQUIRED')
    profile = checker.H/'profiles/telegram-bot-8812646969'
    roots = [checker.H/n for n in ('logs','sessions','memories','user-artifacts')]
    roots += [profile/n for n in ('logs','sessions','memories','workspace','cache','.curator_backups')]
    files = []; visited = 0
    for root in roots:
        canonical_path(root)
        need(not any(q.is_symlink() for q in (root,*root.parents)), 'ASSEMBLY_UNSAFE_CARRIER_ROOT')
        if not root.exists():
            continue
        todo = [root]
        while todo:
            directory = todo.pop()
            before = directory.lstat()
            need(stat.S_ISDIR(before.st_mode) and before.st_uid==os.getuid()
                 and not stat.S_IMODE(before.st_mode)&0o002 and not directory.is_symlink(),
                 'ASSEMBLY_UNSAFE_CARRIER_DIRECTORY')
            with os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    need(visited<=12000,'ASSEMBLY_CARRIER_INVENTORY_TOO_LARGE')
                    f = Path(entry.path); st = entry.stat(follow_symlinks=False)
                    need(st.st_uid==os.getuid() and not stat.S_ISLNK(st.st_mode)
                         and not stat.S_IMODE(st.st_mode)&0o002,'ASSEMBLY_UNSAFE_CARRIER_ENTRY')
                    if stat.S_ISDIR(st.st_mode):
                        todo.append(f)
                    else:
                        need(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'ASSEMBLY_NONREGULAR_CARRIER_ENTRY')
                        files.append(dict(path=str(f),device=st.st_dev,inode=st.st_ino,uid=st.st_uid,gid=st.st_gid,
                            mode=stat.S_IMODE(st.st_mode),nlink=st.st_nlink,bytes=st.st_size,
                            mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns))
            need(identity(before)==identity(directory.lstat()),'ASSEMBLY_CARRIER_DIRECTORY_CHANGED')
    files.sort(key=lambda r:r['path'])
    journal = subprocess.run(['journalctl','--user','-u','hermes-gateway-1b7e7667.service',
        '-n','0','--show-cursor','--no-pager'],check=True,capture_output=True,timeout=10).stdout
    need(type(journal) is bytes and len(journal)<=DEFAULT_LIMIT,'ASSEMBLY_JOURNAL_CURSOR_BOUND')
    cursor = journal.decode('utf-8')
    need(any(line.startswith('-- cursor: ') and line[len('-- cursor: '):] for line in cursor.splitlines()),
         'ASSEMBLY_GENUINE_JOURNAL_CURSOR_REQUIRED')
    need(technical_log_cursor==checker.technical_log_cursor(),'ASSEMBLY_TECHNICAL_CURSOR_CHANGED_DURING_BASELINE')
    return dict(schema='frw.Root.F06.operation-technical-carrier-baseline.v1',operator='Root',
        scope='EXISTING_TEN_ROOTS_AND_GATEWAY_JOURNAL_CURRENT_TWO_SINK_CURSORS_METADATA_ONLY',
        roots=list(map(str,roots)),files=files,db_metadata=clone(databases),journal_cursor=cursor,
        technical_log_cursor=clone(technical_log_cursor),content_read=False,
        verdict='NOT_ESTABLISHED',extra_event_or_replay=False)


def postcondition_plan(c, *, gateway, technical_log_cursor, technical_carrier_baseline):
    """Collection obligation only. Facts are supplied by Root, not observed here."""
    need(reference_shape(technical_carrier_baseline) and type(technical_log_cursor) is dict
         and type(gateway) is dict,'ASSEMBLY_ROOT_BASELINE_REQUIRED')
    return dict(schema='frw.Root.F06.same-upload-correctread-postcondition-plan.v1',
        status='REQUIRED_AFTER_ONE_FUTURE_OPERATION_NOT_ASSESSED',run_id=c['run_id'],phase=c['phase'],
        scenario_sha256=c['scenario_sha256'],source_reference=clone(c['source_reference']),
        installation_closure=clone(c['installation']['closure']),runtime_hashes=clone(c['installation']['runtime_hashes']),
        gateway=clone(gateway),B={k:c['boundary']['B'][k] for k in ('profile','session_id','session_key')},
        technical_log_cursor=clone(technical_log_cursor),technical_carrier_baseline=clone(technical_carrier_baseline),
        actual_full180_reply_capture_required=True,new_technical_carrier_assessment_required=True,
        original_private_request_exemption_only=True,per_site_execution_and_verdict_separate=True,
        missing_site_verdict='NOT_OBSERVED',missing_actual_carriers_acceptance='NOT_ESTABLISHED',
        no_extra_event_or_replay_for_qualification=True,raw_statuses_not_upgraded=True,
        assessment_schema='frw.Root.F06.same-upload-correctread-postcondition-assessment.v1')


def current_template(adapter, checker, c, *, observed=None):
    """Pure existing checker template. No freshness, ownership, clock or grant issued."""
    p = checker.unbound_proof()
    p.update(contract_effect=adapter.effect(c),whole_effect_sha256=digest(adapter.encoded(adapter.effect(c))),
        installation_acceptance=clone(c['installation']['source_acceptance']),
        installation_closure=clone(c['installation']['closure']),
        runtime_privacy_review=clone(c['root_proofs']['private_password_handling']),
        history_semantic_review=clone(c['root_proofs']['all_profile_history_semantic_once']))
    if observed is not None:
        need(type(observed) is dict and observed.get('f06_mutable_boundary')==c['boundary'],
             'ASSEMBLY_ACTUAL_BOUNDARY_MISMATCH')
        p.update(status='ROOT_PREPARED_ONE_FUTURE_OPERATION',observed=clone(observed))
    return p


def bind_observed_fields(c, *, observed):
    """Pure fact copying, not a semantic verdict. Root replaces related proof files."""
    out = clone(c)
    need(observed.get('installed_product')==out['product']
         and observed.get('runtime_hashes')==out['installation']['runtime_hashes'],
         'ASSEMBLY_OBSERVED_INSTALLATION_CHANGED')
    out['boundary'] = clone(observed['f06_mutable_boundary'])
    return out


def selected_private_roots(c, *, proof_path, first, driver_inputs_path, workdir,
                           independent_review, extra_private_refs=(), extra_roots=()):
    """Exact required preparation coverage, including this helper/input/review dirs.
    Deliberately does not recursively label every historical/H/STATE reference private.
    Root supplies actual effective roots separately and calls checker.disjoint().
    """
    refs = [c[k] for k in ('scenario_ref','source','first_ingress','first_validator')]
    refs += list(c['root_proofs'].values())
    refs += [c['resources'][k] for k in ('clock','owned_parent_wait_cleanup')]
    refs += [c['installation'][k] for k in ('closure','source_acceptance')]
    refs += [first['private_custody'],FREEZE,independent_review,*extra_private_refs]
    need(all(reference_shape(r) for r in refs),'ASSEMBLY_PRIVATE_ROOT_REFERENCE_UNBOUND')
    roots = {str(SOURCE),str(PACKAGE),str(canonical_path(proof_path).parent),
             str(canonical_path(driver_inputs_path).parent),str(canonical_path(workdir))}
    roots.update(str(canonical_path(r['path']).parent) for r in refs)
    roots.update(str(canonical_path(root)) for root in extra_roots)
    return sorted(roots)


def assemble_driver_inputs(adapter, driver, c, *, independent_review, review_document, workdir, slot_identity):
    """Pure final input join; driver remains the sole existing executor.
    This takes Root-prepared refs. It creates no authority/current proof/clock/once.
    Root invokes this only after separate semantic/private-material acceptance.
    """
    source_review_shape(review_document)
    c = adapter.canonical_contract(c)
    adapter.contract_shape(c,bound=False)
    need(c['status']=='UNBOUND_NOT_GRANTED' and c['authority'] is None and c['authority_id']=='UNBOUND',
         'ASSEMBLY_OLD_OR_PREISSUED_AUTHORITY_REFUSED')
    need(reference_shape(independent_review) and c['root_proofs']['source_review']==independent_review,
         'ASSEMBLY_EXACT_SOURCE_REVIEW_JOIN_REQUIRED')
    need(all(reference_shape(c[k]) for k in ('scenario_ref','adapter','footer','actual_root_B_checker',
             'root_current_proof','first_validator','first_ingress'))
         and set(c['root_proofs'])==adapter.PROOFS
         and all(reference_shape(r) for r in c['root_proofs'].values()),'ASSEMBLY_COMPLETE_ROOT_REFS_REQUIRED')
    refs = source_refs()
    need(all(c[field]==refs[leaf] for field,leaf in (('adapter','f06_source.py'),('footer','f06_footer.py.txt'),
             ('actual_root_B_checker','current_root.py'),('first_validator','first_ingress.py'))),
         'ASSEMBLY_COHERENT_LOCAL_SOURCE5_REQUIRED')
    r = c['resources']
    need(type(r) is dict and set(r)==set(TIMING)|set(LIMITS)|{'clock','owned_parent_wait_cleanup'}
         and all(type(r[k]) is int and r[k]==v for k,v in {**TIMING,**LIMITS}.items())
         and all(reference_shape(r[k]) for k in ('clock','owned_parent_wait_cleanup')),
         'ASSEMBLY_ORIGINAL_FINITE_BUDGET_REQUIRED')
    # Bound contract validator checks all shape before issuance, using a RAM-only
    # authority witness. It is never serialized or treated as an authority/proof.
    witness = clone(c)
    witness.update(status='ROOT_BOUND_EXACT_F06_CORRECTREAD',authority_id='SYNTACTIC_SHAPE_ONLY_NOT_ISSUED',
                   authority=clone(independent_review))
    adapter.contract_shape(witness)
    need(type(slot_identity) is dict and set(slot_identity)=={'device','inode','uid','mode','nlink'}
         and all(type(v) is int and v>=0 for v in slot_identity.values())
         and slot_identity['mode']==0o600 and slot_identity['nlink']==1,'ASSEMBLY_SLOT_METADATA_UNBOUND')
    v = dict(schema='frw.Root.F06.same-upload-correctread-driver.v1',status='ROOT_BOUND_ONE_FUTURE_OPERATION',
        contract=c,source_freeze=clone(FREEZE),independent_review=clone(independent_review),
        workdir=str(canonical_path(workdir)),slot_identity=clone(slot_identity),expected_binding_sha256=None)
    driver.validate_inputs(v)
    return v


def main(argv=None):
    # No default selected-file reads, constructor, issuer, execution or writes.
    need(argv in (None,[]),'ASSEMBLY_NO_EXECUTION_CLI')
    return {'status':'SOURCE_ONLY_INERT_NO_GRANT','executor':str(SOURCE/'root_bind_dispatch_once.py'),
            'next':'Root imports explicit pure constructors; see ROOT-RECIPE.txt'}


if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True))
