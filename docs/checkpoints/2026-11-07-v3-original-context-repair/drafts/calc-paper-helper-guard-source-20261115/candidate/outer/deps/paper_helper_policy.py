"""Finite stock-paper LOAD dependency policy. Pure metadata, no effects/import GDB.

Runtime observations are supplied by the pinned GDB adapter. This policy grants
neither execution nor runtime attestation. Legacy observers never import it.
"""
import copy
import math
import re

SCHEMA = 'frw.calc.paper-helper-manifest.v1'
MARKER = 'frw.calc.load-dependency-window.v1'


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def exact(value, keys, reason):
    require(type(value) is dict and set(value) == set(keys), reason)


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate_manifest(m, *, fixture=False):
    exact(m, ('schema', 'kind', 'source_sha256', 'caller', 'images', 'shell_link',
              'environment', 'absent_paths', 'dash_vfork_return', 'libc_spawn_returns'), 'helper_manifest_schema')
    require(m['schema'] == SCHEMA and m['kind'] ==
            ('OWN_POPEN_FIXTURE_ONLY' if fixture else 'OFFICE_PAPER_LOAD_DEPENDENCY'), 'helper_manifest_kind')
    require(sha(m['source_sha256']), 'helper_source_pin')
    c = m['caller']
    exact(c, ('path', 'sha256', 'function_offset', 'function_size', 'sites'), 'helper_caller_schema')
    require(sha(c['sha256']) and type(c['path']) is str and c['path'].startswith('/'), 'helper_caller_pin')
    require(type(c['function_offset']) is int and c['function_offset'] > 0
            and type(c['function_size']) is int and 0 < c['function_size'] < 8192, 'helper_caller_range')
    exact(c['sites'], ('popen_return', 'fgets_return', 'pclose_return'), 'helper_call_sites')
    for s in c['sites'].values():
        exact(s, ('offset', 'before', 'after'), 'helper_call_site_schema')
        require(type(s['offset']) is int and c['function_offset'] < s['offset'] <
                c['function_offset'] + c['function_size'], 'helper_call_site_range')
        require(type(s['before']) is str and re.fullmatch('e8[0-9a-f]{8}', s['before'])
                and type(s['after']) is str and re.fullmatch('[0-9a-f]{16}', s['after']), 'helper_call_bytes')
    exact(m['images'], ('dash', 'paperconf', 'libc', 'loader', 'libpaper'), 'helper_image_roles')
    for role, image in m['images'].items():
        exact(image, ('path', 'sha256', 'entry', 'entry_bytes'), 'helper_image_schema')
        require(type(image['path']) is str and image['path'].startswith('/') and sha(image['sha256'])
                and type(image['entry']) is int and image['entry'] > 0
                and type(image['entry_bytes']) is str and re.fullmatch('[0-9a-f]{32}', image['entry_bytes']),
                'helper_image_pin')
    require(m['shell_link'] == {'path': '/bin/sh', 'target': 'dash', 'canonical': '/usr/bin/dash'}, 'helper_shell_topology')
    require(m['images']['dash']['path'] == '/usr/bin/dash'
            and m['images']['paperconf']['path'] == '/usr/bin/paperconf', 'helper_exec_paths')
    e = m['environment']
    require(type(e) is dict and e.get('PATH') == '/usr/bin:/bin' and e.get('LANG') == 'C.UTF-8'
            and e.get('LC_ALL') == 'C.UTF-8' and e.get('HOME') == '/tmp/friday-metric-work/tmp'
            and e.get('XDG_CONFIG_HOME') == '/tmp/friday-metric-work/config'
            and all(type(k) is str and type(v) is str for k, v in e.items()), 'helper_environment_contract')
    require(m['absent_paths'] == ['/etc/paperspecs', '/etc/papersize',
            '/tmp/friday-metric-work/config/paperspecs', '/tmp/friday-metric-work/config/papersize',
            '/tmp/friday-metric-work/tmp/.config/paperspecs', '/tmp/friday-metric-work/tmp/.config/papersize'],
            'helper_paper_inputs_contract')
    require(m['dash_vfork_return'] == 0xa680
            and m['libc_spawn_returns'] == [0x8e247, 0x8e586], 'helper_spawn_route_contract')
    return m


def validate_runtime(r, m, *, prelaunch=False):
    exact(r, ('operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'marker_path',
              'operation_deadline_monotonic'), 'helper_runtime_schema')
    require(type(r['operation_id']) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}', r['operation_id'])
            and type(r['nonce']) is str and re.fullmatch('[0-9a-f]{32}', r['nonce']), 'helper_runtime_identity')
    require(r['source_sha256'] == m['source_sha256'] and r['marker_path'] ==
            '/tmp/friday-metric-work/load-dependency.json', 'helper_runtime_source_path')
    exact(r['manifest_ref'], ('path', 'sha256'), 'helper_manifest_ref_schema')
    require(type(r['manifest_ref']['path']) is str and r['manifest_ref']['path'].startswith('/')
            and sha(r['manifest_ref']['sha256']), 'helper_manifest_ref_pin')
    require((prelaunch and r['operation_deadline_monotonic'] is None)
            or finite(r['operation_deadline_monotonic']), 'helper_absolute_operation_deadline')
    return r


def validate_closed(evidence, runtime, original):
    """Independent consumers check terminal facts, never a bare self-logged PASS."""
    exact(evidence, ('schema', 'operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'original',
        'state', 'invocations', 'children', 'execs', 'popen_returned', 'empty_stdout_eof',
        'pclose_status', 'closure_observed_monotonic', 'deadline_monotonic'), 'helper_evidence_schema')
    require(evidence['schema'] == 'frw.calc.paper-helper-custody.v1' and evidence['state'] == 'CLOSED'
            and type(evidence['invocations']) is int and evidence['invocations'] == 1
            and evidence['execs'] == ['dash', 'paperconf']
            and evidence['popen_returned'] is True and evidence['empty_stdout_eof'] is True
            and type(evidence['pclose_status']) is int and evidence['pclose_status'] == 768,
            'helper_custody_not_closed')
    require(all(evidence[k] == runtime[k] for k in ('operation_id', 'nonce', 'source_sha256', 'manifest_ref'))
            and evidence['original'] == original, 'helper_custody_binding')
    require(finite(evidence['closure_observed_monotonic']) and evidence['deadline_monotonic'] ==
            runtime['operation_deadline_monotonic'] and evidence['closure_observed_monotonic'] <
            evidence['deadline_monotonic'], 'helper_custody_clock')
    require(type(evidence['children']) is list and len(evidence['children']) == 2, 'helper_two_children')
    parent = original['pid']
    seen = {parent}
    for inferior, role, c in zip((2, 3), ('dash', 'paperconf'), evidence['children']):
        exact(c, ('role', 'pid', 'ppid', 'start_ticks', 'inferior', 'exit_code', 'entry_verified',
                  'absent_at_close'), 'helper_child_evidence_schema')
        require(c['role'] == role and all(type(c[k]) is int and c[k] > 0 for k in
                ('pid', 'ppid', 'start_ticks', 'inferior')) and c['pid'] not in seen
                and c['ppid'] == parent and c['inferior'] == inferior
                and type(c['exit_code']) is int and c['exit_code'] == 3
                and c['entry_verified'] is True and c['absent_at_close'] is True, 'helper_child_terminal_binding')
        seen.add(c['pid'])
        parent = c['pid']
    return evidence


class Custody:
    """One invocation; actual observations remain the adapter's responsibility."""
    def __init__(self, manifest, runtime, original, *, fixture=False):
        self.m = validate_manifest(manifest, fixture=fixture)
        self.r = validate_runtime(runtime, manifest)
        self.original = copy.deepcopy(original)
        self.thread = None
        self.e = dict(schema='frw.calc.paper-helper-custody.v1',
            **{k: copy.deepcopy(runtime[k]) for k in ('operation_id', 'nonce', 'source_sha256', 'manifest_ref')},
            original=copy.deepcopy(original), state='DISARMED', invocations=0, children=[], execs=[],
            popen_returned=False, empty_stdout_eof=False, pclose_status=None,
            closure_observed_monotonic=None, deadline_monotonic=runtime['operation_deadline_monotonic'])

    def window(self, marker, phase, original, now, records, active):
        require(finite(now) and now < self.r['operation_deadline_monotonic'], 'helper_deadline_expired')
        require(original == self.original and records == [] and active is None, 'helper_original_or_metric_state')
        require(phase == {'nonce': self.r['nonce'], 'phase': 'IDLE', 'index': None, 'digit': None}, 'helper_outside_IDLE')
        exact(marker, ('schema', 'operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'state',
                       'operation_deadline_monotonic'), 'helper_LOAD_marker_schema')
        require(marker['schema'] == MARKER and marker['state'] == 'LOAD_OPEN'
                and all(marker[k] == self.r[k] for k in ('operation_id', 'nonce', 'source_sha256',
                   'manifest_ref', 'operation_deadline_monotonic')), 'helper_LOAD_marker_binding')

    def arm(self, thread, *, exact_entry, exact_caller, command_equal, mode_equal):
        require(self.e['state'] == 'DISARMED' and self.e['invocations'] == 0, 'helper_extra_invocation')
        require(exact_entry is True and exact_caller is True, 'helper_popen_entry_or_caller')
        require(command_equal is True and mode_equal is True, 'helper_command_or_mode')
        require(type(thread) is list and len(thread) == 3 and thread[0] == self.original['pid']
                and type(thread[1]) is int and thread[1] > 0 and thread[2] == 0, 'helper_popen_thread')
        self.thread = list(thread)
        self.e.update(state='ARMED', invocations=1)

    def birth(self, parent, child, *, route_ok):
        n = len(self.e['children'])
        require(n < 2 and self.e['state'] == ('ARMED' if n == 0 else 'DASH_ENTRY'), 'helper_extra_or_out_of_order_birth')
        expected_parent = self.original if n == 0 else self.e['children'][0]
        require(parent == {'pid': expected_parent['pid'], 'start_ticks': expected_parent['start_ticks']}
                and route_ok is True, 'helper_birth_parent_or_route')
        exact(child, ('pid', 'ppid', 'start_ticks'), 'helper_birth_schema')
        require(all(type(v) is int and v > 0 for v in child.values()) and child['ppid'] == parent['pid']
                and child['pid'] not in [self.original['pid']] + [c['pid'] for c in self.e['children']], 'helper_birth_identity')
        self.e['children'].append(dict(role=('dash' if n == 0 else 'paperconf'), **child,
            inferior=None, exit_code=None, entry_verified=False, absent_at_close=False))
        self.e['state'] = 'DASH_BORN' if n == 0 else 'PAPERCONF_BORN'

    def exec(self, role, child, *, exact_image, exact_argv, custody_ok):
        require(role in ('dash', 'paperconf') and len(self.e['execs']) < 2, 'helper_extra_exec')
        index = len(self.e['execs'])
        require(role == ('dash', 'paperconf')[index] and self.e['state'] ==
                ('DASH_BORN', 'PAPERCONF_BORN')[index], 'helper_exec_order')
        expected = self.e['children'][index]
        require(all(child.get(k) == expected[k] for k in ('pid', 'ppid', 'start_ticks'))
                and type(child.get('inferior')) is int and child['inferior'] == index + 2, 'helper_exec_identity')
        require(exact_image is True and exact_argv is True and custody_ok is True, 'helper_exec_image_argv_or_custody')
        expected['inferior'] = child['inferior']
        self.e['execs'].append(role)
        self.e['state'] = role.upper() + '_EXEC'

    def entry(self, role, child, *, images_ok, custody_ok):
        require(self.e['state'] == role.upper() + '_EXEC', 'helper_entry_order')
        expected = self.e['children'][0 if role == 'dash' else 1]
        require(all(child.get(k) == expected[k] for k in ('pid', 'ppid', 'start_ticks', 'inferior'))
                and images_ok is True and custody_ok is True, 'helper_entry_identity_images_or_custody')
        expected['entry_verified'] = True
        self.e['state'] = role.upper() + '_ENTRY'

    def popen_return(self, thread, *, pipe_ok):
        require(self.e['invocations'] == 1 and not self.e['popen_returned'] and thread == self.thread
                and len(self.e['execs']) >= 1 and pipe_ok is True, 'helper_popen_return_binding')
        self.e['popen_returned'] = True

    def eof(self, thread, *, empty_eof):
        require(self.e['popen_returned'] and not self.e['empty_stdout_eof'] and thread == self.thread
                and len(self.e['children']) == 2 and empty_eof is True, 'helper_stdout_not_empty_EOF')
        self.e['empty_stdout_eof'] = True

    def exit(self, inferior, code):
        matches = [c for c in self.e['children'] if c['inferior'] == inferior]
        require(len(matches) == 1 and matches[0]['entry_verified'] and matches[0]['exit_code'] is None
                and type(code) is int and code == 3, 'helper_unexpected_exit')
        if matches[0]['role'] == 'dash':
            require(self.e['children'][1]['exit_code'] == 3, 'helper_exit_order')
        matches[0]['exit_code'] = code

    def close(self, thread, status, now, *, children_absent, original_ok):
        require(self.e['state'] == 'PAPERCONF_ENTRY' and self.e['popen_returned']
                and self.e['empty_stdout_eof'] and thread == self.thread and type(status) is int
                and status == 768 and children_absent is True and original_ok is True, 'helper_pclose_binding')
        require(all(c['exit_code'] == 3 for c in self.e['children']), 'helper_unreaped_children')
        require(finite(now) and now < self.r['operation_deadline_monotonic'], 'helper_deadline_expired')
        for c in self.e['children']:
            c['absent_at_close'] = True
        self.e.update(state='CLOSED', pclose_status=status, closure_observed_monotonic=now)
        validate_closed(self.e, self.r, self.original)

    def metric(self):
        validate_closed(self.e, self.r, self.original)

    def snapshot(self):
        return copy.deepcopy(self.e)
