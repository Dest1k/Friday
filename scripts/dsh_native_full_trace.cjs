// Observational fixture trace only. File/process enforcement belongs to bubblewrap/systemd.
'use strict';
const fs = require('node:fs');
const original = globalThis.fetch;
const log = row => fs.appendFileSync('/job-home/native-http.jsonl', JSON.stringify({at:new Date().toISOString(),...row})+'\n',{mode:0o600});
globalThis.fetch = async function(input, options) {
  const url = typeof input === 'string' ? input : input.url || String(input);
  let body;
  try { body=JSON.parse(options?.body || '{}'); } catch {}
  log({type:'request',url,method:options?.method || 'GET',model:body?.model,
       max_tokens:body?.max_tokens,max_completion_tokens:body?.max_completion_tokens,
       stream:body?.stream,message_count:body?.messages?.length,tool_count:body?.tools?.length});
  try {
    const response = await original.apply(this,arguments);
    log({type:'response',url,status:response.status});
    // Clone observes the actual stream; never replace returned content or record auth/prompts/thinking.
    void (async () => {
      const reader=response.clone().body?.getReader();
      if (!reader) return;
      let pending='', bytes=0;
      const decoder=new TextDecoder();
      try {
        while(true) {
          const {done,value}=await reader.read(); if(done)break;
          bytes+=value.byteLength; if(bytes>4000000){await reader.cancel();break;}
          pending+=decoder.decode(value,{stream:true});
          const lines=pending.split('\n'); pending=lines.pop();
          for(const line of lines) {
            if(!line.startsWith('data: '))continue;
            try {
              const v=JSON.parse(line.slice(6));
              if(v.usage)log({type:'usage',url,usage:v.usage});
              for(const choice of v.choices || []) if(choice.finish_reason)log({type:'finish',url,reason:choice.finish_reason});
            } catch {}
          }
        }
      } catch {log({type:'trace_stream_interrupted',url});}
    })();
    return response;
  } catch(error) {log({type:'request_error',url,error_class:error.name});throw error;}
};
