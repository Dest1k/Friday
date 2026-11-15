#!/bin/bash
# Invoke using /bin/bash path/to/root_fresh_fork.sh [controller arguments].
# A separate Python child is intentional. Do not replace this with tail exec:
# the lifetime SELF+CHILDREN 256MiB guard must retain literal kernel counters.
/usr/bin/python3 -I -B -S /home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-READER-JOIN-SOURCE-20261115/host/ownc_root_controller.py "$@"
status=$?
exit "$status"
