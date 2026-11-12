"""One bounded fresh installed helper evaluation of two existing10723 buffers.
No Office/edit/model/send and no fabricated ordinary task/path authority.
"""
from pathlib import Path
import ast, datetime, difflib, fcntl, hashlib, importlib.util, json, os, resource, signal, stat, sys, time

B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
D=B/'CORE204-INSTALLED-SAME10723-READER-20261112'
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
N=H/'hermes-agent'
RECIPE=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-ROOT-BOUNDARY-SOURCE-PREP-20261111/SAVED10723-READER-RECIPE.json')
APP=Path('/home/jericho/.cache/FRW-ASTRA-V3-RTF-RICH-SAVED-ACTUAL-REVIEW-20261111/RESULT.json')
OBS=Path('/home/jericho/.cache/FRW-SOL-V3-RTF-RICH-MISSING-ROUNDTRIP-20261111/candidate-r4/app-stage-rich-8g5fa28t/roundtrip-observations.tsv')
os.umask(0o077)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
identity=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def main():
    assert __debug__ and sys.flags.isolated and sys.dont_write_bytecode
    resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);signal.alarm(30)
    D.mkdir(mode=0o700)
    recipe=json.loads(RECIPE.read_text());assert sha(APP)==recipe['accepted_app_proof']['sha256']
    assert sha(H/'hermes-agent.source.json')=='94aea3888c0c89b99022cda3259b7e947d063d91d8525ddbff5bd4df3ac98d6a'
    source=N/'tools/scoped_rtf.py';assert sha(source)=='7f1c0edfd9728fc0c4aa10b7f025a9ce10a24bfd4a76e11205cbbe777c085cdf'
    lock=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock');fd=os.open(lock,os.O_RDONLY|os.O_NOFOLLOW);s=os.fstat(fd);assert (s.st_dev,s.st_ino,s.st_uid,s.st_nlink,stat.S_IMODE(s.st_mode))==(2050,9440373,os.getuid(),1,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    started=time.monotonic()
    try:
        spec=importlib.util.spec_from_file_location('actual_installed204_scoped_rtf',source);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
        notes=[line.partition('\t')[2].replace('\\n','\n').strip() for line in OBS.read_text().splitlines() if line.startswith('NOTE:0\t')]
        assert len(notes)==4 and len(set(notes))==1 and notes[0]
        rows=[];texts=[]
        for ref in recipe['retained_saved_inputs']:
            p=Path(ref['path']);before=identity(p.lstat());data=p.read_bytes();assert len(data)==ref['bytes']==10723 and hashlib.sha256(data).hexdigest()==ref['sha256']
            text=m.extract_rtf(data,checkpoint=lambda:None);meta=text.extraction_metadata
            assert meta['paragraphs']==16 and len(meta['stories'])==3
            assert {r['destination'] for r in meta['stories']}=={'header','footer','footnote'}
            storylines=[line for line in str(text).splitlines() if line.startswith('[STORY ')]
            values=[json.loads(line.split(' ',2)[2][:-1]) for line in storylines]
            foot=[v for v in values if v['destination']=='footnote'];assert len(foot)==1 and notes[0] in foot[0]['text']
            assert meta['semantic_status']=='partial_inert_text_view' and meta['unsupported'] and meta['fields_evaluated'] is False and meta['objects_executed'] is False
            assert identity(p.lstat())==before and sha(p)==ref['sha256']
            texts.append(str(text));rows.append(dict(input=ref,identity_before_after=before,metadata=meta,restored_footnote_matches_retained_App_text=True,text_sha256=hashlib.sha256(str(text).encode()).hexdigest()))
        changes=[(i,a,b) for i,(a,b) in enumerate(zip(texts[1],texts[0])) if a!=b]
        assert len(texts[0])==len(texts[1]) and len(changes)==1 and changes[0][1:]==('3','4')
        assert sha(source)=='7f1c0edfd9728fc0c4aa10b7f025a9ce10a24bfd4a76e11205cbbe777c085cdf'
        result=dict(schema='friday.Root.installed204.saved10723.reader-qualification.v1',state='PASS_BOUNDED_INSTALLED_HELPER_SAME_SAVED_BYTES_PARTIAL_PROFILE',at_moscow=datetime.datetime.now().astimezone().isoformat(),source=dict(path=str(source),sha256=sha(source)),recipe=dict(path=str(RECIPE),sha256=sha(RECIPE)),accepted_App=dict(path=str(APP),sha256=sha(APP)),independent_App_observation=dict(path=str(OBS),sha256=sha(OBS)),rows=rows,source_revision_only_text_delta=changes,elapsed_seconds=time.monotonic()-started,ordinary_read_file_or_user_formal=False,no_Office_native_edit_model_create_send=True,limits='Only installed extract_rtf fresh helper; no scoped_file authority injection. Known partial cs/falt/ftnsep/userprops and layout/annotation/endnote limits retained; numbering not evaluated. Same10723 buffers, no reexport/edit10730/reopenOffice.',complete_V3=False)
        p=D/'RESULT.json';out=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(out,'w') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print(json.dumps(dict(state=result['state'],rows=len(rows),footnotes_restored=2,result_sha256=sha(p))))
    finally:
        os.close(fd);signal.alarm(0)


if __name__=='__main__':main()
