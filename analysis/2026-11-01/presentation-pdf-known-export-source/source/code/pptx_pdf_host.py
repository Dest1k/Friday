#!/usr/bin/env python3
"""B160-compatible sealed host for one PPTX -> PDF export; Root execution only."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import runpy
import selectors
import signal
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parent / 'vendor'
if not VENDOR.exists():
    VENDOR = HERE / 'vendor'
B160 = runpy.run_path(str(VENDOR / 'b160' / 'code' / 'presentation_host.py'))
require = B160['require']
digest = B160['digest']
json_bytes = B160['json_bytes']
START = time.monotonic()
COMPLETE = 'PPTX_PDF_EXPORT_RAW_RUNTIME_OBSERVATIONS_REVIEW_REQUIRED'
EXPORT_CAP = B160['EXPORT_CAP']


class ExportReceiver:
    """The B160 streaming protocol with the finite PDF artifact allowlist."""
    def __init__(self, output):
        self.output, self.buffer, self.files = output, bytearray(), []
        self.current = None
        self.total = 0
        self.trailer = False

    def feed(self, data):
        self.buffer.extend(data)
        while self.buffer:
            if self.trailer:
                require(self.buffer[0] == 10, 'artifact trailer missing')
                del self.buffer[0]
                self.trailer = False
            elif self.current is None:
                where = self.buffer.find(b'\n')
                if where < 0:
                    require(len(self.buffer) <= 4096, 'artifact header too long')
                    break
                require(where <= 4096, 'artifact header too long')
                header = json.loads(bytes(self.buffer[:where]))
                del self.buffer[:where + 1]
                name, size, wanted = header['name'], header['bytes'], header['sha256']
                require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,120}', name), 'unsafe artifact filename')
                allowed = {'ORIGINAL-PPTX-STRUCTURAL.json', 'EXPORTED-PDF-OBSERVATION.json',
                           'DELIVERED-PDF-OBSERVATION.json', 'received-exported.pdf',
                           'EXPORT-SYSCALLS-PRIVATE.log', 'EXPORT-CONSUMER-PRIVATE.log', 'WORKER-RESULT.json'}
                require(name in allowed, 'unexpected artifact name')
                require(name not in {item['name'] for item in self.files}, 'duplicate artifact filename')
                require(isinstance(size, int) and not isinstance(size, bool) and 0 <= size <= EXPORT_CAP, 'invalid artifact size')
                require(isinstance(wanted, str) and re.fullmatch(r'[0-9a-f]{64}', wanted), 'invalid artifact digest')
                require(len(self.files) < 32 and self.total + size <= EXPORT_CAP, 'aggregate artifact export cap')
                fd = os.open(self.output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                self.files.append(header)
                self.total += size
                self.current = [fd, size, hashlib.sha256(), wanted]
                if size == 0:
                    self.finish_file()
            else:
                count = min(len(self.buffer), self.current[1])
                chunk = bytes(self.buffer[:count])
                del self.buffer[:count]
                view = memoryview(chunk)
                while view:
                    view = view[os.write(self.current[0], view):]
                self.current[2].update(chunk)
                self.current[1] -= count
                if self.current[1] == 0:
                    self.finish_file()

    def finish_file(self):
        fd, _, actual, wanted = self.current
        os.fsync(fd)
        os.close(fd)
        self.current = None
        require(actual.hexdigest() == wanted, 'exported artifact digest mismatch')
        self.trailer = True

    def finish(self):
        require(self.current is None and not self.buffer and not self.trailer, 'truncated artifact stream')

    def close(self):
        if self.current is not None:
            os.close(self.current[0])
            self.current = None


def outer(args):
    end = B160['shared_end'](args.deadline_utc)
    require(end - time.monotonic() > B160['CLEANUP_RESERVE'] + 5, 'insufficient shared admission/cleanup budget')
    resource.setrlimit(resource.RLIMIT_AS, (B160['SUPERVISOR_MEMORY'], 1024 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (B160['SUPERVISOR_CPU'], 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (EXPORT_CAP, EXPORT_CAP))
    allowed = sorted(os.sched_getaffinity(0))[:2]
    require(len(allowed) == 2, 'two CPUs unavailable')
    os.sched_setaffinity(0, allowed)
    def forward_alarm(signum, frame):
        raise TimeoutError('supervisor forward wall/CPU budget exhausted')
    signal.signal(signal.SIGXCPU, forward_alarm)
    signal.signal(signal.SIGALRM, forward_alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, end - B160['CLEANUP_RESERVE'] - time.monotonic()))
    output = Path(args.output)
    require(output.is_absolute() and output.parent.resolve() == output.parent, 'output parent must be canonical')
    require(output.parent.stat().st_uid == os.getuid() and stat.S_IMODE(output.parent.stat().st_mode) == 0o700, 'owned0700 output parent required')
    output.mkdir(mode=0o700, exist_ok=False)
    result = {'schema': 'frw.Root.pptx-pdf-export-existing-boundary-host-report.v1', 'state': 'OBSERVER_INCOMPLETE_NOT_PRODUCT_FAIL',
              'visual_acceptance': 'UNACCEPTED_REQUIRES_HUMAN_RENDER_INSPECTION', 'live_product_PASS': False,
              'product_replay': False, 'runtime_qualification': 'UNBOUND_UNTIL_ROOT_EXECUTION',
              'own_processes_zero': True, 'aggregate_cap_bytes': B160['CAP'], 'maximum_wall_seconds': 120,
              'worker_wall_guard_seconds': B160['WORKER_WALL_CAP'], 'aggregate_cpu_cap_seconds': 90,
              'memory_cap_bytes': 1024 * 1024 * 1024, 'export_filter': 'pdf:impress_pdf_Export'}
    fds, process, cgroup, receiver, refs, gate_write = [], None, None, None, [], None
    try:
        vm = runpy.run_path(str(HERE / 'pptx_pdf_boundary.py'))
        binding_data = vm['read_ref']({'path': args.binding, 'sha256': args.binding_sha256}, 65536, private=True)
        binding = json.loads(binding_data)
        suffix = vm['validate'](binding)
        joined = vm['correlate'](binding)
        clock = joined['operation_clock']
        require(clock['boot_id'] == binding['kernel']['boot_id'], 'separate finite Office clock required')
        require(clock['origin_monotonic'] <= time.monotonic() < clock['deadline_monotonic'] - B160['CLEANUP_RESERVE'], 'actual finite Office clock exhausted')
        end = min(end, clock['deadline_monotonic'])
        signal.setitimer(signal.ITIMER_REAL, max(0.001, end - B160['CLEANUP_RESERVE'] - time.monotonic()))
        require(os.uname().release == binding['kernel']['release'], 'actual kernel differs')
        require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == binding['kernel']['boot_id'], 'actual boot differs')
        require(digest(Path(binding['consumer']['executable']['path']).read_bytes()) == binding['consumer']['executable']['sha256'], 'consumer executable differs')
        vm['pinned_read']('/usr/bin/strace', binding['strace']['executable']['sha256'], 4 * 1024 * 1024, owner=0)
        vm['pinned_read'](binding['pdf_reader']['executable']['path'], binding['pdf_reader']['executable']['sha256'], 4 * 1024 * 1024, owner=0)
        reader_raw = vm['read_ref'](binding['pdf_reader']['source'], 1024 * 1024, private=True)
        require(digest(reader_raw) == binding['pdf_reader']['source']['sha256'], 'PDF reader source differs')
        refs = [(args.binding, args.binding_sha256, 65536, True)]
        for name in ('received_artifact', 'delivered_pdf', 'ingress_receipt', 'plan', 'run', 'origin_assessment',
                     'current', 'qualification', 'consumer_qualification', 'operation_clock', 'expectation', 'source_manifest'):
            ref = binding[name]
            cap = 8_000_000 if name == 'delivered_pdf' else 2 * 1024 * 1024
            vm['read_ref'](ref, cap, private=True)
            refs.append((ref['path'], ref['sha256'], cap, True))
        for custody_ref in joined['additional_custody_refs']:
            cap = 8_000_000 if custody_ref['path'].endswith('.pdf') else 2 * 1024 * 1024
            refs.append((custody_ref['path'], custody_ref['sha256'], cap, True))
        data = vm['read_ref'](binding['received_artifact'], 1_000_000, private=True)
        delivered_data = vm['read_ref'](binding['delivered_pdf'], 8_000_000, private=True)
        expectation_data = vm['read_ref'](binding['expectation'], 1_000_000, private=True)
        require(len(data) == binding['received_bytes'] and len(delivered_data) == binding['delivered_pdf_bytes'], 'received length differs')
        args.received_sha256 = binding['received_artifact']['sha256']
        args.delivered_sha256 = binding['delivered_pdf']['sha256']
        args.custody_sha256 = args.binding_sha256
        admitted = [('received.pptx', data), ('delivered.pdf', delivered_data), ('binding.json', binding_data), ('expectation.json', expectation_data)]
        refs.append((binding['received_artifact']['path'], args.received_sha256, 1_000_000, True))
        refs.append((binding['delivered_pdf']['path'], args.delivered_sha256, 8_000_000, True))
        require(sum(len(item[1]) for item in admitted) <= B160['SNAPSHOT_CAP'], 'sealed aggregate snapshot cap')
        for path, expected in {B160['LIBREOFFICE']: B160['WRAPPER_SHA'], **B160['TOOLS']}.items():
            require(digest(Path(path).read_bytes()) == expected, 'helper identity changed: ' + path)
        for name, expected in (('soffice', B160['LAUNCHER_SHA']), ('soffice.bin', B160['BINARY_SHA'])):
            require(digest((Path(B160['TOOLCHAIN']) / 'root/usr/lib/libreoffice/program' / name).read_bytes()) == expected, 'native engine identity changed')
        require(time.monotonic() < end - B160['CLEANUP_RESERVE'] - 3, 'admission consumed shared budget')
        wrapper_data = Path(B160['LIBREOFFICE']).read_bytes()
        binds = []
        for name, payload in admitted:
            fd = B160['sealed_snapshot'](payload)
            fds.append(fd)
            binds += ['--perms', '0400', '--ro-bind-data', str(fd), '/mnt/input/' + name]
        wrapper_fd = B160['sealed_snapshot'](wrapper_data, 0o500)
        fds.append(wrapper_fd)
        tracer_data = vm['pinned_read']('/usr/bin/strace', binding['strace']['executable']['sha256'], 4 * 1024 * 1024, owner=0)
        tracer_fd = B160['sealed_snapshot'](tracer_data, 0o500)
        fds.append(tracer_fd)
        cgroup = B160['Cgroup'](args.cgroup_parent)
        scratch = '/tmp/friday-office-pptx-pdf-' + str(os.getpid())
        worker_end = min(end - B160['CLEANUP_RESERVE'], time.monotonic() + B160['WORKER_WALL_CAP'])
        gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
        fds.append(gate_read)
        etc_binds = []
        for path in ('/etc/fonts', '/etc/ld.so.cache', '/etc/localtime', '/etc/machine-id', '/etc/nsswitch.conf', '/etc/passwd', '/etc/group'):
            if Path(path).exists():
                etc_binds += ['--ro-bind', path, path]
        argv = [B160['BWRAP'], '--unshare-user', '--unshare-all', '--disable-userns', '--die-with-parent', '--new-session', '--ro-bind', '/', '/',
                '--size', str(B160['TMPFS_CAP']), '--tmpfs', '/tmp', '--proc', '/proc', '--remount-ro', '/proc',
                '--dev', '/dev', '--remount-ro', '/dev', '--tmpfs', '/home', '--ro-bind', B160['VENV'], B160['VENV'],
                '--perms', '0500', '--ro-bind-data', str(wrapper_fd), B160['LIBREOFFICE'],
                '--perms', '0500', '--ro-bind-data', str(tracer_fd), '/usr/bin/strace', '--remount-ro', '/home',
                '--tmpfs', '/root', '--remount-ro', '/root', '--tmpfs', '/mnt', '--ro-bind', str(HERE), '/mnt/observer',
                '--ro-bind', str(HERE.parent / 'vendor'), '/mnt/observer/vendor',
                '--ro-bind', str(cgroup.path), '/mnt/observer-cgroup', '--dir', '/mnt/input', *binds, '--remount-ro', '/mnt',
                '--tmpfs', '/media', '--remount-ro', '/media', '--tmpfs', '/srv', '--remount-ro', '/srv',
                '--tmpfs', '/opt', '--ro-bind', B160['TOOLCHAIN'], B160['PRIVATE'],
                '--ro-bind', '/usr/share', B160['PRIVATE'] + '/.host-share', '--ro-bind', B160['TOOLCHAIN'] + '/share-merged', '/usr/share', '--remount-ro', '/opt',
                '--tmpfs', '/etc', *etc_binds, '--remount-ro', '/etc', '--tmpfs', '/var', '--ro-bind-try', '/var/cache/fontconfig', '/var/cache/fontconfig', '--remount-ro', '/var',
                '--tmpfs', '/run', '--remount-ro', '/run', '--chdir', '/tmp', '--clearenv',
                '--setenv', 'HOME', scratch, '--setenv', 'TMPDIR', scratch, '--setenv', 'XDG_CACHE_HOME', scratch + '/cache',
                '--setenv', 'XDG_CONFIG_HOME', scratch + '/config', '--setenv', 'XDG_RUNTIME_DIR', scratch,
                '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'LC_ALL', 'C.UTF-8', '--setenv', 'PATH', '/usr/bin:/bin',
                '--setenv', 'OMP_NUM_THREADS', '1', '--setenv', 'OPENBLAS_NUM_THREADS', '1',
                '--setenv', 'FRW_S12_PARENT_NETNS', os.readlink('/proc/self/ns/net'), '--', B160['PYTHON'], '-I', '-B',
                '/mnt/observer/pptx_pdf_host.py', '--worker', '--worker-end', str(worker_end), '--export-path', str(output),
                '--received-sha256', args.received_sha256, '--delivered-sha256', args.delivered_sha256, '--custody-sha256', args.custody_sha256]
        bootstrap = ('import resource; resource.setrlimit(resource.RLIMIT_CPU,(2,90)); '
                     'import os,sys; gate=int(sys.argv[1]); token=os.read(gate,1); os.close(gate); '
                     'os._exit(124) if token != b"1" else None; os.execv(sys.argv[2],sys.argv[2:])')
        launch = [B160['PYTHON'], '-I', '-B', '-S', '-c', bootstrap, str(gate_read), *argv]
        process = subprocess.Popen(launch, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, pass_fds=fds)
        os.sched_setaffinity(process.pid, allowed)
        (cgroup.path / 'cgroup.procs').write_text(str(process.pid))
        resource.setrlimit(resource.RLIMIT_CPU, (B160['SUPERVISOR_CPU'], 14))
        for fd in fds:
            os.close(fd)
        fds.clear()
        os.write(gate_write, b'1')
        os.close(gate_write)
        gate_write = None
        receiver = ExportReceiver(output)
        selector = selectors.DefaultSelector()
        for stream, kind in ((process.stdout, 'export'), (process.stderr, 'stderr')):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, kind)
        stderr_tail = bytearray()
        try:
            while selector.get_map() or process.poll() is None or cgroup.populated():
                require(time.monotonic() < worker_end, 'shared worker wall guard reached')
                require(cgroup.cpu() < B160['WORKER_CPU_GUARD'], 'aggregate running CPU guard reached')
                for key, _ in selector.select(timeout=min(0.02, max(0, worker_end - time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif key.data == 'export':
                        receiver.feed(chunk)
                    else:
                        stderr_tail.extend(chunk)
                        del stderr_tail[:-4096]
            receiver.finish()
            worker_exit = process.wait(timeout=1)
            result['worker_exit_code'] = worker_exit
            result['worker_stderr_bytes_retained'] = len(stderr_tail)
        finally:
            selector.close()
        for path, expected, limit, private in refs:
            vm['read_ref']({'path': path, 'sha256': expected}, limit, private=private)
        result['original_received_preserved'] = True
        result['delivered_pdf_preserved'] = True
        worker_report = json.loads((output / 'WORKER-RESULT.json').read_text())
        result['worker_report'] = worker_report
        if worker_report['state'] == COMPLETE and worker_exit == 0:
            result['state'] = COMPLETE
    except Exception as exc:
        result['error'] = {'class': type(exc).__name__, 'message': 'PROTECTED_DIAGNOSTIC_REQUIRED'}
    finally:
        signal.signal(signal.SIGALRM, lambda signum, frame: os._exit(124))
        signal.setitimer(signal.ITIMER_REAL, max(0.001, end - time.monotonic()))
        signal.signal(signal.SIGXCPU, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_CPU, (14, 14))
        if gate_write is not None:
            os.close(gate_write)
        for fd in fds:
            os.close(fd)
        if receiver is not None:
            receiver.close()
        cleanup_end = min(end - 1, time.monotonic() + B160['CLEANUP_RESERVE'] - 1)
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if cgroup is not None:
            try:
                result['worker_cpu_seconds'] = round(cgroup.cpu(), 3)
                result['own_processes_zero'] = cgroup.close(cleanup_end)
            except Exception as exc:
                result['own_processes_zero'] = False
                result['cleanup_error'] = {'class': type(exc).__name__, 'message': 'PROTECTED_DIAGNOSTIC_REQUIRED'}
            if not result['own_processes_zero']:
                result['cgroup_retained'] = str(cgroup.path)
                result['state'] = 'STOP_UNCONFIRMED'
        if process is not None:
            try:
                process.wait(timeout=max(0.01, cleanup_end - time.monotonic()))
            except subprocess.TimeoutExpired:
                result['own_processes_zero'] = False
                result['state'] = 'STOP_UNCONFIRMED'
            for stream in (process.stdout, process.stderr):
                stream.close()
        result['consumer_safety'] = 'UNKNOWN'
        result['source_only_acceptance'] = 'INDEPENDENT_ROOT_REVIEW_REQUIRED'
        result['elapsed_seconds_including_cleanup'] = round(time.monotonic() - START, 3)
        result['shared_remaining_seconds_after_cleanup'] = round(end - time.monotonic(), 3)
        result['host_exported_bytes'] = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        try:
            payload = json_bytes(result)
            require(len(payload) <= B160['RESULT_CAP'], 'final report too large')
            fd = os.open(output / 'HOST-OBSERVER-RESULT.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
            print(json.dumps({'state': result['state'], 'result': str(output / 'HOST-OBSERVER-RESULT.json')}))
        except Exception as exc:
            result['state'] = 'OBSERVER_INCOMPLETE_NOT_PRODUCT_FAIL'
            print(json.dumps({'state': result['state'], 'report_write_error': type(exc).__name__, 'own_processes_zero': result['own_processes_zero']}))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if result['state'] == COMPLETE else 2


def worker(args):
    parent_netns = os.environ.get('FRW_S12_PARENT_NETNS')
    require(parent_netns and os.readlink('/proc/self/ns/net') != parent_netns, 'separate network namespace required')
    tmp = os.statvfs('/tmp')
    require(tmp.f_blocks * tmp.f_frsize <= B160['TMPFS_CAP'], 'bounded tmpfs required')
    require(any(line.split()[4] == '/tmp' and ' - tmpfs ' in line for line in Path('/proc/self/mountinfo').read_text().splitlines()), 'actual tmpfs required')
    cg = Path('/mnt/observer-cgroup')
    require(int((cg / 'memory.max').read_text()) == B160['WORKER_MEMORY'] and int((cg / 'memory.swap.max').read_text()) == 0, 'worker memory boundary required')
    require((cg / 'cpu.max').read_text().split() == ['200000', '100000'], 'worker CPU boundary required')
    require(str(os.getpid()) in (cg / 'cgroup.procs').read_text().split(), 'admitted cgroup required')
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (B160['TMPFS_CAP'], B160['TMPFS_CAP']))
    vm = runpy.run_path('/mnt/observer/pptx_pdf_boundary.py')
    binding_data = Path('/mnt/input/binding.json').read_bytes()
    require(digest(binding_data) == args.custody_sha256, 'binding snapshot drift')
    binding = json.loads(binding_data)
    suffix = vm['validate'](binding)
    received = Path('/mnt/input/received.pptx')
    delivered = Path('/mnt/input/delivered.pdf')
    require(digest(received.read_bytes()) == args.received_sha256 and received.stat().st_size == binding['received_bytes'], 'received snapshot drift')
    require(digest(delivered.read_bytes()) == args.delivered_sha256 and delivered.stat().st_size == binding['delivered_pdf_bytes'], 'delivered snapshot drift')
    scratch = Path(os.environ['TMPDIR'])
    scratch.mkdir(mode=0o700)
    end = float(args.worker_end)
    emitted, total = set(), 0
    def emit_data(name, data, diagnostic=False):
        nonlocal total
        require(time.monotonic() < end, 'shared export deadline')
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,120}', name) and name not in emitted and len(emitted) < 32 and total + len(data) <= EXPORT_CAP, 'bounded output protocol')
        sys.stdout.buffer.write(json.dumps({'name': name, 'bytes': len(data), 'sha256': digest(data)}, separators=(',', ':')).encode() + b'\n' + data + b'\n')
        sys.stdout.buffer.flush()
        total += len(data)
        emitted.add(name)
    presentation = runpy.run_path('/mnt/observer/pptx_pdf_worker.py')
    return presentation['run'](args, binding, suffix, received, delivered, scratch, end, emit_data)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    for name in ('worker-end', 'export-path', 'received-sha256', 'delivered-sha256', 'custody-sha256',
                 'binding', 'binding-sha256', 'output', 'deadline-utc', 'cgroup-parent'):
        parser.add_argument('--' + name)
    args = parser.parse_args()
    if args.worker:
        require(all(getattr(args, n) for n in ('worker_end', 'export_path', 'received_sha256', 'delivered_sha256', 'custody_sha256')), 'worker arguments missing')
        return worker(args)
    require(all(getattr(args, n) for n in ('binding', 'binding_sha256', 'output', 'deadline_utc', 'cgroup_parent')), 'Root exact bindings required')
    return outer(args)


if __name__ == '__main__':
    raise SystemExit(main())
