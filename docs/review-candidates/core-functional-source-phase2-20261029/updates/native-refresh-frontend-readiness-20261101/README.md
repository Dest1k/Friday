Before publishing a new native environment, the refresh wrapper now requires a current compiler receipt for the canonical Dashboard output. The check follows source-commit and selected-parent verification and precedes measurement of the target source identity. Build the canonical frontend using the existing preparation helpers before reaching this check.

The receipt reader has a 60-second ceiling inside the original forward deadline. Timeout or interruption stops and reaps its child, restores signal handlers, and refuses native publication. Existing cancellation, recovery reserve and minimum native-build budget remain in force. Missing, stale or untrusted helper/output inputs refuse.

This is a reviewed preparation patch against the Source135 refresh wrapper. It is not installed or bound to a live operation. Integration must update the final wrapper reference and check the resulting package; frontend compilation, installation and visible Dashboard acceptance remain separate. The only publication normalization replaces the private absolute helper path with the equivalent expression relative to HOME.

Independent review passed 21 checks, including three real Python-child timeout/interruption cleanup controls through the pinned helper; Root verified seven additional delta conditions. Node, frontend compilation and native refresh were not run by these checks.
