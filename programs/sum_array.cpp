#include <stdio.h>
#include <pthread.h>

#define NUM_THREADS 2
#define ARRAY_SIZE 10

int totalSum = 0;

typedef struct {
    int *array;
    int start;
    int end;
} ThreadArgs;

void *calculateSum(void *arg) {
    ThreadArgs *args = (ThreadArgs *)arg;
    int *array = args->array;
    int start = args->start;
    int end = args->end;
    int partialSum = 0;

    for (int i = start; i <= end; i++) {
        partialSum += array[i];
    }

    __sync_fetch_and_add(&totalSum, partialSum);

    pthread_exit(NULL);
}

int main() {
    int array[ARRAY_SIZE] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    pthread_t threads[NUM_THREADS];
    ThreadArgs threadArgs[NUM_THREADS];

    int mid = ARRAY_SIZE / 2;
    threadArgs[0].array = array;
    threadArgs[0].start = 0;
    threadArgs[0].end = mid - 1;
    threadArgs[1].array = array;
    threadArgs[1].start = mid;
    threadArgs[1].end = ARRAY_SIZE - 1;

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, calculateSum, (void *)&threadArgs[i]);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("Total sum: %d\n", totalSum);

    return 0;
}
