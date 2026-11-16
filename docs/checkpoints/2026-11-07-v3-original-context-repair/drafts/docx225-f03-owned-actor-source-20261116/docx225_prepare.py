"""F03 retained own-native DOCX request. Source-only until exact Root binding."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types

SELECTED_TESTER='/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py'
SELECTED_SHA='cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
SHARED={'path':'/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113/source/f07_phase_prepare.py','bytes':92510,'sha256':'6eb474ec654cb789be3a70ce783fa3abb40a4c6528a1b06b3afe376d721f6cb6'}
TIMING=dict(operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600)
PHASE_FIELDS = {'scenario', 'input_original', 'scenario_sha256', 'ordinal', 'phase', 'source_scope', 'expected_semantics', 'schema', 'timing', 'state'}
INPUT_FIELDS={'path','bytes','sha256','stat'}
STAT_FIELDS={'ctime_ns','device','inode','mtime_ns','size_bytes','uid'}
MIME='application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def need(ok,code):
 if not ok:raise ValueError(code)

def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def clone(v):return json.loads(encoded(v))
def same(a,b):return encoded(a)==encoded(b)
def sha(v):return type(v) is str and re.fullmatch('[a-f0-9]{64}',v) is not None

def canonical_path(v):
 need(type(v) is str and v.startswith('/') and not v.startswith('//') and str(Path(v))==v
      and all(p not in ('','.','..') for p in v.split('/')[1:])
      and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in v),'WORD_CANONICAL_PATH_REQUIRED')
 v.encode('utf-8');return Path(v)

def reference_shape(v):
 return (type(v) is dict and set(v)=={'path','bytes','sha256'} and canonical_path(v['path']).is_absolute()
         and type(v['bytes']) is int and 0<v['bytes']<=24*1024**2 and sha(v['sha256']))

def load_pinned(reference,reader):
 raw=reader(reference)
 need(type(raw) is bytes and len(raw)==reference['bytes'] and digest(raw)==reference['sha256'],'WORD_PINNED_SOURCE_CHANGED')
 m=types.ModuleType('_word_exact_shared_source');m.__file__=reference['path']
 exec(compile(raw,m.__file__,'exec'),m.__dict__);return m


def source_bytes(reference):
 path=canonical_path(reference['path'])
 need(reference_shape(reference) and not any(p.is_symlink() for p in (path,*path.parents)), 'WORD_SOURCE_LINK_REFUSED')
 with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
  before=os.fstat(stream.fileno());raw=stream.read(reference['bytes']+1);after=os.fstat(stream.fileno())
 identity=lambda s:tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
 need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
      and not stat.S_IMODE(before.st_mode)&0o002 and identity(before)==identity(after)==identity(path.stat())
      and len(raw)==reference['bytes'] and digest(raw)==reference['sha256'],'WORD_SOURCE_CUSTODY_CHANGED')
 return raw



SOURCE_KIND='OWN_USER_WORKSPACE_NATIVE_OUTPUT_NOT_RECEIVED'
SOURCE_SHA='1c95836b4d65b30488d8289c629bcea2835382136b85a324bde042198c900ebb'
SOURCE_BYTES=8791
SOURCE_NAME='Mayak_v1_structured_original_converted.docx'
OUTPUT_NAME='Mayak_v1_structured_deadline_23.docx'
LEAF = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX-F03-ORDINARY-SOURCE-RECIPE-20261116/source/docx_f03_prepare.py', 'bytes': 7551, 'sha256': '833cf8318c9938ce56ab1d0b5311c49a8287f233b85a535b3eb1a02d5fcd3f25'}
OBLIGATION=dict(case_id='F-03',case_index=164,operation_pointer='/operation_rows/9',
 source_kind=SOURCE_KIND,source_sha256=SOURCE_SHA,source_name=SOURCE_NAME,output_name=OUTPUT_NAME,
 selection_part='word/document.xml',literal_before='Срок сдачи: 22 октября 2026 года.',
 literal_after='Срок сдачи: 23 октября 2026 года.',maximum_trials=1,
 no_old_diagnostic_or_benchmark_replay=True)
SCOPE_KEYS={'workspace_root','destination_path','principal','source_kind','access_evidence'}
PRINCIPAL=dict(id='20261030_093055_43bba39f',source='telegram',user_id='8812646969',
 chat_id='8812646969',chat_type='dm',session_key='agent:telegram-bot-8812646969:telegram:dm:8812646969',
 profile_name='telegram-bot-8812646969',transport_profile='default')


def validate_input(original):
 need(type(original) is dict and set(original)==INPUT_FIELDS
      and canonical_path(original['path']).name==SOURCE_NAME
      and original['bytes']==SOURCE_BYTES and original['sha256']==SOURCE_SHA,
      'DOCX225_EXACT_OWN_NATIVE_INPUT_REQUIRED')
 s=original['stat']
 need(type(s) is dict and set(s)==STAT_FIELDS and all(type(v) is int and v>=0 for v in s.values())
      and s['inode']>0 and s['size_bytes']==SOURCE_BYTES and s['uid']==os.getuid(),
      'DOCX225_ROOT_FRESH_INPUT_STAT_REQUIRED')
 return original


def validate_preparation(phase):
 need(type(phase) is dict and set(phase)==PHASE_FIELDS
      and phase['schema']=='frw.DOCX225.F03-retained-preparation.v1'
      and phase['state']=='SOURCE_ONLY_UNBOUND_NOT_GRANTED' and phase['phase']=='F03_DOCX_BODY_ONE_FACT'
      and type(phase['ordinal']) is int and phase['ordinal']==1 and same(phase['timing'],TIMING)
      and phase['expected_semantics']=='original_F03_single_BODY_deadline_22_to_23_source_preserved'
      and phase['scenario_sha256']==digest(encoded(phase['scenario'])), 'DOCX225_EXACT_PREPARATION_REQUIRED')
 validate_input(phase['input_original'])
 scope=phase['source_scope'];source=canonical_path(phase['input_original']['path'])
 need(type(scope) is dict and set(scope)==SCOPE_KEYS and scope['source_kind']==SOURCE_KIND
      and scope['principal']==PRINCIPAL and type(scope['access_evidence']) is list and bool(scope['access_evidence']),
      'DOCX225_ROOT_CURRENT_OWN_WORKSPACE_SCOPE_REQUIRED')
 root=canonical_path(scope['workspace_root']);destination=canonical_path(scope['destination_path'])
 need(root==Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')/'profiles'/PRINCIPAL['profile_name']/'workspace'
      and source.parent==root and destination==root/OUTPUT_NAME and source!=destination,
      'DOCX225_SAME_OWN_WORKSPACE_SOURCE_CREATE_ONLY_DESTINATION_REQUIRED')
 for r in scope['access_evidence']:need(reference_shape(r),'DOCX225_CURRENT_ACCESS_SOURCE_EVIDENCE_REQUIRED')
 leaf=load_pinned(LEAF,source_bytes)
 s=phase['scenario'];expected=leaf.scenario_data(tester_id=s.get('tester_id'),peer_id=s.get('peer_id'),peer_username=s.get('peer_username'))
 need(same(s,expected),'DOCX225_EXACT_REQUEST_ONLY_SCENARIO_REQUIRED')
 return True


def preparation(*,scenario,input_original,source_scope):
 phase=dict(schema='frw.DOCX225.F03-retained-preparation.v1',state='SOURCE_ONLY_UNBOUND_NOT_GRANTED',
  phase='F03_DOCX_BODY_ONE_FACT',ordinal=1,scenario=clone(scenario),scenario_sha256=digest(encoded(scenario)),
  timing=clone(TIMING),input_original=clone(input_original),source_scope=clone(source_scope),
  expected_semantics='original_F03_single_BODY_deadline_22_to_23_source_preserved')
 validate_preparation(phase);return phase


def authority_shape(authority,reference,*,run_id,phase):
 validate_preparation(phase)
 need(reference_shape(reference) and reference['bytes']==len(encoded(authority))
      and reference['sha256']==digest(encoded(authority)),'DOCX225_EXACT_ROOT_AUTHORITY_REF_REQUIRED')
 need(same(authority.get('docx_original_case'),OBLIGATION)
      and same(authority.get('docx_input_original'),phase['input_original'])
      and same(authority.get('docx_source_scope'),phase['source_scope'])
      and reference_shape(authority.get('word_scenario'))
      and authority['word_scenario']['sha256']==phase['scenario_sha256']
      and authority['word_scenario']['bytes']==len(encoded(phase['scenario'])),
      'DOCX225_EXPLICIT_ROOT_F03_OWN_NATIVE_SCOPE_REQUIRED')
 return True


HISTORY_READONLY_COMPAT = {'path': '/home/jericho/.cache/FRW-ASTRA-DOCX-F03-OWNED-ACTOR-ROOT-INPUTS-20261116/operational-source/history_compat.source-limit-r2.py', 'bytes': 7836, 'sha256': '0f1ff7f29b8f63a099b983756c21756fc8ec35b4e002e28979441ae67af3b9cf'}


def compose_source(base_raw,phase,*,run_id,authority_ref,authority,input_original=None,shared_module=None):
 validate_preparation(phase);authority_shape(authority,authority_ref,run_id=run_id,phase=phase)
 need(input_original is None or same(input_original,phase['input_original']),'DOCX225_ORIGINAL_INPUT_CHANGED')
 need(shared_module is None,'DOCX225_ONLY_PINNED_HISTORY_COMPAT_ALLOWED')
 leaf=load_pinned(LEAF,source_bytes);shared_raw=source_bytes(SHARED)
 ordinary=leaf.compose_source(base_raw,shared_raw,scenario=phase['scenario'],run_id=run_id,
  authority=authority,authority_ref=authority_ref)
 history=load_pinned(HISTORY_READONLY_COMPAT,source_bytes)
 return history.compose_source(ordinary)


def qualify_selected_ordinary_readonly(runner,*,run_id,phase):
 validate_preparation(phase);need(runner.api is None,'DOCX225_READONLY_API_MUST_BE_NONE')
 result=runner._f07_qualify_new_prefix_readonly(run_id,phase['scenario'])
 admission=runner.ordinary_independent_admission(run_id,phase['scenario'])
 need(admission is not None,'DOCX225_EXACT_ORDINARY_ADMISSION_REQUIRED')
 runner.ordinary_independent_current_rows(admission,run_id)
 need(result['scenario_sha256']==phase['scenario_sha256'],'DOCX225_READONLY_SCENARIO_CHANGED')
 return dict(state='WHOLE_DOCX225_PRE_SAVE_READONLY_QUALIFIED_NOT_ADMISSION',original_new_prefix=result,
  input_original=clone(phase['input_original']),source_kind=SOURCE_KIND,upload=False,
  new_called=False,save_called=False,API_called=False,send_called=False,
  once_claim_created=False,operation_clock_created=False)


def effect_domain(phase):
 validate_preparation(phase)
 return dict(original_case=clone(OBLIGATION),source_path=phase['input_original']['path'],
  destination_path=phase['source_scope']['destination_path'],source_kind=SOURCE_KIND,
  principal=clone(PRINCIPAL),scenario_sha256=phase['scenario_sha256'])
