from pathlib import Path
import ast,difflib,hashlib,json,os
os.umask(0o077)
B=Path(__file__).resolve().parent/'ordinary-edge'
SRC=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112')
native={'tools/scoped_odf_password.py': ('ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae', 'b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d', 28189, False)}
const="CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v9'\nCURRENT_SOURCE_NINTH_LAYER = 'f06-modern-odt-authenticated-profile-after-source206'\nCURRENT_SOURCE_NINTH_MANIFEST = '76121597cdc8a366239ba5f9ad1c58b434943e267bfe72a2faf6525ba3d6237e'\nCURRENT_SOURCE_NINTH_PATCH = 'fb80e67986642c3ae9b830ebc66f2815396575463400d65a7c65c6a41f9aa4b8'\nCURRENT_SOURCE_NINTH_NATIVE = "+repr(native)+"\n"
changes={}
for flavour,sub,expected in [('public','public','40a404292832b258e48c4f5af7bac3fdf263ce30a4077bde0af0ab8eaed0a174'),('private','project493','489f6a23a4015bbb1daad9c405028b83e55b10725cd4f5e8b56ce678ee6e1eb9')]:
 src=SRC/sub/'scripts/friday_ordinary_install.py'; old=src.read_text();assert hashlib.sha256(src.read_bytes()).hexdigest()==expected
 s=old
 def replace(a,b):
  global s
  assert s.count(a)==1,(flavour,a[:100],s.count(a))
  s=s.replace(a,b)
 replace('# At most eight authenticated native CP edges','# At most nine authenticated native CP edges')
 replace("CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v8'\n",const+"CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v8'\n")
 start=s.index('_CURRENT_SOURCE_EIGHTH_HISTORY_SEAL = object()')
 end=s.index('\n_CURRENT_SOURCE_SEVENTH_HISTORY_SEAL',start)
 hist=s[start:end].replace('EIGHTH','NINTH').replace('Eighth','Ninth').replace('eighth','ninth').replace('CP205','CP206').replace('seventh_reference','eighth_reference').replace('sixth_reference','seventh_reference')
 s=s[:start]+hist+'\n'+s[start:]
 start=s.index('def _current_source_eighth_successor_checked')
 end=s.index('\ndef _current_source_seventh_successor_checked',start)
 wrapper=s[start:end]
 # Derive the fixed v8 wrapper from the existing fixed v7 wrapper.
 ninth=wrapper.replace('EIGHTH','NINTH').replace('Eighth','Ninth').replace('eighth','ninth').replace('SEVENTH','EIGHTH').replace('Seventh','Eighth').replace('seventh','eighth')
 ninth=ninth.replace('CP205 -> selected CP206','CP205 -> CP206 -> selected CP207').replace('Historical CP205','Historical CP206')
 s=s[:start]+ninth+'\n'+s[start:]
 replace('def _current_source_eighth_successor_checked(value, request, *, cli_only, source_update):','def _current_source_eighth_successor_checked(value, request, *, cli_only, source_update,\n        historical_marker=None, _ninth_history=None):')
 # The ninth wrapper must mint its sealed proof; the now historical-capable eighth must require it.
 start=s.index('def _current_source_eighth_successor_checked')
 end=s.index('\ndef _current_source_seventh_successor_checked',start)
 eighth=s[start:end]
 eighth=eighth.replace("    marker = _current_source_json(home/f.MARKER)\n", "    f.require(historical_marker is None or type(_ninth_history) is _CurrentSourceNinthHistory\n        and _ninth_history._seal is _CURRENT_SOURCE_NINTH_HISTORY_SEAL,\n        'ordinary_current_successor_internal_ninth_history_required')\n    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)\n")
 eighth=eighth.replace('        source_update=source_update,prior_edge=seventh)','        source_update=source_update,prior_edge=seventh,\n        historical_marker=historical_marker,_ninth_history=_ninth_history)')
 s=s[:start]+eighth+s[end:]
 replace('"""The v6 root and eight fixed authenticated native CP edges."""','"""The v6 root and nine fixed authenticated native CP edges."""')
 replace("    if context.get('schema') == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA:\n", "    if context.get('schema') == CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA:\n        return _current_source_ninth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)\n    if context.get('schema') == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA:\n")
 replace('_seventh_history=None, _eighth_history=None):','_seventh_history=None, _eighth_history=None, _ninth_history=None):')
 replace("    eighth = continuation and context.get('schema') == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA", "    ninth = continuation and context.get('schema') == CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA\n    eighth = continuation and context.get('schema') == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA")
 replace('second = continuation and not third and not fourth and not fifth and not sixth and not seventh and not eighth','second = continuation and not third and not fourth and not fifth and not sixth and not seventh and not eighth and not ninth')
 replace("and context['schema'] == (CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA if eighth else", "and context['schema'] == (CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA if ninth else\n            CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA if eighth else")
 replace('(CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA if eighth else','(CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA if ninth else\n                CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA if eighth else')
 replace('        and not (eighth and historical_marker is not None)','        and not (ninth and historical_marker is not None)\n        and (not (eighth and historical_marker is not None) or\n            type(_ninth_history) is _CurrentSourceNinthHistory\n            and _ninth_history._seal is _CURRENT_SOURCE_NINTH_HISTORY_SEAL)')
 start=s.index('    if seventh and historical_marker is not None:',s.index('def _current_native_source_edge_checked'))
 end=s.index('    root_request,previous = ',start)
 seventhbinding=s[start:end]
 eighthbinding=seventhbinding.replace('seventh','eighth').replace('Seventh','Eighth').replace('SEVENTH','EIGHTH').replace('_eighth_history','_ninth_history').replace('eighth_reference','eighth_reference').replace('sixth_reference','seventh_reference').replace('CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA,','CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,').replace('CP205','CP206').replace('CP204','CP205').replace("selected eighth's","selected ninth's")
 # selected-context reference label remains the just-authenticated eighth transaction.
 eighthbinding=eighthbinding.replace('ordinary_current_successor_authenticated_ninth_history_required','ordinary_current_successor_authenticated_eighth_history_required')
 s=s[:end]+eighthbinding+s[end:]
 replace('before_layers = 205 if eighth else','before_layers = 206 if ninth else 205 if eighth else')
 replace('before_native_count = 17891 if eighth or seventh or sixth else','before_native_count = 17891 if ninth or eighth or seventh or sixth else')
 replace('before_project_count = 491 if eighth else','before_project_count = 493 if ninth else 491 if eighth else')
 replace("    f.require(not eighth or names == [CURRENT_SOURCE_EIGHTH_LAYER],\n        'ordinary_current_successor_exact_eighth_layer_required')", "    f.require(not ninth or names == [CURRENT_SOURCE_NINTH_LAYER],\n        'ordinary_current_successor_exact_ninth_layer_required')\n    f.require(not eighth or names == [CURRENT_SOURCE_EIGHTH_LAYER],\n        'ordinary_current_successor_exact_eighth_layer_required')")
 replace("    f.require(not eighth or changes == {PROJECT_DSH_CURRENT_HELPER},", "    f.require(not ninth or changes == {PROJECT_DSH_CURRENT_HELPER},\n        'ordinary_current_successor_exact_ninth_helper_scope_required')\n    f.require(not eighth or changes == {PROJECT_DSH_CURRENT_HELPER},")
 replace("        'ordinary_current_successor_exact_eighth_layer_images_required')\n    for name,expected in files.items():\n", "        'ordinary_current_successor_exact_eighth_layer_images_required')\n    f.require(not ninth or (files.get(manifest_name) == CURRENT_SOURCE_NINTH_MANIFEST\n        and files.get(patch_name) == CURRENT_SOURCE_NINTH_PATCH),\n        'ordinary_current_successor_exact_ninth_layer_images_required')\n    for name,expected in files.items():\n")
 replace("    for row in rows:\n        name = row['path']; prior = expected_files.get(name)", "    f.require(not ninth or {row['path'] for row in rows} == set(CURRENT_SOURCE_NINTH_NATIVE),\n        'ordinary_current_successor_exact_ninth_native_scope_required')\n    for row in rows:\n        name = row['path']; prior = expected_files.get(name)")
 replace("        after = dict(prior) if prior is not None else {}\n", "        if ninth:\n            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_NINTH_NATIVE[name],\n                'ordinary_current_successor_exact_ninth_native_images_required')\n        after = dict(prior) if prior is not None else {}\n")
 replace("    expected_receipt['layers'].append({'manifest':manifest_name,'manifest_sha256':files[manifest_name],", "    f.require(not ninth or len(expected_files) == 17891,\n        'ordinary_current_successor_exact_ninth_native_count_required')\n    expected_receipt['layers'].append({'manifest':manifest_name,'manifest_sha256':files[manifest_name],")
 ast.parse(s)
 dest=B/flavour/'scripts/friday_ordinary_install.py';dest.parent.mkdir(mode=0o700,parents=True,exist_ok=True);dest.write_text(s);dest.chmod(0o600)
 (B/(flavour+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/scripts/friday_ordinary_install.py',tofile='b/scripts/friday_ordinary_install.py')))
 changes[flavour]={'source':str(src),'source_sha256':expected,'candidate':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(B/'SOURCES.json').write_text(json.dumps(changes,indent=2)+'\n')
print(json.dumps(changes,indent=2))
