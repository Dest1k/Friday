"""Pure offline checks; never imports GDB or executes emitted target code."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


p = module('gpgme_source_preparation', ROOT / 'gpgme_engine_policy.py')
m = module('gpgme_current_map_pure_join', ROOT / 'gpgme_mapped_image.py')
profile = json.loads((ROOT / 'GPGME-ENGINE-INIT-SOURCE-PROFILE.json').read_text())
checks = []


def passed(name):
    checks.append(dict(name=name, result='PASS_PURE_OR_STATIC_ONLY'))


def refused(name, fn, reason=None):
    try:
        fn()
    except RuntimeError as exc:
        if reason is not None:
            assert str(exc) == reason, (name, str(exc))
        passed(name)
        return str(exc)
    raise AssertionError(name + '_unexpectedly_accepted')


original = dict(pid=21, ppid=20, start_ticks=100)
operation = dict(operation_id='OWN_SOURCE_PROTOCOL_ONLY', nonce='1' * 32, deadline_monotonic=240.0)
context = dict(operation, now=2.0, original=original, all_stop=True, phase='LOAD_OPEN',
               records_count=0, metric_active=False, library_current_bound=True,
               environment_current_bound=True, configuration_isolated=True, resource_custody_bound=True)
env = dict(p.ISOLATED, XDG_DATA_HOME='/tmp/friday-metric-work/data')
helpers = {name: dict(path='/owned-source-fixture/' + name, sha256=hashlib.sha256(name.encode()).hexdigest(),
                     dev=2050, ino=1000 + i) for i, name in enumerate(('gpgconf', 'gpg', 'gpgsm', 'g13'))}
pipe_read = dict(dev=15, ino=200, type=stat.S_IFIFO, rdev=0, access=0, cloexec=True)
pipe_write = dict(pipe_read, access=1)
null = dict(dev=1, ino=5, type=stat.S_IFCHR, rdev=259, access=2, cloexec=False)
fds = {0: null, 1: dict(pipe_write, cloexec=False), 2: dict(null)}


def machine(mode='COLD_GPGCONF'):
    return p.EngineInitPreparation(profile, original, operation, env, source_mode=mode, helpers=helpers,
                                   reaper=dict(pid=1,ppid=0,start_ticks=10))


def arm(c, branch='list_dirs', **overrides):
    kwargs = dict(context=context, branch=branch, thread=[21, 32, 0],
                  command=[helpers[p.ROLES[branch]]['path'], p.OPTIONS[branch]],
                  selected_image=helpers[p.ROLES[branch]], read_fd=pipe_read, write_fd=pipe_write,
                  source_route=branch)
    kwargs.update(overrides)
    c.arm(**kwargs)


def invocation(c, branch, index, *, final_exit_first=False):
    arm(c, branch)
    intermediate = dict(pid=100 + index * 2, ppid=21, start_ticks=1000 + index * 2)
    final = dict(pid=101 + index * 2, ppid=intermediate['pid'], start_ticks=1001 + index * 2)
    c.birth(context, original, intermediate, 4 + index * 2, event='fork',
            return_offset=p.FIRST_FORK_RETURN, thread=[21, 32, 0])
    c.birth(context, intermediate, final, 5 + index * 2, event='fork',
            return_offset=p.SECOND_FORK_RETURN, thread=[intermediate['pid'], intermediate['pid'], 0])
    c.exec_before_execution(context, final, helpers[p.ROLES[branch]],
        [helpers[p.ROLES[branch]]['path'], p.OPTIONS[branch]], fds, env, null_rdev=259,
        event='exec_before_first_instruction')
    c.entry(context, final, image_and_exact_dependency_set_bound=True)
    if final_exit_first:
        c.exit(context, final, 5 + index * 2, 0, absent=True)
    c.exit(context, intermediate, 4 + index * 2, 0, absent=True)
    c.spawn_return(context, [21, 32, 0], 0)
    terminal = 'OBSERVED_NEWLINE_THEN_READ_CLOSE' if branch in p.VERSIONS else 'OBSERVED_READ_EOF'
    c.pipe_terminal(context, [21, 32, 0], c.current['pipe'], read_closed=True, terminal=terminal)
    if not final_exit_first:
        c.exit(context, final, 5 + index * 2, 0, absent=True)
    c.close_invocation(context, no_writer_or_other_descendant=True, pipe_read_end_absent=True)


p.validate_profile(profile)
passed('exact_profile_all_six_branches_and_three_pseudo_protocols')
refused('changed_source_manifest_pin_refused',lambda:p.validate_profile(dict(profile,
    source_manifest_ref=dict(profile['source_manifest_ref'],sha256='0'*64))))
refused('source_profile_cannot_admit_runtime', lambda: p.runtime_phase_gate(profile),
        'gpgme_engine_init_source_preparation_only')
c = machine()
for i, branch in enumerate(p.BRANCHES):
    invocation(c, branch, i, final_exit_first=i % 2 == 0)
c.finish_initialization(context, exact_engine_info_return=True, known_no_more_spawn=True)
assert c.snapshot()['source_protocol_closed'] is True and c.snapshot()['runtime_attested'] is False
assert 'owned-source-fixture' not in json.dumps(c.snapshot())
passed('cold_discovery_plus_all_four_versions_arbitrary_inferior_ids_and_exit_interleavings')
passed('snapshot_has_no_raw_selected_paths_or_argv')
c = machine('FALLBACK_OR_CACHED')
invocation(c, 'gpg_version', 0)
invocation(c, 'gpgconf_version', 1)
c.finish_initialization(context, exact_engine_info_return=True, known_no_more_spawn=True)
passed('fallback_or_cached_optional_version_subsequence')
c = machine('FALLBACK_OR_CACHED')
c.finish_initialization(context, exact_engine_info_return=True, known_no_more_spawn=True)
passed('no_spawn_requires_explicit_engine_info_return')

for label, changed in (
    ('deadline_changed', dict(context, deadline_monotonic=241.0)),
    ('deadline_expired', dict(context, now=240.0)),
    ('original_birth_changed', dict(context, original=dict(original, start_ticks=101))),
    ('not_all_stop', dict(context, all_stop=False)),
    ('outside_load', dict(context, phase='LOAD_CLOSED')),
    ('metric_already_active', dict(context, metric_active=True)),
    ('metric_records_exist', dict(context, records_count=1)),
    ('mapped_library_unproved', dict(context, library_current_bound=False)),
    ('current_environment_unproved', dict(context, environment_current_bound=False)),
    ('configuration_unproved', dict(context, configuration_isolated=False)),
    ('resources_unproved', dict(context, resource_custody_bound=False))):
    c = machine()
    first = refused(label, lambda: arm(c, context=changed))
    refused(label + '_first_refusal_terminal', lambda: arm(c), first)

for label, overrides in (
    ('wrong_thread', dict(thread=[21, 0, 0])),
    ('float_thread_identity_refused', dict(thread=[21.0, 32, 0])),
    ('wrong_argv', dict(command=[helpers['gpgconf']['path'], '--list-dirs', '--extra'])),
    ('wrong_source_route', dict(source_route='list_components')),
    ('same_basename_different_inode', dict(selected_image=dict(helpers['gpgconf'], ino=99999))),
    ('wrong_pipe_pair', dict(write_fd=dict(pipe_write, ino=999))),
    ('discovery_reordered', dict(branch='list_components'))):
    c = machine()
    first = refused(label, lambda: arm(c, **overrides))
    refused(label + '_first_refusal_terminal', lambda: arm(c), first)

c = machine(); arm(c)
child = dict(pid=100, ppid=21, start_ticks=1000)
refused('vfork_is_not_standard_gpgme_fork', lambda: c.birth(context, original, child, 4,
    event='vfork', return_offset=p.FIRST_FORK_RETURN, thread=[21, 32, 0]))
c = machine(); arm(c)
refused('second_fork_offset_cannot_authorize_first_fork', lambda: c.birth(context, original, child, 4,
    event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[21, 32, 0]))
c = machine(); arm(c)
c.birth(context, original, child, 4, event='fork', return_offset=p.FIRST_FORK_RETURN, thread=[21,32,0])
grandchild = dict(pid=101, ppid=100, start_ticks=1001)
c.birth(context, child, grandchild, 5, event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[100,100,0])
refused('third_fork_refused', lambda: c.birth(context, grandchild, dict(pid=102,ppid=101,start_ticks=1002), 6,
    event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[101,101,0]))
for label, data in (
    ('extra_fd_refused', dict(fds, **{})),
    ('paper_stdin_readonly_not_gpgme_null_RDWR', {**fds, 0: dict(null, access=0)}),
    ('paper_stderr_writeonly_not_gpgme_null_RDWR', {**fds, 2: dict(null, access=1)}),
    ('different_stdout_pipe', {**fds, 1: dict(fds[1], ino=999)})):
    if label == 'extra_fd_refused': data[3] = dict(null)
    refused(label, lambda: p.validate_exec_fds(data, p.pipe_identity(pipe_read, access=0), null_rdev=259))
refused('GNUPGHOME_refused', lambda: p.validate_environment(dict(env, GNUPGHOME='/elsewhere'), dict(env, GNUPGHOME='/elsewhere')))
refused('inherited_environment_changed', lambda: p.validate_environment(dict(env, EXTRA='x'), env))
c = machine(); arm(c)
c.birth(context, original, child, 4, event='fork', return_offset=p.FIRST_FORK_RETURN, thread=[21,32,0])
c.birth(context, child, grandchild, 5, event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[100,100,0])
refused('SIGPIPE_or_nonzero_exit_never_implied_success', lambda: c.exit(context, child, 4, -13, absent=True))
c = machine(); arm(c)
c.birth(context, original, child, 4, event='fork', return_offset=p.FIRST_FORK_RETURN, thread=[21,32,0])
c.birth(context, child, grandchild, 5, event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[100,100,0])
c.exit(context, child, 4, 0, absent=True)
c.spawn_return(context, [21,32,0], 0)
refused('discovery_buffer_full_or_newline_is_not_EOF', lambda: c.pipe_terminal(context,[21,32,0],c.current['pipe'],
    read_closed=True,terminal='OBSERVED_NEWLINE_THEN_READ_CLOSE'))
c = machine(); arm(c)
refused('premature_initialization_close', lambda: c.finish_initialization(context,
    exact_engine_info_return=True, known_no_more_spawn=True))
c = machine(); arm(c)
c.birth(context, original, child, 4, event='fork', return_offset=p.FIRST_FORK_RETURN, thread=[21,32,0])
c.birth(context, child, grandchild, 5, event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[100,100,0])
c.exit(context, child, 4, 0, absent=True)
reparented=dict(grandchild,ppid=1)
c.reparent(context,reparented,exact_reaper_identity=dict(pid=1,ppid=0,start_ticks=10),old_parent_absent=True)
c.exec_before_execution(context,reparented,helpers['gpgconf'],[helpers['gpgconf']['path'],'--list-dirs'],
    fds,env,null_rdev=259,event='exec_before_first_instruction')
c.entry(context,reparented,image_and_exact_dependency_set_bound=True)
c.spawn_return(context,[21,32,0],0)
c.pipe_terminal(context,[21,32,0],c.current['pipe'],read_closed=True,terminal='OBSERVED_READ_EOF')
c.exit(context,reparented,5,0,absent=True)
c.close_invocation(context,no_writer_or_other_descendant=True,pipe_read_end_absent=True)
assert c.invocations[0]['children'][1]['birth_identity']==grandchild
assert c.invocations[0]['children'][1]['identity']==reparented
passed('reparent_only_to_exact_current_reaper_after_observed_intermediate_exit_retains_birth_ancestry')
c = machine(); arm(c)
c.birth(context, original, child, 4, event='fork', return_offset=p.FIRST_FORK_RETURN, thread=[21,32,0])
c.birth(context, child, grandchild, 5, event='fork', return_offset=p.SECOND_FORK_RETURN, thread=[100,100,0])
refused('reparent_without_parent_exit_refused',lambda:c.reparent(context,reparented,
    exact_reaper_identity=dict(pid=1,ppid=0,start_ticks=10),old_parent_absent=True))

# Real immutable candidate bytes, static file read only; maps are synthetic.
raw = Path(profile['library']['path']).read_bytes()
metadata = m.elf_metadata(raw)
assert metadata['sha256'] == p.LIBRARY_SHA256 and metadata['build_id'] == p.BUILD_ID
st = Path(profile['library']['path']).stat()
file_stamp = dict(dev_major=os.major(st.st_dev),dev_minor=os.minor(st.st_dev),ino=st.st_ino,
    size=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,mode=st.st_mode,uid=st.st_uid,nlink=st.st_nlink)
bias = 0x700000000000
maps = []
for segment in metadata['loads']:
    start = bias + (segment['vaddr'] & ~4095)
    length = ((segment['offset'] % 4096 + segment['filesz'] + 4095) & ~4095)
    flags = segment['flags']
    perms = ('r' if flags & 4 else '-') + ('w' if flags & 2 else '-') + ('x' if flags & 1 else '-') + 'p'
    maps.append(f"{start:x}-{start+length:x} {perms} {segment['offset']&~4095:08x} {os.major(st.st_dev):02x}:{os.minor(st.st_dev):02x} {st.st_ino} {profile['library']['path']}\n")
map_bytes = ''.join(maps).encode()
args = [map_bytes,map_bytes,file_stamp,file_stamp,raw,profile['library'],bias+p.FIRST_FORK_RETURN]
joined = m.bind_current_image(*args)
assert joined['relative_pc'] == p.FIRST_FORK_RETURN and joined['load_bias'] == bias
assert joined['runtime_attested'] is False and joined['collector_complete'] is False
passed('real_candidate_static_ELF_plus_synthetic_mapping_join_not_runtime_proof')
for label, index, value in (
    ('maps_CAS_drift',1,map_bytes+b'\n'),
    ('file_CAS_drift',3,dict(file_stamp,ctime_ns=file_stamp['ctime_ns']+1)),
    ('wrong_backing_inode',2,dict(file_stamp,ino=st.st_ino+1)),
    ('wrong_backing_owner',2,dict(file_stamp,uid=1000)),
    ('wrong_ELF_hash',5,dict(profile['library'],sha256='0'*64)),
    ('wrong_ELF_build_id',5,dict(profile['library'],build_id='0'*40)),
    ('basename_alias_not_identity',5,dict(profile['library'],path='/other/libgpgme.so.45.0.1')),
    ('PC_outside_mapping',6,bias+0x999999)):
    altered=list(args);altered[index]=value
    if label in ('wrong_backing_inode','wrong_backing_owner'): altered[3]=value
    refused(label,lambda:m.bind_current_image(*altered))
deleted=map_bytes.replace(profile['library']['path'].encode(),(profile['library']['path']+' (deleted)').encode())
refused('deleted_mapping_refused',lambda:m.bind_current_image(deleted,deleted,*args[2:]))
offset_drift=map_bytes.replace(b'00008000',b'00009000')
if offset_drift==map_bytes: offset_drift=map_bytes.replace(b'00000000',b'00001000',1)
refused('mapping_offset_wrong_PT_LOAD',lambda:m.bind_current_image(offset_drift,offset_drift,*args[2:]))

# Caller delta executes only extracted inert functions with fake metadata state.
native=(ROOT/'candidate/native_return_observer.py').read_text()
tree=ast.parse(native)
functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
stub=type('Stub',(),{})();stub.pending='CONTINUE';stub.pending_stop=('pending',);stub.to_create=[1]
ns=dict(STATE={'error':'first_reason'},pending_action='CONTINUE',helper=stub,save=lambda:None)
exec(compile(ast.Module(body=[functions['fail']],type_ignores=[]),'extracted-fail-only','exec'),ns)
assert ns['fail']('later_reason') is True and ns['STATE']['error']=='first_reason'
assert ns['pending_action'] is None and stub.pending is None and stub.pending_stop is None and stub.to_create==[]
passed('caller_first_refusal_immutable_no_latent_CONTINUE_or_creation')
ns=dict(os=type('EnvStub',(),{'environ':{'FRW_NATIVE_GPGME_ENGINE_INIT_REF':'must_not_be_ignored'}})(),require=p.need)
exec(compile(ast.Module(body=[functions['load_helper']],type_ignores=[]),'extracted-load-guard-only','exec'),ns)
refused('native_explicit_GPG_optin_fails_before_any_read_or_starti',ns['load_helper'],
        'gpgme_engine_init_source_preparation_only')
ns['os'].environ={}
assert ns['load_helper']() is None
passed('legacy_no_optin_no_helper_still_returns_None_without_read_or_GDB')
paper = module('unchanged_paper_policy', ROOT/'candidate/paper_helper_policy.py')
paper_manifest_path=Path('/home/jericho/.cache/FRW-ASTRA-CALC-ACTIVE-PUBLICATION-READER-DELTA-20261115/candidate/outer/deps/PAPER-HELPER-OFFICE-MANIFEST.json')
paper_manifest=json.loads(paper_manifest_path.read_text())
paper.validate_manifest(paper_manifest)
passed('nearest_paper_consumer_accepts_real_unchanged_manifest')
refused('nearest_paper_consumer_refuses_GPG_key_no_silent_widening',lambda:paper.validate_manifest(dict(paper_manifest,gpgme_engine_init=profile)))
for path in ROOT.rglob('*.py'):
    compile(path.read_bytes(),str(path),'exec')
passed('all_candidate_Python_sources_compile_without_importing_GDB_or_launching_target')
print(json.dumps(dict(schema='frw.calc.gpgme-engine-source-pure-checks.v1',
    stage='SOURCE_PREPARATION_ONLY',checks=checks,count=len(checks),
    actual_runtime_proof=False,emitted_target_executed=False),sort_keys=True,indent=2))
