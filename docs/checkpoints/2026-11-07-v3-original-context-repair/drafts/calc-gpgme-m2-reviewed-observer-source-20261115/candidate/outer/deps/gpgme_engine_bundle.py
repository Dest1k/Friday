"""Pure strict joins for a separately opted-in GPGME engine-init observer.

No process, ELF execution, discovery, authorization, or runtime claim occurs
here. Root supplies pinned code, exact current inputs and the original clock.
"""
import math
import os
import builtins
import re
import stat
import types
from pathlib import PurePosixPath

SCHEMA = 'frw.calc.gpgme-engine-init-bundle.v2'
MANIFEST = 'frw.calc.gpgme-engine-init-manifest.v2'
EVIDENCE = 'frw.calc.gpgme-engine-init-evidence.v2'
WORK = '/tmp/friday-metric-work'
BUNDLE_PATH = WORK + '/output/observer-gpgme-engine-init-bundle.json'
EVIDENCE_PATH = WORK + '/output/observer-gpgme-engine-init.json'
PAPER_MANIFEST_SHA256 = '92b94f4100609c820f25891e09ec15267802833fb4665c393ff746c4565691d0'
RUNTIME_KEYS = {'operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'paper_manifest_ref',
                'marker_path', 'operation_deadline_monotonic', 'bundle_path', 'evidence_path'}
MODULES = {'validator': 'gpgme_engine_bundle.py', 'collector': 'gpgme_boundary_collector.py',
           'adapter': 'gpgme_engine_gdb.py', 'policy': 'gpgme_engine_policy.py',
           'mapper': 'gpgme_mapped_image.py'}
BRANCHES = ('list_dirs', 'list_components', 'gpg_version', 'gpgsm_version', 'gpgconf_version', 'g13_version')
ROLES = ('gpgconf', 'gpgconf', 'gpg', 'gpgsm', 'gpgconf', 'g13')


class Refused(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refused(code)


def exact(value, keys, code):
    need(type(value) is dict and set(value) == set(keys), code)


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def path(value):
    need(type(value) is str and value.startswith('/') and '\0' not in value
         and '\\' not in value and str(PurePosixPath(value)) == value
         and '..' not in PurePosixPath(value).parts, 'gpgme_canonical_path')
    return value


def ref(value):
    exact(value, ('path', 'sha256'), 'gpgme_file_ref')
    path(value['path'])
    need(sha(value['sha256']), 'gpgme_file_pin')
    return value


def validate_binding(binding):
    exact(binding, ('manifest', *MODULES), 'gpgme_observer_binding_schema')
    for role, value in binding.items():
        ref(value)
        if role in MODULES:
            need(PurePosixPath(value['path']).name == MODULES[role], 'gpgme_fixed_source_role:' + role)
    need(len({value['path'] for value in binding.values()}) == len(binding), 'gpgme_distinct_source_refs')
    return binding


def load_sources(binding, reader):
    """Load only the three fixed, pinned, import-safe metadata source roles.

    Collector's two sibling imports bind to the authenticated source modules;
    ambient sys.path/sys.modules can never substitute their implementations.
    """
    validate_binding(binding)
    modules = {}
    siblings = {'gpgme_engine_policy': 'policy', 'gpgme_mapped_image': 'mapper'}
    standard = {'copy', 'errno', 'fcntl', 'hashlib', 'json', 'math', 'os', 're', 'stat', 'time', 'struct'}
    def pinned_import(name, globals=None, locals=None, fromlist=(), level=0):
        need(level == 0, 'gpgme_source_relative_import_forbidden')
        if name in siblings:
            need(siblings[name] in modules, 'gpgme_source_import_order')
            return modules[siblings[name]]
        need(name in standard, 'gpgme_source_import_not_fixed')
        return builtins.__import__(name, globals, locals, fromlist, level)
    for role in ('policy', 'mapper', 'collector'):
        module = types.ModuleType('frw_pinned_gpgme_' + role)
        module.__file__ = binding[role]['path']
        module.__dict__['__builtins__'] = dict(vars(builtins), __import__=pinned_import)
        exec(compile(reader(binding[role]), module.__file__, 'exec'), module.__dict__)
        modules[role] = module
    return modules


def validate_runtime(runtime, *, manifest_ref=None, paper_runtime=None, prelaunch=False):
    exact(runtime, RUNTIME_KEYS, 'gpgme_runtime_schema')
    need(type(runtime['operation_id']) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}', runtime['operation_id'])
         and type(runtime['nonce']) is str and re.fullmatch('[0-9a-f]{32}', runtime['nonce'])
         and sha(runtime['source_sha256']), 'gpgme_runtime_operation_binding')
    ref(runtime['manifest_ref'])
    ref(runtime['paper_manifest_ref'])
    need(runtime['paper_manifest_ref']['sha256'] == PAPER_MANIFEST_SHA256
         and runtime['marker_path'] == WORK + '/load-dependency.json'
         and runtime['bundle_path'] == BUNDLE_PATH and runtime['evidence_path'] == EVIDENCE_PATH,
         'gpgme_exact_paper_window_and_outputs')
    deadline = runtime['operation_deadline_monotonic']
    need((prelaunch and deadline is None) or (not prelaunch and type(deadline) in (int, float)
         and math.isfinite(deadline) and deadline > 0), 'gpgme_original_absolute_clock')
    if manifest_ref is not None:
        need(runtime['manifest_ref'] == manifest_ref, 'gpgme_runtime_manifest_binding')
    if paper_runtime is not None:
        need(all(runtime[key] == paper_runtime[key] for key in ('operation_id', 'nonce', 'source_sha256',
             'marker_path', 'operation_deadline_monotonic'))
             and runtime['paper_manifest_ref'] == paper_runtime['manifest_ref'], 'gpgme_same_paper_load_window')
    return runtime


def validate_manifest(manifest, policy, collector):
    exact(manifest, ('schema', 'profile', 'collector_pins', 'helpers', 'source_mode'), 'gpgme_manifest_schema')
    need(manifest['schema'] == MANIFEST and manifest['source_mode'] in ('COLD_GPGCONF', 'FALLBACK_OR_CACHED'),
         'gpgme_manifest_version_or_source_mode')
    policy.validate_profile(manifest['profile'])
    collector.validate_pins(manifest['collector_pins'])
    helpers = manifest['helpers']
    need(type(helpers) is dict and set(helpers) <= {'gpgconf', 'gpg', 'gpgsm', 'g13'}
         and (manifest['source_mode'] != 'COLD_GPGCONF' or 'gpgconf' in helpers), 'gpgme_manifest_helper_roles')
    for role, image in helpers.items():
        policy.helper_image(image)
        dependencies = manifest['collector_pins']['dependencies'].get(role)
        need(type(dependencies) is list and any(v['path'] == image['path'] and v['sha256'] == image['sha256']
             and v['host_stamp']['ino'] == image['ino']
             and (v['host_stamp']['dev_major'], v['host_stamp']['dev_minor'])
                 == (os.major(image['dev']), os.minor(image['dev']))
             for v in dependencies), 'gpgme_helper_dependency_identity_join')
    return manifest


def validate_bundle(bundle, manifest, policy, collector):
    exact(bundle, ('schema', 'manifest_ref', 'validator_ref', 'collector_ref', 'adapter_ref', 'policy_ref',
                   'mapper_ref', 'runtime', 'evidence_path'), 'gpgme_bundle_schema')
    need(bundle['schema'] == SCHEMA and bundle['evidence_path'] == EVIDENCE_PATH, 'gpgme_bundle_version_or_output')
    validate_binding({'manifest': bundle['manifest_ref'], **{role: bundle[role + '_ref'] for role in MODULES}})
    validate_manifest(manifest, policy, collector)
    runtime = validate_runtime(bundle['runtime'], manifest_ref=bundle['manifest_ref'])
    op = manifest['collector_pins']['operation']
    need(op is None or op == {'operation_id': runtime['operation_id'], 'nonce': runtime['nonce'],
                              'deadline_monotonic': runtime['operation_deadline_monotonic']},
         'gpgme_collector_original_clock')
    return bundle


def identity(value):
    exact(value, ('pid', 'ppid', 'start_ticks'), 'gpgme_evidence_identity_schema')
    need(all(type(value[k]) is int and value[k] > 0 for k in ('pid', 'start_ticks'))
         and type(value['ppid']) is int and value['ppid'] >= 0, 'gpgme_evidence_identity_values')


def validate_evidence(value, runtime, original, *, manifest):
    validate_runtime(runtime)
    exact(value, ('schema', 'status', 'runtime', 'original', 'reaper', 'invocations', 'first_refusal',
                  'actual_M', 'runtime_attested'), 'gpgme_evidence_schema')
    need(value['schema'] == EVIDENCE and value['status'] == 'CLOSED' and value['runtime'] == runtime
         and value['first_refusal'] is None and value['actual_M'] is None
         and value['runtime_attested'] is False, 'gpgme_evidence_not_closed_or_authority')
    identity(value['original'])
    need(value['original'] == {'pid': original['pid'], 'ppid': original['gdb_pid'], 'start_ticks': original['start_ticks']}
         and (manifest['collector_pins']['original'] is None or value['original'] == manifest['collector_pins']['original']),
         'gpgme_evidence_original_binding')
    identity(value['reaper'])
    need(value['reaper']['pid'] == 1 and value['reaper']['ppid'] == 0
         and value['reaper']['pid'] != value['original']['pid']
         and (manifest['collector_pins']['reaper'] is None or value['reaper'] == manifest['collector_pins']['reaper']),
         'gpgme_evidence_actual_reaper_binding')
    invocations = value['invocations']
    need(type(invocations) is list and len(invocations) <= 6, 'gpgme_evidence_invocation_bound')
    if manifest['source_mode'] == 'COLD_GPGCONF':
        need(len(invocations) >= 2 and [v.get('branch') for v in invocations[:2]] == list(BRANCHES[:2]),
             'gpgme_evidence_discovery_pair')
    reaper_pid = value['reaper']['pid']
    pids, inferiors, previous = {original['pid'], reaper_pid}, {1, 2, 3}, -1
    for invocation in invocations:
        exact(invocation, ('branch', 'role', 'thread', 'children', 'pipe', 'exec_seen', 'entry_seen',
              'parent_read_closed', 'stdout_terminal', 'spawn_returned', 'selected_sha256', 'closure_class',
              'observations'), 'gpgme_evidence_invocation_schema')
        need(invocation['branch'] in BRANCHES, 'gpgme_evidence_unknown_branch')
        ordinal = BRANCHES.index(invocation['branch'])
        role = ROLES[ordinal]
        need(ordinal > previous and invocation['role'] == role and role in manifest['helpers']
             and invocation['selected_sha256'] == manifest['helpers'][role]['sha256'], 'gpgme_evidence_branch_or_helper')
        need(manifest['source_mode'] == 'COLD_GPGCONF' or ordinal >= 2, 'gpgme_evidence_fallback_discovery')
        previous = ordinal
        thread = invocation['thread']
        need(type(thread) is list and len(thread) == 3 and all(type(v) is int for v in thread)
             and thread[0] == original['pid'] and thread[1] > 0 and thread[2] == 0, 'gpgme_evidence_calling_thread')
        need(all(invocation[k] is True for k in ('exec_seen', 'entry_seen', 'parent_read_closed', 'spawn_returned'))
             and invocation['closure_class'] == 'OBSERVED_READ_CLOSE_AND_FINAL_WRITER_EXIT_ABSENCE',
             'gpgme_evidence_invocation_unclosed')
        allowed_terminal = ('OBSERVED_READ_EOF',) if ordinal < 2 else ('OBSERVED_READ_EOF', 'OBSERVED_NEWLINE_THEN_READ_CLOSE')
        need(invocation['stdout_terminal'] in allowed_terminal, 'gpgme_evidence_stdout_terminal')
        pipe = invocation['pipe']
        exact(pipe, ('dev', 'ino', 'type', 'rdev'), 'gpgme_evidence_pipe_schema')
        need(all(type(v) is int and v >= 0 for v in pipe.values()) and pipe['ino'] > 0
             and pipe['type'] == stat.S_IFIFO, 'gpgme_evidence_pipe_identity')
        children = invocation['children']
        need(type(children) is list and len(children) == 2, 'gpgme_evidence_two_children')
        for index, child in enumerate(children):
            exact(child, ('identity', 'birth_identity', 'inferior', 'exit_code', 'absent'), 'gpgme_evidence_child_schema')
            identity(child['identity'])
            identity(child['birth_identity'])
            need(child['identity']['pid'] == child['birth_identity']['pid']
                 and child['identity']['start_ticks'] == child['birth_identity']['start_ticks']
                 and child['identity']['pid'] not in pids and type(child['inferior']) is int
                 and child['inferior'] > 3 and child['inferior'] not in inferiors
                 and type(child['exit_code']) is int and child['exit_code'] == 0 and child['absent'] is True,
                 'gpgme_evidence_child_exit_or_identity')
            expected_parent = original['pid'] if index == 0 else children[0]['identity']['pid']
            need(child['birth_identity']['ppid'] == expected_parent
                 and child['identity']['ppid'] in ({expected_parent} if index == 0 else
                      {expected_parent, reaper_pid}), 'gpgme_evidence_child_ancestry')
            pids.add(child['identity']['pid'])
            inferiors.add(child['inferior'])
        observations = invocation['observations']
        stages = ('arm', 'birth1', 'birth2', 'exec', 'entry', 'spawn_return', 'pipe_terminal', 'exit1', 'exit2', 'close')
        need(type(observations) is list and len(observations) in (10, 11), 'gpgme_evidence_observation_bound')
        for observation in observations:
            exact(observation, ('stage', 'sha256'), 'gpgme_evidence_observation_schema')
            need(observation['stage'] in (*stages, 'reparent') and sha(observation['sha256']), 'gpgme_evidence_observation')
        order = {v['stage']: i for i, v in enumerate(observations)}
        need(len(order) == len(observations) and set(stages) <= set(order), 'gpgme_evidence_observation_stages')
        for before, after in (('arm', 'birth1'), ('birth1', 'birth2'), ('birth2', 'exit1'), ('birth2', 'exec'),
                              ('exec', 'entry'), ('entry', 'pipe_terminal'), ('exit1', 'spawn_return'),
                              ('spawn_return', 'pipe_terminal'), ('entry', 'exit2'), ('pipe_terminal', 'close'),
                              ('exit1', 'close'), ('exit2', 'close')):
            need(order[before] < order[after], 'gpgme_evidence_observation_order')
        reparented = children[1]['identity']['ppid'] != children[1]['birth_identity']['ppid']
        need(('reparent' in order) == reparented, 'gpgme_evidence_reparent_observation')
        if reparented:
            need(order['exit1'] < order['reparent'] < order['exit2'], 'gpgme_evidence_reparent_order')
    return value
