"""Finite, local installed-code check; never replays the original Telegram operation."""
import argparse
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import resource
import stat
import sys

ROOT = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
SOURCE = Path('/home/jericho/.cache/FRW-ASTRA-JSON-V03-EDIT228-ROOT-20261117/local-candidate/genuine-source.json')
SOURCE_SHA = '7cdb35df96b479fd31732bb08a6d05cc0fa79b65c6289a1e077fc62f82356133'
MODULE = ROOT / 'hermes_cli/friday_workspace_json.py'
MODULE_SHA = 'cef3cb72db98bd333244a70a347ea99cf5426e4e00e682af014551b5dc125600'


def require(ok, label):
    if not ok:
        raise ValueError(label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-home', required=True, type=Path)
    parser.add_argument('--result', required=True, type=Path)
    args = parser.parse_args()
    home = args.isolated_home
    require(home.is_absolute() and str(home).startswith('/home/jericho/.cache/FRW-ASTRA-CORE229-'), 'isolated_private_cache_required')
    require(not home.exists() and not args.result.exists(), 'new_home_and_result_required')
    for path in (SOURCE, MODULE):
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1, 'owned_regular_single_link_input_required')
        require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink_input_refused')
    original = SOURCE.read_bytes()
    require(len(original) == 831 and hashlib.sha256(original).hexdigest() == SOURCE_SHA, 'genuine_source_identity_required')
    require(hashlib.sha256(MODULE.read_bytes()).hexdigest() == MODULE_SHA, 'installed229_json_module_required')
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (2147483648, 2147483648))
    home.mkdir(mode=0o700)
    os.environ['HERMES_HOME'] = str(home)
    sys.path.insert(0, str(ROOT))
    module = importlib.import_module('hermes_cli.friday_workspace_json')
    require(Path(module.__file__) == MODULE and hashlib.sha256(MODULE.read_bytes()).hexdigest() == MODULE_SHA, 'actual_installed_module_identity_required')
    result = module.replace_string(original, SOURCE_SHA, '/date_display', '05.04.2026', '06.04.2026')
    require(original.count(b'05.04.2026') == 1, 'single_expected_source_token_required')
    require(result == original.replace(b'05.04.2026', b'06.04.2026', 1), 'all_unselected_bytes_must_be_retained')
    before, after = json.loads(original), json.loads(result)
    require(before['date_display'] == '05.04.2026' and after['date_display'] == '06.04.2026', 'requested_string_change_required')
    after['date_display'] = before['date_display']
    require(after == before, 'unselected_semantics_and_types_required')
    refusals = []
    for label, sha, expected, reason in (
        ('stale_hash', '0' * 64, '05.04.2026', 'source_hash_mismatch'),
        ('wrong_expected', SOURCE_SHA, '07.04.2026', 'expected_mismatch'),
    ):
        try:
            module.replace_string(original, sha, '/date_display', expected, '06.04.2026')
        except module.JsonEditRefused as error:
            require(str(error) == reason, 'exact_negative_control_required')
            refusals.append(label)
        else:
            raise ValueError('negative_control_did_not_refuse')
    require(SOURCE.read_bytes() == original, 'genuine_saved_source_must_remain_unchanged')
    report = {
        'schema': 'frw.Core229.installed-pure-json-same-saved-source-assessment.v1',
        'at_moscow': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
        'state': 'PASS_INSTALLED_PURE_STRING_REPLACEMENT_ONLY',
        'installed_module': {'path': str(MODULE), 'sha256': MODULE_SHA},
        'source': {'bytes': len(original), 'sha256': SOURCE_SHA},
        'in_memory_result': {'bytes': len(result), 'sha256': hashlib.sha256(result).hexdigest()},
        'requested_change_and_all_unselected_bytes_and_semantics': True,
        'negative_controls': refusals,
        'original_2837_window_and_local883_semantic_FAIL_preserved': True,
        'new_model_producer_send_Office_or_user_operation': False,
        'workspace_custody_publisher_delivery_or_formal_acceptance_credit': False,
        'scope': 'Pure installed replace_string on the same saved genuine831 bytes. No capability, source workspace write, output artifact, Store/API/model or original-operation replay. Installation closure, current admission and end-to-end acceptance are separate Root checks.',
    }
    with args.result.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    args.result.chmod(0o600)
    print(json.dumps({'state': report['state'], 'result': str(args.result)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
