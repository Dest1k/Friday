# Calc GPGME locale contract — SOURCE only

This archive contains the exact R2 [collector afterimage](source/gpgme_boundary_collector.py)
and the unaltered author [original-to-R2 patch](SOURCE15-TO-R2.patch). The exact
public beforeimage is the sibling [cached-postload collector](../calc-gpgme-cached-postload-source-20261116/source/gpgme_boundary_collector.py),
SHA-256 `0baf3f025669b8c56238d0f0fc9c8ffdd71bb9d17ea64641c74f3f3d83324e03`.
The final collector SHA-256 is
`0e72a8f821771ee365563fb45440eaeb4e6376f684e482463d3373c9873e66dd`.

For the exact pinned GnuPG helpers, finite branches and glibc initialization
contract, the shared predicate requires `LANG == LC_ALL == C.UTF-8`, permits
unchanged absent/empty/nonempty `LANGUAGE`, permits only absent/exact-empty
`LOCPATH`, and requires `GCONV_PATH` absent, including refusal of empty presence.
The same predicate now runs at full effective-parent freeze after structural
ENV and fifteen font-input joins, before final CAS/immutable tuple commit and
new GPGME helper effects. The full parent/helper ENV equality, exact fourteen
passive mappings, source/image/branch/UID/hash/CAS checks and resource/cancellation
rules remain required. No ENV rewriting or general key allowlist is added.

This relies on fixed fresh-helper initialization and pinned glibc's actual
C/C.* category gettext path. An ENV string does not observe actual `LC_MESSAGES`.
Other applications, changed helpers, explicit category switching, other gettext
implementations and unpinned inputs are outside the source proof. Package/source
and static ELF joins do not prove whole-binary reproducible source equivalence.

[Source status](SOURCE-STATUS.json), [dependencies and reconstruction](SOURCE-DEPENDENCIES.json),
[primary-source metadata](PRIMARY-SOURCE-METADATA.json), [provenance](PROVENANCE.json),
[copy allowlist](PUBLIC-COPY-ALLOWLIST.json), [manifest](PUBLIC-MANIFEST.json) and
[freeze](PUBLIC-FREEZE.json) bound this publication. Reconstruct only in an isolated
work directory using the explicit beforeimage argument described in the dependency
file; the original patch's absolute headers are provenance, not live destinations.

The completed eight-method R2 source controls and twenty-five branch/language
positive cases are reused; their GDB/current-process/ENV leaves were synthetic,
with real pinned ELF/passive backing files. Earlier unchanged R1 evidence is
reused separately. These are not newly rerun tests or summed unique counts.

Historical f59e remains consumed/closed after a real partial gpgconf effect;
its offending ENV selector and actual values were not captured, fix coverage is
unproved, and actual exact-fourteen success is not established. This source
archive grants no operation and claims no actual Office fix, M, installation,
ordinary 35/40 fit, full 170/120/B00 or semantic acceptance. Root independently
owns final exact composition and any future bounded qualifier. Private tests,
raw traces, ENV values, user files, plans/grants/receipts, upstream source bodies,
binaries, fonts and secrets are excluded; this is not a standalone runtime closure.
