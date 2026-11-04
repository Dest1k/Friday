# Source152 native engineering and recovery update

Source152 is installed, and Gateway and Dashboard service readiness was verified. User and semantic acceptance for this update remain pending. The [19-file native patch](source152-after151.patch) extends the installed Source151 native tree; it is not the complete installed artifact or a patch directly against upstream Hermes.

The patch joins structured tool-schema guidance, bounded context and replay preservation, explicit source-backed text edits, bounded presentation template reuse, scoped ZIP handling, and safe persistence recovery. When a rejected mixed tool batch contains restricted names, recovery keeps the original private evidence, removes only its exact adjacent unpersisted error rows from the public continuation, and preserves prior uncertain effects and unrelated history. A genuine database failure remains a persistence failure.

The final native bytes passed 63 isolated local regressions. These include real temporary-workspace file read/write and SQLite persistence/recovery, synthetic privacy/effect controls, and negative tests for restricted paths, mixed-batch errors, prior uncertainty and actual database failure. The earlier failed harness run and independent V2 privacy failure remain recorded separately in [observations](OBSERVATIONS.json); the later PASS does not rewrite them. Local tests do not establish Telegram behavior or semantic acceptance.

The native upstream commit is `781334eea4b9225a3e194faf0c241d9afe218634`. [NATIVE-FILES.json](NATIVE-FILES.json) records the exact Source151 preimages, final bytes, modes and receipt digests. Source152 uses the installed native generation `3409f529a478444eaba0ff4da95bf1c9`. Its complete installation also retains a private A0 composition bridge binding; that binding and private installation machinery are not portable public source and are excluded here. The native patch must not be presented as the whole installed A0 artifact.

Gateway initially failed to start within the existing 90-second systemd limit. The separate [systemd drop-in](gateway-startup180.conf) sets `TimeoutStartSec=180s`; the base unit was unchanged and the next start reached readiness in 105.372 seconds. This persistent service configuration is separate from the 19 native files and is not a semantic PASS. A local read-only source-guard profile likewise is not a new product source correction.

To reproduce the published regressions, use a disposable complete Source151 native tree with its existing dependencies, apply `source152-after151.patch` with `patch -p1`, then run from this directory:

```sh
python tests/isolated_pytest.py --source /path/to/disposable-source152 --work /path/to/new-test-work tests/test_privacy_effect_semantics.py tests/test_scoped_file_persistence_recovery.py --tb=short
```

Use the interpreter for that tree's already-installed test dependencies; the launcher does not install packages. It verifies all 19 final file hashes, gives tests fresh temporary state, blocks network and child processes, and replaces baseline accounting only within the test process. Its assertions use synthetic inputs. It never opens the live coordinator. This trusted local audit fence is not a hostile-process sandbox. No credentials, user inputs, raw histories, private handoff paths or session records are included.
