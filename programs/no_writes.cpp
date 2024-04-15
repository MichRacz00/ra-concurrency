//An example concurrent program without a datarace
#include <atomic>
#include <thread>
#include <iostream>
#define THREADS 2

std::atomic_int shared_data;

void print_shared_data(int id) {
    int tmp = shared_data.load();
    std::cout << "Shared val: " << tmp << "\n";
}

int main() {
    std::thread threads[THREADS];
    shared_data.store(100);

    for (int i = 0; i < THREADS; ++i) {
        threads[i] = std::thread(print_shared_data, i);
    }

    for (int i = 0; i < THREADS; ++i) {
        threads[i].join();
    }

    return 0;
}

