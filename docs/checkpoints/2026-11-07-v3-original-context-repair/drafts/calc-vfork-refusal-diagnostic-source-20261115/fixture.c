#include <unistd.h>
#include <sys/wait.h>
#include <stdlib.h>
__attribute__((noinline)) static int frw_fixture_boundary(void) {
 pid_t p=vfork();
 if(p==0) _exit(0);
 if(p<0) return 3;
 int status=0; return waitpid(p,&status,0)==p ? 0:4;
}
int main(void) { return frw_fixture_boundary(); }
