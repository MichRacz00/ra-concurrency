//An example concurrent program without a datarace
#include <atomic>
#include <thread>
#include <mutex>
#include <iostream>
#define THREADS 2
#define ITERATIONS 4

std::atomic_int shared_data;
std::mutex mtx;

void increment_shared_data(int id, int increments) {
    for (int i = 0; i < increments; ++i) {
        mtx.lock();
        int tmp = shared_data.load() + 1;
        shared_data.store(tmp);
        mtx.unlock();
    }
}

int main() {
    std::thread threads[THREADS];
    shared_data.store(0);

    for (int i = 0; i < THREADS; ++i) {
        threads[i] = std::thread(increment_shared_data, i, ITERATIONS);
    }

    for (int i = 0; i < THREADS; ++i) {
        threads[i].join();
    }

    std::cout << "Sum is: " << shared_data << "\n";

    return 0;
}

