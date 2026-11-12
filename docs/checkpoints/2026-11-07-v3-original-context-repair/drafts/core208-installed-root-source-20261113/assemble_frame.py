"""Finite source assembly only; never imports or invokes any live workflow."""
from pathlib import Path
import ast,hashlib,json,re,textwrap,difflib
B=Path(__file__).parent
OLD=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/drafts/core207-installed-root-source-20261112')
OLD207='/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112'
OLD206='/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT206-ROOT-SOURCE-AFTER205-20261112'
W=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112')
S207='/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112'
S206='/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112'
LAYER='inbound-turn-log-metadata-after-source207'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(n,v):
 p=B/n;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);p.write_bytes(v.encode()if isinstance(v,str)else v);p.chmod(0o600)
comp=json.loads((W/'NATIVE208-PROSPECTIVE-COMPOSITION.json').read_bytes())['expected_inventory']
AFTER=hashlib.sha256(raw(comp)).hexdigest()
replacements=[
('f06-modern-odt-authenticated-profile-after-source206','@LAYER@'),
(OLD207,'@NEWFRAME@'),(OLD206,'@OLD207FRAME@'),
(S207,'@NEWPROJECT@'),(S206,'@OLDPROJECT@'),
('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112',str(W)),
('faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b','@AFTER@'),
('253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21','@BEFORE@'),
('e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39','c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'),
('be6ae04a4a463e319fd050a2d9cb4bcaa9ea23e1a29b0d942c73f519850751cb','f09987fe57e3138e04160c74ba679c817e6f74313f210e867234c011a6f422ed'),
('489f6a23a4015bbb1daad9c405028b83e55b10725cd4f5e8b56ce678ee6e1eb9','d6c68fb6350d2f97b94d8f2f07694858ac1e3e67bbd30f8ca646537495e66601'),
('frw-astra-native207-install-after206-20261112.service','frw-astra-native208-install-after207-20261113.service')]
def transform(s):
 for a,b in replacements:s=s.replace(a,b)
 # Namespace/count substitutions do not touch hex digests.
 s=re.sub(r'(?<![0-9a-f])207(?![0-9a-f])','@N208@',s)
 s=re.sub(r'(?<![0-9a-f])206(?![0-9a-f])','207',s)
 s=s.replace('@N208@','208')
 # Embedded identifiers and state literals need their explicit spellings.
 for a,b in [('native207','native208'),('NATIVE207','NATIVE208'),('root207','root208'),('Root207','Root208'),('core207','core208'),('Core207','Core208'),('CORE207','CORE208'),('EXACT207','EXACT208'),('CURRENT206','CURRENT207'),('actual206','actual207'),('accepted206','accepted207'),('current206','current207'),('OLD206','OLD207'),('native206','native207'),('NATIVE206','NATIVE207'),('ROOT-206','ROOT-207'),('F206','F207'),('INPUT206','INPUT207')]:s=s.replace(a,b)
 s=s.replace('project495','@P497@').replace('PROJECT495','@UP497@').replace('project493','project495').replace('PROJECT493','PROJECT495').replace('@P497@','project497').replace('@UP497@','PROJECT497')
 s=re.sub(r'\b495\b','@C497@',s);s=re.sub(r'\b493\b','495',s);s=s.replace('@C497@','497')
 for a,b in [('@LAYER@',LAYER),('@NEWFRAME@',str(B)),('@OLD207FRAME@',OLD207),('@NEWPROJECT@',str(W)),('@OLDPROJECT@',S207),('@AFTER@',AFTER),('@BEFORE@','faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b')]:s=s.replace(a,b)
 return s

def guarded(s,constants):
 """Hoist only imports, definitions, and declared inert constants; live program to main.
 Safety function bodies are byte-for-byte source segments, not regenerated AST.
 Module globals are preserved for original function semantics and globals() guards.
 """
 tree=ast.parse(s);module=[];body=[];assigned=set()
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) or (isinstance(node,(ast.Import,ast.ImportFrom)) and not (isinstance(node,ast.ImportFrom) and node.module.split('.')[0] in {'scripts','hermes_cli'})):
   module.append(ast.get_source_segment(s,node));continue
  if isinstance(node,ast.Expr)and isinstance(node.value,ast.Constant)and isinstance(node.value.value,str):module.insert(0,repr(node.value.value));continue
  names={t.id for t in ast.walk(node)if isinstance(t,ast.Name)and isinstance(t.ctx,ast.Store)}
  if isinstance(node,(ast.Assign,ast.AnnAssign))and names and names<=constants:
   module.append(ast.get_source_segment(s,node));continue
  body.append(ast.get_source_segment(s,node))
  assigned|=names
  for t in ast.walk(node):
   if isinstance(t,(ast.Import,ast.ImportFrom)):
    assigned|={a.asname or(a.name.split('.')[0]if isinstance(t,ast.Import)else a.name)for a in t.names}
 # Imports under live-body may supply globals used by preserved functions.
 # Nested definitions (prove) are referenced only inside main but global is harmless.
 main='def main():\n    global '+', '.join(sorted(assigned))+'\n'+textwrap.indent('\n\n'.join(body),'    ')+'\n'
 return '\n\n'.join(module)+'\n\n'+main+'\nif __name__ == "__main__":\n    main()\n'

def main():
 import sys
 if sys.argv[1:]!=['--assemble-source-only']:raise ValueError('explicit_finite_source_assembly_mode_required')
 for old,new in [('boundary_contract.py','boundary_contract.py'),('native_scope.py','native_scope.py'),('f06-207-first-actual-root.py','core208-first-actual-root.py'),('start_core207_once.py','start_core208_once.py'),('run_native207_once.py','run_native208_once.py'),('resume_native207_services.py','resume_native208_services.py')]:
  s=transform((OLD/old).read_text())
  s=s.replace('f06-208-first-actual-root.py','core208-first-actual-root.py').replace('@OLD208FRAME@',OLD207).replace('native208-install-after208-20261113','native208-install-after207-20261113').replace('new_future207_budgets','new_future208_budgets').replace('committed206to208','committed207to208')
  if new=='boundary_contract.py':s=s.replace('modern208_accepted_source_only_not_runtime_qualified','logging208_accepted_source_only_not_runtime_qualified')
  if new=='core208-first-actual-root.py':
   s=s.replace("op = load(F207/'ROOT-NATIVE208-LIVE-OPERATION.json')","op = load(F207/'ROOT-NATIVE207-LIVE-OPERATION.json')").replace("op['state'] == 'NATIVE208_PROJECT495_FRESH_PERMANENT_SERVICES_RUNNING'","op['state'] == 'NATIVE207_PROJECT495_FRESH_PERMANENT_SERVICES_RUNNING'")
   s=s.replace("projection['selected_target_count'] == 7", "projection['selected_target_count'] == 8").replace('exact208_sevenCAS_required','exact208_eightCAS_required')
   s=s.replace("reference='8d392e47c27e9d09d97645e50d2690c087b5c7f3'","reference='36459e940d4cef1fa621fd0459543fbfd5d28961'")
   s=s.replace('explicit_singlelayer_canonical207_builder_required','explicit_singlelayer_canonical207_builder_required')
   s=s.replace("scope='Genuine committed207to208 future source-install boundary; no user/model/Office replay'","scope='Genuine committed207to208 future logging source-install boundary; no user/model/Office replay'")
  if new=='run_native208_once.py':
   s=s.replace("assert len(targets) == 1", "assert len(targets) == 2")
   s=s.replace("bound['selected_target_count'] == 7", "bound['selected_target_count'] == 8")
   s=s.replace("'friday.current-source-native-successor.v9'","'friday.current-source-native-successor.v10'")
   s=s.replace("'c38e23cde1bdbffbc8935fa63d59ecf9e57b5e27a722b8734205eb79a83da1b4'","'ROOT208_METADATA_HASH_TO_FINALIZE'")
   s=s.replace("'6dbe37a87da611c07c98c0f624b8fb248b298505409d6f24fc1ace1c8ac18983'",repr(sha(W/'publication/friday_v3_layer_publication.py')))
   s=s.replace("'17b4ad3652f2649d01a88506f5aaf27cceb7d7acea07db34a61961375ff54555'","'ROOT208_RECOVERY_HASH_TO_FINALIZE'")
   constants={'B','H','N','P','C','CP','RESTORE','REQ','PY','GW','DASH','PUB','now','sha','SOURCE_ACCEPTANCE','SPEC','ADMISSION','J'}
   s=guarded(s,constants)
  if new=='resume_native208_services.py':s=guarded(s,{'B','H','N','GW','DASH','PUB','J','now','sha'})
  put(new,s)
 observer=guarded((OLD/'admission-retained/observe-current-retained-units.py').read_text().replace("sys.dont_write_bytecode=True;","assert __debug__ and sys.flags.isolated and sys.dont_write_bytecode and sys.argv[1:]==['--observe-readonly-retained-once'], 'explicit_isolated_readonly_observer_required'\nsys.dont_write_bytecode=True;"),set())
 put('admission-retained/observe-current-retained-units.py',observer)
 for name in ['build-layer-publication-request.py','friday_v3_layer_publication.py']:put('publication/'+name,(W/'publication'/name).read_bytes())
 # Rebind observer final source pin in new actor only; retained program semantics unchanged.
 a=(B/'run_native208_once.py').read_text().replace("str(B / 'admission-retained/observe-current-retained-units.py')],","str(B / 'admission-retained/observe-current-retained-units.py'), '--observe-readonly-retained-once'],").replace('c719860c492f9ae2eb88c6267905d06aac338fec97f05f12bbd2c787e043d6d5',sha(B/'admission-retained/observe-current-retained-units.py'))
 put('run_native208_once.py',a)
 put('PROSPECTIVE208-PROJECTION.json',raw({'state':'PROJECTION_ONLY_NOT_INSTALLED','expected_receipt_sha256':AFTER,'source_composition':{'path':str(W/'NATIVE208-PROSPECTIVE-COMPOSITION.json'),'sha256':sha(W/'NATIVE208-PROSPECTIVE-COMPOSITION.json')},'counts':{'layers':208,'project':497,'native':17891,'base':17730,'plugins':52},'native_modified':2,'native_untouched':17889,'selected_CAS':8}))
 print(json.dumps({'state':'SOURCE_ASSEMBLED_NOT_EXECUTED','expected_receipt_sha256':AFTER}))

if __name__=="__main__":main()
