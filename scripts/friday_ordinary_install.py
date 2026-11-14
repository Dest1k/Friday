"""Finite ordinary Telegram source activation; native owners retain the receiver.

There is one explicit reviewed deployment transaction. It never resets a CLI
clock, executes a consumed query, enables a worker, approves a user or starts a
consumer. Subsequent service starts use the installed native CLI and unit.
"""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
from pathlib import Path
import stat

MANIFEST = 'patches/hermes/ordinary-telegram-manifest.json'
TRANSACTION = 'preparation/ordinary-gateway'
UPDATE_MANIFEST = 'patches/hermes/ordinary-native-repair-manifest.json'
UPDATE_FILES = {'hermes_cli/friday_dashboard_owner.py', 'hermes_cli/friday_credential_admission.py'}
PRIVATE_STATE_MANIFEST = 'patches/hermes/ordinary-private-state-manifest.json'
PRIVATE_STATE_FILES = {'hermes_cli/plugins_state.py', 'utils.py'}
FILE_CONTINUATION_MANIFEST = 'patches/hermes/ordinary-file-continuation-manifest.json'
FILE_CONTINUATION_FILES = {'hermes_cli/friday_user_scope.py', 'gateway/run_inbound_media.py',
    'gateway/platforms/base.py', 'gateway/run_notifications.py', 'gateway/run_plugin_delivery.py',
    'gateway/run_turn.py', 'plugins/platforms/telegram/adapter.py'}
WORKER_ATTACH_PLUGIN_FILES = {'plugins/friday_rework/onboarding.py',
    'plugins/friday_rework/worker_provision.py', 'plugins/friday_rework/dashboard/api.py',
    'plugins/friday_rework/dashboard/index.js'}

ADMIN_RESTART_MANIFEST = 'patches/hermes/ordinary-admin-restart-manifest.json'
ADMIN_RESTART_FILES = {'hermes_cli/web_server.py', 'hermes_cli/friday_dashboard_owner.py', 'hermes_cli/gateway.py'}

ADMIN_BROADCAST_MANIFEST = 'patches/hermes/ordinary-admin-broadcast-manifest.json'
ADMIN_BROADCAST_FILES = {'hermes_cli/free_tier_bootstrap.py'}

WEB_CONTINUATION_MANIFEST = 'patches/hermes/ordinary-web-continuation-manifest.json'
WEB_CONTINUATION_FILES = {'tools/web_tools_truncate.py', 'tools/web_tools.py', 'model_tools.py'}

WEB_OUTPUT_MANIFEST = 'patches/hermes/ordinary-web-output-manifest.json'
WEB_OUTPUT_FILES = {'agent/bounded_context.py', 'tools/web_tools_truncate.py', 'tools/web_tools.py', 'tools/file_tools.py', 'hermes_cli/friday_user_scope.py'}

SEARCH_RECOVERY_MANIFEST = 'patches/hermes/ordinary-search-recovery-manifest.json'
SEARCH_RECOVERY_FILES = {'tools/web_tools.py', 'tools/web_tools_truncate.py'}

# One reviewed Native78 -> Native79 boundary. Final public native pins must be
# bound after the frozen patch/manifest are independently reviewed; None refuses
# execution, including dry preparation against mutable native afterimages.
SPARK_MULTIPASS_MANIFEST = 'patches/hermes/spark-primary-multipass-manifest.json'
SPARK_MULTIPASS_PATCH = 'patches/hermes/spark-primary-multipass.patch'
SPARK_MULTIPASS_MANIFEST_SHA256 = '37cb4931953833926827f24d9018db667444b34fd3cd3bdb99a71b35a2793919'
SPARK_MULTIPASS_PATCH_SHA256 = 'bc3f5363b2fe33306b5ae66e2dfc1fab5057b1abe0ff44225cdd0d749b1f9fdc'
SPARK_MULTIPASS_PREVIOUS_INPUT = '7aeee4cadb96ce5e4ce392ccbecfb34df691ffae6bf9c1dca46f2d0112782896'
SPARK_MULTIPASS_NEW_FILES = {'agent/context_compressor_multipass.py',
    'tests/agent/test_bounded_multipass.py', 'tests/hermes_cli/test_friday_compression_role.py'}
SPARK_MULTIPASS_FILES = SPARK_MULTIPASS_NEW_FILES | {'agent/auxiliary_client.py',
    'agent/bounded_context.py', 'agent/bounded_summary_output.py', 'agent/context_compressor.py',
    'agent/context_compressor_summary.py', 'agent/conversation_compression.py',
    'agent/usage_anchor.py', 'agent/process_bootstrap.py', 'hermes_state_compression.py', 'hermes_cli/friday_credential_admission.py'}
SPARK_MULTIPASS_PLUGIN_FILES = {'plugins/friday_rework/onboarding.py'}
SPARK_MULTIPASS_NATIVE_FILES = 17683
SPARK_MULTIPASS_PROJECT_BEFORE = {'plugins/friday_rework/onboarding.py': '63f1476661fb4e1dff0a828cd11c298d89661025416836bb115e8ab6abd529b6', 'scripts/friday_ordinary_install.py': '8d8b9cc23f2436ff9903ef29671c97d6147e10d62194cd20e300e9e39a11a1ac', 'tools/configure_local_test.py': '0bc17aa5d2f6e9aa75fad10246205421f49db23e91300fab11900c269bf9666e', 'tools/configure_product.py': '0494489e42f17558893d5372aa988d74ab8a148108836add71eb5a7f440cefdc', 'scripts/friday_install.py': '8b9109adc3b690b47791ff1b9d75073b812e502ac16810361a1692059f0f67dd'}
SPARK_MULTIPASS_PROJECT_AFTER = {'plugins/friday_rework/onboarding.py': '42e262612c464e81568dbcc30266b0c67be365f1cb780fa1700a04ca59ec5c42', 'tools/configure_local_test.py': '0794011d5a06842046746b437ac7beed9eb8da1d18d8b822d701a8f91ca8c523', 'tools/configure_product.py': '7d5ce5209e21c41442e6c44598a85accc011a5c3f6c81c772fe85d9dd2016a82', 'scripts/friday_install.py': '73521e7a4dd09b243d41c9db0869bcfc2bd85e0ecd3eac22537dbe4cbeda8901'}

# Source79/helper-v4 -> Source80: unreviewed native/producer pins refuse execution.
SPARK_REQUEST_BUDGET_MANIFEST = 'patches/hermes/spark-request-budget-manifest.json'
SPARK_REQUEST_BUDGET_PATCH = 'patches/hermes/spark-request-budget.patch'
SPARK_REQUEST_BUDGET_MANIFEST_SHA256 = '0df5366e1f18905c96a8e80df85165fd50a68d8f0e4dfc41178c43165182c16b'
SPARK_REQUEST_BUDGET_PATCH_SHA256 = 'e6840b425e01444036f6f1b8b147bca6b9d2fcf883bdb0e07d3ba09aadfaf708'
SPARK_REQUEST_BUDGET_PREVIOUS_INPUT = '2c0c0ae479145a658ba1b089f82bdfcfdeca1fa14586ac853a9331457f641f7c'
SPARK_REQUEST_BUDGET_NEW_FILES = {'agent/request_budget.py', 'gateway/run_turn_status.py', 'tests/agent/test_named_request_budget.py', 'tests/agent/test_nonstream_request_budget.py', 'tests/agent/test_request_budget_terminal.py', 'tests/gateway/test_telegram_live_turn_status.py', 'tests/hermes_cli/test_named_request_budget.py'}
SPARK_REQUEST_BUDGET_FILES = {'agent/chat_completion_helpers.py', 'agent/chat_completion_nonstream.py', 'agent/chat_completion_stream_monitor.py', 'agent/client_lifecycle.py', 'agent/history_commentary.py', 'agent/request_budget.py', 'agent/turn_api_error.py', 'agent/turn_response_intake.py', 'gateway/platforms/api_server.py', 'gateway/platforms/api_server_openai_routes.py', 'gateway/platforms/base.py', 'gateway/run_turn.py', 'gateway/run_turn_runner.py', 'gateway/run_turn_status.py', 'gateway/turn_context.py', 'hermes_cli/config_providers.py', 'hermes_cli/friday_user_scope.py', 'hermes_cli/timeouts.py', 'hermes_cli/web_routers/sessions.py', 'run_agent.py', 'tests/agent/test_named_request_budget.py', 'tests/agent/test_nonstream_request_budget.py', 'tests/agent/test_privacy_effect_semantics.py', 'tests/agent/test_request_budget_terminal.py', 'tests/gateway/test_telegram_live_turn_status.py', 'tests/hermes_cli/test_named_request_budget.py'}
SPARK_REQUEST_BUDGET_PLUGIN_FILES = {'plugins/friday_rework/user_worker_join.py'}
SPARK_REQUEST_BUDGET_NATIVE_FILES = 17686
SPARK_REQUEST_BUDGET_PROJECT_BEFORE = {
    'scripts/friday_ordinary_install.py':'ea37453fee3a919f196b0cb0a906bcfe6f7b04d21a698cb3f731c31e90a1d907',
    'tools/configure_local_test.py':'0794011d5a06842046746b437ac7beed9eb8da1d18d8b822d701a8f91ca8c523',
    'tools/configure_product.py':'7d5ce5209e21c41442e6c44598a85accc011a5c3f6c81c772fe85d9dd2016a82',
    'plugins/friday_rework/user_worker_join.py':'3bc8de8bff973b2e782cd4157fba97178d0b960d4a7bf88ae978492e845bd9e8',
}
# The updater is pinned by current_input, avoiding a self-referential hash.
SPARK_REQUEST_BUDGET_PROJECT_AFTER = {
    'tools/configure_local_test.py':'6859d082f85620c160b388a9b70077cb8ac59393bdb9af5739315a4f15fb1c19',
    'tools/configure_product.py':'0dc06e69e81f448b9da3627711b28d9433f559915c8db52cf189e7a7a1501216',
    'plugins/friday_rework/user_worker_join.py':'ad10ba044308a0bcdf1697998a37fb33a8d3737025ea2a6e4e244dd3122a9cf2',
}

SOURCE80_HELPER_REQUEST = '85146114e897d29fa2540f026716c018eef2d4700045be941775de8c86462e3a'
SOURCE80_REBIND_REQUEST = 'cdd6438774d0081e5969e6e39c097232b3979f33e2e89d6c406c39d8a379a97b'
SOURCE80_REBIND_INTENT = '059efd03e5323114c9f759d92096e4c9623dadc24d1ed7ebe23b8af10f3d10eb'
SOURCE80_REBIND_COMMITTED = 'ca24f428f0ae4f611a5eaa9c86087db82f11d505799cbc6b9b23d6369c17978f'
SOURCE80_HISTORY_FILES = 566

# One exact Source80 + closed budget-only v2 -> Source81 source transition.
FILE_TOOL_CONTRACT_MANIFEST = 'patches/hermes/ordinary-file-tool-contract-manifest.json'
FILE_TOOL_CONTRACT_PATCH = 'patches/hermes/ordinary-file-tool-contract.patch'
FILE_TOOL_CONTRACT_MANIFEST_SHA256 = 'c0b847d230e4ac03e91c455a2f07282a8b117cfc95f6d207b0c89216a0b12007'
FILE_TOOL_CONTRACT_PATCH_SHA256 = '6c053a31678b7ebbf66167d465a7d54b66ad177082090b5d47f4cf3c8bff1a8a'
FILE_TOOL_CONTRACT_FILES = {'model_tools.py','hermes_cli/friday_prompt_scope.py','agent/system_prompt.py','gateway/run.py'}
FILE_TOOL_CONTRACT_PREVIOUS_INPUT = '7ed481576a38ccc7f99e38f92b25e733dc9b90fa84a613e21aa47d9f97306524'
FILE_TOOL_CONTRACT_NATIVE_FILES = 17693
FILE_TOOL_CONTRACT_PLUGIN_FILES = {'plugins/friday_rework/admin_settings.py'}
FILE_TOOL_CONTRACT_PROJECT_BEFORE = {'scripts/friday_ordinary_install.py': '3576edd1374d5093477aa4412af7dc4382c4c1d8036f3e312a724cbf44408290', 'plugins/friday_rework/admin_settings.py': '8e5642aaa9581448fc3a31f187461a914c26127065194f4c78fc7f92546eea5f'}
FILE_TOOL_CONTRACT_PROJECT_AFTER = {'plugins/friday_rework/admin_settings.py': '1b9f3ef44ab9483ff2ea230ae9d00640510ee8bc35e645feb2b01483ebc3510e'}
SOURCE81_PREDECESSOR_REQUEST = 'a10f7fde0f63ef317dda4eeefeacabf487518362d5af4bc13b28c57e475782f3'
SOURCE81_BUDGET_REQUEST = '5aaebaa33a549fbf5878d25f8b76c1ec4295fea9f18a7083eab46f6479b9459c'
SOURCE81_BUDGET_INTENT = '05ba73d4226f5e1e10e6bd9cfd983b57d0e0a3d3ef3c2062fc2a2dd1f10137c3'
SOURCE81_BUDGET_COMMITTED = '35635275e9b9d84a7b9cf8b44711cb29d381ae28f23eb6c506c32dd86949ed9a'
SOURCE81_HISTORY_FILES = 632
SOURCE81_RETAINED_FILES = 669

# Exact Source81 -> Source82 web credential boundary; no operational rewrite.
WEB_INPUT_MANIFEST = 'patches/hermes/ordinary-web-input-privacy-manifest.json'
WEB_INPUT_PATCH = 'patches/hermes/ordinary-web-input-privacy.patch'
WEB_INPUT_MANIFEST_SHA256 = 'b75fe7b0a44e740c3cdd1258fd7cf4c71720faee3728d468929ecbdd6412cab1'
WEB_INPUT_PATCH_SHA256 = '640ad9dcce0627bdd942df9c29713f5483d7dcfee6a7dceef81332749fdd1567'
WEB_INPUT_FILES = {'tools/web_tools.py','tools/web_tools_extract.py'}
WEB_INPUT_PREVIOUS_INPUT = '58d2f1eeb34b844a5cfd6b59b262f8a820c05614fca9aefe88ceb74b5be93038'
WEB_INPUT_PREDECESSOR_REQUEST = 'bc2fd9911709a89c59748e6946ae78b7c648da9d4d16b3121aac5224d24fb30c'
WEB_INPUT_PREVIOUS_UPDATER = '23fb0ed00ca2cda041ca07115847f232de01061648863b930d16ea55f0f72cca'
WEB_INPUT_NATIVE_FILES = 17693
WEB_INPUT_HISTORY_FILES = 646
WEB_INPUT_SELECTED_CONFIG = 'fe8a6ae2c6998b57f67f75e7affc35d988c30a800baae1daece8569c031af4fd'
WEB_INPUT_PROFILE_FILES = {'profiles/dest_telegram/'+n for n in
    ('config.yaml','.friday-onboarding.json','.friday-user-scope.json','.env')}

# Package Source83: one combined native layer directly on installed Source81.
# Source82/v36 was prepared only; it is never accepted as executed ancestry here.
COMBINED_INPUT_MANIFEST = 'patches/hermes/ordinary-web-delivery-privacy-manifest.json'
COMBINED_INPUT_PATCH = 'patches/hermes/ordinary-web-delivery-privacy.patch'
COMBINED_INPUT_MANIFEST_SHA256 = 'f80b64f11c2a9bdfdd37ef5bdc87a9edd5534f30f19b04c4a8562fd08a6a8d3a'
COMBINED_INPUT_PATCH_SHA256 = '5fc427aeb1298e6137941ad1162524b896b497f4c842f907b9db5dfac4536506'
COMBINED_INPUT_FILES = {'tools/web_tools.py','tools/web_tools_extract.py',
    'gateway/run_plugin_delivery.py','hermes_cli/friday_user_scope.py',
    'hermes_cli/friday_prompt_scope.py'}
COMBINED_INPUT_PREVIOUS_INPUT = '58d2f1eeb34b844a5cfd6b59b262f8a820c05614fca9aefe88ceb74b5be93038'
COMBINED_INPUT_PREDECESSOR_REQUEST = 'bc2fd9911709a89c59748e6946ae78b7c648da9d4d16b3121aac5224d24fb30c'
COMBINED_INPUT_PREVIOUS_UPDATER = '23fb0ed00ca2cda041ca07115847f232de01061648863b930d16ea55f0f72cca'
COMBINED_INPUT_NATIVE_FILES = 17693
COMBINED_INPUT_HISTORY_FILES = 646

# Source84: one reviewed native file presentation layer on committed Source83.
# No mutable afterimages are admitted. Final patch, manifest and exact target set
# are bound together after composition; None fails before reading runtime inputs.
FILE_REPLY_CONTEXT_MANIFEST = 'patches/hermes/ordinary-file-reply-context-caption-manifest.json'
FILE_REPLY_CONTEXT_PATCH = 'patches/hermes/ordinary-file-reply-context-caption.patch'
FILE_REPLY_CONTEXT_MANIFEST_SHA256 = '7c8bbe7894d2c6a85bb75dd3f7ba17e9631a05d47398383d53ab4e0d4bae87e0'
FILE_REPLY_CONTEXT_PATCH_SHA256 = '6be8c37934121f9c8fcabd9d1d4cbdf855785a6cde4673c9825f4f7a2da5295c'
FILE_REPLY_CONTEXT_FILES = {'agent/agent_runtime_helpers.py','agent/chat_completion_helpers.py','agent/context_compressor.py','agent/context_compressor_multipass.py','agent/conversation_compression.py','agent/turn_context.py','gateway/platforms/base.py','gateway/run_plugin_delivery.py','hermes_cli/friday_user_scope.py'}
FILE_REPLY_CONTEXT_PREVIOUS_INPUT = 'f50b97045eaa0a18aa43f99f73701b60fb13c2705058e397b456bc5372172c72'
FILE_REPLY_CONTEXT_PREDECESSOR_REQUEST = 'e03b886b92b37b604b19dbfb19a9bc8d497f76400cf792085b1bc99636137d13'
FILE_REPLY_CONTEXT_PREDECESSOR_COMMITTED = 'f1320cb2d5d800355ab98e72f5fb9bebd12ae50280b52e757b74c31bc3142f92'
FILE_REPLY_CONTEXT_PREVIOUS_UPDATER = '4ce32ffd2e70896f88256e5ab33f63b74223d210599b3941f3e3e660e389909b'
FILE_REPLY_CONTEXT_NATIVE_FILES = 17693
FILE_REPLY_CONTEXT_HISTORY_FILES = 661

# Source85: one reviewed combined web/runtime/history layer on committed Source84.
# No mutable afterimages are admitted. Final patch, manifest and exact target set
# are bound together after composition; None fails before reading runtime inputs.
WEB_RUNTIME_HISTORY_MANIFEST = 'patches/hermes/ordinary-web-runtime-history-manifest.json'
WEB_RUNTIME_HISTORY_PATCH = 'patches/hermes/ordinary-web-runtime-history.patch'
WEB_RUNTIME_HISTORY_MANIFEST_SHA256 = 'b1c7ee3f1df0517a2167c26b2cc5a13b1bdea2c4a32f9a66f301f3e8cb4b6bef'
WEB_RUNTIME_HISTORY_PATCH_SHA256 = 'e8d6651fd3563cb63148289d1ea44b3985dfd9eaf92fec8d1b3fbf572cb3f324'
WEB_RUNTIME_HISTORY_FILES = {'agent/chat_completion_helpers.py','agent/turn_context.py','agent/turn_request_assembly.py','hermes_cli/friday_user_scope.py','tools/browser_process_child.py','tools/web_process.py','tools/web_process_child.py'}
WEB_RUNTIME_HISTORY_PREVIOUS_INPUT = '2b353a5c4aecfcb2cd3f8c401bc83965b0827aa8b54e68fb650ae4dd52a896e0'
WEB_RUNTIME_HISTORY_PREDECESSOR_REQUEST = 'c7b7b3eb267350bccbc46a66b3401f79e8e32afc784376b6b487834a7ba80458'
WEB_RUNTIME_HISTORY_PREDECESSOR_COMMITTED = '39d41a417c2431885aa4d34410ff4a0b091c8e158b0496d7355b4d63e0e4c0a0'
WEB_RUNTIME_HISTORY_PREVIOUS_UPDATER = '439f33677ecf9698e66f98cb9c13f85e301867a928e8c6caa325b47947741b4d'
WEB_RUNTIME_HISTORY_NATIVE_FILES = 17693
WEB_RUNTIME_HISTORY_HISTORY_FILES = 684

# Source87: exact compressor runtime, dependency declarations and bundled assets.
# Source publication never installs dependencies or grants renderer readiness.
# The integrator binds these only after freezing the complete reviewed layer.
PROTECTED_COMPRESSOR_MANIFEST = 'patches/hermes/ordinary-protected-compressor-manifest.json'
PROTECTED_COMPRESSOR_PATCH = 'patches/hermes/ordinary-protected-compressor.patch'
PROTECTED_COMPRESSOR_MANIFEST_SHA256 = None
PROTECTED_COMPRESSOR_PATCH_SHA256 = None
PROTECTED_COMPRESSOR_FILES = None
PROTECTED_COMPRESSOR_NEW_FILES = None
PROTECTED_COMPRESSOR_NEW_DIRECTORIES = None
PROTECTED_COMPRESSOR_PREVIOUS_INPUT = None
PROTECTED_COMPRESSOR_PREDECESSOR_REQUEST = None
PROTECTED_COMPRESSOR_PREDECESSOR_COMMITTED = None
PROTECTED_COMPRESSOR_PREVIOUS_UPDATER = None
PROTECTED_COMPRESSOR_NATIVE_FILES = 17693
PROTECTED_COMPRESSOR_HISTORY_FILES = None

# v42 is one source/project bundle directly on committed Source86. v41 was
# never installed and is not accepted as ancestry. All final pins remain inert
# until the integrator freezes both native layers and the merged project tuple.
BUNDLE_SCHEMA = 'friday.ordinary-telegram-source-update.v42'
BUNDLE_MANIFESTS = (PROTECTED_COMPRESSOR_MANIFEST,
    'patches/hermes/ordinary-bot-principal-manifest.json')
BUNDLE_PATCHES = (PROTECTED_COMPRESSOR_PATCH,
    'patches/hermes/ordinary-bot-principal.patch')
BUNDLE_PLUGIN_FILES = {'plugins/friday_rework/runtime_containment.py',
    'plugins/friday_rework/runtime_process.py'}
BUNDLE_PROJECT_FILES = BUNDLE_PLUGIN_FILES | {'scripts/friday_ordinary_install.py',
    'tools/configure_product.py', 'tools/configure_local_test.py'}
BUNDLE_LAYER_PINS = ({'manifest_sha256': '59612f40ecb53082ff03bbd3696063af742e745ae1ffefdb868dfcef8ad177b0', 'patch_sha256': '8db6eb8d8639ccfb2d5e97120a4e31e15c2515b99921b4f775891ca6359cf7c3', 'files': {'agent/bounded_context.py', 'agent/compression_attempts.py', 'agent/context_compressor_multipass.py', 'agent/protected_compressor_normalize.py', 'agent/protected_compressor_renderer.py', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/ASSET-MANIFEST.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/LICENSE-APACHE-2.0.txt', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/LICENSE-MODEL.txt', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/NOTICE.txt', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/chat_template.jinja', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/generation_config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/tokenizer.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/tokenizer_config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/processor-evidence/preprocessor_config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/processor-evidence/video_preprocessor_config.json', 'hermes_cli/friday_credential_admission.py', 'pyproject.toml', 'uv.lock'}, 'new_files': {'agent/compression_attempts.py', 'agent/protected_compressor_normalize.py', 'agent/protected_compressor_renderer.py', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/ASSET-MANIFEST.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/LICENSE-APACHE-2.0.txt', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/LICENSE-MODEL.txt', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/NOTICE.txt', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/chat_template.jinja', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/generation_config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/tokenizer.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model/tokenizer_config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/processor-evidence/preprocessor_config.json', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/processor-evidence/video_preprocessor_config.json'}}, {'manifest_sha256': 'bf0ac48929f8f4eeaf1c00f761ab1ace77d7dbdacf5489150a93c3533302a9ff', 'patch_sha256': '0dbf047d4e18997056d057a8bda38042cefe954907d03bed09b7ffbe8a80b2b7', 'files': {'gateway/pairing.py', 'gateway/run_inbound.py', 'hermes_cli/friday_bot_pairing.py'}, 'new_files': {'hermes_cli/friday_bot_pairing.py'}},)
BUNDLE_NEW_DIRECTORIES = {'hermes_cli/data', 'hermes_cli/data/protected_compressor', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/model', 'hermes_cli/data/protected_compressor/5e16869ab75a582aa3925fc379cbcfa514b41e0375bda0e28748fd8e0a92be75/processor-evidence'}
BUNDLE_PROJECT_BEFORE = {'scripts/friday_ordinary_install.py': '24c0b269dc7897d7ec042b59888eee1e6c920911b0fcc4022e85bc871a413483', 'plugins/friday_rework/runtime_containment.py': '41ba7c6853dadae5021fa6fee4520dfe4e620187d726ba4fb6693bb0df1953f7', 'plugins/friday_rework/runtime_process.py': 'edad3f51e9a8b180173eb1c17f1bde065eefc317e4ab3ceeb8ea9ef5499b5c6f', 'tools/configure_product.py': '0dc06e69e81f448b9da3627711b28d9433f559915c8db52cf189e7a7a1501216', 'tools/configure_local_test.py': '6859d082f85620c160b388a9b70077cb8ac59393bdb9af5739315a4f15fb1c19'}
# Includes both helpers even if one is unchanged; updater pins its actual file.
BUNDLE_PROJECT_AFTER = {'plugins/friday_rework/runtime_containment.py': 'f2503bc03b8e3c500f73fb9ead3361ac1e193fc75716ecceaa768c06ca2dce6a', 'plugins/friday_rework/runtime_process.py': '4faa69fdce523679fd158ca1d92958a9d83fff5bc0f76de0b153d7afa4ebc0fb', 'tools/configure_product.py': 'ff737472e587c42238b2e6ead282afcf4cad4198751d3acc3382016b096349f4', 'tools/configure_local_test.py': 'b97e44c94461040c263c2318db910f0404a5ab28900a5cd0f3288f6669157148'}
BUNDLE_PREVIOUS_INPUT = '9440d09ffb0b56b06dedc1dfe11db6a31e0297495f18af667e064698a32ecd5d'
BUNDLE_PREDECESSOR_REQUEST = 'c57c455f3321770494f195209a53d4d4d5f080f4efce793cd2f2b25bcbb9ebcd'
BUNDLE_PREDECESSOR_COMMITTED = '3b5687d2f705f029a88c1516fc55d602626be9739e5483a85b4378faa9eb1255'
BUNDLE_HISTORY_FILES = 771
BUNDLE_NATIVE_FILES = 17693

# Exact genuine Source86 compatibility: only the independent CLI launcher layer
# moved from installed index32 to canonical index2. Never reorder old receipts.
BUNDLE_SOURCE86_INSTALLED_PREFIX_SHA256 = '8d37e68787f8fb88024ac142ac40c9bb2e5e5da827947dbf2fee36651dc1d49a'
BUNDLE_SOURCE86_CANONICAL_PREFIX_SHA256 = 'afe99a859657f2bd32762f7c140c913816c352c90a79ae245f3175d316dcdcf9'

# Source86: manual ordinary compression on the exact committed Source85 archive.
# Exact native bytes; source binding does not grant runtime authority.
MANUAL_COMPRESSION_MANIFEST = 'patches/hermes/ordinary-manual-compression-manifest.json'
MANUAL_COMPRESSION_PATCH = 'patches/hermes/ordinary-manual-compression.patch'
MANUAL_COMPRESSION_MANIFEST_SHA256 = '934aef036472b0fc94f63765cff91212c5c1ae320bb4ad3793273a692ed231a5'
MANUAL_COMPRESSION_PATCH_SHA256 = 'e39ae3733d8d6cf39ee110914d795c672b47187105461d3dacfcee97be5c9a39'
MANUAL_COMPRESSION_FILES = {'gateway/platforms/base.py', 'gateway/run_agent_cache.py', 'gateway/run_busy.py', 'gateway/run_shutdown.py', 'gateway/slash_commands.py', 'gateway/slash_commands_session.py', 'hermes_cli/friday_user_scope.py'}
MANUAL_COMPRESSION_PREVIOUS_INPUT = 'a6783137234e360da8cf7897d0e9642453dfc3947d2968b72f39cbd5c95a1cd9'
MANUAL_COMPRESSION_PREDECESSOR_REQUEST = 'f7809de47b0f654cf3a18f04cbb6411f0af3fe4f2babaec8dd44df7ab7b2d438'
MANUAL_COMPRESSION_PREDECESSOR_COMMITTED = '927b83a616c2e748e12808a5f19252eb90d8d10ed31902f3179265e3f4a0b134'
MANUAL_COMPRESSION_PREVIOUS_UPDATER = '24d2844cf1093b07ce6b6bd2903857567afb253e7b6daa5d06bec00b0484714a'
MANUAL_COMPRESSION_NATIVE_FILES = 17693
MANUAL_COMPRESSION_HISTORY_FILES = 752
MANUAL_COMPRESSION_ARCHIVE_REQUEST = '8dbd0fa64aa705a99fe682bab0f37d8a1105fb2adbff9cf415a5c879d9b85a5f'
MANUAL_COMPRESSION_ARCHIVE_INTENT = 'b947106f79a0e5e994c1da50d3b6d792dea0a56703e8c86738b8652821b33a28'
MANUAL_COMPRESSION_ARCHIVE_COMMITTED = 'e3f7dfd1e44af31dd127192856f268d9e09f87313e92eb0b89ae8f9ddd200135'

PRIVACY_EFFECT_MANIFEST = 'patches/hermes/ordinary-private-refusal-effect-manifest.json'
PRIVACY_EFFECT_NEW_FILES = {'tests/agent/test_privacy_effect_semantics.py'}
PRIVACY_EFFECT_FILES = PRIVACY_EFFECT_NEW_FILES | {'agent/tool_executor.py', 'agent/tool_result_classification.py', 'agent/turn_context.py', 'agent/turn_finalizer.py', 'gateway/run_turn.py', 'gateway/run_turn_runner.py', 'hermes_cli/friday_user_scope.py'}
PRIVACY_EFFECT_PLUGIN_FILES = {'plugins/friday_rework/user_worker_join.py'}
PRIVACY_EFFECT_NATIVE_FILES = 17682
PRIVACY_EFFECT_PLUGIN_BEFORE = 'e0dab0f3a21c3ac3ce841aa6d8176d4fd60ea4c57f6b633cdc0e2091e3e55358'
PRIVACY_EFFECT_PLUGIN_AFTER = '3bc8de8bff973b2e782cd4157fba97178d0b960d4a7bf88ae978492e845bd9e8'

DOCX_CREATION_MANIFEST = 'patches/hermes/ordinary-docx-creation-manifest.json'
DOCX_CREATION_FILES = {'hermes_cli/friday_user_scope.py','tools/file_tools.py','hermes_cli/friday_workspace_docx.py','hermes_cli/friday_plain_docx_template.b64','hermes_cli/friday_plain_docx_template.LICENSE'}
DOCX_CREATION_NEW_FILES = {'hermes_cli/friday_workspace_docx.py','hermes_cli/friday_plain_docx_template.b64','hermes_cli/friday_plain_docx_template.LICENSE'}

DOCUMENT_EXTRACTION_MANIFEST = 'patches/hermes/ordinary-document-extraction-manifest.json'
DOCUMENT_EXTRACTION_FILES = {'hermes_cli/friday_user_scope.py','tools/read_extract.py'}

FILE_REVISION_MANIFEST = 'patches/hermes/ordinary-file-revision-manifest.json'
FILE_REVISION_NEW_FILES = {'hermes_cli/friday_workspace_revision.py'}
FILE_REVISION_FILES = FILE_REVISION_NEW_FILES | {'hermes_cli/friday_user_scope.py','tools/file_tools.py','agent/tool_executor.py','agent/turn_api_call.py','gateway/run_plugin_delivery.py'}

TOOL_RESULT_CONTEXT_MANIFEST = 'patches/hermes/ordinary-tool-result-context-manifest.json'
TOOL_RESULT_CONTEXT_FILES = {'agent/tool_executor.py','agent/web_call_context.py','run_agent.py'}

DSH_SANDBOX_MANIFEST = 'patches/hermes/ordinary-dsh-native-sandbox-profile-manifest.json'
DSH_SANDBOX_FILES = {'tools/render_dsh_local.py','gateway/run_turn_runner.py'}

CURRENT_TURN_MANIFEST = 'patches/hermes/ordinary-current-turn-compaction-privacy-reply-manifest.json'
CURRENT_TURN_FILES = set(['agent/bounded_context.py', 'agent/bounded_summary_output.py', 'agent/context_compressor.py', 'agent/turn_context.py', 'agent/turn_context_compaction.py', 'agent/turn_finalizer.py', 'gateway/run_turn.py', 'hermes_cli/friday_user_scope.py'])
CONTEXT_SELF_MANIFEST = 'patches/hermes/ordinary-context-self-disclosure-manifest.json'
CONTEXT_SELF_PLUGIN_FILES = {'plugins/friday_rework/admin_settings.py'}
CONTEXT_SELF_FILES = {'agent/bounded_context.py', 'agent/conversation_compression.py', 'agent/chat_completion_helpers.py', 'agent/turn_context.py', 'hermes_cli/friday_prompt_scope.py', 'hermes_cli/friday_user_scope.py'}
PRIVATE_REPLY_MANIFEST = 'patches/hermes/ordinary-private-reply-compression-manifest.json'
PRIVATE_REPLY_FILES = {'agent/bounded_context.py', 'agent/chat_completion_helpers.py', 'agent/conversation_compression.py', 'agent/session_persistence.py', 'agent/stream_delivery.py', 'agent/system_prompt.py', 'agent/turn_context.py', 'agent/turn_finalizer.py', 'agent/turn_tool_round.py', 'gateway/platforms/base.py', 'gateway/run_turn.py', 'hermes_cli/friday_prompt_scope.py', 'hermes_cli/friday_user_scope.py', 'tools/registry.py'}
PROMPT_PRIVACY_MANIFEST = 'patches/hermes/ordinary-prompt-privacy-dialogue-manifest.json'
PROMPT_PRIVACY_FILES = {'hermes_cli/friday_prompt_scope.py', 'agent/prompt_builder.py', 'agent/system_prompt.py'}
MEMORY_SCOPE_MANIFEST = 'patches/hermes/ordinary-memory-scope-privacy-manifest.json'
MEMORY_SCOPE_FILES = {'tools/memory_tool_store.py', 'tools/write_approval.py', 'hermes_cli/write_approval_commands.py', 'hermes_cli/friday_user_scope.py', 'tools/memory_tool.py'}
FIRST_CONTACT_COPY_MANIFEST = 'patches/hermes/ordinary-first-contact-copy-manifest.json'
FIRST_CONTACT_COPY_FILES = {'gateway/slash_commands.py', 'agent/onboarding.py', 'gateway/run_turn.py'}
INLINE_PRIVACY_MANIFEST = 'patches/hermes/ordinary-inline-privacy-connected-repair-manifest.json'
INLINE_PRIVACY_FILES = {'gateway/run_turn.py', 'agent/inline_tool_executors.py'}
TOOL_METADATA_MANIFEST = 'patches/hermes/ordinary-tool-metadata-progress-privacy-manifest.json'
TOOL_METADATA_FILES = set(['agent/turn_finalizer.py', 'gateway/platforms/base.py', 'gateway/run_busy.py', 'gateway/run_turn.py', 'hermes_cli/friday_user_scope.py', 'tools/registry.py', 'tools/session_search_tool.py'])
TOOL_METADATA_PLUGIN_FILES = {'plugins/friday_rework/adapters/dsh.py','plugins/friday_rework/artifacts.py','plugins/friday_rework/results.py'}
PUBLIC_SURFACE_MANIFEST = 'patches/hermes/ordinary-public-surface-privacy-manifest.json'
PUBLIC_SURFACE_FILES = {'gateway/slash_commands_status.py', 'hermes_cli/dashboard_auth/middleware.py', 'hermes_cli/friday_product_access.py', 'gateway/slash_commands_session.py', 'gateway/platforms/base.py', 'gateway/slash_commands.py', 'hermes_cli/friday_user_scope.py', 'gateway/run_turn.py', 'tools/registry.py', 'gateway/run_busy.py'}
WORKER_TOOLS_MANIFEST = 'patches/hermes/ordinary-worker-tools-packaging-manifest.json'
WORKER_TOOLS_PLUGIN_FILES = {'plugins/friday_rework/worker_provision.py', 'plugins/friday_rework/onboarding.py', 'plugins/friday_rework/user_worker_join.py'}
WORKER_TOOLS_FILES = {'tools/render_dsh_local.py', 'tools/web_profile.py', 'config/RESEARCH.md'}
DIALOGUE_CONTINUATION_MANIFEST = 'patches/hermes/ordinary-dialogue-continuation-manifest.json'
DIALOGUE_CONTINUATION_FILES = {'hermes_cli/friday_prompt_scope.py', 'agent/system_prompt.py'}

FIRST_CONTACT_STATE_MANIFEST = 'patches/hermes/ordinary-first-contact-state-manifest.json'
FIRST_CONTACT_STATE_FILES = {'agent/onboarding.py'}

TURN_SCOPE_MANIFEST = 'patches/hermes/ordinary-telegram-turn-scope-manifest.json'
TURN_SCOPE_FILES = {'gateway/run_inbound.py'}

ADMIN_STARTUP_MANIFEST = 'patches/hermes/ordinary-admin-startup-manifest.json'
ADMIN_STARTUP_FILES = {'hermes_cli/friday_dashboard_owner.py'}

INTERACTION_SCOPE_MANIFEST = 'patches/hermes/ordinary-interaction-scope-manifest.json'
INTERACTION_SCOPE_FILES = {'gateway/run_inbound_consumer.py',
    'hermes_cli/friday_dashboard_owner.py', 'hermes_cli/web_routers/status.py'}

PROFILE_RUNTIME_MANIFEST = 'patches/hermes/ordinary-profile-runtime-manifest.json'
PROFILE_RUNTIME_FILES = {'hermes_cli/friday_credential_admission.py', 'gateway/config.py',
    'gateway/run_adapters.py', 'hermes_cli/friday_gateway_owner.py',
    'hermes_cli/friday_dashboard_owner.py', 'hermes_cli/friday_product_access.py'}

BROWSER_GATEWAY_MANIFEST = 'patches/hermes/ordinary-browser-gateway-manifest.json'
BROWSER_GATEWAY_FILES = {'hermes_cli/friday_ordinary_gateway.py'}

BROWSER_MANIFEST = 'patches/hermes/ordinary-browser-manifest.json'
BROWSER_NEW_FILES = {'tools/browser_scoped.py', 'tools/browser_process_child.py',
    'tools/browser_public_transport.py', 'tools/browser_native_ipc.py'}
BROWSER_FILES = BROWSER_NEW_FILES | {'hermes_cli/friday_user_scope.py', 'toolsets.py',
    'tools/browser_tool.py', 'tools/browser_tool_lifecycle.py', 'tools/process_registry_web.py'}
BROWSER_PLUGIN_FILES = {'plugins/friday_rework/admin.py', 'plugins/friday_rework/onboarding.py',
    'plugins/friday_rework/dashboard/api.py', 'plugins/friday_rework/dashboard/index.js'}

# Source87 (committed v42) -> Source88: exactly two existing native files.
EXACT_RESPONSE_SCHEMA = 'friday.ordinary-telegram-source-update.v43'
EXACT_RESPONSE_MANIFEST = 'patches/hermes/ordinary-exact-response-manifest.json'
EXACT_RESPONSE_PATCH = 'patches/hermes/ordinary-exact-response.patch'
EXACT_RESPONSE_MANIFEST_SHA256 = 'bda8f351069fac02daa1c3f550bc3d9a55a9ac13e988e9e73784ade463a06b90'
EXACT_RESPONSE_PATCH_SHA256 = '3c8df6c5eb99aa97dea6f4622bd389adccbbcaff63c282243f7c759f9fe2e880'
EXACT_RESPONSE_FILES = {'agent/onboarding.py','hermes_cli/friday_prompt_scope.py'}
EXACT_RESPONSE_PREVIOUS_INPUT = '27efcf9f029a314533fd85b9ddbc64cfa6fd4551be3e9064b5acb182918ef440'
EXACT_RESPONSE_PREDECESSOR_REQUEST = 'd08050a6373b88ceeafaf09698a8758d58d8ef85707aa296dff7776083c89a2a'
EXACT_RESPONSE_PREDECESSOR_COMMITTED = 'a5c1424069deaaeba79429a83b360522452949d8f6de29483b189988f9b43d74'
EXACT_RESPONSE_PREVIOUS_UPDATER = '1b095b205caf3c62b74bc675d1ebb49b91dc77fe559d502f98397e7d699af875'
EXACT_RESPONSE_NATIVE_FILES = 17708
EXACT_RESPONSE_RETAINED_MAX_FILES = 100000
EXACT_RESPONSE_RETAINED_MAX_BYTES = 4 * 1024**3
EXACT_RESPONSE_RETAINED_TREES = ('profiles','workspace','history','memories','sessions',
    'platforms','pairing','plugin-data','user-artifacts','pending_messages','skills','cron','kanban')
EXACT_RESPONSE_RETAINED_ROOT_FILES = {'state.db','state.db-wal','state.db-shm',
    'SOUL.md','MEMORY.md','USER.md','.friday-onboarding.json','.friday-user-scope.json',
    'shared-state.db','shared-state.db-wal','shared-state.db-shm',
    'kanban.db','kanban.db-wal','kanban.db-shm',
    'channel_directory.json','spawn-ledger.json'}
EXACT_RESPONSE_BINDING_FILES = {'protected-compressor-binding-20261017-r1.json',
    'protected-compressor-deployment-20261017-r1.json'}


def api():
    from scripts import friday_install
    return friday_install


def prepare_workers(request, request_path, budget):
    """Continue installation declarations without changing the receiving runtime."""
    from scripts.friday_worker_preparation import prepare
    return prepare(request, request_path, budget)


def write(path, data, mode=0o600):
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def replace(path, data, mode=0o600):
    temporary = path.with_name(path.name + '.ordinary-staged')
    fd = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        os.fchmod(fd,mode)  # Preserve the exact beforeimage mode under any umask.
        with os.fdopen(fd,'wb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists(): temporary.unlink()
    fd = os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


class SourceUpdateDirectories:
    """Hold exact directory descriptors across additive source publication.

    Only declared absent parents may be created. Every operation is relative to
    a held descriptor, so replacing a path with a link cannot redirect a write.
    Named inode checks still refuse any replacement and retain foreign entries.
    """
    def __init__(self, home, files, new_directories):
        f = api(); self.home = home; self.fds = {}; self.identities = {}; self.created = []
        self.new = set(new_directories); self.allowed = {}; self.parents = {}; self.workspace = None
        try:
            for name in set(files) | self.new:
                relative = Path(name)
                f.require(type(name) is str and not relative.is_absolute()
                    and name == relative.as_posix() and name != '.'
                    and not any(p in ('.','..') for p in relative.parts),
                    'ordinary_update_directory_relative_path_required')
            required = {''}
            for name in files:
                child = Path(name)
                while child != Path('.'):
                    parent = str(child.parent) if child.parent != Path('.') else ''
                    self.allowed.setdefault(parent,set()).add(child.name)
                    required.add(parent); child = child.parent
            f.require(self.new <= required and '' not in self.new,
                'ordinary_update_unused_new_directory')
            self.ordered = sorted(required,key=lambda n:(len(Path(n).parts),n))
            for name in self.ordered:
                parent = str(Path(name).parent) if name and Path(name).parent != Path('.') else ''
                self.parents[name] = parent
                if name in self.new:
                    if parent in self.fds:
                        try: os.stat(Path(name).name,dir_fd=self.fds[parent],follow_symlinks=False)
                        except FileNotFoundError: pass
                        else: f.require(False,'ordinary_update_new_directory_exists')
                    else:
                        f.require(parent in self.new,'ordinary_update_new_directory_parent_required')
                    continue
                f.require(not name or parent in self.fds,'ordinary_update_missing_directory')
                fd = (os.open(home,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW) if not name else
                    os.open(Path(name).name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=self.fds[parent]))
                self.fds[name] = fd; self.identities[name] = self.identity(os.fstat(fd))
            self.prove()
        except BaseException:
            self.close(); raise

    @staticmethod
    def identity(info):
        api().require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700,'ordinary_update_private_directory_required')
        return tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_mode'))

    def prove(self):
        f = api()
        if self.workspace is not None:
            path, fd, identity = self.workspace
            f.require(self.identity(path.lstat()) == self.identity(os.fstat(fd)) == identity,
                'ordinary_update_directory_staging_changed')
        for name in self.ordered:
            parent = self.parents[name]
            if name not in self.fds:
                if parent in self.fds:
                    try: os.stat(Path(name).name,dir_fd=self.fds[parent],follow_symlinks=False)
                    except FileNotFoundError: continue
                    f.require(False,'ordinary_update_new_directory_appeared')
                continue
            named = (self.home.lstat() if not name else
                os.stat(Path(name).name,dir_fd=self.fds[parent],follow_symlinks=False))
            f.require(self.identity(named) == self.identity(os.fstat(self.fds[name])) == self.identities[name],
                'ordinary_update_directory_ownership_changed')
            if name in self.created:
                f.require(set(os.listdir(self.fds[name])) <= self.allowed.get(name,set()),
                    'ordinary_update_directory_inventory_changed')

    def create(self, staging):
        # Establish ownership before a source name is published. The transaction
        # namespace is private and owned, like its existing before/after trees.
        staging.mkdir(mode=0o700)
        fd = os.open(staging,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        self.workspace = (staging,fd,self.identity(os.fstat(fd)))
        self.prove()
        for number,name in enumerate(self.ordered):
            if name not in self.new: continue
            self.prove(); parent_fd = self.fds[self.parents[name]]
            temporary = 'new-'+str(number)
            os.mkdir(temporary,mode=0o700,dir_fd=fd)
            owned_fd = os.open(temporary,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            try:
                identity = self.identity(os.fstat(owned_fd))
                api().require(self.identity(os.stat(temporary,dir_fd=fd,follow_symlinks=False)) == identity,
                    'ordinary_update_directory_staging_changed')
                rename_directory_noreplace(fd,temporary,parent_fd,Path(name).name)
                self.fds[name] = owned_fd; owned_fd = None
                self.identities[name] = identity; self.created.append(name)
                self.prove(); os.fsync(parent_fd); os.fsync(fd)
            finally:
                if owned_fd is not None: os.close(owned_fd)

    def parent_fd(self, name):
        parent = str(Path(name).parent) if Path(name).parent != Path('.') else ''
        return self.fds.get(parent)

    def remove_created(self):
        self.prove()
        if not self.created: return
        staging, staging_fd, _ = self.workspace
        for number,name in enumerate(reversed(self.created[:])):
            self.prove()
            api().require(not os.listdir(self.fds[name]),'ordinary_update_directory_not_empty')
            parent_fd = self.fds[self.parents[name]]; quarantine = 'removed-'+str(number)
            # A concurrent replacement is moved intact, never recursively erased.
            # Verify the moved inode in our private namespace before removing it.
            rename_directory_noreplace(parent_fd,Path(name).name,staging_fd,quarantine)
            info = os.stat(quarantine,dir_fd=staging_fd,follow_symlinks=False)
            moved = tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_mode'))
            if moved != self.identities[name]:
                # Undo our move if its destination remains absent. NOREPLACE
                # preserves any third-party entry that appeared in the meantime.
                rename_directory_noreplace(staging_fd,quarantine,parent_fd,Path(name).name)
                api().require(False,'ordinary_update_directory_ownership_changed')
            api().require(not os.listdir(self.fds[name]),'ordinary_update_directory_not_empty')
            os.rmdir(quarantine,dir_fd=staging_fd); os.fsync(parent_fd); os.fsync(staging_fd)
            os.close(self.fds.pop(name)); self.identities.pop(name); self.created.remove(name)
            self.prove()

    def close(self):
        if self.workspace is not None:
            os.close(self.workspace[1]); self.workspace = None
        for fd in reversed(list(self.fds.values())): os.close(fd)
        self.fds.clear()

    def __enter__(self): return self
    def __exit__(self,*args): self.close()


def rename_directory_noreplace(source_fd, source_name, target_fd, target_name):
    """Linux atomic directory claim; an existing destination is never replaced."""
    import ctypes
    libc = ctypes.CDLL(None,use_errno=True)
    rename = libc.renameat2
    rename.argtypes = (ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(source_fd,os.fsencode(source_name),target_fd,os.fsencode(target_name),1) != 0:
        number = ctypes.get_errno()
        raise OSError(number,os.strerror(number))


def update_file_state_at(path, parent_fd):
    """Read one owned regular file relative to a retained parent descriptor."""
    f = api()
    try: fd = os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent_fd)
    except FileNotFoundError: return None
    try:
        first = os.fstat(fd)
        f.require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid() and first.st_nlink == 1,
            'ordinary_update_owned_regular_file_required')
        with os.fdopen(fd,'rb',closefd=False) as stream: data = stream.read(64*1024**2+1)
        last = os.fstat(fd); named = os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False)
        keys = ('st_dev','st_ino','st_uid','st_nlink','st_mode','st_size','st_mtime_ns','st_ctime_ns')
        f.require(len(data) <= 64*1024**2 and all(getattr(first,k)==getattr(last,k)==getattr(named,k) for k in keys),
            'ordinary_update_file_identity_changed')
        return {'data':data,'mode':stat.S_IMODE(first.st_mode),
            'identity':tuple(getattr(first,k) for k in ('st_dev','st_ino','st_uid','st_nlink','st_mode'))}
    finally: os.close(fd)


def update_file_state(path, parent_fd=None):
    """Exact bytes and inode custody; absence is never an empty beforeimage."""
    if parent_fd is not None: return update_file_state_at(path,parent_fd)
    f = api()
    if not os.path.lexists(path): return None
    first = path.lstat()
    data = f.owned_file(path)
    last = path.lstat()
    keys = ('st_dev','st_ino','st_uid','st_nlink','st_mode')
    identity = tuple(getattr(first,k) for k in keys)
    f.require(identity == tuple(getattr(last,k) for k in keys), 'ordinary_update_file_identity_changed')
    return {'data':data,'mode':stat.S_IMODE(first.st_mode),'identity':identity}


def same_update_file(path, expected, parent_fd=None):
    return update_file_state(path,parent_fd) == expected


def publish_update_file(path, data, mode, before, owned, name, parent_fd=None):
    """Publish one recorded inode; new files use an exclusive hard-link claim."""
    f = api(); temporary = path.with_name(path.name+'.ordinary-staged')
    target = path if parent_fd is None else path.name
    stage = temporary if parent_fd is None else temporary.name
    def present():
        try: os.stat(stage,dir_fd=parent_fd,follow_symlinks=False); return True
        except FileNotFoundError: return False
    try:
        fd = os.open(stage,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode,dir_fd=parent_fd)
    except FileExistsError as exc:
        from scripts.dsh_prepare import StopUnconfirmed
        raise StopUnconfirmed('ordinary update staging path ownership requires reconciliation') from exc
    created = None
    try:
        os.fchmod(fd,mode)
        with os.fdopen(fd,'wb',closefd=False) as stream:
            stream.write(data);stream.flush();os.fsync(fd)
        st = os.fstat(fd)
        created = {'data':data,'mode':mode,'identity':tuple(getattr(st,k) for k in
            ('st_dev','st_ino','st_uid','st_nlink','st_mode'))}
        f.require(same_update_file(path,before,parent_fd),'ordinary_update_publication_identity_changed')
        f.require(same_update_file(temporary,created,parent_fd),'ordinary_update_staging_identity_changed')
        owned[name] = created
        if before is None:
            os.link(stage,target,src_dir_fd=parent_fd,dst_dir_fd=parent_fd,follow_symlinks=False)
            # owned_file intentionally rejects hard links; here both names
            # must still identify exactly our descriptor before unlinking one.
            linked = tuple(2 if i == 3 else value for i,value in enumerate(created['identity']))
            for candidate in (temporary,path):
                info=os.stat(candidate if parent_fd is None else candidate.name,dir_fd=parent_fd,follow_symlinks=False)
                f.require(tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_nlink','st_mode'))
                    == linked,'ordinary_update_link_identity_changed')
            os.unlink(stage,dir_fd=parent_fd)
        else:
            os.replace(stage,target,src_dir_fd=parent_fd,dst_dir_fd=parent_fd)
        f.require(same_update_file(path,created,parent_fd),'ordinary_update_published_identity_changed')
        if parent_fd is None: sync_directory(path.parent)
        else: os.fsync(parent_fd)
    finally:
        os.close(fd)
        if present():
            # If publication failed, only our own exact staging inode is removed.
            if created is None or not same_update_file(temporary,created,parent_fd):
                from scripts.dsh_prepare import StopUnconfirmed
                raise StopUnconfirmed('ordinary update staging ownership requires reconciliation')
            os.unlink(stage,dir_fd=parent_fd)


def restore_update_files(home, saved, owned, directories=None):
    f = api()
    def parent_fd(name): return directories.parent_fd(name) if directories is not None else None
    # Prove the entire affected set before changing any path. Same bytes on a
    # foreign inode or with a changed mode do not confer restoration ownership.
    for name,before in saved.items():
        state = update_file_state(home/name,parent_fd(name))
        f.require(state == before or (name in owned and state == owned[name]),
            'ordinary_update_restore_ownership_changed')
    restored = {}
    for name,before in reversed(list(saved.items())):
        if directories is not None: directories.prove()
        path = home/name; state = update_file_state(path,parent_fd(name))
        if state == before: continue
        f.require(name in owned and state == owned[name],'ordinary_update_restore_ownership_changed')
        if before is None:
            os.unlink(path if parent_fd(name) is None else path.name,dir_fd=parent_fd(name))
            if parent_fd(name) is None: sync_directory(path.parent)
            else: os.fsync(parent_fd(name))
        else:
            publish_update_file(path,before['data'],before['mode'],owned[name],restored,name,**({'parent_fd':parent_fd(name)} if directories is not None else {}))
    for name,before in saved.items():
        current = update_file_state(home/name,parent_fd(name))
        f.require(current == restored.get(name,before),
            'ordinary_update_restore_failed')


def private_parents(root, relative):
    """Create each new private beforeimage directory with its own explicit mode.

    pathlib parents=True uses default permissions for intermediate components;
    no existing historical directory is repaired or relaxed here.
    """
    f = api(); f.directory(root)
    name = Path(relative)
    f.require(not name.is_absolute() and all(p not in ('.','..') for p in name.parts),
        'ordinary_beforeimage_relative_path_required')
    current = root
    for part in name.parent.parts:
        current = current/part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            pass
        f.directory(current)
    return current


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def inputs(request, budget):
    f = api()
    f.require(type(request) is dict and set(request) == {'schema','seconds','home','installation_input','previous_input','current_input',
        'marker','source_receipt','configuration','pending_configuration','profile','launcher','tool_search_defer','credential_files'} |
        ({'prior_rolled_back'} if request.get('schema') == 'friday.ordinary-telegram-activation.v2' else set())
        and request['schema'] in ('friday.ordinary-telegram-activation.v1','friday.ordinary-telegram-activation.v2')
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 180, 'ordinary_explicit_request_required')
    home = f.directory(f.canonical(request['home'])); source = home/'hermes-agent'
    paths = {name:budget.call(f.pin, request[name]) for name in request if name not in ('schema','seconds','home','tool_search_defer','credential_files','prior_rolled_back')}
    f.require(paths['marker'] == home/f.MARKER and paths['source_receipt'] == home/'hermes-agent.source.json'
        and paths['configuration'] == home/'config.yaml' and paths['profile'] == home/'FRIDAY-PROFILE.json'
        and paths['launcher'] == source/'.hermes/bin/hermes', 'ordinary_exact_installed_inputs_required')
    credentials=request['credential_files']
    f.require(type(credentials) is dict and set(credentials)=={'.env','auth.json'}, 'ordinary_credential_pins_required')
    for name,ref in credentials.items():
        path=home/name
        if ref is None:
            f.require(not os.path.lexists(path),'ordinary_credential_absence_changed')
        else:
            f.require(f.pin(ref)==path and f.digest(f.owned_file(path,private=True))==ref['sha256'],'ordinary_credential_pin_changed')
    previous = budget.call(f.read_json, paths['previous_input'])
    current = budget.call(f.read_json, paths['current_input'])
    marker = budget.call(f.read_json, paths['marker'])
    f.require(marker.get('completion_stage') == 'CLI_HOST_ONLY' and marker.get('runtime_ready') is False
        and marker.get('gateway_installed') is False and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('source_receipt_sha256') == request['source_receipt']['sha256']
        and marker.get('input_sha256') == request['installation_input']['sha256']
        and marker.get('postinstall_source_input') == request['previous_input'], 'ordinary_cli_history_required')
    original = budget.call(f.read_json, paths['installation_input'])
    f.require({k:v for k,v in original.items() if k != 'project_files'} ==
        {k:v for k,v in previous.items() if k != 'project_files'}, 'ordinary_original_installation_scope_changed')
    f.require(request['previous_input'] != request['current_input'], 'ordinary_update_new_input_required')
    f.require({k:v for k,v in previous.items() if k != 'project_files'} ==
        {k:v for k,v in current.items() if k != 'project_files'} and current['home'] == str(home),
        'ordinary_deployment_scope_changed')
    f.require(f.cli_historical_scope_closed(marker['original_attempt'],'friday.native-install.v1')
        and (marker.get('cli_segment') is None or f.cli_historical_scope_closed(marker['cli_segment']['clock'],'friday.cli-segment-clock.v1')),
        'ordinary_previous_scope_not_closed')
    f.spec_checked(current, cli_only=True)
    # The current source is an exact ordered prefix; the only new layer is this
    # reviewed manifest. No old layer, consumed intent or historical pin moves.
    receipt = budget.call(f.read_json, paths['source_receipt'])
    donors = {r['id']:r for r in f.read_json(f.pin(current['sources_lock']))['repositories']}
    f.composition_checked(previous, source, receipt, donors['hermes'])
    manifest = f.read_json(f.ROOT/MANIFEST)
    f.require(current['project_files'][MANIFEST] == f.digest(f.owned_file(f.ROOT/MANIFEST))
        and set(current['project_files']) == set(previous['project_files']) | {MANIFEST, manifest['patch'], 'scripts/friday_ordinary_install.py'}
        and all(current['project_files'][name] == pin for name,pin in previous['project_files'].items()
                if name not in ('scripts/friday_install.py','scripts/friday_native.py','scripts/friday_start.py','plugins/friday_rework/onboarding.py')),
        'ordinary_additive_source_required')
    f.require(manifest['base_commit'] == receipt['commit'], 'ordinary_manifest_required')
    f.require(set(manifest['installed_prefix']) == {r['manifest'] for r in receipt['layers']}
        and all(manifest['installed_prefix'][r['manifest']] == r['manifest_sha256'] for r in receipt['layers']),
        'ordinary_exact_prefix_required')
    # Overlay manifests use patch prerequisites for composition. Prefix manifests
    # are pinned separately so old private scopes cannot be silently rewritten.
    for row in manifest['files']:
        p = source/row['path']
        if row['new_file']:
            f.require(not p.exists() and not p.is_symlink(), 'ordinary_new_source_exists')
        else:
            f.require(f.digest(f.owned_file(p)) == row['before_sha256']
                and receipt['files'][row['path']]['sha256'] == row['before_sha256'], 'ordinary_source_changed')
    f.require(f.digest(f.owned_file(f.ROOT/manifest['patch'])) == manifest['patch_sha256'], 'ordinary_patch_changed')
    raw = f.owned_file(paths['pending_configuration'], private=True)
    # Native YAML parser is imported only after the complete old source inventory.
    f.native_packages(source)
    from hermes_cli.friday_dashboard_owner import source_identity
    source_identity(home,source=source)
    f.require(all(f.digest(f.owned_file(home/name,private=True))==pin for name,pin in marker['profile_files'].items()),'ordinary_profile_history_changed')
    from hermes_cli.config_effective import read_user_config_effective_readonly
    cfg = budget.call(read_user_config_effective_readonly, paths['pending_configuration'])
    old_cfg = budget.call(read_user_config_effective_readonly, home/'config.yaml')
    import copy
    changed = copy.deepcopy(old_cfg)
    changed['platforms']['telegram'].setdefault('extra', {})['drop_pending_on_cold_boot'] = False
    changed['platforms']['telegram']['extra']['unauthorized_dm_behavior'] = 'pair'
    changed['gateway']['systemd_watchdog_seconds'] = 30
    deferred = request['tool_search_defer']
    f.require(type(deferred) is list and bool(deferred) and len(deferred) == len(set(deferred))
        and all(isinstance(n,str) and n.isidentifier() for n in deferred)
        and not {'read_file','session_search','clarify'}.intersection(deferred), 'ordinary_progressive_tools_required')
    plans = changed['plugins']['entries']['friday_rework']['settings']['onboarding']['templates']
    f.require(bool(plans), 'ordinary_worker_free_template_required')
    # Keep the full worker template intact. An explicit ordinary template uses
    # the same local model, personality, tools and required scoped credentials.
    ordinary_name = 'friday-ordinary-local'
    f.require('friday-local' in plans and ordinary_name not in plans,
              'ordinary_explicit_template_required')
    template = copy.deepcopy(plans['friday-local'])
    template.pop('worker_inputs', None)
    own = template['config']['plugins']['entries']['friday_rework']['settings']
    f.require(own.get('runtime') == {'enabled':False} and 'worker_requirements' not in own,
              'ordinary_worker_free_template_required')
    template['config'].setdefault('tools',{}).setdefault('tool_search',{})['defer'] = deferred
    plans[ordinary_name] = template
    f.require(cfg == changed, 'ordinary_only_pending_and_progressive_tools_change_required')
    settings = cfg['plugins']['entries']['friday_rework']['settings']
    f.require(settings.get('runtime') == {'enabled':False} and 'worker_requirements' not in settings
        and settings.get('user_isolation') is None and cfg['gateway'].get('profile_routes',[]) == []
        and len(settings['product_access']['accounts']) == 1
        and settings['product_access']['accounts'][0]['platform'] == 'telegram', 'ordinary_worker_free_bootstrap_required')
    if request['schema'] == 'friday.ordinary-telegram-activation.v1':
        f.require(not os.path.lexists(home/TRANSACTION)
            and not os.path.lexists(home/'preparation/ordinary-gateway-archive'), 'ordinary_transaction_already_exists')
    else:
        recovery_checked(request, home, manifest)
    return home, source, paths, previous, current, marker, receipt, manifest, raw, cfg


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def saved_names(manifest):
    return ['FRIDAY-INSTALL.json','hermes-agent.source.json','config.yaml','hermes-agent/install-stamp.json'] + [
        'hermes-agent/'+r['path'] for r in manifest['files'] if not r['new_file']] + ['plugins/friday_rework/onboarding.py']


def no_consumer(home):
    # Same native ownership boundary as explicit source rollback: never stop,
    # uninstall or wake a service to manufacture eligibility for continuation.
    f = api(); f.native_packages(home/'hermes-agent')
    from gateway import host_rendezvous as hr
    from hermes_cli import gateway as gw
    f.require(not gw.get_systemd_unit_path(system=False).exists()
        and not gw.get_systemd_unit_path(system=True).exists()
        and hr.read_record(hr.ROLE_GATEWAY,include_stale=True) is None
        and not gw.find_gateway_pids(), 'ordinary_recovery_no_consumer_required')


def recovery_checked(request, home, manifest):
    """One explicit corrected host candidate after a proven source-only refusal."""
    f=api(); ref=request['prior_rolled_back']; tx=home/TRANSACTION
    f.require(type(ref) is dict and set(ref)=={'request','intent','rollback','archive'},
              'ordinary_recovery_exact_references_required')
    f.directory(tx); before=f.directory(tx/'before')
    f.require({p.name for p in tx.iterdir()} == {'before','intent.json','rolled-back.json'},
              'ordinary_recovery_uncommitted_rollback_required')
    for key,name in [('intent','intent.json'),('rollback','rolled-back.json')]:
        f.require(f.pin(ref[key])==tx/name,'ordinary_recovery_exact_references_required')
    intent=f.read_json(tx/'intent.json'); rollback=f.read_json(tx/'rolled-back.json')
    old=f.read_json(f.pin(ref['request']))
    f.require(intent.get('schema')=='friday.ordinary-telegram-transaction.v1'
        and intent.get('state')=='SOURCE_TRANSACTION_STARTED_NOT_RUNTIME'
        and intent.get('request_sha256')==ref['request']['sha256']
        and rollback=={'state':'ROLLED_BACK_SOURCE_ONLY_NO_RUNTIME_STARTED'},
        'ordinary_recovery_closed_rollback_required')
    f.require(old.get('schema')=='friday.ordinary-telegram-activation.v1'
        and {k:v for k,v in request.items() if k not in ('schema','current_input','prior_rolled_back')} ==
            {k:v for k,v in old.items() if k not in ('schema','current_input')},
        'ordinary_recovery_scope_changed')
    old_input=f.read_json(f.pin(old['current_input']))
    new_input=f.read_json(f.pin(request['current_input']))
    f.require({k:v for k,v in old_input.items() if k!='project_files'} ==
              {k:v for k,v in new_input.items() if k!='project_files'},'ordinary_recovery_scope_changed')
    a=old_input['project_files']; b=new_input['project_files']
    changed={name for name in set(a)|set(b) if a.get(name)!=b.get(name)}
    f.require(changed=={'scripts/friday_ordinary_install.py'} and set(a)==set(b)
        and b['scripts/friday_ordinary_install.py']==f.digest(f.owned_file(f.ROOT/'scripts/friday_ordinary_install.py')),
        'ordinary_recovery_corrected_host_candidate_required')
    f.require(set(intent.get('before',{}))==set(saved_names(manifest))
        and intent.get('new_files')==[r['path'] for r in manifest['files'] if r['new_file']],
        'ordinary_recovery_beforeimage_scope_changed')
    # Validate the complete retained tree, including absence of untracked files.
    expected=set(intent['before'])
    actual=set()
    for path in before.rglob('*'):
        if path.is_dir(): f.directory(path)
        else:
            f.owned_file(path,private=True); actual.add(str(path.relative_to(before)))
    f.require(actual==expected,'ordinary_recovery_beforeimage_scope_changed')
    for name,row in intent['before'].items():
        f.require(type(row) is dict and set(row)=={'sha256','mode'}
            and type(row['mode']) is int and row['mode'] in (0o600,0o644,0o700,0o755),
            'ordinary_recovery_beforeimage_mode_changed')
        f.require(f.digest(f.owned_file(before/name,private=True))==row['sha256']
            and f.digest(f.owned_file(home/name))==row['sha256']
            and stat.S_IMODE((home/name).stat().st_mode)==row['mode'],
            'ordinary_recovery_beforeimage_changed')
    for name in intent['new_files']:
        f.require(not os.path.lexists(home/'hermes-agent'/name),'ordinary_recovery_new_source_present')
    archive=home/'preparation/ordinary-gateway-archive'/ref['request']['sha256']
    f.require(ref['archive']==str(archive) and not os.path.lexists(archive)
        and not os.path.lexists(archive.with_name(archive.name+'.json')),
              'ordinary_recovery_archive_required')
    if os.path.lexists(archive.parent): f.directory(archive.parent)
    no_consumer(home)
    return archive


def archive_rollback(request, home, manifest):
    f=api(); archive=recovery_checked(request,home,manifest); tx=home/TRANSACTION
    if not archive.parent.exists():
        archive.parent.mkdir(mode=0o700); sync_directory(archive.parent.parent)
    # The retained transaction is never edited or deleted. The sibling receipt
    # and directory rename are durable before the new standard-path journal.
    receipt=archive.with_name(archive.name+'.json')
    f.require(not os.path.lexists(receipt),'ordinary_recovery_archive_required')
    os.rename(tx,archive); sync_directory(archive.parent); sync_directory(tx.parent)
    write(receipt,encoded({'schema':'friday.ordinary-telegram-rollback-archive.v1',
        'state':'ROLLED_BACK_TRANSACTION_RETAINED_NOT_REPLAYED',
        'prior_rolled_back':request['prior_rolled_back'],'archive':str(archive)}))
    sync_directory(archive.parent)


def activate(request, request_path, budget):
    """Journal beforeimages, apply exact layer, publish native marker last.

    Exclusive file lock plus exact rechecks protect this transaction. Before any
    consumer starts, exceptions restore its own bytes; the journal is retained
    and never blindly retried. Ambiguous external service effects are outside
    this source-only action and are handled by the native service handoff.
    """
    f = api()
    home = f.directory(f.canonical(request['home']))
    fd = os.open(home, os.O_RDONLY|os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        prepared = inputs(request, budget)
        home, source, paths, previous, current, marker, receipt, manifest, config_raw, cfg = prepared
        f.require(f.read_json(request_path) == request, 'ordinary_request_changed')
        # Read and validate every saved owner/mode before creating any journal.
        names = saved_names(manifest)
        saved = {}; history = {}; beforeimages = {}
        for name in names:
            path=home/name
            data=f.owned_file(path,private=name != 'hermes-agent/install-stamp.json' and not name.startswith('hermes-agent/hermes_cli/'))
            mode=stat.S_IMODE(path.stat().st_mode)
            f.require(mode in (0o600,0o644,0o700,0o755),'ordinary_beforeimage_mode_required')
            beforeimages[name]=data; saved[name]={'sha256':f.digest(data),'mode':mode}
        if request.get('schema') == 'friday.ordinary-telegram-activation.v2':
            archive_rollback(request,home,manifest)
        transaction = home/TRANSACTION
        transaction.mkdir(mode=0o700)
        before = transaction/'before'; before.mkdir(mode=0o700)
        for name in names:
            data = beforeimages[name]
            target = before/name; private_parents(before,name)
            write(target,data)
            if name == 'FRIDAY-INSTALL.json': history[str(target.relative_to(home))] = f.digest(data)
        for path in home.glob('FRIDAY-INSTALL.*'):
            if path.name != f.MARKER and path.is_file(): history[path.name] = f.digest(f.owned_file(path,private=True))
        write(transaction/'intent.json',encoded({'schema':'friday.ordinary-telegram-transaction.v1',
            'state':'SOURCE_TRANSACTION_STARTED_NOT_RUNTIME','request_sha256':f.digest(f.owned_file(request_path,private=True)),
            'before':saved,'new_files':[r['path'] for r in manifest['files'] if r['new_file']]}))
        touched = []
        try:
            for name,ref in request['credential_files'].items():
                f.require((not os.path.lexists(home/name)) if ref is None else f.digest(f.owned_file(home/name,private=True))==ref['sha256'],'ordinary_credential_pin_changed')
            from scripts.dsh_prepare import run
            apply_env = f.clean_environment(home)
            apply_env['GIT_CEILING_DIRECTORIES'] = str(source.parent)
            for checking in (True,False):
                command = ['git','--no-optional-locks','apply','--whitespace=nowarn']
                if checking: command.append('--check')
                command.append(str(f.ROOT/manifest['patch']))
                run(command, source, timeout=min(20,budget.check(reserve=1)),env=apply_env,deadline=budget.deadline)
            for row in manifest['files']:
                p = source/row['path']; data = f.owned_file(p)
                f.require(f.digest(data) == row['sha256'] and len(data) == row['bytes'], 'ordinary_patch_output_changed')
                receipt['files'][row['path']] = {k:row[k] for k in ('sha256','bytes','mode')}
            receipt['layers'].append({'manifest':MANIFEST,'manifest_sha256':current['project_files'][MANIFEST],
                'patch_sha256':manifest['patch_sha256']})
            f.composition_checked(current,source,receipt, {r['id']:r for r in f.read_json(f.pin(current['sources_lock']))['repositories']}['hermes'])
            plugin_name = 'plugins/friday_rework/onboarding.py'
            f.require(f.digest(f.owned_file(home/plugin_name,private=True)) == previous['project_files'][plugin_name], 'ordinary_installed_plugin_changed')
            replace(home/plugin_name,f.owned_file(f.ROOT/plugin_name),saved[plugin_name]['mode']); touched.append(plugin_name)
            stamp = f.read_json(source/'install-stamp.json')
            stamp['fridaySource'] = {'baseTree':receipt['base_tree'],'layers':receipt['layers']}
            for name, data in [('hermes-agent.source.json',encoded(receipt)), ('hermes-agent/install-stamp.json',encoded(stamp)), ('config.yaml',config_raw)]:
                budget.check(); replace(home/name,data); touched.append(name)
            # Reload the changed installed modules in a fresh interpreter at
            # normal launch. This installer uses pure binding helpers only.
            import importlib.util
            spec = importlib.util.spec_from_file_location('_friday_ordinary_binding',source/'hermes_cli/friday_ordinary_gateway.py')
            ordinary = importlib.util.module_from_spec(spec); spec.loader.exec_module(ordinary)
            settings = cfg['plugins']['entries']['friday_rework']['settings']
            binding = {'schema':ordinary.SCHEMA,'scope':'TELEGRAM_RECEIVER_AND_AUTHENTICATED_ONBOARDING_ONLY',
                'configuration_sha256':ordinary.normalized_configuration(cfg),
                'credential_files':{n:(ordinary.credential_identity(home)[0] if n == '.env' else f.digest(f.owned_file(home/n,private=True)) if os.path.lexists(home/n) else None) for n in ('.env','auth.json')},
                'profile_sha256':f.digest(f.owned_file(home/'FRIDAY-PROFILE.json',private=True)),
                'source_receipt_sha256':f.digest(encoded(receipt)),
                'baseline':{'runtime_profiles':settings['product_access']['accounts'][0]['runtime_profiles'],
                            'admin_profiles':settings['admin']['profiles'],'telegram_allowed_users':ordinary.credential_identity(home)[1]}, 'history':history,
                'operator_entry':{'script':{'path':str(f.ROOT/'scripts/friday_native.py'),'sha256':current['project_files']['scripts/friday_native.py']},
                    'input':request['current_input']}}
            updated = dict(marker,completion_stage=ordinary.STAGE,input_sha256=request['current_input']['sha256'],
                source_receipt_sha256=binding['source_receipt_sha256'],ordinary_gateway=binding)
            updated['profile_files'] = dict(marker['profile_files'],**{'config.yaml':f.digest(config_raw)})
            updated['plugin_files'] = dict(marker['plugin_files'],**{plugin_name:current['project_files'][plugin_name]})
            budget.check(); replace(home/f.MARKER,encoded(updated)); touched.append(f.MARKER)
            write(transaction/'committed.json', encoded({'state':'SOURCE_ACTIVATED_NOT_RUNTIME_ACCEPTED','workers_enabled':False,
                'source_receipt_sha256':binding['source_receipt_sha256'],'gateway_started':False}))
            return {'state':'TELEGRAM_ORDINARY_SOURCE_ACTIVATED','ready':False,'workers_enabled':False,'gateway_started':False,
                'ordinary_onboarding':'AUTHENTICATED_NATIVE_API_AND_PAIRING_REQUIRED','full_release_accepted':False}
        except BaseException as original:
            # No service or message effect belongs to this transaction. Restore
            # exact owned beforeimages and only the newly introduced source files.
            try:
                for row in manifest['files']:
                    path = source/row['path']
                    if row['new_file'] and path.exists():
                        f.require(f.digest(f.owned_file(path))==row['sha256'],'ordinary_new_source_ownership_changed')
                        path.unlink()
                for name,row in saved.items():
                    replace(home/name,f.owned_file(before/name,private=True),row['mode'])
                write(transaction/'rolled-back.json',encoded({'state':'ROLLED_BACK_SOURCE_ONLY_NO_RUNTIME_STARTED'}))
            except BaseException as restoration:
                from scripts.dsh_prepare import StopUnconfirmed
                f.remember_secondary(original,restoration)
                raise StopUnconfirmed('ordinary source restoration requires reconciliation') from original
            raise
    finally:
        os.close(fd)


def checked_update_keyless_history(home, reference, predecessor, history):
    """Read the consumed recovery as ancestry; never replay or revalidate setup."""
    import re
    f = api(); recovery = f.read_json(f.pin(reference))
    recovery_id = recovery.get('recovery_id')
    f.require(predecessor.get('schema') == PROJECT_RUNTIME_SCHEMA
        and recovery.get('schema') == 'friday.ordinary-worker-keyless-recovery.v1'
        and isinstance(recovery_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,64}',recovery_id)
        and recovery.get('home') == str(home)
        and recovery.get('installed_input') == predecessor['current_input']
        and recovery.get('transition') == 'NEW_PRODUCT_MAINTENANCE_NO_RUNTIME_AUTHORITY',
        'ordinary_update_exact_keyless_predecessor_required')
    old = f.read_json(f.pin(recovery['installed_input']))
    new = f.read_json(f.pin(recovery['recovery_input']))
    allowed = {'scripts/friday_install.py','scripts/friday_worker_preparation.py'}
    before = old['project_files']; after = new['project_files']
    f.require(len(before) == 227 and set(before) == set(after) and allowed <= set(before)
        and {k:v for k,v in old.items() if k != 'project_files'} ==
            {k:v for k,v in new.items() if k != 'project_files'}
        and all(after[k] == h for k,h in before.items() if k not in allowed)
        and all(after[k] != before[k] for k in allowed),
        'ordinary_update_keyless_input_changed')
    refs = recovery.get('history')
    f.require(type(refs) is list and len(refs) == len(history)
        and all(type(row) is dict and set(row) == {'path','sha256'} for row in refs)
        and {str(home/n):h for n,h in history.items()} == {r['path']:r['sha256'] for r in refs},
        'ordinary_update_keyless_history_changed')
    name = 'preparation/ordinary-keyless-recovery-'+recovery_id
    tx = f.directory(home/name)
    intent = f.read_json(tx/'intent.json'); committed = f.read_json(tx/'committed.json')
    mapping = {str(home/'profiles'/recovery['profile']/'workers/qualification'):str(tx/'failed-qualification')}
    f.require(intent.get('schema') == recovery['schema'] and intent.get('state') == 'CONSUMED_NO_RETRY'
        and intent.get('request_sha256') == reference['sha256']
        and committed.get('request_sha256') == reference['sha256']
        and intent.get('recovery_id') == committed.get('recovery_id') == recovery_id
        and committed.get('state') == 'REPAIRED_CONSUMERS_STOPPED_WORKERS_OFF_NEW_RUNTIME_NOT_AUTHORIZED'
        and intent.get('failure') == recovery['failure']
        and intent.get('archive_mapping') == committed.get('archive_mapping') == mapping
        and intent.get('original_attempt') == committed.get('original_attempt')
        and intent.get('runtime_authority') == committed.get('runtime_acceptance') == committed.get('new_runtime_authority') == 'NOT_GRANTED'
        and all(row.get(k) is False for row in (intent,committed)
            for k in ('consumers_started','workers_enabled','resume_allowed'))
        and committed.get('ready') is False and committed.get('old_attempt_retry_authorized') is False
        and not os.path.lexists(tx/'rolled-back.json'),
        'ordinary_update_committed_keyless_predecessor_required')
    previous_tx = home/'preparation'/('ordinary-source-update-'+predecessor['previous_input']['sha256'])
    f.require(f.read_json(previous_tx/'intent.json').get('project_only') is True
        and f.read_json(previous_tx/'committed.json').get('project_only') is True
        and f.read_json(previous_tx/'committed.json').get('source_receipt_sha256') == recovery['source_receipt']['sha256']
        and f.digest(f.owned_file(tx/'before'/f.MARKER,private=True)) == recovery['root_marker']['sha256'],
        'ordinary_update_keyless_source_binding_changed')
    failed = recovery['qualification_files']
    f.require(set(failed) == {'failure.json','dsh-safety/inputs/bootstrap.py','dsh-safety/inputs/web-ca.pem','dsh-safety/inputs/web-network.mjs'}
        and all(f.digest(f.owned_file(tx/folder/n,private=True)) == h
            for folder in ('failed-before','failed-qualification') for n,h in failed.items()),
        'ordinary_update_keyless_archive_changed')
    return name


def checked_source81_budget_history(home, reference, predecessor):
    """Exact closed Source80 budget-only journal; no operation is dispatched."""
    f=api()
    f.require(type(reference) is dict and reference.get('sha256') == SOURCE81_BUDGET_REQUEST,
        'ordinary_update_exact_budget_history_required')
    request=f.read_json(f.pin(reference))
    f.require(request.get('schema') == REBIND_BUDGET_SCHEMA and request.get('home') == str(home)
        and request.get('profile') == 'dest_telegram' and request.get('seconds') == 180
        and request['previous_input'] == predecessor['current_input']
        and request['current_input']['sha256'] == FILE_TOOL_CONTRACT_PREVIOUS_INPUT,
        'ordinary_update_closed_budget_binding_required')
    f.pin(request['previous_input']);f.pin(request['current_input'])
    tx=f.directory(home/'preparation'/('ordinary-inference-rebind-'+request['previous_input']['sha256']))
    intent=f.read_json(tx/'intent.json');committed=f.read_json(tx/'committed.json')
    names={f.MARKER,'config.yaml','profiles/dest_telegram/config.yaml',
        'profiles/dest_telegram/.friday-onboarding.json','profiles/dest_telegram/.friday-user-scope.json'}
    f.require(intent.get('schema') == REBIND_BUDGET_SCHEMA and intent.get('state') == 'CONSUMED_NO_RETRY'
        and intent.get('request_sha256') == reference['sha256'] and intent.get('seconds') == 180
        and intent.get('previous_input') == request['previous_input']
        and intent.get('current_input') == request['current_input']
        and committed.get('state') == 'EXACT_REQUEST_BUDGET_REBOUND_CONSUMERS_STOPPED_NOT_RUNTIME_ACCEPTED'
        and committed.get('ready') is False
        and all(body.get(field) is False for body in (intent,committed)
            for field in ('consumers_started','workers_enabled','database_changed'))
        and set(request['before']) == set(intent['before']) == set(committed['after']) == names
        and all(intent['before'][n] == {'sha256':request['before'][n]['sha256'],'mode':0o600}
            and request['before'][n]['path'] == str(home/n) for n in names),
        'ordinary_update_closed_budget_semantics_required')
    exact={'intent.json':SOURCE81_BUDGET_INTENT,'committed.json':SOURCE81_BUDGET_COMMITTED,
        **{'before/'+n:intent['before'][n]['sha256'] for n in names},
        **{'stage/'+n:committed['after'][n] for n in names},
        'stage/FRIDAY-PROFILE.json':request['retained']['FRIDAY-PROFILE.json']['sha256'],
        'stage/config.yaml.lock':f.digest(b''),'stage/profiles/dest_telegram/config.yaml.lock':f.digest(b'')}
    actual={}
    for path in tx.rglob('*'):
        f.require(not path.is_symlink(),'ordinary_update_history_link_refused')
        if path.is_dir(): f.directory(path)
        else: actual[str(path.relative_to(tx))]=f.digest(f.owned_file(path,private=True))
    f.require(actual == exact,'ordinary_update_budget_history_changed')
    return {str(tx.relative_to(home))+'/'+n:h for n,h in actual.items()}


def checked_source82_retained(home, request):
    """Retain the current admin-edited profile, never restore closed budget bytes."""
    f=api();refs=request['retained_profile_files']
    f.require(type(refs) is dict and set(refs) == WEB_INPUT_PROFILE_FILES
        and refs['profiles/dest_telegram/config.yaml']['sha256'] == WEB_INPUT_SELECTED_CONFIG,
        'ordinary_update_current_profile_pins_required')
    for name,ref in refs.items():
        f.require(f.pin(ref) == home/name,'ordinary_update_current_profile_changed')
    for name in ('previous_input','current_input','configuration','profile','launcher','native_unit'):
        f.pin(request[name])
    for name,ref in request['credential_files'].items():
        f.require(not os.path.lexists(home/name) if ref is None else f.pin(ref) == home/name,
            'ordinary_update_credential_pin_changed')


def checked_source81_retained(home, request, *, after=False):
    """Preserve all closed budget retained refs except this reviewed source delta."""
    f=api();budget_request=f.read_json(f.pin(request['inference_rebind']))
    retained=budget_request['retained']
    f.require(type(retained) is dict and len(retained) == SOURCE81_RETAINED_FILES,
        'ordinary_update_budget_retained_set_changed')
    allowed={'hermes-agent/'+n for n in FILE_TOOL_CONTRACT_FILES} | FILE_TOOL_CONTRACT_PLUGIN_FILES | {
        'hermes-agent.source.json','hermes-agent/install-stamp.json'}
    for name,ref in retained.items():
        f.require(ref['path'] == str(home/name),'ordinary_update_retained_path_changed')
        if not (after and name in allowed): f.pin(ref)
    tx=home/'preparation'/('ordinary-inference-rebind-'+budget_request['previous_input']['sha256'])
    for name,sha in f.read_json(tx/'committed.json')['after'].items():
        if not (after and name == f.MARKER): f.pin({'path':str(home/name),'sha256':sha})
    for name in ('previous_input','current_input','configuration','profile','launcher','native_unit'):
        f.pin(request[name])
    for name,ref in request['credential_files'].items():
        f.require(not os.path.lexists(home/name) if ref is None else f.pin(ref) == home/name,
            'ordinary_update_credential_pin_changed')


def checked_update_inference_history(home, reference, predecessor):
    """Retain one already committed helper/rebind edge; never replay either."""
    f = api()
    if predecessor.get('schema') == 'friday.ordinary-telegram-source-update.v34':
        return checked_source81_budget_history(home,reference,predecessor)
    f.require(type(reference) is dict and reference.get('sha256') == SOURCE80_REBIND_REQUEST
        and predecessor.get('schema') == PROJECT_INFERENCE_HELPER_SCHEMA,
        'ordinary_update_exact_inference_history_required')
    request = f.read_json(f.pin(reference))
    f.require(request.get('schema') == REBIND_SCHEMA and request.get('home') == str(home)
        and request.get('profile') == 'dest_telegram'
        and request.get('seconds') == 180
        and request['previous_input'] == predecessor['current_input']
        and request['current_input']['sha256'] == SPARK_REQUEST_BUDGET_PREVIOUS_INPUT,
        'ordinary_update_committed_inference_binding_required')
    f.pin(request['previous_input']); f.pin(request['current_input'])
    tx = f.directory(home/'preparation'/('ordinary-inference-rebind-'+request['previous_input']['sha256']))
    intent = f.read_json(tx/'intent.json'); committed = f.read_json(tx/'committed.json')
    names = {'.env','config.yaml',f.MARKER,'FRIDAY-PROFILE.json',
        'profiles/dest_telegram/.env','profiles/dest_telegram/config.yaml',
        'profiles/dest_telegram/.friday-onboarding.json','profiles/dest_telegram/.friday-user-scope.json'}
    f.require(intent.get('schema') == REBIND_SCHEMA and intent.get('state') == 'CONSUMED_NO_RETRY'
        and intent.get('request_sha256') == reference['sha256'] and intent.get('seconds') == 180
        and intent.get('previous_input') == request['previous_input']
        and intent.get('current_input') == request['current_input']
        and committed.get('state') == 'EXACT_INFERENCE_REBOUND_CONSUMERS_STOPPED_NOT_RUNTIME_ACCEPTED'
        and committed.get('ready') is False
        and all(body.get(field) is False for body in (intent,committed)
            for field in ('consumers_started','workers_enabled','database_changed'))
        and set(request['before']) == set(intent['before']) == set(committed['after']) == names
        and all(intent['before'][n] == {'sha256':request['before'][n]['sha256'],'mode':0o600}
            and request['before'][n]['path'] == str(home/n) for n in names),
        'ordinary_update_committed_inference_semantics_required')
    required = {'intent.json':SOURCE80_REBIND_INTENT,
        'committed.json':SOURCE80_REBIND_COMMITTED,
        **{'before/'+n:intent['before'][n]['sha256'] for n in names},
        **{'stage/'+n:committed['after'][n] for n in names},
        'stage/config.yaml.lock':f.digest(b''),
        'stage/profiles/dest_telegram/config.yaml.lock':f.digest(b'')}
    reconciliation = f.directory(home/PROJECT_INFERENCE_RECONCILIATION)
    for name,sha in PROJECT_INFERENCE_RECONCILIATION_PINS.items():
        f.pin({'path':str(home/name),'sha256':sha})
    archived = f.read_json(reconciliation/'intent.json')['tree']['files']
    exact = dict(PROJECT_INFERENCE_RECONCILIATION_PINS)
    for folder in ('failed-before','failed-qualification'):
        for name,row in archived.items():
            path = reconciliation/folder/name
            state = update_file_state(path)
            f.require(state is not None and f.digest(state['data']) == row['sha256']
                and len(state['data']) == row['bytes']
                and state['mode'] == (row['mode'] if folder == 'failed-qualification' else row['mode'] & 0o700)
                and (folder != 'failed-qualification' or list(state['identity']) == row['identity']),
                'ordinary_update_closed_archive_changed')
            exact[str(path.relative_to(home))] = row['sha256']
    exact.update({str(tx.relative_to(home))+'/'+n:h for n,h in required.items()})
    actual = {}
    for root in (reconciliation,tx):
        for path in root.rglob('*'):
            f.require(not path.is_symlink(), 'ordinary_update_history_link_refused')
            if path.is_dir(): f.directory(path)
            else:
                private = not path.is_relative_to(reconciliation/'failed-qualification')
                actual[str(path.relative_to(home))] = f.digest(f.owned_file(path,private=private))
    f.require(actual == exact, 'ordinary_update_inference_history_changed')
    return actual


def checked_manual_compression_archive(home, reference, predecessor, original_history):
    """Verify one consumed archive edge without replaying its old attempt."""
    f=api()
    f.require(type(reference) is dict and reference.get('sha256') == MANUAL_COMPRESSION_ARCHIVE_REQUEST,
        'ordinary_update_exact_worker_archive_required')
    archived=f.read_json(f.pin(reference)); previous=f.read_json(f.pin(predecessor))
    f.require(archived.get('schema') == 'friday.ordinary-closed-worker-reconciliation.v2'
        and archived.get('home') == str(home) and archived.get('profile') == 'dest_telegram'
        and archived.get('transition') == 'EXPLICIT_CLOSED_ARCHIVE_NO_RUNTIME_AUTHORITY'
        and archived.get('current_update') == predecessor
        and archived.get('installed_input') == previous['current_input']
        and archived['recovery_input']['sha256'] == MANUAL_COMPRESSION_PREVIOUS_INPUT,
        'ordinary_update_worker_archive_binding_changed')
    f.pin(archived['installed_input']); f.pin(archived['recovery_input'])
    f.require({str(f.canonical(r['path']).relative_to(home)):r['sha256'] for r in archived['history']} == original_history
        and len(archived['history']) == len(original_history), 'ordinary_update_worker_archive_history_changed')
    name='preparation/ordinary-closed-reconciliation-'+archived['recovery_id']
    tx=f.directory(home/name)
    intent=f.read_json(f.pin({'path':str(tx/'intent.json'),'sha256':MANUAL_COMPRESSION_ARCHIVE_INTENT}))
    committed=f.read_json(f.pin({'path':str(tx/'committed.json'),'sha256':MANUAL_COMPRESSION_ARCHIVE_COMMITTED}))
    mapping={str(home/'profiles/dest_telegram/workers/qualification'):str(tx/'failed-qualification')}
    f.require(intent.get('state') == 'CONSUMED_NO_RETRY'
        and intent.get('request_sha256') == reference['sha256']
        and committed.get('state') == 'ARCHIVED_CLOSED_FAILURE_WORKERS_OFF_NO_CONTINUATION_AUTHORITY'
        and intent.get('archive_mapping') == committed.get('archive_mapping') == mapping
        and intent.get('original_attempt') == committed.get('original_attempt')
        and intent.get('runtime_authority') == committed.get('runtime_authority') == 'NOT_GRANTED'
        and intent.get('old_attempt_retry_authorized') is False
        and all(committed.get(k) is False for k in ('ready','runtime_acceptance','consumers_started',
            'workers_enabled','resume_allowed','old_attempt_retry_authorized')),
        'ordinary_update_worker_archive_semantics_changed')
    expected={'intent.json':MANUAL_COMPRESSION_ARCHIVE_INTENT,
        'committed.json':MANUAL_COMPRESSION_ARCHIVE_COMMITTED,
        'before/'+f.MARKER:intent['before'][f.MARKER]['sha256']}
    for folder in ('failed-before','failed-qualification'):
        for relative,row in intent['tree']['files'].items():
            state=update_file_state(tx/folder/relative)
            f.require(state is not None and f.digest(state['data']) == row['sha256']
                and len(state['data']) == row['bytes'] and state['mode'] == row['mode']
                and (folder != 'failed-qualification' or list(state['identity']) == row['identity']),
                'ordinary_update_worker_archive_file_changed')
            expected[folder+'/'+relative]=row['sha256']
    archive=tx/'failed-qualification'; directories={}
    for path in [archive,*archive.rglob('*')]:
        f.require(not path.is_symlink(),'ordinary_update_history_link_refused')
        if path.is_dir():
            f.directory(path); info=path.lstat()
            directories[str(path.relative_to(archive))]=[getattr(info,k) for k in
                ('st_dev','st_ino','st_uid','st_mode')]
    f.require(directories == intent['tree']['directories'],
        'ordinary_update_worker_archive_directory_changed')
    actual={}
    for path in tx.rglob('*'):
        f.require(not path.is_symlink(),'ordinary_update_history_link_refused')
        if path.is_dir(): f.directory(path)
        else: actual[str(path.relative_to(tx))]=f.digest(f.owned_file(path,private=True))
    f.require(actual == expected, 'ordinary_update_worker_archive_inventory_changed')
    return {name+'/'+n:h for n,h in actual.items()}


def update_history(home, expected, predecessor=None, keyless_recovery=None, inference_rebind=None, worker_archive=None):
    """Pin the complete original activation transaction and rollback archive."""
    f = api(); actual = {}
    roots = [TRANSACTION, 'preparation/ordinary-gateway-archive']
    if predecessor is not None:
        # This is the already committed 46->47 transaction, never an operation
        # to rerun. Its exact request and all beforeimages remain pinned.
        old = f.read_json(f.pin(predecessor))
        if old.get('schema') in ('friday.ordinary-telegram-project-update.v1','friday.ordinary-telegram-project-update.v2','friday.ordinary-telegram-project-update.v3','friday.ordinary-telegram-source-update.v2','friday.ordinary-telegram-source-update.v3','friday.ordinary-telegram-source-update.v4','friday.ordinary-telegram-source-update.v5','friday.ordinary-telegram-source-update.v6','friday.ordinary-telegram-source-update.v7','friday.ordinary-telegram-source-update.v8','friday.ordinary-telegram-source-update.v9','friday.ordinary-telegram-source-update.v10','friday.ordinary-telegram-source-update.v11','friday.ordinary-telegram-source-update.v12','friday.ordinary-telegram-source-update.v13','friday.ordinary-telegram-source-update.v14','friday.ordinary-telegram-source-update.v15','friday.ordinary-telegram-source-update.v16','friday.ordinary-telegram-source-update.v17','friday.ordinary-telegram-source-update.v18','friday.ordinary-telegram-source-update.v19','friday.ordinary-telegram-source-update.v20','friday.ordinary-telegram-source-update.v21','friday.ordinary-telegram-source-update.v22','friday.ordinary-telegram-source-update.v23','friday.ordinary-telegram-source-update.v24','friday.ordinary-telegram-source-update.v25','friday.ordinary-telegram-source-update.v26','friday.ordinary-telegram-source-update.v27','friday.ordinary-telegram-source-update.v28','friday.ordinary-telegram-source-update.v29','friday.ordinary-telegram-source-update.v30','friday.ordinary-telegram-source-update.v31','friday.ordinary-telegram-source-update.v32','friday.ordinary-telegram-source-update.v33','friday.ordinary-telegram-source-update.v34','friday.ordinary-telegram-source-update.v35','friday.ordinary-telegram-source-update.v36','friday.ordinary-telegram-source-update.v37','friday.ordinary-telegram-source-update.v38','friday.ordinary-telegram-source-update.v39','friday.ordinary-telegram-source-update.v40','friday.ordinary-telegram-source-update.v41',BUNDLE_SCHEMA,EXACT_RESPONSE_SCHEMA,'friday.ordinary-telegram-project-update.v4',
            'friday.ordinary-telegram-source-update.v44'):
            # Every exact historical committed update journal survives this transition.
            actual = update_history(home, old['transaction_history'], old['predecessor_update'], old.get('keyless_recovery'), old.get('inference_rebind'), old.get('worker_archive'))
            roots = []
        f.require(old.get('schema') in ('friday.ordinary-telegram-project-update.v1','friday.ordinary-telegram-project-update.v2','friday.ordinary-telegram-project-update.v3','friday.ordinary-telegram-source-update.v1',
            'friday.ordinary-telegram-source-update.v2','friday.ordinary-telegram-source-update.v3','friday.ordinary-telegram-source-update.v4','friday.ordinary-telegram-source-update.v5','friday.ordinary-telegram-source-update.v6','friday.ordinary-telegram-source-update.v7','friday.ordinary-telegram-source-update.v8','friday.ordinary-telegram-source-update.v9','friday.ordinary-telegram-source-update.v10','friday.ordinary-telegram-source-update.v11','friday.ordinary-telegram-source-update.v12','friday.ordinary-telegram-source-update.v13','friday.ordinary-telegram-source-update.v14','friday.ordinary-telegram-source-update.v15','friday.ordinary-telegram-source-update.v16','friday.ordinary-telegram-source-update.v17','friday.ordinary-telegram-source-update.v18','friday.ordinary-telegram-source-update.v19','friday.ordinary-telegram-source-update.v20','friday.ordinary-telegram-source-update.v21','friday.ordinary-telegram-source-update.v22','friday.ordinary-telegram-source-update.v23','friday.ordinary-telegram-source-update.v24','friday.ordinary-telegram-source-update.v25','friday.ordinary-telegram-source-update.v26','friday.ordinary-telegram-source-update.v27','friday.ordinary-telegram-source-update.v28','friday.ordinary-telegram-source-update.v29','friday.ordinary-telegram-source-update.v30','friday.ordinary-telegram-source-update.v31','friday.ordinary-telegram-source-update.v32','friday.ordinary-telegram-source-update.v33','friday.ordinary-telegram-source-update.v34','friday.ordinary-telegram-source-update.v35','friday.ordinary-telegram-source-update.v36','friday.ordinary-telegram-source-update.v37','friday.ordinary-telegram-source-update.v38','friday.ordinary-telegram-source-update.v39','friday.ordinary-telegram-source-update.v40','friday.ordinary-telegram-source-update.v41',BUNDLE_SCHEMA,EXACT_RESPONSE_SCHEMA,'friday.ordinary-telegram-project-update.v4',
            'friday.ordinary-telegram-source-update.v44'),
            'ordinary_update_exact_predecessor_required')
        f.pin(old['previous_input']); f.pin(old['current_input'])
        name = 'preparation/ordinary-source-update-'+old['previous_input']['sha256']
        tx = f.directory(home/name)
        intent = f.read_json(tx/'intent.json'); committed = f.read_json(tx/'committed.json')
        f.require(intent.get('schema') == 'friday.ordinary-telegram-source-update-transaction.v1'
            and intent.get('state') == 'SOURCE_UPDATE_CONSUMED_NO_RETRY'
            and intent.get('request_sha256') == predecessor['sha256']
            and committed.get('state') == 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
            and committed.get('previous_input') == old['previous_input']
            and committed.get('current_input') == old['current_input']
            and committed.get('gateway_started') is False and committed.get('workers_enabled') is False
            and not os.path.lexists(tx/'rolled-back.json'), 'ordinary_update_committed_predecessor_required')
        roots.append(name)
    for name in roots:
        root = f.directory(home/name)
        for path in root.rglob('*'):
            f.require(not path.is_symlink(), 'ordinary_update_history_link_refused')
            if path.is_dir():
                f.directory(path)
            else:
                actual[str(path.relative_to(home))] = f.digest(f.owned_file(path,private=True))
    if keyless_recovery is not None:
        name = checked_update_keyless_history(home, keyless_recovery, old, actual)
        for path in f.directory(home/name).rglob('*'):
            f.require(not path.is_symlink(), 'ordinary_update_history_link_refused')
            if path.is_dir(): f.directory(path)
            else: actual[str(path.relative_to(home))] = f.digest(f.owned_file(path,private=True))
    if inference_rebind is not None:
        actual.update(checked_update_inference_history(home,inference_rebind,old))
    if worker_archive is not None:
        actual.update(checked_manual_compression_archive(home,worker_archive,predecessor,actual))
    f.require(type(expected) is dict and actual == expected
        and TRANSACTION+'/committed.json' in actual, 'ordinary_update_transaction_history_changed')
    f.require(f.read_json(home/TRANSACTION/'committed.json').get('state') ==
        'SOURCE_ACTIVATED_NOT_RUNTIME_ACCEPTED', 'ordinary_update_committed_history_required')
    return actual


def checked_plugin_inventory(home, expected):
    """The installed private package, including all unchanged source files."""
    f = api(); actual = set(); root = f.directory(home/'plugins/friday_rework')
    for path in root.rglob('*'):
        f.require(not path.is_symlink(), 'ordinary_update_plugin_link_refused')
        if path.is_dir():
            f.directory(path)
        else:
            name = str(path.relative_to(home)); actual.add(name)
            f.require(name in expected and f.digest(f.owned_file(path,private=True)) == expected[name],
                'ordinary_update_installed_plugin_changed')
    f.require(actual == set(expected), 'ordinary_update_plugin_inventory_changed')


def check_browser_gateway(home, source, manifest, budget, *, staged):
    """Use only the pinned v10 afterimage for the complete ordinary check.

    Existing installed bytes are verified separately against the old receipt.
    This repairs the old checker predicate without weakening any binding check.
    """
    import tempfile
    import types
    f = api(); row, = manifest['files']; relative = row['path']
    f.require(relative == 'hermes_cli/friday_ordinary_gateway.py'
        and row.get('new_file') is False, 'ordinary_update_exact_browser_gateway_required')
    if staged:
        from scripts.dsh_prepare import run
        # No installed path changes before the consumed transaction journal.
        with tempfile.TemporaryDirectory(prefix='.ordinary-browser-gateway-',dir=home/'preparation') as name:
            root = Path(name); private_parents(root,relative)
            before = f.owned_file(source/relative)
            f.require(f.digest(before) == row['before_sha256'], 'ordinary_update_source_changed')
            write(root/relative,before,0o644)
            env = f.clean_environment(home); env['GIT_CEILING_DIRECTORIES'] = str(home)
            for checking in (True,False):
                command = ['git','--no-optional-locks','apply','--whitespace=nowarn']
                if checking: command.append('--check')
                command.append(str(f.ROOT/manifest['patch']))
                run(command,root,timeout=min(20,budget.check(reserve=1)),env=env,deadline=budget.deadline)
            data = f.owned_file(root/relative)
    else:
        data = f.owned_file(source/relative)
    f.require(f.digest(data) == row['sha256'] and len(data) == row['bytes'],
        'ordinary_update_browser_gateway_afterimage_changed')
    module = types.ModuleType('_friday_reviewed_browser_gateway')
    module.__file__ = str(source/relative)
    exec(compile(data,module.__file__,'exec'),module.__dict__)
    return module.check(home,role=False)


def checked_worker_declaration_publication(home, request, predecessor, marker):
    """Bridge v10 only through the exact already-consumed worker publication.

    Source updates do not rerun preparation or admit a generic input mismatch.
    The successful pinned journal binds the unchanged Native56 source, original
    request clock, both input generations and the installed marker beforeimage.
    """
    import copy
    import re
    f = api(); proof = request['worker_declaration_publication']
    f.require(type(proof) is dict and set(proof) == {'request','result'},
        'ordinary_update_worker_publication_pins_required')
    prepared = f.read_json(f.pin(proof['request']))
    result_path = f.pin(proof['result']); result = f.read_json(result_path)
    request_id = prepared.get('request_id')
    f.require(prepared.get('schema') == 'friday.ordinary-worker-preparation.v1'
        and isinstance(request_id,str) and re.fullmatch('[A-Za-z0-9_-]{1,64}',request_id)
        and prepared.get('home') == str(home)
        and prepared.get('current_input') == predecessor['current_input']
        and prepared.get('preparation_input') == request['previous_input']
        and prepared.get('source_receipt') == request['source_receipt']
        and prepared.get('profile') == request['profile']
        and prepared.get('native_unit') == request['native_unit'],
        'ordinary_update_worker_publication_binding_changed')
    tx = f.directory(home/'preparation'/('ordinary-workers-'+request_id))
    f.require(result_path == tx/'result.json' and not os.path.lexists(tx/'failure.json'),
        'ordinary_update_successful_worker_publication_required')
    intent = f.read_json(tx/'intent.json')
    f.require(result.get('state') == 'BOTH_WORKER_DECLARATIONS_PUBLISHED_QUALIFICATION_PENDING'
        and result.get('ready') is False and result.get('runtime_enabled') is False
        and result.get('runtime_acceptance') == 'NOT_GRANTED'
        and result.get('original_attempt') == intent
        and intent.get('request_id') == request_id
        and intent.get('request_sha256') == proof['request']['sha256']
        and intent.get('seconds') == prepared.get('seconds')
        and intent.get('resume_allowed') is False
        and type(intent.get('started_mono')) in (int,float)
        and type(intent.get('deadline_mono')) in (int,float)
        and abs(intent['deadline_mono']-intent['started_mono']-intent['seconds']) < 0.001
        and result.get('reports') == prepared.get('reports')
        and type(result.get('reports')) is dict
        and set(result['reports']) == {'source','toolchain','build','smoke','inventory','a0'},
        'ordinary_update_consumed_worker_publication_required')
    for ref in [*result['reports'].values(),*prepared['history']]: f.pin(ref)
    before_path = tx/('before-'+f.MARKER)
    before = f.read_json(before_path)
    f.require(f.digest(f.owned_file(before_path,private=True)) == prepared['marker']['sha256']
        and prepared['marker']['path'] == str(home/f.MARKER)
        and prepared['configuration']['path'] == str(home/'config.yaml')
        and f.digest(f.owned_file(tx/'before-config.yaml',private=True)) == prepared['configuration']['sha256']
        and before.get('input_sha256') == predecessor['current_input']['sha256']
        and before.get('source_receipt_sha256') == request['source_receipt']['sha256']
        and before.get('ordinary_gateway',{}).get('operator_entry',{}).get('input') == predecessor['current_input']
        and marker['ordinary_gateway']['operator_entry']['input'] == request['previous_input']
        and marker['profile_files']['config.yaml'] == result.get('configuration_sha256'),
        'ordinary_update_worker_beforeimage_changed')
    old = f.read_json(f.pin(prepared['current_input']))
    new = f.read_json(f.pin(prepared['preparation_input']))
    # The previous preparer admitted only its coherent installer package and
    # refreshed egress evidence. No operational setting is widened here.
    allowed = {'scripts/friday_install.py','scripts/friday_ordinary_install.py',
        'scripts/worker_install.py','scripts/friday_worker_preparation.py',
        'scripts/a0_prepare.py','scripts/friday_ordinary_a0_registration.py'}
    prior = old['project_files']; fresh = new['project_files']
    f.require(len(prior) == 178 and len(fresh) == 180
        and set(fresh) == set(prior) | {'scripts/friday_worker_preparation.py','scripts/friday_ordinary_a0_registration.py'}
        and all(fresh[name] == pin for name,pin in prior.items() if name not in allowed),
        'ordinary_update_worker_source_changed')
    left = copy.deepcopy(old); right = copy.deepcopy(new)
    for value in (left,right):
        value.pop('project_files')
        value['worker_install']['dsh']['web'].pop('egress_evidence')
    f.require(left == right and new['product']['runtime'] == {'enabled':False},
        'ordinary_update_worker_settings_changed')
    entry = marker['ordinary_gateway']['operator_entry']
    f.pin(entry['script'])
    f.require(entry['script']['sha256'] == fresh['scripts/friday_native.py'],
        'ordinary_update_worker_operator_changed')
    expected = copy.deepcopy(before)
    expected['input_sha256'] = marker['input_sha256']
    expected['profile_files']['config.yaml'] = marker['profile_files']['config.yaml']
    for field in ('operator_entry','configuration_sha256'):
        expected['ordinary_gateway'][field] = marker['ordinary_gateway'][field]
    f.require(expected == marker, 'ordinary_update_worker_marker_changed')


def bundle_pins_checked():
    """Closed reviewed tuple, never a request-supplied scope or permission list."""
    import re
    f = api()
    sha = lambda value: type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None
    f.require(all(sha(value) for value in (BUNDLE_PREVIOUS_INPUT,
        BUNDLE_PREDECESSOR_REQUEST,BUNDLE_PREDECESSOR_COMMITTED))
        and type(BUNDLE_HISTORY_FILES) is int and BUNDLE_HISTORY_FILES > 0
        and type(BUNDLE_PROJECT_BEFORE) is dict and set(BUNDLE_PROJECT_BEFORE) == BUNDLE_PROJECT_FILES
        and type(BUNDLE_PROJECT_AFTER) is dict and set(BUNDLE_PROJECT_AFTER) == BUNDLE_PROJECT_FILES-{'scripts/friday_ordinary_install.py'}
        and all(sha(value) for value in (*BUNDLE_PROJECT_BEFORE.values(),*BUNDLE_PROJECT_AFTER.values()))
        and all(BUNDLE_PROJECT_BEFORE[name] != BUNDLE_PROJECT_AFTER[name] for name in BUNDLE_PLUGIN_FILES)
        and type(BUNDLE_LAYER_PINS) is tuple and len(BUNDLE_LAYER_PINS) == 2
        and type(BUNDLE_NEW_DIRECTORIES) is set and bool(BUNDLE_NEW_DIRECTORIES),
        'ordinary_update_final_bundle_pins_required')
    seen = set()
    for pin,counts in zip(BUNDLE_LAYER_PINS,((19,14),(3,1))):
        f.require(type(pin) is dict and set(pin) == {'manifest_sha256','patch_sha256','files','new_files'}
            and sha(pin['manifest_sha256']) and sha(pin['patch_sha256'])
            and type(pin['files']) is set and len(pin['files']) == counts[0]
            and type(pin['new_files']) is set and len(pin['new_files']) == counts[1]
            and pin['new_files'] < pin['files'] and not seen & pin['files'],
            'ordinary_update_final_bundle_layer_pins_required')
        for name in pin['files']:
            f.require(type(name) is str and not Path(name).is_absolute() and name == Path(name).as_posix()
                and not any(part in ('.','..') for part in Path(name).parts),
                'ordinary_update_bundle_relative_path_required')
        seen.update(pin['files'])


def bundle_layer_prefix_checked(layers, installed):
    """Accept exact order, or only the proven genuine Source86 CLI commutation.

    Both entire ordered85-element triples are fixed by digest. The specific
    index32->2 move is additionally checked, together with disjoint target files
    and no prerequisite crossing. No generic mapping or arbitrary-order path.
    Installed receipt order is retained verbatim by the transaction.
    """
    f = api(); keys = ('manifest','manifest_sha256','patch_sha256')
    canonical = [{key:row[1][key] for key in keys} for row in layers]
    if canonical == installed: return
    f.require(len(installed) == len(canonical) == 85
        and f.digest(encoded(installed)) == BUNDLE_SOURCE86_INSTALLED_PREFIX_SHA256
        and f.digest(encoded(canonical)) == BUNDLE_SOURCE86_CANONICAL_PREFIX_SHA256
        and canonical == installed[:2]+[installed[32]]+installed[2:32]+installed[33:]
        and installed[32] == {
            'manifest':'patches/hermes/cli-launcher-no-bytecode-manifest.json',
            'manifest_sha256':'4addb7050d7bb2753e5ad89d3c625689df5cf623d8dc3ddd94111acc4cc665bd',
            'patch_sha256':'4058d53f1fc673428fa5f33b8570547bb1fbdb4f4284138477dd0a51b52a7a51'},
        'ordinary_update_exact_bundle_layer_order_required')
    patch, moved = layers[2]; target = 'hermes_cli/_launchers.py'
    f.require(patch == 'patches/hermes/cli-launcher-no-bytecode.patch'
        and moved['requires'] == {} and set(moved['files']) == {target}
        and moved['files'][target] == {
            'path':target,'before_sha256':'968dbe9c893c36d82efd22edce5cf59662b2af5675177524254ae6b61983bef8',
            'sha256':'3e43487a5a27babb45db219783021285b594e789edaf6359389962d0e67533c0',
            'bytes':34670,'mode':'100644','new_file':False}
        and all(target not in row['files'] and patch not in row['requires']
            for _,row in layers[3:33]),
        'ordinary_update_exact_cli_order_compatibility_required')


def bundle_manifests_checked(home,source,previous,current,receipt,budget):
    """Bind two disjoint ordered layers to the private historical receipt prefix."""
    f = api(); old = previous['project_files']; new = current['project_files']
    expected_after = {**BUNDLE_PROJECT_AFTER,
        'scripts/friday_ordinary_install.py':f.digest(f.owned_file(Path(__file__)))}
    changed = {name for name in BUNDLE_PROJECT_FILES if BUNDLE_PROJECT_BEFORE[name] != expected_after[name]}
    f.require(len(old) == 243 and len(new) == 247
        and set(new) == set(old) | set(BUNDLE_MANIFESTS) | set(BUNDLE_PATCHES)
        and set(BUNDLE_PROJECT_FILES) <= set(old)
        and all(old[name] == pin for name,pin in BUNDLE_PROJECT_BEFORE.items())
        and all(new[name] == pin for name,pin in expected_after.items())
        and {name for name in old if old[name] != new[name]} == changed
        and {'scripts/friday_ordinary_install.py'} | BUNDLE_PLUGIN_FILES <= changed,
        'ordinary_update_exact_bundle_project_delta_required')
    f.require(len(receipt['layers']) == 85 and len(receipt['files']) == BUNDLE_NATIVE_FILES
        and receipt['layers'][-1]['manifest'] == MANUAL_COMPRESSION_MANIFEST,
        'ordinary_update_exact_bundle_source86_required')
    prefix = {row['manifest']:row['manifest_sha256'] for row in receipt['layers']}
    rows = []; manifests = []
    for name,patch,pin in zip(BUNDLE_MANIFESTS,BUNDLE_PATCHES,BUNDLE_LAYER_PINS):
        raw = f.owned_file(f.ROOT/name); manifest = json.loads(raw,object_pairs_hook=f.unique)
        f.require(name not in prefix and new[name] == pin['manifest_sha256'] == f.digest(raw)
            and manifest.get('base_commit') == receipt['commit'] and manifest.get('installed_prefix') == prefix
            and manifest.get('patch') == patch
            and manifest.get('patch_sha256') == new[patch] == pin['patch_sha256'] == f.digest(f.owned_file(f.ROOT/patch)),
            'ordinary_update_exact_bundle_prefix_required')
        native = manifest.get('files')
        f.require(type(native) is list and len(native) == len(pin['files'])
            and {row['path'] for row in native} == pin['files'],
            'ordinary_update_exact_bundle_native_files_required')
        for row in native:
            f.require(row.get('mode') == '100644', 'ordinary_update_bundle_mode_required')
            if row['path'] in pin['new_files']:
                f.require(row.get('new_file') is True and row.get('before_sha256') is None
                    and row['path'] not in receipt['files'] and not os.path.lexists(source/row['path']),
                    'ordinary_update_new_source_exists')
            else:
                f.require(row.get('new_file') is False
                    and row['before_sha256'] == receipt['files'][row['path']]['sha256']
                    and row['before_sha256'] == f.digest(f.owned_file(source/row['path'])),
                    'ordinary_update_source_changed')
        rows.extend(native); manifests.append((name,manifest)); prefix[name] = pin['manifest_sha256']
    with SourceUpdateDirectories(home,['hermes-agent/'+row['path'] for row in rows],
            {'hermes-agent/'+name for name in BUNDLE_NEW_DIRECTORIES}) as directories:
        directories.prove()
    from scripts.hermes_prepare import overlay_layers, Budget as SourceBudget
    layers = budget.call(overlay_layers,f.ROOT,receipt['commit'],SourceBudget(budget.deadline))
    f.require([row[1]['manifest'] for row in layers[-2:]] == list(BUNDLE_MANIFESTS)
        and len(layers) == 87, 'ordinary_update_exact_bundle_layer_order_required')
    bundle_layer_prefix_checked(layers[:-2],receipt['layers'])
    return {'files':rows,'bundle_layers':manifests}


def exact_response_pins_checked():
    import re
    f=api()
    f.require(all(type(pin) is str and re.fullmatch('[0-9a-f]{64}',pin) for pin in (
        EXACT_RESPONSE_MANIFEST_SHA256,EXACT_RESPONSE_PATCH_SHA256,
        EXACT_RESPONSE_PREVIOUS_INPUT,EXACT_RESPONSE_PREDECESSOR_REQUEST,
        EXACT_RESPONSE_PREDECESSOR_COMMITTED,EXACT_RESPONSE_PREVIOUS_UPDATER))
        and EXACT_RESPONSE_FILES == {'agent/onboarding.py','hermes_cli/friday_prompt_scope.py'},
        'ordinary_update_final_exact_response_pins_required')


def source88_retained_inventory(home,budget):
    """Fixed retained namespaces under private H; metadata only until pin checks.

    Native profile/runtime tools create owned0755/0775 subdirectories. Their
    exact current modes and identities are captured by Root and rechecked; no
    chmod or broader namespace is admitted. Symlinks/world writes refuse.
    """
    f=api();f.directory(home);names=set();directories={};total_bytes=0
    def directory(path):
        budget.check();f.canonical(str(path));info=path.lstat()
        f.require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) in (0o700,0o755,0o775),
            'ordinary_update_retained_directory_required')
        directories[str(path.relative_to(home))]={'path':str(path),
            'mode':stat.S_IMODE(info.st_mode),
            'identity':[getattr(info,key) for key in ('st_dev','st_ino','st_uid','st_gid')]}
        f.require(len(directories)+len(names) <= EXACT_RESPONSE_RETAINED_MAX_FILES,
            'ordinary_update_retained_resource_limit')
    def retain(path,info):
        nonlocal total_bytes
        budget.check()
        f.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid(),
            'ordinary_update_retained_regular_required')
        names.add(str(path.relative_to(home)));total_bytes += info.st_size
        f.require(len(names)+len(directories) <= EXACT_RESPONSE_RETAINED_MAX_FILES
            and total_bytes <= EXACT_RESPONSE_RETAINED_MAX_BYTES,
            'ordinary_update_retained_resource_limit')
    directory(home)
    for name in EXACT_RESPONSE_RETAINED_TREES:
        budget.check();root=home/name
        if not os.path.lexists(root):continue
        directory(root)
        for path in root.rglob('*'):
            budget.check()
            f.require(not path.is_symlink(),'ordinary_update_retained_link_refused')
            if path.is_dir():directory(path)
            else:retain(path,path.lstat())
    for name in EXACT_RESPONSE_RETAINED_ROOT_FILES | EXACT_RESPONSE_BINDING_FILES:
        budget.check()
        if os.path.lexists(home/name):retain(home/name,(home/name).lstat())
    # Native Telegram receipts use one root leaf per account. Discover this
    # fixed namespace without embedding a deployment's account identifier.
    # Every found leaf is retained opaquely and the complete set is rechecked.
    for path in home.glob('telegram_update_receipts_*.json'):
        budget.check();retain(path,path.lstat())
    f.require(EXACT_RESPONSE_BINDING_FILES <= names,
        'ordinary_update_current_renderer_binding_required')
    return names,directories


def source88_retained_paths(home,budget):
    """Compatibility helper; Root also captures the returned directory refs."""
    return source88_retained_inventory(home,budget)[0]


def checked_source88_retained(home,request,budget):
    """Fresh opaque byte/mode pins; old pre-bot data never serves as current."""
    f=api();refs=request['retained_data_files']
    names,directories=source88_retained_inventory(home,budget)
    f.require(type(request.get('retained_data_directories')) is dict
        and request['retained_data_directories'] == directories,
        'ordinary_update_current_directory_inventory_changed')
    f.require(type(refs) is dict and set(refs) == names,
        'ordinary_update_current_data_inventory_changed')
    for name,ref in refs.items():
        budget.check()
        f.require(type(ref) is dict and set(ref) == {'path','sha256','mode'}
            and ref['path'] == str(home/name) and type(ref['mode']) is int
            and stat.S_IMODE((home/name).lstat().st_mode) == ref['mode']
            and (name not in EXACT_RESPONSE_BINDING_FILES or ref['mode'] == 0o600),
            'ordinary_update_current_data_metadata_changed')
        f.require(budget.call(f.pin,{key:ref[key] for key in ('path','sha256')}) == home/name,
            'ordinary_update_current_data_changed')
    checked_source82_retained(home,request)


def exact_response_manifest_checked(home,source,previous,current,receipt,budget):
    """One reviewed layer appended to genuine87, preserving installed order."""
    f=api();old=previous['project_files'];new=current['project_files']
    updater='scripts/friday_ordinary_install.py'
    f.require(len(old) == 247 and len(new) == 249
        and set(new) == set(old) | {EXACT_RESPONSE_MANIFEST,EXACT_RESPONSE_PATCH}
        and old[updater] == EXACT_RESPONSE_PREVIOUS_UPDATER
        and new[updater] == f.digest(f.owned_file(Path(__file__)))
        and old[updater] != new[updater]
        and all(new[name] == value for name,value in old.items() if name != updater),
        'ordinary_update_exact_response_project_delta_required')
    f.require(len(receipt['layers']) == 87 and len(receipt['files']) == EXACT_RESPONSE_NATIVE_FILES
        and [row['manifest'] for row in receipt['layers'][-2:]] == list(BUNDLE_MANIFESTS)
        and all(receipt['layers'][index-2]['manifest_sha256'] == pin['manifest_sha256']
            and receipt['layers'][index-2]['patch_sha256'] == pin['patch_sha256']
            for index,pin in enumerate(BUNDLE_LAYER_PINS)),
        'ordinary_update_exact_response_source87_required')
    raw=f.owned_file(f.ROOT/EXACT_RESPONSE_MANIFEST)
    manifest=json.loads(raw,object_pairs_hook=f.unique)
    f.require(new[EXACT_RESPONSE_MANIFEST] == EXACT_RESPONSE_MANIFEST_SHA256 == f.digest(raw)
        and manifest.get('patch') == EXACT_RESPONSE_PATCH
        and manifest.get('patch_sha256') == new[EXACT_RESPONSE_PATCH] == EXACT_RESPONSE_PATCH_SHA256
        and EXACT_RESPONSE_PATCH_SHA256 == f.digest(f.owned_file(f.ROOT/EXACT_RESPONSE_PATCH))
        and manifest.get('base_commit') == receipt['commit']
        and manifest.get('installed_prefix') == {row['manifest']:row['manifest_sha256'] for row in receipt['layers']},
        'ordinary_update_exact_response_prefix_required')
    rows=manifest.get('files')
    f.require(type(rows) is list and len(rows) == 2
        and {row['path'] for row in rows} == EXACT_RESPONSE_FILES,
        'ordinary_update_exact_response_files_required')
    for row in rows:
        f.require(row.get('new_file') is False and row.get('mode') == '100644'
            and row.get('before_sha256') == receipt['files'][row['path']]['sha256']
            and row['before_sha256'] == f.digest(f.owned_file(source/row['path'])),
            'ordinary_update_source_changed')
    from scripts.hermes_prepare import overlay_layers,Budget as SourceBudget
    layers=budget.call(overlay_layers,f.ROOT,receipt['commit'],SourceBudget(budget.deadline))
    f.require(len(layers) == 88 and layers[-1][1]['manifest'] == EXACT_RESPONSE_MANIFEST
        and [{key:body[key] for key in ('manifest','manifest_sha256','patch_sha256')}
            for _,body in layers[-3:-1]] == receipt['layers'][-2:],
        'ordinary_update_exact_response_layer_order_required')
    bundle_layer_prefix_checked(layers[:-3],receipt['layers'][:-2])
    with SourceUpdateDirectories(home,['hermes-agent/'+row['path'] for row in rows],set()) as directories:
        directories.prove()
    return {'files':rows,'bundle_layers':[(EXACT_RESPONSE_MANIFEST,manifest)]}


def update_inputs(request, budget):
    f = api()
    fields = {'schema','seconds','home','previous_input','current_input','marker','source_receipt',
        'stamp','configuration','profile','launcher','credential_files','native_unit','transaction_history'}
    exact_response = type(request) is dict and request.get('schema') == EXACT_RESPONSE_SCHEMA
    source88 = type(request) is dict and request.get('schema') == BUNDLE_SCHEMA
    source87 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v41'
    source86 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v40'
    source85 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v39'
    source84 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v38'
    source83 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v37'
    source82 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v36'
    source81 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v35'
    source80 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v34'
    source79 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v33'
    source78 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v32'
    source77 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v31'
    source76 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v30'
    source75 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v29'
    source74 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v28'
    source73 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v27'
    source72 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v26'
    source71 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v25'
    source70 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v24'
    source69 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v23'
    source68 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v22'
    source67 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v21'
    source66 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v20'
    source65 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v19'
    source64 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v18'
    source63 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v17'
    source62 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v16'
    source61 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v15'
    source60 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v14'
    source59 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v13'
    source58 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v12'
    source57 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v11'
    source56 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v10'
    source55 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v9'
    source54 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v8'
    source53 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v7'
    source52 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v6'
    source51 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v5'
    source50 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v4'
    source49 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v3'
    source48 = type(request) is dict and request.get('schema') == 'friday.ordinary-telegram-source-update.v2'
    f.require(type(request) is dict and set(request) == fields | ({'predecessor_update'} if source48 or source49 or source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response else set()) | ({'worker_declaration_publication'} if source57 else set()) | ({'keyless_recovery'} if source78 else set()) | ({'inference_rebind'} if source80 or source81 else set()) | ({'worker_archive'} if source86 else set()) | ({'retained_data_files','retained_data_directories'} if exact_response else set()) | ({'retained_profile_files'} if source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response else set())
        and request['schema'] in ('friday.ordinary-telegram-source-update.v1','friday.ordinary-telegram-source-update.v2','friday.ordinary-telegram-source-update.v3','friday.ordinary-telegram-source-update.v4','friday.ordinary-telegram-source-update.v5','friday.ordinary-telegram-source-update.v6','friday.ordinary-telegram-source-update.v7','friday.ordinary-telegram-source-update.v8','friday.ordinary-telegram-source-update.v9','friday.ordinary-telegram-source-update.v10','friday.ordinary-telegram-source-update.v11','friday.ordinary-telegram-source-update.v12','friday.ordinary-telegram-source-update.v13','friday.ordinary-telegram-source-update.v14','friday.ordinary-telegram-source-update.v15','friday.ordinary-telegram-source-update.v16','friday.ordinary-telegram-source-update.v17','friday.ordinary-telegram-source-update.v18','friday.ordinary-telegram-source-update.v19','friday.ordinary-telegram-source-update.v20','friday.ordinary-telegram-source-update.v21','friday.ordinary-telegram-source-update.v22','friday.ordinary-telegram-source-update.v23','friday.ordinary-telegram-source-update.v24','friday.ordinary-telegram-source-update.v25','friday.ordinary-telegram-source-update.v26','friday.ordinary-telegram-source-update.v27','friday.ordinary-telegram-source-update.v28','friday.ordinary-telegram-source-update.v29','friday.ordinary-telegram-source-update.v30','friday.ordinary-telegram-source-update.v31','friday.ordinary-telegram-source-update.v32','friday.ordinary-telegram-source-update.v33','friday.ordinary-telegram-source-update.v34','friday.ordinary-telegram-source-update.v35','friday.ordinary-telegram-source-update.v36','friday.ordinary-telegram-source-update.v37','friday.ordinary-telegram-source-update.v38','friday.ordinary-telegram-source-update.v39','friday.ordinary-telegram-source-update.v40','friday.ordinary-telegram-source-update.v41',BUNDLE_SCHEMA,EXACT_RESPONSE_SCHEMA)
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 180,
        'ordinary_update_explicit_request_required')
    if exact_response: exact_response_pins_checked()
    if source88: bundle_pins_checked()
    if source87:
        import re
        f.require(all(type(pin) is str and re.fullmatch('[0-9a-f]{64}',pin) for pin in (
            PROTECTED_COMPRESSOR_MANIFEST_SHA256, PROTECTED_COMPRESSOR_PATCH_SHA256,
            PROTECTED_COMPRESSOR_PREVIOUS_INPUT, PROTECTED_COMPRESSOR_PREDECESSOR_REQUEST,
            PROTECTED_COMPRESSOR_PREDECESSOR_COMMITTED, PROTECTED_COMPRESSOR_PREVIOUS_UPDATER))
            and type(PROTECTED_COMPRESSOR_FILES) is set and bool(PROTECTED_COMPRESSOR_FILES)
            and type(PROTECTED_COMPRESSOR_NEW_FILES) is set and bool(PROTECTED_COMPRESSOR_NEW_FILES)
            and PROTECTED_COMPRESSOR_NEW_FILES < PROTECTED_COMPRESSOR_FILES
            and type(PROTECTED_COMPRESSOR_NEW_DIRECTORIES) is set and bool(PROTECTED_COMPRESSOR_NEW_DIRECTORIES)
            and type(PROTECTED_COMPRESSOR_HISTORY_FILES) is int and PROTECTED_COMPRESSOR_HISTORY_FILES > 0,
            'ordinary_update_final_protected_compressor_pins_required')
    if source86:
        f.require(MANUAL_COMPRESSION_MANIFEST_SHA256 is not None
            and MANUAL_COMPRESSION_PATCH_SHA256 is not None
            and type(MANUAL_COMPRESSION_FILES) is set and bool(MANUAL_COMPRESSION_FILES),
            'ordinary_update_final_manual_compression_pins_required')
    if source85:
        f.require(WEB_RUNTIME_HISTORY_MANIFEST_SHA256 is not None
            and WEB_RUNTIME_HISTORY_PATCH_SHA256 is not None
            and type(WEB_RUNTIME_HISTORY_FILES) is set and bool(WEB_RUNTIME_HISTORY_FILES),
            'ordinary_update_final_web_runtime_history_pins_required')
    if source84:
        f.require(FILE_REPLY_CONTEXT_MANIFEST_SHA256 is not None
            and FILE_REPLY_CONTEXT_PATCH_SHA256 is not None
            and type(FILE_REPLY_CONTEXT_FILES) is set and bool(FILE_REPLY_CONTEXT_FILES),
            'ordinary_update_final_file_reply_context_pins_required')
    if source83:
        f.require(COMBINED_INPUT_MANIFEST_SHA256 is not None and COMBINED_INPUT_PATCH_SHA256 is not None,
            'ordinary_update_final_combined_input_pins_required')
    if source82:
        f.require(WEB_INPUT_MANIFEST_SHA256 is not None and WEB_INPUT_PATCH_SHA256 is not None,
            'ordinary_update_final_web_input_pins_required')
    if source81:
        f.require(FILE_TOOL_CONTRACT_MANIFEST_SHA256 is not None
            and FILE_TOOL_CONTRACT_PATCH_SHA256 is not None,
            'ordinary_update_final_file_tool_pins_required')
    if source80:
        f.require(SPARK_REQUEST_BUDGET_MANIFEST_SHA256 is not None
            and SPARK_REQUEST_BUDGET_PATCH_SHA256 is not None
            and type(SPARK_REQUEST_BUDGET_FILES) is set and bool(SPARK_REQUEST_BUDGET_FILES)
            and type(SPARK_REQUEST_BUDGET_NEW_FILES) is set
            and SPARK_REQUEST_BUDGET_NEW_FILES <= SPARK_REQUEST_BUDGET_FILES,
            'ordinary_update_final_request_budget_pins_required')
    home = f.directory(f.canonical(request['home'])); source = f.directory(home/'hermes-agent')
    f.require(os.environ.get('HERMES_HOME') == str(home), 'ordinary_update_exact_environment_required')
    paths = {name:budget.call(f.pin,request[name]) for name in
        ('previous_input','current_input','marker','source_receipt','stamp','configuration','profile','launcher','native_unit')}
    for name, path in {'marker':home/f.MARKER,'source_receipt':home/'hermes-agent.source.json',
        'stamp':source/'install-stamp.json','configuration':home/'config.yaml',
        'profile':home/'FRIDAY-PROFILE.json','launcher':source/'.hermes/bin/hermes'}.items():
        f.require(paths[name] == path, 'ordinary_update_exact_installed_inputs_required')
    previous = f.read_json(paths['previous_input']); current = f.read_json(paths['current_input'])
    f.require(request['previous_input'] != request['current_input'], 'ordinary_update_new_input_required')
    f.require({k:v for k,v in previous.items() if k != 'project_files'} ==
        {k:v for k,v in current.items() if k != 'project_files'} and current['home'] == str(home),
        'ordinary_update_operational_settings_changed')
    _, donors = budget.call(f.spec_checked,current,cli_only=True)
    marker = f.read_json(paths['marker']); receipt = f.read_json(paths['source_receipt'])
    f.require(marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE'
        and marker.get('schema') == f.SCHEMA and marker.get('home') == str(home)
        and marker.get('source') == str(source) and marker.get('runtime_ready') is False
        and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('input_sha256') == request['previous_input']['sha256']
        and marker.get('source_receipt_sha256') == request['source_receipt']['sha256']
        and current['product']['runtime'] == {'enabled':False}, 'ordinary_update_committed_phase_required')
    budget.call(f.composition_checked,previous,source,receipt,donors['hermes'])
    old = previous['project_files']; new = current['project_files']
    if exact_response:
        manifest = exact_response_manifest_checked(home,source,previous,current,receipt,budget)
    elif source88:
        manifest = bundle_manifests_checked(home,source,previous,current,receipt,budget)
    else:
        manifest_name = EXACT_RESPONSE_MANIFEST if exact_response else PROTECTED_COMPRESSOR_MANIFEST if source87 else MANUAL_COMPRESSION_MANIFEST if source86 else WEB_RUNTIME_HISTORY_MANIFEST if source85 else FILE_REPLY_CONTEXT_MANIFEST if source84 else COMBINED_INPUT_MANIFEST if source83 else WEB_INPUT_MANIFEST if source82 else FILE_TOOL_CONTRACT_MANIFEST if source81 else SPARK_REQUEST_BUDGET_MANIFEST if source80 else SPARK_MULTIPASS_MANIFEST if source79 else PRIVACY_EFFECT_MANIFEST if source78 else DOCX_CREATION_MANIFEST if source77 else DOCUMENT_EXTRACTION_MANIFEST if source76 else FILE_REVISION_MANIFEST if source75 else TOOL_RESULT_CONTEXT_MANIFEST if source74 else DSH_SANDBOX_MANIFEST if source73 else CURRENT_TURN_MANIFEST if source72 else CONTEXT_SELF_MANIFEST if source71 else PRIVATE_REPLY_MANIFEST if source70 else PROMPT_PRIVACY_MANIFEST if source69 else MEMORY_SCOPE_MANIFEST if source68 else FIRST_CONTACT_COPY_MANIFEST if source67 else INLINE_PRIVACY_MANIFEST if source66 else TOOL_METADATA_MANIFEST if source65 else PUBLIC_SURFACE_MANIFEST if source64 else WORKER_TOOLS_MANIFEST if source63 else DIALOGUE_CONTINUATION_MANIFEST if source62 else FIRST_CONTACT_STATE_MANIFEST if source61 else TURN_SCOPE_MANIFEST if source60 else ADMIN_STARTUP_MANIFEST if source59 else INTERACTION_SCOPE_MANIFEST if source58 else PROFILE_RUNTIME_MANIFEST if source57 else BROWSER_GATEWAY_MANIFEST if source56 else BROWSER_MANIFEST if source55 else SEARCH_RECOVERY_MANIFEST if source54 else WEB_OUTPUT_MANIFEST if source53 else WEB_CONTINUATION_MANIFEST if source52 else ADMIN_BROADCAST_MANIFEST if source51 else ADMIN_RESTART_MANIFEST if source50 else FILE_CONTINUATION_MANIFEST if source49 else PRIVATE_STATE_MANIFEST if source48 else UPDATE_MANIFEST
        native_files = PROTECTED_COMPRESSOR_FILES if source87 else MANUAL_COMPRESSION_FILES if source86 else WEB_RUNTIME_HISTORY_FILES if source85 else FILE_REPLY_CONTEXT_FILES if source84 else COMBINED_INPUT_FILES if source83 else WEB_INPUT_FILES if source82 else FILE_TOOL_CONTRACT_FILES if source81 else SPARK_REQUEST_BUDGET_FILES if source80 else SPARK_MULTIPASS_FILES if source79 else PRIVACY_EFFECT_FILES if source78 else DOCX_CREATION_FILES if source77 else DOCUMENT_EXTRACTION_FILES if source76 else FILE_REVISION_FILES if source75 else TOOL_RESULT_CONTEXT_FILES if source74 else DSH_SANDBOX_FILES if source73 else CURRENT_TURN_FILES if source72 else CONTEXT_SELF_FILES if source71 else PRIVATE_REPLY_FILES if source70 else PROMPT_PRIVACY_FILES if source69 else MEMORY_SCOPE_FILES if source68 else FIRST_CONTACT_COPY_FILES if source67 else INLINE_PRIVACY_FILES if source66 else TOOL_METADATA_FILES if source65 else PUBLIC_SURFACE_FILES if source64 else WORKER_TOOLS_FILES if source63 else DIALOGUE_CONTINUATION_FILES if source62 else FIRST_CONTACT_STATE_FILES if source61 else TURN_SCOPE_FILES if source60 else ADMIN_STARTUP_FILES if source59 else INTERACTION_SCOPE_FILES if source58 else PROFILE_RUNTIME_FILES if source57 else BROWSER_GATEWAY_FILES if source56 else BROWSER_FILES if source55 else SEARCH_RECOVERY_FILES if source54 else WEB_OUTPUT_FILES if source53 else WEB_CONTINUATION_FILES if source52 else ADMIN_BROADCAST_FILES if source51 else ADMIN_RESTART_FILES if source50 else FILE_CONTINUATION_FILES if source49 else PRIVATE_STATE_FILES if source48 else UPDATE_FILES
        manifest = json.loads(f.owned_file(f.ROOT/manifest_name),object_pairs_hook=f.unique)
        old = previous['project_files']; new = current['project_files']
        patch = manifest['patch']
        f.require(patch == (PROTECTED_COMPRESSOR_PATCH if source87 else MANUAL_COMPRESSION_PATCH if source86 else WEB_RUNTIME_HISTORY_PATCH if source85 else FILE_REPLY_CONTEXT_PATCH if source84 else COMBINED_INPUT_PATCH if source83 else WEB_INPUT_PATCH if source82 else FILE_TOOL_CONTRACT_PATCH if source81 else SPARK_REQUEST_BUDGET_PATCH if source80 else SPARK_MULTIPASS_PATCH if source79 else 'patches/hermes/ordinary-private-refusal-effect.patch' if source78 else 'patches/hermes/ordinary-docx-creation.patch' if source77 else 'patches/hermes/ordinary-document-extraction.patch' if source76 else 'patches/hermes/ordinary-file-revision.patch' if source75 else 'patches/hermes/ordinary-tool-result-context.patch' if source74 else 'patches/hermes/ordinary-dsh-native-sandbox-profile.patch' if source73 else 'patches/hermes/ordinary-current-turn-compaction-privacy-reply.patch' if source72 else 'patches/hermes/ordinary-context-self-disclosure.patch' if source71 else 'patches/hermes/ordinary-private-reply-compression.patch' if source70 else 'patches/hermes/ordinary-prompt-privacy-dialogue.patch' if source69 else 'patches/hermes/ordinary-memory-scope-privacy.patch' if source68 else 'patches/hermes/ordinary-first-contact-copy.patch' if source67 else 'patches/hermes/ordinary-inline-privacy-connected-repair.patch' if source66 else 'patches/hermes/ordinary-tool-metadata-progress-privacy.patch' if source65 else 'patches/hermes/ordinary-public-surface-privacy.patch' if source64 else 'patches/hermes/ordinary-worker-tools-packaging.patch' if source63 else 'patches/hermes/ordinary-dialogue-continuation.patch' if source62 else 'patches/hermes/ordinary-first-contact-state.patch' if source61 else 'patches/hermes/ordinary-telegram-turn-scope.patch' if source60 else 'patches/hermes/ordinary-admin-startup.patch' if source59 else 'patches/hermes/ordinary-interaction-scope.patch' if source58 else 'patches/hermes/ordinary-profile-runtime.patch' if source57 else 'patches/hermes/ordinary-browser-gateway.patch' if source56 else 'patches/hermes/ordinary-browser.patch' if source55 else 'patches/hermes/ordinary-search-recovery.patch' if source54 else 'patches/hermes/ordinary-web-output.patch' if source53 else 'patches/hermes/ordinary-web-continuation.patch' if source52 else 'patches/hermes/ordinary-admin-broadcast.patch' if source51 else 'patches/hermes/ordinary-admin-restart.patch' if source50 else 'patches/hermes/ordinary-file-continuation.patch' if source49 else 'patches/hermes/ordinary-private-state.patch' if source48 else 'patches/hermes/ordinary-native-repair.patch')
            and set(new) == set(old) | {manifest_name,patch}
            and all(new[name] == pin for name,pin in old.items()
                    if name not in (({'scripts/friday_ordinary_install.py'} if source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response else {'scripts/friday_install.py','scripts/friday_ordinary_install.py'}) |
                                    ({'scripts/friday_start.py'} if source48 or source54 else set()) |
                                    ({'tools/render_dsh_local.py'} if source73 else set()) |
                                    (set(FILE_TOOL_CONTRACT_PROJECT_AFTER) if source81 else set(SPARK_REQUEST_BUDGET_PROJECT_AFTER) if source80 else set(SPARK_MULTIPASS_PROJECT_AFTER) if source79 else set()) |
                                    (SPARK_MULTIPASS_PLUGIN_FILES if source79 else PRIVACY_EFFECT_PLUGIN_FILES if source78 else CONTEXT_SELF_PLUGIN_FILES if source71 else TOOL_METADATA_PLUGIN_FILES if source65 else WORKER_TOOLS_PLUGIN_FILES if source63 else BROWSER_PLUGIN_FILES if source55 else WORKER_ATTACH_PLUGIN_FILES if source49 else set()))),
            'ordinary_update_only_reviewed_source_required')
        f.require(manifest.get('base_commit') == receipt['commit']
            and len(receipt['layers']) == (85 if source87 else 84 if source86 else 83 if source85 else 82 if source84 else 81 if source83 or source82 else 80 if source81 else 79 if source80 else 78 if source79 else 77 if source78 else 76 if source77 else 75 if source76 else 74 if source75 else 73 if source74 else 72 if source73 else 71 if source72 else 70 if source71 else 69 if source70 else 68 if source69 else 67 if source68 else 66 if source67 else 65 if source66 else 64 if source65 else 63 if source64 else 62 if source63 else 61 if source62 else 60 if source61 else 59 if source60 else 58 if source59 else 57 if source58 else 56 if source57 else 55 if source56 else 54 if source55 else 53 if source54 else 52 if source53 else 51 if source52 else 50 if source51 else 49 if source50 else 48 if source49 else 47 if source48 else 46) and manifest_name not in {r['manifest'] for r in receipt['layers']}
            and manifest.get('installed_prefix') == {r['manifest']:r['manifest_sha256'] for r in receipt['layers']}
            and new[manifest_name] == f.digest(f.owned_file(f.ROOT/manifest_name))
            and manifest['patch_sha256'] == new[patch] == f.digest(f.owned_file(f.ROOT/patch)),
            'ordinary_update_exact_prefix_required')
        rows = manifest['files']
        f.require(type(rows) is list and len(rows) == len(native_files) and {r['path'] for r in rows} == native_files,
            'ordinary_update_exact_native_files_required')
        if source63:
            f.directory(source/'tools')
            f.require(not os.path.lexists(source/'config'), 'ordinary_update_new_directory_exists')
        for row in rows:
            added = (source87 and row['path'] in PROTECTED_COMPRESSOR_NEW_FILES) or (source80 and row['path'] in SPARK_REQUEST_BUDGET_NEW_FILES) or (source79 and row['path'] in SPARK_MULTIPASS_NEW_FILES) or (source78 and row['path'] in PRIVACY_EFFECT_NEW_FILES) or (source77 and row['path'] in DOCX_CREATION_NEW_FILES) or (source75 and row['path'] in FILE_REVISION_NEW_FILES) or (source55 and row['path'] in BROWSER_NEW_FILES) or (source63 and row['path'] in WORKER_TOOLS_FILES)
            if added:
                f.require(row.get('new_file') is True and row.get('mode') == '100644'
                    and row.get('before_sha256') is None and row['path'] not in receipt['files']
                    and not os.path.lexists(source/row['path']), 'ordinary_update_new_source_exists')
            else:
                f.require(row.get('new_file') is False and row.get('mode') == '100644'
                    and row['before_sha256'] == receipt['files'][row['path']]['sha256']
                    and row['before_sha256'] == f.digest(f.owned_file(source/row['path'])),
                    'ordinary_update_source_changed')
        if source87:
            # Validate the complete nested parent topology before consuming a journal.
            # New directories must be absent, even when a foreign directory is empty.
            with SourceUpdateDirectories(home,
                    ['hermes-agent/'+row['path'] for row in rows],
                    {'hermes-agent/'+name for name in (set() if exact_response else BUNDLE_NEW_DIRECTORIES if source88 else PROTECTED_COMPRESSOR_NEW_DIRECTORIES)}) as directories:
                directories.prove()
        # Reuse the shipped preparer's Git parser before any mutation. An extra
        # patch target must never escape this transaction's owned-file rollback.
        from scripts.hermes_prepare import overlay_layers, Budget as SourceBudget
        layers = budget.call(overlay_layers,f.ROOT,receipt['commit'],SourceBudget(budget.deadline))
        f.require(layers[-1][1]['manifest'] == manifest_name,
            'ordinary_update_final_layer_required')
    predecessor = request.get('predecessor_update')
    update_history(home,request['transaction_history'],predecessor,request.get('keyless_recovery'),request.get('inference_rebind'),request.get('worker_archive'))
    if source48 or source49 or source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
        old_request = f.read_json(f.pin(predecessor))
        f.require(old_request['schema'] == (BUNDLE_SCHEMA if exact_response else 'friday.ordinary-telegram-source-update.v40' if source87 or source88 else 'friday.ordinary-telegram-source-update.v39' if source86 else 'friday.ordinary-telegram-source-update.v38' if source85 else 'friday.ordinary-telegram-source-update.v37' if source84 else 'friday.ordinary-telegram-source-update.v35' if source83 or source82 else 'friday.ordinary-telegram-source-update.v34' if source81 else PROJECT_INFERENCE_HELPER_SCHEMA if source80 else 'friday.ordinary-telegram-source-update.v32' if source79 else PROJECT_RUNTIME_SCHEMA if source78 else 'friday.ordinary-telegram-source-update.v30' if source77 else 'friday.ordinary-telegram-source-update.v29' if source76 else 'friday.ordinary-telegram-source-update.v28' if source75 else 'friday.ordinary-telegram-source-update.v27' if source74 else 'friday.ordinary-telegram-source-update.v26' if source73 else 'friday.ordinary-telegram-source-update.v25' if source72 else 'friday.ordinary-telegram-source-update.v24' if source71 else 'friday.ordinary-telegram-source-update.v23' if source70 else 'friday.ordinary-telegram-source-update.v22' if source69 else 'friday.ordinary-telegram-source-update.v21' if source68 else 'friday.ordinary-telegram-source-update.v20' if source67 else 'friday.ordinary-telegram-source-update.v19' if source66 else 'friday.ordinary-telegram-source-update.v18' if source65 else 'friday.ordinary-telegram-source-update.v17' if source64 else 'friday.ordinary-telegram-source-update.v16' if source63 else 'friday.ordinary-telegram-source-update.v15' if source62 else 'friday.ordinary-telegram-source-update.v14' if source61 else 'friday.ordinary-telegram-source-update.v13' if source60 else 'friday.ordinary-telegram-source-update.v12' if source59 else 'friday.ordinary-telegram-source-update.v11' if source58 else 'friday.ordinary-telegram-source-update.v10' if source57 else 'friday.ordinary-telegram-source-update.v9' if source56 else 'friday.ordinary-telegram-source-update.v8' if source55 else 'friday.ordinary-telegram-source-update.v7' if source54 else 'friday.ordinary-telegram-source-update.v6' if source53 else 'friday.ordinary-telegram-source-update.v5' if source52 else 'friday.ordinary-telegram-source-update.v4' if source51 else 'friday.ordinary-telegram-source-update.v3' if source50 else 'friday.ordinary-telegram-source-update.v2' if source49
            else 'friday.ordinary-telegram-source-update.v1'), 'ordinary_update_predecessor_version_changed')
        old_tx = home/'preparation'/('ordinary-source-update-'+old_request['previous_input']['sha256'])
        committed = f.read_json(old_tx/'committed.json')
        if source57:
            budget.call(checked_worker_declaration_publication,home,request,old_request,marker)
        if source78:
            recovery = f.read_json(f.pin(request['keyless_recovery']))
            f.require(recovery['recovery_input'] == request['previous_input']
                and recovery['source_receipt'] == request['source_receipt']
                and recovery['stamp'] == request['stamp'],
                'ordinary_update_keyless_current_binding_changed')
        f.require(old_request['home'] == str(home) and (source57 or (source78 and f.read_json(f.pin(request['keyless_recovery']))['recovery_input'] == request['previous_input']) or ((source80 or source81) and f.read_json(f.pin(request['inference_rebind']))['current_input'] == request['previous_input']) or (source86 and f.read_json(f.pin(request['worker_archive']))['recovery_input'] == request['previous_input']) or old_request['current_input'] == request['previous_input'])
            and committed['source_receipt_sha256'] == request['source_receipt']['sha256'],
            'ordinary_update_predecessor_binding_changed')
    # Complete native identity/configuration/credential validation is reused;
    # no consumed query or historical installer phase is ever invoked.
    f.native_packages(source)
    from hermes_cli.friday_ordinary_gateway import check
    if source56:
        check_browser_gateway(home,source,manifest,budget,staged=True)
    else:
        check(home,role=False)
    f.require(all(f.digest(f.owned_file(home/name,private=True)) == pin
        for name,pin in marker['profile_files'].items() if not ((source49 or source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response) and name == 'config.yaml')),
        'ordinary_update_profile_changed')
    if source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
        before_plugins = {n:p for n,p in previous['project_files'].items() if n.startswith('plugins/friday_rework/')}
        f.require(marker.get('plugin_files') == before_plugins, 'ordinary_update_installed_plugin_marker_changed')
        checked_plugin_inventory(home, before_plugins)
    if exact_response:
        f.require(request['previous_input']['sha256'] == EXACT_RESPONSE_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == EXACT_RESPONSE_PREDECESSOR_REQUEST
            and f.digest(f.owned_file(old_tx/'committed.json',private=True)) == EXACT_RESPONSE_PREDECESSOR_COMMITTED
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False), 'ordinary_update_exact_response_ancestry_required')
        checked_source88_retained(home,request,budget)
    if source88:
        f.require(request['previous_input']['sha256'] == BUNDLE_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == BUNDLE_PREDECESSOR_REQUEST
            and f.digest(f.owned_file(old_tx/'committed.json',private=True)) == BUNDLE_PREDECESSOR_COMMITTED
            and len(request['transaction_history']) == BUNDLE_HISTORY_FILES and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False), 'ordinary_update_exact_bundle_ancestry_required')
        checked_source82_retained(home,request)
    if source87:
        f.require(new[manifest_name] == PROTECTED_COMPRESSOR_MANIFEST_SHA256
            and new[patch] == PROTECTED_COMPRESSOR_PATCH_SHA256
            and request['previous_input']['sha256'] == PROTECTED_COMPRESSOR_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == PROTECTED_COMPRESSOR_PREDECESSOR_REQUEST
            and len(request['transaction_history']) == PROTECTED_COMPRESSOR_HISTORY_FILES
            and len(old) == 243 and len(new) == 245
            and len(receipt['files']) == PROTECTED_COMPRESSOR_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == MANUAL_COMPRESSION_MANIFEST
            and PROTECTED_COMPRESSOR_FILES - PROTECTED_COMPRESSOR_NEW_FILES <= set(receipt['files'])
            and not PROTECTED_COMPRESSOR_NEW_FILES & set(receipt['files'])
            and {n for n in old if old[n] != new[n]} == {'scripts/friday_ordinary_install.py'}
            and old['scripts/friday_ordinary_install.py'] == PROTECTED_COMPRESSOR_PREVIOUS_UPDATER
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and f.digest(f.owned_file(old_tx/'committed.json',private=True)) == PROTECTED_COMPRESSOR_PREDECESSOR_COMMITTED
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_protected_compressor_delta_required')
        checked_source82_retained(home,request)
    if source86:
        f.require(new[manifest_name] == MANUAL_COMPRESSION_MANIFEST_SHA256
            and new[patch] == MANUAL_COMPRESSION_PATCH_SHA256
            and request['previous_input']['sha256'] == MANUAL_COMPRESSION_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == MANUAL_COMPRESSION_PREDECESSOR_REQUEST
            and len(request['transaction_history']) == MANUAL_COMPRESSION_HISTORY_FILES
            and len(old) == 241 and len(new) == 243
            and len(receipt['files']) == MANUAL_COMPRESSION_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == WEB_RUNTIME_HISTORY_MANIFEST
            and MANUAL_COMPRESSION_FILES <= set(receipt['files'])
            and {n for n in old if old[n] != new[n]} == {'scripts/friday_ordinary_install.py'}
            and old['scripts/friday_ordinary_install.py'] == MANUAL_COMPRESSION_PREVIOUS_UPDATER
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and f.digest(f.owned_file(old_tx/'committed.json',private=True)) == MANUAL_COMPRESSION_PREDECESSOR_COMMITTED
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_manual_compression_delta_required')
        checked_source82_retained(home,request)
    if source85:
        f.require(new[manifest_name] == WEB_RUNTIME_HISTORY_MANIFEST_SHA256
            and new[patch] == WEB_RUNTIME_HISTORY_PATCH_SHA256
            and request['previous_input']['sha256'] == WEB_RUNTIME_HISTORY_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == WEB_RUNTIME_HISTORY_PREDECESSOR_REQUEST
            and len(request['transaction_history']) == WEB_RUNTIME_HISTORY_HISTORY_FILES
            and len(old) == 239 and len(new) == 241
            and len(receipt['files']) == WEB_RUNTIME_HISTORY_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == FILE_REPLY_CONTEXT_MANIFEST
            and WEB_RUNTIME_HISTORY_FILES <= set(receipt['files'])
            and {n for n in old if old[n] != new[n]} == {'scripts/friday_ordinary_install.py'}
            and old['scripts/friday_ordinary_install.py'] == WEB_RUNTIME_HISTORY_PREVIOUS_UPDATER
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and f.digest(f.owned_file(old_tx/'committed.json',private=True)) == WEB_RUNTIME_HISTORY_PREDECESSOR_COMMITTED
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_web_runtime_history_delta_required')
        checked_source82_retained(home,request)
    if source84:
        f.require(new[manifest_name] == FILE_REPLY_CONTEXT_MANIFEST_SHA256
            and new[patch] == FILE_REPLY_CONTEXT_PATCH_SHA256
            and request['previous_input']['sha256'] == FILE_REPLY_CONTEXT_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == FILE_REPLY_CONTEXT_PREDECESSOR_REQUEST
            and len(request['transaction_history']) == FILE_REPLY_CONTEXT_HISTORY_FILES
            and len(old) == 237 and len(new) == 239
            and len(receipt['files']) == FILE_REPLY_CONTEXT_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == COMBINED_INPUT_MANIFEST
            and FILE_REPLY_CONTEXT_FILES <= set(receipt['files'])
            and {n for n in old if old[n] != new[n]} == {'scripts/friday_ordinary_install.py'}
            and old['scripts/friday_ordinary_install.py'] == FILE_REPLY_CONTEXT_PREVIOUS_UPDATER
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and f.digest(f.owned_file(old_tx/'committed.json',private=True)) == FILE_REPLY_CONTEXT_PREDECESSOR_COMMITTED
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_file_reply_context_delta_required')
        checked_source82_retained(home,request)
    if source83:
        f.require(new[manifest_name] == COMBINED_INPUT_MANIFEST_SHA256
            and new[patch] == COMBINED_INPUT_PATCH_SHA256
            and request['previous_input']['sha256'] == COMBINED_INPUT_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == COMBINED_INPUT_PREDECESSOR_REQUEST
            and len(request['transaction_history']) == COMBINED_INPUT_HISTORY_FILES
            and len(old) == 235 and len(new) == 237
            and len(receipt['files']) == COMBINED_INPUT_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == FILE_TOOL_CONTRACT_MANIFEST
            and COMBINED_INPUT_FILES <= set(receipt['files'])
            and {n for n in old if old[n] != new[n]} == {'scripts/friday_ordinary_install.py'}
            and old['scripts/friday_ordinary_install.py'] == COMBINED_INPUT_PREVIOUS_UPDATER
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_combined_input_delta_required')
        checked_source82_retained(home,request)
    if source82:
        f.require(new[manifest_name] == WEB_INPUT_MANIFEST_SHA256
            and new[patch] == WEB_INPUT_PATCH_SHA256
            and request['previous_input']['sha256'] == WEB_INPUT_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == WEB_INPUT_PREDECESSOR_REQUEST
            and len(request['transaction_history']) == WEB_INPUT_HISTORY_FILES
            and len(old) == 235 and len(new) == 237
            and len(receipt['files']) == WEB_INPUT_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == FILE_TOOL_CONTRACT_MANIFEST
            and WEB_INPUT_FILES <= set(receipt['files'])
            and {n for n in old if old[n] != new[n]} == {'scripts/friday_ordinary_install.py'}
            and old['scripts/friday_ordinary_install.py'] == WEB_INPUT_PREVIOUS_UPDATER
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and len(before_plugins) == 45
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_web_input_delta_required')
        checked_source82_retained(home,request)
    if source81:
        f.require(new[manifest_name] == FILE_TOOL_CONTRACT_MANIFEST_SHA256
            and new[patch] == FILE_TOOL_CONTRACT_PATCH_SHA256
            and request['previous_input']['sha256'] == FILE_TOOL_CONTRACT_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == SOURCE81_PREDECESSOR_REQUEST
            and request['inference_rebind']['sha256'] == SOURCE81_BUDGET_REQUEST
            and len(request['transaction_history']) == SOURCE81_HISTORY_FILES
            and len(old) == 233 and len(new) == 235
            and len(receipt['files']) == FILE_TOOL_CONTRACT_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == SPARK_REQUEST_BUDGET_MANIFEST
            and FILE_TOOL_CONTRACT_FILES <= set(receipt['files'])
            and set(FILE_TOOL_CONTRACT_PROJECT_AFTER) == FILE_TOOL_CONTRACT_PLUGIN_FILES
            and {n for n in old if old[n] != new[n]} == set(FILE_TOOL_CONTRACT_PROJECT_BEFORE)
            and all(old[n] == h for n,h in FILE_TOOL_CONTRACT_PROJECT_BEFORE.items())
            and all(new[n] == h for n,h in FILE_TOOL_CONTRACT_PROJECT_AFTER.items())
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and len(before_plugins) == 45
            and {n for n in before_plugins if old[n] != new[n]} == FILE_TOOL_CONTRACT_PLUGIN_FILES
            and not f.read_json(old_tx/'intent.json').get('project_only',False)
            and not committed.get('project_only',False),
            'ordinary_update_exact_file_tool_delta_required')
        checked_source81_retained(home,request)
    if source80:
        rebound = f.read_json(f.pin(request['inference_rebind']))
        after = f.read_json(home/'preparation'/('ordinary-inference-rebind-'+
            rebound['previous_input']['sha256'])/'committed.json')['after']
        for name,sha in PROJECT_INFERENCE_RECONCILIATION_PINS.items():
            f.pin({'path':str(home/name),'sha256':sha})
        f.require(SPARK_REQUEST_BUDGET_MANIFEST_SHA256 is not None
            and SPARK_REQUEST_BUDGET_PATCH_SHA256 is not None
            and new[manifest_name] == SPARK_REQUEST_BUDGET_MANIFEST_SHA256
            and new[patch] == SPARK_REQUEST_BUDGET_PATCH_SHA256
            and all(h is not None for h in SPARK_REQUEST_BUDGET_PROJECT_AFTER.values()),
            'ordinary_update_final_request_budget_pins_required')
        f.require(request['previous_input']['sha256'] == SPARK_REQUEST_BUDGET_PREVIOUS_INPUT
            and request['predecessor_update']['sha256'] == SOURCE80_HELPER_REQUEST
            and request['inference_rebind']['sha256'] == SOURCE80_REBIND_REQUEST
            and len(request['transaction_history']) == SOURCE80_HISTORY_FILES
            and len(old) == 231 and len(new) == 233
            and len(receipt['files']) == SPARK_REQUEST_BUDGET_NATIVE_FILES
            and receipt['layers'][-1]['manifest'] == SPARK_MULTIPASS_MANIFEST
            and set(receipt['files']) >= SPARK_REQUEST_BUDGET_FILES - SPARK_REQUEST_BUDGET_NEW_FILES
            and not (set(receipt['files']) & SPARK_REQUEST_BUDGET_NEW_FILES)
            and not (set(old) & SPARK_REQUEST_BUDGET_FILES)
            and set(SPARK_REQUEST_BUDGET_PROJECT_AFTER) == set(SPARK_REQUEST_BUDGET_PROJECT_BEFORE) - {'scripts/friday_ordinary_install.py'}
            and {n for n in old if old[n] != new[n]} == set(SPARK_REQUEST_BUDGET_PROJECT_BEFORE)
            and all(old[n] == h for n,h in SPARK_REQUEST_BUDGET_PROJECT_BEFORE.items())
            and all(new[n] == h for n,h in SPARK_REQUEST_BUDGET_PROJECT_AFTER.items())
            and new['scripts/friday_ordinary_install.py'] == f.digest(f.owned_file(Path(__file__)))
            and len(before_plugins) == 45
            and {n for n in before_plugins if old[n] != new[n]} == SPARK_REQUEST_BUDGET_PLUGIN_FILES
            and f.read_json(old_tx/'intent.json').get('project_only') is True
            and committed.get('project_only') is True
            and type(current['product']['runtime']['enabled']) is bool,
            'ordinary_update_exact_request_budget_delta_required')
        f.require(request['marker']['sha256'] == after[f.MARKER],
            'ordinary_update_rebound_marker_changed')
        for name,sha in after.items():
            f.pin({'path':str(home/name),'sha256':sha})
    if source79:
        f.require(SPARK_MULTIPASS_MANIFEST_SHA256 is not None
            and SPARK_MULTIPASS_PATCH_SHA256 is not None
            and new[manifest_name] == SPARK_MULTIPASS_MANIFEST_SHA256
            and new[patch] == SPARK_MULTIPASS_PATCH_SHA256,
            'ordinary_update_final_spark_pins_required')
        f.require(request['previous_input']['sha256'] == SPARK_MULTIPASS_PREVIOUS_INPUT
            and len(old) == 229 and len(new) == 231
            and len(receipt['files']) == SPARK_MULTIPASS_NATIVE_FILES
            and set(receipt['files']) >= SPARK_MULTIPASS_FILES - SPARK_MULTIPASS_NEW_FILES
            and not (set(receipt['files']) & SPARK_MULTIPASS_NEW_FILES)
            and not (set(old) & SPARK_MULTIPASS_FILES)
            and {n for n in old if old[n] != new[n]} == set(SPARK_MULTIPASS_PROJECT_BEFORE)
            and all(old[n] == h for n,h in SPARK_MULTIPASS_PROJECT_BEFORE.items())
            and all(new[n] == h for n,h in SPARK_MULTIPASS_PROJECT_AFTER.items())
            and len(before_plugins) == 45
            and {n for n in before_plugins if old[n] != new[n]} == SPARK_MULTIPASS_PLUGIN_FILES,
            'ordinary_update_exact_spark_multipass_delta_required')
    if source78:
        f.require(len(old) == 227 and len(new) == 229 and len(receipt['files']) == PRIVACY_EFFECT_NATIVE_FILES
            and set(receipt['files']) >= PRIVACY_EFFECT_FILES - PRIVACY_EFFECT_NEW_FILES
            and not (set(receipt['files']) & PRIVACY_EFFECT_NEW_FILES)
            and not (set(old) & PRIVACY_EFFECT_FILES)
            and {n for n in old if n.startswith('plugins/friday_rework/') and old[n] != new[n]} == PRIVACY_EFFECT_PLUGIN_FILES
            and all(old[n] == PRIVACY_EFFECT_PLUGIN_BEFORE and new[n] == PRIVACY_EFFECT_PLUGIN_AFTER for n in PRIVACY_EFFECT_PLUGIN_FILES),
            'ordinary_update_exact_privacy_effect_delta_required')
    if source77:
        f.require(len(old) == 220 and len(new) == 222 and set(receipt['files']) >= DOCX_CREATION_FILES - DOCX_CREATION_NEW_FILES
            and not (set(receipt['files']) & DOCX_CREATION_NEW_FILES) and not (set(old) & DOCX_CREATION_FILES),
            'ordinary_update_exact_docx_creation_delta_required')
    if source76:
        f.require(len(old) == 218 and len(new) == 220 and set(receipt['files']) >= DOCUMENT_EXTRACTION_FILES
            and not (set(old) & DOCUMENT_EXTRACTION_FILES),
            'ordinary_update_exact_document_extraction_delta_required')
    if source75:
        f.require(len(old) == 216 and len(new) == 218 and set(receipt['files']) >= FILE_REVISION_FILES - FILE_REVISION_NEW_FILES
            and not (set(old) & FILE_REVISION_FILES),
            'ordinary_update_exact_file_revision_delta_required')
    if source74:
        f.require(len(old) == 214 and len(new) == 216 and set(receipt['files']) >= TOOL_RESULT_CONTEXT_FILES
            and not (set(old) & TOOL_RESULT_CONTEXT_FILES),
            'ordinary_update_exact_tool_result_context_delta_required')
    if source73:
        f.require(len(old) == 212 and len(new) == 214 and set(receipt['files']) >= DSH_SANDBOX_FILES
            and all(old[row['path']] == row['before_sha256'] and new[row['path']] == row['sha256']
                for row in rows if row['path'] == 'tools/render_dsh_local.py'),
            'ordinary_update_exact_dsh_sandbox_delta_required')
    if source72:
        f.require(len(old) == 210 and len(new) == 212 and set(receipt['files']) >= CURRENT_TURN_FILES,
            'ordinary_update_exact_current_turn_delta_required')
    if source71:
        f.require(len(old) == 208 and len(new) == 210 and set(receipt['files']) >= CONTEXT_SELF_FILES
            and {n for n in old if n.startswith('plugins/friday_rework/') and old[n] != new[n]} == CONTEXT_SELF_PLUGIN_FILES,
            'ordinary_update_exact_context_self_delta_required')
    if source70:
        f.require(len(old) == 206 and len(new) == 208 and set(receipt['files']) >= PRIVATE_REPLY_FILES,
            'ordinary_update_exact_private_reply_delta_required')
    if source69:
        f.require(len(old) == 204 and len(new) == 206 and set(receipt['files']) >= PROMPT_PRIVACY_FILES,
            'ordinary_update_exact_prompt_privacy_delta_required')
    if source68:
        f.require(len(old) == 202 and len(new) == 204 and set(receipt['files']) >= MEMORY_SCOPE_FILES,
            'ordinary_update_exact_memory_scope_delta_required')
    if source67:
        f.require(len(old) == 200 and len(new) == 202 and set(receipt['files']) >= FIRST_CONTACT_COPY_FILES,
            'ordinary_update_exact_first_contact_copy_delta_required')
    if source66:
        f.require(len(old) == 198 and len(new) == 200 and set(receipt['files']) >= INLINE_PRIVACY_FILES,
            'ordinary_update_exact_inline_privacy_delta_required')
    if source65:
        f.require(len(old) == 196 and len(new) == 198 and set(receipt['files']) >= TOOL_METADATA_FILES
            and {n for n in old if n.startswith('plugins/friday_rework/') and old[n] != new[n]} == TOOL_METADATA_PLUGIN_FILES,
            'ordinary_update_exact_tool_metadata_delta_required')
    if source64:
        f.require(len(old) == 194 and len(new) == 196 and set(receipt['files']) >= PUBLIC_SURFACE_FILES,
            'ordinary_update_exact_public_surface_delta_required')
    if source63:
        f.require(len(old) == 192 and len(new) == 194
            and not (set(receipt['files']) & WORKER_TOOLS_FILES)
            and {n for n in old if n.startswith('plugins/friday_rework/') and old[n] != new[n]} == WORKER_TOOLS_PLUGIN_FILES,
            'ordinary_update_exact_worker_tools_delta_required')
    if source62:
        f.require(len(old) == 190 and len(new) == 192
            and set(receipt['files']) >= DIALOGUE_CONTINUATION_FILES,
            'ordinary_update_exact_dialogue_continuation_delta_required')
    if source61:
        f.require(len(old) == 188 and len(new) == 190
            and set(receipt['files']) >= FIRST_CONTACT_STATE_FILES,
            'ordinary_update_exact_first_contact_state_delta_required')
    if source60:
        f.require(len(old) == 186 and len(new) == 188
            and set(receipt['files']) >= TURN_SCOPE_FILES,
            'ordinary_update_exact_turn_scope_delta_required')
    if source59:
        f.require(len(old) == 184 and len(new) == 186
            and set(receipt['files']) >= ADMIN_STARTUP_FILES,
            'ordinary_update_exact_admin_startup_delta_required')
    if source58:
        f.require(len(old) == 182 and len(new) == 184
            and set(receipt['files']) >= INTERACTION_SCOPE_FILES,
            'ordinary_update_exact_interaction_scope_delta_required')
    if source57:
        f.require(len(old) == 180 and len(new) == 182
            and set(receipt['files']) >= PROFILE_RUNTIME_FILES,
            'ordinary_update_exact_profile_runtime_delta_required')
    if source56:
        f.require(len(old) == 176 and len(new) == 178
            and set(receipt['files']) >= BROWSER_GATEWAY_FILES,
            'ordinary_update_exact_browser_gateway_delta_required')
    if source55:
        before_plugins = {n:p for n,p in old.items() if n.startswith('plugins/friday_rework/')}
        after_plugins = {n:p for n,p in new.items() if n.startswith('plugins/friday_rework/')}
        f.require(len(old) == 174 and len(new) == 176 and set(before_plugins) == set(after_plugins)
            and {n for n in before_plugins if before_plugins[n] != after_plugins[n]} == BROWSER_PLUGIN_FILES,
            'ordinary_update_exact_browser_plugin_delta_required')
    if source49:
        before_plugins = {n:p for n,p in previous['project_files'].items() if n.startswith('plugins/friday_rework/')}
        after_plugins = {n:p for n,p in current['project_files'].items() if n.startswith('plugins/friday_rework/')}
        f.require(marker.get('plugin_files') == before_plugins and set(before_plugins) == set(after_plugins)
            and {n for n in before_plugins if before_plugins[n] != after_plugins[n]} == WORKER_ATTACH_PLUGIN_FILES,
            'ordinary_update_exact_worker_plugin_delta_required')
        checked_plugin_inventory(home, before_plugins)
    credentials = request['credential_files']
    f.require(type(credentials) is dict and set(credentials) == {'.env','auth.json'},
        'ordinary_update_credential_pins_required')
    for name,ref in credentials.items():
        f.require(not os.path.lexists(home/name) if ref is None else f.pin(ref) == home/name,
            'ordinary_update_credential_pin_changed')
    tx = home/'preparation'/('ordinary-source-update-'+request['previous_input']['sha256'])
    f.require(not os.path.lexists(tx), 'ordinary_update_consumed_no_retry')
    return home, source, previous, current, marker, receipt, manifest, donors, tx


@contextlib.contextmanager
def stopped_consumers(home, unit_ref, budget):
    """Prove native stop, then retain standard native custody for all three roles."""
    f = api()
    from gateway import host_rendezvous as hr
    from gateway.status import get_running_pid_identity_strict
    from hermes_cli import gateway as gw
    f.require(gw.get_systemd_unit_path(system=False) == f.pin(unit_ref)
        and not os.path.lexists(gw.get_systemd_unit_path(system=True)),
        'ordinary_update_exact_native_user_unit_required')
    runtime = f.directory(Path('/run/user')/str(os.getuid())); bus = runtime/'bus'; info = bus.lstat()
    f.require(stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
        'ordinary_update_owned_user_bus_required')
    unit = gw.get_service_name()+'.service'
    command = ['/usr/bin/env','XDG_RUNTIME_DIR='+str(runtime),
        'DBUS_SESSION_BUS_ADDRESS=unix:path='+str(bus),'SYSTEMCTL_FORCE_BUS=1','/usr/bin/systemctl','--user','show',unit,
        '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID']
    from scripts.dsh_prepare import run
    def prove():
        output = run(command,f.ROOT,timeout=min(15,budget.check(reserve=1)),
            env=f.clean_environment(home),deadline=budget.deadline)[0]
        pairs = [line.split('=',1) for line in output.splitlines() if line]
        f.require(len(pairs) == 6 and all(len(row) == 2 for row in pairs)
            and dict(pairs) == {'Id':unit,'LoadState':'loaded','ActiveState':'inactive',
                'SubState':'dead','MainPID':'0','ControlPID':'0'}, 'ordinary_update_native_stop_required')
        f.require(get_running_pid_identity_strict(home/'gateway.pid') is None,
            'ordinary_update_gateway_pid_present')
        for role in (hr.ROLE_GATEWAY,hr.ROLE_SERVE,hr.ROLE_DESKTOP_SERVE):
            f.require(not os.path.lexists(hr.record_path(role))
                and hr.read_record(role,include_stale=True) is None,
                'ordinary_update_no_native_consumer_required')
    claimed = []
    try:
        prove()
        f.directory(hr.host_state_dir())
        for role in (hr.ROLE_GATEWAY,hr.ROLE_SERVE,hr.ROLE_DESKTOP_SERVE):
            path = hr.lock_path(role)
            f.require(path.parent == hr.host_state_dir() and not hr.owns_host_lock(role),
                'ordinary_update_native_lock_scope_changed')
            before = None
            if os.path.lexists(path):
                f.owned_file(path); info = path.stat(); before = (info.st_dev,info.st_ino)
            outcome,_ = hr.claim_host_lock(role)
            f.require(outcome is hr.HostLockOutcome.ACQUIRED,
                'ordinary_update_native_lock_held_or_unavailable')
            claimed.append(role)
            # Native claim may create its ordinary empty lock; it never
            # publishes a role record or starts a gateway/dashboard consumer.
            f.owned_file(path); info = path.stat()
            f.require(hr.owns_host_lock(role) and (before is None or before == (info.st_dev,info.st_ino)),
                'ordinary_update_native_lock_identity_changed')
        prove()
        yield prove
    finally:
        for role in reversed(claimed): hr.release_host_lock(role)
        f.require(not any(hr.owns_host_lock(role) for role in claimed),
            'ordinary_update_native_lock_release_unconfirmed')


@contextlib.contextmanager
def retained_build_lock(source, *, lock_path=None, required=False):
    """Retain the exact existing native build lock; never create or replace it."""
    f = api(); path = source/'.web_ui_build.lock' if lock_path is None else f.canonical(str(lock_path))
    if not os.path.lexists(path):
        f.require(not required,'ordinary_update_existing_native_pm_lock_required')
        yield lambda: f.require(not os.path.lexists(path),'ordinary_update_web_build_lock_appeared')
        return
    before = path.lstat()
    f.require(f.owned_file(path) == b'', 'ordinary_update_native_build_lock_required')
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK); held = False
    try:
        def prove():
            current = os.fstat(fd); named = path.lstat()
            fields = ('st_dev','st_ino','st_mode','st_uid','st_nlink','st_size','st_mtime_ns')
            f.require(stat.S_ISREG(current.st_mode) and current.st_uid == os.getuid()
                and current.st_nlink == 1 and current.st_size == 0
                and stat.S_IMODE(current.st_mode) in (0o600,0o644,0o664)
                and all(getattr(before,k) == getattr(current,k) == getattr(named,k) for k in fields),
                'ordinary_update_native_build_lock_changed')
        prove()
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB); held = True
        prove(); yield prove
    finally:
        try:
            if held:
                try: prove()
                except BaseException as exc:
                    from scripts.dsh_prepare import StopUnconfirmed
                    raise StopUnconfirmed('native build lock custody requires reconciliation') from exc
        finally: os.close(fd)


@contextlib.contextmanager
def retained_pm_lock(home, source):
    """Hold the existing native PM install lock without creating PM state.

    pm.environments.install_key uses the first sixteen SHA256 hex characters of
    the canonical source path. Source updates run only in their owning home.
    """
    f = api(); installs = f.directory(home/'installs')
    state = f.directory(installs/f.digest(str(source).encode('utf-8'))[:16])
    with retained_build_lock(source,lock_path=state/'.install.lock',required=True) as prove:
        yield prove



# Exact Source90 dashboard typed-settings successor; helper remains project source.
PROJECT_DASHBOARD_SCHEMA = 'friday.ordinary-telegram-project-update.v5'
PROJECT_DASHBOARD_PROJECT_SHA256 = 'c47a8cad7932e557c06aaaac85d571c514e474b001e774e83e8b2619a107d58f'
PROJECT_DASHBOARD_RECEIPT_SHA256 = 'd722d6bc33d045a8d0d6571e89c0cb9ea58bbb5f8230dff4b3b85b7c91ca39ab'
PROJECT_DASHBOARD_NATIVE_FILES = 17710
PROJECT_DASHBOARD_BEFORE = {
    'plugins/friday_rework/admin_settings.py':'1b9f3ef44ab9483ff2ea230ae9d00640510ee8bc35e645feb2b01483ebc3510e',
    'plugins/friday_rework/dashboard/index.js':'7fdfef695c8bd56068338e69346a170b0ac8dc1f473a492e72bf807b88a3e9bf',
}
PROJECT_DASHBOARD_AFTER = {
    'plugins/friday_rework/admin_settings.py':'fd3bb8f97c61ba08bcd670e1a68fec9ba219ecb3d4e1e1d5198649dacc58ea97',
    'plugins/friday_rework/dashboard/index.js':'39ad98f3b34357bd1418814a9992bc7f026a48fb1e9a5cfc3cae9a2908d6be70',
}


def project_dashboard_history(home, request):
    """Retain the real Source90 commit and its one later renderer-v3 journal.

    References are supplied and pinned by the owning operator at admission;
    no historical input, clock or count is promoted to fresh execution proof.
    """
    f = api(); predecessor = f.read_json(f.pin(request['predecessor_update']))
    f.require(predecessor.get('schema') == 'friday.ordinary-telegram-source-update.v44'
        and predecessor.get('home') == str(home), 'ordinary_project_source90_predecessor_required')
    source_input = f.read_json(f.pin(predecessor['current_input']))
    f.require(f.digest(encoded(source_input['project_files'])) == PROJECT_DASHBOARD_PROJECT_SHA256,
        'ordinary_project_source90_project_ancestry_changed')
    updates = request['rebind_updates']
    f.require(type(updates) is list and len(updates) == 1,
        'ordinary_project_exact_source90_renderer_chain_required')
    reference = updates[0]; rebind = f.read_json(f.pin(reference))
    f.require(rebind.get('schema') == REBIND_RENDERER_SCHEMA and rebind.get('home') == str(home)
        and rebind.get('profile') == 'dest_telegram'
        and rebind.get('previous_input') == predecessor['current_input']
        and rebind.get('current_input') == request['previous_input'],
        'ordinary_project_latest_renderer_binding_required')
    latest = f.read_json(f.pin(rebind['current_input']))
    f.require(encoded({k:v for k,v in source_input.items() if k != 'product'}) ==
        encoded({k:v for k,v in latest.items() if k != 'product'}),
        'ordinary_project_renderer_source_inventory_changed')
    inference_renderer_delta(source_input['product'], latest['product'])
    name = 'preparation/ordinary-inference-rebind-'+rebind['previous_input']['sha256']
    tx = f.directory(home/name); intent = f.read_json(tx/'intent.json')
    committed = f.read_json(tx/'committed.json')
    names = {f.MARKER,'config.yaml','profiles/dest_telegram/config.yaml',
        'profiles/dest_telegram/.friday-onboarding.json','profiles/dest_telegram/.friday-user-scope.json'}
    f.require(intent.get('schema') == REBIND_RENDERER_SCHEMA and intent.get('state') == 'CONSUMED_NO_RETRY'
        and intent.get('request_sha256') == reference['sha256']
        and intent.get('seconds') == rebind['seconds']
        and intent.get('previous_input') == rebind['previous_input']
        and intent.get('current_input') == rebind['current_input']
        and committed.get('state') == 'EXACT_COMPRESSOR_RENDERER_REBOUND_CONSUMERS_STOPPED_NOT_RUNTIME_ACCEPTED'
        and committed.get('ready') is False
        and all(body.get(field) is False for body in (intent,committed)
            for field in ('consumers_started','workers_enabled','database_changed'))
        and set(rebind['before']) == set(intent['before']) == set(committed['after']) == names
        and all(intent['before'][n] == {'sha256':rebind['before'][n]['sha256'],'mode':0o600}
            and rebind['before'][n]['path'] == str(home/n) for n in names)
        and not os.path.lexists(tx/'rolled-back.json'),
        'ordinary_project_committed_renderer_required')
    exact = {'intent.json':f.digest(f.owned_file(tx/'intent.json',private=True)),
        'committed.json':f.digest(f.owned_file(tx/'committed.json',private=True)),
        **{'before/'+n:intent['before'][n]['sha256'] for n in names},
        **{'stage/'+n:committed['after'][n] for n in names},
        'stage/FRIDAY-PROFILE.json':rebind['retained']['FRIDAY-PROFILE.json']['sha256'],
        'stage/config.yaml.lock':f.digest(b''),'stage/profiles/dest_telegram/config.yaml.lock':f.digest(b'')}
    actual = {}
    for path in tx.rglob('*'):
        f.require(not path.is_symlink(),'ordinary_update_history_link_refused')
        if path.is_dir(): f.directory(path)
        else: actual[str(path.relative_to(tx))] = f.digest(f.owned_file(path,private=True))
    f.require(actual == exact,'ordinary_project_renderer_inventory_changed')
    history = request['transaction_history']
    f.require(type(history) is dict and {n[len(name)+1:]:h for n,h in history.items()
        if n.startswith(name+'/')} == exact,'ordinary_project_renderer_history_changed')
    update_history(home,{n:h for n,h in history.items() if not n.startswith(name+'/')},
        request['predecessor_update'])
    own = 'ordinary-source-update-'+request['previous_input']['sha256']
    for root in f.directory(home/'preparation').iterdir():
        if root.name == own or not root.name.startswith(('ordinary-source-update-','ordinary-inference-rebind-')):
            continue
        f.require(not root.is_symlink(),'ordinary_update_history_link_refused')
        f.directory(root)
        for path in root.rglob('*'):
            f.require(not path.is_symlink(),'ordinary_update_history_link_refused')
            if path.is_dir(): f.directory(path)
            else:
                f.require(history.get(str(path.relative_to(home))) ==
                    f.digest(f.owned_file(path,private=True)),'ordinary_project_unaccounted_current_history')
    previous_tx = home/'preparation'/('ordinary-source-update-'+predecessor['previous_input']['sha256'])
    f.require(f.read_json(previous_tx/'committed.json')['source_receipt_sha256'] ==
        request['source_receipt']['sha256'], 'ordinary_update_predecessor_binding_changed')
    retained = request['retained']
    required = {n:ref['sha256'] for n,ref in rebind['retained'].items()}
    required.update({n:h for n,h in committed['after'].items() if n != f.MARKER})
    # facts.json is the native PM selection record, not a second selector.
    state = 'installs/'+f.digest(str(home/'hermes-agent').encode('utf-8'))[:16]
    facts_name = state+'/facts.json'
    f.require(type(retained) is dict and facts_name in retained
        and f.MARKER not in retained and not any(n.startswith('plugins/') for n in retained),
        'ordinary_project_pm_retained_references_required')
    for n,ref in retained.items():
        path = Path(n)
        f.require(not path.is_absolute() and path.parts and not {'.','..'} & set(path.parts)
            and n not in {'source_receipt','stamp','configuration','profile','launcher','native_unit'}
            and f.pin(ref) == home/path,'ordinary_project_exact_retained_path_required')
    facts = f.read_json(home/facts_name)
    # Read the one native PM selection; an absent/broken record grants no
    # permission to select a fallback or a different retained generation.
    f.require(type(facts) is dict and type(facts.get('schema')) is int and facts['schema'] == 1
        and type(facts.get('packages')) is dict
        and type(facts['packages'].get('venv')) is dict
        and type(facts['packages']['venv'].get('environment')) is str,
        'ordinary_project_native_pm_environment_required')
    environment = f.canonical(facts['packages']['venv']['environment'])
    f.require(environment.is_relative_to(home/state/'environments')
        and str(environment.relative_to(home))+'/pyvenv.cfg' in retained
        and all(n in retained and retained[n]['sha256'] == h for n,h in required.items())
        and committed['after'][f.MARKER] == request['marker']['sha256'],
        'ordinary_project_latest_retained_scope_changed')
    return retained


PROJECT_UPDATE_SCHEMA = 'friday.ordinary-telegram-project-update.v1'
PROJECT_QUALIFICATION_SCHEMA = 'friday.ordinary-telegram-project-update.v2'
PROJECT_QUALIFICATION_NATIVE_FILES = 17682
PROJECT_QUALIFICATION_HISTORY_FILES = 417
PROJECT_QUALIFICATION_BEFORE = {
    'plugins/friday_rework/host_runtime.py':'89a45984ab69ca3c6fb8d339c09a123d7b76e4dda1a47099fa5a63e61b5d795c',
    'plugins/friday_rework/user_worker_join.py':'98094b0b4063ebc419c8c5de5cc3e0fc394ad5a577c3ad361964da67da5f1894',
    'scripts/worker_qualification.py':'fcb09bcb67e650141f057d3a32a67bc42bb9215e108c43171f3c9365fe5ac294',
    'scripts/friday_ordinary_install.py':'a271ae1941edbabebfd7359eef955d18c773c787542f989eb7c22635313b44d5',
}
PROJECT_QUALIFICATION_AFTER = {
    'plugins/friday_rework/host_runtime.py':'6435ccc10e8ea3f2b9a7fc1c639e5788f32ff18141344a6f58f0c5fcf68fd585',
    'plugins/friday_rework/user_worker_join.py':'41b560fd9c290cd7c07cbbe518e14767fde4fafb09a616778144ad6851bb5dd1',
    'scripts/worker_qualification.py':'3368b230ead0a1d371b8f8afb6a46298765d5832e9ef97fa3528876432ea92e1',
}
# This exact successor adds the installed worker helper closure. Source-only
# scripts remain in the reviewed project inventory and are never copied to home.
PROJECT_RUNTIME_SCHEMA = 'friday.ordinary-telegram-project-update.v3'
PROJECT_RUNTIME_NATIVE_FILES = 17682
PROJECT_RUNTIME_HISTORY_FILES = 422
PROJECT_INFERENCE_HELPER_SCHEMA = 'friday.ordinary-telegram-project-update.v4'
PROJECT_INFERENCE_HELPER = 'scripts/friday_ordinary_install.py'
PROJECT_INFERENCE_HELPER_BEFORE = '660e2901317ddd1c63f936c6157e043a6d2fcd0bdb49d1aaacce4d0e5fdbaa28'
PROJECT_INFERENCE_NATIVE_FILES = 17686
PROJECT_INFERENCE_HISTORY_FILES = 494
PROJECT_INFERENCE_INPUT_BEFORE = 'cbd86dd4da6febed50c38050150f66fba59bb8de71edbbc6798a66b1582d79b1'
PROJECT_INFERENCE_PREDECESSOR_INPUT = 'b0a7f22999b881b04a8ae1059d7d21feb562e7a2b2aa0958e87a686d375e0cc4'
PROJECT_INFERENCE_RECONCILIATION = 'preparation/ordinary-closed-reconciliation-native79-closed23-userbus-repair-20261016'
PROJECT_INFERENCE_RECONCILIATION_PINS = {
    PROJECT_INFERENCE_RECONCILIATION+'/intent.json':'9e3f99a9202c9e643ebadfe5178337c9b5aad16f89b73207cf466f1762195afd',
    PROJECT_INFERENCE_RECONCILIATION+'/committed.json':'dce9f69849dbf13378583b27b8de32d862cf0174b890aed07ad221b1ce223407',
    PROJECT_INFERENCE_RECONCILIATION+'/before/FRIDAY-INSTALL.json':'64a126decee4c29862ff1fdb118b52d92c9dcdae923a7d6ab5ed5e01442390d0',
}
PROJECT_RUNTIME_NEW = {
    'plugins/friday_rework/runtime_observers.py',
    'plugins/friday_rework/runtime_process.py',
    'plugins/friday_rework/runtime_containment.py',
    'plugins/friday_rework/runtime_primitives.py',
}
PROJECT_RUNTIME_BEFORE = {
    'plugins/friday_rework/host_runtime.py':'6435ccc10e8ea3f2b9a7fc1c639e5788f32ff18141344a6f58f0c5fcf68fd585',
    'plugins/friday_rework/user_worker_join.py':'41b560fd9c290cd7c07cbbe518e14767fde4fafb09a616778144ad6851bb5dd1',
    'plugins/friday_rework/a0_bootstrap.py':'16ff14e9a84d9786f8996d4e6ca041747daf4fa312a3bb01a5660025ead2a478',
    'scripts/worker_qualification.py':'3368b230ead0a1d371b8f8afb6a46298765d5832e9ef97fa3528876432ea92e1',
    'scripts/dsh_prepare.py':'d1a67a444530aaac43a6c86948fd26ef56fe272d8935282ea2c1f800f4417fa0',
    'scripts/install_containment.py':'e8a877bd2838df69a0bdf6ecde9dcec69887115f3b1043a150b58589949a643b',
    'scripts/friday_install.py':'882666c21807c7a243e91b3849302d0757f7ddc358fa1acbe1aabc2c712f9964',
    'scripts/friday_ordinary_install.py':'92b6bb29eb52fccaf6b3133b493372c23e918b28f13bdba2d200dd502831fb25',
}
# Frozen helper-closure candidate; the updater itself is pinned by current_input.
PROJECT_RUNTIME_AFTER = {
    'plugins/friday_rework/a0_bootstrap.py':'f64bf2427f2006417169a284293622c0cab31ff088537f995e2c512edd07251a',
    'plugins/friday_rework/host_runtime.py':'3855f0495dbd2547d96d44110a51cb0838e002f0e0bf4b3dac3f95077c049d7b',
    'plugins/friday_rework/runtime_containment.py':'41ba7c6853dadae5021fa6fee4520dfe4e620187d726ba4fb6693bb0df1953f7',
    'plugins/friday_rework/runtime_observers.py':'17d56e263a52610bb3872f9f97f5d5a95ebf2eaf9b9c0ac5faefacc33f5e7f6c',
    'plugins/friday_rework/runtime_primitives.py':'3a068a65fe6fbea085a07b50a37fcaddfe62fe5ba524be4de46d282321379fe6',
    'plugins/friday_rework/runtime_process.py':'edad3f51e9a8b180173eb1c17f1bde065eefc317e4ab3ceeb8ea9ef5499b5c6f',
    'plugins/friday_rework/user_worker_join.py':'e0dab0f3a21c3ac3ce841aa6d8176d4fd60ea4c57f6b633cdc0e2091e3e55358',
    'scripts/dsh_prepare.py':'f5c40cf793965f7c414256eb378bb9c2e6b61c0cbb71ae111276e61c8d32c663',
    'scripts/friday_install.py':'2685a9be13b27e5aab91c9502e8ca813d7aadf8ba23aba3dd70d9c4b35d7f03b',
    'scripts/install_containment.py':'e877f76a1e4b373bf1fecf083aef9c2af24befba2c55b19b25bfd65ecbbad3f1',
    'scripts/worker_qualification.py':'5af4c0b735da3c392c3adb12d6f637307764877dfa238cd09b0bd01518053dee',
}
PROJECT_DSH = 'plugins/friday_rework/adapters/dsh.py'
PROJECT_POLICY = 'config/apparmor/friday-dsh-native-v1'
PROJECT_DSH_BEFORE = 'ae00308381e976dd0c7130901979f6dc1bac1d84f9e25cc49fbc7bde1408a066'
PROJECT_AFTER = {
    PROJECT_DSH:'b055c33ece99f669ec2a185f8227ffa70eea54b1afb696384670641ccd2c0554',
    PROJECT_POLICY:'5a400147afe52cf1ce879112ca41f6d2ff5718032971f438f7e5461b02e4176b',
    'scripts/friday_start.py':'19547c818e52ead58e824baf3e115f4b8fa1fdc07f5e938dbe7198a8dde47406',
    'scripts/friday_native.py':'ef647de600903e70feb3ec4a3b4d907e1c6907843f737de1519ba5e7b35b43f4',
}


# Exact current198 DSH project-only successor. Native layers and receipt are retained.
PROJECT_DSH_CURRENT_SCHEMA = 'friday.ordinary-telegram-project-update.v6'
PROJECT_DSH_CURRENT_DELTA_SCHEMA = 'friday.dsh-current-project-reviewed-delta.v1'
PROJECT_DSH_CURRENT_INPUT = 'dfc6fd4a552d9088887746c7329febcf1f4b152f01c81841cd2bb36241a891df'
PROJECT_DSH_CURRENT_INVENTORY = '4badb3bb935877a7f41d3b3b30a6f25ca070126cd698008c21df83e1be8165f1'
PROJECT_DSH_CURRENT_RECEIPT = 'ace1b232a41736589c0185821003a74b0502e5aeda5c3ca21bdff39d232b989f'
PROJECT_DSH_CURRENT_STAMP = '94197aeda7061c67ac163e93e2ba920ae71504bd29c6a0188f3af99e8919f911'
PROJECT_DSH_CURRENT_ANCESTOR = {
    'request':'e4ba5af4591331bd65a699b139a5e39dad91e61813b67502dfd656a9cabd85c5',
    'intent':'a37eeb484a99670aeb86e512bbffb5716d0837b3a599450ff483748e850c5696',
    'committed':'6c7b2c048e4eb347c11ca3046e5af06871a5c0adbda34eea3e5767f84e85f8fd',
}
PROJECT_DSH_CURRENT_HELPER = 'scripts/friday_ordinary_install.py'
PROJECT_DSH_CURRENT_ADDITION = 'plugins/friday_rework/dsh_current_availability.py'
PROJECT_DSH_CURRENT_REQUIRED = frozenset('plugins/friday_rework/'+name for name in (
    'host_runtime.py','runtime_observers.py','stopped_operator.py','user_worker_join.py',
    'worker_declaration_writer.py','worker_declarations.py','worker_web.py'))
PROJECT_DSH_CURRENT_OPTIONAL = frozenset({'plugins/friday_rework/adapters/dsh.py'})


PROJECT_DSH_CURRENT_HELPERS = frozenset({PROJECT_DSH_CURRENT_HELPER,'scripts/friday_install.py'})
PROJECT_DSH_CURRENT_REQUEST_FIELDS = frozenset({'schema','seconds','home','previous_input','current_input',
    'marker','source_receipt','stamp','configuration','profile','launcher','credential_files','native_unit',
    'transaction_history','predecessor_update','publication_ancestor','reviewed_delta'})


def project_current_request_metadata(request):
    """The immutable typed request, without reopening its mutable before pins."""
    f = api()
    f.require(type(request) is dict and set(request) == PROJECT_DSH_CURRENT_REQUEST_FIELDS
        and request['schema'] == PROJECT_DSH_CURRENT_SCHEMA
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 7200,
        'ordinary_project_current198_explicit_request_required')


# At most thirteen authenticated native CP edges after the current198 project transaction.
# Neither a future request digest nor a future input digest is compiled here.
CURRENT_SOURCE_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v1'
CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v2'
CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v3'
CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v4'
CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v5'
CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v6'
CURRENT_SOURCE_NINETEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v19'
CURRENT_SOURCE_NINETEENTH_LAYER = 'ordinary-document-owner-through-attachments-after-source216'
CURRENT_SOURCE_NINETEENTH_MANIFEST = 'c0f7467d2b7d47e30f7681714b6ee10a3f44a4446acc5f816d77b40a70051d09'
CURRENT_SOURCE_NINETEENTH_PATCH = 'e8cca9c167082041417a4fa8b97aad0bc716c3a712f71337a4e1ec50e93b31f2'
CURRENT_SOURCE_NINETEENTH_NATIVE = {'gateway/platforms/base.py': ('ac41d4600cc6ec19c7509ecd81eadd3cbdd7dccfbbc0d7fcf548efca0131e264', '1f71f364a5f50290022b7f02d2edad4fda7821e0c48adbe253188bdb0d7fb8ef', 290853, False), 'gateway/run_plugin_delivery.py': ('264451c7ff2338ad8d7f0d2e6054af0668d2b8b9b11177a889471b3d075a2f9b', '0af4c99b9357b8865509202305129a43957c176ac1c041b9642b9cbd7611b674', 31348, False)}
CURRENT_SOURCE_NINETEENTH_PREVIOUS_REQUEST = '8af4e67455d319628f53f7565dd70c7eee1fd29108724e18ecdb3154a4bd63e1'
CURRENT_SOURCE_NINETEENTH_PREVIOUS_INPUT = '74b811ff168e1c388997cac561da76adc5c44485eb1f56b8ce7b5e5baf1c2525'
CURRENT_SOURCE_NINETEENTH_PREVIOUS_RECEIPT = '0414cf2a6e88c8481f83780aaef119efbe985220f37e9ace86f66da7e570fe7b'
CURRENT_SOURCE_NINETEENTH_PREVIOUS_STAMP = '7d38171f02d7bdb26c7d83c7411a482d3de9fdebfd992d679879e787f372d1df'
CURRENT_SOURCE_NINETEENTH_PREVIOUS_INTENT = 'ed79ecc05c39b768efc332730fb929c6d078727a4dba021efaa223bbdfb370c5'
CURRENT_SOURCE_NINETEENTH_PREVIOUS_COMMITTED = '726e271a6cff2c9bf0d9214d874e6e0908336193ef48372007b98630b89ded7c'
CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v18'
CURRENT_SOURCE_EIGHTEENTH_LAYER = 'm09-real-web-custody-receipt-after-source215'
CURRENT_SOURCE_EIGHTEENTH_MANIFEST = 'd8acb493ea7496e6c111254860a2bea4be6ed28f7f457c39acd01c9e1571c53d'
CURRENT_SOURCE_EIGHTEENTH_PATCH = '1e211f290d150c479894b0e3b4d9339fe999846e6924e429f9412a7c7fb619bd'
CURRENT_SOURCE_EIGHTEENTH_NATIVE = {'gateway/ordinary_turn_projection.py': ('ab51a86a42938b4d7ad012d7c196b290acfdccd62b2b1aa58127b98e09d254a0', 'ac0c1ed4b53f6ebebfab9ceadfc74e14e553a8f74e59df10a5813fae850c76c7', 40726, False)}
CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_REQUEST = '5c59a24e0075adf7b78571da9c5b8b7a411bde2ad1c46e72a0a0b2a663d9e6bd'
CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_INPUT = '30f92544d3b55451c82f21e36db8a54b43316de6144babc328bf33a783fcdf89'
CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_RECEIPT = '527004bcf620c5f9873df0e7dda2c4af94f5008209b748e737e25af1f4d59177'
CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_STAMP = '6c8cc9ef2068e14e97ee0293ec2d4137b2a20977c486e603655696cb9c9a2749'
CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_INTENT = '5d4b9bc99c74bc3ac99ce7270c6f578f266c5fd5ec9426850d18196601230f7b'
CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_COMMITTED = 'f65f2ff8f8bb321c46a6af8a3bbad14925641840a82837d6be1ad957081059e6'
CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v17'
CURRENT_SOURCE_SEVENTEENTH_LAYER = 'word-fidelity-and-docx-copy-after-source214'
CURRENT_SOURCE_SEVENTEENTH_MANIFEST = 'b274e734cadc84e9cd32de90cde8f2d01fca6b1ef6c0bd54adb8bbf071b41976'
CURRENT_SOURCE_SEVENTEENTH_PATCH = 'e2373943119b000928a35ae6dba58d312717b2f941ff23b8d7bde505702c91f1'
CURRENT_SOURCE_SEVENTEENTH_NATIVE = {'tools/scoped_word_conversion.py': ('62c61f166b10a4ef2ff6b903ad7e00c95a0814adf84d68050221e4882b2ccf8b', 'f7209b8e4e92cf0b50c3cc515797c35c62a34c42fe3a8ae5d95f0578a5f91584', 116377, False), 'hermes_cli/friday_workspace_word_conversion.py': ('60eb4e71cca35edf1424d34189896049d100c5d214d78e02a807934f47d16a76', 'cb2ba1c7cf8ac34f816bfca012e918acbee5ca06050fed26885100cfd8fcc8bd', 11337, False), 'hermes_cli/friday_prompt_scope.py': ('c51ac7998ec909a67283fb0d164cac91ea3f28a7e819600c025d03ad3488d450', 'abd8bd67bd762b75f63fd9e8956f76a65496f91eca9e165a99581e7e718e2c13', 135391, False), 'hermes_cli/friday_user_scope.py': ('dc8ea5271f0937915fbf8cd0e39f74bd240e8f7d289d4a15e4f4062a7bf50d4a', 'abad3f299d1099914455781176ac0a3e09b4d40d4a2afd14b342dcb990087dba', 149634, False), 'hermes_cli/friday_workspace_docx.py': ('197c5ebdc0a86d5641f7b150c63d09d28c3e5ad5fd936e51e556262ac2ced926', '289bab471507b7477afc4c95cde7a878199d9e74a1d1c528d80f5d371b985608', 37901, False), 'tools/file_tools.py': ('b834615c95438c2f1cb725247cc2ea0b6e1d5e1566cc3498fec2a069bc21a40f', '246bb05029881a002db7374f4452b0f196a8e56e2ca1cd5a63423fda532ad42f', 186098, False)}
CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_REQUEST = '783baae6d27e5c70f39f1f9f3328cb9467673f207bd26947ea3fb531d9a1e6cc'
CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_INPUT = 'e0ff7f39553d7bfdb94e5f89959f6503a5f98dd61828aa56237a842f982b549c'
CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_RECEIPT = '2fa2a5ac879175be9c516254240ab2572438634df2969729812152f840cb3ce9'
CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_STAMP = '520508bd5fdebe6c9acfb5b22d36b4c7d688b2f118cc23eb6e7fd5ca271ad17d'
CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_INTENT = 'b38bf0c927991be95c67887cfa109184fd26d2e235df64c21fc848075dfd90b0'
CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_COMMITTED = 'd70d9b2d53430a62e309cd988a5f856aab323b31c61b7b94934337591def5825'
CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v16'
CURRENT_SOURCE_SIXTEENTH_LAYER = 'm09-retained-projection-bridge-after-source213'
CURRENT_SOURCE_SIXTEENTH_MANIFEST = '157c8e3914a9d372984a27e87525252140f44bb4cae8671dc05629565a0088de'
CURRENT_SOURCE_SIXTEENTH_PATCH = '03a7d1f5194f5cfe2dde5a539eea3fd2fe63148bfd9b79ca3f34ef0936ccab77'
CURRENT_SOURCE_SIXTEENTH_NATIVE = {'gateway/ordinary_turn_projection.py': ('a9cb03130c2893b1c9f6083dcad9f38a22a0e3540ab7c4fe47e9bfa0270b64aa', 'ab51a86a42938b4d7ad012d7c196b290acfdccd62b2b1aa58127b98e09d254a0', 40715, False)}
CURRENT_SOURCE_SIXTEENTH_PREVIOUS_REQUEST = '495bb24e41f26fb212ca5d8a62e41056b8131affdf133b7c14f511f91e6733f0'
CURRENT_SOURCE_SIXTEENTH_PREVIOUS_INPUT = '5ed3a806952004a7e8c648f571610e30ef71790207ab7698cc7d64fc2e1c6bd1'
CURRENT_SOURCE_SIXTEENTH_PREVIOUS_RECEIPT = 'f13cbbd8b49c97f04719140d778915811d6f89c0558e212d3f5478ffbd74a971'
CURRENT_SOURCE_SIXTEENTH_PREVIOUS_STAMP = 'b0c625f21c0432cc27191025e7ba70c9714ca630841faeb3f92ddeb5e63b20ad'
CURRENT_SOURCE_SIXTEENTH_PREVIOUS_INTENT = '45705190a4b4fcaa6f0295a8b826d242417e33b2024f6295415171f723397c2b'
CURRENT_SOURCE_SIXTEENTH_PREVIOUS_COMMITTED = '081591fd5fc4a4b8f1234550104b3065d8ad8bbeeabaaa23c635ea53833318de'
CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v15'
CURRENT_SOURCE_FIFTEENTH_LAYER = 'r02-managed-file-output-phase-after-source212'
CURRENT_SOURCE_FIFTEENTH_MANIFEST = 'd1493fb9b3bbda66b4c530ea58bddc0e226cb531dd03eee3ee7c8e5e3cf06f57'
CURRENT_SOURCE_FIFTEENTH_PATCH = '04dabd4c2f9533cf3edf0d0c25de1dc49c99306946d7083c01c09ccfbd6f9cd4'
CURRENT_SOURCE_FIFTEENTH_NATIVE = {'gateway/run_plugin_delivery.py': ('747f75f4e0d3975264ff19841f2d398ac41af9bf1e8aabaf0a68b9c8b38f3b42', '264451c7ff2338ad8d7f0d2e6054af0668d2b8b9b11177a889471b3d075a2f9b', 30253, False), 'gateway/run_startup.py': ('9b196ee9d72de6dd8ace584df7868e25bf50e88117e829d0cf81929cfa0d065d', '20d85f2e8a99a635ab4dd7db692bef16ec0b3727bd7028d93a704da03f2c55a8', 138601, False), 'gateway/run_turn.py': ('c041af5cdfb0cca26b7ee31ae97651f72d4418950b942288a57857a260937699', '215d2410bc986a0f327afb3b2ad46bfee298a2b53a68021e9b9a6cd2110f83c8', 271189, False), 'gateway/session_lifecycle.py': ('a38fd4b17e204795fb3bb912d7a5b9ac17f7223779e14c977bab8de729907968', 'aa541351d555fb11708e2ff55fde72d5231018075c1f659de41d997c8f235025', 24752, False)}
CURRENT_SOURCE_FIFTEENTH_PREVIOUS_REQUEST = 'c8354b3e9e42d8d241e41d185db33236a335b65e62f2e1259b20b169278c7fd3'
CURRENT_SOURCE_FIFTEENTH_PREVIOUS_INPUT = 'ab3206bb9d5a50a5f6ed5d89e4587d02b758db35dc24df1eecb4f9e093516aa6'
CURRENT_SOURCE_FIFTEENTH_PREVIOUS_RECEIPT = 'aac131f1e67200944574984c52369c65434b62e2e35ee16ae0f7f58cf0ba7872'
CURRENT_SOURCE_FIFTEENTH_PREVIOUS_STAMP = 'd0bc6a0b81f725a35c1987960ef8059aa1da9e72923c4c0dc738aa6a09ca7608'
CURRENT_SOURCE_FIFTEENTH_PREVIOUS_INTENT = 'b4ba19032954ae6e5a9ad204cde61235eb5d1cb97d0cb1637dfe42fc582ac917'
CURRENT_SOURCE_FIFTEENTH_PREVIOUS_COMMITTED = '44d25d6d1d3076f2b4d3c6ade4f519d257b35db5db623bef47a45134cddc126e'
CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v14'
CURRENT_SOURCE_FOURTEENTH_LAYER = 'r02-boot-sweep-observation-after-source211'
CURRENT_SOURCE_FOURTEENTH_MANIFEST = '043da4ed0422dae2b7acb0331607426e74fb17175c3e7b8b2d93ad96640b2958'
CURRENT_SOURCE_FOURTEENTH_PATCH = 'c6dd8b0496883a0ebb421dd65e5bff3f0f4e6cb97bc0de631c54eca6ffa55f71'
CURRENT_SOURCE_FOURTEENTH_NATIVE = {'gateway/run_startup.py': ('d2c7047f77ba829ab416a985e12745dca9ea7d768741ca3316a5e1ad9a6b73a1', '9b196ee9d72de6dd8ace584df7868e25bf50e88117e829d0cf81929cfa0d065d', 137854, False), 'gateway/ordinary_turn_projection.py': ('3a6b003622bc17ff5265e5c5117e0eb1f4572676d967763cb368e80947fc79b4', 'a9cb03130c2893b1c9f6083dcad9f38a22a0e3540ab7c4fe47e9bfa0270b64aa', 23953, False)}
CURRENT_SOURCE_FOURTEENTH_PREVIOUS_REQUEST = 'f44e796e9b62566ed95ff5e73546ad32132e671b8c045a8aab2c74a29d965aee'
CURRENT_SOURCE_FOURTEENTH_PREVIOUS_INPUT = '6b8bbd7719a6e09ece57ba122c4083598d78f3d03dc1c96178d770599dfcb5bd'
CURRENT_SOURCE_FOURTEENTH_PREVIOUS_RECEIPT = '1901e38b880b77394cd313a049f1b6918d87f47a51df1fbc23315d5780a7706a'
CURRENT_SOURCE_FOURTEENTH_PREVIOUS_STAMP = '7bc1c07bb19f4b856bca318cf8cc919862b0f23a1239126c6bec345287f3682a'
CURRENT_SOURCE_FOURTEENTH_PREVIOUS_INTENT = '54395ac28fe332b11d0e068f65281b0fa74532a90b119f4e213cf6a4e94e3f61'
CURRENT_SOURCE_FOURTEENTH_PREVIOUS_COMMITTED = 'ea7761c977759426597facf47988bd9ccd0bd62a41c7abbefae29bd6eec67120'
CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v13'
CURRENT_SOURCE_THIRTEENTH_LAYER = 'r02-telegram-text-uncertain-recovery-after-source210'
CURRENT_SOURCE_THIRTEENTH_MANIFEST = '082eec729d3006543784e3e882266409161930e514ee3bcc75460959e5ddff7c'
CURRENT_SOURCE_THIRTEENTH_PATCH = 'f95ea4ba023aff1cc43d66f5417fbbdcfbe3cd0dc15150faeeb526a59ba176c6'
CURRENT_SOURCE_THIRTEENTH_NATIVE = {'gateway/delivery_ledger.py': ('5633890ac93523cb902fcb9f50749f1b66e0f946404ddb9bc26e4ae5f9550451', 'e23e14be70e98c819df3e235462623bee779976cc2eb5ab999b424e5d6c0e032', 37685, False), 'gateway/platforms/base.py': ('a61dde52dbab739607744b870f67af3d618392921ab15a48a813ebf62111d6c4', 'ac41d4600cc6ec19c7509ecd81eadd3cbdd7dccfbbc0d7fcf548efca0131e264', 290112, False), 'gateway/run_startup.py': ('e2ac69d6e7da2a342943f5658ad4bd0496ac1edb70127a13d8dbcbb59b2ec2fa', 'd2c7047f77ba829ab416a985e12745dca9ea7d768741ca3316a5e1ad9a6b73a1', 131171, False), 'plugins/platforms/telegram/adapter.py': ('266406a68f3eb7d60087bc6c45e11432ccd9d567b39dd046463ca503cceb1952', 'd0e6e3b9008aa05b8990146e2ec58cd8c9c2d6e8d0e7e210678138f499c1ec18', 433586, False)}
CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v12'
CURRENT_SOURCE_TWELFTH_LAYER = 'f07-malformed-docx-error-provenance-after-source209'
CURRENT_SOURCE_TWELFTH_MANIFEST = 'deb27efa37c5ea61e5df0f886c6cade19f78642ac07291be123372e29b8ceaa4'
CURRENT_SOURCE_TWELFTH_PATCH = '8d4ef6bc9506e790e1d203682e591495a6d9cb2d03830de6c71885380390bc88'
CURRENT_SOURCE_TWELFTH_NATIVE = {'hermes_cli/friday_user_scope.py': ('3dff39b51c8da112339ad5e2f5065a332fe102877303bf442a57624f07404474', 'dc8ea5271f0937915fbf8cd0e39f74bd240e8f7d289d4a15e4f4062a7bf50d4a', 148946, False)}
CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v11'
CURRENT_SOURCE_ELEVENTH_LAYER = 'f07-bounded-docx-structure-after-source208'
CURRENT_SOURCE_ELEVENTH_MANIFEST = '38368327c4dcfc6a11f2c823f45bffe9c45b32bc145f5251d17d56b7d106b787'
CURRENT_SOURCE_ELEVENTH_PATCH = 'd331b386ea71c07865bc481127140f82ce063aade6fb5d9985bf1af8d6762947'
CURRENT_SOURCE_ELEVENTH_NATIVE = {'hermes_cli/friday_workspace_revision.py': ('2705e4175e80bb809c640b8d0f9aa00b78d43dfddd83b7cfe63dd57f3f048f0e', 'a84959c7ddc6fec3a028e5b67b4af64b7ee5d7f462776b9a59150a1891b10dc4', 17901, False), 'hermes_cli/friday_user_scope.py': ('fb45b65f899a7c1561156b53fa167f309e48445b9ea00a14f8ed90d002b07dad', '3dff39b51c8da112339ad5e2f5065a332fe102877303bf442a57624f07404474', 147946, False)}
CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v10'
CURRENT_SOURCE_TENTH_LAYER = 'inbound-turn-log-metadata-after-source207'
CURRENT_SOURCE_TENTH_MANIFEST = '742d2a1b8f3de54e647ee17a607910480bac49685026173c9c368236b03b4db4'
CURRENT_SOURCE_TENTH_PATCH = '2045aa2d0603a63c0cc5eeb72fbb4bdaab907d18ee521e6b383cf0948f851f7f'
CURRENT_SOURCE_TENTH_NATIVE = {'gateway/run_turn.py': ('a2d166316f286b540281b8b87c850d3765bc0a780d14d745f6ccef7ba4ec086b', 'c041af5cdfb0cca26b7ee31ae97651f72d4418950b942288a57857a260937699', 270020, False), 'agent/turn_context.py': ('9bfb5c11c1555bcff33de007e8baa2793fdc8d0afc38eeae06dc520ae14d7a7d', 'ab921e236f6b7c9c9cfd721abb6ad6f18aed2b71333bcaa9daf0f00c8a5ab2cd', 71855, False)}
CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v9'
CURRENT_SOURCE_NINTH_LAYER = 'f06-modern-odt-authenticated-profile-after-source206'
CURRENT_SOURCE_NINTH_MANIFEST = '76121597cdc8a366239ba5f9ad1c58b434943e267bfe72a2faf6525ba3d6237e'
CURRENT_SOURCE_NINTH_PATCH = 'fb80e67986642c3ae9b830ebc66f2815396575463400d65a7c65c6a41f9aa4b8'
CURRENT_SOURCE_NINTH_NATIVE = {'tools/scoped_odf_password.py': ('ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae', 'b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d', 28189, False)}
CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v8'
CURRENT_SOURCE_EIGHTH_LAYER = 'f06-protected-office-profiles-after-source205'
CURRENT_SOURCE_EIGHTH_MANIFEST = '6cdf8c728aec40260a2a9c1dd93795f136726437a1564b0618aa1a65b6a48300'
CURRENT_SOURCE_EIGHTH_PATCH = '955e95163fb6c745ca135180666d7f5c78f5d023ea0ea2a264ce30cc89504147'
CURRENT_SOURCE_EIGHTH_NATIVE = {'agent/agent_runtime_helpers.py': ('231eaa550cf8b4a37c9ffe0144ccfeefe78fd35d38ae1d921b347fbb5fbef33d', 'b3a71476ab48aecb4b4fe7058c2a7626c769b01a919c50c9f5935e96b67da39e', 214434, False), 'agent/display.py': ('285d29e0c18b002d6b4f65b85dca0a4dde5b1c4178f2f7d1d2ad55db0a02abe7', '9e0b8e2721260f513031194b04e86da3c57c118b3543850abe3658cf00126aec', 59626, False), 'agent/message_sanitization.py': ('840e1380bc18a7c6697099c5f1bb3805002230c81e0fbf9e1b0dedbd614d75fa', '08823b1e54f6aa78f49ebf1f0f92092f9c558bd982c3961ef9ed8cd99642f5ec', 45728, False), 'agent/session_persistence.py': ('7058ac00f9414aa373719de7831b007686a0844d109c7f006c6c970b107f9892', 'de1049ed9adc152c38349e6942edf79f3ef1778e2353a9dc3a68f793716e5006', 35304, False), 'hermes_cli/friday_prompt_scope.py': ('beea2a674906f3d9fa6e4972a3f8dcd3593d8f29eb6a0d2cfaafdeba959788c5', 'c51ac7998ec909a67283fb0d164cac91ea3f28a7e819600c025d03ad3488d450', 134183, False), 'hermes_cli/friday_workspace_ooxml_password.py': ('dc73d0a076607ef20548ec00b8da8eb51ec142d007fb55f2bdb5012b7fbab1e1', '0be85ff3458cd47ffd9818a4f4791b0b9f67bfd4131e6fe9b688c23fe4619d86', 12184, False), 'hermes_state_messages.py': ('a3b5b9775799c3e4f6c2621dfcfcaa4cd1358274b2b358d67db7742facc5a664', 'a4ae3e55ffe47bc2029e816bd52c77f075319d0fd2eb05714fcdfc7b3dd0f529', 131465, False), 'tools/file_tools.py': ('4caa0e0dd1fbbca918b89b6d489f1463b57dc463d9ee1581cf1f875533b06834', 'b834615c95438c2f1cb725247cc2ea0b6e1d5e1566cc3498fec2a069bc21a40f', 184031, False), 'tools/scoped_odf_password.py': ('19e7369a1473a6c33c9e96467e06ed98941dbd434b7ecaf5c88e699ef799214d', 'ea59d8aa1225ea1ef25227b8a65cb94fcabef5932d90d2ad901ab0cfbd98b1ae', 22607, False), 'tools/scoped_ooxml_password.py': ('526661f867116d07d04e84c0d71afcbfee6646c7efe6d048a83cb3acba9855b5', '59c65471582a30baf61ed8367925b477d00af70d6d1211e6044ecb2a3d35029c', 30958, False), 'tools/scoped_ooxml_password_edit.py': ('350e613e407107297ffe36eaad33b94e1f990a5cf8b3128fea9c8a708065998b', 'e5c9588cd5e22590809cb1231affa72238435c98c43429041d6b37c5761f3ca4', 12308, False)}
CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA = 'friday.current-source-native-successor.v7'
CURRENT_SOURCE_SEVENTH_LAYER = 'core-user-result-contracts-after-source204'
CURRENT_SOURCE_SEVENTH_MANIFEST = '8b5f13c1eda87bb778feab789abf06beea3bdf3c185bdbe30a61a5749fd777b4'
CURRENT_SOURCE_SEVENTH_PATCH = '87655a477c642da1a897c3abcde77200c51c1b59932224cf6d59fdf2c31f3087'
CURRENT_SOURCE_SEVENTH_NATIVE = {'gateway/run_attachment_presentation.py': ('a677721a1fc68ab4a215c5065b40b54a4ead3cfd6f70c4b9156035891cfbcbbd', '51439ea9a9d2986865b213e2417292de9c2d3971f79f60bccbfa7756d8f52843', 12156, False), 'hermes_cli/friday_prompt_scope.py': ('4b7131d965e56f8606ab8866a781ac99a2e0694cb2ca588e6c911aa793f5c99a', 'beea2a674906f3d9fa6e4972a3f8dcd3593d8f29eb6a0d2cfaafdeba959788c5', 133907, False), 'hermes_cli/friday_workspace_presentation.py': ('2f6417738f5c441d3b6332a10886156c5218f24b3755014c8af59e7b2dc8dd21', '0526a026e0a4b9c37d5d62d10c82d53fbab39c08c7ce2587e4c2a89192945d1d', 23177, False), 'tools/session_search_tool.py': ('984cece35ed2f91c33f13b6ec7d691bae58a7ac0a6607b75c21ec5822ebe8b7f', '64f56b0b33065c8622cd69c0e9a61c8ec539d940c6556aad834c93c6925a549c', 56710, False)}
CURRENT_SOURCE_SIXTH_LAYER = 'rtf-optional-footnote-reader-after-source203'
CURRENT_SOURCE_SIXTH_MANIFEST = '0cef90c50fa23afe9c73ad880680f5b74956126b4b6f79affdaa6dee4234581d'
CURRENT_SOURCE_SIXTH_PATCH = '8eeff0c650b66c5e32833ecca6c688616305d8add3feffbf00eb9f1d2f9e0027'
CURRENT_SOURCE_SIXTH_NATIVE = {
    'tools/scoped_rtf.py':('cf652ee67d08de6349900a81b84ccbd8ab0ce3a3253f91c6460c066dabff3af5',
        '7f1c0edfd9728fc0c4aa10b7f025a9ce10a24bfd4a76e11205cbbe777c085cdf', 37980, False),
}
CURRENT_SOURCE_FIFTH_LAYER = 'core-file-readability-and-context-provenance-after-source202'
CURRENT_SOURCE_FIFTH_MANIFEST = '8f63631f8878a04a5c770cc1a3aed43b95834d556e5848d290a4ad6713013c9d'
CURRENT_SOURCE_FIFTH_PATCH = '8fe15b5e569ba7e249845aa47577d36f0bc67a8d76f1f117205a79f6f6911abb'
CURRENT_SOURCE_FIFTH_NATIVE = {'agent/context_compressor.py': ('c1b05056bdb0f80b1783c37ed3c1f2290dff3a5b8688d7a8fd99570ae6f3cdf7', '7a52317724a0a9885c591e042a45dfc263e3f865da22dfbaa911bb5a4b928766', 357149, False), 'hermes_cli/friday_prompt_scope.py': ('d6ccec1324270283ad5484787c481637c93a1be214281362349644acbcc3388b', '4b7131d965e56f8606ab8866a781ac99a2e0694cb2ca588e6c911aa793f5c99a', 133797, False), 'hermes_cli/friday_workspace_presentation_text.py': ('ebeebc571d22bc6bd230bc3e8deb51edb5413c3b88d78e13d3259be69765235e', '87c1098cd85fb4664bc7fe99b44a63837834c1e20f69705c2eb3f69256208960', 2386, False), 'tools/file_tools.py': ('ac1b3388815a1f9006a74ea7684ec15b85bdda5c820a71b50cde3e4eeb02ce68', '4caa0e0dd1fbbca918b89b6d489f1463b57dc463d9ee1581cf1f875533b06834', 183634, False), 'tools/scoped_presentation_layout.py': (None, '859330233dbe4409f57f61f6540e2c6c2cdb7386f513788bf4e21ed8ca21bd4b', 25616, True), 'tools/scoped_presentation_text.py': ('528e5a469c69dc6d17fdb452d2ecbea2b4ff63e27aa1c51514d7462b483595a9', '00a76eec63b9259f94791ef5c83b7adbdd6dc65f0ebf4db80508650ee24fe6bc', 14030, False), 'tools/scoped_presentation_write.py': ('07b8fb513cf90d862d1504574bd2a4b862da243b33fa9dc549c3634cd242ab8d', '5816edf6d919d0a5fe85de3abc09211831a496cf6462a3dfbc46060fe7350153', 77065, False)}
CURRENT_SOURCE_FOURTH_LAYER = 'rtf-rich-odp-followup-and-office-bank-after-source201'
CURRENT_SOURCE_FOURTH_MANIFEST = '38d600d2cdb4d2d6881845430e8dd4232e18ff09c12ba4f3ea44d82aba62e6f3'
CURRENT_SOURCE_FOURTH_PATCH = 'd0a1358735c64c17bd3a4d1da5ee9874a969620db927131c215eb1530fc0367a'
CURRENT_SOURCE_FOURTH_NATIVE = {
    'hermes_cli/friday_prompt_scope.py':('0b7d416d12f1d3a6aea12f40ae45e290721004b179af59cd017cd4e25c7761db', 'd6ccec1324270283ad5484787c481637c93a1be214281362349644acbcc3388b', 133170, False),
    'hermes_cli/friday_workspace_pdf.py':('b86a67b5e2aa109c79f9bed06d409a180e6ecff869b6979a348ae1d0ae205015', '71b27cee76d8b927bfad064ea8b79a4da7c2791357ab2a82c747e453e7ad03b5', 15861, False),
    'hermes_cli/friday_workspace_presentation.py':('bec6d1f450e6e09d044d456e026e14061c182787898793615ad0d99d893a3c15', '2f6417738f5c441d3b6332a10886156c5218f24b3755014c8af59e7b2dc8dd21', 22441, False),
    'tools/file_tools.py':('760a49c482e3e9febe18712ab96ab7ef8f6fafbc90881bd4e41e10090808237a', 'ac1b3388815a1f9006a74ea7684ec15b85bdda5c820a71b50cde3e4eeb02ce68', 183000, False),
    'tools/read_extract.py':('6f9cb4be488308ec5055fd27ffe624e9190adcd317d45282384d26a2e1e247f4', '8f3ad405263470eac948a9f14fa6c0af18144697cf5244c6c8c8a4f7d543b339', 74912, False),
    'tools/scoped_presentation_generated_odp.py':(None, 'f6bd93e88eb0d3049d89773c4b0e9f97f7547fcbc0f761ca3867b7114f0f1ca5', 11547, True),
    'tools/scoped_presentation_odp_text_source.py':(None, 'd3f5d04456281e33df9fc5a6e4a2e13243a6c7805aa0d16ed373decc86c322a2', 4428, True),
    'tools/scoped_presentation_text.py':('0893b1b22807a418618203dabd01a1bdc75f314930b4e389c176657af78bb9cf', '528e5a469c69dc6d17fdb452d2ecbea2b4ff63e27aa1c51514d7462b483595a9', 13270, False),
    'tools/scoped_presentation_write.py':('f0138465ce1c2f0a9585d60f9a11b3020e93658ce1eb2f12c85cfbd48eb58842', '07b8fb513cf90d862d1504574bd2a4b862da243b33fa9dc549c3634cd242ab8d', 71590, False),
    'tools/scoped_rtf.py':('ca17634765beb5210181ec5808d997150dcbcefad947b3d8d9a7c13f67e3d6dc', 'cf652ee67d08de6349900a81b84ccbd8ab0ce3a3253f91c6460c066dabff3af5', 37835, False),
}
CURRENT_SOURCE_THIRD_LAYER = 'retained-calc-xlsx-destination-after-source200'
CURRENT_SOURCE_THIRD_MANIFEST = 'd9fec39ff5985fe0ccfcd3dd1cf4cfc8087b35f8d1994320cd1e40075589a185'
CURRENT_SOURCE_THIRD_PATCH = '5b6a8ab625ad38f443ef13d4659b682ad25ea33d30db21b1060a30c49acb97e5'
CURRENT_SOURCE_THIRD_NATIVE = {
    'tools/scoped_spreadsheet_conversion.py':('2b87906e30a590ec1e145edeb50e841d0161519147fe12a4069fe246bc2be040',
        'a33795729bcb75e87fd2f7f6b0629c18c40fbbf0398cb5bb8753a58b393fc5eb'),
}
CURRENT_SOURCE_SECOND_LAYER = 'ods-calc-retained-source-profile-after-source199'
CURRENT_SOURCE_SECOND_NATIVE = {
    'tools/scoped_ods.py':('25569a964ee65dbe7ea7ee7dabbfa199c503b039725451e13e479cbd32b66df7',
        'f31e03b82395e8fc6fb873d2b080e252de4912a2fa9562a61ad6b3f262411cc5'),
    'tools/scoped_spreadsheet_conversion.py':('2afbe63a166449e6b8acc0b907def046f01735b6c7690c9facbeba92958b9d03',
        '2b87906e30a590ec1e145edeb50e841d0161519147fe12a4069fe246bc2be040'),
}
CURRENT_SOURCE_CP_FIELDS = frozenset({'schema','seconds','home','previous_input','current_input',
    'candidate_input','candidate_project','marker','source_receipt','target_receipt','stamp',
    'configuration','profile','launcher','native_unit','transaction_history','predecessor_request',
    'predecessor_current_input_sha256','predecessor_receipt_sha256','installed_layers','installed_files',
    'project_inventory','project_inventory_sha256','layer_names','layer_manifest_updates',
    'project_file_updates','plugin_set','plugin_additions','staged_files','current_source_successor'})
CURRENT_SOURCE_CP_INTENT_FIELDS = frozenset({'schema','state','request_sha256','request_reference',
    'current_source_successor','home','previous_input','current_input','source_receipt','layers','files',
    'plugin_set','plugin_additions','project_file_updates','metadata','gateway_started','workers_enabled'})
CURRENT_SOURCE_CP_COMMIT_FIELDS = frozenset({'schema','state','request_sha256','request_reference',
    'current_source_successor','previous_input','current_input','predecessor_request_sha256',
    'predecessor_receipt_sha256','source_receipt_sha256','layers','files','gateway_started','workers_enabled','seconds'})


def _current_source_json(path, *, private=True):
    """All new continuity JSON is duplicate-free, finite and size bounded."""
    f = api(); raw = f.owned_file(path,private=private)
    f.require(len(raw) <= 16 * 1024**2,'ordinary_current_successor_document_too_large')
    def nonfinite(_):
        f.require(False,'ordinary_current_successor_nonfinite_json')
    def finite_float(text):
        value = float(text)
        f.require(__import__('math').isfinite(value),'ordinary_current_successor_nonfinite_json')
        return value
    return json.loads(raw,object_pairs_hook=f.unique,parse_constant=nonfinite,parse_float=finite_float)


def _current_source_reference(ref):
    f = api()
    f.require(type(ref) is dict and set(ref) == {'path','sha256'}
        and type(ref['path']) is str and type(ref['sha256']) is str
        and len(ref['sha256']) == 64 and all(c in '0123456789abcdef' for c in ref['sha256']),
        'ordinary_current_successor_exact_reference_required')
    return f.pin(ref)


def _project_current_root_checked(home, reference):
    """Authenticate v6 evidence, without reopening ancestral mutable/source pins."""
    f = api(); tx = f.directory(home/'preparation'/('ordinary-source-update-'+PROJECT_DSH_CURRENT_INPUT))
    f.require(not os.path.lexists(tx/'rolled-back.json'),'ordinary_project_current_source_rolled_back')
    intent = _current_source_json(tx/'intent.json'); committed = _current_source_json(tx/'committed.json')
    intent_fields = {'schema','state','project_only','native_source_unchanged','request_reference',
        'request_sha256','seconds','previous_input','current_input','publication_ancestor','reviewed_delta',
        'gateway_started','workers_enabled','before'}
    commit_fields = {'schema','state','project_only','native_source_unchanged','request_reference',
        'request_sha256','previous_input','current_input','source_receipt_sha256','gateway_started','workers_enabled'}
    f.require(type(intent) is dict and set(intent) == intent_fields
        and type(committed) is dict and set(committed) == commit_fields
        and intent['state'] == 'SOURCE_UPDATE_CONSUMED_NO_RETRY'
        and committed['state'] == 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
        and all(body['schema'] == 'friday.ordinary-telegram-source-update-transaction.v1'
            and body['project_only'] is True and body['native_source_unchanged'] is True
            and body['gateway_started'] is False and body['workers_enabled'] is False
            for body in (intent,committed)), 'ordinary_project_current_source_committed_proof_required')
    request_ref = intent['request_reference']
    _current_source_reference(request_ref)
    f.require(encoded(reference) == encoded(request_ref) == encoded(committed['request_reference'])
        and intent['request_sha256'] == committed['request_sha256'] == request_ref.get('sha256'),
        'ordinary_current_successor_root_request_changed')
    request = _current_source_json(_current_source_reference(request_ref))
    project_current_request_metadata(request)
    f.require(request['home'] == str(home),'ordinary_project_current_source_home_changed')
    previous = _current_source_json(_current_source_reference(request['previous_input']))
    current = _current_source_json(_current_source_reference(request['current_input']))
    plugins = project_current_delta(request,previous,current,check_origin=False)
    f.require(current.get('home') == str(home)
        and encoded(current['product']['runtime']) == encoded({'enabled':False})
        and all(encoded(body['previous_input']) == encoded(request['previous_input'])
            and encoded(body['current_input']) == encoded(request['current_input']) for body in (intent,committed))
        and encoded(intent['seconds']) == encoded(request['seconds'])
        and encoded(intent['publication_ancestor']) == encoded(request['publication_ancestor'])
        and encoded(intent['reviewed_delta']) == encoded(request['reviewed_delta'])
        and committed['source_receipt_sha256'] == PROJECT_DSH_CURRENT_RECEIPT,
        'ordinary_project_current_source_commit_binding_changed')
    before = intent['before']; names = set(plugins) | {f.MARKER}
    f.require(type(before) is dict and set(before) == names
        and all(type(before[n]) is dict and set(before[n]) == {'sha256','mode'}
            and type(before[n]['mode']) is int and before[n]['mode'] in (0o600,0o644)
            and before[n]['sha256'] == (request['marker']['sha256'] if n == f.MARKER else previous['project_files'][n])
            if n == f.MARKER or n in previous['project_files'] else before[n] is None for n in names),
        'ordinary_project_current_source_before_metadata_changed')
    for name,row in before.items():
        if row is not None:
            f.require(f.digest(f.owned_file(tx/'before'/name,private=True)) == row['sha256'],
                'ordinary_current_successor_root_beforeimage_changed')
    project_current_history(home,request)
    return request,current


def _current_source_cp_transactions(home, leaf):
    """Select by either half of a claim so partial claims cannot become fallback."""
    f = api(); matches = []; roots = list(f.directory(home/'preparation').iterdir())
    f.require(len(roots) <= 4096,'ordinary_current_successor_history_limit')
    for tx in roots:
        if not tx.name.startswith('ordinary-source-update-v45-'): continue
        f.directory(tx)
        selected = False
        for name in ('intent.json','committed.json','request.json'):
            if not os.path.lexists(tx/name): continue
            body = _current_source_json(tx/name)
            ref = body.get('current_input') if type(body) is dict else None
            if type(ref) is dict and (ref.get('path') == leaf['path'] or ref.get('sha256') == leaf['sha256']):
                selected = True
        if selected: matches.append(tx)
    f.require(len(matches) <= 1,'ordinary_current_successor_duplicate_edge')
    return matches[0] if matches else None


def _current_source_cp_proof(home, tx, request, *, committed):
    f = api(); f.directory(tx)
    f.require(not os.path.lexists(tx/'rolled-back.json'),'ordinary_current_successor_rolled_back')
    raw = f.owned_file(tx/'request.json',private=True); raw_sha = f.digest(raw)
    f.require(stat.S_IMODE((tx/'request.json').lstat().st_mode) == 0o600,
        'ordinary_current_successor_raw_request_private_mode_required')
    reference = {'path':str(tx/'request.json'),'sha256':raw_sha}
    f.require(tx.name == 'ordinary-source-update-v45-'+raw_sha[:16]
        and encoded(_current_source_json(_current_source_reference(reference))) == encoded(request),
        'ordinary_current_successor_canonical_request_changed')
    intent = _current_source_json(tx/'intent.json')
    f.require(type(intent) is dict and set(intent) == CURRENT_SOURCE_CP_INTENT_FIELDS
        and intent['state'] == 'SOURCE_UPDATE_INTENT' and intent['home'] == str(home),
        'ordinary_current_successor_intent_required')
    bodies = [intent]; commit = None
    if committed or os.path.lexists(tx/'committed.json'):
        commit = _current_source_json(tx/'committed.json')
        f.require(type(commit) is dict and set(commit) == CURRENT_SOURCE_CP_COMMIT_FIELDS
            and commit['state'] == 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
            and type(commit['seconds']) in (int,float) and __import__('math').isfinite(commit['seconds'])
            and 0 <= commit['seconds'] <= request['seconds']
            and commit['predecessor_request_sha256'] == request['predecessor_request']['sha256']
            and commit['predecessor_receipt_sha256'] == request['predecessor_receipt_sha256'],
            'ordinary_current_successor_commit_required')
        bodies.append(commit)
    f.require(all(body['schema'] == 'friday.ordinary-telegram-source-update-transaction.v1'
        and body['request_sha256'] == raw_sha and encoded(body['request_reference']) == encoded(reference)
        and encoded(body['current_source_successor']) == encoded(request['current_source_successor'])
        and encoded(body['previous_input']) == encoded(request['previous_input'])
        and encoded(body['current_input']) == encoded(request['current_input'])
        and body['gateway_started'] is False and body['workers_enabled'] is False
        for body in bodies), 'ordinary_current_successor_journal_binding_changed')
    for key in ('source_receipt','plugin_set','plugin_additions','project_file_updates'):
        f.require(encoded(intent[key]) == encoded(request[key]),'ordinary_current_successor_intent_binding_changed')
    f.require(encoded(intent['metadata']) == encoded(['hermes-agent.source.json',f.MARKER,'hermes-agent/install-stamp.json']),
        'ordinary_current_successor_metadata_scope_changed')
    for key,name in {'source_receipt':'hermes-agent.source.json','marker':f.MARKER,
            'stamp':'hermes-agent/install-stamp.json'}.items():
        f.require(f.digest(f.owned_file(tx/'before'/name,private=True)) == request[key]['sha256'],
            'ordinary_current_successor_beforeimage_changed')
    return intent,commit


_CURRENT_SOURCE_FOURTH_HISTORY_SEAL = object()


class _CurrentSourceFourthHistory:
    """Internal authenticated CP201 facts, scoped to one exact selected fourth edge."""
    __slots__ = ('third_reference','second_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, third_reference, second_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_FOURTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_fourth_history_required')
        self._seal = _seal
        self.selected_context = encoded(selected_context)
        self.third_reference = encoded(third_reference)
        self.second_reference = encoded(second_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)


_CURRENT_SOURCE_FIFTH_HISTORY_SEAL = object()


class _CurrentSourceFifthHistory:
    """Internal authenticated CP202 facts, scoped to one exact selected fifth edge."""
    __slots__ = ('fourth_reference','third_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, fourth_reference, third_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_FIFTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_fifth_history_required')
        self._seal = _seal
        self.fourth_reference = encoded(fourth_reference)
        self.third_reference = encoded(third_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_SIXTH_HISTORY_SEAL = object()


class _CurrentSourceSixthHistory:
    """Internal authenticated CP203 facts, scoped to one exact selected sixth edge."""
    __slots__ = ('fifth_reference','fourth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, fifth_reference, fourth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_SIXTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_sixth_history_required')
        self._seal = _seal
        self.fifth_reference = encoded(fifth_reference)
        self.fourth_reference = encoded(fourth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_NINETEENTH_HISTORY_SEAL = object()


class _CurrentSourceNineteenthHistory:
    """Internal authenticated CP216 facts, scoped to one exact selected nineteenth edge."""
    __slots__ = ('eighteenth_reference','seventeenth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, eighteenth_reference, seventeenth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_NINETEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_nineteenth_history_required')
        self._seal = _seal
        self.eighteenth_reference = encoded(eighteenth_reference)
        self.seventeenth_reference = encoded(seventeenth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_EIGHTEENTH_HISTORY_SEAL = object()


class _CurrentSourceEighteenthHistory:
    """Internal authenticated CP215 facts, scoped to one exact selected eighteenth edge."""
    __slots__ = ('seventeenth_reference','sixteenth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, seventeenth_reference, sixteenth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_EIGHTEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_eighteenth_history_required')
        self._seal = _seal
        self.seventeenth_reference = encoded(seventeenth_reference)
        self.sixteenth_reference = encoded(sixteenth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_SEVENTEENTH_HISTORY_SEAL = object()


class _CurrentSourceSeventeenthHistory:
    """Internal authenticated CP214 facts, scoped to one exact selected seventeenth edge."""
    __slots__ = ('sixteenth_reference','fifteenth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, sixteenth_reference, fifteenth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_SEVENTEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_seventeenth_history_required')
        self._seal = _seal
        self.sixteenth_reference = encoded(sixteenth_reference)
        self.fifteenth_reference = encoded(fifteenth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_SIXTEENTH_HISTORY_SEAL = object()


class _CurrentSourceSixteenthHistory:
    """Internal authenticated CP213 facts, scoped to one exact selected sixteenth edge."""
    __slots__ = ('fifteenth_reference','fourteenth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, fifteenth_reference, fourteenth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_SIXTEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_sixteenth_history_required')
        self._seal = _seal
        self.fifteenth_reference = encoded(fifteenth_reference)
        self.fourteenth_reference = encoded(fourteenth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_FIFTEENTH_HISTORY_SEAL = object()


class _CurrentSourceFifteenthHistory:
    """Internal authenticated CP212 facts, scoped to one exact selected fifteenth edge."""
    __slots__ = ('fourteenth_reference','thirteenth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, fourteenth_reference, thirteenth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_FIFTEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_fifteenth_history_required')
        self._seal = _seal
        self.fourteenth_reference = encoded(fourteenth_reference)
        self.thirteenth_reference = encoded(thirteenth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_FOURTEENTH_HISTORY_SEAL = object()


class _CurrentSourceFourteenthHistory:
    """Internal authenticated CP211 facts, scoped to one exact selected fourteenth edge."""
    __slots__ = ('thirteenth_reference','twelfth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, thirteenth_reference, twelfth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_FOURTEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_fourteenth_history_required')
        self._seal = _seal
        self.thirteenth_reference = encoded(thirteenth_reference)
        self.twelfth_reference = encoded(twelfth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_THIRTEENTH_HISTORY_SEAL = object()


class _CurrentSourceThirteenthHistory:
    """Internal authenticated CP210 facts, scoped to one exact selected thirteenth edge."""
    __slots__ = ('twelfth_reference','eleventh_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, twelfth_reference, eleventh_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_THIRTEENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_thirteenth_history_required')
        self._seal = _seal
        self.twelfth_reference = encoded(twelfth_reference)
        self.eleventh_reference = encoded(eleventh_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_TWELFTH_HISTORY_SEAL = object()


class _CurrentSourceTwelfthHistory:
    """Internal authenticated CP209 facts, scoped to one exact selected twelfth edge."""
    __slots__ = ('eleventh_reference','tenth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, eleventh_reference, tenth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_TWELFTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_twelfth_history_required')
        self._seal = _seal
        self.eleventh_reference = encoded(eleventh_reference)
        self.tenth_reference = encoded(tenth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_ELEVENTH_HISTORY_SEAL = object()


class _CurrentSourceEleventhHistory:
    """Internal authenticated CP208 facts, scoped to one exact selected eleventh edge."""
    __slots__ = ('tenth_reference','ninth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, tenth_reference, ninth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_ELEVENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_eleventh_history_required')
        self._seal = _seal
        self.tenth_reference = encoded(tenth_reference)
        self.ninth_reference = encoded(ninth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_TENTH_HISTORY_SEAL = object()


class _CurrentSourceTenthHistory:
    """Internal authenticated CP207 facts, scoped to one exact selected tenth edge."""
    __slots__ = ('ninth_reference','eighth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, ninth_reference, eighth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_TENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_tenth_history_required')
        self._seal = _seal
        self.ninth_reference = encoded(ninth_reference)
        self.eighth_reference = encoded(eighth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_NINTH_HISTORY_SEAL = object()


class _CurrentSourceNinthHistory:
    """Internal authenticated CP206 facts, scoped to one exact selected ninth edge."""
    __slots__ = ('eighth_reference','seventh_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, eighth_reference, seventh_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_NINTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_ninth_history_required')
        self._seal = _seal
        self.eighth_reference = encoded(eighth_reference)
        self.seventh_reference = encoded(seventh_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_EIGHTH_HISTORY_SEAL = object()


class _CurrentSourceEighthHistory:
    """Internal authenticated CP205 facts, scoped to one exact selected eighth edge."""
    __slots__ = ('seventh_reference','sixth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, seventh_reference, sixth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_EIGHTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_eighth_history_required')
        self._seal = _seal
        self.seventh_reference = encoded(seventh_reference)
        self.sixth_reference = encoded(sixth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


_CURRENT_SOURCE_SEVENTH_HISTORY_SEAL = object()


class _CurrentSourceSeventhHistory:
    """Internal authenticated CP204 facts, scoped to one exact selected seventh edge."""
    __slots__ = ('sixth_reference','fifth_reference','root_reference','selected_previous','selected_context','_seal')

    def __init__(self, sixth_reference, fifth_reference, root_reference, selected_previous, selected_context, *, _seal):
        api().require(_seal is _CURRENT_SOURCE_SEVENTH_HISTORY_SEAL,
            'ordinary_current_successor_internal_seventh_history_required')
        self._seal = _seal
        self.sixth_reference = encoded(sixth_reference)
        self.fifth_reference = encoded(fifth_reference)
        self.root_reference = encoded(root_reference)
        self.selected_previous = encoded(selected_previous)
        self.selected_context = encoded(selected_context)


def _current_source_nineteenth_successor_checked(value, request, *, cli_only, source_update):
    """Fixed root198 through CP199..CP216, then selected CP217."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_NINETEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    eighteenth_ref = context['previous_native_update']
    eighteenth_request = _current_source_json(_current_source_reference(eighteenth_ref))
    _current_source_request_metadata(eighteenth_request,home)
    eighteenth_context = eighteenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(eighteenth_request['current_input'])
        and encoded(eighteenth_context) == encoded({'schema':CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':eighteenth_context.get('previous_native_update')}),
        'ordinary_current_successor_eighteenth_edge_required')
    eighteenth_tx = _current_source_cp_transactions(home,eighteenth_request['current_input'])
    f.require(eighteenth_tx is not None and eighteenth_ref['path'] == str(eighteenth_tx/'request.json'),
        'ordinary_current_successor_eighteenth_canonical_request_required')
    f.require(eighteenth_ref['sha256'] == CURRENT_SOURCE_NINETEENTH_PREVIOUS_REQUEST
        and eighteenth_request['current_input']['sha256'] == CURRENT_SOURCE_NINETEENTH_PREVIOUS_INPUT,
        'ordinary_current_successor_exact_nineteenth_previous_required')
    f.require(f.digest(f.owned_file(eighteenth_tx/'intent.json',private=True)) == CURRENT_SOURCE_NINETEENTH_PREVIOUS_INTENT
        and f.digest(f.owned_file(eighteenth_tx/'committed.json',private=True)) == CURRENT_SOURCE_NINETEENTH_PREVIOUS_COMMITTED,
        'ordinary_current_successor_exact_nineteenth_previous_proof_required')
    _current_source_cp_proof(home,eighteenth_tx,eighteenth_request,committed=True)
    marker = _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed eighteenth reconstruction authenticates every earlier committed edge.
    # Historical CP216 is admitted only by this exact sealed nineteenth join.
    proof = _CurrentSourceNineteenthHistory(eighteenth_ref,eighteenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_NINETEENTH_HISTORY_SEAL)
    eighteenth = _current_source_eighteenth_successor_checked(
        _current_source_json(_current_source_reference(eighteenth_request['current_input'])),
        eighteenth_request,cli_only=cli_only,source_update=eighteenth_request,
        historical_marker=marker,_nineteenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=eighteenth)


def _current_source_eighteenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _nineteenth_history=None):
    """Fixed root198 through CP199..CP215, then selected CP216."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    seventeenth_ref = context['previous_native_update']
    seventeenth_request = _current_source_json(_current_source_reference(seventeenth_ref))
    _current_source_request_metadata(seventeenth_request,home)
    seventeenth_context = seventeenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(seventeenth_request['current_input'])
        and encoded(seventeenth_context) == encoded({'schema':CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':seventeenth_context.get('previous_native_update')}),
        'ordinary_current_successor_seventeenth_edge_required')
    seventeenth_tx = _current_source_cp_transactions(home,seventeenth_request['current_input'])
    f.require(seventeenth_tx is not None and seventeenth_ref['path'] == str(seventeenth_tx/'request.json'),
        'ordinary_current_successor_seventeenth_canonical_request_required')
    f.require(seventeenth_ref['sha256'] == CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_REQUEST
        and seventeenth_request['current_input']['sha256'] == CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_INPUT,
        'ordinary_current_successor_exact_eighteenth_previous_required')
    f.require(f.digest(f.owned_file(seventeenth_tx/'intent.json',private=True)) == CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_INTENT
        and f.digest(f.owned_file(seventeenth_tx/'committed.json',private=True)) == CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_COMMITTED,
        'ordinary_current_successor_exact_eighteenth_previous_proof_required')
    _current_source_cp_proof(home,seventeenth_tx,seventeenth_request,committed=True)
    f.require(historical_marker is None or type(_nineteenth_history) is _CurrentSourceNineteenthHistory
        and _nineteenth_history._seal is _CURRENT_SOURCE_NINETEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_nineteenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed seventeenth reconstruction authenticates every earlier committed edge.
    # Historical CP215 is admitted only by this exact sealed eighteenth join.
    proof = _CurrentSourceEighteenthHistory(seventeenth_ref,seventeenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_EIGHTEENTH_HISTORY_SEAL)
    seventeenth = _current_source_seventeenth_successor_checked(
        _current_source_json(_current_source_reference(seventeenth_request['current_input'])),
        seventeenth_request,cli_only=cli_only,source_update=seventeenth_request,
        historical_marker=marker,_eighteenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=seventeenth,
        historical_marker=historical_marker,_nineteenth_history=_nineteenth_history)


def _current_source_seventeenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _eighteenth_history=None):
    """Fixed root198 through CP199..CP214, then selected CP215."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    sixteenth_ref = context['previous_native_update']
    sixteenth_request = _current_source_json(_current_source_reference(sixteenth_ref))
    _current_source_request_metadata(sixteenth_request,home)
    sixteenth_context = sixteenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(sixteenth_request['current_input'])
        and encoded(sixteenth_context) == encoded({'schema':CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':sixteenth_context.get('previous_native_update')}),
        'ordinary_current_successor_sixteenth_edge_required')
    sixteenth_tx = _current_source_cp_transactions(home,sixteenth_request['current_input'])
    f.require(sixteenth_tx is not None and sixteenth_ref['path'] == str(sixteenth_tx/'request.json'),
        'ordinary_current_successor_sixteenth_canonical_request_required')
    f.require(sixteenth_ref['sha256'] == CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_REQUEST
        and sixteenth_request['current_input']['sha256'] == CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_INPUT,
        'ordinary_current_successor_exact_seventeenth_previous_required')
    f.require(f.digest(f.owned_file(sixteenth_tx/'intent.json',private=True)) == CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_INTENT
        and f.digest(f.owned_file(sixteenth_tx/'committed.json',private=True)) == CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_COMMITTED,
        'ordinary_current_successor_exact_seventeenth_previous_proof_required')
    _current_source_cp_proof(home,sixteenth_tx,sixteenth_request,committed=True)
    f.require(historical_marker is None or type(_eighteenth_history) is _CurrentSourceEighteenthHistory
        and _eighteenth_history._seal is _CURRENT_SOURCE_EIGHTEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_eighteenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed sixteenth reconstruction authenticates every earlier committed edge.
    # Historical CP214 is admitted only by this exact sealed seventeenth join.
    proof = _CurrentSourceSeventeenthHistory(sixteenth_ref,sixteenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_SEVENTEENTH_HISTORY_SEAL)
    sixteenth = _current_source_sixteenth_successor_checked(
        _current_source_json(_current_source_reference(sixteenth_request['current_input'])),
        sixteenth_request,cli_only=cli_only,source_update=sixteenth_request,
        historical_marker=marker,_seventeenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=sixteenth,
        historical_marker=historical_marker,_eighteenth_history=_eighteenth_history)


def _current_source_sixteenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _seventeenth_history=None):
    """Fixed root198 through CP199..CP213, then selected CP214."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    fifteenth_ref = context['previous_native_update']
    fifteenth_request = _current_source_json(_current_source_reference(fifteenth_ref))
    _current_source_request_metadata(fifteenth_request,home)
    fifteenth_context = fifteenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(fifteenth_request['current_input'])
        and encoded(fifteenth_context) == encoded({'schema':CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':fifteenth_context.get('previous_native_update')}),
        'ordinary_current_successor_fifteenth_edge_required')
    fifteenth_tx = _current_source_cp_transactions(home,fifteenth_request['current_input'])
    f.require(fifteenth_tx is not None and fifteenth_ref['path'] == str(fifteenth_tx/'request.json'),
        'ordinary_current_successor_fifteenth_canonical_request_required')
    f.require(fifteenth_ref['sha256'] == CURRENT_SOURCE_SIXTEENTH_PREVIOUS_REQUEST
        and fifteenth_request['current_input']['sha256'] == CURRENT_SOURCE_SIXTEENTH_PREVIOUS_INPUT,
        'ordinary_current_successor_exact_sixteenth_previous_required')
    f.require(f.digest(f.owned_file(fifteenth_tx/'intent.json',private=True)) == CURRENT_SOURCE_SIXTEENTH_PREVIOUS_INTENT
        and f.digest(f.owned_file(fifteenth_tx/'committed.json',private=True)) == CURRENT_SOURCE_SIXTEENTH_PREVIOUS_COMMITTED,
        'ordinary_current_successor_exact_sixteenth_previous_proof_required')
    _current_source_cp_proof(home,fifteenth_tx,fifteenth_request,committed=True)
    f.require(historical_marker is None or type(_seventeenth_history) is _CurrentSourceSeventeenthHistory
        and _seventeenth_history._seal is _CURRENT_SOURCE_SEVENTEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_seventeenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed fifteenth reconstruction authenticates every earlier committed edge.
    # Historical CP213 is admitted only by this exact sealed sixteenth join.
    proof = _CurrentSourceSixteenthHistory(fifteenth_ref,fifteenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_SIXTEENTH_HISTORY_SEAL)
    fifteenth = _current_source_fifteenth_successor_checked(
        _current_source_json(_current_source_reference(fifteenth_request['current_input'])),
        fifteenth_request,cli_only=cli_only,source_update=fifteenth_request,
        historical_marker=marker,_sixteenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=fifteenth,
        historical_marker=historical_marker,_seventeenth_history=_seventeenth_history)


def _current_source_fifteenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _sixteenth_history=None):
    """Fixed root198 through CP199..CP212, then selected CP213."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    fourteenth_ref = context['previous_native_update']
    fourteenth_request = _current_source_json(_current_source_reference(fourteenth_ref))
    _current_source_request_metadata(fourteenth_request,home)
    fourteenth_context = fourteenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(fourteenth_request['current_input'])
        and encoded(fourteenth_context) == encoded({'schema':CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':fourteenth_context.get('previous_native_update')}),
        'ordinary_current_successor_fourteenth_edge_required')
    fourteenth_tx = _current_source_cp_transactions(home,fourteenth_request['current_input'])
    f.require(fourteenth_tx is not None and fourteenth_ref['path'] == str(fourteenth_tx/'request.json'),
        'ordinary_current_successor_fourteenth_canonical_request_required')
    f.require(fourteenth_ref['sha256'] == CURRENT_SOURCE_FIFTEENTH_PREVIOUS_REQUEST
        and fourteenth_request['current_input']['sha256'] == CURRENT_SOURCE_FIFTEENTH_PREVIOUS_INPUT,
        'ordinary_current_successor_exact_fifteenth_previous_required')
    f.require(f.digest(f.owned_file(fourteenth_tx/'intent.json',private=True)) == CURRENT_SOURCE_FIFTEENTH_PREVIOUS_INTENT
        and f.digest(f.owned_file(fourteenth_tx/'committed.json',private=True)) == CURRENT_SOURCE_FIFTEENTH_PREVIOUS_COMMITTED,
        'ordinary_current_successor_exact_fifteenth_previous_proof_required')
    _current_source_cp_proof(home,fourteenth_tx,fourteenth_request,committed=True)
    f.require(historical_marker is None or type(_sixteenth_history) is _CurrentSourceSixteenthHistory
        and _sixteenth_history._seal is _CURRENT_SOURCE_SIXTEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_sixteenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed fourteenth reconstruction authenticates every earlier committed edge.
    # Historical CP212 is admitted only by this exact sealed fifteenth join.
    proof = _CurrentSourceFifteenthHistory(fourteenth_ref,fourteenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_FIFTEENTH_HISTORY_SEAL)
    fourteenth = _current_source_fourteenth_successor_checked(
        _current_source_json(_current_source_reference(fourteenth_request['current_input'])),
        fourteenth_request,cli_only=cli_only,source_update=fourteenth_request,
        historical_marker=marker,_fifteenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=fourteenth,
        historical_marker=historical_marker,_sixteenth_history=_sixteenth_history)


def _current_source_fourteenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _fifteenth_history=None):
    """Fixed root198 through CP199..CP211, then selected CP212."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    thirteenth_ref = context['previous_native_update']
    thirteenth_request = _current_source_json(_current_source_reference(thirteenth_ref))
    _current_source_request_metadata(thirteenth_request,home)
    thirteenth_context = thirteenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(thirteenth_request['current_input'])
        and encoded(thirteenth_context) == encoded({'schema':CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':thirteenth_context.get('previous_native_update')}),
        'ordinary_current_successor_thirteenth_edge_required')
    thirteenth_tx = _current_source_cp_transactions(home,thirteenth_request['current_input'])
    f.require(thirteenth_tx is not None and thirteenth_ref['path'] == str(thirteenth_tx/'request.json'),
        'ordinary_current_successor_thirteenth_canonical_request_required')
    f.require(thirteenth_ref['sha256'] == CURRENT_SOURCE_FOURTEENTH_PREVIOUS_REQUEST
        and thirteenth_request['current_input']['sha256'] == CURRENT_SOURCE_FOURTEENTH_PREVIOUS_INPUT,
        'ordinary_current_successor_exact_fourteenth_previous_required')
    f.require(f.digest(f.owned_file(thirteenth_tx/'intent.json',private=True)) == CURRENT_SOURCE_FOURTEENTH_PREVIOUS_INTENT
        and f.digest(f.owned_file(thirteenth_tx/'committed.json',private=True)) == CURRENT_SOURCE_FOURTEENTH_PREVIOUS_COMMITTED,
        'ordinary_current_successor_exact_fourteenth_previous_proof_required')
    _current_source_cp_proof(home,thirteenth_tx,thirteenth_request,committed=True)
    f.require(historical_marker is None or type(_fifteenth_history) is _CurrentSourceFifteenthHistory
        and _fifteenth_history._seal is _CURRENT_SOURCE_FIFTEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_fifteenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed thirteenth reconstruction authenticates every earlier committed edge.
    # Historical CP211 is admitted only by this exact sealed fourteenth join.
    proof = _CurrentSourceFourteenthHistory(thirteenth_ref,thirteenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_FOURTEENTH_HISTORY_SEAL)
    thirteenth = _current_source_thirteenth_successor_checked(
        _current_source_json(_current_source_reference(thirteenth_request['current_input'])),
        thirteenth_request,cli_only=cli_only,source_update=thirteenth_request,
        historical_marker=marker,_fourteenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=thirteenth,
        historical_marker=historical_marker,_fifteenth_history=_fifteenth_history)


def _current_source_thirteenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _fourteenth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> CP205 -> CP206 -> CP207 -> CP208 -> CP209 -> CP210 -> selected CP211."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    twelfth_ref = context['previous_native_update']
    twelfth_request = _current_source_json(_current_source_reference(twelfth_ref))
    _current_source_request_metadata(twelfth_request,home)
    twelfth_context = twelfth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(twelfth_request['current_input'])
        and encoded(twelfth_context) == encoded({'schema':CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':twelfth_context.get('previous_native_update')}),
        'ordinary_current_successor_twelfth_edge_required')
    twelfth_tx = _current_source_cp_transactions(home,twelfth_request['current_input'])
    f.require(twelfth_tx is not None and twelfth_ref['path'] == str(twelfth_tx/'request.json'),
        'ordinary_current_successor_twelfth_canonical_request_required')
    _current_source_cp_proof(home,twelfth_tx,twelfth_request,committed=True)
    f.require(historical_marker is None or type(_fourteenth_history) is _CurrentSourceFourteenthHistory
        and _fourteenth_history._seal is _CURRENT_SOURCE_FOURTEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_fourteenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed twelfth reconstruction authenticates every earlier committed edge.
    # Historical CP210 is admitted only by this exact sealed thirteenth join.
    proof = _CurrentSourceThirteenthHistory(twelfth_ref,twelfth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_THIRTEENTH_HISTORY_SEAL)
    twelfth = _current_source_twelfth_successor_checked(
        _current_source_json(_current_source_reference(twelfth_request['current_input'])),
        twelfth_request,cli_only=cli_only,source_update=twelfth_request,
        historical_marker=marker,_thirteenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=twelfth,
        historical_marker=historical_marker,_fourteenth_history=_fourteenth_history)


def _current_source_twelfth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _thirteenth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> CP205 -> CP206 -> CP207 -> CP208 -> CP209 -> selected CP210."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    eleventh_ref = context['previous_native_update']
    eleventh_request = _current_source_json(_current_source_reference(eleventh_ref))
    _current_source_request_metadata(eleventh_request,home)
    eleventh_context = eleventh_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(eleventh_request['current_input'])
        and encoded(eleventh_context) == encoded({'schema':CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':eleventh_context.get('previous_native_update')}),
        'ordinary_current_successor_eleventh_edge_required')
    eleventh_tx = _current_source_cp_transactions(home,eleventh_request['current_input'])
    f.require(eleventh_tx is not None and eleventh_ref['path'] == str(eleventh_tx/'request.json'),
        'ordinary_current_successor_eleventh_canonical_request_required')
    _current_source_cp_proof(home,eleventh_tx,eleventh_request,committed=True)
    f.require(historical_marker is None or type(_thirteenth_history) is _CurrentSourceThirteenthHistory
        and _thirteenth_history._seal is _CURRENT_SOURCE_THIRTEENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_thirteenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed eleventh reconstruction authenticates every earlier committed edge.
    # Historical CP209 is admitted only by this exact sealed twelfth join.
    proof = _CurrentSourceTwelfthHistory(eleventh_ref,eleventh_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_TWELFTH_HISTORY_SEAL)
    eleventh = _current_source_eleventh_successor_checked(
        _current_source_json(_current_source_reference(eleventh_request['current_input'])),
        eleventh_request,cli_only=cli_only,source_update=eleventh_request,
        historical_marker=marker,_twelfth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=eleventh,
        historical_marker=historical_marker,_thirteenth_history=_thirteenth_history)


def _current_source_eleventh_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _twelfth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> CP205 -> CP206 -> CP207 -> CP208 -> selected CP209."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    tenth_ref = context['previous_native_update']
    tenth_request = _current_source_json(_current_source_reference(tenth_ref))
    _current_source_request_metadata(tenth_request,home)
    tenth_context = tenth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(tenth_request['current_input'])
        and encoded(tenth_context) == encoded({'schema':CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':tenth_context.get('previous_native_update')}),
        'ordinary_current_successor_tenth_edge_required')
    tenth_tx = _current_source_cp_transactions(home,tenth_request['current_input'])
    f.require(tenth_tx is not None and tenth_ref['path'] == str(tenth_tx/'request.json'),
        'ordinary_current_successor_tenth_canonical_request_required')
    _current_source_cp_proof(home,tenth_tx,tenth_request,committed=True)
    f.require(historical_marker is None or type(_twelfth_history) is _CurrentSourceTwelfthHistory
        and _twelfth_history._seal is _CURRENT_SOURCE_TWELFTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_twelfth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed tenth reconstruction authenticates every earlier committed edge.
    # Historical CP208 is admitted only by this exact sealed eleventh join.
    proof = _CurrentSourceEleventhHistory(tenth_ref,tenth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_ELEVENTH_HISTORY_SEAL)
    tenth = _current_source_tenth_successor_checked(
        _current_source_json(_current_source_reference(tenth_request['current_input'])),
        tenth_request,cli_only=cli_only,source_update=tenth_request,
        historical_marker=marker,_eleventh_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=tenth,
        historical_marker=historical_marker,_twelfth_history=_twelfth_history)


def _current_source_tenth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _eleventh_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> CP205 -> CP206 -> CP207 -> selected CP208."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    ninth_ref = context['previous_native_update']
    ninth_request = _current_source_json(_current_source_reference(ninth_ref))
    _current_source_request_metadata(ninth_request,home)
    ninth_context = ninth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(ninth_request['current_input'])
        and encoded(ninth_context) == encoded({'schema':CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':ninth_context.get('previous_native_update')}),
        'ordinary_current_successor_ninth_edge_required')
    ninth_tx = _current_source_cp_transactions(home,ninth_request['current_input'])
    f.require(ninth_tx is not None and ninth_ref['path'] == str(ninth_tx/'request.json'),
        'ordinary_current_successor_ninth_canonical_request_required')
    _current_source_cp_proof(home,ninth_tx,ninth_request,committed=True)
    f.require(historical_marker is None or type(_eleventh_history) is _CurrentSourceEleventhHistory
        and _eleventh_history._seal is _CURRENT_SOURCE_ELEVENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_eleventh_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed ninth reconstruction authenticates every earlier committed edge.
    # Historical CP207 is admitted only by this exact sealed tenth join.
    proof = _CurrentSourceTenthHistory(ninth_ref,ninth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_TENTH_HISTORY_SEAL)
    ninth = _current_source_ninth_successor_checked(
        _current_source_json(_current_source_reference(ninth_request['current_input'])),
        ninth_request,cli_only=cli_only,source_update=ninth_request,
        historical_marker=marker,_tenth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=ninth,
        historical_marker=historical_marker,_eleventh_history=_eleventh_history)


def _current_source_ninth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _tenth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> CP205 -> CP206 -> selected CP207."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    eighth_ref = context['previous_native_update']
    eighth_request = _current_source_json(_current_source_reference(eighth_ref))
    _current_source_request_metadata(eighth_request,home)
    eighth_context = eighth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(eighth_request['current_input'])
        and encoded(eighth_context) == encoded({'schema':CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':eighth_context.get('previous_native_update')}),
        'ordinary_current_successor_eighth_edge_required')
    eighth_tx = _current_source_cp_transactions(home,eighth_request['current_input'])
    f.require(eighth_tx is not None and eighth_ref['path'] == str(eighth_tx/'request.json'),
        'ordinary_current_successor_eighth_canonical_request_required')
    _current_source_cp_proof(home,eighth_tx,eighth_request,committed=True)
    f.require(historical_marker is None or type(_tenth_history) is _CurrentSourceTenthHistory
        and _tenth_history._seal is _CURRENT_SOURCE_TENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_tenth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed eighth reconstruction authenticates every earlier committed edge.
    # Historical CP206 is admitted only by this exact sealed ninth join.
    proof = _CurrentSourceNinthHistory(eighth_ref,eighth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_NINTH_HISTORY_SEAL)
    eighth = _current_source_eighth_successor_checked(
        _current_source_json(_current_source_reference(eighth_request['current_input'])),
        eighth_request,cli_only=cli_only,source_update=eighth_request,
        historical_marker=marker,_ninth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=eighth,
        historical_marker=historical_marker,_tenth_history=_tenth_history)


def _current_source_eighth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _ninth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> CP205 -> selected CP206."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    seventh_ref = context['previous_native_update']
    seventh_request = _current_source_json(_current_source_reference(seventh_ref))
    _current_source_request_metadata(seventh_request,home)
    seventh_context = seventh_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(seventh_request['current_input'])
        and encoded(seventh_context) == encoded({'schema':CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':seventh_context.get('previous_native_update')}),
        'ordinary_current_successor_seventh_edge_required')
    seventh_tx = _current_source_cp_transactions(home,seventh_request['current_input'])
    f.require(seventh_tx is not None and seventh_ref['path'] == str(seventh_tx/'request.json'),
        'ordinary_current_successor_seventh_canonical_request_required')
    _current_source_cp_proof(home,seventh_tx,seventh_request,committed=True)
    f.require(historical_marker is None or type(_ninth_history) is _CurrentSourceNinthHistory
        and _ninth_history._seal is _CURRENT_SOURCE_NINTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_ninth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed seventh reconstruction authenticates every earlier committed edge.
    # Historical CP205 is admitted only by this exact sealed eighth join.
    proof = _CurrentSourceEighthHistory(seventh_ref,seventh_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_EIGHTH_HISTORY_SEAL)
    seventh = _current_source_seventh_successor_checked(
        _current_source_json(_current_source_reference(seventh_request['current_input'])),
        seventh_request,cli_only=cli_only,source_update=seventh_request,
        historical_marker=marker,_eighth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=seventh,
        historical_marker=historical_marker,_ninth_history=_ninth_history)


def _current_source_seventh_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _eighth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> CP204 -> selected CP205."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    sixth_ref = context['previous_native_update']
    sixth_request = _current_source_json(_current_source_reference(sixth_ref))
    _current_source_request_metadata(sixth_request,home)
    sixth_context = sixth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(sixth_request['current_input'])
        and encoded(sixth_context) == encoded({'schema':CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':sixth_context.get('previous_native_update')}),
        'ordinary_current_successor_sixth_edge_required')
    sixth_tx = _current_source_cp_transactions(home,sixth_request['current_input'])
    f.require(sixth_tx is not None and sixth_ref['path'] == str(sixth_tx/'request.json'),
        'ordinary_current_successor_sixth_canonical_request_required')
    _current_source_cp_proof(home,sixth_tx,sixth_request,committed=True)
    f.require(historical_marker is None or type(_eighth_history) is _CurrentSourceEighthHistory
        and _eighth_history._seal is _CURRENT_SOURCE_EIGHTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_eighth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed sixth reconstruction authenticates every earlier committed edge.
    # Historical CP204 is admitted only by this exact sealed seventh join.
    proof = _CurrentSourceSeventhHistory(sixth_ref,sixth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_SEVENTH_HISTORY_SEAL)
    sixth = _current_source_sixth_successor_checked(
        _current_source_json(_current_source_reference(sixth_request['current_input'])),
        sixth_request,cli_only=cli_only,source_update=sixth_request,
        historical_marker=marker,_seventh_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=sixth,
        historical_marker=historical_marker,_eighth_history=_eighth_history)


def _current_source_sixth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _seventh_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> CP203 -> selected CP204."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    fifth_ref = context['previous_native_update']
    fifth_request = _current_source_json(_current_source_reference(fifth_ref))
    _current_source_request_metadata(fifth_request,home)
    fifth_context = fifth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(fifth_request['current_input'])
        and encoded(fifth_context) == encoded({'schema':CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':fifth_context.get('previous_native_update')}),
        'ordinary_current_successor_fifth_edge_required')
    fifth_tx = _current_source_cp_transactions(home,fifth_request['current_input'])
    f.require(fifth_tx is not None and fifth_ref['path'] == str(fifth_tx/'request.json'),
        'ordinary_current_successor_fifth_canonical_request_required')
    _current_source_cp_proof(home,fifth_tx,fifth_request,committed=True)
    f.require(historical_marker is None or type(_seventh_history) is _CurrentSourceSeventhHistory
        and _seventh_history._seal is _CURRENT_SOURCE_SEVENTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_seventh_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed fifth reconstruction authenticates every earlier committed edge.
    # Historical CP203 is admitted only by this exact sealed sixth join.
    proof = _CurrentSourceSixthHistory(fifth_ref,fifth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_SIXTH_HISTORY_SEAL)
    fifth = _current_source_fifth_successor_checked(
        _current_source_json(_current_source_reference(fifth_request['current_input'])),
        fifth_request,cli_only=cli_only,source_update=fifth_request,
        historical_marker=marker,_sixth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=fifth,
        historical_marker=historical_marker,_seventh_history=_seventh_history)


def _current_source_fifth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _sixth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> CP202 -> selected CP203."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    fourth_ref = context['previous_native_update']
    fourth_request = _current_source_json(_current_source_reference(fourth_ref))
    _current_source_request_metadata(fourth_request,home)
    fourth_context = fourth_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(fourth_request['current_input'])
        and encoded(fourth_context) == encoded({'schema':CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':fourth_context.get('previous_native_update')}),
        'ordinary_current_successor_fourth_edge_required')
    fourth_tx = _current_source_cp_transactions(home,fourth_request['current_input'])
    f.require(fourth_tx is not None and fourth_ref['path'] == str(fourth_tx/'request.json'),
        'ordinary_current_successor_fourth_canonical_request_required')
    _current_source_cp_proof(home,fourth_tx,fourth_request,committed=True)
    f.require(historical_marker is None or type(_sixth_history) is _CurrentSourceSixthHistory
        and _sixth_history._seal is _CURRENT_SOURCE_SIXTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_sixth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    # The fixed fourth reconstruction authenticates all three earlier commits.
    # Its final historical edge is admitted only by this exact sealed fifth join.
    proof = _CurrentSourceFifthHistory(fourth_ref,fourth_context['previous_native_update'],
        context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_FIFTH_HISTORY_SEAL)
    fourth = _current_source_fourth_successor_checked(
        _current_source_json(_current_source_reference(fourth_request['current_input'])),
        fourth_request,cli_only=cli_only,source_update=fourth_request,
        historical_marker=marker,_fifth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=fourth,
        historical_marker=historical_marker,_sixth_history=_sixth_history)


def _current_source_fourth_successor_checked(value, request, *, cli_only, source_update,
        historical_marker=None, _fifth_history=None):
    """Fixed root198 -> CP199 -> CP200 -> CP201 -> selected CP202; no recursion."""
    f = api(); home = f.canonical(value['home']); context = request['current_source_successor']
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context['schema'] == CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA,
        'ordinary_current_successor_context_required')
    third_ref = context['previous_native_update']
    third_request = _current_source_json(_current_source_reference(third_ref))
    _current_source_request_metadata(third_request,home)
    third_context = third_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(third_request['current_input'])
        and encoded(third_context) == encoded({'schema':CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':third_context.get('previous_native_update')}),
        'ordinary_current_successor_third_edge_required')
    third_tx = _current_source_cp_transactions(home,third_request['current_input'])
    f.require(third_tx is not None and third_ref['path'] == str(third_tx/'request.json'),
        'ordinary_current_successor_third_canonical_request_required')
    _current_source_cp_proof(home,third_tx,third_request,committed=True)
    second_ref = third_context['previous_native_update']
    second_request = _current_source_json(_current_source_reference(second_ref))
    _current_source_request_metadata(second_request,home)
    second_context = second_request['current_source_successor']
    f.require(encoded(third_request['previous_input']) == encoded(second_request['current_input'])
        and encoded(second_context) == encoded({'schema':CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA,
            'root_project_update':context['root_project_update'],
            'previous_native_update':second_context.get('previous_native_update')}),
        'ordinary_current_successor_prior_edge_required')
    second_tx = _current_source_cp_transactions(home,second_request['current_input'])
    f.require(second_tx is not None and second_ref['path'] == str(second_tx/'request.json'),
        'ordinary_current_successor_prior_canonical_request_required')
    _current_source_cp_proof(home,second_tx,second_request,committed=True)
    first_ref = second_context['previous_native_update']
    first_request = _current_source_json(_current_source_reference(first_ref))
    _current_source_request_metadata(first_request,home)
    f.require(encoded(first_request['current_source_successor']) == encoded({
            'schema':CURRENT_SOURCE_SUCCESSOR_SCHEMA,'root_project_update':context['root_project_update']})
        and encoded(second_request['previous_input']) == encoded(first_request['current_input']),
        'ordinary_current_successor_first_edge_required')
    first_tx = _current_source_cp_transactions(home,first_request['current_input'])
    f.require(first_tx is not None and first_ref['path'] == str(first_tx/'request.json'),
        'ordinary_current_successor_first_canonical_request_required')
    _current_source_cp_proof(home,first_tx,first_request,committed=True)
    f.require(historical_marker is None or type(_fifth_history) is _CurrentSourceFifthHistory
        and _fifth_history._seal is _CURRENT_SOURCE_FIFTH_HISTORY_SEAL,
        'ordinary_current_successor_internal_fifth_history_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    if marker.get('input_sha256') == request['current_input']['sha256']:
        selected_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(selected_tx is not None,'ordinary_current_successor_leaf_journal_required')
        marker = _current_source_json(selected_tx/'before'/f.MARKER)
    first = _current_native_source_edge_checked(
        _current_source_json(_current_source_reference(first_request['current_input'])),
        cli_only=cli_only,source_update=first_request,
        historical_marker=_current_source_json(second_tx/'before'/f.MARKER))
    second = _current_native_source_edge_checked(
        _current_source_json(_current_source_reference(second_request['current_input'])),
        cli_only=cli_only,source_update=second_request,prior_edge=first,
        historical_marker=_current_source_json(third_tx/'before'/f.MARKER))
    # Mint only after all three canonical requests/commits and the fixed root/joins
    # have been authenticated. It cannot enable arbitrary historical third mode.
    proof = _CurrentSourceFourthHistory(third_ref,second_ref,context['root_project_update'],request['previous_input'],context,
        _seal=_CURRENT_SOURCE_FOURTH_HISTORY_SEAL)
    third = _current_native_source_edge_checked(
        _current_source_json(_current_source_reference(third_request['current_input'])),
        cli_only=cli_only,source_update=third_request,prior_edge=second,
        historical_marker=marker,_fourth_history=proof)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=third,
        historical_marker=historical_marker,_fifth_history=_fifth_history)


def current_native_source_successor_checked(value, *, cli_only, source_update=None):
    """The v6 root and nineteen fixed authenticated native CP edges."""
    f = api()
    if type(value) is not dict or type(value.get('home')) is not str:
        f.require(source_update is None,'ordinary_current_successor_value_required'); return None
    home = f.canonical(value['home'])
    tx_root = home/'preparation'/('ordinary-source-update-'+PROJECT_DSH_CURRENT_INPUT)
    if source_update is None and not os.path.lexists(tx_root): return None
    f.require(cli_only is True,'ordinary_project_current_source_cli_only_required'); f.directory(home)
    if source_update is None:
        root_intent = _current_source_json(tx_root/'intent.json')
        f.require(type(root_intent) is dict,'ordinary_current_successor_root_intent_required')
        _,root_value = _project_current_root_checked(home,root_intent.get('request_reference'))
        if encoded(value) == encoded(root_value): return None
        leaf_ref = f.read_json(home/f.MARKER).get('ordinary_gateway',{}).get('operator_entry',{}).get('input')
        _current_source_reference(leaf_ref)
        tx = _current_source_cp_transactions(home,leaf_ref)
        f.require(tx is not None,'ordinary_current_successor_committed_edge_required')
        request = _current_source_json(tx/'request.json')
    else:
        request = source_update
    _current_source_request_metadata(request,home)
    context = request['current_source_successor']
    if context.get('schema') == CURRENT_SOURCE_SUCCESSOR_SCHEMA:
        return _current_native_source_edge_checked(value,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_NINETEENTH_SUCCESSOR_SCHEMA:
        return _current_source_nineteenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA:
        return _current_source_eighteenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA:
        return _current_source_seventeenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA:
        return _current_source_sixteenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA:
        return _current_source_fifteenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA:
        return _current_source_fourteenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA:
        return _current_source_thirteenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA:
        return _current_source_twelfth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA:
        return _current_source_eleventh_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA:
        return _current_source_tenth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA:
        return _current_source_ninth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA:
        return _current_source_eighth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA:
        return _current_source_seventh_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA:
        return _current_source_sixth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA:
        return _current_source_fifth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    if context.get('schema') == CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA:
        return _current_source_fourth_successor_checked(value,request,cli_only=cli_only,source_update=source_update)
    third = context.get('schema') == CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA
    f.require(set(context) == {'schema','root_project_update','previous_native_update'}
        and context.get('schema') in (CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA,CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA),
        'ordinary_current_successor_context_required')
    prior_ref = context['previous_native_update']
    prior_request = _current_source_json(_current_source_reference(prior_ref))
    _current_source_request_metadata(prior_request,home)
    prior_context = prior_request['current_source_successor']
    f.require(encoded(request['previous_input']) == encoded(prior_request['current_input'])
        and (type(prior_context) is dict and set(prior_context) == {'schema','root_project_update','previous_native_update'}
            and prior_context.get('schema') == CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA
            and encoded(prior_context['root_project_update']) == encoded(context['root_project_update']) if third
            else encoded(prior_context) == encoded({'schema':CURRENT_SOURCE_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update']})),
        'ordinary_current_successor_prior_edge_required')
    prior_tx = _current_source_cp_transactions(home,prior_request['current_input'])
    f.require(prior_tx is not None and prior_ref['path'] == str(prior_tx/'request.json'),
        'ordinary_current_successor_prior_canonical_request_required')
    _current_source_cp_proof(home,prior_tx,prior_request,committed=True)
    current_marker = _current_source_json(home/f.MARKER)
    leaf = current_marker.get('input_sha256') == request['current_input']['sha256']
    if leaf:
        tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(tx is not None,'ordinary_current_successor_leaf_journal_required')
        prior_marker = _current_source_json(tx/'before'/f.MARKER)
    else:
        prior_marker = current_marker
    first = None
    if third:
        # Fixed CP199 -> CP200 history, never a recursively extensible chain.
        first_ref = prior_context['previous_native_update']
        first_request = _current_source_json(_current_source_reference(first_ref))
        _current_source_request_metadata(first_request,home)
        f.require(encoded(first_request['current_source_successor']) == encoded({
            'schema':CURRENT_SOURCE_SUCCESSOR_SCHEMA,'root_project_update':context['root_project_update']})
            and encoded(prior_request['previous_input']) == encoded(first_request['current_input']),
            'ordinary_current_successor_first_edge_required')
        first_tx = _current_source_cp_transactions(home,first_request['current_input'])
        f.require(first_tx is not None and first_ref['path'] == str(first_tx/'request.json'),
            'ordinary_current_successor_first_canonical_request_required')
        _current_source_cp_proof(home,first_tx,first_request,committed=True)
        first_value = _current_source_json(_current_source_reference(first_request['current_input']))
        first_marker = _current_source_json(prior_tx/'before'/f.MARKER)
        first = _current_native_source_edge_checked(first_value,cli_only=cli_only,
            source_update=first_request,historical_marker=first_marker)
    # Historical facts authenticate retained before/staged/journal bytes. Only
    # the selected current edge below reaches actual native/plugin authority.
    prior_value = _current_source_json(_current_source_reference(prior_request['current_input']))
    prior = _current_native_source_edge_checked(prior_value,cli_only=cli_only,
        source_update=prior_request,historical_marker=prior_marker,prior_edge=first)
    return _current_native_source_edge_checked(value,cli_only=cli_only,
        source_update=source_update,prior_edge=prior)


def _current_source_request_metadata(request,home):
    f = api()
    f.require(type(request) is dict and set(request) == CURRENT_SOURCE_CP_FIELDS
        and request['schema'] == 'friday.ordinary-telegram-source-update.v46'
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 7200
        and request['home'] == str(home) and type(request['current_source_successor']) is dict,
        'ordinary_current_successor_explicit_request_required')


def _current_native_source_edge_checked(value, *, cli_only, source_update=None,
        historical_marker=None, prior_edge=None, _fourth_history=None, _fifth_history=None, _sixth_history=None, _seventh_history=None, _eighth_history=None, _ninth_history=None, _tenth_history=None, _eleventh_history=None, _twelfth_history=None, _thirteenth_history=None, _fourteenth_history=None, _fifteenth_history=None, _sixteenth_history=None, _seventeenth_history=None, _eighteenth_history=None, _nineteenth_history=None):
    """Validate one bounded edge; historical mode returns facts, never admission."""
    f = api()
    if type(value) is not dict or type(value.get('home')) is not str:
        f.require(source_update is None,'ordinary_current_successor_value_required'); return None
    home = f.canonical(value['home']); tx_root = home/'preparation'/('ordinary-source-update-'+PROJECT_DSH_CURRENT_INPUT)
    if source_update is None and not os.path.lexists(tx_root): return None
    f.require(cli_only is True,'ordinary_project_current_source_cli_only_required'); f.directory(home)
    source = f.directory(home/'hermes-agent')
    leaf_ref = None; tx = None
    if source_update is None:
        root_intent = _current_source_json(tx_root/'intent.json')
        f.require(type(root_intent) is dict,'ordinary_current_successor_root_intent_required')
        root_ref = root_intent.get('request_reference')
        root_request,previous = _project_current_root_checked(home,root_ref)
        if encoded(value) == encoded(previous): return None
        leaf_ref = f.read_json(home/f.MARKER).get('ordinary_gateway',{}).get('operator_entry',{}).get('input')
        _current_source_reference(leaf_ref)
        tx = _current_source_cp_transactions(home,leaf_ref)
        f.require(tx is not None,'ordinary_current_successor_committed_edge_required')
        request = _current_source_json(tx/'request.json')
    else:
        request = source_update
    f.require(type(request) is dict and set(request) == CURRENT_SOURCE_CP_FIELDS
        and request['schema'] == 'friday.ordinary-telegram-source-update.v46'
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 7200
        and request['home'] == str(home),'ordinary_current_successor_explicit_request_required')
    context = request['current_source_successor']
    continuation = prior_edge is not None
    nineteenth = continuation and context.get('schema') == CURRENT_SOURCE_NINETEENTH_SUCCESSOR_SCHEMA
    eighteenth = continuation and context.get('schema') == CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA
    seventeenth = continuation and context.get('schema') == CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA
    sixteenth = continuation and context.get('schema') == CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA
    fifteenth = continuation and context.get('schema') == CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA
    fourteenth = continuation and context.get('schema') == CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA
    thirteenth = continuation and context.get('schema') == CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA
    twelfth = continuation and context.get('schema') == CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA
    eleventh = continuation and context.get('schema') == CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA
    tenth = continuation and context.get('schema') == CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA
    ninth = continuation and context.get('schema') == CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA
    eighth = continuation and context.get('schema') == CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA
    seventh = continuation and context.get('schema') == CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA
    sixth = continuation and context.get('schema') == CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA
    fifth = continuation and context.get('schema') == CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA
    fourth = continuation and context.get('schema') == CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA
    third = continuation and context.get('schema') == CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA
    second = continuation and not third and not fourth and not fifth and not sixth and not seventh and not eighth and not ninth and not tenth and not eleventh and not twelfth and not thirteenth and not fourteenth and not fifteenth and not sixteenth and not seventeenth and not eighteenth and not nineteenth
    f.require(type(context) is dict
        and set(context) == ({'schema','root_project_update','previous_native_update'} if continuation
            else {'schema','root_project_update'})
        and context['schema'] == (CURRENT_SOURCE_NINETEENTH_SUCCESSOR_SCHEMA if nineteenth else
            CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA if eighteenth else
            CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA if seventeenth else
            CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA if sixteenth else
            CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA if fifteenth else
            CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA if fourteenth else
            CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA if thirteenth else
            CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA if twelfth else
            CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA if eleventh else
            CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA if tenth else
            CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA if ninth else
            CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA if eighth else
            CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA if seventh else
            CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA if sixth else
            CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA if fifth else
            CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA if fourth else
            CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA if third else
            CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA if second else CURRENT_SOURCE_SUCCESSOR_SCHEMA)
        and (not continuation or prior_edge['request']['current_source_successor']['schema'] ==
            (CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA if nineteenth else
                CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA if eighteenth else
                CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA if seventeenth else
                CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA if sixteenth else
                CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA if fifteenth else
                CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA if fourteenth else
                CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA if thirteenth else
                CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA if twelfth else
                CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA if eleventh else
                CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA if tenth else
                CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA if ninth else
                CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA if eighth else
                CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA if seventh else
                CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA if sixth else
                CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA if fifth else
                CURRENT_SOURCE_THIRD_SUCCESSOR_SCHEMA if fourth else
                CURRENT_SOURCE_SECOND_SUCCESSOR_SCHEMA if third else CURRENT_SOURCE_SUCCESSOR_SCHEMA))
        and not (nineteenth and historical_marker is not None)
        and (not (eighteenth and historical_marker is not None) or
            type(_nineteenth_history) is _CurrentSourceNineteenthHistory
            and _nineteenth_history._seal is _CURRENT_SOURCE_NINETEENTH_HISTORY_SEAL)
        and (not (seventeenth and historical_marker is not None) or
            type(_eighteenth_history) is _CurrentSourceEighteenthHistory
            and _eighteenth_history._seal is _CURRENT_SOURCE_EIGHTEENTH_HISTORY_SEAL)
        and (not (sixteenth and historical_marker is not None) or
            type(_seventeenth_history) is _CurrentSourceSeventeenthHistory
            and _seventeenth_history._seal is _CURRENT_SOURCE_SEVENTEENTH_HISTORY_SEAL)
        and (not (fifteenth and historical_marker is not None) or
            type(_sixteenth_history) is _CurrentSourceSixteenthHistory
            and _sixteenth_history._seal is _CURRENT_SOURCE_SIXTEENTH_HISTORY_SEAL)
        and (not (fourteenth and historical_marker is not None) or
            type(_fifteenth_history) is _CurrentSourceFifteenthHistory
            and _fifteenth_history._seal is _CURRENT_SOURCE_FIFTEENTH_HISTORY_SEAL)
        and (not (thirteenth and historical_marker is not None) or
            type(_fourteenth_history) is _CurrentSourceFourteenthHistory
            and _fourteenth_history._seal is _CURRENT_SOURCE_FOURTEENTH_HISTORY_SEAL)
        and (not (twelfth and historical_marker is not None) or
            type(_thirteenth_history) is _CurrentSourceThirteenthHistory
            and _thirteenth_history._seal is _CURRENT_SOURCE_THIRTEENTH_HISTORY_SEAL)
        and (not (eleventh and historical_marker is not None) or
            type(_twelfth_history) is _CurrentSourceTwelfthHistory
            and _twelfth_history._seal is _CURRENT_SOURCE_TWELFTH_HISTORY_SEAL)
        and (not (tenth and historical_marker is not None) or
            type(_eleventh_history) is _CurrentSourceEleventhHistory
            and _eleventh_history._seal is _CURRENT_SOURCE_ELEVENTH_HISTORY_SEAL)
        and (not (ninth and historical_marker is not None) or
            type(_tenth_history) is _CurrentSourceTenthHistory
            and _tenth_history._seal is _CURRENT_SOURCE_TENTH_HISTORY_SEAL)
        and (not (eighth and historical_marker is not None) or
            type(_ninth_history) is _CurrentSourceNinthHistory
            and _ninth_history._seal is _CURRENT_SOURCE_NINTH_HISTORY_SEAL)
        and (not (seventh and historical_marker is not None) or
            type(_eighth_history) is _CurrentSourceEighthHistory
            and _eighth_history._seal is _CURRENT_SOURCE_EIGHTH_HISTORY_SEAL)
        and (not (sixth and historical_marker is not None) or
            type(_seventh_history) is _CurrentSourceSeventhHistory
            and _seventh_history._seal is _CURRENT_SOURCE_SEVENTH_HISTORY_SEAL)
        and (not (fifth and historical_marker is not None) or
            type(_sixth_history) is _CurrentSourceSixthHistory
            and _sixth_history._seal is _CURRENT_SOURCE_SIXTH_HISTORY_SEAL)
        and (not (fourth and historical_marker is not None) or
            type(_fifth_history) is _CurrentSourceFifthHistory
            and _fifth_history._seal is _CURRENT_SOURCE_FIFTH_HISTORY_SEAL)
        and (not (third and historical_marker is not None) or
            type(_fourth_history) is _CurrentSourceFourthHistory
            and _fourth_history._seal is _CURRENT_SOURCE_FOURTH_HISTORY_SEAL),
        'ordinary_current_successor_context_required')
    if third and historical_marker is not None:
        # The internal proof is bound to this canonical CP201, its exact CP200
        # predecessor, the shared root, and the selected fourth's before input.
        third_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(third_tx is not None
            and _fourth_history.third_reference == encoded({'path':str(third_tx/'request.json'),
                'sha256':f.digest(f.owned_file(third_tx/'request.json',private=True))})
            and _fourth_history.second_reference == encoded(context['previous_native_update'])
            and _fourth_history.root_reference == encoded(context['root_project_update'])
            and _fourth_history.selected_previous == encoded(request['current_input'])
            and _fourth_history.selected_context == encoded({'schema':CURRENT_SOURCE_FOURTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(third_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(third_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_third_history_required')
        _current_source_cp_proof(home,third_tx,request,committed=True)
    if fourth and historical_marker is not None:
        # Bind CP202 history to its canonical request, CP201 predecessor, shared
        # root and the selected fifth's exact before input and typed context.
        fourth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(fourth_tx is not None
            and _fifth_history.fourth_reference == encoded({'path':str(fourth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(fourth_tx/'request.json',private=True))})
            and _fifth_history.third_reference == encoded(context['previous_native_update'])
            and _fifth_history.root_reference == encoded(context['root_project_update'])
            and _fifth_history.selected_previous == encoded(request['current_input'])
            and _fifth_history.selected_context == encoded({'schema':CURRENT_SOURCE_FIFTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(fourth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(fourth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_fourth_history_required')
        _current_source_cp_proof(home,fourth_tx,request,committed=True)
    if fifth and historical_marker is not None:
        # Bind CP203 history to its canonical request, CP202 predecessor, shared
        # root and the selected sixth's exact before input and typed context.
        fifth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(fifth_tx is not None
            and _sixth_history.fifth_reference == encoded({'path':str(fifth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(fifth_tx/'request.json',private=True))})
            and _sixth_history.fourth_reference == encoded(context['previous_native_update'])
            and _sixth_history.root_reference == encoded(context['root_project_update'])
            and _sixth_history.selected_previous == encoded(request['current_input'])
            and _sixth_history.selected_context == encoded({'schema':CURRENT_SOURCE_SIXTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(fifth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(fifth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_fifth_history_required')
        _current_source_cp_proof(home,fifth_tx,request,committed=True)
    if sixth and historical_marker is not None:
        # Bind CP204 history to its canonical request, CP203 predecessor, shared
        # root and the selected seventh's exact before input and typed context.
        sixth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(sixth_tx is not None
            and _seventh_history.sixth_reference == encoded({'path':str(sixth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(sixth_tx/'request.json',private=True))})
            and _seventh_history.fifth_reference == encoded(context['previous_native_update'])
            and _seventh_history.root_reference == encoded(context['root_project_update'])
            and _seventh_history.selected_previous == encoded(request['current_input'])
            and _seventh_history.selected_context == encoded({'schema':CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(sixth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(sixth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_sixth_history_required')
        _current_source_cp_proof(home,sixth_tx,request,committed=True)
    if seventh and historical_marker is not None:
        # Bind CP205 history to its canonical request, CP204 predecessor, shared
        # root and the selected eighth's exact before input and typed context.
        seventh_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(seventh_tx is not None
            and _eighth_history.seventh_reference == encoded({'path':str(seventh_tx/'request.json'),
                'sha256':f.digest(f.owned_file(seventh_tx/'request.json',private=True))})
            and _eighth_history.sixth_reference == encoded(context['previous_native_update'])
            and _eighth_history.root_reference == encoded(context['root_project_update'])
            and _eighth_history.selected_previous == encoded(request['current_input'])
            and _eighth_history.selected_context == encoded({'schema':CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(seventh_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(seventh_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_seventh_history_required')
        _current_source_cp_proof(home,seventh_tx,request,committed=True)
    if eighth and historical_marker is not None:
        # Bind CP206 history to its canonical request, CP205 predecessor, shared
        # root and the selected ninth's exact before input and typed context.
        eighth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(eighth_tx is not None
            and _ninth_history.eighth_reference == encoded({'path':str(eighth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(eighth_tx/'request.json',private=True))})
            and _ninth_history.seventh_reference == encoded(context['previous_native_update'])
            and _ninth_history.root_reference == encoded(context['root_project_update'])
            and _ninth_history.selected_previous == encoded(request['current_input'])
            and _ninth_history.selected_context == encoded({'schema':CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(eighth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(eighth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_eighth_history_required')
        _current_source_cp_proof(home,eighth_tx,request,committed=True)
    if ninth and historical_marker is not None:
        # Bind CP207 history to its canonical request, CP206 predecessor, shared
        # root and the selected tenth's exact before input and typed context.
        ninth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(ninth_tx is not None
            and _tenth_history.ninth_reference == encoded({'path':str(ninth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(ninth_tx/'request.json',private=True))})
            and _tenth_history.eighth_reference == encoded(context['previous_native_update'])
            and _tenth_history.root_reference == encoded(context['root_project_update'])
            and _tenth_history.selected_previous == encoded(request['current_input'])
            and _tenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_TENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(ninth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(ninth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_ninth_history_required')
        _current_source_cp_proof(home,ninth_tx,request,committed=True)
    if tenth and historical_marker is not None:
        # Bind CP208 history to its canonical request, CP207 predecessor, shared
        # root and the selected eleventh's exact before input and typed context.
        tenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(tenth_tx is not None
            and _eleventh_history.tenth_reference == encoded({'path':str(tenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(tenth_tx/'request.json',private=True))})
            and _eleventh_history.ninth_reference == encoded(context['previous_native_update'])
            and _eleventh_history.root_reference == encoded(context['root_project_update'])
            and _eleventh_history.selected_previous == encoded(request['current_input'])
            and _eleventh_history.selected_context == encoded({'schema':CURRENT_SOURCE_ELEVENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(tenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(tenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_tenth_history_required')
        _current_source_cp_proof(home,tenth_tx,request,committed=True)
    if eleventh and historical_marker is not None:
        # Bind CP209 history to its canonical request, CP208 predecessor, shared
        # root and the selected twelfth's exact before input and typed context.
        eleventh_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(eleventh_tx is not None
            and _twelfth_history.eleventh_reference == encoded({'path':str(eleventh_tx/'request.json'),
                'sha256':f.digest(f.owned_file(eleventh_tx/'request.json',private=True))})
            and _twelfth_history.tenth_reference == encoded(context['previous_native_update'])
            and _twelfth_history.root_reference == encoded(context['root_project_update'])
            and _twelfth_history.selected_previous == encoded(request['current_input'])
            and _twelfth_history.selected_context == encoded({'schema':CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(eleventh_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(eleventh_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_eleventh_history_required')
        _current_source_cp_proof(home,eleventh_tx,request,committed=True)
    if twelfth and historical_marker is not None:
        # Bind CP210 history to its canonical request, CP209 predecessor, shared
        # root and the selected thirteenth's exact before input and typed context.
        twelfth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(twelfth_tx is not None
            and _thirteenth_history.twelfth_reference == encoded({'path':str(twelfth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(twelfth_tx/'request.json',private=True))})
            and _thirteenth_history.eleventh_reference == encoded(context['previous_native_update'])
            and _thirteenth_history.root_reference == encoded(context['root_project_update'])
            and _thirteenth_history.selected_previous == encoded(request['current_input'])
            and _thirteenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_THIRTEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(twelfth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(twelfth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_twelfth_history_required')
        _current_source_cp_proof(home,twelfth_tx,request,committed=True)
    if thirteenth and historical_marker is not None:
        # Bind CP211 history to its canonical request, CP210 predecessor, shared
        # root and the selected fourteenth's exact before input and typed context.
        thirteenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(thirteenth_tx is not None
            and _fourteenth_history.thirteenth_reference == encoded({'path':str(thirteenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(thirteenth_tx/'request.json',private=True))})
            and _fourteenth_history.twelfth_reference == encoded(context['previous_native_update'])
            and _fourteenth_history.root_reference == encoded(context['root_project_update'])
            and _fourteenth_history.selected_previous == encoded(request['current_input'])
            and _fourteenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_FOURTEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(thirteenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(thirteenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_thirteenth_history_required')
        _current_source_cp_proof(home,thirteenth_tx,request,committed=True)
    if fourteenth and historical_marker is not None:
        # Bind CP212 history to its canonical request, CP211 predecessor, shared
        # root and the selected fifteenth's exact before input and typed context.
        fourteenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(fourteenth_tx is not None
            and _fifteenth_history.fourteenth_reference == encoded({'path':str(fourteenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(fourteenth_tx/'request.json',private=True))})
            and _fifteenth_history.thirteenth_reference == encoded(context['previous_native_update'])
            and _fifteenth_history.root_reference == encoded(context['root_project_update'])
            and _fifteenth_history.selected_previous == encoded(request['current_input'])
            and _fifteenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_FIFTEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(fourteenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(fourteenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_fourteenth_history_required')
        _current_source_cp_proof(home,fourteenth_tx,request,committed=True)
    if fifteenth and historical_marker is not None:
        # Bind CP213 history to its canonical request, CP212 predecessor, shared
        # root and the selected sixteenth's exact before input and typed context.
        fifteenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(fifteenth_tx is not None
            and _sixteenth_history.fifteenth_reference == encoded({'path':str(fifteenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(fifteenth_tx/'request.json',private=True))})
            and _sixteenth_history.fourteenth_reference == encoded(context['previous_native_update'])
            and _sixteenth_history.root_reference == encoded(context['root_project_update'])
            and _sixteenth_history.selected_previous == encoded(request['current_input'])
            and _sixteenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_SIXTEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(fifteenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(fifteenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_fifteenth_history_required')
        _current_source_cp_proof(home,fifteenth_tx,request,committed=True)
    if sixteenth and historical_marker is not None:
        # Bind CP214 history to its canonical request, CP213 predecessor, shared
        # root and the selected seventeenth's exact before input and typed context.
        sixteenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(sixteenth_tx is not None
            and _seventeenth_history.sixteenth_reference == encoded({'path':str(sixteenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(sixteenth_tx/'request.json',private=True))})
            and _seventeenth_history.fifteenth_reference == encoded(context['previous_native_update'])
            and _seventeenth_history.root_reference == encoded(context['root_project_update'])
            and _seventeenth_history.selected_previous == encoded(request['current_input'])
            and _seventeenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_SEVENTEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(sixteenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(sixteenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_sixteenth_history_required')
        _current_source_cp_proof(home,sixteenth_tx,request,committed=True)
    if seventeenth and historical_marker is not None:
        # Bind CP215 history to its canonical request, CP214 predecessor, shared
        # root and the selected eighteenth's exact before input and typed context.
        seventeenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(seventeenth_tx is not None
            and _eighteenth_history.seventeenth_reference == encoded({'path':str(seventeenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(seventeenth_tx/'request.json',private=True))})
            and _eighteenth_history.sixteenth_reference == encoded(context['previous_native_update'])
            and _eighteenth_history.root_reference == encoded(context['root_project_update'])
            and _eighteenth_history.selected_previous == encoded(request['current_input'])
            and _eighteenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_EIGHTEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(seventeenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(seventeenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_seventeenth_history_required')
        _current_source_cp_proof(home,seventeenth_tx,request,committed=True)
    if eighteenth and historical_marker is not None:
        # Bind CP216 history to its canonical request, CP215 predecessor, shared
        # root and the selected nineteenth's exact before input and typed context.
        eighteenth_tx = _current_source_cp_transactions(home,request['current_input'])
        f.require(eighteenth_tx is not None
            and _nineteenth_history.eighteenth_reference == encoded({'path':str(eighteenth_tx/'request.json'),
                'sha256':f.digest(f.owned_file(eighteenth_tx/'request.json',private=True))})
            and _nineteenth_history.seventeenth_reference == encoded(context['previous_native_update'])
            and _nineteenth_history.root_reference == encoded(context['root_project_update'])
            and _nineteenth_history.selected_previous == encoded(request['current_input'])
            and _nineteenth_history.selected_context == encoded({'schema':CURRENT_SOURCE_NINETEENTH_SUCCESSOR_SCHEMA,
                'root_project_update':context['root_project_update'],
                'previous_native_update':{'path':str(eighteenth_tx/'request.json'),
                    'sha256':f.digest(f.owned_file(eighteenth_tx/'request.json',private=True))}})
            and encoded(prior_edge['request']['current_input']) == encoded(request['previous_input']),
            'ordinary_current_successor_authenticated_eighteenth_history_required')
        _current_source_cp_proof(home,eighteenth_tx,request,committed=True)
    root_request,previous = _project_current_root_checked(home,context['root_project_update'])
    previous_ref = root_request['current_input']
    expected_before_receipt = PROJECT_DSH_CURRENT_RECEIPT
    expected_before_stamp = PROJECT_DSH_CURRENT_STAMP
    before_layers = 198
    before_native_count = 17888
    before_project_count = 477
    if continuation:
        previous = prior_edge['value']; previous_ref = prior_edge['request']['current_input']
        expected_before_receipt = prior_edge['receipt_sha256']
        expected_before_stamp = prior_edge['stamp_sha256']
        before_layers = 216 if nineteenth else 215 if eighteenth else 214 if seventeenth else 213 if sixteenth else 212 if fifteenth else 211 if fourteenth else 210 if thirteenth else 209 if twelfth else 208 if eleventh else 207 if tenth else 206 if ninth else 205 if eighth else 204 if seventh else 203 if sixth else 202 if fifth else 201 if fourth else 200 if third else 199
        before_native_count = 17891 if nineteenth or eighteenth or seventeenth or sixteenth or fifteenth or fourteenth or thirteenth or twelfth or eleventh or tenth or ninth or eighth or seventh or sixth else 17890 if fifth else 17888
        before_project_count = 513 if nineteenth else 511 if eighteenth else 509 if seventeenth else 507 if sixteenth else 505 if fifteenth else 503 if fourteenth else 501 if thirteenth else 499 if twelfth else 497 if eleventh else 495 if tenth else 493 if ninth else 491 if eighth else 489 if seventh else 487 if sixth else 485 if fifth else 483 if fourth else 481 if third else 479
    f.require(not fourteenth or (expected_before_receipt == CURRENT_SOURCE_FOURTEENTH_PREVIOUS_RECEIPT
        and expected_before_stamp == CURRENT_SOURCE_FOURTEENTH_PREVIOUS_STAMP),
        'ordinary_current_successor_exact_fourteenth_before_metadata_required')
    f.require(not fifteenth or (expected_before_receipt == CURRENT_SOURCE_FIFTEENTH_PREVIOUS_RECEIPT
        and expected_before_stamp == CURRENT_SOURCE_FIFTEENTH_PREVIOUS_STAMP),
        'ordinary_current_successor_exact_fifteenth_before_metadata_required')
    f.require(not sixteenth or (expected_before_receipt == CURRENT_SOURCE_SIXTEENTH_PREVIOUS_RECEIPT
        and expected_before_stamp == CURRENT_SOURCE_SIXTEENTH_PREVIOUS_STAMP),
        'ordinary_current_successor_exact_sixteenth_before_metadata_required')
    f.require(not seventeenth or (expected_before_receipt == CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_RECEIPT
        and expected_before_stamp == CURRENT_SOURCE_SEVENTEENTH_PREVIOUS_STAMP),
        'ordinary_current_successor_exact_seventeenth_before_metadata_required')
    f.require(not eighteenth or (expected_before_receipt == CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_RECEIPT
        and expected_before_stamp == CURRENT_SOURCE_EIGHTEENTH_PREVIOUS_STAMP),
        'ordinary_current_successor_exact_eighteenth_before_metadata_required')
    f.require(not nineteenth or (expected_before_receipt == CURRENT_SOURCE_NINETEENTH_PREVIOUS_RECEIPT
        and expected_before_stamp == CURRENT_SOURCE_NINETEENTH_PREVIOUS_STAMP),
        'ordinary_current_successor_exact_nineteenth_before_metadata_required')
    _current_source_reference(request['previous_input']); _current_source_reference(request['current_input'])
    current = _current_source_json(Path(request['current_input']['path']))
    f.require(encoded(value) == encoded(current) and current.get('home') == str(home)
        and encoded(request['previous_input']) == encoded(previous_ref)
        and request['previous_input']['sha256'] != request['current_input']['sha256']
        and request['previous_input']['path'] != request['current_input']['path']
        and encoded(request['candidate_input']) == encoded(request['current_input'])
        and type(request['candidate_project']) is str
        and (historical_marker is not None
            and str(f.canonical(request['candidate_project'])) == request['candidate_project']
            or request['candidate_project'] == str(f.ROOT))
        and encoded({k:v for k,v in previous.items() if k != 'project_files'}) ==
            encoded({k:v for k,v in current.items() if k != 'project_files'}),
        'ordinary_current_successor_input_join_changed')
    old_cp = _current_source_json(_current_source_reference(root_request['publication_ancestor']['request']))
    f.require(all(encoded(request[k]) == encoded(old_cp[k]) for k in
        ('predecessor_request','predecessor_current_input_sha256','predecessor_receipt_sha256','transaction_history')),
        'ordinary_current_successor_engineering_anchor_changed')
    for key,name in {'source_receipt':'hermes-agent.source.json','target_receipt':'hermes-agent.source.json',
            'marker':f.MARKER,'stamp':'hermes-agent/install-stamp.json','configuration':'config.yaml'}.items():
        _current_source_reference_metadata = request[key]
        f.require(type(_current_source_reference_metadata) is dict
            and set(_current_source_reference_metadata) == {'path','sha256'}
            and _current_source_reference_metadata['path'] == str(home/name)
            and type(_current_source_reference_metadata['sha256']) is str
            and len(_current_source_reference_metadata['sha256']) == 64
            and all(c in '0123456789abcdef' for c in _current_source_reference_metadata['sha256']),
            'ordinary_current_successor_before_reference_changed')
    f.require(encoded(request['source_receipt']) == encoded(request['target_receipt'])
        and request['source_receipt']['sha256'] == expected_before_receipt
        and request['stamp']['sha256'] == expected_before_stamp
        and type(request['installed_layers']) is int and request['installed_layers'] == before_layers
        and type(request['installed_files']) is int and request['installed_files'] == before_native_count
        and encoded(request['plugin_set']) == encoded([]) and encoded(request['plugin_additions']) == encoded([])
        and encoded(request['staged_files']) == encoded([]),'ordinary_current_successor_exact_native198_required')
    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)
    leaf = marker.get('input_sha256') == request['current_input']['sha256']
    f.require(historical_marker is None or leaf,'ordinary_current_successor_historical_leaf_required')
    for key,name in {'configuration':'config.yaml','profile':'FRIDAY-PROFILE.json',
            'launcher':'hermes-agent/.hermes/bin/hermes'}.items():
        if key == 'configuration' and leaf:
            # The CP request authenticates its before-config, not every later
            # native onboarding edit. Current bytes still have private custody
            # and must satisfy the unchanged native normalized deployment seal.
            f.owned_file(home/name,private=True)
        else:
            _current_source_reference(request[key])
        f.require(request[key]['path'] == str(home/name),'ordinary_current_successor_current_pin_path_changed')
    _current_source_reference(request['native_unit'])
    f.require(request['native_unit']['path'] == root_request['native_unit']['path'],
        'ordinary_current_successor_native_unit_path_changed')
    names = request['layer_names']
    f.require(type(names) is list and len(names) == 1 and type(names[0]) is str
        and names[0] and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in names[0]),
        'ordinary_current_successor_one_layer_required')
    f.require(not second or names == [CURRENT_SOURCE_SECOND_LAYER],
        'ordinary_current_successor_exact_second_layer_required')
    f.require(not third or names == [CURRENT_SOURCE_THIRD_LAYER],
        'ordinary_current_successor_exact_third_layer_required')
    f.require(not fourth or names == [CURRENT_SOURCE_FOURTH_LAYER],
        'ordinary_current_successor_exact_fourth_layer_required')
    f.require(not fifth or names == [CURRENT_SOURCE_FIFTH_LAYER],
        'ordinary_current_successor_exact_fifth_layer_required')
    f.require(not sixth or names == [CURRENT_SOURCE_SIXTH_LAYER],
        'ordinary_current_successor_exact_sixth_layer_required')
    f.require(not thirteenth or names == [CURRENT_SOURCE_THIRTEENTH_LAYER],
        'ordinary_current_successor_exact_thirteenth_layer_required')
    f.require(not fourteenth or names == [CURRENT_SOURCE_FOURTEENTH_LAYER],
        'ordinary_current_successor_exact_fourteenth_layer_required')
    f.require(not fifteenth or names == [CURRENT_SOURCE_FIFTEENTH_LAYER],
        'ordinary_current_successor_exact_fifteenth_layer_required')
    f.require(not sixteenth or names == [CURRENT_SOURCE_SIXTEENTH_LAYER],
        'ordinary_current_successor_exact_sixteenth_layer_required')
    f.require(not seventeenth or names == [CURRENT_SOURCE_SEVENTEENTH_LAYER],
        'ordinary_current_successor_exact_seventeenth_layer_required')
    f.require(not eighteenth or names == [CURRENT_SOURCE_EIGHTEENTH_LAYER],
        'ordinary_current_successor_exact_eighteenth_layer_required')
    f.require(not nineteenth or names == [CURRENT_SOURCE_NINETEENTH_LAYER],
        'ordinary_current_successor_exact_nineteenth_layer_required')
    f.require(not twelfth or names == [CURRENT_SOURCE_TWELFTH_LAYER],
        'ordinary_current_successor_exact_twelfth_layer_required')
    f.require(not eleventh or names == [CURRENT_SOURCE_ELEVENTH_LAYER],
        'ordinary_current_successor_exact_eleventh_layer_required')
    f.require(not tenth or names == [CURRENT_SOURCE_TENTH_LAYER],
        'ordinary_current_successor_exact_tenth_layer_required')
    f.require(not ninth or names == [CURRENT_SOURCE_NINTH_LAYER],
        'ordinary_current_successor_exact_ninth_layer_required')
    f.require(not eighth or names == [CURRENT_SOURCE_EIGHTH_LAYER],
        'ordinary_current_successor_exact_eighth_layer_required')
    f.require(not seventh or names == [CURRENT_SOURCE_SEVENTH_LAYER],
        'ordinary_current_successor_exact_seventh_layer_required')
    manifest_name = 'patches/hermes/'+names[0]+'-manifest.json'; patch_name = 'patches/hermes/'+names[0]+'.patch'
    old = previous['project_files']; files = current['project_files']
    f.require(type(old) is dict and type(files) is dict,'ordinary_current_successor_project_inventory_required')
    changes = {n for n in old if files.get(n) != old[n]}
    f.require(not thirteenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_thirteenth_helper_scope_required')
    f.require(not fourteenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_fourteenth_helper_scope_required')
    f.require(not fifteenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_fifteenth_helper_scope_required')
    f.require(not sixteenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_sixteenth_helper_scope_required')
    f.require(not seventeenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_seventeenth_helper_scope_required')
    f.require(not eighteenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_eighteenth_helper_scope_required')
    f.require(not nineteenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_nineteenth_helper_scope_required')
    f.require(not twelfth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_twelfth_helper_scope_required')
    f.require(not eleventh or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_eleventh_helper_scope_required')
    f.require(not tenth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_tenth_helper_scope_required')
    f.require(not ninth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_ninth_helper_scope_required')
    f.require(not eighth or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_eighth_helper_scope_required')
    f.require(not seventh or changes == {PROJECT_DSH_CURRENT_HELPER},
        'ordinary_current_successor_exact_seventh_helper_scope_required')
    f.require(type(files) is dict and len(old) == before_project_count and len(files) == before_project_count + 2
        and set(files) == set(old) | {manifest_name,patch_name}
        and manifest_name not in old and patch_name not in old
        and changes <= PROJECT_DSH_CURRENT_HELPERS
        and encoded(request['project_file_updates']) == encoded(sorted(changes))
        and encoded(request['layer_manifest_updates']) == encoded([manifest_name])
        and encoded(request['project_inventory']) == encoded(files)
        and request['project_inventory_sha256'] == f.digest(encoded(files)),
        'ordinary_current_successor_exact_project_delta_required')
    f.require(not third or (files.get(manifest_name) == CURRENT_SOURCE_THIRD_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_THIRD_PATCH),
        'ordinary_current_successor_exact_third_layer_images_required')
    f.require(not fourth or (files.get(manifest_name) == CURRENT_SOURCE_FOURTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_FOURTH_PATCH),
        'ordinary_current_successor_exact_fourth_layer_images_required')
    f.require(not fifth or (files.get(manifest_name) == CURRENT_SOURCE_FIFTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_FIFTH_PATCH),
        'ordinary_current_successor_exact_fifth_layer_images_required')
    f.require(not sixth or (files.get(manifest_name) == CURRENT_SOURCE_SIXTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_SIXTH_PATCH),
        'ordinary_current_successor_exact_sixth_layer_images_required')
    f.require(not seventh or (files.get(manifest_name) == CURRENT_SOURCE_SEVENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_SEVENTH_PATCH),
        'ordinary_current_successor_exact_seventh_layer_images_required')
    f.require(not eighth or (files.get(manifest_name) == CURRENT_SOURCE_EIGHTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_EIGHTH_PATCH),
        'ordinary_current_successor_exact_eighth_layer_images_required')
    f.require(not ninth or (files.get(manifest_name) == CURRENT_SOURCE_NINTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_NINTH_PATCH),
        'ordinary_current_successor_exact_ninth_layer_images_required')
    f.require(not tenth or (files.get(manifest_name) == CURRENT_SOURCE_TENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_TENTH_PATCH),
        'ordinary_current_successor_exact_tenth_layer_images_required')
    f.require(not eleventh or (files.get(manifest_name) == CURRENT_SOURCE_ELEVENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_ELEVENTH_PATCH),
        'ordinary_current_successor_exact_eleventh_layer_images_required')
    f.require(not twelfth or (files.get(manifest_name) == CURRENT_SOURCE_TWELFTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_TWELFTH_PATCH),
        'ordinary_current_successor_exact_twelfth_layer_images_required')
    f.require(not thirteenth or (files.get(manifest_name) == CURRENT_SOURCE_THIRTEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_THIRTEENTH_PATCH),
        'ordinary_current_successor_exact_thirteenth_layer_images_required')
    f.require(not fourteenth or (files.get(manifest_name) == CURRENT_SOURCE_FOURTEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_FOURTEENTH_PATCH),
        'ordinary_current_successor_exact_fourteenth_layer_images_required')
    f.require(not fifteenth or (files.get(manifest_name) == CURRENT_SOURCE_FIFTEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_FIFTEENTH_PATCH),
        'ordinary_current_successor_exact_fifteenth_layer_images_required')
    f.require(not sixteenth or (files.get(manifest_name) == CURRENT_SOURCE_SIXTEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_SIXTEENTH_PATCH),
        'ordinary_current_successor_exact_sixteenth_layer_images_required')
    f.require(not seventeenth or (files.get(manifest_name) == CURRENT_SOURCE_SEVENTEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_SEVENTEENTH_PATCH),
        'ordinary_current_successor_exact_seventeenth_layer_images_required')
    f.require(not eighteenth or (files.get(manifest_name) == CURRENT_SOURCE_EIGHTEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_EIGHTEENTH_PATCH),
        'ordinary_current_successor_exact_eighteenth_layer_images_required')
    f.require(not nineteenth or (files.get(manifest_name) == CURRENT_SOURCE_NINETEENTH_MANIFEST
        and files.get(patch_name) == CURRENT_SOURCE_NINETEENTH_PATCH),
        'ordinary_current_successor_exact_nineteenth_layer_images_required')
    for name,expected in files.items():
        path = Path(name)
        f.require(type(name) is str and not path.is_absolute() and name == path.as_posix()
            and not any(part in ('.','..') for part in path.parts)
            and type(expected) is str and len(expected) == 64 and all(c in '0123456789abcdef' for c in expected)
            and (historical_marker is not None and name in PROJECT_DSH_CURRENT_HELPERS
                or f.digest(f.owned_file(f.ROOT/name)) == expected),
            'ordinary_current_successor_project_pin_changed')
    f.require(Path(f.__file__).resolve() == f.ROOT/'scripts/friday_install.py'
        and Path(__file__).resolve() == f.ROOT/PROJECT_DSH_CURRENT_HELPER,
        'ordinary_current_successor_helper_origin_changed')
    required = {str(p.relative_to(f.ROOT)) for relative in ('plugins/friday_rework','patches/hermes')
        for p in (f.ROOT/relative).rglob('*') if p.is_file() or p.is_symlink()}
    f.require(historical_marker is not None or required <= set(files),
        'ordinary_current_successor_extra_project_file')
    manifest = _current_source_json(f.ROOT/manifest_name,private=False)
    f.require(type(manifest) is dict and manifest.get('patch') == patch_name and manifest.get('patch_sha256') == files[patch_name]
        and type(manifest.get('files')) is list and manifest['files'],
        'ordinary_current_successor_manifest_required')
    rows = manifest['files']; touched = [r.get('path') for r in rows if type(r) is dict]
    f.require(len(touched) == len(rows) and len(touched) == len(set(touched))
        and all(type(n) is str and n and not Path(n).is_absolute() and n == Path(n).as_posix()
            and not any(p in ('.','..') for p in Path(n).parts) for n in touched),
        'ordinary_current_successor_manifest_paths_changed')
    if tx is None: tx = _current_source_cp_transactions(home,request['current_input'])
    intent = commit = None
    if tx is not None: intent,commit = _current_source_cp_proof(home,tx,request,
        committed=source_update is None or historical_marker is not None)
    f.require(source_update is not None or leaf,'ordinary_current_successor_current_marker_required')
    f.require(not leaf or tx is not None,'ordinary_current_successor_leaf_journal_required')
    before_receipt = _current_source_json(tx/'before/hermes-agent.source.json') if leaf else _current_source_json(home/'hermes-agent.source.json')
    if continuation:
        f.require(encoded(before_receipt) == encoded(prior_edge['receipt']),
            'ordinary_current_successor_prior_receipt_changed')
    before_marker = _current_source_json(tx/'before'/f.MARKER) if leaf else marker
    before_stamp = _current_source_json(tx/'before/hermes-agent/install-stamp.json') if leaf else _current_source_json(source/'install-stamp.json')
    if not leaf:
        for key in ('source_receipt','marker','stamp'): _current_source_reference(request[key])
    f.require(len(before_receipt.get('layers',[])) == before_layers and len(before_receipt.get('files',{})) == before_native_count
        and type(before_receipt.get('source_file_count')) is int and before_receipt['source_file_count'] == 17730
        and manifest.get('base_commit') == before_receipt.get('commit')
        and before_marker.get('input_sha256') == request['previous_input']['sha256']
        and before_marker.get('source_receipt_sha256') == expected_before_receipt
        and before_marker.get('ordinary_gateway',{}).get('source_receipt_sha256') == expected_before_receipt
        and encoded(before_marker.get('ordinary_gateway',{}).get('operator_entry',{}).get('input')) == encoded(request['previous_input'])
        and encoded(before_stamp.get('fridaySource')) == encoded({'baseTree':before_receipt['base_tree'],'layers':before_receipt['layers']})
        and encoded(before_stamp.get('commit')) == encoded(before_receipt['commit']) and before_stamp.get('dirty') is True,
        'ordinary_current_successor_before_native_join_changed')
    previous_script = before_marker['ordinary_gateway']['operator_entry'].get('script')
    f.require(type(previous_script) is dict and set(previous_script) == {'path','sha256'}
        and type(previous_script['path']) is str
        and str(f.canonical(previous_script['path'])) == previous_script['path']
        and Path(previous_script['path']).parts[-2:] == ('scripts','friday_native.py')
        and previous_script['sha256'] == old['scripts/friday_native.py'],
        'ordinary_current_successor_previous_operator_changed')
    if not leaf:
        _current_source_reference(previous_script)
    if continuation:
        f.require(encoded(before_marker) == encoded(prior_edge['marker'])
            and encoded(before_stamp) == encoded(prior_edge['stamp']),
            'ordinary_current_successor_prior_metadata_changed')
    expected_receipt = json.loads(json.dumps(before_receipt)); expected_files = expected_receipt['files']
    f.require(not second or {row['path'] for row in rows} == set(CURRENT_SOURCE_SECOND_NATIVE),
        'ordinary_current_successor_exact_second_native_scope_required')
    f.require(not third or {row['path'] for row in rows} == set(CURRENT_SOURCE_THIRD_NATIVE),
        'ordinary_current_successor_exact_third_native_scope_required')
    f.require(not fourth or {row['path'] for row in rows} == set(CURRENT_SOURCE_FOURTH_NATIVE),
        'ordinary_current_successor_exact_fourth_native_scope_required')
    f.require(not fifth or {row['path'] for row in rows} == set(CURRENT_SOURCE_FIFTH_NATIVE),
        'ordinary_current_successor_exact_fifth_native_scope_required')
    f.require(not sixth or {row['path'] for row in rows} == set(CURRENT_SOURCE_SIXTH_NATIVE),
        'ordinary_current_successor_exact_sixth_native_scope_required')
    f.require(not seventh or {row['path'] for row in rows} == set(CURRENT_SOURCE_SEVENTH_NATIVE),
        'ordinary_current_successor_exact_seventh_native_scope_required')
    f.require(not eighth or {row['path'] for row in rows} == set(CURRENT_SOURCE_EIGHTH_NATIVE),
        'ordinary_current_successor_exact_eighth_native_scope_required')
    f.require(not ninth or {row['path'] for row in rows} == set(CURRENT_SOURCE_NINTH_NATIVE),
        'ordinary_current_successor_exact_ninth_native_scope_required')
    f.require(not tenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_TENTH_NATIVE),
        'ordinary_current_successor_exact_tenth_native_scope_required')
    f.require(not eleventh or {row['path'] for row in rows} == set(CURRENT_SOURCE_ELEVENTH_NATIVE),
        'ordinary_current_successor_exact_eleventh_native_scope_required')
    f.require(not twelfth or {row['path'] for row in rows} == set(CURRENT_SOURCE_TWELFTH_NATIVE),
        'ordinary_current_successor_exact_twelfth_native_scope_required')
    f.require(not thirteenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_THIRTEENTH_NATIVE),
        'ordinary_current_successor_exact_thirteenth_native_scope_required')
    f.require(not fourteenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_FOURTEENTH_NATIVE),
        'ordinary_current_successor_exact_fourteenth_native_scope_required')
    f.require(not fifteenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_FIFTEENTH_NATIVE),
        'ordinary_current_successor_exact_fifteenth_native_scope_required')
    f.require(not sixteenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_SIXTEENTH_NATIVE),
        'ordinary_current_successor_exact_sixteenth_native_scope_required')
    f.require(not seventeenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_SEVENTEENTH_NATIVE),
        'ordinary_current_successor_exact_seventeenth_native_scope_required')
    f.require(not eighteenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_EIGHTEENTH_NATIVE),
        'ordinary_current_successor_exact_eighteenth_native_scope_required')
    f.require(not nineteenth or {row['path'] for row in rows} == set(CURRENT_SOURCE_NINETEENTH_NATIVE),
        'ordinary_current_successor_exact_nineteenth_native_scope_required')
    for row in rows:
        name = row['path']; prior = expected_files.get(name)
        f.require(type(row.get('new_file')) is bool and row['new_file'] is (prior is None)
            and row.get('before_sha256') == (None if prior is None else prior['sha256'])
            and type(row.get('bytes')) is int and row['bytes'] >= 0 and row.get('mode') == '100644'
            and type(row.get('sha256')) is str and len(row['sha256']) == 64
            and all(c in '0123456789abcdef' for c in row['sha256']),
            'ordinary_current_successor_native_preimage_changed')
        if second:
            f.require(row['new_file'] is False
                and (row['before_sha256'],row['sha256']) == CURRENT_SOURCE_SECOND_NATIVE[name],
                'ordinary_current_successor_exact_second_native_images_required')
        if third:
            f.require(row['new_file'] is False
                and (row['before_sha256'],row['sha256']) == CURRENT_SOURCE_THIRD_NATIVE[name],
                'ordinary_current_successor_exact_third_native_images_required')
        if fourth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_FOURTH_NATIVE[name],
                'ordinary_current_successor_exact_fourth_native_images_required')
        if fifth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_FIFTH_NATIVE[name],
                'ordinary_current_successor_exact_fifth_native_images_required')
        if sixth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_SIXTH_NATIVE[name],
                'ordinary_current_successor_exact_sixth_native_images_required')
        if seventh:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_SEVENTH_NATIVE[name],
                'ordinary_current_successor_exact_seventh_native_images_required')
        if eighth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_EIGHTH_NATIVE[name],
                'ordinary_current_successor_exact_eighth_native_images_required')
        if ninth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_NINTH_NATIVE[name],
                'ordinary_current_successor_exact_ninth_native_images_required')
        if tenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_TENTH_NATIVE[name],
                'ordinary_current_successor_exact_tenth_native_images_required')
        if eleventh:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_ELEVENTH_NATIVE[name],
                'ordinary_current_successor_exact_eleventh_native_images_required')
        if twelfth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_TWELFTH_NATIVE[name],
                'ordinary_current_successor_exact_twelfth_native_images_required')
        if thirteenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_THIRTEENTH_NATIVE[name],
                'ordinary_current_successor_exact_thirteenth_native_images_required')
        if fourteenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_FOURTEENTH_NATIVE[name],
                'ordinary_current_successor_exact_fourteenth_native_images_required')
        if fifteenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_FIFTEENTH_NATIVE[name],
                'ordinary_current_successor_exact_fifteenth_native_images_required')
        if sixteenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_SIXTEENTH_NATIVE[name],
                'ordinary_current_successor_exact_sixteenth_native_images_required')
        if seventeenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_SEVENTEENTH_NATIVE[name],
                'ordinary_current_successor_exact_seventeenth_native_images_required')
        if eighteenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_EIGHTEENTH_NATIVE[name],
                'ordinary_current_successor_exact_eighteenth_native_images_required')
        if nineteenth:
            f.require((row['before_sha256'],row['sha256'],row['bytes'],row['new_file']) == CURRENT_SOURCE_NINETEENTH_NATIVE[name],
                'ordinary_current_successor_exact_nineteenth_native_images_required')
        after = dict(prior) if prior is not None else {}
        after.update({'sha256':row['sha256'],'bytes':row['bytes'],'mode':'100644'}); expected_files[name] = after
    f.require(not fourth or len(expected_files) == 17890,
        'ordinary_current_successor_exact_fourth_native_count_required')
    f.require(not fifth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_fifth_native_count_required')
    f.require(not sixth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_sixth_native_count_required')
    f.require(not seventh or len(expected_files) == 17891,
        'ordinary_current_successor_exact_seventh_native_count_required')
    f.require(not eighth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_eighth_native_count_required')
    f.require(not ninth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_ninth_native_count_required')
    f.require(not tenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_tenth_native_count_required')
    f.require(not eleventh or len(expected_files) == 17891,
        'ordinary_current_successor_exact_eleventh_native_count_required')
    f.require(not twelfth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_twelfth_native_count_required')
    f.require(not thirteenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_thirteenth_native_count_required')
    f.require(not fourteenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_fourteenth_native_count_required')
    f.require(not fifteenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_fifteenth_native_count_required')
    f.require(not sixteenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_sixteenth_native_count_required')
    f.require(not seventeenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_seventeenth_native_count_required')
    f.require(not eighteenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_eighteenth_native_count_required')
    f.require(not nineteenth or len(expected_files) == 17891,
        'ordinary_current_successor_exact_nineteenth_native_count_required')
    expected_receipt['layers'].append({'manifest':manifest_name,'manifest_sha256':files[manifest_name],
        'patch_sha256':files[patch_name]})
    expected_receipt['sources_lock_sha256'] = current['sources_lock']['sha256']
    receipt_path = tx/'hermes-agent.source.json' if historical_marker is not None else home/'hermes-agent.source.json'
    stamp_path = tx/'install-stamp.json' if historical_marker is not None else source/'install-stamp.json'
    receipt = _current_source_json(receipt_path); receipt_sha = f.digest(f.owned_file(receipt_path,private=True))
    stamp = _current_source_json(stamp_path)
    expected_stamp = dict(before_stamp)
    expected_stamp['fridaySource'] = {'baseTree':expected_receipt['base_tree'],'layers':expected_receipt['layers']}
    selected = request['current_input'] if leaf else request['previous_input']; selected_files = files if leaf else old
    f.require(encoded(receipt) == encoded(expected_receipt if leaf else before_receipt)
        and encoded(stamp) == encoded(expected_stamp if leaf else before_stamp)
        and (not leaf or len(receipt['layers']) == before_layers + 1)
        and (commit is None or commit['source_receipt_sha256'] == receipt_sha),
        'ordinary_current_successor_native_after_changed')
    if intent is not None:
        f.require(encoded(intent['layers']) == encoded([manifest_name]) and encoded(intent['files']) == encoded(touched)
            and (commit is None or encoded(commit['layers']) == encoded([manifest_name])
                and encoded(commit['files']) == encoded(touched)), 'ordinary_current_successor_journal_native_scope_changed')
    plugins = {n:h for n,h in selected_files.items() if n.startswith('plugins/friday_rework/')}
    f.require(len(plugins) == 52 and encoded(before_marker.get('plugin_files')) == encoded(plugins)
        and marker.get('schema') == f.SCHEMA and marker.get('home') == str(home) and marker.get('source') == str(source)
        and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE' and marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('runtime_ready') is False and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('input_sha256') == selected['sha256'] and marker.get('source_receipt_sha256') == receipt_sha
        and marker.get('ordinary_gateway',{}).get('source_receipt_sha256') == receipt_sha
        and encoded(marker.get('plugin_files')) == encoded(plugins), 'ordinary_current_successor_marker_changed')
    if leaf:
        expected_marker = json.loads(json.dumps(before_marker))
        expected_marker['input_sha256'] = request['current_input']['sha256']; expected_marker['source_receipt_sha256'] = receipt_sha
        expected_marker['ordinary_gateway']['source_receipt_sha256'] = receipt_sha
        expected_marker['ordinary_gateway']['operator_entry'] = {'input':request['current_input'],
            'script':{'path':str(Path(request['candidate_project'])/'scripts/friday_native.py'),
                'sha256':files['scripts/friday_native.py']}}
        # Keep the published CP afterimage immutable and exact. The native
        # five-file declaration writer later refreshes only the root config's
        # raw serialization pin; native ordinary.check deliberately validates
        # that config semantically, including its permitted onboarding/theme
        # edits. Never let a later marker replace the original deployment seal.
        staged_marker = _current_source_json(tx/'FRIDAY-INSTALL.json')
        profile_files = marker.get('profile_files')
        f.require(type(profile_files) is dict and type(profile_files.get('config.yaml')) is str
            and len(profile_files['config.yaml']) == 64
            and all(c in '0123456789abcdef' for c in profile_files['config.yaml']),
            'ordinary_current_successor_native_config_metadata_changed')
        source_marker = json.loads(json.dumps(marker))
        source_marker['profile_files']['config.yaml'] = expected_marker['profile_files']['config.yaml']
        f.require(encoded(staged_marker) == encoded(expected_marker)
            and f.owned_file(tx/'FRIDAY-INSTALL.json',private=True) == encoded(expected_marker)
            and encoded(source_marker) == encoded(expected_marker)
            and f.digest(f.owned_file(tx/'hermes-agent.source.json',private=True)) == receipt_sha
            and f.digest(f.owned_file(tx/'install-stamp.json',private=True)) == f.digest(f.owned_file(stamp_path,private=True)),
            'ordinary_current_successor_metadata_afterimage_changed')
    if historical_marker is not None:
        return {'request':request,'value':current,'receipt':receipt,'receipt_sha256':receipt_sha,
            'stamp':stamp,'stamp_sha256':f.digest(f.owned_file(stamp_path,private=True)),'marker':marker}
    checked_plugin_inventory(home,plugins)
    lock = _current_source_json(_current_source_reference(current['sources_lock']))
    donors = {row['id']:row for row in lock['repositories']}
    f.require({'hermes','dsh','a0'} <= set(donors),'complete_donor_pins_required')
    f.composition_checked(current if leaf else previous,source,receipt,donors['hermes'])
    if 'tls' in current['product']['dashboard']:
        expected_tls = {relative:current['dashboard_tls'][key]['sha256'] for key,relative in current['product']['dashboard']['tls'].items()}
        f.require(encoded(marker.get('tls_files')) == encoded(expected_tls)
            and all(f.digest(f.owned_file(home/n,private=True)) == sha for n,sha in expected_tls.items()),'installed_dashboard_tls_changed')
    f.native_packages(source)
    from hermes_cli.friday_ordinary_gateway import check
    from hermes_cli.friday_user_scope import authority
    with authority(home): check(home,role=False)
    return home,donors


def project_current_source_checked(value, *, cli_only, project_update=None, source_update=None):
    """Current project source, never archival installation or worker preparation.

    Before commit, only the explicit typed publisher context selects this path.
    Afterwards the canonical transaction and exact current marker select it.
    An occupied but incomplete purported transaction is a refusal, never fallback.
    """
    f = api()
    f.require(project_update is None or source_update is None,'ordinary_current_successor_conflicting_context')
    if project_update is None:
        successor = current_native_source_successor_checked(value,cli_only=cli_only,source_update=source_update)
        if successor is not None: return successor
    if type(value) is not dict or type(value.get('home')) is not str:
        f.require(project_update is None,'ordinary_project_current_source_value_required')
        return None
    home = Path(value['home'])
    tx = home/'preparation'/('ordinary-source-update-'+PROJECT_DSH_CURRENT_INPUT)
    if project_update is None and not os.path.lexists(tx): return None
    f.require(cli_only is True,'ordinary_project_current_source_cli_only_required')
    home = f.directory(f.canonical(str(home))); source = f.directory(home/'hermes-agent')
    committed_context = project_update is None
    if committed_context:
        f.directory(tx)
        f.require(not os.path.lexists(tx/'rolled-back.json'),'ordinary_project_current_source_rolled_back')
        intent = f.read_json(tx/'intent.json'); committed = f.read_json(tx/'committed.json')
        intent_fields = {'schema','state','project_only','native_source_unchanged','request_reference',
            'request_sha256','seconds','previous_input','current_input','publication_ancestor','reviewed_delta',
            'gateway_started','workers_enabled','before'}
        commit_fields = {'schema','state','project_only','native_source_unchanged','request_reference',
            'request_sha256','previous_input','current_input','source_receipt_sha256','gateway_started','workers_enabled'}
        f.require(type(intent) is dict and set(intent) == intent_fields
            and type(committed) is dict and set(committed) == commit_fields
            and intent['state'] == 'SOURCE_UPDATE_CONSUMED_NO_RETRY'
            and committed['state'] == 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
            and all(body['schema'] == 'friday.ordinary-telegram-source-update-transaction.v1'
                and body['project_only'] is True and body['native_source_unchanged'] is True
                and body['gateway_started'] is False and body['workers_enabled'] is False
                for body in (intent,committed)), 'ordinary_project_current_source_committed_proof_required')
        request_ref = intent['request_reference']
        f.require(type(request_ref) is dict and set(request_ref) == {'path','sha256'}
            and encoded(committed['request_reference']) == encoded(request_ref)
            and intent['request_sha256'] == committed['request_sha256'] == request_ref['sha256'],
            'ordinary_project_current_source_request_binding_changed')
        request = f.read_json(f.pin(request_ref))
    else:
        request = project_update
    project_current_request_metadata(request)
    f.require(request['home'] == str(home),'ordinary_project_current_source_home_changed')
    previous = f.read_json(f.pin(request['previous_input']))
    current = f.read_json(f.pin(request['current_input']))
    f.require(encoded(value) == encoded(current) and current.get('home') == str(home)
        and encoded(current['product']['runtime']) == encoded({'enabled':False}) and current['product']['runtime']['enabled'] is False,
        'ordinary_project_current_source_exact_value_required')
    plugins_after = project_current_delta(request,previous,current)
    if committed_context:
        f.require(all(encoded(body['previous_input']) == encoded(request['previous_input'])
            and encoded(body['current_input']) == encoded(request['current_input']) for body in (intent,committed))
            and encoded(intent['seconds']) == encoded(request['seconds'])
            and encoded(intent['publication_ancestor']) == encoded(request['publication_ancestor'])
            and encoded(intent['reviewed_delta']) == encoded(request['reviewed_delta'])
            and committed['source_receipt_sha256'] == PROJECT_DSH_CURRENT_RECEIPT,
            'ordinary_project_current_source_commit_binding_changed')
        before = intent['before']; expected_names = set(plugins_after) | {f.MARKER}
        f.require(type(before) is dict and set(before) == expected_names
            and type(before[f.MARKER]) is dict and set(before[f.MARKER]) == {'sha256','mode'}
            and before[f.MARKER]['sha256'] == request['marker']['sha256']
            and type(before[f.MARKER]['mode']) is int and before[f.MARKER]['mode'] in (0o600,0o644)
            and all(before[n] is None if previous['project_files'].get(n) is None else
                type(before[n]) is dict and set(before[n]) == {'sha256','mode'}
                and before[n]['sha256'] == previous['project_files'][n]
                and type(before[n]['mode']) is int and before[n]['mode'] in (0o600,0o644)
                for n in plugins_after), 'ordinary_project_current_source_before_metadata_changed')
    # Old installer leaf references are inert metadata authenticated by the exact
    # old198 input. Only the current project and source lock are consumed here.
    files = current['project_files']
    f.require(len(files) == 477 and Path(f.__file__).resolve() == f.ROOT/'scripts/friday_install.py'
        and f.digest(f.owned_file(Path(f.__file__).resolve())) == files['scripts/friday_install.py'],
        'ordinary_project_current_source_consumer_origin_changed')
    for name,expected in files.items():
        path = Path(name)
        f.require(type(name) is str and not path.is_absolute() and name == path.as_posix()
            and not any(part in ('.','..') for part in path.parts)
            and type(expected) is str and len(expected) == 64
            and all(c in '0123456789abcdef' for c in expected)
            and f.digest(f.owned_file(f.ROOT/name)) == expected,
            'ordinary_project_current_source_pin_changed')
    required = {str(p.relative_to(f.ROOT)) for relative in ('plugins/friday_rework','patches/hermes')
        for p in (f.ROOT/relative).rglob('*') if p.is_file() or p.is_symlink()}
    f.require(required <= set(files),'ordinary_project_current_source_extra_file')
    lock = f.read_json(f.pin(current['sources_lock']))
    donors = {row['id']:row for row in lock['repositories']}
    f.require({'hermes','dsh','a0'} <= set(donors),'complete_donor_pins_required')
    f.require(encoded(request['source_receipt']) == encoded({'path':str(home/'hermes-agent.source.json'),
            'sha256':PROJECT_DSH_CURRENT_RECEIPT})
        and encoded(request['stamp']) == encoded({'path':str(source/'install-stamp.json'),'sha256':PROJECT_DSH_CURRENT_STAMP})
        and f.digest(f.owned_file(home/'hermes-agent.source.json',private=True)) == PROJECT_DSH_CURRENT_RECEIPT
        and f.digest(f.owned_file(source/'install-stamp.json',private=True)) == PROJECT_DSH_CURRENT_STAMP,
        'ordinary_project_current_source_native_pins_changed')
    receipt = f.read_json(home/'hermes-agent.source.json')
    stamp = f.read_json(source/'install-stamp.json')
    f.require(len(receipt.get('layers',[])) == 198 and len(receipt.get('files',{})) == 17888
        and receipt.get('source_file_count') == 17730
        and encoded(stamp.get('fridaySource')) == encoded({'baseTree':receipt['base_tree'],'layers':receipt['layers']})
        and encoded(stamp.get('commit')) == encoded(receipt['commit']) and stamp.get('dirty') is True,
        'ordinary_project_current_source_native_identity_changed')
    f.composition_checked(current,source,receipt,donors['hermes'])
    project_current_history(home,request)
    marker_raw = f.owned_file(home/f.MARKER,private=True); marker = f.read_json(home/f.MARKER)
    installed = request['current_input'] if marker.get('input_sha256') == request['current_input']['sha256'] else request['previous_input']
    installed_files = files if encoded(installed) == encoded(request['current_input']) else previous['project_files']
    f.require(marker.get('schema') == f.SCHEMA and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE'
        and marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('home') == str(home) and marker.get('source') == str(source)
        and marker.get('runtime_ready') is False and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('input_sha256') == installed['sha256']
        and (not committed_context or encoded(installed) == encoded(request['current_input']))
        and (encoded(installed) == encoded(request['current_input']) or f.digest(marker_raw) == request['marker']['sha256'])
        and marker.get('source_receipt_sha256') == PROJECT_DSH_CURRENT_RECEIPT,
        'ordinary_project_current_source_marker_changed')
    ancestor = f.read_json(f.pin(request['publication_ancestor']['request']))
    operator_root = f.ROOT if encoded(installed) == encoded(request['current_input']) else Path(ancestor['candidate_project'])
    f.require(encoded(marker.get('ordinary_gateway',{}).get('operator_entry')) == encoded({'input':installed,
            'script':{'path':str(operator_root/'scripts/friday_native.py'),
                'sha256':installed_files['scripts/friday_native.py']}})
        and marker['ordinary_gateway'].get('source_receipt_sha256') == PROJECT_DSH_CURRENT_RECEIPT,
        'ordinary_project_current_source_operator_entry_changed')
    plugins = {n:h for n,h in installed_files.items() if n.startswith('plugins/friday_rework/')}
    f.require(encoded(marker.get('plugin_files')) == encoded(plugins),'ordinary_project_current_source_plugin_marker_changed')
    checked_plugin_inventory(home,plugins)
    if 'tls' in current['product']['dashboard']:
        expected_tls = {relative:current['dashboard_tls'][key]['sha256']
            for key,relative in current['product']['dashboard']['tls'].items()}
        f.require(encoded(marker.get('tls_files')) == encoded(expected_tls)
            and all(f.digest(f.owned_file(home/n,private=True)) == sha for n,sha in expected_tls.items()),
            'installed_dashboard_tls_changed')
    f.native_packages(source)
    from hermes_cli.friday_ordinary_gateway import check
    from hermes_cli.friday_user_scope import authority
    with authority(home): check(home,role=False)
    return home,donors


def project_current_delta(request, previous, current, *, check_origin=True):
    """Bind the reviewed final hashes without widening historical project predicates."""
    f = api(); delta = f.read_json(f.pin(request['reviewed_delta']))
    old = previous.get('project_files'); new = current.get('project_files')
    f.require(type(old) is dict and type(new) is dict
        and request['previous_input']['sha256'] == PROJECT_DSH_CURRENT_INPUT
        and len(old) == 476 and len(new) == 477
        and f.digest(encoded(old)) == PROJECT_DSH_CURRENT_INVENTORY
        and encoded({k:v for k,v in previous.items() if k != 'project_files'}) ==
            encoded({k:v for k,v in current.items() if k != 'project_files'})
        and set(new) == set(old) | {PROJECT_DSH_CURRENT_ADDITION}
        and PROJECT_DSH_CURRENT_ADDITION not in old,
        'ordinary_project_exact_current198_inventory_required')
    f.require(type(delta) is dict and set(delta) == {'schema','previous_input_sha256',
        'previous_project_files_sha256','source_receipt_sha256','native_layers','native_files',
        'project_file_updates'} and delta['schema'] == PROJECT_DSH_CURRENT_DELTA_SCHEMA
        and delta['previous_input_sha256'] == PROJECT_DSH_CURRENT_INPUT
        and delta['previous_project_files_sha256'] == PROJECT_DSH_CURRENT_INVENTORY
        and delta['source_receipt_sha256'] == PROJECT_DSH_CURRENT_RECEIPT
        and type(delta['native_layers']) is int and delta['native_layers'] == 198
        and type(delta['native_files']) is int and delta['native_files'] == 17888,
        'ordinary_project_reviewed_current198_delta_required')
    rows = delta['project_file_updates']
    f.require(type(rows) is list and all(type(row) is dict and set(row) ==
        {'path','before_sha256','after_sha256'} and type(row['path']) is str for row in rows),
        'ordinary_project_exact_reviewed_delta_rows_required')
    names = [row['path'] for row in rows]
    changed = {n for n in new if new[n] != old.get(n)}
    plugins = changed - PROJECT_DSH_CURRENT_HELPERS
    f.require(names == sorted(set(names)) and set(names) == changed
        and PROJECT_DSH_CURRENT_REQUIRED | {PROJECT_DSH_CURRENT_ADDITION} <= plugins
        and plugins <= PROJECT_DSH_CURRENT_REQUIRED | PROJECT_DSH_CURRENT_OPTIONAL | {PROJECT_DSH_CURRENT_ADDITION}
        and PROJECT_DSH_CURRENT_HELPERS <= changed
        and all(row['before_sha256'] == old.get(row['path'])
            and row['after_sha256'] == new[row['path']]
            and type(row['after_sha256']) is str and len(row['after_sha256']) == 64
            and all(c in '0123456789abcdef' for c in row['after_sha256'])
            for row in rows), 'ordinary_project_exact_reviewed_current198_delta_required')
    if check_origin:
        f.require(Path(__file__).resolve() == f.ROOT/PROJECT_DSH_CURRENT_HELPER
            and f.digest(f.owned_file(Path(__file__).resolve())) == new[PROJECT_DSH_CURRENT_HELPER],
            'ordinary_project_exact_current198_helper_origin_required')
    return {n:new[n] for n in sorted(plugins)}


def project_current_history(home, request):
    """Authenticate the actual V3 commit and retain its engineering ancestry unchanged."""
    f = api(); refs = request['publication_ancestor']
    f.require(type(refs) is dict and set(refs) == set(PROJECT_DSH_CURRENT_ANCESTOR)
        and all(type(refs[n]) is dict and refs[n].get('sha256') == sha
            for n,sha in PROJECT_DSH_CURRENT_ANCESTOR.items())
        and encoded(request['predecessor_update']) == encoded(refs['request']),
        'ordinary_project_exact_current198_ancestor_required')
    paths = {n:f.pin(ref) for n,ref in refs.items()}
    old = f.read_json(paths['request'])
    tx = home/'preparation'/('ordinary-source-update-v45-'+refs['request']['sha256'][:16])
    f.require(paths['intent'] == tx/'intent.json' and paths['committed'] == tx/'committed.json'
        and not os.path.lexists(tx/'rolled-back.json')
        and old.get('schema') == 'friday.ordinary-telegram-source-update.v46'
        and old.get('home') == str(home) and encoded(old.get('current_input')) == encoded(request['previous_input'])
        and old.get('project_inventory_sha256') == PROJECT_DSH_CURRENT_INVENTORY,
        'ordinary_project_exact_current198_predecessor_required')
    intent = f.read_json(paths['intent']); committed = f.read_json(paths['committed'])
    f.require(intent.get('state') == 'SOURCE_UPDATE_INTENT'
        and committed.get('state') == 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
        and all(body.get('schema') == 'friday.ordinary-telegram-source-update-transaction.v1'
            and body.get('request_sha256') == refs['request']['sha256']
            and encoded(body.get('previous_input')) == encoded(old['previous_input'])
            and encoded(body.get('current_input')) == encoded(request['previous_input'])
            and body.get('gateway_started') is False and body.get('workers_enabled') is False
            for body in (intent,committed))
        and committed.get('source_receipt_sha256') == request['source_receipt']['sha256']
            == PROJECT_DSH_CURRENT_RECEIPT
        and encoded(intent.get('source_receipt')) == encoded(old['source_receipt']),
        'ordinary_project_current198_commit_binding_changed')
    for field,name in {'source_receipt':'hermes-agent.source.json','marker':'FRIDAY-INSTALL.json',
            'stamp':'hermes-agent/install-stamp.json'}.items():
        f.require(f.digest(f.owned_file(tx/'before'/name,private=True)) == old[field]['sha256'],
            'ordinary_project_current198_original_beforeimage_changed')
    before_receipt = f.read_json(tx/'before/hermes-agent.source.json')
    before_marker = f.read_json(tx/'before/FRIDAY-INSTALL.json')
    f.require(len(before_receipt.get('layers',[])) == 197
        and before_marker.get('input_sha256') == old['previous_input']['sha256']
        and before_marker.get('source_receipt_sha256') == old['source_receipt']['sha256']
        and f.digest(f.owned_file(tx/'hermes-agent.source.json',private=True)) == PROJECT_DSH_CURRENT_RECEIPT
        and f.digest(f.owned_file(tx/'install-stamp.json',private=True)) == request['stamp']['sha256']
            == PROJECT_DSH_CURRENT_STAMP, 'ordinary_project_current198_original_images_changed')
    # The original engineering156 request/receipt remain historical facts. In
    # particular its after[] receipt and later corrected receipt are not conflated.
    engineering_ref = old['predecessor_request']; engineering = f.read_json(f.pin(engineering_ref))
    engineering_tx = home/'preparation'/('ordinary-source-update-successor-'+engineering_ref['sha256'])
    f.require(Path(engineering_ref['path']) == engineering_tx/'request.json'
        and engineering.get('schema') == 'frw.root.engineering152-successor-request.v1'
        and engineering.get('home') == str(home)
        and engineering.get('current_input',{}).get('sha256') == old['predecessor_current_input_sha256'],
        'ordinary_project_current198_engineering_ancestor_changed')
    engineering_commit = f.read_json(engineering_tx/'committed.json')
    f.require(engineering_commit.get('state') == 'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
        and encoded(engineering_commit.get('current_input')) == encoded(engineering['current_input'])
        and encoded(engineering_commit.get('previous_input')) == encoded(engineering['previous_input'])
        and engineering_commit.get('source_receipt_sha256') == old['predecessor_receipt_sha256']
        and engineering_commit.get('gateway_started') is False
        and engineering_commit.get('workers_enabled') is False
        and not os.path.lexists(engineering_tx/'rolled-back.json'),
        'ordinary_project_current198_engineering_commit_changed')
    f.pin(old['previous_input']); f.pin(old['current_input'])
    actual = {}; base = {}
    roots = (TRANSACTION,'preparation/ordinary-gateway-archive',
        str(engineering_tx.relative_to(home)),str(tx.relative_to(home)))
    for index,name in enumerate(roots):
        for path in f.directory(home/name).rglob('*'):
            f.require(not path.is_symlink(),'ordinary_update_history_link_refused')
            if path.is_dir(): f.directory(path)
            else:
                key = str(path.relative_to(home)); actual[key] = f.digest(f.owned_file(path,private=True))
                if index < 2: base[key] = actual[key]
    f.require(encoded(base) == encoded(old['transaction_history']) and type(request['transaction_history']) is dict
        and encoded(actual) == encoded(request['transaction_history'])
        and f.read_json(home/TRANSACTION/'committed.json').get('state') ==
            'SOURCE_ACTIVATED_NOT_RUNTIME_ACCEPTED', 'ordinary_project_current198_history_changed')
    return actual


@contextlib.contextmanager
def project_current_admission_locks(home, budget):
    """Retain existing admission locks in every native root/named-profile store.

    No PluginState constructor property that initializes storage is used. The
    existing native readonly directory API resolves the namespace under authority.
    """
    from hermes_cli.plugins_state import PluginState
    from hermes_cli.friday_user_scope import authority
    f = api(); profiles = f.directory(home/'profiles')
    names = sorted(p.name for p in profiles.iterdir())
    homes = [home]+[f.directory(profiles/n) for n in names]
    held = []; directories = {}
    def identity(path):
        f.directory(path); s = path.lstat()
        return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_mode'))
    directories[profiles] = identity(profiles)
    try:
        for profile_home in homes:
            budget.check(reserve=15)
            with authority(profile_home):
                directory = PluginState('friday_rework').directory_storage_readonly
            f.require(directory.parent == profile_home/'plugin-data',
                'ordinary_project_current198_admission_scope_changed')
            for path in (profile_home,directory.parent,directory): directories[path] = identity(path)
            path = directory/'admission.lock'; state = update_file_state(path)
            f.require(state is not None and state['data'] == b'v1\n' and state['mode'] == 0o600,
                'ordinary_project_current198_existing_admission_required')
            fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
            try:
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                info = os.fstat(fd)
                f.require(tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_nlink','st_mode'))
                    == state['identity'],'ordinary_project_current198_admission_identity_changed')
            except BaseException:
                os.close(fd); raise
            held.append((path,fd,state))
        def prove():
            f.require(sorted(p.name for p in profiles.iterdir()) == names
                and all(identity(p) == value for p,value in directories.items()),
                'ordinary_project_current198_profile_custody_changed')
            for path,fd,state in held:
                info = os.fstat(fd)
                f.require(tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_nlink','st_mode'))
                    == state['identity'] and same_update_file(path,state),
                    'ordinary_project_current198_admission_identity_changed')
        prove(); yield prove; prove()
    finally:
        for path,fd,state in reversed(held): os.close(fd)


def project_current_inputs(request, budget):
    """Exact current198 admission; the v1-v5 validators below stay unchanged."""
    f = api(); budget.check(reserve=15)
    fields = {'schema','seconds','home','previous_input','current_input','marker','source_receipt',
        'stamp','configuration','profile','launcher','credential_files','native_unit',
        'transaction_history','predecessor_update','publication_ancestor','reviewed_delta'}
    f.require(type(request) is dict and set(request) == fields
        and request['schema'] == PROJECT_DSH_CURRENT_SCHEMA
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 7200,
        'ordinary_project_current198_explicit_request_required')
    home = f.directory(f.canonical(request['home'])); source = f.directory(home/'hermes-agent')
    f.require(os.environ.get('HERMES_HOME') == str(home),'ordinary_update_exact_environment_required')
    paths = {name:budget.call(f.pin,request[name]) for name in ('previous_input','current_input',
        'marker','source_receipt','stamp','configuration','profile','launcher','native_unit')}
    for name,path in {'marker':home/f.MARKER,'source_receipt':home/'hermes-agent.source.json',
        'stamp':source/'install-stamp.json','configuration':home/'config.yaml',
        'profile':home/'FRIDAY-PROFILE.json','launcher':source/'.hermes/bin/hermes'}.items():
        f.require(paths[name] == path,'ordinary_update_exact_installed_inputs_required')
    previous = f.read_json(paths['previous_input']); current = f.read_json(paths['current_input'])
    expected = project_current_delta(request,previous,current)
    f.require(current.get('home') == str(home) and encoded(current['product']['runtime']) == encoded({'enabled':False}) and current['product']['runtime']['enabled'] is False
        and encoded(request['previous_input']) != encoded(request['current_input']),
        'ordinary_update_operational_settings_changed')
    _,donors = budget.call(f.spec_checked,current,cli_only=True,project_update=request)
    marker = f.read_json(paths['marker']); receipt = f.read_json(paths['source_receipt'])
    plugins = {n:h for n,h in previous['project_files'].items() if n.startswith('plugins/friday_rework/')}
    f.require(marker.get('schema') == f.SCHEMA and marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE'
        and marker.get('home') == str(home) and marker.get('source') == str(source)
        and marker.get('runtime_ready') is False
        and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('input_sha256') == PROJECT_DSH_CURRENT_INPUT
        and marker.get('source_receipt_sha256') == request['source_receipt']['sha256'] == PROJECT_DSH_CURRENT_RECEIPT
        and request['stamp']['sha256'] == PROJECT_DSH_CURRENT_STAMP
        and marker.get('ordinary_gateway',{}).get('source_receipt_sha256') == PROJECT_DSH_CURRENT_RECEIPT
        and encoded(marker['ordinary_gateway'].get('operator_entry',{}).get('input')) == encoded(request['previous_input'])
        and encoded(marker.get('plugin_files')) == encoded(plugins) and len(plugins) == 51
        and len(receipt.get('layers',[])) == 198 and len(receipt.get('files',{})) == 17888
        and receipt.get('source_file_count') == 17730,
        'ordinary_project_exact_current198_installed_required')
    old_entry = marker['ordinary_gateway']['operator_entry']['script']
    old_script = f.pin(old_entry)
    ancestor = f.read_json(f.pin(request['publication_ancestor']['request']))
    f.require(old_script == Path(ancestor['candidate_project'])/'scripts/friday_native.py'
        and old_entry['sha256'] == previous['project_files']['scripts/friday_native.py'],
        'ordinary_project_current198_previous_operator_changed')
    checked_plugin_inventory(home,plugins)
    for name in expected:
        f.require(f.digest(f.owned_file(f.ROOT/name)) == expected[name],
            'ordinary_update_worker_plugin_source_changed')
    budget.call(f.composition_checked,previous,source,receipt,donors['hermes'])
    budget.call(f.composition_checked,current,source,receipt,donors['hermes'])
    project_current_history(home,request)
    f.require(all(f.digest(f.owned_file(home/name,private=True)) == sha
        for name,sha in marker['profile_files'].items() if name != 'config.yaml'),
        'ordinary_update_profile_changed')
    credentials = request['credential_files']
    f.require(type(credentials) is dict and set(credentials) == {'.env','auth.json'},
        'ordinary_update_credential_pins_required')
    for name,ref in credentials.items():
        f.require(not os.path.lexists(home/name) if ref is None else f.pin(ref) == home/name,
            'ordinary_update_credential_pin_changed')
    f.native_packages(source)
    from hermes_cli.friday_ordinary_gateway import check
    check(home,role=False)
    tx = home/'preparation'/('ordinary-source-update-'+request['previous_input']['sha256'])
    f.directory(tx.parent)
    f.require(not os.path.lexists(tx),'ordinary_update_consumed_no_retry')
    return home,source,previous,current,marker,receipt,donors,tx


def project_current_update(request, request_path, budget):
    """Publish only reviewed plugin files through the existing native custody/CAS path."""
    import copy
    f = api(); home = f.directory(f.canonical(request['home']))
    fd = os.open(home,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW); directories = None
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        home,source,previous,current,marker,receipt,donors,tx = project_current_inputs(request,budget)
        expected = project_current_delta(request,previous,current)
        names = [*sorted(expected),f.MARKER]
        pm_name = 'installs/'+f.digest(str(source).encode('utf-8'))[:16]+'/.install.lock'
        directories = SourceUpdateDirectories(home,[*names,'preparation/.project-only-custody',
            'hermes-agent/.project-only-custody',pm_name],set())
        f.require(SourceUpdateDirectories.identity(os.fstat(fd)) == directories.identities[''],
            'ordinary_project_home_lock_generation_changed')
        with stopped_consumers(home,request['native_unit'],budget) as native_prove, \
                retained_build_lock(source) as build_prove, retained_pm_lock(home,source) as pm_prove, \
                project_current_admission_locks(home,budget) as admission_prove:
            from gateway import host_rendezvous as hr
            role_directory = f.directory(hr.host_state_dir())
            role_identity = SourceUpdateDirectories.identity(role_directory.lstat())
            role_states = {role:(hr.lock_path(role),update_file_state(hr.lock_path(role)))
                for role in (hr.ROLE_GATEWAY,hr.ROLE_SERVE,hr.ROLE_DESKTOP_SERVE)}
            f.require(all(state is not None and hr.owns_host_lock(role)
                for role,(path,state) in role_states.items()),'ordinary_project_native_role_custody_required')
            def prove(*,forward=True):
                f.require(SourceUpdateDirectories.identity(os.fstat(fd)) == directories.identities[''],
                    'ordinary_project_home_lock_generation_changed')
                directories.prove(); native_prove(); build_prove(); pm_prove(); admission_prove()
                f.require(SourceUpdateDirectories.identity(role_directory.lstat()) == role_identity
                    and all(hr.owns_host_lock(role) and same_update_file(path,state)
                    for role,(path,state) in role_states.items()),'ordinary_project_native_role_custody_changed')
                budget.check(reserve=15 if forward else 0)
            request_state = update_file_state(request_path)
            f.require(request_state is not None and request_state['mode'] == 0o600
                and encoded(json.loads(request_state['data'],object_pairs_hook=f.unique)) == encoded(request),
                'ordinary_update_request_changed')
            project_current_inputs(request,budget)
            saved = {n:update_file_state(home/n,directories.parent_fd(n)) for n in names}
            pins = {n:previous['project_files'].get(n) for n in expected}; pins[f.MARKER] = request['marker']['sha256']
            f.require(all((row is None and pins[n] is None) or (row is not None
                and row['mode'] in (0o600,0o644) and f.digest(row['data']) == pins[n])
                for n,row in saved.items()),'ordinary_update_beforeimage_changed')
            retained_paths = {n:Path(request[n]['path']) for n in ('previous_input','current_input',
                'source_receipt','stamp','configuration','profile','launcher','native_unit','reviewed_delta')}
            retained_paths.update({n:home/n for n in ('.env','auth.json')})
            retained = {n:update_file_state(path) for n,path in retained_paths.items()}
            f.require(all(state is not None and f.digest(state['data']) == request[n]['sha256']
                for n,state in retained.items() if n not in ('.env','auth.json')),
                'ordinary_project_retained_pin_changed')
            for n in ('.env','auth.json'):
                state = retained[n]; ref = request['credential_files'][n]
                f.require(state is None if ref is None else state is not None
                    and f.digest(state['data']) == ref['sha256'],'ordinary_update_credential_pin_changed')
            def unchanged(*,forward=True,composition=False):
                prove(forward=forward)
                f.require(same_update_file(request_path,request_state)
                    and all(same_update_file(retained_paths[n],state) for n,state in retained.items()),
                    'ordinary_project_retained_file_changed')
                project_current_history(home,request)
                if composition:
                    budget.call(f.spec_checked,current,cli_only=True,project_update=request)
                    budget.call(f.composition_checked,current,source,receipt,donors['hermes'])
                prove(forward=forward)
            updated = copy.deepcopy(marker)
            updated['input_sha256'] = request['current_input']['sha256']
            updated['plugin_files'] = {n:h for n,h in current['project_files'].items() if n.startswith('plugins/friday_rework/')}
            updated['ordinary_gateway']['operator_entry'] = {'input':request['current_input'],
                'script':{'path':str(f.ROOT/'scripts/friday_native.py'),
                    'sha256':current['project_files']['scripts/friday_native.py']}}
            plugin_data = {n:f.owned_file(f.ROOT/n) for n in sorted(expected)}
            f.require(all(f.digest(data) == expected[n] for n,data in plugin_data.items()),
                'ordinary_update_worker_plugin_source_changed')
            unchanged(composition=True)
            # The previous-input key is consumed even after rollback; changing
            # request names, hashes or seconds never creates another effect slot.
            os.mkdir(tx.name,mode=0o700,dir_fd=directories.fds['preparation'])
            before = tx/'before'; before.mkdir(mode=0o700)
            for name,row in saved.items():
                budget.check(reserve=15)
                if row is not None:
                    private_parents(before,name); write(before/name,row['data'])
            budget.check(reserve=15)
            write(tx/'intent.json',encoded({'schema':'friday.ordinary-telegram-source-update-transaction.v1',
                'state':'SOURCE_UPDATE_CONSUMED_NO_RETRY','project_only':True,'native_source_unchanged':True,
                'request_sha256':f.digest(request_state['data']),
                'request_reference':{'path':str(f.canonical(str(request_path))),'sha256':f.digest(request_state['data'])},
                'seconds':request['seconds'],
                'previous_input':request['previous_input'],'current_input':request['current_input'],
                'publication_ancestor':request['publication_ancestor'],'reviewed_delta':request['reviewed_delta'],
                'gateway_started':False,'workers_enabled':False,
                'before':{n:None if row is None else {'sha256':f.digest(row['data']),'mode':row['mode']}
                    for n,row in saved.items()}}),0o400)
            sync_directory(before); sync_directory(tx); sync_directory(tx.parent)
            owned = {}; commit_started = False
            try:
                unchanged()
                for name,data in [*plugin_data.items(),(f.MARKER,encoded(updated))]:
                    unchanged()
                    publish_update_file(home/name,data,saved[name]['mode'] if saved[name] is not None else 0o600,
                        saved[name],owned,name,parent_fd=directories.parent_fd(name))
                from hermes_cli.friday_ordinary_gateway import check
                check(home,role=False); checked_plugin_inventory(home,updated['plugin_files'])
                budget.call(f.inspect,current,request['current_input']['sha256'],project_update=request)
                unchanged(composition=True)
                f.require(all(same_update_file(home/n,owned[n],directories.parent_fd(n)) for n in names),
                    'ordinary_update_commit_ownership_changed')
                commit_started = True
                write(tx/'committed.json',encoded({'schema':'friday.ordinary-telegram-source-update-transaction.v1',
                    'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED',
                    'request_reference':{'path':str(f.canonical(str(request_path))),'sha256':f.digest(request_state['data'])},
                    'request_sha256':f.digest(request_state['data']),
                    'project_only':True,'native_source_unchanged':True,
                    'previous_input':request['previous_input'],'current_input':request['current_input'],
                    'source_receipt_sha256':request['source_receipt']['sha256'],
                    'gateway_started':False,'workers_enabled':False}),0o400)
                sync_directory(tx)
                return {'state':'TELEGRAM_ORDINARY_PROJECT_UPDATED','ready':False,'gateway_started':False,
                    'workers_enabled':False,'full_release_accepted':False,'native_source_unchanged':True,
                    'source_receipt_sha256':request['source_receipt']['sha256']}
            except BaseException as original:
                if commit_started and os.path.lexists(tx/'committed.json'):
                    from scripts.dsh_prepare import StopUnconfirmed
                    raise StopUnconfirmed('ordinary project commit publication requires reconciliation') from original
                try:
                    prove(forward=False); restore_update_files(home,saved,owned,directories)
                    unchanged(forward=False)
                    write(tx/'rolled-back.json',encoded({'state':'ROLLED_BACK_OWN_SOURCE_ONLY_NO_RETRY',
                        'project_only':True,'native_source_unchanged':True}),0o400); sync_directory(tx)
                except BaseException as restoration:
                    from scripts.dsh_prepare import StopUnconfirmed
                    f.remember_secondary(original,restoration)
                    raise StopUnconfirmed('ordinary project update restoration requires reconciliation') from original
                raise
    finally:
        if directories is not None: directories.close()
        os.close(fd)


def project_update_inputs(request, budget):
    """Exact project-only successors; no donor source layer is introduced."""
    if type(request) is dict and request.get('schema') == PROJECT_DSH_CURRENT_SCHEMA:
        return project_current_inputs(request,budget)
    f = api()
    dashboard = type(request) is dict and request.get('schema') == PROJECT_DASHBOARD_SCHEMA
    fields = {'schema','seconds','home','previous_input','current_input','marker','source_receipt',
        'stamp','configuration','profile','launcher','credential_files','native_unit',
        'transaction_history','predecessor_update'} | ({'rebind_updates','retained'} if dashboard else set())
    f.require(type(request) is dict and set(request) == fields
        and request['schema'] in (PROJECT_UPDATE_SCHEMA, PROJECT_QUALIFICATION_SCHEMA,
            PROJECT_RUNTIME_SCHEMA, PROJECT_INFERENCE_HELPER_SCHEMA, PROJECT_DASHBOARD_SCHEMA)
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 180,
        'ordinary_project_explicit_request_required')
    home = f.directory(f.canonical(request['home'])); source = f.directory(home/'hermes-agent')
    f.require(os.environ.get('HERMES_HOME') == str(home), 'ordinary_update_exact_environment_required')
    paths = {name:budget.call(f.pin,request[name]) for name in
        ('previous_input','current_input','marker','source_receipt','stamp','configuration',
         'profile','launcher','native_unit','predecessor_update')}
    for name,path in {'marker':home/f.MARKER,'source_receipt':home/'hermes-agent.source.json',
        'stamp':source/'install-stamp.json','configuration':home/'config.yaml',
        'profile':home/'FRIDAY-PROFILE.json','launcher':source/'.hermes/bin/hermes'}.items():
        f.require(paths[name] == path, 'ordinary_update_exact_installed_inputs_required')
    previous = f.read_json(paths['previous_input']); current = f.read_json(paths['current_input'])
    old = previous['project_files']; new = current['project_files']
    f.require(request['previous_input'] != request['current_input']
        and {k:v for k,v in previous.items() if k != 'project_files'} ==
            {k:v for k,v in current.items() if k != 'project_files'}
        and current['home'] == str(home) and current['product']['runtime'] == {'enabled':False},
        'ordinary_update_operational_settings_changed')
    qualification = request['schema'] == PROJECT_QUALIFICATION_SCHEMA
    runtime = request['schema'] == PROJECT_RUNTIME_SCHEMA
    inference_helper = request['schema'] == PROJECT_INFERENCE_HELPER_SCHEMA
    if dashboard:
        helper = 'scripts/friday_ordinary_install.py'
        allowed = set(PROJECT_DASHBOARD_AFTER) | {helper}
        f.require(type(old) is dict and type(new) is dict and len(old) == 253 and set(new) == set(old)
            and f.digest(encoded(old)) == PROJECT_DASHBOARD_PROJECT_SHA256
            and all(old.get(n) == h for n,h in PROJECT_DASHBOARD_BEFORE.items())
            and all(new.get(n) == h for n,h in PROJECT_DASHBOARD_AFTER.items())
            and {n for n in old if old[n] != new[n]} == allowed
            and f.digest(f.owned_file(Path(__file__).resolve())) == new[helper]
            and encoded({k:v for k,v in previous.items() if k != 'project_files'}) ==
                encoded({k:v for k,v in current.items() if k != 'project_files'})
            and current['product']['runtime']['enabled'] is False,
            'ordinary_project_exact_source90_dashboard_delta_required')
    elif inference_helper:
        f.require(len(old) == 231 and set(new) == set(old)
            and old.get(PROJECT_INFERENCE_HELPER) == PROJECT_INFERENCE_HELPER_BEFORE
            and {n for n in old if old[n] != new[n]} == {PROJECT_INFERENCE_HELPER}
            and type(current['product']['runtime']['enabled']) is bool,
            'ordinary_project_exact_inference_helper_delta_required')
    elif runtime:
        allowed = set(PROJECT_RUNTIME_BEFORE)
        f.require(set(PROJECT_RUNTIME_AFTER) == (allowed-{'scripts/friday_ordinary_install.py'}) | PROJECT_RUNTIME_NEW
            and len(old) == 223 and set(new) == set(old) | PROJECT_RUNTIME_NEW
            and not (set(old) & PROJECT_RUNTIME_NEW)
            and all(old.get(n) == h for n,h in PROJECT_RUNTIME_BEFORE.items())
            and all(new.get(n) == h and new[n] != old.get(n)
                for n,h in PROJECT_RUNTIME_AFTER.items())
            and new['scripts/friday_ordinary_install.py'] != old['scripts/friday_ordinary_install.py']
            and all(new[n] == h for n,h in old.items() if n not in allowed)
            and all(old.get(n) == h for n,h in PROJECT_AFTER.items()),
            'ordinary_project_only_reviewed_runtime_delta_required')
    elif qualification:
        allowed = set(PROJECT_QUALIFICATION_BEFORE)
        f.require(len(old) == 223 and set(new) == set(old)
            and all(old.get(n) == h for n,h in PROJECT_QUALIFICATION_BEFORE.items())
            and all(new.get(n) == h and new[n] != old[n]
                for n,h in PROJECT_QUALIFICATION_AFTER.items())
            and new['scripts/friday_ordinary_install.py'] != old['scripts/friday_ordinary_install.py']
            and all(new[n] == h for n,h in old.items() if n not in allowed)
            and all(old.get(n) == h for n,h in PROJECT_AFTER.items()),
            'ordinary_project_only_reviewed_delta_required')
    else:
        allowed = {PROJECT_DSH,'scripts/friday_ordinary_install.py','scripts/friday_start.py','scripts/friday_native.py'}
        f.require(len(old) == 222 and set(new) == set(old) | {PROJECT_POLICY}
            and PROJECT_POLICY not in old and old.get(PROJECT_DSH) == PROJECT_DSH_BEFORE
            and all(new.get(name) == sha for name,sha in PROJECT_AFTER.items())
            and all(new[name] == sha for name,sha in old.items() if name not in allowed)
            and old[PROJECT_DSH] != new[PROJECT_DSH], 'ordinary_project_only_reviewed_delta_required')
    _,donors = budget.call(f.spec_checked,current,cli_only=True)
    marker = f.read_json(paths['marker']); receipt = f.read_json(paths['source_receipt'])
    f.require(marker.get('schema') == f.SCHEMA and marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE'
        and marker.get('home') == str(home) and marker.get('source') == str(source)
        and marker.get('runtime_ready') is False
        and marker.get('worker_state') == 'BOTH_WORKERS_PREPARATION_PENDING'
        and marker.get('input_sha256') == request['previous_input']['sha256']
        and marker.get('source_receipt_sha256') == request['source_receipt']['sha256']
        and len(receipt['layers']) == (90 if dashboard else 79 if inference_helper else 77)
        and receipt['layers'][-1]['manifest'] == ('patches/hermes/ordinary-coherent-memory-skills-source90-manifest.json'
            if dashboard else SPARK_MULTIPASS_MANIFEST if inference_helper else DOCX_CREATION_MANIFEST),
        'ordinary_project_exact_source90_required' if dashboard else
        'ordinary_project_exact_source79_required' if inference_helper else 'ordinary_project_exact_source77_required')
    if dashboard:
        f.require(request['source_receipt']['sha256'] == PROJECT_DASHBOARD_RECEIPT_SHA256
            and len(receipt['files']) == PROJECT_DASHBOARD_NATIVE_FILES,
            'ordinary_project_exact_source90_inventory_required')
    elif inference_helper:
        f.require(len(receipt['files']) == PROJECT_INFERENCE_NATIVE_FILES
            and len(request['transaction_history']) == PROJECT_INFERENCE_HISTORY_FILES,
            'ordinary_project_exact_inference_inventory_required')
    elif runtime:
        f.require(len(receipt['files']) == PROJECT_RUNTIME_NATIVE_FILES
            and len(request['transaction_history']) == PROJECT_RUNTIME_HISTORY_FILES,
            'ordinary_project_exact_runtime_inventory_required')
    elif qualification:
        f.require(len(receipt['files']) == PROJECT_QUALIFICATION_NATIVE_FILES
            and len(request['transaction_history']) == PROJECT_QUALIFICATION_HISTORY_FILES,
            'ordinary_project_exact_qualification_inventory_required')
    budget.call(f.composition_checked,previous,source,receipt,donors['hermes'])
    budget.call(f.composition_checked,current,source,receipt,donors['hermes'])
    if dashboard: project_dashboard_history(home,request)
    else: update_history(home,request['transaction_history'],request['predecessor_update'])
    predecessor = f.read_json(paths['predecessor_update'])
    if inference_helper:
        # The accepted archive-only reconciliation already admitted two helper
        # repairs after v33. Keep that completed transition and its old clocks;
        # it is ancestry to retain, never another recovery operation to execute.
        f.require(request['previous_input']['sha256'] == PROJECT_INFERENCE_INPUT_BEFORE
            and predecessor['current_input']['sha256'] == PROJECT_INFERENCE_PREDECESSOR_INPUT,
            'ordinary_project_exact_reconciled_input_required')
        for name,sha in PROJECT_INFERENCE_RECONCILIATION_PINS.items():
            f.pin({'path':str(home/name),'sha256':sha})
    f.require(predecessor.get('schema') == ('friday.ordinary-telegram-source-update.v44' if dashboard else
        'friday.ordinary-telegram-source-update.v33' if inference_helper else
        PROJECT_QUALIFICATION_SCHEMA if runtime else PROJECT_UPDATE_SCHEMA if qualification else
        'friday.ordinary-telegram-source-update.v31')
        and predecessor['home'] == str(home)
        and (dashboard or inference_helper or predecessor['current_input'] == request['previous_input']),
        'ordinary_project_source79_predecessor_required' if inference_helper else 'ordinary_project_source77_predecessor_required')
    previous_tx = home/'preparation'/('ordinary-source-update-'+predecessor['previous_input']['sha256'])
    f.require(f.read_json(previous_tx/'committed.json')['source_receipt_sha256'] ==
        request['source_receipt']['sha256'], 'ordinary_update_predecessor_binding_changed')
    if qualification or runtime:
        f.require(f.read_json(previous_tx/'intent.json').get('project_only') is True
            and f.read_json(previous_tx/'committed.json').get('project_only') is True,
            'ordinary_project_exact_committed_project_predecessor_required')
    f.native_packages(source)
    from hermes_cli.friday_ordinary_gateway import check
    check(home,role=False)
    plugins = {n:p for n,p in old.items() if n.startswith('plugins/friday_rework/')}
    f.require(marker.get('plugin_files') == plugins, 'ordinary_update_installed_plugin_marker_changed')
    checked_plugin_inventory(home,plugins)
    f.require(all(f.digest(f.owned_file(home/name,private=True)) == sha
        for name,sha in marker['profile_files'].items() if name != 'config.yaml'), 'ordinary_update_profile_changed')
    credentials = request['credential_files']
    f.require(type(credentials) is dict and set(credentials) == {'.env','auth.json'},
        'ordinary_update_credential_pins_required')
    for name,ref in credentials.items():
        f.require(not os.path.lexists(home/name) if ref is None else f.pin(ref) == home/name,
            'ordinary_update_credential_pin_changed')
    tx = home/'preparation'/('ordinary-source-update-'+request['previous_input']['sha256'])
    f.require(not os.path.lexists(tx), 'ordinary_update_consumed_no_retry')
    return home,source,previous,current,marker,receipt,donors,tx


def project_update(request, request_path, budget):
    """Existing ordinary custody and journal, restricted to the reviewed installed plugin delta."""
    if type(request) is dict and request.get('schema') == PROJECT_DSH_CURRENT_SCHEMA:
        return project_current_update(request,request_path,budget)
    f = api(); home = f.directory(f.canonical(request['home']))
    fd = os.open(home,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        home,source,previous,current,marker,receipt,donors,tx = project_update_inputs(request,budget)
        dashboard = request['schema'] == PROJECT_DASHBOARD_SCHEMA
        with stopped_consumers(home,request['native_unit'],budget) as native_prove, retained_build_lock(source) as build_prove, \
                (retained_pm_lock(home,source) if dashboard else contextlib.nullcontext(lambda:None)) as pm_prove:
            def prove(): native_prove(); build_prove(); pm_prove(); budget.check()
            f.owned_file(request_path,private=True)
            request_state = update_file_state(request_path)
            f.require(request_state is not None and json.loads(request_state['data'],object_pairs_hook=f.unique) == request,
                'ordinary_update_request_changed')
            project_update_inputs(request,budget)
            expected_after = (PROJECT_DASHBOARD_AFTER if dashboard else
                {} if request['schema'] == PROJECT_INFERENCE_HELPER_SCHEMA else
                PROJECT_RUNTIME_AFTER if request['schema'] == PROJECT_RUNTIME_SCHEMA else
                PROJECT_QUALIFICATION_AFTER if request['schema'] == PROJECT_QUALIFICATION_SCHEMA else PROJECT_AFTER)
            plugin_names = sorted(n for n in expected_after if n.startswith('plugins/'))
            names = [*plugin_names,f.MARKER]
            saved = {name:update_file_state(home/name) for name in names}
            pins = {n:previous['project_files'].get(n) for n in plugin_names}
            pins[f.MARKER] = request['marker']['sha256']
            f.require(all((row is None and pins[name] is None) or (row is not None
                and row['mode'] in (0o600,0o644) and f.digest(row['data']) == pins[name])
                for name,row in saved.items()),
                'ordinary_update_beforeimage_changed')
            retained = {name:update_file_state(path) for name,path in {
                'source_receipt':home/'hermes-agent.source.json','stamp':source/'install-stamp.json',
                'configuration':home/'config.yaml','profile':home/'FRIDAY-PROFILE.json',
                'launcher':source/'.hermes/bin/hermes','native_unit':Path(request['native_unit']['path']),
                **{name:home/name for name in ('.env','auth.json')},
                **({name:Path(ref['path']) for name,ref in request['retained'].items()} if dashboard else {}),
                **({name:home/name for name in PROJECT_INFERENCE_RECONCILIATION_PINS}
                    if request['schema'] == PROJECT_INFERENCE_HELPER_SCHEMA else {}),
            }.items()}
            f.require(all(state is not None and f.digest(state['data']) ==
                (PROJECT_INFERENCE_RECONCILIATION_PINS[name] if name in PROJECT_INFERENCE_RECONCILIATION_PINS
                 else request['retained'][name]['sha256'] if dashboard and name in request['retained']
                 else request[name]['sha256'])
                for name,state in retained.items() if name not in ('.env','auth.json')),
                'ordinary_project_retained_pin_changed')
            for name in ('.env','auth.json'):
                ref = request['credential_files'][name]; state = retained[name]
                f.require((ref is None and state is None) or (ref is not None and state is not None
                    and f.digest(state['data']) == ref['sha256']), 'ordinary_update_credential_pin_changed')
            def unchanged():
                f.pin(request['previous_input']); f.pin(request['current_input'])
                budget.call(f.spec_checked,current,cli_only=True)
                for name,state in retained.items():
                    path = (Path(request['native_unit']['path']) if name == 'native_unit' else
                        source/'install-stamp.json' if name == 'stamp' else
                        source/'.hermes/bin/hermes' if name == 'launcher' else
                        home/'hermes-agent.source.json' if name == 'source_receipt' else
                        home/'config.yaml' if name == 'configuration' else
                        home/'FRIDAY-PROFILE.json' if name == 'profile' else home/name)
                    f.require(same_update_file(path,state),'ordinary_project_retained_file_changed')
                f.require(same_update_file(request_path,request_state),'ordinary_update_request_changed')
                if dashboard: project_dashboard_history(home,request)
                else: update_history(home,request['transaction_history'],request['predecessor_update'])
                budget.call(f.composition_checked,current,source,receipt,donors['hermes'])
                prove()
            import copy
            updated = copy.deepcopy(marker)
            updated['input_sha256'] = request['current_input']['sha256']
            for name in plugin_names:
                updated['plugin_files'][name] = current['project_files'][name]
            updated['ordinary_gateway']['operator_entry'] = {'input':request['current_input'],
                'script':{'path':str(f.ROOT/'scripts/friday_native.py'),
                    'sha256':current['project_files']['scripts/friday_native.py']}}
            plugin_data = {n:f.owned_file(f.ROOT/n) for n in plugin_names}
            f.require(all(f.digest(data) == expected_after[n] for n,data in plugin_data.items()),
                'ordinary_update_worker_plugin_source_changed')
            unchanged()
            tx.mkdir(mode=0o700); before = tx/'before'; before.mkdir(mode=0o700)
            for name,row in saved.items():
                if row is not None:
                    private_parents(before,name); write(before/name,row['data'])
            write(tx/'intent.json',encoded({'schema':'friday.ordinary-telegram-source-update-transaction.v1',
                'state':'SOURCE_UPDATE_CONSUMED_NO_RETRY','project_only':True,
                'request_sha256':f.digest(request_state['data']),
                'before':{n:None if v is None else {'sha256':f.digest(v['data']),'mode':v['mode']}
                    for n,v in saved.items()}}),0o400)
            sync_directory(before); sync_directory(tx); sync_directory(tx.parent)
            owned = {}
            try:
                unchanged()
                for name,data in [*plugin_data.items(),(f.MARKER,encoded(updated))]:
                    prove(); publish_update_file(home/name,data,saved[name]['mode'] if saved[name] is not None else 0o600,saved[name],owned,name)
                from hermes_cli.friday_ordinary_gateway import check
                check(home,role=False); checked_plugin_inventory(home,updated['plugin_files'])
                unchanged()
                f.require(all(same_update_file(home/n,owned[n]) for n in names),
                    'ordinary_update_commit_ownership_changed')
                write(tx/'committed.json',encoded({'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED',
                    'project_only':True,'previous_input':request['previous_input'],
                    'current_input':request['current_input'],'source_receipt_sha256':request['source_receipt']['sha256'],
                    'gateway_started':False,'workers_enabled':False}),0o400)
                sync_directory(tx)
                return {'state':'TELEGRAM_ORDINARY_PROJECT_UPDATED','ready':False,'gateway_started':False,
                    'workers_enabled':False,'full_release_accepted':False,'native_source_unchanged':True,
                    'source_receipt_sha256':request['source_receipt']['sha256']}
            except BaseException as original:
                try:
                    prove(); restore_update_files(home,saved,owned); unchanged()
                    write(tx/'rolled-back.json',encoded({'state':'ROLLED_BACK_OWN_SOURCE_ONLY_NO_RETRY',
                        'project_only':True}),0o400); sync_directory(tx)
                except BaseException as restoration:
                    from scripts.dsh_prepare import StopUnconfirmed
                    f.remember_secondary(original,restoration)
                    raise StopUnconfirmed('ordinary project update restoration requires reconciliation') from original
                raise
    finally:
        os.close(fd)


def update(request, request_path, budget):
    """One finite committed-phase source update; original activation stays intact."""
    if type(request) is dict and request.get('schema') in (PROJECT_UPDATE_SCHEMA, PROJECT_QUALIFICATION_SCHEMA,
            PROJECT_RUNTIME_SCHEMA, PROJECT_INFERENCE_HELPER_SCHEMA, PROJECT_DASHBOARD_SCHEMA, PROJECT_DSH_CURRENT_SCHEMA):
        return project_update(request,request_path,budget)
    f = api(); home = f.directory(f.canonical(request['home']))
    directories = None
    fd = os.open(home,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        home,source,previous,current,marker,receipt,manifest,donors,tx = update_inputs(request,budget)
        exact_response = request['schema'] == EXACT_RESPONSE_SCHEMA
        source88 = request['schema'] == BUNDLE_SCHEMA
        source87 = request['schema'] == 'friday.ordinary-telegram-source-update.v41'
        with stopped_consumers(home,request['native_unit'],budget) as native_prove, retained_build_lock(source) as build_prove, \
                (retained_pm_lock(home,source) if source87 or source88 or exact_response else contextlib.nullcontext(lambda:None)) as pm_prove:
            def prove(): native_prove(); build_prove(); pm_prove()
            f.require(f.read_json(request_path) == request, 'ordinary_update_request_changed')
            # Recheck every explicit pin immediately before the source-only journal.
            update_inputs(request,budget)
            source87 = request['schema'] == 'friday.ordinary-telegram-source-update.v41'
            source86 = request['schema'] == 'friday.ordinary-telegram-source-update.v40'
            source85 = request['schema'] == 'friday.ordinary-telegram-source-update.v39'
            source84 = request['schema'] == 'friday.ordinary-telegram-source-update.v38'
            source83 = request['schema'] == 'friday.ordinary-telegram-source-update.v37'
            source82 = request['schema'] == 'friday.ordinary-telegram-source-update.v36'
            source81 = request['schema'] == 'friday.ordinary-telegram-source-update.v35'
            source80 = request['schema'] == 'friday.ordinary-telegram-source-update.v34'
            source79 = request['schema'] == 'friday.ordinary-telegram-source-update.v33'
            source78 = request['schema'] == 'friday.ordinary-telegram-source-update.v32'
            source77 = request['schema'] == 'friday.ordinary-telegram-source-update.v31'
            source76 = request['schema'] == 'friday.ordinary-telegram-source-update.v30'
            source75 = request['schema'] == 'friday.ordinary-telegram-source-update.v29'
            source74 = request['schema'] == 'friday.ordinary-telegram-source-update.v28'
            source73 = request['schema'] == 'friday.ordinary-telegram-source-update.v27'
            source72 = request['schema'] == 'friday.ordinary-telegram-source-update.v26'
            source71 = request['schema'] == 'friday.ordinary-telegram-source-update.v25'
            source70 = request['schema'] == 'friday.ordinary-telegram-source-update.v24'
            source69 = request['schema'] == 'friday.ordinary-telegram-source-update.v23'
            source68 = request['schema'] == 'friday.ordinary-telegram-source-update.v22'
            source67 = request['schema'] == 'friday.ordinary-telegram-source-update.v21'
            source66 = request['schema'] == 'friday.ordinary-telegram-source-update.v20'
            source65 = request['schema'] == 'friday.ordinary-telegram-source-update.v19'
            source64 = request['schema'] == 'friday.ordinary-telegram-source-update.v18'
            source63 = request['schema'] == 'friday.ordinary-telegram-source-update.v17'
            source62 = request['schema'] == 'friday.ordinary-telegram-source-update.v16'
            source61 = request['schema'] == 'friday.ordinary-telegram-source-update.v15'
            source60 = request['schema'] == 'friday.ordinary-telegram-source-update.v14'
            source59 = request['schema'] == 'friday.ordinary-telegram-source-update.v13'
            source58 = request['schema'] == 'friday.ordinary-telegram-source-update.v12'
            source57 = request['schema'] == 'friday.ordinary-telegram-source-update.v11'
            source56 = request['schema'] == 'friday.ordinary-telegram-source-update.v10'
            source55 = request['schema'] == 'friday.ordinary-telegram-source-update.v9'
            source54 = request['schema'] == 'friday.ordinary-telegram-source-update.v8'
            source53 = request['schema'] == 'friday.ordinary-telegram-source-update.v7'
            source52 = request['schema'] == 'friday.ordinary-telegram-source-update.v6'
            source51 = request['schema'] == 'friday.ordinary-telegram-source-update.v5'
            source50 = request['schema'] == 'friday.ordinary-telegram-source-update.v4'
            source49 = request['schema'] == 'friday.ordinary-telegram-source-update.v3'
            plugin_changes = sorted(FILE_TOOL_CONTRACT_PLUGIN_FILES if source81 else SPARK_REQUEST_BUDGET_PLUGIN_FILES if source80 else SPARK_MULTIPASS_PLUGIN_FILES if source79 else PRIVACY_EFFECT_PLUGIN_FILES if source78 else CONTEXT_SELF_PLUGIN_FILES if source71 else TOOL_METADATA_PLUGIN_FILES if source65 else WORKER_TOOLS_PLUGIN_FILES if source63 else BROWSER_PLUGIN_FILES if source55 else WORKER_ATTACH_PLUGIN_FILES) if source81 or source80 or source79 or source78 or source71 or source65 or source63 or source55 or source49 else []
            if source88: plugin_changes = sorted(BUNDLE_PLUGIN_FILES)
            names = [f.MARKER,'hermes-agent.source.json','hermes-agent/install-stamp.json'] + [
                'hermes-agent/'+row['path'] for row in manifest['files']] + plugin_changes
            new_files = set().union(*(pin["new_files"] for pin in BUNDLE_LAYER_PINS)) if source88 else PROTECTED_COMPRESSOR_NEW_FILES if source87 else SPARK_REQUEST_BUDGET_NEW_FILES if source80 else SPARK_MULTIPASS_NEW_FILES if source79 else PRIVACY_EFFECT_NEW_FILES if source78 else DOCX_CREATION_NEW_FILES if source77 else FILE_REVISION_NEW_FILES if source75 else WORKER_TOOLS_FILES if source63 else BROWSER_NEW_FILES if source55 else set()
            absent = {'hermes-agent/'+name for name in new_files}
            if source87 or source88 or exact_response:
                directories = SourceUpdateDirectories(home,names,
                    {'hermes-agent/'+name for name in (set() if exact_response else BUNDLE_NEW_DIRECTORIES if source88 else PROTECTED_COMPRESSOR_NEW_DIRECTORIES)})
            def parent_fd(name): return directories.parent_fd(name) if directories is not None else None
            def publish(path,data,mode,before,owned,name):
                if directories is not None:
                    directories.prove()
                    result = publish_update_file(path,data,mode,before,owned,name,parent_fd=parent_fd(name))
                    directories.prove(); return result
                return publish_update_file(path,data,mode,before,owned,name)

            saved = ({name:(None if (source87 or source88 or exact_response) and name in absent else update_file_state(home/name,parent_fd(name))) for name in names}
                if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response else {name:{'data':f.owned_file(home/name),
                    'mode':stat.S_IMODE((home/name).stat().st_mode)} for name in names})
            f.require(all(row is None or row['mode'] in (0o600,0o644) for row in saved.values()),
                'ordinary_update_beforeimage_mode_required')
            if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                before_pins = {f.MARKER:request['marker']['sha256'],
                    'hermes-agent.source.json':request['source_receipt']['sha256'],
                    'hermes-agent/install-stamp.json':request['stamp']['sha256']}
                before_pins.update({'hermes-agent/'+row['path']:row['before_sha256']
                    for row in manifest['files'] if row['path'] not in new_files})
                before_pins.update({name:previous['project_files'][name] for name in plugin_changes})
                f.require(all((row is None) == (name in absent) and
                    (row is None or f.digest(row['data']) == before_pins[name])
                    for name,row in saved.items()), 'ordinary_update_beforeimage_changed')
            import copy
            receipt = copy.deepcopy(receipt)
            for row in manifest['files']:
                receipt['files'][row['path']] = {k:row[k] for k in ('sha256','bytes','mode')}
            manifest_name = EXACT_RESPONSE_MANIFEST if exact_response else PROTECTED_COMPRESSOR_MANIFEST if source87 else MANUAL_COMPRESSION_MANIFEST if source86 else WEB_RUNTIME_HISTORY_MANIFEST if source85 else FILE_REPLY_CONTEXT_MANIFEST if source84 else COMBINED_INPUT_MANIFEST if source83 else WEB_INPUT_MANIFEST if source82 else FILE_TOOL_CONTRACT_MANIFEST if source81 else SPARK_REQUEST_BUDGET_MANIFEST if source80 else SPARK_MULTIPASS_MANIFEST if source79 else PRIVACY_EFFECT_MANIFEST if source78 else DOCX_CREATION_MANIFEST if source77 else DOCUMENT_EXTRACTION_MANIFEST if source76 else FILE_REVISION_MANIFEST if source75 else TOOL_RESULT_CONTEXT_MANIFEST if source74 else DSH_SANDBOX_MANIFEST if source73 else CURRENT_TURN_MANIFEST if source72 else CONTEXT_SELF_MANIFEST if source71 else PRIVATE_REPLY_MANIFEST if source70 else PROMPT_PRIVACY_MANIFEST if source69 else MEMORY_SCOPE_MANIFEST if source68 else FIRST_CONTACT_COPY_MANIFEST if source67 else INLINE_PRIVACY_MANIFEST if source66 else TOOL_METADATA_MANIFEST if source65 else PUBLIC_SURFACE_MANIFEST if source64 else WORKER_TOOLS_MANIFEST if source63 else DIALOGUE_CONTINUATION_MANIFEST if source62 else FIRST_CONTACT_STATE_MANIFEST if source61 else TURN_SCOPE_MANIFEST if source60 else ADMIN_STARTUP_MANIFEST if source59 else INTERACTION_SCOPE_MANIFEST if source58 else PROFILE_RUNTIME_MANIFEST if source57 else BROWSER_GATEWAY_MANIFEST if source56 else BROWSER_MANIFEST if source55 else SEARCH_RECOVERY_MANIFEST if source54 else WEB_OUTPUT_MANIFEST if source53 else WEB_CONTINUATION_MANIFEST if source52 else ADMIN_BROADCAST_MANIFEST if source51 else ADMIN_RESTART_MANIFEST if source50 else FILE_CONTINUATION_MANIFEST if source49 else PRIVATE_STATE_MANIFEST if request['schema'].endswith('.v2') else UPDATE_MANIFEST
            for layer_name,layer in (manifest['bundle_layers'] if source88 or exact_response else [(manifest_name,manifest)]):
                receipt['layers'].append({'manifest':layer_name,
                    'manifest_sha256':current['project_files'][layer_name],'patch_sha256':layer['patch_sha256']})
            stamp = f.read_json(source/'install-stamp.json')
            stamp['fridaySource'] = {'baseTree':receipt['base_tree'],'layers':receipt['layers']}
            receipt_data = encoded(receipt); receipt_sha = f.digest(receipt_data)
            updated = copy.deepcopy(marker)
            updated['input_sha256'] = request['current_input']['sha256']
            updated['source_receipt_sha256'] = receipt_sha
            if source88 or source81 or source80 or source79 or source78 or source71 or source65 or source63 or source55 or source49:
                updated['plugin_files'] = {n:p for n,p in current['project_files'].items() if n.startswith('plugins/friday_rework/')}
            updated['ordinary_gateway']['source_receipt_sha256'] = receipt_sha
            updated['ordinary_gateway']['operator_entry'] = {'input':request['current_input'],
                'script':{'path':str(f.ROOT/'scripts/friday_native.py'),
                    'sha256':current['project_files']['scripts/friday_native.py']}}
            publication = [('hermes-agent.source.json',receipt_data),
                ('hermes-agent/install-stamp.json',encoded(stamp)),(f.MARKER,encoded(updated))]
            after = {name:f.digest(data) for name,data in publication}
            after.update({'hermes-agent/'+row['path']:row['sha256'] for row in manifest['files']})
            plugin_data = {name:f.owned_file(f.ROOT/name) for name in plugin_changes}
            f.require(all(f.digest(data) == current['project_files'][name] for name,data in plugin_data.items()),
                'ordinary_update_worker_plugin_source_changed')
            after.update({name:f.digest(data) for name,data in plugin_data.items()})
            tx.mkdir(mode=0o700); before = tx/'before'; before.mkdir(mode=0o700)
            for name,row in saved.items():
                if row is None: continue
                target = before/name; private_parents(before,name)
                write(target,row['data'])
            write(tx/'intent.json',encoded({'schema':'friday.ordinary-telegram-source-update-transaction.v1',
                'state':'SOURCE_UPDATE_CONSUMED_NO_RETRY','request_sha256':f.digest(f.owned_file(request_path,private=True)),
                **({'new_directories':sorted(directories.new), 'directory_before':directories.identities} if source87 or source88 or exact_response else
                    {'new_directories':['hermes-agent/config']} if source63 else {}),
                'before':{name:({'absent':True} if row is None else {'sha256':f.digest(row['data']),'mode':row['mode']}) for name,row in saved.items()}}))
            sync_directory(before); sync_directory(tx); sync_directory(tx.parent)
            owned = {}; created_directory = None
            commit_publication_started = False
            def directory_custody():
                if directories is not None: directories.prove()
                if created_directory is not None:
                    path = source/'config'; f.directory(path)
                    info = path.lstat()
                    f.require(tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_mode')) == created_directory
                        and {p.name for p in path.iterdir()} <= {'RESEARCH.md'},
                        'ordinary_update_directory_ownership_changed')
            try:
                prove()
                if source87 or source88 or exact_response:
                    directories.create(tx/'directories')
                    write(tx/'created-directories.json',encoded({name:directories.identities[name]
                        for name in directories.created}))
                    sync_directory(tx)
                if source63:
                    # Exact absent parent belongs to this additive layer only.
                    # Never adopt an existing directory or follow a symlink.
                    (source/'config').mkdir(mode=0o700)
                    info = (source/'config').lstat()
                    created_directory = tuple(getattr(info,k) for k in ('st_dev','st_ino','st_uid','st_mode'))
                    directory_custody(); sync_directory(source)
                from scripts.dsh_prepare import run
                env = f.clean_environment(home); env['GIT_CEILING_DIRECTORIES'] = str(source.parent)
                patch_root = source
                if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                    # Git mutates only our private staging tree. Actual source
                    # publication records the precise created inode before rename/link.
                    patch_root = tx/'after'; patch_root.mkdir(mode=0o700)
                    for row in manifest['files']:
                        name = 'hermes-agent/'+row['path']
                        private_parents(patch_root,row['path'])
                        if saved[name] is not None:
                            write(patch_root/row['path'],saved[name]['data'],saved[name]['mode'])
                for _,layer in (manifest['bundle_layers'] if source88 or exact_response else [(manifest_name,manifest)]):
                    for checking in (True,False):
                        command = ['git','--no-optional-locks','apply','--whitespace=nowarn']
                        if checking: command.append('--check')
                        command.append(str(f.ROOT/layer['patch']))
                        run(command,patch_root,timeout=min(20,budget.check(reserve=1)),env=env,deadline=budget.deadline)
                for row in manifest['files']:
                    data = f.owned_file(patch_root/row['path'])
                    f.require(f.digest(data) == row['sha256'] and len(data) == row['bytes'],
                        'ordinary_update_patch_output_changed')
                    if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response: (patch_root/row['path']).chmod(0o600)
                if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                    for row in manifest['files']:
                        name = 'hermes-agent/'+row['path']; budget.check(); prove(); directory_custody()
                        publish(home/name,f.owned_file(patch_root/row['path']),
                            0o644,saved[name],owned,name)
                for name,data in plugin_data.items():
                    # Same owned exact-byte private publication used by the native installer.
                    f.require(f.digest(f.owned_file(home/name,private=True)) == f.digest(saved[name]['data']),
                        'ordinary_update_worker_plugin_preimage_changed')
                    if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response: publish(home/name,data,saved[name]['mode'],saved[name],owned,name)
                    else: replace(home/name,data,saved[name]['mode'])
                if source49 or source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                    checked_plugin_inventory(home, updated['plugin_files'])
                budget.call(f.composition_checked,current,source,receipt,donors['hermes'])
                for name,data in publication:
                    budget.check()
                    if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response: publish(home/name,data,saved[name]['mode'],saved[name],owned,name)
                    else: replace(home/name,data,saved[name]['mode'])
                # The ordinary binding and complete native source identity must
                # agree before the update can commit. No service is launched.
                from hermes_cli.friday_ordinary_gateway import check
                if source56:
                    check_browser_gateway(home,source,manifest,budget,staged=False)
                else:
                    check(home,role=False)
                if source49 or source50 or source51 or source52 or source53 or source54 or source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                    checked_plugin_inventory(home, updated['plugin_files'])
                update_history(home,request['transaction_history'],request.get('predecessor_update'),request.get('keyless_recovery'),request.get('inference_rebind'),request.get('worker_archive')); prove(); budget.check()
                if source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                    checked_source88_retained(home,request,budget) if exact_response else checked_source82_retained(home,request)
                    budget.call(f.spec_checked,current,cli_only=True)
                if source81:
                    checked_source81_retained(home,request,after=True)
                    budget.call(f.spec_checked,current,cli_only=True)
                if source80:
                    rebound = f.read_json(f.pin(request['inference_rebind']))
                    after_rebind = f.read_json(home/'preparation'/('ordinary-inference-rebind-'+
                        rebound['previous_input']['sha256'])/'committed.json')['after']
                    for name,sha in after_rebind.items():
                        if name != f.MARKER: f.pin({'path':str(home/name),'sha256':sha})
                    for name in ('previous_input','current_input','configuration','profile','launcher','native_unit'):
                        f.pin(request[name])
                    for name,ref in request['credential_files'].items():
                        f.require(not os.path.lexists(home/name) if ref is None else f.pin(ref) == home/name,
                            'ordinary_update_credential_pin_changed')
                    for name,sha in PROJECT_INFERENCE_RECONCILIATION_PINS.items():
                        f.pin({'path':str(home/name),'sha256':sha})
                    budget.call(f.spec_checked,current,cli_only=True)

                if source57:
                    budget.call(checked_worker_declaration_publication,home,request,
                        f.read_json(f.pin(request['predecessor_update'])),marker)
                if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                    f.require(all(name in owned and same_update_file(home/name,owned[name],parent_fd(name)) for name in names),
                        'ordinary_update_commit_ownership_changed')
                directory_custody()
                if source88: budget.call(checked_plugin_inventory,home,updated['plugin_files'])
                committed_data = encoded({'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED',
                    'previous_input':request['previous_input'],'current_input':request['current_input'],
                    'source_receipt_sha256':receipt_sha,'gateway_started':False,'workers_enabled':False})
                budget.check()
                # Once commit publication is attempted, a partial/visible/durable
                # receipt may exist. Never roll source back beneath that record.
                commit_publication_started = True
                write(tx/'committed.json',committed_data)
                sync_directory(tx); budget.check()
                return {'state':'TELEGRAM_ORDINARY_SOURCE_UPDATED','ready':False,'gateway_started':False,
                    'workers_enabled':False,'full_release_accepted':False,'source_receipt_sha256':receipt_sha}
            except BaseException as original:
                if commit_publication_started:
                    from scripts.dsh_prepare import StopUnconfirmed
                    raise StopUnconfirmed('ordinary source update commit publication requires reconciliation') from original
                try:
                    prove(); directory_custody()
                    if source55 or source56 or source57 or source58 or source59 or source60 or source61 or source62 or source63 or source64 or source65 or source66 or source67 or source68 or source69 or source70 or source71 or source72 or source73 or source74 or source75 or source76 or source77 or source78 or source79 or source80 or source81 or source82 or source83 or source84 or source85 or source86 or source87 or source88 or exact_response:
                        restore_update_files(home,saved,owned,directories)
                        if directories is not None: directories.remove_created()
                        if created_directory is not None:
                            directory_custody()
                            (source/'config').rmdir(); sync_directory(source)
                    else:
                        # Unknown concurrent bytes are never overwritten by rollback.
                        f.require(all(f.digest(f.owned_file(home/name)) in
                            {f.digest(row['data']),after[name]} for name,row in saved.items()),
                            'ordinary_update_restore_ownership_changed')
                        # Restore only this transaction's exact Native/plugin/metadata beforeimages.
                        for name,row in reversed(list(saved.items())):
                            replace(home/name,row['data'],row['mode'])
                        f.require(all(f.digest(f.owned_file(home/name)) == f.digest(row['data'])
                            and stat.S_IMODE((home/name).stat().st_mode) == row['mode'] for name,row in saved.items()),
                            'ordinary_update_restore_failed')
                    update_history(home,request['transaction_history'],request.get('predecessor_update'),request.get('keyless_recovery'),request.get('inference_rebind'),request.get('worker_archive'))
                    if source88:
                        checked_plugin_inventory(home,marker['plugin_files'])
                    write(tx/'rolled-back.json',encoded({'state':'ROLLED_BACK_OWN_SOURCE_ONLY_NO_RETRY'}))
                    sync_directory(tx)
                except BaseException as restoration:
                    from scripts.dsh_prepare import StopUnconfirmed
                    f.remember_secondary(original,restoration)
                    raise StopUnconfirmed('ordinary source update restoration requires reconciliation') from original
                raise
    finally:
        if directories is not None: directories.close()
        os.close(fd)


def start(value,input_path,input_hash,budget):
    """Re-exec the exact native PM generation for the ordinary service handoff."""
    f = api()
    home,donors = budget.call(f.spec_checked,value,cli_only=True)
    marker = budget.call(f.read_json,home/f.MARKER)
    f.require(marker.get('completion_stage') == 'TELEGRAM_ORDINARY'
        and marker.get('input_sha256') == input_hash
        and f.digest(f.owned_file(input_path,private=True)) == input_hash,
        'ordinary_current_installation_required')
    source = home/'hermes-agent'
    f.composition_checked(value,source,f.read_json(home/'hermes-agent.source.json'),donors['hermes'])
    from scripts.install_containment import Containment
    custody = Containment(value['containment'],budget,f.clean_environment(home))
    selected = custody.run([value['bootstrap_python']['path'],'-B','-c',
        'from pm.environments import project_python;from pathlib import Path;print(project_python(Path.cwd()))'],
        source,timeout=15)[0]
    f.require(Path(selected).is_absolute() and Path(selected).is_file(),'native_pm_python_missing')
    budget.check()
    os.execve(selected,[selected,'-B',str(f.ROOT/'scripts/friday_native.py'),'start-telegram',
        '--input',str(input_path),'--deadline',str(budget.deadline)],f.clean_environment(home))


def rollback(request,budget):
    """Restore this transaction only after native stop/uninstall is proved.

    Product/user/session data are retained. Unknown service ownership or changed
    beforeimages refuse restoration; this is never a gateway stop/retry command.
    """
    f=api()
    f.require(type(request) is dict and set(request)=={'schema','seconds','home','current_input'}
        and request['schema']=='friday.ordinary-telegram-rollback.v1'
        and type(request['seconds']) is int and 30<=request['seconds']<=180,'ordinary_rollback_request_required')
    home=f.directory(f.canonical(request['home']));source=home/'hermes-agent'
    value=f.read_json(f.pin(request['current_input']));f.spec_checked(value,cli_only=True)
    marker=f.read_json(home/f.MARKER)
    f.require(marker.get('completion_stage')=='TELEGRAM_ORDINARY'
        and marker.get('input_sha256')==request['current_input']['sha256'],'ordinary_rollback_current_source_required')
    donors={r['id']:r for r in f.read_json(f.pin(value['sources_lock']))['repositories']}
    f.composition_checked(value,source,f.read_json(home/'hermes-agent.source.json'),donors['hermes'])
    f.native_packages(source)
    from gateway import host_rendezvous as hr
    from hermes_cli import gateway as gw
    f.require(not gw.get_systemd_unit_path(system=False).exists()
        and not gw.get_systemd_unit_path(system=True).exists()
        and hr.read_record(hr.ROLE_GATEWAY,include_stale=True) is None
        and not gw.find_gateway_pids(),'ordinary_rollback_native_stop_and_uninstall_required')
    tx=home/TRANSACTION;before=tx/'before';intent=f.read_json(tx/'intent.json')
    committed=f.read_json(tx/'committed.json')
    f.require(committed['state']=='SOURCE_ACTIVATED_NOT_RUNTIME_ACCEPTED'
        and not os.path.lexists(tx/'source-rollback.intent.json'),'ordinary_rollback_once_required')
    manifest=f.read_json(f.ROOT/MANIFEST)
    expected={'FRIDAY-INSTALL.json','hermes-agent.source.json','config.yaml','hermes-agent/install-stamp.json',
              'plugins/friday_rework/onboarding.py'}|{'hermes-agent/'+r['path'] for r in manifest['files'] if not r['new_file']}
    f.require(set(intent['before'])==expected and intent['new_files']==[r['path'] for r in manifest['files'] if r['new_file']],
        'ordinary_rollback_scope_changed')
    for name,row in intent['before'].items():
        f.require(f.digest(f.owned_file(before/name,private=True))==row['sha256'], 'ordinary_rollback_beforeimage_changed')
    fd=os.open(home,os.O_RDONLY|os.O_DIRECTORY)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget.check()
        rollback_before=tx/'rollback-before';rollback_before.mkdir(mode=0o700)
        retained={}
        for name in ('config.yaml','FRIDAY-INSTALL.json'):
            raw=f.owned_file(home/name,private=True);write(rollback_before/name,raw);retained[name]={'path':str(rollback_before/name),'sha256':f.digest(raw)}
        write(tx/'source-rollback.intent.json',encoded({'state':'CONSUMED_SOURCE_ROLLBACK','retained_current_configuration':retained}))
        for row in manifest['files']:
            if row['new_file']:
                budget.check();(source/row['path']).unlink()
        for name,row in intent['before'].items():
            if name==f.MARKER:continue
            budget.check();replace(home/name,f.owned_file(before/name,private=True),row['mode'])
        row=intent['before'][f.MARKER];replace(home/f.MARKER,f.owned_file(before/f.MARKER,private=True),row['mode'])
        f.require(all(f.digest(f.owned_file(home/name))==row['sha256'] for name,row in intent['before'].items()),'ordinary_rollback_verification_failed')
        write(tx/'source-rollback.done.json',encoded({'state':'SOURCE_ROLLED_BACK','runtime_data_retained':True}))
        return {'state':'ORDINARY_SOURCE_ROLLED_BACK','ready':False,'runtime_data_retained':True}
    finally:os.close(fd)


FIRST_CONTACT_CONFIG_SUFFIX = b'onboarding:\n  seen:\n    profile_build_offered: true\n'


def first_contact_recovery_inputs(request, home, source, *, restored=False):
    """Validate original admission without admitting the known-invalid config.

    The exception is one byte-exact native append. No receipt, access generation,
    root policy or ordinary profile checker is relaxed or rewritten.
    """
    f = api()
    from hermes_cli import friday_user_scope as user
    from hermes_cli import friday_product_access as access
    from hermes_cli.friday_ordinary_gateway import check
    from hermes_cli.plugins_state import _plugin_data_namespace
    from hermes_yaml import safe_load
    refs = ('installed_input','root_marker','source_receipt','stamp','root_configuration',
            'root_profile','native_unit','onboarding','user_marker','configuration','backup','access_state')
    paths = {}
    for name in refs:
        ref = request[name]
        # The BAD pin is intentionally replaced only after committed publication.
        paths[name] = f.canonical(ref['path']) if restored and name == 'configuration' else f.pin(ref)
        f.owned_file(paths[name],private=name not in ('stamp','source_receipt','native_unit'))
        mode = stat.S_IMODE(paths[name].stat().st_mode)
        f.require(mode in ((0o400,0o600) if name == 'installed_input' else (0o600,0o644) if name in ('stamp','source_receipt','native_unit') else (0o600,)),
            'ordinary_recovery_input_mode_required')
    profile = access.profile_name(request['profile'])
    f.require(profile != 'default', 'ordinary_recovery_named_profile_required')
    f.directory(home/'profiles')
    profile_home = f.directory(home/'profiles'/profile)
    for name,path in {'root_marker':home/f.MARKER,'source_receipt':home/'hermes-agent.source.json',
        'stamp':source/'install-stamp.json','root_configuration':home/'config.yaml',
        'root_profile':home/'FRIDAY-PROFILE.json','onboarding':profile_home/user.ONBOARDING,
        'user_marker':profile_home/user.MARKER,'configuration':profile_home/'config.yaml',
        'access_state':home/'plugin-data'/_plugin_data_namespace('friday_rework','')/'state.json'}.items():
        f.require(paths[name] == path,'ordinary_recovery_exact_paths_required')
    backup = paths['backup']
    # Native mkdir uses0755 or0775 beneath the already-checked admitted0700
    # home. That private ancestor prevents group access; backup files stay0600.
    for parent in (profile_home/'backups',profile_home/'backups/config'):
        f.canonical(str(parent)); info = parent.lstat()
        f.require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) in (0o700,0o755,0o775),
            'ordinary_recovery_owned_native_backup_directory_required')
    f.require(backup.parent == profile_home/'backups/config'
        and backup.name.startswith('config.yaml.good.') and len(backup.name) > len('config.yaml.good.'),
        'ordinary_recovery_native_backup_required')
    original = f.read_json(paths['installed_input']); marker = f.read_json(paths['root_marker'])
    receipt = f.read_json(paths['source_receipt']); stamp = f.read_json(paths['stamp'])
    f.require(original.get('home') == str(home) and marker.get('home') == str(home)
        and marker.get('source') == str(source) and marker.get('input_sha256') == request['installed_input']['sha256']
        and marker.get('source_receipt_sha256') == request['source_receipt']['sha256']
        and stamp.get('fridaySource',{}).get('baseTree') == receipt.get('base_tree')
        and stamp.get('fridaySource',{}).get('layers') == receipt.get('layers'),
        'ordinary_recovery_original_source_binding_required')
    # Root-only checker retains its original source/credential/history/route checks.
    check(home,role=False)
    # Root check already validates the policy. Read exact pinned raw YAML here:
    # native settings()/load_config_readonly() may initialize a home skeleton.
    root_cfg = safe_load(f.owned_file(paths['root_configuration'],private=True))
    settings = root_cfg['plugins']['entries']['friday_rework']['settings']
    policy = settings['user_isolation']; accounts = settings['product_access']['accounts']
    binding = request['binding']
    f.require(type(binding) is dict and binding.get('runtime_profile') == profile
        and binding.get('platform') == 'telegram' and policy is not None
        and [r for r in policy['bindings'] if r['runtime_profile'] == profile] == [binding],
        'ordinary_recovery_original_binding_required')
    principal = tuple(binding[k] for k in ('platform','transport_profile','account_id','user_id'))
    key = access.principal_id(*principal)
    f.require(len([r for r in accounts if tuple(r[k] for k in
        ('platform','transport_profile','account_id')) == principal[:3] and profile in r['runtime_profiles']]) == 1,
        'ordinary_recovery_original_account_required')
    state = f.read_json(paths['access_state'])
    admitted = access.validate_access(state[access.KEY])['users'].get(key)
    f.require(admitted is not None and admitted['enabled'] is True and admitted['role'] == 'user'
        and tuple(admitted[k] for k in ('platform','transport_profile','account_id','user_id')) == principal
        and admitted.get('generation') == request['generation'], 'ordinary_recovery_original_access_required')
    onboarding = f.read_json(paths['onboarding']); user_marker = f.read_json(paths['user_marker'])
    info = profile_home.stat()
    f.require(set(onboarding) == {'schema','binding_sha256','config_sha256','soul_sha256',
        'required_secrets','directory_identity','template','authorization_home'}
        and onboarding['schema'] == 'friday.onboarding.v1' and onboarding['authorization_home'] == str(home)
        and onboarding['directory_identity'] == [info.st_dev,info.st_ino]
        and onboarding['binding_sha256'] == user._fingerprint(binding)
        and onboarding['config_sha256'] == request['backup']['sha256'],
        'ordinary_recovery_original_receipt_required')
    f.require(user_marker == {'schema':'friday.user-home.v1','principal':key,'profile':profile,
        'binding_sha256':user._fingerprint(binding),'onboarding_sha256':request['onboarding']['sha256']},
        'ordinary_recovery_original_marker_required')
    f.require(f.digest(f.owned_file(profile_home/'SOUL.md',private=True)) == onboarding['soul_sha256'],
        'ordinary_recovery_original_soul_required')
    from agent.secret_scope import load_env_file
    names = onboarding['required_secrets']; f.owned_file(profile_home/'.env',private=True)
    f.require(type(names) is list and bool(names) and all(type(n) is str for n in names),
        'ordinary_recovery_original_secret_scope_required')
    values = load_env_file(profile_home/'.env')
    f.require(all(values.get(n) for n in names),'ordinary_recovery_original_secrets_required')
    before = update_file_state(paths['configuration']); old = f.owned_file(backup,private=True)
    f.require(before is not None and before['mode'] == 0o600
        and (restored or list(before['identity']) == request['configuration_identity']),
        'ordinary_recovery_configuration_identity_changed')
    f.require(stat.S_IMODE(backup.stat().st_mode) == 0o600,'ordinary_recovery_private_backup_mode_required')
    cfg = safe_load(old)
    f.require(type(cfg) is dict and 'onboarding' not in cfg,
        'ordinary_recovery_backup_already_has_onboarding')
    if restored:
        f.require(before['data'] == old,'ordinary_recovery_restored_bytes_changed')
    else:
        f.require(before['data'] == old + FIRST_CONTACT_CONFIG_SUFFIX,
            'ordinary_recovery_exact_native_append_required')
        expected = dict(cfg); expected['onboarding'] = {'seen':{'profile_build_offered':True}}
        f.require(safe_load(before['data']) == expected,'ordinary_recovery_only_known_field_required')
    return profile_home, before, old


@contextlib.contextmanager
def retained_first_contact_config_lock(config_path):
    """Refuse unsafe native a+ lock targets before its PID stamp can write."""
    f = api(); path = config_path.with_name(config_path.name+'.lock')
    before = update_file_state(path)
    f.require(before is not None and before['data'] == b'' and before['mode'] in (0o600,0o644,0o664),
        'ordinary_recovery_existing_native_config_lock_required')
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        def prove():
            opened = os.fstat(fd)
            identity = tuple(getattr(opened,k) for k in ('st_dev','st_ino','st_uid','st_nlink','st_mode'))
            current = update_file_state(path)
            f.require(identity == before['identity'] and current is not None
                and current['identity'] == before['identity'], 'ordinary_recovery_native_config_lock_identity_changed')
        prove()
        from hermes_cli.config import config_write_transaction
        with config_write_transaction(config_path):
            prove()
            yield
            prove()
    finally:
        os.close(fd)


def recover_first_contact_config(request, request_path, budget):
    """One consumed exact-byte repair, always leaving native consumers stopped."""
    f = api()
    fields = {'schema','seconds','home','profile','binding','generation','allowed_delta','configuration_identity',
        'installed_input','root_marker','source_receipt','stamp','root_configuration','root_profile',
        'native_unit','onboarding','user_marker','configuration','backup','access_state'}
    f.require(type(request) is dict and set(request) == fields
        and request['schema'] == 'friday.ordinary-first-contact-config-recovery.v1'
        and type(request['seconds']) is int and 30 <= request['seconds'] <= 180
        and type(request['generation']) is int and request['generation'] >= 1
        and request['allowed_delta'] == 'append-onboarding.seen.profile_build_offered=true'
        and type(request['configuration_identity']) is list and len(request['configuration_identity']) == 5
        and all(type(n) is int for n in request['configuration_identity']),
        'ordinary_recovery_explicit_request_required')
    home = f.directory(f.canonical(request['home'])); source = f.directory(home/'hermes-agent')
    f.require(os.environ.get('HERMES_HOME') == str(home),'ordinary_recovery_exact_environment_required')
    f.directory(home/'preparation')
    request_path = f.canonical(str(request_path)); request_state = update_file_state(request_path)
    f.owned_file(request_path,private=True)
    f.require(f.read_json(request_path) == request,'ordinary_recovery_request_changed')
    fd = os.open(home,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        opened = os.fstat(fd); linked = home.lstat()
        f.require((opened.st_dev,opened.st_ino) == (linked.st_dev,linked.st_ino),
            'ordinary_recovery_home_identity_changed')
        # Authenticate native code before importing the code that holds host custody.
        original = f.read_json(f.pin(request['installed_input']))
        receipt = f.read_json(f.pin(request['source_receipt']))
        donors = {r['id']:r for r in f.read_json(f.pin(original['sources_lock']))['repositories']}
        budget.call(f.composition_checked,original,source,receipt,donors['hermes'])
        f.native_packages(source)
        with stopped_consumers(home,request['native_unit'],budget) as prove, retained_build_lock(source) as build_prove:
            budget.check(); prove(); build_prove()
            pinned_before = {name:update_file_state(f.canonical(ref['path'])) for name,ref in request.items()
                if type(ref) is dict and set(ref) == {'path','sha256'}}
            profile_home,before,old = first_contact_recovery_inputs(request,home,source)
            tx = home/'preparation'/('ordinary-first-contact-config-recovery-'+request['configuration']['sha256'])
            f.require(not os.path.lexists(tx),'ordinary_recovery_consumed_no_retry')
            with retained_first_contact_config_lock(profile_home/'config.yaml'):
                prove();build_prove();budget.check()
                f.require(same_update_file(request_path,request_state),'ordinary_recovery_request_identity_changed')
                # Revalidate every pin, policy, access-history byte and inode under native CAS lock.
                _,again,checked_old = first_contact_recovery_inputs(request,home,source)
                f.require(again == before and checked_old == old,'ordinary_recovery_cas_changed')
                f.require(all(same_update_file(Path(request[name]['path']),state)
                    for name,state in pinned_before.items()),'ordinary_recovery_pinned_identity_changed')
                tx.mkdir(mode=0o700)
                write(tx/'bad-config.yaml',before['data'])
                write(tx/'intent.json',encoded({'schema':'friday.ordinary-first-contact-config-recovery-transaction.v1',
                    'state':'CONSUMED_NO_RETRY','request_sha256':f.digest(request_state['data']),
                    'bad_sha256':request['configuration']['sha256'],'restored_sha256':request['backup']['sha256'],
                    'consumers_started':False,'source_updated':False,'database_changed':False}))
                sync_directory(tx);sync_directory(tx.parent)
                owned = {}
                try:
                    prove();build_prove();budget.check()
                    publish_update_file(profile_home/'config.yaml',old,before['mode'],before,owned,'config.yaml')
                    _,after,_ = first_contact_recovery_inputs(request,home,source,restored=True)
                    f.require(after == owned['config.yaml'],'ordinary_recovery_publication_identity_changed')
                    f.require(all(same_update_file(Path(request[name]['path']),state)
                        for name,state in pinned_before.items() if name != 'configuration'),
                        'ordinary_recovery_unchanged_original_identity_required')
                    from hermes_cli import friday_user_scope as user
                    user.check_onboarding_home(home,profile_home,request['binding'])
                    principal = tuple(request['binding'][k] for k in
                        ('platform','transport_profile','account_id','user_id'))
                    info = profile_home.stat()
                    # Unchanged complete per-event admission check, with no published capability.
                    with user.authority(profile_home):
                        user.UserScope(home,profile_home,request['profile'],principal,dict(request['binding']),
                            (info.st_dev,info.st_ino),request['generation']).check()
                    prove();build_prove();budget.check()
                    write(tx/'committed.json',encoded({'state':'EXACT_CONFIG_RESTORED_CONSUMERS_STOPPED',
                        'config_sha256':request['backup']['sha256'],'source_updated':False,
                        'database_changed':False,'runtime_accepted':False,'consumers_started':False}))
                    sync_directory(tx)
                except BaseException as original_error:
                    # Publication may already have happened. Never restore BAD or retry blindly.
                    try:
                        prove();build_prove()
                        write(tx/'failed.json',encoded({'state':'CONSUMED_RECONCILIATION_REQUIRED',
                            'restored_config_retained':bool(owned) and same_update_file(profile_home/'config.yaml',owned.get('config.yaml')),
                            'consumers_stopped':True,'consumers_started':False}))
                        sync_directory(tx)
                    except BaseException as evidence_error:
                        from scripts.dsh_prepare import StopUnconfirmed
                        f.remember_secondary(original_error,evidence_error)
                        raise StopUnconfirmed('ordinary recovery stop/evidence requires reconciliation') from original_error
                    raise
                return {'state':'EXACT_CONFIG_RESTORED_CONSUMERS_STOPPED','ready':False,
                    'source_updated':False,'database_changed':False,'consumers_started':False}
    finally:
        os.close(fd)


# Exact, separate CURRENT-deployment inference rebind. Source update v33 above
# remains unchanged. This action never starts a consumer or changes an admission.
REBIND_SCHEMA = 'friday.ordinary-existing-inference-rebind.v1'
REBIND_BUDGET_SCHEMA = 'friday.ordinary-existing-inference-rebind.v2'
REBIND_RENDERER_SCHEMA = 'friday.ordinary-existing-inference-rebind.v3'


def inference_delta(current, original, replacement):
    """Apply compiler-caused changes only; reject drift at every changed leaf.

    Native onboarding identities and owner settings outside that delta survive.
    A changed list is one exact CAS value, never an implicit scope merge.
    """
    import copy
    f = api()
    if original == replacement: return copy.deepcopy(current)
    if type(original) is dict and type(replacement) is dict:
        f.require(type(current) is dict, 'ordinary_rebind_configuration_delta_drift')
        result = copy.deepcopy(current)
        for key in set(original) | set(replacement):
            if key not in original:
                f.require(key not in current, 'ordinary_rebind_configuration_delta_drift')
                result[key] = copy.deepcopy(replacement[key])
            elif key not in replacement:
                f.require(key in current and current[key] == original[key],
                    'ordinary_rebind_configuration_delta_drift')
                del result[key]
            elif original[key] != replacement[key]:
                f.require(key in current, 'ordinary_rebind_configuration_delta_drift')
                result[key] = inference_delta(current[key],original[key],replacement[key])
        return result
    f.require(current == original, 'ordinary_rebind_configuration_delta_drift')
    return copy.deepcopy(replacement)


def inference_private_reasoning(config):
    """Explicit requested privacy migration even when historical flags are absent."""
    f=api()
    for mapping,key in ((config,'display'),):
        f.require(key not in mapping or type(mapping[key]) is dict,'ordinary_rebind_reasoning_display_shape_required')
    display=config.setdefault('display',{})
    display['show_reasoning']=False
    f.require('platforms' not in display or type(display['platforms']) is dict,
        'ordinary_rebind_reasoning_display_shape_required')
    platforms=display.setdefault('platforms',{})
    f.require('telegram' not in platforms or type(platforms['telegram']) is dict,
        'ordinary_rebind_reasoning_display_shape_required')
    platforms.setdefault('telegram',{})['show_reasoning']=False
    return config


def inference_env_values(raw):
    """Parse owned dotenv without interpolation or process/global fallbacks."""
    import io
    from dotenv.parser import parse_stream
    f = api(); values = {}; parts = []
    try:
        text = raw.decode('utf-8')
        f.require('${' not in text, 'ordinary_rebind_dotenv_interpolation_refused')
        for item in parse_stream(io.StringIO(text)):
            f.require(not item.error, 'ordinary_rebind_dotenv_invalid')
            if item.key is not None:
                f.require(item.key not in values and isinstance(item.value,str),
                    'ordinary_rebind_dotenv_duplicate_or_invalid')
                values[item.key] = item.value
            parts.append((item.key,item.original.string))
    except (UnicodeError,TypeError):
        raise ValueError('ordinary_rebind_dotenv_invalid') from None
    return values,parts


def inference_secret(value):
    api().require(isinstance(value,str) and 0 < len(value) <= 16384 and value.isascii()
        and value == value.strip() and '${' not in value
        and not any(ord(c)<32 or ord(c)==127 for c in value),
        'ordinary_rebind_credential_missing_or_invalid')
    return value


def inference_env_after(raw, new_primary):
    """Retain this home's 27B key independently and preserve every other byte."""
    f = api(); values,parts = inference_env_values(raw)
    primary = 'FRIDAY_LLM_API_KEY'; compressor = 'FRIDAY_COMPRESSION_API_KEY'
    old = inference_secret(values.get(primary)); inference_secret(new_primary)
    f.require(compressor not in values or values[compressor] == old,
        'ordinary_rebind_existing_compression_key_conflict')
    def line(name,value):
        # python-dotenv's supported single-quoted representation; no interpolation.
        return name + "='" + value.replace('\\','\\\\').replace("'","\\'") + "'\n"
    result = ''.join(line(primary,new_primary) if name == primary else original
        for name,original in parts)
    if compressor not in values:
        result += ('' if not result or result.endswith('\n') else '\n') + line(compressor,old)
    after = result.encode(); checked,_ = inference_env_values(after)
    f.require(checked == dict(values,**{primary:new_primary,compressor:old}),
        'ordinary_rebind_credential_roundtrip_failed')
    return after


def inference_primary_reference(reference):
    """Read exactly the supplied protected selector, never search for a key."""
    from scripts.install_credentials import references
    f = api(); references({'FRIDAY_LLM_API_KEY':reference})
    raw = f.owned_file(f.canonical(reference['path']),private=True)
    f.require(len(raw)<=1024*1024, 'ordinary_rebind_credential_source_too_large')
    try:
        values = (json.loads(raw,object_pairs_hook=f.unique) if reference['format']=='json'
            else inference_env_values(raw)[0])
        f.require(type(values) is dict, 'ordinary_rebind_credential_source_invalid')
        return inference_secret(values.get(reference['name']))
    except (UnicodeError,TypeError,KeyError):
        raise ValueError('ordinary_rebind_credential_source_invalid') from None


@contextlib.contextmanager
def inference_locks(home, profile_home, access_path, budget):
    """Native ordering: state, root/user config, root/user dotenv; no new locks."""
    from hermes_cli.config import _env_write_lock
    from hermes_cli.plugins_state import PluginState
    from plugins.friday_rework.associations import Associations
    from hermes_cli.auth import _auth_store_lock
    f = api(); paths = [home/'config.yaml.lock',profile_home/'config.yaml.lock',
        home/'.env.lock',profile_home/'.env.lock',home/'auth.lock',profile_home/'auth.lock',
        access_path.with_name('.state.json.lock')]
    states = {}
    for path in paths:
        state = update_file_state(path)
        f.require(state is not None and state['data'] == b'' and state['mode'] == 0o600,
            'ordinary_rebind_existing_private_native_lock_required')
        states[path] = state['identity']
    def prove():
        for path,identity in states.items():
            state = update_file_state(path)
            f.require(state is not None and state['identity'] == identity,
                'ordinary_rebind_native_lock_identity_changed')
    # Native admission.lock serializes supported access/onboarding writers.
    # Holding .state.json.lock across native proof reads would self-deadlock.
    admission=access_path.with_name('admission.lock')
    state=update_file_state(admission)
    f.require(state is not None and state['data']==b'v1\n' and state['mode']==0o600,
        'ordinary_rebind_existing_native_admission_required')
    states[admission]=state['identity']
    state_document=f.read_json(access_path)
    f.require('associations.v1' in state_document,'ordinary_rebind_existing_associations_required')
    with Associations(PluginState('friday_rework'))._locked():
        with retained_first_contact_config_lock(home/'config.yaml'):
            with retained_first_contact_config_lock(profile_home/'config.yaml'):
                with _auth_store_lock(target_path=home/'auth.json'), _auth_store_lock(target_path=profile_home/'auth.json'), \
                        _env_write_lock(home/'.env'), _env_write_lock(profile_home/'.env'):
                    prove(); yield prove; prove()


def inference_renderer_references(product):
    """Validate the compressor's two local pins; no installation/live attestation.

    Native load_renderer verifies the pinned documents, local implementation,
    tokenizer assets and dependency bytes. External PM/deployment evidence must
    already have been independently authenticated by the operator; its digest
    fields alone do not establish installation or live serving acceptance.
    """
    f=api();exact=product['compression_inference'].get('exact_renderer')
    f.require(type(exact) is dict and set(exact)=={'binding','deployment'},
        'ordinary_rebind_exact_renderer_pins_required')
    refs=[]
    for name in ('binding','deployment'):
        ref=exact[name]
        f.require(type(ref) is dict and set(ref)=={'path','sha256'},
            'ordinary_rebind_exact_renderer_pins_required')
        refs.append(f.pin(ref))
    f.require(refs[0]!=refs[1],'ordinary_rebind_distinct_renderer_pins_required')
    from agent.protected_compressor_renderer import load_renderer
    load_renderer(*(exact[name][field] for name in ('binding','deployment')
        for field in ('path','sha256')))
    return tuple(refs)


def inference_renderer_delta(old,new):
    """One new compressor exact_renderer leaf; preserve every other typed input value."""
    f=api();field='exact_renderer'
    f.require(type(old) is dict and type(new) is dict
        and {'inference','compression_inference','compression_multipass'}<=set(old)
        and type(old['inference']) is dict
        and field not in old['inference']
        and type(old['compression_inference']) is dict
        and type(new.get('compression_inference')) is dict
        and field not in old['compression_inference']
        and field in new['compression_inference']
        and encoded({k:v for k,v in old.items() if k!='compression_inference'})==
            encoded({k:v for k,v in new.items() if k!='compression_inference'})
        and encoded(old['compression_inference'])==
            encoded({k:v for k,v in new['compression_inference'].items() if k!=field})
        and old['inference'].get('key_env')=='FRIDAY_LLM_API_KEY'
        and old['compression_inference'].get('key_env')=='FRIDAY_COMPRESSION_API_KEY'
        and all(type(p.get('runtime')) is dict and set(p['runtime'])=={'enabled'}
            and p['runtime']['enabled'] is False for p in (old,new)),
        'ordinary_rebind_exact_compressor_renderer_delta_required')
    return inference_renderer_references(new)


def inference_rebind_inputs(request, budget):
    """Exact pinned beforeimages, unchanged source inventory and historical clocks."""
    f = api()
    budget_only = type(request) is dict and request.get('schema') == REBIND_BUDGET_SCHEMA
    renderer_only = type(request) is dict and request.get('schema') == REBIND_RENDERER_SCHEMA
    config_only = budget_only or renderer_only
    fields = {'schema','seconds','home','profile','previous_input','current_input',
        'native_unit','before','retained'} | (set() if config_only else {'primary_credentials'})
    f.require(type(request) is dict and set(request)==fields
        and request['schema'] in (REBIND_SCHEMA,REBIND_BUDGET_SCHEMA,REBIND_RENDERER_SCHEMA) and request['profile']=='dest_telegram'
        and type(request['seconds']) is int and 30<=request['seconds']<=180,
        'ordinary_rebind_explicit_request_required')
    home = f.directory(f.canonical(request['home']));source=f.directory(home/'hermes-agent')
    f.require(os.environ.get('HERMES_HOME')==str(home),'ordinary_rebind_exact_environment_required')
    f.directory(home/'profiles');profile_home=f.directory(home/'profiles'/request['profile'])
    f.directory(home/'preparation')
    # Authenticate the existing native package before importing its helpers.
    before_input=f.read_json(f.pin(request['previous_input']))
    after_input=f.read_json(f.pin(request['current_input']))
    budget.call(f.inspect,before_input,request['previous_input']['sha256'])
    from hermes_cli import friday_user_scope as user
    from hermes_cli.plugins_state import _plugin_data_namespace
    relative = 'profiles/'+request['profile']+'/'
    names = {'config.yaml','FRIDAY-PROFILE.json',f.MARKER,'.env',relative+'config.yaml',
        relative+user.ONBOARDING,relative+user.MARKER,relative+'.env'}
    if config_only: names -= {'.env',relative+'.env','FRIDAY-PROFILE.json'}
    f.require(type(request['before']) is dict and set(request['before'])==names,
        'ordinary_rebind_exact_before_inventory_required')
    for name,ref in request['before'].items():
        f.require(f.pin(ref)==home/name,'ordinary_rebind_exact_before_path_required')
        f.owned_file(home/name,private=True)
        f.require(update_file_state(home/name)['mode']==0o600,
            'ordinary_rebind_existing_private_file_required')
    # Existing pools can override provider credentials. Preserve them and refuse
    # until their exact provider-entry migration is independently reviewed.
    for own in (home,profile_home):
        f.require(not os.path.lexists(own/'auth.json'),
            'ordinary_rebind_existing_auth_pool_migration_required')
    if not config_only:
        credentials=request['primary_credentials']
        f.require(type(credentials) is dict and set(credentials)=={'root','user'},
            'ordinary_rebind_separate_home_credential_references_required')
        from scripts.install_credentials import references
        for reference in credentials.values(): references({'FRIDAY_LLM_API_KEY':reference})
    f.require(request['previous_input']!=request['current_input']
        and before_input.get('home')==after_input.get('home')==str(home)
        and {k:v for k,v in before_input.items() if k!='product'}==
            {k:v for k,v in after_input.items() if k!='product'}
        and (not renderer_only or encoded({k:v for k,v in before_input.items() if k!='product'})==
            encoded({k:v for k,v in after_input.items() if k!='product'})),
        'ordinary_rebind_source_inventory_or_original_budget_changed')
    old=before_input['product'];new=after_input['product']
    if renderer_only:
        inference_renderer_delta(old,new)
    elif budget_only:
        budget_field='request_budget_seconds'
        f.require(type(old) is dict and type(new) is dict
            and {'inference','compression_inference','compression_multipass'} <= set(old)
            and type(old['inference']) is dict and type(new.get('inference')) is dict
            and budget_field in new['inference']
            and old['inference'].get(budget_field) != new['inference'][budget_field]
            and {k:v for k,v in old.items() if k!='inference'} ==
                {k:v for k,v in new.items() if k!='inference'}
            and {k:v for k,v in old['inference'].items() if k!=budget_field} ==
                {k:v for k,v in new['inference'].items() if k!=budget_field}
            and old['inference']['key_env']=='FRIDAY_LLM_API_KEY'
            and old['compression_inference']['key_env']=='FRIDAY_COMPRESSION_API_KEY'
            and all(type(p['runtime']) is dict and set(p['runtime'])=={'enabled'}
                and p['runtime']['enabled'] is False for p in (old,new)),
            'ordinary_rebind_exact_primary_request_budget_delta_required')
    else:
        route_fields={'inference','compression_inference','compression_multipass'}
        f.require(type(old) is dict and type(new) is dict
            and 'compression_inference' not in old and 'compression_multipass' not in old
            and route_fields<=set(new)
            and all(type(p['runtime']) is dict and set(p['runtime'])=={'enabled'}
                and p['runtime']['enabled'] is False for p in (old,new))
            and {k:v for k,v in old.items() if k not in route_fields}==
                {k:v for k,v in new.items() if k not in route_fields}
            and old['inference']['key_env']==new['inference']['key_env']=='FRIDAY_LLM_API_KEY'
            and new['compression_inference']['key_env']=='FRIDAY_COMPRESSION_API_KEY'
            and {k:v for k,v in old['inference'].items() if k!='key_env'}==
                {k:v for k,v in new['compression_inference'].items() if k!='key_env'},
            'ordinary_rebind_exact_preserved_compressor_and_scope_required')
    # Do not bypass the normal restart input validator: current versions reject
    # split declarations until its separately reviewed integration is installed.
    budget.call(f.spec_checked,after_input,cli_only=True)
    marker=f.read_json(home/f.MARKER)
    f.require(marker.get('completion_stage')=='TELEGRAM_ORDINARY'
        and marker.get('runtime_ready') is False
        and f.cli_historical_scope_closed(marker['original_attempt'],'friday.native-install.v1')
        and (marker.get('cli_segment') is None or
            f.cli_historical_scope_closed(marker['cli_segment']['clock'],'friday.cli-segment-clock.v1')),
        'ordinary_rebind_closed_original_clocks_required')
    access_path=home/'plugin-data'/_plugin_data_namespace('friday_rework','')/'state.json'
    required={'hermes-agent.source.json','hermes-agent/install-stamp.json',
        'hermes-agent/.hermes/bin/hermes','SOUL.md',relative+'SOUL.md',str(access_path.relative_to(home)),
        str(access_path.with_name('admission.lock').relative_to(home)),
        *marker['ordinary_gateway']['history']}
    if config_only: required.update({'.env',relative+'.env','FRIDAY-PROFILE.json'})
    retained=request['retained']
    f.require(type(retained) is dict and required<=set(retained)
        and not set(retained)&names,'ordinary_rebind_retained_history_required')
    for name,ref in retained.items():
        path=Path(name)
        f.require(not path.is_absolute() and '..' not in path.parts and '.' not in path.parts
            and f.pin(ref)==home/path,'ordinary_rebind_exact_retained_path_required')
    f.pin(request['native_unit'])
    return home,source,profile_home,access_path,before_input,after_input,marker


@contextlib.contextmanager
def inference_retaining_cleanup(fd):
    """Native custody teardown cannot replace the transaction's primary cause."""
    primary=None
    try:
        with contextlib.ExitStack() as stack:
            stack.callback(os.close,fd)
            try:
                yield stack
            except BaseException as error:
                primary=error
                raise
    except BaseException as cleanup:
        if primary is None or cleanup is not primary:
            from scripts.dsh_prepare import StopUnconfirmed
            cause=primary if primary is not None else cleanup
            if cleanup is not cause: api().remember_secondary(cause,cleanup)
            raise StopUnconfirmed('ordinary inference rebind custody cleanup requires reconciliation') from cause
        raise


def rebind_inference(request, request_path, budget):
    """One finite operator transaction; consumers remain stopped, all-or-rollback.

    Only compiler-caused inference deltas and native reseals are published. The
    journal is not a capability or a new history entry in ordinary_gateway.
    """
    import copy
    budget_only = request.get('schema') == REBIND_BUDGET_SCHEMA
    renderer_only = request.get('schema') == REBIND_RENDERER_SCHEMA
    config_only = budget_only or renderer_only
    f=api();request_path=f.canonical(str(request_path))
    request_state=update_file_state(request_path);f.owned_file(request_path,private=True)
    f.require(request_state is not None and json.loads(request_state['data'],object_pairs_hook=f.unique)==request,
        'ordinary_rebind_request_changed')
    # Statically reject unknown fields/pools/unsupported restart inputs before
    # host custody or any journal/configuration/credential publication.
    home,source,profile_home,access_path,previous,current,marker=inference_rebind_inputs(request,budget)
    renderer_states=({path:update_file_state(path) for path in
        inference_renderer_references(current['product'])} if renderer_only else {})
    tx=home/'preparation'/('ordinary-inference-rebind-'+request['previous_input']['sha256'])
    f.require(not os.path.lexists(tx),'ordinary_rebind_consumed_no_retry')
    fd=os.open(home,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    with inference_retaining_cleanup(fd) as native_stack:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        home_identity=(os.fstat(fd).st_dev,os.fstat(fd).st_ino)
        directory_identities={path:(path.lstat().st_dev,path.lstat().st_ino) for path in
            (home,home/'profiles',profile_home,source,home/'preparation',access_path.parent)}
        def directories_unchanged():
            for path,identity in directory_identities.items():
                f.directory(path);info=path.lstat()
                f.require((info.st_dev,info.st_ino)==identity,'ordinary_rebind_directory_identity_changed')
        native_prove=native_stack.enter_context(stopped_consumers(home,request['native_unit'],budget))
        build_prove=native_stack.enter_context(retained_build_lock(source))
        lock_prove=native_stack.enter_context(inference_locks(home,profile_home,access_path,budget))
        def custody():
            native_prove();build_prove();lock_prove();directories_unchanged();budget.check()
            info=home.lstat()
            f.require((info.st_dev,info.st_ino)==home_identity,'ordinary_rebind_home_identity_changed')
        again=inference_rebind_inputs(request,budget)
        f.require(again==(home,source,profile_home,access_path,previous,current,marker),
            'ordinary_rebind_cas_changed')
        saved={name:update_file_state(home/name) for name in request['before']}
        retained={name:update_file_state(home/name) for name in request['retained']}
        f.require(all(v is not None and f.digest(v['data'])==request['before'][n]['sha256'] for n,v in saved.items())
            and all(v is not None and f.digest(v['data'])==request['retained'][n]['sha256'] for n,v in retained.items()),
            'ordinary_rebind_exact_snapshot_hash_changed')
        external={request_path:request_state,Path(request['previous_input']['path']):update_file_state(Path(request['previous_input']['path'])),
            Path(request['current_input']['path']):update_file_state(Path(request['current_input']['path'])),
            Path(request['native_unit']['path']):update_file_state(Path(request['native_unit']['path']))}
        f.require(all(state is not None and f.digest(state['data'])==ref['sha256'] for ref,state in
            ((request['previous_input'],external[Path(request['previous_input']['path'])]),
             (request['current_input'],external[Path(request['current_input']['path'])]),
             (request['native_unit'],external[Path(request['native_unit']['path'])]))),
            'ordinary_rebind_exact_external_hash_changed')
        if renderer_only:
            for path,state in renderer_states.items():
                f.require(same_update_file(path,state),'ordinary_rebind_renderer_reference_identity_changed')
                f.require(path not in {home/n for n in saved} and path not in {home/n for n in retained}
                    and path not in external,'ordinary_rebind_renderer_reference_alias_refused')
                external[path]=state
        # A reference may not alias any destination or historical state.
        for reference in request.get('primary_credentials',{}).values():
            path=f.canonical(reference['path'])
            f.require(path not in {home/n for n in saved} and path not in {home/n for n in retained},
                'ordinary_rebind_credential_source_alias_refused')
            state=update_file_state(path);f.owned_file(path,private=True)
            external[path]=state
        def retained_unchanged():
            custody()
            if renderer_only: inference_renderer_references(current['product'])
            f.require(all(same_update_file(home/n,v) for n,v in retained.items())
                and all(same_update_file(p,v) for p,v in external.items())
                and all(not os.path.lexists(h/'auth.json') for h in (home,profile_home)),
                'ordinary_rebind_retained_or_protected_reference_changed')
        def before_unchanged():
            retained_unchanged()
            f.require(all(same_update_file(home/n,v) for n,v in saved.items()),
                'ordinary_rebind_beforeimage_identity_changed')
        from tools.configure_product import compose_product
        from plugins.friday_rework.onboarding import prepare_admin_config_edit,finish_admin_config_edit,validate_template
        from hermes_cli.config import atomic_config_write
        from hermes_cli import friday_user_scope as user
        from hermes_cli.friday_ordinary_gateway import normalized_configuration,credential_identity,check
        from hermes_yaml import safe_load
        old_bundle=compose_product(previous['product']);new_bundle=compose_product(current['product'])
        original_cfg=safe_load(saved['config.yaml']['data'])
        settings_path=lambda cfg:cfg['plugins']['entries']['friday_rework']['settings']
        templates=settings_path(original_cfg)['onboarding']['templates']
        f.require(type(templates) is dict and set(templates)=={'friday-local','friday-ordinary-local'},
            'ordinary_rebind_exact_existing_templates_required')
        ordinary_before=templates['friday-ordinary-local']
        ordinary_settings=settings_path(ordinary_before['config'])
        f.require('worker_inputs' not in ordinary_before
            and type(ordinary_settings.get('runtime')) is dict
                    and set(ordinary_settings['runtime'])=={'enabled'}
                    and ordinary_settings['runtime']['enabled'] is False
            and 'worker_requirements' not in ordinary_settings,
            'ordinary_rebind_ordinary_template_independence_required')
        root_cfg=inference_delta(original_cfg,old_bundle['config'],new_bundle['config'])
        old_base=old_bundle['config']['plugins']['entries']['friday_rework']['settings']['onboarding']['templates']['friday-local']
        new_base=new_bundle['config']['plugins']['entries']['friday_rework']['settings']['onboarding']['templates']['friday-local']
        old_ordinary=copy.deepcopy(old_base);old_ordinary.pop('worker_inputs',None)
        new_ordinary=copy.deepcopy(new_base);new_ordinary.pop('worker_inputs',None)
        rebound_templates=settings_path(root_cfg)['onboarding']['templates']
        rebound_templates['friday-ordinary-local']=inference_delta(ordinary_before,old_ordinary,new_ordinary)
        if not config_only: inference_private_reasoning(root_cfg)
        for selected_template in rebound_templates.values():
            if not config_only: inference_private_reasoning(selected_template['config'])
            validate_template(selected_template)
        proof_name='profiles/'+request['profile']+'/'+user.ONBOARDING
        user_prefix='profiles/'+request['profile']+'/'
        proof=json.loads(saved[proof_name]['data']);template=proof['template']
        f.require(template in templates,'ordinary_rebind_existing_template_alias_required')
        old_template=old_base if template=='friday-local' else old_ordinary
        new_template=rebound_templates[template]
        user_cfg=inference_delta(safe_load(saved[user_prefix+'config.yaml']['data']),old_template['config'],
            new_base['config'])
        if not config_only: inference_private_reasoning(user_cfg)
        required=list(proof['required_secrets'])
        if not config_only and 'FRIDAY_COMPRESSION_API_KEY' not in required: required.append('FRIDAY_COMPRESSION_API_KEY')
        # Existing profiles may have additional, already admitted capabilities
        # (for example the scoped browser). The native edit validator below
        # checks the complete candidate against that profile's current binding;
        # the base template's tools are not its authorization inventory.
        prepared=prepare_admin_config_edit(profile_home,user_cfg,required_secrets=required)
        f.require(prepared is not None and prepared['marker'] is not None,
            'ordinary_rebind_existing_admitted_onboarding_required')
        profile=(None if config_only else inference_delta(json.loads(saved['FRIDAY-PROFILE.json']['data']),old_bundle['contract'],new_bundle['contract']))
        if config_only:
            f.require(old_bundle['contract']==new_bundle['contract'], 'ordinary_rebind_configuration_only_contract_changed')
        before_unchanged();f.require(not os.path.lexists(tx),'ordinary_rebind_consumed_no_retry')
        tx.mkdir(mode=0o700);stage=tx/'stage';stage.mkdir(mode=0o700)
        before=tx/'before';before.mkdir(mode=0o700)
        # Intent is consumed before any staging/publication. A failed
        # preparation is retained, never re-executed under a new clock.
        write(tx/'intent.json',encoded({'schema':request['schema'],'state':'CONSUMED_NO_RETRY',
            'request_sha256':f.digest(request_state['data']),'seconds':request['seconds'],
            'previous_input':request['previous_input'],'current_input':request['current_input'],
            'before':{n:{'sha256':f.digest(v['data']),'mode':v['mode']} for n,v in saved.items()},
            'consumers_started':False,'workers_enabled':False,'database_changed':False}),0o400)
        sync_directory(tx);sync_directory(tx.parent)
        owned={}
        try:
            for name,state in saved.items():
                private_parents(before,name);write(before/name,state['data'])
            for prefix,cfg in (('',root_cfg),(user_prefix,user_cfg)):
                private_parents(stage,prefix+'config.yaml')
                # Fresh private staging destination: complete afterimage
                # through the native atomic writer, no omission bypass.
                atomic_config_write(stage/prefix/'config.yaml',cfg)
                f.require(safe_load(f.owned_file(stage/prefix/'config.yaml',private=True))==cfg,
                    'ordinary_rebind_staged_configuration_changed')
                if not config_only:
                    original=saved[prefix+'.env']['data']
                    selected=inference_primary_reference(request['primary_credentials']['user' if prefix else 'root'])
                    write(stage/prefix/'.env',inference_env_after(original,selected));del selected
            stage_user=stage/user_prefix
            write(stage_user/user.ONBOARDING,saved[proof_name]['data'])
            write(stage_user/user.MARKER,saved[user_prefix+user.MARKER]['data'])
            finish_admin_config_edit(stage_user,prepared)
            write(stage/'FRIDAY-PROFILE.json',retained['FRIDAY-PROFILE.json']['data'] if config_only else encoded(profile))
            updated=copy.deepcopy(marker)
            updated['input_sha256']=request['current_input']['sha256']
            updated['profile_files']['config.yaml']=f.digest(f.owned_file(stage/'config.yaml',private=True))
            updated['profile_files']['FRIDAY-PROFILE.json']=f.digest(f.owned_file(stage/'FRIDAY-PROFILE.json',private=True))
            phase=updated['ordinary_gateway']
            phase['profile_sha256']=updated['profile_files']['FRIDAY-PROFILE.json']
            # Effective native config includes defaults; raw-YAML hashing
            # would differ from the exact ordinary check on restart.
            from hermes_cli.config_effective import load_user_config_effective
            phase['configuration_sha256']=normalized_configuration(load_user_config_effective(stage/'config.yaml',fail_closed=True))
            if not config_only: phase['credential_files']['.env']=credential_identity(stage)[0]
            phase['operator_entry']['input']=request['current_input']
            write(stage/f.MARKER,encoded(updated))
            staged={name:update_file_state(stage/name) for name in saved}
            f.require(all(v is not None and v['mode']==0o600 for v in staged.values()),
                'ordinary_rebind_complete_private_stage_required')
            # Native split admission and root contract validation before
            # replacing the first durable live file. No test receipt can
            # substitute for these real native configuration validators.
            from hermes_cli.friday_credential_admission import local_route,profile_policy
            local_route(root_cfg);local_route(user_cfg);profile_policy(stage,root_cfg)
            # Bytes were fsynced by write(); retain all nested directory entries
            # durably before replacing the first existing deployment file.
            for durable_root in (before,stage):
                for directory in sorted((p for p in durable_root.rglob('*') if p.is_dir()),
                        key=lambda p:len(p.parts),reverse=True):
                    f.directory(directory);sync_directory(directory)
                sync_directory(durable_root)
            sync_directory(tx)
            before_unchanged()
            order=['config.yaml',user_prefix+'config.yaml',proof_name,user_prefix+user.MARKER,f.MARKER] if config_only else [
                '.env',user_prefix+'.env','config.yaml',user_prefix+'config.yaml',
                'FRIDAY-PROFILE.json',proof_name,user_prefix+user.MARKER,f.MARKER]
            for name in order:
                retained_unchanged();budget.check(reserve=15)
                f.require(all(same_update_file(home/n,owned.get(n,v)) for n,v in saved.items()),
                    'ordinary_rebind_publication_cas_changed')
                f.require(same_update_file(stage/name,staged[name]),'ordinary_rebind_stage_identity_changed')
                publish_update_file(home/name,staged[name]['data'],saved[name]['mode'],saved[name],owned,name)
            retained_unchanged();check(home,role=False)
            settings=root_cfg['plugins']['entries']['friday_rework']['settings']
            bindings=[b for b in settings['user_isolation']['bindings'] if b['runtime_profile']==request['profile']]
            f.require(len(bindings)==1,'ordinary_rebind_single_existing_binding_required')
            binding=bindings[0];principal=tuple(binding[k] for k in ('platform','transport_profile','account_id','user_id'))
            from hermes_cli.friday_product_access import current_access,principal_id
            with user.authority(home): row=current_access()['users'][principal_id(*principal)]
            f.require(row['enabled'] is True and row['role']=='user','ordinary_rebind_original_user_disabled')
            info=profile_home.stat()
            with user.authority(profile_home):
                user.UserScope(home,profile_home,request['profile'],principal,dict(binding),
                    (info.st_dev,info.st_ino),row['generation']).check()
            budget.call(f.inspect,current,request['current_input']['sha256'])
            retained_unchanged()
            f.require(all(same_update_file(home/n,owned[n]) for n in saved),
                'ordinary_rebind_commit_identity_changed')
            result={'state':('EXACT_COMPRESSOR_RENDERER_REBOUND_CONSUMERS_STOPPED_NOT_RUNTIME_ACCEPTED' if renderer_only else
                'EXACT_REQUEST_BUDGET_REBOUND_CONSUMERS_STOPPED_NOT_RUNTIME_ACCEPTED' if budget_only else
                'EXACT_INFERENCE_REBOUND_CONSUMERS_STOPPED_NOT_RUNTIME_ACCEPTED'),
                'ready':False,'workers_enabled':False,'consumers_started':False,'database_changed':False,
                'after':{n:f.digest(v['data']) for n,v in staged.items()}}
            write(tx/'committed.json',encoded(result),0o400);sync_directory(tx)
            return result
        except BaseException as original_error:
            try:
                # Retain original finite custody and budget. If their
                # proof fails, preserve the primary error and stop closed.
                native_prove();build_prove();lock_prove();directories_unchanged()
                if renderer_only:
                    f.require(not os.path.lexists(tx/'committed.json'),
                        'ordinary_rebind_renderer_commit_outcome_ambiguous')
                restore_update_files(home,saved,owned)
                f.require(all(same_update_file(home/n,v) for n,v in retained.items())
                    and all(same_update_file(p,v) for p,v in external.items()),
                    'ordinary_rebind_rollback_retained_state_changed')
                check(home,role=False)
                write(tx/'rolled-back.json',encoded({'state':'ROLLED_BACK_CONSUMED_NO_RETRY',
                    'consumers_started':False,'database_changed':False}),0o400);sync_directory(tx)
            except BaseException as restoration:
                from scripts.dsh_prepare import StopUnconfirmed
                f.remember_secondary(original_error,restoration)
                raise StopUnconfirmed('ordinary inference rebind rollback requires reconciliation') from original_error
            raise


def _dispatch_dsh_current_native(request, *, request_path, request_sha256, operation):
    """Bootstrap the exact installed child after authenticating native source.

    This selects code, not authority. The writer retains the raw request and
    original clock and obtains all admission/stop/CAS custody itself.
    """
    import importlib.util
    import sys
    from _friday_install_validation_plugins.friday_rework.worker_declarations import (
        DSH_CURRENT_APPLY_SCHEMA, _read_reference, _same, require,
    )
    require(sys.dont_write_bytecode, 'dsh_current_native_no_bytecode_required')
    require(operation in ('declaration', 'observation'), 'dsh_current_native_operation_required')
    schema = (DSH_CURRENT_APPLY_SCHEMA if operation == 'declaration'
        else 'friday.dsh-current-observation.apply.v1')
    require(type(request) is dict and request.get('schema') == schema,
        'dsh_current_exact_apply_schema_required' if operation == 'declaration'
            else 'dsh_current_exact_observation_schema_required')
    if operation == 'observation':
        require(set(request) == {'schema', 'seconds', 'home', 'profile', 'current_input',
            'native_unit', 'native_pm', 'clock', 'pending_transaction'},
            'dsh_current_exact_observation_request_required')
    reference = {'path': str(request_path), 'sha256': request_sha256}
    require(_same(_read_reference(reference), request), 'dsh_current_raw_request_changed')
    if operation == 'declaration':
        require(request['previous_input'] == request['current_input'],
            'dsh_current_installation_input_must_remain_unchanged')
    current = _read_reference(request['current_input'])
    f = api()
    home = f.directory(f.canonical(request['home']))
    source = f.directory(home / 'hermes-agent')
    require(current.get('home') == str(home)
        and os.environ.get('HERMES_HOME') == str(home),
        'dsh_current_exact_native_home_required')
    checked_home, donors = f.spec_checked(current, cli_only=True)
    require(checked_home == home, 'dsh_current_current_input_home_changed')
    marker = f.read_json(home / f.MARKER)
    entry = marker['ordinary_gateway']['operator_entry']
    require(marker.get('input_sha256') == request['current_input']['sha256']
        and type(entry) is dict and set(entry) == {'script', 'input'}
        and entry['input'] == request['current_input']
        and entry['script'] == {'path': str(f.ROOT / 'scripts/friday_native.py'),
            'sha256': current['project_files']['scripts/friday_native.py']},
        'dsh_current_native_operator_input_join_changed')
    for name in ('scripts/friday_install.py', 'scripts/friday_ordinary_install.py',
            'scripts/friday_native.py'):
        require(f.digest(f.owned_file(f.ROOT / name)) == current['project_files'][name],
            'dsh_current_selected_operator_source_changed')
    receipt_raw = f.owned_file(home / 'hermes-agent.source.json', private=True)
    require(f.digest(receipt_raw) == marker.get('source_receipt_sha256'),
        'dsh_current_native_source_receipt_changed')
    receipt = json.loads(receipt_raw, object_pairs_hook=f.unique)
    f.composition_checked(current, source, receipt, donors['hermes'])

    prefix = 'plugins/friday_rework/'
    expected = {name: sha for name, sha in current['project_files'].items()
        if name.startswith(prefix)}
    require(expected and prefix + '__init__.py' in expected
        and marker.get('plugin_files') == expected,
        'dsh_current_installed_plugin_inventory_changed')
    child = f.directory(home / 'plugins' / 'friday_rework')
    expected_directories = {str(parent) for name in expected
        for parent in Path(name).parents if str(parent).startswith(prefix.rstrip('/'))}
    actual = set()
    # Check every installed leaf, including non-Python resources, before init.
    # No linked directory, extra file, bytecode cache or borrowed inode is code.
    for directory, directories, files in os.walk(child, followlinks=False):
        require(str(Path(directory).relative_to(home)) in expected_directories,
            'dsh_current_installed_plugin_inventory_changed')
        f.directory(Path(directory))
        for name in directories:
            path = Path(directory) / name
            require(str(path.relative_to(home)) in expected_directories,
                'dsh_current_installed_plugin_inventory_changed')
            f.directory(path)
        for name in files:
            path = Path(directory) / name
            relative = str(path.relative_to(home))
            require(relative in expected and f.digest(f.owned_file(path, private=True))
                == expected[relative], 'dsh_current_installed_plugin_source_changed')
            actual.add(relative)
            require(len(actual) <= len(expected), 'dsh_current_installed_plugin_inventory_changed')
    require(actual == set(expected), 'dsh_current_installed_plugin_inventory_changed')

    canonical = 'plugins.friday_rework'
    def loaded_origins():
        for name, module in tuple(sys.modules.items()):
            if name != canonical and not name.startswith(canonical + '.'):
                continue
            relative = prefix + name[len(canonical):].lstrip('.').replace('.', '/')
            package = getattr(module, '__path__', None) is not None
            relative = (relative.rstrip('/') + '/__init__.py' if package else relative + '.py')
            path = home / relative
            require(relative in expected and getattr(module, '__file__', None) == str(path)
                and Path(module.__file__).resolve() == path
                and getattr(getattr(module, '__spec__', None), 'origin', None) == str(path)
                and (not package or list(module.__path__) == [str(path.parent)])
                and f.digest(f.owned_file(path, private=True)) == expected[relative],
                'dsh_current_loaded_installed_plugin_origin_required')

    loaded_origins()  # Refuse active foreign children; never replace them.
    require(_same(_read_reference(reference), request)
        and _same(_read_reference(request['current_input']), current)
        and f.read_json(home / f.MARKER) == marker,
        'dsh_current_bootstrap_inputs_changed')
    f.native_packages(source)  # Native parents retain N + selected project.
    parents = {name: (getattr(sys.modules[name], '__file__', None),
        getattr(getattr(sys.modules[name], '__spec__', None), 'origin', None),
        tuple(sys.modules[name].__path__)) for name in ('plugins', 'tools')}
    require(str(home / 'plugins') not in sys.path,
        'dsh_current_installed_parent_search_path_refused')
    parent = sys.modules['plugins']
    loaded = sys.modules.get(canonical)
    attached = getattr(parent, 'friday_rework', None)
    require(attached is None or attached is loaded,
        'dsh_current_loaded_installed_plugin_origin_required')
    loaded_origins()
    if loaded is None:
        spec = importlib.util.spec_from_file_location(canonical, child / '__init__.py',
            submodule_search_locations=[str(child)])
        require(spec is not None and spec.loader is not None,
            'dsh_current_installed_plugin_loader_required')
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[canonical] = loaded
        spec.loader.exec_module(loaded)
        parent.friday_rework = loaded
    if operation == 'declaration':
        from plugins.friday_rework.worker_declaration_writer import apply_declarations
        execute = apply_declarations
    else:
        from plugins.friday_rework.stopped_operator import observe_current_native
        execute = observe_current_native
    loaded_origins()
    require(all(parents[name] == (getattr(sys.modules[name], '__file__', None),
        getattr(getattr(sys.modules[name], '__spec__', None), 'origin', None),
        tuple(sys.modules[name].__path__)) for name in parents)
        and str(home / 'plugins') not in sys.path,
        'dsh_current_native_parent_origin_changed')
    return execute(request, request_path=request_path,
        request_sha256=request_sha256)


def apply_dsh_current_declarations(request, *, request_path, request_sha256):
    return _dispatch_dsh_current_native(request, request_path=request_path,
        request_sha256=request_sha256, operation='declaration')


def observe_dsh_current(request, *, request_path, request_sha256):
    return _dispatch_dsh_current_native(request, request_path=request_path,
        request_sha256=request_sha256, operation='observation')


def _dsh_current_observation_failure_diagnostic(error, f, *, phase='observe-dsh-current'):
    """Bounded causal metadata only; never exception text, locals or paths."""
    import sys
    diagnostic = f.retained_diagnostic(error, phase)
    reasons = {'diagnostic_unavailable', 'stop_unconfirmed', 'native_operation_failed',
        'native_io_failed', 'invalid_input_shape', 'original_install_budget_exhausted'}
    reason = diagnostic.get('reason')
    safe = {'reason': reason if type(reason) is str and reason in reasons
        else 'native_operation_failed'}
    for key in ('timeout', 'reaped'):
        value = diagnostic.get(key)
        if type(value) is bool:
            safe[key] = value
    for key in ('errno', 'returncode'):
        value = diagnostic.get(key)
        if type(value) is int and -(2**31) <= value < 2**31:
            safe[key] = value
    cessation = diagnostic.get('cessation')
    if type(cessation) is str and cessation in ('UNCONFIRMED', 'REAPED'):
        safe['cessation'] = cessation
    known = {OSError: 'os_error', PermissionError: 'permission_error',
        FileNotFoundError: 'file_not_found', RuntimeError: 'runtime_error',
        TypeError: 'type_error', ValueError: 'value_error', KeyError: 'key_error',
        IndexError: 'index_error', AssertionError: 'assertion_error',
        TimeoutError: 'timeout_error', json.JSONDecodeError: 'json_decode_error'}
    native = sys.modules.get('scripts.dsh_prepare')
    for cls, label in ((getattr(native, 'StopUnconfirmed', None), 'stop_unconfirmed'),
            (getattr(native, 'CommandFailed', None), 'command_failed'),
            (getattr(f, 'Refused', None), 'source_refused')):
        if isinstance(cls, type):
            known[cls] = label
    for prefix in ('plugins.friday_rework', '_friday_install_validation_plugins.friday_rework'):
        module = sys.modules.get(prefix + '.worker_declarations')
        cls = vars(module).get('DeclarationError') if module is not None else None
        if isinstance(cls, type):
            known[cls] = 'declaration_error'
    location = {'exception_type': known.get(type(error), 'other'), 'source_frames': []}
    allowed = {__file__: 'scripts/friday_ordinary_install.py'}
    # Use only already-loaded fixed modules; failure handling cannot bootstrap H.
    for name, relative in (
            ('scripts.friday_install', 'scripts/friday_install.py'),
            ('scripts.dsh_prepare', 'scripts/dsh_prepare.py'),
            *[(prefix + '.' + name, 'plugins/friday_rework/' + name + '.py')
                for prefix in ('plugins.friday_rework',
                    '_friday_install_validation_plugins.friday_rework')
                for name in ('stopped_operator', 'dsh_current_availability',
                    'worker_declaration_writer', 'worker_declarations', 'runtime_process',
                    'runtime_primitives', 'runtime_containment')]):
        module = sys.modules.get(name)
        filename = vars(module).get('__file__') if module is not None else None
        if type(filename) is str:
            allowed[filename] = relative
    tb = BaseException.__traceback__.__get__(error)
    for _ in range(64):
        if tb is None:
            break
        module = allowed.get(tb.tb_frame.f_code.co_filename)
        if module is not None and 0 < tb.tb_lineno < 2**31:
            location['source_frames'].append({'module': module, 'line': tb.tb_lineno})
            location['source_frames'] = location['source_frames'][-8:]
        tb = tb.tb_next
    location['trace_truncated'] = tb is not None
    return {'diagnostic': safe, 'failure_location': location}


def dsh_current_observation_cli(request, *, request_path, request_sha256):
    """Finish this observation invocation; print no proof, path or private data."""
    import sys
    try:
        result = observe_dsh_current(request, request_path=request_path,
            request_sha256=request_sha256)
        if (type(result) is not dict
                or result.get('state') != 'DSH_CURRENT_OBSERVATION_COMPLETE'
                or result.get('ready') is not False
                or result.get('effects') != 'OBSERVATION_ONLY'
                or result.get('per_job_authority') != 'NOT_GRANTED'):
            from scripts.dsh_prepare import StopUnconfirmed
            raise StopUnconfirmed('dsh current observation returned outcome unconfirmed')
    except Exception as error:
        native = sys.modules.get('scripts.dsh_prepare')
        uncertain_type = getattr(native, 'StopUnconfirmed', None)
        uncertain = isinstance(uncertain_type, type) and isinstance(error, uncertain_type)
        f = api()
        # Original custody owns the terminal before diagnostics, formatting or IO.
        transfer = f.InstallerExit(3 if uncertain else 2, error)
        detail = {'phase': 'observe-dsh-current',
            'request_sha256': request_sha256 if type(request_sha256) is str
                and len(request_sha256) == 64
                and all(c in '0123456789abcdef' for c in request_sha256) else 'UNAVAILABLE',
            'diagnostic': {'reason': 'diagnostic_unavailable'},
            'failure_location': {'exception_type': 'other', 'source_frames': [],
                'trace_truncated': False}}
        try:
            detail.update(_dsh_current_observation_failure_diagnostic(error, f))
        except BaseException as secondary:
            f.remember_secondary(error, secondary)
        # Root captures stderr privately. Each failed projection remains secondary;
        # neither stream may replace the typed original or suppress the other.
        def emit(value, channel):
            try:
                encoded = json.dumps(value, sort_keys=True)
            except BaseException as secondary:
                f.remember_secondary(error, secondary)
                return
            stream = getattr(sys, channel)
            try:
                stream.write(encoded + '\n')
                stream.flush()
            except BaseException as secondary:
                f.remember_secondary(error, secondary)
                # CPython retries original standard-stream flush at shutdown and
                # replaces SystemExit 2/3 with 120 on failure. This terminal owns
                # no further output; detach only its failed original IO stream.
                if (isinstance(secondary, OSError)
                        and stream is getattr(sys, '__' + channel + '__')
                        and getattr(sys, channel) is stream):
                    setattr(sys, channel, None)
        emit(detail, 'stderr')
        emit({'state': 'STOP_UNCONFIRMED' if uncertain else
            'FAILED_CLOSED_RECONCILE_EXACT_JOURNAL', 'ready': False,
            'error': 'dsh_current_observation_stop_unconfirmed' if uncertain else
                'dsh_current_observation_failed_closed',
            'effects': 'NO_ACCEPTANCE_CLAIM', 'per_job_authority': 'NOT_GRANTED'}, 'stdout')
        transfer.friday_custody_secondary = getattr(error, 'friday_secondary_failures', ())
        raise transfer from error
    print(json.dumps({'state': 'DSH_CURRENT_OBSERVATION_COMPLETE', 'ready': False,
        'effects': 'OBSERVATION_ONLY', 'per_job_authority': 'NOT_GRANTED'}, sort_keys=True))
    # The file retains a second historical __main__; never enter it after P.
    raise SystemExit(0)


def dsh_current_declaration_cli(request, *, request_path, request_sha256):
    """Project only bounded status; journals and private pins stay private."""
    import sys
    try:
        result = apply_dsh_current_declarations(request, request_path=request_path,
            request_sha256=request_sha256)
        if (type(result) is not dict
                or result.get('state') != 'WORKER_DECLARATIONS_REBOUND_CONSUMERS_STOPPED'
                or result.get('ready') is not False
                or result.get('workers_enabled') is not False
                or result.get('native_migration') != 'IMPLEMENTED'
                or result.get('consumers_started') is not False
                or result.get('runtime_acceptance') != 'NOT_GRANTED'):
            # A returned unexpected result can follow commit. Do not label it
            # a failed preflight or publish any value supplied in that result.
            print(json.dumps({'state': 'STOP_UNCONFIRMED', 'ready': False,
                'error': 'worker_declaration_returned_outcome_unconfirmed',
                'native_migration': 'NO_ACCEPTANCE_CLAIM'}, sort_keys=True))
            raise SystemExit(3)
    except Exception as error:
        native = sys.modules.get('scripts.dsh_prepare')
        uncertain_type = getattr(native, 'StopUnconfirmed', None)
        uncertain = isinstance(uncertain_type, type) and isinstance(error, uncertain_type)
        f = api()
        # Preserve original custody before best-effort correlation or output.
        transfer = f.InstallerExit(3 if uncertain else 2, error)
        detail = {'phase': 'rebind-worker-declarations',
            'request_sha256': request_sha256 if type(request_sha256) is str
                and len(request_sha256) == 64
                and all(c in '0123456789abcdef' for c in request_sha256) else 'UNAVAILABLE',
            'diagnostic': {'reason': 'diagnostic_unavailable'},
            'failure_location': {'exception_type': 'other', 'source_frames': [],
                'trace_truncated': False}}
        try:
            detail.update(_dsh_current_observation_failure_diagnostic(error, f,
                phase='rebind-worker-declarations'))
        except BaseException as secondary:
            f.remember_secondary(error, secondary)
        def emit(value, channel):
            try:
                encoded = json.dumps(value, sort_keys=True)
            except BaseException as secondary:
                f.remember_secondary(error, secondary)
                return
            stream = getattr(sys, channel)
            try:
                stream.write(encoded + '\n')
                stream.flush()
            except BaseException as secondary:
                f.remember_secondary(error, secondary)
                if (isinstance(secondary, OSError)
                        and stream is getattr(sys, '__' + channel + '__')
                        and getattr(sys, channel) is stream):
                    setattr(sys, channel, None)
        emit(detail, 'stderr')
        emit({'state': 'STOP_UNCONFIRMED' if uncertain else
                'FAILED_CLOSED_RECONCILE_EXACT_JOURNAL', 'ready': False,
            'error': 'worker_declaration_stop_unconfirmed' if uncertain else
                'worker_declaration_request_failed_closed',
            'native_migration': 'NO_ACCEPTANCE_CLAIM'}, 'stdout')
        transfer.friday_custody_secondary = getattr(error, 'friday_secondary_failures', ())
        raise transfer from error
    print(json.dumps({'state': 'WORKER_DECLARATIONS_REBOUND_CONSUMERS_STOPPED',
        'ready': False, 'workers_enabled': False, 'native_migration': 'IMPLEMENTED',
        'runtime_acceptance': 'NOT_GRANTED'}, sort_keys=True))
    # The retained ordinary file has a second historical __main__ below this
    # dispatcher. Finish this exact current invocation before that old entry.
    raise SystemExit(0)


def recovery_main():
    """Dedicated maintenance dispatch; the ordinary installer phases stay unchanged."""
    import sys
    import time
    if any(phase in sys.argv[1:] for phase in ('rebind-worker-declarations',
            'observe-dsh-current')) and not sys.dont_write_bytecode:
        # Refuse before importing a product module that could populate an
        # installed __pycache__ outside the five-file transaction.
        print(json.dumps({'state': 'NOT_STARTED', 'ready': False,
            'error': 'worker_declaration_native_no_bytecode_required'}), file=sys.stderr)
        raise SystemExit(2)
    # Direct module/script invocation resolves the existing product package.
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    f = api(); started = time.monotonic()
    parser = f.SafeParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('phase',choices=('recover-first-contact-config','rebind-inference',
        'rebind-worker-declarations', 'observe-dsh-current'))
    parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--request-sha256')
    args = parser.parse_args(); os.umask(0o077)
    try:
        if args.phase in ('rebind-worker-declarations', 'observe-dsh-current'):
            if args.phase == 'observe-dsh-current':
                f.require(type(args.request_sha256) is str and len(args.request_sha256) == 64
                    and all(char in '0123456789abcdef' for char in args.request_sha256),
                    'dsh_current_exact_request_sha256_required')
            # The new maintenance phase owns an externally pinned original
            # clock; it must never inherit this dispatcher's fresh start.
            # Read only the pure selected-project validator before selecting
            # the exact current branch; native child code is still cold.
            from _friday_install_validation_plugins.friday_rework.worker_declarations import (
                DSH_CURRENT_APPLY_SCHEMA, _read_reference as read_current_request,
            )
            current_request = read_current_request(
                {'path': str(args.request), 'sha256': args.request_sha256})
            if args.phase == 'observe-dsh-current':
                # This terminal phase cannot dispatch a declaration transaction.
                f.require(type(current_request) is dict and current_request.get('schema')
                    == 'friday.dsh-current-observation.apply.v1',
                    'dsh_current_exact_observation_schema_required')
                dsh_current_observation_cli(current_request, request_path=args.request,
                    request_sha256=args.request_sha256)
                return
            f.require(type(current_request) is not dict or current_request.get('schema')
                != 'friday.dsh-current-observation.apply.v1',
                'dsh_current_observation_requires_own_phase')
            if (type(current_request) is dict
                    and current_request.get('schema') == DSH_CURRENT_APPLY_SCHEMA):
                dsh_current_declaration_cli(current_request, request_path=args.request,
                    request_sha256=args.request_sha256)
                return
            from plugins.friday_rework.worker_declarations import _read_reference
            from plugins.friday_rework.worker_declaration_writer import apply_declarations
            request = _read_reference({'path': str(args.request), 'sha256': args.request_sha256})
            result = apply_declarations(request, request_path=args.request,
                request_sha256=args.request_sha256)
            print(json.dumps(result, sort_keys=True))
            return
        f.require(args.request_sha256 is None, 'ordinary_legacy_request_pin_option_refused')
        request = f.read_json(args.request)
        from scripts.install_containment import Budget
        budget = Budget(request.get('seconds'),started=started)
        result = (rebind_inference(request,args.request,budget) if args.phase=='rebind-inference'
            else recover_first_contact_config(request,args.request,budget))
        print(json.dumps(result,sort_keys=True))
    except Exception as exc:
        from scripts.dsh_prepare import StopUnconfirmed
        if args.phase in ('rebind-inference','rebind-worker-declarations',
                'observe-dsh-current') and isinstance(exc,StopUnconfirmed):
            f.exit_retaining_cause(parser,3,exc,args.phase)
        f.exit_retaining_cause(parser,2,exc,args.phase)


if __name__ == '__main__':
    recovery_main()
