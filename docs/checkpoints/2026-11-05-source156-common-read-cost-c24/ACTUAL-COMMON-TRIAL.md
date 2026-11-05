# Actual common trial and source-only observations

R23 preparation failed with `PreparationBudgetExpired` before native Run or send.
The 540-second preparation cutoff and original clocks were preserved. The parent
process exited with code 2 after 554.349 seconds, was reaped, and was not retried.
The admission was reconciled as consumed closed noRun; the once claim was absent,
with no send/receive witnesses. Reply and post-reply acceptance were not executed.
This is a tester preparation failure; the product result is `NOT_RUN`.

| R23 observed phase | Wall seconds |
| --- | ---: |
| Bridge preparation | 226.870 |
| History scope | 54.796 |
| Native continuation read-only | 102.782 |
| New cursor preparation | 77.031 |
| New material, interrupted before completion | 42.459 |

These are nested intervals and must not be added to infer overall elapsed time.
A separate read-only namespace measurement after R23 closure took 0.163 seconds
for 581 directories and 7,764 entries. It was not original R23 instrumentation,
does not attribute the original cutoff, and provides no functional credit. No
namespace optimization was selected.

C24 current-source and partial-source qualifiers passed in concurrent runs:
68.613 and 42.517 seconds respectively. Those durations describe source
qualification only; they do not measure common-trial preparation or product
performance. Final wiring review was pending at this checkpoint, and the R24
functional result is `NOT_RUN`.

The initial C24 assembler attempt also preserved a `FileNotFoundError`: a lexical
loader read a physical source path before that staged source existed on disk.
The correction persisted only exact own generated sources with exclusive create
before using that loader, then verified them. That refused attempt started no
qualifier or trial and caused no shared/runtime effects. This tester correction
is separate from the R23 failure and from product behavior.
