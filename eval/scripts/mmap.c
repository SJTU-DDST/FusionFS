#include <stdio.h>
#include <sys/mman.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <time.h>
#include <errno.h>
#define PAGE_SIZE               4096

void delay(int number_of_seconds)
{
    // Converting time into milli_seconds
    int milli_seconds = 1000 * number_of_seconds;
 
    // Storing start time
    clock_t start_time = clock();
 
    // looping till required time is not achieved
    while (clock() < start_time + milli_seconds)
        ;
}

int main(int argc, char *argv[])
{
    int fd = open("/home/congyong/Odinfs/eval/benchmark/fxmark/bin/root/test.txt", O_CREAT | O_RDWR, S_IRWXU), err = 0;
    if (fd < 0)
    {
        printf("Error %d \n", errno);
        // return 1;
    }
    assert(fd > 0);

    char* ptr = mmap(NULL, PAGE_SIZE * 3, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    assert(ptr != MAP_FAILED);

    char ch;
    while (ch = getchar()) {
        // delay(1);
        if (ch == 'q') {
            break;
        }
        else if (ch == '1') {
            printf("1\n");
            ptr[0] = 'a';
            // for (size_t i = 0; i < 4096; i++)
            // {
            //     ptr[i] = 'a';
            // }
        }
        else if (ch == '2') {
            printf("2\n");
            ptr[4097] = 'b';
            // for (size_t i = 4097; i < 8192; i++)
            // {
            //     ptr[i] = 'b';
            // }
        } else if (ch == 'm') {
            printf("MSYNC\n");
            msync(ptr, 8192, MS_SYNC);
        } else if (ch == 'f') {
            printf("FSYNC\n");
            fsync(fd);
        }
    }

    err = munmap(ptr, PAGE_SIZE * 3);

    if (err != 0)
    {
        printf("UnMapping Failed\n");
        return 1;
    }
    close(fd);
    return 0;
}