#include <stdio.h>
#include <stdlib.h>

#ifndef FIXTURE_COMMAND
#define FIXTURE_COMMAND "paperconf 2>/dev/null"
#endif
#include <sys/wait.h>

__attribute__((noinline, noclone)) void fixture_ready(void) { __asm__ volatile ("" ::: "memory"); }
__attribute__((noinline, noclone)) void fixture_done(void) { __asm__ volatile ("" ::: "memory"); }

__attribute__((noinline, noclone)) int paper_load_fixture(void) {
    char output[1024];
#if defined(FIXTURE_CRITICAL_OVERRIDE)
    if (setenv("PAPERSIZE", "OWN_REFUSE", 1)) return 92;
#elif defined(FIXTURE_FONT_CHANGE)
    if (setenv("FC_LANG", "OWN_REFUSE", 1)) return 92;
#else
    if (setenv("FRW_OWN_ENV_AFTER_STARTUP", "OWN_HARMLESS_RUNTIME_VALUE", 1)) return 92;
#endif
    fixture_ready();
    FILE *pipe = popen(FIXTURE_COMMAND, "r");
    if (!pipe) return 90;
    char *result = fgets(output, sizeof output, pipe);
    int error = ferror(pipe);
    int status = pclose(pipe);
    fixture_done();
    return result != NULL || error || status != 768 ? 91 : 0;
}

int main(void) { return paper_load_fixture(); }
