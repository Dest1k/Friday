#!/usr/bin/env python3
"""Portable synthetic-fixture checker excerpt; static semantics only.

No Office/formula engine, tester admission, runtime or user acceptance is implied.
"""
from decimal import Decimal
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile

EXPECTED_S17 = {
    "changed_inputs": {"Orders!C3": ["3", "4"], "Orders!F3": ["1", "2"]},
    "added_rows": 0,
    "deleted_rows": 0,
    "base_total_rub": "10101.20",
    "correction_total_rub": "10601.10",
    "delta_rub": "499.90",
    "g3": ["1499.70", "1999.60"],
}


EXPECTED_FORMULAS = {
    "Orders!G2": "C2*D2",
    "Orders!G3": "C3*D3",
    "Orders!G4": "C4*D4",
    "Orders!G5": "C5*D5",
    "Summary!B2": "SUM(Orders!G2:G5)",
}


EXPECTED_NAMES = {
    "OrderSourceRows": "'Orders'!$A$2:$G$5",
    "_xlnm._FilterDatabase": "'Orders'!$A$1:$G$5",
    "OrderTotal": "'Summary'!$B$6",
}


EXPECTED_CHART_REFS = ["'Orders'!G1", "'Orders'!$A$2:$A$5", "'Orders'!$G$2:$G$5"]


def local(tag):
    return tag.rsplit("}", 1)[-1]


def money(value):
    return f"{value:.2f}"


class Workbook:
    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as archive:
            self.bad_crc = archive.testzip()
            self.members = {info.filename: archive.read(info.filename) for info in archive.infolist()}
        self.xml = {}
        for name, data in self.members.items():
            if name.endswith(".xml") or name.endswith(".rels"):
                self.xml[name] = ET.fromstring(data)
        self.shared = []
        if "xl/sharedStrings.xml" in self.xml:
            for item in self.xml["xl/sharedStrings.xml"]:
                self.shared.append("".join(node.text or "" for node in item.iter() if local(node.tag) == "t"))
        relationships = {}
        for node in self.xml["xl/_rels/workbook.xml.rels"]:
            relationships[node.attrib["Id"]] = node.attrib["Target"]
        self.sheets = {}
        for node in self.xml["xl/workbook.xml"].iter():
            if local(node.tag) != "sheet":
                continue
            rel_id = next(value for key, value in node.attrib.items() if local(key) == "id")
            target = relationships[rel_id].lstrip("/")
            if not target.startswith("xl/"):
                target = str(PurePosixPath("xl") / target)
            self.sheets[node.attrib["name"]] = str(PurePosixPath(target))
        self.names = {}
        for node in self.xml["xl/workbook.xml"].iter():
            if local(node.tag) == "definedName":
                self.names[node.attrib["name"]] = node.text
        self.chart_parts = sorted(name for name in self.members if name.startswith("xl/charts/") and name.endswith(".xml"))
        self.table_parts = sorted(name for name in self.members if name.startswith("xl/tables/") and name.endswith(".xml"))
        self.chart_refs = [node.text for name in self.chart_parts for node in self.xml[name].iter() if local(node.tag) == "f"]
        self.external_relationships = []
        for name, root in self.xml.items():
            if not name.endswith(".rels"):
                continue
            for node in root:
                if node.attrib.get("TargetMode") == "External":
                    self.external_relationships.append({"part": name, "target": node.attrib.get("Target")})

    def cells(self, sheet):
        result = {}
        for node in self.xml[self.sheets[sheet]].iter():
            if local(node.tag) != "c":
                continue
            children = {local(child.tag): child for child in node}
            value_node = children.get("v")
            raw = value_node.text if value_node is not None else None
            kind = node.attrib.get("t", "n")
            if kind == "s" and raw is not None:
                value = self.shared[int(raw)]
            elif kind == "inlineStr":
                value = "".join(child.text or "" for child in node.iter() if local(child.tag) == "t")
            else:
                value = raw
            result[node.attrib["r"]] = {
                "value": value,
                "type": kind,
                "formula": children["f"].text if "f" in children else None,
            }
        return result

    def validations(self, sheet):
        result = []
        for node in self.xml[self.sheets[sheet]].iter():
            if local(node.tag) != "dataValidation":
                continue
            children = {local(child.tag): child.text for child in node}
            result.append({"attributes": dict(node.attrib), "formulas": children})
        return result

    def table_refs(self):
        return [self.xml[name].attrib.get("ref") for name in self.table_parts]


def formula_map(book):
    result = {}
    for sheet in book.sheets:
        for cell, value in book.cells(sheet).items():
            if value["formula"] is not None:
                result[f"{sheet}!{cell}"] = value["formula"]
    return result


def orders(book):
    cells = book.cells("Orders")
    rows = []
    for row in range(2, 6):
        values = [cells[f"{column}{row}"]["value"] for column in "ABCDEF"]
        rows.append(dict(zip(("order_id", "sku", "qty", "unit_price", "currency", "revision"), values)))
    return rows


def totals(rows):
    lines = [Decimal(row["qty"]) * Decimal(row["unit_price"]) for row in rows]
    return lines, sum(lines, Decimal("0"))


def compare_s17(base, correction):
    base_cells, correction_cells = base.cells("Orders"), correction.cells("Orders")
    changed = {}
    for cell in sorted(set(base_cells) | set(correction_cells)):
        before, after = base_cells.get(cell, {}), correction_cells.get(cell, {})
        if before.get("value") != after.get("value") and before.get("formula") is None and after.get("formula") is None:
            changed["Orders!" + cell] = [before.get("value"), after.get("value")]
    base_rows, correction_rows = orders(base), orders(correction)
    base_lines, base_total = totals(base_rows)
    correction_lines, correction_total = totals(correction_rows)
    base_ids = [row["order_id"] for row in base_rows]
    correction_ids = [row["order_id"] for row in correction_rows]
    return {
        "changed_inputs": changed,
        "added_rows": len(set(correction_ids) - set(base_ids)),
        "deleted_rows": len(set(base_ids) - set(correction_ids)),
        "row_lineage": [{"order_id": row["order_id"], "base_row": index + 2, "correction_row": correction_ids.index(row["order_id"]) + 2} for index, row in enumerate(base_rows)],
        "base_total_rub": money(base_total),
        "correction_total_rub": money(correction_total),
        "delta_rub": money(correction_total - base_total),
        "g3": [money(base_lines[1]), money(correction_lines[1])],
        "formulas_before": formula_map(base),
        "formulas_after": formula_map(correction),
        "text_ids_preserved": all(cell["type"] in {"s", "inlineStr", "str"} for book in (base, correction) for cell in [book.cells("Orders")[f"A{row}"] for row in range(2, 6)]),
    }


def valid_reference(reference, book):
    cell = r"(?:\$[A-Z]+\$\d+|[A-Z]+\d+)"
    match = re.fullmatch(r"'([^']+)'!(" + cell + r"(?::" + cell + r")?)", reference or "")
    return bool(match and match.group(1) in book.sheets)


def related_part(book, part, identifier, kind):
    """Resolve one internal relationship with the required feature type."""
    import posixpath
    path = PurePosixPath(part)
    relationships = str(path.parent / "_rels" / (path.name + ".rels"))
    for node in book.xml.get(relationships, ()):
        if (node.attrib.get("Id") == identifier
                and node.attrib.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/" + kind
                and node.attrib.get("TargetMode") != "External"):
            value = node.attrib.get("Target", "")
            if not value:
                return None
            resolved = posixpath.normpath(value.lstrip("/") if value.startswith("/")
                                         else str(path.parent / value))
            if not resolved.startswith("../") and resolved in book.xml:
                return resolved
    return None


def reachable_features(book):
    """Follow actual sheet references; orphan XML is not a retained feature."""
    relation_id = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    charts, tables = set(), set()
    for sheet in book.sheets.values():
        for node in book.xml[sheet].iter():
            if local(node.tag) == "tablePart":
                table = related_part(book, sheet, node.attrib.get(relation_id), "table")
                if table is not None:
                    tables.add(table)
            if local(node.tag) != "drawing":
                continue
            drawing = related_part(book, sheet, node.attrib.get(relation_id), "drawing")
            if drawing is None:
                continue
            for chart_node in book.xml[drawing].iter():
                if local(chart_node.tag) != "chart":
                    continue
                chart = related_part(book, drawing, chart_node.attrib.get(relation_id), "chart")
                if chart is not None:
                    charts.add(chart)
    return charts, tables


def validate_s18(book):
    failures = []
    validations = book.validations("Orders")
    expected_validation = {"type": "whole", "operator": "between", "allowBlank": "0", "showErrorMessage": "1", "errorStyle": "stop", "sqref": "C2:C5"}
    if len(validations) != 1 or any(validations[0]["attributes"].get(key) != value for key, value in expected_validation.items()):
        failures.append("validation_rule")
    if not validations or validations[0]["formulas"].get("formula1") != "1" or validations[0]["formulas"].get("formula2") != "100":
        failures.append("validation_bounds")
    if book.names != EXPECTED_NAMES:
        failures.append("defined_names")
    if any(not valid_reference(value, book) for value in book.names.values()):
        failures.append("defined_name_targets")
    # Resolve local scope to its sheet name: sheet order is not a requirement.
    sheet_names = [node.attrib.get("name") for node in book.xml["xl/workbook.xml"].iter()
                   if local(node.tag) == "sheet"]
    actual_names, seen_names, invalid_scope = [], set(), False
    for node in book.xml["xl/workbook.xml"].iter():
        if local(node.tag) != "definedName":
            continue
        raw_scope = node.attrib.get("localSheetId")
        scope = None
        if raw_scope is not None:
            if not re.fullmatch(r"[+-]?[0-9]+", raw_scope.strip()):
                invalid_scope = True
                continue
            try:
                index = int(raw_scope)
            except ValueError:
                invalid_scope = True
                continue
            if index < 0 or index >= len(sheet_names):
                invalid_scope = True
                continue
            scope = sheet_names[index]
        name = node.attrib.get("name")
        identity = (name.casefold() if isinstance(name, str) else name, scope)
        if identity in seen_names:
            invalid_scope = True
        seen_names.add(identity)
        actual_names.append((name, scope, node.text))
    expected_names = [(name, "Orders" if name == "_xlnm._FilterDatabase" else None, value)
                      for name, value in EXPECTED_NAMES.items()]
    if invalid_scope or sorted(actual_names, key=repr) != sorted(expected_names, key=repr):
        failures.append("defined_name_scope")
    if book.chart_refs != EXPECTED_CHART_REFS or any(not valid_reference(value, book) for value in book.chart_refs):
        failures.append("chart_targets")
    reachable_charts, reachable_tables = reachable_features(book)
    if not any([node.text for node in book.xml[part].iter() if local(node.tag) == "f"]
               == EXPECTED_CHART_REFS for part in reachable_charts):
        failures.append("chart_linkage")
    if book.table_refs() != ["A1:G5"]:
        failures.append("table")
    if not any(book.xml[part].attrib.get("ref") == "A1:G5" for part in reachable_tables):
        failures.append("table_linkage")
    if book.external_relationships:
        failures.append("external_relationships")
    return failures
