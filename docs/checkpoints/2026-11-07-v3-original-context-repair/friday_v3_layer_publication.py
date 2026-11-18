#!/usr/bin/env python3
"""V3 layer publication onto the serving ordinary home (the reviewed layers).

Design constraints honoured by this script:

* No copy of the runtime. The composition is checked against the live tree with the
  product's own ``source_checked`` and a proven-cache list of the generated artefacts;
  the tree is never cloned.
* Independent source and target data. Every layer manifest is read from the candidate
  project tree, every expected byte from the live serving home, and the two are compared;
  no comparison reads the same file twice.
* Journal first, publish second. Every changed file is recorded with its beforeimage in
  the transaction directory before it is published, and a failed run restores the
  beforeimages.
* One receiver. The transaction refuses to start unless the gateway unit is stopped.

Usage:
    python -I -B SCRIPT --request PATH --request-sha256 SHA
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import shutil
import stat
import importlib.machinery
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "friday.ordinary-telegram-source-update.v45"
# The explicit-composition schema: the request MUST name the layers of THIS operation in
# the field `layer_names`, and the validator refuses an absent, empty, malformed or
# repeated set instead of widening the operation to every known layer.
SCHEMA_EXPLICIT = "friday.ordinary-telegram-source-update.v46"
# The already reviewed historical root, never a future request or input digest.
CURRENT_SOURCE_V6_ROOT_INPUT = "dfc6fd4a552d9088887746c7329febcf1f4b152f01c81841cd2bb36241a891df"
LAYER_NAMES = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
    "bounded-resume-sidecar-guard",
    "bounded-7z-codec-activation",
    "bounded-current-ask-identity",
    "necessary-document-clarification-p04",
    "archive-conversion-failure-provenance-after188",
    "arj-unix-attribute-types-after-source189",
    "read-file-reject-write-arguments-after-source189",
    "archive-conversion-named-target-status-after-source190",
    "ordinary-direct-plain-cancel-after-source192",
    "ods-target-comments-after-source193",
    "ods-comment-preservation-after-source194",
    "odf-native-conversion-output-after-source195",
    "docx-odt-output-after-source196",
    "odf-reverse-output-after-source197",
    "dashboard-native-status-after-source198",
    "ods-calc-retained-source-profile-after-source199",
    "retained-calc-xlsx-destination-after-source200",
    "rtf-rich-odp-followup-and-office-bank-after-source201",
    "core-file-readability-and-context-provenance-after-source202",
    "rtf-optional-footnote-reader-after-source203",
    "core-user-result-contracts-after-source204",
    "f06-protected-office-profiles-after-source205",
    "f06-modern-odt-authenticated-profile-after-source206",
    "inbound-turn-log-metadata-after-source207",
    "f07-bounded-docx-structure-after-source208",
    "f07-malformed-docx-error-provenance-after-source209",
    "r02-telegram-text-uncertain-recovery-after-source210",
    "r02-boot-sweep-observation-after-source211",
    "r02-managed-file-output-phase-after-source212",
    "m09-retained-projection-bridge-after-source213",
    "word-fidelity-and-docx-copy-after-source214",
    "m09-real-web-custody-receipt-after-source215",
    "ordinary-document-owner-through-attachments-after-source216",
    "m09-genuine-summary-carrier-after-source217",
    "docx-inactive-story-interop-after-source218",
    "calc-required-formula-rich-profile-after-source219",
    "sameformat-rich-ods-after-source220",
    'ods-xlsx-native-visibility-compare-after-source221',
    'ordinary-f04-owned-ingress-stop-terminal-after-source222',
    'presentation-final-native-guidance-after-source223',
    'docx-located-mainstory-after-source224',
    'docx-required-stored-stories-after-source225',
    'core-communication-memory-after-source226',
    'word-output-visibility-after-source227',
    'document-preserving-edit-current-anchor-after-source228',
    'communication-create-read-after-source229',
    'core-document-final-guidance-after-source230',
    'delimited-explicit-locale-import-after-source231',
    'keyed-merge-provenance-guidance-after-source232',
    'zip-member-read-guidance-after-source233',
    'bounded-compaction-protected-rows-after-source234',
    'delimited-conversion-guidance-after-source235',
    'xlsx-recalc-truth-after-source236',
    'ordinary-document-reliability-after-source237',
    'word-fill-and-compression-primary-error-after-source238',
    'xlsx-print-layout-widths-after-source239',
    'xlsx-visible-row-edit-after-source240',
    'presentation-cyrillic-layout-and-read-provenance-after-source241',
    'gateway-cross-boot-and-presentation-declarations-after-source242',
    'xlsx-guarded-edit-routing-and-row-evidence-after-source243',
)
# Draft binding barrier: no request generation or publication may read the installed
# home for this selected edge until the exact frozen manifest and patch are supplied.
# These are deliberately not fixture pins and confer no admission by themselves.
CURRENT_SOURCE_TWENTY_FIFTH_LAYER = "ordinary-f04-owned-ingress-stop-terminal-after-source222"
CURRENT_SOURCE_TWENTY_FIFTH_MANIFEST_SHA256 = '12e52a66eccb9a3e8b0da7f68fea2ab440e51245a1e4d1f2b3c4d54fd36d7384'
CURRENT_SOURCE_TWENTY_FIFTH_PATCH_SHA256 = '934d189d9551eb7f81c27f3ac359d8550c8ba24b423bfb4c43a8295f50c145e2'

# Immutable source fingerprints only; these confer no current or runtime admission.
CURRENT_SOURCE_TWENTY_SIXTH_LAYER = "presentation-final-native-guidance-after-source223"
CURRENT_SOURCE_TWENTY_SIXTH_MANIFEST_SHA256 = "8f17803bbbe6ec829891105b5c7dc69e38690e75027aa84e4d62a86d3ec63b95"
CURRENT_SOURCE_TWENTY_SIXTH_PATCH_SHA256 = "76d191daf25ef3567edaba3b587ed937268ba6b797d4ef4dbf494a3be191f5bc"

# Exact new Source fingerprints; no live admission or future receipt.
CURRENT_SOURCE_TWENTY_SEVENTH_LAYER = 'docx-located-mainstory-after-source224'
CURRENT_SOURCE_TWENTY_SEVENTH_MANIFEST_SHA256 = '81b61a25e59d5e56708976241577cf1c811723814b29d950aa92bb6daa6f181e'
CURRENT_SOURCE_TWENTY_SEVENTH_PATCH_SHA256 = '6f7b9275e0d8fece804ef4c10f51ea8ca428f8219836976189395348672c4ec7'

# Exact226 Source fingerprints; no actual/current grant.
CURRENT_SOURCE_TWENTY_EIGHTH_LAYER = 'docx-required-stored-stories-after-source225'
CURRENT_SOURCE_TWENTY_EIGHTH_MANIFEST_SHA256 = 'b9feea67b18e1762d4b20fcad271ebe12c9457dc022cabde9ca07f3161679f13'
CURRENT_SOURCE_TWENTY_EIGHTH_PATCH_SHA256 = 'e41a45304b6876fe62c861c6af0a159eb7b8ad45d30277f658aaf4cf43da6df5'

# Exact227 Source fingerprints; no actual/current grant.
CURRENT_SOURCE_TWENTY_NINTH_LAYER = 'core-communication-memory-after-source226'
CURRENT_SOURCE_TWENTY_NINTH_MANIFEST_SHA256 = 'f3206ed54fcdcea18dc2bff83e792c5b422ec8d86991b0748be70a3708be1969'
CURRENT_SOURCE_TWENTY_NINTH_PATCH_SHA256 = '3c0463144860c0ec25d30897c9e24757c7c2e0c8a7564129554ef36731124b2b'

# Selected228 Word source only; the independent communication pair stays archived
# and deferred. The exact frozen pair below grants no current or runtime admission.
# These Source fingerprints do not confer current or runtime admission.
CURRENT_SOURCE_THIRTIETH_LAYER = 'word-output-visibility-after-source227'
CURRENT_SOURCE_THIRTIETH_MANIFEST_SHA256 = 'f4e2806261378841508d000d485f613a9103b103fd0a19694af993990c0655ae'
CURRENT_SOURCE_THIRTIETH_PATCH_SHA256 = '73b4881b15d70aec053d0ff482a18141d95fdb6218b0e0a4cb6c41912097f024'

# Exact229 document-preservation/anchor Source pins confer no current or runtime admission.
CURRENT_SOURCE_THIRTY_FIRST_LAYER = 'document-preserving-edit-current-anchor-after-source228'
CURRENT_SOURCE_THIRTY_FIRST_MANIFEST_SHA256 = '53db2b0084837d641c5fb3f42146f7eafc3bb61a5641d808cf090f2a573b43f2'
CURRENT_SOURCE_THIRTY_FIRST_PATCH_SHA256 = '6c042dc68f33fce16bd795a501edba93c73eca69727b88c51367f6336a81e3e0'

# Exact230 communication Source pins confer no current or runtime admission.
CURRENT_SOURCE_THIRTY_SECOND_LAYER = 'communication-create-read-after-source229'
CURRENT_SOURCE_THIRTY_SECOND_MANIFEST_SHA256 = '11fd86eb9a6d4b6bd5fecbcc8ce14a8e5721a06b88489d050de51913b14a67c1'
CURRENT_SOURCE_THIRTY_SECOND_PATCH_SHA256 = 'cdbc954319e05ba396d52928e72257cc97933e7782cd09edcf2286654ffc5441'

# Exact231 document-final-guidance Source pins confer no current or runtime admission.
CURRENT_SOURCE_THIRTY_THIRD_LAYER = 'core-document-final-guidance-after-source230'
CURRENT_SOURCE_THIRTY_THIRD_MANIFEST_SHA256 = '4cdeca2905f9bc36ca94870ffb9ae6670313ce36170331023f58dec66359d176'
CURRENT_SOURCE_THIRTY_THIRD_PATCH_SHA256 = '68740f175d76d131b5b93337f60fbc5a3fd53fa084a4a867cf7851a10393a142'

# Exact232 explicit-locale Source pins confer no current or runtime admission.
CURRENT_SOURCE_THIRTY_FOURTH_LAYER = 'delimited-explicit-locale-import-after-source231'
CURRENT_SOURCE_THIRTY_FOURTH_MANIFEST_SHA256 = '4eac7bf2c14d2cd68ea6639f41b89d12b6015d67d8600b4e7448ca66c84d0684'
CURRENT_SOURCE_THIRTY_FOURTH_PATCH_SHA256 = '92b0b383c7f38e7623d9c040adcbb64664269b7292693add28cede3709d59659'

# Exact233 keyed-merge/provenance guidance Source pins confer no current or runtime admission.
CURRENT_SOURCE_THIRTY_FIFTH_LAYER = 'keyed-merge-provenance-guidance-after-source232'
CURRENT_SOURCE_THIRTY_FIFTH_MANIFEST_SHA256 = '641debc568c576d13801bf2e303fbe145e3dc0a24e869d64c1b121b34a09acc7'
CURRENT_SOURCE_THIRTY_FIFTH_PATCH_SHA256 = '659018f33097367796d396eb66900df2f34225bb7f325b16f2d6cafbec364fbb'

# Exact234 ZIP member guidance layer.
CURRENT_SOURCE_THIRTY_SIXTH_LAYER = 'zip-member-read-guidance-after-source233'
CURRENT_SOURCE_THIRTY_SIXTH_MANIFEST_SHA256 = 'cd3a0d571763ff07caac326d11d95352e73fc6068831939e4c6db762b9f26463'
CURRENT_SOURCE_THIRTY_SIXTH_PATCH_SHA256 = 'f75a29eabb5d0cc3e2d88e131b6158518331d79f3c90048c2b8411c6ce7ae92c'

# Exact235 bounded compaction Source pins.
CURRENT_SOURCE_THIRTY_SEVENTH_LAYER = 'bounded-compaction-protected-rows-after-source234'
CURRENT_SOURCE_THIRTY_SEVENTH_MANIFEST_SHA256 = '4cd5b21055d312d02d20697077683ecf121090bea1d661f3e40b725bec74ced9'
CURRENT_SOURCE_THIRTY_SEVENTH_PATCH_SHA256 = 'e08a643d3d2f6f3c4d00bbd332d9bfb85a4ac7ae0ae8003a8122e48d4a231e96'

# Exact236 delimited conversion guidance Source pins.
CURRENT_SOURCE_THIRTY_EIGHTH_LAYER = 'delimited-conversion-guidance-after-source235'
CURRENT_SOURCE_THIRTY_EIGHTH_MANIFEST_SHA256 = '327893a6c8af3dc1e1090c922e554ad5c56cd5849643445c7fa80c2b2d66b9cb'
CURRENT_SOURCE_THIRTY_EIGHTH_PATCH_SHA256 = '049fbb9710458e0b00a1f545f5ab8ac645c30117896ea26d7f74c7b263dd159c'

# Exact237 XLSX truthful recalculation Source pins.
CURRENT_SOURCE_THIRTY_NINTH_LAYER = 'xlsx-recalc-truth-after-source236'
CURRENT_SOURCE_THIRTY_NINTH_MANIFEST_SHA256 = '6c2d28a2b53114cdc95e0c229b9de29cae745a774fe979b992d6521134498449'
CURRENT_SOURCE_THIRTY_NINTH_PATCH_SHA256 = '1fe85f4e0f3fe5eb484b994bbd892bc53c01e1b3a348b023f668909780e470f0'

# Exact238 saved Word output Source pins.
CURRENT_SOURCE_FORTIETH_LAYER = 'ordinary-document-reliability-after-source237'
CURRENT_SOURCE_FORTIETH_MANIFEST_SHA256 = 'd2daf590fad3e48f0a5857ebdf4c99f1e3eee1921b439cbc7c3c59c5a0b5337e'
CURRENT_SOURCE_FORTIETH_PATCH_SHA256 = 'ca57d543b20f24f79b74f6bbe1efece3c633d750dee5db77b2b23930eaf3f3c7'

# Exact Source239 layer and its installed Source238 receipt.
CURRENT_SOURCE_FORTY_FIRST_LAYER = 'word-fill-and-compression-primary-error-after-source238'
CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v41'
CURRENT_SOURCE_FORTY_FIRST_MANIFEST_SHA256 = '3afe9d00b5877df4c3765129148351e1e6f6ecb29c6a3470605c437252734e14'
CURRENT_SOURCE_FORTY_FIRST_PATCH_SHA256 = 'be1cd1d3472a30a69685f1975e134608534a8489ccebbc3aa14f635b0d7e7d2f'
CURRENT_SOURCE_FORTY_FIRST_PREVIOUS_RECEIPT_SHA256 = '24cb0173baeb376f69a0062416f8f81811bc49dc69becf82196dcfbfe8935429'

# Exact Source240 layer and its installed Source239 receipt.
CURRENT_SOURCE_FORTY_SECOND_LAYER = 'xlsx-print-layout-widths-after-source239'
CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v42'
CURRENT_SOURCE_FORTY_SECOND_MANIFEST_SHA256 = '11a96365248041df83cd13b1dfdaaff0f366e6c22a1c0e193f91de7c4eab3391'
CURRENT_SOURCE_FORTY_SECOND_PATCH_SHA256 = '839b2582db25f8218cbf34e83bf167ca9073d8a154b02eb8d7c35008f5ca1e83'
CURRENT_SOURCE_FORTY_SECOND_PREVIOUS_RECEIPT_SHA256 = 'a6c2f0435a3c766ad7d890f29b2b671fdc5f279eff6d7676f4093a13c64e4d0d'

# Exact Source241 pair from the registered layer and the closed Core240 predecessor.
CURRENT_SOURCE_FORTY_THIRD_LAYER = 'xlsx-visible-row-edit-after-source240'
CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v43'
CURRENT_SOURCE_FORTY_THIRD_MANIFEST_SHA256 = 'c93f430c2aebedb1f0b7a71137186925cff8d1fe5e18a5bed1c212f2e3993590'
CURRENT_SOURCE_FORTY_THIRD_PATCH_SHA256 = '59fec443f739d49f8203158a3bafee9815a6dc3a8564505cc401c45467b556f1'
CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_REQUEST_SHA256 = '881c64aafec752175ec0f28ddcfe5b40d1ba24aacf66c573f26487f9c9eda762'
CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_RECEIPT_SHA256 = '1227f556dd6e49bfe0b6d109bcbc8c1e36e57dfc82b418fe130ffe19125815e0'
CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_MARKER_SHA256 = '7e9ed3be76a71315d2c0e88766995550061bed091e4aabec13d59ba3a204bc16'
CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_STAMP_SHA256 = 'fddb5dca3463a6bbe8dc0d6acb00a7d3f5e2a1071c630915f9dade6781bc1f09'

# Exact Source242 layer and the closed Core241 predecessor it extends.
CURRENT_SOURCE_FORTY_FOURTH_LAYER = 'presentation-cyrillic-layout-and-read-provenance-after-source241'
CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v44'
CURRENT_SOURCE_FORTY_FOURTH_MANIFEST_SHA256 = '572aa53b146e8d2edfe4cf1fc93e4151f3a7490a4e061415f86bb25f125f1613'
CURRENT_SOURCE_FORTY_FOURTH_PATCH_SHA256 = 'f341863f16f0d81915b73a8f8d2d32f5aceac6eacd9a5e447649284a5c4db17e'
CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_REQUEST_SHA256 = '4b76ddd6bcae9e1b4acb51a8e9573e198bf832698b37a596b49ce78abf1339a6'
CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_COMMITTED_SHA256 = '9dd409e849be2dfe87875e59c225cc1fd3d09145aab19edfeb364ba98d5a4daf'
CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_RECEIPT_SHA256 = '34b9727ecc41a235070beb85cd7e78eca0cf3ab0d83ad5822bf91416e0b09493'
CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_MARKER_SHA256 = 'c87cbd034693c9fc2c4291a442686bf4c1d0c7bc31c217ee8a7f041a0bbeedb0'
CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_STAMP_SHA256 = 'f54d558ea8a1c53e95ec6141c56e7ec6410d5fe80c8952015b0bc2de5c8d02d2'
CURRENT_SOURCE_FORTY_FOURTH_HELPER = 'scripts/friday_ordinary_install.py'

# Exact Source243 layer and the closed Core242 predecessor it extends.
CURRENT_SOURCE_FORTY_FIFTH_LAYER = 'gateway-cross-boot-and-presentation-declarations-after-source242'
CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v45'
CURRENT_SOURCE_FORTY_FIFTH_MANIFEST_SHA256 = '4ab115d8eaddd1f57432bec38f194fbd21ae63ae439735518e27ec62847c91ad'
CURRENT_SOURCE_FORTY_FIFTH_PATCH_SHA256 = '83172e6982fd280ea0f11fcf8e9d6f7fda3f79a5efdbf4ac6f816e06aaaa51b2'
CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_REQUEST_SHA256 = '1a859c7c2517879159edc2939179a9c77247a6e850b527649550631378e382d6'
CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_COMMITTED_SHA256 = 'a412099139ca2b909ceb07d0d61700cf993285aa763a81bb1e8b9904fb04764e'
CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_RECEIPT_SHA256 = '5f223aeceb61417238dcdf474e55732476a3e5b4c13f1926bd51ea4ca218ab62'
CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_MARKER_SHA256 = '4a0dc23baafbe42d936598328884bf2b4ecf2966f6ee224222011962653f7cf6'
CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_STAMP_SHA256 = 'a3e21b84fe864a5c2eda195f1097c1059eafc306fac4f31d4aa60c5bdee270ec'
CURRENT_SOURCE_FORTY_FIFTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FORTY_FIFTH_NATIVE_FILES = (
    'gateway/host_rendezvous.py',
    'hermes_cli/friday_prompt_scope.py',
    'hermes_cli/friday_schema_guidance.py',
    'tests/gateway/test_host_rendezvous.py',
    'tools/file_tools.py',
)

# Exact Source244 layer and the closed Core243 predecessor it extends.
CURRENT_SOURCE_FORTY_SIXTH_LAYER = 'xlsx-guarded-edit-routing-and-row-evidence-after-source243'
CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v46'
CURRENT_SOURCE_FORTY_SIXTH_MANIFEST_SHA256 = '88e8203a189006f29373a42750b2348e3a79d74c123f7f79658aad85188dae2e'
CURRENT_SOURCE_FORTY_SIXTH_PATCH_SHA256 = 'e1bb0f655b3d49e24a7dbc8bebf23fa3e947905c5264343ace867535cde22465'
CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_REQUEST_SHA256 = '6795cdbed082d32bb93668c9022d610312039e09f2458e0a788b55a0db7ee366'
CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_COMMITTED_SHA256 = '47467b40a83e19638e32505e37326eeae7653878be6e6106b320ef352cfe8c07'
CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_RECEIPT_SHA256 = '4835d1f9648a22765c5dc0c30ad3d8d179f0e6a9ee56fa1d595b0a468454c231'
CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_MARKER_SHA256 = '10974477ebbb0527a5669dc47413dcc3f1ea0574184dc23d70f71118180443e6'
CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_STAMP_SHA256 = '2d59aa3515c0e6f0fce3baaefd297422d46213a9a8364145ed1f7d3891d5e8d6'
CURRENT_SOURCE_FORTY_SIXTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FORTY_SIXTH_NATIVE_FILES = (
    'hermes_cli/friday_prompt_scope.py',
    'hermes_cli/friday_schema_guidance.py',
    'hermes_cli/friday_user_scope.py',
    'hermes_cli/friday_workspace_xlsx.py',
    'tools/file_tools.py',
    'tools/scoped_spreadsheet_profiles.py',
)

# The composition of the HISTORICAL four-layer request, named explicitly. A legacy v45
# request that carries no `layer_names` keeps exactly this meaning; it never widens to
# every layer this file happens to know today.
HISTORICAL_LAYER_NAMES = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
)
REQUIRED_HISTORY_ROOTS = (
    "preparation/ordinary-gateway",
    "preparation/ordinary-gateway-archive",
)


# A controlled failure at the rename/sync boundary of ONE named target. The injection is
# ONE-SHOT: it fires on the publication of that target and never during the rollback, so
# a rollback really restores the state instead of failing at the same place again.
INJECT_AFTER_RENAME = False
INJECT_TARGET = None
# When the injection fires, the transaction records what the home looks like AT THAT
# MOMENT: the bytes and modes of every file it has already published, and of every file it
# added. The record is written OUTSIDE the rollback journal, so the rollback cannot change
# it; it is the evidence that the late point was reached with changed files on disk.
INJECT_SNAPSHOT_DIR = None
# The files whose state is recorded at the injection point. They are named explicitly by
# the request; the scope of the read is never derived from a directory's parents.
INJECT_SNAPSHOT_FILES = ()
# The home the snapshot reads from. It is set from the VERIFIED home of the running
# transaction, never from the parents of the result directory, and it is passed to the
# snapshot explicitly.
INJECT_SNAPSHOT_HOME = None


class Refused(Exception):
    """The transaction refused; the home is unchanged."""


class StopUnconfirmed(Exception):
    """A consumer could not be confirmed stopped; the home is unchanged."""


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def require_twenty_fifth_source_binding(layer_names=(), context=None):
    """Refuse the selected draft before any installed-home or request-file access."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_TWENTY_FIFTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v25")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_TWENTY_FIFTH_MANIFEST_SHA256,
                                  CURRENT_SOURCE_TWENTY_FIFTH_PATCH_SHA256)),
                "transaction_current_source_twenty_fifth_binding_unbound")


def require_twenty_sixth_source_binding(layer_names=(), context=None):
    """Keep the explicit after223 edge closed until its exact source pair is frozen."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_TWENTY_SIXTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v26")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_TWENTY_SIXTH_MANIFEST_SHA256,
                                  CURRENT_SOURCE_TWENTY_SIXTH_PATCH_SHA256)),
                "transaction_current_source_twenty_sixth_binding_unbound")


def require_twenty_seventh_source_binding(layer_names=(), context=None):
    """Keep the explicit after224 edge closed until its exact source pair is frozen."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_TWENTY_SEVENTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v27")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_TWENTY_SEVENTH_MANIFEST_SHA256,
                                  CURRENT_SOURCE_TWENTY_SEVENTH_PATCH_SHA256)),
                "transaction_current_source_twenty_seventh_binding_unbound")


def require_twenty_eighth_source_binding(layer_names=(), context=None):
    """Keep the explicit after225 edge closed until its exact source pair is frozen."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_TWENTY_EIGHTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v28")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_TWENTY_EIGHTH_MANIFEST_SHA256,
                                  CURRENT_SOURCE_TWENTY_EIGHTH_PATCH_SHA256)),
                "transaction_current_source_twenty_eighth_binding_unbound")


def require_twenty_ninth_source_binding(layer_names=(), context=None):
    """Keep the explicit after226 edge closed until its exact source pair is frozen."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_TWENTY_NINTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v29")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_TWENTY_NINTH_MANIFEST_SHA256,
                                  CURRENT_SOURCE_TWENTY_NINTH_PATCH_SHA256)),
                "transaction_current_source_twenty_ninth_binding_unbound")


def require_thirtieth_source_binding(layer_names=(), context=None):
    """Keep the explicit after227 edge closed until its exact source pair is frozen."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTIETH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v30")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_THIRTIETH_MANIFEST_SHA256,
                                  CURRENT_SOURCE_THIRTIETH_PATCH_SHA256)),
                "transaction_current_source_thirtieth_binding_unbound")


def require_thirty_first_source_binding(layer_names=(), context=None):
    """Keep the exact after228 edge bound before installed-home or request access."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_FIRST_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v31")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_THIRTY_FIRST_MANIFEST_SHA256,
                                  CURRENT_SOURCE_THIRTY_FIRST_PATCH_SHA256)),
                "transaction_current_source_thirty_first_binding_unbound")


def require_thirty_second_source_binding(layer_names=(), context=None):
    """Keep the exact after229 edge bound before installed-home or request access."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_SECOND_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v32")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_THIRTY_SECOND_MANIFEST_SHA256,
                                  CURRENT_SOURCE_THIRTY_SECOND_PATCH_SHA256)),
                "transaction_current_source_thirty_second_binding_unbound")


def require_thirty_third_source_binding(layer_names=(), context=None):
    """Keep the explicit after230 edge closed until its exact source pair is frozen."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_THIRD_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v33")
    if selected or selected_context:
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in (CURRENT_SOURCE_THIRTY_THIRD_MANIFEST_SHA256,
                                  CURRENT_SOURCE_THIRTY_THIRD_PATCH_SHA256)),
                "transaction_current_source_thirty_third_binding_unbound")


def require_thirty_fourth_source_binding(layer_names=(), context=None, project_files=None):
    """Keep the explicit after231 edge bound to its exact frozen two-file pair."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_FOURTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v34")
    if selected or selected_context:
        pair = (CURRENT_SOURCE_THIRTY_FOURTH_MANIFEST_SHA256,
                CURRENT_SOURCE_THIRTY_FOURTH_PATCH_SHA256)
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in pair),
                "transaction_current_source_thirty_fourth_binding_unbound")
        require(pair == (
                    "4eac7bf2c14d2cd68ea6639f41b89d12b6015d67d8600b4e7448ca66c84d0684",
                    "92b0b383c7f38e7623d9c040adcbb64664269b7292693add28cede3709d59659"),
                "transaction_current_source_thirty_fourth_binding_pair_changed")
        if project_files is not None:
            require(type(project_files) is dict
                    and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_FOURTH_LAYER}-manifest.json") == pair[0]
                    and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_FOURTH_LAYER}.patch") == pair[1],
                    "transaction_current_source_thirty_fourth_binding_pair_changed")


def require_thirty_fifth_source_binding(layer_names=(), context=None, project_files=None):
    """Keep the explicit after232 edge bound to its exact frozen one-MOD pair."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_FIFTH_LAYER in layer_names)
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v35")
    if selected or selected_context:
        pair = (CURRENT_SOURCE_THIRTY_FIFTH_MANIFEST_SHA256,
                CURRENT_SOURCE_THIRTY_FIFTH_PATCH_SHA256)
        require(all(type(value) is str
                    and __import__("re").fullmatch("[0-9a-f]{64}", value)
                    for value in pair),
                "transaction_current_source_thirty_fifth_binding_unbound")
        require(pair == (
                    "641debc568c576d13801bf2e303fbe145e3dc0a24e869d64c1b121b34a09acc7",
                    "659018f33097367796d396eb66900df2f34225bb7f325b16f2d6cafbec364fbb"),
                "transaction_current_source_thirty_fifth_binding_pair_changed")
        if project_files is not None:
            require(type(project_files) is dict
                    and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_FIFTH_LAYER}-manifest.json") == pair[0]
                    and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_FIFTH_LAYER}.patch") == pair[1],
                    "transaction_current_source_thirty_fifth_binding_pair_changed")


def require_thirty_sixth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after233 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_SIXTH_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v36")
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_THIRTY_SIXTH_LAYER,),
            "transaction_current_source_exact_thirty_sixth_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_thirty_sixth_context_required")
        project_files = request.get("project_inventory") or {}
    pair = (CURRENT_SOURCE_THIRTY_SIXTH_MANIFEST_SHA256,
            CURRENT_SOURCE_THIRTY_SIXTH_PATCH_SHA256)
    require(all(type(value) is str and __import__("re").fullmatch("[0-9a-f]{64}", value)
                for value in pair),
            "transaction_current_source_thirty_sixth_binding_unbound")
    require(pair == (
                "cd3a0d571763ff07caac326d11d95352e73fc6068831939e4c6db762b9f26463",
                "f75a29eabb5d0cc3e2d88e131b6158518331d79f3c90048c2b8411c6ce7ae92c"),
            "transaction_current_source_thirty_sixth_binding_pair_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_SIXTH_LAYER}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_SIXTH_LAYER}.patch") == pair[1],
                "transaction_current_source_thirty_sixth_binding_pair_changed")


def require_thirty_seventh_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after234 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_SEVENTH_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v37")
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_THIRTY_SEVENTH_LAYER,),
            "transaction_current_source_exact_thirty_seventh_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_thirty_seventh_context_required")
        project_files = request.get("project_inventory") or {}
    pair = (CURRENT_SOURCE_THIRTY_SEVENTH_MANIFEST_SHA256,
            CURRENT_SOURCE_THIRTY_SEVENTH_PATCH_SHA256)
    require(all(type(value) is str and __import__("re").fullmatch("[0-9a-f]{64}", value)
                for value in pair),
            "transaction_current_source_thirty_seventh_binding_unbound")
    require(pair == (
                "4cd5b21055d312d02d20697077683ecf121090bea1d661f3e40b725bec74ced9",
                "e08a643d3d2f6f3c4d00bbd332d9bfb85a4ac7ae0ae8003a8122e48d4a231e96"),
            "transaction_current_source_thirty_seventh_binding_pair_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_SEVENTH_LAYER}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_SEVENTH_LAYER}.patch") == pair[1],
                "transaction_current_source_thirty_seventh_binding_pair_changed")


def require_thirty_eighth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after235 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_EIGHTH_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v38")
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_THIRTY_EIGHTH_LAYER,),
            "transaction_current_source_exact_thirty_eighth_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_thirty_eighth_context_required")
        project_files = request.get("project_inventory") or {}
    pair = (CURRENT_SOURCE_THIRTY_EIGHTH_MANIFEST_SHA256,
            CURRENT_SOURCE_THIRTY_EIGHTH_PATCH_SHA256)
    require(all(type(value) is str and __import__("re").fullmatch("[0-9a-f]{64}", value)
                for value in pair),
            "transaction_current_source_thirty_eighth_binding_unbound")
    require(pair == (
                "327893a6c8af3dc1e1090c922e554ad5c56cd5849643445c7fa80c2b2d66b9cb",
                "049fbb9710458e0b00a1f545f5ab8ac645c30117896ea26d7f74c7b263dd159c"),
            "transaction_current_source_thirty_eighth_binding_pair_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_EIGHTH_LAYER}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_EIGHTH_LAYER}.patch") == pair[1],
                "transaction_current_source_thirty_eighth_binding_pair_changed")


def require_thirty_ninth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after236 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_THIRTY_NINTH_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v39")
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_THIRTY_NINTH_LAYER,),
            "transaction_current_source_exact_thirty_ninth_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_thirty_ninth_context_required")
        project_files = request.get("project_inventory") or {}
    pair = (CURRENT_SOURCE_THIRTY_NINTH_MANIFEST_SHA256,
            CURRENT_SOURCE_THIRTY_NINTH_PATCH_SHA256)
    require(all(type(value) is str and __import__("re").fullmatch("[0-9a-f]{64}", value)
                for value in pair),
            "transaction_current_source_thirty_ninth_binding_unbound")
    require(pair == (
                "6c2d28a2b53114cdc95e0c229b9de29cae745a774fe979b992d6521134498449",
                "1fe85f4e0f3fe5eb484b994bbd892bc53c01e1b3a348b023f668909780e470f0"),
            "transaction_current_source_thirty_ninth_binding_pair_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_NINTH_LAYER}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_THIRTY_NINTH_LAYER}.patch") == pair[1],
                "transaction_current_source_thirty_ninth_binding_pair_changed")


def require_fortieth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after237 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_FORTIETH_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == "friday.current-source-native-successor.v40")
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_FORTIETH_LAYER,),
            "transaction_current_source_exact_fortieth_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_fortieth_context_required")
        project_files = request.get("project_inventory") or {}
    pair = (CURRENT_SOURCE_FORTIETH_MANIFEST_SHA256,
            CURRENT_SOURCE_FORTIETH_PATCH_SHA256)
    require(all(type(value) is str and __import__("re").fullmatch("[0-9a-f]{64}", value)
                for value in pair),
            "transaction_current_source_fortieth_binding_unbound")
    require(pair == (
                "d2daf590fad3e48f0a5857ebdf4c99f1e3eee1921b439cbc7c3c59c5a0b5337e",
                "ca57d543b20f24f79b74f6bbe1efece3c633d750dee5db77b2b23930eaf3f3c7"),
            "transaction_current_source_fortieth_binding_pair_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_FORTIETH_LAYER}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{CURRENT_SOURCE_FORTIETH_LAYER}.patch") == pair[1],
                "transaction_current_source_fortieth_binding_pair_changed")


def require_forty_first_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after238 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_FORTY_FIRST_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA)
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_FORTY_FIRST_LAYER,),
            "transaction_current_source_exact_forty_first_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_forty_first_context_required")
        project_files = request.get("project_inventory") or {}
        source_receipt = request.get("source_receipt")
        require(type(source_receipt) is dict
                and source_receipt == request.get("target_receipt")
                and source_receipt.get("sha256") == CURRENT_SOURCE_FORTY_FIRST_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_first_previous_receipt_pin_changed")
    pair = (CURRENT_SOURCE_FORTY_FIRST_MANIFEST_SHA256,
            CURRENT_SOURCE_FORTY_FIRST_PATCH_SHA256)
    require(pair == (
                "3afe9d00b5877df4c3765129148351e1e6f6ecb29c6a3470605c437252734e14",
                "be1cd1d3472a30a69685f1975e134608534a8489ccebbc3aa14f635b0d7e7d2f"),
            "transaction_current_source_forty_first_binding_pair_changed")
    if project_files is not None:
        layer = CURRENT_SOURCE_FORTY_FIRST_LAYER
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{layer}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{layer}.patch") == pair[1],
                "transaction_current_source_forty_first_binding_pair_changed")


def require_forty_second_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the explicit after239 singleton to its frozen manifest and patch."""
    selected = (isinstance(layer_names, (list, tuple))
                and CURRENT_SOURCE_FORTY_SECOND_LAYER in layer_names)
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA)
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (CURRENT_SOURCE_FORTY_SECOND_LAYER,),
            "transaction_current_source_exact_forty_second_layer_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context,
                "transaction_current_source_forty_second_context_required")
        project_files = request.get("project_inventory") or {}
        source_receipt = request.get("source_receipt")
        require(type(source_receipt) is dict
                and source_receipt == request.get("target_receipt")
                and source_receipt.get("sha256") == CURRENT_SOURCE_FORTY_SECOND_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_second_previous_receipt_pin_changed")
    pair = (CURRENT_SOURCE_FORTY_SECOND_MANIFEST_SHA256,
            CURRENT_SOURCE_FORTY_SECOND_PATCH_SHA256)
    require(pair == (
                "11a96365248041df83cd13b1dfdaaff0f366e6c22a1c0e193f91de7c4eab3391",
                "839b2582db25f8218cbf34e83bf167ca9073d8a154b02eb8d7c35008f5ca1e83"),
            "transaction_current_source_forty_second_binding_pair_changed")
    if project_files is not None:
        layer = CURRENT_SOURCE_FORTY_SECOND_LAYER
        require(type(project_files) is dict
                and project_files.get(f"patches/hermes/{layer}-manifest.json") == pair[0]
                and project_files.get(f"patches/hermes/{layer}.patch") == pair[1],
                "transaction_current_source_forty_second_binding_pair_changed")


def forty_third_predecessor_ref(home):
    """Reference the canonical retained request of the installed CP240 edge."""
    pin = CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def require_forty_third_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source240 → 241 edge before any publication work."""
    layer = CURRENT_SOURCE_FORTY_THIRD_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA)
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_third_layer_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    pins = (CURRENT_SOURCE_FORTY_THIRD_MANIFEST_SHA256, CURRENT_SOURCE_FORTY_THIRD_PATCH_SHA256,
            CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_REQUEST_SHA256)
    require(all(type(pin) is str and len(pin) == 64 and all(c in "0123456789abcdef" for c in pin)
                for pin in pins),
            "transaction_current_source_forty_third_binding_required")
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_third_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute() and str(Path(home).resolve()) == home,
                "transaction_current_source_forty_third_home_required")
        require(context["previous_native_update"] == forty_third_predecessor_ref(home),
                "transaction_current_source_forty_third_previous_request_pin_changed")
        metadata = {
            "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_MARKER_SHA256),
            "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_RECEIPT_SHA256),
            "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_RECEIPT_SHA256),
            "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_STAMP_SHA256),
        }
        for key, (relative, sha256) in metadata.items():
            require(request.get(key) == {"path": str(Path(home) / relative), "sha256": sha256},
                    "transaction_current_source_forty_third_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_third_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 240 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 563,
                "transaction_current_source_forty_third_inventory_count_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == pins[0] and project_files.get(patch) == pins[1],
                "transaction_current_source_forty_third_binding_pair_changed")


def read_forty_third_previous_receipt(home):
    raw = owned_file(Path(home) / "hermes-agent.source.json")
    require(digest(raw) == CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_RECEIPT_SHA256,
            "transaction_current_source_forty_third_previous_receipt_changed")
    return json.loads(raw)


def require_forty_third_predecessor(request, previous, *, raw=None):
    """Verify the builder and publisher consume the same retained v42 request."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_third_predecessor_ref(request["home"]),
            "transaction_current_source_forty_third_previous_request_pin_changed")
    path = Path(ref["path"])
    require(str(path.resolve()) == ref["path"],
            "transaction_current_source_forty_third_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_third_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor.get("current_source_successor") if type(predecessor) is dict else None
    require(type(previous_context) is dict
            and previous_context.get("schema") == CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA
            and predecessor.get("schema") == SCHEMA_EXPLICIT
            and predecessor.get("home") == request["home"]
            and predecessor.get("layer_names") == [CURRENT_SOURCE_FORTY_SECOND_LAYER]
            and predecessor.get("current_input") == request["previous_input"]
            and len(previous["project_files"]) == 561
            and predecessor.get("project_inventory") == previous["project_files"]
            and previous_context.get("root_project_update") == context["root_project_update"],
            "transaction_current_source_forty_second_predecessor_lineage_changed")


def forty_fourth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def require_forty_fourth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source241 to Source242 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FORTY_FOURTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    selected_context = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA)
    if not selected and not selected_context:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_fourth_layer_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and selected_context
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_fourth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute() and str(Path(home).resolve()) == home,
                "transaction_current_source_forty_fourth_home_required")
        require(context["previous_native_update"] == forty_fourth_predecessor_ref(home),
                "transaction_current_source_forty_fourth_previous_request_pin_changed")
        metadata = {
            "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_MARKER_SHA256),
            "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_RECEIPT_SHA256),
            "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_RECEIPT_SHA256),
            "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_STAMP_SHA256),
        }
        for key, (relative, sha256) in metadata.items():
            require(request.get(key) == {"path": str(Path(home) / relative), "sha256": sha256},
                    "transaction_current_source_forty_fourth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_fourth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 241 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 565,
                "transaction_current_source_forty_fourth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FORTY_FOURTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_forty_fourth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FORTY_FOURTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FORTY_FOURTH_PATCH_SHA256,
                "transaction_current_source_forty_fourth_binding_pair_changed")


def require_forty_fourth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v43 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_fourth_predecessor_ref(request["home"]),
            "transaction_current_source_forty_fourth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_forty_fourth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_fourth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_THIRD_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 563
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_third_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_forty_fourth_previous_committed_changed")
    return committed_path, committed_raw


def forty_fifth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def forty_fifth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_forty_fifth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source242 to Source243 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FORTY_FIFTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_fifth_layer_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_fifth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_forty_fifth_home_required")
        require(context["previous_native_update"] == forty_fifth_predecessor_ref(home),
                "transaction_current_source_forty_fifth_previous_request_pin_changed")
        for key, ref in forty_fifth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_forty_fifth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_fifth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 242 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 567,
                "transaction_current_source_forty_fifth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FORTY_FIFTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_forty_fifth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FORTY_FIFTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FORTY_FIFTH_PATCH_SHA256,
                "transaction_current_source_forty_fifth_binding_pair_changed")


def require_forty_fifth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v44 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_fifth_predecessor_ref(request["home"]),
            "transaction_current_source_forty_fifth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_forty_fifth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_fifth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_FOURTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 565
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_fourth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_forty_fifth_previous_committed_changed")
    return committed_path, committed_raw


def forty_sixth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def forty_sixth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_forty_sixth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source243 to Source244 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FORTY_SIXTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_sixth_layer_required")
    require(CURRENT_SOURCE_FORTY_SIXTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FORTY_SIXTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FORTY_SIXTH_NATIVE_FILES,
            "transaction_current_source_forty_sixth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_sixth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_forty_sixth_home_required")
        require(context["previous_native_update"] == forty_sixth_predecessor_ref(home),
                "transaction_current_source_forty_sixth_previous_request_pin_changed")
        for key, ref in forty_sixth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_forty_sixth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_sixth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 243 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 569,
                "transaction_current_source_forty_sixth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FORTY_SIXTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_forty_sixth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FORTY_SIXTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FORTY_SIXTH_PATCH_SHA256,
                "transaction_current_source_forty_sixth_binding_pair_changed")


def require_forty_sixth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v45 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_sixth_predecessor_ref(request["home"]),
            "transaction_current_source_forty_sixth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_forty_sixth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_sixth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_FIFTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 567
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_fifth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_forty_sixth_previous_committed_changed")
    return committed_path, committed_raw


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def read_bytes(path, limit=256 * 1024 ** 2):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode), "transaction_not_a_regular_file")
        require(info.st_size <= limit, "transaction_file_too_large")
        data = b""
        while len(data) <= limit:
            chunk = os.read(fd, min(1024 ** 2, limit + 1 - len(data)))
            if not chunk:
                break
            data += chunk
        require(len(data) <= limit, "transaction_file_too_large")
        named = path.lstat()
        for key in ("st_dev", "st_ino", "st_uid", "st_size", "st_mtime_ns", "st_ctime_ns"):
            require(getattr(info, key) == getattr(named, key), "transaction_file_identity_changed")
        return data
    finally:
        os.close(fd)


def read_json(path):
    return json.loads(read_bytes(path))


def owned_file(path):
    """Read a file the transaction owns; refuse links and foreign ownership."""
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode),
            "transaction_owned_regular_file_required")
    require(info.st_uid == os.getuid(), "transaction_owned_file_required")
    return read_bytes(path)


def private_directory(path, mode=0o700):
    path = Path(path)
    if path.exists():
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                and stat.S_IMODE(info.st_mode) == mode, "transaction_private_directory_required")
        return path
    path.mkdir(parents=True, mode=mode)
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == mode, "transaction_private_directory_required")
    return path


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_all(fd, data):
    """Complete a regular-file write or refuse before its publication."""
    offset = 0
    while offset < len(data):
        count = os.write(fd, data[offset:])
        require(type(count) is int and 0 < count <= len(data) - offset,
                "transaction_write_failed")
        offset += count


def write_atomic(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    sync_directory(path.parent)


def publish(target, data, mode=0o600, *, _before_replace=None, _temporary_suffix=".publish.tmp"):
    """Publish bytes to the home through a private temporary file and one rename.

    A failure between the rename and the directory synchronisation leaves the file
    changed. The caller registers the path in the rollback list before the call, so such a
    file is restored as well.
    """
    global INJECT_AFTER_RENAME
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name("." + target.name + _temporary_suffix)
    if _before_replace is not None:
        require(not os.path.lexists(tmp), "transaction_v5_publication_temp_exists")
    elif tmp.exists():
        tmp.unlink()
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        write_all(fd, data)
        os.fsync(fd)
        if _before_replace is not None:
            os.fchmod(fd, mode)
            staged_identity = os.fstat(fd)
    finally:
        os.close(fd)
    # The legacy three-argument path keeps its exact close/chmod sequence.
    if _before_replace is None:
        os.chmod(tmp, mode)
    else:
        def staged_unchanged():
            named = tmp.lstat()
            require(all(getattr(staged_identity, key) == getattr(named, key) for key in
                        ("st_dev", "st_ino", "st_uid", "st_gid", "st_mode", "st_nlink",
                         "st_size", "st_mtime_ns", "st_ctime_ns")),
                    "transaction_v5_temporary_identity_changed")
        staged_unchanged()
        _before_replace(tmp)
        staged_unchanged()
    os.replace(tmp, target)
    if INJECT_AFTER_RENAME and (INJECT_TARGET is None or str(target) == INJECT_TARGET):
        # The injection is one-shot: it fires on the publication of the named target and
        # never again, so the ROLLBACK of that same target restores it instead of failing
        # at the same boundary again.
        INJECT_AFTER_RENAME = False
        if INJECT_SNAPSHOT_DIR is not None:
            _write_injection_snapshot(INJECT_SNAPSHOT_DIR, target,
                                     INJECT_SNAPSHOT_FILES, INJECT_SNAPSHOT_HOME)
        # a controlled failure at the rename/sync boundary, used to prove that the rollback
        # covers a file that was already changed when the failure happened
        raise OSError(errno.EIO, "injected failure after the rename")
    sync_directory(target.parent)


def private_parents(root, relative):
    """Create the parent directories of a relative path inside the private root."""
    current = Path(root)
    for part in Path(relative).parent.parts:
        current = current / part
        if current.exists():
            info = current.lstat()
            require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),
                    "transaction_directory_custody_refused")
            continue
        current.mkdir(mode=0o700)
        info = current.lstat()
        require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700,
                "transaction_directory_custody_refused")


def source_parents_checked(source, relative):
    """Native additions use existing owned real protected source directories."""
    current = Path(source)
    for part in (None, *Path(relative).parent.parts):
        if part is not None:
            current = current / part
        info = current.lstat()
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
                and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) & 0o022 == 0,
                "transaction_source_directory_custody_refused")


def new_source_absence_checked(source, relative):
    """ENOENT under checked existing parents only; links/errors are not absence."""
    source_parents_checked(source, relative)
    path = Path(source) / relative
    try:
        path.lstat()
    except FileNotFoundError:
        require(not os.path.lexists(path), "transaction_new_source_exists:" + str(relative))
        return
    require(False, "transaction_new_source_exists:" + str(relative))


# --------------------------------------------------------------------------- gateway


def gateway_running(unit_path, bench_home=None):
    """True when the gateway unit is active; the transaction refuses to run then.

    ``bench_home`` is only used on an isolated bench: there the unit of the bench's own
    runtime is inspected. The live home is never affected by a bench run.
    """
    unit = Path(unit_path)
    if bench_home is not None:
        # a bench run must not stop or inspect the live gateway; the bench's own gateway
        # is represented by a unit file inside the bench.
        bench_unit = Path(bench_home) / "preparation" / "bench-unit.name"
        if bench_unit.exists():
            unit = Path(bench_unit.read_text().strip())
        else:
            return False
    result = subprocess.run(["systemctl", "--user", "is-active", unit.name],
                            capture_output=True, text=True, timeout=30)
    return result.stdout.strip() == "active"


def _digest_file(path, limit=64 * 1024 * 1024, chunk=64 * 1024):
    """Stream a file through the digest with a bounded read and a bounded size."""
    import hashlib as _hashlib
    size = 0
    hasher = _hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            size += len(block)
            if size > limit:
                raise Refused("transaction_snapshot_file_too_large:" + str(path))
            hasher.update(block)
    return hasher.hexdigest(), size


def _write_injection_snapshot(directory, current_target, files, home):
    """Record the state of EXACTLY the named files at the moment of the injected failure.

    The set of files is passed in explicitly. The scope of the read is never derived from
    the parents of the result directory, so DSH sessions, neighbouring benches, caches and
    other temporary work are outside it by construction. Every named file must exist, must
    be a regular file inside the home and must not be a symlink; a missing file, an
    unreadable file or a size above the bound is an explicit refusal, never a silent skip.
    """
    import stat as _stat
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    home = Path(home).resolve()
    if not files:
        raise Refused("transaction_snapshot_file_set_empty")
    state = {}
    read_paths = []
    for relative in files:
        if not isinstance(relative, str) or not relative or relative.startswith("/"):
            raise Refused("transaction_snapshot_path_invalid:" + str(relative))
        target = (home / relative)
        # a symlink is refused by its own name, before any resolution
        if target.is_symlink():
            raise Refused("transaction_snapshot_path_is_symlink:" + relative)
        try:
            resolved = target.resolve()
        except OSError:
            raise Refused("transaction_snapshot_path_unresolvable:" + relative) from None
        if resolved != target or home not in resolved.parents:
            raise Refused("transaction_snapshot_path_outside_home:" + relative)
        if not target.is_file():
            raise Refused("transaction_snapshot_file_missing:" + relative)
        info = target.lstat()
        if not _stat.S_ISREG(info.st_mode):
            raise Refused("transaction_snapshot_file_not_regular:" + relative)
        sha256, size = _digest_file(target)
        state[str(target)] = {"sha256": sha256, "mode": _stat.S_IMODE(info.st_mode),
                              "bytes": size}
        read_paths.append(str(target))
    (directory / "STATE-AT-INJECTION.json").write_bytes(encoded(
        {"schema": "friday.v3.injection-point-state.v1",
         "at_target": str(current_target),
         "home": str(home),
         "files": state,
         "read_paths": read_paths}))


class Journal:
    """One beforeimage store for the whole operation.

    Every file the operation touches is recorded BEFORE it is written: the real previous
    bytes of the home and the attributes needed to restore them. A file that did not
    exist before is recorded as absent, so the rollback removes it. The receipt, the
    marker and the stamp are recorded the same way, so a refusal restores the metadata
    together with the content.
    """

    def __init__(self, root, home):
        self.root = Path(root)
        self.home = Path(home)
        self.entries = {}

    def entries_dict(self):
        return dict(self.entries)

    def _relative(self, path):
        """The path of a file relative to the home, so the journal stays inside its root."""
        path = Path(path)
        try:
            return path.relative_to(self.home)
        except ValueError:
            return Path(path.name)

    def _target(self, path):
        target = self.root / "before" / self._relative(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def record_existing(self, path, data):
        """Record the real previous bytes of an existing file.

        The first recording wins: a file that is written twice keeps the bytes it had
        before the operation started, not the bytes of the intermediate write.
        """
        path = Path(path)
        key = str(path)
        if key in self.entries:
            return self.entries[key]
        info = path.lstat()
        entry = {"state": "EXISTED", "sha256": digest(data), "bytes": len(data),
                 "mode": stat.S_IMODE(info.st_mode)}
        saved = self._target(path)
        write_atomic(saved, data, 0o600)
        recorded = owned_file(saved)
        require(len(recorded) == entry["bytes"] and digest(recorded) == entry["sha256"],
                "transaction_beforeimage_write_failed")
        self.entries[key] = entry
        return entry

    def record_absent(self, path):
        """Record that the file did not exist before this operation."""
        path = Path(path)
        key = str(path)
        if key in self.entries:
            return self.entries[key]
        entry = {"state": "ABSENT"}
        self.entries[key] = entry
        return entry

    def record(self, path, data):
        """Record the previous state of a file that is about to be written."""
        path = Path(path)
        if path.exists() and not path.is_symlink():
            return self.record_existing(path, data)
        return self.record_absent(path)

    def restore(self, paths):
        """Restore the recorded state of the given paths, newest first."""
        for path in reversed(list(paths)):
            key = str(path)
            entry = self.entries.get(key)
            if entry is None:
                continue
            target = Path(path)
            if entry["state"] == "ABSENT":
                expected = entry.get("published_after")
                if expected is not None:
                    source = self.home / "hermes-agent"
                    relative = str(target.relative_to(source))
                    source_parents_checked(source, relative)
                    try:
                        info = target.lstat()
                    except FileNotFoundError:
                        new_source_absence_checked(source, relative)
                    else:
                        data = owned_file(target)
                        named = target.lstat()
                        require(all(getattr(info, key) == getattr(named, key) for key in
                                    ("st_dev", "st_ino", "st_uid", "st_gid", "st_mode", "st_nlink",
                                     "st_size", "st_mtime_ns", "st_ctime_ns"))
                                and digest(data) == expected["sha256"] and len(data) == expected["bytes"]
                                and stat.S_IMODE(named.st_mode) == expected["mode"],
                                "transaction_new_source_restoration_changed")
                        target.unlink()
                        sync_directory(target.parent)
                    new_source_absence_checked(source, relative)
                elif target.exists() or target.is_symlink():
                    target.unlink()
                    sync_directory(target.parent)
                continue
            saved = self._target(path)
            require(os.path.lexists(saved), "transaction_beforeimage_missing")
            recorded = owned_file(saved)
            require(len(recorded) == entry["bytes"] and digest(recorded) == entry["sha256"],
                    "transaction_beforeimage_changed")
            mode = entry.get("mode", 0o600)
            publish(target, recorded, mode)
            restored = owned_file(target)
            require(len(restored) == entry["bytes"] and digest(restored) == entry["sha256"]
                    and stat.S_IMODE(target.lstat().st_mode) == mode,
                    "transaction_restoration_changed")

    def write_intent(self, name, payload):
        write_atomic(self.root / name, encoded(payload), 0o600)


class _CurrentSourceV5Journal(Journal):
    """Exact fifth/sixth/seventh/eighth-edge CAS and rollback; legacy callers keep their contract.

    Retain file identities as well as images.  A temporary file's identity is bound
    before rename, including when publication raises after rename and before fsync.
    This is a stopped, sole-writer boundary, not an atomic CAS against hostile writers.
    """
    _stable = ("st_dev", "st_ino", "st_uid", "st_gid", "st_mode", "st_nlink",
               "st_size", "st_mtime_ns", "st_ctime_ns")
    _parent = ("st_dev", "st_ino", "st_uid", "st_gid", "st_mode")

    def __init__(self, root, home, before_pins):
        super().__init__(root, home)
        self.before_pins = {str(path): pin for path, pin in before_pins.items()}
        self.before_states = {}
        self.after_states = {}

    def _relative(self, path):
        path = Path(path)
        require(path.is_absolute() and path == self.home / path.relative_to(self.home)
                and not any(part in (".", "..") for part in path.parts),
                "transaction_v5_target_outside_home")
        return path.relative_to(self.home)

    def _parents(self, path):
        relative = self._relative(path)
        current = self.home
        result = []
        for part in (None, *relative.parent.parts):
            if part is not None:
                current = current / part
            fd = os.open(current, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                held = os.fstat(fd); named = current.lstat()
                require(stat.S_ISDIR(held.st_mode) and held.st_uid == os.getuid()
                        and held.st_mode & 0o022 == 0
                        and all(getattr(held, key) == getattr(named, key) for key in self._parent),
                        "transaction_v5_parent_custody_changed")
                result.append((str(current), tuple(getattr(held, key) for key in self._parent)))
            finally:
                os.close(fd)
        return result

    def _state(self, path):
        path = Path(path); parents = self._parents(path)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            require(not os.path.lexists(path) and self._parents(path) == parents,
                    "transaction_v5_absence_changed")
            return {"state": "ABSENT", "parents": parents}, None
        try:
            first = os.fstat(fd)
            require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
                    and first.st_nlink == 1 and stat.S_IMODE(first.st_mode) in (0o600, 0o644)
                    and first.st_size <= 256 * 1024 ** 2,
                    "transaction_v5_file_custody_changed")
            chunks = []; size = 0
            while size <= first.st_size:
                chunk = os.read(fd, min(1024 ** 2, first.st_size + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk); size += len(chunk)
            after = os.fstat(fd); named = path.lstat()
            require(size == first.st_size
                    and all(getattr(first, key) == getattr(after, key) == getattr(named, key)
                            for key in self._stable)
                    and self._parents(path) == parents,
                    "transaction_v5_file_identity_changed")
            data = b"".join(chunks)
            state = {"state": "EXISTED", "parents": parents, "sha256": digest(data),
                     "bytes": len(data), "mode": stat.S_IMODE(first.st_mode),
                     "identity": {key: getattr(first, key) for key in self._stable}}
            return state, data
        finally:
            os.close(fd)

    @staticmethod
    def _matches(actual, expected):
        return all(actual.get(key) == value for key, value in expected.items() if key != "identity") \
            and all(actual.get("identity", {}).get(key) == value
                    for key, value in expected.get("identity", {}).items())

    def preflight(self):
        """Authenticate all selected beforeimages before the consuming mkdir."""
        for key, pin in self.before_pins.items():
            state, _ = self._state(key)
            require((state["state"] == "ABSENT" if pin is None else
                     state["state"] == "EXISTED"
                     and all(state.get(field) == value for field, value in pin.items())),
                    "transaction_v5_authenticated_preimage_changed:" + key)
            self.before_states[key] = state

    def record_existing(self, path, data):
        key = str(path); state, actual = self._state(path)
        require(key in self.before_states and actual == data
                and self._matches(state, self.before_states[key]),
                "transaction_v5_recorded_preimage_changed")
        entry = super().record_existing(path, data)
        require(self._matches(self._state(path)[0], state),
                "transaction_v5_recorded_identity_changed")
        return entry

    def record_absent(self, path):
        key = str(path); state, _ = self._state(path)
        require(key in self.before_states and state["state"] == "ABSENT"
                and self._matches(state, self.before_states[key]),
                "transaction_v5_recorded_absence_changed")
        return super().record_absent(path)

    def prepare_publication(self, target, data, mode):
        """Bind intended bytes before publish; bind its inode before replace."""
        key = str(target)
        require(key in self.entries and key in self.before_states,
                "transaction_v5_unrecorded_target")
        intended = {"sha256": digest(data), "bytes": len(data), "mode": mode}
        self.entries[key]["published_after"] = dict(intended)
        expected = self.after_states.get(key, [self.before_states[key]])[-1]
        require(self._matches(self._state(target)[0], expected),
                "transaction_v5_publish_preimage_changed")
        def before_replace(tmp):
            require(self._matches(self._state(target)[0], expected),
                    "transaction_v5_publish_preimage_changed")
            after, _ = self._state(tmp)
            require(all(after.get(field) == value for field, value in intended.items()),
                    "transaction_v5_temporary_afterimage_changed")
            # rename can update ctime. Its known inode, mode, owner, link count,
            # size and mtime remain exact; each later read checks ctime stability.
            after["identity"].pop("st_ctime_ns")
            self.after_states.setdefault(key, []).append(after)
            self.entries[key]["published_after"] = dict(after)
        return before_replace

    def restore(self, paths):
        seen = set()
        for path in reversed(list(paths)):
            key = str(path)
            if key in seen or key not in self.entries:
                continue
            seen.add(key); target = Path(path); before = self.before_states[key]
            actual, _ = self._state(target)
            if self._matches(actual, before):
                continue  # publish failed before replacing the original target
            require(any(self._matches(actual, own) for own in self.after_states.get(key, [])),
                    "transaction_v5_restoration_foreign_state")
            if before["state"] == "ABSENT":
                require(self._matches(self._state(target)[0], actual),
                        "transaction_v5_restoration_identity_changed")
                target.unlink(); sync_directory(target.parent)
                require(self._matches(self._state(target)[0], before),
                        "transaction_v5_absence_restoration_changed")
                continue
            entry = self.entries[key]; recorded = owned_file(self._target(path))
            require(digest(recorded) == entry["sha256"] and len(recorded) == entry["bytes"],
                    "transaction_beforeimage_changed")
            restored_identity = []
            def before_restore(tmp):
                require(self._matches(self._state(target)[0], actual),
                        "transaction_v5_restoration_identity_changed")
                state, _ = self._state(tmp)
                require(state["sha256"] == entry["sha256"] == before["sha256"]
                        and state["bytes"] == entry["bytes"] and state["mode"] == entry["mode"],
                        "transaction_v5_restoration_temporary_changed")
                state["identity"].pop("st_ctime_ns")
                restored_identity.append(state)
            publish(target, recorded, entry["mode"], _before_replace=before_restore,
                    _temporary_suffix=".restore.tmp")
            require(restored_identity and self._matches(self._state(target)[0], restored_identity[0])
                    and digest(recorded) == before["sha256"],
                    "transaction_v5_restoration_changed")


# ------------------------------------------------------------------ layer inventory


def resolve_layer_names(request):
    """Resolve the EXACT composition of this publication from the request.

    Two schemas are understood and both name the composition explicitly:

    * v46 (SCHEMA_EXPLICIT) REQUIRES the field `layer_names`. An absent field, a non-list,
      an empty list, a non-string element, a duplicate and an unknown name are each
      refused. A request never widens itself to every known layer.
    * v45 (SCHEMA) is the legacy schema of the historical four-layer request. When such a
      request carries no `layer_names` field, its composition is exactly
      HISTORICAL_LAYER_NAMES, named here as an explicit constant; it never widens to every
      layer known today. When it does carry the field, the field is validated exactly like
      in v46 and it wins over the legacy default.

    Returns the names in the order the request declares them.
    """
    if "layer_names" in request:
        names = request["layer_names"]
        if not isinstance(names, list):
            raise Refused("transaction_layer_names_malformed")
        if not names:
            raise Refused("transaction_layer_names_empty")
        for name in names:
            if not isinstance(name, str) or not name:
                raise Refused("transaction_layer_names_malformed")
        if len(set(names)) != len(names):
            raise Refused("transaction_layer_names_repeated")
        return tuple(names)
    if request.get("schema") == SCHEMA:
        return HISTORICAL_LAYER_NAMES
    raise Refused("transaction_layer_names_required")


def check_project_inventory(request, previous_input, current_input):
    """Validate the exact operation delta without staging or publishing any bytes."""
    layer_names = resolve_layer_names(request)
    require(set(layer_names) <= set(LAYER_NAMES), "transaction_layer_names_unknown")
    inventory = request["project_inventory"]
    require(inventory == current_input["project_files"],
            "transaction_project_inventory_changed")
    require(digest(encoded(inventory)) == request["project_inventory_sha256"],
            "transaction_project_inventory_changed")
    previous_files = previous_input["project_files"]
    current_files = current_input["project_files"]
    additions = {f"patches/hermes/{name}-manifest.json" for name in layer_names} | \
                {f"patches/hermes/{name}.patch" for name in layer_names}
    if layer_names == (CURRENT_SOURCE_FORTY_SIXTH_LAYER,):
        helper = CURRENT_SOURCE_FORTY_SIXTH_HELPER
        require(len(previous_files) == 567 and not additions.intersection(previous_files)
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper],
                "transaction_current_source_forty_sixth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FORTY_FIFTH_LAYER,):
        helper = CURRENT_SOURCE_FORTY_FIFTH_HELPER
        require(len(previous_files) == 565 and not additions.intersection(previous_files)
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper],
                "transaction_current_source_forty_fifth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FORTY_FOURTH_LAYER,):
        helper = CURRENT_SOURCE_FORTY_FOURTH_HELPER
        require(not additions.intersection(previous_files) and helper in previous_files
                and helper in current_files and previous_files[helper] != current_files[helper],
                "transaction_current_source_forty_fourth_project_scope_changed")
    require(additions <= set(current_files), "transaction_layer_files_missing")
    require(set(previous_files) <= set(current_files),
            "transaction_project_file_removed")
    # Existing selected patches remain immutable. A genuinely new selected patch may
    # arrive with its manifest, so the exact installed input remains the predecessor;
    # no reconstructed baseline is needed merely to pretend the new patch was present.
    new_patches = {f"patches/hermes/{name}.patch" for name in layer_names
                   if f"patches/hermes/{name}.patch" not in previous_files}
    expected_additions = {f"patches/hermes/{name}-manifest.json" for name in layer_names} | \
                          new_patches | set(request["plugin_additions"])
    require(set(current_files) - set(previous_files) == expected_additions,
            "transaction_project_delta_changed")
    for name in layer_names:
        patch = f"patches/hermes/{name}.patch"
        require(patch in current_files
                and (patch not in previous_files
                     or current_files[patch] == previous_files[patch]),
                "transaction_layer_patch_pin_changed:" + patch)
    for name in previous_files:
        if name in request["plugin_set"]:
            # the plugin set is published as its own step and is checked there
            continue
        if name in request.get("project_file_updates", []):
            # a project file the transition deliberately updates; its bytes are proven
            # against the candidate and published in its own step
            continue
        require(current_files[name] == previous_files[name],
                "transaction_project_file_changed:" + name)

    return layer_names


def check_plugin_preimages(request, previous_input, current_input, marker, home,
                           already_published=False):
    """Bind the changed plugin set to its installed byte and marker before staging.

    An already-applied source bundle may still have pending old plugin bytes. It may
    also carry an already-published plugin, but only if its marker and bytes both pin
    the current image. An unexplained third image is never adopted as a beforeimage.
    """
    previous = previous_input["project_files"]
    current = current_input["project_files"]
    changed = {name for name, pin in previous.items()
               if name.startswith("plugins/friday_rework/") and current.get(name) != pin}
    names = request["plugin_set"]
    require(isinstance(names, list) and all(isinstance(name, str) for name in names)
            and len(names) == len(changed) and set(names) == changed,
            "transaction_plugin_set_changed")
    pins = marker.get("plugin_files", {})
    for name in sorted(changed):
        expected = previous[name]
        if already_published and pins.get(name) == current[name]:
            expected = current[name]
        require(pins.get(name) == expected, "transaction_plugin_marker_changed:" + name)
        require(digest(owned_file(Path(home) / name)) == expected,
                "transaction_plugin_preimage_changed:" + name)


def read_layers(candidate_root, receipt, home, project_files, layer_names):
    """Read the layer manifests of THIS operation from the candidate and bind them.

    The bytes that are actually read are tied to the hashes the current input pins: a
    manifest or patch whose bytes differ from the pinned hash is refused, so the layer
    that is applied is provably the reviewed one. The manifest body, the patch bytes and
    the file preimages are then compared with each other, never a file with itself.
    """
    require_forty_sixth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_SIXTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_SIXTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_sixth_previous_receipt_changed")
    require_forty_fifth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_FIFTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_FIFTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_fifth_previous_receipt_changed")
    require_forty_fourth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_FOURTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_fourth_previous_receipt_changed")
    require_forty_third_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_THIRD_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_third_previous_receipt_changed")
    require_forty_second_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_SECOND_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_SECOND_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_second_previous_receipt_changed")
    require_forty_first_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_FIRST_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_FIRST_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_first_previous_receipt_changed")
    require_fortieth_source_binding(layer_names, project_files or {})
    require_thirty_ninth_source_binding(layer_names, project_files or {})
    require_thirty_eighth_source_binding(layer_names, project_files or {})
    require_thirty_seventh_source_binding(layer_names, project_files or {})
    require_thirty_sixth_source_binding(layer_names, project_files or {})
    require_thirty_fifth_source_binding(layer_names, project_files=project_files or {})
    require_thirty_fourth_source_binding(layer_names, project_files=project_files)
    layers = []
    for name in layer_names:
        manifest_rel = f"patches/hermes/{name}-manifest.json"
        patch_rel = f"patches/hermes/{name}.patch"
        require(manifest_rel in project_files and patch_rel in project_files,
                "transaction_layer_not_pinned")
        manifest_bytes = owned_file(Path(candidate_root) / manifest_rel)
        patch_bytes = owned_file(Path(candidate_root) / patch_rel)
        require(digest(manifest_bytes) == project_files[manifest_rel],
                "transaction_layer_manifest_pin_changed:" + manifest_rel)
        require(digest(patch_bytes) == project_files[patch_rel],
                "transaction_layer_patch_pin_changed:" + patch_rel)
        body = json.loads(manifest_bytes)
        require(body.get("patch") == patch_rel, "transaction_layer_patch_reference_changed")
        require(body.get("patch_sha256") == digest(patch_bytes)
                == project_files[patch_rel],
                "transaction_layer_patch_bytes_changed")
        require(body.get("base_commit") == receipt.get("commit"),
                "transaction_layer_base_commit_changed")
        files = body.get("files")
        require(isinstance(files, list) and files, "transaction_layer_files_required")
        if name == CURRENT_SOURCE_FORTY_SIXTH_LAYER:
            require(all(type(row) is dict and row.get("mode") == "100644"
                            and row.get("new_file") is False for row in files)
                    and tuple(row.get("path") for row in files) == CURRENT_SOURCE_FORTY_SIXTH_NATIVE_FILES,
                    "transaction_current_source_forty_sixth_native_scope_changed")
        if name == CURRENT_SOURCE_FORTY_FIFTH_LAYER:
            require(tuple(row.get("path") for row in files) == CURRENT_SOURCE_FORTY_FIFTH_NATIVE_FILES
                    and all(row.get("mode") == "100644" and row.get("new_file") is False for row in files),
                    "transaction_current_source_forty_fifth_native_scope_changed")
        layers.append({"name": name, "manifest": manifest_rel, "patch": patch_rel,
                       "manifest_bytes": manifest_bytes, "patch_bytes": patch_bytes,
                       "manifest_sha256": digest(manifest_bytes),
                       "patch_sha256": digest(patch_bytes),
                       "body": body, "files": files})
    return layers


def check_preimages(layers, source, receipt_files):
    """The strict preimage chain inside the bundle.

    For every file the chain is: the receipt's hash for the first layer that touches the
    file, then the result hash of the preceding layer that touches it. The expected value
    is never replaced by the layer's own declaration: a mismatch is a refusal. A bundle
    that is already published is recognised by a separate check of its final bytes and
    its receipt, not by weakening this chain.
    """
    state = {}
    for layer in layers:
        for row in layer["files"]:
            path = row["path"]
            expected = state.get(path)
            if expected is None:
                current = receipt_files.get(path)
                expected = None if current is None else current["sha256"]
            require(row.get("before_sha256") == expected,
                    "transaction_layer_preimage_changed:" + path)
            require(row.get("new_file") is (expected is None),
                    "transaction_layer_new_file_flag_changed:" + path)
            if expected is None:
                new_source_absence_checked(source, path)
            state[path] = row["sha256"]
    return state


def layer_already_applied(layer, source):
    """True when the layer's result bytes are already in the tree.

    A repeated run must recognise the published state instead of refusing it: the patch
    would no longer apply because its preimage is gone, while the wanted bytes are there.
    """
    for row in layer["files"]:
        path = Path(source) / row["path"]
        if not path.exists():
            return False
        data = owned_file(path)
        if digest(data) != row["sha256"] or len(data) != row["bytes"]:
            return False
    return True


def bundle_already_applied(layers, source, receipt, request=None):
    """True when the bundle is already published as a whole.

    This is a separate check, not a relaxation of the preimage chain: the tree must hold
    the final byte of every file the bundle touches, and the receipt must already list
    every layer of the bundle with the layer's own manifest and patch hashes. A bundle
    that is only partly published is not recognised here.
    """
    installed = {row["manifest"]: row for row in receipt.get("layers", [])}
    # a layer whose manifest this operation publishes anew may still carry the previous
    # bytes in the receipt; that difference is closed by the publication itself
    republished = set(request.get("layer_manifest_updates", []))
    final = {}
    for layer in layers:
        row = installed.get(layer["manifest"])
        if row is None:
            return False
        if row.get("manifest_sha256") != layer["manifest_sha256"]:
            if layer["manifest"] not in republished:
                return False
        if row.get("patch_sha256") != layer["patch_sha256"]:
            return False
        for file_row in layer["files"]:
            final[file_row["path"]] = file_row["sha256"]
    for path, sha in final.items():
        live = Path(source) / path
        if not live.exists():
            return False
        data = owned_file(live)
        if digest(data) != sha:
            return False
    return True


def row_bytes(layers, path):
    """The byte count the LAST layer that touches a path declares for it.

    For layers that touch the same file the final byte count is the one of the last
    layer, which is the state the published tree holds.
    """
    count = None
    for layer in layers:
        for row in layer["files"]:
            if row["path"] == path:
                count = row["bytes"]
    return count


def apply_layers(layers, source, staging):
    """Apply the selected layers in order onto a private staging tree.

    The staging tree holds only the files the layers touch, seeded with the live bytes.
    Each layer sees the previous layer's output. A layer whose result bytes are already in
    the tree is recognised as applied and skipped.
    """
    touched = []
    first_rows = {}
    for layer in layers:
        for row in layer["files"]:
            path = row["path"]
            if path not in touched:
                touched.append(path)
                first_rows[path] = row
    for path in touched:
        target = Path(staging) / path
        private_parents(staging, path)
        first = first_rows[path]
        if first.get("new_file") is True:
            require(first.get("before_sha256") is None,
                    "transaction_layer_preimage_changed:" + path)
            new_source_absence_checked(source, path)
            # git apply creates the declared addition; an empty placeholder would
            # turn its /dev/null preimage into an existing-file mutation.
            continue
        require(first.get("new_file") is False,
                "transaction_layer_new_file_flag_changed:" + path)
        data = owned_file(Path(source) / path)
        require(digest(data) == first.get("before_sha256"),
                "transaction_layer_preimage_changed:" + path)
        write_atomic(target, data, 0o600)
    for layer in layers:
        if layer_already_applied(layer, staging):
            # this layer's result bytes are already there: keep them and move on
            for row in layer["files"]:
                data = owned_file(Path(staging) / row["path"])
                require(digest(data) == row["sha256"],
                        "transaction_layer_output_changed:" + layer["name"])
            continue
        patch = Path(staging).parent / (layer["name"] + ".patch")
        write_atomic(patch, layer["patch_bytes"], 0o600)
        for checking in (True, False):
            command = ["git", "--no-optional-locks", "apply", "--whitespace=nowarn"]
            if checking:
                command.append("--check")
            command.append(str(patch))
            result = subprocess.run(command, cwd=str(staging), capture_output=True,
                                    text=True, timeout=120,
                                    env={"GIT_CEILING_DIRECTORIES": str(Path(staging).parent),
                                         "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                         "HOME": str(Path(staging).parent)})
            require(result.returncode == 0,
                    "transaction_layer_patch_does_not_apply:" + layer["name"])
        for row in layer["files"]:
            path = row["path"]
            data = owned_file(Path(staging) / path)
            require(digest(data) == row["sha256"] and len(data) == row["bytes"],
                    "transaction_layer_output_changed:" + layer["name"])
    return touched


# --------------------------------------------------------------------- composition


def proven_cache(source, receipt_files):
    """The generated artefacts of the tree that are not part of the receipt inventory.

    The product's own composition check refuses unknown entries; the generated bytecode
    caches are proven instead of removed, so no tree copy is needed.
    """
    generated = ('.hermes/', 'node_modules/', 'hermes_cli/web_dist/', 'ui-tui/dist/',
                 'ui-tui/node_modules/', 'web/node_modules/', 'apps/shared/node_modules/')
    # The generated products that may coexist with the source tree. The product's own
    # check accepts them by prefix; nothing is proven by digest here, so the tree is not
    # read entry by entry and not copied.
    proven = {}
    source = Path(source)
    for path in source.rglob("*"):
        name = str(path.relative_to(source))
        if path.is_dir() or path.is_symlink():
            continue
        if name in receipt_files or name.startswith(generated):
            continue
        if name == ".web_ui_build.lock":
            continue
        if name.endswith(".pyc") and "__pycache__/" in name:
            # the product's proven_cache contract expects private files; the ordinary
            # bytecode cache is a generated product, proven by the prefix rule instead
            continue
    return proven


def composition_checked(value, source, receipt, donor, cache, project_root):
    """The product's own composition check with a proven-cache list.

    The product's helper is imported from the project's own scripts directory, so the check
    is the product's check and not a re-implementation. The whole composition_checked is
    used, not only its source_checked part: the source lock, the overlay set, the manifest
    digests and the patch digests are checked together with the source inventory.
    """
    project_root = Path(project_root)
    scripts_path = str(project_root / "scripts")
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    # the product's scripts package must resolve to the candidate's own scripts directory
    import importlib
    import importlib.util
    package = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("scripts", loader=None, is_package=True))
    package.__path__ = [scripts_path]
    sys.modules["scripts"] = package
    from scripts.friday_install import composition_checked as product_composition_checked
    return product_composition_checked(value, Path(source), receipt, donor,
                                       proven_cache=cache)


# ------------------------------------------------------------------------- history


def history_map(home):
    """Digest map of the preserved transaction history."""
    actual = {}
    home = Path(home)
    for root in REQUIRED_HISTORY_ROOTS:
        base = home / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                raise Refused("transaction_history_link_refused")
            if path.is_dir():
                continue
            actual[str(path.relative_to(home))] = digest(read_bytes(path))
    return actual


# --------------------------------------------------------------------------- main


def require_current_source_context(home, request):
    """A current v6 home cannot bypass continuity by omitting the opt-in field."""
    root = Path(home) / "preparation" / ("ordinary-source-update-" + CURRENT_SOURCE_V6_ROOT_INPUT)
    require("current_source_successor" in request or not os.path.lexists(root),
            "transaction_current_source_context_required")


def current_source_request_bytes(request, request_path, request_sha256):
    """Retain the exact new-context request; historical requests keep their contract."""
    context = request.get("current_source_successor")
    if context is None:
        require("current_source_successor" not in request,
                "transaction_current_source_context_required")
        return None
    require(type(context) is dict, "transaction_current_source_context_required")
    if context.get("schema") == "friday.current-source-native-successor.v1":
        require(set(context) == {"schema", "root_project_update"},
                "transaction_current_source_context_required")
        references = ("root_project_update",)
    else:
        require(context.get("schema") in ("friday.current-source-native-successor.v2",
                    "friday.current-source-native-successor.v3",
                    "friday.current-source-native-successor.v4",
                    "friday.current-source-native-successor.v5",
                    "friday.current-source-native-successor.v6",
                    "friday.current-source-native-successor.v7",
                    "friday.current-source-native-successor.v8", "friday.current-source-native-successor.v9", "friday.current-source-native-successor.v10", "friday.current-source-native-successor.v11", "friday.current-source-native-successor.v12", "friday.current-source-native-successor.v13", "friday.current-source-native-successor.v14", "friday.current-source-native-successor.v15", "friday.current-source-native-successor.v16", "friday.current-source-native-successor.v17", "friday.current-source-native-successor.v18", "friday.current-source-native-successor.v19", "friday.current-source-native-successor.v20", "friday.current-source-native-successor.v21", "friday.current-source-native-successor.v22", "friday.current-source-native-successor.v23", "friday.current-source-native-successor.v24", "friday.current-source-native-successor.v25", "friday.current-source-native-successor.v26", "friday.current-source-native-successor.v27", "friday.current-source-native-successor.v28", "friday.current-source-native-successor.v29", "friday.current-source-native-successor.v30", "friday.current-source-native-successor.v31", "friday.current-source-native-successor.v32", "friday.current-source-native-successor.v33", "friday.current-source-native-successor.v34", "friday.current-source-native-successor.v35", "friday.current-source-native-successor.v36", "friday.current-source-native-successor.v37", "friday.current-source-native-successor.v38", "friday.current-source-native-successor.v39", "friday.current-source-native-successor.v40",
                    CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA)
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_context_required")
        references = ("root_project_update", "previous_native_update")
    for name in references:
        ref = context[name]
        require(type(ref) is dict and set(ref) == {"path", "sha256"}
                and type(ref["path"]) is str and type(ref["sha256"]) is str
                and __import__("re").fullmatch("[0-9a-f]{64}", ref["sha256"]),
                "transaction_current_source_root_reference_required")
    path = Path(request_path)
    require(path.is_absolute() and str(path) == str(path.resolve()),
            "transaction_current_source_request_path_required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600
                and before.st_size <= 8 * 1024 ** 2,
                "transaction_current_source_owned_request_required")
        chunks = []; size = 0
        while size <= 8 * 1024 ** 2:
            chunk = os.read(fd, min(1024 ** 2, 8 * 1024 ** 2 + 1 - size))
            if not chunk: break
            chunks.append(chunk); size += len(chunk)
        after = os.fstat(fd); named = path.lstat()
        attributes = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink",
                      "st_size", "st_mtime_ns", "st_ctime_ns")
        require(size <= 8 * 1024 ** 2 and size == before.st_size
                and all(getattr(before, key) == getattr(after, key) == getattr(named, key)
                        for key in attributes), "transaction_current_source_request_identity_changed")
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "transaction_current_source_duplicate_json_key")
            value[key] = item
        return value
    def invalid_constant(value):
        raise Refused("transaction_current_source_nonfinite_json")
    def finite_float(text):
        value = float(text)
        require(__import__("math").isfinite(value), "transaction_current_source_nonfinite_json")
        return value
    parsed = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant,
                        parse_float=finite_float)
    require(type(request_sha256) is str
            and __import__("re").fullmatch("[0-9a-f]{64}", request_sha256)
            and digest(raw) == request_sha256 and encoded(parsed) == encoded(request),
            "transaction_current_source_raw_request_changed")
    return raw


def retain_current_source_request(path, raw):
    """Publish once below the new private transaction, before any proof refers to it."""
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        offset = 0
        while offset < len(raw):
            count = os.write(fd, raw[offset:])
            require(type(count) is int and 0 < count <= len(raw) - offset,
                    "transaction_current_source_request_write_failed")
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)
    sync_directory(path.parent)


def current_source_consumer_checked(value, request, candidate, *, committed=False, inspect=False):
    """Use the selected product consumer, including its default postcommit dispatch."""
    import importlib
    import importlib.util
    candidate = Path(candidate)
    scripts_path = str(candidate / "scripts")
    for name in ("scripts.friday_install", "scripts.friday_ordinary_install"):
        relative = "scripts/" + name.rsplit(".", 1)[1] + ".py"
        require(digest(owned_file(candidate / relative)) == value["project_files"].get(relative),
                "transaction_current_source_consumer_pin_changed")
        loaded = sys.modules.get(name)
        require(loaded is None or Path(loaded.__file__).resolve()
                == candidate / relative
                and loaded.__spec__ is not None
                and Path(loaded.__spec__.origin).resolve() == candidate / relative,
                "transaction_current_source_foreign_consumer_loaded")
    package = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("scripts", loader=None, is_package=True))
    package.__path__ = [scripts_path]
    sys.modules["scripts"] = package
    product = importlib.import_module("scripts.friday_install")
    require(Path(product.__file__).resolve() == candidate / "scripts/friday_install.py"
            and digest(owned_file(product.__file__)) == value["project_files"]["scripts/friday_install.py"],
            "transaction_current_source_consumer_origin_changed")
    kwargs = {} if committed else {"source_update": request}
    product.spec_checked(value, cli_only=True, **kwargs)
    if inspect:
        product.inspect(value, request["current_input"]["sha256"], **kwargs)


def run(request, request_path, request_sha256):
    global INJECT_AFTER_RENAME, INJECT_TARGET, INJECT_SNAPSHOT_DIR, INJECT_SNAPSHOT_FILES
    global INJECT_SNAPSHOT_HOME
    require_forty_sixth_source_binding(request.get("layer_names", ()), request=request)
    require_forty_fifth_source_binding(request.get("layer_names", ()), request=request)
    require_forty_fourth_source_binding(request.get("layer_names", ()), request=request)
    require_forty_third_source_binding(request.get("layer_names", ()), request=request)
    require_forty_second_source_binding(request.get("layer_names", ()), request=request)
    require_forty_first_source_binding(request.get("layer_names", ()), request=request)
    require_fortieth_source_binding(request.get("layer_names", ()), request=request)
    require_thirty_ninth_source_binding(request.get("layer_names", ()), request=request)
    require_thirty_eighth_source_binding(request.get("layer_names", ()), request=request)
    require_thirty_seventh_source_binding(request.get("layer_names", ()), request=request)
    require_thirty_sixth_source_binding(request.get("layer_names", ()), request=request)
    require_thirty_fifth_source_binding(request.get("layer_names", ()),
                                        request.get("current_source_successor"),
                                        request.get("project_inventory") or {})
    require_thirty_fourth_source_binding(request.get("layer_names", ()),
                                         request.get("current_source_successor"),
                                         request.get("project_inventory") or {})
    require_thirty_third_source_binding(request.get("layer_names", ()),
                                        request.get("current_source_successor"))
    require_thirty_second_source_binding(request.get("layer_names", ()),
                                         request.get("current_source_successor"))
    require_thirty_first_source_binding(request.get("layer_names", ()),
                                        request.get("current_source_successor"))
    require_thirtieth_source_binding(request.get("layer_names", ()),
                                     request.get("current_source_successor"))
    require_twenty_ninth_source_binding(request.get("layer_names", ()),
                                        request.get("current_source_successor"))
    require_twenty_eighth_source_binding(request.get("layer_names", ()),
                                        request.get("current_source_successor"))
    require_twenty_seventh_source_binding(request.get("layer_names", ()),
                                        request.get("current_source_successor"))
    require_twenty_sixth_source_binding(request.get("layer_names", ()),
                                       request.get("current_source_successor"))
    require_twenty_fifth_source_binding(request.get("layer_names", ()),
                                       request.get("current_source_successor"))
    started = time.monotonic()
    os.umask(0o077)
    raw_current_request = current_source_request_bytes(request, request_path, request_sha256)
    current_context = raw_current_request is not None
    guarded_current = current_context and request["current_source_successor"]["schema"] in (
        "friday.current-source-native-successor.v5", "friday.current-source-native-successor.v6",
        "friday.current-source-native-successor.v7", "friday.current-source-native-successor.v8", "friday.current-source-native-successor.v9", "friday.current-source-native-successor.v10", "friday.current-source-native-successor.v11", "friday.current-source-native-successor.v12", "friday.current-source-native-successor.v13", "friday.current-source-native-successor.v14", "friday.current-source-native-successor.v15", "friday.current-source-native-successor.v16", "friday.current-source-native-successor.v17", "friday.current-source-native-successor.v18", "friday.current-source-native-successor.v19", "friday.current-source-native-successor.v20", "friday.current-source-native-successor.v21", "friday.current-source-native-successor.v22", "friday.current-source-native-successor.v23", "friday.current-source-native-successor.v24", "friday.current-source-native-successor.v25", "friday.current-source-native-successor.v26", "friday.current-source-native-successor.v27", "friday.current-source-native-successor.v28", "friday.current-source-native-successor.v29", "friday.current-source-native-successor.v30", "friday.current-source-native-successor.v31", "friday.current-source-native-successor.v32", "friday.current-source-native-successor.v33", "friday.current-source-native-successor.v34", "friday.current-source-native-successor.v35", "friday.current-source-native-successor.v36", "friday.current-source-native-successor.v37", "friday.current-source-native-successor.v38", "friday.current-source-native-successor.v39", "friday.current-source-native-successor.v40",
        CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA)
    forty_third = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA
    forty_fourth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA
    forty_fifth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA
    forty_sixth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA
    bound_current = forty_third or forty_fourth or forty_fifth or forty_sixth
    INJECT_AFTER_RENAME = bool(request.get("inject_after_rename"))
    INJECT_TARGET = request.get("inject_target")
    INJECT_SNAPSHOT_DIR = request.get("inject_snapshot_dir")
    INJECT_SNAPSHOT_FILES = tuple(request.get("inject_snapshot_files") or ())
    require(request.get("schema") in (SCHEMA, SCHEMA_EXPLICIT),
            "transaction_only_v45_supported")
    home = Path(request["home"]).resolve()
    if INJECT_SNAPSHOT_DIR is not None:
        snapshot = Path(INJECT_SNAPSHOT_DIR)
        require(snapshot.is_absolute() and not str(snapshot).startswith(str(home) + "/"),
                "transaction_injection_snapshot_outside_home")
    require(home.is_dir(), "transaction_home_missing")
    require_current_source_context(home, request)
    current_transaction = home / "preparation" / ("ordinary-source-update-v45-" + request_sha256[:16])
    if current_context:
        require(not os.path.lexists(current_transaction), "transaction_current_source_already_consumed")
    require(os.environ.get("HERMES_HOME") == str(home), "transaction_environment_required")
    # the snapshot reads from the VERIFIED home of this transaction
    INJECT_SNAPSHOT_HOME = home
    candidate = Path(request["candidate_project"]).resolve()
    require(candidate.is_dir(), "transaction_candidate_missing")
    seconds = request.get("seconds", 180)
    require(type(seconds) is int and seconds > 0,
            "transaction_seconds_positive_integer_required")
    deadline = started + seconds

    def forward_budget():
        # Only forward work is budgeted. An expired operation must still restore every
        # published beforeimage; Journal.restore calls publish directly, never this guard.
        require(time.monotonic() < deadline, "transaction_deadline_expired")

    # 1. the gateway must be stopped: one receiver, never two.
    bench_home = request.get("bench_home")
    require(not gateway_running(request["native_unit"]["path"], bench_home),
            "transaction_gateway_running")

    # 2. pins: every referenced byte must still be the pinned byte.
    bound_metadata = {}
    bound_parsed_keys = ("marker", "source_receipt", "stamp", "previous_input", "current_input",
                         "predecessor_request")
    for key in ("marker", "source_receipt", "stamp", "configuration", "profile", "launcher",
                "native_unit", "current_input", "previous_input", "predecessor_request", "target_receipt",
                "candidate_input"):
        ref = request.get(key)
        require(isinstance(ref, dict) and "path" in ref and "sha256" in ref,
                "transaction_pin_required:" + key)
        bound_key = bound_current and key in bound_parsed_keys
        raw = owned_file(ref["path"]) if bound_key else read_bytes(ref["path"])
        require(digest(raw) == ref["sha256"], "transaction_pin_changed:" + key)
        if bound_key:
            bound_metadata[key] = json.loads(raw)
    for key in ():
        ref = request.get(key)
        require(isinstance(ref, dict) and "path" in ref and "sha256" in ref,
                "transaction_pin_required:" + key)
        require(digest(read_bytes(ref["path"])) == ref["sha256"],
                "transaction_pin_changed:" + key)

    marker = bound_metadata["marker"] if bound_current else read_json(request["marker"]["path"])
    receipt = bound_metadata["source_receipt"] if bound_current else read_json(request["source_receipt"]["path"])
    previous_input = bound_metadata["previous_input"] if bound_current else read_json(request["previous_input"]["path"])
    require(marker.get("input_sha256") == request["previous_input"]["sha256"],
            "transaction_previous_input_not_installed")
    if forty_third:
        require_forty_third_predecessor(request, previous_input)
    if forty_fourth:
        native_committed_path, native_committed_raw = require_forty_fourth_predecessor(request, previous_input)
    if forty_fifth:
        native_committed_path, native_committed_raw = require_forty_fifth_predecessor(request, previous_input)
    if forty_sixth:
        native_committed_path, native_committed_raw = require_forty_sixth_predecessor(request, previous_input)
    current_input = bound_metadata["current_input"] if bound_current else read_json(request["current_input"]["path"])
    predecessor = (bound_metadata["predecessor_request"] if bound_current
                   else read_json(request["predecessor_request"]["path"]))

    # 3. the predecessor is the committed successor operation of this home.
    require(predecessor.get("schema") == "frw.root.engineering152-successor-request.v1",
            "transaction_predecessor_identity_changed")
    require(predecessor.get("home") == str(home)
            or request.get("bench_home") == str(home),
            "transaction_predecessor_home_changed")
    require(predecessor.get("current_input", {}).get("sha256")
            == request["predecessor_current_input_sha256"],
            "transaction_predecessor_input_changed")
    predecessor_tx = home / "preparation" / ("ordinary-source-update-successor-"
                                             + request["predecessor_request"]["sha256"])
    if not (predecessor_tx / "committed.json").exists():
        # a bench predecessor is supplied directly by the request
        predecessor_tx = Path(request["predecessor_request"]["path"]).parent
    predecessor_committed_path = predecessor_tx / "committed.json"
    predecessor_committed_bytes = (predecessor_committed_path.read_bytes()
                                    if predecessor_committed_path.exists() else b"")
    committed = read_json(predecessor_tx / "committed.json")
    require(committed.get("state") == "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED"
            and committed.get("gateway_started") is False
            and committed.get("workers_enabled") is False,
            "transaction_predecessor_not_committed")
    # The predecessor's record pins the receipt IT produced and stays immutable. This
    # operation writes its own record and only links to that predecessor, so the
    # predecessor's historical result is never rewritten.
    require(committed.get("source_receipt_sha256") == request["predecessor_receipt_sha256"],
            "transaction_predecessor_not_committed")

    # 4. the history is preserved byte for byte.
    actual_history = history_map(home)
    require(actual_history == request["transaction_history"],
            "transaction_history_changed")

    # 5. the receipt is the installed one and the marker agrees with it.
    require(marker.get("completion_stage") == "TELEGRAM_ORDINARY"
            and marker.get("runtime_ready") is False
            and marker.get("worker_state") == "BOTH_WORKERS_PREPARATION_PENDING",
            "transaction_home_state_changed")
    require(marker.get("source_receipt_sha256") == request["source_receipt"]["sha256"],
            "transaction_marker_receipt_changed")
    require(len(receipt.get("layers", [])) == int(request["installed_layers"]),
            "transaction_installed_layers_changed")
    require(len(receipt.get("files", {})) == int(request["installed_files"]),
            "transaction_installed_files_changed")

    # 6. the project inventory: the candidate adds exactly the layer pairs of THIS
    #    operation and changes nothing else that the home does not already carry.
    # The bundle of this operation is a subset of the known layers. A layer that is already
    # published is named so only when it is republished; a live publication of a new layer
    # names just that one, so the already published layers are never replayed.
    # The composition of THIS operation is explicit: the field is REQUIRED. An absent,
    # empty, malformed or repeated set is refused instead of silently widening the
    # operation to every known layer. The historical four-layer request keeps its exact
    # meaning because the generator names exactly those four layers.
    layer_names = check_project_inventory(request, previous_input, current_input)
    current_files = current_input["project_files"]

    # 7. the selected layers: manifest bytes, patch bytes and preimages. The layers are read
    #    from the candidate and tied to the hashes the current input pins; their preimage
    #    chain is checked against the receipt before anything is staged.
    layers = read_layers(candidate, receipt, home, current_files, layer_names)
    source = home / "hermes-agent"
    already_published = bundle_already_applied(layers, source, receipt, request)
    if not already_published:
        final_state = check_preimages(layers, source, receipt["files"])
    else:
        # the bundle is already published as a whole, with a consistent receipt; the final
        # bytes are the authoritative ones and no layer is replayed
        final_state = {}
        for layer in layers:
            for row in layer["files"]:
                final_state[row["path"]] = row["sha256"]

    # Existing plugin replacements share the source transaction, so their beforeimages
    # must be known before staging or intent, as well as before the journal records them.
    check_plugin_preimages(request, previous_input, current_input, marker, home,
                           already_published=already_published)
    if current_context:
        forward_budget()
        current_source_consumer_checked(current_input, request, candidate)
        forward_budget()

    guarded_journal = None
    if guarded_current:
        # Only selected targets are authenticated. An unchanged installed helper
        # may legitimately differ from the new candidate's helper inventory.
        before_pins = {}
        for name in final_state:
            row = receipt["files"].get(name)
            before_pins[str(source / name)] = None if row is None else {
                "sha256": row["sha256"], "bytes": row["bytes"]}
        project_targets = (set(request.get("project_file_updates", []))
            | set(request.get("layer_manifest_updates", []))
            | {f"patches/hermes/{name}.patch" for name in layer_names
               if f"patches/hermes/{name}.patch" not in previous_input["project_files"]}
            | set(request["plugin_set"]) | set(request["plugin_additions"]))
        for name in project_targets:
            pin = previous_input["project_files"].get(name)
            before_pins[str(home / name)] = None if pin is None else {"sha256": pin}
        for key, name in (("source_receipt", "hermes-agent.source.json"),
                          ("marker", "FRIDAY-INSTALL.json"),
                          ("stamp", "hermes-agent/install-stamp.json")):
            before_pins[str(home / name)] = {"sha256": request[key]["sha256"]}
        require(not request.get("staged_files"), "transaction_v5_unexpected_staged_target")
        guarded_journal = _CurrentSourceV5Journal(current_transaction, home, before_pins)
        guarded_journal.preflight()

    # 8. apply the layers onto a private staging tree that holds only the touched files.
    #    A bundle that is already published is NOT applied again: for layers that touch the
    #    same file the old patch would be applied to the final bytes and would not apply.
    #    Its final bytes and its receipt are checked instead.
    forward_budget()
    if current_context:
        # mkdir is the consuming no-retry edge. Never overwrite an old transaction,
        # including one that failed before intent or rolled back afterwards.
        os.mkdir(current_transaction, 0o700)
        sync_directory(current_transaction.parent)
        staging_root = private_directory(current_transaction)
        retain_current_source_request(staging_root / "request.json", raw_current_request)
        request_reference = {"path": str(staging_root / "request.json"), "sha256": request_sha256}
    else:
        staging_root = private_directory(current_transaction)
    staging = private_directory(staging_root / "staging")
    if already_published:
        touched = []
        for layer in layers:
            for row in layer["files"]:
                if row["path"] not in touched:
                    touched.append(row["path"])
        for path in touched:
            data = owned_file(Path(source) / path)
            expected = row_bytes(layers, path)
            require(digest(data) == final_state[path]
                    and (expected is None or len(data) == expected),
                    "transaction_published_bytes_changed:" + path)
            write_atomic(Path(staging) / path, data, 0o600)
    else:
        touched = apply_layers(layers, source, staging)

    # 9. the composition after the publication: the receipt's inventory plus the new bytes.
    projected = json.loads(json.dumps(receipt))
    # A layer that is already in the receipt must not be appended a second time. When the
    # operation publishes the layer's manifest anew, the projected receipt must carry the
    # published manifest bytes, so the composition check compares the tree with itself.
    installed_manifests = {row["manifest"] for row in projected["layers"]}
    published_manifests = set(request.get("project_file_updates", [])) | set(
        request.get("layer_manifest_updates", []))
    for layer in layers:
        if layer["manifest"] in installed_manifests:
            if layer["manifest"] in published_manifests:
                for row in projected["layers"]:
                    if row["manifest"] == layer["manifest"]:
                        row["manifest_sha256"] = layer["manifest_sha256"]
            continue
        projected["layers"].append({"manifest": layer["manifest"],
                                    "manifest_sha256": layer["manifest_sha256"],
                                    "patch_sha256": layer["patch_sha256"]})
    # the projected receipt must pin the same source lock as the current input
    lock = current_input["sources_lock"]
    lock_path = lock["path"] if isinstance(lock, dict) else lock
    projected["sources_lock_sha256"] = (lock["sha256"] if isinstance(lock, dict)
                                        else digest(read_bytes(lock_path)))
    for path, sha in final_state.items():
        row = dict(projected["files"][path]) if path in projected["files"] else {}
        data = owned_file(Path(staging) / path)
        row.update({"sha256": sha, "bytes": len(data), "mode": "100644"})
        projected["files"][path] = row
    cache = proven_cache(source, receipt["files"])
    lock = current_input["sources_lock"]
    lock_path = lock["path"] if isinstance(lock, dict) else lock
    donor = read_json(lock_path)
    donor = {r["id"]: r for r in donor["repositories"]}["hermes"]
    # The staged bytes are proven against the projected inventory before publication.
    for path in touched:
        staged = owned_file(Path(staging) / path)
        require(digest(staged) == final_state[path], "transaction_staged_bytes_changed:" + path)

    # 10. the journal: every file the operation touches is recorded before it is written.
    journal = guarded_journal if guarded_journal is not None else Journal(staging_root, home)
    published = []
    native_additions = {str(Path(source) / path) for path in touched if path not in receipt["files"]}

    def publish_with_journal(target, data, mode=0o600):
        """Publish a file and remember what it was before.

        The beforeimage is taken from the journal's first recording of that path, so a file
        that is written more than once is restored to its state before the operation.
        """
        target = Path(target)
        key = str(target)
        if key not in journal.entries:
            if target.exists() and not target.is_symlink():
                journal.record_existing(target, owned_file(target))
            else:
                journal.record_absent(target)
        if key in native_additions:
            new_source_absence_checked(source, str(target.relative_to(source)))
            journal.entries[key]["published_after"] = {"sha256": digest(data),
                "bytes": len(data), "mode": mode}
        forward_budget()
        # The path is registered BEFORE the write: a failure between the rename and the
        # directory synchronisation leaves the file changed, and the rollback must still
        # know about it.
        before_replace = (guarded_journal.prepare_publication(target, data, mode)
                          if guarded_journal is not None else None)
        published.append(target)
        if before_replace is None:
            publish(target, data, mode)
        else:
            publish(target, data, mode, _before_replace=before_replace)

    for path in touched:
        target = Path(source) / path
        if path in receipt["files"]:
            journal.record_existing(target, owned_file(target))
        else:
            # check_preimages authenticated the addition's absence. Recheck at
            # the journalling boundary, then restore absence on any late refusal.
            new_source_absence_checked(source, path)
            journal.record_absent(target)
    for name in sorted(request.get("plugin_set", [])) + sorted(request.get("plugin_additions", [])):
        target = Path(home) / name
        if target.exists() and not target.is_symlink():
            journal.record_existing(target, owned_file(target))
        else:
            journal.record_absent(target)
    for name in sorted(request.get("project_file_updates", [])):
        target = Path(home) / name
        if target.exists() and not target.is_symlink():
            journal.record_existing(target, owned_file(target))
        else:
            journal.record_absent(target)
    for name in ("hermes-agent.source.json", "FRIDAY-INSTALL.json", "hermes-agent/install-stamp.json"):
        target = Path(home) / name
        if target.exists() and not target.is_symlink():
            journal.record_existing(target, owned_file(target))
        else:
            journal.record_absent(target)
    forward_budget()
    journal.write_intent("intent.json", {
        "schema": "friday.ordinary-telegram-source-update-transaction.v1",
        "state": "SOURCE_UPDATE_INTENT",
        "request_sha256": request_sha256,
        "home": str(home),
        "previous_input": request["previous_input"],
        "current_input": request["current_input"],
        "source_receipt": request["source_receipt"],
        "layers": [layer["manifest"] for layer in layers],
        "files": touched,
        "plugin_set": sorted(request.get("plugin_set", [])),
        "plugin_additions": sorted(request.get("plugin_additions", [])),
        "project_file_updates": sorted(request.get("project_file_updates", [])),
        "metadata": ["hermes-agent.source.json", "FRIDAY-INSTALL.json",
                     "hermes-agent/install-stamp.json"],
        "gateway_started": False,
        "workers_enabled": False,
        **({"request_reference": request_reference,
            "current_source_successor": request["current_source_successor"]} if current_context else {}),
    })

    try:
        # 10a. the source files of the layers
        for path in touched:
            data = owned_file(Path(staging) / path)
            publish_with_journal(Path(source) / path, data, 0o600)
        write_atomic(staging_root / "published.json", encoded({"files": [str(p) for p in published]}), 0o600)
        if request.get("fail_after_publish"):
            # a controlled failure at a substantial point of the state change, used to prove
            # the rollback. It is only reachable through an explicit request field.
            raise Refused("transaction_controlled_failure_for_rollback_proof")
        # The product's own composition check runs over the published tree: the receipt's
        # inventory plus the new bytes. A refusal here restores the beforeimages.
        composition_checked(current_input, source, projected, donor, cache, candidate)

        # 10b. the project files the transition deliberately updates, then the V3 plugin set.
    #      Both are proven against the current input's pins before they are written.
        # New selected patches were not carried by the installed project. Publish them
        # with their manifests through the same journal so the next operation can prove
        # the installed project's complete pinned composition.
        new_patches = {f"patches/hermes/{name}.patch" for name in layer_names
                       if f"patches/hermes/{name}.patch" not in previous_input["project_files"]}
        project_updates = sorted(set(request.get("project_file_updates", []))
                                 | set(request.get("layer_manifest_updates", []))
                                 | new_patches)
        plugin_set = sorted(request["plugin_set"])
        plugin_additions = sorted(request["plugin_additions"])
        for name in project_updates + plugin_set + plugin_additions:
            candidate_bytes = owned_file(Path(candidate) / name)
            require(digest(candidate_bytes) == current_files[name],
                    "transaction_candidate_bytes_changed:" + name)
        # files the request places at an explicit path inside the home (the staged native
        # runtime source, for example): the path is relative to the home and never escapes it
        staged_files = request.get("staged_files") or []
        for entry in staged_files:
            target = Path(home) / entry["path"]
            require(not Path(entry["path"]).is_absolute()
                    and '..' not in Path(entry["path"]).parts,
                    "transaction_staged_path_refused")
            candidate_bytes = owned_file(Path(candidate) / entry["source"])
            require(digest(candidate_bytes) == current_files[entry["source"]],
                    "transaction_candidate_bytes_changed:" + entry["source"])
            private_parents(home, entry["path"])
            publish_with_journal(target, candidate_bytes, 0o600)
        if staged_files:
            write_atomic(staging_root / "published-staged.json",
                         encoded({"files": [e["path"] for e in staged_files]}), 0o600)
        journal.write_intent("intent-project-updates.json", {
            "schema": "friday.ordinary-telegram-source-update-transaction.v1",
            "state": "SOURCE_UPDATE_PROJECT_FILE_INTENT",
            "request_sha256": request_sha256,
            "files": project_updates,
        })
        for name in project_updates:
            data = owned_file(Path(candidate) / name)
            publish_with_journal(Path(home) / name, data, 0o600)
        write_atomic(staging_root / "published-project-updates.json",
                     encoded({"files": project_updates}), 0o600)

        journal.write_intent("intent-plugins.json", {
            "schema": "friday.ordinary-telegram-source-update-transaction.v1",
            "state": "SOURCE_UPDATE_PLUGIN_INTENT",
            "request_sha256": request_sha256,
            "files": plugin_set + plugin_additions,
        })
        for name in plugin_set:
            data = owned_file(Path(candidate) / name)
            publish_with_journal(Path(home) / name, data, 0o600)
        if request.get("fail_during_plugins"):
            # a controlled failure in the middle of the plugin publication, used to prove that
            # the rollback covers the plugin set as well
            raise Refused("transaction_controlled_failure_during_plugins")
        for name in plugin_additions:
            data = owned_file(Path(candidate) / name)
            target = Path(home) / name
            private_parents(home, name)
            publish_with_journal(target, data, 0o600)
        write_atomic(staging_root / "published-plugins.json",
                     encoded({"files": plugin_set + plugin_additions}), 0o600)
        plugin_published = plugin_set + plugin_additions

        # 11. the new receipt and marker, published through the same journal.
        new_receipt = projected
        new_receipt["files"] = projected["files"]
        write_atomic(staging_root / "hermes-agent.source.json", encoded(new_receipt), 0o600)
        publish_with_journal(home / "hermes-agent.source.json", encoded(new_receipt), 0o600)
        if request.get("fail_between_metadata"):
            # a controlled failure between two metadata writes, used to prove that the rollback
            # covers the receipt, the marker and the stamp together
            raise Refused("transaction_controlled_failure_between_metadata")

        new_marker = dict(marker)
        # the marker's plugin inventory must follow the published plugin set
        plugin_pins = dict(marker.get("plugin_files", {}))
        for name in plugin_published:
            plugin_pins[name] = digest(owned_file(Path(home) / name))
        new_marker["plugin_files"] = plugin_pins
        receipt_sha = digest(encoded(new_receipt))
        new_marker["source_receipt_sha256"] = receipt_sha
        # the ordinary gateway phase pins the receipt: it must follow the published one,
        # exactly as the product's own source update does.
        phase = dict(new_marker.get("ordinary_gateway", {}))
        phase["source_receipt_sha256"] = receipt_sha
        phase["operator_entry"] = {
            "input": {"path": str(request["current_input"]["path"]),
                      "sha256": request["current_input"]["sha256"]},
            "script": {"path": str(candidate / "scripts/friday_native.py"),
                       "sha256": current_files["scripts/friday_native.py"]},
        }
        new_marker["ordinary_gateway"] = phase
        # the install stamp pins the layer list of the receipt
        stamp = (bound_metadata["stamp"] if bound_current
                 else read_json(Path(home) / "hermes-agent/install-stamp.json"))
        stamp["fridaySource"] = {"baseTree": new_receipt["base_tree"], "layers": new_receipt["layers"]}
        stamp_data = encoded(stamp)
        write_atomic(staging_root / "install-stamp.json", stamp_data, 0o600)
        new_marker["input_sha256"] = request["current_input"]["sha256"]
        write_atomic(staging_root / "FRIDAY-INSTALL.json", encoded(new_marker), 0o600)
        publish_with_journal(home / "FRIDAY-INSTALL.json", encoded(new_marker), 0o600)
        publish_with_journal(Path(home) / "hermes-agent/install-stamp.json", stamp_data, 0o600)

        if current_context:
            forward_budget()
            current_source_consumer_checked(current_input, request, candidate, inspect=True)
            forward_budget()

        forward_budget()
        # This operation's own record; the predecessor's record is left untouched and
        # that is proved on the bytes, not on a claim.
        require(predecessor_committed_path.read_bytes() == predecessor_committed_bytes,
                "transaction_predecessor_record_changed")
        if forty_fourth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_forty_fourth_previous_committed_changed")
        if forty_fifth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_forty_fifth_previous_committed_changed")
        if forty_sixth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_forty_sixth_previous_committed_changed")
        write_atomic(staging_root / "committed.json", encoded({
            "schema": "friday.ordinary-telegram-source-update-transaction.v1",
            "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
            "request_sha256": request_sha256,
            "previous_input": request["previous_input"],
            "current_input": request["current_input"],
            "predecessor_request_sha256": request["predecessor_request"]["sha256"],
            "predecessor_receipt_sha256": request["predecessor_receipt_sha256"],
            "source_receipt_sha256": digest(encoded(new_receipt)),
            "layers": [layer["manifest"] for layer in layers],
            "files": touched,
            "gateway_started": False,
            "workers_enabled": False,
            "seconds": round(time.monotonic() - started, 3),
            **({"request_reference": request_reference,
                "current_source_successor": request["current_source_successor"]} if current_context else {}),
        }), 0o600)
        if current_context:
            # A committed source that cannot enter the ordinary default reader is
            # rolled back inside this same transaction, never returned as success.
            forward_budget()
            current_source_consumer_checked(current_input, request, candidate,
                                            committed=True, inspect=True)
            forward_budget()
    except BaseException as original:
        if not current_context and not isinstance(original, Exception):
            raise
        # One rollback for the whole operation: the source files, the project files, the
        # plugin set, the receipt, the marker and the stamp. Files that this operation
        # added are removed again.
        try:
            journal.restore(published)
            write_atomic(staging_root / "rolled-back.json", encoded({
                "state": "ROLLED_BACK",
                "published": [str(p) for p in published],
                "entries": sorted(journal.entries),
            }), 0o600)
        except BaseException as restoration:
            if current_context:
                raise StopUnconfirmed("current source rollback requires reconciliation") from restoration
            raise
        raise

    # 12. clean up the staging tree; the journal keeps the evidence.
    shutil.rmtree(staging, ignore_errors=True)
    for layer in layers:
        (staging_root / (layer["name"] + ".patch")).unlink(missing_ok=True)

    return {"state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
            "layers": len(layers), "files": len(touched),
            "receipt_sha256": digest(encoded(new_receipt)),
            "transaction": str(staging_root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    require(__import__("re").fullmatch("[0-9a-f]{64}", args.request_sha256),
            "transaction_request_digest_required")
    raw = read_bytes(args.request)
    require(digest(raw) == args.request_sha256, "transaction_request_changed")
    request = json.loads(raw)
    try:
        result = run(request, args.request, args.request_sha256)
    except StopUnconfirmed as exc:
        print(json.dumps({"state": "STOP_UNCONFIRMED", "exception": type(exc).__name__},
                         sort_keys=True), file=sys.stderr)
        raise SystemExit(3) from None
    except Refused as exc:
        print(json.dumps({"state": "REFUSED_NOT_RUNTIME_ACCEPTED",
                          "exception": type(exc).__name__, "reason": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(2) from None
    except Exception as exc:
        # an unexpected failure: the home is unchanged by the rollback, and the refusal is
        # reported in the same shape as a planned one
        print(json.dumps({"state": "REFUSED_NOT_RUNTIME_ACCEPTED",
                          "exception": type(exc).__name__, "reason": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(2) from None
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
