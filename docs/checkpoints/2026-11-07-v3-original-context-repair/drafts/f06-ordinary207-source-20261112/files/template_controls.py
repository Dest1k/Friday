"""Template-only regression after independent stale206 nested pins finding."""
import hashlib,json,os,types
from pathlib import Path
os.umask(0o077)
P=Path(__file__).resolve().parent
p=P/'current207.py';m=types.ModuleType('inert_current207');m.__file__=str(p)
exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
v=json.loads((P/'ROOT-REVIEW-TEMPLATES.UNBOUND.json').read_bytes())
privacy=v['runtime_privacy_review']
assert privacy['schema']=='frw.Root.F06.installed207-runtime-privacy-review.v1'
assert privacy['installed_product']==m.EXPECTED
assert privacy['runtime_hashes']==m.RUNTIME_HASHES
flags=['genuine_installed_runtime_consumer_observed','no_marker_or_import_bypass','raw_user_chat_retention_separately_reviewed','no_blanket_no_secret_persistence_claim']
assert all(privacy[k] is None for k in flags)
assert privacy['status']=='UNBOUND_NOT_GRANTED' and v['status']=='UNBOUND_NO_AUTHORITY'
assert privacy['Standard3_2_data_integrity_verified'] is False
old=json.loads((P/'ROOT-REVIEW-TEMPLATES.PRE-FIX.UNBOUND.json').read_bytes())
old['runtime_privacy_review']['installed_product']=m.EXPECTED
old['runtime_privacy_review']['runtime_hashes']=m.RUNTIME_HASHES
assert old==v
result={'schema':'frw.F06.ordinary207-template-regression.v1','status':'PASS_SOURCE_ONLY','checks':6,'regression':'Independent review found nested installed_product/runtime_hashes still206 under adapted207 schema; corrected only those static expected pins.','actual_Root_judgment_defaults_all_null':True,'only_nested_expected_product_and_runtime_hashes_changed':True,'current207_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'template_sha256':hashlib.sha256((P/'ROOT-REVIEW-TEMPLATES.UNBOUND.json').read_bytes()).hexdigest(),'unchanged_version30_controls_rerun':False,'external_reads_or_effects':0}
f=P/'TEMPLATE-CONTROLS.json';f.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');f.chmod(0o600)
print(json.dumps({'status':result['status'],'checks':result['checks']}))
