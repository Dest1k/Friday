{
 "schema": "friday.v3.segment-record.v1",
 "at_moscow": "2026-11-08T14:45:00+03:00",
 "segment": "Safe checkpoint: A0 qualification reconciliation path analysed; no new live effects; goal paused for a DSH restart",
 "lead": "DSH session (sole lead/integrator)",
 "state_at_checkpoint": {
  "goal": "FRIDAY-RELEASE-V3 active (phase resumed for this segment); paused by owner request after this checkpoint",
  "repository": {
   "HEAD": "819ee94 checkpoint: operator session authorized; product onboarding path executed for the Jarvis area",
   "pushed": "819ee94 is on origin/main (git push succeeded: d323e2b..819ee94)",
   "working_tree": "only the pre-existing unrelated changes remain unstaged: docs/foundation-status.md (modified) and docs/checkpoints/2026-11-07-v2-bounded-diagnostics/PROVIDER-SWITCH-TECHNICAL-NOTE-2026-11-07.md (untracked); both were preserved and never included in a commit",
   "checkpoint_checksums": "docs/checkpoints/2026-11-07-v3-original-context-repair/SHA256SUMS: 87 entries, sha256sum -c reports 87 OK"
  },
  "installed_runtime": {
   "home": "/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108",
   "config_sha256": "8c01e5c245508eff0c502806fbe47d332b89ae8c2ba0380318d03b058369ba92 (changed by the product's own onboarding transaction: user_isolation binding, account runtime_profiles, admin.profiles, gateway.profile_routes)",
   "plugin_tree": "digest-pinned file set matches FRIDAY-INSTALL.json plugin_files exactly (51 files); the stray __pycache__ that broke the source-identity proof was removed",
   "friday_install": "state INSTALLED_TEMPLATE_INCOMPLETE, worker_state BOTH_DEPLOYMENTS_QUALIFIED, runtime_ready false"
  },
  "services": {
   "gateway": "hermes-gateway-1e9db5b2.service active, MainPID 1353928, start_time 15149770, NRestarts 0, telegram connected, active_agents 0, served_profiles ['default', 'telegram-bot-8812646969']",
   "second_receiver": "none - exactly one gateway process and one dashboard process; the old unit hermes-gateway-1b7e7667 stays inactive",
   "dashboard": "pid 1358387, listening 192.168.12.128:9119 (TLS), /api/health 200, /login 200, /api/auth/me 401 without a session"
  },
  "user_areas": {
   "jarvis": {
    "runtime_profile": "telegram-bot-8812646969",
    "principal": "b21d67fc1b4ccce97241421bf86e3bc7416064133f7afd0822e6734ac6d5eef5 (8812646969)",
    "binding_sha256": "cbf7f45a811951c5198620e98817f36c525211a961237123989a477133c8b5f1 (equal to the reviewed binding of the preserved old home)",
    "home": "profiles/telegram-bot-8812646969 exists with .friday-onboarding.json (authorization_home = the new root, template friday-local, directory_identity [2050, 21852621]), profile config.yaml, SOUL.md, .env with the four required secrets, workspace/memories/skills/cron",
    "product_access_row": "tombstone: enabled=false, role=user, generation 1",
    "scope_marker": "NOT published - the product only publishes it in activate(), which was not reached",
    "consequence": "the area is prepared but disabled; the live gateway still serves only the default profile for product admission, so no user traffic is admitted into an unfinished area"
   },
   "owner_area": "not started - 467035772 -> dest_telegram will follow the same product path after the Jarvis area is settled",
   "isolation": "user_isolation binding for 8812646969 is committed by the product in the root config; the second binding for 467035772 is not yet present"
  },
  "preserved_data": {
   "quarantine": "preparation/user-area-restore-attempt-20261108T1210/ (43M; MANIFEST.json sha256 133a3cfae97cbbaaf09f42a31b66fd4414d2e96fdf63ac52bfcffd2f42f3d19c) - the withdrawn legacy attempt, moved not deleted",
   "old_home": ".runtime/friday-normal-both-workers-frw032 untouched: both bindings, both onboarding receipts and markers, access rows (generation 2 and 1), pairing approvals",
   "secrets": "never printed, logged, committed or written into project materials"
  },
  "tester": {
   "records": 444,
   "jarvis-restore-smoke-01-r43": "EVIDENCE_READY / send_state sent / send_attempts 1 / seen [] / message_ids [] - a known effect, recorded and not repeated",
   "r42": "untouched negative result",
   "unknown_send": "2 records still preserved as unknown effects",
   "admission": "R43 is bound to the dead gateway pid 1346033 / start_time 15052070 and is therefore fail-closed; a fresh admission must be issued against the then-current gateway pid/start_time before any live send"
  }
 },
 "analysis_of_the_a0_blocker_and_the_products_own_recovery_path": {
  "symptom": "Onboarding.qualify_workers stopped at a0_probe_cleanup with friday_rework.runtime_process.StopUnconfirmed('A0 initial probe exact owner cleanup unconfirmed'); workers/qualification/failure.json records state STOP_UNCONFIRMED, qualification_stage a0_probe_cleanup, retry_authorized false",
  "established_facts": [
   "the A0 container 3488cb15... was created and then stopped (docker config.v2.json State Running=false, Pid=0, ExitCode=0)",
   "the native stop receipt .runtime/a0-runtime-sol/1aa21b1f.../stop.json says STOP_CONFIRMED with current_sampling OBSERVED_OR_ALREADY_EXITED and 27 descendant_checks all confirmed",
   "all nine sampled processes are gone and the container cgroup scope no longer exists",
   "friday-rework-docker.service is inactive (dead) with an empty InvocationID, and unix:///run/user/1000/friday-rework-docker/docker.sock no longer exists",
   "the route bridge br-frwa0local does not exist; the launcher request file and route guard were removed by the recorded stop route",
   "the profile-scoped A0 keys are still PREPARED (the product removes them only on a fully confirmed stop)",
   "the retirement receipt .runtime/a0-runtime-sol/1aa21b1f.../retirement.json was never written"
  ],
  "root_cause": "retire_initial_probe() in worker-runtime-source/scripts/a0_runtime.py performs `docker rm` through the live rootless daemon socket. The daemon had already been stopped and unloaded by the recorded stop route, so the retirement ACK was unobtainable. The product therefore refused to declare the cleanup settled instead of recording a false success - which is correct behaviour, not a defect.",
  "comparison": "the earlier root-level composition (workers/a0, 09:11 MSK) reached the same stop state but its sol dir e67597f0.../retirement.json exists with INITIAL_PROBE_RETIRED: there the daemon was still reachable at retirement time",
  "products_recovery_path": "Onboarding.archive_workers() with a signed worker-archive request (plugins/friday_rework/worker_archive.py) consumes one exact stale stopped setup, renames workers/ into worker-setup-archive/transactions/<tree_key>/workers and writes a permanent CONSUMED_NO_RETRY claim, so a fresh qualification can proceed without replaying the old attempt",
  "archive_request_requirements_found": [
   "document schema friday.worker-stale-archive.v1, intent ARCHIVE_STALE_WORKER_SETUP_NO_RETRY, exact home/profile/binding_sha256/generation, a complete tree manifest of the profile's workers/ directory, and pinned refs for original_failure, closed_custody, original_clock, native_cessation, native_unit",
   "the closed-custody document must state the exact-current-normal-diagnostic-closure.v1 shape with the original attempt, the original 420 s physical deadline preserved, one qualification POST, no retry, A0 not started from the diagnostic's point of view and no worker runtime",
   "the provenance check requires the profile-scoped failure document to carry the recorded attempt (the current failure.json has state STOP_UNCONFIRMED and error_kind stop_unconfirmed, while the archiver expects state REFUSED_OR_UNCERTAIN with error_kind internal_error) - so the archive request for THIS attempt needs the product's own closed-attempt closure documents, which the current failed qualification did not produce",
   "the native guard additionally requires the gateway to be stopped and unclaimed, the workers tree to be free of live artefacts (qualification/, a0/bootstrap, a0/probe-plan.json, a0/runtime-receipt.json, dsh/runtime-receipt.json, the launcher request file, rootlesskit child_pid and route-guard.json) and the own dsh-safety scope to be terminal",
   "the profile currently holds workers/qualification, workers/a0/bootstrap and workers/a0/probe-plan.json, i.e. the live-artefact set the guard refuses, and the gateway host lock is currently held by the running gateway"
  ],
  "conclusion": "the archive transaction is the sanctioned way to consume this stale setup, but it cannot start while the gateway runs and while the failed attempt's own artefacts are still in place; the exact closed-attempt provenance documents for this attempt must also be produced by the product's own diagnostic closure, not by hand"
 },
 "next_steps_for_the_restarted_session": [
  "read this checkpoint and DSH-SEGMENT-2026-11-08-operator-onboarding.json first; re-verify live state before any write",
  "establish how the product produces the closed-attempt closure documents for a stopped qualification (friday.exact-current-normal-diagnostic-closure.v1 + ROOT-DIAGNOSTIC-CLOCK.json + ROOT-DIAGNOSTIC-RESULT.json) - the archiving route expects exactly those, and they must be generated by the product's diagnostic path, not synthesised",
  "perform a managed gateway stop at a safe boundary so the archive native guard can claim the host lock, then run Onboarding.archive_workers() for the stale Jarvis worker setup",
  "re-run prepare_workers/qualify_workers for the same principal and reach activate, which publishes the scope marker bound to the receipt sha256",
  "repeat for 467035772 -> dest_telegram, preserving the owner's conversation",
  "merge the preserved sessions/state.db/workspace/memories from the old home into the activated profiles",
  "issue a fresh targeted admission bound to the then-current gateway pid/start_time, run one controlled Jarvis turn check, then the new D-12 regression and the wrong-format / ordinary-write / out-of-scope live checks",
  "continue the V3 remainder: 170 cases, 120 format extensions through the live path, TIFF P-06 (P1), prescribed repeats, recovery verification, residual defects (friday_start.launch inside bwrap, dashboard non-loopback bind, TIFF ingress, write_file loop fix)"
 ],
 "explicitly_not_done": [
  "no live Telegram send in this segment",
  "no repeat of r42 or of any UNKNOWN_SEND record",
  "no deletion of profiles, quarantine contents or historical receipts",
  "no modification of installed product sources, of the model/weights/endpoint, of the owner's personal conversation, of the agreed cursor or of the single-receiver arrangement",
  "no password, cookie or token in chat, logs, commits or project files"
 ]
}
