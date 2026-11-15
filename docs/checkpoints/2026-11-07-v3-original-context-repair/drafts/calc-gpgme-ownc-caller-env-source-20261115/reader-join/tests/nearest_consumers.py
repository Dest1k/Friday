"""Re-evaluate unchanged actual metadata/host tests against new caller afterimages.

Read exact existing source tests, set their file context to this current private
scope so source()/BASE resolve current caller/plans. No copied test source, no
backend, namespace, GDB or target execution. Their bodies remain unchanged.
"""
from pathlib import Path
import hashlib
import types
import unittest
BASE=Path(__file__).resolve().parents[1]
ORIGINAL=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115/host')
PINS={'test_host_source.py':'8e1f592b87436cfb2f3921fbbbbaf39e9e47690bf1ac791969a2814d50031ad7',
      'test_actual_joins.py':'890c62a3c3c9ec02e86ff5cdf3ab37e17963d3e3bf73d9e5fb944aa507f7302e'}
suite=unittest.TestSuite()
for name,pin in PINS.items():
    raw=(ORIGINAL/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==pin
    m=types.ModuleType('nearest_'+name[:-3]);m.__file__=str(BASE/'host'/name)
    exec(compile(raw,str(ORIGINAL/name),'exec'),m.__dict__)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m))
if __name__=='__main__':
    outcome=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
