"""Grade the exact grouped S05 workbook and caption from a closed R4 capture."""

from decimal import DecimalException
from struct import error as ZipHeaderError
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from ordinary_current import source_module
from ordinary_d03_reply import pinned_bytes
from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "35262768ba35539e96342da042c7d8d3141d9704adadf862eaf7dbf2c7d64758"
SOURCE_SHA256 = "7cf54f00905d2df7a879156158a222a28e95edcca862337bc4c1fcfef91da763"
ORACLE_SHA256 = "e1fed8fc3ff57f0b2b9d2d214499974eedfd83109a6c5a8dfc43d54773f5ed23"
ZIP_READER_SHA256 = "fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127"
OUTPUT_NAME = "S05-East-Grouped-Typed.xlsx"


def assess_saved_grouped_workbook(observer, store, *, run_id, run_ref, cursor_ref, oracle_ref, zip_reader_ref):
    def assess_content(upload, raw, recipient):
        original = observer.read_document_input(upload, lambda: None)
        if len(original) != 255 or digest(original) != SOURCE_SHA256:
            raise ValueError("Exact S05 grouped CSV source required")
        if oracle_ref.get("sha256") != ORACLE_SHA256 or zip_reader_ref.get("sha256") != ZIP_READER_SHA256:
            raise ValueError("Exact S05 grouped oracle and bounded ZIP reader required")
        grouped = source_module(oracle_ref, "_s05_grouped_oracle")
        reader = source_module(zip_reader_ref, "_s05_bounded_zip_reader")
        # The grouped loader verifies the nested strengthened checker and sets the grouped values.
        oracle = grouped.load_oracle()

        class BoundedZipFile(ZipFile):
            def read(self, name):
                return reader.read_zip_member(self, raw, self.getinfo(name), oracle.MAX_XML_BYTES)

        oracle.ZipFile = BoundedZipFile
        receipt_ref = recipient["receipt"]
        receipt = pinned_bytes(observer, receipt_ref)
        try:
            report = grouped.check(oracle, original, raw, receipt, receipt_ref["sha256"])
        except ValueError as error:
            return {"status": "FAIL", "reason": str(error)}
        except (BadZipFile, ParseError, ZipHeaderError, EOFError, LookupError, DecimalException, RuntimeError):
            return {"status": "FAIL", "reason": "MALFORMED_S05_XLSX_PACKAGE"}

        saved = report["saved_reply"]
        if (report["status"] != "S05_GROUPED_SAVED_ARTIFACT_AND_CAPTION_PASS"
                or report["source"] != {"bytes": len(original), "sha256": SOURCE_SHA256}
                or report["xlsx"] != {key: recipient["download"][key] for key in ("bytes", "sha256")}
                or saved["receipt"] != {key: receipt_ref[key] for key in ("bytes", "sha256")}
                or saved["filename"] != OUTPUT_NAME or saved["message_id"] != recipient["message_id"]
                or saved["update_id"] != recipient["update_id"]
                or saved["caption"]["sha256"] != digest(recipient["caption"].encode("utf-8"))):
            raise ValueError("S05 oracle assessed different bytes or reply")
        return {"status": "PASS", "content_oracle": report}

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S05",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content,
    )
    return {**evidence, "native_read_convert_readback_delivery": "OPEN",
            "f04_csv_to_xlsx": "OPEN", "formal_acceptance": "OPEN"}
