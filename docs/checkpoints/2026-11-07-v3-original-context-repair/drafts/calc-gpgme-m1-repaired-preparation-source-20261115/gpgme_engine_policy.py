"""SOURCE preparation only: finite GpgME2.0.1 engine-init metadata protocol.

No GDB, procfs, subprocess, writes, imports of candidate ELF, or permission.
The future adapter must establish each supplied observation independently.
This module intentionally has no runtime create()/admit()/continue() entry.
Do not import it as a replacement for unchanged paper_helper_policy.
"""
import copy
import hashlib
import math
import re
import stat

SCHEMA = 'frw.calc.gpgme-engine-init-source-profile.v1'
STAGE = 'SOURCE_PREPARATION_ONLY'
LIBRARY_SHA256 = 'caece624998149737441172de399b6927b93b303e55fdd0123ae20904df1234b'
BUILD_ID = '02f4a817c120c7589db38532c6891df016fcfbdc'
LIBRARY_PATH = '/usr/lib/x86_64-linux-gnu/libgpgme.so.45.0.1'
SOURCE_MANIFEST = {
    'path': '/home/jericho/.cache/FRW-ASTRA-CALC-OFFICE-GPGME-LOAD-DEPENDENCY-SOURCE-20261115/exact-source/MANIFEST.json',
    'sha256': 'f689aa77b13b5fe06565281592c93e425b86eb6306a1ab38253a5d7745ea2e99'}
CONDITIONAL_JOIN = {
    'path': '/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-CLOSED-STACK-CANDIDATE-JOIN-20261115/RESULT.json',
    'sha256': '6749db9ef22376e9effabfa927bb349f00217d80deb513476d50e59c8f9b6f3d'}
BRANCHES = ('list_dirs', 'list_components', 'gpg_version', 'gpgsm_version',
            'gpgconf_version', 'g13_version')
OPTIONS = dict(zip(BRANCHES, ('--list-dirs', '--list-components', '--version',
                            '--version', '--version', '--version')))
ROLES = dict(zip(BRANCHES, ('gpgconf', 'gpgconf', 'gpg', 'gpgsm', 'gpgconf', 'g13')))
VERSIONS = BRANCHES[2:]
FIRST_FORK_RETURN = 0x37785
SECOND_FORK_RETURN = 0x378c5
SPAWN_ENTRY = 0x37620
EXEC_CALL = 0x37aae
UNSUPPORTED = ('ASSUAN', 'UISERVER', 'SPAWN')
ISOLATED = {'HOME': '/tmp/friday-metric-work/tmp', 'TMPDIR': '/tmp/friday-metric-work/tmp',
            'XDG_CONFIG_HOME': '/tmp/friday-metric-work/config',
            'XDG_CACHE_HOME': '/tmp/friday-metric-work/cache',
            'XDG_RUNTIME_DIR': '/tmp/friday-metric-work/runtime',
            'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
OPTIONAL_ISOLATED = {'XDG_DATA_HOME': '/tmp/friday-metric-work/data'}
FORBIDDEN = {'GNUPGHOME', 'GPG_AGENT_INFO', 'GPG_TTY', 'GPGME_DEBUG', 'LD_PRELOAD',
             'LD_AUDIT', 'ENV', 'BASH_ENV', 'GPGCONF', 'GPG', 'GPGSM'}


def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def exact(value, keys, reason):
    need(type(value) is dict and set(value) == set(keys), reason)


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def identity(value):
    exact(value, ('pid', 'ppid', 'start_ticks'), 'gpgme_identity_schema')
    need(all(type(value[k]) is int and value[k] > 0 for k in ('pid', 'start_ticks'))
         and type(value['ppid']) is int and value['ppid'] >= 0, 'gpgme_identity_values')
    return value


def thread_identity(value):
    need(type(value) is list and len(value) == 3
         and all(type(v) is int for v in value)
         and value[0] > 0 and value[1] > 0 and value[2] == 0, 'gpgme_thread_identity_schema')
    return value


def helper_image(value):
    exact(value, ('path', 'sha256', 'dev', 'ino'), 'gpgme_helper_pin_schema')
    path = value['path']
    need(type(path) is str and path.startswith('/') and '\0' not in path and '\\' not in path
         and all(v not in ('', '.', '..') for v in path.split('/')[1:])
         and sha(value['sha256']) and all(type(value[k]) is int and value[k] > 0 for k in ('dev', 'ino')),
         'gpgme_helper_identity_pin')
    return value


def validate_profile(value):
    exact(value, ('schema', 'stage', 'library', 'source_manifest_ref', 'conditional_join_ref',
                  'branches', 'pseudo_protocols', 'budgets', 'runtime_available'), 'gpgme_profile_schema')
    need(value['schema'] == SCHEMA and value['stage'] == STAGE
         and value['runtime_available'] is False, 'gpgme_source_only_profile')
    need(value['library'] == {'path': LIBRARY_PATH, 'sha256': LIBRARY_SHA256,
                             'build_id': BUILD_ID}, 'gpgme_candidate_library_pin')
    for key in ('source_manifest_ref', 'conditional_join_ref'):
        exact(value[key], ('path', 'sha256'), 'gpgme_source_ref_schema')
        need(type(value[key]['path']) is str and value[key]['path'].startswith('/')
             and sha(value[key]['sha256']), 'gpgme_source_ref_pin')
    need(value['source_manifest_ref'] == SOURCE_MANIFEST and value['conditional_join_ref'] == CONDITIONAL_JOIN,
         'gpgme_exact_source_or_conditional_join_pin')
    need(value['branches'] == [{'branch': b, 'role': ROLES[b], 'option': OPTIONS[b]} for b in BRANCHES]
         and value['pseudo_protocols'] == list(UNSUPPORTED), 'gpgme_exact_source_templates')
    need(value['budgets'] == {'wall_seconds': 240, 'cpu_seconds': 120, 'memory_bytes': 2147483648,
                             'deadline_rule': 'SAME_ORIGINAL_ABSOLUTE_OPERATION_DEADLINE_NO_RESET'},
         'gpgme_original_budgets')
    return value


def runtime_phase_gate(profile):
    """Always reject this preparation candidate before target launch/effects."""
    validate_profile(profile)
    raise RuntimeError('gpgme_engine_init_source_preparation_only')


def validate_environment(env, expected):
    need(type(env) is dict and type(expected) is dict and env == expected,
         'gpgme_exact_current_environment_changed')
    need(all(type(k) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', k)
             and type(v) is str and '\0' not in v for k, v in env.items()), 'gpgme_environment_encoding')
    need(all(env.get(k) == v for k, v in ISOLATED.items()) and not (set(env) & FORBIDDEN),
         'gpgme_environment_isolation_or_override')
    # An unset XDG_DATA_HOME falls back beneath the already isolated HOME.
    # If explicitly present, require the exact private location, never a prefix.
    need(all(k not in env or env[k] == v for k, v in OPTIONAL_ISOLATED.items()),
         'gpgme_data_home_isolation_or_override')


def fd(value):
    exact(value, ('dev', 'ino', 'type', 'rdev', 'access', 'cloexec'), 'gpgme_fd_schema')
    need(all(type(value[k]) is int and value[k] >= 0 for k in ('dev', 'ino', 'type', 'rdev', 'access'))
         and type(value['cloexec']) is bool, 'gpgme_fd_values')
    return value


def pipe_identity(value, *, access):
    fd(value)
    need(value['type'] == stat.S_IFIFO and value['ino'] > 0 and value['access'] == access,
         'gpgme_stdout_pipe_access')
    return {k: value[k] for k in ('dev', 'ino', 'type', 'rdev')}


def pipe_key(value):
    exact(value, ('dev', 'ino', 'type', 'rdev'), 'gpgme_pipe_identity_schema')
    need(all(type(value[k]) is int and value[k] >= 0 for k in value)
         and value['type'] == stat.S_IFIFO and value['ino'] > 0, 'gpgme_pipe_identity_values')
    return value


def validate_exec_fds(fds, pipe, *, null_rdev):
    need(type(fds) is dict and set(fds) == {0, 1, 2} and all(type(n) is int for n in fds),
         'gpgme_exec_exact_three_fds')
    need(type(null_rdev) is int and null_rdev >= 0, 'gpgme_current_devnull_identity')
    for v in fds.values():
        fd(v)
    for n in (0, 2):
        need(fds[n]['type'] == stat.S_IFCHR and fds[n]['rdev'] == null_rdev
             and fds[n]['access'] == 2 and fds[n]['cloexec'] is False,
             'gpgme_missing_stdio_requires_null_RDWR')
    need(pipe_identity(fds[1], access=1) == pipe and fds[1]['cloexec'] is False,
         'gpgme_exec_stdout_binding')


def transition(fn):
    """Any invalid observation terminally retains the first controlled reason."""
    def guarded(self, *args, **kwargs):
        if self.refusal is not None:
            raise RuntimeError(self.refusal)
        try:
            return fn(self, *args, **kwargs)
        except Exception as exc:
            reason = str(exc) if type(exc) is RuntimeError else type(exc).__name__
            self.refusal = self.refusal or reason
            raise RuntimeError(self.refusal) from None
    return guarded


class EngineInitPreparation:
    """Synthetic metadata checks for the future adapter, never live evidence.

    One initial engine-info traversal. Discovery pair and optional increasing
    engine-version subsequence are bounded to six double-fork invocations.
    Reordered exits are supported; births/exec remain exact and unambiguous.
    Original deadline is supplied once, then checked on every transition.
    """
    def __init__(self, profile, original, operation, environment, *, source_mode, helpers, reaper):
        validate_profile(profile)
        identity(original)
        identity(reaper)
        need(reaper['pid'] != original['pid'], 'gpgme_exact_namespace_reaper_identity')
        exact(operation, ('operation_id', 'nonce', 'deadline_monotonic'), 'gpgme_operation_schema')
        need(type(operation['operation_id']) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}', operation['operation_id'])
             and type(operation['nonce']) is str and re.fullmatch('[0-9a-f]{32}', operation['nonce'])
             and positive(operation['deadline_monotonic']), 'gpgme_operation_binding')
        need(source_mode in ('COLD_GPGCONF', 'FALLBACK_OR_CACHED'), 'gpgme_source_mode_unproved')
        validate_environment(environment, environment)
        need(type(helpers) is dict and set(helpers) <= {'gpgconf', 'gpg', 'gpgsm', 'g13'}, 'gpgme_helper_roles')
        for h in helpers.values():
            helper_image(h)
        self.original, self.op, self.env = copy.deepcopy((original, operation, environment))
        self.helpers = copy.deepcopy(helpers)
        self.reaper = copy.deepcopy(reaper)
        self.mode = source_mode
        self.invocations, self.current = [], None
        self.all_pids, self.all_inferiors = {original['pid'], reaper['pid']}, {1}
        self.refusal, self.closed = None, False
        self.last_ordinal = -1

    def _need(self, ok, reason):
        if self.refusal is not None:
            raise RuntimeError(self.refusal)
        if not ok:
            self.refusal = reason
            raise RuntimeError(reason)

    def _boundary(self, context):
        self._need(self.refusal is None and not self.closed, 'gpgme_already_refused_or_closed')
        expected = {'operation_id', 'nonce', 'deadline_monotonic', 'now', 'original', 'all_stop',
                    'phase', 'records_count', 'metric_active', 'library_current_bound',
                    'environment_current_bound', 'configuration_isolated', 'resource_custody_bound'}
        self._need(type(context) is dict and set(context) == expected, 'gpgme_context_schema')
        identity(context['original'])
        self._need(all(type(context[k]) is type(self.op[k]) and context[k] == self.op[k] for k in self.op)
                   and context['original'] == self.original,
                   'gpgme_context_identity_or_clock_changed')
        self._need(positive(context['now']) and context['now'] < self.op['deadline_monotonic'],
                   'gpgme_original_deadline_expired')
        self._need(context['all_stop'] is True and context['phase'] == 'LOAD_OPEN'
                   and type(context['records_count']) is int and context['records_count'] == 0
                   and context['metric_active'] is False, 'gpgme_outside_idle_load_window')
        self._need(all(context[k] is True for k in ('library_current_bound', 'environment_current_bound',
                   'configuration_isolated', 'resource_custody_bound')), 'gpgme_current_boundary_unproved')

    @transition
    def arm(self, context, branch, thread, command, selected_image, read_fd, write_fd, *, source_route):
        self._boundary(context)
        self._need(self.current is None and branch in BRANCHES and len(self.invocations) < 6,
                   'gpgme_extra_or_nested_invocation')
        ordinal = BRANCHES.index(branch)
        if self.mode == 'COLD_GPGCONF' and len(self.invocations) < 2:
            self._need(branch == BRANCHES[len(self.invocations)], 'gpgme_discovery_pair_order')
        else:
            self._need(branch in VERSIONS and ordinal > self.last_ordinal, 'gpgme_version_branch_order')
        thread_identity(thread)
        self._need(thread[0] == self.original['pid'],
                   'gpgme_calling_thread')
        h = self.helpers.get(ROLES[branch])
        helper_image(selected_image)
        self._need(h is not None and selected_image == h and type(command) is list
                   and all(type(v) is str for v in command) and command == [h['path'], OPTIONS[branch]],
                   'gpgme_selected_executable_or_argv')
        self._need(source_route == branch, 'gpgme_exact_source_branch_unproved')
        p = pipe_identity(read_fd, access=0)
        self._need(pipe_identity(write_fd, access=1) == p, 'gpgme_parent_pipe_pair')
        self.current = dict(branch=branch, role=ROLES[branch], thread=list(thread), children=[],
            pipe=p, exec_seen=False, entry_seen=False, parent_read_closed=False, stdout_terminal=None,
            spawn_returned=False, selected_sha256=h['sha256'], helper_identity=copy.deepcopy(h))
        self.last_ordinal = ordinal

    @transition
    def birth(self, context, parent, child, inferior, *, event, return_offset, thread):
        self._boundary(context)
        c = self.current
        self._need(c is not None and len(c['children']) < 2 and event == 'fork', 'gpgme_unknown_birth')
        n = len(c['children'])
        identity(child)
        expected_parent = self.original if n == 0 else c['children'][0]['identity']
        identity(parent)
        thread_identity(thread)
        self._need(n == 0 or (c['children'][0]['exit_code'] is None and c['children'][0]['absent'] is False),
                   'gpgme_second_fork_after_parent_exit')
        self._need(parent == expected_parent and return_offset == (FIRST_FORK_RETURN, SECOND_FORK_RETURN)[n]
                   and type(return_offset) is int
                   and thread == (c['thread'] if n == 0 else [parent['pid'], parent['pid'], 0]),
                   'gpgme_fork_parent_thread_route')
        self._need(child['ppid'] == parent['pid'] and child['pid'] not in self.all_pids
                   and type(inferior) is int and inferior > 1 and inferior not in self.all_inferiors,
                   'gpgme_descendant_identity_or_inferior')
        self.all_pids.add(child['pid'])
        self.all_inferiors.add(inferior)
        c['children'].append(dict(identity=copy.deepcopy(child), birth_identity=copy.deepcopy(child), inferior=inferior,
                                  exit_code=None, absent=False))

    @transition
    def reparent(self, context, final_identity, *, exact_reaper_identity, old_parent_absent):
        self._boundary(context)
        c = self.current
        identity(exact_reaper_identity)
        self._need(c is not None and len(c['children']) == 2 and c['children'][0]['exit_code'] == 0
                   and old_parent_absent is True and exact_reaper_identity == self.reaper,
                   'gpgme_reparent_without_observed_parent_exit_or_reaper')
        identity(final_identity)
        final = c['children'][1]
        self._need(final['exit_code'] is None and final['identity'] == final['birth_identity']
                   and all(final_identity[k] == final['birth_identity'][k] for k in ('pid', 'start_ticks'))
                   and final_identity['ppid'] == self.reaper['pid'], 'gpgme_reparent_birth_or_parent_changed')
        final['identity'] = copy.deepcopy(final_identity)

    @transition
    def exec_before_execution(self, context, child, image, command, fds, env, *, null_rdev, event):
        self._boundary(context)
        c = self.current
        self._need(c is not None and len(c['children']) == 2 and not c['exec_seen']
                   and event == 'exec_before_first_instruction', 'gpgme_exec_order_or_boundary')
        identity(child)
        helper_image(image)
        self._need(child == c['children'][1]['identity'] and image == c['helper_identity']
                   and type(command) is list and all(type(v) is str for v in command)
                   and command == [image['path'], OPTIONS[c['branch']]], 'gpgme_exec_identity_argv')
        validate_environment(env, self.env)
        validate_exec_fds(fds, c['pipe'], null_rdev=null_rdev)
        c['exec_seen'] = True

    @transition
    def entry(self, context, child, *, image_and_exact_dependency_set_bound):
        self._boundary(context)
        c = self.current
        identity(child)
        self._need(c is not None and c['exec_seen'] and not c['entry_seen']
                   and child == c['children'][1]['identity']
                   and image_and_exact_dependency_set_bound is True, 'gpgme_entry_binding')
        c['entry_seen'] = True

    @transition
    def spawn_return(self, context, thread, status):
        self._boundary(context)
        thread_identity(thread)
        c = self.current
        self._need(c is not None and len(c['children']) == 2 and thread == c['thread']
                   and not c['spawn_returned'] and type(status) is int and status == 0,
                   'gpgme_spawn_return_binding')
        self._need(c['children'][0]['exit_code'] == 0, 'gpgme_intermediate_exit_not_observed')
        c['spawn_returned'] = True

    @transition
    def pipe_terminal(self, context, thread, pipe, *, read_closed, terminal):
        self._boundary(context)
        thread_identity(thread)
        pipe_key(pipe)
        c = self.current
        self._need(c is not None and c['entry_seen'] and c['spawn_returned']
                   and thread == c['thread'] and pipe == c['pipe']
                   and not c['parent_read_closed'] and read_closed is True, 'gpgme_pipe_terminal_binding')
        allowed = ('OBSERVED_READ_EOF', 'OBSERVED_NEWLINE_THEN_READ_CLOSE') if c['branch'] in VERSIONS else ('OBSERVED_READ_EOF',)
        self._need(terminal in allowed, 'gpgme_stdout_not_proved_terminal')
        c['parent_read_closed'], c['stdout_terminal'] = True, terminal

    @transition
    def exit(self, context, identity_value, inferior, code, *, absent):
        self._boundary(context)
        identity(identity_value)
        self._need(type(inferior) is int and inferior > 1, 'gpgme_exit_inferior_schema')
        c = self.current
        matches = [] if c is None else [v for v in c['children']
            if v['identity'] == identity_value and v['inferior'] == inferior]
        self._need(len(matches) == 1 and matches[0]['exit_code'] is None and type(code) is int
                   and code == 0 and absent is True, 'gpgme_exit_not_zero_observed_absent')
        self._need(matches[0] is c['children'][0] or c['entry_seen'], 'gpgme_final_exit_before_entry')
        self._need(matches[0] is not c['children'][0] or len(c['children']) == 2,
                   'gpgme_intermediate_exit_before_second_birth')
        matches[0].update(exit_code=code, absent=True)

    @transition
    def close_invocation(self, context, *, no_writer_or_other_descendant, pipe_read_end_absent):
        self._boundary(context)
        c = self.current
        self._need(c is not None and len(c['children']) == 2 and c['exec_seen'] and c['entry_seen']
                   and c['spawn_returned'] and c['parent_read_closed'] and c['stdout_terminal'] is not None
                   and all(v['exit_code'] == 0 and v['absent'] is True for v in c['children'])
                   and no_writer_or_other_descendant is True and pipe_read_end_absent is True,
                   'gpgme_invocation_not_closed')
        # This is writer-absence closure, never an invented read()==0 observation.
        c['closure_class'] = 'OBSERVED_READ_CLOSE_AND_FINAL_WRITER_EXIT_ABSENCE'
        self.invocations.append(c)
        self.current = None

    @transition
    def finish_initialization(self, context, *, exact_engine_info_return, known_no_more_spawn):
        self._boundary(context)
        self._need(self.current is None and exact_engine_info_return is True and known_no_more_spawn is True
                   and (self.mode != 'COLD_GPGCONF' or len(self.invocations) >= 2), 'gpgme_initialization_not_closed')
        self.closed = True

    def snapshot(self):
        # This shape is deliberately incompatible with a production PASS reader.
        invocations = copy.deepcopy(self.invocations)
        for invocation in invocations:
            invocation.pop('helper_identity')  # No raw selected path or argv in output.
        return dict(schema='frw.calc.gpgme-engine-init-preparation-transcript.v1', stage=STAGE,
            runtime_attested=False, runtime_available=False, original=copy.deepcopy(self.original),
            operation=copy.deepcopy(self.op), invocations=invocations,
            active=self.current is not None, source_protocol_closed=self.closed, first_refusal=self.refusal)
