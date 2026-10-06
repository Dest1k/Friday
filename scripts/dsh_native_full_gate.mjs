// Finite public native-provider acceptance. No test hooks, probe overrides or policy changes.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { spawnSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import assert from 'node:assert/strict';

const [donor, kind] = process.argv.slice(2);
const require = createRequire(donor + '/packages/sandbox/sandbox-local/package.json');
const { Context } = await import(pathToFileURL(require.resolve('@deepseek-ai/cordis')));
const { LocalSandboxProvider } = await import(pathToFileURL(donor + '/packages/sandbox/sandbox-local/lib/index.js'));
const ctx = new Context();
await ctx.plugin(LocalSandboxProvider, {});
const sandbox = ctx.sandbox;
assert.equal(sandbox.runnerCommand, undefined);
assert.deepEqual(sandbox.internals, {});
const report = { kind, automatic: true, controls: [] };
const policy = { mode: 'workspace-write', workspaceRoot: '/workspace' };
async function confined(code, mode = 'workspace-write') {
  const wrapped = await sandbox.confine(['/usr/bin/python3', '-I', '-c', code], { ...policy, mode });
  assert.equal(wrapped.enforcement, 'full', 'Partial confinement cannot authorize model effects');
  report.controls.push({ mode, ...wrapped });
  return wrapped;
}
function execute(wrapped) {
  const r = spawnSync(wrapped.argv[0], wrapped.argv.slice(1), { encoding: 'utf8', timeout: 10000 });
  report.controls.at(-1).result = { status: r.status, signal: r.signal, stdout: r.stdout, stderr: r.stderr };
  assert.equal(r.error, undefined);
  return r;
}
try {
  if (kind === 'enforcement') {
    // The outer boundary deliberately permits these canary writes: only INNER policy denies them.
    fs.writeFileSync('/job-home/outside-canary', 'unchanged\n');
    fs.writeFileSync('/job-home/outer-positive', 'outer-writable\n');
    fs.symlinkSync('/job-home/outside-canary', '/workspace/outside-link');
    const positive = execute(await confined("from pathlib import Path; p=Path('/workspace/allowed'); p.write_text('owned'); assert p.read_text()=='owned'; p.rename('/workspace/renamed'); Path('/workspace/renamed').unlink(); print('WORKSPACE_PASS')"));
    assert.equal(positive.status, 0); assert.match(positive.stdout, /WORKSPACE_PASS/);
    for (const [label, target, mode] of [
      ['outside-create', '/job-home/native-denied', 'workspace-write'],
      ['outside-modify', '/job-home/outside-canary', 'workspace-write'],
      ['symlink', '/workspace/outside-link', 'workspace-write'],
      ['readonly-workspace', '/workspace/readonly-denied', 'read-only'],
      ['readonly-tmp', '/tmp/readonly-denied', 'read-only'],
      ['readonly-input', '/job-input/readonly-canary', 'workspace-write'],
    ]) {
      const r = execute(await confined(`open(${JSON.stringify(target)}, 'w').write('forbidden')`, mode));
      report.controls.at(-1).label = label;
      assert.notEqual(r.status, 0); assert.match(r.stderr, /Permission denied|Read-only file system/);
    }
    const inherited = execute(await confined("import subprocess; r=subprocess.run(['/usr/bin/python3','-I','-c',\"open('/job-home/descendant-denied','w').write('forbidden')\"],capture_output=True,text=True); assert r.returncode!=0 and 'Permission denied' in r.stderr; print('INHERIT_PASS')"));
    assert.equal(inherited.status, 0); assert.match(inherited.stdout, /INHERIT_PASS/);
    for (const p of ['/job-home/native-denied', '/job-home/descendant-denied', '/workspace/readonly-denied', '/tmp/readonly-denied']) assert.equal(fs.existsSync(p), false);
    assert.equal(fs.readFileSync('/job-home/outside-canary', 'utf8'), 'unchanged\n');
    assert.equal(fs.readFileSync('/job-input/readonly-canary', 'utf8'), 'owned readonly negative control\n');
    report.status = 'PASS_FULL_AUTOMATIC_ENFORCEMENT';
    console.log(JSON.stringify(report));
  } else {
    assert.ok(['deadline', 'stop'].includes(kind));
    const wrapped = await confined("import os,time; from pathlib import Path; Path('/workspace/ready').write_text('NATIVE_FULL'); pid=os.fork();\nif pid==0:\n os.setsid()\n if os.fork(): os._exit(0)\n while True:\n  with open('/workspace/descendant-ticks','a') as f: f.write('tick\\n')\n  time.sleep(.1)\nwhile True: time.sleep(1)");
    report.status = 'STARTING_NATIVE_FULL_DESCENDANTS';
    console.log(JSON.stringify(report));
    const p = spawn(wrapped.argv[0], wrapped.argv.slice(1), { stdio: 'inherit' });
    await new Promise((resolve, reject) => { p.once('error', reject); p.once('exit', (code, signal) => resolve({code, signal})); });
  }
} finally {
  await ctx.fiber.dispose();
}
