"""Post-install qualification on the retained developer bytes; no converter/send.

Requires an externally read-back installed receipt hash. It cannot run against
227 or substitute the historical user-delivered body-only artifact.
"""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree as E
import argparse,copy,datetime,hashlib,json,os,stat,sys,types
os.umask(0o077)
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
Q=Path('/home/jericho/.cache/FRW-ASTRA-DOCXODT227-STYLE-REJECTION-SOURCE-20261117')
N=Path(__file__).parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def protected(path,expected):
    before=path.lstat()
    assert stat.S_ISREG(before.st_mode)and before.st_uid==os.getuid()and before.st_nlink==1 and not before.st_mode&0o022 and not any(p.is_symlink()for p in(path,*path.parents))
    raw=path.read_bytes();after=path.lstat()
    assert all(getattr(before,k)==getattr(after,k)for k in('st_dev','st_ino','st_uid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))and sha(raw)==expected
    return raw
def mutate(data,member,change):
    with ZipFile(BytesIO(data))as package:entries=[(copy.copy(info),package.read(info))for info in package.infolist()]
    out=BytesIO()
    with ZipFile(out,'w')as package:
        for info,raw in entries:
            if info.filename==member:
                root=E.fromstring(raw);change(root);raw=E.tostring(root,encoding='utf-8',xml_declaration=True)
            package.writestr(info,raw)
    return out.getvalue()
def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--installed-receipt-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if not (__debug__ and sys.flags.isolated and sys.dont_write_bytecode):
        raise SystemExit('qualification requires python3 -I -B without optimization')
    assert args.output.is_absolute()and args.output.parent==N and not any(p.is_symlink()for p in(N,*N.parents))and not args.output.exists()
    receipt_raw=protected(H/'hermes-agent.source.json',args.installed_receipt_sha256)
    receipt=json.loads(receipt_raw)
    assert len(receipt['layers'])==228 and len(receipt['files'])==17895
    assert receipt['layers'][-1]['manifest']=='patches/hermes/word-output-visibility-after-source227-manifest.json'
    expected={'tools/scoped_word_conversion.py':'6dd133c4d9572eec1c3e0e24bd025092ab21f1466cbab48bc33d9f3dbed7e910',
              'hermes_cli/friday_workspace_word_conversion.py':'d9de55e7ec7da21c7c56db8460c38d0696ad3a69986cc0906647f37e10015e11'}
    for name,pin in expected.items():
        assert receipt['files'][name]['sha256']==pin
        protected(H/'hermes-agent'/name,pin)
    pin_file=Path('/home/jericho/.cache/FRW-ASTRA-WORD-STYLE-REFUSAL-TRACE-SOURCE-20261117/LOADER-PINS.json')
    modules=json.loads(protected(pin_file,'c5eb90fe538076670e316da37c2bcfac0bcd6f66512a98288671862bae059f5b'))['modules']
    assert [item['module']for item in modules]==[
        'tools.scoped_zip','tools.scoped_word_profiles','tools.scoped_presentation',
        'tools.scoped_odt','tools.scoped_odt_create','tools.scoped_odf_profiles',
        'tools.scoped_word_conversion']
    assert not any(k=='tools'or k.startswith('tools.')for k in sys.modules)
    package=types.ModuleType('tools');package.__path__=[];sys.modules['tools']=package
    loaded=[]
    for item in modules:
        name=item['module'];relative=name.replace('.','/')+'.py';pin=expected.get(relative,item['sha256'])
        assert receipt['files'][relative]['sha256']==pin
        path=H/'hermes-agent'/relative;raw=protected(path,pin)
        module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
        exec(compile(raw,str(path),'exec'),module.__dict__)
        loaded.append(dict(module=name,path=str(path),sha256=pin,bytes=len(raw)))
    word=sys.modules['tools.scoped_word_conversion']
    original=protected(Q/'work/input.docx','6408c64ba6b05549ef7d7aa24b99d310f536aeb4954690e3efca7a46e05412d6')
    raw=protected(Q/'work/out/input.odt','4f4661563beaeade8cadca2c425f48db7054998470adbc7e5ca3427b0e1a041a')
    derived,repair=word.restore_docx_odt_output(original,raw)
    assert sha(derived)=='f807c54e04d29060d9b688a09a72addf3c1e087055ffed8ca1b005b65b8b9946'
    details=word.validate_conversion(original,'docx',derived,'odt')
    assert details['body_blocks']==5 and details['header_stories']==details['footer_stories']==1
    checks=['installed228_actual_code_and_pure_dependencies_loaded','same_retained_developer_raw_restores_expected_bytes','full_body_and_both_stories_semantic_validation']
    def refuse(data,name):
        try:word.restore_docx_odt_output(original,data)
        except word.WordConversionError:checks.append(name)
        else:raise AssertionError(name)
    S=word.S;LO='urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0';q=word.q
    def opacity(root):
        title=next(node for node in root.iter(q(S,'style'))if node.get(q(S,'name'))=='Title')
        title.find(q(S,'text-properties')).set(q(LO,'opacity'),'0%')
    refuse(mutate(derived,'styles.xml',opacity),'used_Title_opacity_still_refused_by_installed_consumer')
    def loss(root):
        for parent in root.iter():
            for child in list(parent):
                if child.tag==q(S,'footer'):parent.remove(child)
    refuse(mutate(derived,'styles.xml',loss),'lost_required_footer_still_refused_by_installed_consumer')
    # Preserve source, retained raw package, installed receipt and all user bytes.
    protected(Q/'work/input.docx',sha(original));protected(Q/'work/out/input.odt',sha(raw))
    assert protected(H/'hermes-agent.source.json',args.installed_receipt_sha256)==receipt_raw
    result=dict(schema='frw.Root.installed228.Word-same-retained-developer-output-qualification.v1',at_moscow=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),installed_receipt_sha256=args.installed_receipt_sha256,actual_loaded_native=loaded,checks=checks,details=details,repair=repair,developer_original_sha256=sha(original),retained_raw_Office_sha256=sha(raw),derived_sha256=sha(derived),historical_received2830_regraded=False,Office_model_API_send_or_new_conversion_producer=False,source_and_retained_raw_unchanged=True,actual_installed_pure_consumer='PASS',ordinary_live_journey_or_App_or_formal='NOT_ESTABLISHED_BY_THIS_QUALIFICATION',full170_120_B00='OPEN')
    assert args.output.is_relative_to(N)and not args.output.exists()
    with args.output.open('x')as file:json.dump(result,file,ensure_ascii=False,indent=2);file.write('\n')
    args.output.chmod(0o600)
    print(json.dumps(dict(result=str(args.output),sha256=sha(args.output.read_bytes()),installed_consumer='PASS',new_live_effect=False)))
if __name__=='__main__':main()
