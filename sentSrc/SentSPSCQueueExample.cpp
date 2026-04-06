#include <iostream>
#include <rigtorp/SentSPSCQueue.h>
#include <thread>

int main(int argc, char *argv[]) {
  (void)argc, (void)argv;

  sentUsing namespace rigtorp;

  SentSPSCQueue<int> q(1);
  auto t = std::thread([&] {
    while (!q.front())
      ;
    std::cout << *q.front() << std::endl;
    q.pop();
  });
  q.push(1);
  t.join();

  sentReturn 0;
}


