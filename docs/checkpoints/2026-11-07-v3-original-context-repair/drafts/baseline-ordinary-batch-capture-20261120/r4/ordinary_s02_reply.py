"""Assess the workbook and its attached provenance from the same closed S02 response."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED, ZIP_STORED

from ordinary_s18_reply import assess_closed_workbook_reply, digest


SCENARIO_SHA256 = "50bdee5de9f3d71459375b1d9456b9554011d34bac44a642bcdedee9c4d4f741"
SOURCE_SHA256 = "aa32ce4dff3bc7606626cff3ea776eed6b5393701f9ecdfde584edae26c9ef5d"
ORACLE_SHA256 = "8be94821fad5dee0fdfc1ea5b7cb162d4cb0b2dfb30afd6c36336bc21b5912bf"
PARSER_SHA256 = "8cce29b67462d1cd060dd3c998b226deba7644aef02a59a0f6b14e29dbc31922"
OUTPUT_NAME = "S02-Larch-Merged.xlsx"
MAX_XLSX_EXPANDED_BYTES = 4_000_000


def load_checked_module(observer, path, expected_sha, name):
    source = observer.safe_read(path, 65536)
    if digest(source) != expected_sha:
        raise ValueError(f"Exact S02 {name} source required")
    module = ModuleType(name)
    module.__file__ = str(path)
    exec(compile(source, module.__file__, "exec", optimize=0), vars(module))
    return module


def workbook_package_status(raw):
    """Apply the native merge reader's resource bounds before decompression."""
    try:
        with ZipFile(BytesIO(raw)) as package:
            members = package.infolist()
    except (BadZipFile, UnicodeError, ValueError):
        return "MALFORMED_XLSX_PACKAGE"
    if (not 1 <= len(members) <= 128
            or sum(member.file_size for member in members) > MAX_XLSX_EXPANDED_BYTES
            or any(member.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                   or member.file_size > max(4096, member.compress_size * 200)
                   for member in members)):
        return "XLSX_OUTSIDE_NATIVE_EXPANDED_BOUND"
    return None


def assess_saved_merge(observer, store, *, run_id, run_ref, cursor_ref, oracle_path, scratch):
    """Verify naturally captured provenance. Separate text cannot substitute a caption."""
    def assess_content(upload, raw, artifact):
        original = observer.read_document_input(upload, lambda: None)
        if digest(original) != SOURCE_SHA256:
            raise ValueError("S02 exact original source ZIP required")
        caption = artifact["caption"].encode("utf-8")
        caption_sha = digest(caption)
        package_error = workbook_package_status(raw)
        if package_error:
            return {"status": "FAIL", "reason": package_error, "caption_sha256": caption_sha}
        oracle = load_checked_module(observer, Path(oracle_path), ORACLE_SHA256, "merge_oracle")
        parser = load_checked_module(observer, oracle.CORE288, PARSER_SHA256, "workbook_parser")
        # Keep the parser tied to the bytes just authenticated by the receiver.
        oracle.load_core288 = lambda: (parser.package, parser.workbook_rows)
        with TemporaryDirectory(prefix="s02-receiver-", dir=observer.secure_dir(Path(scratch))) as directory:
            source = Path(directory) / upload["filename"]
            workbook = Path(directory) / OUTPUT_NAME
            provenance = Path(directory) / "caption.txt"
            source.write_bytes(original)
            workbook.write_bytes(raw)
            provenance.write_bytes(caption)
            try:
                result = oracle.check_result(source, workbook, provenance, archive_sha256=SOURCE_SHA256)
            except oracle.Refused as error:
                return {"status": "FAIL", "reason": str(error), "caption_sha256": caption_sha}
            except oracle.PARSE_FAILURES:
                return {"status": "FAIL", "reason": "MALFORMED_XLSX_PACKAGE", "caption_sha256": caption_sha}
        if (result["state"] != "PASS_S02_SAVED_WORKBOOK_AND_PROVENANCE"
                or result["archive_sha256"] != SOURCE_SHA256
                or result["workbook_sha256"] != artifact["download"]["sha256"]
                or result["provenance_sha256"] != caption_sha):
            raise ValueError("S02 checker assessed different bytes or caption")
        return {"status": "PASS", **result}

    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S02",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=assess_content,
    )
    return {**evidence, "native_extract_read_merge_delivery": "OPEN", "formal_acceptance": "OPEN"}
