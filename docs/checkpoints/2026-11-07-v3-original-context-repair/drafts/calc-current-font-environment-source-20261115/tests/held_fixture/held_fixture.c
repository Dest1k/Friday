#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

/* These are own-fixture control markers, not font-width calls or UNO state. */
#define MARKER __attribute__((noinline, noclone))
MARKER void fixture_ready(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_paper_done(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_after_load(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_query_marker(unsigned index) { __asm__ volatile ("" :: "r"(index) : "memory"); }
MARKER void fixture_restore_marker(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_close_marker(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_after_close(void) { __asm__ volatile ("" ::: "memory"); }

MARKER int paper_load_fixture(void) {
    char output[1024];
    if (setenv("FRW_OWN_ENV_AFTER_STARTUP", "OWN_HARMLESS_RUNTIME_VALUE", 1)) return 92;
    fixture_ready();
    FILE *pipe = popen("paperconf 2>/dev/null", "r");
    if (!pipe) return 90;
    char *result = fgets(output, sizeof output, pipe);
    int error = ferror(pipe);
    int status = pclose(pipe);
    fixture_paper_done();
    return result != NULL || error || status != 768 ? 91 : 0;
}

static double monotonic_now(void) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) return -1;
    return now.tv_sec + now.tv_nsec / 1000000000.0;
}

static int wait_for_fixture_advance(const char *path, double deadline) {
    /* Root owns both this exact writable directory and the outer cgroup clock.
       Reading this fixture-only gate performs no handshake or environment read. */
    struct timespec delay = {0, 1000000};
    while (access(path, F_OK)) {
        if (errno != ENOENT || monotonic_now() <= 0 || monotonic_now() >= deadline) return 93;
        nanosleep(&delay, NULL);
    }
    return 0;
}

int main(int argc, char **argv) {
    char *tail = NULL;
    if (argc != 2) return 94;
    double deadline = strtod(argv[1], &tail);
    if (!tail || *tail || !(deadline > monotonic_now())) return 94;
    int status = paper_load_fixture();
    if (status) return status;
#if defined(FIXTURE_AFTER_LOAD_FONT_CHANGE)
    if (setenv("FC_LANG", "FRW_OWN_HELD_AFTER_LOAD", 1)) return 92;
#endif
    fixture_after_load();
    status = wait_for_fixture_advance("/tmp/friday-metric-work/own-fixture-loaded-go", deadline);
    if (status) return status;
    for (unsigned i = 0; i < 10; i++) fixture_query_marker(i);
    fixture_restore_marker();
    fixture_close_marker();
#if defined(FIXTURE_AFTER_CLOSE_FONT_CHANGE)
    if (setenv("FC_LANG", "FRW_OWN_HELD_AFTER_CLOSE", 1)) return 92;
#endif
    fixture_after_close();
    return wait_for_fixture_advance("/tmp/friday-metric-work/own-fixture-closed-go", deadline);
}
