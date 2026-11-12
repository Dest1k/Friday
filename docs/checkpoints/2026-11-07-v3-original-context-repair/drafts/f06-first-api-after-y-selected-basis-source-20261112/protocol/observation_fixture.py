def obs_digest(value):return sha(encoded(value))
def identity(inode, size=1, mode=0o600):
    return dict(device=1, inode=inode, uid=1000, gid=1000, mode=mode,
                nlink=1, bytes=size, mtime_ns=10, ctime_ns=10)

def refresh(value):
    value['custody']['sha256'] = obs_digest(value['custody']['records'])
    b = value['f06_mutable_boundary']
    b['once_sha256'] = value['custody']['sha256']
    b['native_boundary_sha256'] = obs_digest(value['databases'])
    b['history_manifest_sha256'] = value['history']['manifest_sha256']
    b['cursor_sha256'] = value['cursor']['sha256']
    b['ingress_lineage_sha256'] = obs_digest(dict(source=value['source'], databases=value['databases'],
                                             custody=value['custody']['sha256']))

def fixture_pair():
    """A small synthetic pair with faithful current207 metadata shape."""
    dbs = {}
    for n, label in enumerate(('default', 'dest', 'tester'), 1):
        dbs[label] = dict(path='/synthetic/' + label + '/state.db',
            identity={k: v for k, v in identity(n).items() if k in ('device','inode','uid','gid','mode','nlink')},
            messages={'default':30,'dest':196,'tester':5510}[label], max_message_id=n * 10000,
            sessions=n, leases=0, all_origin_pending_delegations=0,
            session_metadata_sha256=obs_digest(['synthetic-session', label]),
            message_metadata_sha256=obs_digest(['synthetic-message-metadata', label]), pending_message_entries=0)
    dbs['tester']['principal'] = dict(id='synthetic-session', source='telegram', user_id='synthetic-user',
        chat_id='synthetic-chat', chat_type='dm', session_key='synthetic-key',
        profile_name='synthetic-profile', transport_profile='default')
    records = [[f'synthetic-run-{n:03}.json', obs_digest(['synthetic-canonical', n]), n + 1] for n in range(512)]
    gateway = dict(pid=123, start_time=456, synthetic=True, finite_sample=0.5)
    value = dict(installed_product=copy.deepcopy(y._EXPECTED),
        services=dict(gateway=dict(unit={'ActiveState':'active'}, identity=gateway),
                      dashboard=dict(unit={'ActiveState':'active'}, identity={'pid':124})),
        gateway=gateway, native_readonly=dict(identity=gateway, session_id='synthetic-session'), databases=dbs,
        history=dict(records=records, run_ids=[r[0][:-5] for r in records], manifest_sha256=obs_digest(records)),
        cursor=dict(path='/synthetic/cursor.json', bytes=2, sha256=obs_digest(['synthetic-cursor']), identity=identity(50, 2)),
        cooldown=None,
        custody=dict(records=[['cursor.json', identity(50, 2)], ['once', identity(51, 4096, 0o700)],
                              ['once/token.json', identity(52, 8)]], sha256='0'*64, contents_read=False),
        source=dict(path='/synthetic/source.bin', bytes=10, sha256=obs_digest(['synthetic-source'])),
        profile_configs={label:dict(path='/synthetic/'+label+'/config.yaml', bytes=20, sha256=obs_digest(['config',label])) for label in dbs},
        source_identity=dict(device=1, inode=60, size_bytes=10, uid=1000, mtime_ns=10, ctime_ns=10),
        f06_mutable_boundary=dict(history_manifest_sha256='0'*64, cursor_sha256='0'*64,
            native_boundary_sha256='0'*64, once_sha256='0'*64, ingress_lineage_sha256='0'*64,
            gateway=gateway, B=dict(profile='synthetic-profile', session_id='synthetic-session',
                session_key='synthetic-key', native_max_id=30000),
            phase_unconsumed=True, uploads_this_operation=1, producer_calls=0, restarts=0),
        all_profile_projection_limit='ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED')
    refresh(value)
    new = copy.deepcopy(value)
    new['custody']['records'].append([y.LEAF, identity(70, 444)])
    new['custody']['records'].sort(key=lambda r: tuple(r[0].split('/')))
    refresh(new)
    return value, new
