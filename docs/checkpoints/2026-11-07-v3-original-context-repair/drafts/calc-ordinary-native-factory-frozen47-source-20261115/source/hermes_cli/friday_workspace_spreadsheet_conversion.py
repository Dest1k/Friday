"""Bounded real XLSX↔ODS conversion behind spreadsheet_convert.

Family-local adapter; the shared renderer and macro-preserving path stay separate.
The fixed Office process runs under the existing native custody/deadline fence.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from zipfile import ZipFile

PAIRS = {('xlsx','ods'): ('ods:calc8', 'application/vnd.oasis.opendocument.spreadsheet'),
         ('ods','xlsx'): ('xlsx:Calc MS Excel 2007 XML', None)}
_MARKER = b'SPREADSHEET_NATIVE_VALIDATED\n'


def _office_command(source, target):
    if (source,target) not in PAIRS:
        raise ValueError('conversion_pair_unsupported')
    program = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/soffice'
    return [program, '--headless', '--norestore', '--nodefault', '--nolockcheck',
            '--nofirststartwizard', '-env:UserInstallation=file:///work/home/profile',
            '--convert-to', PAIRS[source,target][0], '--outdir', '/work/out', '/work/input.'+source]


def _argv(work, toolchain, source, target):
    from hermes_cli.friday_workspace_pdf import _PREFIX, ExportRefused
    if (source,target) not in PAIRS: raise ExportRefused('conversion_pair_unsupported')
    argv = ['/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session',
            '--as-pid-1','--cap-drop','ALL','--clearenv','--ro-bind','/usr','/usr']
    for alias in ('bin','sbin','lib','lib64'):
        item = Path('/')/alias
        if item.exists():
            resolved = item.resolve()
            if not resolved.is_relative_to('/usr'): raise ExportRefused('renderer_unavailable')
            argv += ['--symlink',str(resolved),str(item)]
    argv += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/opt',
             '--ro-bind',str(toolchain),_PREFIX,
             '--ro-bind','/usr/share',_PREFIX+'/.host-share',
             '--ro-bind',str(toolchain/'share-merged'),'/usr/share','--dir','/etc']
    for item in ('/etc/fonts','/etc/ld.so.cache','/var/cache/fontconfig'):
        if Path(item).exists(): argv += ['--ro-bind',item,item]
    argv += ['--bind',str(work),'/work',
             '--ro-bind',str(work/('input.'+source)),'/work/input.'+source,
             '--ro-bind',str(work/'renderer.py'),'/renderer.py',
             '--chdir','/work','--remount-ro','/','--','/usr/bin/python3','-I','-B','-S',
             '/renderer.py','--render',source,target]
    return argv


def _read_output(work, target):
    from hermes_cli.friday_workspace_pdf import ExportRefused, _private_bytes
    root = output = None
    try:
        root = os.open(work,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        output = os.open('out',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=root)
        for fd in (root,output):
            info = os.fstat(fd)
            if info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ExportRefused('invalid_spreadsheet_output')
        if os.listdir(output) != ['input.'+target]:
            raise ExportRefused('invalid_spreadsheet_output')
        data = _private_bytes(output,'input.'+target,1000000)
        if _private_bytes(root,'validated',len(_MARKER)) != _MARKER:
            raise ExportRefused('invalid_spreadsheet_output')
        return data
    except OSError:
        raise ExportRefused('invalid_spreadsheet_output') from None
    finally:
        if output is not None: os.close(output)
        if root is not None: os.close(root)


def render(cap, data, source, target, *, _calc_metric_context=None):
    from hermes_cli.friday_workspace_pdf import _run, _toolchain, ExportRefused
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_spreadsheet_conversion import inventory, validate_destination, FORMULA_DIALECT
    from tools.scoped_spreadsheet_rich import fidelity_report
    if (source,target) not in PAIRS: raise ExportRefused('conversion_pair_unsupported')
    check(cap)
    before = inventory(data,source,checkpoint=lambda:check(cap))
    from hermes_cli import friday_workspace_calc_measured as measured
    use_measured = measured.finite_native_family(before,source,target)
    if use_measured and _calc_metric_context is not None:
        raise ExportRefused('external_calc_metric_context_refused')
    toolchain = _toolchain()
    work = Path(tempfile.mkdtemp(prefix='friday-spreadsheet-convert-'))
    try:
        work.chmod(0o700)
        for name in ('out','home','tmp'): (work/name).mkdir(mode=0o700)
        for name,value in (('input.'+source,data),('renderer.py',Path(__file__).read_bytes())):
            (work/name).write_bytes(value); (work/name).chmod(0o600)
        check(cap)
        operation = None
        if use_measured:
            from agent.web_call_context import _current, same_web_authority
            call = _current.get()
            if call is None or not same_web_authority(call):
                raise ExportRefused('native_deadline_required')
            try:
                operation = measured.prepare_operation(work,data,before,
                    deadline=min(call.deadline(),time.monotonic()+35))
            except measured.MeasuredRefused as exc:
                raise ExportRefused(str(exc)) from None
            check(cap)
            receipt = _run(cap,operation.argv,work)  # SAME original custody, parent40/child35
            operation.execution.append(receipt)
        else:
            _run(cap,_argv(work,toolchain,source,target),work)
        rendered = _read_output(work,target)
        if use_measured:
            check(cap)
            try:
                verified = measured.read_verified_operation(work,operation,data,rendered)
            except measured.MeasuredRefused as exc:
                raise ExportRefused(str(exc)) from None
            check(cap)
            # Facts originate ONLY from the fixed controlled same-operation
            # producer/native/terminal custody. JSON/type/hash alone admit none.
            from tools.scoped_spreadsheet_calc_metric import CalcReferenceMetricContext
            _calc_metric_context = CalcReferenceMetricContext(
                source_sha256=hashlib.sha256(data).hexdigest(),source_bytes=len(data),
                destination_sha256=hashlib.sha256(rendered).hexdigest(),destination_bytes=len(rendered),
                producer_version=verified['producer_version'],
                reviewed_source_commit=verified['reviewed_source_commit'],
                numeric_rule=verified['numeric_rule'],recipe_sha256=verified['recipe_sha256'],
                component_sha256=verified['component_sha256'],
                source_style_name=verified['source_style_name'],source_font=verified['source_font'],
                default_script=verified['default_script'],export_name=verified['export_name'],
                export_charset=verified['export_charset'],raw_font_height=verified['raw_font_height'],
                font_descriptor_sha256=verified['font_descriptor_sha256'],
                font_view_sha256=verified['font_view_sha256'],
                reference_state_sha256=verified['reference_state_sha256'],
                applicability_sha256=verified['applicability_sha256'],raw_m=verified['raw_m'])
        after = validate_destination(before,rendered,target,checkpoint=lambda:check(cap),
                                     _calc_metric_context=_calc_metric_context)
        check(cap)
        fidelity = fidelity_report(before.rich_signature, after.rich_signature,
                                   source_kind=source, target_kind=target,
                                   _calc_metric_context=_calc_metric_context) if before.rich_signature else None
        losses = fidelity['declared_losses'] if fidelity else []
        unassessed = fidelity['unassessed'] if fidelity else []
        return rendered, dict(native_editable=True, formulas_preserved=True,
                              formula_cache_validation='independent_bounded_decimal_recomputation',
                              formula_dialect=FORMULA_DIALECT,
                              semantic_inventory_sha256=after.digest(), **after.counts(),
                              preservation=('typed_literals_sheet_order_supported_formula_references_and_validated_spreadsheet_structure_with_declared_fidelity'
                                            if losses or unassessed else 'typed_literals_sheet_order_supported_formula_references_and_validated_spreadsheet_structure'
                                            if before.rich_signature else 'typed_literals_sheet_order_and_supported_formula_references'),
                              declared_limits=('bounded_scalar_cells_dates_SUM_rectangle_two_cell_product_and_validated_spreadsheet_features; unknown_features_refused'
                                               if before.rich_signature else 'plain_scalar_cells_dates_SUM_rectangle_two_cell_product; no_names_tables_custom_styles'),
                              **({'rich_spreadsheet_profile_preserved': not bool(losses or unassessed),
                                  'declared_losses': losses, 'fidelity': fidelity}
                                 if before.rich_signature else {}),
                              office_filter=PAIRS[source,target][0], runtime_qualified=False)
    finally:
        try: shutil.rmtree(work)
        except OSError:
            from agent.web_call_context import _current
            call = _current.get()
            if call is not None and hasattr(call,'agent'):
                call.agent._friday_reply_effect_unknown = True
            raise ExportRefused('renderer_cleanup_unconfirmed') from None


def execute_conversion(cap, fd, leaf, path, source_name, source, target):
    """Called only for the two directed pairs; publication retains the existing CAS."""
    from hermes_cli.friday_user_scope import ScopeDenied
    from hermes_cli.friday_workspace_docx import _check_parent
    from hermes_cli.friday_workspace_presentation import _read_source, _publish
    from hermes_cli.friday_workspace_pdf import ExportRefused
    from hermes_cli.friday_workspace_revision import check
    from tools.scoped_spreadsheet_conversion import ConversionRefused
    if (source,target) not in PAIRS or Path(path).suffix.lower() != '.'+target:
        raise ScopeDenied()
    try:
        check(cap); _check_parent(cap,fd,path)
        try: os.stat(leaf,dir_fd=fd,follow_symlinks=False)
        except FileNotFoundError: pass
        else: return json.dumps(dict(success=False,error='document_already_exists',effect_disposition='none'))
        item,relative,data,identity = _read_source(source_name,cap,'.'+source)
        rendered,facts = render(cap,data,source,target)
        check(cap)
        facts.update(source=relative,source_sha256=hashlib.sha256(data).hexdigest(),
                     source_unchanged=True,macros_executed=False,export_mode=source+'_'+target)
        return _publish(cap,fd,leaf,path,rendered,target,(item,data,identity),facts)
    except ScopeDenied:
        raise
    except (ConversionRefused,ExportRefused) as error:
        unknown = str(error) == 'renderer_cleanup_unconfirmed'
        return json.dumps(dict(success=False,error='spreadsheet_conversion_refused',reason=str(error),
                               effect_disposition='unknown' if unknown else 'none'))
    except (OSError,RuntimeError,TimeoutError):
        return json.dumps(dict(success=False,error='spreadsheet_conversion_stopped',effect_disposition='none'))


def _render_child(source,target):
    # This entrypoint imports only stdlib, and receives fixed enumerated pairs.
    import resource
    if (source,target) not in PAIRS: raise ValueError('conversion_pair_unsupported')
    os.umask(0o077)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0,cpus)
    for key,value in ((resource.RLIMIT_AS,1024**3),(resource.RLIMIT_CPU,35),
                      (resource.RLIMIT_FSIZE,16*1024**2),(resource.RLIMIT_CORE,0),
                      (resource.RLIMIT_NOFILE,128)):
        resource.setrlimit(key,(value,value))
    profile = Path('/work/home/profile'); profile.mkdir(mode=0o700)
    (profile/'user').mkdir(mode=0o700)
    # Disable macro execution and link update independently of the preflight.
    (profile/'user/registrymodifications.xcu').write_text(
        '<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry">'
        '<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item>'
        '<item oor:path="/org.openoffice.Office.Calc/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>0</value></prop></item></oor:items>',encoding='utf-8')
    prefix = '/opt/friday-document-toolchain'
    program = prefix+'/root/usr/lib/libreoffice/program'
    env = {'PATH':'/usr/bin:/bin','HOME':'/work/home','TMPDIR':'/work/tmp',
           'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','SAL_USE_VCLPLUGIN':'svp',
           'MAX_CONCURRENCY':str(len(cpus)),
           'XDG_CACHE_HOME':'/work/home/cache','XDG_CONFIG_HOME':'/work/home/config',
           'XDG_RUNTIME_DIR':'/work/tmp',
           'LD_LIBRARY_PATH':program+':'+prefix+'/root/usr/lib/x86_64-linux-gnu'}
    subprocess.run(_office_command(source,target),env=env,stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=35,check=True)
    # Marker only signals child completion. Parent performs authoritative bounded validation.
    with ZipFile('/work/out/input.'+target) as package:
        if target == 'ods' and package.read('mimetype') != PAIRS[source,target][1].encode():
            raise ValueError('invalid_ods')
        if target == 'xlsx' and 'xl/workbook.xml' not in package.namelist():
            raise ValueError('invalid_xlsx')
    Path('/work/validated').write_bytes(_MARKER)


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] != '--render': raise SystemExit(2)
    try: _render_child(sys.argv[2],sys.argv[3])
    except BaseException: raise SystemExit(1)
