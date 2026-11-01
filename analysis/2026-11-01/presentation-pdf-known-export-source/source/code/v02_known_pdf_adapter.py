"""Pure V02 seam: accept only Root-reviewed, closed actual known-PDF evidence.

No Office/model/send/installation/qualification effect occurs here. The raw
producer certificate is separate from Root's acceptance. Genuine user artifacts
and expectations are intentionally absent from this known-only ABI.
"""
from pathlib import Path
import hashlib
import json
import os
import runpy

HERE = Path(__file__).resolve().parent
BOUNDARY = runpy.run_path(str(HERE / 'pptx_pdf_boundary.py'))
ACCEPT_FIELDS = {'schema', 'operator', 'accepted', 'qualification', 'actual_observation',
                 'current_bindings', 'source_manifest', 'source_directory', 'adapter',
                 'known_input', 'known_expectation', 'consumer', 'strace', 'pdf_reader', 'kernel',
                 'qualification_closed', 'own_processes_zero', 'temporary_homes_removed',
                 'original_effect_closed', 'runtime_or_semantic_acceptance'}


def validate(b, pkg, value):
    need = BOUNDARY['need']
    need(type(pkg) is dict and type(value) is dict
         and value.get('known_pdf_qualification') == pkg.get('known_pdf_qualification')
         and BOUNDARY['reference'](pkg.get('known_pdf_qualification')),
         'V02_EXACT_KNOWN_QUALIFICATION_REFERENCE_REQUIRED')
    qualifier_ref = pkg['known_pdf_qualification']
    qualifier = b.document(qualifier_ref)
    acceptance_ref = pkg.get('known_pdf_acceptance')
    need(BOUNDARY['reference'](acceptance_ref), 'V02_ROOT_KNOWN_ACCEPTANCE_REF_REQUIRED')
    acceptance = b.document(acceptance_ref)
    need(type(acceptance) is dict and set(acceptance) == ACCEPT_FIELDS
         and acceptance['schema'] == 'frw.Root.pptx-pdf-known-export-accepted.v1'
         and acceptance['operator'] == 'Root' and acceptance['accepted'] is True
         and acceptance['qualification'] == qualifier_ref
         and acceptance['current_bindings'] == value.get('current_bindings')
         and all(acceptance[n] is True for n in ('qualification_closed', 'own_processes_zero',
                    'temporary_homes_removed', 'original_effect_closed'))
         and acceptance['runtime_or_semantic_acceptance'] is False,
         'V02_EXACT_ROOT_KNOWN_PDF_ACCEPTANCE_REQUIRED')
    need(acceptance['source_directory'] == str(HERE)
         and acceptance['adapter'] == pkg.get('known_pdf_consumer')
         and acceptance['adapter'] == {'path': str(HERE / 'v02_known_pdf_adapter.py'),
             'sha256': hashlib.sha256((HERE / 'v02_known_pdf_adapter.py').read_bytes()).hexdigest()},
         'V02_ROOT_KNOWN_SOURCE_ADAPTER_JOIN')
    need(acceptance['kernel'] == {'release': os.uname().release,
          'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()},
         'V02_KNOWN_ACTUAL_KERNEL_BOOT_REQUIRED')
    binding = {n: acceptance[n] for n in ('consumer', 'strace', 'pdf_reader', 'kernel', 'source_manifest')}
    binding['import_settings'] = BOUNDARY['IMPORT_SETTINGS']
    BOUNDARY['qualification_identity'](binding, qualifier)
    need(acceptance['actual_observation'] == qualifier['actual_observation'], 'V02_KNOWN_OBSERVATION_PIN_JOIN')
    manifest = b.document(acceptance['source_manifest'])
    leaves = {r.get('path'): r.get('sha256') for r in manifest.get('files', []) if type(r) is dict}
    for path in [*HERE.glob('*.py'), HERE.parent / 'base/qualify_office.py']:
        name = path.relative_to(HERE.parent).as_posix()
        need(leaves.get(name) == hashlib.sha256(path.read_bytes()).hexdigest(), 'V02_KNOWN_COMPLETE_SOURCE_MANIFEST_JOIN')
    need(acceptance['known_input'] == {'path': str(HERE.parent / 'fixtures/known-visible-label.pptx'),
             'sha256': leaves.get('fixtures/known-visible-label.pptx')}
         and acceptance['known_expectation'] == {'path': str(HERE.parent / 'fixtures/KNOWN-PPTX-PDF-EXPECTATION.json'),
             'sha256': leaves.get('fixtures/KNOWN-PPTX-PDF-EXPECTATION.json')}, 'V02_ACCEPTED_KNOWN_FIXTURE_PINS_REQUIRED')
    BOUNDARY['_check_known_qualification'](binding, {'consumer_qualification': qualifier})
    # b.read enforces the caller's actual protected file/CAS contract. These
    # mutable records are re-read rather than accepted from a source fixture.
    for ref in (qualifier_ref, acceptance_ref, value['current_bindings']):
        b.read(ref)
    for tool in ('strace', 'pdf_reader'):
        ref = binding[tool]['executable']
        BOUNDARY['pinned_read'](ref['path'], ref['sha256'], 4 * 1024 * 1024, owner=0)
    ref = binding['consumer']['executable']
    BOUNDARY['pinned_read'](ref['path'], ref['sha256'], 64 * 1024 * 1024, owner=os.getuid())
    need(b.document(qualifier_ref) == qualifier and b.document(acceptance_ref) == acceptance,
         'V02_KNOWN_QUALIFICATION_ACCEPTANCE_CAS_CHANGED')
    return True
