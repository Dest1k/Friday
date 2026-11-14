# Scoped Calc profile source regressions

This small offline bundle tests the changed formula, rich digest, reference and refusal boundaries using the two original public XLSX inputs and clearly labelled bounded synthetic vectors. It does not create Office output or qualify a real conversion. Previously retained real-output qualifications remain separate private evidence; these checks do not recreate that evidence or its credit.

Use Python 3.10 or newer with the standard library. Supply all three roots explicitly:

```sh
python3 -I -B check_calc_profile.py \
  --native-root "$NATIVE_ROOT" \
  --public-evidence "$PUBLIC_EVIDENCE" \
  --work-root "$OWNED_WORK_ROOT"
```

`NATIVE_ROOT` must contain the selected final isolated native sources, including `tools/scoped_spreadsheet_conversion.py`, `tools/scoped_spreadsheet_rich.py`, their real pure dependencies, `tools/file_tools.py`, and `hermes_cli/friday_workspace_presentation.py`. Every imported parser module must originate inside that root. The runner supplies only a package namespace to locate those real modules; it does not execute the full runtime package initializer, import `file_tools`, or substitute parser primitives. The emitted report records module paths relative to the supplied root and their SHA-256 hashes. Native source preparation is separate from this bundle.

`PUBLIC_EVIDENCE` must contain these exact original public fixtures:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| S-01-orders_base.xlsx | 5660 | 714bdf80668250af362d607f24c5bf4c054f35094215f005b3631f90a67e7dd1 |
| S-11-orders_complex_features.xlsx | 8926 | f805315c82d40bb220b52dbe709063c2dbfc08b5c5a746bf0daae0916c9c9497 |

`OWNED_WORK_ROOT` must be a new path with an existing parent, or an empty directory owned by the current user with mode `0700`, outside the input/source roots. Existing nonempty roots and path links are refused. No default source, fixture or work paths exist. Bounded mutated XLSX files are explicitly named synthetic, confined to this directory and removed after their checks. Only `CHECKS.json`, mode `0600`, remains. Preserve that report as execution evidence; use a different empty work root for a justified rerun.

Checks cover public source parsing; independent formula recomputation from the parsed public inputs without oracle totals; preservation of absent source caches; rejection of stale caches, unknown attributes/formulas and active formulas; typed rich digest sensitivity and unsupported atoms; reference bounds and table bindings; formula namespaces; and bounded original XML refusal. Same-source fidelity metadata checks do not imply cross-format fidelity.

The opaque metadata transport check compiles only the unchanged pure AST branches that merge extra facts into a successful publication JSON response and return scoped JSON unchanged in `write_file_tool`. Its payload is visibly synthetic and includes nested extension fields. All effectful statements are omitted. It exercises neither a producer nor runtime adapters, source custody, CAS, file creation, delivery, registry dispatch or App acceptance.

The report and stdout omit spreadsheet values, formulas, captions and oracle totals. Inputs and imported source hashes are checked again at the end. No private fixture is required. No Office, model, provider, network, service or publication calls are made. This is a focused source regression bundle, not a universal Office suite, installation check or runtime acceptance.
