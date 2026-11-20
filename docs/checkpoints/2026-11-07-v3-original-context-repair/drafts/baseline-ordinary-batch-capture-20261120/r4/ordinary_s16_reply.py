"""Assess the saved literal workbook from the exact separate S16 input."""

from struct import error as ZipHeaderError
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from zlib import error as DeflateError

from ordinary_current import source_module
from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "f08405d046b402e776c2c3396e9c71a086634630c00e6c54ea5c5775e30bd93a"
SOURCE_SHA256 = "dbf66f4dd07d5391aace181c9ad9ebf501e269d47cd26462fc9c3e3de29d3ed2"
ORACLE_SHA256 = "a43e7a7d54abf633138cc61d78a57d861a7c94502df47b703a07e16e34843007"
OUTPUT_NAME = "S16-Birch-Literal.xlsx"


def assess_saved_literal_workbook(observer, store, *, run_id, run_ref, cursor_ref, oracle_ref):
    def assess_content(upload, raw, recipient):
        original = observer.read_document_input(upload, lambda: None)
        if len(original) != 577 or digest(original) != SOURCE_SHA256:
            raise ValueError("Exact S16 Birch source bytes required")
        if oracle_ref.get("sha256") != ORACLE_SHA256:
            raise ValueError("Exact S16 literal workbook checker required")
        oracle = source_module(oracle_ref, "_s16_literal_workbook_checker")
        expected_rows = oracle.source_rows(original, SOURCE_SHA256)
        try:
            result = oracle.verify_xlsx(raw, expected_rows)
        except ValueError as error:
            return {"status": "FAIL", "reason": str(error)}
        except (BadZipFile, ParseError, DeflateError, ZipHeaderError, EOFError,
                LookupError, RecursionError, NotImplementedError):
            return {"status": "FAIL", "reason": "MALFORMED_S16_XLSX_PACKAGE"}
        return {"status": "PASS", "source_sha256": SOURCE_SHA256,
                "xlsx_sha256": recipient["download"]["sha256"], **result}

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S16",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content,
    )
    return {**evidence, "native_read_create_readback_delivery": "OPEN",
            "calc_same_received_bytes": "OPEN", "formal_acceptance": "OPEN"}
