"""Captured Telegram function bodies on inert SDK, route and transport leaves."""
import ast
import asyncio
import builtins
import copy
import hashlib
import io
import json
from pathlib import Path
import types

CAPTURE = Path('/home/jericho/.cache/FRW-ASTRA-SOL-T90-F04-ROOT-ORDINARY-CALLER-20261115/static-native-stop-source')
refs = json.loads((CAPTURE / 'INGRESS-SOURCE-REFS.json').read_bytes())
checks = []


def require(ok):
    if not ok:
        raise AssertionError('INDEPENDENT_INGRESS_SOURCE_ASSERTION')


def check(name, function):
    try:
        function()
    except Exception as exc:
        checks.append({'check': name, 'passed': False, 'class': type(exc).__name__})
    else:
        checks.append({'check': name, 'passed': True})


trees = {}
for name, ref in refs['files'].items():
    raw = Path(ref['path']).read_bytes()
    require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'])
    trees[Path(name).name] = ast.parse(raw)

tree = trees['telegram_ingress.py']
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in
         {'_id', '_attachment', 'media_provenance', 'message_provenance'}]
ns = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<captured-ingress-functions>', 'exec'), ns)


def provenance_fixture():
    bot = types.SimpleNamespace(id=8751854128)
    chat = types.SimpleNamespace(id=8812646969, type='private')
    doc = types.SimpleNamespace(file_id='INERT_NATIVE_FILE_ID', file_unique_id='INERT_NATIVE_UNIQUE_ID', file_size=16538)
    message = types.SimpleNamespace(photo=[], document=doc, video=None, audio=None,
        voice=None, sticker=None, animation=None, message_id=4895,
        from_user=types.SimpleNamespace(id=8812646969), chat=chat,
        reply_to_message=None, get_bot=lambda: bot)
    source = types.SimpleNamespace(chat_type='dm', user_id='8812646969', chat_id='8812646969',
                                   thread_id='', message_id='4895')
    origin = {'bot_id': '8751854128', 'chat_id': '8812646969', 'message_id': '4895',
              'file_id': doc.file_id, 'file_unique_id': doc.file_unique_id, 'declared_bytes': 16538}
    content = {'sha256': 'a' * 64, 'bytes': 16538, 'inert_only': True}
    event = types.SimpleNamespace(raw_message=message, internal=False, _ingress_merged=False,
        source=source, platform_update_id=17, _ingress_update_id=17, message_id='4895',
        reply_to_message_id=None, media_urls=['/INERT_ONLY/product.ods'], media_types=['INERT_ODS'],
        _telegram_media_receipts={'/INERT_ONLY/product.ods': {'origin': origin, 'content': content}})
    adapter = types.SimpleNamespace(_bot=bot, _effective_message_thread_id=lambda message: '')
    return adapter, event


def positive_provenance():
    adapter, event = provenance_fixture()
    result = ns['message_provenance'](adapter, event)
    require(result['message_id'] == '4895' and result['platform_update_id'] == '17'
            and result['media'][0]['origin']['message_id'] == '4895'
            and result['media'][0]['content'] == event._telegram_media_receipts[event.media_urls[0]]['content'])
    require('tester_message_id' not in result and 'generation' not in result and 'lease' not in result)


check('actual_native_provenance_preserves_native_ids_and_content_label_not_tester_bridge', positive_provenance)
for name, mutate in (
    ('merged_event_refuses_provenance', lambda a, e: setattr(e, '_ingress_merged', True)),
    ('foreign_bot_object_refuses_even_same_numeric_id', lambda a, e: setattr(a, '_bot', types.SimpleNamespace(id=a._bot.id))),
    ('source_message_identity_mismatch_refuses', lambda a, e: setattr(e.source, 'message_id', '2789')),
    ('native_update_identity_mismatch_refuses', lambda a, e: setattr(e, '_ingress_update_id', 18)),
):
    def run(mutate=mutate):
        a, e = provenance_fixture()
        mutate(a, e)
        require(ns['message_provenance'](a, e) is None)
    check(name, run)


def labels_are_not_byte_verification():
    a, e = provenance_fixture()
    e._telegram_media_receipts[e.media_urls[0]]['content']['sha256'] = '0' * 64
    require(ns['message_provenance'](a, e)['media'][0]['content']['sha256'] == '0' * 64)


check('actual_provenance_copies_content_label_and_does_not_itself_verify_file_bytes', labels_are_not_byte_verification)


class SendResult:
    def __init__(self, success, **kwargs):
        self.success = success
        self.__dict__.update(kwargs)


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == 'gateway.run_plugin_delivery':
        return types.SimpleNamespace(freeze_route=lambda route: copy.deepcopy(route))
    raise AssertionError('UNEXPECTED_RUNTIME_IMPORT')


nodes = [n for n in trees['telegram_document_bytes.py'].body
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
         and n.name in {'_original_route_kwargs', 'send_document_bytes'}]
out_ns = {'hashlib': hashlib, 'io': io, 'SendResult': SendResult,
          '__builtins__': dict(vars(builtins), __import__=guarded_import)}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<captured-native-document-functions>', 'exec'), out_ns)


def output_control(*, bad_reply=False, bad_size=False, uncertain=False):
    sends, checks_run = [], []
    data = b'INERT_ONLY_SYNTHETIC_BYTES'
    async def send(**kwargs):
        sends.append(kwargs['document'].getvalue())
        if uncertain:
            raise RuntimeError('INERT_TRANSPORT_EXCEPTION')
        return types.SimpleNamespace(message_id=7001, chat=types.SimpleNamespace(id=8812646969),
            message_thread_id=None, document=types.SimpleNamespace(file_id='INERT_RETURN_FILE_ID',
                file_size=len(data) + int(bad_size)))
    bot = types.SimpleNamespace(id=8751854128, send_document=send)
    adapter = types.SimpleNamespace(_bot=bot, is_connected=True,
        _caption_1024=lambda text: text, _metadata_thread_id=lambda metadata: '',
        _message_thread_id_for_send=lambda tid: None,
        _media_send_kwargs=lambda chat, reply, metadata: (None, {'chat_id': chat,
            'reply_to_message_id': int(reply), 'message_thread_id': None}))
    route = {'bot_id': '8751854128', 'source': {'chat_id': '8812646969', 'message_id': '4895', 'thread_id': ''}}
    metadata = {'_friday_document_authority': (lambda: checks_run.append('authority_check'), route)}
    result = asyncio.run(out_ns['send_document_bytes'](adapter, 8812646969, data,
        file_name='INERT.xlsx', reply_to='9999' if bad_reply else '4895', caption='INERT', metadata=metadata))
    if bad_reply:
        require(not result.success and sends == [])
    elif bad_size or uncertain:
        require(not result.success and len(sends) == 1)
    else:
        require(result.success and sends == [data] and checks_run == ['authority_check'])
        proof = result.raw_response
        require(proof['sha256'] == hashlib.sha256(data).hexdigest() and proof['bytes'] == len(data)
                and proof['reply_to'] == '4895' and proof['message_id'] == '7001')
        require(not {'tester_message_id', 'generation', 'lease', 'operation_id'} & set(proof))


check('actual_native_document_proof_has_bytes_and_native_route_but_no_turn_tester_bridge', output_control)
check('actual_native_document_foreign_reply_route_refuses_before_send', lambda: output_control(bad_reply=True))
check('actual_native_document_wrong_ack_size_never_retries', lambda: output_control(bad_size=True))
check('actual_native_document_uncertain_send_never_retries', lambda: output_control(uncertain=True))

report = {'schema': 'frw.T90.independent-ingress-source-controls.v1', 'source_only': True,
          'source_refs_sha256': hashlib.sha256((CAPTURE / 'INGRESS-SOURCE-REFS.json').read_bytes()).hexdigest(),
          'all_SDK_route_network_leaves_inert': True, 'actual_file_or_native_or_Telegram_effect': False,
          'passed': sum(row['passed'] for row in checks), 'failed': sum(not row['passed'] for row in checks),
          'checks': checks}
p = Path(__file__).with_name('INGRESS-SOURCE-CONTROLS.json')
p.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
p.chmod(0o600)
print(json.dumps({'passed': report['passed'], 'failed': report['failed'], 'path': str(p)}))
raise SystemExit(bool(report['failed']))
