# Frozen paper-helper guard source archive — 2026-11-15

**REVISION2 SOURCE + NON-OFFICE HELPER FIXTURE PASS · NOT-INSTALLED · NOT-OFFICE-ADMITTED · actual_M=null · fullV3 / full170/120/B00 OPEN**

This code archive preserves historical frozen candidate **M** and the separate **revision2** adapter correction accepted by Root's source delta check and non-Office enforcing fixture, against repository HEAD `86b947e4366c143b803efc5d78390c17c0978ca7`. The top-level `candidate/` remains byte-exact M; revision2 files are added under `revision2/`. It preserves M's Python code, fixed paper-helper algorithm manifest, source contract and intentionally invalid `OFFICE_UNADMITTED` config template, and `.py`/`.c` test sources. Candidate and test directories keep their original relative layout. `PUBLIC-MANIFEST.json` records each archived source byte count and SHA-256.

M consists of original source S, V's four-file reviewer correction, and fixture-metadata relocation only. The relocated prepared metadata is omitted. The two patches are byte-exact historical inputs: `changes.patch` is S's original source delta; `REVIEWER-FIX.patch` is V's later four-file correction. Their path bases differ. M's copied files are the assembled snapshot; the patches are provenance, not a standalone installer.

The Office helper manifest declares fixed code/ELF roles, offsets, image hashes, algorithm constants and expected environment/absence checks. It contains no runtime grant. The template has an invalid nonce and placeholder operation paths. Neither file authorizes execution.

## Known status at this archive boundary

- S reported 26 pure source tests passing. Root's actual enforcing helper fixture R1 then **REFUSED `helper_stdout_not_empty_EOF`**, despite a later helper-custody `CLOSED` snapshot. That refusal remains authoritative.
- V corrected the stop predicate to remain pure, queued each real stop once with context rechecks, and added a first-error latch. V reported 26 source tests plus nine reviewer controls passing. Root independently reviewed that correction and assembled M.
- Root's actual enforcing helper fixture R2 on frozen M **still REFUSED the same EOF condition**. Two actual same-PC EOF breakpoint stops were separated by dash exit and original-inferior selection. The first-error latch stopped progress. Exact call-ordering cause was not fully traced. Pure test results do not establish helper runtime success.
- Root reported all own PIDs/units/cgroups from these helper fixtures closed or retired. These were non-Office helper fixtures with `actual_M=null`; cleanup does not change either refusal into acceptance.
- Root's corrected legacy ABI-only R2 fixture on exact M native hook `d4425be4…` **PASS**: ten `126` values in the positive mode; seven negative modes, including raw64 `4294967422` narrowed to `126`, correctly refused. All own inferiors were absent and its own fixture binary was removed. This establishes only that separate legacy ABI fixture. The earlier `symbol_owner` refusal was Root's harness relocation error: its absolute RUNPATH required the actual original library reference. Only that harness reference was corrected. It was not diagnosed as a product regression.
- Revision2 gives return-site/helper-entry breakpoints a one-shot lifetime. Only a successful context/value observation retires the breakpoint, outside callbacks; libc popen ENTRY remains armed. A delivered retired event refuses. Root independently checked the exact 4085-byte delta. No generic EOF ignore or guard weakening was added; native hook, policy and Office manifest remain unchanged.
- Revision2 reported **14 pure controls PASS**. The unchanged 26-source-test result and eight actual legacy ABI modes were reused by exact unchanged source/hook identity; these were not rerun by the packager.
- Root's new actual enforcing non-Office helper fixture R3 on revision2 **PASS (`COMPLETE_HELPER_FIXTURE_ONLY`)**: null error, exit0, 0.340 seconds, empty EOF, pclose768 and both child exit3 observations. All six owned host PIDs were absent and the unit/cgroup retired. This is a new fixture result; R1/R2 refusals and closed effects remain preserved.

`revision2/REVISION2.patch` and `revision2/source/candidate/outer/deps/paper_helper_gdb.py` are byte-exact V2 patch/afterimage. The latter is the sole runtime-code change from M to Root's M2 assembly. `revision2/reviewer_checks.py` preserves the 14-control source. The path layout matches V2; unchanged sources remain in top-level M, so this is a review archive rather than a directly runnable V2 test tree. Root's actual evidence is separately selected for publication.

Root separately binds and admits any real Office plan/current operation. Revision2's source and non-Office fixture PASS do not admit Office, change installed224, produce actual M, establish historical/physical fidelity, or accept a user case/App/fullV3. No Office execution was performed here.

Source availability, source readiness, installation, helper runtime, legacy ABI fixture, Office observation, user-case semantics, App acceptance and formal acceptance remain separate facts. Installed224 is unchanged. This archive establishes none of actual M, historical producer equivalence, physical fidelity, or full170/120/B00 acceptance. Original R2/R3 user-effect boundaries, closed/consumed effects and clocks are preserved; no replay is authorized.

## Provenance pins

| Input | SHA-256 |
| --- | --- |
| `S_original_source_result_sha256` | `21a0fa5cae6049f1f73aaa4ed586ebac5a9abd5884f333128a9cde0b381b03fc` |
| `S_original_source_freeze_sha256` | `d6db99724198cafd50f8f79360c72acf1f32eb4037f3687769ab418a78217234` |
| `V_independent_review_result_sha256` | `236c3006affe26566aa796594a48916c08f716b18f1001dcec44ba7493e6f3ae` |
| `V_reviewer_fix_freeze_sha256` | `52fa9f103a843e613c019cabb72a7c75d54178853b493c55bb86f93355d95d9a` |
| `M_merged_source_result_sha256` | `97ed277d85dcc35e267dadc463d271b6288dfe45f60ff270dca292e602503321` |
| `M_merged_source_freeze_sha256` | `46ea49de464dd5b9336755248fc285608e1544d77b96bbbeea35eb0bd5dedc71` |
| `legacy_ABI_R2_root_result_sha256` | `61f6f94f1dc1a93207b4056a22332b02ebe176d03d5a63e471bfda23899ba481` |
| `V2_reviewer_result_sha256` | `f128c7a6cacf1057ad23771710dcd0fbb481ecc40db0447c5521106d594e9f05` |
| `V2_reviewer_freeze_sha256` | `eb4a8abcfb33bb2be716461a86b049ceeb1327138bc3e283e6bc75161ac422f4` |
| `M2_root_assembly_result_sha256` | `b0a293bbe96d1d8e4702215411dbf95d160f586b41a3acab97e39053163ea462` |
| `M2_root_assembly_freeze_sha256` | `7e5c2c8e3c475da44710a2d61fd8c395f68db7e61b4a5b6b0fa41dac2bffac43` |
| `helper_fixture_R3_root_result_sha256` | `bd73159e8fd96cfd61cdf1834dc00ab842306c2294c2b4bd165ad899f852ad35` |
| `initial_code_archive_result_sha256` | `a2f410f131187a9b2c4c00987c43ae85743b0b3b4e52511ba3819526a5d1462b` |
| `initial_code_archive_manifest_sha256` | `bfde85c6e40afd2fe4067353979d3733862d48b8165a999adecd0cf0b8b2271f` |

The original result/freeze documents and actual runtime evidence remain outside this code archive. The integrator publishes separately selected evidence and the current status; these source pins do not substitute for it.

## Deliberate omissions and limits

No beforeimages, large base trees, font baseline, namespace provenance, private R3 result, user data/documents, prepared fixture metadata, compiled binary, prepared plans, runtime bundle, grant, once-state, cache payload, logs or raw traces are included. The original standalone `verify_patch.py` and the earlier review harness are omitted because this code-only selection omits their private/base inputs. Only the separately frozen revision2 reviewer-check source is added; its private/base inputs remain omitted. Default source references remain unchanged; their referenced private files are not shipped.

**This is not a standalone installation or runnable test bundle.** Omitted base/private inputs are required by some consumers and tests. Do not weaken guards, substitute fixtures for actual observations, apply generic EOF idempotence, overwrite source, or replay closed effects to obtain a passing result. Any new revision needs its own exact-byte review and separately admitted runtime checks.

Packaging checks were limited to exact copied-byte comparison, JSON parsing, in-memory Python compilation and static publication screening. No archived code, tests, GDB, helper, Office/UNO, namespace, service, model or send was executed by the packager.
