"""Compile/static-bind the tiny own fixture. Never executes its resulting ELF.

Root must provide a fresh private namespace/cgroup and actual absolute clock.
The shared exact adapter/policy are referenced, never copied/reimplemented here.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

BASE = Path(__file__).resolve().parent
DEPS = BASE.parent / 'candidate/outer/deps'


def file_ref(p):
    return {'path': str(p.resolve()), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def elf_reader(path):
    raw = Path(path).read_bytes()
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    assert raw[:6] == b'\x7fELF\x02\x01'
    loads = []
    for i in range(h[10]):
        t, flags, off, va, _pa, size, _mem, _align = struct.unpack_from('<IIQQQQQQ', raw, h[5] + i * h[9])
        if t == 1:
            loads.append((off, va, size))
    def get(va, n):
        offsets = [off + va - start for off, start, size in loads if start <= va and va + n <= start + size]
        assert len(offsets) == 1
        return raw[offsets[0]:offsets[0] + n]
    return get


def prepare(out):
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    exe = out / 'paper_fixture'
    subprocess.run(['/usr/bin/cc', '-O0', '-g', '-fno-omit-frame-pointer', '-fPIE', '-pie',
        '-Wl,-z,now', '-o', str(exe), str(BASE / 'paper_fixture.c')], check=True)
    symbols = {}
    for line in subprocess.check_output(['/usr/bin/nm', '-S', str(exe)], text=True).splitlines():
        f = line.split()
        if len(f) == 4 and f[3] in ('paper_load_fixture', 'fixture_ready', 'fixture_done'):
            symbols[f[3]] = (int(f[0], 16), int(f[1], 16))
    assert len(symbols) == 3
    get = elf_reader(exe)
    text = subprocess.check_output(['/usr/bin/objdump', '-d', '--disassemble=paper_load_fixture', str(exe)], text=True)
    sites = {}
    for name in ('popen', 'fgets', 'pclose'):
        rows = [line for line in text.splitlines() if re.search(r'call\s+.*<' + name + r'@plt>', line)]
        assert len(rows) == 1
        fields = rows[0].split('\t')
        offset = int(fields[0].strip().rstrip(':'), 16) + len(bytes.fromhex(fields[1]))
        sites[name + '_return'] = {'offset': offset, 'before': get(offset - 5, 5).hex(), 'after': get(offset, 8).hex()}
    manifest = copy.deepcopy(json.loads((DEPS / 'PAPER-HELPER-OFFICE-MANIFEST.json').read_text()))
    manifest.update(kind='OWN_POPEN_FIXTURE_ONLY', source_sha256=file_ref(BASE / 'paper_fixture.c')['sha256'])
    manifest['caller'] = dict(file_ref(exe), function_offset=symbols['paper_load_fixture'][0],
                              function_size=symbols['paper_load_fixture'][1], sites=sites)
    manifest_path = out / 'fixture-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    manifest_path.chmod(0o600)
    prepared = dict(schema='frw.own-paper-helper-fixture-preparation.v1',
        target=file_ref(exe), source=file_ref(BASE / 'paper_fixture.c'), manifest_ref=file_ref(manifest_path),
        adapter_ref=file_ref(DEPS / 'paper_helper_gdb.py'), policy_ref=file_ref(DEPS / 'paper_helper_policy.py'),
        driver_ref=file_ref(BASE / 'paper_fixture_gdb.py'),
        ready_offset=symbols['fixture_ready'][0], done_offset=symbols['fixture_done'][0],
        runtime_template=dict(operation_id='REPLACE', nonce='REPLACE', source_sha256=manifest['source_sha256'],
            manifest_ref=file_ref(manifest_path), marker_path='/tmp/friday-metric-work/load-dependency.json',
            operation_deadline_monotonic=None),
        preparation_only=True, runtime_executed=False,
        runtime_contract='Root replaces identity/absolute clock, writes protected helper-runtime.json bundle, '
            'sets FRW_NATIVE_LOAD_DEPENDENCY_REF to its exact JSON file ref and FRW_PAPER_FIXTURE_CONFIG '
            'to protected config {target,target_sha256,nonce,ready_offset,done_offset}; exact fixed WORK, '
            'owned gdb.log as both inferior stdout/stderr, stdin /dev/null, original namespace environment. '
            'Root owns hard deadline/cgroup cleanup and actual terminal/PID absence verification.')
    (out / 'PREPARED.json').write_text(json.dumps(prepared, indent=2, sort_keys=True) + '\n')
    (out / 'PREPARED.json').chmod(0o600)
    return prepared


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(args.prepare), sort_keys=True))
    else:
        print(json.dumps({'status': 'SOURCE_ONLY_NO_COMPILE_NO_EXECUTION'}))
