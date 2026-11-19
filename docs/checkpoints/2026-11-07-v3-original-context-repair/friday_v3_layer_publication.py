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
    'epub-receipt-and-spreadsheet-report-evidence-after-source244',
    'epub-preserving-archive-repack-after-source245',
    'stock-xls-read-and-utc-ics-create-after-source246',
    'xlsx-create-inline-text-after-source247',
    'scope-ods-chart-calc-linked-after-source248',
    'calc-saved-ods-chart-read-after-source249',
    'xls-calc-multisheet-read-after-source250',
    'xls-literal-create-and-preserving-edit-after-source251',
    'ruled-png-whole-grid-and-word-macro-guidance-after-source252',
    'pptx-opc-default-namespace-after-source253',
    'xps-oxps-default-namespace-after-source254',
    'pptx-template-opc-default-namespace-after-source255',
    'pptx-template-inherited-title-fit-after-source256',
    's13-owned-jpeg-photo-and-vision-privacy-after-source257',
    'xls-biff8-number-preserving-edit-after-source258',
    'odp-chart-edit-with-owned-capture-after-source259',
    'pdf-text-to-editable-docx-after-source260',
    'pdf-ocr-to-editable-docx-after-source261',
    'ocr-omission-disclosure-after-source262',
    'passive-layered-pdf-redaction-after-source263',
    'telegram-tiff-document-ingress-after-source264',
    'structured-file-password-containment-after-source265',
    'telegram-image-delivery-provenance-after-source266',
    'pdf-ocr-ambiguous-total-disclosure-after-source267',
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

# Exact Source245 layer and the closed Core244 predecessor it extends.
CURRENT_SOURCE_FORTY_SEVENTH_LAYER = 'epub-receipt-and-spreadsheet-report-evidence-after-source244'
CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v47'
CURRENT_SOURCE_FORTY_SEVENTH_MANIFEST_SHA256 = 'f5dd20e38ab2143d575b72f7bb9e20b43d956b25a33e4916426b49fea6ce3116'
CURRENT_SOURCE_FORTY_SEVENTH_PATCH_SHA256 = '81135b743e8e7504547a394db3d74062a069fe42b27b64feaad889526fdb6400'
CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_REQUEST_SHA256 = '2aabfefb1c17586c5caf82087f80fa5caca2ba60ce9ab27fd85d412264b33bc2'
CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_COMMITTED_SHA256 = 'fc0c26ab4b7fff57e235bc54e587195e3da6a311250f0a95a9b739de60557538'
CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_RECEIPT_SHA256 = 'e9e3bd25bfb376f8d6f32f0a4919efafeb71bdaa254255b06338735d2f1cfe6c'
CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_MARKER_SHA256 = 'eedbbb4f7af2b0b836b368d27398c0041103784be6e7730f8dc244d3e4b475d2'
CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_STAMP_SHA256 = '204ff18860ff8eb4d555b793ed9ee2831430ae4229682fddd97d20f664bededf'
CURRENT_SOURCE_FORTY_SEVENTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FORTY_SEVENTH_NATIVE_FILES = (
    'hermes_cli/friday_prompt_scope.py',
    'hermes_cli/friday_schema_guidance.py',
    'tools/scoped_epub_write.py',
)

# Exact Source246 layer and the closed Core245 predecessor it extends.
CURRENT_SOURCE_FORTY_EIGHTH_LAYER = 'epub-preserving-archive-repack-after-source245'
CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v48'
CURRENT_SOURCE_FORTY_EIGHTH_MANIFEST_SHA256 = '40073b434f80e896a153e8f0a4730f7ca044fcd909620c253e59ffb3470f0851'
CURRENT_SOURCE_FORTY_EIGHTH_PATCH_SHA256 = '088ca0846e3aa2e26a7092c3246d7ba234690b41269fd43c7d7fccb5461662ad'
CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_REQUEST_SHA256 = '2e918b571c993a128cc8b2ce2abce251249f15cdf0ca72fc5914efc7068eb384'
CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_COMMITTED_SHA256 = 'fe3aa185b884d436915fc4b45a5ca49d39f2799fb61052b06e9df16da23c8b64'
CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_RECEIPT_SHA256 = '1cb5cf73e758714335a69a660ed3a52af032b105bfdbf64b77f6582b4e8dfecb'
CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_MARKER_SHA256 = 'fe7398db1c79e255a3bfe8d1eefc49bc45a2973045dfc1deb751d172285a9b66'
CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_STAMP_SHA256 = '764e1a523b8663cef589e1ec921aa7c9b9724f95a55f3d40ee90c29ed75acfd2'
CURRENT_SOURCE_FORTY_EIGHTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FORTY_EIGHTH_NATIVE_FILE = {
    'before_sha256': '83ec7a125e81d5f9838a061298cf90a7cb9e5a5c6867c42d8585b27f7832bc61',
    'bytes': 28884,
    'mode': '100644',
    'new_file': False,
    'path': 'tools/scoped_epub_write.py',
    'sha256': 'd1156e633de6256d802ab4a1d33dda4cbb51ecc17b6a006fd9b826ca2ba9962b',
}


# Exact Source247 layer and the closed Core246 predecessor it extends.
CURRENT_SOURCE_FORTY_NINTH_LAYER = 'stock-xls-read-and-utc-ics-create-after-source246'
CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v49'
CURRENT_SOURCE_FORTY_NINTH_MANIFEST_SHA256 = 'b94fe9a49368284fdfdeee50d7bf4d45ae5a71e714765cdb12eef428812ae7c9'
CURRENT_SOURCE_FORTY_NINTH_PATCH_SHA256 = 'cc9e83c4fabd512b0996ae8364e40279fc8e30c03b957a5eeb07095173ad2f84'
CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_REQUEST_SHA256 = 'f3bb8a281114710db7c67be706345097dd01a67d71567a89c1ba0adaa65a9336'
CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_COMMITTED_SHA256 = 'aed3108aaad3436f094ec04ec08f1b68138bb2616d5cb6ead3d9b89fd9bb978f'
CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_RECEIPT_SHA256 = '1d4ee871772b6438f7b34cac5d2ac65d45039d43cf37e91a1b1a5220964b68a3'
CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_MARKER_SHA256 = 'be20ebad178548aa8cf836bd5bb5d18cb1674ac5d516e854e369fc09d016c59b'
CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_STAMP_SHA256 = 'bfb48d1db144f5aee85c7c4fe5d8dc0ae6fdaece6a15f6564c4d4491aac1a1de'
CURRENT_SOURCE_FORTY_NINTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FORTY_NINTH_NATIVE_FILES = (
    {
        'before_sha256': '2ae3806e55ee06489d7a30012306c5df925d2c348bb8ac2796b1725d5fd94f82',
        'bytes': 136606,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': 'd70b18c97386d471632314bc1b6111f3262b686163136d3b9d705d0d40fdd023',
    },
    {
        'before_sha256': '9836481a3d493e349fdc5ada2b89991bd13324b832e716b40e7520cc56edb725',
        'bytes': 11558,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_communication.py',
        'sha256': '8c2381a7dde5431fa48a5100ccde123d871d57a78fe24c05fcee13f97a7baac9',
    },
    {
        'before_sha256': '9c53ab219f23738a2a77a12466249b319850a5967f22c240b837a4ed833b8648',
        'bytes': 206886,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': 'a0ea4a26696c8801fac9aa81be70041c740368878d82bcf0a40d5878d3c6c51d',
    },
    {
        'before_sha256': '84e7fcb33873b9d6008bf28c505b57a1f1a285bd6552da3913062ede5bea23f4',
        'bytes': 36353,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_communication.py',
        'sha256': '3fd06f2588c16f17d236d495661b63c57634d35f9e05ce89d6d8a77a6f44dfa7',
    },
    {
        'before_sha256': 'fb22bfc7d9f494ab2845eb64783a9186dd43b9085f25d0105d8c5c4b0ee8c43b',
        'bytes': 31342,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_xls.py',
        'sha256': 'ef4bd9f96fa951582542084bcbc9955324a28fa6e5faa3b086313e1d712304b1',
    },
)

# Exact Source248 layer and the closed Core247 predecessor it extends.
CURRENT_SOURCE_FIFTIETH_LAYER = 'xlsx-create-inline-text-after-source247'
CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v50'
CURRENT_SOURCE_FIFTIETH_MANIFEST_SHA256 = '6a3ea3e0e09c488cf00dcbd0c6db5fb24d42e8e1fef06e24d55fb6ce8dc6558e'
CURRENT_SOURCE_FIFTIETH_PATCH_SHA256 = '1e608ee643f834fc2603bf6b005b40e329aaef891b35f3cfbd18b703e40d1608'
CURRENT_SOURCE_FIFTIETH_PREVIOUS_REQUEST_SHA256 = 'a20e02dc491e819f9a77c69dca1f77fa1496f1503b672d6de12b98e6b5e35f70'
CURRENT_SOURCE_FIFTIETH_PREVIOUS_COMMITTED_SHA256 = 'dc6641d9b69324cbb834f8733f3ce82fadbd0068740cf4db09128a1a8e0f2a04'
CURRENT_SOURCE_FIFTIETH_PREVIOUS_RECEIPT_SHA256 = '33dcef738f41002c97014fc70b098c68ad0a5067c074db4dad9361111ea77ee0'
CURRENT_SOURCE_FIFTIETH_PREVIOUS_MARKER_SHA256 = 'df154930594aa50f5a2abbbb0da3edd569eaf2d35cde2c9d40cdfcc6a8af3c88'
CURRENT_SOURCE_FIFTIETH_PREVIOUS_STAMP_SHA256 = '831c27409fe94a393c6927628a387d0f5954f43d1a5bd0d2ab5b5593e66abc25'
CURRENT_SOURCE_FIFTIETH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTIETH_NATIVE_FILE = {
    'before_sha256': 'ee3da2dbb32d66d253c0fc374294496b883379c6ae30658bd3fa4a00499d3db0',
    'bytes': 43929,
    'mode': '100644',
    'new_file': False,
    'path': 'hermes_cli/friday_workspace_xlsx_table.py',
    'sha256': '96bfd0e682da068f30c19d907c083af1e23c9b1f50a57e865f34b8c1a9b9de71',
}

# Exact Source249 layer and the closed Core248 predecessor it extends.
CURRENT_SOURCE_FIFTY_FIRST_LAYER = 'scope-ods-chart-calc-linked-after-source248'
CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v51'
CURRENT_SOURCE_FIFTY_FIRST_MANIFEST_SHA256 = 'cfdf6b25209eb61ebcd89d1118dcd6ecee1864b9ffa7fa743eed744eb5ec9d2d'
CURRENT_SOURCE_FIFTY_FIRST_PATCH_SHA256 = '088cee89f55378181f7cbfaa721745cfd6297e5eecfd1f44a67ffe2c5e3eaecf'
CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_REQUEST_SHA256 = '9c66b15ea1cec30c29178a2a8d16a4cf490b53b84103e2b00e15ff68b540d6cd'
CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_COMMITTED_SHA256 = '3884416a1a89962c69f9fc842339ec88248848d0a60b1b95cc5a70f4b35eb210'
CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_RECEIPT_SHA256 = 'e26d0b806e719ea08d3296137897938136387a0b7bb0ab361fc6f9010369256d'
CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_MARKER_SHA256 = '95419fb1b8d2844fdb19265fa9a50a7d8837d767b25affde76b5d800b047ea9a'
CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_STAMP_SHA256 = 'bbf5f063bd24cada3386d4097e1aec6ffd9132d88cd8033ac602bcf4316abdfb'
CURRENT_SOURCE_FIFTY_FIRST_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_FIRST_NATIVE_FILE = {
    'before_sha256': '58a2afdd53b7366bffaa91b83ab3355cf47a42a96c5d98699d89edeea2fe0784',
    'bytes': 23296,
    'mode': '100644',
    'new_file': False,
    'path': 'tools/scoped_ods_chart.py',
    'sha256': 'dfe4511ddba61c8928c8fc29a0fc0d1dba7b1c2a1a28da79d881cafa9b49c11b',
}

# Exact Source250 layer and the closed Core249 predecessor it extends.
CURRENT_SOURCE_FIFTY_SECOND_LAYER = 'calc-saved-ods-chart-read-after-source249'
CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v52'
CURRENT_SOURCE_FIFTY_SECOND_MANIFEST_SHA256 = 'd2eef234b7b32688ac56126d74941aee4d7bf0961752929a608bf6d37e758045'
CURRENT_SOURCE_FIFTY_SECOND_PATCH_SHA256 = '174b6c4a1e25e360322ded36f7b0168247dd6aed37684a5e5add5641067c3a6b'
CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_REQUEST_SHA256 = '3dc91c31d1fa4a911c2640248a2c0a78b9b3d7e37e8096f90ec1c4dc90b05ccf'
CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_COMMITTED_SHA256 = 'ecffa235d81c5bd352a59f992ae930862b1d3b0c7092aee1ea1c2ad20f32da40'
CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_RECEIPT_SHA256 = '4395c2184de907a6756a09ff21b4c345f678eb440d5ab1dfa6ea492a8192d80b'
CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_MARKER_SHA256 = 'bf94a6abe770af182c70a19abe20348c8c6e768cda4ebca45a1787150099867c'
CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_STAMP_SHA256 = 'e29e5151a9788a8bcb29438b3dbc2a0f7148beb9a5b877c4253473c7d5a48bd0'
CURRENT_SOURCE_FIFTY_SECOND_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_SECOND_NATIVE_FILES = (
    {
        'before_sha256': '358c7b59d1557e89382383608a0ffa25c921d50f43fdc3e243154530a9a51bb3',
        'bytes': 37084,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_ods.py',
        'sha256': '2b086c714a356923cc5434eeac0f0cc6f1e3c183e845529e9bbce2eadc1d9629',
    },
    {
        'before_sha256': 'dfe4511ddba61c8928c8fc29a0fc0d1dba7b1c2a1a28da79d881cafa9b49c11b',
        'bytes': 29030,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_ods_chart.py',
        'sha256': '37a79ed436a062a97597e14f6d5209e97649d2abcb304e8bd40c07fbd073f371',
    },
)

# Exact Source251 layer and the closed Core250 predecessor it extends.
CURRENT_SOURCE_FIFTY_THIRD_LAYER = 'xls-calc-multisheet-read-after-source250'
CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v53'
CURRENT_SOURCE_FIFTY_THIRD_MANIFEST_SHA256 = 'a13dbfa65ceefe548f8fa8e17b641628a0705033dcedf674baa23967251ea9d0'
CURRENT_SOURCE_FIFTY_THIRD_PATCH_SHA256 = 'b1f1a67ed77414871ca1b463dba3b57e89efd20b2716060967893e74d45d138d'
CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_REQUEST_SHA256 = 'ced501d40dc9ba70b604dc41168ceebb2aa737337ea98fc672f35c00ecb1ea3b'
CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_COMMITTED_SHA256 = '444d19b59bfd776d01b9a07623967e4c7e437ede6d7baf0bf231a300011b0fb8'
CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_RECEIPT_SHA256 = '5d2581f5151043ef86ec767b35c5d4e3c9519d2589e239a313ef89227ab9e39f'
CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_MARKER_SHA256 = '2cd3fc53b4676c364a55faf74725ad5b111e6fb3da7ae67fc67001ac1d3acbf4'
CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_STAMP_SHA256 = '11f9dc31741358a653e6c2458916c5cb4815c0a793c712684d4e2cb2b83373a9'
CURRENT_SOURCE_FIFTY_THIRD_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_THIRD_NATIVE_FILES = (
    {
        'before_sha256': 'ef4bd9f96fa951582542084bcbc9955324a28fa6e5faa3b086313e1d712304b1',
        'bytes': 32435,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_xls.py',
        'sha256': '64049455cc2d118e68e66caa99d0efaacda524080775fb123ba53f5cdba03bc0',
    },
)

# Exact Source252 layer and the closed Core251 predecessor it extends.
CURRENT_SOURCE_FIFTY_FOURTH_LAYER = 'xls-literal-create-and-preserving-edit-after-source251'
CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v54'
CURRENT_SOURCE_FIFTY_FOURTH_MANIFEST_SHA256 = '1c243fdf554cb77d6a9518cec15701e11dc3c3986de015cdfe186064e661e3f7'
CURRENT_SOURCE_FIFTY_FOURTH_PATCH_SHA256 = '114ade288203b0542b184a7155f3464b8f74b562bb7c0a08f63746c0aaf98b6c'
CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_REQUEST_SHA256 = '8fdbe941ba1d3dcc29504d13c322e401c579057d476f9d4090ebc5e64dd85faf'
CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_COMMITTED_SHA256 = '62105479e2883c7873185ff1d82b4b896f1b372d68d3ad44ec138cf341db1d41'
CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_RECEIPT_SHA256 = 'c564c0968eeee0276fbdbf3025f8f6ea684269a241bc2da49bd5f908cbd6b6d6'
CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_MARKER_SHA256 = 'e42823d7f4927cc1f0a97c3e35fb02573bc054dd7202e9e9d8bfee2a1dbc7179'
CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_STAMP_SHA256 = '51b7675073b1dceaef3113b759646ac26091ea8b3fe35ba793362c7bcf172dc0'
CURRENT_SOURCE_FIFTY_FOURTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_FOURTH_NATIVE_FILES = (
    {
        'before_sha256': 'd70b18c97386d471632314bc1b6111f3262b686163136d3b9d705d0d40fdd023',
        'bytes': 137041,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': '369d5ba8df4fd4498407e2d5ab412a8009bf61dc1d8ef276adade7fd9a7fe0d8',
    },
    {
        'before_sha256': '97842b366c21a3dc6c6b2227c161e440612859c41e187aa6249c9660b04c7c47',
        'bytes': 7250,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_spreadsheet.py',
        'sha256': 'f03f8e5df798eafa691fa84b73c14e2991b956e93bef7f6bb695862954a0aa2d',
    },
    {
        'before_sha256': 'a0ea4a26696c8801fac9aa81be70041c740368878d82bcf0a40d5878d3c6c51d',
        'bytes': 207237,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': '694cdb293bcdff3294b21b0e12cafe60356aa808ba840310fd25a80197f3330e',
    },
    {
        'before_sha256': '64049455cc2d118e68e66caa99d0efaacda524080775fb123ba53f5cdba03bc0',
        'bytes': 33793,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_xls.py',
        'sha256': '08a19f2cbbe04aea5c187fe8d88922b85855ee9786712c725df43b7ec4d4054f',
    },
    {
        'before_sha256': None,
        'bytes': 9393,
        'mode': '100644',
        'new_file': True,
        'path': 'tools/scoped_xls_edit.py',
        'sha256': '4fe4b160aeeff2bbe8b425820523759cd9ce46f23973627798b050975ebc9893',
    },
    {
        'before_sha256': None,
        'bytes': 6914,
        'mode': '100644',
        'new_file': True,
        'path': 'tools/scoped_xls_write.py',
        'sha256': '3c469d467ee7e2f4e6629d6f9b0ed479d5ddb8d96ef2121480efce346706188f',
    },
)

# Exact Source253 layer and the closed Core252 predecessor it extends.
CURRENT_SOURCE_FIFTY_FIFTH_LAYER = 'ruled-png-whole-grid-and-word-macro-guidance-after-source252'
CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v55'
CURRENT_SOURCE_FIFTY_FIFTH_MANIFEST_SHA256 = '8069266891881fb3cbd1b2a68523e6dc08d8d55233e8cdf0b7fab99ac0c3bbaf'
CURRENT_SOURCE_FIFTY_FIFTH_PATCH_SHA256 = 'a64344e4e3443eb917b1ab0f1e1470423305cda229482cf0f43f3f71fb5244bf'
CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_REQUEST_SHA256 = '8174f8c5ecf19142950b2b90e75f5c2033835cda7cbcbd5391349464f974ff8c'
CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_COMMITTED_SHA256 = '29fa94bf2c84686fd18e6c6a652c49683cfbeddd590e274e23faa889d2954a13'
CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_RECEIPT_SHA256 = '9387a1bfdfd6c9021e9dffa0566717b08938c5af1929c6b71f0f78c98c483c04'
CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_MARKER_SHA256 = '17c1befc02b512e2b51a4cebd363d02a4098f337f7e2ed21316e0739cd09b9fd'
CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_STAMP_SHA256 = '8e882bdbff37ba7a6e57047a5a4efd43905dd6fa23bda10278704f1cee79cf0f'
CURRENT_SOURCE_FIFTY_FIFTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_FIFTH_NATIVE_FILES = (
    {
        'before_sha256': '369d5ba8df4fd4498407e2d5ab412a8009bf61dc1d8ef276adade7fd9a7fe0d8',
        'bytes': 137181,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': '3239881d1e46d6a1cfc16ed351a103c8a35687fda3d4717e32a12a39f28a2767',
    },
    {
        'before_sha256': '790f923353ed0f6f9a4158f4cd8675a6fbd2c98d719843a3954f58c86cac5642',
        'bytes': 4485,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_schema_guidance.py',
        'sha256': '629879fb8e789332f0421c865c087d2f762fea29d846657cad91c5661b6ba14d',
    },
    {
        'before_sha256': '6b1c6510794bed4ee75641077298436aacae04cc969076814c2d8b1c11ada230',
        'bytes': 151390,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_user_scope.py',
        'sha256': '32679cb2de1144afcf35bc7966bde4c8b6afb738e6158c820341554afda226b9',
    },
    {
        'before_sha256': '3f8eda41f982371a843f49fcd81b1e6a1d8f48d1ba31a0162ae860a7fe2d5e88',
        'bytes': 17945,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_raster.py',
        'sha256': '044cf8f8c30833d9bd3b9fce8be714b845b4e48c264e216bb1453ef327cefaa2',
    },
    {
        'before_sha256': '694cdb293bcdff3294b21b0e12cafe60356aa808ba840310fd25a80197f3330e',
        'bytes': 208204,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': 'c584a3369187e35b62329b567a39e65ee19bb757515c55a4cea0f895f7ff9ee3',
    },
    {
        'before_sha256': '218c2ac446f485957b5e82920506133a0ef8de832d7b6cabc455a7c88e3f5726',
        'bytes': 20771,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_pdf_ocr.py',
        'sha256': 'dae1bb6a313f5119473d4ffb7136d28ced0c8265fc8ef98e59d0ce816f925b6e',
    },
    {
        'before_sha256': None,
        'bytes': 18884,
        'mode': '100644',
        'new_file': True,
        'path': 'tools/scoped_png_table.py',
        'sha256': '049848e347e7c074502c1a976b78410b19ab84e66daf076be04e2323f32bff06',
    },
)

# Exact Source254 layer and the closed Core253 predecessor it extends.
CURRENT_SOURCE_FIFTY_SIXTH_LAYER = 'pptx-opc-default-namespace-after-source253'
CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v56'
CURRENT_SOURCE_FIFTY_SIXTH_MANIFEST_SHA256 = 'adf5a8518b11de45cacad82d5a69f50973c3c6e145bf588a91d08627dda39910'
CURRENT_SOURCE_FIFTY_SIXTH_PATCH_SHA256 = 'a7a0d4503eaa18a5651179859cc4bcc0961405859203ee62494e032518db502d'
CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_REQUEST_SHA256 = '256006c6b577770b8f19a248e701f2843ffce6676e4eaccbd9e6b836ed67cc76'
CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_COMMITTED_SHA256 = '35b5c530b111085fdf18f35a96c524f559061294db7c6d949618a537ecfe9e06'
CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_RECEIPT_SHA256 = '0693ccc0e7b2bb72d1f5fa0b21504d0077a973078a9f4ce530d798bd470383aa'
CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_MARKER_SHA256 = 'b175386639e97b1de20961c453ffa0615b3ed56bcb55160e1a152d85f66a5ab2'
CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_STAMP_SHA256 = 'eaf05e41c0b9fc08f709a4275a77a39aebd49349463dd9c9ead0207bfd8fe1b3'
CURRENT_SOURCE_FIFTY_SIXTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_SIXTH_NATIVE_FILES = (
    {
        'before_sha256': 'db242f08bb47cdfc11ab12c38e455563e7b08223e76947ccb719496ec9d80b49',
        'bytes': 22259,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_presentation_merge.py',
        'sha256': '93578e43b45ffb7611301717967e606debe796333e1d4b44abafd9dae378fb66',
    },
)

# Exact Source255 layer and the closed Core254 predecessor it extends.
CURRENT_SOURCE_FIFTY_SEVENTH_LAYER = 'xps-oxps-default-namespace-after-source254'
CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v57'
CURRENT_SOURCE_FIFTY_SEVENTH_MANIFEST_SHA256 = '3c97028e4264d0900bf236b0bf2ee635e9359a768879ca2701182b283b3a84c1'
CURRENT_SOURCE_FIFTY_SEVENTH_PATCH_SHA256 = 'f0bb56237ea1355c2a6f8d0b87377ac1dd84d3f9baede77e9404e6fff40cff6b'
CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_REQUEST_SHA256 = 'd8936e281a7884c47fe473da2e597308b82c2dc207572dbabb0261a598c58535'
CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_COMMITTED_SHA256 = '426b540032b9d13c9b6ada3b0490232251a1fc6db9c55e44bb24306e8f71cef0'
CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_RECEIPT_SHA256 = 'ecf1c6d62b83504575ef45a2af7e147765a31dcda300639fa7a8fb07362c9479'
CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_MARKER_SHA256 = 'a406d1ac0e8c437a242388be3087c5acac9c0d68bc162f49fea20e6126a66a69'
CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_STAMP_SHA256 = 'beef6092d37e4e0ea26e7f45a83690567ae62523db2f90c73af536c4ebce8f3d'
CURRENT_SOURCE_FIFTY_SEVENTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_SEVENTH_NATIVE_FILES = (
    {
        'before_sha256': '9136025b53b9be3d4a16cf7934d6062489a24f797614d08ebffda25d9fc09834',
        'bytes': 9911,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_xps_write.py',
        'sha256': '008113783552dbe056af4a6f3aee1e38b6d15cff3ab054ac03d4046924317149',
    },
)

# Exact Source256 layer and the closed Core255 predecessor it extends.
CURRENT_SOURCE_FIFTY_EIGHTH_LAYER = 'pptx-template-opc-default-namespace-after-source255'
CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v58'
CURRENT_SOURCE_FIFTY_EIGHTH_MANIFEST_SHA256 = 'affb69428110af3f3a165f91351719ab4d45eb827cddfa03c922b1691eb68636'
CURRENT_SOURCE_FIFTY_EIGHTH_PATCH_SHA256 = 'ba3777727b69850c33059be961f0347b176efe6aca0405453ef6cc090233011a'
CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_REQUEST_SHA256 = '74cd74ecc4a46e36c850dda0dd7c3e6f75a22c0c5e3b7a6ea5f53d3e8144f3de'
CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_COMMITTED_SHA256 = 'cb5c02a350a0deca0ab8505ad5a1221d0e3f14ce819d4e3ebeb1bb9f3025be70'
CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_RECEIPT_SHA256 = '642cabb008bac2c0059c53057a3043a0d058331777ab4d8c34d9c8776f2c4cc1'
CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_MARKER_SHA256 = 'c6d40cd379fb86aaf19480b019e062bd207039e04cf891beacda89027ca5c9e0'
CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_STAMP_SHA256 = 'd81aaf4a830a0c9d033223d207501ad6009e819d8f714bbea09fd466acd46cb3'
CURRENT_SOURCE_FIFTY_EIGHTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_EIGHTH_NATIVE_FILES = (
    {
        'before_sha256': '8591f5a209a8a0e3fd9f3a4573cb9b1fdea761a1a10a5a0463816d08ad8d1e36',
        'bytes': 22091,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_presentation_template.py',
        'sha256': 'b48cd2b1417251b2c823dc48dc28edc5ae0c0c66e710c85f2f6dd9e1046475fd',
    },
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


# Exact Source257 layer and the closed Core256 predecessor it extends.
CURRENT_SOURCE_FIFTY_NINTH_LAYER = 'pptx-template-inherited-title-fit-after-source256'
CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v59'
CURRENT_SOURCE_FIFTY_NINTH_MANIFEST_SHA256 = '8a3e7ed3e0a24e5ccb885bc6d9afb935c65860b0237485003884bccffffa57a2'
CURRENT_SOURCE_FIFTY_NINTH_PATCH_SHA256 = 'adbfb19de73aec613900502cff367261dab39eb8e9ec0e288df9e4a1c2f44f4b'
CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_REQUEST_SHA256 = '872fc0cc99506fb9aa4c8cbcc135eeea12e4497dca9d0d3067b02aff0e7ed79a'
CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_COMMITTED_SHA256 = '80568c22d9ec3a17983edc059ab024570d7d92d473eac6bffe7201a7078b6518'
CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_RECEIPT_SHA256 = '3fffecce2d8a2c3cbeac17cf48635a48e277440f1947907518245bd8e570ea6f'
CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_MARKER_SHA256 = '4ca01b9b14e45983492f57ba918fc89447689c09ab18c9ac97b417f254ccd46d'
CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_STAMP_SHA256 = '219e9654d30f06be0b0916f1240afb1fba0401f7de791535f9394c16b8e9ba95'
CURRENT_SOURCE_FIFTY_NINTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_FIFTY_NINTH_NATIVE_FILES = (
    {
        'before_sha256': 'b48cd2b1417251b2c823dc48dc28edc5ae0c0c66e710c85f2f6dd9e1046475fd',
        'bytes': 30896,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_presentation_template.py',
        'sha256': '8b60bb853c547e23ccedf15ee7a1623c99509c9cbcf7288627c8b28e131b2d41',
    },
    {
        'before_sha256': '0526a026e0a4b9c37d5d62d10c82d53fbab39c08c7ce2587e4c2a89192945d1d',
        'bytes': 23385,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_presentation.py',
        'sha256': '414db2e3a1c2552295e4d177db6fa60d8853939e8eb67565969d1fc6e38fa614',
    },
)

# Exact Source258 layer and the closed Core257 predecessor it extends.
CURRENT_SOURCE_SIXTIETH_LAYER = 's13-owned-jpeg-photo-and-vision-privacy-after-source257'
CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v60'
CURRENT_SOURCE_SIXTIETH_MANIFEST_SHA256 = 'fe60dfd82d6e40ae8ed00b51c6f13f0ef06c7a5b8a2cb7ba47077b81a705981c'
CURRENT_SOURCE_SIXTIETH_PATCH_SHA256 = 'f0c0f9fc224d50641306a6fce41a263bdf4294f404f141aba990178f16f7b524'
CURRENT_SOURCE_SIXTIETH_PREVIOUS_REQUEST_SHA256 = '6567c8c3558641db145020cd3cecb99b167fdaee8c437eb7444c2e8819bc9b03'
CURRENT_SOURCE_SIXTIETH_PREVIOUS_COMMITTED_SHA256 = '6edfd883c964e17165d6a5945eaf499552a3295835839b213b13c0cf71070d0f'
CURRENT_SOURCE_SIXTIETH_PREVIOUS_RECEIPT_SHA256 = 'd28c03b8f4a265a588723e77df95897d6ec4fb3990e78fbd7aa422babcf60647'
CURRENT_SOURCE_SIXTIETH_PREVIOUS_MARKER_SHA256 = 'de7ea00682bdc814d9bc430170d129c6d1aff482488c091dd4dfb4248ee14abf'
CURRENT_SOURCE_SIXTIETH_PREVIOUS_STAMP_SHA256 = 'c85ecaf56a9edb2c950ceab3b2cc9f86d4142975868d5cd7ab89a10ac52582b6'
CURRENT_SOURCE_SIXTIETH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTIETH_NATIVE_FILES = (
    {
        'before_sha256': '4343b37c452c24c2029b2fa4cc1331c6c4ccf4783cee744cd653c9f30f1ef366',
        'bytes': 119758,
        'mode': '100644',
        'new_file': False,
        'path': 'gateway/run_inbound.py',
        'sha256': 'd5887f1f03ac5cfe3b1f523fc7ebe0269d25cc50db150333314e112e30700461',
    },
    {
        'before_sha256': '95d0a94121370e26def5a49fd2dc41e819b2e6bb87a61ffc7c53d2bd43b7530d',
        'bytes': 16588,
        'mode': '100644',
        'new_file': False,
        'path': 'gateway/run_inbound_media.py',
        'sha256': '384bb3114ee5e9349794b7c5a23b97320fdb6751cd8328486f4c413ae7353744',
    },
    {
        'before_sha256': '629879fb8e789332f0421c865c087d2f762fea29d846657cad91c5661b6ba14d',
        'bytes': 4617,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_schema_guidance.py',
        'sha256': 'ae7cb29c030e099bf57d6acb1e4700fc446158eea1c17d505a7b754fdc4b4f18',
    },
    {
        'before_sha256': '32679cb2de1144afcf35bc7966bde4c8b6afb738e6158c820341554afda226b9',
        'bytes': 151430,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_user_scope.py',
        'sha256': '2b12bf530ed4cebafb8502497f210f0b1ee26952e18cb7d31ff2df6d21a83ec0',
    },
    {
        'before_sha256': '044cf8f8c30833d9bd3b9fce8be714b845b4e48c264e216bb1453ef327cefaa2',
        'bytes': 18148,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_raster.py',
        'sha256': '60526b9842a2c0c75be24a373e34b27ebb921cb0a1f1df71c41f3f9d8e040cb4',
    },
    {
        'before_sha256': 'c584a3369187e35b62329b567a39e65ee19bb757515c55a4cea0f895f7ff9ee3',
        'bytes': 208212,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': 'c3e6ac8fdb4cf0d150b52b88386703878e279bcd82dd6aed3656778b62936002',
    },
    {
        'before_sha256': '049848e347e7c074502c1a976b78410b19ab84e66daf076be04e2323f32bff06',
        'bytes': 19203,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_png_table.py',
        'sha256': '51a8d85fff34c3744147c1965b91b520cb81f10f0dc65bc1e92fb308bb117ec5',
    },
    {
        'before_sha256': '9bfc2e4379439f742fa019c6c3fad801c6bbdd70837e82fae4d5efdea85220ae',
        'bytes': 9996,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_raster.py',
        'sha256': '620c6b4d6c6c7dffdb68faea70c61b18a96701551a3073dfb5a0bab630216f06',
    },
)

# Exact Source259 layer and the closed Core258 predecessor it extends.
CURRENT_SOURCE_SIXTY_FIRST_LAYER = 'xls-biff8-number-preserving-edit-after-source258'
CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v61'
CURRENT_SOURCE_SIXTY_FIRST_MANIFEST_SHA256 = '0d2fc15428b393877d97c24c67b13f471ee667b8c029ccad7732d41fe9c082c3'
CURRENT_SOURCE_SIXTY_FIRST_PATCH_SHA256 = 'cf01b3b293acecbee5d589b1d143902f91533a0f3d63f5995f6223a742eaf1aa'
CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_REQUEST_SHA256 = '4497701b2511ac64990445d15cee8f096691e2a0ee134e27a07c2f1f8d7a0e67'
CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_COMMITTED_SHA256 = '2e1d09d9a380436bfdee424b78f3ae43ef50bd90f75ffb0a0f687b2c7b7e8e19'
CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_RECEIPT_SHA256 = 'e88ec65398b162e9883a3675c2fb5b291edac84013745503d9e636ef39284607'
CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_MARKER_SHA256 = 'a070d5832583b990baa4c951384f2d0b04f4cb57a1eb3cb82aaabe2ebba9efab'
CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_STAMP_SHA256 = 'd1effa29accfe7c76349dec2b172c318e29065c61848c4b5fd2130f9ad3cc471'
CURRENT_SOURCE_SIXTY_FIRST_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_FIRST_NATIVE_FILES = (
    {
        'before_sha256': '3239881d1e46d6a1cfc16ed351a103c8a35687fda3d4717e32a12a39f28a2767',
        'bytes': 137176,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': '4c7dcce424aebb2ee67f645d41d8d070be45e56c41ff585ac747d991b6c58a09',
    },
    {
        'before_sha256': 'f03f8e5df798eafa691fa84b73c14e2991b956e93bef7f6bb695862954a0aa2d',
        'bytes': 7377,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_spreadsheet.py',
        'sha256': '1433e21d110520dc92bff7edf8d9ea9066d0ca403b691af7b48ecf93c64f46b7',
    },
    {
        'before_sha256': '4fe4b160aeeff2bbe8b425820523759cd9ce46f23973627798b050975ebc9893',
        'bytes': 14174,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_xls_edit.py',
        'sha256': 'ec5d1943b373a88274f297f52f30c01286fc1baeefdaaaa7ce3dd7abefdd39b8',
    },
)

# Exact Source260 layer and the closed Core259 predecessor it extends.
CURRENT_SOURCE_SIXTY_SECOND_LAYER = 'odp-chart-edit-with-owned-capture-after-source259'
CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v62'
CURRENT_SOURCE_SIXTY_SECOND_MANIFEST_SHA256 = '65e903cf6d072118804140f0b1de84b410909a2900fd0175a10decc468180e81'
CURRENT_SOURCE_SIXTY_SECOND_PATCH_SHA256 = 'da94d8c2c46416dbb7ec2ca5249b935aaeaaded724b322b84684658d550c6f7d'
CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_REQUEST_SHA256 = '50b80ea2895da6a961797bb71f9bc67a6b31eb9c41fc8ee017a60856f5e479af'
CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_COMMITTED_SHA256 = '69654951a0dcd1fde665b3ef35137f4b303fc33a5ca5762f91437a907ee64d89'
CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_RECEIPT_SHA256 = '091ba4590668b9cdca588ec1531ed59acdce1b53decc6e1f09c13617b1360692'
CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_MARKER_SHA256 = '426a3346ac7470532af9e263832d4a2f50c0015da5229d54a6b2b4f7814006c1'
CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_STAMP_SHA256 = '8795d9f4f81161ab1cc71cebef24f1826fc45a56e623f84036e0155efeec1448'
CURRENT_SOURCE_SIXTY_SECOND_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_SECOND_NATIVE_FILES = (
    {
        'before_sha256': '4c7dcce424aebb2ee67f645d41d8d070be45e56c41ff585ac747d991b6c58a09',
        'bytes': 138011,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': '6abc0c2593ad439986f24fb8516bbe2cc7c10af65e2d3a4a509ac965e34ddb2d',
    },
    {
        'before_sha256': 'ae7cb29c030e099bf57d6acb1e4700fc446158eea1c17d505a7b754fdc4b4f18',
        'bytes': 4617,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_schema_guidance.py',
        'sha256': 'cb68bf47f803094f04cf27633925b2c45a6e2cad565c7603419bbc7a1a9a741e',
    },
    {
        'bytes': 17158,
        'mode': '100644',
        'new_file': True,
        'path': 'hermes_cli/friday_workspace_odp_chart_capture.py',
        'sha256': '32bf1ac9946a6642282bfa9ee7b6ccef2c04ddd661bf60975d5e82688ec9a2bf',
    },
    {
        'before_sha256': 'b097212d49519b24f94a2875f9ed5da4228ae722445cc0914741374647db912a',
        'bytes': 6042,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_presentation_variants.py',
        'sha256': '25633458f80c97781c0ca36f82eaa8cdf8bc597b0194c9afac01f8d837296a21',
    },
    {
        'before_sha256': 'c3e6ac8fdb4cf0d150b52b88386703878e279bcd82dd6aed3656778b62936002',
        'bytes': 208892,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': 'f54938a7f23510912290ac6e8c64ae39ac676dcefd8ffc28c60e49f777b071f3',
    },
    {
        'bytes': 21819,
        'mode': '100644',
        'new_file': True,
        'path': 'tools/scoped_presentation_odp_chart_edit.py',
        'sha256': '28f644bc5d7cc2b64028f2aa4a3d5256bfd073e43ecc545afdeddad45eec5710',
    },
)

# Exact Source261 layer and the closed Core260 predecessor it extends.
CURRENT_SOURCE_SIXTY_THIRD_LAYER = 'pdf-text-to-editable-docx-after-source260'
CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v63'
CURRENT_SOURCE_SIXTY_THIRD_MANIFEST_SHA256 = '8aa104c7434aea2cc2295d6938de2560f61f34b9109431430efde806b0d88abc'
CURRENT_SOURCE_SIXTY_THIRD_PATCH_SHA256 = 'f63813deaeb596b015f62ed24d3cd1c384ac22b56e42f2a7ef6d6ecabcaa9b0a'
CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_REQUEST_SHA256 = '7ab248c29943a2d1b6f8dc728ba6fc6b64fcbc2c708f4dd39d42e521b700e0e0'
CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_COMMITTED_SHA256 = 'c4411ff1f322ee95d3ee14f94379afbdcc5b98ef6e6a3eec13468212022b0b1d'
CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_RECEIPT_SHA256 = 'd75236791f691099a4551391f383d3e7d3c94d389cf5f79a7ed77aa91720d814'
CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_MARKER_SHA256 = '7e379aefb83339dc07c4b2b81107d1d1c2ac167c900b99223d0254408b7f8bd6'
CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_STAMP_SHA256 = '55f2bd2f06d659568f5643c6ae2db0652957449ee1944777fbf81081807a5174'
CURRENT_SOURCE_SIXTY_THIRD_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_THIRD_NATIVE_FILES = (
    {
        'before_sha256': '6abc0c2593ad439986f24fb8516bbe2cc7c10af65e2d3a4a509ac965e34ddb2d',
        'bytes': 138173,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': 'e51e009b8fefe39bfd01d43c832ab418bfd68d3362e86bccd59a89ce04f047e5',
    },
    {
        'before_sha256': '2b12bf530ed4cebafb8502497f210f0b1ee26952e18cb7d31ff2df6d21a83ec0',
        'bytes': 151464,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_user_scope.py',
        'sha256': '8d70f272beb0283416d91ee73d23fe1c4ba9aab0fa8b3e288c8d93f8a98a97ad',
    },
    {
        'before_sha256': 'd9de55e7ec7da21c7c56db8460c38d0696ad3a69986cc0906647f37e10015e11',
        'bytes': 14094,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_word_conversion.py',
        'sha256': '7ff217139e99f742601aa48b615d3300cb74f2252d088ccb484c7690348e2bc5',
    },
    {
        'before_sha256': 'f54938a7f23510912290ac6e8c64ae39ac676dcefd8ffc28c60e49f777b071f3',
        'bytes': 209116,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': 'ed7ba65303ce5ec58200d202f0e8695e92d66a13f592be254927e43f31dda30a',
    },
    {
        'before_sha256': 'dae1bb6a313f5119473d4ffb7136d28ced0c8265fc8ef98e59d0ce816f925b6e',
        'bytes': 24159,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_pdf_ocr.py',
        'sha256': 'c17cbf2cd83c2c5402543cc9d71ea9469d1cbcedbc6a2034900fb6b23b3d0bc0',
    },
)

# Exact Source262 layer and the closed Core261 predecessor it extends.
CURRENT_SOURCE_SIXTY_FOURTH_LAYER = 'pdf-ocr-to-editable-docx-after-source261'
CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v64'
CURRENT_SOURCE_SIXTY_FOURTH_MANIFEST_SHA256 = 'df793195c8718199eabaa45cf019a3a5bde9cdad3c63f88d4ebcc59e8169b8e1'
CURRENT_SOURCE_SIXTY_FOURTH_PATCH_SHA256 = '795516e3609ba542fd5f183c0ddaa055f932a66a388fd561a5405004e263c616'
CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_REQUEST_SHA256 = '96d72151776398c2f6794bd76b004d9511aeefddaaf93724227c90c1e1110c48'
CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_COMMITTED_SHA256 = '8eb55eda445e4551eaa9d6281b945d42fca8f4cfc5bcb7fcf74a86cdf961ff38'
CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_RECEIPT_SHA256 = '57a406b726941be2abf84b5747144d27b55c9c0d9582782c66fcc89d895d7d4e'
CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_MARKER_SHA256 = '5b8bcedd80efca789f631668ce50821e266165d37f75764eacc2e2ed6b420939'
CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_STAMP_SHA256 = '16a8353569ad8a3fcbb3b9b14f5429810ef15ac84fd54a8d8afb70885763a53d'
CURRENT_SOURCE_SIXTY_FOURTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_FOURTH_NATIVE_FILES = (
    {
        'before_sha256': 'e51e009b8fefe39bfd01d43c832ab418bfd68d3362e86bccd59a89ce04f047e5',
        'bytes': 138236,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': 'd204f20f94d6bddda48320da848a1de99c054d621d61e62af2c913f028116b66',
    },
    {
        'before_sha256': '8d70f272beb0283416d91ee73d23fe1c4ba9aab0fa8b3e288c8d93f8a98a97ad',
        'bytes': 151496,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_user_scope.py',
        'sha256': 'e0730b19fff614046bd059f71a6e0065f7423521db4855aa39e88265ee62a133',
    },
    {
        'before_sha256': '7ff217139e99f742601aa48b615d3300cb74f2252d088ccb484c7690348e2bc5',
        'bytes': 16799,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_word_conversion.py',
        'sha256': '3b1a4ab7f91ff3eff752f52ffce6aa093c447216d62664a8ba9e94b4e9a3e595',
    },
    {
        'before_sha256': 'ed7ba65303ce5ec58200d202f0e8695e92d66a13f592be254927e43f31dda30a',
        'bytes': 209213,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': 'd06e1c7831d4ec9959fc3d24a85fd7d160c49dddb645eb32b3692b31d9c03d4e',
    },
    {
        'before_sha256': 'c17cbf2cd83c2c5402543cc9d71ea9469d1cbcedbc6a2034900fb6b23b3d0bc0',
        'bytes': 28504,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_pdf_ocr.py',
        'sha256': '31766c6086f4af38b92c270b990c40ad5959525fec1ea11c0cf381a63ec133c0',
    },
)

# Exact Source263 layer and the closed Core262 predecessor it extends.
CURRENT_SOURCE_SIXTY_FIFTH_LAYER = 'ocr-omission-disclosure-after-source262'
CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v65'
CURRENT_SOURCE_SIXTY_FIFTH_MANIFEST_SHA256 = '399c3d90162b9b726fb8d73e434f3776a1980d7ba1570638a01b33d73613d944'
CURRENT_SOURCE_SIXTY_FIFTH_PATCH_SHA256 = '0691c111602527f08c60c870290ae76ed6e1f25e89759cea4fb18250b2d7adfc'
CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_REQUEST_SHA256 = '63c71ecab6bd49cc156b14754842c342eb00951ae5908388c90a3e67007ad657'
CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_COMMITTED_SHA256 = 'c39b141696d859b7e765e1f31a39924f1e4268b9874ac2ce63aaac322e8db445'
CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_RECEIPT_SHA256 = 'a8031f4d541a3b0686ec2123d117302bd9f60ba74ecfc6d6430ac6a42cc4538b'
CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_MARKER_SHA256 = 'fb6e85781c02a70d84794650bcb7a7c65c38909e63ef07ab81c606e41d36633d'
CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_STAMP_SHA256 = '2a3d0f1baf738eeb78a781415ffd3c7fbb84be4e5fd58d34565c790836e23c54'
CURRENT_SOURCE_SIXTY_FIFTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_FIFTH_NATIVE_FILES = (
    {
        'before_sha256': '3b1a4ab7f91ff3eff752f52ffce6aa093c447216d62664a8ba9e94b4e9a3e595',
        'bytes': 16986,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_word_conversion.py',
        'sha256': '2dc646f09ae208cb0d69257e3bb99fad467bdc21a7b305cd0c4a5380e83889d5',
    },
)

# Exact Source264 layer and the closed Core263 predecessor it extends.
CURRENT_SOURCE_SIXTY_SIXTH_LAYER = 'passive-layered-pdf-redaction-after-source263'
CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v66'
CURRENT_SOURCE_SIXTY_SIXTH_MANIFEST_SHA256 = 'f6c8fb31c410482eff28532f8ca78dd090f519fc50800384747e0a17e02ff215'
CURRENT_SOURCE_SIXTY_SIXTH_PATCH_SHA256 = 'f5d7364a4b75970d6aedf48533115f4b1996deae041aa6867e80058ff22d20f2'
CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_REQUEST_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_COMMITTED_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_RECEIPT_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_MARKER_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_STAMP_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SIXTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_SIXTH_NATIVE_FILES = (
    {
        'before_sha256': 'd204f20f94d6bddda48320da848a1de99c054d621d61e62af2c913f028116b66',
        'bytes': 139634,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_prompt_scope.py',
        'sha256': '78a75592be5d0ef5a2052caf5d149cba01f3634e2339a3eedd133089050b0cbc',
    },
    {
        'before_sha256': 'e0730b19fff614046bd059f71a6e0065f7423521db4855aa39e88265ee62a133',
        'bytes': 152540,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_user_scope.py',
        'sha256': '84baab627cd84c4d49d387995806ae6bbfa1ec28122061bdd76506f6812ceed6',
    },
    {
        'before_sha256': 'f58138ee777d15e95a0b04562db68872970e199478e598eb8ec891bff3e49cfa',
        'bytes': 2901,
        'mode': '100644',
        'new_file': False,
        'path': 'hermes_cli/friday_workspace_pdf_redact.py',
        'sha256': '1c0be2ff37767d7642b233b9d3188451b56fad12a715611c3433b74c59e6f9d4',
    },
    {
        'before_sha256': 'd06e1c7831d4ec9959fc3d24a85fd7d160c49dddb645eb32b3692b31d9c03d4e',
        'bytes': 210959,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/file_tools.py',
        'sha256': '2fd07c75b27195be7ac81daa793734cff451f933b5f5bcc6a6ad3babb5f1a940',
    },
    {
        'before_sha256': '1aef9480d1fe1164042a5b7ea2fb358dfe4889a1a796d5eed44547547c0c22c8',
        'bytes': 23533,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_pdf_pages.py',
        'sha256': '7adcdae2f10a4690fd710d670f82b984cff7fd94793b729a08fdd02ad63e8253',
    },
    {
        'before_sha256': 'ff8e80fc68b7158d6d5d0b3be32945cd7a9e1078abb81e827d673e308b13dfd3',
        'bytes': 40431,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_pdf_redact.py',
        'sha256': '3aee4c58812ba9f8a49663159954c9d832bacf4c299e381fb22e168863e4b1f9',
    },
)

# Exact Source265 layer and the closed Core264 predecessor it extends.
CURRENT_SOURCE_SIXTY_SEVENTH_LAYER = 'telegram-tiff-document-ingress-after-source264'
CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v67'
CURRENT_SOURCE_SIXTY_SEVENTH_MANIFEST_SHA256 = 'f8a8f269ab1e756cd1d7bff2948ae10e535638c9677ff682b331f5d094d250cf'
CURRENT_SOURCE_SIXTY_SEVENTH_PATCH_SHA256 = '2879d17a4c0af4bb861dcc37185f0376c79c0267a1a5167be384ada5e4efb750'
CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_REQUEST_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_COMMITTED_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_RECEIPT_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_MARKER_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_STAMP_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_SEVENTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_SEVENTH_NATIVE_FILES = (
    {
        'before_sha256': '03a0e4d2ff292f9b59ec350f7bf7a1fcc12a6a079b30b425d7471d22c694c4c4',
        'bytes': 14781,
        'mode': '100644',
        'new_file': False,
        'path': 'plugins/platforms/telegram/telegram_file_boundary.py',
        'sha256': '3ee6bbd98393311aab50909fbd87c0a380fe11158e151834a73d952d31750e24',
    },
)

# Exact Source266 layer and the closed Core265 predecessor it extends.
CURRENT_SOURCE_SIXTY_EIGHTH_LAYER = 'structured-file-password-containment-after-source265'
CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v68'
CURRENT_SOURCE_SIXTY_EIGHTH_MANIFEST_SHA256 = '9c4f5b0be1c44dc421b5efd3f12a992f6f67037668edfdf62d904b6268290d7d'
CURRENT_SOURCE_SIXTY_EIGHTH_PATCH_SHA256 = 'a0292e0a455f9c81bc6475d984cdaa9c4e1fe4c1a86c8e66f5d684babe99d00a'
CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_REQUEST_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_COMMITTED_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_RECEIPT_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_MARKER_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_STAMP_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_EIGHTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_EIGHTH_NATIVE_FILES = (
    {
        'before_sha256': '08823b1e54f6aa78f49ebf1f0f92092f9c558bd982c3961ef9ed8cd99642f5ec',
        'bytes': 49106,
        'mode': '100644',
        'new_file': False,
        'path': 'agent/message_sanitization.py',
        'sha256': 'c8b0ac1946e57badd9488da17bb3e8a9e7dd72d3d7acb063f9666f106897e3e2',
    },
    {
        'before_sha256': '55ec1efe69d66eafedadc97150f4e057f1e00936299e191619410478be8e1c41',
        'bytes': 15813,
        'mode': '100644',
        'new_file': False,
        'path': 'agent/turn_tool_round.py',
        'sha256': '3082e4eff0d5f073e8f4b3c61e8fd8e7e3d46b692062065c948490857f831f7b',
    },
    {
        'before_sha256': '8d5c84fb2aec4ff030aec822351c8559298faea15c6267d78ebcf925b8416309',
        'bytes': 15530,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/tool_search_validation.py',
        'sha256': '6778a3374d5f05da029e1832d4cea9e65d99cd5e8c3d67dafd6565ab4a6cf501',
    },
)

# Exact Source267 layer and the closed Core266 predecessor it extends.
CURRENT_SOURCE_SIXTY_NINTH_LAYER = 'telegram-image-delivery-provenance-after-source266'
CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v69'
CURRENT_SOURCE_SIXTY_NINTH_MANIFEST_SHA256 = '44a64b9daf1199d26895813ad03065885926c7e428fd34500b0cdcb4072e6583'
CURRENT_SOURCE_SIXTY_NINTH_PATCH_SHA256 = 'fdbc30f0983a492406d18ef330a7cc3e38269bdb7eb10c846ba58d10a49eac6c'
CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_REQUEST_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_COMMITTED_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_RECEIPT_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_MARKER_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_STAMP_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SIXTY_NINTH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SIXTY_NINTH_NATIVE_FILES = (
    {
        'before_sha256': 'd5887f1f03ac5cfe3b1f523fc7ebe0269d25cc50db150333314e112e30700461',
        'bytes': 119798,
        'mode': '100644',
        'new_file': False,
        'path': 'gateway/run_inbound.py',
        'sha256': 'c6509fdb3c70d92ba00213c78cb07b31ba8a18c3802e56861dcf9e080aa55682',
    },
    {
        'before_sha256': '384bb3114ee5e9349794b7c5a23b97320fdb6751cd8328486f4c413ae7353744',
        'bytes': 17710,
        'mode': '100644',
        'new_file': False,
        'path': 'gateway/run_inbound_media.py',
        'sha256': '98e8635b25606e91028097c0201fcd2e3cce6465a6805056f4ce769cd7a9371d',
    },
    {
        'before_sha256': '3ee6bbd98393311aab50909fbd87c0a380fe11158e151834a73d952d31750e24',
        'bytes': 15058,
        'mode': '100644',
        'new_file': False,
        'path': 'plugins/platforms/telegram/telegram_file_boundary.py',
        'sha256': 'cbdfb26a570404dfe5326a2bf78e2cefad6e713a2f0181ab4d67f7e0f3f2f4ca',
    },
)

# Exact Source268 layer and the closed Core267 predecessor it extends.
CURRENT_SOURCE_SEVENTIETH_LAYER = 'pdf-ocr-ambiguous-total-disclosure-after-source267'
CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v70'
CURRENT_SOURCE_SEVENTIETH_MANIFEST_SHA256 = '45df35e438b965a3d6ff3549f0a8ea36649496e5fc9aedc582b56f362d181de9'
CURRENT_SOURCE_SEVENTIETH_PATCH_SHA256 = '10cd9743854e435933a304b2caf4b00039027a2af9bdbb0f34ceb3746079856c'
CURRENT_SOURCE_SEVENTIETH_PREVIOUS_REQUEST_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SEVENTIETH_PREVIOUS_COMMITTED_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SEVENTIETH_PREVIOUS_RECEIPT_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SEVENTIETH_PREVIOUS_MARKER_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SEVENTIETH_PREVIOUS_STAMP_SHA256 = 'UNBOUND'
CURRENT_SOURCE_SEVENTIETH_HELPER = 'scripts/friday_ordinary_install.py'
CURRENT_SOURCE_SEVENTIETH_NATIVE_FILES = (
    {
        'before_sha256': '31766c6086f4af38b92c270b990c40ad5959525fec1ea11c0cf381a63ec133c0',
        'bytes': 29818,
        'mode': '100644',
        'new_file': False,
        'path': 'tools/scoped_pdf_ocr.py',
        'sha256': '2456c59d9a0dddad368384a631c02a057a2ba6653d5edf34258fa3c2fa88e494',
    },
)

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


def forty_seventh_predecessor_ref(home):
    pin = CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def forty_seventh_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_forty_seventh_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source244 to Source245 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FORTY_SEVENTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_seventh_layer_required")
    require(CURRENT_SOURCE_FORTY_SEVENTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FORTY_SEVENTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FORTY_SEVENTH_NATIVE_FILES,
            "transaction_current_source_forty_seventh_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_seventh_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_forty_seventh_home_required")
        require(context["previous_native_update"] == forty_seventh_predecessor_ref(home),
                "transaction_current_source_forty_seventh_previous_request_pin_changed")
        for key, ref in forty_seventh_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_forty_seventh_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_seventh_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 244 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 571,
                "transaction_current_source_forty_seventh_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FORTY_SEVENTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_forty_seventh_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FORTY_SEVENTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FORTY_SEVENTH_PATCH_SHA256,
                "transaction_current_source_forty_seventh_binding_pair_changed")


def require_forty_seventh_predecessor(request, previous, *, raw=None):
    """Check the exact retained v46 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_seventh_predecessor_ref(request["home"]),
            "transaction_current_source_forty_seventh_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_forty_seventh_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_seventh_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_SIXTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 569
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_sixth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_forty_seventh_previous_committed_changed")
    return committed_path, committed_raw


def forty_eighth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def forty_eighth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_forty_eighth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source245 to Source246 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FORTY_EIGHTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_eighth_layer_required")
    require(CURRENT_SOURCE_FORTY_EIGHTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FORTY_EIGHTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FORTY_EIGHTH_NATIVE_FILE,
            "transaction_current_source_forty_eighth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_eighth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_forty_eighth_home_required")
        require(context["previous_native_update"] == forty_eighth_predecessor_ref(home),
                "transaction_current_source_forty_eighth_previous_request_pin_changed")
        for key, ref in forty_eighth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_forty_eighth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_eighth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 245 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 573,
                "transaction_current_source_forty_eighth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FORTY_EIGHTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_forty_eighth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FORTY_EIGHTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FORTY_EIGHTH_PATCH_SHA256,
                "transaction_current_source_forty_eighth_binding_pair_changed")


def require_forty_eighth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v47 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_eighth_predecessor_ref(request["home"]),
            "transaction_current_source_forty_eighth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_forty_eighth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_eighth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_SEVENTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 571
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_seventh_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_forty_eighth_previous_committed_changed")
    return committed_path, committed_raw


def forty_ninth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def forty_ninth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_forty_ninth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source246 to Source247 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FORTY_NINTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_forty_ninth_layer_required")
    require(CURRENT_SOURCE_FORTY_NINTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FORTY_NINTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FORTY_NINTH_NATIVE_FILES,
            "transaction_current_source_forty_ninth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_forty_ninth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_forty_ninth_home_required")
        require(context["previous_native_update"] == forty_ninth_predecessor_ref(home),
                "transaction_current_source_forty_ninth_previous_request_pin_changed")
        for key, ref in forty_ninth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_forty_ninth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_forty_ninth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 246 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 575,
                "transaction_current_source_forty_ninth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FORTY_NINTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_forty_ninth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FORTY_NINTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FORTY_NINTH_PATCH_SHA256,
                "transaction_current_source_forty_ninth_binding_pair_changed")


def require_forty_ninth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v48 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == forty_ninth_predecessor_ref(request["home"]),
            "transaction_current_source_forty_ninth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_forty_ninth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_forty_ninth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_EIGHTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 573
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_eighth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_forty_ninth_previous_committed_changed")
    return committed_path, committed_raw


def fiftieth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTIETH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fiftieth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTIETH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTIETH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTIETH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTIETH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fiftieth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source247 to Source248 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTIETH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fiftieth_layer_required")
    require(CURRENT_SOURCE_FIFTIETH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTIETH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTIETH_NATIVE_FILE,
            "transaction_current_source_fiftieth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fiftieth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fiftieth_home_required")
        require(context["previous_native_update"] == fiftieth_predecessor_ref(home),
                "transaction_current_source_fiftieth_previous_request_pin_changed")
        for key, ref in fiftieth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fiftieth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fiftieth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 247 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 577,
                "transaction_current_source_fiftieth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTIETH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fiftieth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTIETH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTIETH_PATCH_SHA256,
                "transaction_current_source_fiftieth_binding_pair_changed")


def require_fiftieth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v49 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fiftieth_predecessor_ref(request["home"]),
            "transaction_current_source_fiftieth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fiftieth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fiftieth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FORTY_NINTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 575
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_forty_ninth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTIETH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fiftieth_previous_committed_changed")
    return committed_path, committed_raw


def fifty_first_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_first_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_first_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source248 to Source249 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_FIRST_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_first_layer_required")
    require(CURRENT_SOURCE_FIFTY_FIRST_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_FIRST_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_FIRST_NATIVE_FILE,
            "transaction_current_source_fifty_first_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_first_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_first_home_required")
        require(context["previous_native_update"] == fifty_first_predecessor_ref(home),
                "transaction_current_source_fifty_first_previous_request_pin_changed")
        for key, ref in fifty_first_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_first_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_first_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 248 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 579,
                "transaction_current_source_fifty_first_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_FIRST_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_first_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_FIRST_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_FIRST_PATCH_SHA256,
                "transaction_current_source_fifty_first_binding_pair_changed")


def require_fifty_first_predecessor(request, previous, *, raw=None):
    """Check the exact retained v50 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_first_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_first_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_first_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_first_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTIETH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 577
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fiftieth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_first_previous_committed_changed")
    return committed_path, committed_raw


def fifty_second_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_second_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_second_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source249 to Source250 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_SECOND_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_second_layer_required")
    require(CURRENT_SOURCE_FIFTY_SECOND_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_SECOND_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_SECOND_NATIVE_FILES,
            "transaction_current_source_fifty_second_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_second_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_second_home_required")
        require(context["previous_native_update"] == fifty_second_predecessor_ref(home),
                "transaction_current_source_fifty_second_previous_request_pin_changed")
        for key, ref in fifty_second_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_second_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_second_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 249 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 581,
                "transaction_current_source_fifty_second_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_SECOND_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_second_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_SECOND_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_SECOND_PATCH_SHA256,
                "transaction_current_source_fifty_second_binding_pair_changed")


def require_fifty_second_predecessor(request, previous, *, raw=None):
    """Check the exact retained v51 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_second_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_second_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_second_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_second_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_FIRST_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 579
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_first_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_second_previous_committed_changed")
    return committed_path, committed_raw


def fifty_third_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_third_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_third_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source250 to Source251 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_THIRD_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_third_layer_required")
    require(CURRENT_SOURCE_FIFTY_THIRD_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_THIRD_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_THIRD_NATIVE_FILES,
            "transaction_current_source_fifty_third_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_third_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_third_home_required")
        require(context["previous_native_update"] == fifty_third_predecessor_ref(home),
                "transaction_current_source_fifty_third_previous_request_pin_changed")
        for key, ref in fifty_third_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_third_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_third_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 250 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 583,
                "transaction_current_source_fifty_third_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_THIRD_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_third_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_THIRD_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_THIRD_PATCH_SHA256,
                "transaction_current_source_fifty_third_binding_pair_changed")


def require_fifty_third_predecessor(request, previous, *, raw=None):
    """Check the exact retained v52 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_third_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_third_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_third_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_third_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_SECOND_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 581
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_second_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_third_previous_committed_changed")
    return committed_path, committed_raw

def fifty_fourth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_fourth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_fourth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source251 to Source252 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_FOURTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_fourth_layer_required")
    require(CURRENT_SOURCE_FIFTY_FOURTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_FOURTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_FOURTH_NATIVE_FILES,
            "transaction_current_source_fifty_fourth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_fourth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_fourth_home_required")
        require(context["previous_native_update"] == fifty_fourth_predecessor_ref(home),
                "transaction_current_source_fifty_fourth_previous_request_pin_changed")
        for key, ref in fifty_fourth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_fourth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_fourth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 251 and request.get("installed_files") == 17896
                and type(project_files) is dict and len(project_files) == 585,
                "transaction_current_source_fifty_fourth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_FOURTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_fourth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_FOURTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_FOURTH_PATCH_SHA256,
                "transaction_current_source_fifty_fourth_binding_pair_changed")


def require_fifty_fourth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v53 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_fourth_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_fourth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_fourth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_fourth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_THIRD_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 583
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_third_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_fourth_previous_committed_changed")
    return committed_path, committed_raw

def fifty_fifth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_fifth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_fifth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source252 to Source253 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_FIFTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_fifth_layer_required")
    require(CURRENT_SOURCE_FIFTY_FIFTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_FIFTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_FIFTH_NATIVE_FILES,
            "transaction_current_source_fifty_fifth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_fifth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_fifth_home_required")
        require(context["previous_native_update"] == fifty_fifth_predecessor_ref(home),
                "transaction_current_source_fifty_fifth_previous_request_pin_changed")
        for key, ref in fifty_fifth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_fifth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_fifth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 252 and request.get("installed_files") == 17898
                and type(project_files) is dict and len(project_files) == 587,
                "transaction_current_source_fifty_fifth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_FIFTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_fifth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_FIFTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_FIFTH_PATCH_SHA256,
                "transaction_current_source_fifty_fifth_binding_pair_changed")


def require_fifty_fifth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v54 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_fifth_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_fifth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_fifth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_fifth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_FOURTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 585
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_fourth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_fifth_previous_committed_changed")
    return committed_path, committed_raw


def fifty_sixth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_sixth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_sixth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source253 to Source254 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_SIXTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_sixth_layer_required")
    require(CURRENT_SOURCE_FIFTY_SIXTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_SIXTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_SIXTH_NATIVE_FILES,
            "transaction_current_source_fifty_sixth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_sixth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_sixth_home_required")
        require(context["previous_native_update"] == fifty_sixth_predecessor_ref(home),
                "transaction_current_source_fifty_sixth_previous_request_pin_changed")
        for key, ref in fifty_sixth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_sixth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_sixth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 253 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 589,
                "transaction_current_source_fifty_sixth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_SIXTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_sixth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_SIXTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_SIXTH_PATCH_SHA256,
                "transaction_current_source_fifty_sixth_binding_pair_changed")


def require_fifty_sixth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v55 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_sixth_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_sixth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_sixth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_sixth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_FIFTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 587
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_fifth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_sixth_previous_committed_changed")
    return committed_path, committed_raw


def fifty_seventh_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_seventh_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_seventh_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source254 to Source255 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_SEVENTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_seventh_layer_required")
    require(CURRENT_SOURCE_FIFTY_SEVENTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_SEVENTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_SEVENTH_NATIVE_FILES,
            "transaction_current_source_fifty_seventh_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_seventh_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_seventh_home_required")
        require(context["previous_native_update"] == fifty_seventh_predecessor_ref(home),
                "transaction_current_source_fifty_seventh_previous_request_pin_changed")
        for key, ref in fifty_seventh_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_seventh_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_seventh_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 254 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 591,
                "transaction_current_source_fifty_seventh_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_SEVENTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_seventh_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_SEVENTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_SEVENTH_PATCH_SHA256,
                "transaction_current_source_fifty_seventh_binding_pair_changed")


def require_fifty_seventh_predecessor(request, previous, *, raw=None):
    """Check the exact retained v56 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_seventh_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_seventh_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_seventh_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_seventh_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_SIXTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 589
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_sixth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_seventh_previous_committed_changed")
    return committed_path, committed_raw


def fifty_eighth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_eighth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_eighth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source255 to Source256 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_EIGHTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_eighth_layer_required")
    require(CURRENT_SOURCE_FIFTY_EIGHTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_EIGHTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_EIGHTH_NATIVE_FILES,
            "transaction_current_source_fifty_eighth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_eighth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_eighth_home_required")
        require(context["previous_native_update"] == fifty_eighth_predecessor_ref(home),
                "transaction_current_source_fifty_eighth_previous_request_pin_changed")
        for key, ref in fifty_eighth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_eighth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_eighth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 255 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 593,
                "transaction_current_source_fifty_eighth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_EIGHTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_eighth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_EIGHTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_EIGHTH_PATCH_SHA256,
                "transaction_current_source_fifty_eighth_binding_pair_changed")


def require_fifty_eighth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v57 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_eighth_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_eighth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_eighth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_eighth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_SEVENTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 591
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_seventh_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_eighth_previous_committed_changed")
    return committed_path, committed_raw


def fifty_ninth_predecessor_ref(home):
    pin = CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def fifty_ninth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_fifty_ninth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source256 to Source257 publication before reading its inputs."""
    layer = CURRENT_SOURCE_FIFTY_NINTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_fifty_ninth_layer_required")
    require(CURRENT_SOURCE_FIFTY_NINTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_NINTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_FIFTY_NINTH_NATIVE_FILES,
            "transaction_current_source_fifty_ninth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_fifty_ninth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_fifty_ninth_home_required")
        require(context["previous_native_update"] == fifty_ninth_predecessor_ref(home),
                "transaction_current_source_fifty_ninth_previous_request_pin_changed")
        for key, ref in fifty_ninth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_fifty_ninth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_fifty_ninth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 256 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 595,
                "transaction_current_source_fifty_ninth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_FIFTY_NINTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_fifty_ninth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_FIFTY_NINTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_FIFTY_NINTH_PATCH_SHA256,
                "transaction_current_source_fifty_ninth_binding_pair_changed")


def require_fifty_ninth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v58 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == fifty_ninth_predecessor_ref(request["home"]),
            "transaction_current_source_fifty_ninth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_fifty_ninth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_fifty_ninth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_EIGHTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 593
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_eighth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_fifty_ninth_previous_committed_changed")
    return committed_path, committed_raw


def sixtieth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTIETH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixtieth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTIETH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTIETH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTIETH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTIETH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixtieth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source257 to Source258 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTIETH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixtieth_layer_required")
    require(CURRENT_SOURCE_SIXTIETH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_SIXTIETH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_SIXTIETH_NATIVE_FILES,
            "transaction_current_source_sixtieth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixtieth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixtieth_home_required")
        require(context["previous_native_update"] == sixtieth_predecessor_ref(home),
                "transaction_current_source_sixtieth_previous_request_pin_changed")
        for key, ref in sixtieth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixtieth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixtieth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 257 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 597,
                "transaction_current_source_sixtieth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTIETH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixtieth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTIETH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTIETH_PATCH_SHA256,
                "transaction_current_source_sixtieth_binding_pair_changed")


def require_sixtieth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v59 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixtieth_predecessor_ref(request["home"]),
            "transaction_current_source_sixtieth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixtieth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixtieth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_FIFTY_NINTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 595
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_fifty_ninth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTIETH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixtieth_previous_committed_changed")
    return committed_path, committed_raw


def sixty_first_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_first_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_first_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source258 to Source259 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_FIRST_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_first_layer_required")
    require(CURRENT_SOURCE_SIXTY_FIRST_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_FIRST_PATCH_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_FIRST_NATIVE_FILES,
            "transaction_current_source_sixty_first_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_first_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_first_home_required")
        require(context["previous_native_update"] == sixty_first_predecessor_ref(home),
                "transaction_current_source_sixty_first_previous_request_pin_changed")
        for key, ref in sixty_first_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_first_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_first_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 258 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 599,
                "transaction_current_source_sixty_first_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_FIRST_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_first_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_FIRST_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_FIRST_PATCH_SHA256,
                "transaction_current_source_sixty_first_binding_pair_changed")


def require_sixty_first_predecessor(request, previous, *, raw=None):
    """Check the exact retained v60 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_first_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_first_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_first_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_first_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTIETH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 597
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixtieth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_first_previous_committed_changed")
    return committed_path, committed_raw


def sixty_second_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_second_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_second_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source259 to Source260 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_SECOND_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_second_layer_required")
    require(CURRENT_SOURCE_SIXTY_SECOND_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_SECOND_PATCH_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_SECOND_NATIVE_FILES,
            "transaction_current_source_sixty_second_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_second_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_second_home_required")
        require(context["previous_native_update"] == sixty_second_predecessor_ref(home),
                "transaction_current_source_sixty_second_previous_request_pin_changed")
        for key, ref in sixty_second_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_second_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_second_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 259 and request.get("installed_files") == 17899
                and type(project_files) is dict and len(project_files) == 601,
                "transaction_current_source_sixty_second_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_SECOND_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_second_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_SECOND_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_SECOND_PATCH_SHA256,
                "transaction_current_source_sixty_second_binding_pair_changed")


def require_sixty_second_predecessor(request, previous, *, raw=None):
    """Check the exact retained v61 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_second_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_second_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_second_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_second_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_FIRST_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 599
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_first_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_second_previous_committed_changed")
    return committed_path, committed_raw


def sixty_third_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_third_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_third_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source260 to Source261 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_THIRD_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_third_layer_required")
    require(CURRENT_SOURCE_SIXTY_THIRD_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_THIRD_PATCH_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_THIRD_NATIVE_FILES,
            "transaction_current_source_sixty_third_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_third_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_third_home_required")
        require(context["previous_native_update"] == sixty_third_predecessor_ref(home),
                "transaction_current_source_sixty_third_previous_request_pin_changed")
        for key, ref in sixty_third_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_third_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_third_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 260 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 603,
                "transaction_current_source_sixty_third_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_THIRD_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_third_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_THIRD_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_THIRD_PATCH_SHA256,
                "transaction_current_source_sixty_third_binding_pair_changed")


def require_sixty_third_predecessor(request, previous, *, raw=None):
    """Check the exact retained v62 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_third_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_third_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_third_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_third_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_SECOND_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 601
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_second_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_third_previous_committed_changed")
    return committed_path, committed_raw


def sixty_fourth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_fourth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_fourth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source261 to Source262 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_FOURTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_fourth_layer_required")
    require(CURRENT_SOURCE_SIXTY_FOURTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_FOURTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_FOURTH_NATIVE_FILES,
            "transaction_current_source_sixty_fourth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_fourth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_fourth_home_required")
        require(context["previous_native_update"] == sixty_fourth_predecessor_ref(home),
                "transaction_current_source_sixty_fourth_previous_request_pin_changed")
        for key, ref in sixty_fourth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_fourth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_fourth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 261 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 605,
                "transaction_current_source_sixty_fourth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_FOURTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_fourth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_FOURTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_FOURTH_PATCH_SHA256,
                "transaction_current_source_sixty_fourth_binding_pair_changed")


def require_sixty_fourth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v63 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_fourth_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_fourth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_fourth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_fourth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_THIRD_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 603
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_third_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_fourth_previous_committed_changed")
    return committed_path, committed_raw


def sixty_fifth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_fifth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_fifth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source262 to Source263 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_FIFTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_fifth_layer_required")
    require(CURRENT_SOURCE_SIXTY_FIFTH_MANIFEST_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_FIFTH_PATCH_SHA256 is not None
            and CURRENT_SOURCE_SIXTY_FIFTH_NATIVE_FILES,
            "transaction_current_source_sixty_fifth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_fifth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_fifth_home_required")
        require(context["previous_native_update"] == sixty_fifth_predecessor_ref(home),
                "transaction_current_source_sixty_fifth_previous_request_pin_changed")
        for key, ref in sixty_fifth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_fifth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_fifth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 262 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 607,
                "transaction_current_source_sixty_fifth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_FIFTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_fifth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_FIFTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_FIFTH_PATCH_SHA256,
                "transaction_current_source_sixty_fifth_binding_pair_changed")


def require_sixty_fifth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v64 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_fifth_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_fifth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_fifth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_fifth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_FOURTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 605
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_fourth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_fifth_previous_committed_changed")
    return committed_path, committed_raw


def sixty_sixth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_sixth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_sixth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source263 to Source264 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_SIXTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_sixth_layer_required")
    pins = (CURRENT_SOURCE_SIXTY_SIXTH_MANIFEST_SHA256, CURRENT_SOURCE_SIXTY_SIXTH_PATCH_SHA256,
            CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_REQUEST_SHA256, CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_COMMITTED_SHA256,
            CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_RECEIPT_SHA256, CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_MARKER_SHA256,
            CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_STAMP_SHA256)
    require(CURRENT_SOURCE_SIXTY_SIXTH_NATIVE_FILES and all(
            type(pin) is str and __import__("re").fullmatch("[0-9a-f]{64}", pin) for pin in pins),
            "transaction_current_source_sixty_sixth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_sixth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_sixth_home_required")
        require(context["previous_native_update"] == sixty_sixth_predecessor_ref(home),
                "transaction_current_source_sixty_sixth_previous_request_pin_changed")
        for key, ref in sixty_sixth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_sixth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_sixth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 263 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 609,
                "transaction_current_source_sixty_sixth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_SIXTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_sixth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_SIXTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_SIXTH_PATCH_SHA256,
                "transaction_current_source_sixty_sixth_binding_pair_changed")


def require_sixty_sixth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v65 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_sixth_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_sixth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_sixth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_sixth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_FIFTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 607
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_fifth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_sixth_previous_committed_changed")
    return committed_path, committed_raw


def sixty_seventh_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_seventh_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_seventh_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source264 to Source265 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_SEVENTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_seventh_layer_required")
    pins = (CURRENT_SOURCE_SIXTY_SEVENTH_MANIFEST_SHA256, CURRENT_SOURCE_SIXTY_SEVENTH_PATCH_SHA256,
            CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_REQUEST_SHA256, CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_COMMITTED_SHA256,
            CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_RECEIPT_SHA256, CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_MARKER_SHA256,
            CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_STAMP_SHA256)
    require(CURRENT_SOURCE_SIXTY_SEVENTH_NATIVE_FILES and all(
            type(pin) is str and __import__("re").fullmatch("[0-9a-f]{64}", pin) for pin in pins),
            "transaction_current_source_sixty_seventh_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_seventh_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_seventh_home_required")
        require(context["previous_native_update"] == sixty_seventh_predecessor_ref(home),
                "transaction_current_source_sixty_seventh_previous_request_pin_changed")
        for key, ref in sixty_seventh_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_seventh_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_seventh_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 264 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 611,
                "transaction_current_source_sixty_seventh_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_SEVENTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_seventh_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_SEVENTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_SEVENTH_PATCH_SHA256,
                "transaction_current_source_sixty_seventh_binding_pair_changed")


def require_sixty_seventh_predecessor(request, previous, *, raw=None):
    """Check the exact retained v66 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_seventh_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_seventh_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_seventh_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_seventh_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_SIXTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 609
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_sixth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_seventh_previous_committed_changed")
    return committed_path, committed_raw


def sixty_eighth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_eighth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_eighth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source265 to Source266 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_EIGHTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_eighth_layer_required")
    pins = (CURRENT_SOURCE_SIXTY_EIGHTH_MANIFEST_SHA256, CURRENT_SOURCE_SIXTY_EIGHTH_PATCH_SHA256,
            CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_REQUEST_SHA256, CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_COMMITTED_SHA256,
            CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_RECEIPT_SHA256, CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_MARKER_SHA256,
            CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_STAMP_SHA256)
    require(CURRENT_SOURCE_SIXTY_EIGHTH_NATIVE_FILES and all(
            type(pin) is str and __import__("re").fullmatch("[0-9a-f]{64}", pin) for pin in pins),
            "transaction_current_source_sixty_eighth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_eighth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_eighth_home_required")
        require(context["previous_native_update"] == sixty_eighth_predecessor_ref(home),
                "transaction_current_source_sixty_eighth_previous_request_pin_changed")
        for key, ref in sixty_eighth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_eighth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_eighth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 265 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 613,
                "transaction_current_source_sixty_eighth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_EIGHTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_eighth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_EIGHTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_EIGHTH_PATCH_SHA256,
                "transaction_current_source_sixty_eighth_binding_pair_changed")


def require_sixty_eighth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v67 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_eighth_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_eighth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_eighth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_eighth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_SEVENTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 611
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_seventh_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_eighth_previous_committed_changed")
    return committed_path, committed_raw


def sixty_ninth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def sixty_ninth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_sixty_ninth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source266 to Source267 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SIXTY_NINTH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_sixty_ninth_layer_required")
    pins = (CURRENT_SOURCE_SIXTY_NINTH_MANIFEST_SHA256, CURRENT_SOURCE_SIXTY_NINTH_PATCH_SHA256,
            CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_REQUEST_SHA256, CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_COMMITTED_SHA256,
            CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_RECEIPT_SHA256, CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_MARKER_SHA256,
            CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_STAMP_SHA256)
    require(CURRENT_SOURCE_SIXTY_NINTH_NATIVE_FILES and all(
            type(pin) is str and __import__("re").fullmatch("[0-9a-f]{64}", pin) for pin in pins),
            "transaction_current_source_sixty_ninth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_sixty_ninth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_sixty_ninth_home_required")
        require(context["previous_native_update"] == sixty_ninth_predecessor_ref(home),
                "transaction_current_source_sixty_ninth_previous_request_pin_changed")
        for key, ref in sixty_ninth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_sixty_ninth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_sixty_ninth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 266 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 615,
                "transaction_current_source_sixty_ninth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SIXTY_NINTH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_sixty_ninth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SIXTY_NINTH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SIXTY_NINTH_PATCH_SHA256,
                "transaction_current_source_sixty_ninth_binding_pair_changed")


def require_sixty_ninth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v68 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == sixty_ninth_predecessor_ref(request["home"]),
            "transaction_current_source_sixty_ninth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_sixty_ninth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_sixty_ninth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_EIGHTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 613
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_eighth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_sixty_ninth_previous_committed_changed")
    return committed_path, committed_raw


def seventieth_predecessor_ref(home):
    pin = CURRENT_SOURCE_SEVENTIETH_PREVIOUS_REQUEST_SHA256
    path = Path(home) / "preparation" / f"ordinary-source-update-v45-{pin[:16]}" / "request.json"
    return {"path": str(path), "sha256": pin}


def seventieth_metadata_refs(home):
    metadata = {
        "marker": ("FRIDAY-INSTALL.json", CURRENT_SOURCE_SEVENTIETH_PREVIOUS_MARKER_SHA256),
        "source_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SEVENTIETH_PREVIOUS_RECEIPT_SHA256),
        "target_receipt": ("hermes-agent.source.json", CURRENT_SOURCE_SEVENTIETH_PREVIOUS_RECEIPT_SHA256),
        "stamp": ("hermes-agent/install-stamp.json", CURRENT_SOURCE_SEVENTIETH_PREVIOUS_STAMP_SHA256),
    }
    return {key: {"path": str(Path(home) / relative), "sha256": sha256}
            for key, (relative, sha256) in metadata.items()}


def require_seventieth_source_binding(layer_names, project_files=None, *, request=None):
    """Bind the exact Source267 to Source268 publication before reading its inputs."""
    layer = CURRENT_SOURCE_SEVENTIETH_LAYER
    selected = isinstance(layer_names, (list, tuple)) and layer in layer_names
    context = request.get("current_source_successor") if request is not None else None
    context_selected = (type(context) is dict
                        and context.get("schema") == CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA)
    if not selected and not context_selected:
        return
    require(selected and tuple(layer_names) == (layer,),
            "transaction_current_source_exact_seventieth_layer_required")
    pins = (CURRENT_SOURCE_SEVENTIETH_MANIFEST_SHA256, CURRENT_SOURCE_SEVENTIETH_PATCH_SHA256,
            CURRENT_SOURCE_SEVENTIETH_PREVIOUS_REQUEST_SHA256, CURRENT_SOURCE_SEVENTIETH_PREVIOUS_COMMITTED_SHA256,
            CURRENT_SOURCE_SEVENTIETH_PREVIOUS_RECEIPT_SHA256, CURRENT_SOURCE_SEVENTIETH_PREVIOUS_MARKER_SHA256,
            CURRENT_SOURCE_SEVENTIETH_PREVIOUS_STAMP_SHA256)
    require(CURRENT_SOURCE_SEVENTIETH_NATIVE_FILES and all(
            type(pin) is str and __import__("re").fullmatch("[0-9a-f]{64}", pin) for pin in pins),
            "transaction_current_source_seventieth_binding_required")
    manifest = f"patches/hermes/{layer}-manifest.json"
    patch = f"patches/hermes/{layer}.patch"
    if request is not None:
        require(request.get("schema") == SCHEMA_EXPLICIT and context_selected
                and set(context) == {"schema", "root_project_update", "previous_native_update"},
                "transaction_current_source_seventieth_context_required")
        home = request.get("home")
        require(type(home) is str and Path(home).is_absolute(),
                "transaction_current_source_seventieth_home_required")
        require(context["previous_native_update"] == seventieth_predecessor_ref(home),
                "transaction_current_source_seventieth_previous_request_pin_changed")
        for key, ref in seventieth_metadata_refs(home).items():
            require(request.get(key) == ref,
                    "transaction_current_source_seventieth_previous_metadata_pin_changed:" + key)
        require(request.get("current_input") == request.get("candidate_input")
                and request.get("current_input") != request.get("previous_input"),
                "transaction_current_source_seventieth_input_pin_changed")
        project_files = request.get("project_inventory")
        require(request.get("installed_layers") == 267 and request.get("installed_files") == 17901
                and type(project_files) is dict and len(project_files) == 617,
                "transaction_current_source_seventieth_inventory_count_changed")
        require(request.get("layer_manifest_updates") == [manifest]
                and request.get("project_file_updates") == [CURRENT_SOURCE_SEVENTIETH_HELPER]
                and all(request.get(key) == [] for key in ("plugin_set", "plugin_additions", "staged_files")),
                "transaction_current_source_seventieth_project_scope_changed")
    if project_files is not None:
        require(type(project_files) is dict
                and project_files.get(manifest) == CURRENT_SOURCE_SEVENTIETH_MANIFEST_SHA256
                and project_files.get(patch) == CURRENT_SOURCE_SEVENTIETH_PATCH_SHA256,
                "transaction_current_source_seventieth_binding_pair_changed")


def require_seventieth_predecessor(request, previous, *, raw=None):
    """Check the exact retained v69 request and its successful commit."""
    context = request["current_source_successor"]
    ref = context["previous_native_update"]
    require(ref == seventieth_predecessor_ref(request["home"]),
            "transaction_current_source_seventieth_previous_request_pin_changed")
    path = Path(ref["path"])
    committed_path = path.with_name("committed.json")
    require(path.resolve() == path and committed_path.resolve() == committed_path,
            "transaction_current_source_seventieth_previous_request_path_changed")
    raw = owned_file(path) if raw is None else raw
    require(digest(raw) == ref["sha256"],
            "transaction_current_source_seventieth_previous_request_changed")
    predecessor = json.loads(raw)
    previous_context = predecessor["current_source_successor"]
    require(predecessor["schema"] == SCHEMA_EXPLICIT
            and predecessor["home"] == request["home"]
            and predecessor["layer_names"] == [CURRENT_SOURCE_SIXTY_NINTH_LAYER]
            and predecessor["current_input"] == request["previous_input"]
            and len(previous["project_files"]) == 615
            and predecessor["project_inventory"] == previous["project_files"]
            and previous_context["schema"] == CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA
            and previous_context["root_project_update"] == context["root_project_update"],
            "transaction_current_source_sixty_ninth_predecessor_lineage_changed")
    committed_raw = owned_file(committed_path)
    require(digest(committed_raw) == CURRENT_SOURCE_SEVENTIETH_PREVIOUS_COMMITTED_SHA256,
            "transaction_current_source_seventieth_previous_committed_changed")
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
    if layer_names == (CURRENT_SOURCE_SEVENTIETH_LAYER,):
        helper = CURRENT_SOURCE_SEVENTIETH_HELPER
        require(len(previous_files) == 615 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_seventieth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_NINTH_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_NINTH_HELPER
        require(len(previous_files) == 613 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_ninth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_EIGHTH_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_EIGHTH_HELPER
        require(len(previous_files) == 611 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_eighth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_SEVENTH_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_SEVENTH_HELPER
        require(len(previous_files) == 609 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_seventh_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_SIXTH_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_SIXTH_HELPER
        require(len(previous_files) == 607 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_sixth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_FIFTH_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_FIFTH_HELPER
        require(len(previous_files) == 605 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_fifth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_FOURTH_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_FOURTH_HELPER
        require(len(previous_files) == 603 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_fourth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_THIRD_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_THIRD_HELPER
        require(len(previous_files) == 601 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_third_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_SECOND_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_SECOND_HELPER
        require(len(previous_files) == 599 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_second_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTY_FIRST_LAYER,):
        helper = CURRENT_SOURCE_SIXTY_FIRST_HELPER
        require(len(previous_files) == 597 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixty_first_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_SIXTIETH_LAYER,):
        helper = CURRENT_SOURCE_SIXTIETH_HELPER
        require(len(previous_files) == 595 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_sixtieth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_NINTH_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_NINTH_HELPER
        require(len(previous_files) == 593 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_ninth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_EIGHTH_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_EIGHTH_HELPER
        require(len(previous_files) == 591 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_eighth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_SEVENTH_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_SEVENTH_HELPER
        require(len(previous_files) == 589 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_seventh_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_SIXTH_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_SIXTH_HELPER
        require(len(previous_files) == 587 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_sixth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_FIFTH_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_FIFTH_HELPER
        require(len(previous_files) == 585 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_fifth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_FOURTH_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_FOURTH_HELPER
        require(len(previous_files) == 583 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_fourth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_THIRD_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_THIRD_HELPER
        require(len(previous_files) == 581 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_third_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_SECOND_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_SECOND_HELPER
        require(len(previous_files) == 579 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_second_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTY_FIRST_LAYER,):
        helper = CURRENT_SOURCE_FIFTY_FIRST_HELPER
        require(len(previous_files) == 577 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fifty_first_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FIFTIETH_LAYER,):
        helper = CURRENT_SOURCE_FIFTIETH_HELPER
        require(len(previous_files) == 575 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_fiftieth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FORTY_NINTH_LAYER,):
        helper = CURRENT_SOURCE_FORTY_NINTH_HELPER
        require(len(previous_files) == 573 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_forty_ninth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FORTY_EIGHTH_LAYER,):
        helper = CURRENT_SOURCE_FORTY_EIGHTH_HELPER
        require(len(previous_files) == 571 and current_files.keys() - previous_files.keys() == additions
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper]
                and all(current_files.get(name) == sha for name, sha in previous_files.items()
                        if name != helper),
                "transaction_current_source_forty_eighth_project_scope_changed")
    if layer_names == (CURRENT_SOURCE_FORTY_SEVENTH_LAYER,):
        helper = CURRENT_SOURCE_FORTY_SEVENTH_HELPER
        require(len(previous_files) == 569 and not additions.intersection(previous_files)
                and helper in previous_files and helper in current_files
                and previous_files[helper] != current_files[helper],
                "transaction_current_source_forty_seventh_project_scope_changed")
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
    require_seventieth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SEVENTIETH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SEVENTIETH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_seventieth_previous_receipt_changed")
    require_sixty_ninth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_NINTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_NINTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_ninth_previous_receipt_changed")
    require_sixty_eighth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_EIGHTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_EIGHTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_eighth_previous_receipt_changed")
    require_sixty_seventh_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_SEVENTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_SEVENTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_seventh_previous_receipt_changed")
    require_sixty_sixth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_SIXTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_SIXTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_sixth_previous_receipt_changed")
    require_sixty_fifth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_FIFTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_FIFTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_fifth_previous_receipt_changed")
    require_sixty_fourth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_FOURTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_FOURTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_fourth_previous_receipt_changed")
    require_sixty_third_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_THIRD_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_THIRD_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_third_previous_receipt_changed")
    require_sixty_second_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_SECOND_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_SECOND_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_second_previous_receipt_changed")
    require_sixty_first_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTY_FIRST_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTY_FIRST_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixty_first_previous_receipt_changed")
    require_sixtieth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_SIXTIETH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_SIXTIETH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_sixtieth_previous_receipt_changed")
    require_fifty_ninth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_NINTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_NINTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_ninth_previous_receipt_changed")
    require_fifty_eighth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_EIGHTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_EIGHTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_eighth_previous_receipt_changed")
    require_fifty_seventh_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_SEVENTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_SEVENTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_seventh_previous_receipt_changed")
    require_fifty_sixth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_SIXTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_SIXTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_sixth_previous_receipt_changed")
    require_fifty_fifth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_FIFTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_FIFTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_fifth_previous_receipt_changed")
    require_fifty_fourth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_FOURTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_FOURTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_fourth_previous_receipt_changed")
    require_fifty_third_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_THIRD_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_THIRD_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_third_previous_receipt_changed")
    require_fifty_second_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_SECOND_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_SECOND_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_second_previous_receipt_changed")
    require_fifty_first_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTY_FIRST_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTY_FIRST_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fifty_first_previous_receipt_changed")
    require_fiftieth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FIFTIETH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FIFTIETH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_fiftieth_previous_receipt_changed")
    require_forty_ninth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_NINTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_NINTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_ninth_previous_receipt_changed")
    require_forty_eighth_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_EIGHTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_EIGHTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_eighth_previous_receipt_changed")
    require_forty_seventh_source_binding(layer_names, project_files or {})
    if CURRENT_SOURCE_FORTY_SEVENTH_LAYER in layer_names:
        require(digest(encoded(receipt)) == CURRENT_SOURCE_FORTY_SEVENTH_PREVIOUS_RECEIPT_SHA256,
                "transaction_current_source_forty_seventh_previous_receipt_changed")
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
        if name == CURRENT_SOURCE_SEVENTIETH_LAYER:
            require(files == list(CURRENT_SOURCE_SEVENTIETH_NATIVE_FILES),
                    "transaction_current_source_seventieth_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_NINTH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_NINTH_NATIVE_FILES),
                    "transaction_current_source_sixty_ninth_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_EIGHTH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_EIGHTH_NATIVE_FILES),
                    "transaction_current_source_sixty_eighth_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_SEVENTH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_SEVENTH_NATIVE_FILES),
                    "transaction_current_source_sixty_seventh_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_SIXTH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_SIXTH_NATIVE_FILES),
                    "transaction_current_source_sixty_sixth_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_FIFTH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_FIFTH_NATIVE_FILES),
                    "transaction_current_source_sixty_fifth_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_FOURTH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_FOURTH_NATIVE_FILES),
                    "transaction_current_source_sixty_fourth_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_THIRD_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_THIRD_NATIVE_FILES),
                    "transaction_current_source_sixty_third_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_SECOND_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_SECOND_NATIVE_FILES),
                    "transaction_current_source_sixty_second_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTY_FIRST_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTY_FIRST_NATIVE_FILES),
                    "transaction_current_source_sixty_first_native_scope_changed")
        if name == CURRENT_SOURCE_SIXTIETH_LAYER:
            require(files == list(CURRENT_SOURCE_SIXTIETH_NATIVE_FILES),
                    "transaction_current_source_sixtieth_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_NINTH_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_NINTH_NATIVE_FILES),
                    "transaction_current_source_fifty_ninth_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_EIGHTH_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_EIGHTH_NATIVE_FILES),
                    "transaction_current_source_fifty_eighth_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_SEVENTH_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_SEVENTH_NATIVE_FILES),
                    "transaction_current_source_fifty_seventh_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_SIXTH_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_SIXTH_NATIVE_FILES),
                    "transaction_current_source_fifty_sixth_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_FIFTH_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_FIFTH_NATIVE_FILES),
                    "transaction_current_source_fifty_fifth_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_FOURTH_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_FOURTH_NATIVE_FILES),
                    "transaction_current_source_fifty_fourth_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_THIRD_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_THIRD_NATIVE_FILES),
                    "transaction_current_source_fifty_third_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_SECOND_LAYER:
            require(files == list(CURRENT_SOURCE_FIFTY_SECOND_NATIVE_FILES),
                    "transaction_current_source_fifty_second_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTY_FIRST_LAYER:
            require(files == [CURRENT_SOURCE_FIFTY_FIRST_NATIVE_FILE],
                    "transaction_current_source_fifty_first_native_scope_changed")
        if name == CURRENT_SOURCE_FIFTIETH_LAYER:
            require(files == [CURRENT_SOURCE_FIFTIETH_NATIVE_FILE],
                    "transaction_current_source_fiftieth_native_scope_changed")
        if name == CURRENT_SOURCE_FORTY_NINTH_LAYER:
            require(files == list(CURRENT_SOURCE_FORTY_NINTH_NATIVE_FILES),
                    "transaction_current_source_forty_ninth_native_scope_changed")
        if name == CURRENT_SOURCE_FORTY_EIGHTH_LAYER:
            require(files == [CURRENT_SOURCE_FORTY_EIGHTH_NATIVE_FILE],
                    "transaction_current_source_forty_eighth_native_scope_changed")
        if name == CURRENT_SOURCE_FORTY_SEVENTH_LAYER:
            require(all(type(row) is dict and row.get("mode") == "100644"
                            and row.get("new_file") is False for row in files)
                    and tuple(row.get("path") for row in files) == CURRENT_SOURCE_FORTY_SEVENTH_NATIVE_FILES,
                    "transaction_current_source_forty_seventh_native_scope_changed")
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
                    CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA,
                    CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA)
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
    require_seventieth_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_ninth_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_eighth_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_seventh_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_sixth_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_fifth_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_fourth_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_third_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_second_source_binding(request.get("layer_names", ()), request=request)
    require_sixty_first_source_binding(request.get("layer_names", ()), request=request)
    require_sixtieth_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_ninth_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_eighth_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_seventh_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_sixth_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_fifth_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_fourth_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_third_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_second_source_binding(request.get("layer_names", ()), request=request)
    require_fifty_first_source_binding(request.get("layer_names", ()), request=request)
    require_fiftieth_source_binding(request.get("layer_names", ()), request=request)
    require_forty_ninth_source_binding(request.get("layer_names", ()), request=request)
    require_forty_eighth_source_binding(request.get("layer_names", ()), request=request)
    require_forty_seventh_source_binding(request.get("layer_names", ()), request=request)
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
        CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA, CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA,
        CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA)
    forty_third = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA
    forty_fourth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA
    forty_fifth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA
    forty_sixth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA
    forty_seventh = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA
    forty_eighth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA
    forty_ninth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA
    seventieth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA
    sixty_ninth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA
    sixty_eighth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA
    sixty_seventh = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA
    sixty_sixth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA
    sixty_fifth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA
    sixty_fourth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA
    sixty_third = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA
    sixty_second = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA
    sixty_first = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA
    sixtieth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA
    fifty_ninth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA
    fifty_eighth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA
    fifty_seventh = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA
    fifty_sixth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA
    fifty_fifth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA
    fifty_fourth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA
    fifty_third = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA
    fifty_second = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA
    fifty_first = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA
    fiftieth = current_context and request["current_source_successor"]["schema"] == CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA
    bound_current = forty_third or forty_fourth or forty_fifth or forty_sixth or forty_seventh or forty_eighth or forty_ninth or fiftieth or fifty_first or fifty_second or fifty_third or fifty_fourth or fifty_fifth or fifty_sixth or fifty_seventh or fifty_eighth or fifty_ninth or sixtieth or sixty_first or sixty_second or sixty_third or sixty_fourth or sixty_fifth or sixty_sixth or sixty_seventh or sixty_eighth or sixty_ninth or seventieth
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
    if seventieth:
        native_committed_path, native_committed_raw = require_seventieth_predecessor(request, previous_input)
    if sixty_ninth:
        native_committed_path, native_committed_raw = require_sixty_ninth_predecessor(request, previous_input)
    if sixty_eighth:
        native_committed_path, native_committed_raw = require_sixty_eighth_predecessor(request, previous_input)
    if sixty_seventh:
        native_committed_path, native_committed_raw = require_sixty_seventh_predecessor(request, previous_input)
    if sixty_sixth:
        native_committed_path, native_committed_raw = require_sixty_sixth_predecessor(request, previous_input)
    if sixty_fifth:
        native_committed_path, native_committed_raw = require_sixty_fifth_predecessor(request, previous_input)
    if sixty_fourth:
        native_committed_path, native_committed_raw = require_sixty_fourth_predecessor(request, previous_input)
    if sixty_third:
        native_committed_path, native_committed_raw = require_sixty_third_predecessor(request, previous_input)
    if sixty_second:
        native_committed_path, native_committed_raw = require_sixty_second_predecessor(request, previous_input)
    if sixty_first:
        native_committed_path, native_committed_raw = require_sixty_first_predecessor(request, previous_input)
    if sixtieth:
        native_committed_path, native_committed_raw = require_sixtieth_predecessor(request, previous_input)
    if fifty_ninth:
        native_committed_path, native_committed_raw = require_fifty_ninth_predecessor(request, previous_input)
    if fifty_eighth:
        native_committed_path, native_committed_raw = require_fifty_eighth_predecessor(request, previous_input)
    if fifty_seventh:
        native_committed_path, native_committed_raw = require_fifty_seventh_predecessor(request, previous_input)
    if fifty_sixth:
        native_committed_path, native_committed_raw = require_fifty_sixth_predecessor(request, previous_input)
    if fifty_fifth:
        native_committed_path, native_committed_raw = require_fifty_fifth_predecessor(request, previous_input)
    if fifty_fourth:
        native_committed_path, native_committed_raw = require_fifty_fourth_predecessor(request, previous_input)
    if fifty_third:
        native_committed_path, native_committed_raw = require_fifty_third_predecessor(request, previous_input)
    if fifty_second:
        native_committed_path, native_committed_raw = require_fifty_second_predecessor(request, previous_input)
    if fifty_first:
        native_committed_path, native_committed_raw = require_fifty_first_predecessor(request, previous_input)
    if fiftieth:
        native_committed_path, native_committed_raw = require_fiftieth_predecessor(request, previous_input)
    if forty_ninth:
        native_committed_path, native_committed_raw = require_forty_ninth_predecessor(request, previous_input)
    if forty_eighth:
        native_committed_path, native_committed_raw = require_forty_eighth_predecessor(request, previous_input)
    if forty_seventh:
        native_committed_path, native_committed_raw = require_forty_seventh_predecessor(request, previous_input)
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
        if seventieth:
            layer = CURRENT_SOURCE_SEVENTIETH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SEVENTIETH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SEVENTIETH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_seventieth_cas_scope_changed")
            before_pins[str(source / "tools/scoped_pdf_ocr.py")]["mode"] = 0o600
        if sixty_ninth:
            layer = CURRENT_SOURCE_SIXTY_NINTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_NINTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_NINTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_ninth_cas_scope_changed")
            for name, mode in (
                ('gateway/run_inbound.py', 0o600),
                ('gateway/run_inbound_media.py', 0o600),
                ('plugins/platforms/telegram/telegram_file_boundary.py', 0o600),
            ):
                before_pins[str(source / name)]["mode"] = mode
        if sixty_eighth:
            layer = CURRENT_SOURCE_SIXTY_EIGHTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_EIGHTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_EIGHTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_eighth_cas_scope_changed")
            for name, mode in (
                ('agent/message_sanitization.py', 0o600),
                ('agent/turn_tool_round.py', 0o644),
                ('tools/tool_search_validation.py', 0o644),
            ):
                before_pins[str(source / name)]["mode"] = mode
        if sixty_seventh:
            layer = CURRENT_SOURCE_SIXTY_SEVENTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_SEVENTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_SEVENTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_seventh_cas_scope_changed")
        if sixty_sixth:
            layer = CURRENT_SOURCE_SIXTY_SIXTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_SIXTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_SIXTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_sixth_cas_scope_changed")
        if sixty_fifth:
            layer = CURRENT_SOURCE_SIXTY_FIFTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_FIFTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_FIFTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_fifth_cas_scope_changed")
        if sixty_fourth:
            layer = CURRENT_SOURCE_SIXTY_FOURTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_FOURTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_FOURTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_fourth_cas_scope_changed")
        if sixty_third:
            layer = CURRENT_SOURCE_SIXTY_THIRD_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_THIRD_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_THIRD_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_third_cas_scope_changed")
        if sixty_second:
            layer = CURRENT_SOURCE_SIXTY_SECOND_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_SECOND_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_SECOND_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_second_cas_scope_changed")
        if sixty_first:
            layer = CURRENT_SOURCE_SIXTY_FIRST_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTY_FIRST_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTY_FIRST_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixty_first_cas_scope_changed")
        if sixtieth:
            layer = CURRENT_SOURCE_SIXTIETH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_SIXTIETH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_SIXTIETH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_sixtieth_cas_scope_changed")
        if fifty_ninth:
            layer = CURRENT_SOURCE_FIFTY_NINTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_NINTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_NINTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_ninth_cas_scope_changed")
        if fifty_eighth:
            layer = CURRENT_SOURCE_FIFTY_EIGHTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_EIGHTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_EIGHTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_eighth_cas_scope_changed")
        if fifty_seventh:
            layer = CURRENT_SOURCE_FIFTY_SEVENTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_SEVENTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_SEVENTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_seventh_cas_scope_changed")
        if fifty_sixth:
            layer = CURRENT_SOURCE_FIFTY_SIXTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_SIXTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_SIXTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_sixth_cas_scope_changed")
        if fifty_fifth:
            layer = CURRENT_SOURCE_FIFTY_FIFTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_FIFTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_FIFTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_fifth_cas_scope_changed")
        if fifty_fourth:
            layer = CURRENT_SOURCE_FIFTY_FOURTH_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_FOURTH_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_FOURTH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_fourth_cas_scope_changed")
        if fifty_third:
            layer = CURRENT_SOURCE_FIFTY_THIRD_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_THIRD_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_THIRD_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_third_cas_scope_changed")
        if fifty_second:
            layer = CURRENT_SOURCE_FIFTY_SECOND_LAYER
            expected_targets = {
                *(source / row["path"] for row in CURRENT_SOURCE_FIFTY_SECOND_NATIVE_FILES),
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_SECOND_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_second_cas_scope_changed")
        if fifty_first:
            layer = CURRENT_SOURCE_FIFTY_FIRST_LAYER
            expected_targets = {
                source / CURRENT_SOURCE_FIFTY_FIRST_NATIVE_FILE["path"],
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTY_FIRST_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fifty_first_cas_scope_changed")
        if fiftieth:
            layer = CURRENT_SOURCE_FIFTIETH_LAYER
            expected_targets = {
                source / CURRENT_SOURCE_FIFTIETH_NATIVE_FILE["path"],
                home / f"patches/hermes/{layer}-manifest.json",
                home / f"patches/hermes/{layer}.patch",
                home / CURRENT_SOURCE_FIFTIETH_HELPER,
                home / "hermes-agent.source.json",
                home / "FRIDAY-INSTALL.json",
                home / "hermes-agent/install-stamp.json",
            }
            require(set(before_pins) == {str(target) for target in expected_targets},
                    "transaction_current_source_fiftieth_cas_scope_changed")
        if forty_ninth:
            require(len(before_pins) == 11,
                    "transaction_current_source_forty_ninth_cas_scope_changed")
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
        if seventieth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_seventieth_previous_committed_changed")
        if sixty_ninth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_ninth_previous_committed_changed")
        if sixty_eighth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_eighth_previous_committed_changed")
        if sixty_seventh:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_seventh_previous_committed_changed")
        if sixty_sixth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_sixth_previous_committed_changed")
        if sixty_fifth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_fifth_previous_committed_changed")
        if sixty_fourth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_fourth_previous_committed_changed")
        if sixty_third:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_third_previous_committed_changed")
        if sixty_second:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_second_previous_committed_changed")
        if sixty_first:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixty_first_previous_committed_changed")
        if sixtieth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_sixtieth_previous_committed_changed")
        if fifty_ninth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_ninth_previous_committed_changed")
        if fifty_eighth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_eighth_previous_committed_changed")
        if fifty_seventh:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_seventh_previous_committed_changed")
        if fifty_sixth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_sixth_previous_committed_changed")
        if fifty_fifth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_fifth_previous_committed_changed")
        if fifty_fourth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_fourth_previous_committed_changed")
        if fifty_third:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_third_previous_committed_changed")
        if fifty_second:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_second_previous_committed_changed")
        if fifty_first:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fifty_first_previous_committed_changed")
        if fiftieth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_fiftieth_previous_committed_changed")
        if forty_ninth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_forty_ninth_previous_committed_changed")
        if forty_eighth:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_forty_eighth_previous_committed_changed")
        if forty_seventh:
            require(owned_file(native_committed_path) == native_committed_raw,
                    "transaction_current_source_forty_seventh_previous_committed_changed")
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
