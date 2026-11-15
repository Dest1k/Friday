"""Fixed installed ordinary Calc asset index reader; no runtime admission.

The factory supplies a digest pinned by reviewed installed SOURCE. Neither an
index nor this reader creates Office/GDB authority, operation facts, or a launch.
Builder tooling lives separately and is never invoked by the ordinary renderer.
"""
from pathlib import Path
import hashlib
import json
import os
import stat

from hermes_cli import friday_workspace_calc_native_layout as layout

INDEX_NAME = 'index.json'
ENTRY_NAME = 'ordinary_entry.py'
HOST_PIN = 'hermes_cli/friday_workspace_calc_native_pin.py'
DIRECTORY_NAME = '_calc_native_assets'
SCHEMA = 'frw.calc.native-code-generation.v1'
INDEX_LIMIT = 262144


class AssetsRefused(ValueError):
    pass


def need(value, reason):
    if not value:
        raise AssetsRefused(reason)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'native_assets_duplicate_json_key')
            result[key] = value
        return result
    def nonfinite(_):
        raise AssetsRefused('native_assets_nonfinite_json')
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, UnicodeError, TypeError) as error:
        if isinstance(error, AssetsRefused):
            raise
        raise AssetsRefused('native_assets_json') from None


def _rows(raw):
    data = decode(raw)
    need(type(data) is dict and set(data) == {'schema', 'entry', 'files'}
         and data['schema'] == SCHEMA, 'native_assets_index_schema')
    need(canonical(data) == raw, 'native_assets_index_noncanonical')
    entry = str(layout.safe_relative(data['entry']))
    need(entry == ENTRY_NAME, 'native_assets_fixed_ordinary_entry')
    files = data['files']
    need(type(files) is list and 0 < len(files) <= layout.MAX_ASSETS,
         'native_assets_index_count')
    seen = set()
    rows = []
    for item in files:
        need(type(item) is dict and set(item) == {'relative', 'sha256'},
             'native_assets_row_schema')
        relative = str(layout.safe_relative(item['relative']))
        digest = item['sha256']
        need(relative not in (INDEX_NAME, HOST_PIN) and relative not in seen,
             'native_assets_duplicate_or_index_member')
        need(type(digest) is str and len(digest) == 64
             and all(c in '0123456789abcdef' for c in digest),
             'native_assets_digest_shape')
        seen.add(relative)
        rows.append((relative, digest))
    need(rows == sorted(rows) and entry in seen, 'native_assets_order_or_entry')
    # No member may also be a directory containing another member.
    need(not any(str(parent) in seen for rel in seen
                 for parent in Path(rel).parents if str(parent) != '.'),
         'native_assets_file_directory_collision')
    return entry, tuple(rows)


def _tree(root, rows):
    expected_files = {relative for relative, _ in rows} | {INDEX_NAME}
    expected_dirs = set()
    for relative in expected_files:
        parts = Path(relative).parts
        expected_dirs.update(str(Path(*parts[:i])) for i in range(1, len(parts)))
    actual_files, actual_dirs = set(), set()
    stamps = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        layout.private_directory(directory)
        before = layout.stamp(directory.lstat())
        stamps[directory] = before
        with os.scandir(directory) as entries:
            for item in entries:
                path = directory / item.name
                relative = str(path.relative_to(root))
                info = item.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    need(relative in expected_dirs, 'native_assets_extra_directory')
                    actual_dirs.add(relative)
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    need(relative in expected_files, 'native_assets_extra_file')
                    actual_files.add(relative)
                else:
                    raise AssetsRefused('native_assets_symlink_or_special')
        need(layout.stamp(directory.lstat()) == before, 'native_assets_tree_race')
    need(actual_files == expected_files and actual_dirs == expected_dirs,
         'native_assets_missing_member')
    for directory, before in stamps.items():
        need(layout.stamp(directory.lstat()) == before, 'native_assets_tree_race')
    return stamps


def validate_generation(index_path, expected_index_sha256, *, counterparts=()):
    """Validate a pinned complete installed tree without executing any asset.

    `counterparts` are exact installed source copies required by the fixed host
    consumer; digests come from the already pinned index, never from those files.
    The index remains the exact existing commonlayoutR2 stage_code schema.
    """
    index = layout.exact_path(index_path)
    need(index.name == INDEX_NAME, 'native_assets_index_name')
    root = layout.private_directory(index.parent)
    raw = layout.read_exact_file(index, expected_index_sha256, limit=INDEX_LIMIT)
    entry, rows = _rows(raw)
    stamps = _tree(root, rows)
    total = 0
    for relative, digest in rows:
        total += len(layout.read_exact_file(root / relative, digest))
        need(total <= layout.MAX_ASSET_BYTES, 'native_assets_total_bytes')
    known = dict(rows)
    seen = set()
    for relative, installed in counterparts:
        relative = str(layout.safe_relative(relative))
        need(relative in known and relative not in seen,
             'native_assets_counterpart_membership')
        seen.add(relative)
        layout.read_exact_file(installed, known[relative])
    for directory, before in stamps.items():
        need(layout.stamp(directory.lstat()) == before, 'native_assets_tree_race')
    need(layout.read_exact_file(index, expected_index_sha256, limit=INDEX_LIMIT) == raw,
         'native_assets_index_race')
    return entry, rows


def installed_index(factory_file, expected_index_sha256):
    """Resolve only the generation next to the real installed factory SOURCE.

    Every indexed hermes_cli SOURCE must have the identical installed counterpart;
    no old grant, plan, user path, cache search, or environment fallback is used.
    The fixed factory passes __file__ and its fixed reviewed index digest.
    """
    factory = layout.exact_path(factory_file)
    need(factory.name == 'friday_workspace_calc_native_factory.py',
         'native_assets_factory_name')
    root = layout.private_directory(factory.parent / DIRECTORY_NAME)
    index = root / INDEX_NAME
    # First parse still uses the installed digest. No asset is loaded/imported.
    raw = layout.read_exact_file(index, expected_index_sha256, limit=INDEX_LIMIT)
    _, rows = _rows(raw)
    counterparts = tuple((relative, factory.parent / Path(relative).relative_to('hermes_cli'))
                         for relative, _ in rows
                         if Path(relative).parts[0] == 'hermes_cli')
    validate_generation(index, expected_index_sha256, counterparts=counterparts)
    return index


def stage_installed(work, factory_file, expected_index_sha256):
    """Validate installed exacttree/counterparts, then use accepted stage_code."""
    index = installed_index(factory_file, expected_index_sha256)
    staged = layout.stage_code(work, index, expected_index_sha256)
    # Whole prepared generation is checked before it reaches namespace_argv.
    layout.exact_generation_tree(staged)
    return staged
