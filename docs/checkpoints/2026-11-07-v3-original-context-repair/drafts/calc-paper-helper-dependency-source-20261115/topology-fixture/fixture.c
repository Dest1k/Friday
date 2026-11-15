#include <stdio.h>
#include <sys/wait.h>

int main(void) {
    static const char command[] = "paperconf 2>/dev/null";
    unsigned char output[1024];
    puts("FRW_POPEN_BEGIN");
    fflush(stdout);
    FILE *pipe = popen(command, "r");
    if (pipe == NULL) return 90;
    size_t n = fread(output, 1, sizeof(output), pipe);
    int read_error = ferror(pipe) != 0;
    int status = pclose(pipe);
    printf("FRW_POPEN_RESULT bytes=%zu read_error=%d status=%d exited=%d exit_code=%d hex=",
           n, read_error, status, status >= 0 && WIFEXITED(status),
           status >= 0 && WIFEXITED(status) ? WEXITSTATUS(status) : -1);
    for (size_t i = 0; i < n; i++) printf("%02x", output[i]);
    putchar('\n');
    fflush(stdout);
    return read_error || n == sizeof(output) || status < 0 ||
           !WIFEXITED(status) || WEXITSTATUS(status) != 0 ? 91 : 0;
}
