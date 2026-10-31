"""Offline profile preparation copied from the accepted recalculation repair.
No Office process is launched. The caller must provide a new directory name.
"""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path


def need(condition, message):
    if not condition:
        raise ValueError(message)


RECALC_PROFILE_XML = (b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<oor:items xmlns:oor="http://openoffice.org/2001/registry">'
    b'<item oor:path="/org.openoffice.Office.Calc/Formula/Load">'
    b'<prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop>'
    b'</item></oor:items>\n')


def seed_recalculation_profile(profile):
    """Initialize an empty owned phase profile before the fixed Office invocation."""
    info = profile.lstat()
    need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
         and stat.S_IMODE(info.st_mode) == 0o700 and not any(profile.iterdir()),
         'FRESH_EMPTY_OWNED_RECALC_PROFILE_REQUIRED')
    user = profile / 'user'
    user.mkdir(mode=0o700)
    target = user / 'registrymodifications.xcu'
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(RECALC_PROFILE_XML)
    return {'path': str(target), 'sha256': hashlib.sha256(RECALC_PROFILE_XML).hexdigest(),
            'bytes': len(RECALC_PROFILE_XML), 'initialized_before_office': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    args = parser.parse_args()
    args.profile.mkdir(mode=0o700)  # Existing paths refuse reuse.
    print(json.dumps(seed_recalculation_profile(args.profile), sort_keys=True))


if __name__ == '__main__':
    main()
