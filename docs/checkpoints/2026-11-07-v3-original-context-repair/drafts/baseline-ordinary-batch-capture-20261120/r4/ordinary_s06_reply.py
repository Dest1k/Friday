"""Check Orchard's saved workbook and physical totals in its direct caption."""

from struct import error as ZipHeaderError
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from zlib import error as DeflateError

from ordinary_current import source_module
from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "5e3d70ffbdf095714b69482012c139933ebd79fa01d749c1d824acb7ae017f56"
SOURCE_SHA256 = "d12842b0c8d333b9eee573adbfc1ace2b2d5211503f8776ef698aab191357bc8"
ORACLE_SHA256 = "6f874a608931ac909eed5687ff330ce609c323c79b73baa2b8bb80f480715735"
ZIP_READER_SHA256 = "fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127"
OUTPUT_NAME = "S06-Orchard-Physical-Totals.xlsx"


def assess_saved_physical_totals(observer, store, *, run_id, run_ref, cursor_ref, oracle_ref, zip_reader_ref):
    def assess_content(upload, raw, recipient):
        caption = recipient["caption"]
        if type(caption) is not str:
            raise ValueError("Exact S06 captured caption required")
        reply = caption.encode("utf-8")
        if not reply.strip():
            return {"status": "FAIL", "reason": "S06_JSON_CAPTION_MISSING"}
        original = observer.read_document_input(upload, lambda: None)
        if len(original) != 2759 or digest(original) != SOURCE_SHA256:
            raise ValueError("Exact S06 Orchard source workbook required")
        if oracle_ref.get("sha256") != ORACLE_SHA256 or zip_reader_ref.get("sha256") != ZIP_READER_SHA256:
            raise ValueError("Exact S06 oracle and bounded ZIP reader required")
        oracle = source_module(oracle_ref, "_s06_physical_totals_oracle")
        reader = source_module(zip_reader_ref, "_s06_bounded_zip_reader")
        oracle.bounded_decoder = lambda: reader.read_zip_member
        try:
            report = oracle.assessment(original, raw, reply)
        except oracle.Refusal as error:
            return {"status": "FAIL", "reason": str(error)}
        except (BadZipFile, ParseError, DeflateError, ZipHeaderError, EOFError, LookupError,
                ValueError, NotImplementedError, ArithmeticError, AttributeError):
            return {"status": "FAIL", "reason": "MALFORMED_S06_WORKBOOK_OR_JSON"}
        if (report["state"] != "S06_SAVED_CONTENT_MATCH" or report["source_sha256"] != SOURCE_SHA256
                or report["output_sha256"] != recipient["download"]["sha256"]
                or report["reply_sha256"] != digest(reply)):
            raise ValueError("S06 oracle assessed different bytes")
        return {"status": "PASS", "content_oracle": report}

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S06",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content,
    )
    return {**evidence, "native_read_create_readback_delivery": "OPEN",
            "calc_recalculation_on_received_bytes": "OPEN", "formal_acceptance": "OPEN"}
