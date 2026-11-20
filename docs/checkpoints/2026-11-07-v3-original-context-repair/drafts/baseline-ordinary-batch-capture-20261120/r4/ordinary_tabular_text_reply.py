"""Grade closed S10 amount summaries and S17 workbook comparisons."""

from decimal import DecimalException
from pathlib import Path

from ordinary_s11_reply import assess_closed_text_reply, digest


PHASES = {
    "S-10": (
        "d7ab134b468362d1e5564f642e61d1899c05b5f9bf8c573963491257b5f806d2",
        "4d6bb93ccf89ebc1edacfd32c79180c2d6d5f5f439f177d66061485ffcaf02df",
        "8954de20ab0be0487e0e720d020cf6b05cbacbba6d9cdef7f4621258506734cb",
    ),
    "S-17": (
        "3c2c9b0675d04c0905a9e0d3bb4cee1ac15b27fff28552d889837f491e129821",
        "c26567f2b86cf56456f55cc38bbd0fb637bc70bdd285de078c6e65ca14615b18",
        "3bb9b906c842016b9e1e208bc9cd3ba7641e58caf3e78ef667723e21a6df9358",
    ),
}


def assess_saved_tabular_text(observer, store, *, case, run_id, run_ref, cursor_ref, oracle_path):
    """Use one exact source and one authenticated direct reply through the existing R4 Store."""
    if case not in PHASES:
        raise ValueError("Exact S-10 or S-17 case required")
    scenario_sha, source_sha, oracle_sha = PHASES[case]

    def assess_content(upload, texts, attachment_count):
        if len(texts) != 1 or attachment_count:
            return {"status": "FAIL", "reason": "EXPECTED_ONE_DIRECT_TEXT_REPLY"}
        original = observer.read_document_input(upload, lambda: None)
        if digest(original) != source_sha:
            raise ValueError(f"{case} original source bytes changed")
        path = Path(oracle_path)
        source = observer.safe_read(path, 65536)
        if digest(source) != oracle_sha:
            raise ValueError(f"Exact {case} semantic checker required")
        oracle = {"__name__": "_tabular_text_oracle", "__file__": str(path)}
        exec(compile(source, str(path), "exec", optimize=0), oracle)
        body, = texts
        if case == "S-17":
            expected = oracle["verify_archive"](original, source_sha)["facts"]
        try:
            if case == "S-10":
                result = oracle["check_response"](original, source_sha, body)
            else:
                oracle["grade_reply"](body, expected)
        except (ValueError, DecimalException, RecursionError) as error:
            return {"status": "FAIL_CHECKER", "reason": str(error)}
        if case == "S-10" and (result["state"] != "PASS_OFFLINE_RESPONSE_SEMANTICS"
                                or result["source_sha256"] != source_sha
                                or result["response_sha256"] != digest(body)):
            raise ValueError("S-10 checker assessed different source or response bytes")
        return {"status": "PASS", "source_sha256": source_sha, "response_sha256": digest(body)}

    evidence = assess_closed_text_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label=case,
        scenario_sha=scenario_sha, source_sha=source_sha, assess_content=assess_content,
        require_ack_size=True,
    )
    return {**evidence, "case": case, "native_source_read": "OPEN", "formal_acceptance": "OPEN"}
