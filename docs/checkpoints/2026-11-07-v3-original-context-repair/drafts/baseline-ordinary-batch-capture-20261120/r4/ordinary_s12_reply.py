"""Check the saved structure of the exact ordinary S12 print-ready workbook."""

from pathlib import Path
from types import ModuleType

from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "c4cc8ba44f89e50e5d303a738daf66e5a89728921219fcd01a3e36f66ab3284f"
SOURCE_SHA256 = "2f1b9ce0740d3d7dccd82fcc2e5d7f205ec93d63158527b550206f0c002e1e4a"
ORACLE_SHA256 = "8b2e4e6795776a593fa71d841e330eae6d3a2e9b422c08677b46aaba0746d447"
OUTPUT_NAME = "S12-Willow-Printable.xlsx"


def assess_saved_printable_workbook(observer, store, *, run_id, run_ref, cursor_ref, oracle_path):
    def assess_content(upload, raw, artifact):
        original = observer.read_document_input(upload, lambda: None)
        if len(original) != 379 or digest(original) != SOURCE_SHA256:
            raise ValueError("S12 original JSON bytes changed")
        path = Path(oracle_path)
        source = observer.safe_read(path, 65536)
        if digest(source) != ORACLE_SHA256:
            raise ValueError("Exact S12 printable workbook checker required")
        oracle = ModuleType("_pinned_s12_workbook_checker")
        oracle.__file__ = str(path)
        exec(compile(source, oracle.__file__, "exec"), vars(oracle))
        recipient = artifact["download"]
        result = oracle.check_workbook(raw, expected_sha256=recipient["sha256"])
        if (result["sha256"] != recipient["sha256"] or result["bytes"] != recipient["bytes"]
                or result["status"] not in ("PASS", "FAIL")):
            raise ValueError("S12 checker assessed different bytes")
        return result

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S12",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content,
    )
    return {**evidence, "native_read_create_delivery": "OPEN", "calc_same_received_bytes": "OPEN",
            "formal_acceptance": "OPEN"}
