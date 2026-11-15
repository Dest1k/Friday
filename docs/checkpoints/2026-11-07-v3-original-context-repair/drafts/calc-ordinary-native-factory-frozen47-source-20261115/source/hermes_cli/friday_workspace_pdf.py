"""Fixed own-workspace DOCX export; isolated local rendering, create-only PDF.

The renderer sees a private input copy, system fonts and the installed, read-only
LibreOffice toolchain. It never receives a user path, shell command or network.
"""
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from xml.etree import ElementTree as ET
from xml.parsers import expat
from zipfile import ZipFile, BadZipFile
import zlib

MAX_OUTPUT = 1000000
RENDER_SECONDS = 40
_TOOLCHAIN_NAME = 'libreoffice-26.2.5.2-ubuntu26.04-amd64'
_PRESENTATION_TOOLCHAIN_NAME = 'libreofficedev-26.2.5.2-frw-b711-c459-direct-20261111'
_PREFIX = '/opt/friday-document-toolchain'


class ExportRefused(ValueError):
    """Finite public codes, without private filenames or child diagnostics."""


def _source_spec(content, cap):
    from hermes_cli.friday_user_scope import ScopeDenied
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ScopeDenied()
            result[key] = value
        return result
    if not isinstance(content, str) or len(content) > 4096:
        raise ScopeDenied()
    try:
        spec = json.loads(content, object_pairs_hook=pairs)
        if not isinstance(spec, dict) or set(spec) != {'source'}: raise ScopeDenied()
        raw = spec['source']
        if not isinstance(raw, str) or not raw or '\x00' in raw: raise ScopeDenied()
        source = Path(raw)
        root = cap.home/'workspace'
        if not source.is_absolute(): source = root/source
        relative = source.relative_to(root)
        if (not relative.parts or source.suffix.lower() != '.docx'
                or any(p in ('.', '..') or p.startswith('.') for p in relative.parts)):
            raise ScopeDenied()
        return source, relative.as_posix()
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ScopeDenied() from None


def _validate_docx(data):
    from hermes_cli.friday_workspace_docx import _edit_parts, _EditRefused, _edit_xml, _W
    try:
        with ZipFile(BytesIO(data)) as package:
            _, parts = _edit_parts(package)
        for name, raw in parts.items():
            if name.startswith(('word/embeddings/', 'word/activeX/')):
                raise ExportRefused('unsupported_package')
            if name.endswith('.xml'):
                root, _ = _edit_xml(raw)
                # No live fields, imported HTML, controls or executable objects.
                if any(n.tag in {_W+'instrText', _W+'fldSimple', _W+'altChunk', _W+'object', _W+'control'}
                       for n in root.iter()):
                    raise ExportRefused('unsupported_package')
    except (BadZipFile, KeyError, _EditRefused, RuntimeError, ET.ParseError,
            expat.ExpatError, zlib.error, NotImplementedError, OSError):
        raise ExportRefused('unsupported_package') from None


def _toolchain(*, family='default'):
    if type(family) is not str or family not in ('default', 'presentation'):
        raise ExportRefused('renderer_unavailable')
    name = _TOOLCHAIN_NAME if family == 'default' else _PRESENTATION_TOOLCHAIN_NAME
    root = Path(pwd.getpwuid(os.getuid()).pw_dir)/'.jericho/toolchains'/name
    try:
        info = root.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o277 or root.resolve() != root):
            raise ExportRefused('renderer_unavailable')
        if not (root/'root/usr/lib/libreoffice/program/soffice').is_file():
            raise ExportRefused('renderer_unavailable')
        if not (root/'share-merged').is_dir(): raise ExportRefused('renderer_unavailable')
    except OSError:
        raise ExportRefused('renderer_unavailable') from None
    return root


def _argv(work, toolchain):
    argv = ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session',
            '--as-pid-1', '--cap-drop', 'ALL', '--clearenv', '--ro-bind', '/usr', '/usr']
    for alias in ('bin', 'sbin', 'lib', 'lib64'):
        path = Path('/')/alias
        if path.exists():
            target = path.resolve()
            if not target.is_relative_to('/usr'): raise ExportRefused('renderer_unavailable')
            argv += ['--symlink', str(target), str(path)]
    argv += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/opt',
             '--ro-bind', str(toolchain), _PREFIX,
             '--ro-bind', '/usr/share', _PREFIX+'/.host-share',
             '--ro-bind', str(toolchain/'share-merged'), '/usr/share', '--dir', '/etc']
    for path in ('/etc/fonts', '/etc/ld.so.cache', '/var/cache/fontconfig'):
        if Path(path).exists(): argv += ['--ro-bind', path, path]
    argv += ['--bind', str(work), '/work', '--ro-bind', str(work/'input.docx'), '/work/input.docx',
             '--ro-bind', str(work/'renderer.py'), '/renderer.py', '--chdir', '/work',
             '--remount-ro', '/', '--', '/usr/bin/python3', '-I', '-B', '-S',
             '/renderer.py', '--render']
    return argv


class _RenderCustody:
    """Finite child registered in the existing native turn's synchronous stop fence."""
    uses_web = False

    def __init__(self, call):
        self.call, self.process = call, None
        self.lock = threading.RLock()

    def stop(self):
        with self.lock:
            process = self.process
            if process is not None:
                try:
                    # Own new process group; namespace init death reaps all children.
                    if process.poll() is None:
                        try: os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                    process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    return {'status': 'STOP_UNCONFIRMED', 'reason': 'document_renderer_unsettled'}
            return {'status': 'QUIESCENT'}


class _RenderRegistry:
    """Adapt local custody to the existing original-call stop interface."""

    def __init__(self, custody):
        self.custody = custody

    def settle_web(self, session, *, stop):
        if session is not self.custody or stop is not True:
            return {'status': 'STOP_UNCONFIRMED', 'reason': 'document_custody_mismatch'}
        return self.custody.stop()


_RUN_COMPLETION_AUTHORITY = object()


class _RenderReceipt:
    """Internal result of the existing real launch+stop fence, never JSON."""
    __slots__ = ('argv','work','pid','started','finished','deadline','returncode','authority')

    def __init__(self, argv, work, process, started, deadline, authority):
        if authority is not _RUN_COMPLETION_AUTHORITY:
            raise ExportRefused('document_run_receipt_authority')
        self.argv, self.work, self.pid = tuple(argv), Path(work), process.pid
        self.started, self.finished, self.deadline = started, time.monotonic(), deadline
        self.returncode, self.authority = process.returncode, authority


def _run(cap, argv, work):
    from agent.web_call_context import _current, same_web_authority
    from hermes_cli.friday_workspace_revision import check
    call = _current.get()
    if call is None or not same_web_authority(call): raise ExportRefused('native_deadline_required')
    custody = _RenderCustody(call)
    registry = _RenderRegistry(custody)
    bound = False
    prior = None
    deadline = min(call.deadline(), time.monotonic()+RENDER_SECONDS)
    started = time.monotonic()
    try:
        with call.turn.lock:
            check(cap)
            if call.session is not None or call.registry is not None:
                raise ExportRefused('native_custody_busy')
            if time.monotonic() >= deadline: raise TimeoutError()
            prior = call.session, call.registry
            call.session, call.registry = custody, registry
            bound = True
            call.turn.calls.add(custody)
            # Original-call stop, turn stop and launch share the native stop lock.
            custody.process = subprocess.Popen(argv, cwd=work, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                start_new_session=True, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
        while custody.process.poll() is None:
            check(cap)
            if time.monotonic() >= deadline: raise TimeoutError()
            try: custody.process.wait(timeout=min(.05, max(.001, deadline-time.monotonic())))
            except subprocess.TimeoutExpired: pass
        check(cap)
        if custody.process.returncode != 0: raise ExportRefused('renderer_failed')
    finally:
        receipt = custody.stop()
        with call.turn.lock:
            if receipt['status'] == 'QUIESCENT':
                if bound and (call.session is not custody or call.registry is not registry):
                    receipt = {'status': 'STOP_UNCONFIRMED', 'reason': 'document_custody_mismatch'}
                else:
                    if bound:
                        call.session, call.registry = prior
                    call.turn.calls.discard(custody)
        if receipt['status'] != 'QUIESCENT':
            if hasattr(call, 'agent'): call.agent._friday_reply_effect_unknown = True
            raise ExportRefused('renderer_cleanup_unconfirmed')
    # Reached only after successful actual Popen/wait AND the original finally
    # confirmed cleanup/registry restoration. Existing callers may ignore it.
    return _RenderReceipt(argv, work, custody.process, started, deadline, _RUN_COMPLETION_AUTHORITY)


def _private_bytes(parent, leaf, limit):
    item = os.open(leaf, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK, dir_fd=parent)
    try:
        before = os.fstat(item)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_mode & 0o077
                or before.st_uid != os.getuid() or not 0 < before.st_size <= limit):
            raise ExportRefused('invalid_pdf')
        chunks, size = [], 0
        while chunk := os.read(item, min(65536, limit+1-size)):
            chunks.append(chunk); size += len(chunk)
            if size > limit: raise ExportRefused('invalid_pdf')
        after = os.fstat(item)
        named = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        identity = lambda st: tuple(getattr(st, f) for f in fields)
        if (identity(before) != identity(after) or identity(after) != identity(named)
                or size != before.st_size): raise ExportRefused('invalid_pdf')
        return b''.join(chunks)
    finally:
        os.close(item)


def _read_pdf(work):
    root = output = None
    try:
        root = os.open(work, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        output = os.open('out', os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=root)
        for descriptor in (root, output):
            info = os.fstat(descriptor)
            if info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ExportRefused('invalid_pdf')
        data = _private_bytes(output, 'input.pdf', MAX_OUTPUT)
        if not data.startswith(b'%PDF-') or not data.rstrip().endswith(b'%%EOF'):
            raise ExportRefused('invalid_pdf')
        # All child processes are reaped; both reads still distrust scratch paths.
        if _private_bytes(root, 'validated', 14) != b'PDF_VALIDATED\n':
            raise ExportRefused('invalid_pdf')
        return data
    except OSError:
        raise ExportRefused('invalid_pdf') from None
    finally:
        if output is not None: os.close(output)
        if root is not None: os.close(root)


def render(cap, data):
    from hermes_cli.friday_workspace_revision import check
    check(cap)
    toolchain = _toolchain()
    work = Path(tempfile.mkdtemp(prefix='friday-docx-pdf-'))
    try:
        work.chmod(0o700)
        for name in ('out', 'home', 'tmp'): (work/name).mkdir(mode=0o700)
        (work/'input.docx').write_bytes(data); (work/'input.docx').chmod(0o600)
        (work/'renderer.py').write_bytes(Path(__file__).read_bytes())
        (work/'renderer.py').chmod(0o600)
        _run(cap, _argv(work, toolchain), work)
        result = _read_pdf(work)
        check(cap)
        return result
    finally:
        try: shutil.rmtree(work)
        except OSError:
            from agent.web_call_context import _current
            call = _current.get()
            if call is not None and hasattr(call, 'agent'):
                call.agent._friday_reply_effect_unknown = True
            raise ExportRefused('renderer_cleanup_unconfirmed') from None


def create_pdf(cap, fd, leaf, path, content):
    from hermes_cli.friday_user_scope import workspace_document, ScopeDenied
    from hermes_cli.friday_workspace_revision import check
    from hermes_cli.friday_workspace_docx import _create_bytes, _check_parent
    check(cap); _check_parent(cap, fd, path)
    source, relative = _source_spec(content, cap)
    try:
        os.stat(leaf, dir_fd=fd, follow_symlinks=False)
        return json.dumps({'success': False, 'error': 'document_already_exists', 'path': path})
    except FileNotFoundError: pass
    try:
        data, _, identity = workspace_document(str(source), with_identity=True)
        _validate_docx(data)
        rendered = render(cap, data)
        def verify():
            check(cap)
            current, _, version = workspace_document(str(source), with_identity=True)
            if current != data or version != identity: raise ScopeDenied()
        result = json.loads(_create_bytes(cap, fd, leaf, path, rendered,
                                         output_format='pdf', verify_source=verify))
        if result.get('success'):
            result.update(source=relative, source_sha256=hashlib.sha256(data).hexdigest(),
                          export_mode='docx_pdf', source_unchanged=True)
        return json.dumps(result)
    except ExportRefused as error:
        unknown = str(error) == 'renderer_cleanup_unconfirmed'
        return json.dumps({'success': False, 'error': 'document_export_refused', 'reason': str(error),
                           'effect_disposition': 'unknown' if unknown else 'none'})
    except (TimeoutError, RuntimeError, OSError):
        return json.dumps({'success': False, 'error': 'document_export_stopped', 'effect_disposition': 'none'})


def _check_pdf_info(info):
    # Metadata can contain newlines. Never trust an injected first Pages line.
    pages = re.findall(rb'^Pages:\s+([1-9][0-9]*)\s*$', info, re.MULTILINE)
    if len(info) > 8192 or len(pages) != 1 or int(pages[0]) > 200:
        raise ValueError('invalid_pdf')


def _render_child():
    """Stdlib-only fixed namespace entrypoint; no caller-supplied options."""
    import resource
    os.umask(0o077)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    for key, value in ((resource.RLIMIT_AS, 2*1024**3), (resource.RLIMIT_CPU, 35),
                       (resource.RLIMIT_FSIZE, 16*1024**2), (resource.RLIMIT_CORE, 0),
                       (resource.RLIMIT_NOFILE, 128)):
        resource.setrlimit(key, (value, value))
    program = _PREFIX+'/root/usr/lib/libreoffice/program'
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/work/home', 'TMPDIR': '/work/tmp',
           'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'SAL_USE_VCLPLUGIN': 'svp',
           'XDG_CACHE_HOME': '/work/home/cache', 'XDG_CONFIG_HOME': '/work/home/config',
           'XDG_RUNTIME_DIR': '/work/tmp',
           'LD_LIBRARY_PATH': program+':'+_PREFIX+'/root/usr/lib/x86_64-linux-gnu'}
    command = [program+'/soffice', '--headless', '--norestore', '--nodefault',
               '--nolockcheck', '--nofirststartwizard',
               '-env:UserInstallation=file:///work/home/profile', '--convert-to',
               'pdf:writer_pdf_Export', '--outdir', '/work/out', '/work/input.docx']
    subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=35, check=True)
    with open('/work/pdfinfo', 'wb') as output:
        subprocess.run(['/usr/bin/pdfinfo', '/work/out/input.pdf'], env=env,
                       stdin=subprocess.DEVNULL, stdout=output,
                       stderr=subprocess.DEVNULL, timeout=3, check=True)
    with open('/work/pdfinfo', 'rb') as output: info = output.read(8193)
    _check_pdf_info(info)
    Path('/work/validated').write_bytes(b'PDF_VALIDATED\n')


if __name__ == '__main__':
    if sys.argv[1:] != ['--render']: raise SystemExit(2)
    try: _render_child()
    except BaseException: raise SystemExit(1)
