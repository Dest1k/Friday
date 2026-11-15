#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <math.h>
#include <pthread.h>
#include <string.h>
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


/* Own markers only; e616 driver continues to observe only its original seven. */
MARKER void fixture_solib_before(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_solib_loaded(void) { __asm__ volatile ("" ::: "memory"); }
MARKER void fixture_solib_after(void) { __asm__ volatile ("" ::: "memory"); }

#define TRIGGER_PATH "/home/jericho/.cache/FRW-ASTRA-GDB-RETIRED-CHILD-BP-SOLIB-FIXTURE-20261115/trigger/frw_own_retired_bp_trigger.so"
#define TRIGGER_SYMBOL "frw_fixture_solib_probe"
#define TRIGGER_VALUE 0x46525731

/* Called only after paper_load_fixture returned success. Its paper_done marker
   therefore already ran the unchanged driver helper CLOSED/LOAD_CLOSED checks.
   A later fixture_after_load marker implies every check below succeeded.
   Root must recheck the pinned DSO bytes/identity and mount its stand read-only.
   No observed native event or breakpoint deletion is claimed by these markers. */
MARKER int fixture_late_solib(void) {
    fixture_solib_before();
    void *already = dlopen(TRIGGER_PATH, RTLD_NOW | RTLD_LOCAL | RTLD_NOLOAD);
    if (already != NULL) {
        (void)dlclose(already);
        return 95;
    }
    (void)dlerror();
    void *handle = dlopen(TRIGGER_PATH, RTLD_NOW | RTLD_LOCAL);
    if (handle == NULL) return 96;
    void *address = dlsym(handle, TRIGGER_SYMBOL);
    int (*probe)(void) = NULL;
    _Static_assert(sizeof(probe) == sizeof(address), "ELF x86-64 function pointer size");
    memcpy(&probe, &address, sizeof probe);
    if (address == NULL || dlerror() != NULL || probe() != TRIGGER_VALUE) {
        (void)dlclose(handle);
        return 97;
    }
    fixture_solib_loaded();
    if (dlclose(handle)) return 98;
    fixture_solib_after();
    return 0;
}

MARKER int run_fixture(double deadline) {
    int status = paper_load_fixture();
    if (status) return status;
    status = fixture_late_solib();
    if (status) return status;
    fixture_after_load();
    status = wait_for_fixture_advance("/tmp/friday-metric-work/own-fixture-loaded-go", deadline);
    if (status) return status;
    for (unsigned i = 0; i < 10; i++) fixture_query_marker(i);
    fixture_restore_marker();
    fixture_close_marker();
    fixture_after_close();
    return wait_for_fixture_advance("/tmp/friday-metric-work/own-fixture-closed-go", deadline);
}

#if defined(FIXTURE_WORKER_THREAD)
/* Main and sibling use the same absolute monotonic deadline as the worker.
   Holding this mutex until pthread_cond_timedwait atomically parks main means
   worker cannot pass its ready check before main has entered that wait. */
static pthread_mutex_t shape_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t shape_cond;
static int sibling_ready, main_parked, worker_done, stop_sibling, worker_status, sibling_error;
static struct timespec shape_deadline;
static double worker_deadline;

static int shape_wait(void) {
    return pthread_cond_timedwait(&shape_cond, &shape_mutex, &shape_deadline);
}

MARKER void *fixture_parked_sibling(void *unused) {
    (void)unused;
    if (pthread_mutex_lock(&shape_mutex)) return NULL;
    sibling_ready = 1;
    (void)pthread_cond_broadcast(&shape_cond);
    while (!stop_sibling) {
        if (shape_wait()) {
            if (!stop_sibling) sibling_error = 1;
            break;
        }
    }
    (void)pthread_mutex_unlock(&shape_mutex);
    return NULL;
}

MARKER void *fixture_worker(void *unused) {
    (void)unused;
    int status = 99;
    if (pthread_mutex_lock(&shape_mutex)) return NULL;
    while (!(sibling_ready && main_parked)) {
        if (shape_wait()) goto finish;
    }
    if (pthread_mutex_unlock(&shape_mutex)) return NULL;
    status = run_fixture(worker_deadline);
    if (pthread_mutex_lock(&shape_mutex)) return NULL;
finish:
    worker_status = status;
    worker_done = 1;
    stop_sibling = 1;
    (void)pthread_cond_broadcast(&shape_cond);
    (void)pthread_mutex_unlock(&shape_mutex);
    return NULL;
}

static int run_thread_shape(double deadline) {
    pthread_condattr_t attr;
    pthread_t sibling, worker;
    worker_deadline = deadline;
    shape_deadline.tv_sec = (time_t)deadline;
    shape_deadline.tv_nsec = (long)((deadline - shape_deadline.tv_sec) * 1000000000.0);
    if (pthread_condattr_init(&attr)) return 99;
    int error = pthread_condattr_setclock(&attr, CLOCK_MONOTONIC);
    if (!error) error = pthread_cond_init(&shape_cond, &attr);
    (void)pthread_condattr_destroy(&attr);
    if (error || pthread_mutex_lock(&shape_mutex)) return 99;
    if (pthread_create(&sibling, NULL, fixture_parked_sibling, NULL)) {
        (void)pthread_mutex_unlock(&shape_mutex);
        return 99;
    }
    while (!sibling_ready) {
        if (shape_wait()) {
            stop_sibling = 1;
            (void)pthread_cond_broadcast(&shape_cond);
            (void)pthread_mutex_unlock(&shape_mutex);
            (void)pthread_join(sibling, NULL);
            return 99;
        }
    }
    if (pthread_create(&worker, NULL, fixture_worker, NULL)) {
        stop_sibling = 1;
        (void)pthread_cond_broadcast(&shape_cond);
        (void)pthread_mutex_unlock(&shape_mutex);
        (void)pthread_join(sibling, NULL);
        return 99;
    }
    main_parked = 1;
    (void)pthread_cond_broadcast(&shape_cond);
    while (!worker_done) {
        if (shape_wait()) {
            stop_sibling = 1;
            (void)pthread_cond_broadcast(&shape_cond);
            (void)pthread_mutex_unlock(&shape_mutex);
            /* Failure path exits this entire fixture process; Root still owns
               hard whole-cgroup closure. No cancellation/resume is attempted. */
            return 99;
        }
    }
    int status = sibling_error ? 99 : worker_status;
    (void)pthread_mutex_unlock(&shape_mutex);
    if (pthread_join(worker, NULL) || pthread_join(sibling, NULL)) return 99;
    if (pthread_cond_destroy(&shape_cond) || pthread_mutex_destroy(&shape_mutex)) return 99;
    return status;
}
#endif

int main(int argc, char **argv) {
    char *tail = NULL;
    if (argc != 2) return 94;
    double deadline = strtod(argv[1], &tail);
    if (!tail || *tail || !isfinite(deadline) || !(deadline > monotonic_now())) return 94;
#if defined(FIXTURE_WORKER_THREAD)
    return run_thread_shape(deadline);
#else
    return run_fixture(deadline);
#endif
}
