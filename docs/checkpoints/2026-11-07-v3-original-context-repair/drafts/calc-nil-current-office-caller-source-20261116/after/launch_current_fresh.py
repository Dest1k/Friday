"""Root-only launcher: fork once before loading caller/heavy Python modules."""
import os,sys
if __name__ != '__main__':raise RuntimeError('launch_as_fresh_process_only')
if len(sys.argv)<2 or sys.argv[1] not in ('prepare','run'):raise SystemExit('usage: launch_current_fresh.py prepare|run [caller args]')
role=sys.argv[1]
child=os.fork()
if child:
 _,status=os.waitpid(child,0)
 raise SystemExit(os.waitstatus_to_exitcode(status))
# Non-tail child path starts here, before runpy/json/importlib/caller imports.
os.environ['FRW_NIL_FRESH_FORK_PID']=str(os.getpid())
os.environ['FRW_NIL_FRESH_FORK_PARENT']=str(os.getppid())
import runpy
script=__file__.rsplit('/',1)[0]+('/prepare_plan.py' if role=='prepare' else '/run_current_once.py')
sys.argv=[script]+sys.argv[2:]
runpy.run_path(script,run_name='__main__')
