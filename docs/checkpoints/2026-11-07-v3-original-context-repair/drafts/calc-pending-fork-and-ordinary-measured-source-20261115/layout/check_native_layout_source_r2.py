"""Real-filesystem SOURCE controls only. No namespace/Office/native launch."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import ast
import pwd
import stat
from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

os.umask(0o077)
P = Path(__file__).resolve().parent
MODULE = P / 'candidate-r2/hermes_cli/friday_workspace_calc_native_layout.py'
spec = importlib.util.spec_from_file_location('frw_native_layout_under_test', MODULE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
root = Path(tempfile.mkdtemp(prefix='layout-r2-source-only-', dir=P))
results = []


def asset_fixture(tag, files=None):
    base = root / tag
    base.mkdir(mode=0o700)
    work = base / 'work'
    work.mkdir(mode=0o700)
    for name in ('out', 'home', 'tmp'):
        (work / name).mkdir(mode=0o700)
    source = work / 'input.ods'
    source.write_bytes(b'PRIVATE SYNTHETIC SOURCE, NOT AN OFFICE ARTIFACT')
    source.chmod(0o600)
    assets = base / 'assets'
    assets.mkdir(mode=0o700)
    (assets / 'entry.py').write_bytes(b'# SOURCE TEST VECTOR ONLY\n')
    index = assets / 'index.json'
    index.write_text(json.dumps({'schema': 'frw.calc.native-code-generation.v1',
                                'entry': 'entry.py', 'files': files or [
                                    {'relative': 'entry.py', 'sha256': sha(assets / 'entry.py')}]}))
    toolchain = base / 'toolchain'
    toolchain.mkdir(mode=0o700)
    program = toolchain / 'root/usr/lib/libreoffice/program'
    program.mkdir(parents=True, mode=0o700)
    (program / 'soffice.bin').write_bytes(b'NOT EXECUTABLE; SOURCE PATH VECTOR ONLY')
    (toolchain / 'share-merged').mkdir(mode=0o700)
    toolchain.chmod(0o500)
    return work, source, index, toolchain


def refuses(name, action, reason):
    try:
        action()
    except m.LayoutRefused as error:
        assert str(error) == reason, (name, str(error), reason)
        results.append({'name': name, 'result': 'EXPECTED_SOURCE_REFUSAL', 'reason': reason})
    else:
        raise AssertionError(name + ': accepted invalid source input')


try:
    work, source, index, toolchain = asset_fixture('positive')
    original = source.read_bytes()
    staged = m.stage_code(work, index, sha(index))
    argv = m.namespace_argv(work, toolchain, staged, source_sha256=sha(source), source_bytes=len(original))
    assert argv.count('--bind') == 1
    assert argv[argv.index('--bind') + 1:argv.index('--bind') + 3] == (str(work), m.WORK)
    assert '/work' not in argv
    triples = [argv[i:i+3] for i, value in enumerate(argv) if value == '--ro-bind']
    assert ('--ro-bind', str(source), m.WORK + '/input.ods') in triples
    assert ('--ro-bind', str(staged.directory), m.WORK + '/code') in triples
    assert argv[-5:] == ('/usr/bin/python3', '-I', '-B', '-S', m.WORK + '/code/entry.py')
    assert source.read_bytes() == original
    assert (staged.directory / 'entry.py').stat().st_mode & 0o777 == 0o400
    results.append({'name': 'real_file_stage_and_single_canonical_mount', 'result': 'SOURCE_PASS'})
    # Evaluate the unchanged nearest source selector on its ACTUAL managed root,
    # without importing product globals or starting any namespace/Office actor.
    pdf = Path('/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115/native224-provider-caller-source/hermes_cli/friday_workspace_pdf.py')
    assert sha(pdf) == '71b27cee76d8b927bfad064ea8b79a4da7c2791357ab2a82c747e453e7ad03b5'
    tree = ast.parse(pdf.read_text())
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('_TOOLCHAIN_NAME','_PRESENTATION_TOOLCHAIN_NAME'):
                    constants[target.id] = ast.literal_eval(node.value)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_toolchain')
    namespace = dict(Path=Path, pwd=pwd, os=os, stat=stat, ExportRefused=m.LayoutRefused, **constants)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(pdf), 'exec'), namespace)
    actual = namespace['_toolchain']()
    actual_before = m.stamp(actual.lstat())
    actual_argv = m.namespace_argv(work,actual,staged,source_sha256=sha(source),source_bytes=len(original))
    assert actual_before == m.stamp(actual.lstat())
    assert ('--ro-bind', str(actual), m.PREFIX) in [actual_argv[i:i+3] for i,v in enumerate(actual_argv) if v=='--ro-bind']
    actual_toolchain = {'path':str(actual),'mode':oct(stat.S_IMODE(actual.stat().st_mode)),
                        'unchanged_source_selector':str(pdf),'selector_source_sha256':sha(pdf),
                        'metadata_unchanged':True,'actual_source_namespace_argv_built':True,
                        'runtime_or_component_qualification':False}
    results.append({'name':'actual_managed_toolchain_nearest_selector','result':'SOURCE_INPUT_PASS'})
    try:
        m.stage_code(work, index, sha(index))
    except FileExistsError:
        results.append({'name': 'repeat_generation_no_merge', 'result': 'EXPECTED_EXCLUSIVE_CREATE_REFUSAL'})
    else:
        raise AssertionError('generation merged')
    assert source.read_bytes() == original
    refuses('forged_entry_traversal', lambda: m.namespace_argv(work,toolchain,replace(staged,entry='../input.ods'),source_sha256=sha(source),source_bytes=len(original)), 'native_layout_relative_name')
    refuses('wrong_source_hash', lambda: m.namespace_argv(work,toolchain,staged,source_sha256='0'*64,source_bytes=len(original)), 'native_layout_source_hash')
    refuses('wrong_source_length', lambda: m.namespace_argv(work,toolchain,staged,source_sha256=sha(source),source_bytes=1), 'native_layout_original_source')
    (staged.directory / 'entry.py').chmod(0o600)
    (staged.directory / 'entry.py').write_bytes(b'CHANGED SOURCE')
    refuses('staged_code_drift', lambda: m.namespace_argv(work,toolchain,staged,source_sha256=sha(source),source_bytes=len(original)), 'native_layout_source_hash')
    w,s,i,t = asset_fixture('source_symlink')
    original_target = s.parent / 'actual-source'
    s.rename(original_target)
    s.symlink_to(original_target)
    refuses('source_symlink',lambda:m.read_exact_file(s,sha(original_target)), 'native_layout_path_alias')
    w,s,i,t = asset_fixture('writable_source')
    s.chmod(0o666)
    refuses('writable_source',lambda:m.read_exact_file(s,sha(s)), 'native_layout_source_file')
    w,s,i,t = asset_fixture('duplicate_index')
    j=json.loads(i.read_text());j['files']*=2;i.write_text(json.dumps(j))
    refuses('duplicate_asset',lambda:m.stage_code(w,i,sha(i)), 'native_layout_duplicate_member')
    assert not (w/'code').exists()
    w,s,i,t = asset_fixture('corrupt_index')
    old=sha(i);i.write_text(i.read_text()+' ')
    refuses('index_hash_drift',lambda:m.stage_code(w,i,old), 'native_layout_source_hash')
    w,s,i,t = asset_fixture('nested_positive')
    a=i.parent
    (a/'sub').mkdir(mode=0o700);(a/'sub/entry.py').write_bytes(b'# child\n')
    j={'schema':'frw.calc.native-code-generation.v1','entry':'entry.py','files':[
        {'relative':'entry.py','sha256':sha(a/'entry.py')},
        {'relative':'sub/entry.py','sha256':sha(a/'sub/entry.py')}]}
    i.write_text(json.dumps(j))
    # Staging nested source directories must retain private ownership/modes.
    nested=m.stage_code(w,i,sha(i));assert (nested.directory/'sub/entry.py').exists()
    results.append({'name':'nested_protected_source_generation','result':'SOURCE_PASS'})
    for name,mutate,reason in [
        ('extra_code_file',lambda d:(d/'unindexed.py').write_bytes(b'# unindexed\n'),'native_layout_unindexed_file'),
        ('extra_code_directory',lambda d:(d/'unindexed').mkdir(mode=0o700),'native_layout_unindexed_directory'),
        ('extra_code_symlink',lambda d:(d/'alias.py').symlink_to(d/'entry.py'),'native_layout_generation_type')]:
        w,s,i,t=asset_fixture(name)
        generation=m.stage_code(w,i,sha(i));mutate(generation.directory)
        refuses(name,lambda:m.namespace_argv(w,t,generation,source_sha256=sha(s),source_bytes=s.stat().st_size),reason)
    w,s,i,t=asset_fixture('writable_toolchain_mode')
    generation=m.stage_code(w,i,sha(i));t.chmod(0o700)
    refuses('writable_toolchain_mode',lambda:m.namespace_argv(w,t,generation,source_sha256=sha(s),source_bytes=s.stat().st_size),'native_layout_managed_toolchain')
    w,s,i,t=asset_fixture('toolchain_beneath_work')
    generation=m.stage_code(w,i,sha(i));nested_t=w/'toolchain';t.chmod(0o700);t.rename(nested_t);nested_t.chmod(0o500)
    refuses('toolchain_beneath_work',lambda:m.namespace_argv(w,nested_t,generation,source_sha256=sha(s),source_bytes=s.stat().st_size),'native_layout_toolchain_work_overlap')
    w,s,i,t=asset_fixture('work_beneath_toolchain')
    generation=m.stage_code(w,i,sha(i));t.chmod(0o700);nested_w=t/'work';w.rename(nested_w);t.chmod(0o500)
    refuses('work_beneath_toolchain',lambda:m.namespace_argv(nested_w,t,replace(generation,directory=nested_w/'code'),source_sha256=sha(nested_w/'input.ods'),source_bytes=(nested_w/'input.ods').stat().st_size),'native_layout_toolchain_work_overlap')
    assert os.getpid() != 1
    refuses('native_limits_cannot_touch_host_process',m.apply_child_limits,'native_layout_namespace_init_required')
    result={'schema':'frw.Root.native-layout.source-controls.v1','at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
            'module_ref':{'path':str(MODULE),'sha256':sha(MODULE)},'source_controls':results,
            'control_count':len(results),'all_passed':True,'scope':'Real filesystem source staging and pure namespace argv only; synthetic non-Office source/toolchain vectors. No namespace/Office/UNO/GDB/native/producer/render/send or RLIMIT mutation executed.',
            'actual_M':None,'runtime_readiness':False,'whole_factory_implemented':False,
            'actual_toolchain_nearest_consumer':actual_toolchain,
            'R1_preserved':'R1 controls passed only their synthetic0700 toolchain domain and missed actual _toolchain compatibility; independent review required3 source repairs, not a runtime failure.'}
finally:
    for owned in root.rglob('*'):
        if owned.is_dir() and not owned.is_symlink():
            assert owned.resolve().is_relative_to(root) and owned.stat().st_uid == os.getuid()
            owned.chmod(0o700)
    shutil.rmtree(root)
result['source_fixture_removed']=not root.exists()
out=P/'NATIVE-LAYOUT-R2-SOURCE-CONTROLS.json'
with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'result':str(out),'sha256':sha(out),'controls':len(results),'actor':False,'fixture_removed':not root.exists()}))
