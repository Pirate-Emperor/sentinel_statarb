#include "spsc_ring.hpp"
#include "execution_core.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
namespace {
using Clock=std::chrono::steady_clock;
constexpr std::size_t kCapacity=1U<<16;
struct Tick { std::uint64_t sequence=0,timestamp_ns=0; double bid=0.0,ask=0.0; double mid() const {return (bid+ask)*0.5;} };
struct Stats { std::uint64_t accepted=0,debounced=0,stop_triggers=0,invalid_ticks=0; bool stop_marketable=false; };
std::uint64_t percentile(std::vector<std::uint64_t> values,double p) {
  if(values.empty()) return 0;
  auto index=static_cast<std::size_t>(p*static_cast<double>(values.size()-1));
  std::nth_element(values.begin(),values.begin()+index,values.end()); return values[index];
}
int run(std::uint64_t count) {
  if(count<1) throw std::invalid_argument("--ticks must be positive");
  sentinel::SpscRing<Tick,kCapacity> queue;
  sentinel::DynamicDebouncer gate(100000,2000000,5.0);
  sentinel::OcoStopLimit order(100.0,25.0,5.0);
  Stats stats; std::vector<std::uint64_t> samples;
  const std::uint64_t warmup=std::min<std::uint64_t>(count/10,10000);
  const std::uint64_t stride=std::max<std::uint64_t>(1,count/20000);
  std::uint64_t consumed=0; Clock::time_point start{},stop{};
  std::thread producer([&queue,count](){
    std::uint64_t rng=0x9e3779b97f4a7c15ULL;
    for(std::uint64_t i=0;i<count;++i){
      rng=rng*6364136223846793005ULL+1442695040888963407ULL;
      const double noise=(static_cast<double>((rng>>33)%2001)-1000.0)/100000000.0;
      // Bounded normal regime plus one deliberate 180 bps gap.
      const double base=i>=count/2?98.2:100.0;
      const double price=base+noise;
      Tick t{i,i*10000ULL,price-0.005,price+0.005};
      while(!queue.try_push(t)) std::this_thread::yield();
    }
  });
  Tick t;
  while(consumed<count){
    if(!queue.try_pop(t)){std::this_thread::yield();continue;}
    if(t.bid<=0||t.ask<t.bid||!std::isfinite(t.mid())){++stats.invalid_ticks;++consumed;continue;}
    if(consumed==warmup) start=Clock::now();
    const bool sample=consumed>=warmup&&(consumed%stride==0);
    const auto event_start=sample?Clock::now():Clock::time_point{};
    if(order.observe(t.mid())){++stats.stop_triggers;stats.stop_marketable=order.marketable();}
    if(gate.accept(t.timestamp_ns,t.mid()))++stats.accepted;else ++stats.debounced;
    if(sample)samples.push_back(static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-event_start).count()));
    ++consumed;if(consumed==count)stop=Clock::now();
  }
  producer.join();
  if(count<=warmup){start=Clock::now();stop=start;}
  const double measured=static_cast<double>(count-warmup);
  const double elapsed=std::chrono::duration<double>(stop-start).count();
  std::cout<<"engine=sentinel_cpp_simulation\n"<<"ticks="<<count<<"\n"<<"warmup_ticks="<<warmup<<"\n"
    <<"measured_ticks="<<static_cast<std::uint64_t>(measured)<<"\n"
    <<"queue_lock_free_atomics="<<(queue.is_lock_free()?"true":"false")<<"\n"
    <<"signals_accepted="<<stats.accepted<<"\n"<<"signals_debounced="<<stats.debounced<<"\n"
    <<"stop_triggers="<<stats.stop_triggers<<"\n"<<"stop_limit_marketable_at_gap="<<(stats.stop_marketable?"true":"false")<<"\n"
    <<"invalid_ticks="<<stats.invalid_ticks<<"\n"<<std::fixed<<std::setprecision(2)
    <<"measured_throughput_events_per_second="<<(elapsed>0?measured/elapsed:0.0)<<"\n"<<std::setprecision(3)
    <<"sampled_processing_p50_us="<<percentile(samples,0.50)/1000.0<<"\n"
    <<"sampled_processing_p95_us="<<percentile(samples,0.95)/1000.0<<"\n"
    <<"sampled_processing_p99_us="<<percentile(samples,0.99)/1000.0<<"\n"<<"latency_sample_count="<<samples.size()<<"\n";
  return 0;
}
}
int main(int argc,char** argv) {
  try {
    std::uint64_t count=100000;
    for(int i=1;i<argc;++i){std::string arg(argv[i]);if(arg=="--ticks"&&i+1<argc)count=std::stoull(argv[++i]);
      else if(arg=="--help"){std::cout<<"Usage: sentinel_engine --ticks COUNT\n";return 0;}
      else throw std::invalid_argument("unknown argument: "+arg);}
    return run(count);
  } catch(const std::exception& e){std::cerr<<"error: "<<e.what()<<'\n';return 2;}
}
