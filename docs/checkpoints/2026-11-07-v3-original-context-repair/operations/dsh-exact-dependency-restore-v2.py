"""V2 preassembled-branch no-replace publication. This module grants no authority.

No imports of mutable project modules. Descriptor edge retention follows
worker_archive._Directory; rename_noreplace is the existing ordinary installer
renameat2(RENAME_NOREPLACE) boundary. All writes belong to one consumed intent.
CLI: preflight REQUEST SHA | execute REQUEST SHA | reconcile REQUEST SHA.
The caller (Root) must independently admit the exact request and current state.
"""
import os
import sys
import stat
import json
import hashlib
import time
import ctypes
from pathlib import PurePosixPath

MAX_JSON = 8 * 1024 * 1024
MAX_NODES = 6000
MAX_BYTES = 200 * 1024 * 1024
FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC


class Refused(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def unique(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, 'duplicate_json_key')
        obj[key] = value
    return obj


def decode(data):
    require(len(data) <= MAX_JSON, 'json_size')
    return json.loads(data, object_pairs_hook=unique,
        parse_constant=lambda x: (_ for _ in ()).throw(Refused('nonfinite_json')))


def identity(info, content=False):
    keys = ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode')
    if content:
        keys += ('st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    return {key: getattr(info, key) for key in keys}


def parts(path):
    require(type(path) is str and path.startswith('/') and str(PurePosixPath(path)) == path
        and '..' not in PurePosixPath(path).parts and path != '/', 'absolute_normal_path')
    return PurePosixPath(path).parts[1:]


class Chain:
    """Keep every directory edge open and prove it before/after each effect.

    Every source/anchor directory edge is retained and inode-pinned. V2 creates
    no canonical directories and never adopts a directory created during execute.
    """
    def __init__(self, path, allow_missing=False):
        self.path = path
        self.fds = [os.open('/', FLAGS | os.O_DIRECTORY)]
        self.edges = []
        self.missing = []
        protected = False
        try:
            for name in parts(path):
                parent = self.fds[-1]
                try:
                    fd = os.open(name, FLAGS | os.O_DIRECTORY, dir_fd=parent)
                except FileNotFoundError:
                    require(allow_missing, 'missing_directory')
                    self.missing = list(parts(path)[len(self.edges):])
                    break
                self.fds.append(fd)
                info = os.fstat(fd)
                require(info.st_uid in (0, os.getuid()) and
                    (not stat.S_IMODE(info.st_mode) & 0o022 or protected), 'unsafe_ancestor')
                if info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o077:
                    protected = True
                self.edges.append((parent, name, fd, identity(info)))
            self.prove()
        except BaseException:
            self.close()
            raise

    @property
    def fd(self):
        return self.fds[-1]

    def prove(self):
        for parent, name, fd, expected in self.edges:
            require(identity(os.fstat(fd)) == expected == identity(
                os.stat(name, dir_fd=parent, follow_symlinks=False)), 'parent_identity_changed')

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)
        self.fds = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def file_state_at(parent, name, *, expected=None, bound=MAX_BYTES, data=False, tick=lambda: None):
    fd = os.open(name, FLAGS | os.O_NONBLOCK, dir_fd=parent)
    try:
        first = os.fstat(fd)
        require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
            and first.st_nlink == 1 and first.st_size <= bound, 'owned_regular_single_link')
        digest = hashlib.sha256()
        chunks = []
        count = 0
        while True:
            tick()
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            digest.update(block)
            count += len(block)
            require(count <= bound, 'file_size_bound')
            if data:
                chunks.append(block)
        require(identity(first, True) == identity(os.fstat(fd), True) == identity(
            os.stat(name, dir_fd=parent, follow_symlinks=False), True), 'file_changed')
        row = {'identity': identity(first, True), 'sha256': digest.hexdigest(), 'bytes': count}
        if expected is not None:
            require(row == expected, 'source_or_guard_CAS_changed')
        if data:
            row['data'] = b''.join(chunks)
        return row
    finally:
        os.close(fd)


def file_state(path, **kwargs):
    p = PurePosixPath(path)
    with Chain(str(p.parent)) as chain:
        chain.prove()
        row = file_state_at(chain.fd, p.name, **kwargs)
        chain.prove()
        return row


def rename_noreplace(source_fd, source_name, target_fd, target_name):
    """Linux native primitive; no unsafe rename fallback on unsupported FS/kernel."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameat2
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(source_fd, os.fsencode(source_name), target_fd, os.fsencode(target_name), 1):
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number))


def absent_at(fd, name):
    try:
        os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise Refused('occupied_target')


class Budget:
    def __init__(self, seconds):
        require(type(seconds) is int and 120 <= seconds <= 240, 'bounded_future_budget_required')
        self.started_ns = time.monotonic_ns()
        self.deadline_ns = self.started_ns + seconds * 10**9

    def check(self):
        require(time.monotonic_ns() < self.deadline_ns, 'operation_deadline_consumed')


class Journal:
    def __init__(self, path, request_hash, budget):
        self.path = PurePosixPath(path)
        self.parent = Chain(str(self.path.parent))
        self.fd = None
        try:
            self.parent.prove()
            require(stat.S_IMODE(os.fstat(self.parent.fd).st_mode) == 0o700
                and os.fstat(self.parent.fd).st_uid == os.getuid(), 'private_journal_parent')
            self.fd = os.open(self.path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                | os.O_CLOEXEC, 0o600, dir_fd=self.parent.fd)
            require(stat.S_IMODE(os.fstat(self.fd).st_mode) == 0o600, 'journal_creation_mode')
            self.id = identity(os.fstat(self.fd))
            os.fsync(self.fd)
            os.fsync(self.parent.fd)
            self.write('INTENT_CONSUMED', request_sha256=request_hash,
                started_monotonic_ns=budget.started_ns, deadline_monotonic_ns=budget.deadline_ns)
        except BaseException:
            self.close()
            raise

    def write(self, event, **values):
        self.parent.prove()
        require(identity(os.fstat(self.fd)) == self.id == identity(os.stat(self.path.name,
            dir_fd=self.parent.fd, follow_symlinks=False)), 'journal_identity_changed')
        raw = encoded({'event': event, 'at_monotonic_ns': time.monotonic_ns(), **values})
        while raw:
            count = os.write(self.fd, raw)
            require(count > 0, 'journal_short_write')
            raw = raw[count:]
        os.fsync(self.fd)
        os.fsync(self.parent.fd)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        self.parent.close()


def prove_edges(edges):
    for parent, name, fd, expected in edges:
        require(identity(os.fstat(fd)) == expected == identity(
            os.stat(name, dir_fd=parent, follow_symlinks=False)), 'parent_identity_changed')


def held_tree(fd, *, tick=lambda: None):
    """Inventory a held root. Never reopen a path as a post-publication root."""
    root_dev = os.fstat(fd).st_dev
    observed = {}
    total = 0
    def walk(current, relative):
        nonlocal total
        tick()
        first = os.fstat(current)
        require(stat.S_ISDIR(first.st_mode) and first.st_uid == os.getuid()
            and first.st_gid == os.getgid() and first.st_dev == root_dev
            and stat.S_IMODE(first.st_mode) in (0o700, 0o755), 'tree_directory')
        observed[relative] = {'type': 'directory', 'identity': identity(first, True)}
        for name in sorted(os.listdir(current)):
            tick()
            require(name not in ('.', '..') and '/' not in name, 'member_name')
            child = name if relative == '.' else relative + '/' + name
            require(len(observed) < MAX_NODES, 'member_bound')
            before = os.stat(name, dir_fd=current, follow_symlinks=False)
            require(before.st_dev == root_dev and before.st_uid == os.getuid()
                and before.st_gid == os.getgid(), 'member_owner_device')
            if stat.S_ISDIR(before.st_mode):
                sub = os.open(name, FLAGS | os.O_DIRECTORY, dir_fd=current)
                try:
                    require(identity(before, True) == identity(os.fstat(sub), True), 'directory_open_race')
                    walk(sub, child)
                finally:
                    os.close(sub)
            elif stat.S_ISREG(before.st_mode):
                require(stat.S_IMODE(before.st_mode) in (0o600, 0o644, 0o755), 'member_file_mode')
                row = file_state_at(current, name, tick=tick)
                observed[child] = {'type': 'file', **row}
                total += row['bytes']
                require(total <= MAX_BYTES, 'tree_bytes')
            else:
                require(stat.S_ISLNK(before.st_mode) and before.st_nlink == 1
                    and stat.S_IMODE(before.st_mode) == 0o777, 'member_special_or_link_count')
                target = os.readlink(name, dir_fd=current)
                require(target and not target.startswith('/'), 'relative_link_required')
                resolved = os.path.normpath(str(PurePosixPath(child).parent / target))
                require(resolved != '..' and not resolved.startswith('../'), 'escaping_link')
                observed[child] = {'type': 'symlink', 'identity': identity(before, True),
                    'target': target, 'target_utf8_sha256': hashlib.sha256(target.encode()).hexdigest()}
            require(identity(before, True) == identity(os.stat(name, dir_fd=current,
                follow_symlinks=False), True), 'member_changed')
        require(identity(first, True) == identity(os.fstat(current), True), 'directory_changed')
    walk(fd, '.')
    for path, row in observed.items():
        if row['type'] == 'symlink':
            resolved = os.path.normpath(str(PurePosixPath(path).parent / row['target']))
            require(observed.get(resolved, {}).get('type') == 'file', 'link_target_not_regular_member')
    return {'entries': observed, 'count': len(observed), 'regular_bytes': total}


def same_tree(observed, expected, moved=False):
    require(observed['count'] == expected['count'] and observed['regular_bytes'] == expected['regular_bytes']
        and set(observed['entries']) == set(expected['entries']), 'tree_shape_changed')
    for name, original in expected['entries'].items():
        current = observed['entries'][name]
        if moved and name == '.':
            # Rename can update only this branch root's ctime. Never substitute its inode.
            before, after = dict(original['identity']), dict(current['identity'])
            before.pop('st_ctime_ns')
            after.pop('st_ctime_ns')
            require(current['type'] == original['type'] == 'directory' and before == after,
                'moved_root_identity_changed')
        else:
            require(current == original, 'tree_identity_or_bytes_changed')


def guard_state(request):
    for row in request['guards']:
        file_state(row['path'], expected=row['state'])
    for row in request['unchanged_symlinks']:
        path = PurePosixPath(row['path'])
        with Chain(str(path.parent)) as chain:
            chain.prove()
            info = os.stat(path.name, dir_fd=chain.fd, follow_symlinks=False)
            require(stat.S_ISLNK(info.st_mode) and identity(info, True) == row['identity']
                and os.readlink(path.name, dir_fd=chain.fd) == row['target'], 'unchanged_alias_CAS')
            chain.prove()


def load_request(path, sha):
    row = file_state(path, bound=MAX_JSON, data=True)
    require(row['sha256'] == sha, 'request_sha256')
    request = decode(row['data'])
    require(request['schema'] == 'frw.exact-dependency-preassembled-branches-request.v2'
        and len(request['branches']) == 3 and len(request['guards']) >= 1, 'request_shape')
    names, paths = [], []
    for branch in request['branches']:
        name = branch['target_name']
        require(type(name) is str and name not in ('', '.', '..') and '/' not in name, 'first_missing_branch_name')
        parts(branch['source'])
        names.append(name)
        paths.append(branch['source'])
    require(len(set(names)) == 3 and len(set(paths)) == 3, 'distinct_branches')
    require(not any(a != b and a.startswith(b + '/') for a in paths for b in paths), 'nested_source_branches')
    return request


class BranchHold:
    def __init__(self, branch, anchor, tick=lambda: None):
        self.branch = branch
        self.chain = Chain(branch['source'])
        try:
            expected_edges = branch['source_ancestry']
            require([edge[3] for edge in self.chain.edges] == expected_edges, 'source_ancestry_CAS')
            self.root_identity = branch['root_identity']
            require(identity(os.fstat(self.fd)) == self.root_identity
                and self.root_identity['st_dev'] == os.fstat(anchor.fd).st_dev
                and stat.S_IMODE(os.fstat(self.fd).st_mode) == 0o700, 'source_root_CAS_or_device')
            # One checked inode/byte state: no split read/hash acceptance.
            inventory_row = file_state(branch['inventory']['path'], bound=MAX_JSON, data=True)
            require(inventory_row['sha256'] == branch['inventory']['sha256'], 'inventory_sha256')
            self.inventory = decode(inventory_row['data'])
            require(self.inventory['entries']['.']['identity'] == branch['root_full_identity'], 'inventory_root_pin')
            self.prove_source()
            same_tree(held_tree(self.fd, tick=tick), self.inventory)
            self.prove_source()
        except BaseException:
            self.chain.close()
            raise

    @property
    def fd(self):
        return self.chain.fd

    @property
    def parent_fd(self):
        return self.chain.fds[-2]

    @property
    def name(self):
        return PurePosixPath(self.branch['source']).name

    def prove_source(self):
        self.chain.prove()
        require(identity(os.fstat(self.fd)) == self.root_identity, 'source_root_replaced')

    def prove_published(self, anchor):
        anchor.prove()
        prove_edges(self.chain.edges[:-1])
        require(identity(os.fstat(self.fd)) == self.root_identity == identity(
            os.stat(self.branch['target_name'], dir_fd=anchor.fd, follow_symlinks=False)), 'published_root_named_edge_changed')
        absent_at(self.parent_fd, self.name)

    def close(self):
        self.chain.close()


def holds_for(request, budget=None):
    tick = budget.check if budget else (lambda: None)
    anchor = Chain(request['anchor']['path'])
    holds = []
    try:
        require(identity(os.fstat(anchor.fd)) == request['anchor']['identity']
            and os.fstat(anchor.fd).st_uid == os.getuid()
            and stat.S_IMODE(os.fstat(anchor.fd).st_mode) == 0o700, 'anchor_CAS')
        guard_state(request)
        journal = PurePosixPath(request['journal'])
        with Chain(str(journal.parent)) as parent:
            absent_at(parent.fd, journal.name)
        for branch in request['branches']:
            tick()
            require(not branch['source'].startswith(request['anchor']['path'] + '/'), 'source_inside_canonical_anchor')
            absent_at(anchor.fd, branch['target_name'])
            holds.append(BranchHold(branch, anchor, tick))
        require(len({(h.root_identity['st_dev'], h.root_identity['st_ino']) for h in holds}) == 3,
            'source_root_alias')
        return anchor, holds
    except BaseException:
        for hold in holds:
            hold.close()
        anchor.close()
        raise


def preflight(request):
    anchor, holds = holds_for(request)
    try:
        return {'state': 'PREFLIGHT_PREEXISTING_BRANCHES_ONLY_NO_EFFECT_NO_AUTHORITY',
            'branch_counts': [h.inventory['count'] for h in holds], 'DSH_ready': False}
    finally:
        for hold in holds:
            hold.close()
        anchor.close()


def execute(request, request_sha):
    budget = Budget(request['budget_seconds'])
    anchor, holds = holds_for(request, budget)
    journal = None
    published = []
    pending = False
    any_attempted = False
    try:
        budget.check()
        journal = Journal(request['journal'], request_sha, budget)
        for index, hold in enumerate(holds):
            budget.check()
            guard_state(request)
            anchor.prove()
            for prior in holds[:index]:
                prior.prove_published(anchor)
            for future in holds[index:]:
                future.prove_source()
            same_tree(held_tree(hold.fd, tick=budget.check), hold.inventory)
            hold.prove_source()
            anchor.prove()
            absent_at(anchor.fd, hold.branch['target_name'])
            pending = True
            any_attempted = True
            journal.write('BRANCH_PUBLICATION_PENDING', index=index, source=hold.branch['source'],
                target=request['anchor']['path'] + '/' + hold.branch['target_name'],
                identity=hold.root_identity, inventory=hold.branch['inventory'])
            # After journal fsync re-prove the retained names before the single native syscall.
            hold.prove_source()
            anchor.prove()
            rename_noreplace(hold.parent_fd, hold.name, anchor.fd, hold.branch['target_name'])
            os.fsync(hold.fd)
            os.fsync(hold.parent_fd)
            os.fsync(anchor.fd)
            hold.prove_published(anchor)
            # Postwalk uses exactly the fd held BEFORE rename. Name is proved on both sides.
            same_tree(held_tree(hold.fd, tick=budget.check), hold.inventory, moved=True)
            hold.prove_published(anchor)
            receipt = {'source_consumed': hold.branch['source'],
                'canonical': request['anchor']['path'] + '/' + hold.branch['target_name'],
                'physical_root_identity': hold.root_identity, 'inventory': hold.branch['inventory']}
            published.append(receipt)
            journal.write('BRANCH_DURABLE_VERIFIED_SOURCE_CONSUMED', index=index, **receipt)
            hold.prove_published(anchor)
            pending = False
        budget.check()
        guard_state(request)
        # Final full inventories+held/named roots: no same-bytes replacement can be logged as ours.
        for hold in holds:
            hold.prove_published(anchor)
            same_tree(held_tree(hold.fd, tick=budget.check), hold.inventory, moved=True)
            hold.prove_published(anchor)
        budget.check()
        journal.write('EXACT_BRANCHES_RESTORED_ONLY', consumed_source_to_canonical=published)
        for hold in holds:
            hold.prove_published(anchor)
        return {'state': 'EXACT_BRANCHES_RESTORED_ONLY', 'consumed_source_to_canonical': published,
            'DSH_ready': False}
    except BaseException as exc:
        if journal is not None:
            try:
                journal.write('UNKNOWN_RECONCILE_REQUIRED' if pending or any_attempted else 'PARTIAL_KNOWN_STOPPED',
                    exception_class=type(exc).__name__, verified_source_to_canonical=published,
                    reason=exc.args[0] if isinstance(exc, Refused) else 'filesystem_or_runtime_error')
            except BaseException:
                pass
        raise
    finally:
        if journal is not None:
            journal.close()
        for hold in holds:
            hold.close()
        anchor.close()


def observe_root(path, branch, moved):
    """Read-only: never recurse into a same-bytes foreign replacement root."""
    path = PurePosixPath(path)
    root_seen = False
    try:
        with Chain(str(path.parent)) as parent:
            info = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
            root_seen = True
            if identity(info) != branch['root_identity']:
                return {'state': 'FOREIGN_OR_REPLACED_ROOT_NOT_ADOPTED', 'identity': identity(info, True)}
            fd = os.open(path.name, FLAGS | os.O_DIRECTORY, dir_fd=parent.fd)
            try:
                require(identity(os.fstat(fd)) == branch['root_identity'], 'observed_open_race')
                inventory = file_state(branch['inventory']['path'], bound=MAX_JSON, data=True)
                require(inventory['sha256'] == branch['inventory']['sha256'], 'inventory_sha256')
                same_tree(held_tree(fd), decode(inventory['data']), moved=moved)
                require(identity(os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False))
                    == identity(os.fstat(fd)) == branch['root_identity'], 'observed_named_root_changed')
                parent.prove()
                return {'state': 'EXACT_KNOWN_ROOT_AND_TREE', 'identity': identity(os.fstat(fd), True)}
            finally:
                os.close(fd)
    except FileNotFoundError:
        return {'state': 'UNRESOLVED', 'reason': 'known_root_or_validation_input_disappeared'} \
            if root_seen else {'state': 'ABSENT'}
    except Refused as exc:
        return {'state': 'UNRESOLVED', 'reason': str(exc)}


def reconcile(request):
    rows = []
    for branch in request['branches']:
        canonical = request['anchor']['path'] + '/' + branch['target_name']
        rows.append({'source': branch['source'], 'canonical': canonical,
            'source_observation': observe_root(branch['source'], branch, False),
            'canonical_observation': observe_root(canonical, branch, True)})
    try:
        journal = file_state(request['journal'], bound=MAX_JSON, data=True)
        events = []
        for line in journal.pop('data').splitlines():
            try:
                events.append(decode(line))
            except (ValueError, Refused):
                journal['truncated_or_invalid_tail'] = True
                break
        journal['events'] = events
    except FileNotFoundError:
        journal = {'state': 'ABSENT'}
    return {'state': 'READ_ONLY_CONSUMPTION_RECONCILIATION_NO_RETRY_AUTHORITY', 'branches': rows,
        'journal': journal, 'retry_permitted': False, 'DSH_ready': False}


def main():
    require(len(sys.argv) == 4 and sys.argv[1] in ('preflight', 'execute', 'reconcile'), 'usage')
    for key in ('HOME', 'TMPDIR', 'XDG_CACHE_HOME'):
        value = os.environ.get(key)
        require(value, 'private_environment_required')
        with Chain(value) as chain:
            info = os.fstat(chain.fd)
            require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'private_environment_required')
    import resource
    for limit, wanted in ((resource.RLIMIT_CPU, 240), (resource.RLIMIT_AS, 1024**3),
                          (resource.RLIMIT_NOFILE, 1024), (resource.RLIMIT_CORE, 0)):
        _, hard = resource.getrlimit(limit)
        value = wanted if hard == resource.RLIM_INFINITY else min(wanted, hard)
        resource.setrlimit(limit, (value, value))
    request = load_request(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'execute':
        import signal
        seconds = request['budget_seconds']
        require(type(seconds) is int and 120 <= seconds <= 240, 'bounded_future_budget_required')
        def expired(signum, frame):
            raise TimeoutError('finite_branch_publication_wall_deadline_consumed')
        signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            result = execute(request, sys.argv[3])
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    elif sys.argv[1] == 'preflight':
        result = preflight(request)
    else:
        result = reconcile(request)
    print(encoded(result).decode(), end='')


if __name__ == '__main__':
    main()
