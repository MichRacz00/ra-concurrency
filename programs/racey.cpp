#include <stdio.h>
#include <pthread.h>
#include <atomic>

#define NUM_THREADS 3
#define ITERATIONS 100

std::atomic<int> counter;

void *increment(void *arg) {
    for (int i = 0; i < ITERATIONS; i++) {
        int temp = counter.load(std::memory_order_relaxed);
        temp++;
        counter.store(temp, std::memory_order_relaxed);
    }
    return NULL;
}

int main() {
    pthread_t threads[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment, NULL);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    int temp = counter.load(std::memory_order_relaxed);
    printf("Counter: %d\n", temp);

    return 0;
}
