"""Final dormant templates/source integrity. Root actual prebirth is NOT an upload."""
import ast,hashlib,json,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent;V=B/'revision3';C=V/'candidate';checks=[]
def load(n):
 p=C/n;m=types.ModuleType(n[:-3]);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=load('f06_source.py');F=load('first_ingress.py');doc={p.name:json.loads(p.read_bytes()) for p in V.glob('*.UNBOUND.json')};proof=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112/PREBIRTH-ISSUER-ONLY-CLOSURE.json');raw=proof.read_bytes();assert hashlib.sha256(raw).hexdigest()=='d8f6c472ab34a1349e8dfb49ead0a95383aa479728c8d0fa818a4446b12a83f5'
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,AttributeError):checks.append(n);return
 raise AssertionError(n)
def audit(ev,args):
 if ev=='open' or ev.startswith(('socket.','subprocess.','os.system','os.spawn','os.exec')):raise RuntimeError('PURE_NO_IO')
sys.addaudithook(audit)
ok('contract_exact_unbound',doc['CONTRACT.UNBOUND.json']==A.unbound())
ok('actual_tuple_receipt_input_all_unbound',all(x is None for x in doc['INSTALLATION.UNBOUND.json']['product'].values()))
ok('scenario_has_no_actual_secret_or_step',doc['SCENARIO.UNBOUND.json']['scenario'] is None)
ok('no_future_first_source_or_ACK',doc['FIRST-INGRESS.UNBOUND.json']['source_reference'] is None and doc['FIRST-INGRESS.UNBOUND.json']['ack'] is None)
ok('no_clock_or_admission_constructed',all(v is None for k,v in doc['ROOT-CLOCK.UNBOUND.json'].items() if k!='schema'))
t=doc['ROOT-REVIEW-TEMPLATES.UNBOUND.json'];ok('new_original_custody_ref_unbound',t['closed_first_operation']['original_consumer_custody'] is None)
ok('new_original_custody_not_accepted',t['original_consumer_custody']['status']=='UNBOUND_NOT_GRANTED')
ok('private_oracle_not_synthetic_fact',t['correct_read_private_oracle']['correct_secret_verified_for_same_source'] is None and t['correct_read_private_oracle']['actual_retained_first_paragraph_oracle'] is None)
c=A.unbound();c['first_ingress']={'path':str(proof),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
refuse('actual_prebirth_issued_authority_is_NOT_upload',lambda:F.validate(c,lambda p:raw))
# Pure constructor cannot use an issuer-only or UNBOUND proof to create request.
refuse('constructor_prebirth_not_closed_upload',lambda:A.construct_scenario(supplied_password='SYNTHETIC-ONLY',first_dependency=json.loads(raw)))
refuse('constructor_unbound_not_closed_upload',lambda:A.construct_scenario(supplied_password='SYNTHETIC-ONLY',first_dependency=doc['FIRST-INGRESS.UNBOUND.json']))
print(json.dumps({'state':'PASS_UNBOUND_METADATA_SOURCE_ONLY','count':len(checks),'checks':checks,'actual_current_H_or_document_or_Telegram':0},sort_keys=True))
