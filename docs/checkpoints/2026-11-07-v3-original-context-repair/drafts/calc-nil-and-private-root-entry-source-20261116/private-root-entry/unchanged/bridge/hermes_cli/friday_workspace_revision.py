"""Descriptor-only ordinary text revision using native read coverage and custody.

No model-provided authorization/version proof. After restart a normal read_file
re-establishes coverage. Linux NOREPLACE captures then publishes: a concurrent
replacement is never overwritten; interrupted transactions remain recoverable.
The renameat2 setup follows the existing native friday_skill_io publish seam.
"""
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import stat
import time
import uuid
from tools import file_tools_read_tracking as tracking
from hermes_cli.friday_user_scope import ScopeDenied

_FIELDS = ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink','st_uid')


def check(cap):
    cap.check()
    from agent.web_call_context import _current
    call = _current.get()
    if call is not None:
        call.check()


def _key(cap, task_id):
    from agent.web_call_context import _current
    call = _current.get()
    return ('ordinary_workspace', cap.key, cap.admission_generation,
            cap.directory_identity, getattr(call, 'session_id', ''), task_id)


class NonTextSnapshotError(ValueError):
    """Authenticated file bytes failed UTF-8 decoding; no content is exposed."""


def snapshot(fd, leaf, *, durable=False, require_utf8=True):
    if type(require_utf8) is not bool:
        raise ScopeDenied()
    item = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        before = os.fstat(item)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or before.st_uid != os.getuid() or before.st_mode & 0o077
                or before.st_size > 1000000):
            raise ScopeDenied()
        chunks=[]; size=0
        while chunk := os.read(item, min(65536,1000001-size)):
            size += len(chunk); chunks.append(chunk)
            if size > 1000000: raise ScopeDenied()
        if durable: os.fsync(item)
        after = os.fstat(item)
        named = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
        version = tuple(getattr(before,k) for k in _FIELDS)
        if (size != before.st_size or version != tuple(getattr(after,k) for k in _FIELDS)
                or version != tuple(getattr(named,k) for k in _FIELDS)):
            raise ScopeDenied()
        data=b''.join(chunks)
        if require_utf8:
            try:
                data.decode('utf-8')
            except UnicodeDecodeError:
                raise NonTextSnapshotError() from None
        return data, (*version,hashlib.sha256(data).digest())
    finally:
        os.close(item)


def note_read(cap, task_id, path, version, ranges, total, rendered):
    """Stage native coverage on its original call; raw tool success grants nothing."""
    from agent.web_call_context import _current
    call = _current.get()
    if call is None or call.task_id != task_id or not hasattr(call, 'agent'):
        return
    check(cap)
    call._workspace_read = (cap, _key(cap,task_id), path, version,
                            tuple(ranges), total, rendered)


def prepare_read_delivery(message):
    """Called only after the canonical native result append/flush succeeds."""
    from agent.web_call_context import _current
    call = _current.get()
    if call is not None and hasattr(call, '_workspace_read'):
        call._workspace_read_message = message


def finalize_read_delivery(call, message):
    # The complete batch has passed per-tool/aggregate persistence and steer.
    # Still no grant: compression and provider formatting happen later.
    read = getattr(call, '_workspace_read', None)
    if read is not None and getattr(call, '_workspace_read_message', None) is message:
        call._workspace_read_ready = message.get('content') == read[-1]


def _wire_reads(payload):
    """Recognized native provider result envelopes only; never infer from prose."""
    if '_moa_prepared_request' in payload:
        return []
    extra = payload.get('extra_body')
    if isinstance(extra,dict) and any(k in extra for k in ('messages','input')):
        return []
    rows = payload.get('messages', payload.get('input'))
    if not isinstance(rows, list):
        return []
    found = []
    def text(value):
        if isinstance(value,str): return value
        if (isinstance(value,list) and len(value)==1 and isinstance(value[0],dict)
                and value[0].get('type') in ('text','input_text')):
            return value[0].get('text')
        return None
    for row in rows:
        if not isinstance(row,dict): continue
        if row.get('role') == 'tool':
            found.append((row.get('tool_call_id'),text(row.get('content'))))
        elif row.get('type') == 'function_call_output':
            found.append((row.get('call_id'),text(row.get('output'))))
        elif row.get('role') == 'user' and isinstance(row.get('content'),list):
            for block in row['content']:
                if isinstance(block,dict) and block.get('type') == 'tool_result':
                    found.append((block.get('tool_use_id'),text(block.get('content'))))
    return found


def read_delivery_candidates(agent, payload, task_id):
    """Take the exact final transport input after execution middleware/preflight."""
    # Codex may prune again on a zero-event retry below this seam. Its native
    # transport still runs, but this unqualified route cannot grant new coverage.
    if getattr(agent,'api_mode',None) == 'codex_responses':
        return []
    rows = _wire_reads(payload)
    result=[]
    for (task, ident),call in getattr(agent,'_tool_result_calls',{}).items():
        read=getattr(call,'_workspace_read',None)
        if task != task_id or read is None or not getattr(call,'_workspace_read_ready',False):
            continue
        matched=[body for call_id,body in rows if call_id == ident]
        if len(matched)==1 and matched[0] == read[-1]:
            result.append((call,read))
    return result


def accept_read_delivery(agent, candidates):
    """A successful native transport return confirms delivery, not model recall.

    Original authority and clocks are checked again. Failed transport calls never
    invoke this function, and later request omission cannot grant an unseen page.
    """
    from agent.tool_executor import _tool_result_environment
    from agent.web_call_context import _current
    from hermes_cli.friday_user_scope import current
    for call,read in candidates:
        if getattr(call,'_workspace_read',None) is not read: continue
        call._workspace_read = None
        call._workspace_read_message = None
        call._workspace_read_ready = False
        cap,key,path,version,ranges,total,_ = read
        with _tool_result_environment(agent,call.task_id,call.call_id):
            if _current.get() is not call or current() is not cap: continue
            try: check(cap)
            except (ScopeDenied,RuntimeError,TimeoutError): continue
            if _key(cap,call.task_id) != key: continue
            with tracking._read_tracker_lock:
                state=tracking._task_data(key)
                for start,end in ranges:
                    full,redacted=tracking._note_read_coverage(state,path,version,start,end,total,False)
                    if full and not redacted: state['full_write_baselines'][path]=version
                tracking._cap_read_tracker_data(state)


def _baseline(cap,task_id,path):
    with tracking._read_tracker_lock:
        state=tracking._read_tracker.get(_key(cap,task_id),{})
        return state.get('full_write_baselines',{}).get(path)


def _rename(fd, source, target):
    return _move(fd,source,fd,target)


def _same_captured(left,right):
    # rename changes ctime; all other observed identity/permission/byte fields stay.
    return left[:4]+left[5:] == right[:4]+right[5:]


def _failure(error,ref,unknown=False):
    if unknown:
        from agent.web_call_context import _current
        call=_current.get()
        if call is not None and hasattr(call,'agent'):
            call.agent._friday_reply_effect_unknown=True
    return json.dumps({'success':False,'error':error,'recovery_ref':ref,
                       'effect_disposition':'unknown' if unknown else 'none'})



# Local ceiling only: the original capability/call deadline can expire sooner.
_WRITE_LOCK_WAIT_SECONDS = 2.0
_WRITE_LOCK_POLL_SECONDS = 0.02


def _acquire_write_lock(cap, fd):
    """Wait briefly for this held directory, without extending native authority.

    scoped_file opens a separate directory description for each call. Its flock
    serializes distinct leaves and the same leaf across threads/processes, so an
    additional unbounded per-path threading lock is unnecessary on this path.
    """
    deadline = time.monotonic() + _WRITE_LOCK_WAIT_SECONDS
    while True:
        check(cap)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                check(cap)
                return False
            time.sleep(min(_WRITE_LOCK_POLL_SECONDS, remaining))


def write(cap,fd,leaf,path,content,task_id):
    """No overwrite syscall: capture current name then publish only if absent.

    A fixed per-leaf fence blocks automatic retry after a crash. Beforeimages are
    retained privately; no physical home path or authority key is returned.
    """
    data=content.encode('utf-8')
    tag=hashlib.sha256(leaf.encode()).hexdigest()[:32]
    fence='.friday-revision-'+tag
    ref=uuid.uuid4().hex
    if _acquire_write_lock(cap, fd):
        try:
            check(cap)
            try: os.stat(fence,dir_fd=fd,follow_symlinks=False)
            except FileNotFoundError: pass
            else: return _failure('file_revision_reconciliation_required',tag,True)
            # A retained archive also fences the leaf if restoring the fixed
            # fence and recreating its name both fail. Pending markers predate
            # archive rename and survive until the durable commit is complete.
            pending='.pending-'+tag
            for name in os.listdir(fd):
                if not name.startswith('.friday-before-'): continue
                archive_fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                try:
                    try: os.stat(pending,dir_fd=archive_fd,follow_symlinks=False)
                    except FileNotFoundError: pass
                    else: return _failure('file_revision_reconciliation_required',name[len('.friday-before-'):],True)
                finally: os.close(archive_fd)
            try: os.stat(leaf,dir_fd=fd,follow_symlinks=False)
            except FileNotFoundError:
                # Text needs the same complete-byte publication and uncertain-
                # effect accounting as documents. Never expose a partial final
                # name or report a post-publication failure as an absent write.
                # Late import: the publisher shares this module's check/_move.
                from hermes_cli.friday_workspace_docx import _create_bytes
                return _create_bytes(cap,fd,leaf,path,data,output_format='text')
            original,version=snapshot(fd,leaf)
            if _baseline(cap,task_id,path) != version:
                return json.dumps({'success':False,'error':'file_revision_requires_current_full_read',
                    'path':path,'hint':'Read the complete current file with read_file, continue any partial pages, merge the change, then write_file.'})
            # Capability/OS check happens before a transaction or original move.
            check(cap)
            libc=ctypes.CDLL(None)
            if not hasattr(libc,'renameat2'): raise ScopeDenied()
            os.mkdir(fence,0o700,dir_fd=fd)
            tx=os.open(fence,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            captured=False;published=False;archive_attempted=False
            try:
                item=os.open('new',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=tx)
                with os.fdopen(item,'wb') as stream:
                    stream.write(data);stream.flush();os.fsync(stream.fileno())
                os.fsync(tx);os.fsync(fd)
                staged,new_version=snapshot(tx,'new')
                if staged != data: raise ScopeDenied()
                check(cap)
                # Cross-directory rename uses the same native NOREPLACE primitive.
                _move(fd,leaf,tx,'before');captured=True
                actual,captured_version=snapshot(tx,'before',durable=True)
                if actual != original or not _same_captured(version,captured_version):
                    raise ScopeDenied()
                # Persist the exact old inode and both sides of the capture
                # before exposing the replacement.
                os.fsync(tx);os.fsync(fd)
                check(cap)
                staged,stage_version=snapshot(tx,'new')
                if staged != data or stage_version != new_version: raise ScopeDenied()
                # The captured inode is the only old object; a new leaf wins.
                _move(tx,'new',fd,leaf);published=True
                os.fsync(tx);os.fsync(fd)
                check(cap)
                after,after_version=snapshot(fd,leaf)
                old,old_version=snapshot(tx,'before')
                if (after != data or not _same_captured(new_version,after_version)
                        or old != original or not _same_captured(version,old_version)):
                    return _failure('file_revision_publication_uncertain',tag,True)
                marker=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=tx)
                try: os.fsync(marker)
                finally: os.close(marker)
                os.fsync(tx)
                archive_attempted=True
                _rename(fd,fence,'.friday-before-'+ref)
                os.fsync(fd)
                # The content and archive are now durably committed. Marker
                # cleanup failure can only conservatively block another write.
                cleanup_pending=False
                try: os.unlink(pending,dir_fd=tx);os.fsync(tx)
                except OSError: cleanup_pending=True
                # Future full writes still require a displayed read of this version.
                return json.dumps({'success':True,'path':path,'bytes_written':len(data),
                    'scope':'own_user_workspace','create_only':False,'verified':True,
                    'previous_version_preserved':True,'revision_ref':ref,
                    'revision_cleanup_pending':cleanup_pending})
            except (OSError,ScopeDenied,RuntimeError,TimeoutError):
                if published:
                    # Rename may have completed even if its wrapper raised. Use
                    # descriptor identity, never an assumed name, for recovery.
                    archive='.friday-before-'+ref
                    recovery=tag
                    if archive_attempted:
                        try:
                            named=os.stat(archive,dir_fd=fd,follow_symlinks=False)
                            held=os.fstat(tx)
                            if (named.st_dev,named.st_ino)==(held.st_dev,held.st_ino):
                                recovery=ref
                                try:
                                    _rename(fd,archive,fence)
                                    recovery=tag
                                    os.fsync(fd)
                                except OSError:
                                    # A remaining archive must still block native
                                    # replay. This mkdir never replaces a name.
                                    try: os.mkdir(fence,0o700,dir_fd=fd)
                                    except FileExistsError: pass
                                    except OSError: pass
                        except OSError: pass
                        # Account for a wrapper that raised after restoring too.
                        try:
                            named=os.stat(fence,dir_fd=fd,follow_symlinks=False)
                            held=os.fstat(tx)
                            if (named.st_dev,named.st_ino)==(held.st_dev,held.st_ino):
                                recovery=tag
                        except OSError: pass
                    return _failure('file_revision_publication_uncertain',recovery,True)
                if captured:
                    try: _move(tx,'before',fd,leaf);os.fsync(fd)
                    except OSError: return _failure('file_revision_restore_conflict',tag,True)
                # Only known uncommitted stage is removed. Unknown remnants stay.
                try:
                    os.unlink('new',dir_fd=tx)
                    os.rmdir(fence,dir_fd=fd);os.fsync(fd)
                except OSError:
                    return _failure('file_revision_cleanup_incomplete',tag,True)
                return _failure('file_revision_not_committed',tag)
            finally: os.close(tx)
        finally: fcntl.flock(fd,fcntl.LOCK_UN)
    return json.dumps({'success':False,'error':'workspace_write_busy',
                       'retryable':True,'effect_disposition':'none'})


def _move(source_fd,source,target_fd,target):
    libc=ctypes.CDLL(None,use_errno=True)
    rename=getattr(libc,'renameat2',None)
    if rename is None: raise OSError(errno.ENOSYS,'atomic no-replace unavailable')
    rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
    rename.restype=ctypes.c_int
    if rename(source_fd,os.fsencode(source),target_fd,os.fsencode(target),1):
        code=ctypes.get_errno();raise OSError(code,os.strerror(code))
