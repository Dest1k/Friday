# Calc OwnC post-exit contract — SOURCE only

This archive contains one exact reviewed OwnC driver afterimage and its original
patch. The final readiness check now uses the observed normal exit, CLOSED
helper custody, exact closed phase and process absence. Active load, marker and
held checks still require the original live identity. First refusal, exact
native definitions, serializer and mandatory final cleanup remain unchanged.
No FileNotFoundError suppression or success allowlist is introduced.

[Source status](SOURCE-STATUS.json), [dependencies](SOURCE-DEPENDENCIES.json),
[provenance](PROVENANCE.json), [publication checks](PUBLICATION-CHECKS.json) and
the [public manifest](PUBLIC-MANIFEST.json) bound this publication. The sole
source copy is the [driver](source/ownc_gdb.py).

Copy the exact OwnC driver beforeimage referenced by the sibling
[clone source-return archive](../calc-gpgme-clone-source-return-source-20261116/SOURCE-DEPENDENCIES.json)
from [cached-postload](../calc-gpgme-cached-postload-source-20261116/source/ownc_gdb.py)
to `driver/ownc_gdb.py` in an isolated directory. Apply the unmodified
[patch](POSTEXIT-CONTRACT.patch) with `patch --fuzz=0 --batch --forward -p1`;
require zero offsets and the exact afterimage hash in the dependencies file.
Headers map source roles, never live destinations. The other named public
modules and the remaining runtime graph are unbundled; this is not a standalone
executable.

The exact functional Source review is reused. Its explicit synthetic exit/proc
leaves and four Source consumers qualify the correction only as Source. This
archive does not rerun those tests, start GDB or qualify actual execution of the
corrected driver.

Root separately accepted a new DERIVED positive semantic assessment on the
identical saved c400 artifact: the admitted harmless worker-cached OwnC helper
lifecycle, two held ENV projections, ten inert markers, observed restore/close
markers, normal native exit and recorded cleanup. No positive was replayed.
The original literal driver REFUSED/FileNotFoundError, GDB exit2, namespace
exit2 and Root monitor refusal remain unchanged. Those original success
attestations are false; derived semantic acceptance does not rewrite them.
The three separate runtime negative controls remained NOT_RUN at this snapshot;
no complete positive-plus-negatives battery acceptance follows.

INERT markers and ENV projections establish no Office/UNO/native64 measurement,
actual font restoration, canonical/effective font CAS, continuous ENV stability,
actual M, 35/40 fit, user-document, product, formal or fullV3 acceptance. Old
consumed/UNKNOWN effects, clocks and stop obligations remain preserved. This
publication asserts no installed state and grants no execution or replay authority.

Only bounded provenance references and hashes are included. Private plans,
full manifests/index/configuration/grants/receipts/handoffs, proof bodies, raw
traces/payloads, user content, credentials, upstream source copies, binaries and
fonts are omitted.
