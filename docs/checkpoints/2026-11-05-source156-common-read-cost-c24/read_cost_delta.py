"""Exact C24 selected source excerpts, for inspection only.

This is incomplete source context, not a runnable tester or execution grant.
Only the named function/method text is extracted verbatim. The class containers
and this description are editorial. Required globals, validators, state setup,
sealed closure descriptors, source bindings and all other methods are omitted.
No entry point or example invocation is supplied. Timing below is observation
instrumentation; authority and effect clock implementations are not included.
"""

import time

# Exact helper function, including its existing observation instrumentation.
def closed_no_run_inventory(reader,c,runner):
    snapshot=getattr(reader,'_engineering_snapshot',None);started=time.perf_counter();cpu=time.process_time()
    try:
        if snapshot is not None:return snapshot.inventory(reader,c,runner)
        return _closed_no_run_inventory(reader,c,runner)
    finally:
        if snapshot is not None:
            stats=snapshot.stats;stats['inventory_calls']=stats.get('inventory_calls',0)+1
            stats['inventory_wall_seconds']=stats.get('inventory_wall_seconds',0)+time.perf_counter()-started
            stats['inventory_cpu_seconds']=stats.get('inventory_cpu_seconds',0)+time.process_time()-cpu


class InvocationSnapshot:
    # Exact methods; constructor, check(), bindings and state are omitted.
    def _consumer(self,reader,c,runner):
        # reader is a carrier made by bind(), its protected callbacks still
        # point to the originally bound reader and are checked above.
        need(self._identity(reader.read)==self._bound[3] and
            self._identity(reader.document)==self._bound[4] and c is self._bound[1]
            and str(runner.store.root)==self._bound[2]
            and self._identity(runner.store.run_path)==self._bound[-1],
            'snapshot_consumer_changed')

    def inventory(self,reader,c,runner):
        # A warm inventory contains only the already authenticated sealed
        # history entries. Check all tracked physical/executable identities at
        # both boundaries, without repeating the same check for every entry.
        # Current authority, cursor and actual native inventories remain on
        # their original fresh paths in _validate().
        self.check();self._consumer(reader,c,runner)
        pins=tuple(enc(ref(pin))for pin in CLOSED_NO_RUN_CLOSURES)
        if not all(pin in self._closed for pin in pins):
            result=_closed_no_run_inventory(reader,c,runner)
        else:
            entries={};keys=set()
            for pin in pins:
                entry=self._closed[pin];rid=entry['effect']['id']
                need(rid not in entries and entry['key']not in keys,'closed_no_run_unique_inventory')
                entries[rid]=entry;keys.add(entry['key'])
            result=self._copy(entries)
            self.stats['closed_hits']+=len(pins)
        self.check()
        return result


class Runner:
    # Exact materialized TRANSFORMS[14][1]; every other Runner method is omitted.
    def reject_consumed_orphan_effect(self, scenario, plan=None):
        matches=[]
        for entry in self.engineering_closed_no_run_inventory().values():
            for step in scenario.get('steps',[]):
                try:signature=orphan_public_effect(step)
                except Refused:continue
                if signature==entry['signature']:matches.append(entry)
        if not matches:return
        # One fresh complete grant for this synchronous guard invocation. The
        # remaining comparisons are pure reads of the already captured rows;
        # no grant/current result survives this call or another effect boundary.
        grant=self.engineering_regression_material(plan) if plan is not None else None
        for entry in matches:
            known=None if grant is None else grant['known'].get(entry['effect']['id'])
            if not(known is not None and known['effect']['kind']=='no_run_admission' and known['row']==entry['row']):
                raise Refused('Consumed no-run public effect requires fresh reconciled authority')

