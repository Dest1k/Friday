"Inert, bounded Root-only stopped recovery observation. Never imports native code.\n\nThe caller authenticates Root's scope and holds existing common admission custody.\nObserve SQLite BEFORE freezing bytes; after handles close, only snapshots are used.\nNo payloads, route keys, session IDs or message contents enter returned observations.\n"
from pathlib import Path
import datetime, hashlib, json, os, sqlite3, stat, time

MAX_MEMBERS = 4096
MAX_FILE_BYTES = 16 * 1024**2
MAX_HASH_BYTES = 128 * 1024**2

def require(value, reason):
    if not value:
        raise ValueError(reason)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def exact_path(value):
    require(type(value) is str and value.startswith('/') and 'UNBOUND' not in value,
            'Root_exact_absolute_recovery_path_required')
    path = Path(value)
    require(str(path) == value and '..' not in path.parts, 'Root_canonical_recovery_path_required')
    return path

def checked(scope, *, home, frame):
    home, frame = Path(home), Path(frame)
    require(type(scope) is dict and scope.get('root_qualified_complete_scope') is True
            and scope.get('other_relevant_writers_admission_sealed') is True,
            'Root_complete_stopped_recovery_scope_and_writer_seal_required')
    require(set(scope.get('covered_categories', [])) == {'active_turn', 'resume_flags', 'once', 'cancel'}
            and scope.get('evidence'), 'Root_recovery_categories_and_evidence_required')
    require(scope.get('launch_home') == str(home), 'Root_exact_launch_home_required')
    expected = {'default': str(home), 'dest_telegram': str(home / 'profiles/dest_telegram'),
                'telegram-bot-8812646969': str(home / 'profiles/telegram-bot-8812646969')}
    require(scope.get('served_home_roster') == expected
            and scope.get('root_qualified_actual_served_homes') is True,
            'Root_actual_exact_served_home_roster_required')
    homes = [exact_path(value) for value in expected.values()]
    sessions = exact_path(scope.get('routing_sessions_dir'))
    require(sessions.is_relative_to(home) and sessions != home
            and scope.get('root_qualified_actual_routing_sessions_dir') is True,
            'Root_actual_routing_sessions_dir_required')
    paths = [home / name for name in ['.clean_shutdown', '.restart_failure_counts',
             'gateway/restart_loop.json', '.restart_notify.json', '.restart_pending.json']]
    paths += [sessions / 'sessions.json'] + [p / 'processes.json' for p in homes]
    extra = scope.get('root_qualified_additional_state_paths')
    require(type(extra) is list and extra == sorted(set(extra)) and len(extra) <= 64,
            'Root_bounded_exact_additional_recovery_paths_required')
    for name in extra:
        path = exact_path(name)
        require(any(path.is_relative_to(p) and path != p for p in homes)
                and not path.is_relative_to(frame)
                and path.name not in {'state.db', 'state.db-wal', 'state.db-shm'}
                and path.name not in {'ROOT-NATIVE220-LIVE-OPERATION.json','.ROOT-NATIVE220-LIVE-OPERATION.json.pending','ROOT-NATIVE215-LIVE-OPERATION.json', '.ROOT-NATIVE212-LIVE-OPERATION.json.pending', 'ROOT-NATIVE216-LIVE-OPERATION.json', '.ROOT-NATIVE216-LIVE-OPERATION.json.pending', 'ROOT-NATIVE218-LIVE-OPERATION.json', '.ROOT-NATIVE218-LIVE-OPERATION.json.pending', '.ROOT-NATIVE222-LIVE-OPERATION.json.pending', '.ROOT-NATIVE214-LIVE-OPERATION.json.pending', '.ROOT-NATIVE215-LIVE-OPERATION.json.pending', 'ROOT-NATIVE214-LIVE-OPERATION.json', 'ROOT-NATIVE212-LIVE-OPERATION.json', 'ROOT-NATIVE222-LIVE-OPERATION.json'}
                and path.name not in {'ROOT-NATIVE221-LIVE-OPERATION.json','.ROOT-NATIVE221-LIVE-OPERATION.json.pending','ROOT-NATIVE223-LIVE-OPERATION.json', '.ROOT-NATIVE223-LIVE-OPERATION.json.pending'}
                and not path.name.startswith('s05-own-stop-')
                and 'pending_messages' not in path.parts,
                'Root_extra_path_outside_qualified_singleton_scope')
        paths.append(path)
    # This actor never calls the native cancel verb: no historical tester once files.
    require(scope.get('operation_cancel_receipt') is None, 'unused_old_cancel_receipt_not_startup_input')
    names = sorted(str(p) for p in paths)
    require(len(names) == len(set(names)) and scope.get('related_recovery_state_paths') == names,
            'Root_complete_source_derived_singletons_required')
    return homes, sessions, [Path(p) for p in names]

def identity(info):
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns]

def directory(path, *, home):
    'Every existing ancestor is real; managed directories must be owned.\n\n    Missing directories retain the nearest real ancestor and exact absent suffix.\n    A dangling link is never treated as absence.\n    '
    path, home = Path(path), Path(home)
    require(path.is_relative_to(home), 'recovery_directory_outside_home')
    chain = list(reversed(path.parents)) + [path]
    result, missing = {}, False
    for item in chain:
        if item == Path('/'):
            continue
        if missing or not os.path.lexists(item):
            require(item.is_relative_to(home), 'recovery_home_ancestor_missing')
            result[str(item)] = None
            missing = True
            continue
        info = item.lstat()
        require(stat.S_ISDIR(info.st_mode), 'recovery_directory_or_parent_is_link_or_not_directory')
        if item.is_relative_to(home):
            require(info.st_uid == os.getuid(), 'recovery_directory_not_owned')
        # Directory size/times change with irrelevant sibling writes. Identity and mode
        # are stable; pending directory membership itself is recorded independently.
        result[str(item)] = identity(info)[:5]
    return result, missing

def file_snapshot(path, *, home, check, budget):
    check()
    parents, absent_parent = directory(path.parent, home=home)
    if absent_parent or not os.path.lexists(path):
        return {'parents': parents, 'file': None}
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1,
            'recovery_file_not_owned_regular_singlelink')
    require(before.st_size <= MAX_FILE_BYTES, 'recovery_file_size_limit')
    budget[0] += before.st_size
    require(budget[0] <= MAX_HASH_BYTES, 'recovery_total_hash_limit')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        require(identity(os.fstat(fd)) == identity(before), 'recovery_file_changed_before_open')
        hashed = hashlib.sha256()
        while True:
            check()
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            hashed.update(chunk)
        require(identity(os.fstat(fd)) == identity(before) == identity(path.lstat()),
                'recovery_file_changed_during_hash')
    finally:
        os.close(fd)
    return {'parents': parents, 'file': {'sha256': hashed.hexdigest(), 'metadata': identity(before)}}

def member_names(fd, *, check, limit):
    # Refuse the first excess entry before materializing an unbounded directory.
    names = []
    with os.scandir(fd) as entries:
        for entry in entries:
            check()
            require(len(names) < limit, 'recovery_directory_member_limit')
            names.append(entry.name)
    return sorted(names)

def snapshot(scope, *, home, frame, check):
    homes, _sessions, singletons = checked(scope, home=home, frame=frame)
    result = {'schema': 'frw.root222.stopped-related-recovery-snapshot.v2',
              'scope_sha256': digest(scope), 'singletons': {}, 'pending_directories': {}}
    budget = [0]
    for path in singletons:
        result['singletons'][str(path)] = file_snapshot(path, home=home, check=check, budget=budget)
    total_members = 0
    for served in homes:
        check()
        path = served / 'pending_messages'
        parents, missing = directory(path, home=home)
        row = {'parents': parents, 'members': None if missing else {}, 'json_files': {}}
        if not missing:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                before = identity(os.fstat(fd))
                names = member_names(fd, check=check, limit=MAX_MEMBERS - total_members)
                total_members += len(names)
                require(total_members <= MAX_MEMBERS, 'recovery_directory_member_limit')
                for name in names:
                    check()
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    require(info.st_uid == os.getuid() and stat.S_ISREG(info.st_mode)
                            and info.st_nlink == 1, 'pending_member_not_owned_flat_regular_singlelink')
                    row['members'][name] = identity(info)
                    if name.endswith('.json'):
                        row['json_files'][name] = file_snapshot(path / name, home=home, check=check, budget=budget)['file']
                require(names == member_names(fd, check=check, limit=MAX_MEMBERS)
                        and before == identity(os.fstat(fd))
                        == identity(path.lstat()), 'pending_membership_changed_during_snapshot')
            finally:
                os.close(fd)
        result['pending_directories'][str(path)] = row
    return result

def read_json(path, *, check):
    check()
    if not os.path.lexists(path):
        return None
    require(path.lstat().st_size <= MAX_FILE_BYTES, 'recovery_json_size_limit')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        with os.fdopen(fd, 'r', encoding='utf-8-sig') as stream:
            value = json.load(stream)
    except BaseException:
        raise ValueError('malformed_stopped_recovery_json') from None
    check()
    return value

def route_checked(key, value):
    # Deliberately conservative finite-operation acceptance; malformed primary rows
    # must not be silently skipped and turn a shadowed legacy marker effective.
    require(type(key) is str and key and type(value) is dict and value.get('session_key') == key,
            'invalid_primary_or_fallback_route')
    for field in ['session_id', 'created_at', 'updated_at']:
        require(type(value.get(field)) is str and value[field], 'invalid_route_required_field')
    require('/' not in value['session_id'] and '\\' not in value['session_id']
            and '..' not in value['session_id'] and '..' not in key
            and not key.startswith(('/', '\\'))
            and not (len(key) >= 2 and key[0].isalpha() and key[1] == ':')
            and not (len(value['session_id']) >= 2 and value['session_id'][0].isalpha()
                     and value['session_id'][1] == ':'), 'unsafe_route_session_identity')
    for field in ['created_at', 'updated_at']:
        try:
            datetime.datetime.fromisoformat(value[field])
        except ValueError:
            raise ValueError('invalid_route_datetime') from None
    require(value.get('transport_profile') in {'default', 'dest_telegram', 'telegram-bot-8812646969'},
            'route_transport_profile_not_Root_served')
    require(value.get('metadata') is None or type(value['metadata']) is dict,
            'route_metadata_would_fail_native_parse')
    for field in ['model_override', 'prompt_pin']:
        require(value.get(field) is None or type(value[field]) is dict,
                'route_optional_mapping_shape_required')
    last_resume = value.get('last_resume_marked_at')
    if last_resume is not None:
        require(type(last_resume) is str, 'route_optional_datetime_shape_required')
        try:
            datetime.datetime.fromisoformat(last_resume)
        except ValueError:
            raise ValueError('invalid_route_optional_datetime') from None
    origin = value.get('origin')
    require(origin is None or (type(origin) is dict and origin.get('platform') == 'telegram'
                              and 'chat_id' in origin), 'finite_Telegram_route_origin_parse_required')
    require(not value.get('active_turn_token') and not value.get('active_turn_started_at')
            and not value.get('resume_pending') and not value.get('suspended'),
            'effective_route_has_active_resume_or_suspended_conflict')

def observe_before_freeze(scope, *, home, frame, check, writers_sealed, db_snapshot):
    'Only future actor invokes this inside common custody, before byte freeze.\n\n    Handles close before return. Primary load failure/invalid rows is a refusal;\n    missing-key legacy fallback participates in the effective set. Shadowed old\n    mirror markers are retained byte-for-byte and never become false conflicts.\n    '
    require(writers_sealed is True, 'all_actual_writers_must_be_sealed_before_qualifier')
    homes, sessions, _singletons = checked(scope, home=home, frame=frame)
    initial = snapshot(scope, home=home, frame=frame, check=check)
    conflicts = []
    for row in initial['pending_directories'].values():
        if row['json_files']:
            conflicts.append('pending_history_spool')
    for served in homes:
        value = read_json(served / 'processes.json', check=check)
        if value not in (None, []):
            conflicts.append('pending_process_custody')
    for name in ['.restart_notify.json', '.restart_pending.json']:
        if os.path.lexists(Path(home) / name):
            conflicts.append('restart_notification_input')
    value = read_json(Path(home) / '.restart_failure_counts', check=check)
    if value not in (None, {}):
        conflicts.append('restart_failure_counter_input')
    # All SQLite work is before freeze. Do not use native constructors, PRAGMA
    # checkpoint, repair, backups, immutable=1 (which could ignore a real WAL), or writes.
    routes, profile_rows, ledger_rows = {}, [], 0
    for served in homes:
        check()
        dbpath = served / 'state.db'
        # Parent/path/owner/link checks before SQLite follows any path.
        _parents, missing = directory(dbpath.parent, home=home)
        require(not missing and os.path.lexists(dbpath), 'Root_served_database_missing')
        info = dbpath.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                'Root_served_database_not_owned_regular_singlelink')
        db = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True, timeout=1)
        try:
            def progress():
                check()
                return 0
            db.set_progress_handler(progress, 1000)
            count, largest, total, malformed = db.execute(
                'SELECT count(*), coalesce(max(length(cast(entry_json as blob))),0), '
                'coalesce(sum(length(cast(entry_json as blob)) + length(cast(scope as blob)) + '
                "length(cast(session_key as blob))),0), coalesce(sum(typeof(entry_json) != 'text' "
                "OR typeof(scope) != 'text' OR typeof(session_key) != 'text'),0) FROM gateway_routing"
            ).fetchone()
            require(count <= MAX_MEMBERS and largest <= MAX_FILE_BYTES
                    and total <= MAX_HASH_BYTES and malformed == 0, 'routing_row_or_payload_limit')
            if served != Path(home):
                require(count == 0, 'secondary_profile_routing_conflict')
            cursor = db.execute('SELECT scope, session_key, entry_json FROM gateway_routing')
            for actual_scope, key, raw in cursor:
                check()
                require(actual_scope == str(sessions), 'unexpected_launch_routing_scope')
                require(key not in routes and type(raw) is str and len(raw) <= MAX_FILE_BYTES,
                        'duplicate_or_oversized_primary_route')
                try:
                    value = json.loads(raw)
                except ValueError:
                    raise ValueError('malformed_primary_route_json') from None
                route_checked(key, value)
                routes[key] = value
            if served == Path(home):
                # THIS finite operation is admitted only with delivered rows. Other
                # terminal product states are not reclassified or deleted.
                ledger_rows, nondelivered = db.execute(
                    "SELECT count(*), coalesce(sum(state != 'delivered' OR state IS NULL),0) FROM delivery_obligations"
                ).fetchone()
                require(nondelivered == 0, 'finite_operation_requires_all_ledger_rows_delivered')
            profile_rows.append(count)
        finally:
            db.close()
        check()
    mirror = read_json(sessions / 'sessions.json', check=check)
    require(mirror is None or type(mirror) is dict, 'legacy_routing_mirror_not_object')
    require(mirror is None or len(mirror) <= MAX_MEMBERS, 'legacy_routing_member_limit')
    fallback = 0
    for key, value in (mirror or {}).items():
        if key.startswith('_') or key in routes:
            continue
        route_checked(key, value)
        routes[key] = value
        fallback += 1
    final = snapshot(scope, home=home, frame=frame, check=check)
    require(initial == final, 'recovery_inputs_changed_during_stopped_qualification')
    check()
    db9 = db_snapshot()  # All three SQLite handles are CLOSED before byte capture.
    check()
    return {'schema': 'frw.root222.current-stopped-recovery-qualification.v1',
            'qualified': not conflicts, 'conflict_classes': sorted(set(conflicts)),
            'scope_sha256': digest(scope), 'related_snapshot_sha256': digest(final),
            'db9_snapshot_sha256': digest(db9),
            'effective_routes': len(routes), 'primary_profile_row_counts': profile_rows,
            'fallback_routes': fallback, 'ledger_rows': ledger_rows,
            'all_ledger_rows_delivered': True, 'sqlite_handles_closed': True,
            'observed_monotonic': time.monotonic(),
            'qualification': 'CURRENT_STOPPED_INPUTS_ONLY_NOT_POSITIVE_STARTUP_SWEEP'}

def frozen_qualification_checked(qualification, snapshot_value, scope):
    require(type(qualification) is dict and qualification.get('qualified') is True
            and qualification.get('sqlite_handles_closed') is True
            and qualification.get('scope_sha256') == digest(scope)
            and qualification.get('related_snapshot_sha256') == digest(snapshot_value['related'])
            and qualification.get('db9_snapshot_sha256') == digest(snapshot_value['DB9']),
            'actual_stopped_qualification_must_join_exact_frozen_recovery_inputs')
    return True
