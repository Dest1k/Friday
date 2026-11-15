"""Generate bounded SOURCE inputs, never execute a target or start a clock."""
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
N={'__file__':str(HERE/'ownc_inputs.py'),'__name__':'frw_ownc_metadata'}
exec(compile((HERE/'ownc_inputs.py').read_bytes(),str(HERE/'ownc_inputs.py'),'exec'),N)
BASE=N['BASE'];DEPS=N['DEPS'];WORK=N['WORK'];ref=N['ref'];put=N['put'];need=N['need']
COMPOSITION={'path':str(N['REVIEWED']/'ROOT-COMPOSITION.json'),
             'sha256':'0669a77bfbc2b7204d57335b6cfb77eecea822f69b855500c05280df70ebec8a'}
SELECTED={'worker_cached':('cached-getter/held_gpgme_cached_fixture.c','cached-getter/own-gpgme-worker-cached'),
          'extra_fork':('held_gpgme_fixture.c','own-gpgme-extra_fork'),
          'forbidden_gpg_home':('held_gpgme_fixture.c','own-gpgme-forbidden_gpg_home'),
          'wrong_gpgconf_name':('held_gpgme_fixture.c','own-gpgme-wrong_gpgconf_name')}
EXPECTED={'worker_cached':None,'extra_fork':{'stage':'boundary:fork',
          'code':'gpgme_unexpected_fork_vfork_exec_outside_initialization','affected_child_released':False},
          'forbidden_gpg_home':{'stage':'bootstrap_entry',
          'code':'gpgme_environment_isolation_or_override','affected_child_released':False},
          'wrong_gpgconf_name':{'stage':'dirs_entry',
          'code':'gpgme_exact_string_mismatch','affected_child_released':False}}


def generate():
    os.umask(0o077)
    need(ref(Path(COMPOSITION['path']))==COMPOSITION,'reviewed_composition_pin')
    composition=json.loads(Path(COMPOSITION['path']).read_bytes())
    for item in composition['files']:
        r=item['selected'];need(ref(Path(r['path']))['sha256']==r['sha256'],'reviewed_input_pin')
    prep_ref={'path':str(N['PREP']/'RESULT.json'),'sha256':'b8cf5f5bd9f5d80ff7e34ef62cdc3995f48a79ce99fd9d9eb2971852d0004e6b'}
    cached_ref={'path':str(N['PREP']/'cached-getter/RESULT.json'),'sha256':'9bd2705488024f725892902346064db0b35909d5b1862eec2a9e2bdee520f50f'}
    need(ref(Path(prep_ref['path']))==prep_ref and ref(Path(cached_ref['path']))==cached_ref,'selected_preparation_pin')
    prep=json.loads(Path(prep_ref['path']).read_bytes());cached=json.loads(Path(cached_ref['path']).read_bytes())
    common_gpg=N['gpgme_manifest']()
    gmanifest_ref=put(HERE/'GPGME-MANIFEST.json',common_gpg)
    variants={}
    for variant,(source_name,target_name) in SELECTED.items():
        out=HERE/variant;out.mkdir(mode=0o700)
        source=N['PREP']/source_name;target=N['PREP']/target_name
        expected=cached if variant=='worker_cached' else {'source':prep['source'],'target':prep['variants'][variant]['target']}
        need(ref(source)=={k:expected['source'][k] for k in ('path','sha256')}
             and ref(target)=={k:expected['target'][k] for k in ('path','sha256')},'selected_exact_source_and_target')
        elf=N['ELF'](target);paper=N['paper_manifest'](source,target)
        mref=put(out/'PAPER-MANIFEST.json',paper)
        old=(DEPS/'gpgme_engine_bundle.py').read_text()
        before="PAPER_MANIFEST_SHA256 = '92b94f4100609c820f25891e09ec15267802833fb4665c393ff746c4565691d0'"
        after="PAPER_MANIFEST_SHA256 = '"+mref['sha256']+"'"
        need(old.count(before)==1,'fixture_validator_exact_one_pin')
        validator=old.replace(before,after)
        need(validator.replace(after,before)==old,'fixture_validator_no_other_change')
        vpath=out/'gpgme_engine_bundle.py';vpath.write_text(validator);vpath.chmod(0o600)
        patch=''.join(difflib.unified_diff(old.splitlines(True),validator.splitlines(True),
            fromfile=str(DEPS/'gpgme_engine_bundle.py'),tofile=str(vpath)))
        (out/'fixture-validator.patch').write_text(patch);(out/'fixture-validator.patch').chmod(0o600)
        binding={'manifest':gmanifest_ref,'validator':ref(vpath)}|{role:ref(DEPS/name) for role,name in
            {'collector':'gpgme_boundary_collector.py','adapter':'gpgme_engine_gdb.py',
             'policy':'gpgme_engine_policy.py','mapper':'gpgme_mapped_image.py'}.items()}
        paper_runtime=dict(operation_id=None,nonce=None,source_sha256=paper['source_sha256'],manifest_ref=mref,
            marker_path=WORK+'/load-dependency.json',operation_deadline_monotonic=None)
        gpg_runtime=dict(paper_runtime,manifest_ref=gmanifest_ref,paper_manifest_ref=mref,
            bundle_path=WORK+'/output/observer-gpgme-engine-init-bundle.json',
            evidence_path=WORK+'/output/observer-gpgme-engine-init.json')
        prepared=dict(schema='frw.ownc.gpgme-prepared.v1',kind='OWN_POPEN_FIXTURE_ONLY',variant=variant,
            source_ref=ref(source),target_ref=ref(target),manifest_ref=mref,adapter_ref=ref(DEPS/'paper_helper_gdb.py'),
            policy_ref=ref(DEPS/'paper_helper_policy.py'),native_observer_ref=ref(DEPS/'native_return_observer.py'),
            namespace_ref=ref(DEPS.parent/'namespace_entry.py'),gdb_driver_ref=ref(BASE/'driver/ownc_gdb.py'),
            supervisor_ref=ref(BASE/'host/ownc_namespace_supervisor.py'),marker_offsets={name:elf.symbols[name][0]-elf.origin
            for name in N['MARKERS']},marker_entry_bytes={name:elf.get(elf.symbols[name][0],min(16,elf.symbols[name][1])).hex()
            for name in N['MARKERS']},target_elf_origin=elf.origin,runtime_template=paper_runtime,
            gpgme_runtime_template=gpg_runtime,gpgme_binding=binding,target_environment=dict(N['ENV']),
            expected_refusal=EXPECTED[variant],preparation_only=True,runtime_executed=False,actual_M=None,
            runtime_attested=False,record_semantics='FIXTURE_MARKER_ONLY',reviewed_composition=COMPOSITION,
            expected_negative_paper_gate='ACTUAL_PAPER_CLOSED_TWO_CHILDREN_EXIT_ABSENCE_REQUIRED_NOT_YET_OBSERVED')
        pref=put(out/'PREPARED.json',prepared)
        source_refs={'outer_runner':ref(DEPS.parent/'outer_runner.py'),'metric_namespace':ref(DEPS/'metric_namespace.py'),
            'namespace':prepared['namespace_ref'],'supervisor':prepared['supervisor_ref'],
            'gdb_driver':prepared['gdb_driver_ref']}
        plan=dict(schema='frw.ownc.gpgme-static-plan.v1',kind=prepared['kind'],variant=variant,
            budgets=dict(wall_seconds=240,cpu_seconds=120,memory_bytes=2147483648,cleanup_seconds=10,
                         startup_seconds=60,tasks_max=64),
            tools={role:ref(Path(path).resolve()) for role,path in
                   {'python':'/usr/bin/python3','gdb':'/usr/bin/gdb','bwrap':'/usr/bin/bwrap'}.items()},
            readonly_roots=[str(BASE),str(N['REVIEWED']),str(N['PREP'])],
            binding_root='/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115/python-uno-binding/root',
            prepared_ref=pref,source_refs=source_refs,target_environment=dict(N['ENV']),
            observer=dict(config=dict(target_sha256=prepared['target_ref']['sha256']),
                load_dependency=dict(manifest=mref,adapter=prepared['adapter_ref'],policy=prepared['policy_ref']),
                gpgme_engine_init=binding))
        variants[variant]={'prepared_ref':pref,'plan_ref':put(out/'STATIC-PLAN.json',plan)}
    return put(HERE/'SELECTED-INPUTS.json',dict(schema='frw.ownc.selected-source-inputs.v1',
        reviewed_composition=COMPOSITION,variants=variants,full_target_startup_environment=N['ENV'],
        future_execution=False,actual_M=None,fixture_only=True))


if __name__=='__main__':print(json.dumps(generate(),sort_keys=True))
