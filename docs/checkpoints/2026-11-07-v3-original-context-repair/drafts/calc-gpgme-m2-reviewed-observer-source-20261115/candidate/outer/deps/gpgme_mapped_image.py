"""Finite pure current-map/backing-ELF join, SOURCE preparation only.

Inputs must be collected at one exact stopped owned-process boundary. This
module performs no procfs access, memory read, GDB command, or continuation.
An external collector still needs original birth/thread/all-stop/CAS checks.
"""
import hashlib
import re
import stat
import struct


def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def parse_maps(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 524288, 'gpgme_maps_bound')
    try:
        lines = raw.decode('ascii').splitlines()
    except UnicodeError:
        raise RuntimeError('gpgme_maps_encoding') from None
    rows = []
    previous_end = 0
    for line in lines:
        parts = line.split(None, 5)
        need(len(parts) in (5, 6), 'gpgme_maps_row_schema')
        address, perms, offset, dev, ino = parts[:5]
        need(re.fullmatch('[0-9a-f]+-[0-9a-f]+', address) is not None
             and re.fullmatch('[r-][w-][x-][ps]', perms) is not None
             and re.fullmatch('[0-9a-f]+', offset) is not None
             and re.fullmatch('[0-9a-f]+:[0-9a-f]+', dev) is not None
             and ino.isdecimal(), 'gpgme_maps_numeric_encoding')
        start, end = (int(v, 16) for v in address.split('-'))
        major, minor = (int(v, 16) for v in dev.split(':'))
        need(0 < start < end <= 1 << 64 and start >= previous_end, 'gpgme_maps_ranges')
        need(start % 4096 == end % 4096 == int(offset, 16) % 4096 == 0,
             'gpgme_maps_page_alignment')
        previous_end = end
        rows.append(dict(start=start, end=end, perms=perms, offset=int(offset, 16),
                         dev_major=major, dev_minor=minor, ino=int(ino),
                         path=parts[5] if len(parts) == 6 else ''))
    need(0 < len(rows) <= 8192, 'gpgme_maps_row_bound')
    return rows


def elf_metadata(raw):
    need(type(raw) is bytes and 64 <= len(raw) <= 2097152 and raw[:7] == b'\x7fELF\x02\x01\x01',
         'gpgme_ELF64_LE_bound')
    header = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    need(header[1:4] == (3, 62, 1) and header[8] == 64 and header[9] == 56
         and 0 < header[10] <= 64, 'gpgme_ELF_type_machine_headers')
    phoff, phnum = header[5], header[10]
    need(64 <= phoff <= len(raw) and phoff + phnum * 56 <= len(raw), 'gpgme_ELF_phdr_bound')
    loads, builds = [], []
    for index in range(phnum):
        kind, flags, offset, vaddr, _paddr, filesz, memsz, align = struct.unpack_from('<IIQQQQQQ', raw, phoff + 56 * index)
        need(offset <= len(raw) and offset + filesz <= len(raw), 'gpgme_ELF_segment_file_bound')
        if kind == 1:
            need(0 < filesz <= memsz and align == 4096 and offset % align == vaddr % align,
                 'gpgme_ELF_load_contract')
            loads.append(dict(flags=flags, offset=offset, vaddr=vaddr, filesz=filesz, memsz=memsz))
        if kind == 4:
            cursor, stop = offset, offset + filesz
            while cursor < stop:
                need(cursor + 12 <= stop, 'gpgme_ELF_note_header')
                namesz, descsz, note_type = struct.unpack_from('<III', raw, cursor)
                cursor += 12
                name_end = cursor + namesz
                desc_start = (name_end + 3) & ~3
                desc_end = desc_start + descsz
                need(name_end <= stop and desc_end <= stop, 'gpgme_ELF_note_bound')
                if raw[cursor:name_end] == b'GNU\0' and note_type == 3:
                    need(0 < descsz <= 64, 'gpgme_ELF_build_id_bound')
                    builds.append(raw[desc_start:desc_end].hex())
                cursor = (desc_end + 3) & ~3
            need(cursor == stop, 'gpgme_ELF_note_alignment')
    need(1 <= len(loads) <= 16 and len(builds) == 1, 'gpgme_ELF_load_or_build_id_ambiguity')
    return dict(loads=loads, build_id=builds[0], sha256=hashlib.sha256(raw).hexdigest())


def bind_current_image(maps_before, maps_after, file_before, file_after, raw, image, pc):
    """Return sanitized numerical binding; never accept a basename-only owner.

    file_before/file_after are HOST-side fstat of the SAME already opened
    backing FD, with host uid0. An inside-namespace overflow uid is deliberately
    refused here, not equated to host root. A future namespace collector must
    independently bind its actual uid_map/overflow policy and the Root-pinned
    host owner/device/inode/hash/metadata before supplying a host-view stamp.
    The collector must also compare that FD to final current namespace path
    identity and to original process/thread before returning observations.
    This pure join alone is deliberately insufficient for runtime admission.
    """
    need(type(image) is dict and set(image) == {'path', 'sha256', 'build_id'}, 'gpgme_image_schema')
    path = image['path']
    need(type(path) is str and path.startswith('/') and '\\' not in path
         and all(v not in ('', '.', '..') for v in path.split('/')[1:]), 'gpgme_image_canonical_path')
    need(type(maps_before) is bytes and type(maps_after) is bytes
         and maps_before == maps_after, 'gpgme_current_maps_changed')
    keys = {'dev_major', 'dev_minor', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'uid', 'nlink'}
    need(type(file_before) is dict and type(file_after) is dict and set(file_before) == set(file_after) == keys
         and all(type(v) is int and v >= 0 for stamp in (file_before, file_after) for v in stamp.values())
         and file_before == file_after,
         'gpgme_backing_file_changed')
    need(all(type(v) is int and v >= 0 for v in file_before.values())
         and file_before['ino'] > 0 and file_before['size'] == len(raw)
         and stat.S_ISREG(file_before['mode']) and not file_before['mode'] & 0o022
         and file_before['nlink'] == 1 and file_before['uid'] == 0, 'gpgme_backing_file_rights')
    meta = elf_metadata(raw)
    need(meta['sha256'] == image['sha256'] and meta['build_id'] == image['build_id'],
         'gpgme_backing_ELF_hash_build_id')
    rows = parse_maps(maps_before)
    own = [r for r in rows if r['path'] == path]
    same_backing = [r for r in rows if r['ino'] == file_before['ino']
        and r['dev_major'] == file_before['dev_major'] and r['dev_minor'] == file_before['dev_minor']]
    need(all(r['path'] == path for r in same_backing), 'gpgme_backing_mapping_alias_or_deleted')
    need(0 < len(own) <= 16 and all(r['ino'] == file_before['ino']
         and r['dev_major'] == file_before['dev_major'] and r['dev_minor'] == file_before['dev_minor']
         and r['perms'].endswith('p') for r in own), 'gpgme_mapped_inode_device_or_sharing')
    need(type(pc) is int and pc > 0, 'gpgme_mapped_PC_value')
    selected = [r for r in own if r['start'] <= pc < r['end'] and 'x' in r['perms']]
    need(len(selected) == 1, 'gpgme_PC_executable_mapping')
    down = lambda v: v & ~4095
    up = lambda v: (v + 4095) & ~4095
    candidates = None
    for row in own:
        offsets = set()
        for segment in meta['loads']:
            if (down(segment['offset']) <= row['offset'] < up(segment['offset'] + segment['filesz'])
                    and row['offset'] + row['end'] - row['start'] <= up(segment['offset'] + segment['filesz'])
                    and all(p == '-' or segment['flags'] & flag
                            for p, flag in zip(row['perms'][:3], (4, 2, 1)))):
                bias = row['start'] - (down(segment['vaddr']) + row['offset'] - down(segment['offset']))
                if bias >= 0 and bias % 4096 == 0:
                    offsets.add(bias)
        need(bool(offsets), 'gpgme_mapping_not_ELF_PT_LOAD')
        candidates = offsets if candidates is None else candidates & offsets
    need(candidates is not None and len(candidates) == 1, 'gpgme_load_bias_ambiguous')
    bias = candidates.pop()
    relative = pc - bias
    need(any(s['flags'] & 1 and s['vaddr'] <= relative < s['vaddr'] + s['memsz'] for s in meta['loads']),
         'gpgme_PC_not_executable_PT_LOAD')
    return dict(schema='frw.calc.gpgme-current-map-pure-join.v1',
        backing_sha256=meta['sha256'], build_id=meta['build_id'],
        device_major=file_before['dev_major'], device_minor=file_before['dev_minor'], inode=file_before['ino'],
        executable_map_start=selected[0]['start'], executable_map_end=selected[0]['end'],
        executable_file_offset=selected[0]['offset'], load_bias=bias, relative_pc=relative,
        runtime_attested=False, collector_complete=False)
