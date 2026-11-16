"""Read only exact pinned primary dependencies; produce a source table, no runtime.

The parser extracts only ImplTextEncodingData aggregate fields, not converters.
"""
import concurrent.futures
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).parent
DEST = ROOT / 'native-table'
PRIMARY = DEST / 'primary'
for p in (DEST, PRIMARY):
    p.mkdir(mode=0o700, exist_ok=True)
    p.chmod(0o700)
COMMIT = 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
BASE = pathlib.Path('/home/jericho/.cache/FRW-SOL-V3-CALC-REFERENCE-RUNTIME-QUALIFIER-CORE-20261115/font-resolver/primary')
OLD = pathlib.Path('/home/jericho/.cache/FRW-SOL-V3-CALC-REFERENCE-METRIC-OBSERVER-SOURCE-CORE-20261115/internal-path/official-source')
cached = {'sal/textenc/tables.cxx': BASE/'sal__textenc__tables.cxx',
          'sal/textenc/textenc.cxx': BASE/'sal__textenc__textenc.cxx',
          'sal/textenc/tenchelp.hxx': BASE/'sal__textenc__tenchelp.hxx',
          'sal/textenc/tencinfo.cxx': OLD/'sal__textenc__tencinfo.cxx',
          'include/rtl/textenc.h': OLD/'include__rtl__textenc.h'}
records = []
sources = {}
for upstream, p in cached.items():
    b = p.read_bytes()
    sources[upstream] = b.decode()
    records.append(dict(upstream_path=upstream, path=str(p), sha256=hashlib.sha256(b).hexdigest(),
                        url=f'https://github.com/LibreOffice/core/blob/{COMMIT}/{upstream}', access='CACHED_READ_ONLY'))
includes = re.findall(r'^#include "([^"]+\.tab)"', sources['sal/textenc/tables.cxx'], re.M)

def fetch(name):
    upstream = 'sal/textenc/' + name
    p = PRIMARY / upstream.replace('/', '__')
    url = f'https://raw.githubusercontent.com/LibreOffice/core/{COMMIT}/{upstream}'
    if not p.exists():
        req = urllib.request.Request(url, headers={'User-Agent':'SourceContract/1'})
        with urllib.request.urlopen(req, timeout=40) as r:
            b = r.read(20_000_001)
        if len(b) > 20_000_000:
            raise ValueError('unexpected source size')
        p.write_bytes(b)
        p.chmod(0o400)
    b = p.read_bytes()
    return upstream, b.decode(), dict(upstream_path=upstream, path=str(p),
        sha256=hashlib.sha256(b).hexdigest(), bytes=len(b), url=url, access='EXACT_PINNED_PRIMARY_FETCH')

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for upstream, source, rec in pool.map(fetch, includes):
        sources[upstream] = source
        records.append(rec)

def no_comments(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)

def top_fields(text, start):
    depth = 0
    in_string = False
    escaped = False
    fields = []
    begin = start+1
    for pos in range(start, len(text)):
        c = text[pos]
        if in_string:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == '"': in_string = False
            continue
        if c == '"': in_string = True
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                fields.append(text[begin:pos].strip())
                return fields
        elif c == ',' and depth == 1:
            fields.append(text[begin:pos].strip())
            begin = pos+1
    raise ValueError('unterminated initializer')

definitions = {}
for upstream, text in sources.items():
    # Keeping newlines preserves primary-source line locations.
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m:'\n'*m.group().count('\n'), text, flags=re.S)
    for m in re.finditer(r'ImplTextEncodingData\s+(?:const\s+)?(\w+)\s*=\s*\{', clean):
        fields = top_fields(clean, m.end()-1)
        if len(fields) != 8 or not re.fullmatch(r'\d+', fields[6]):
            raise ValueError(('unrecognized aggregate', upstream, m.group(1), fields))
        if m.group(1) in definitions:
            raise ValueError('duplicate encoding definition')
        definitions[m.group(1)] = dict(windows_byte=int(fields[6]), upstream_path=upstream,
            line=text.count('\n',0,m.start())+1, definition=m.group(1))

header=sources['include/rtl/textenc.h']
enums = {m.group(1):int(m.group(2),0) for m in re.finditer(r'^#define RTL_TEXTENCODING_(\w+)\s+\(RTL_TEXTENC_CAST\(\s*(0x[0-9A-Fa-f]+|\d+)\s*\)\)',header,re.M)}
enums = {name:value for name,value in enums.items() if not name.startswith('USER_')}
assert len([v for v in enums.values() if v < 97]) == 96 # reserved9 is not defined

# Parse all-locale branch and retain each conditional declaration explicitly.
table = sources['sal/textenc/tables.cxx'].split('= { nullptr, /* DONTKNOW */',1)[1].split('static_assert(',1)[0]
table = 'nullptr, /* DONTKNOW */'+table
chosen=[]
condition=None
enabled=True
for line in table.splitlines():
    if line.startswith('#if '):
        assert condition is None
        condition=line[4:]
        enabled=True
    elif line.startswith('#else'): enabled=False
    elif line.startswith('#endif'):
        condition=None
        enabled=True
    elif enabled:
        m=re.search(r'(&\w+|nullptr|NULL)\s*[,};]*\s*/\*\s*(.*?)\s*\*/',line)
        if m: chosen.append(dict(pointer=m.group(1), comment=m.group(2), condition=condition))
assert len(chosen) == 97, len(chosen)
direct=dict(re.findall(r'case RTL_TEXTENCODING_(\w+):\s*return &(\w+);',sources['sal/textenc/textenc.cxx']))
inverse=dict((int(byte),enums[name]) for byte,name in re.findall(r'case\s+(\d+):\s+eTextEncoding = RTL_TEXTENCODING_(\w+)',sources['sal/textenc/tencinfo.cxx'].split('rtl_getTextEncodingFromWindowsCharset',1)[1].split('return eTextEncoding;',1)[0]))
entries=[]
for name,value in sorted(enums.items(),key=lambda x:x[1]):
    if name in direct:
        info=definitions[direct[name]]
        kind='DIRECT_CORE_TABLE'
        condition=None
    elif value < len(chosen):
        row=chosen[value]
        condition=row['condition']
        if row['pointer'].startswith('&'):
            info=definitions[row['pointer'][1:]]
            kind='FULL_TABLE_CONDITIONAL' if condition else 'FULL_TABLE'
        else:
            info=None
            kind='DEFINED_ENUM_NO_CONVERTER_TABLE'
    else:
        info=None
        condition=None
        kind='DEFINED_ENUM_OUTSIDE_TABLE'
    win=info['windows_byte'] if info else 1
    export=inverse.get(win,0)
    # Conditional table absent: native fallback Windows1/export0; record both.
    alternatives=[dict(windows_byte=win,export_RTL_encoding=export)]
    if condition:
        alternatives.append(dict(windows_byte=1,export_RTL_encoding=0,when='LOCALE_TABLE_NOT_COMPILED'))
    entries.append(dict(name=name,RTL_encoding=value,UNO_short=value if value<32768 else value-65536,
        source_kind=kind,table=info,build_condition=condition,alternatives=alternatives,
        canonical_export_profile=all(x['export_RTL_encoding'] in (0,1) for x in alternatives),
        build_independent_roundtrip=len({(x['windows_byte'],x['export_RTL_encoding']) for x in alternatives})==1))

profile={e['UNO_short']:(e['alternatives'][0]['windows_byte'],e['alternatives'][0]['export_RTL_encoding'])
    for e in entries if e['canonical_export_profile'] and e['build_independent_roundtrip']}
result=dict(schema='frw.pinned.charset-native-table.Source.v1',source_commit=COMMIT,version='26.2.5.2',
    status='SOURCE_TABLE_COMPLETE_ENUMS_NOT_RUNTIME_OBSERVATIONS',
    api_type='UNO short / sal_Int16; exact Python int required by consumer',native_type='rtl_TextEncoding / sal_uInt16',
    entries=entries,canonical_build_independent_profile={str(k):list(v) for k,v in sorted(profile.items())},
    reserved_9=dict(defined_enum=False,windows_byte=1,export_RTL_encoding=0,accepted_profile=False),
    unassigned_and_user_values=dict(range='uint16 values outside named enums, including user markers/range',
        native_no_table_windows_byte=1,native_inverse_export_RTL=0,accepted_profile=False,
        reason='Fallback behavior is not evidence of a supported source encoding; no blanket uint16 acceptance.'),
    full_library_unavailable='Direct core encodings1,11,12,76,90 do not need full table lookup; other lookups use linked full table or dynamic library. Dynamic library load/symbol failure aborts in source, not a fabricated null/fallback result. Candidate excludes conditional ambiguous canonical cases; external pinned component binding still required.',
    source_records=records,
    checks=dict(table_entries=97,named_encodings=len(entries),direct_definitions=len(direct),aggregate_definitions=len(definitions),
                exact_needed_includes=len(includes),inverse_explicit_cases=len(inverse),all_definitions_parsed=True),
    effects=dict(Office=False,UNO=False,runtime=False,model=False,userdata=False,network='ONLY_EXACT_PINNED_PRIMARY_SOURCE_FETCH'))
p=DEST/'MAP.json'
p.write_text(json.dumps(result,indent=2)+'\n'); p.chmod(0o600)
print(json.dumps(dict(status=result['status'],checks=result['checks'],profile=result['canonical_build_independent_profile'],sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
