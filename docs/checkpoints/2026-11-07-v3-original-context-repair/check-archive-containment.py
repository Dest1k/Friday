#!/usr/bin/env python3
"""Offline A-13/A-14 observations through the installed archive consumer.

Run with the installed dependency interpreter and -I -B. All authority, state,
archives and outputs are synthetic and disposable. No live configuration is read,
no service/model/transport is contacted, and no checker-owned extractor exists.

This qualifies the native workspace boundary, including cancellation before
publication. It does not qualify gateway ingress/stop propagation, cancellation
inside a running codec child, or missing RAR/LHA/ARJ/7z-hardlink fixtures. Prior
codec-only evidence can be hash-bound and reused with --previous-evidence; those
controls are deliberately not repeated. Historical records are never rewritten.
"""
import argparse
import asyncio
from contextlib import contextmanager
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tarfile
import tempfile
import threading
import time
from types import SimpleNamespace
import zipfile
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]
MSK = ZoneInfo('Europe/Moscow')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(path):
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=digest(data))


def tree(path):
    """Record files, modes and links without following any symlink."""
    result = {}
    for parent, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            item = Path(parent) / name
            info = item.lstat()
            row = dict(mode=stat.S_IMODE(info.st_mode), nlink=info.st_nlink)
            if stat.S_ISLNK(info.st_mode):
                row['link'] = os.readlink(item)
            elif stat.S_ISREG(info.st_mode):
                row.update(bytes=info.st_size, sha256=digest(item.read_bytes()))
            else:
                row['directory'] = stat.S_ISDIR(info.st_mode)
            result[str(item.relative_to(path))] = row
    return result


def private_write(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)


def outside_workspace(bench, workspace):
    prefix = str(workspace.relative_to(bench))
    return {key: value for key, value in tree(bench).items()
            if key != prefix and not key.startswith(prefix + '/')}


class Boundary:
    """Guard known Python-audited effects outside this one owned bench.

    This observer is not an OS sandbox: native syscalls bypass Python auditing.
    Installed descriptor custody and the codec child's own restrictions remain
    the product boundary; before/after observations are reported separately.
    """
    def __init__(self, root, product):
        self.root, self.product = root, product
        self.active = True
        self.denied = []
        self.children = []
        self.network = []
        self.original_open = os.open
        self.open_context = threading.local()

    def descriptor_open(self, path, flags, mode=0o777, *, dir_fd=None):
        # Python's open audit tuple omits dir_fd. Preserve the real syscall and
        # supply its actual descriptor-relative name to the observer, avoiding
        # false claims that a native state lock was opened under the CWD.
        if self.active and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            self.writable(path, dir_fd, follow=True)
        previous = getattr(self.open_context, 'path', None)
        self.open_context.path = self.path(path, dir_fd)
        try:
            return self.original_open(path, flags, mode, dir_fd=dir_fd)
        finally:
            self.open_context.path = previous

    def path(self, value, directory=None):
        if isinstance(value, int):
            return Path(os.readlink('/proc/self/fd/' + str(value))).resolve()
        value = Path(os.fsdecode(value))
        if not value.is_absolute():
            base = Path.cwd() if directory in (None, -1) else Path(os.readlink('/proc/self/fd/' + str(directory)))
            value = base / value
        # Resolve the parent, so creating/unlinking an inert symlink is allowed;
        # opening its target is separately checked using the full resolution.
        return value.parent.resolve() / value.name

    def writable(self, value, directory=None, *, follow=False):
        if isinstance(value, int) and stat.S_ISFIFO(os.fstat(value).st_mode):
            return  # Anonymous subprocess IPC descriptor, no filesystem output.
        path = self.path(value, directory)
        if follow:
            path = path.resolve()
        if path == Path('/dev/null'):
            return
        if not path.is_relative_to(self.root):
            self.denied.append(str(path))
            raise PermissionError('checker_write_outside_disposable_bench')

    def __call__(self, event, args):
        if not self.active:
            return
        if event == 'open' and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            self.writable(getattr(self.open_context, 'path', None) or args[0], follow=True)
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir'):
            self.writable(args[0], args[2] if event == 'os.mkdir' else args[1])
        elif event in ('os.chmod', 'os.utime', 'os.chown'):
            self.writable(args[0], args[2] if event == 'os.chmod' else args[3], follow=True)
        elif event == 'os.truncate':
            self.writable(args[0], follow=True)
        elif event in ('os.rename', 'os.link'):
            self.writable(args[0], args[2]); self.writable(args[1], args[3])
        elif event == 'os.symlink':
            self.writable(args[1], args[2])
        elif event in ('socket.connect', 'socket.getaddrinfo', 'socket.sendto', 'socket.bind', 'urllib.Request'):
            self.network.append(event)
            raise PermissionError('checker_network_forbidden')
        elif event == 'subprocess.Popen':
            executable, argv, cwd, environment = args
            allowed = (len(argv) == 6 and argv[1:3] == ['-I', '-B']
                       and Path(executable).absolute() == Path(sys.executable).absolute()
                       and Path(argv[0]).absolute() == Path(sys.executable).absolute()
                       and Path(argv[3]) == self.product / 'hermes_cli/friday_workspace_7z_codec.py'
                       and argv[4] == '--worker' and str(argv[5]) == str(os.getpid())
                       and cwd == '/' and environment == {'LANG': 'C.UTF-8', 'PATH': '/usr/bin:/bin'})
            if not allowed:
                raise PermissionError('checker_unexpected_subprocess')
            self.children.append(dict(executable=str(executable), argv=argv, cwd=cwd))


def owned_children():
    children = set()
    for task in Path('/proc/self/task').iterdir():
        try:
            children.update(int(value) for value in (task / 'children').read_text().split())
        except FileNotFoundError:
            pass
    return sorted(children)


def zip_bytes(rows):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload, kind in rows:
            member = zipfile.ZipInfo(name)
            member.compress_type = zipfile.ZIP_DEFLATED
            member.create_system = 3
            member.external_attr = ((stat.S_IFLNK if kind == 'symlink' else stat.S_IFREG) | 0o600) << 16
            archive.writestr(member, payload)
    return output.getvalue()


def tar_bytes(rows):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for name, payload, kind in rows:
            member = tarfile.TarInfo(name)
            member.mode = 0o600
            if kind in ('symlink', 'hardlink'):
                member.type = tarfile.SYMTYPE if kind == 'symlink' else tarfile.LNKTYPE
                member.linkname = payload.decode('utf-8')
            else:
                member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload) if kind == 'file' else None)
    return output.getvalue()


@contextmanager
def admitted_scope(scope, source):
    with scope.authority(source._identity.runtime_home), scope.scoped_source(source) as cap:
        yield cap


def prepare_scope(root, scope, access):
    """Use real product preparation, state generation and scope checks."""
    from gateway.session_identity import RoutingIdentity
    from hermes_cli.plugins_state import PluginState
    authorization = root / 'authorization'
    authorization.mkdir(mode=0o700)
    binding = dict(platform='telegram', transport_profile='default',
                   account_id='offline-archive-bot', user_id='offline-archive-user',
                   runtime_profile='offline-archive-user', tools=['read_file', 'write_file'])
    settings = dict(user_isolation=dict(enabled=True, bindings=[binding]),
                    product_access=dict(enabled=True, accounts=[dict(
                        platform='telegram', transport_profile='default',
                        account_id=binding['account_id'], runtime_profiles=[binding['runtime_profile']])]))
    private_write(authorization / 'config.yaml', json.dumps(dict(
        plugins=dict(entries=dict(friday_rework=dict(settings=settings))))).encode())
    principal = tuple(binding[key] for key in ('platform', 'transport_profile', 'account_id', 'user_id'))
    with scope.authority(authorization):
        PluginState('friday_rework').set('product_access.v1', dict(schema='product_access.v1', users={
            access.principal_id(*principal): dict(zip(
                ('platform', 'transport_profile', 'account_id', 'user_id'), principal)) | dict(enabled=True, role='user')}))
    home = scope.provision_new_home(authorization, binding, {})
    source = SimpleNamespace(platform=SimpleNamespace(value='telegram'), user_id=binding['user_id'],
                             profile=binding['runtime_profile'], _identity=RoutingIdentity(
                                 'default', binding['runtime_profile'], authorization, home))
    scope.admit_source(source)
    with admitted_scope(scope, source) as cap:
        cap.check()
    return source


def check_case(label, source, payload, suffix, output_format, expected, modules, *, customize=None):
    scope, file_tools = modules
    from agent.web_call_context import WebTurn, WebCall, bind_web_call
    workspace = source._identity.runtime_home / 'workspace'
    name = label + suffix
    private_write(workspace / name, payload)
    destination = label + '-output'
    content = dict(source=name)
    path = destination
    if customize:
        path, content = customize(workspace, destination, content)
    before = tree(workspace)
    bench = source._identity.authorization_home.parent
    outside_before = outside_workspace(bench, workspace)
    reached = set()
    def profile(frame, event, arg):
        if event == 'call' and frame.f_code.co_filename.endswith((
                '/hermes_cli/friday_workspace_zip.py', '/hermes_cli/friday_user_scope.py')):
            reached.add(frame.f_code.co_name)
    call = WebCall(WebTurn(), time.monotonic() + 30, 'offline-' + label, 'offline-session', label)
    with admitted_scope(scope, source), bind_web_call(call):
        sys.setprofile(profile)
        try:
            raw = file_tools.write_file_tool(path=path, content=json.dumps(content), format=output_format,
                                             task_id='offline-archive-' + label)
        finally:
            sys.setprofile(None)
    result = json.loads(raw)
    after = tree(workspace)
    outside_unchanged = outside_workspace(bench, workspace) == outside_before
    if expected is None:
        passed = result.get('success') is False and after == before
    else:
        output = workspace / destination
        output_tree = tree(output)
        actual = {str(p.relative_to(output)): p.read_bytes() for p in output.rglob('*')
                  if stat.S_ISREG(p.lstat().st_mode) and p.lstat().st_nlink == 1}
        passed = (result.get('success') is True and result.get('verified') is True
                  and actual == expected
                  and all(row.get('directory') is True or ('sha256' in row and row['nlink'] == 1)
                          for row in output_tree.values())
                  and all(stat.S_IMODE(p.stat().st_mode) == (0o700 if p.is_dir() else 0o600)
                          for p in [output, *output.rglob('*')])
                  and all(after.get(key) == value for key, value in before.items()))
    archive_fixture = label.startswith(('zip_', 'tar_', 'seven_'))
    passed = (passed and not any(key.startswith('.friday-zip-') for key in after)
              and outside_unchanged and (not archive_fixture or 'extract_zip' in reached))
    return dict(check=label, format=output_format, fixture_bytes=len(payload), fixture_sha256=digest(payload),
                result=result, workspace_unchanged=after == before,
                bench_outside_workspace_unchanged=outside_unchanged,
                product_scope_functions_reached=sorted(reached),
                no_private_stage=not any(key.startswith('.friday-zip-') for key in after), passed=passed)


async def check_cancellation(source, modules, archive_module):
    """Stop the actual native call after real staging, then await the extractor."""
    scope, file_tools = modules
    from agent.web_call_context import WebTurn, WebCall, bind_web_call
    workspace = source._identity.runtime_home / 'workspace'
    payload = zip_bytes([('first.txt', b'first inert file\n', 'file'),
                         ('nested/second.txt', b'second inert file\n', 'file')])
    private_write(workspace / 'cancel.zip', payload)
    before = tree(workspace)
    ready, release = threading.Event(), threading.Event()
    observed = {}
    source_lines = Path(archive_module.__file__).read_text().splitlines()
    barrier_line = next(number for number, line in enumerate(source_lines, 1)
                        if '_tree_snapshot(tree, rows); os.fsync(tree); verify();' in line)
    call = WebCall(WebTurn(), time.monotonic() + 10, 'offline-cancel', 'offline-session', 'offline-call')

    def trace(frame, event, arg):
        if (event == 'line' and frame.f_code.co_filename == archive_module.__file__
                and frame.f_lineno == barrier_line and not ready.is_set()):
            observed['stage'] = frame.f_locals['stage']
            observed['staged_tree'] = tree(workspace / observed['stage'])
            ready.set()
            if not release.wait(5):
                raise TimeoutError('checker_cancel_barrier_timeout')
        return trace

    def extract():
        sys.settrace(trace)
        try:
            return file_tools.write_file_tool(path='cancel-output', content=json.dumps(dict(source='cancel.zip')),
                                             format='zip_extract', task_id='offline-cancel')
        finally:
            sys.settrace(None)

    with admitted_scope(scope, source), bind_web_call(call):
        task = asyncio.create_task(asyncio.to_thread(extract))
        try:
            reached = await asyncio.to_thread(ready.wait, 4)
            if not reached:
                raise RuntimeError('checker_real_staging_boundary_not_reached')
            observed['destination_absent_at_stop'] = not (workspace / 'cancel-output').exists()
            receipt = call.stop()  # The real native stop latch, not a killed dummy process.
        finally:
            release.set()
        result = json.loads(await asyncio.wait_for(task, 5))
    after = tree(workspace)
    expected_stage = {'first.txt': digest(b'first inert file\n'), 'nested/second.txt': digest(b'second inert file\n')}
    actual_stage = {name: row['sha256'] for name, row in observed['staged_tree'].items() if 'sha256' in row}
    passed = (actual_stage == expected_stage and observed['destination_absent_at_stop']
              and result.get('success') is False and result.get('error') == 'archive_not_extracted'
              and result.get('effect_disposition') == 'none' and after == before
              and not owned_children())
    return dict(check='native_async_workspace_cancel_after_real_staging', passed=passed, result=result,
                native_stop_receipt=receipt, observed=observed, workspace_unchanged=after == before,
                extractor_awaited=True, owned_children_remaining=owned_children(),
                scope_limit='Native async workspace only; gateway stop propagation and in-codec cancellation remain unqualified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-home', type=Path, default=REPO / '.runtime/friday-normal-both-workers-frw032')
    parser.add_argument('--scratch-parent', type=Path, default=Path('/home/jericho/.dsh/tmp'))
    parser.add_argument('--previous-evidence', type=Path)
    parser.add_argument('--seven-fixture', type=Path, help='Optional existing inert R34 fixture, never recreated.')
    args = parser.parse_args()
    started, clock = datetime.now(MSK), time.monotonic()
    product = args.installed_home.resolve() / 'hermes-agent'
    sys.path.insert(0, str(product))
    # Resolve dependencies under the actual serving home before entering the
    # disposable authority. An unset home can select an unrelated global venv.
    os.environ['HERMES_HOME'] = str(args.installed_home.resolve())
    from pm.environments import committed_venv, runtime_facts_path, venv_python
    selected_environment = committed_venv(product)
    selected_python = venv_python(selected_environment) if selected_environment else None
    selection = dict(environment=str(selected_environment), python=str(selected_python),
                     facts=fingerprint(runtime_facts_path(product)))
    if selected_python is None or Path(sys.executable).absolute() != selected_python.absolute():
        print(json.dumps(dict(passed=False, preparation_gap='Use the actual serving-home selected interpreter with -I -B.',
                              interpreter=sys.executable, selection=selection), indent=2))
        return 1
    bench = Path(tempfile.mkdtemp(prefix='sol-v3-archive-consumer-20261110-', dir=args.scratch_parent)).resolve()
    boundary = Boundary(bench, product)
    os.environ['HERMES_HOME'] = str(bench)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.addaudithook(boundary)
    os.open = boundary.descriptor_open
    report = dict(schema='friday.v3.installed-archive-consumer-check.v1',
                  started_at_moscow=started.isoformat(), interpreter=sys.executable,
                  native_dependency_selection=selection,
                  checker=fingerprint(Path(__file__).resolve()), installed_home=str(args.installed_home.resolve()),
                  bench=str(bench), checks=[], network_calls=False, model_calls=False, transport_sends=False,
                  authority_scope='Disposable product-prepared legacy-contract user scope; no ingress, pairing or onboarding qualification.',
                  remaining_gaps=['RAR expanded-boundary genuine fixture', 'LHA expanded-boundary genuine fixture',
                                  'ARJ link genuine fixture', 'LHA hardlink genuine fixture', '7z hardlink genuine fixture',
                                  'Gateway async stop propagation', 'Cancellation while a codec child is executing'])
    try:
        from hermes_cli import friday_user_scope as scope, friday_product_access as access
        from hermes_cli import friday_workspace_zip as archive_module
        from tools import file_tools
        core_paths = [product / relative for relative in (
            'hermes_cli/friday_workspace_zip.py', 'hermes_cli/friday_workspace_7z_codec.py',
            'hermes_cli/friday_user_scope.py', 'hermes_cli/friday_workspace_revision.py',
            'hermes_cli/friday_workspace_docx.py', 'tools/file_tools.py',
            'tools/scoped_tar.py', 'tools/scoped_zip.py', 'agent/web_call_context.py')]
        report['consumer_core_before'] = [fingerprint(path) for path in core_paths]
        from importlib.metadata import version, PackageNotFoundError
        try:
            report['py7zr_version'] = version('py7zr')
        except PackageNotFoundError:
            report['py7zr_version'] = None
        source = prepare_scope(bench, scope, access)
        modules = scope, file_tools
        # The public tool's ordinary error presentation lazily initializes the
        # native profile layout. Perform that real, disposable-only preparation
        # before measuring archive effects; keep its observed delta separate.
        from hermes_cli.config import load_config
        prepared_before = tree(bench / 'authorization')
        with admitted_scope(scope, source):
            load_config()
        prepared_after = tree(bench / 'authorization')
        report['fixture_native_initialization'] = {key: prepared_after[key]
            for key in prepared_after if prepared_before.get(key) != prepared_after[key]}
        sentinel = bench / 'outside.txt'
        private_write(sentinel, b'outside workspace sentinel\n')
        sentinel_before = fingerprint(sentinel)
        authority_before = tree(bench / 'authorization')
        report['fixture_authority'] = dict(profile=source.profile,
            admission_generation=source._friday_user_scope.admission_generation,
            workspace=str(source._identity.runtime_home / 'workspace'))
        if args.previous_evidence:
            old = json.loads(args.previous_evidence.read_text())
            current = fingerprint(product / 'hermes_cli/friday_workspace_7z_codec.py')
            report['prior_codec_evidence'] = dict(evidence=fingerprint(args.previous_evidence),
                codec_unchanged=current['sha256'] == old['installed_codec']['sha256'],
                prior_checks=len(old['controls']), prior_all_passed=all(row['passed'] for row in old['controls']),
                reuse_scope='Codec-only evidence; not promoted to workspace/gateway acceptance.')
            if not report['prior_codec_evidence']['codec_unchanged']:
                raise RuntimeError('checker_prior_codec_evidence_changed')
        regular = [('inside.txt', 'готово\n'.encode(), 'file'), ('nested/note.txt', b'bounded\n', 'file')]
        # Moderate compression keeps the compressed input below one MiB and
        # its ratio below 200; refusal reaches the expanded-byte boundary.
        block = hashlib.shake_256(b'offline archive expanded boundary').digest(16384)
        expanded = (block * (archive_module.MAX_BYTES // len(block) + 1))[:archive_module.MAX_BYTES + 1]
        def run(label, rows, kind='zip', expected=None, customize=None):
            maker, suffix, output = (zip_bytes, '.zip', 'zip_extract') if kind == 'zip' else (tar_bytes, '.tar.gz', 'tar_extract')
            report['checks'].append(check_case(label, source, maker(rows), suffix, output, expected, modules, customize=customize))
        wanted = {name: data for name, data, _ in regular}
        run('zip_regular_publication', regular, expected=wanted)
        run('tar_regular_publication', regular, kind='tar', expected=wanted)
        if args.seven_fixture:
            original = fingerprint(args.seven_fixture)
            if original['sha256'] != '4ffbacf1b16a55a90ed4e92894e851e905fd090d82dbc48a8c773225697335e2':
                raise RuntimeError('checker_known_inert_seven_fixture_required')
            seven_payload = args.seven_fixture.read_bytes()
            if digest(seven_payload) != original['sha256']:
                raise RuntimeError('checker_seven_fixture_changed_before_consumption')
            seven_result = check_case('seven_existing_fixture_consumer', source,
                seven_payload, '.7z', '7z_extract',
                {'inside7.txt': 'готово'.encode()} if report['py7zr_version'] == '1.1.0' else None, modules)
            seven_result['source_custody_unchanged'] = fingerprint(args.seven_fixture) == original
            seven_result['passed'] = seven_result['passed'] and seven_result['source_custody_unchanged']
            if report['py7zr_version'] != '1.1.0':
                seven_result['check'] = 'seven_existing_fixture_dependency_refusal'
                seven_result['qualification'] = 'UNAVAILABLE: selected interpreter lacks reviewed py7zr; safe refusal only.'
                seven_result['operation_established'] = False
                seven_result['passed'] = (seven_result['passed'] and seven_result['result'].get('error') == 'archive_codec_unavailable')
                report['remaining_gaps'].append('7z workspace publication: reviewed py7zr unavailable in selected interpreter')
            report['checks'].append(seven_result)
        else:
            report['remaining_gaps'].append('7z workspace consumer not selected: supply the known inert --seven-fixture')
        for kind in ('zip', 'tar'):
            run(kind + '_expanded_at_limit', [('large.bin', expanded[:-1], 'file')],
                kind=kind, expected={'large.bin': expanded[:-1]})
            run(kind + '_traversal', [('good.txt', b'valid first\n', 'file'), ('../outside.txt', b'bad\n', 'file')], kind=kind)
            run(kind + '_symlink', [('escape.txt', str(sentinel).encode(), 'symlink')], kind=kind)
            run(kind + '_expanded_limit', [('large.bin', expanded, 'file')], kind=kind)
        run('tar_hardlink', [('first.txt', b'plain\n', 'file'), ('linked.txt', b'first.txt', 'hardlink')], kind='tar')
        def existing(workspace, dest, content):
            (workspace / dest).mkdir(mode=0o700)
            private_write(workspace / dest / 'preserved.txt', b'keep existing destination\n')
            return dest, content
        run('existing_destination_preserved', regular, customize=existing)
        def source_link(workspace, dest, content):
            link = workspace / 'source-symlink.zip'; link.symlink_to(workspace / content['source'])
            return dest, dict(source=link.name)
        run('symlink_source_refused', regular, customize=source_link)
        def source_hardlink(workspace, dest, content):
            link = workspace / 'source-hardlink.zip'; os.link(workspace / content['source'], link)
            return dest, dict(source=link.name)
        run('hardlink_source_refused', regular, customize=source_hardlink)
        run('output_outside_workspace_refused', regular,
            customize=lambda workspace, dest, content: (str(bench / dest), content))
        def parent_link(workspace, dest, content):
            (workspace / 'parent-symlink').symlink_to(bench, target_is_directory=True)
            return 'parent-symlink/' + dest, content
        run('symlink_parent_refused', regular, customize=parent_link)
        report['checks'].append(asyncio.run(check_cancellation(source, modules, archive_module)))
        report['outside_sentinel_unchanged'] = fingerprint(sentinel) == sentinel_before
        # Workspace changes are expected; all other prepared authority is fixed.
        authority_after = tree(bench / 'authorization')
        stable = lambda rows: {key: value for key, value in rows.items()
                               if '/workspace/' not in key and not key.endswith('/workspace')}
        report['authority_unchanged_outside_workspace'] = stable(authority_before) == stable(authority_after)
        report['authority_changes_outside_workspace'] = {key: dict(before=stable(authority_before).get(key), after=stable(authority_after).get(key))
            for key in stable(authority_before).keys() | stable(authority_after).keys()
            if stable(authority_before).get(key) != stable(authority_after).get(key)}
        report['consumer_core_after'] = [fingerprint(path) for path in core_paths]
        report['consumer_core_unchanged'] = report['consumer_core_after'] == report['consumer_core_before']
        report['passed'] = (all(row['passed'] for row in report['checks'])
                            and report['outside_sentinel_unchanged'] and report['authority_unchanged_outside_workspace']
                            and report['consumer_core_unchanged'])
    except Exception as exc:
        report['passed'] = False
        report['checker_failure'] = dict(exception=type(exc).__name__, detail=str(exc)[:200])
    finally:
        report['installed_modules'] = [fingerprint(Path(module.__file__))
            for module in list(sys.modules.values()) if getattr(module, '__file__', None)
            and Path(module.__file__).is_relative_to(product)
            and Path(module.__file__).is_file()]
        report['installed_modules'].sort(key=lambda row: row['path'])
        report['codec_child_invocations'] = boundary.children
        report['denied_writes'] = boundary.denied
        report['network_attempts'] = boundary.network
        report['owned_children_remaining'] = owned_children()
        report['passed'] = report.get('passed', False) and not boundary.denied and not boundary.network and not owned_children()
        # A live own child would require diagnosis, never deleting its inputs.
        if not owned_children():
            shutil.rmtree(bench)
        report['scratch_removed'] = not bench.exists()
        os.open = boundary.original_open
        boundary.active = False
        report['completed_at_moscow'] = datetime.now(MSK).isoformat()
        report['elapsed_seconds'] = round(time.monotonic() - clock, 6)
        report['scope_verdict'] = ('Available native workspace checks pass; whole A-13/A-14 remains incomplete.'
                                   if report['passed'] else 'Available gate failed; no whole-case acceptance claimed.')
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report['passed'] and report['scratch_removed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
