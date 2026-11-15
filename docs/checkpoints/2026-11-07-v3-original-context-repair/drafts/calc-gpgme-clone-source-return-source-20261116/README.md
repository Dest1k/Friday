# Calc GPGME clone source-return protocol V2 — SOURCE only

This archive contains two exact reviewed Python afterimages and the unmodified
baseline-to-V2 patch. The adapter binds each invocation to an observed clone
entry/fork/birth and requires both exact pinned GPGME parent source-return
completions. Optional raw syscall observations retain their real metadata labels;
missing events, errno or children are never invented. Negative kernel returns
remain refusals. Native cleanup checks accepted descendants before parents while
preserving current birth/PPID checks, the first refusal and the strict conjunction
of kernel absence and debugger inferior retirement.

[Source status](SOURCE-STATUS.json), [dependencies and role mappings](SOURCE-DEPENDENCIES.json),
[provenance](PROVENANCE.json), [publication checks](PUBLICATION-CHECKS.json) and the
[public manifest](PUBLIC-MANIFEST.json) describe this bounded publication. Exact
source afterimages: [adapter](source/gpgme_engine_gdb.py) and
[native observer](source/native_return_observer.py).

Copy the exact named public beforeimages from the sibling
[cached-postload R3](../calc-gpgme-cached-postload-source-20261116/README.md) and
[eager-exit custody R2](../calc-gpgme-eager-exit-custody-source-20261116/README.md)
archives to their mapped role paths in an isolated directory. Apply the
[original patch](CLONE-RETURN-PROTOCOL.patch) with
`patch --fuzz=0 --batch --forward -p1`; require zero offsets and both exact final
hashes. Preserve the original context bytes. Collector and OwnC driver are
unchanged and referenced by exact public hashes. The remaining runtime graph
and external dependencies are unbundled; this is not a standalone executable.

The exact final V2 functional source review and Root source acceptance are reused.
Their explicit synthetic GDB/OS/helper/held-host leaves do not establish actual
kernel delivery, runtime progress, native cleanup or semantic acceptance. The
pinned GNU/glibc source does not prove an installed-kernel trap ordering theorem.
The old ff5 entry/errno/cleanup exception remains NOT_CAPTURED; its native cleanup
remains historically UNCONFIRMED. Old CPUUNKNOWN and consumed/UNKNOWN effects,
clocks, budgets and cleanup/stop obligations stay unchanged, without replay.

The [ordinary cached source archive](../calc-ordinary-cached-postload-source-20261116/README.md)
is a separate frozen branch and excludes these newer V2 adapter/native changes.
This publication performs no composition between the branches. At the pinned
source result cut no runtime admission or qualification is credited. Later Root
runtime outcomes are separate facts. No installed state, actual M, 35/40 fit,
ordinary/fullV3, user, semantic or formal acceptance follows from this archive.

Private references and hashes provide provenance only. Private index/manifests,
plans, grants, handoff/runtime/caller proof bodies, raw payloads, upstream/vendor
source, binaries, fonts, user documents and credentials are omitted.
