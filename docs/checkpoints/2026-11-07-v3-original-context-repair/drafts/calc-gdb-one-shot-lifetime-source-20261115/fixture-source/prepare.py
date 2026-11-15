"""Own source/compile/ELF preparation only; never execute the emitted ELFs or helpers."""
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import struct
import subprocess
import time

BASE = Path('/home/jericho/.cache/FRW-ASTRA-GDB-RETIRED-CHILD-BP-SOLIB-FIXTURE-20261115')
F = Path('/home/jericho/.cache/FRW-ASTRA-CALC-CURRENT-FONT-ENV-BOUNDARY-SOURCE-20261115')
D = Path('/home/jericho/.cache/FRW-ASTRA-CALC-ACTIVE-PUBLICATION-READER-DELTA-20261115')
G = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GDB-OFFICE-CORE-DIAGNOSIS-20261115')
DEPS = D / 'candidate/outer/deps'
MARKERS = ('fixture_ready', 'fixture_paper_done', 'fixture_after_load', 'fixture_query_marker',
           'fixture_restore_marker', 'fixture_close_marker', 'fixture_after_close')
EXTRA = ('fixture_solib_before', 'fixture_solib_loaded', 'fixture_solib_after')
VARIANTS = {'postclose_solib': [], 'worker_postclose_solib': ['-DFIXTURE_WORKER_THREAD', '-pthread']}
PINS = {
    F / 'tests/held_fixture/held_fixture.c': '4234c407b4ec319b5b9e3cd65e8070bdb41762e4c2f5449188eb08ec2ac6bc73',
    F / 'tests/held_fixture/held_fixture_gdb.py': 'e6163f921bdc8db702cdbcc0cccd8f527ee981576388fd59df68b3d94221c5a7',
    D / 'fixture-source/held_fixture_supervisor.py': 'f665b9ac00d022694cf5d2494419d8f26775677ad00a5775755297073b28ee3d',
    D / 'candidate/outer/namespace_entry.py': '43dff62706d65eb92455855473177122353ac4d9df4f35d3a1485cc1d666efb3',
    DEPS / 'native_return_observer.py': '4eb25d42b9487b151d9014771d25b2eb19878410c58d748aa19b0187c9c9fd29',
    DEPS / 'paper_helper_policy.py': 'd4cb74cd814fa78eeaeb249f9b2d6177f506dc881458f287cb372191b2a4ec61',
    DEPS / 'paper_helper_gdb.py': '3f4f28f7e11fbe9e7808e6a012164964f27096c90d62e99c69cc329111b0ebeb',
    G / 'candidate/paper_helper_gdb.py': '6c7f293cb7636b34f747143b797f9e6601d96d83ff5e49a752446bbfff334b10',
}


def ref(path):
    path = Path(path)
    assert path.is_absolute() and path.resolve() == path
    s = path.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_uid in (0, os.getuid()) and not s.st_mode & 0o022
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write(path, value):
    assert path.is_relative_to(BASE)
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(raw)
    return ref(path)


def limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


def command(argv):
    assert argv[0] in ('/usr/bin/cc', '/usr/bin/nm', '/usr/bin/objdump', '/usr/bin/readelf')
    p = subprocess.run(argv, check=True, capture_output=True, text=True, timeout=15, preexec_fn=limits)
    assert len(p.stdout) + len(p.stderr) < 262144
    return p.stdout


def elf_read(path):
    raw = path.read_bytes()
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    assert raw[:6] == b'\x7fELF\x02\x01' and h[1] == 3 and h[2] == 62
    loads = []
    for i in range(h[10]):
        kind, flags, off, va, pa, size, mem, align = struct.unpack_from('<IIQQQQQQ', raw, h[5] + i * h[9])
        if kind == 1:
            loads.append((off, va, size))
    def get(va, size):
        match = [off + va - start for off, start, length in loads if start <= va and va + size <= start + length]
        assert len(match) == 1
        return raw[match[0]:match[0] + size]
    return get


def functions(path, names):
    raw = path.read_text()
    tree = ast.parse(raw, filename=str(path))
    nodes = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    return {n: {'line': nodes[n].lineno, 'sha256': hashlib.sha256(ast.get_source_segment(raw, nodes[n]).encode()).hexdigest()}
            for n in names}


def c_paper(raw):
    return raw[raw.index('MARKER int paper_load_fixture'):raw.index('\nstatic double monotonic_now')]


def main():
    os.umask(0o077)
    start = time.monotonic()
    assert BASE.resolve() == BASE and BASE.stat().st_mode & 0o777 == 0o700
    for path, expected in PINS.items():
        assert ref(path)['sha256'] == expected, str(path)
    for path in [BASE / 'prepare.py', F / 'tests/held_fixture/held_fixture_gdb.py',
                 D / 'fixture-source/held_fixture_supervisor.py', G / 'candidate/paper_helper_gdb.py']:
        compile(path.read_bytes(), str(path), 'exec')  # Syntax only, no exec/import.
    source = BASE / 'held_fixture.c'
    old = F / 'tests/held_fixture/held_fixture.c'
    assert c_paper(source.read_text()) == c_paper(old.read_text())
    (BASE / 'held-fixture-source.patch').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True), source.read_text().splitlines(True), fromfile=str(old), tofile=str(source))))
    trigger = BASE / 'trigger/frw_own_retired_bp_trigger.so'
    dso_argv = ['/usr/bin/cc', '-O0', '-g', '-fPIC', '-fno-stack-protector', '-shared', '-nostdlib',
                '-Wl,-z,now,-z,relro,-z,noexecstack,--no-undefined,-soname,frw_own_retired_bp_trigger.so',
                '-Wall', '-Wextra', '-Werror', '-o', str(trigger), str(BASE / 'trigger/trigger.c')]
    command(dso_argv)
    trigger.chmod(0o600)
    dso_dynamic = command(['/usr/bin/readelf', '-d', str(trigger)])
    dso_symbols = command(['/usr/bin/nm', '-D', str(trigger)])
    assert '(NEEDED)' not in dso_dynamic and '(INIT)' not in dso_dynamic and '(FINI)' not in dso_dynamic
    assert '(INIT_ARRAY)' not in dso_dynamic and '(FINI_ARRAY)' not in dso_dynamic
    assert len(dso_symbols.splitlines()) == 1 and ' T frw_fixture_solib_probe' in dso_symbols
    trigger_static = write(BASE / 'trigger/STATIC.json', {
        'schema': 'frw.own-retired-child-bp-trigger-static.v1', 'source_ref': ref(BASE / 'trigger/trigger.c'),
        'target_ref': ref(trigger), 'compile_argv': dso_argv, 'readelf_dynamic': dso_dynamic,
        'readelf_program_headers': command(['/usr/bin/readelf', '-l', str(trigger)]),
        'nm_dynamic': dso_symbols,
        'disassembly': command(['/usr/bin/objdump', '-d', '--disassemble=frw_fixture_solib_probe', str(trigger)]),
        'needed': [], 'constructors': False, 'destructors': False, 'runtime_executed': False})
    old_prepared = json.loads((D / 'PREPARED-after_close_font_change.json').read_text())
    baseline_manifest = json.loads(Path(old_prepared['manifest_ref']['path']).read_text())
    outrefs = {}
    for variant, flags in VARIANTS.items():
        out = BASE / 'prepared' / variant
        out.mkdir(mode=0o700, parents=True)
        target = out / 'held_fixture'
        argv = ['/usr/bin/cc', '-O0', '-g', '-fno-omit-frame-pointer', '-fPIE', '-pie', '-Wl,-z,now,-z,relro,-z,noexecstack',
                '-Wall', '-Wextra', '-Werror', *flags, '-o', str(target), str(source), '-ldl']
        command(argv)
        target.chmod(0o700)
        nm = command(['/usr/bin/nm', '-S', str(target)])
        symbols = {}
        for row in nm.splitlines():
            f = row.split()
            if len(f) == 4 and f[2].lower() == 't':
                symbols[f[3]] = [int(f[0], 16), int(f[1], 16)]
        assert all(n in symbols and symbols[n][1] > 0 for n in (*MARKERS, *EXTRA, 'paper_load_fixture', 'fixture_late_solib', 'run_fixture'))
        get = elf_read(target)
        dis = command(['/usr/bin/objdump', '-d', str(target)])
        paper_dis = command(['/usr/bin/objdump', '-d', '--disassemble=paper_load_fixture', str(target)])
        sites = {}
        for name in ('popen', 'fgets', 'pclose'):
            rows = [r for r in paper_dis.splitlines() if re.search(r'call\s+.*<' + name + '@plt>', r)]
            assert len(rows) == 1
            f = rows[0].split('\t')
            offset = int(f[0].strip().rstrip(':'), 16) + len(bytes.fromhex(f[1]))
            sites[name + '_return'] = {'offset': offset, 'before': get(offset - 5, 5).hex(), 'after': get(offset, 8).hex()}
        assert len(re.findall(r'call\s+.*<popen@plt>', dis)) == 1
        assert len(re.findall(r'call\s+.*<fgets@plt>', dis)) == 1
        assert len(re.findall(r'call\s+.*<pclose@plt>', dis)) == 1
        dynamic = command(['/usr/bin/readelf', '-d', str(target)])
        needed = re.findall(r'\(NEEDED\).*\[(.*?)\]', dynamic)
        assert needed == ['libc.so.6'] and 'BIND_NOW' in dynamic
        assert trigger.name not in needed and 'libm' not in dynamic
        if variant == 'worker_postclose_solib':
            assert 'fixture_worker' in symbols and 'fixture_parked_sibling' in symbols
            assert 'pthread_create@plt' in dis and 'pthread_cond_timedwait@plt' in dis
        else:
            assert 'fixture_worker' not in symbols and 'pthread_create@plt' not in dis
        manifest = copy.deepcopy(baseline_manifest)
        manifest.update(kind='OWN_POPEN_FIXTURE_ONLY', source_sha256=ref(source)['sha256'])
        manifest['caller'] = dict(ref(target), function_offset=symbols['paper_load_fixture'][0],
                                  function_size=symbols['paper_load_fixture'][1], sites=sites)
        c = manifest['caller']
        assert c['function_size'] < 8192 and set(c['sites']) == {'popen_return', 'fgets_return', 'pclose_return'}
        for s in sites.values():
            assert c['function_offset'] < s['offset'] < c['function_offset'] + c['function_size']
            assert re.fullmatch('e8[0-9a-f]{8}', s['before']) and re.fullmatch('[0-9a-f]{16}', s['after'])
        manifest_ref = write(out / 'fixture-manifest.json', manifest)
        (out / 'DISASSEMBLY.txt').write_text(dis)
        static_ref = write(out / 'STATIC.json', {'schema': 'frw.own-retired-child-bp-solib-static.v1',
            'variant': variant, 'compile_argv': argv, 'compiler_ref': ref(Path('/usr/bin/cc').resolve()),
            'symbols': symbols, 'marker_entry_bytes': {n: get(symbols[n][0], min(16, symbols[n][1])).hex() for n in (*MARKERS, *EXTRA)},
            'call_site_bindings': sites, 'readelf_dynamic': dynamic, 'needed': needed,
            'readelf_program_headers': command(['/usr/bin/readelf', '-l', str(target)]),
            'disassembly_ref': ref(out / 'DISASSEMBLY.txt'),
            'paper_load_fixture_body_unchanged': True, 'paper_load_fixture_body_sha256': hashlib.sha256(c_paper(source.read_text()).encode()).hexdigest(),
            'exactly_one_compiled_popen_fgets_pclose_call_each': True,
            'trigger_is_not_NEEDED': True, 'runtime_executed': False,
            'late_solib_success_path': 'pclose return validated by adapter -> fixture_paper_done CLOSED/LOAD_CLOSED -> paper_load_fixture returns0 -> RTLD_NOLOAD absent -> dlopen fixed path -> dlsym/probe46525731 -> dlclose0 -> fixture_after_load',
            'event_observation': 'NOT_RUN: source/ELF support only; no native solib event fabricated'})
        prepared = dict(old_prepared)
        prepared.update(variant=variant, source_ref=ref(source), target_ref=ref(target), manifest_ref=manifest_ref,
            adapter_ref=ref(G / 'candidate/paper_helper_gdb.py'), prepare_ref=ref(BASE / 'prepare.py'),
            static_ref=static_ref, marker_offsets={n: symbols[n][0] for n in MARKERS},
            extra_marker_offsets={n: symbols[n][0] for n in EXTRA},
            expected_refusal=None, expected_status='COMPLETE_TWO_HELD_POINTS_FIXTURE_ONLY',
            source_pins_status='EXACT_SOURCE_COMPILE_ONLY_AFTER_RETIRED_BP_CANDIDATE_FREEZE',
            trigger_ref=ref(trigger), trigger_source_ref=ref(BASE / 'trigger/trigger.c'), trigger_static_ref=trigger_static,
            trigger_admission='Root must recheck exact canonical/uid/nlink/rights/hash and RO namespace path before effect; existing supervisor does not consume this extra pin',
            old_adapter_ref=ref(DEPS / 'paper_helper_gdb.py'),
            native_adapter_qualification='NOT_RUN; one-shot .delete remains source/pure-qualified only')
        prepared['source_functions'] = functions(DEPS / 'native_return_observer.py',
            ('font_file', 'font_read', 'font_write', 'capture_font_runtime', 'stopped'))
        prepared['namespace_functions'] = functions(D / 'candidate/outer/namespace_entry.py',
            ('LocalServices', 'validate_font_runtime_proof', 'validate_font_runtime_pair'))
        prepared['adapter_functions'] = functions(G / 'candidate/paper_helper_gdb.py', ('read_ref', 'create', 'Adapter'))
        prepared['runtime_template'] = dict(old_prepared['runtime_template'], source_sha256=manifest['source_sha256'], manifest_ref=manifest_ref)
        outrefs[variant] = write(out / 'PREPARED.json', prepared)
    write(BASE / 'COMPILE-SUMMARY.json', {'status': 'TWO_VARIANTS_COMPILED_STATIC_ONLY', 'prepared': outrefs,
        'elapsed_seconds': round(time.monotonic() - start, 6), 'trigger_ref': ref(trigger), 'pins_checked': [ref(p) for p in PINS],
        'subprocess_bounds': {'each_wall_seconds': 15, 'each_CPU_seconds': 10, 'each_AS_bytes': 512 * 1024**2,
                              'each_file_bytes': 16 * 1024**2, 'each_NOFILE': 64, 'each_core_bytes': 0},
        'ELFs_or_helper_or_driver_or_namespace_executed': False})
    print(json.dumps(outrefs, sort_keys=True))

if __name__ == '__main__':
    main()
