"""Root-only first ordinary qualifier SOURCE; no command launches an actor.

Invoke the private callable only from a genuinely admitted current native call.
Selecting reviewed SOURCE does not authorize an operation or qualify production.
The production render() guard is never modified, patched or called around here.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
INPUT = Path('/home/jericho/.cache/FRW-SOL-V3-ORDINARY-CALC-D6-PROVIDER-BINDING-CORE-20261116/consumers/native-r3/new-private-source.ods')
INPUT_SHA = '0d871b267454bfce04906fd76c603655c4278e50c2fd3c39f5ea45084af3b855'
PROVENANCE = INPUT.parent / 'PROVENANCE.json'
PROVENANCE_SHA = '62663a85eb14c92421edd6d948c3c018ba17d501d20817714c7b7734b3f2cd03'

# Fixed reviewed whole58 SOURCE selection; exact metadata pinned in this Source.
# This does not admit a Root operation, qualify production or create authority.
# No CLI option, environment, JSON, cap argument or prior PASS sets this value.
SELECTED_SOURCE = (
    Path('/home/jericho/.cache/FRW-ASTRA-ORDINARY-CONTROL700-SOURCE-DELTA-20261116/candidate/native'),
    '3fb002b68a9e0d3b75df91dd9c5c016a9e87f9052d38917533630fac29ee557b',
    Path('/home/jericho/.cache/FRW-ASTRA-ORDINARY-CONTROL700-SOURCE-DELTA-20261116/future-runtime-work'),
    Path('/home/jericho/.cache/FRW-ASTRA-ORDINARY-CONTROL700-SOURCE-DELTA-20261116/SELECTED-NATIVE58-PINS.json'),
    '4122b24f9ac502faaf1320e32d8b3a5b88063e92d494f1e7280fa08404c7eb8e',
)
INDEX_RELATIVE = 'hermes_cli/_calc_native_assets/index.json'
HOST_PIN_RELATIVE = 'hermes_cli/friday_workspace_calc_native_pin.py'
ASSET_PREFIX = 'hermes_cli/_calc_native_assets/'


class QualifierRefused(ValueError):
    pass


class CleanupUnknown(RuntimeError):
    """Root must reconcile retained work/custody; never retry automatically."""

    def __init__(self, reason, work):
        super().__init__(reason)
        self.work = work  # private exact owned path, never a public response


def need(value, reason):
    if not value:
        raise QualifierRefused(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(info):
    return tuple(getattr(info, key) for key in (
        'st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_nlink',
        'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def private_read(path, expected, limit=1000000, *, allow_empty=False,
                 modes=(0o400, 0o600)):
    need(path.is_absolute() and path.resolve() == path, 'qualifier_exact_path_required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
             and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) in modes
             and (0 if allow_empty else 1) <= before.st_size <= limit,
             'qualifier_private_file_required')
        chunks, count = [], 0
        while True:
            part = os.read(fd, min(65536, limit + 1 - count))
            if not part:
                break
            chunks.append(part)
            count += len(part)
            need(count <= limit, 'qualifier_file_limit')
        raw = b''.join(chunks)
        need(stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat())
             and count == before.st_size and sha(raw) == expected,
             'qualifier_file_CAS')
        return raw
    finally:
        os.close(fd)


def inspect_baseline():
    """Verify the fixed selected Source only; no authority, nonce or runtime query."""
    root, generation, _ = _selected()
    data = private_read(INPUT, INPUT_SHA)
    private_read(PROVENANCE, PROVENANCE_SHA)
    return dict(source_only=True, selected_source_verified=True,
                selected_source_prefix=str(root), selected_files=58, staged_files=35,
                selected_index_sha256=generation, input_sha256=sha(data), input_bytes=len(data),
                provenance='PRIVATE_SOURCE_DERIVED_PASSIVE_SCAFFOLD_INVENTED_SEMANTICS',
                selected_execution_source=True, Root_entry='PRIVATE_ROOT_KIND_SOURCE_BOUND',
                execution_ready=False, actual_M=None, runtime_executed=False,
                production_enabled=False)


def require_stock_qname_bindings(data):
    """Narrow first-stock-output invariant; canonical metadata has this limit."""
    with ZipFile(BytesIO(data)) as archive:
        raw = archive.read('docProps/core.xml')
    xsi_type = '{http://www.w3.org/2001/XMLSchema-instance}type'
    pending, stack, seen = [], [], []
    for event, item in ET.iterparse(BytesIO(raw), events=('start-ns', 'start', 'end')):
        if event == 'start-ns':
            pending.append(item)
        elif event == 'start':
            scope = dict(stack[-1]) if stack else {}
            scope.update(pending)
            pending.clear()
            stack.append(scope)
            value = item.get(xsi_type)
            if value is not None:
                need(value == 'dcterms:W3CDTF'
                     and scope.get('dcterms') == 'http://purl.org/dc/terms/',
                     'qualifier_stock_metadata_QName_binding')
                seen.append(value)
        else:
            stack.pop()
    # An absent typed date is not fabricated; canonical core profile decides
    # required shape. This function only verifies every actual lexical value.
    return dict(checked='docProps/core.xml xsi:type', values=len(seen))


def _selected():
    """Read-only exact selected58/index/outside-host-pin composition checks."""
    need(SELECTED_SOURCE is not None, 'qualifier_fixed_source_selection_unbound')
    root, generation, work_parent, manifest, manifest_sha = SELECTED_SOURCE
    need(isinstance(root, Path) and isinstance(work_parent, Path)
         and root.is_absolute() and root.resolve() == root
         and work_parent.is_absolute() and work_parent.resolve() == work_parent,
         'qualifier_source_selection')
    raw = private_read(manifest, manifest_sha, 262144)
    pins = json.loads(raw)
    need(pins['prefix'] == str(root) and pins['index_sha256'] == generation
         and type(pins['leaves']) is dict and len(pins['leaves']) == 58,
         'qualifier_selected_manifest')
    need(INDEX_RELATIVE in pins['leaves'] and HOST_PIN_RELATIVE in pins['leaves']
         and pins['leaves'][INDEX_RELATIVE]['sha256'] == generation,
         'qualifier_selected_generation_mismatch')
    expected_dirs = {str(parent) for relative in pins['leaves']
                     for parent in Path(relative).parents if parent != Path('.')}
    found, seen, pending = set(), set(), [root]
    # Bounded by manifest58 plus its finite directory set. An undeclared entry
    # is refused immediately; symlinks/special files are never followed.
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = str(path.relative_to(root))
                need(relative not in seen, 'qualifier_selected_tree_CAS')
                seen.add(relative)
                info = entry.stat(follow_symlinks=False)
                need(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),
                     'qualifier_selected_tree_entry')
                if stat.S_ISDIR(info.st_mode):
                    need(relative in expected_dirs, 'qualifier_selected_exact_tree58')
                    pending.append(path)
                else:
                    need(relative in pins['leaves'], 'qualifier_selected_exact_tree58')
                    found.add(relative)
    need(found == set(pins['leaves']), 'qualifier_selected_exact_tree58')
    checked = {}
    for relative, row in pins['leaves'].items():
        need(type(relative) is str and not Path(relative).is_absolute()
             and '..' not in Path(relative).parts and str(Path(relative)) == relative,
             'qualifier_selected_relative')
        data = private_read(root / relative, row['sha256'], 160 * 1024 * 1024,
                            allow_empty=True, modes=(0o400,))
        need(len(data) == row['bytes'], 'qualifier_selected_source_size')
        if relative in (INDEX_RELATIVE, HOST_PIN_RELATIVE):
            checked[relative] = data
    index = json.loads(checked[INDEX_RELATIVE])
    need(index['schema'] == 'frw.calc.native-code-generation.v1'
         and index['entry'] == 'ordinary_entry.py'
         and type(index['files']) is list and len(index['files']) == 35,
         'qualifier_selected_index')
    indexed = set()
    for row in index['files']:
        relative = row['relative']
        need(type(relative) is str and not Path(relative).is_absolute()
             and '..' not in Path(relative).parts and str(Path(relative)) == relative
             and relative not in indexed, 'qualifier_selected_index_relative')
        indexed.add(relative)
        target = ASSET_PREFIX + relative
        need(target in pins['leaves'] and row['sha256'] == pins['leaves'][target]['sha256'],
             'qualifier_selected_index_mixed_generation')
    managed = {name[len(ASSET_PREFIX):] for name in pins['leaves']
               if name.startswith(ASSET_PREFIX) and name != INDEX_RELATIVE}
    need(indexed == managed, 'qualifier_selected_managed_assets')
    # Parse the outside-index host pin as SOURCE; never import/execute its code.
    assignments = [node for node in ast.parse(checked[HOST_PIN_RELATIVE]).body
                   if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                           and type(node.value.value) is str)]
    need(len(assignments) == 1 and isinstance(assignments[0], ast.Assign)
         and len(assignments[0].targets) == 1
         and isinstance(assignments[0].targets[0], ast.Name)
         and assignments[0].targets[0].id == 'GENERATION_SHA256'
         and isinstance(assignments[0].value, ast.Constant)
         and assignments[0].value.value == generation,
         'qualifier_selected_host_pin_generation')
    return root, generation, work_parent


def _require_root_qualifier_entry():
    """Require the actual trusted issuer's current private Root lease.

    The separate native scope validates its real Root admission/once/current
    binding. Neither a record nor construction/ContextVar binding grants entry.
    """
    from hermes_cli.friday_root_qualification import RootQualificationScope, current
    cap = current(required=True)
    need(type(cap) is RootQualificationScope and cap.principal[0] == 'root-qualification',
         'qualifier_actual_Root_qualification_scope_required')
    cap.check()
    return cap


def _qualify_current_native_call():
    """Future Root invocation, inside an already authenticated native context.

    This source is intentionally not admitted/executed. No constructor creates
    a user scope, web context, nonce, receipt or runtime proof on the caller's
    behalf. No model-visible tool is added. Root must separately bind its exact
    authorization entry before calling this code; fixed Source is not admission.
    """
    cap = _require_root_qualifier_entry()
    # The trusted Root boundary captured these BEFORE current/admission/once.
    # Consume its original immutable clock; never restamp a later local entry.
    entered, parent_deadline = cap.entered_monotonic, cap.deadline
    need(type(entered) is float and math.isfinite(entered)
         and type(parent_deadline) is float and math.isfinite(parent_deadline)
         and entered < parent_deadline <= entered+40,
         'qualifier_original_Root_entry_clock_required')
    cap.check()
    root, generation, work_parent = _selected()
    from agent.web_call_context import _current, same_web_authority, WebCall
    from hermes_cli.friday_root_qualification import current, RootQualificationScope, check_agent
    from tools.approval_context import get_current_session_key
    from hermes_cli import friday_workspace_pdf as pdf
    from hermes_cli import friday_workspace_spreadsheet_conversion as renderer
    from hermes_cli import friday_workspace_calc_measured as measured
    from hermes_cli import friday_workspace_calc_native_factory as factory
    from tools.scoped_spreadsheet_conversion import inventory, validate_destination
    from tools.scoped_spreadsheet_rich import fidelity_report
    need(current(required=True) is cap, 'qualifier_original_Root_scope_changed')
    call = _current.get()
    need(type(cap) is RootQualificationScope and type(call) is WebCall and same_web_authority(call),
         'qualifier_actual_native_cap_and_web_call_required')
    need(cap.principal[0] == 'root-qualification', 'qualifier_private_Root_kind_required')
    agent = getattr(call, 'agent', None)
    need(agent is not None, 'qualifier_existing_agent_required')
    original_gate = call.authorization_gate  # preserve the native gate, never clear it
    original_fields = (call.base_deadline, call.run_deadline, call.task_id,
                       call.call_id, call.session_id, call.session_key, call.turn_id, call.turn)

    def registered_current_call():
        # These are identity/cancellation checks on an ALREADY admitted entry.
        # make_web_call/bind_web_call alone do not authorize a Root operation.
        check_agent(agent)
        session_key = get_current_session_key(default='') or agent.session_id
        need(getattr(call, 'agent', None) is agent
             and getattr(agent, '_friday_root_qualification_scope', None) is cap
             and getattr(agent, '_web_turn', None) is call.turn
             and type(call.task_id) is str and bool(call.task_id)
             and type(call.call_id) is str and bool(call.call_id)
             and getattr(agent, '_tool_result_calls', {}).get((call.task_id, call.call_id)) is call
             and call.session_id == agent.session_id and call.session_key == session_key
             and call.turn_id == getattr(agent, '_current_turn_id', '')
             and call.run_deadline == getattr(agent, '_web_run_deadline', None)
             and not getattr(agent, '_interrupt_requested', False)
             and call.turn.failure is None
             and call.authorization_gate is original_gate
             and original_fields == (call.base_deadline, call.run_deadline, call.task_id,
                                     call.call_id, call.session_id, call.session_key,
                                     call.turn_id, call.turn),
             'qualifier_actual_registered_agent_or_original_clock_changed')

    registered_current_call()
    original_deadline = call.deadline()
    need(type(original_deadline) in (int, float) and math.isfinite(original_deadline)
         and original_deadline == parent_deadline
         and entered < original_deadline <= entered + 40,
         'qualifier_original_native_deadline_outside_parent40')
    parent_deadline = original_deadline
    child_deadline = min(original_deadline, entered + 35)

    def checkpoint():
        need(_current.get() is call and current(required=True) is cap
             and same_web_authority(call) and call.deadline() == original_deadline
             and cap.entered_monotonic == entered and cap.deadline == parent_deadline,
             'qualifier_original_call_or_cap_changed')
        cap.check()
        registered_current_call()
        need(not getattr(getattr(call, 'agent', None), '_friday_reply_effect_unknown', False),
             'qualifier_prior_or_current_unknown_effect')
        need(time.monotonic() < parent_deadline, 'qualifier_parent_deadline')

    checkpoint()
    # Bind real loaded modules; a same-name module/JSON pin is not provenance.
    for module in (pdf, renderer, measured, factory):
        path = Path(module.__file__)
        need(path.resolve() == path and path.parent == root / 'hermes_cli',
             'qualifier_loaded_source_path')
    from hermes_cli import friday_workspace_calc_native_pin as pin
    need(Path(pin.__file__).resolve() == root / 'hermes_cli/friday_workspace_calc_native_pin.py'
         and pin.GENERATION_SHA256 == generation, 'qualifier_selected_generation_mismatch')
    context_type = renderer._canonical_calc_context_type()
    data = private_read(INPUT, INPUT_SHA)
    private_read(PROVENANCE, PROVENANCE_SHA)
    before = inventory(data, 'ods', checkpoint=checkpoint)
    need(measured.finite_native_family(before, 'ods', 'xlsx'), 'qualifier_exact_D6_family')
    checkpoint()
    info = work_parent.lstat()
    need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
         and stat.S_IMODE(info.st_mode) == 0o700, 'qualifier_private_work_parent')
    work = Path(tempfile.mkdtemp(prefix='ordinary-first-qualifier-', dir=work_parent))
    unknown = False
    result = None
    try:
        work.chmod(0o700)
        for name in ('out', 'home', 'tmp'):
            (work / name).mkdir(mode=0o700)
        for name, value in (('input.ods', data), ('renderer.py', Path(renderer.__file__).read_bytes())):
            fd = os.open(work / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(value)
        checkpoint()
        operation = measured.prepare_operation(work, data, before, deadline=child_deadline)
        need(operation.generation_sha256 == generation, 'qualifier_prepared_generation')
        checkpoint()
        try:
            # Live Root guards share child active time; original entry/Dp do
            # not change. The guard exits only after _run's own stop finally.
            with cap.child_execution_ceiling(child_deadline):
                completion = pdf._run(cap, operation.argv, work, _absolute_deadline=child_deadline)  # original custody ONLY
        except BaseException as exc:
            # The existing stop fence owns cancellation. Do not delete work
            # beneath live or unconfirmed custody and never retry a launch.
            unknown = (call.session is not None or call.registry is not None
                       or getattr(getattr(call, 'agent', None), '_friday_reply_effect_unknown', False)
                       or (isinstance(exc, pdf.ExportRefused)
                           and exc.args == ('renderer_cleanup_unconfirmed',)))
            raise
        need(type(completion) is pdf._RenderReceipt
             and completion.authority is pdf._RUN_COMPLETION_AUTHORITY
             and completion.finished <= child_deadline,
             'qualifier_original_typed_receipt_child35_close_required')
        child_closed = time.monotonic()
        need(child_closed <= child_deadline, 'qualifier_child35_closure_overrun')
        operation.execution.append(completion)  # genuine typed _run output only
        checkpoint()
        rendered = renderer._read_output(work, 'xlsx')
        facts = measured.read_verified_operation(work, operation, data, rendered)
        checkpoint()
        context = context_type(source_sha256=sha(data), source_bytes=len(data),
                               destination_sha256=sha(rendered), destination_bytes=len(rendered),
                               **facts)
        after = validate_destination(before, rendered, 'xlsx', checkpoint=checkpoint,
                                     _calc_metric_context=context)
        fidelity = fidelity_report(before.rich_signature, after.rich_signature,
                                   source_kind='ods', target_kind='xlsx',
                                   _calc_metric_context=context)
        qnames = require_stock_qname_bindings(rendered)
        checkpoint()
        # Capture only fixed private evidence after the real terminal verifier;
        # these bytes/digests remain observations, never execution authority.
        evidence = {name: measured.private_read(work / name, 1048576) for name in (
            'ordinary-job.json', 'ordinary-result.json', 'ordinary-inner-result.json',
            'native-trace.json', 'native-terminal-base.json')}
        result = dict(output=rendered, context=context, fidelity=fidelity,
                      metadata_qnames=qnames, evidence=evidence,
                      entered=entered, child_deadline=child_deadline,
                      child_closed=child_closed, parent_deadline=parent_deadline,
                      generation_sha256=generation, production_enabled=False)
        checkpoint()
    finally:
        if unknown:
            raise CleanupUnknown('qualifier_custody_unknown_work_retained', work) from None
        try:
            shutil.rmtree(work)
        except OSError:
            if hasattr(call, 'agent'):
                call.agent._friday_reply_effect_unknown = True
            raise CleanupUnknown('qualifier_work_cleanup_unconfirmed', work) from None
    checkpoint()
    finished = time.monotonic()
    need(finished <= parent_deadline and finished - entered <= 40,
         'qualifier_parent40_final_cleanup_overrun')
    result.update(finished=finished, work_removed=True,
                  runtime_fit='MEASURED_THIS_OPERATION_ONLY', activation=False)
    return result


if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['--inspect']:
        raise SystemExit('Only --inspect is supported; no actor CLI/admission exists.')
    print(json.dumps(inspect_baseline(), indent=2, sort_keys=True))
