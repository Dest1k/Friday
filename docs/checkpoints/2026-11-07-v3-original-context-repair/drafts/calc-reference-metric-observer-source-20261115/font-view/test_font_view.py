"""Pure negative controls: no font/config filesystem mutation or font engine."""
import copy, json, os, pathlib, tempfile
ns={};p=pathlib.Path(__file__).with_name('font_view.py');exec(compile(p.read_bytes(),str(p),'exec'),ns)
view={'entries':[{'path':'/usr/share/fonts/test.ttf','resolved':'/trusted/test.ttf','lstat':{'uid':0,'mode':33188,'size':7,'ctime_ns':101},'stat':{'uid':0,'mode':33188,'size':7,'ctime_ns':101},'sha256':'a'*64,'kind':'file'}],'symlink_topology':{'/usr/share/fonts/test.ttf':{'target':'/trusted/test.ttf','lstat':{'uid':0,'mode':41471}}},'roots':['/usr/share/fonts']}
base={'view':copy.deepcopy(view),'view_sha256':ns['digest'](view)};done=[]
def reject(name,call):
    try:call()
    except ns['Refusal'] as e:done.append({'name':name,'status':'PASS','refusal':str(e)})
    else:raise AssertionError(name+' accepted')
ns['checked_baseline'](base,base['view_sha256']);ns['assert_view_matches'](view,base)
done.append({'name':'unchanged pinned baseline','status':'PASS'})
for key,value in [('uid',1000),('mode',33152),('size',8),('ctime_ns',102)]:
    changed=copy.deepcopy(view);changed['entries'][0]['stat'][key]=value
    reject('changed '+key,lambda c=changed:ns['assert_view_matches'](c,base))
changed=copy.deepcopy(view);changed['symlink_topology']['/usr/share/fonts/test.ttf']['target']='/trusted/other.ttf'
reject('same byte size but changed symlink mapping',lambda:ns['assert_view_matches'](changed,base))
changed=copy.deepcopy(view);changed['entries'].append({'path':'/usr/share/fonts/new.ttf'})
reject('added path set',lambda:ns['assert_view_matches'](changed,base))
changed=copy.deepcopy(view);changed['entries']=[]
reject('removed path set',lambda:ns['assert_view_matches'](changed,base))
changed=copy.deepcopy(view);changed['entries'][0]['sha256']='b'*64
reject('critical bytes digest drift',lambda:ns['assert_view_matches'](changed,base))
forged={'view':changed,'view_sha256':ns['digest'](changed)}
reject('self-consistent forged baseline lacks pinned authority',lambda:ns['checked_baseline'](forged,base['view_sha256']))
reject('missing external baseline pin',lambda:ns['checked_baseline'](base,None))
envbase=copy.deepcopy(base);envbase['view']['environment']={'LANG':'unexpected'};envbase['view_sha256']=ns['digest'](envbase['view'])
reject('callback refuses environment before any scan',lambda:ns['validate_static_font_config_view'](envbase,expected_view_digest=envbase['view_sha256']))
reject('uncovered XDG font directory',lambda:ns['assert_user_directive']('dir','other-fonts','xdg'))
reject('uncovered HOME include file',lambda:ns['assert_user_directive']('include','~/other.conf',None))
reject('relative font dir cannot inherit config parent',lambda:ns['static_system_target']('dir','extra-fonts','/etc/fonts/evil.conf'))
reject('relative cache dir cannot inherit config parent',lambda:ns['static_system_target']('cachedir','extra-cache','/etc/fonts/evil.conf'))
reject('unrecognized relative include',lambda:ns['static_system_target']('include','other.conf','/etc/fonts/evil.conf'))
assert ns['static_system_target']('include','local.conf','/etc/fonts/conf.d/51-local.conf')=='/etc/fonts/local.conf'
done.append({'name':'stock local.conf include maps system base','status':'PASS'})
# Test real scanner reuse guard with pure synthetic metadata/resolution methods.
s=ns['Scanner'](base);s.resolve=lambda p:('/trusted/test.ttf',None)
# Structural view comparator above covers missing/added paths; test the actual
# per-font stat gate by a synthetic stat result without touching any path.
class Stat:
    st_dev=1;st_ino=2;st_mode=33188;st_uid=0;st_gid=0;st_nlink=1;st_size=8;st_mtime_ns=9;st_ctime_ns=10
metadata=ns['metadata'](Stat());ns['os'].lstat_orig=ns['os'].lstat
try:
    ns['os'].lstat=lambda p:Stat()
    s.resolve=lambda p:('/trusted/test.ttf',Stat())
    reject('scanner refuses changed font metadata before reuse',lambda:s.add('/usr/share/fonts/test.ttf'))
finally:
    ns['os'].lstat=ns['os'].lstat_orig;del ns['os'].lstat_orig
# Isolated own scratch descriptor controls use synthetic bytes only. No real
# font/config files are modified, resolved or loaded.
with tempfile.TemporaryDirectory(prefix='fd-control-',dir=p.parent.parent/'work') as temp:
    root=pathlib.Path(temp);(root/'dir').mkdir();(root/'dir/data').write_bytes(b'synthetic')
    ns['TRUSTED'].append(str(root));expected=ns['metadata']((root/'dir/data').stat())
    fd=ns['open_regular'](str(root/'dir/data'),expected)
    assert os.read(fd,9)==b'synthetic';os.close(fd)
    done.append({'name':'pinned no-symlink regular descriptor','status':'PASS'})
    (root/'leaf').symlink_to(root/'dir/data');(root/'ancestor').symlink_to(root/'dir',target_is_directory=True)
    def reject_os(name,call):
        try:call()
        except (OSError,ns['Refusal']):done.append({'name':name,'status':'PASS'})
        else:raise AssertionError(name+' accepted')
    reject_os('leaf symlink refused before data read',lambda:ns['open_regular'](str(root/'leaf'),expected))
    reject_os('ancestor symlink refused before data read',lambda:ns['open_regular'](str(root/'ancestor/data'),expected))
    wrong=dict(expected);wrong['ino']+=1
    reject('wrong inode refused before data read',lambda:ns['open_regular'](str(root/'dir/data'),wrong))
    ns['TRUSTED'].pop()
print(json.dumps({'status':'PASS','checks':done,'count':len(done),'effects':'in-memory controls plus isolated synthetic own-scratch descriptor controls; no real font/config writes, process loading or engine calls'},sort_keys=True,indent=2))
