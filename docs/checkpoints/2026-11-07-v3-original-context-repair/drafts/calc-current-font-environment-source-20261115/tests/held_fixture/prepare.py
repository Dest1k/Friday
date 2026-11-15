"""OwnC compile/static binding only. Never launches GDB or the resulting ELF.

Repeat preparation after parent candidate stability to refresh exact pins.
Outputs stay inside this explicitly owned fixture directory.
"""
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess

BASE = Path(__file__).resolve().parent
CANDIDATE = BASE.parent.parent / 'candidate'
DEPS = CANDIDATE / 'outer/deps'
VARIANTS = {
    'baseline': [],
    'after_load_font_change': ['-DFIXTURE_AFTER_LOAD_FONT_CHANGE'],
    'after_close_font_change': ['-DFIXTURE_AFTER_CLOSE_FONT_CHANGE'],
}
MARKERS = ('fixture_ready', 'fixture_paper_done', 'fixture_after_load', 'fixture_query_marker',
           'fixture_restore_marker', 'fixture_close_marker', 'fixture_after_close')


def file_ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def put(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(raw)
    path.chmod(0o600)
    return file_ref(path)


def elf_reader(path):
    raw = path.read_bytes()
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    assert raw[:6] == b'\x7fELF\x02\x01' and h[1] == 3 and h[2] == 62
    loads = []
    for i in range(h[10]):
        kind, _flags, off, va, _pa, size, _mem, _align = struct.unpack_from('<IIQQQQQQ', raw, h[5] + i * h[9])
        if kind == 1:
            loads.append((off, va, size))
    def get(va, length):
        matches = [off + va - start for off, start, size in loads if start <= va and va + length <= start + size]
        assert len(matches) == 1
        return raw[matches[0]:matches[0] + length]
    return get


def functions_ref(path, names):
    raw = path.read_text()
    tree = ast.parse(raw, filename=str(path))
    nodes = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    result = {}
    for name in names:
        node = nodes[name]
        text = ast.get_source_segment(raw, node).encode()
        result[name] = dict(line=node.lineno, sha256=hashlib.sha256(text).hexdigest())
    return result


def prepare(variant):
    assert variant in VARIANTS and BASE.is_dir() and BASE.stat().st_mode & 0o777 == 0o700
    os.umask(0o077)
    out = BASE / 'prepared' / variant
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = out / 'held_fixture'
    command = ['/usr/bin/cc', '-O0', '-g', '-fno-omit-frame-pointer', '-fPIE', '-pie', '-Wl,-z,now',
               '-Wall', '-Wextra', '-Werror', *VARIANTS[variant], '-o', str(target), str(BASE / 'held_fixture.c')]
    compiled = subprocess.run(command, check=True, capture_output=True, text=True)
    target.chmod(0o700)
    symbols = {}
    for line in subprocess.check_output(['/usr/bin/nm', '-S', str(target)], text=True).splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[3] in (*MARKERS, 'paper_load_fixture'):
            symbols[fields[3]] = (int(fields[0], 16), int(fields[1], 16))
    assert set(symbols) == {*MARKERS, 'paper_load_fixture'} and all(size > 0 for _offset, size in symbols.values())
    get = elf_reader(target)
    disassembly = subprocess.check_output(['/usr/bin/objdump', '-d', '--disassemble=paper_load_fixture', str(target)], text=True)
    sites = {}
    for name in ('popen', 'fgets', 'pclose'):
        rows = [line for line in disassembly.splitlines() if re.search(r'call\s+.*<' + name + r'@plt>', line)]
        assert len(rows) == 1
        fields = rows[0].split('\t')
        offset = int(fields[0].strip().rstrip(':'), 16) + len(bytes.fromhex(fields[1]))
        sites[name + '_return'] = dict(offset=offset, before=get(offset - 5, 5).hex(), after=get(offset, 8).hex())
    manifest = copy.deepcopy(json.loads((DEPS / 'PAPER-HELPER-OFFICE-MANIFEST.json').read_text()))
    manifest.update(kind='OWN_POPEN_FIXTURE_ONLY', source_sha256=file_ref(BASE / 'held_fixture.c')['sha256'])
    manifest['caller'] = dict(file_ref(target), function_offset=symbols['paper_load_fixture'][0],
                              function_size=symbols['paper_load_fixture'][1], sites=sites)
    manifest_ref = put(out / 'fixture-manifest.json', manifest)
    native = DEPS / 'native_return_observer.py'
    namespace = CANDIDATE / 'outer/namespace_entry.py'
    for name in ('held_fixture_gdb.py', 'held_fixture_supervisor.py', 'prepare.py'):
        compile((BASE / name).read_bytes(), str(BASE / name), 'exec')  # Syntax only; never exec.
    static = dict(schema='frw.own-held-font-fixture-static.v1', compile_argv=command,
        compiler_ref=file_ref(Path('/usr/bin/cc')), compile_stdout=compiled.stdout, compile_stderr=compiled.stderr,
        compile_exit_code=compiled.returncode, elf_class='ELF64_LE_X86_64_ET_DYN', symbols=symbols,
        call_site_bindings=sites, marker_entry_bytes={name: get(symbols[name][0], min(symbols[name][1], 16)).hex() for name in MARKERS},
        readelf_dynamic=subprocess.check_output(['/usr/bin/readelf', '-d', str(target)], text=True),
        getter_not_copied=True, handshake_not_copied=True, runtime_executed=False)
    static_ref = put(out / 'STATIC.json', static)
    expected = None if variant == 'baseline' else dict(
        boundary='AFTER_LOAD_BEFORE_QUERY' if variant == 'after_load_font_change' else 'AFTER_READONLY_CLOSE',
        code='font_runtime_projection_changed', proof_expected=True, release_expected=False, accepted_expected=False)
    prepared = dict(schema='frw.own-held-font-fixture-prepared.v1', kind='OWN_POPEN_FIXTURE_ONLY',
        variant=variant, source_ref=file_ref(BASE / 'held_fixture.c'), target_ref=file_ref(target),
        manifest_ref=manifest_ref, adapter_ref=file_ref(DEPS / 'paper_helper_gdb.py'),
        policy_ref=file_ref(DEPS / 'paper_helper_policy.py'), native_observer_ref=file_ref(native),
        namespace_ref=file_ref(namespace), gdb_driver_ref=file_ref(BASE / 'held_fixture_gdb.py'),
        supervisor_ref=file_ref(BASE / 'held_fixture_supervisor.py'), prepare_ref=file_ref(BASE / 'prepare.py'),
        static_ref=static_ref, marker_offsets={name: symbols[name][0] for name in MARKERS},
        source_functions=functions_ref(native, ('font_file', 'font_read', 'font_write', 'capture_font_runtime', 'stopped')),
        namespace_functions=functions_ref(namespace, ('LocalServices', 'validate_font_runtime_proof', 'validate_font_runtime_pair')),
        runtime_template=dict(operation_id='REPLACE_BY_ROOT', nonce='REPLACE_BY_ROOT',
            source_sha256=manifest['source_sha256'], manifest_ref=manifest_ref,
            marker_path='/tmp/friday-metric-work/load-dependency.json', operation_deadline_monotonic=None),
        expected_status='COMPLETE_TWO_HELD_POINTS_FIXTURE_ONLY' if expected is None else
            'EXPECTED_PROJECTION_REFUSAL_REQUIRES_ROOT_CGROUP_CLEANUP', expected_refusal=expected,
        preparation_only=True, runtime_executed=False, actual_M=None, runtime_attested=False,
        source_pins_status='AT_PREPARATION_REFRESH_AFTER_PARENT_STABILITY',
        observation_scope='TWO_REQUESTED_ALL_STOP_POINTS_ONLY_NOT_CONTINUOUS_ENVIRONMENT',
        fixture_limitations=['FIXTURE_MARKER_ONLY_RECORDS_0_AND_10', 'NO_NATIVE_RANGE_PROOF',
            'NO_ACTUAL_M', 'NO_OFFICE_UNO', 'NO_ACTUAL_RESTORATION', 'NO_CANONICAL_EFFECTIVE_FONT_CAS'])
    return put(out / 'PREPARED.json', prepared)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--variant', choices=tuple(VARIANTS))
    args = parser.parse_args()
    if args.all:
        print(json.dumps({variant: prepare(variant) for variant in VARIANTS}, sort_keys=True))
    elif args.variant:
        print(json.dumps(prepare(args.variant), sort_keys=True))
    else:
        print(json.dumps(dict(status='SOURCE_ONLY_NO_COMPILE_NO_EXECUTION')))
