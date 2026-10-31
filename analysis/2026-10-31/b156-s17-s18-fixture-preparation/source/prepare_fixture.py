#!/usr/bin/env python3
import argparse
import hashlib
import os
from pathlib import Path
import re
import zipfile

RICH_SHA256 = "bda844ed5c8e57b76668da9225cfcd28677122ba3e00d31d079c6999ab254d5f"
SHEET = "xl/worksheets/sheet1.xml"
VALIDATION = (
    b'<dataValidations count="1"><dataValidation type="whole" operator="between" '
    b'allowBlank="0" showInputMessage="1" showErrorMessage="1" errorStyle="stop" '
    b'sqref="C2:C5"><formula1>1</formula1><formula2>100</formula2>'
    b'</dataValidation></dataValidations>'
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite(source, destination, changes):
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must differ")
    temporary = destination.with_name(destination.name + ".tmp")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(temporary, "w") as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename in changes:
                    data = changes[info.filename](data)
                dst.writestr(info, data)
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(source, destination):
    if digest(source) != RICH_SHA256:
        raise ValueError("Rich fixture hash changed")
    def change(data):
        if b"<dataValidations" in data or data.count(b"<pageMargins") != 1:
            raise ValueError("Unexpected worksheet validation or insertion layout")
        return data.replace(b"<pageMargins", VALIDATION + b"<pageMargins", 1)
    rewrite(source, destination, {SHEET: change})


def set_numeric_cell(data, reference, value):
    pattern = re.compile(rb'<c\b(?=[^>]*\br="' + reference.encode() + rb'")[^>]*>.*?</c>', re.DOTALL)
    matches = list(pattern.finditer(data))
    if len(matches) != 1:
        raise ValueError("Expected exactly one cell " + reference)
    cell = matches[0].group()
    if b"<f" in cell or len(re.findall(rb"<v>.*?</v>", cell, re.DOTALL)) != 1:
        raise ValueError("Expected one nonformula numeric value")
    replacement = re.sub(rb"<v>.*?</v>", b"<v>" + str(value).encode() + b"</v>", cell, count=1, flags=re.DOTALL)
    return data[:matches[0].start()] + replacement + data[matches[0].end():]


def negatives(correction, rich, destination):
    destination.mkdir(parents=True, exist_ok=True)
    rewrite(correction, destination / "wrong_correction.xlsx", {SHEET: lambda data: set_numeric_cell(data, "C3", 5)})
    def broken_name(data):
        old = b"'Orders'!$A$2:$G$5"
        if data.count(old) != 1:
            raise ValueError("OrderSourceRows target not found")
        return data.replace(old, b"'Missing'!$A$2:$G$5", 1)
    rewrite(rich, destination / "broken_named_range.xlsx", {"xl/workbook.xml": broken_name})
    def broken_chart(data):
        old = b"'Orders'!$A$2:$A$5"
        if data.count(old) != 1:
            raise ValueError("Chart category target not found")
        return data.replace(old, b"'Missing'!$A$2:$A$5", 1)
    rewrite(rich, destination / "broken_chart.xlsx", {"xl/charts/chart1.xml": broken_chart})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rich", type=Path, required=True)
    parser.add_argument("--correction", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--negative-dir", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.rich, args.fixture)
    negatives(args.correction, args.rich, args.negative_dir)


if __name__ == "__main__":
    main()
