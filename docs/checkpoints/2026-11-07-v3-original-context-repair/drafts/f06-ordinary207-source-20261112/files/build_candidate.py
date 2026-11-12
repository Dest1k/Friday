"""Finite source copy/adaptation only. Never imports installed product or observes it."""
import ast
import hashlib
import json
import os
from pathlib import Path

W = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY-SINGLETON-SOURCE-20261112')
OUT = Path(__file__).resolve().parent
CLOSURE = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/CORE207-ACTUAL-INSTALLED-CLOSED-20261112.json')
CLOSURE_SHA = '996b43c584c8eb6d5c8dbbeb60f500958c873427cda0881ae74a7618d920f963'
os.umask(0o077)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)+'\n').encode()

def save(name, raw):
    p = OUT/name
    p.write_bytes(raw)
    p.chmod(0o600)

def replace(text, before, after, count=1):
    assert text.count(before)==count, (before,text.count(before),count)
    return text.replace(before,after)

freeze_raw=(W/'SOURCE-FREEZE-R3.json').read_bytes()
assert digest(freeze_raw)=='0a18e6b90c18b06441c2905595f02f35c17bf16a8a304628cad9c06a0e726151'
freeze=json.loads(freeze_raw)
closure_raw=CLOSURE.read_bytes()
assert digest(closure_raw)==CLOSURE_SHA
closure=json.loads(closure_raw)
assert closure['state']=='INSTALLED207_PROJECT495_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'
assert closure['installed']['canonical4']['source_receipt']['sha256']=='faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b'
assert closure['installed']['canonical4']['current_input']['sha256']=='c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'
for leaf in ('f06_source.py','current206.py','f06_footer.py.txt','root_bind_dispatch_once.py'):
    raw=(W/leaf).read_bytes()
    assert digest(raw)==freeze['files'][leaf]['sha256'] and len(raw)==freeze['files'][leaf]['bytes'],leaf

text=(W/'f06_source.py').read_text()
text=replace(text,"'source_layers':206,'project_files':493", "'source_layers':207,'project_files':495")
text=replace(text,'F06_GENUINE206_COUNTS_REQUIRED','F06_GENUINE207_COUNTS_REQUIRED')
text=replace(text,'F06_ROOT_ACTUAL206_UNBOUND','F06_ROOT_ACTUAL207_UNBOUND')
save('f06_source.py',text.encode())

text=(W/'current206.py').read_text()
text=text.replace('206','207').replace('493','495')
text=replace(text,"CLOSURE_SHA = '20e1a9ca845f52eeb0b6a149acc47fd91c9bc70142140e18095acdf18476b900'",
             "CLOSURE_SHA = '"+CLOSURE_SHA+"'")
text=replace(text,'253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21',
             'faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b')
text=replace(text,'e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39',
             'c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838')
text=replace(text,"'tools/scoped_odf_password.py':'ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae'",
             "'tools/scoped_odf_password.py':'b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d'")
save('current207.py',text.encode())

text=(W/'root_bind_dispatch_once.py').read_text()
text=replace(text,"'Root_first_F06_current206'","'Root_first_F06_current207'")
save('root_bind_dispatch_once.py',text.encode())
save('f06_footer.py.txt',(W/'f06_footer.py.txt').read_bytes())
for leaf in ('SCENARIO.UNBOUND.json','ROOT-CLOCK.UNBOUND.json'):
    save(leaf,(W/leaf).read_bytes())

def source_module(leaf):
    import types
    p=OUT/leaf
    module=types.ModuleType('_inert_'+leaf.replace('.','_'))
    module.__file__=str(p)
    exec(compile(p.read_bytes(),str(p),'exec'),module.__dict__)
    return module

a=source_module('f06_source.py')
m=source_module('current207.py')
save('CONTRACT.UNBOUND.json',encoded(a.unbound()))
save('CURRENT207-PROOF.UNBOUND.json',encoded(m.unbound_proof()))
binding=json.loads((W/'ROOT-BINDING-INPUTS.UNBOUND.json').read_bytes())
binding['contract']=a.unbound()
save('ROOT-BINDING-INPUTS.UNBOUND.json',encoded(binding))
reviews=json.loads((W/'ROOT-REVIEW-TEMPLATES.UNBOUND.json').read_bytes())
def adapt(v):
    if isinstance(v,dict):return {k:adapt(x) for k,x in v.items()}
    if isinstance(v,list):return [adapt(x) for x in v]
    if type(v) is str:return v.replace('installed206-runtime','installed207-runtime')
    return v
reviews=adapt(reviews)
reviews['runtime_privacy_review']['installed_product']=dict(m.EXPECTED)
reviews['runtime_privacy_review']['runtime_hashes']=dict(m.RUNTIME_HASHES)
save('ROOT-REVIEW-TEMPLATES.UNBOUND.json',encoded(reviews))
save('VERSION-PINS.ACTUAL-ROOT-CLOSURE.json',encoded(dict(
    schema='frw.F06.ordinary207-source-version-pins.v1',status='SOURCE_ONLY_EXACT_ROOT_CLOSED207_METADATA_PINNED',
    expected_product=m.EXPECTED,closure_path=str(m.CLOSURE),actual_closure_sha256=CLOSURE_SHA,
    only_runtime_hash_delta={'tools/scoped_odf_password.py':{
        'before':'ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae',
        'after':'b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d'}},
    original_R3_freeze_sha256=digest(freeze_raw),actual_runtime_admission_or_effect=False)))
print(json.dumps({'state':'SOURCE_CANDIDATE_PREPARED_ACTUAL_ROOT_CLOSED207_PINNED','source_files':4}))
