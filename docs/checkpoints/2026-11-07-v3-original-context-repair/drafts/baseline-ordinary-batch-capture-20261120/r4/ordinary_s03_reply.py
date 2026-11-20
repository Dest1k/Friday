"""Check the closed North workbook and its one correlated JSON reply."""

from struct import error as ZipHeaderError
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile, ZipInfo
from zlib import error as DeflateError

from ordinary_current import source_module
from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "52131f5bfe86bfb0d7492750b7849165a644dc91467c0460775f82ddf0b4dec6"
SOURCE_SHA256 = "d8084574aeb52aaa5c00e70dbf6cbd03c56b776605b92a7e91028ae00f50f190"
ORACLE_SHA256 = "83aad8d9ec622f2644895130658aa2dd1565de8a8d7183e6e4dcb0f95123ca0d"
ZIP_READER_SHA256 = "fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127"
OUTPUT_NAME = "S03-North-Joined.xlsx"


def assess_saved_joined_orders(observer, store, *, run_id, run_ref, cursor_ref, oracle_ref, zip_reader_ref):
    def assess_content(upload, raw, recipient, texts):
        caption = recipient["caption"]
        if type(caption) is not str:
            raise ValueError("Exact S03 captured caption required")
        reply = texts[0] if texts else caption.encode("utf-8")
        if not reply.strip():
            return {"status": "FAIL", "reason": "S03_JSON_MISSING"}
        if texts and caption.lstrip().startswith(("{", "[", "```")):
            return {"status": "FAIL", "reason": "S03_MULTIPLE_JSON_CARRIERS"}
        original = observer.read_document_input(upload, lambda: None)
        if len(original) != 630 or digest(original) != SOURCE_SHA256:
            raise ValueError("Exact S03 original source ZIP required")
        if (oracle_ref.get("sha256") != ORACLE_SHA256 or oracle_ref.get("bytes") != 13181
                or zip_reader_ref.get("sha256") != ZIP_READER_SHA256):
            raise ValueError("Exact S03 oracle and bounded ZIP reader required")
        oracle = source_module(oracle_ref, "_s03_saved_north_oracle")
        reader = source_module(zip_reader_ref, "_s03_bounded_zip_reader")

        class BoundedZipFile(ZipFile):
            def __init__(self, stream):
                self.data = stream.getvalue()
                super().__init__(stream)

            def read(self, name):
                member = name if isinstance(name, ZipInfo) else self.getinfo(name)
                if member.flag_bits & 1:
                    raise oracle.Mismatch("WORKBOOK_ENCRYPTED")
                return reader.read_zip_member(self, self.data, member, oracle.XLSX_LIMIT)

        oracle.ZipFile = BoundedZipFile
        try:
            report = oracle.assess(original, raw, reply)
        except oracle.Mismatch as error:
            return {"status": "FAIL", "reason": str(error)}
        except (BadZipFile, ParseError, DeflateError, ZipHeaderError, EOFError, LookupError,
                ValueError, NotImplementedError, ArithmeticError):
            return {"status": "FAIL", "reason": "MALFORMED_S03_WORKBOOK_OR_JSON"}
        if (report["state"] != "SAVED_CONTENT_MATCH" or report["archive_sha256"] != SOURCE_SHA256
                or report["workbook_sha256"] != recipient["download"]["sha256"]
                or report["reply_sha256"] != digest(reply)):
            raise ValueError("S03 oracle assessed different bytes")
        screen = {"status": "PASS", "json_carrier": "separate_text" if texts else "caption", **report}
        if texts and caption.strip():
            screen.update(status="REVIEW_REQUIRED", reason="S03_ADDITIONAL_CAPTION")
        return screen

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S03",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content, allow_separate_text=True,
    )
    return {**evidence, "native_extract_read_create_delivery": "OPEN", "formal_acceptance": "OPEN"}
