"""Direct real StoppedOperator._workers_stopped with retained native stores.

Only systemd RPC transport is synthetic. Native PluginState, admission lock,
association producer/validator, SessionDB schema/read-only queries and native
supervisor parsing run. This is not full StoppedOperator authority or live stop.
"""
from contextlib import ExitStack
import copy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import time
import sys

import pytest
from test_dsh_current_availability import candidate, env
from friday_admin_controls.stopped_operator import StoppedOperator,DeclarationError
from friday_admin_controls.associations import Associations,KEY
from friday_admin_controls.host_record import association_address,owner_from_ingress
from friday_admin_controls.boundary import WorkBrief
from hermes_cli import friday_user_scope as users
from hermes_cli.plugins_state import PluginState
from hermes_cli.friday_native_supervision import NativeSupervisor
from hermes_state import SessionDB
from scripts import friday_ordinary_install as ordinary
from scripts.install_containment import Budget


def test_profile_admission_authenticates_open_descriptor_against_named_lock(quiescent,monkeypatch):
    """Deterministic ABA while original operator retains the named EX lock."""
    from friday_admin_controls.associations import AssociationError
    s=quiescent
    b=StoppedOperator({},Budget(180));b.home=s.a.home;b.profile_home=s.a.profile_home
    b.ordinary=ordinary;b.f=ordinary.api();b._stack=ExitStack()
    path=s.a._dsh_profile_store/'admission.lock'
    alternate=path.with_name('coherent-alternate.lock');saved=path.with_name('coherent-saved.lock')
    alternate.write_bytes(b'v1\n');alternate.chmod(0o600)
    original=os.open;swapped=[]
    def opening(target,flags,*args,**kwargs):
        if Path(target)==path and not swapped and sys._getframe(1).f_code.co_name=='_dsh_profile_admission':
            swapped.append(True);path.rename(saved);alternate.rename(path)
            try: fd=original(target,flags,*args,**kwargs)
            finally: path.rename(alternate);saved.rename(path)
            return fd
        return original(target,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',opening)
    try:
        with pytest.raises(AssociationError,match='unsafe_admission_lock'):
            with b._dsh_profile_admission():pass
        assert swapped == [True]
    finally:
        b._stack.close();alternate.unlink()


def tree(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()
        and not p.name.endswith(('-shm','-wal'))}


def association(f,submitted=False):
    call={key:'synthetic-'+key for key in ('task_id','session_id','turn_id','api_request_id','tool_call_id')}
    call['task_id']=call['session_id']
    ingress={'platform':'telegram','session_key':'synthetic-key','source_profile':'default',
        'transport_profile':'default','runtime_profile':f.c['runtime_profile'],
        'message':{'bot_id':'bot-A','user_id':'1','chat_id':'fixture-chat','thread_id':'',
            'message_id':'1','platform_update_id':'1','reply_to_message_id':'','media':[]}}
    brief=WorkBrief('dsh','Synthetic retained task','Original safe closure remains unchanged')
    ident=association_address(call,ingress);binding={'correlation':call,'ingress':ingress,
        'brief':vars(brief),'runtime':copy.deepcopy(f.c)}
    with users.authority(f.h):
        store=Associations(PluginState('friday_rework'))
        row,_=store.claim(task_id=ident,admission_key=ident,owner=owner_from_ingress(call,ingress),
            brief=brief,workspace_reference=str(Path(f.c['workspace_root'])/ident),
            supervisor={'scope':'user','unit':'friday-rework-worker-'+ident[7:39]+'.service'},
            budget_seconds=f.c['budget_seconds'],deadline_unix=time.time()+f.c['budget_seconds']-1,
            host_binding=binding)
        if submitted:
            store.begin_submission(ident,row['owner'])
            store.attach_native(ident,row['owner'],{'invocation_id':'b'*32,'worker_reference':'retained-native-worker'})
            store.observe(ident,row['owner'],native={'invocation_id':'b'*32,'worker_reference':'retained-native-worker'},evidence_reference='retained-cessation',elapsed_seconds=1)
        store.request_stop(ident,row['owner'],'cancel')
        if submitted:
            from friday_admin_controls.host_record import quiescence_record
            from hermes_cli.friday_native_supervision import UnitObservation
            quiet=quiescence_record(UnitObservation(row['supervisor']['unit'],'','inactive','dead','success',0,'',False,True),time.time)
        else:quiet={'kind':'never_submitted','at_unix':time.time(),'observation':None}
        row=store.retain_outcome(ident,row['owner'],quiescence=quiet)
    return row


@pytest.fixture
def quiescent(candidate,monkeypatch,request):
    f=candidate
    # Correct only our synthetic constructor layout to native provision's0700.
    # No actual/H or historical file mode is changed.
    (f.h/'workers').chmod(0o700)
    for home in (f.e.home,f.h):
        with users.authority(home):
            state=PluginState('friday_rework');store=Associations(state)
            with store._locked():pass
            with SessionDB(home/'state.db') as db:pass
        (home/'state.db').chmod(0o600)
    row=association(f,submitted=getattr(request,"param",False))
    retained=f.h/'workers/qualification/KEEP-HISTORY'
    retained.write_bytes(b'RETAINED STOP_UNCONFIRMED/600 AND DISTINCT300; DO NOT REWRITE\n');retained.chmod(0o600)
    # Preserve a nonempty job directory too, not merely a qualification flag.
    job=Path(row['workspace_reference']);job.mkdir(mode=0o700)
    (job/'delivered-artifact.txt').write_bytes(b'ALREADY DELIVERED ARTIFACT; NEVER REPLAY\n')
    a=StoppedOperator({},Budget(180));a.home=f.e.home;a.profile_home=f.h
    a.ordinary=ordinary;a.f=ordinary.api();a.dsh_current=True;a.active=False
    a._worker_root=f.e.home/'a0-private';a._worker_state=f.e.home/'a0-state'
    a._worker_unit_name='synthetic-workers.service';a._stack=ExitStack()
    native={'mode':'missing','listed':[],'scope':'inactive','populated':False,'calls':[]}
    from scripts import dsh_prepare
    def run(argv,cwd,**kw):
        native['calls'].append(argv)
        assert kw['timeout']<=5 and kw['deadline']<=a.budget.deadline
        if 'list-units' in argv:return '\n'.join(native['listed']),{}
        if 'show' in argv:
            unit=argv[argv.index('show')+1]
            if unit==a._worker_unit_name:
                return '\n'.join(k+'='+v for k,v in {'LoadState':'loaded','ActiveState':'inactive',
                    'SubState':'dead','MainPID':'0','ControlPID':'0','ControlGroup':'','InvocationID':''}.items()),{}
            return '\n'.join(k+'='+v for k,v in {'Id':unit,'LoadState':'loaded',
                'ActiveState':native['scope'],'SubState':'dead' if native['scope']=='inactive' else 'running',
                'ControlGroup':''}.items()),{}
        raise AssertionError(argv)
    monkeypatch.setattr(dsh_prepare,'run',run)
    from hermes_cli.friday_native_control import CountedNativeCommands
    def command(self,argv,timeout,**kw):
        native['calls'].append(argv);unit=argv[argv.index('show')+1]
        assert timeout<=3
        if native['mode']=='missing':
            values={'LoadState':'not-found','Transient':'no','Description':unit,'InvocationID':'',
                'ActiveState':'inactive','SubState':'dead','Result':'success','MainPID':'0','ControlGroup':'',
                'KillMode':'control-group','SendSIGKILL':'yes'}
        else:
            values={'LoadState':'loaded','Transient':'yes','Description':NativeSupervisor.description(row),
                'InvocationID':'b'*32,'ActiveState':'active','SubState':'running','Result':'success',
                'MainPID':'99','ControlGroup':'/user.slice/'+unit,'KillMode':'control-group','SendSIGKILL':'yes'}
        if native['mode']=='malformed':values.pop('Result')
        return SimpleNamespace(returncode=0,stdout='\n'.join(k+'='+v for k,v in values.items()))
    monkeypatch.setattr(CountedNativeCommands,'run',command)
    monkeypatch.setattr(NativeSupervisor,'_populated',staticmethod(lambda group:native['populated'] or bool(group)))
    from gateway import status
    monkeypatch.setattr(status,'get_running_pid_identity_strict',lambda path:None)
    with users.authority(f.e.home):
        a._dsh_profile_admission_prove=a._stack.enter_context(a._dsh_profile_admission())
        a.active=True
        yield SimpleNamespace(f=f,a=a,native=native,row=row)
    a.active=False;a._stack.close()


@pytest.mark.parametrize("quiescent",[False,True],indirect=True)
def test_real_native_predicate_accepts_retained_quiescent_workers_without_changing_history(quiescent):
    s=quiescent;before=tree(s.f.e.home)
    s.a._workers_stopped()
    assert tree(s.f.e.home)==before
    assert (s.f.h/'workers/qualification/KEEP-HISTORY').is_file()
    assert any('list-units' in call for call in s.native['calls'])
    assert any('show' in call and s.row['supervisor']['unit'] in call for call in s.native['calls'])


@pytest.mark.parametrize('kind',['active','malformed','unknown-row','legacy-row','lease','expired-lease','compression','orphan-worker','active-qualifier','populated-qualifier','metadata-drift','no-lock'])
def test_real_native_predicate_refuses_active_or_unknown_and_keeps_data(quiescent,kind):
    s=quiescent
    if kind in ('active','malformed'):s.native['mode']=kind
    elif kind in ('unknown-row','legacy-row'):
        with users.authority(s.f.h):
            state=PluginState('friday_rework');data=state.get_storage_readonly(KEY)
            row=next(iter(data['jobs'].values()))
            if kind=='unknown-row':row['host']['quiescence']=None
            else:row.pop('host')
            state.set(KEY,data)
        # Deliberately refresh the fixture's snapshot so the actual schema/
        # activity check is reached; this is not a StoppedOperator admission.
        s.a._dsh_profile_state_before=ordinary.update_file_state(s.a._dsh_profile_store/'state.json')
    elif kind in ('lease','expired-lease','compression'):
        with SessionDB(s.f.h/'state.db') as db:
            table='compression_locks' if kind=='compression' else 'session_turn_leases'
            key='session_id' if kind=='compression' else 'conversation_id'
            db._conn.execute('INSERT INTO '+table+'('+key+',holder,acquired_at,expires_at) VALUES (?,?,?,?)',
                ('retained','owner',1,2 if kind=='expired-lease' else time.time()+300))
    elif kind=='orphan-worker':s.native['listed']=['friday-rework-worker-'+'c'*32+'.service loaded inactive dead Unknown']
    elif kind in ('active-qualifier','populated-qualifier'):
        s.native['listed']=['friday-qualify-dsh-'+'d'*24+'-1.scope loaded inactive dead Scope']
        s.native['scope']='active' if kind=='active-qualifier' else 'inactive'
        s.native['populated']=kind=='populated-qualifier'
    elif kind=='metadata-drift':
        path=s.a._dsh_profile_store/'state.json';path.write_bytes(path.read_bytes()+b'\n')
    elif kind=='no-lock':s.a._dsh_admission_held=False
    before=tree(s.f.e.home)
    with pytest.raises((RuntimeError,ValueError,OSError,PermissionError)):s.a._workers_stopped()
    assert tree(s.f.e.home)==before
    # Restore only the fixture authority marker for its deterministic teardown.
    if kind=='no-lock':s.a._dsh_admission_held=True
    if kind=='metadata-drift':s.a._dsh_profile_state_before=ordinary.update_file_state(s.a._dsh_profile_store/'state.json')


def test_legacy_a0_predicate_keeps_no_workers_prerequisite(quiescent):
    s=quiescent;s.a.dsh_current=False
    with pytest.raises(DeclarationError,match='native_worker_activity_present'):s.a._workers_stopped()


def test_existing_uncheckpointed_wal_lease_is_observed_not_ignored(quiescent):
    s=quiescent
    with SessionDB(s.f.h/'state.db') as writer:
        writer._conn.execute('INSERT INTO session_turn_leases VALUES (?,?,?,?)',('live','holder',1,time.time()+300))
        before=tree(s.f.e.home)
        with pytest.raises(DeclarationError,match='native_lease_or_lock_present'):s.a._workers_stopped()
        assert tree(s.f.e.home)==before
        assert writer._conn.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0]==1


def test_quiet_existing_wal_and_unrelated_history_are_preserved(quiescent):
    s=quiescent
    with SessionDB(s.f.h/'state.db') as writer:
        writer._conn.execute('CREATE TABLE retained_fixture_history(payload BLOB)')
        writer._conn.execute('INSERT INTO retained_fixture_history VALUES (?)',(b'IMMUTABLE OWN FIXTURE HISTORY',))
        before=tree(s.f.e.home)
        wal=Path(str(s.f.h/'state.db')+'-wal');data=wal.read_bytes()
        s.a._workers_stopped()
        assert tree(s.f.e.home)==before and wal.read_bytes()==data
        assert writer._conn.execute('SELECT payload FROM retained_fixture_history').fetchone()[0]==b'IMMUTABLE OWN FIXTURE HISTORY'


def test_missing_native_lease_schema_is_unknown_not_quiet(quiescent):
    s=quiescent
    with SessionDB(s.f.h/'state.db') as writer:writer._conn.execute('DROP TABLE session_turn_leases')
    before=tree(s.f.e.home)
    import sqlite3
    with pytest.raises(sqlite3.OperationalError,match='no such table'):s.a._workers_stopped()
    assert tree(s.f.e.home)==before


def test_duplicate_native_metadata_cannot_hide_an_existing_row(quiescent):
    s=quiescent;path=s.a._dsh_profile_store/'state.json'
    import json
    first=json.loads(path.read_bytes())[KEY]
    path.write_text('{"associations.v1":'+json.dumps(first)+',"associations.v1":{"schema_version":1,"jobs":{}}}')
    s.a._dsh_profile_state_before=ordinary.update_file_state(path)
    before=tree(s.f.e.home)
    with pytest.raises(DeclarationError,match='duplicate_json'):s.a._workers_stopped()
    assert tree(s.f.e.home)==before


def test_existing_profile_admission_busy_is_not_bypassed_or_created(quiescent):
    s=quiescent;b=StoppedOperator({},Budget(180));b.home=s.a.home;b.profile_home=s.a.profile_home
    b.ordinary=ordinary;b.f=ordinary.api();b._stack=ExitStack();before=tree(s.f.e.home)
    try:
        with pytest.raises(DeclarationError,match='profile_admission_busy'):
            with b._dsh_profile_admission():pass
        assert tree(s.f.e.home)==before and s.a._dsh_admission_held
    finally:b._stack.close()


def test_released_native_snapshot_reads_retained_data_without_reacquiring_admission(quiescent):
    s=quiescent;s.a.active=False;s.a._stack.close();before=tree(s.f.e.home)
    s.a._workers_stopped(cleanup=True)
    assert tree(s.f.e.home)==before and not s.a._dsh_admission_held


def test_inactive_retained_native_qualification_scope_is_quiet_without_data_deletion(quiescent):
    s=quiescent;s.native['listed']=['friday-qualify-dsh-'+'d'*24+'-1.scope loaded inactive dead Scope']
    before=tree(s.f.e.home)
    s.a._workers_stopped()
    assert tree(s.f.e.home)==before


def test_no_wal_immutable_read_refuses_a_concurrent_wal_lease_writer(quiescent,monkeypatch):
    s=quiescent
    import sqlite3
    original=sqlite3.connect;writers=[]
    def racing(database,*args,**kwargs):
        if str(s.f.h/'state.db') in str(database) and 'immutable=1' in str(database) and not writers:
            # External supported writer starts AFTER our beforeimage. It must
            # not be hidden by the no-WAL read's immutable view.
            writer=original(s.f.h/'state.db',isolation_level=None)
            writer.execute('INSERT INTO session_turn_leases VALUES (?,?,?,?)',('concurrent','external',1,time.time()+300))
            writers.append(writer)
        return original(database,*args,**kwargs)
    monkeypatch.setattr(sqlite3,'connect',racing)
    try:
        with pytest.raises(DeclarationError,match='native_database_changed'):s.a._workers_stopped()
        assert writers[0].execute('SELECT count(*) FROM session_turn_leases').fetchone()[0]==1
    finally:
        for writer in writers:writer.close()


@pytest.mark.parametrize("quiescent",[True],indirect=True)
def test_retained_native_invocation_replacement_is_not_accepted_as_quiescent(quiescent,monkeypatch):
    s=quiescent
    from hermes_cli.friday_native_control import CountedNativeCommands
    from hermes_cli.friday_native_supervision import SupervisorError
    def replaced(self,argv,timeout,**kw):
        unit=argv[argv.index('show')+1]
        values={'LoadState':'loaded','Transient':'yes','Description':NativeSupervisor.description(s.row),
            'InvocationID':'c'*32,'ActiveState':'inactive','SubState':'dead','Result':'success',
            'MainPID':'0','ControlGroup':'','KillMode':'control-group','SendSIGKILL':'yes'}
        return SimpleNamespace(returncode=0,stdout='\n'.join(k+'='+v for k,v in values.items()))
    # association(submitted=True) used actual native association producers.
    monkeypatch.setattr(CountedNativeCommands,'run',replaced)
    before=tree(s.f.e.home)
    with pytest.raises(SupervisorError,match='invocation_changed'):s.a._workers_stopped()
    assert tree(s.f.e.home)==before
