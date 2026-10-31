"""Own-workspace native presentation writes and typed bounded Office conversion."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, BadZipFile

_OPERATIONS = {
    'pptx_pdf': {'source': '.pptx', 'output': '.pdf', 'input': 'pptx', 'result': 'pdf',
                 'filter': 'pdf:impress_pdf_Export'},
    'odp_pptx': {'source': '.odp', 'output': '.pptx', 'input': 'odp', 'result': 'pptx',
                 'filter': 'pptx:Impress MS PowerPoint 2007 XML'},
    'pptx_odp': {'source': '.pptx', 'output': '.odp', 'input': 'pptx', 'result': 'odp',
                 'filter': 'odp:impress8'},
}


def _office_command(operation):
    if operation not in _OPERATIONS:
        raise ValueError('unsupported_conversion')
    spec = _OPERATIONS[operation]
    program = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/soffice'
    return [program, '--headless', '--norestore', '--nodefault',
            '--nolockcheck', '--nofirststartwizard',
            '-env:UserInstallation=file:///work/home/profile', '--convert-to',
            spec['filter'], '--outdir', '/work/out', '/work/input' + spec['source']]


def _source(raw, cap, suffix):
    from hermes_cli.friday_user_scope import ScopeDenied
    if not isinstance(raw, str) or not raw or '\x00' in raw:
        raise ScopeDenied()
    source = Path(raw)
    root = cap.home / 'workspace'
    if not source.is_absolute():
        source = root / source
    try:
        relative = source.relative_to(root)
    except ValueError:
        raise ScopeDenied() from None
    if (not relative.parts or source.suffix.lower() != suffix
            or any(part in ('.', '..') or part.startswith('.') for part in relative.parts)):
        raise ScopeDenied()
    return source, relative.as_posix()


def _read_source(raw, cap, suffix):
    from hermes_cli.friday_user_scope import workspace_document
    source, relative = _source(raw, cap, suffix)
    data, _, identity = workspace_document(str(source), with_identity=True)
    return source, relative, data, identity


def _publish(cap, fd, leaf, path, data, output_format, source_state=None, extra=None):
    from hermes_cli.friday_user_scope import ScopeDenied, workspace_document
    from hermes_cli.friday_workspace_docx import _create_bytes
    from hermes_cli.friday_workspace_revision import check
    verify = None
    if source_state is not None:
        source, original, identity = source_state
        def verify():
            check(cap)
            current, _, version = workspace_document(str(source), with_identity=True)
            if current != original or version != identity:
                raise ScopeDenied()
    result = json.loads(_create_bytes(cap, fd, leaf, path, data,
                                     output_format=output_format, verify_source=verify))
    if result.get('success') and extra:
        result.update(extra)
    return json.dumps(result, ensure_ascii=False)


def create_pptx(cap, fd, leaf, path, content):
    from hermes_cli.friday_user_scope import ScopeDenied
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_presentation_write import create_pptx as render, json_object, orders_facts, PresentationRefused
    try:
        check(cap)
        spec = json_object(content, ('source', 'slides', 'series'))
        source, relative, data, identity = _read_source(spec['source'], cap, '.xlsx')
        facts = orders_facts(data)
        rendered = render(facts, spec)
        facts_public = {key: facts[key] for key in ('totals', 'grand_total', 'currency', 'largest_sku')}
        return _publish(cap, fd, leaf, path, rendered, 'pptx', (source, data, identity),
                        {'source': relative, 'source_sha256': hashlib.sha256(data).hexdigest(),
                         'source_unchanged': True, 'native_editable': True,
                         'slides': 5, 'native_charts': 1, 'source_facts': facts_public})
    except PresentationRefused:
        raise ScopeDenied() from None


def create_odp(cap, fd, leaf, path, content):
    from hermes_cli.friday_user_scope import ScopeDenied
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_presentation_write import create_odp as render, json_object, PresentationRefused
    try:
        check(cap)
        spec = json_object(content, ('slides',))
        return _publish(cap, fd, leaf, path, render(spec), 'odp',
                        extra={'native_editable': True, 'slides': len(spec['slides'])})
    except PresentationRefused:
        raise ScopeDenied() from None


def edit_pptx(cap, fd, leaf, path, content):
    from hermes_cli.friday_user_scope import ScopeDenied
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_presentation_write import edit_pptx as edit, json_object, PresentationRefused, validate_native
    fields = ('source', 'slide', 'old_title', 'new_title', 'category', 'old_value', 'new_value')
    try:
        check(cap)
        spec = json_object(content, fields)
        source, relative, data, identity = _read_source(spec['source'], cap, '.pptx')
        validate_native(data, 'pptx')
        rendered = edit(data, spec)
        return _publish(cap, fd, leaf, path, rendered, 'pptx', (source, data, identity),
                        {'source': relative, 'source_sha256': hashlib.sha256(data).hexdigest(),
                         'source_unchanged': True, 'preserving_edit': True})
    except PresentationRefused:
        raise ScopeDenied() from None


def edit_odp(cap, fd, leaf, path, content):
    from hermes_cli.friday_user_scope import ScopeDenied
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_presentation_write import edit_odp as edit, json_object, PresentationRefused, validate_native
    fields = ('source', 'slide', 'table', 'row', 'column', 'old_value', 'new_value')
    try:
        check(cap)
        spec = json_object(content, fields)
        source, relative, data, identity = _read_source(spec['source'], cap, '.odp')
        validate_native(data, 'odp')
        rendered = edit(data, spec)
        return _publish(cap, fd, leaf, path, rendered, 'odp', (source, data, identity),
                        {'source': relative, 'source_sha256': hashlib.sha256(data).hexdigest(),
                         'source_unchanged': True, 'preserving_edit': True})
    except PresentationRefused:
        raise ScopeDenied() from None


def _argv(work, toolchain, operation):
    from hermes_cli.friday_workspace_pdf import _PREFIX, ExportRefused
    spec = _OPERATIONS[operation]
    input_name = 'input' + spec['source']
    argv = ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session',
            '--as-pid-1', '--cap-drop', 'ALL', '--clearenv', '--ro-bind', '/usr', '/usr']
    for alias in ('bin', 'sbin', 'lib', 'lib64'):
        item = Path('/') / alias
        if item.exists():
            target = item.resolve()
            if not target.is_relative_to('/usr'):
                raise ExportRefused('renderer_unavailable')
            argv += ['--symlink', str(target), str(item)]
    argv += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/opt',
             '--ro-bind', str(toolchain), _PREFIX,
             '--ro-bind', '/usr/share', _PREFIX + '/.host-share',
             '--ro-bind', str(toolchain / 'share-merged'), '/usr/share', '--dir', '/etc']
    for item in ('/etc/fonts', '/etc/ld.so.cache', '/var/cache/fontconfig'):
        if Path(item).exists():
            argv += ['--ro-bind', item, item]
    argv += ['--bind', str(work), '/work', '--ro-bind', str(work / input_name), '/work/' + input_name,
             '--ro-bind', str(work / 'renderer.py'), '/renderer.py', '--chdir', '/work',
             '--remount-ro', '/', '--', '/usr/bin/python3', '-I', '-B', '-S',
             '/renderer.py', '--render', operation]
    return argv


def _read_native(work, operation):
    from hermes_cli.friday_workspace_pdf import ExportRefused, _private_bytes
    from tools.scoped_presentation_write import validate_native, PresentationRefused
    spec = _OPERATIONS[operation]
    root = output = None
    try:
        root = os.open(work, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        output = os.open('out', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        for descriptor in (root, output):
            info = os.fstat(descriptor)
            if info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ExportRefused('invalid_native_output')
        data = _private_bytes(output, 'input' + spec['output'], 1000000)
        if _private_bytes(root, 'validated', 17) != b'NATIVE_VALIDATED\n':
            raise ExportRefused('invalid_native_output')
        validate_native(data, spec['result'])
        return data
    except (OSError, PresentationRefused):
        raise ExportRefused('invalid_native_output') from None
    finally:
        if output is not None:
            os.close(output)
        if root is not None:
            os.close(root)


def render(cap, data, operation):
    from hermes_cli.friday_workspace_pdf import _read_pdf, _run, _toolchain
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_presentation_write import validate_native
    if operation not in _OPERATIONS:
        raise ValueError('unsupported_conversion')
    spec = _OPERATIONS[operation]
    check(cap)
    validate_native(data, spec['input'])
    toolchain = _toolchain()
    work = Path(tempfile.mkdtemp(prefix='friday-presentation-convert-'))
    try:
        work.chmod(0o700)
        for name in ('out', 'home', 'tmp'):
            (work / name).mkdir(mode=0o700)
        input_name = 'input' + spec['source']
        (work / input_name).write_bytes(data)
        (work / input_name).chmod(0o600)
        (work / 'renderer.py').write_bytes(Path(__file__).read_bytes())
        (work / 'renderer.py').chmod(0o600)
        _run(cap, _argv(work, toolchain, operation), work)
        result = _read_pdf(work) if operation == 'pptx_pdf' else _read_native(work, operation)
        check(cap)
        return result
    finally:
        try:
            shutil.rmtree(work)
        except OSError:
            from agent.web_call_context import _current
            from hermes_cli.friday_workspace_pdf import ExportRefused
            call = _current.get()
            if call is not None and hasattr(call, 'agent'):
                call.agent._friday_reply_effect_unknown = True
            raise ExportRefused('renderer_cleanup_unconfirmed') from None


def create_conversion(cap, fd, leaf, path, content, operation):
    from hermes_cli.friday_user_scope import ScopeDenied
    from hermes_cli.friday_workspace_docx import _check_parent
    from hermes_cli.friday_workspace_pdf import ExportRefused
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_presentation_write import json_object, PresentationRefused
    if operation not in _OPERATIONS:
        raise ScopeDenied()
    spec = _OPERATIONS[operation]
    try:
        check(cap)
        _check_parent(cap, fd, path)
        request = json_object(content, ('source',), limit=4096)
        try:
            os.stat(leaf, dir_fd=fd, follow_symlinks=False)
            return json.dumps({'success': False, 'error': 'document_already_exists', 'path': path})
        except FileNotFoundError:
            pass
        source, relative, data, identity = _read_source(request['source'], cap, spec['source'])
        rendered = render(cap, data, operation)
        return _publish(cap, fd, leaf, path, rendered, spec['result'], (source, data, identity),
                        {'source': relative, 'source_sha256': hashlib.sha256(data).hexdigest(),
                         'source_unchanged': True, 'export_mode': operation,
                         'office_filter': spec['filter'], 'runtime_qualified': False})
    except PresentationRefused:
        raise ScopeDenied() from None
    except ExportRefused as error:
        unknown = str(error) == 'renderer_cleanup_unconfirmed'
        return json.dumps({'success': False, 'error': 'document_export_refused',
                           'reason': str(error), 'effect_disposition': 'unknown' if unknown else 'none'})
    except (TimeoutError, RuntimeError, OSError):
        return json.dumps({'success': False, 'error': 'document_export_stopped',
                           'effect_disposition': 'none'})


def _render_child(operation):
    import resource
    import re
    prefix = '/opt/friday-document-toolchain'
    if operation not in _OPERATIONS:
        raise ValueError('unsupported_conversion')
    spec = _OPERATIONS[operation]
    os.umask(0o077)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    for key, value in ((resource.RLIMIT_AS, 2 * 1024**3), (resource.RLIMIT_CPU, 35),
                       (resource.RLIMIT_FSIZE, 16 * 1024**2), (resource.RLIMIT_CORE, 0),
                       (resource.RLIMIT_NOFILE, 128)):
        resource.setrlimit(key, (value, value))
    program = prefix + '/root/usr/lib/libreoffice/program'
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/work/home', 'TMPDIR': '/work/tmp',
           'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'SAL_USE_VCLPLUGIN': 'svp',
           'XDG_CACHE_HOME': '/work/home/cache', 'XDG_CONFIG_HOME': '/work/home/config',
           'XDG_RUNTIME_DIR': '/work/tmp',
           'LD_LIBRARY_PATH': program + ':' + prefix + '/root/usr/lib/x86_64-linux-gnu'}
    command = _office_command(operation)
    subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=35, check=True)
    if operation == 'pptx_pdf':
        with open('/work/pdfinfo', 'wb') as output:
            subprocess.run(['/usr/bin/pdfinfo', '/work/out/input.pdf'], env=env,
                           stdin=subprocess.DEVNULL, stdout=output,
                           stderr=subprocess.DEVNULL, timeout=3, check=True)
        with open('/work/pdfinfo', 'rb') as output:
            info = output.read(8193)
        pages = re.findall(rb'^Pages:\s+([1-9][0-9]*)\s*$', info, re.MULTILINE)
        if len(info) > 8192 or len(pages) != 1 or int(pages[0]) > 200:
            raise ValueError('invalid_pdf')
        Path('/work/validated').write_bytes(b'PDF_VALIDATED\n')
    else:
        output_name = '/work/out/input' + spec['output']
        with ZipFile(output_name) as package:
            names = set(package.namelist())
            if spec['result'] == 'pptx' and 'ppt/presentation.xml' not in names:
                raise ValueError('invalid_pptx')
            if spec['result'] == 'odp' and package.read('mimetype') != b'application/vnd.oasis.opendocument.presentation':
                raise ValueError('invalid_odp')
        Path('/work/validated').write_bytes(b'NATIVE_VALIDATED\n')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--render':
        raise SystemExit(2)
    try:
        _render_child(sys.argv[2])
    except BaseException:
        raise SystemExit(1)
