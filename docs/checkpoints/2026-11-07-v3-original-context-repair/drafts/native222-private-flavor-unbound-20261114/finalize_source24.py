"""Inert Root binding seam for v24. Byte inputs only; no authority or side effects.

Caller supplies frozen reviewed artifacts and a fresh external currentness decision.
This validates consistency, not permission. Never calls build/prepare/update/process.
"""
from __future__ import annotations
import ast
import hashlib
import json
import math
from pathlib import PurePosixPath

TEMPLATE_SHA256='3e6d5d522d8c0de1d69d0c68138810d088ab17fdde9eda430646996a9ee962c1'
PRIVATE_TEMPLATE_SHA256='6c9c7e06dc2e317bb4fc369692e890f2e64886fe878d5ea2dce65a8fc2b5348f'
PUBLIC_BASE_SHA256='a281dafffc509974ed6f40bfe5cef7e21f86838f00173f1c9227f05e5c4939a8'
PRIVATE_BASE_SHA256='e4c4e33d07fd370c62ada08c67c6fafe42c64228a54c6b73fcb947d893b598d9'
EXPORT_SHA256='20d0f3a5cea9efd37deb6d91994d366ad367715e752dd6327e025d2f0f02447d'
PINS={'request':'0c04fac41fed1ddbe4c4e7c12140f5caecf6f8bc904cddff66b00235411f2141',
 'input':'60d879571771e861df8441a02489cb74bf8d8707e2f14e0ae3448b81ed87504d',
 'source_receipt':'a4d278c67b044b684c3182107947bdb9d82a592b54924d9a5bb283fc11ac1d40',
 'stamp':'042fc36fff478ad14504ff02745fdbfbe739746a5d33247cc1de6aa641e3bf49',
 'marker':'b309597c8de460f1cb01a4bf64c0a42d5c4aafe2f8de66752ff218ce31c77bdb',
 'intent':'f496e7ef47c79b680a38d7f403117139f8121cfcb332eebbe45a6fd6bbe1841d',
 'committed':'69324c6e414db897038d5edb9e5a9222e49e93051e936443e40e319503e43978'}
class Refused(ValueError):pass
def require(condition,reason):
 if not condition:raise Refused(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def exact(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def load(raw):
 require(type(raw) is bytes and len(raw)<=16*1024**2,'bounded_json_bytes_required')
 def unique(rows):
  out={}
  for k,v in rows:require(k not in out,'duplicate_json_key');out[k]=v
  return out
 def reject(value):raise Refused('nonfinite_json')
 def float_value(value):
  result=float(value);require(math.isfinite(result),'nonfinite_json');return result
 return json.loads(raw,object_pairs_hook=unique,parse_constant=reject,parse_float=float_value)
def hex64(value):return type(value) is str and len(value)==64 and set(value)<=set('0123456789abcdef')
def relative(value):
 require(type(value) is str and value and '\\' not in value,'relative_path_required')
 p=PurePosixPath(value)
 require(bool(p.parts) and not p.is_absolute() and p.as_posix()==value and not any(x in ('.','..','.git') for x in p.parts),'relative_path_required')
 return value

def predecessor_checked(export_raw, copies):
 """Validate exported actual221 shapes without reopening any original path."""
 require(sha(export_raw)==EXPORT_SHA256,'actual221_export_changed')
 export=load(export_raw)
 require(type(copies) is dict and set(copies)==set(PINS),'exact_seven_actual221_copies_required')
 docs={}
 for key,pin in PINS.items():
  require(type(copies[key]) is bytes and sha(copies[key])==pin==export['inputs'][key]['copy']['sha256']==export['inputs'][key]['original']['sha256'],'actual221_copy_changed_'+key)
  docs[key]=load(copies[key])
 req=docs['request'];inp=docs['input'];intent=docs['intent'];commit=docs['committed'];receipt=docs['source_receipt'];stamp=docs['stamp'];marker=docs['marker']
 require(req['schema']=='friday.ordinary-telegram-source-update.v46' and req['current_source_successor']['schema']=='friday.current-source-native-successor.v23','actual221_schema_required')
 ref={'path':export['inputs']['request']['original']['path'],'sha256':PINS['request']}
 require(ref['path']==req['home']+'/preparation/ordinary-source-update-v45-'+PINS['request'][:16]+'/request.json','actual221_canonical_request_required')
 require(req['current_input']==req['candidate_input']=={'path':export['inputs']['input']['original']['path'],'sha256':PINS['input']} and req['current_input']!=req['previous_input'],'actual221_input_join_changed')
 require(len(inp['project_files'])==523 and inp['home']==req['home'] and inp['product']['runtime']=={'enabled':False},'actual221_typed_input_required')
 require(intent['state']=='SOURCE_UPDATE_INTENT' and commit['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED','actual221_committed_required')
 require(type(commit['seconds']) in (int,float) and math.isfinite(commit['seconds']) and 0<=commit['seconds']<=req['seconds'],'actual221_commit_duration_changed')
 for body in (intent,commit):
  require(body['request_reference']==ref and body['request_sha256']==PINS['request'] and body['current_input']==req['current_input'] and body['previous_input']==req['previous_input'] and body['current_source_successor']==req['current_source_successor'] and body['gateway_started'] is False and body['workers_enabled'] is False,'actual221_journal_join_changed')
 require(commit['source_receipt_sha256']==PINS['source_receipt'] and len(receipt['layers'])==221 and len(receipt['files'])==17893 and receipt['source_file_count']==17730,'actual221_receipt_join_changed')
 require(stamp['fridaySource']=={'baseTree':receipt['base_tree'],'layers':receipt['layers']} and stamp['commit']==receipt['commit'] and stamp['dirty'] is True,'actual221_stamp_join_changed')
 require(marker['home']==req['home'] and marker['input_sha256']==PINS['input'] and marker['source_receipt_sha256']==PINS['source_receipt'] and marker['ordinary_gateway']['source_receipt_sha256']==PINS['source_receipt'] and marker['ordinary_gateway']['operator_entry']['input']==req['current_input'] and len(marker['plugin_files'])==52,'actual221_marker_join_changed')
 return docs

def bind(template_raw,freeze_raw,manifest_raw,patch_raw,export_raw,copies,*,now,base_flavor='public'):
 """Produce bound source bytes only; Root still owns fresh admission and integration."""
 require(type(base_flavor) is str and base_flavor in ('public','actual221-private'),'explicit_known_base_flavor_required')
 template_pin=TEMPLATE_SHA256 if base_flavor=='public' else PRIVATE_TEMPLATE_SHA256
 require(type(template_raw) is bytes and sha(template_raw)==template_pin,'unbound_template_changed')
 docs=predecessor_checked(export_raw,copies);receipt=docs['source_receipt']
 freeze=load(freeze_raw)
 fields={'schema','template_sha256','predecessor_request_sha256','predecessor_input_sha256','predecessor_receipt_sha256','layer_name','manifest_sha256','patch_sha256','created_at','expires_at'}
 require(type(freeze) is dict and set(freeze)==fields and freeze['schema']=='friday.source-only-successor24-freeze.v1','exact_freeze_required')
 require(freeze['template_sha256']==template_pin and freeze['predecessor_request_sha256']==PINS['request'] and freeze['predecessor_input_sha256']==PINS['input'] and freeze['predecessor_receipt_sha256']==PINS['source_receipt'],'actual221_freeze_join_changed')
 require(type(now) in (int,float) and math.isfinite(now) and all(type(freeze[k]) in (int,float) and math.isfinite(freeze[k]) for k in ('created_at','expires_at')) and freeze['created_at']<=now<freeze['expires_at'],'freeze_expired_or_future')
 name=freeze['layer_name']
 require(type(name) is str and name and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name),'explicit_final_layer_name_required')
 manifest_name='patches/hermes/'+name+'-manifest.json';patch_name='patches/hermes/'+name+'.patch'
 require(manifest_name not in docs['input']['project_files'] and patch_name not in docs['input']['project_files'],'new_layer_required')
 require(type(manifest_raw) is bytes and type(patch_raw) is bytes and patch_raw and sha(manifest_raw)==freeze['manifest_sha256'] and sha(patch_raw)==freeze['patch_sha256'],'frozen_artifact_changed')
 manifest=load(manifest_raw)
 require(type(manifest) is dict and manifest.get('patch')==patch_name and manifest.get('patch_sha256')==sha(patch_raw) and manifest.get('base_commit')==receipt['commit'],'manifest_join_changed')
 prerequisites={row['manifest'].removesuffix('-manifest.json')+'.patch':row['patch_sha256'] for row in receipt['layers']}
 require(manifest.get('prerequisites')==prerequisites and len(prerequisites)==221,'exact_actual221_complete_prefix_required')
 rows=manifest.get('files');require(type(rows) is list and rows,'native_scope_required');native={}
 for row in rows:
  require(type(row) is dict and set(row)=={'path','before_sha256','sha256','bytes','mode','new_file'},'exact_native_row_required')
  path=relative(row['path']);require(path not in native,'duplicate_native_path')
  prior=receipt['files'].get(path)
  require(type(row['new_file']) is bool and row['new_file'] is (prior is None) and row['before_sha256']==(None if prior is None else prior['sha256']),'actual221_native_lineage_changed')
  require(hex64(row['sha256']) and row['sha256']!=row['before_sha256'] and type(row['bytes']) is int and row['bytes']>=0 and row['mode']=='100644','native_after_pin_required')
  native[path]=(row['before_sha256'],row['sha256'],row['bytes'],row['new_file'])
 text=template_raw.decode();bindings={'LAYER':name,'MANIFEST':sha(manifest_raw),'PATCH':sha(patch_raw),'NATIVE':native}
 for key,value in bindings.items():
  before='CURRENT_SOURCE_TWENTY_FOURTH_'+key+' = None'
  require(text.count(before)==1,'binding_seam_changed');text=text.replace(before,'CURRENT_SOURCE_TWENTY_FOURTH_'+key+' = '+repr(value))
 ast.parse(text)
 return text.encode(),{'schema':'friday.source-only-successor24-bindings.v1','authority_granted':False,'runtime_accepted':False,'base_flavor':base_flavor,'base_sha256':PUBLIC_BASE_SHA256 if base_flavor=='public' else PRIVATE_BASE_SHA256,'template_sha256':template_pin,'source_sha256':sha(text.encode()),'manifest':manifest_name,'manifest_sha256':sha(manifest_raw),'patch':patch_name,'patch_sha256':sha(patch_raw),'native':native,'after_native_count':17893+sum(int(row[3]) for row in native.values())}

CALLER_TEMPLATES={'build-layer-publication-request.py':'45a6b87117893028e0b3c71789e8d932555215cd493e6c3b2c114c608545c7ff','friday_v3_layer_publication.py':'ba135fdf5dd12b96d36aafe3b638ae65d8a877587eb4d84c2c30534ebd079dfd'}
def bind_callers(builder_raw,consumer_raw,*,layer_name):
    """Bind matching explicit builder/consumer name; historical defaults stay intact."""
    require(type(layer_name) is str and layer_name and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in layer_name),'explicit_final_layer_name_required')
    inputs={'build-layer-publication-request.py':builder_raw,'friday_v3_layer_publication.py':consumer_raw};outputs={}
    for name,raw in inputs.items():
        require(type(raw) is bytes and sha(raw)==CALLER_TEMPLATES[name],'caller_template_changed_'+name)
        text=raw.decode()
        if name.startswith('build'):
            old='CURRENT_SOURCE_TWENTY_FOURTH_LAYER = None';require(text.count(old)==1,'builder_binding_seam_changed')
            text=text.replace(old,'CURRENT_SOURCE_TWENTY_FOURTH_LAYER = '+repr(layer_name))
        else:
            tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LAYER_NAMES' for t in n.targets))
            names=ast.literal_eval(node.value);require(layer_name not in names,'existing_layer_refused')
            lines=text.splitlines(True);lines[node.end_lineno-1:node.end_lineno-1]=['    '+repr(layer_name)+',\n'];text=''.join(lines)
        ast.parse(text);outputs[name]=text.encode()
    return outputs

def finalize_package(template_raw,builder_raw,consumer_raw,freeze_raw,manifest_raw,patch_raw,export_raw,copies,*,now,base_flavor='public'):
    """Single coherent pure binding seam; returns bytes, never grants execution."""
    source,bindings=bind(template_raw,freeze_raw,manifest_raw,patch_raw,export_raw,copies,now=now,base_flavor=base_flavor)
    callers=bind_callers(builder_raw,consumer_raw,layer_name=load(freeze_raw)['layer_name'])
    outputs={'scripts/friday_ordinary_install.py':source,**callers}
    return outputs,{**bindings,'outputs':{name:sha(raw) for name,raw in outputs.items()},'effects_performed':False,'fresh_root_admission_required':True,'independent_final_binding_review_required':True}
