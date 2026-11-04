# DSH postboot policy ancestry repair

Source-only candidate for Source154. Source153 is currently installed; this patch has not yet passed installed or user acceptance.

The DSH validator now authenticates the retained intermediate policy transaction before a new current-boot successor. Exact source, native environment, owner, policy, network and publication checks remain enforced. The fourteen Source153 native fixes are retained unchanged.

Validation: independent delta review, exact AST comparison, the retained real policy history and negative rejection controls. Original failures remain recorded; local checks do not count as B00 PASS.

Apply `project-functional.patch` to the Source153 project file identified in `PROJECT-FILES.json`.
