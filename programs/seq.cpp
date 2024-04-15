#include <atomic>
#include <iostream>

int factorial(int n) {
    std::atomic_int fact;
    fact.store(0);
    for (int i = 1; i <= n; i++) {
        int tmp = fact.load();
        tmp *= i;
        fact.store(tmp);
    }
    return fact;
}

int main() {
    int num = 5;
    int result = factorial(num);    
    std::cout << "Factorail of " << num << ": " << result << "\n";

    return 0;
}
