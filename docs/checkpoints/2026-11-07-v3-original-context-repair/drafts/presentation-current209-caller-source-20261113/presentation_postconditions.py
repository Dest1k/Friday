"""After-the-same-operation source consumer. Never a preintent prerequisite.

Explicit Root invocation over saved actual receipts; no producer/model/send/App
or current quiescence recreation. Semantics require a separate Root assessment
of these very bytes, or exact accepted-byte applicability. Raw status is kept.
"""
from __future__ import annotations
import hashlib
import json
import types

SELECTED_SHA='cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
SOURCE_SHA='64556440f31c88320569f795020e486f56b9792ceb5fb4908a66797ef0fd780a'
SAVED_ODP_SHA='6e0425e0ef3502954aa73d52ecfc35176835e0d1c907770029044ca98a3d7501'
MIME='application/vnd.oasis.opendocument.presentation'
SEMANTIC_FLAGS=('original_five_ordered_slides','exact_native_editable_text','table_5x2_literal_0001_to_0004',
 'native_chart_and_seven_represented_workbook_cells','five_associated_speaker_notes',
 'same_original_uploaded_source_mapping','applicable_appearance_assessed','notes_geometry_loss_disclosed')


def need(ok,code):
    if not ok:raise ValueError(code)


def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()


def native_kind_from_selected(base_raw,data):
    """Exact existing bounded actual native parser, no renderer or Store."""
    need(type(base_raw) is bytes and digest(base_raw)==SELECTED_SHA,'PRESENTATION_POST_SELECTED_SOURCE_CHANGED')
    need(type(data) is bytes and 0<len(data)<=8388608,'PRESENTATION_ACTUAL_OUTPUT_BYTES_REQUIRED')
    m=types.ModuleType('_presentation_exact_saved_native_parser');m.__file__='<selected-pinned-source>'
    exec(compile(base_raw,m.__file__,'exec'),m.__dict__)
    return m._presentation_native_kind(data)


def assess_saved_actual(runner,run,phase,*,base_raw,read_reference,source_after,semantic_review=None,semantic_review_ref=None):
    """FUTURE ROOT only, actual original custody methods and received bytes.

    runner is the genuine reviewed composition with api=None. read_reference is
    Root's bounded owner/path/link/FD/stat/hash reader. It reads this exact saved
    output only, not directory history; all returned data is metadata/enum flags.
    source_after is Root's saved postoperation CAS {sha256,bytes,stat}, not a
    fresh pre-intent check. No future file or ACK is required during preparation.
    """
    need(runner.api is None,'PRESENTATION_SAVED_ASSESSMENT_NO_API')
    need(encoded(run.get('scenario'))==encoded(phase['scenario']) and run.get('scenario_sha256')==phase['scenario_sha256']
         and run.get('send_state')=='sent' and type(run.get('send_attempts')) is int and run['send_attempts']==1
         and type(run.get('sent_message_id')) is int and run['sent_message_id']>0
         and run.get('capture_window_complete') is True,'PRESENTATION_ACTUAL_SINGLE_SEND_FULL180_REQUIRED')
    # No current209 observe/check or new/send here: product may be busy or history
    # advanced after this consumed operation. Saved custody is the right boundary.
    runner.verify_capture_context(run);runner.verify_window(run);runner.verify_reply_custody(run)
    _,_,drain=runner.receive_inventory(run,terminal=True)
    need(type(drain) is dict and set(drain)=={'intent','response','complete'}
         and all(type(v) is dict for v in drain.values())
         and drain['complete'].get('kind')=='terminal_complete',
         'PRESENTATION_AUTHENTICATED_FULL180_TERMINAL_DRAIN_REQUIRED')
    docs=[o for o in run.get('observations',[]) if o.get('kind')=='document']
    need(len(docs)==1,'PRESENTATION_EXACTLY_ONE_ACTUAL_DOCUMENT_REQUIRED')
    document=docs[0]
    need(document.get('complete_artifact') is True and type(document.get('bytes')) is int
         and 0<document['bytes']<=8388608 and document.get('advertised_document',{}).get('mime_type')==MIME,
         'PRESENTATION_COMPLETE_ODP_CUSTODY_REQUIRED')
    reference={k:document[k] for k in ('path','bytes','sha256')}
    data=read_reference(reference)
    need(type(data) is bytes and len(data)==reference['bytes'] and digest(data)==reference['sha256'],
         'PRESENTATION_SAME_ACTUAL_RECEIVED_BYTES_REQUIRED')
    need(native_kind_from_selected(base_raw,data)=='odp','PRESENTATION_ACTUAL_NATIVE_ODP_REQUIRED')
    original=phase['retained_unit']['current_source']
    need(type(source_after) is dict and set(source_after)=={'sha256','bytes','stat'}
         and encoded(source_after)==encoded({k:original[k] for k in ('sha256','bytes','stat')}),
         'PRESENTATION_SAME_UPLOADED_SOURCE_PRESERVATION_REQUIRED')
    result=dict(schema='frw.Root.PRESENTATION.saved-actual-postconditions.v1',run_id=run['id'],
        raw_status=run.get('status'),raw_reply_text_acceptance=run.get('reply_text_acceptance'),
        raw_document_acceptance=document.get('acceptance'),send_ACK=run['sent_message_id'],
        send_ACK_is_not_native_platform_id=True,full180=True,exactly_one_complete_native_ODP=True,
        actual_output=reference,source_preserved=True,semantic='NOT_ESTABLISHED',appearance='NOT_ESTABLISHED',
        formal='NOT_ESTABLISHED',native_host_close='NOT_ESTABLISHED',privacy='NOT_ESTABLISHED',
        accepted_saved_byte_match=(reference['bytes']==30482 and reference['sha256']==SAVED_ODP_SHA),
        no_new_effect=True,no_retry=True)
    if semantic_review is not None:
        need(type(semantic_review_ref) is dict and read_reference(semantic_review_ref)==encoded(semantic_review),
             'PRESENTATION_EXACT_INDEPENDENT_SAVED_ASSESSMENT_REQUIRED')
        need(type(semantic_review) is dict and semantic_review.get('schema')=='frw.Root.PRESENTATION.same-actual-semantic-review.v1'
             and semantic_review.get('operator')=='Root' and semantic_review.get('independently_assessed') is True
             and semantic_review.get('run_id')==run['id'] and semantic_review.get('scenario_sha256')==phase['scenario_sha256']
             and encoded(semantic_review.get('actual_output'))==encoded(reference) and semantic_review.get('source_sha256')==SOURCE_SHA
             and all(semantic_review.get(k) is True for k in SEMANTIC_FLAGS)
             and type(semantic_review.get('evidence')) is list and bool(semantic_review['evidence']),
             'PRESENTATION_ACTUAL_GOLDEN_APPEARANCE_DISCLOSURE_REVIEW_REQUIRED')
        for r in semantic_review['evidence']:
            raw=read_reference(r);need(type(raw) is bytes and len(raw)==r['bytes'] and digest(raw)==r['sha256'],
                 'PRESENTATION_SAVED_REVIEW_EVIDENCE_CHANGED')
        if semantic_review.get('reuse_accepted_saved_pair') is True:
            need(result['accepted_saved_byte_match'] and semantic_review.get('same_source_and_context_mapping_proven') is True,
                 'PRESENTATION_SAVED_PAIR_REUSE_APPLICABILITY_REQUIRED')
        result.update(semantic='PASS_SCOPED_ORIGINAL_FORWARD',appearance='PASS_SCOPED_WITH_DECLARED_LOSS',
                      semantic_review=semantic_review_ref)
    return result
