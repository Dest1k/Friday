"""Check literal identifiers in the single saved S04 workbook."""

from pathlib import Path
from types import ModuleType, SimpleNamespace
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile
from zlib import error as DeflateError

from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "f1bf10b96ad7f861ae83c250076c8b8eeaea7f47ebf10f6999350eb97a9e77e4"
SOURCE_SHA256 = "cc7c1e304f7225df0987946dd1eb89382d814d25434c14d1e966098ec0fac296"
ORACLE_SHA256 = "9a6230ffc45b32a6865d9b0f0abfa238acd7824648e4405a00f1ff789b28e17f"
ZIP_READER_SHA256 = "fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127"
OUTPUT_NAME = "S04-Linden-Combined.xlsx"


def load_pinned_module(observer, path, expected_sha, name):
    path = Path(path)
    source = observer.safe_read(path, 65536)
    if digest(source) != expected_sha:
        raise ValueError(f"Exact S04 {name} required")
    module = ModuleType("_s04_" + name.replace(" ", "_"))
    module.__file__ = str(path)
    exec(compile(source, module.__file__, "exec", optimize=0), vars(module))
    return module


def assess_saved_identifiers(observer, store, *, run_id, run_ref, cursor_ref, oracle_path, zip_reader_path):
    def assess_content(upload, raw, artifact):
        original = observer.read_document_input(upload, lambda: None)
        if len(original) != 3668 or digest(original) != SOURCE_SHA256:
            raise ValueError("S04 exact original source ZIP required")
        oracle = load_pinned_module(observer, oracle_path, ORACLE_SHA256, "literal workbook checker")
        reader = load_pinned_module(observer, zip_reader_path, ZIP_READER_SHA256, "bounded ZIP reader")

        class BoundedZipFile(ZipFile):
            def __init__(self, stream):
                self.data = stream.getvalue()
                super().__init__(stream)

            def read(self, info):
                return reader.read_zip_member(self, self.data, info, oracle.LIMIT)

        # Keep the oracle's package checks and use the native bounded member decoder.
        oracle.zipfile = SimpleNamespace(ZipFile=BoundedZipFile, ZIP_STORED=ZIP_STORED,
                                        ZIP_DEFLATED=ZIP_DEFLATED, BadZipFile=BadZipFile)
        oracle.INPUT = Path(upload["path"])
        expected, checked_source = oracle.source_oracle(SOURCE_SHA256)
        if checked_source["sha256"] != SOURCE_SHA256 or checked_source["bytes"] != len(original):
            raise ValueError("S04 checker read different source bytes")
        try:
            content = oracle.check_saved(raw, expected)
        except oracle.Rejected as error:
            return {"status": "FAIL", "reason": str(error)}
        except (BadZipFile, ParseError, DeflateError, EOFError, LookupError, ValueError, NotImplementedError):
            return {"status": "FAIL", "reason": "MALFORMED_XLSX_PACKAGE"}
        return {"status": "PASS", "source_sha256": SOURCE_SHA256,
                "source_members": checked_source["members_in_order"],
                "workbook_sha256": artifact["download"]["sha256"], **content}

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S04",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content,
    )
    return {**evidence, "native_extract_read_create_delivery": "OPEN",
            "calc_same_received_bytes": "OPEN", "formal_acceptance": "OPEN"}
