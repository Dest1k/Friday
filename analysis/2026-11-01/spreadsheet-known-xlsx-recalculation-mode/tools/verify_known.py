"""Read-only verifier for this explicitly published synthetic XLSX fixture.
This checks stored OOXML values/formulas; it does not run a spreadsheet engine.
"""
import argparse
import hashlib
import json
import stat
import zipfile
from decimal import Decimal
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def inspect(path, expected, stale):
    raw = path.read_bytes()
    require(len(raw) <= 1024 * 1024, 'bounded fixture required')
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        require(len(names) == len(set(names)) and len(names) <= 32, 'unique bounded ZIP entries required')
        require(sum(item.file_size for item in infos) <= 2 * 1024 * 1024, 'bounded XML parts required')
        for item in infos:
            name = PurePosixPath(item.filename)
            require(not name.is_absolute() and '..' not in name.parts and '\\' not in item.filename,
                    'unsafe ZIP name')
            require(not stat.S_ISLNK(item.external_attr >> 16), 'ZIP symlink rejected')
            require(item.filename.endswith(('.xml', '.rels')), 'unexpected non-XML part')
            body = archive.read(item)
            require(b'<!DOCTYPE' not in body and b'<!ENTITY' not in body, 'XML entity declarations rejected')
            root = ET.fromstring(body)
            if item.filename.endswith('.rels'):
                require(not any(node.get('TargetMode') == 'External' for node in root), 'external relation rejected')
        shared = []
        if 'xl/sharedStrings.xml' in names:
            shared = [''.join(item.itertext()) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        cells = {}
        for cell in sheet.findall('.//s:sheetData/s:row/s:c', NS):
            key = cell.get('r')
            require(key not in cells, 'duplicate cell')
            formula = cell.find('s:f', NS)
            value = cell.findtext('s:v', default='', namespaces=NS)
            kind = cell.get('t', 'n')
            if kind == 's':
                value = shared[int(value)]
            elif kind == 'inlineStr':
                value = ''.join(cell.find('s:is', NS).itertext())
            entry = {'kind': 'text' if kind in ('s', 'inlineStr') else 'number', 'value': value}
            if formula is not None:
                entry['formula'] = formula.text or ''
            cells[key] = entry
        wanted = expected['cells']
        require(set(cells) == set(wanted), 'exact 12-cell set required')
        for key, goal in wanted.items():
            actual = cells[key]
            require(actual.get('formula') == goal.get('formula'), 'formula changed: ' + key)
            require(actual['kind'] == goal['kind'], 'cell type changed: ' + key)
            value = expected['stale_cached_cells'][key] if stale and key in expected['stale_cached_cells'] else goal['value']
            require((Decimal(actual['value']) == Decimal(value)) if goal['kind'] == 'number' else actual['value'] == value,
                    'unexpected stored value: ' + key)
        if 'docProps/core.xml' in names:
            core = ET.fromstring(archive.read('docProps/core.xml'))
            require(all(not (n.text or '').strip() for n in core if n.tag.rsplit('}', 1)[-1] in
                        ('creator', 'lastModifiedBy', 'title', 'subject', 'description')), 'nonempty personal metadata')
    return {'file': path.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'cells': len(cells),
            'formula_cells': sum('formula' in c for c in cells.values()),
            'stored_formula_values': {k: cells[k]['value'] for k in expected['stale_cached_cells']},
            'result': 'EXPECTED_STALE_INPUT' if stale else 'EXPECTED_CALCULATED_OUTPUT'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('xlsx', type=Path, nargs='+')
    parser.add_argument('--expected', type=Path, default=Path(__file__).resolve().parents[1] / 'expected-values.json')
    parser.add_argument('--stale', action='store_true', help='Expect the deliberately stale input cache values')
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text(encoding='utf-8'))
    print(json.dumps([inspect(path, expected, args.stale) for path in args.xlsx], ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
