#!/usr/bin/env python3
"""Run exactly one finalized task-authorized whole synthetic source gate, once."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import resource
import runpy
import signal
import sys
import time
sys.dont_write_bytecode = True
os.umask(0o077)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gate_common import KINDS, LIMITS, require, verify_recipe, verify_python, json_read
W = Path(__file__).resolve().parent

def write(path, value, exclusive=False):
    with path.open('x' if exclusive else 'w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2); stream.write('\n')
    path.chmod(0o600)

def now(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()

def usage():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'user_cpu_seconds': own.ru_utime, 'system_cpu_seconds': own.ru_stime,
            'maximum_rss_kib': own.ru_maxrss, 'input_blocks': own.ru_inblock, 'output_blocks': own.ru_oublock,
            'children': {'user_cpu_seconds': children.ru_utime, 'system_cpu_seconds': children.ru_stime,
                         'maximum_rss_kib': children.ru_maxrss, 'input_blocks': children.ru_inblock,
                         'output_blocks': children.ru_oublock},
            'combined_cpu_seconds': own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime}

def resources():
    result = {'cpu_count': os.cpu_count(), 'cpu_affinity': sorted(os.sched_getaffinity(0))}
    for name in ('cpu.max', 'memory.max', 'memory.current', 'cpu.pressure', 'io.pressure'):
        path = Path('/sys/fs/cgroup') / name
        try: result[name] = path.read_text().strip()
        except OSError as error: result[name] = {'unavailable': type(error).__name__}
    try: result['meminfo'] = '\n'.join(line for line in Path('/proc/meminfo').read_text().splitlines()
                                       if line.startswith(('MemTotal:', 'MemAvailable:')))
    except OSError as error: result['meminfo'] = {'unavailable': type(error).__name__}
    return result

def own_bytes():
    return sum(p.stat().st_size for p in W.parent.rglob('*') if p.is_file())

def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--recipe-sha256', required=True)
    parser.add_argument('--kind', choices=KINDS, required=True)
    a = parser.parse_args()
    require(__debug__, 'optimized Python prohibited')
    start = time.monotonic()
    def expired(*unused): raise TimeoutError('synthetic_whole_gate_wall_budget_exhausted')
    resource.setrlimit(resource.RLIMIT_CPU, (LIMITS['cpu_seconds'], LIMITS['cpu_seconds']))
    resource.setrlimit(resource.RLIMIT_AS, (LIMITS['address_space_bytes'], LIMITS['address_space_bytes']))
    signal.signal(signal.SIGALRM, expired); signal.setitimer(signal.ITIMER_REAL, LIMITS['wall_seconds'])
    value = verify_recipe(a.recipe, a.recipe_sha256, W)
    verify_python(value)  # Exact PM literal/prefix/ruamel before the consuming marker.
    require(own_bytes() <= LIMITS['maximum_declared_own_total_bytes'], 'own material cap exceeded before intent')
    argv = value['runs'][a.kind]['argv']
    require(Path(argv[0]).resolve() == W / 'controls/check_current_source_edges.py', 'wrong harness')
    runroot = Path(argv[argv.index('--run-root') + 1]).resolve()
    require(runroot == W / 'runs' / a.kind, 'run-root outside exact own kind')
    from source_guard import install_guard
    guard = install_guard(W, runroot)
    os.environ['PATH'] = '/usr/bin:/bin'
    available_cpus = sorted(os.sched_getaffinity(0))
    require(bool(available_cpus), 'no available CPU')
    os.sched_setaffinity(0, available_cpus[:LIMITS['maximum_cpus']])
    lock = (W / '.gate-run.lock').open('a+')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise ValueError('another gate is active; sequential gates required')
    out = W / 'executions'; out.mkdir(mode=0o700, exist_ok=True)
    for previous_kind in KINDS[:KINDS.index(a.kind)]:
        previous = json_read(out / (previous_kind + '.json'))
        require(previous['state'] == 'COMPLETED_SEE_ACTUAL_REPORT'
                and previous['recipe']['sha256'] == a.recipe_sha256,
                'prior sequential gate incomplete or from another recipe')
        previous_report = Path(previous['report']).resolve(strict=True)
        require(previous_report.is_relative_to(W / 'runs' / previous_kind)
                and json_read(previous_report)['state'] == 'PASS', 'prior actual gate did not PASS')
    marker = out / (a.kind + '.json')
    record = {'state': 'STARTED_CONSUMED_DO_NOT_REPLAY', 'kind': a.kind, 'started_moscow': now(),
              'recipe': {'path': str(a.recipe.resolve()), 'sha256': a.recipe_sha256},
              'limits': LIMITS, 'resources_before': resources(), 'usage_before': usage(),
              'authority': value['authority'], 'resource_scope': value['limit_scope'], 'guard': guard, 'pid': os.getpid(), 'python': sys.executable, 'own_bytes_before': own_bytes(), 'own_material_root': str(W.parent)}
    write(marker, record, exclusive=True)
    try:
        for variable, suffix in (('HERMES_HOME', 'bootstrap-home'), ('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'xdg-cache')):
            path = W / 'sandbox' / a.kind / suffix; path.mkdir(mode=0o700, parents=True, exist_ok=True); os.environ[variable] = str(path)
        os.environ['FRW_F06_BOUND_RECIPE'] = str(a.recipe.resolve())
        os.environ['FRW_F06_BOUND_RECIPE_SHA256'] = a.recipe_sha256
        os.environ['FRW_F06_DEADLINE_MONOTONIC'] = str(start + LIMITS['wall_seconds'])
        sys.argv = argv
        runpy.run_path(argv[0], run_name='__main__')
        require(own_bytes() <= LIMITS['maximum_declared_own_total_bytes'], 'own material cap exceeded at terminal result')
        reports = list(runroot.glob('r1-current-*/RESULT.json'))
        require(len(reports) == 1, 'expected one actual final report')
        require(json_read(reports[0])['state'] == 'PASS', 'actual final report is not PASS')
        record['report'] = str(reports[0]); record['state'] = 'COMPLETED_SEE_ACTUAL_REPORT'
    except BaseException as error:
        record['state'] = 'FAILED_OR_INTERRUPTED_CONSUMED_DO_NOT_REPLAY'
        record['exception_class'] = type(error).__name__
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        record.update(completed_moscow=now(), actual_wall_seconds=time.monotonic() - start,
                      usage_after=usage(), resources_after=resources(), own_bytes_after=own_bytes())
        write(marker, record)
        fcntl.flock(lock, fcntl.LOCK_UN); lock.close()

if __name__ == '__main__': main()
