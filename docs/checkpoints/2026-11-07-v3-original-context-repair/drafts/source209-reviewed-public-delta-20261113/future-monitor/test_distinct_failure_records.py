"""One additional same-source control: initial/final failure metadata differ."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

D = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-PRESENTATION-DISK-MONITOR-ATTRIBUTION-20261113')
ns = {'__name__': 'inert_control_definitions'}
exec(compile((D / 'test_monitor_delta.py').read_bytes(), 'inert_control_definitions', 'exec'), ns)
h = ns['load_selected']((D / 'source/root_f07_once.py').read_bytes(), 'unchanged_future_monitor')
scope, child, patch = ns['scope'], ns['child'], ns['patch']
work = D / 'distinct-record-fixture'
work.mkdir(mode=0o700)
target = work / 'own-target'
target.write_bytes(b'own-fixture')
root = work / 'scanned'
root.mkdir(mode=0o700)
path = root / 'changes-type-after-cleanup'
path.symlink_to(target)
actor = child('import time; time.sleep(20)')
stop_reap = h.stop_reap


def cleanup_then_change_fixture(*args, **kwargs):
    code = stop_reap(*args, **kwargs)
    path.unlink()
    os.mkfifo(path, 0o600)
    return code


try:
    with patch.object(h, 'stop_reap', cleanup_then_change_fixture):
        result = h.wait_owned(actor, dict(deadline_monotonic=time.monotonic() + 12), scope(root), {}, 4096, [])
    first, final = result['monitor_failure'], result['final_monitor_failure']
    assert first['enum'] == 'F07_OPERATION_WRITE_SCOPE_LINK_RECONCILE_ONLY'
    assert first['stage'] == 'SCAN_ENTRY_LINK_GUARD'
    assert final['enum'] == 'F07_WRITE_SCOPE_SPECIAL_FILE'
    assert final['stage'] == 'SCAN_ENTRY_TYPE_GUARD'
    assert first['path'] == final['path'] == str(path)
    assert result['stop_reason'] == 'AGGREGATE_DISK_MONITOR_REFUSED'
    assert result['cleanup_signals'] == [int(signal.SIGINT)] and actor.poll() is not None
    assert actor.wait(timeout=0) == result['exit_code']
    report = dict(status='PASS', schema='frw.Root.F04.future-monitor-distinct-failures-control.v1',
                  reason_for_additional_control='Same candidate; prove final refusal does not overwrite a different initial refusal.',
                  source_sha256=hashlib.sha256((D / 'source/root_f07_once.py').read_bytes()).hexdigest(),
                  first=first, final=final, original_stop_reason_retained=True,
                  own_children_created=1, own_children_reaped=1, own_fixture_removed=True,
                  product_effects=False, original_operation_replayed=False)
finally:
    if actor.poll() is None:
        actor.kill()
        actor.wait(timeout=2)
    shutil.rmtree(work)
raw = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
with os.fdopen(os.open(D / 'FUTURE-DELTA-DISTINCT-FAILURES-CONTROL.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as out:
    out.write(raw)
print(json.dumps(dict(status=report['status'], source_sha256=report['source_sha256'], own_child_reaped=True,
                      first_enum=first['enum'], final_enum=final['enum'])))
