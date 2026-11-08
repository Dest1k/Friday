#!/usr/bin/env python3
"""Remove the scratch home copy from /tmp (per-user tmpfs quota is exhausted).

The apply-stage dry run filled the tmpfs quota with a full copy of the serving home,
so the DSH shell executor cannot start commands. This helper deletes that copy.
"""
import os
import shutil

TARGET = "/tmp/v45-home-acuinnaj"
if os.path.isdir(TARGET):
    shutil.rmtree(TARGET, ignore_errors=True)
print("removed" if not os.path.exists(TARGET) else "still present: " + TARGET)
