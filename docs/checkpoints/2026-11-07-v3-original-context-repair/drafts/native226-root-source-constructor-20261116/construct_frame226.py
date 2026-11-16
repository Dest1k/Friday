"""Finite four-target source-only adaptation of the accepted226 constructor.

prepare_source_plan reads only explicitly pinned CODE/provenance dependencies.
Actual Root envelopes, origins, requests, receipts and closure arrive by value.
render_bound_frame returns virtual cache bytes to Root; it never writes them,
opens a Root-data path, observes current, starts a clock, or grants execution.
"""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import ast
import copy
import hashlib
import json
import os
import stat
import types

B = Path(__file__).parent
BOUNDARY = {'path': '/home/jericho/.cache/FRW-SOL-V3-NATIVE226-FOUR-TARGET-COMPOSITION-CORE-20261116/frame-draft/assemble_source_input226.py', 'sha256': 'b3ca07ba99dce9730e066b4e338519fcbdf06204d673e54381bc2c014a1ff389', 'bytes': 10274}
# Render from the pinned Source draft, independently of this constructor's copy.
D = Path(BOUNDARY['path']).parent
ACTUAL225 = {'path': '/home/jericho/.cache/FRW-SOL-V3-NATIVE226-ROOT-FRAME-SOURCE-CORE-20261116/ACTUAL225-SOURCE-PROJECTION.json', 'sha256': '3badc86a053d4e7116fe316656e357ff54158018ca1df5f386a1cd0688d89b24', 'bytes': 2793}
PREDECESSOR_PRODUCT_COMMIT = '9ad40f35a841e52b78159f7f9397343c8b5495de'
REVIEWED_NATIVE_ROWS = [{'path': 'hermes_cli/friday_workspace_docx.py', 'before_sha256': '289bab471507b7477afc4c95cde7a878199d9e74a1d1c528d80f5d371b985608', 'sha256': '0bc25b322c58c6a1aba5b4db2b6cf108b0b815b886d2e33f3c9cd2d02e881377', 'bytes': 38137, 'mode': '100644', 'new_file': False}, {'path': 'tools/file_tools.py', 'before_sha256': '98c34240d4285bb22d970466043900fa7a0ef8557126e16726e93785d6c0ef9b', 'sha256': 'cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1', 'bytes': 191360, 'mode': '100644', 'new_file': False}, {'path': 'tools/scoped_word_profiles.py', 'before_sha256': 'c2e579cd399fbaa95c68f3c167b7c88e1970c5d3f0f0c309fd96f9d442ad101a', 'sha256': '4718c402bff018cb23544cc7d207755151c9ad93c327646ac1a84db90c34cf68', 'bytes': 25594, 'mode': '100644', 'new_file': False}, {'path': 'tools/scoped_word_stories.py', 'before_sha256': None, 'sha256': 'cf9760ecf984f5477047ad332832bd33a1b85be07c8e9ceca3a861a0ac43dc8f', 'bytes': 14016, 'mode': '100644', 'new_file': True}]
REVIEWED_NATIVE_SOURCE_REFS = {'hermes_cli/friday_workspace_docx.py': {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-FOUR-TARGET-COMPOSITION-20261116/after/hermes_cli/friday_workspace_docx.py', 'sha256': '0bc25b322c58c6a1aba5b4db2b6cf108b0b815b886d2e33f3c9cd2d02e881377', 'bytes': 38137}, 'tools/file_tools.py': {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-FOUR-TARGET-COMPOSITION-20261116/after/tools/file_tools.py', 'sha256': 'cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1', 'bytes': 191360}, 'tools/scoped_word_profiles.py': {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-FOUR-TARGET-COMPOSITION-20261116/after/tools/scoped_word_profiles.py', 'sha256': '4718c402bff018cb23544cc7d207755151c9ad93c327646ac1a84db90c34cf68', 'bytes': 25594}, 'tools/scoped_word_stories.py': {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-FOUR-TARGET-COMPOSITION-20261116/after/tools/scoped_word_stories.py', 'sha256': 'cf9760ecf984f5477047ad332832bd33a1b85be07c8e9ceca3a861a0ac43dc8f', 'bytes': 14016}}
REVIEWED_SOURCE_PAIR = {'manifest': {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-FOUR-TARGET-COMPOSITION-20261116/layer/docx-required-stored-stories-after-source225-manifest.json', 'bytes': 30793, 'sha256': 'b9feea67b18e1762d4b20fcad271ebe12c9457dc022cabde9ca07f3161679f13'}, 'patch': {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX226-FOUR-TARGET-COMPOSITION-20261116/layer/docx-required-stored-stories-after-source225.patch', 'bytes': 18551, 'sha256': 'e41a45304b6876fe62c861c6af0a159eb7b8ad45d30277f658aaf4cf43da6df5'}}
LAYER = 'docx-required-stored-stories-after-source225'
FIXED = {'request', 'private_input', 'public_input', 'before_public_input', 'public_origin', 'public_delta'}
ROLES = {'request', 'intent', 'committed', 'closure', 'input', 'marker', 'receipt', 'stamp'}
# These values match the reviewed actor/current/service consumer literals.
# They describe an unstarted draft. Root must explicitly choose them, or change
# and review every affected consumer before a different future budget is bound.
REVIEWED_FRAME_BUDGETS = dict(operation=2700, forward=1200, external_rollback=300, terminal_cleanup=30, publisher_unit=1530, publisher_client=1560, publisher_CPU=3120, stop_each=45, postcheck=90, cold_gateway=180, cold_dashboard=180, cleanup_reserve=75)
REVIEWED_PYTHON = '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'
_boundary = None


def require(ok, why):
    if not ok:
        raise ValueError(why)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value, size=64):
    return type(value) is str and len(value) == size and all(c in '0123456789abcdef' for c in value)


def absolute(value):
    return type(value) is str and value.startswith('/') and '\\' not in value and str(PurePosixPath(value)) == value and '..' not in PurePosixPath(value).parts


def reference(value):
    require(type(value) is dict and set(value) in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'}) and absolute(value['path']) and digest(value['sha256']) and ('bytes' not in value or type(value['bytes']) is int and value['bytes'] > 0), 'exact_explicit_typed_reference_required')
    return value


def cache_path(value):
    require(absolute(value) and value.startswith('/home/jericho/.cache/') and '/.runtime/' not in value, 'finite_source_cache_path_required')
    path = Path(value)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'source_ancestor_symlink_rejected')
    return path


def source_identity(value):
    return (value.st_dev, value.st_ino, value.st_uid, value.st_gid, value.st_mode,
            value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _read_bounded(value, limit):
    path = cache_path(str(value))
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1 and before.st_size <= limit, 'owned_bounded_singlelink_regular_source')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        require(source_identity(before) == source_identity(os.fstat(stream.fileno())), 'source_changed_before_open')
        raw = stream.read(limit + 1)
        require(source_identity(before) == source_identity(os.fstat(stream.fileno())) == source_identity(path.lstat()), 'source_changed_during_read')
    require(len(raw) == before.st_size and len(raw) <= limit, 'bounded_complete_source_read_required')
    return raw


def read(value):
    """Keep the default metadata/operator/source-reference limit at 16 MiB."""
    return _read_bounded(value, 16 * 1024**2)


def refraw(ref):
    reference(ref)
    raw = read(ref['path'])
    require(sha(raw) == ref['sha256'] and ('bytes' not in ref or len(raw) == ref['bytes']), 'source_ref_changed')
    return raw


def module(name, raw, path):
    ast.parse(raw)
    value = types.ModuleType(name)
    value.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value


def boundary_module(plan=None):
    require(BOUNDARY is not None, 'local226_boundary_not_pinned')
    global _boundary
    if _boundary is None:
        _boundary = module('Source226TypedEnvelopeBoundary', refraw(BOUNDARY), BOUNDARY['path'])
    result = _boundary
    if plan is not None:
        require(result.AFTER_INVENTORY_SHA == {f:sha(encoded(plan.after[f])) for f in ('private','public')}, 'reviewed533_boundary_inventory_join_required')
        require(result.AFTER_HELPER_SHA == {f:plan.after[f]['scripts/friday_ordinary_install.py'] for f in ('private','public')}, 'reviewed533_boundary_helper_join_required')
        pair='patches/hermes/'+LAYER
        require(plan.after['private'][pair+'-manifest.json']==plan.after['public'][pair+'-manifest.json'], 'one_common_manifest_required')
        require(result.MANIFEST_SHA == plan.after['private'][pair+'-manifest.json'] == REVIEWED_SOURCE_PAIR['manifest']['sha256'] and
                result.PATCH_SHA == plan.after['private'][pair+'.patch'] == REVIEWED_SOURCE_PAIR['patch']['sha256'], 'reviewed533_boundary_Root_pair_join_required')
    return result


@dataclass(frozen=True)
class Source226Plan:
    """Authentic CODE maps, source pair and dated metadata; no Root-data body."""
    before: dict
    after: dict
    project_roots: dict
    previous_project_roots: dict
    native_rows: list
    external_callers: dict
    source_metadata: dict
    source_only: bool = True
    current_admission: bool = False
    execution_grant: bool = False


def plan_value(plan):
    require(type(plan) is Source226Plan and plan.source_only is True and plan.current_admission is False and plan.execution_grant is False, 'typed_source_only_plan_required')
    return dict(schema='frw.source226.constructor-authentic-CODE-plan.v1', before=plan.before, after=plan.after, project_roots=plan.project_roots, previous_project_roots=plan.previous_project_roots, native_rows=plan.native_rows, external_callers=plan.external_callers, source_metadata=plan.source_metadata, source_only=True, current_admission=False, execution_grant=False)


def prepare_source_plan(*, before, after, project_roots, previous_project_roots, native_rows, external_callers, source_metadata):
    """Root supplies final independently accepted finite CODE snapshot by value.

    source_metadata.code_snapshots contains exact private/public/previous file,
    mode and frozen identity maps. No final Sol freeze or origin is invented.
    RootSourceAcceptance later binds this exact plan and draft CODE hash map.
    """
    plan = Source226Plan(before, after, project_roots, previous_project_roots,
                         native_rows, external_callers, source_metadata)
    plan_value(plan)
    require(all(type(value) is dict and set(value) == {'private', 'public'}
                for value in (before, after, project_roots, previous_project_roots)) and
            type(source_metadata) is dict and type(external_callers) is dict,
            'exact_private_public_CODE_plan_roles_required')
    require(ACTUAL225 is not None, 'dated_actual225_Source_projection_UNBOUND')
    actual = json.loads(refraw(ACTUAL225))
    require(actual['source_product_commit'] == PREDECESSOR_PRODUCT_COMMIT and
            actual['installed'] == dict(base=17730,layers=225,native=17894,plugins=52,project=531) and
            actual['current_admission'] is False and actual['source_only'] is True and actual['execution_grant'] is False, 'true_dated225_source_projection_required')
    require(source_metadata.get('dated_actual225_projection') == ACTUAL225 and
            source_metadata.get('original225_source_product_commit') == actual['source_product_commit'],
            'Root_final_CODE_plan_true225_origin_required')
    boundary = boundary_module(plan)
    for flavor in ('private','public'):
        boundary.validate_transition(flavor=flavor,before_project_files=before[flavor],after_project_files=after[flavor])
        require(absolute(project_roots[flavor]) and absolute(previous_project_roots[flavor]), 'explicit_CODE_roots_required')
    require(type(native_rows) is list and native_rows == REVIEWED_NATIVE_ROWS,
            'exact_four_reviewed_DOCX_native_rows_required')
    require(len(native_rows) == 4 and len({row['path'] for row in native_rows}) == 4
            and sum(row['new_file'] is False for row in native_rows) == 3
            and sum(row['new_file'] is True for row in native_rows) == 1
            and all(row['before_sha256'] is None if row['new_file'] else digest(row['before_sha256'])
                    for row in native_rows), 'exact_three_modified_one_absent_new_native_required')

    require(set(external_callers) == {'publication/friday_v3_layer_publication.py','publication/build-layer-publication-request.py'}, 'two_explicit_final_Sol_callers_required')
    for r in external_callers.values(): reference(r)
    require(set(source_metadata['code_snapshots']) == {'private','public','previous'}, 'finite_CODE_snapshot_three_roles_required')
    historical=sorted(n for n in before['private'] if before['private'][n] != before['public'][n])
    require(historical == sorted(n for n in after['private'] if after['private'][n] != after['public'][n]) and len(historical)==28, 'retained28_private_public_flavors_required')
    return plan


def selected_project_code(plan):
    """Read exact Root-authenticated final CODE leaves with old32MiB limit.

    This is the nearest CODE binding check, not current or an execution grant.
    No arbitrary path is discovered; each complete inventory/identity/mode map
    must be supplied in the Root-source-accepted plan before this function.
    """
    plan_value(plan); seen=set()
    for flavor in ('private','public','previous'):
        root=cache_path(plan.previous_project_roots['private'] if flavor=='previous' else plan.project_roots[flavor])
        inventory=plan.before['private'] if flavor=='previous' else plan.after[flavor]
        snapshot=plan.source_metadata['code_snapshots'][flavor]
        require(snapshot['tree']==str(root) and snapshot['files']==inventory and set(snapshot['identities'])==set(snapshot['modes'])==set(inventory), 'exact_Root_accepted_CODE_snapshot_required:'+flavor)
        for name,pin in inventory.items():
            require(type(name)is str and name and '\\'not in name and str(PurePosixPath(name))==name and not name.startswith('/') and all(v not in ('','.','..','.git')for v in name.split('/'))and digest(pin), 'safe_finite_CODE_leaf_required')
            frozen=snapshot['identities'][name]
            require(type(frozen)is list and len(frozen)==9 and all(type(v)is int for v in frozen)and 0<frozen[6]<=32*1024**2, 'finite_frozen_CODE_identity_required')
            path=cache_path(str(root/name));before_stat=path.lstat()
            require(source_identity(before_stat)==tuple(frozen)and stat.S_IMODE(before_stat.st_mode)==snapshot['modes'][name], 'CODE_identity_or_mode_changed')
            inode=(before_stat.st_dev,before_stat.st_ino);require(inode not in seen,'CODE_inode_alias_rejected');seen.add(inode)
            raw=_read_bounded(path,32*1024**2)
            require(source_identity(path.lstat())==tuple(frozen)and len(raw)==frozen[6]and sha(raw)==pin,'CODE_bytes_changed:'+flavor+':'+name)
            yield flavor,name,dict(path=str(path),sha256=pin,bytes=len(raw)),raw


@dataclass(frozen=True)
class RootSourceAcceptance:
    """Root's independently authenticated SOURCE decision, never a live grant.

    This pure code verifies pin/plan equality, not the external authority of a
    self-asserted acceptance. Root owns authentication of this trust boundary.
    """
    reference: dict
    source_plan_sha256: str
    reviewed_frame_sha256: dict
    actual225_binding_sha256: object = None
    actual225_closure_authentication_reference: object = None


@dataclass(frozen=True)
class RootEnvelopeInput:
    raw: bytes
    projection: object  # Exact14-field RootEnvelopeProjection, supplied by Root.


@dataclass(frozen=True)
class RootSourceInputs:
    acceptance: RootSourceAcceptance
    private: RootEnvelopeInput
    public: RootEnvelopeInput


def acceptance_checked(plan, acceptance):
    require(type(acceptance) is RootSourceAcceptance, 'Root_source_acceptance_UNBOUND_before_data_parse')
    reference(acceptance.reference)
    require(acceptance.source_plan_sha256 == sha(encoded(plan_value(plan))), 'Root_source_acceptance_wrong_CODE_plan')
    require(type(acceptance.reviewed_frame_sha256) is dict and acceptance.reviewed_frame_sha256 and all(type(n) is str and digest(pin) for n, pin in acceptance.reviewed_frame_sha256.items()), 'Root_reviewed_frame_snapshot_UNBOUND')


def assemble_root_inputs(plan, supplied):
    """Pure bytes-only full14-field assembler; never reads either envelope path."""
    require(type(supplied) is RootSourceInputs, 'Root_private_public_full_envelopes_UNBOUND_before_data_parse')
    acceptance_checked(plan, supplied.acceptance)
    boundary = boundary_module(plan)
    outputs = {}
    for flavor in ('private', 'public'):
        value = getattr(supplied, flavor)
        require(type(value) is RootEnvelopeInput and type(value.projection) is boundary.RootEnvelopeProjection and value.projection.flavor == flavor, 'Root_exact_typed_' + flavor + '_projection_UNBOUND')
        outputs[flavor] = boundary.assemble_source_input(base_envelope_bytes=value.raw, origin=value.projection, before_project_files=plan.before[flavor], after_project_files=plan.after[flavor])
    return outputs


@dataclass(frozen=True)
class SuppliedBytes:
    reference: dict
    raw: bytes


def future_product_origin_ref_checked(product_source_commit, origin_reference):
    """First config barrier: pure Product and explicit new-Origin ref checks.

    A reference passing this check is not an authenticated Git Origin. Only
    Root can authenticate it. No path stat, source read, module or envelope
    parsing is permitted before this initial shape/pin barrier succeeds.
    """
    require(digest(product_source_commit, 40) and
            product_source_commit != PREDECESSOR_PRODUCT_COMMIT,
            'actual_future_distinct226_product_commit_UNBOUND_before_IO')
    reference(origin_reference)
    require('bytes' in origin_reference and origin_reference['bytes'] <= 16 * 1024**2,
            'new_public533_Origin_exact_bytes_reference_UNBOUND_before_IO')


def future_product_origin_checked(product_source_commit, public_origin):
    """First render barrier; validate only Root-supplied Origin bytes in memory.

    This never authenticates a self-asserted Origin and never issues one. The
    later full projection checks every genuine Git blob/mode/full byte join.
    Envelopes, boundary Code and any cache path remain untouched on failure.
    """
    require(digest(product_source_commit, 40) and
            product_source_commit != PREDECESSOR_PRODUCT_COMMIT,
            'actual_future_distinct226_product_commit_UNBOUND_before_IO')
    require(type(public_origin) is SuppliedBytes,
            'new_public533_Origin_Root_typed_bytes_UNBOUND_before_IO')
    future_product_origin_ref_checked(product_source_commit, public_origin.reference)
    raw = public_origin.raw
    require(type(raw) is bytes and 0 < len(raw) <= 16 * 1024**2 and
            len(raw) == public_origin.reference['bytes'] and
            sha(raw) == public_origin.reference['sha256'],
            'new_public533_Origin_Root_typed_bytes_pin_UNBOUND_before_IO')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'new_public533_Origin_duplicate_key')
            value[key] = item
        return value
    try:
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_Origin')))
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise ValueError('new_public533_Origin_Root_bytes_invalid_before_IO') from exc
    require(type(value) is dict and
            value.get('schema') == 'frw.Root.native226.public-origin-committed-project.v1' and
            value.get('commit') == product_source_commit and
            value.get('origin') == 'https://github.com/Dest1k/Friday.git' and
            value.get('branch') == 'main' and value.get('file_count') == 533 and
            absolute(value.get('project')) and
            value.get('only_source_project_no_runtime_or_DB') is True and
            value.get('source_only_not_admission') is True and
            type(value.get('project_files')) is dict and len(value['project_files']) == 533,
            'new_public533_Origin_Product_join_UNBOUND_before_IO')
    return value


def supplied_checked(value):
    require(type(value) is SuppliedBytes, 'typed_Root_supplied_bytes_required')
    reference(value.reference)
    require(type(value.raw) is bytes and 0 < len(value.raw) <= 16 * 1024**2 and sha(value.raw) == value.reference['sha256'] and ('bytes' not in value.reference or len(value.raw) == value.reference['bytes']), 'Root_supplied_raw_pin_or_size_changed')
    cache_path(value.reference['path'])
    return value.raw


def native_after_checked(plan, native_after):
    """Join four named immutable native Source grants to their exact after rows.

    This authenticates supplied Source bytes/pins only; it never observes H or
    claims that a future install/current/Root envelope has been accepted.
    """
    plan_value(plan)
    require(type(plan.native_rows) is list and
            plan.native_rows == REVIEWED_NATIVE_ROWS and
            all(type(row['new_file']) is bool for row in plan.native_rows),
            'exact_four_reviewed_native_Source_rows_required')
    require(type(native_after) is dict and
            set(native_after) == {row['path'] for row in plan.native_rows},
            'exact_four_native_after_sources_required')
    for row in plan.native_rows:
        value = native_after[row['path']]
        require(type(value) is SuppliedBytes and
                value.reference == REVIEWED_NATIVE_SOURCE_REFS[row['path']],
                'exact_Root_reviewed_native_Source_reference:'+row['path'])
        raw = supplied_checked(value)
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'],
                'native_afterimage_changed:'+row['path'])
    return dict(source_only=True, current_admission=False, execution_grant=False,
                native_targets=4, native_modified=3, native_added=1,
                native_after_source_refs=copy.deepcopy(REVIEWED_NATIVE_SOURCE_REFS))


@dataclass(frozen=True)
class RootFrameData:
    inputs: RootSourceInputs
    frame: str
    product_source_commit: str
    fixed: dict  # six SuppliedBytes: request/new private/public/beforepublic/origin/delta.
    actual225_binding: dict  # eight fixed dated pins + Root-authenticated closure/cutoff.
    actual_rows: dict  # eight SuppliedBytes; paths are staged cache, canonical refs remain opaque.
    native_after: dict  # four exact reviewed source afterimage SuppliedBytes.
    frame_sources: dict  # reviewed source bytes by relative filename, incl. inert templates/spec.
    additional_source_bytes: dict  # Root supplies exact immutable addressed closure; no auto-discovery.
    budgets: dict
    python: str
    provenance: dict  # independent product/containing/execution roles; absent remain UNBOUND.


def unbound_requirements():
    return dict(schema='frw.source226.constructor.Root-data-requirements.v1',state='SOURCE_READY_ROOT_DATA_UNBOUND',
        final_CODE='Root independently accepted Sol226 private/public533 trees, frozen identity/mode inventories and two external caller pins; no stale225 frame pin reuse',
        predecessor='Exact authenticated225 eight rows + binding/closure/cutoff; source9ad40,installed225/531/17894/52/17730',
        fixed=sorted(FIXED), source_acceptance='RootSourceAcceptance binds exact plan, draft frame, actual225 binding and closure authentication ref; never current/grant',
        origin='Distinct committed product226 and authentic public Git blob/mode/fullbytes origin + exactdelta; old225 product/execution retained as dated',
        current='UNBOUND_ROOT_SEPARATE_FRESH_LIFECYCLE', budgets='Root explicit new finite reviewed budget map, no old clocks reset',
        input_rule='Preserve genuine private/public225 full nonproject envelopes independently; only project_files changes')


def validate_planned_data_consumer(*, frame, rendered, source_bytes, manifest_raw,
                                   descriptor, static_binding, projection):
    """Run the exact source loader before returning the planned frame bytes.

    All Root data is supplied from the planned source map. The loader retains
    its actual read-only inventory/mode checks on the selected CODE trees.
    This source check never observes current or supplies execution authority.
    """
    out = cache_path(frame)
    virtual_raw = dict(source_bytes)
    manifest_path = str(out/'SOURCE-PINS.json')
    require(manifest_path not in virtual_raw, 'planned_manifest_must_not_self_pin')
    virtual_raw[manifest_path] = manifest_raw
    virtual = module('Bound226DataBeforeOutput', rendered['root226_data.py'], out/'root226_data.py')

    def planned_cache_raw(path):
        path = str(path)
        require(path in virtual_raw and type(virtual_raw[path]) is bytes,
                'constructor_followed_unplanned_source')
        return virtual_raw[path]

    virtual.cache_raw = planned_cache_raw
    consumed = virtual.load(sha(manifest_raw), frame=out)
    require(consumed['descriptor'] == descriptor and
            consumed['static_binding'] == static_binding and
            consumed['projection'] == projection,
            'complete_planned_data_consumer_before_output')
    return consumed


def render_source_text(name, raw, *, frame, substitutions, budgets):
    """Bind finite Source tokens, replacing the longest token names first."""
    text = raw.decode().replace(str(D), str(frame))
    if name.endswith('.py'):
        for key, value in sorted(substitutions.items(), key=lambda item: len(item[0]), reverse=True):
            text = text.replace('UNBOUND_NATIVE226_'+key, value)
        text = text.replace('SOURCE_BOUND = False', 'SOURCE_BOUND = True')
    if name == 'native226_binding.py':
        text = text.replace('BUDGETS = None', 'BUDGETS = '+repr(budgets))
    return text.encode()


def render_bound_frame(plan, data):
    """Future Root-only pure join/render. No write/current/maintenance operation.

    It cannot be called successfully with today's absent Root data. Once real
    data is supplied, all actual225 rows, closure, true v27→v28 history, new
    request/input pairs, exact selected CAS projection and public origin are checked before
    SOURCE_BOUND is rendered true. Root must separately publish/stage these
    virtual bytes, source-accept them, then obtain fresh current/admission.
    """
    require(type(data) is RootFrameData, 'RootFrameData_UNBOUND_before_data_read_or_output')
    # This is deliberately before acceptance, plan, cache paths, boundary Code,
    # refraw/module calls and all private/public operational-envelope parsing.
    # Origin bytes are supplied by value; missing future Root data fails here.
    public_origin = data.fixed.get('public_origin') if type(data.fixed) is dict else None
    future_product_origin_checked(data.product_source_commit, public_origin)
    require(type(data.inputs) is RootSourceInputs and type(data.inputs.acceptance) is RootSourceAcceptance, 'Root_source_acceptance_UNBOUND_before_data_parse')
    acceptance = data.inputs.acceptance
    require(digest(acceptance.actual225_binding_sha256) and acceptance.actual225_binding_sha256 == sha(encoded(data.actual225_binding)), 'Root_trusted_actual225_binding_metadata_UNBOUND_before_data_parse')
    reference(acceptance.actual225_closure_authentication_reference)
    require(data.actual225_binding.get('root_closure_authentication_reference') == acceptance.actual225_closure_authentication_reference, 'Root_trusted_closure_authentication_pin_UNBOUND_before_data_parse')
    assembled = assemble_root_inputs(plan, data.inputs)
    out = cache_path(data.frame)
    require(out.parent == B.parent and out.name.startswith('bound-source-frame226-'), 'future_own_distinct226_frame_required')
    require(data.product_source_commit != plan.source_metadata['original225_source_product_commit'], 'actual_future_distinct226_product_commit_required')
    require(type(data.fixed) is dict and set(data.fixed) == FIXED and type(data.actual_rows) is dict and set(data.actual_rows) == ROLES, 'exact_Root_full_source_and_eight_rows_UNBOUND')
    fixed_raw = {k: supplied_checked(v) for k, v in data.fixed.items()}
    actual_raw = {k: supplied_checked(v) for k, v in data.actual_rows.items()}
    require(fixed_raw['private_input'] == assembled['private'].raw and fixed_raw['public_input'] == assembled['public'].raw and fixed_raw['before_public_input'] == data.inputs.public.raw, 'supplied_fullinputs_must_equal_genuine_full14_assembly')
    require(type(data.frame_sources) is dict and set(data.frame_sources) == set(data.inputs.acceptance.reviewed_frame_sha256) and all(type(raw) is bytes and sha(raw) == data.inputs.acceptance.reviewed_frame_sha256[name] for name, raw in data.frame_sources.items()), 'reviewed_frame_source_changed_or_incomplete')
    require(data.python == REVIEWED_PYTHON and type(data.provenance) is dict, 'explicit_reviewed_Root_python_and_distinct_provenance_required')
    require(data.budgets == REVIEWED_FRAME_BUDGETS, 'Root_future_budget_choice_must_match_reviewed_consumers_or_require_source_delta')
    native_code = data.frame_sources['native226_binding.py']
    native = module('Native226UnboundBudgetCheck', native_code, out/'native226_binding.py')
    native.budget_checked(data.budgets)
    substitutions = dict(REQUEST_SHA=data.fixed['request'].reference['sha256'], INPUT_SHA=data.fixed['private_input'].reference['sha256'], CONSUMER=str(out/'publication/friday_v3_layer_publication.py'), REQUEST=str(out/'ROOT-FRESH-REQUEST.json'), PYTHON=data.python)
    substitutions.update(PRIVATE_HELPER=plan.after['private']['scripts/friday_ordinary_install.py'], PUBLIC_HELPER=plan.after['public']['scripts/friday_ordinary_install.py'],
                         CONSUMER_SHA=sha(data.frame_sources['publication/friday_v3_layer_publication.py']), BUILDER_SHA=sha(data.frame_sources['publication/build-layer-publication-request.py']),
                         MANIFEST_SHA=plan.after['private']['patches/hermes/'+LAYER+'-manifest.json'], PATCH_SHA=plan.after['private']['patches/hermes/'+LAYER+'.patch'], AFTER_MAP_SHA=sha(encoded(plan.after['private'])))
    require(all(digest(substitutions[k]) for k in ('PRIVATE_HELPER','PUBLIC_HELPER','CONSUMER_SHA','BUILDER_SHA','MANIFEST_SHA','PATCH_SHA','AFTER_MAP_SHA')), 'final_Sol226_CODE_controls_UNBOUND')
    require(all(sha(data.frame_sources[k])==plan.external_callers[k]['sha256'] for k in plan.external_callers), 'final_external_callers_plan_join_required')

    rendered = {}
    for name, raw in data.frame_sources.items():
        require(type(name) is str and name and not name.startswith('/') and '..' not in PurePosixPath(name).parts, 'safe_frame_relative_required')
        rendered[name] = render_source_text(name, raw, frame=out,
            substitutions=substitutions, budgets=data.budgets)
    spec_value=json.loads(rendered['SOURCE-SPEC226.json'])
    for role,suffix in (('manifest','-manifest.json'),('patch','.patch')):
        path=Path(plan.project_roots['private'])/('patches/hermes/'+LAYER+suffix)
        raw=refraw(dict(path=str(path),sha256=plan.after['private']['patches/hermes/'+LAYER+suffix]))
        spec_value[role]=dict(path=str(path),bytes=len(raw),sha256=sha(raw))
    spec_value['native_files']=copy.deepcopy(plan.native_rows)
    rendered['SOURCE-SPEC226.json']=encoded(spec_value)
    predecessor = module('ExactActual225Supplied', rendered['predecessor225.py'], out/'predecessor225.py').validate_actual225(data.actual225_binding, actual_raw)
    # Bind only already authenticated, immutable selectors. Fresh current,
    # authority, admission and the execution clock remain separate Root work.
    future = json.loads(rendered['ROOT-FUTURE-COMMANDS.json'])
    future.update(commands=dict(builder=[data.python]),
                  command_prefix_only=True,
                  interpreter_prefix_scope='Reviewed product interpreter only; not a runnable builder command.',
                  no_actual226_request_or_origin_issued=False,
                  state='ROOT_SOURCE_BOUND_INTERPRETER_PREFIX_NO_COMMAND_EXECUTED')
    rendered['ROOT-FUTURE-COMMANDS.json'] = encoded(future)
    snapshot = json.loads(rendered['ROOT-226-FRESH-READBACK-TEMPLATE.json'])
    snapshot.update(installed_receipt_sha256=predecessor['authenticated_row_sha256']['receipt'],
                    installed_input_sha256=predecessor['current_input']['sha256'])
    rendered['ROOT-226-FRESH-READBACK-TEMPLATE.json'] = encoded(snapshot)
    anchor = json.loads(rendered['ROOT-226-CURRENT-SERVICE-ANCHOR-TEMPLATE.json'])
    anchor['installed'].update(receipt_sha256=predecessor['authenticated_row_sha256']['receipt'],
                               input_sha256=predecessor['current_input']['sha256'])
    rendered['ROOT-226-CURRENT-SERVICE-ANCHOR-TEMPLATE.json'] = encoded(anchor)
    for role in ROLES:
        r = data.actual225_binding[role]
        require(data.actual_rows[role].reference == dict(path=r['cache_path'], sha256=r['sha256'], bytes=r['bytes']), 'actual225_staged_row_reference_join:'+role)
    native = module('Bound226Native', rendered['native226_binding.py'], out/'native226_binding.py')
    spec = json.loads(rendered['SOURCE-SPEC226.json'])
    manifest_raw = refraw(spec['manifest'])
    patch_raw = refraw(spec['patch'])
    static = native.bind_static(request_raw=fixed_raw['request'], input_raw=fixed_raw['private_input'], manifest_raw=manifest_raw, patch_raw=patch_raw, predecessor_six=predecessor, actual_rows=actual_raw)
    rendered['native226_binding.py'] = rendered['native226_binding.py'].replace(b'UNBOUND_NATIVE226_STATIC_BINDING_SHA256', sha(encoded(static)).encode())
    history=json.loads(rendered['ROOT-226-CONSUMED-HISTORY-TEMPLATE.json'])
    history['actual225_binding']['sha256']=sha(encoded(data.actual225_binding))
    rendered['ROOT-226-CONSUMED-HISTORY-TEMPLATE.json']=encoded(history)
    fresh=json.loads(rendered['ROOT-226-FRESH-ADMISSION-TEMPLATE.json'])
    for key,name in (('actor','run_native226_once.py'),('recovery','resume_native226_services.py'),('consumed_history','ROOT-226-CONSUMED-HISTORY-TEMPLATE.json')):
        fresh[key]['sha256']=sha(rendered[name])
    fresh['expected_receipt_sha256']=static['prospective_receipt_sha256']
    rendered['ROOT-226-FRESH-ADMISSION-TEMPLATE.json']=encoded(fresh)
    authority=json.loads(rendered['ROOT-226-RUNTIME-AUTHORITY-TEMPLATE.json'])
    for key in ('boundary','caller'):authority[key]['sha256']=sha(rendered['core226-first-actual-root.py'])
    authority['native_pins']={row['path']:row['sha256']for row in plan.native_rows}
    authority['actual225_predecessor']['sha256']=sha(encoded(data.actual225_binding))
    authority['consumed_history']['sha256']=sha(rendered['ROOT-226-CONSUMED-HISTORY-TEMPLATE.json'])
    rendered['ROOT-226-RUNTIME-AUTHORITY-TEMPLATE.json']=encoded(authority)
    qualifier=json.loads(rendered['ROOT-226-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json'])
    qualifier['operational_input']={k:data.fixed['private_input'].reference[k]for k in ('path','sha256')}
    qualifier['native_spec']=dict(path=str(out/'SOURCE-SPEC226.json'),sha256=sha(rendered['SOURCE-SPEC226.json']))
    rendered['ROOT-226-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json']=encoded(qualifier)
    # Rebind static source refs only; missing authority/current refs stay UNBOUND.
    local_static={'ACTUAL225-EIGHT-ROW-BINDING.json':encoded(data.actual225_binding),'ROOT-FRESH-REQUEST.json':fixed_raw['request']}
    def bind_static_refs(value):
        if type(value)is dict:
            result={k:bind_static_refs(v)for k,v in value.items()}
            path=result.get('path')
            if type(path)is str and path.startswith(str(out)+'/'):
                relative=path[len(str(out))+1:]
                raw=local_static.get(relative,rendered.get(relative))
                if raw is not None and 'sha256'in result:result['sha256']=sha(raw)
            return result
        if type(value)is list:return [bind_static_refs(v)for v in value]
        return value
    for name,raw in list(rendered.items()):
        if name.endswith('-TEMPLATE.json'):rendered[name]=encoded(bind_static_refs(json.loads(raw)))
    native_after_checked(plan, data.native_after)
    values = {k: json.loads(raw) for k, raw in fixed_raw.items()}
    require(values['request']['candidate_project'] == plan.project_roots['private'] and values['public_origin']['project'] == plan.project_roots['public'] and values['public_origin']['commit'] == data.product_source_commit, 'actual_future_origin_roots_commit_join')
    project_sources, project_bytes, project_modes, sources = {}, {}, {}, {}
    def add(path, raw):
        path = str(path)
        require(path not in sources or sources[path] == raw, 'conflicting_source_path_bytes')
        sources[path] = raw
    for flavor in ('private', 'public', 'previous'):
        project_sources[flavor] = {}
        if flavor != 'previous':
            project_bytes[flavor], project_modes[flavor] = {}, {}
    for flavor, name, ref, raw in selected_project_code(plan):
        project_sources[flavor][name] = ref
        add(ref['path'], raw)
        if flavor != 'previous':
            project_bytes[flavor][name] = raw
            project_modes[flavor][name] = '100755' if Path(ref['path']).lstat().st_mode & 0o111 else '100644'
    projection = module('Bound226SourceProjection', rendered['root226_projection.py'], out/'root226_projection.py').validate(predecessor=predecessor, static_binding=static, request=values['request'], private_input=values['private_input'], public_input=values['public_input'], before_public_input=values['before_public_input'], public_origin=values['public_origin'], public_delta=values['public_delta'], spec=spec, project_bytes=project_bytes, project_modes=project_modes, product_source_commit=data.product_source_commit)
    clean = lambda ref: {k: ref[k] for k in ('path', 'sha256')}
    fixed = {k: clean(value.reference) for k, value in data.fixed.items()}
    local = {'STATIC-BINDING226.json': encoded(static), 'ACTUAL225-EIGHT-ROW-BINDING.json': encoded(data.actual225_binding), 'ROOT-FRESH-REQUEST.json': fixed_raw['request']}
    for key, name in (('native_spec', 'SOURCE-SPEC226.json'), ('static_binding', 'STATIC-BINDING226.json'), ('actual225_binding', 'ACTUAL225-EIGHT-ROW-BINDING.json')):
        fixed[key] = dict(path=str(out/name), sha256=sha(rendered[name] if name in rendered else local[name]))
    descriptor = dict(schema='frw.root226.typed-origin-source-descriptor.v1', source_only=True, execution_grant=False, current_admission=False, future_root_authority=dict(source_acceptance='UNBOUND_ROOT', current='UNBOUND_ROOT', once='UNBOUND_ROOT', grant='UNBOUND_ROOT', clock='UNBOUND_ROOT'), project_roots={**plan.project_roots, 'previous': plan.previous_project_roots['private']}, dependencies={name: dict(path=str(out/(name+'.py')), sha256=sha(rendered[name+'.py']), bytes=len(rendered[name+'.py'])) for name in ('predecessor225', 'native226_binding')}, fixed=fixed, actual_rows={k: v.reference for k, v in data.actual_rows.items()}, project_sources=project_sources, native_after={k: v.reference for k, v in data.native_after.items()})
    local['ROOT226-DATA-BINDINGS.json'] = encoded(descriptor)
    for value in (*data.fixed.values(), *data.actual_rows.values(), *data.native_after.values()):
        add(value.reference['path'], value.raw)
    require(type(data.additional_source_bytes) is dict, 'explicit_finite_immutable_source_closure_required')
    for path, raw in data.additional_source_bytes.items():
        cache_path(path)
        require(type(raw) is bytes and len(raw) <= 16 * 1024**2, 'bounded_additional_source_bytes_required')
        add(path, raw)
    for name, raw in {**rendered, **local}.items():
        if name.endswith('.py'):
            ast.parse(raw)
            require(b'UNBOUND_NATIVE226_' not in raw, 'unbound_final_executable_source:'+name)
        add(out/name, raw)
    producer = module('Bound226SourcePins', rendered['source_pins_producer.py'], out/'source_pins_producer.py')
    pins = producer.assemble(frame=str(out), source_bytes=sources, historical_bytes={}, source_spec_ref=fixed['native_spec'], product_source_commit=data.product_source_commit, **data.provenance)
    local['SOURCE-PINS.json'] = encoded(pins)
    validate_planned_data_consumer(frame=str(out), rendered=rendered, source_bytes=sources,
                                   manifest_raw=local['SOURCE-PINS.json'], descriptor=descriptor,
                                   static_binding=static, projection=projection)
    return dict(schema='frw.source226.virtual-bound-frame-assembly.v1', source_only=True, current_admission=False, execution_grant=False, output_bytes={**rendered, **local}, descriptor=descriptor, source_pins=pins, static_binding=static, projection=projection, actual_fullinput_consumer_accepted=False, maintenance_started=False, future_current='UNBOUND_ROOT_SEPARATE_FRESH_LIFECYCLE')
