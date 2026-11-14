'Frozen exact223 frame verification; no IO on import.'
from pathlib import Path
import hashlib
import json
import os
import stat
import types


def source_ref(path):
    path = Path(path)
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
    assert not any(p.is_symlink()for p in (path,*path.parents))
    raw = path.read_bytes()
    fields = lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    assert fields(before) == fields(path.lstat()), 'source_identity_changed_during_read'
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest())


def verify_manifest(expected, *, frame):
    frame = Path(frame)
    manifest = frame/'SOURCE-PINS.json'
    assert source_ref(manifest)['sha256'] == expected, 'external_source_manifest_changed'
    pins = json.loads(manifest.read_bytes())
    producer_path = frame/'source_pins_producer.py'
    assert source_ref(producer_path)['sha256'] == pins['source_refs'][str(producer_path)], 'pinned_manifest_producer_required'
    producer = types.ModuleType('Root223SourcePinsProducer')
    producer.__file__ = str(producer_path)
    exec(compile(producer_path.read_bytes(),str(producer_path),'exec'),producer.__dict__)
    explicit = {**pins['source_refs'],**pins['historical_refs']}
    raw = {}
    for path,digest in explicit.items():
        assert source_ref(path)['sha256'] == digest, 'exact_frozen_source_changed:'+path
        raw[path] = Path(path).read_bytes()
        assert hashlib.sha256(raw[path]).hexdigest() == digest
    return producer.validate_source_pins(pins,source_bytes=raw,frame=str(frame))
