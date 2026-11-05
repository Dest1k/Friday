"""Selected C25 preparation-cost source excerpts, for inspection only.

The named function/method text below is exact; this description, imports, class
container and comments separating excerpts are editorial. Dependencies, source
bindings, validators, authority, historical records and all effect implementations
are omitted. This is incomplete source context, not a dispatchable product or an
execution grant. No cache constructor is called and no entry point is supplied.
"""

import ast
import hashlib

# Exact helper-local immutable compilation reuse; no install or exec code included.
def _partial_node_compiler():
    # Cache compilation only, never custody/authority or consumer globals. Keep a
    # small helper-owned provenance tuple so a same-key cache replacement cannot
    # supply code. Code objects and the cached tuples themselves are immutable.
    cache={};owned=()
    def compiled(materialized,filename,need):
        nonlocal owned
        parser=ast.parse;compiler=compile
        dependencies=(parser,getattr(parser,'__code__',None),
                      compiler,getattr(compiler,'__code__',None))
        # Code equality omits location fields. Bind identities, retaining the
        # objects in each entry so an id cannot be recycled while cached.
        key=(materialized,filename,tuple(id(value)for value in dependencies))
        entry=cache.get(key)
        if entry is not None:
            need(any(value is entry and saved_key==key for saved_key,value in owned),
                 'V02_partial_compiled_cache_identity_changed')
            need(all(before is after for before,after in zip(entry[0],dependencies)),
                 'V02_partial_compiled_dependencies_changed')
            return entry[1]
        tree=parser(materialized)
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Runner')
        nodes=tuple((node.name,compiler(ast.Module(body=[node],type_ignores=[]),filename,'exec'))
            for node in cls.body if isinstance(node,ast.FunctionDef)and node.name in
            ('serial_predecessor','receive_inventory','verify_reply_custody'))
        need({name for name,code in nodes}=={'serial_predecessor','receive_inventory','verify_reply_custody'},
             'V02_exact_three_canonical_partial_nodes_required')
        if len(cache)>=4:cache.clear();owned=()
        entry=(dependencies,nodes)
        cache[key]=entry
        owned=tuple((saved_key,value)for saved_key,value in owned if saved_key!=key)+((key,entry),)
        return nodes
    return compiled


# Exact invocation-local AST reuse; caller-supplied trees are not accepted.
def _receive_evaluation_methods(source, observer):
    parsed={}
    def nodes(text):
        if text not in parsed:parsed[text]=ast.parse(text)
        tree=parsed[text]
        owners=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner']
        if len(owners)!=1:
            raise ValueError('receive_exact_runner_owner_required')
        values=[n for n in owners[0].body if isinstance(n,ast.FunctionDef)]
        if len({n.name for n in values})!=len(values):
            raise ValueError('receive_unique_method_names_required')
        return owners[0], {n.name:n for n in values}
    def pin(node):
        return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
    reviewed=observer.decode('utf-8')
    _, wanted=nodes(reviewed)
    for name, expected in RECEIVE_PREDECESSOR_AST.items():
        _, actual=nodes(source)
        if name not in wanted:
            raise ValueError('receive_required_method_missing_'+name)
        if name not in actual:
            if name=='inert_document_metadata_error':continue
            raise ValueError('receive_required_method_missing_'+name)
        if pin(actual[name])==pin(wanted[name]):
            continue
        if pin(actual[name]) not in expected:
            raise ValueError('receive_predecessor_method_changed_'+name)
        before=ast.get_source_segment(source,actual[name])
        if source.count(before)!=1:
            raise ValueError('receive_unique_method_source_required_'+name)
        source=source.replace(before,ast.get_source_segment(reviewed,wanted[name]),1)
    for name in RECEIVE_NEW_METHODS:
        owner,actual=nodes(source)
        if name not in wanted:
            raise ValueError('receive_reviewed_helper_missing_'+name)
        if name in actual:
            if pin(actual[name])!=pin(wanted[name]):
                raise ValueError('receive_helper_collision_'+name)
            continue
        lines=source.splitlines(keepends=True)
        lines.insert(owner.end_lineno,'\n    '+ast.get_source_segment(reviewed,wanted[name])+'\n')
        source=''.join(lines)
    return source


class Runner:
    # Exact decorated materialized TRANSFORMS[1][1] method only.
    # Every other Runner method and the decorator implementation are omitted.
    @engineering_snapshot_measured('successor')
    def engineering_successor_key(self,plan,key):
        """Follow only authenticated consumed no-run edges in this branch."""
        seen=set();grant=None
        while True:
            if key in seen:raise Refused('Consumed no-run successor cycle')
            seen.add(key)
            path=self.store.root/('continue-'+key+'.json')
            if not path.exists() or self.store.get(path).get('plan')==plan:
                # Current authority and the complete native inventory are fresh
                # at both ends of this synchronous walk. Nothing survives it.
                if grant is not None and self.engineering_regression_material(plan)!=grant:
                    raise Refused('Consumed no-run successor authority changed during walk')
                return key
            # Inline only the sealed-entry branch. The standalone method and
            # unsupported legacy path keep their original independent guards.
            inventory=self.engineering_closed_no_run_inventory()
            entries=[entry for entry in inventory.values()if entry['key']==key]
            if not entries:
                key=self.orphan_successor_key(plan,key)
                continue
            material=entries[0];old=material['plan']
            steps=plan.get('new_scenario',{}).get('steps',[])
            if (plan.get('predecessor')!=old.get('predecessor')
                    or plan.get('current_tuple')!=old.get('current_tuple')
                    or plan.get('new_task',{}).get('kind')!='ordinary-document-task'
                    or plan.get('new_task',{}).get('source_reference')is not None
                    or plan.get('new_run_id')==old['new_run_id']
                    or plan.get('action_id')==old['action_id']
                    or plan.get('new_task',{}).get('nonce')==old['new_task']['nonce']
                    or plan.get('clock')==old['clock'] or len(steps)!=1):
                raise Refused('Consumed no-run admission requires one distinct future ordinary effect')
            successor=digest(encoded(dict(consumed_admission=material['admission'],
                Root_operational_closure=material['closure_reference'],predecessor_key=key)))
            if orphan_public_effect(steps[0])==material['signature']:
                if not self.engineering_consumed_successor(plan,successor):
                    # One internally obtained complete grant, never supplied by
                    # a caller or retained in a mutable Runner authority slot.
                    if grant is None:grant=self.engineering_regression_material(plan)
                    if not(grant is not None and material['effect']['id']in grant['known']
                            and grant['known'][material['effect']['id']]['effect']['kind']=='no_run_admission'
                            and grant['known'][material['effect']['id']]['row']==material['row']
                            and any(x['effect']['kind']=='run'for x in grant['known'].values())):
                        raise Refused('Same-signature no-run successor requires fresh full regression authority')
            key=successor
