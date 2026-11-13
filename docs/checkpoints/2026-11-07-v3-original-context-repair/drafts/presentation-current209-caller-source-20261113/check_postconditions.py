"""Finite nonsensitive synthetic saved-byte controls, never ordinary PASS."""
import copy
import hashlib
import io
import json
import pathlib
import resource
import time
import types
import zipfile

BASE=pathlib.Path(__file__).parent
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024**2,100*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
start=time.monotonic()
m=types.ModuleType('_postconditions_controls');m.__file__=str(BASE/'presentation_postconditions.py')
raw=pathlib.Path(m.__file__).read_bytes();exec(compile(raw,m.__file__,'exec'),m.__dict__)
base_raw=pathlib.Path('/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py').read_bytes()
need=m.need;checks=[]
def check(name,fn,refuse=False):
    try:value=fn()
    except (ValueError,KeyError,TypeError) as exc:
        need(refuse,'UNEXPECTED_REFUSAL_'+name);checks.append(dict(name=name,pass_=True,expected='REFUSAL',code=str(exc)));return
    need(not refuse,'UNEXPECTED_ACCEPTANCE_'+name);checks.append(dict(name=name,pass_=True,expected='PASS_SYNTHETIC'));return value
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
    z.writestr('mimetype',m.MIME)
    z.writestr('META-INF/manifest.xml','<m:manifest xmlns:m="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"><m:file-entry m:full-path="/" m:media-type="'+m.MIME+'"/></m:manifest>')
    z.writestr('content.xml','<o:document-content xmlns:o="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:d="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"><o:body><o:presentation><d:page/></o:presentation></o:body></o:document-content>')
data=buf.getvalue();output=dict(path=str(BASE/'NONEXISTENT-SYNTHETIC-ONLY.odp'),bytes=len(data),sha256=m.digest(data))
phase=dict(scenario={'synthetic':'not-an-ordinary-authority'},scenario_sha256='a'*64,retained_unit={'current_source':dict(sha256=m.SOURCE_SHA,bytes=48100,stat={'synthetic':'currentCAS'})})
doc=dict(output,kind='document',complete_artifact=True,advertised_document=dict(mime_type=m.MIME))
run=dict(id='SYNTHETIC_NOT_REAL',scenario=phase['scenario'],scenario_sha256=phase['scenario_sha256'],send_state='sent',send_attempts=1,
    sent_message_id=123,capture_window_complete=True,status='EVIDENCE_READY',observations=[doc])
class Runner:
    api=None
    calls=[]
    drain={'intent':{'kind':'terminal_intent'},'response':{'kind':'terminal_response'},'complete':{'kind':'terminal_complete'}}
    def verify_capture_context(self,r):self.calls.append('capture')
    def verify_window(self,r):self.calls.append('window')
    def verify_reply_custody(self,r):self.calls.append('custody')
    def receive_inventory(self,r,terminal=False):
        need(terminal is True,'TERMINAL_TRUE_REQUIRED');self.calls.append('terminal');return {},{},self.drain
runner=Runner();after={k:phase['retained_unit']['current_source'][k] for k in ('sha256','bytes','stat')}
files={output['path']:data}
def reader(r):
    raw=files[r['path']];need(len(raw)==r['bytes'] and m.digest(raw)==r['sha256'],'SYNTHETIC_REFERENCE_CHANGED');return raw
def assess(r=None,p=None,a=None,rawbase=None,review=None,reviewref=None):
    return m.assess_saved_actual(runner,run if r is None else r,phase if p is None else p,
      base_raw=base_raw if rawbase is None else rawbase,read_reference=reader,source_after=after if a is None else a,
      semantic_review=review,semantic_review_ref=reviewref)
v=check('actual_selected_native_parser_on_synthetic_native_ODP',lambda:assess());need(v['semantic']=='NOT_ESTABLISHED' and v['formal']=='NOT_ESTABLISHED','NO_AUTO_SEMANTIC_PASS')
check('not_saved_pair_same_artifact_not_replayed',lambda:need(v['accepted_saved_byte_match'] is False,'SYNTHETIC_IS_NOT_ACCEPTED_REAL_PAIR'))
need(runner.calls==['capture','window','custody','terminal'],'EXACT_SAVED_CUSTODY_ORDER')
for drain in ({},{'complete':False},{'complete':1},{'complete':True},None):
    runner.drain=drain;check('authenticated_terminal_drain_'+repr(drain),lambda:assess(),True)
runner.drain={'intent':{'kind':'terminal_intent'},'response':{'kind':'terminal_response'},'complete':{'kind':'terminal_complete'}}
for name,change in [('zero_documents',dict(observations=[])),('two_documents',dict(observations=[doc,doc])),('incomplete_artifact',dict(observations=[dict(doc,complete_artifact=False)])),
    ('mime_only_false_pdf',dict(observations=[dict(doc,advertised_document={'mime_type':'application/pdf'})])),('not_full180',dict(capture_window_complete=False)),
    ('second_attempt',dict(send_attempts=2)),('boolean_attempt',dict(send_attempts=True)),('unknown_send',dict(send_state='unknown')),('wrong_scenario',dict(scenario={'different':True})),
    ('boolean_ACK',dict(sent_message_id=True))]:
    r=copy.deepcopy(run);r.update(change);check(name,lambda r=r:assess(r=r),True)
check('source_version_changed',lambda:assess(a=dict(after,stat={'different':True})),True)
check('source_bytes_boolean',lambda:assess(a=dict(after,bytes=True)),True)
check('selected_parser_source_changed',lambda:assess(rawbase=base_raw+b'\n'),True)
files[output['path']]=b'%PDF-synthetic\n%%EOF';check('advertised_ODP_not_native_bytes',lambda:assess(),True);files[output['path']]=data
review=dict(schema='frw.Root.PRESENTATION.same-actual-semantic-review.v1',operator='Root',independently_assessed=True,
    run_id=run['id'],scenario_sha256=phase['scenario_sha256'],actual_output=output,source_sha256=m.SOURCE_SHA,
    evidence=[dict(path=str(BASE/'NONEXISTENT-SYNTHETIC-EVIDENCE.json'),bytes=3,sha256=m.digest(b'{}\n'))],
    **{k:True for k in m.SEMANTIC_FLAGS})
files[review['evidence'][0]['path']]=b'{}\n'
def with_review(v):
    raw=m.encoded(v);ref=dict(path=str(BASE/'NONEXISTENT-SYNTHETIC-REVIEW.json'),bytes=len(raw),sha256=m.digest(raw));files[ref['path']]=raw
    return assess(review=v,reviewref=ref)
value=check('explicit_synthetic_Root_same_byte_semantics_separate',lambda:with_review(review));need(value['formal']=='NOT_ESTABLISHED' and value['privacy']=='NOT_ESTABLISHED','NO_FORMAL_PRIVACY_PROMOTION')
for flag in m.SEMANTIC_FLAGS:
    check('missing_semantic_'+flag,lambda flag=flag:with_review(dict(review,**{flag:False})),True)
check('cannot_reuse_other_saved_pair',lambda:with_review(dict(review,reuse_accepted_saved_pair=True,same_source_and_context_mapping_proven=True)),True)
check('wrong_actual_output_review',lambda:with_review(dict(review,actual_output=dict(output,sha256='0'*64))),True)
check('numeric_actual_output_review_size_float',lambda:with_review(dict(review,actual_output=dict(output,bytes=float(output['bytes'])))),True)
result=dict(schema='frw.presentation.postconditions.sourcecontrols.v1',scope='SOURCE_SYNTHETIC_NONSENSITIVE_NATIVE_BYTES_ONLY_NOT_ACTUAL_ORDINARY_RUNTIME',
    actual_custody_methods='declared stubs here; actual nearest original custody exercised separately by caller-controls and futureRoot',
    source=dict(path=m.__file__,bytes=len(pathlib.Path(m.__file__).read_bytes()),sha256=hashlib.sha256(pathlib.Path(m.__file__).read_bytes()).hexdigest()),
    selected_source_sha256=hashlib.sha256(base_raw).hexdigest(),checks=checks,count=len(checks),all_passed=True,wall_seconds=time.monotonic()-start,
    actual_product_or_current_calls=0,synthetic_fixtures_persisted=False)
(BASE/'POSTCONDITION-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(count=len(checks),all_passed=True,wall_seconds=result['wall_seconds'])))
