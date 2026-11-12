import ast,copy,hashlib,json,os,re
from pathlib import Path
os.umask(0o077)
B=Path(__file__).resolve().parent;S=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112');W=B/'gates';W.mkdir(mode=0o700,exist_ok=True)
def write(p,s):p.parent.mkdir(mode=0o700,exist_ok=True,parents=True);p.write_text(s);p.chmod(0o600)
def shift(s):
 d={'EIGHTH':'NINTH','Eighth':'Ninth','eighth':'ninth','SEVENTH':'EIGHTH','Seventh':'Eighth','seventh':'eighth','SIXTH':'SEVENTH','Sixth':'Seventh','sixth':'seventh'}
 s=re.sub('|'.join(d),lambda m:d[m.group()],s)
 return re.sub(r'\b(203|204|205|206)\b|CP(203|204|205|206)|project(205|206)|leaf(491|493)|project(491|493)',lambda m:str(int(m[0])+1) if m[1] else ('CP'+str(int(m[2])+1) if m[2] else ('project'+str(int(m[3])+1) if m[3] else ('leaf'+str(int(m[4])+2) if m[4] else 'project'+str(int(m[5])+2)))),s)
s=shift((S/'ordinary-edge/check_eighth.py').read_text())
s=s.replace("P=Path('/home/jericho/.cache/FRW-SOL-V3-F06-COHERENT205-SOURCE-COMPOSITION-20261112/SOURCE-PINS.json');pins=json.loads(P.read_bytes())", "P=B.parent/'FINAL-NATIVE-SPEC.json';pins=json.loads(P.read_bytes())")
s=s.replace("pins['files']", "pins['native_files']").replace("r['after_sha256']", "r['sha256']").replace("r['after_bytes']", "r['bytes']")
s=s.replace("len(O.CURRENT_SOURCE_NINTH_NATIVE)==11", "len(O.CURRENT_SOURCE_NINTH_NATIVE)==1")
s=s.replace("for n in range(489)", "for n in range(491)")
s=s.replace("friday.current-source-native-successor.v9'", "friday.current-source-native-successor.v10'") # Only future rejection literals; active uses constants.
s=s.replace("actual_edge_refuses_v9", "actual_edge_refuses_v10")
s=s.replace('CP205/CP206','CP206/CP207').replace('installed_layers=205','installed_layers=206')
write(B/'ordinary-edge/check_ninth.py',s)
for p in (S/'gate-preparation/controls').glob('*.py'):write(W/'controls'/p.name,p.read_text())
# Ninth edge derives the existing whole-consumer operation, with ONE existing native target.
s=shift((S/'gate-preparation/controls/eighth_edge.py').read_text())
# Variable identifiers carry edge ordinal numbers; advance only known identities.
s=re.sub(r'\b(P7|F7|O7|q7|tx7|leaf7|lp7|leaf8|lp8|q8|tx8)\b',lambda m:re.sub(r'\d',lambda n:str(int(n[0])+1),m[0]),s)
s=s.replace("range(1,9)","range(1,10)").replace("(7,8)","(8,9)")
s=s.replace('native_count==11','native_count==1').replace('==17','==7').replace('==493','==495').replace('installed_layers=205','installed_layers=206')
s=s.replace('len(txs)==7','len(txs)==8').replace('len(rec[\'layers\'])==206',"len(rec['layers'])==207")
s=s.replace('schemas[i]', 'schemas[i]')
s=s.replace("schema='friday.current-source-native-successor.v9'", "schema='friday.current-source-native-successor.v10'")
s=s.replace("schema='friday.current-source-native-successor.v8'", "schema='friday.current-source-native-successor.v9'")
s=s.replace("('ninth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v9'))", "('tenth_schema',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v10'))")
s=s.replace("for label,schema in [('v9','friday.current-source-native-successor.v9'),('v8','friday.current-source-native-successor.v8')", "for label,schema in [('v10','friday.current-source-native-successor.v10'),('v9','friday.current-source-native-successor.v9')")
s=s.replace('installed_layers=206,installed_files=17891)\n        bad', 'installed_layers=207,installed_files=17891)\n        bad')
s=s.replace("P8.rename(T/'retired-project206')", "P8.rename(T/'retired-project206')")
s=s.replace('==7891','==17891').replace('==7730','==17730')
s=s.replace('all 17 declared','all 7 declared').replace('All seven ancestral','All eight ancestral').replace('bounded v8','bounded v9').replace('oldv7','oldv8').replace('finalv8','finalv9').replace('exact_v8','exact_v9').replace('new_v8','new_v9').replace('all_eight_canonical','all_nine_canonical').replace('all_seven_original','all_eight_original').replace('seven_real_predecessors','eight_real_predecessors').replace('request206.json','request207.json')
# Source206's eighth edge later retires its parent205; ninth receives only existing current206.
write(W/'controls/ninth_edge.py',s)
s=(W/'controls/eighth_edge.py').read_text()
s=s.replace('    if not args.eighth_rollback:', '    if not args.eighth_rollback and not args.reuse_eighth_negatives:')
# Reuse old negative matrix only; all eighth positives and CP.run still execute.
s=s.replace('    return {\'state\':\'PASS\'', "    from ninth_edge import run_ninth_edge\n    ninth=run_ninth_edge(locals(),e,env)\n    return {'ninth_edge':ninth,'state':'PASS'",1)
write(W/'controls/eighth_edge.py',s)
s=(W/'controls/check_current_source_edges.py').read_text()
needle="parser.add_argument('--eighth-rollback',action='store_true')"
s=s.replace(needle,needle+"\nparser.add_argument('--reuse-eighth-negatives',action='store_true')\n"+"\n".join("parser.add_argument('--ninth-"+suffix+"',type=Path,required=True)" for suffix in ('helpers-root','layer-root','native-before','native-after','native-spec'))+"\nparser.add_argument('--ninth-rollback',action='store_true')")
s=s.replace('if args.seventh_rollback or', 'if args.eighth_rollback or args.seventh_rollback or')
s=s.replace("select --eighth-rollback", "select --ninth-rollback")
write(W/'controls/check_current_source_edges.py',s)
write(W/'source_guard.py',(S/'gate-preparation/source_guard.py').read_text())
