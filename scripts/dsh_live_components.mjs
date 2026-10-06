// Finite public native component execution, with real streaming and persistence.
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import fs from 'node:fs';
const [donor, sessionId, phase] = process.argv.slice(2);
assert(donor && sessionId && ['child','compact','inspect'].includes(phase));
const caseId=fs.readFileSync('/job-input/case-id.txt','utf8');
assert(/^[A-Za-z0-9_.-]+$/.test(caseId));
const requireDonor=createRequire(path.join(donor,'apps/cli/package.json'));
const load=name=>import(pathToFileURL(requireDonor.resolve(name)).href);
const boot=await import(pathToFileURL(path.join(donor,'apps/cli/lib/profile-boot.js')).href);
const launch=await load('@deepseek-ai/dsh-launch-environment');
const agentModule=await load('@deepseek-ai/dsh-agent');
const environment=launch.createLaunchEnvironmentSnapshot([{source:'process',values:{...process.env}}]);
const controller=new AbortController();
process.once('SIGTERM',()=>controller.abort(new Error('owned stop')));
process.once('SIGINT',()=>controller.abort(new Error('owned stop')));
let booted,handle,run;
const report={phase,sessionId,provider:'friday-local',model:'dispatcher',status:'FAIL'};
function collect(observation) {
  const events=Array.from(observation.events);
  return {header:observation.header,event_count:events.length,
    event_types:events.reduce((a,e)=>(a[e.type]=(a[e.type]||0)+1,a),{}),
    completed_turns:events.filter(e=>e.type==='turn/end').map(e=>({seq:e.seq,data:e.data})),
    requests:events.filter(e=>e.type==='request/header').map(e=>({seq:e.seq,config:e.data.header.config})),
    compactions:events.filter(e=>['compaction/start','compaction/summary','compaction/end'].includes(e.type)).map(e=>({seq:e.seq,type:e.type,data:e.data})),
    replacements:events.filter(e=>e.type==='user/message'&&e.surfaceOp?.op==='replace').map(e=>({seq:e.seq,data:e.data,surfaceOp:e.surfaceOp,sourceEventSeqs:e.sourceEventSeqs})),
    child_events:events.filter(e=>e.type.startsWith('subagent/')).map(e=>({seq:e.seq,type:e.type,data:e.data}))};
}
try {
  booted=await boot.runProfile({environment,profile:'headless',patchFiles:['/job-input/local.patch.yml','/job-input/held.patch.yml'],args:[]});
  const ctx=booted.ctx;
  let observation=await ctx.sessionQuery.observeSession(sessionId,{signal:controller.signal});
  try {
    assert.equal(observation.header.cwd,process.cwd());
    assert.equal(observation.header.parentSession,undefined);
    assert.notEqual(observation.header.origin,'subagent');
    assert.equal(observation.header.agentPreset,undefined);
    assert(!Array.from(observation.events).some(e=>e.type==='agent-preset/selected'));
    report.before=collect(observation);
  } finally {observation[Symbol.dispose]();}
  if(phase!=='inspect') {
    const selection=ctx.agentDefaultModel.currentSelection();
    assert.equal(selection.provider,'friday-local');assert.equal(selection.model,'dispatcher');
    handle=await ctx.agents.resume({resumeSessionId:sessionId,agentOptions:selection,
      setup:agentCtx=>{agentModule.installModelSelection(agentCtx,{current:selection,assembled:undefined});}});
    const parent=handle.agent;
    await parent.whenIdle();
    if(phase==='child') {
      run=await ctx.subagents.start('spawn',{parent,label:'finite local child',
        prompt:[{type:'text',text:'Return exactly FRW005_CHILD_OK. Do not use tools or delegate.'}],
        maxDepth:1,signal:controller.signal});
      const result=await run.result;
      report.child={result,sessionId:run.localAgent?.session.id};
      assert.equal(result.stopReason,'completed');
      assert.equal(result.output.filter(x=>x.type==='text').map(x=>x.text).join('').trim(),'FRW005_CHILD_OK');
      if(run.localAgent) {
        await ctx.sessions.flush(run.localAgent.session);
        const childObs=await ctx.sessionQuery.observeSession(run.localAgent.session.id,{signal:controller.signal});
        try{report.child.durable=collect(childObs);assert.equal(childObs.header.parentSession,sessionId);}
        finally{childObs[Symbol.dispose]();}
      }
      await run.dispose();run=undefined;
    } else {
      report.compaction=await ctx.compaction.compactNow(parent,controller.signal);
      assert(report.compaction,'Manual compaction was a no-op');
    }
    await ctx.sessions.flush(parent.session);
    await handle.dispose();handle=undefined;
  }
  observation=await ctx.sessionQuery.observeSession(sessionId,{signal:controller.signal});
  try{report.after=collect(observation);}finally{observation[Symbol.dispose]();}
  if(phase==='compact') {
    const summaries=report.after.compactions.filter(e=>e.type==='compaction/summary');
    assert(summaries.length>report.before.compactions.filter(e=>e.type==='compaction/summary').length);
    const summary=summaries.at(-1).data;
    assert.equal(summary.provider,'friday-local');assert.equal(summary.model,'dispatcher');
    assert.equal(summary.llmStreamCall,true);
    assert(report.after.replacements.length>report.before.replacements.length);
  }
  report.status='PASS';
} catch(error) {
  report.error={name:error.name,message:error.message,code:error.code};
} finally {
  if(run)try{await run.dispose();}catch{}
  if(handle)try{await handle.dispose();}catch{}
  fs.writeFileSync('/job-home/component-'+phase+'-'+caseId+'.json',JSON.stringify(report,null,2)+'\n',{mode:0o600,flag:'wx'});
  console.log(JSON.stringify({phase,status:report.status,sessionId,error:report.error}));
  if(booted)await booted.shutdown.shutdown(report.status==='PASS'?0:1);
}
process.exitCode=report.status==='PASS'?0:1;
