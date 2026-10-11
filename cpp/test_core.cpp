#include "execution_core.hpp"
#include "spsc_ring.hpp"
#include <atomic>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <thread>
namespace {
void ring_basic(){
  sentinel::SpscRing<int,8> q; int x=-1; assert(!q.try_pop(x));
  for(int i=0;i<8;++i)assert(q.try_push(i)); assert(!q.try_push(9));
  for(int i=0;i<8;++i){assert(q.try_pop(x));assert(x==i);} assert(!q.try_pop(x));
}
void ring_threaded(){
  constexpr std::uint64_t n=500000; sentinel::SpscRing<std::uint64_t,1024> q;
  std::atomic<bool> ok{true};
  std::thread p([&](){for(std::uint64_t i=0;i<n;++i)while(!q.try_push(i))std::this_thread::yield();});
  for(std::uint64_t i=0;i<n;++i){std::uint64_t x=0;while(!q.try_pop(x))std::this_thread::yield();if(x!=i)ok=false;}
  p.join(); assert(ok.load());
}
void debouncer(){
  sentinel::DynamicDebouncer d(100000,2000000,5.0);
  assert(d.accept(1000000,100.0)); assert(!d.accept(1010000,100.0));
  assert(d.accept(1200000,100.0)); assert(!d.accept(1300000,98.0));
  assert(d.blocked_until_ns()==3300000); assert(!d.accept(2000000,98.0)); assert(d.accept(3300000,98.0));
}
void oco(){
  sentinel::OcoStopLimit q(100,25,5);
  assert(std::abs(q.stop_price()-99.75)<1e-10);
  assert(std::abs((q.stop_price()-q.limit_price())/q.stop_price()*10000-5)<1e-8);
  assert(!q.observe(100)); assert(q.observe(99.72)); assert(q.triggered()); assert(q.marketable()); assert(!q.observe(100.6));
  sentinel::OcoStopLimit gap(100,25,5); assert(gap.observe(98.2)); assert(gap.triggered()); assert(!gap.marketable());
}
}
int main(){ring_basic();ring_threaded();debouncer();oco();std::cout<<"All C++ core tests passed.\n";}
