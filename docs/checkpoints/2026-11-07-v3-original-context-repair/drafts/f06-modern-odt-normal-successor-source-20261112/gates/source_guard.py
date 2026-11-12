"""Own-root filesystem and exact git-apply process boundary for dormant gates."""
import os,sys
from pathlib import Path


def install_guard(own_root,run_root):
    own=Path(own_root).resolve(strict=True);runs=Path(run_root).resolve()
    if not runs.is_relative_to(own/'runs'):raise ValueError('run outside own runs root')
    def path_checked(path,dir_fd=None,*,follow=True):
        if isinstance(path,int):
            target=Path('/proc/self/fd')/str(path)
        else:
            path=Path(os.fsdecode(path))
            if path.is_absolute():target=path
            elif dir_fd is not None and dir_fd!=-1:target=Path('/proc/self/fd')/str(dir_fd)/path
            else:target=Path.cwd()/path
        # Mutation of an own symlink itself is legal (negative-control cleanup).
        actual=target.resolve() if follow else target.parent.resolve()/target.name
        if not actual.is_relative_to(own):raise PermissionError('fixture_write_outside_ownroot')
    def audit(event,values):
        if event.startswith(('socket.','os.exec','os.spawn','os.posix_spawn','os.fork')) or event=='os.system':
            raise PermissionError('fixture_no_live_effect:'+event)
        if event=='subprocess.Popen':
            executable,command,cwd,env=values
            if (type(command) is not list or len(command) not in (5,6)
                or command[:4]!=['git','--no-optional-locks','apply','--whitespace=nowarn']
                or (len(command)==6 and command[4]!='--check')
                or os.fsdecode(executable) not in ('git','/usr/bin/git') or cwd is None
                or not Path(cwd).resolve(strict=True).is_relative_to(runs)
                or not Path(command[-1]).resolve(strict=True).is_relative_to(runs)
                or type(env) is not dict or set(env)!={'GIT_CEILING_DIRECTORIES','PATH','HOME'}
                or Path(env['HOME']).resolve()!=Path(cwd).resolve().parent
                or env['GIT_CEILING_DIRECTORIES']!=env['HOME']):
                raise PermissionError('fixture_subprocess_not_exact_staged_git_apply')
        if event=='open' and values[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            path_checked(values[0])
        if event in ('os.mkdir','os.remove','os.rmdir'):
            path_checked(values[0],values[2] if event=='os.mkdir' else values[1],follow=False)
        if event in ('os.chmod','os.chown','os.utime'):
            path_checked(values[0],values[2] if event=='os.chmod' else values[-1])
        if event in ('os.rename','os.link'):
            path_checked(values[0],values[2],follow=False);path_checked(values[1],values[3],follow=False)
        if event=='os.symlink':
            # Both link object and its pointed-to location stay in ownroot.
            link=Path(values[1]);target=Path(values[0]);path_checked(link,values[2],follow=False)
            path_checked(target if target.is_absolute() else link.parent/target)
        if event in ('os.truncate','os.setxattr','os.removexattr'):
            path_checked(values[0])
    sys.addaudithook(audit)
    return {'write_root':str(own),'git_apply_cwd_root':str(runs),'network':'DENIED','other_processes':'DENIED'}
