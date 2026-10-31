#!/usr/bin/env python3
"""Narrow static source-origin assessment; never Office/user acceptance.

Known immutable B156 source only. The future natural request MUST explicitly ask
to change Orders!C3 from 3 to 4. No total or other answer oracle is needed.
Caller supplies a SAME received file; this module neither receives nor opens Office.
"""
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

SOURCE_SHA256 = "4038289a6e89c86da8fd547705f9eb98ffbf48566e4dc22652768e405f7dec0d"
M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"
RID = "{" + R + "}id"
GAP = ["Actual SAME received-file custody and runtime bindings are UNBOUND.",
       "Office/consumer reopen, recalculation, validation enforcement, rendering and visual inspection NOT_RUN.",
       "Static retention does not establish product/user acceptance; cached results are ignored.",
       "Style/layout, arbitrary formula equivalence, unsupported extensions and dynamic external formulas are not fully assessed."]


def local(tag):
    return tag.rsplit("}", 1)[-1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_value(node):
    # Rich text runs are equivalent to plain text; phonetic annotations are not values.
    if local(node.tag) == "rPh":
        return ""
    if node.tag == "{" + M + "}t":
        return node.text or ""
    return "".join(text_value(child) for child in node)


def a1_range(value):
    value = (value or "").upper()
    if not re.fullmatch(r"\$?[A-Z]{1,3}\$?[1-9][0-9]*(?::\$?[A-Z]{1,3}\$?[1-9][0-9]*)?", value):
        raise ValueError("unsupported A1 range")
    value = value.replace("$", "")
    return value.split(":")[0] if ":" in value and len(set(value.split(":"))) == 1 else value


def covered(value):
    result = set()
    def col(s):
        n = 0
        for ch in s:
            n = n * 26 + ord(ch) - 64
        return n
    for area in (value or "").split():
        ends = a1_range(area).split(":")
        start, end = ends[0], ends[-1]
        a, b = [re.fullmatch(r"([A-Z]+)([0-9]+)", e).groups() for e in (start, end)]
        x1, x2, y1, y2 = col(a[0]), col(b[0]), int(a[1]), int(b[1])
        if x1 > x2 or y1 > y2 or (x2-x1+1)*(y2-y1+1) > 10000:
            raise ValueError("unsupported validation extent")
        result.update((x, y) for x in range(x1, x2+1) for y in range(y1, y2+1))
    if not result or len(result) > 10000:
        raise ValueError("unsupported validation extent")
    return result


def reference(value, book):
    """Known simple internal A1 references only; other formulas are unsupported."""
    match = re.fullmatch(r"(?:'((?:[^']|'')+)'|([^'!]+))!([^!]+)", (value or "").strip())
    if not match:
        raise ValueError("unsupported reference expression")
    sheet = (match[1].replace("''", "'") if match[1] is not None else match[2])
    a1_range(match[3])
    if sheet.casefold() not in {s.casefold() for s in book.sheets}:
        raise LookupError("reference sheet missing or external")
    # Defined-name relative/absolute anchors are semantic, not serialization.
    return [sheet.casefold(), match[3].upper()]


class Book:
    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [i.filename for i in infos]
            if len(names) != len(set(names)) or len(names) > 4096 or sum(i.file_size for i in infos) > 64*1024*1024:
                raise ValueError("duplicate members or package limit exceeded")
            if any(i.file_size > 16*1024*1024 for i in infos):
                raise ValueError("part limit exceeded")
            if archive.testzip() is not None:
                raise ValueError("CRC failure")
            self.xml = {i.filename: ET.fromstring(archive.read(i)) for i in infos
                        if i.filename.endswith((".xml", ".rels"))}
        package_root = self.related("", "officeDocument")
        if len(package_root) != 1:
            raise ValueError("ambiguous workbook relationship")
        self.workbook = package_root[0]
        root = self.xml[self.workbook]
        if root.tag != "{" + M + "}workbook":
            raise ValueError("unsupported workbook namespace")
        self.sheets = {}
        self.sheet_order = []
        for sheet in root.findall("./{" + M + "}sheets/{" + M + "}sheet"):
            name = sheet.attrib["name"]
            if name.casefold() in {s.casefold() for s in self.sheets}:
                raise ValueError("duplicate sheet name")
            parts = self.related(self.workbook, "worksheet", sheet.get(RID))
            if len(parts) != 1:
                raise ValueError("missing/ambiguous worksheet relationship")
            self.sheets[name] = parts[0]
            self.sheet_order.append(name)
        shared_parts = self.related(self.workbook, "sharedStrings")
        self.shared = [text_value(n) for p in shared_parts for n in self.xml[p]]
        self.names = {}
        for name in root.findall("./{" + M + "}definedNames/{" + M + "}definedName"):
            scope = None
            if "localSheetId" in name.attrib:
                raw = name.get("localSheetId")
                if not re.fullmatch(r"[0-9]+", raw or "") or int(raw) >= len(self.sheet_order):
                    raise ValueError("invalid defined-name scope")
                scope = self.sheet_order[int(raw)].casefold()
            key = (name.attrib["name"].casefold(), scope)
            if key in self.names:
                raise ValueError("duplicate scoped name")
            self.names[key] = name.text or ""

    def related(self, source, kind, identifier=None):
        part = PurePosixPath(source)
        rels = str(part.parent / "_rels" / (part.name + ".rels")) if source else "_rels/.rels"
        result = []
        for rel in self.xml.get(rels, ()):
            if rel.get("Type") != R + "/" + kind or (identifier is not None and rel.get("Id") != identifier):
                continue
            target = rel.get("Target", "")
            if rel.get("TargetMode") == "External" or not target:
                continue
            dest = posixpath.normpath(target.lstrip("/") if target.startswith("/") else str(part.parent / target))
            if dest.startswith("../") or dest not in self.xml:
                continue
            result.append(dest)
        return result

    def cells(self, sheet):
        result = {}
        for cell in self.xml[self.sheets[sheet]].findall("./{" + M + "}sheetData/{" + M + "}row/{" + M + "}c"):
            address = a1_range(cell.attrib["r"])
            if ":" in address or address in result:
                raise ValueError("invalid/duplicate cell")
            f = cell.find("{" + M + "}f")
            if f is not None:
                result[address] = {"kind": "formula", "source": f.text or "", "encoding": f.get("t", "normal")}
                continue
            kind = cell.get("t", "n")
            value = cell.findtext("{" + M + "}v")
            if kind == "inlineStr":
                result[address] = {"kind": "text", "value": text_value(cell)}
            elif kind == "s":
                if value is None or not value.isdigit() or int(value) >= len(self.shared):
                    raise ValueError("invalid shared-string index")
                result[address] = {"kind": "text", "value": self.shared[int(value)]}
            elif kind == "str":
                result[address] = {"kind": "text", "value": value or ""}
            elif value is None:
                continue  # blank formatting-only cells are not source values
            elif kind == "n":
                number = Decimal(value)
                if not number.is_finite():
                    raise ValueError("nonfinite numeric cell")
                result[address] = {"kind": "number", "value": str(number.normalize())}
            elif kind in {"b", "e", "d"}:
                result[address] = {"kind": kind, "value": value}
            else:
                result[address] = {"kind": "unsupported", "type": kind}
        return result

    def validations(self, sheet):
        result = []
        defaults = {"type": "none", "operator": "between", "allowBlank": "0", "showInputMessage": "0",
                    "showErrorMessage": "0", "errorStyle": "stop", "imeMode": "noControl"}
        bools = {"allowBlank", "showInputMessage", "showErrorMessage"}
        for rule in self.xml[self.sheets[sheet]].findall("./{" + M + "}dataValidations/{" + M + "}dataValidation"):
            attrs = dict(defaults)
            attrs.update({local(k): v for k, v in rule.attrib.items() if local(k) not in {"sqref", "uid"}})
            for key in bools:
                attrs[key] = {"false": "0", "true": "1"}.get(attrs[key], attrs[key])
            formulas = [(local(c.tag), c.text or "") for c in rule]
            result.append({"coverage": covered(rule.get("sqref")), "semantic": [sorted(attrs.items()), formulas]})
        return result

    def feature_parts(self, sheet, kind):
        source = self.sheets[sheet]
        if kind == "table":
            return [p for n in self.xml[source].findall("./{" + M + "}tableParts/{" + M + "}tablePart")
                    for p in self.related(source, "table", n.get(RID, ""))]
        return [p for n in self.xml[source].findall("./{" + M + "}drawing")
                for d in self.related(source, "drawing", n.get(RID, ""))
                for chart in self.xml[d].iter() if local(chart.tag) == "chart"
                for p in self.related(d, "chart", chart.get(RID, ""))]

    def chart_signature(self, part):
        entries = []
        def visit(node, path):
            if local(node.tag) == "f":
                entries.append([path, reference(node.text, self)])
            counts = Counter()
            for child in node:
                tag = local(child.tag)
                index = counts[tag]
                counts[tag] += 1
                visit(child, path + "/" + tag + "[" + str(index) + "]")
        visit(self.xml[part], "chartSpace")
        return entries

    def table_signature(self, part):
        table = self.xml[part]
        return {"name": table.get("name", "").casefold(), "displayName": table.get("displayName", "").casefold(),
                "ref": a1_range(table.get("ref")),
                "columns": [n.get("name") for n in table.findall("./{" + M + "}tableColumns/{" + M + "}tableColumn")],
                "autoFilter": a1_range(table.find("{" + M + "}autoFilter").get("ref"))
                if table.find("{" + M + "}autoFilter") is not None else None}

    def external_links(self):
        found = []
        for part, root in self.xml.items():
            for node in root.iter():
                if node.tag == "{" + P + "}Relationship" and node.get("TargetMode", "").casefold() == "external":
                    found.append({"part": part, "kind": "external_relationship", "relationship_type": node.get("Type")})
                if local(node.tag) in {"externalReference", "externalLink"}:
                    found.append({"part": part, "kind": local(node.tag)})
                if local(node.tag) in {"f", "definedName", "formula", "formula1", "formula2", "calculatedColumnFormula", "totalsRowFormula"} and re.search(r"\[[^\]]+\][^!]*!", node.text or ""):
                    found.append({"part": part, "kind": "external_workbook_formula"})
        return found


def feature_report(source, candidate):
    reports = {"validation": [], "named_ranges": [], "chart_references": [], "table_linkage": []}
    for sheet in source.sheets:
        if sheet not in candidate.sheets:
            for kind in ("validation", "chart_references", "table_linkage"):
                reports[kind].append({"sheet": sheet, "status": "lost", "reason": "source sheet missing"})
            continue
        before_rules = source.validations(sheet)
        unsupported_rules = False
        try:
            after_rules = candidate.validations(sheet)
        except ValueError:
            after_rules, unsupported_rules = [], True
        has_extended = any(local(n.tag) == "dataValidation" and n.tag != "{" + M + "}dataValidation"
                           for n in candidate.xml[candidate.sheets[sheet]].iter())
        for i, rule in enumerate(before_rules):
            matching = set().union(*(r["coverage"] for r in after_rules if r["semantic"] == rule["semantic"]))
            conflict = any(r["coverage"] & rule["coverage"] and r["semantic"] != rule["semantic"] for r in after_rules)
            retained = matching >= rule["coverage"] and not conflict
            reports["validation"].append({"sheet": sheet, "source_rule": i, "status": "retained" if retained else "unsupported" if has_extended or unsupported_rules else "lost",
                                          "coverage_cells": len(rule["coverage"]), "conflicting_rule": conflict})
        for kind, label in (("chart", "chart_references"), ("table", "table_linkage")):
            method = "chart_signature" if kind == "chart" else "table_signature"
            after, unsupported = [], False
            for p in candidate.feature_parts(sheet, kind):
                try:
                    after.append(getattr(candidate, method)(p))
                except ValueError:
                    unsupported = True
                except LookupError:
                    pass
            for p in source.feature_parts(sheet, kind):
                wanted = getattr(source, method)(p)
                retained = wanted in after
                reports[label].append({"sheet": sheet, "source_signature": wanted,
                                       "status": "retained" if retained else "unsupported" if unsupported else "lost",
                                       "actual_linkage_required": True})
    for key, expression in source.names.items():
        before = reference(expression, source)
        status = "lost"
        if key in candidate.names:
            try:
                status = "retained" if reference(candidate.names[key], candidate) == before else "lost"
            except ValueError:
                status = "unsupported"
            except LookupError:
                status = "lost"
        reports["named_ranges"].append({"name": key[0], "scope_sheet": key[1], "source_reference": before, "status": status})
    return reports


def assess(source_path, received_path):
    report = {"schema": "frw.s18.same-received-static-assessment.v1", "scope": "SOURCE_ONLY_STATIC",
              "source": {"path": str(source_path), "sha256": sha(source_path)},
              "received": {"path": str(received_path), "sha256": sha(received_path)},
              "declared_edit": {"sheet": "Orders", "cell": "C3", "from": "3", "to": "4"},
              "gaps": GAP, "office_consumer_acceptance": "NOT_RUN", "user_acceptance": "UNACCEPTED"}
    if report["source"]["sha256"] != SOURCE_SHA256:
        raise ValueError("immutable B156 source SHA mismatch")
    source, candidate = Book(source_path), Book(received_path)
    changes, unsupported, additions = [], [], []
    edit_seen = False
    for sheet in source.sheets:
        before = source.cells(sheet)
        after = candidate.cells(sheet) if sheet in candidate.sheets else {}
        for cell, old in before.items():
            new = after.get(cell)
            expected = {"kind": "number", "value": "4"} if (sheet, cell) == ("Orders", "C3") else old
            if (sheet, cell) == ("Orders", "C3"):
                edit_seen = new == expected
            if new is not None and (new.get("kind") == "unsupported" or new.get("encoding", "normal") != "normal"):
                unsupported.append({"sheet": sheet, "cell": cell, "reason": "unsupported cell/formula encoding"})
            elif new != expected:
                changes.append({"sheet": sheet, "cell": cell, "source": old, "expected": expected, "received": new})
        additions.extend({"sheet": sheet, "cell": c} for c in after.keys() - before.keys())
    additions.extend({"sheet": s, "scope": "additional sheet"} for s in candidate.sheets.keys() - source.sheets.keys())
    report["source_data_and_formula_sources"] = {"status": "lost" if changes else "unsupported" if unsupported else "retained",
        "declared_edit_observed": edit_seen, "unexpected_changes": changes, "unsupported": unsupported,
        "additions_for_review_not_automatic_failure": additions, "formula_cached_results": "IGNORED"}
    report["features"] = feature_report(source, candidate)
    report["external_links"] = {"status": "present" if candidate.external_links() else "none_detected",
        "items": candidate.external_links(), "scope": "OOXML external relationships/references and explicit [workbook] formulas; dynamic formulas not exhaustive"}
    statuses = [r["status"] for rows in report["features"].values() for r in rows]
    if changes or "lost" in statuses or report["external_links"]["items"]:
        report["structural_outcome"] = "STRUCTURAL_CHANGE_REQUIRES_REVIEW"
    elif unsupported or "unsupported" in statuses or "unknown" in statuses:
        report["structural_outcome"] = "INCOMPLETE_UNSUPPORTED"
    else:
        report["structural_outcome"] = "SOURCE_ORIGIN_STRUCTURALLY_RETAINED"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--received", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = assess(args.source, args.received)
    except (ValueError, KeyError, IndexError, InvalidOperation, ET.ParseError, zipfile.BadZipFile, OSError) as exc:
        result = {"schema": "frw.s18.same-received-static-assessment.v1", "scope": "SOURCE_ONLY_STATIC",
                  "structural_outcome": "UNKNOWN", "error_class": type(exc).__name__,
                  "reason": "Package/input cannot be assessed by this narrow helper", "gaps": GAP,
                  "features": {kind: [{"status": "unknown", "reason": "input assessment unavailable"}]
                               for kind in ("validation", "named_ranges", "chart_references", "table_linkage")},
                  "source_data_and_formula_sources": {"status": "unknown"},
                  "external_links": {"status": "unknown"},
                  "office_consumer_acceptance": "NOT_RUN", "user_acceptance": "UNACCEPTED"}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if result["structural_outcome"] == "UNKNOWN" else 0


if __name__ == "__main__":
    raise SystemExit(main())
