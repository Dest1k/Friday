"""Check an exact reviewed document preparation under the existing Once locks."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from types import ModuleType


HERE = Path(__file__).resolve().parent
DRIVER_SHA256 = "126fa16c8b22e814d19b876933310e63657abfeaaa20d45d06075ae959a0ce6e"
BINDING_SCHEMA = "frw.Root.ordinary-preclock.v1"
REVIEWED_PHASES = {
    "5e3d70ffbdf095714b69482012c139933ebd79fa01d749c1d824acb7ae017f56": (
        "S-06", "c39445d8bac51a91bcd13023e11775554c1ebdc0cf8179c04018d3c507c989c1",
    ),
    "52131f5bfe86bfb0d7492750b7849165a644dc91467c0460775f82ddf0b4dec6": (
        "S-03", "95e784183b76940520425387660dcc839629ff7e2fd49214549932ec274fd05e",
    ),
    "9b6f6df645c3d07d0b695022349db4b7c81ea2d004c83a64847c63f7d408d78e": (
        "D-04", "1ac3a16f3d6ae8b28eb16f8045fe364794277ac787fbc6089f5d3fb54532592d",
    ),
    "2a5c503fbe0505cf617f15ddb3c935104b96994173234ab16ea5d948c414c449": (
        "D-05", "7f52f6fd77aae6744e9eead13f201827e49d5a808bac5cbad19004ea99c0af55",
    ),
    "037d89d7d315c017172d653ca59670c05b97130f4f8782154e67b854b40d7cb0": (
        "D-06", "e7360483db530bfb47da5e871dc4774341dd06831c2071755818a29bd462174d",
    ),
    "c8b18c77a422fba386b1f52dd68c7e66ab8761e02bf45135666a1e30e125c0e9": (
        "D-09", "19d9fd461d3648493a6129d875d9df93f222934d2b5d86c25da4b808818a5ad2",
    ),
    "b99effc9a4cab5b11ce17b23260564a42f5f269f1fba3d94c3a505e0a5266414": (
        "D-11", "0e6c22c0484ec102d5a521c46bc931b7f16a6cf7125aaf7825ea347b4607ec3f",
    ),
    "5394ac076c92ba1c3cbb7c69361e7f4b2bb9944e312fc030d24b75f3f04933a3": (
        "D-14", "d34ff94e963eeb8280d92f937135c37902739a108947497301ee600abc777d8f",
    ),
    "f1bf10b96ad7f861ae83c250076c8b8eeaea7f47ebf10f6999350eb97a9e77e4": (
        "S-04", "f4d1ac2b216f0d3af35315bac4ee79c16390b9cedd411712c1517f95d3319cc9",
    ),
    "0909a9722fad7e64f4d51099c1e504f0daf19166db30ad700d772bb91b7789ad": (
        "S-11", "8e0e63a60b31594563c124d5fe648d0ba4cec319641d2bd377de44ec0b9ba04b",
    ),
    "c4cc8ba44f89e50e5d303a738daf66e5a89728921219fcd01a3e36f66ab3284f": (
        "S-12", "f87115eb1393e6beee89049ca658839a368306276aaa6b36b8cc0e8c45db5a1d",
    ),
    "3c2c9b0675d04c0905a9e0d3bb4cee1ac15b27fff28552d889837f491e129821": (
        "S-17", "4e161602eae4186253c1801cde063f7d09d9d5db4100100f5559bf948689ff95",
    ),
    "b6bee941754be8f60f3d8b57ce3ad85e5044c760ffe397a418f4077f3ff19b9c": (
        "S-18", "19256d6ddac510824e9007d4d0f3b957c824de4b48d5c1a74152ec9897d7de0a",
    ),
}
PRESERVED_RUNS = {
    "S-06": (
        ("root-b00-s151-s06-20261102-r1",
         "96878a30e519d8c4fa7a134a6b93d8dc209ae231e1db1c8d845b88538d9888ee", "EVIDENCE_READY"),
        ("root-s07-374568107753",
         "c63df6a5928b80efb316d89c1c2c9203b589d0bde69e0b181a4140f1e6190e17", "EVIDENCE_READY"),
        ("root-s07-672df6ad93b3",
         "84fc944eb7eff1739ba7b4d58b68d90a044d3e5fb47b0c343359d72f0f5e7525", "OBSERVING"),
        ("root-s07-d8539484e55a",
         "1700a5dc2362cd6274aaac608a1894ce90d37270b7fd20594e82f6dc6ef92e35", "EVIDENCE_READY"),
        ("root-s07-f346161f8750",
         "5e0ed049d709041c715ff6937c7ed3ee2daa586759bc9a94a298eeabcd98a2da", "OBSERVING"),
    ),
    "S-03": (
        ("root-b00-s151-s03-20261102-r1",
         "32413240298b3bacfaea02184ea1ddd1b595dd9f669f18159f53ab0fc7b405e7", "EVIDENCE_READY"),
        ("root-s07-1496ae0d08cd",
         "32b4aabd61747130d6060b1515a59cdbd00053f44fe4be0d6796ebb6a29edee2", "OBSERVING"),
    ),
    "D-04": (
        ("root-b00-d04-summary-1-physical-01-r17",
         "edbc77bb9e78240477c5ba84824544c446036f2cf67d191f492cd9eb828313ed", "EVIDENCE_READY"),
    ),
    "D-05": (
        ("root-b00-d05-deadline-1-physical-01-r16",
         "6bd41bc954634d52ea4ea2b7e0aa59f62a2b0c352c2e1862f10a355ef5e1af22", "STOPPED"),
    ),
    "D-06": (
        ("root-b00-d06-rename-1-physical-01-r16",
         "6abb9f64a4b1dc6f96b17b8618dda23c80565de90a04e99ae4e1a9d918ac23ed", "EVIDENCE_READY"),
    ),
    "D-09": (
        ("root-b00-d09-translate-1-physical-01-r16",
         "bf772b96ef6bb664b516122f90a27edbd1da50ce25fe5fc5bcfaf0821b3fb7d5", "STOPPED"),
        ("d09-translation-check-01-r55",
         "275bfdffc52fea6771abd059d6c2ceb32db05b302a36d2fa736b05e2a736dc15", "EVIDENCE_READY"),
    ),
    "D-11": (
        ("root-b00-d11-styled-report-1-physical-01-r17",
         "00d47966a411e12af48a541c741f3fe374788d275ddc30fa1d0264c85832dfde", "EVIDENCE_READY"),
    ),
    "D-14": (
        ("root-b00-d15-set1-1-physical-01-r13",
         "42117401ce0e8a429c51afa3f3f9c31ec4f88e622a939c000c83158b9a88c654", "EVIDENCE_READY"),
        ("root-b00-d15-set2-1-physical-01-r13",
         "0727c7770c2b0b9113c998c38da3c44c377156195a84a0aa35675e1620a87cde", "EVIDENCE_READY"),
    ),
    "S-04": (
        ("root-b00-s151-s04-20261102-r1",
         "8fa1f8d0d9a362041672250003a3023f0920c1f19869a1b6ca5dcc14f2e6a04e", "EVIDENCE_READY"),
        ("root-s04-confusable-37c0b13b977f",
         "5259cd8d73f99c333d99bbe763f42dde2e618b1aa66143889953bde007766f84", "EVIDENCE_READY"),
    ),
    "S-11": (
        ("root-b00-s151-s11-20261102-r1",
         "2eca828078ab3021ce90a7b83e34fdcfcdd6c0906bf0a3e34c4df0ba7ef41677", "EVIDENCE_READY"),
    ),
    "S-12": (
        ("root-b00-s151-s12-20261102-r1",
         "ba2511c43f0893c71818b419519b653bce1a1808bc9bb5301a1828486b8c728e", "STOPPED"),
    ),
    "S-17": (
        ("root-b00-s151-s17-20261102-r1",
         "e933028dbad4c8d3230219d9bdbfa5a1d2726bd7fee25da3bdc72cfbc0ff7770", "EVIDENCE_READY"),
        ("root-s17-dd7c006ecd5b",
         "6ee0fc025ac19a8ac59f5c2b730ca264eac2dafe86956ff9cd32b84ccbf70f00", "OBSERVING"),
        ("root-s17-followup-101c59a334b3",
         "a9095e638480d8092e21d319e6b43d227239f83088cf53527672f1ad8fcf66ab", "OBSERVING"),
    ),
    "S-18": (
        ("root-b00-s151-s18-20261102-r1",
         "38852e377c59bc39add0ebf481d7c70de346589830c565e3000fe4f4a7f8738b", "EVIDENCE_READY"),
        ("root-s18-2d453525c2dd",
         "0c0354b14bdcfe6a1a73ac833aee771243904d725b2c357931066d26e9dbe387", "OBSERVING"),
    ),
}


def existing_driver():
    path = HERE / "ordinary_s01_root.py"
    with path.open("rb") as source:
        data = source.read(65537)
    if sha256(data).hexdigest() != DRIVER_SHA256:
        raise ValueError("PRECLOCK_EXISTING_DRIVER_CHANGED")
    driver = ModuleType("_reviewed_ordinary_preclock_driver")
    driver.__file__ = str(path)
    exec(compile(data, driver.__file__, "exec"), vars(driver))
    return driver


def check_history(actor, current, case, contract, authority):
    history = current.document(contract["scope"]["history"])
    inventory = {
        name: {key: row[key] for key in ("sha256", "status", "send_state", "deadline")}
        for name, row in authority["history"].items()
    }
    actor.need(history["history_inventory_sha256"] == current.digest(current.encoded(inventory))
               and history["cursor_sha256"] == contract["cursor"]["sha256"]
               and history["history_count"] == len(inventory),
               "PRECLOCK_COLLISION_REPORT_DOES_NOT_MATCH_CURRENT_HISTORY_AND_CURSOR")
    for prior_id, prior_sha, prior_status in PRESERVED_RUNS[case]:
        old = inventory.get(prior_id, {})
        actor.need((old.get("sha256"), old.get("status"), old.get("send_state")) == (prior_sha, prior_status, "sent"),
                   "PRECLOCK_PRESERVED_HISTORICAL_RUN_CHANGED")


def check_binding(driver, actor, reference):
    value = actor.doc(reference)
    actor.need(value.get("schema") == BINDING_SCHEMA and value.get("status") == "ROOT_READONLY_QUALIFICATION"
               and value.get("operator") == "Root",
               "PRECLOCK_EXPLICIT_QUALIFICATION_REQUIRED")
    work = actor.canonical_path(value["workdir"])
    package = Path(reference["path"]).parent
    actor.protected_directory(package)
    actor.need(work.parent == package and not work.is_relative_to(driver.HOME) and not work.is_relative_to(actor.STATE),
               "PRECLOCK_DISJOINT_PRIVATE_WORK_DIRECTORY_REQUIRED")
    identity = driver.protected_work_identity(actor, work)
    actor.need(identity == value["work_identity"], "PRECLOCK_WORK_DIRECTORY_CHANGED")
    slot_identity = value["slot_identity"]
    actor.need(type(slot_identity) is dict and set(slot_identity) == {"device", "inode", "uid", "mode", "nlink"},
               "PRECLOCK_EXACT_SLOT_IDENTITY_REQUIRED")

    current = driver.installed_module(actor, "ordinary_current", driver.CURRENT_SHA)
    composer = driver.installed_module(actor, "ordinary_admission_source", driver.COMPOSER_SHA)
    once_module = driver.installed_module(actor, "ordinary_once", driver.ONCE_SHA)
    actor.need(value["checker"]["sha256"] == driver.CURRENT_SHA and value["source"]["sha256"] == driver.R4_SHA,
               "PRECLOCK_EXACT_BASE_AND_CHECKER_REQUIRED")
    phase = actor.doc(value["phase"])
    scenario = phase["scenario"]
    normalized = current.digest(current.encoded(scenario))
    run_id = value["run_id"]
    actor.need(type(run_id) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id)
               and phase["scenario_sha256"] == normalized and normalized in REVIEWED_PHASES,
               "PRECLOCK_EXACT_REVIEWED_PHASE_REQUIRED")
    case, observer_sha = REVIEWED_PHASES[normalized]
    contract, authority, prepare = (
        current.document(value[name]) for name in ("contract", "authority", "prepare")
    )
    actor.need(authority.get("qualification_only") is True and contract.get("qualification_only") is True
               and authority["run_scenarios"] == {run_id: normalized}
               and not authority.get("ordered_predecessors")
               and contract.get("authority") == value["authority"]
               and prepare["current_observer"]["sha256"] == observer_sha,
               "PRECLOCK_EXACT_QUALIFICATION_AUTHORITY_AND_OBSERVER_REQUIRED")
    check_history(actor, current, case, contract, authority)
    profile = f"telegram-bot-{scenario['tester_id']}"
    directories, paths = driver.disk_paths(work, actor.STATE, profile)
    disk, resources = value["disk_scope"], value["resources"]
    actor.need(disk["directory_roots"] == directories and disk["file_paths"] == paths
               and type(disk["max_entries"]) is int and 0 < disk["max_entries"] <= 100000
               and type(disk["sample_seconds"]) in (int, float) and 0 < disk["sample_seconds"] <= 1
               and set(resources) == set(driver.RESOURCE_LIMITS)
               and all(type(resources[key]) is int and 0 < resources[key] <= cap
                       for key, cap in driver.RESOURCE_LIMITS.items()),
               "PRECLOCK_BOUND_DISK_SCOPE_REQUIRED")
    class ReadonlyOnce(once_module.Once):
        def observer(self, directory, role, slot_owner, clock=None, invocation=None):
            actor.need(role == "preclock" and clock is None and invocation is None
                       and directory.parent == work and driver.protected_work_identity(actor, work) == identity,
                       "PRECLOCK_WORK_DIRECTORY_CHANGED")
            actor.protected_directory(directory)
            return super().observer(directory, role, slot_owner)

    once = ReadonlyOnce(actor, current, composer, reference)
    result = driver.preclock(once)
    actor.need(driver.protected_work_identity(actor, work) == identity and not list(work.iterdir()),
               "PRECLOCK_WORK_DIRECTORY_CHANGED")
    return {**result, "state": "ORDINARY_R4_READONLY_QUALIFIED", "case": case,
            "run_id": run_id, "scenario_sha256": normalized}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binding")
    parser.add_argument("sha256")
    args = parser.parse_args(argv)
    driver = existing_driver()
    if (Path(sys.executable) != driver.PYTHON or not sys.flags.isolated or not sys.flags.no_site
            or not sys.dont_write_bytecode or sys.flags.optimize):
        raise ValueError("PRECLOCK_EXACT_INTERPRETER_REQUIRED")
    os.umask(0o077)
    actor = driver.load_actor()
    _, reference = actor.exact_file(args.binding, args.sha256)
    report = check_binding(driver, actor, reference)
    sys.stdout.buffer.write(actor.encoded(report))


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        # Exceptions originating in private current observers may include input data.
        detail = str(error) if type(error) is ValueError and re.fullmatch(r"PRECLOCK_[A-Z_]+", str(error)) else type(error).__name__
        print(json.dumps({"state": "PRECLOCK_REFUSED", "code": detail, "execution_authorized": False}), file=sys.stderr)
        sys.exit(2)
