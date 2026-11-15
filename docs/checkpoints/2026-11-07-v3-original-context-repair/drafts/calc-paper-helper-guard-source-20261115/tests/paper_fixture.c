#include <stdio.h>
#include <sys/wait.h>

__attribute__((noinline, noclone)) void fixture_ready(void) { __asm__ volatile ("" ::: "memory"); }
__attribute__((noinline, noclone)) void fixture_done(void) { __asm__ volatile ("" ::: "memory"); }

__attribute__((noinline, noclone)) int paper_load_fixture(void) {
    char output[1024];
    fixture_ready();
    FILE *pipe = popen("paperconf 2>/dev/null", "r");
    if (!pipe) return 90;
    char *result = fgets(output, sizeof output, pipe);
    int error = ferror(pipe);
    int status = pclose(pipe);
    fixture_done();
    return result != NULL || error || status != 768 ? 91 : 0;
}

int main(void) { return paper_load_fixture(); }
