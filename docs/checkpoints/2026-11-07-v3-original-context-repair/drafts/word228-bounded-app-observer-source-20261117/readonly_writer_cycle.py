"""One Root-owned readonly Writer load/observe/close; no launcher or authority.

Root supplies an actual defaultOffice UNO Desktop/module after its own fresh
admission, isolated process and same-open-file-description shared-slot custody.
This module imports no UNO, opens no path, starts no App, and never retries.
"""
from urllib.parse import urlsplit
class ReadonlyCycleError(ValueError):pass

def run_readonly_writer(desktop, uno_api, observer, *, input_url):
    u=urlsplit(input_url) if type(input_url)is str else None
    if u is None or u.scheme!='file' or u.netloc or not u.path.startswith('/') or u.query or u.fragment or not u.path.endswith('.odt') or any(c in input_url for c in ('\x00','\n','\r')):
        raise ReadonlyCycleError('exact_local_owned_odt_file_URL_required')
    if not callable(observer):raise ReadonlyCycleError('pinned_observer_callable_required')
    # Resolve real named UNO constants at Root runtime; no guessed numeric enum.
    never=uno_api.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE')
    no_update=uno_api.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE')
    if type(never)is not int or type(no_update)is not int:
        raise ReadonlyCycleError('actual_named_UNO_policy_constants_required')
    props=[]
    for key,value in (('ReadOnly',True),('Hidden',True),('MacroExecutionMode',never),('UpdateDocMode',no_update)):
        prop=uno_api.createUnoStruct('com.sun.star.beans.PropertyValue');prop.Name=key;prop.Value=value;props.append(prop)
    document=None;observation=None;failure=None
    try:
        document=desktop.loadComponentFromURL(input_url,'_blank',0,tuple(props))
        if document is None:raise ReadonlyCycleError('Writer_load_returned_no_document')
        observation=observer(document,expected_url=input_url)
    except BaseException as error:
        failure=error
    finally:
        if document is not None:
            try:document.close(True)
            except BaseException as error:
                raise ReadonlyCycleError('owned_document_close_unconfirmed')from None
    if failure is not None:raise failure
    return dict(schema='frw.word228.readonly-App-model-cycle-data.v1',scope='DATA_ONLY_NO_ROOT_AUTHORITY_OR_RUNTIME_QUALIFICATION',operation='one_readonly_load_observe_close',load_calls=1,save_calls=0,reopen_calls=0,owned_document_closed=True,observation=observation,namespace_quiescence='ROOT_OUTER_REQUIRED_NOT_ESTABLISHED_BY_DOCUMENT_CLOSE',whole_F04_or_LIVE_BOT_or_canonical2830_regrade=False)
