/* SOURCE / static compilation only. No system GpgME/GnuPG or user content.
 * Root may separately qualify exact compiled fixtures in an admitted window.
 * Every final executable is another copy of this owned fixture, never gpg.
 * Build two separate programs with -DFIXTURE_HELPER or -DFIXTURE_PARENT.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#ifdef FIXTURE_HELPER
static int write_all(int fd, const char *text) {
    size_t left = strlen(text);
    while (left) {
        ssize_t n = write(fd, text, left);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        text += n;
        left -= (size_t)n;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 90;
#ifdef FIXTURE_EXTRA_DESCENDANT
    /* Same permitted argv, a separately pinned deliberately bad helper ELF. */
    pid_t descendant = fork();
    if (!descendant) _exit(0);
    if (descendant < 0 || waitpid(descendant, 0, 0) < 0) return 98;
#endif
#ifdef FIXTURE_NONZERO
    return 9;
#endif
    if (!strcmp(argv[1], "--list-dirs"))
        return write_all(1, "homedir:/tmp/friday-metric-work/tmp/.gnupg\n") ? 91 : 0;
    if (!strcmp(argv[1], "--list-components"))
        return write_all(1, "owned-fixture:metadata-only:/owned-fixture/helper\n") ? 91 : 0;
    if (!strcmp(argv[1], "--version"))
        return write_all(1, "owned-engine-fixture 1.0\n") ? 91 : 0;
    if (!strcmp(argv[1], "--negative-nonzero")) return 9;
    if (!strcmp(argv[1], "--negative-extra-fork")) {
        pid_t extra = fork();
        if (!extra) _exit(0);
        if (extra < 0) return 92;
        return waitpid(extra, 0, 0) < 0 ? 93 : 0;
    }
    if (!strcmp(argv[1], "--negative-discovery-full-buffer")) {
        char bytes[1024];
        memset(bytes, 'X', sizeof bytes - 1); bytes[sizeof bytes - 1] = 0;
        return write_all(1, bytes) ? 91 : 0;
    }
    return 94;
}
#endif

#ifdef FIXTURE_PARENT
static int standard_spawn(const char *path, char *const args[], int writer) {
    pid_t intermediate = fork();
    if (intermediate < 0) return -1;
    if (!intermediate) {
        pid_t final = fork();
        if (!final) {
            int nullfd;
            for (int fd = 0; fd < 4096; ++fd) if (fd != writer) close(fd);
            if (dup2(writer, 1) < 0) _exit(8);
            if (writer != 1) close(writer);
            nullfd = open("/dev/null", O_RDWR);
            if (nullfd < 0 || dup2(nullfd, 0) < 0 || dup2(nullfd, 2) < 0) _exit(8);
            if (nullfd > 2) close(nullfd);
            execv(path, args);
            _exit(8);
        }
        _exit(final < 0 ? 1 : 0);
    }
    int status = -1;
    if (waitpid(intermediate, &status, 0) != intermediate) return -1;
    close(writer);
    return WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 0 : -1;
}

int main(int argc, char **argv) {
    /* Path is Root's exact owned helper; source has no default executable. */
    if (argc != 3 || argv[1][0] != '/') return 95;
    int descriptors[2];
    if (pipe(descriptors) < 0) return 96;
    char *args[] = {argv[1], argv[2], 0};
    if (standard_spawn(argv[1], args, descriptors[1])) return 97;
    char bytes[1024];
    size_t used = 0;
    while (used < sizeof bytes - 1) {
        ssize_t n = read(descriptors[0], bytes + used, sizeof bytes - 1 - used);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) break;
        used += (size_t)n;
        if (!strcmp(argv[2], "--version") && memchr(bytes, '\n', used)) break;
    }
    close(descriptors[0]);
    return 0;
}
#endif
