import ast,copy,hashlib,json,re,types,unittest
from pathlib import Path
B=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-UID-WITNESS-SOURCE-20261115')
SOURCE=B/'candidate/outer/deps/gpgme_boundary_collector.py'
tree=ast.parse(SOURCE.read_bytes())
names={'need','exact','integer','digest','validate_ns','parse_uid_map','_validate_projection_pin','project_host_owner','project_host_root','projection_failure_metadata'}
constants={'UID_WITNESS_SCHEMA','HOST_MAP_VIEW','SELF_MAP_VIEW','UID_MAP_BASIS','UID_WITNESS_KEYS'}
body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
clazz=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BoundaryCollector')
body += [ast.ClassDef(name='BoundaryCollector',bases=[],keywords=[],body=[n for n in clazz.body if isinstance(n,ast.FunctionDef) and n.name=='_projection'],decorator_list=[])]
policy=types.SimpleNamespace(sha=lambda v:type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None)
c=dict(copy=copy,hashlib=hashlib,re=re,policy=policy,os=types.SimpleNamespace(getpid=lambda:999999))
exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(SOURCE),'exec'),c)
HOST=dict(dev=4,ino=10);COL=dict(dev=4,ino=20)
def witness(raw=b'1000 1000 1\n'):
 return dict(schema=c['UID_WITNESS_SCHEMA'],host_map_view=c['HOST_MAP_VIEW'],self_map_view=c['SELF_MAP_VIEW'],mapping_basis=c['UID_MAP_BASIS'],host_uid_map_ascii=raw.decode(),root_host_uid_map_sha256=hashlib.sha256(raw).hexdigest(),overflowuid=65534,collector_userns=COL.copy(),host_userns=HOST.copy())
def obj():
 o=c['BoundaryCollector']();o.host_witness={};o.p=dict(operation={},original={},reaper={},uid_projection=witness())
 o._self_uid_map_sha256=None;o._uid_projection_failure=None;o._uid_projection_failure_attempted=False;o._ns=lambda pid:dict(user=COL.copy())
 o._read=lambda path,limit:b'1000 0 1\n' if path.endswith('/uid_map') else b'65534\n'
 o._publish_projection_failure=lambda value:None
 return o
class ReviewControls(unittest.TestCase):
 def test_nested_host_and_private_owner(self):
  p=c['project_host_root'](b'1000 0 1\n',65534,witness(),COL)
  self.assertEqual(p['actual_uid'],65534)
  self.assertEqual(c['project_host_owner'](c['parse_uid_map'](b'1000 1000 1\n'),1000,65534),1000)
 def test_range_offset_for_hostroot(self):
  w=witness(b'17 0 10\n')
  self.assertEqual(c['project_host_root'](b'17 500 10\n',65534,w,COL)['actual_uid'],17)
  self.assertEqual(c['project_host_owner'](c['parse_uid_map'](b'17 0 10\n'),6,65534),23)
 def test_mutation_of_self_parent_after_join_refuses(self):
  o=obj();o._projection();o._read=lambda p,l:b'1000 9 1\n' if p.endswith('/uid_map') else b'65534\n'
  with self.assertRaisesRegex(RuntimeError,'^gpgme_collector_uid_map_or_namespace_changed$'):o._projection()
 def test_different_namespace_identity_refuses(self):
  with self.assertRaisesRegex(RuntimeError,'uid_map_or_namespace_changed'):
   c['project_host_root'](b'1000 0 1\n',65534,witness(),dict(dev=4,ino=21))
 def test_host_map_digest_and_labels_refuse(self):
  for key,value in [('root_host_uid_map_sha256','0'*64),('mapping_basis',True),('host_map_view','SELF_TO_PARENT_USERNS')]:
   w=witness();w[key]=value
   with self.assertRaises(RuntimeError):c['project_host_root'](b'1000 0 1\n',65534,w,COL)
 def test_sentinel_outside_is_not_overflow_mapping(self):
  with self.assertRaisesRegex(RuntimeError,'uid_map_range'):c['parse_uid_map'](b'0 4294967295 1\n')
 def test_overflow_alias_rejected(self):
  with self.assertRaisesRegex(RuntimeError,'overflow_aliases_mapped_uid'):
   c['project_host_root'](b'65534 0 1\n',65534,witness(b'65534 1000 1\n'),COL)
 def test_boolean_numeric_refused(self):
  for val in (True,False):
   with self.assertRaises(RuntimeError):c['project_host_owner']([(0,0,1)],val,65534)
 def test_diagnostic_failure_preserves_original(self):
  o=obj();o._read=lambda p,l:b'1000 0 1\n' if p.endswith('/uid_map') else b'65535\n'
  o._publish_projection_failure=lambda value:(_ for _ in ()).throw(OSError('synthetic-only'))
  with self.assertRaisesRegex(RuntimeError,'^gpgme_collector_uid_map_or_namespace_changed$'):o._projection()
 def test_first_refusal_metadata_no_message(self):
  data=c['projection_failure_metadata'](b'1000 0 1\n',65535,witness(),COL,None,RuntimeError('SECRET'))
  self.assertNotIn('SECRET',json.dumps(data));self.assertLess(len(json.dumps(data)),8192)
 def test_construction_failure_recursive_bootstrap_attempt_count(self):
  o=obj();o.host_witness=None
  o._read=lambda p,l:b'1000 0 1\n' if p.endswith('/uid_map') else b'65535\n'
  def bind():o.host_witness={};o._projection()
  o._bind_host_witness=bind
  attempts=[];old=c['projection_failure_metadata']
  def failed(*args,**kwargs):attempts.append(1);raise OSError('synthetic construction')
  c['projection_failure_metadata']=failed
  try:
   with self.assertRaisesRegex(RuntimeError,'^gpgme_collector_uid_map_or_namespace_changed$'):o._projection()
  finally:c['projection_failure_metadata']=old
  self.assertEqual(len(attempts),1,'diagnostic construction must be attempted once, including recursive _bind_host_witness')
if __name__=='__main__':unittest.main(verbosity=2)
