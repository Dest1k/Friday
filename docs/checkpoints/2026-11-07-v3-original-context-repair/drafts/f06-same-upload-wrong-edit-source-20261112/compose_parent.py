from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'candidate/f06_source.py';s=p.read_text()
s=s.replace('correct-read SAME upload','wrong-edit SAME upload').replace("PHASE='DOCX-CORRECT-READ-SAME-UPLOAD'","PHASE='DOCX-WRONG-EDIT-SAME-UPLOAD'")
s=s.replace("'correct_read_private_oracle'","'wrong_edit_private_oracle','correct_read_reconciliation'")
s=s.replace("'source_reference','installation'}","'source_reference','installation','correct_read','change_spec'}")
a=s.index('def scope():');z=s.index('\ndef unbound():',a)
s=s[:a]+'''def scope():
    return ('Original F-06/P0/LIVE_BOT one separate wrong-password EDIT of SAME actual closed protected DOCX upload, only after actual correct-read closed, semantically assessed and accepted. One legitimate exact Root-authorized literal replacement; use ONLY the deliberately wrong password supplied for this operation, never previous correct password or history/guessing. Text-only ordinary independent request, max0 uploads/outbound documents. Expected honest password refusal with no source change, plaintext/new/encrypted output, delivery or automatic followup. Actual refusal remains RECEIVED_UNGRADED/NOT_ESTABLISHED until independent Root semantic/privacy/nochange assessment. Exact actual first ACK/source_reference/native ingress/custody plus correct-read linkage/assessment and fresh Root decision required. No producer/native edit/Office/restart, second sendDocument, fake reply_to/inlinepath, correct-edit authorization, old effect replay or clock reset. Exact300/full180/ACK10/reserve5/outer600. Standard3.2 data_integrity_verified=false; password verification/ZIP CRC/readback are not authenticated MAC. Correct-edit/other families/full F06/170/120/B00 remain open.')

REQUEST_PREFIX='В ранее присланном в этой беседе защищённом DOCX f06-new-encrypted.docx выполни одну разрешённую правку: замени ровно одно вхождение строки '
REQUEST_MIDDLE=' на '
REQUEST_PASSWORD='. Для этой операции используй ТОЛЬКО переданный сейчас тестовый пароль '
REQUEST_SUFFIX='. Не используй прежний правильный пароль из истории, другие пароли или подбор. Не включай пароль в ответ и не сохраняй его отдельно. Если этот пароль не подходит, честно сообщи об отказе и ничего не меняй, не создавай расшифрованную копию, новый или зашифрованный файл и не отправляй файл. Не выполняй других правок и продолжений.'

def change_shape(spec):
    need(type(spec) is dict and set(spec)=={'kind','old','new','expected_occurrences'} and spec['kind']=='literal_replace' and type(spec['expected_occurrences']) is int and spec['expected_occurrences']==1,'F06_EXACT_BOUNDED_CHANGE_REQUIRED')
    for key in ('old','new'):
        v=spec[key];need(type(v) is str and 0<len(v)<=1000 and 'UNBOUND' not in v and not any(ord(ch)<32 or 127<=ord(ch)<=159 for ch in v),'F06_PRIVATE_LITERAL_CHANGE_REQUIRED')
        try:v.encode('utf8')
        except UnicodeError:raise ValueError('F06_CHANGE_UTF8_REQUIRED') from None
    need(spec['old']!=spec['new'],'F06_ACTUAL_NONIDENTICAL_CHANGE_REQUIRED');return True

def request_for(supplied_password,change_spec):
    change_shape(change_spec)
    need(type(supplied_password) is str and bool(supplied_password) and 'UNBOUND' not in supplied_password and not any(ord(ch)<32 or 127<=ord(ch)<=159 for ch in supplied_password),'F06_PRIVATE_WRONG_PASSWORD_REQUIRED')
    try: units=len(supplied_password.encode('utf-16-le'))//2
    except UnicodeError:raise ValueError('F06_PASSWORD_UTF16_REQUIRED') from None
    need(units<=255,'F06_PASSWORD_UTF16_BOUND')
    quote=lambda v:json.dumps(v,ensure_ascii=False,allow_nan=False)
    return REQUEST_PREFIX+quote(change_spec['old'])+REQUEST_MIDDLE+quote(change_spec['new'])+REQUEST_PASSWORD+quote(supplied_password)+REQUEST_SUFFIX

def request_parts(text):
    need(type(text) is str and len(text)<=10000 and text.startswith(REQUEST_PREFIX),'F06_EXACT_WRONGEDIT_REQUEST_REQUIRED')
    rest=text[len(REQUEST_PREFIX):];parts=[]
    for suffix in (REQUEST_MIDDLE,REQUEST_PASSWORD,REQUEST_SUFFIX):
        try:value,end=json.JSONDecoder().raw_decode(rest)
        except (ValueError,TypeError):raise ValueError('F06_PRIVATE_REQUEST_LITERAL_REQUIRED') from None
        need(type(value) is str and rest[end:].startswith(suffix),'F06_EXACT_WRONGEDIT_REQUEST_REQUIRED')
        parts.append(value);rest=rest[end+len(suffix):]
    need(rest=='','F06_NO_EXTRA_FOLLOWUP_OR_PERMISSION')
    old,new,password=parts;spec={'kind':'literal_replace','old':old,'new':new,'expected_occurrences':1}
    need(request_for(password,spec)==text,'F06_NONCANONICAL_PRIVATE_REQUEST');return password,spec

def construct_scenario(*,supplied_password,change_spec,first_dependency,correct_dependency):
    # Pure constructor is NOT a Root admission. Real dependencies are validated
    # from exact retained evidence by validate_first before any issuer/birth.
    need(type(first_dependency) is dict and first_dependency.get('schema')=='frw.Root.F06.closed-first-upload.v1' and first_dependency.get('status')=='ROOT_BOUND_CLOSED_RECONCILED' and first_dependency.get('source',{}).get('sha256')==SOURCE['sha256'] and type(first_dependency.get('source_reference')) is dict,'F06_ACTUAL_FIRST_UPLOAD_REQUIRED')
    need(type(correct_dependency) is dict and correct_dependency.get('schema')=='frw.Root.F06.closed-correct-read.v1' and correct_dependency.get('status')=='ROOT_BOUND_CORRECT_READ_ACCEPTED' and correct_dependency.get('source_reference')==first_dependency['source_reference'] and correct_dependency.get('source')==first_dependency['source'],'F06_ACTUAL_ACCEPTED_CORRECT_READ_REQUIRED')
    return {'tester_id':8812646969,'peer_id':8751854128,'peer_username':'@jerichodevbot','deadline_seconds':300,'max_updates':65,'pace_seconds':1,'steps':[{'request':request_for(supplied_password,change_spec),'observe':dict(OBSERVE)}]}

def scenario_shape(s):
    need(type(s) is dict and set(s)=={'tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds','steps'} and type(s['steps']) is list and len(s['steps'])==1,'F06_SINGLETON_WRONG_EDIT_REQUIRED')
    need({k:s.get(k) for k in ('tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds')}=={'tester_id':8812646969,'peer_id':8751854128,'peer_username':'@jerichodevbot','deadline_seconds':300,'max_updates':65,'pace_seconds':1} and all(type(s[k]) is int for k in ('tester_id','peer_id','deadline_seconds','max_updates','pace_seconds')),'F06_EXACT_IDENTITIES_AND_BOUNDS_REQUIRED')
    t=s['steps'][0];need(type(t) is dict and set(t)=={'request','observe'} and t['observe']==OBSERVE and all(type(t['observe'][k]) is int for k in OBSERVE if k!='mode'),'F06_TEXT_ONLY_FULL180_MAX0_REQUIRED')
    request_parts(t['request']);return True

''' +s[z:]
s=s.replace('frw.F06.same-upload-correctread.v1','frw.F06.same-upload-wrongedit.v1').replace('ROOT_BOUND_EXACT_F06_CORRECTREAD','ROOT_BOUND_EXACT_F06_WRONGEDIT')
s=s.replace("'source_reference':None,'installation':None}","'source_reference':None,'installation':None,'correct_read':None,'change_spec':None}")
s=s.replace("'root_current_proof','first_validator','first_ingress'))","'root_current_proof','first_validator','first_ingress','correct_read','change_spec'))")
s=s.replace('F06_EXACT_CORRECT_READ_CONTRACT_REQUIRED','F06_EXACT_WRONG_EDIT_CONTRACT_REQUIRED').replace('F06_ZERO_UPLOAD_CORRECTREAD_ONCE_UNBOUND','F06_ZERO_UPLOAD_WRONGEDIT_ONCE_UNBOUND')
s=s.replace('    m.private_oracle(c,read)\n    return first','    m.correct_read(c,read,first)\n    m.private_oracle(c,read)\n    return first')
s=s.replace("    validate_first(c,read)\n    need(name==", "    validate_first(c,read)\n    change=json.loads(readref(c['change_spec'],read));change_shape(change)\n    need(readref(c['change_spec'],read)==encoded(change) and request_parts(s['steps'][0]['request'])[1]==change,'F06_AUTHORIZED_CHANGE_SCENARIO_MISMATCH')\n    need(name==")
p.write_text(s)
p=B/'candidate/root_bind_dispatch_once.py';s=p.read_text().replace('same-upload correct-read','same-upload wrong-edit').replace('same-upload-correctread','same-upload-wrongedit').replace('same_upload_correctread','same_upload_wrongedit').replace('ROOT_BOUND_EXACT_F06_CORRECTREAD','ROOT_BOUND_EXACT_F06_WRONGEDIT').replace('correct-read of the same reconciled closed upload','wrong-password edit of the same reconciled closed upload after accepted correct-read')
p.write_text(s)
p=B/'candidate/f06_footer.py.txt';s=p.read_text().replace('correct-read SAME closed first upload','wrong-edit SAME closed first upload after accepted correct-read');p.write_text(s)
