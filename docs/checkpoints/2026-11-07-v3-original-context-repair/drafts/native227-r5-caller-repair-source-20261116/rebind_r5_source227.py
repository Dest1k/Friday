"""Prepare exact R5 SOURCE metadata; Root runs the unchanged constructor next.

Reads only the named static config/acceptance and reviewed Code/review metadata.
It never opens any input envelope, Root8 row, runtime path or referenced payload.
--write exclusively creates two new SOURCE metadata files, never the frame or
authority/current/admission/once/clock/intent. No install or runtime permission.
"""
from pathlib import Path
import argparse
import copy
import datetime
import hashlib
import json
import os
import stat
import sys

sys.dont_write_bytecode = True
B = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE227-ROOT-SOURCE-INTEGRATION-20261116')
R5 = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE227-ROOT-CONSTRUCTOR-SOURCE-20261116/r5')
SOL = Path('/home/jericho/.cache/FRW-SOL-V3-NATIVE227-R5-CALLER-REVIEW-CORE-20261116')
OLD_CONFIG = B/'ROOT227-SOURCE-BINDINGS-FINAL-r4.json'
OLD_CONFIG_SHA = '56960f68c788f511bcedb37c4bb02edb82de041b1d85e0b9a403a71d5982d28e'
OLD_ACCEPTANCE_SHA = '230325991fd8a2f52253f330925b34a934993eb42251fd6ae224b24b1be3ea43'
NEW_CONFIG = B/'ROOT227-SOURCE-BINDINGS-FINAL-r5.json'
NEW_ACCEPTANCE = B/'ROOT-227-SOURCE-DATA-BINDING-ACCEPTANCE-r5.json'
OLD_FRAME = B/'bound-source-frame227-0f098a35-r4'
NEW_FRAME = B/'bound-source-frame227-0f098a35-r5'
CONSTRUCTOR = B/'constructor/construct_frame227.py'
CONSTRUCTOR_SHA = 'a52b20cc2f139519623b805d4c35825ac9197aa8e068d74b6749a5091ce30835'
ENTRY = B/'constructor/assemble_bound_frame227.py'
ENTRY_SHA = '2dedadc72b2fe784cfd98a532b3b4388d0b4ee4193b2c0740042329d9e0057ae'
PRODUCT = '0f098a354033317fe4cf20dd7a225ad5b2442361'
CODE = {
    'actor_static_inputs227.py': dict(path=str(R5/'actor_static_inputs227.py'), bytes=11298,
        sha256='ae3f7ecaa1c8bf40a4dea60ef6885a0059f03e47de09b62146d6aa0022ee69e8'),
    'run_native227_once.py': dict(path=str(R5/'run_native227_once.py'), bytes=74734,
        sha256='0b41f6c9ff8695d0763f618a39cf3db8505ea446114149f03a837b87fd4319fa'),
}
REVIEWS = [
    dict(path=str(R5/'RESULT-r5.json'), sha256='63147e398e453a260c57f7ec5110fd75b478e3c56b8d9c668bd29068f1bc9c09'),
    dict(path=str(SOL/'RESULT.json'), sha256='de7073948ff706a469b52029b61d8129375b832c76bb02d611ae553536578608'),
]
CONFIG_FIELDS = {'acceptance','actual226_binding','additional_source_refs','base_envelopes',
    'budgets','current_admission','execution_grant','fixed','frame','frame_sources','native_after',
    'plan','product_source_commit','provenance','python','schema','source_only'}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(path, raw):
    return dict(path=str(path), sha256=sha(raw), bytes=len(raw))


def clean(ref):
    return {k: ref[k] for k in ('path','sha256')}


def read_pinned(path, expected):
    """Only explicitly named metadata/Code paths; never recursively follow refs."""
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and str(path).startswith('/home/jericho/.cache/'), 'own_cache_Source_path_required')
    require(not any(p.is_symlink() for p in (path,*path.parents)), 'Source_symlink_rejected')
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1 and before.st_size <= 16*1024**2, 'owned_singlelink_bounded_Source_required')
    identity = lambda s: (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        require(identity(before) == identity(os.fstat(stream.fileno())), 'Source_identity_changed_before_read')
        raw = stream.read(16*1024**2+1)
        require(identity(before) == identity(os.fstat(stream.fileno())) == identity(path.lstat()), 'Source_identity_changed_during_read')
    require(len(raw) == before.st_size and sha(raw) == expected, 'explicit_Source_pin_changed')
    return raw


def derive(config, acceptance, *, code_refs, review_refs, old_config_ref, new_acceptance_path, new_frame, at_moscow):
    """Pure metadata transform; payload refs and their complete shape stay opaque."""
    require(type(config) is dict and set(config) == CONFIG_FIELDS, 'exact_old_Source_config_fields_required')
    require(config['schema'] == 'frw.Root227.explicit-source-binding-inputs.v1' and
        config['source_only'] is True and config['current_admission'] is False and config['execution_grant'] is False,
        'Source_only_not_execution_required')
    require(config['frame'] == str(OLD_FRAME) and str(new_frame) == str(NEW_FRAME) and str(new_frame) != config['frame'], 'distinct_exact_r5_frame_required')
    require(config['product_source_commit'] == PRODUCT, 'same_ProductSource227_required')
    require(type(acceptance) is dict and acceptance['schema'] == 'frw.Root227.Source-data-binding-acceptance.v1' and
        acceptance['source_only'] is True and acceptance['current_admission'] is False and acceptance['execution_grant'] is False, 'old_Source_acceptance_required')
    require(config['acceptance']['reference'] == dict(path=str(B/'ROOT-227-SOURCE-DATA-BINDING-ACCEPTANCE.json'), sha256=OLD_ACCEPTANCE_SHA), 'exact_old_Source_acceptance_pin_required')
    for key in ('source_plan_sha256','reviewed_frame_sha256','actual226_binding_sha256','actual226_closure_authentication_reference'):
        require(config['acceptance'][key] == acceptance[key], 'old_acceptance_join_required:'+key)
    require(set(code_refs) == set(CODE) and all(code_refs[k] == CODE[k] for k in CODE), 'only_exact_reviewed_R5_Code_required')
    require(len(review_refs) == 2 and all(clean(r) == p for r,p in zip(review_refs,REVIEWS)), 'exact_author_and_independent_R5_review_required')
    require(set(config['frame_sources']) == set(config['acceptance']['reviewed_frame_sha256']), 'complete_old_reviewed_Source_map_required')
    require(all(config['acceptance']['reviewed_frame_sha256'][n] == r['sha256'] for n,r in config['frame_sources'].items()), 'all_old_Source_refs_reviewed_required')
    require(type(config['additional_source_refs']) is list and len({r['path'] for r in config['additional_source_refs']}) == len(config['additional_source_refs']), 'unique_old_additional_Source_refs_required')
    updated = copy.deepcopy(config)
    accepted = copy.deepcopy(acceptance)
    for name,ref in code_refs.items():
        updated['frame_sources'][name] = copy.deepcopy(ref)
        updated['acceptance']['reviewed_frame_sha256'][name] = ref['sha256']
        accepted['reviewed_frame_sha256'][name] = ref['sha256']
    accepted['at_moscow'] = at_moscow
    accepted['full_new_bound_frame_Source_consumer'] = 'NOT_RUN_AFTER_R5_SOURCE_REBIND'
    accepted['R5_Source_delta'] = dict(
        source_only=True, current_admission=False, execution_grant=False,
        previous_Source_config=copy.deepcopy(old_config_ref), previous_Source_acceptance=copy.deepcopy(config['acceptance']['reference']),
        exact_two_Code_refs=copy.deepcopy(code_refs), author_Source_review=copy.deepcopy(review_refs[0]),
        independent_Source_review=copy.deepcopy(review_refs[1]),
        actual_outer_readonly_consumer='ROOT_REQUIRED_AFTER_CONSTRUCTOR',
        consumed_R4='IMMUTABLE_NOT_RETRIED', future_installation='SEPARATE_ROOT_ELIGIBILITY_NO_GRANT')
    acceptance_raw = encoded(accepted)
    acceptance_ref = reference(new_acceptance_path, acceptance_raw)
    updated['acceptance']['reference'] = clean(acceptance_ref)
    updated['frame'] = str(new_frame)
    extras = {r['path']: copy.deepcopy(r) for r in updated['additional_source_refs']}
    for ref in [acceptance_ref,*code_refs.values(),*review_refs]:
        require(ref['path'] not in extras or extras[ref['path']] == ref, 'new_Source_provenance_ref_conflict')
        extras[ref['path']] = copy.deepcopy(ref)
    updated['additional_source_refs'] = sorted(extras.values(),key=lambda r:r['path'])
    # The complete nearest-caller config remains byte-equivalent by value outside
    # these explicit metadata fields; no 14-field envelope parsing/reassembly.
    changed = {k for k in config if config[k] != updated[k]}
    require(changed == {'acceptance','additional_source_refs','frame','frame_sources'}, 'exact_R5_config_delta_required')
    require({n for n in config['frame_sources'] if config['frame_sources'][n] != updated['frame_sources'][n]} == set(CODE), 'exactly_two_Code_changes_required')
    return updated,accepted


def create(path, raw):
    require(path.parent == B and path in (NEW_CONFIG,NEW_ACCEPTANCE), 'only_two_new_Source_metadata_outputs')
    require(not any(p.is_symlink() for p in (path,*path.parents)), 'output_Source_symlink_rejected')
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Root only: exclusively create new r5 Source config/acceptance; then run printed constructor command')
    args = parser.parse_args()
    os.umask(0o077)
    config_raw = read_pinned(OLD_CONFIG,OLD_CONFIG_SHA)
    config = json.loads(config_raw)
    old_acceptance = config['acceptance']['reference']
    acceptance = json.loads(read_pinned(old_acceptance['path'],OLD_ACCEPTANCE_SHA))
    read_pinned(CONSTRUCTOR,CONSTRUCTOR_SHA);read_pinned(ENTRY,ENTRY_SHA)
    code_refs = {name:reference(ref['path'],read_pinned(ref['path'],ref['sha256'])) for name,ref in CODE.items()}
    reviews = [reference(ref['path'],read_pinned(ref['path'],ref['sha256'])) for ref in REVIEWS]
    stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
    updated,accepted = derive(config,acceptance,code_refs=code_refs,review_refs=reviews,
        old_config_ref=reference(OLD_CONFIG,config_raw),new_acceptance_path=NEW_ACCEPTANCE,new_frame=NEW_FRAME,at_moscow=stamp)
    new_raw,accepted_raw = encoded(updated),encoded(accepted)
    require(not any(os.path.lexists(p) for p in (NEW_CONFIG,NEW_ACCEPTANCE,NEW_FRAME)), 'new_r5_Source_outputs_must_not_exist_no_overwrite')
    if args.write:
        create(NEW_ACCEPTANCE,accepted_raw)
        create(NEW_CONFIG,new_raw)
    print(json.dumps(dict(schema='frw.Root227.r5.source-metadata-rebind.v1',
        state='SOURCE_METADATA_WRITTEN' if args.write else 'VIRTUAL_SOURCE_METADATA_ONLY',
        source_only=True,current_admission=False,execution_grant=False,
        new_config=reference(NEW_CONFIG,new_raw),new_acceptance=reference(NEW_ACCEPTANCE,accepted_raw),new_frame=str(NEW_FRAME),
        actual_data_read=False,frame_written=False,actual_outer_readonly='NOT_RUN_ROOT_REQUIRED',
        Root_next_constructor_argv=['/usr/bin/python3','-I','-B',str(ENTRY),'--root-inputs',str(NEW_CONFIG),'--sha256',sha(new_raw),'--write'],
        Root_next_after_constructor='Invoke SAME new-frame run_native227_once.read_static_source_inputs on complete real H226 with manifest/bound joins; do not call actor main or infer live permission.'),sort_keys=True))


if __name__ == '__main__':
    main()
