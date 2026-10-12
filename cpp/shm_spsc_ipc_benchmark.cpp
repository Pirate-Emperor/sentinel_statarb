// Measure lock-free process-to-process message handoff through shared memory.
// Intended for Linux runners; the report verifies whether the atomics are lock-free.
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <new>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include <signal.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

namespace {
using Clock = std::chrono::steady_clock;
constexpr std::size_t kCapacity = 4096;
static_assert(sizeof(std::atomic<std::uint64_t>) <= 64, "atomic must fit in one cache line");
struct Tick {
  std::uint64_t sequence=0;
  std::int64_t sent_ns=0;
};
struct alignas(64) SharedSpscQueue {
  std::atomic<std::uint64_t> head;
  char head_padding[64 - sizeof(std::atomic<std::uint64_t>)];
  alignas(64) std::atomic<std::uint64_t> tail;
  char tail_padding[64 - sizeof(std::atomic<std::uint64_t>)];
  alignas(64) Tick slots[kCapacity];
  SharedSpscQueue() : head(0), head_padding{}, tail(0), tail_padding{}, slots{} {}
  bool lock_free() const {
    return head.is_lock_free() && tail.is_lock_free();
  }
  bool try_push(const Tick& tick) {
    const auto h=head.load(std::memory_order_relaxed);
    const auto t=tail.load(std::memory_order_acquire);
    if(h-t>=kCapacity) return false;
    slots[h%kCapacity]=tick;
    head.store(h+1,std::memory_order_release);
    return true;
  }
  bool try_pop(Tick& tick) {
    const auto t=tail.load(std::memory_order_relaxed);
    const auto h=head.load(std::memory_order_acquire);
    if(t==h) return false;
    tick=slots[t%kCapacity];
    tail.store(t+1,std::memory_order_release);
    return true;
  }
};
struct Summary {
  int ok=0;
  int atomics_lock_free=0;
  std::uint64_t sample_count=0;
  std::uint64_t bad_sequences=0;
  std::uint64_t invalid_timestamps=0;
  double p50_us=0,p95_us=0,p99_us=0,max_us=0,mean_us=0;
  double throughput_messages_per_second=0,duration_ms=0;
};
void require(bool ok,const std::string& message) {
  if(!ok) throw std::runtime_error(message);
}
std::int64_t now_ns() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
      Clock::now().time_since_epoch()).count();
}
bool write_all(int fd,const void* data,std::size_t size) {
  const char* p=static_cast<const char*>(data);
  std::size_t written=0;
  while(written<size) {
    const ssize_t n=write(fd,p+written,size-written);
    if(n<=0) return false;
    written+=static_cast<std::size_t>(n);
  }
  return true;
}
bool read_all(int fd,void* data,std::size_t size) {
  char* p=static_cast<char*>(data);
  std::size_t got=0;
  while(got<size) {
    const ssize_t n=read(fd,p+got,size-got);
    if(n<=0) return false;
    got+=static_cast<std::size_t>(n);
  }
  return true;
}
double percentile(const std::vector<std::uint64_t>& values,double p) {
  if(values.empty())return 0.0;
  auto copy=values;
  const auto index=static_cast<std::size_t>(p*static_cast<double>(copy.size()-1));
  std::nth_element(copy.begin(),copy.begin()+index,copy.end());
  return static_cast<double>(copy[index])/1000.0;
}
int consume(SharedSpscQueue* queue,std::uint64_t count,std::uint64_t warmup,
            int ready_fd,int result_fd) {
  if(!queue->lock_free()) {
    const char no=0;(void)write_all(ready_fd,&no,1);
    close(ready_fd);close(result_fd);return 2;
  }
  const char yes=1;
  if(!write_all(ready_fd,&yes,1)) {close(ready_fd);close(result_fd);return 3;}
  close(ready_fd);
  std::vector<std::uint64_t> samples;
  samples.reserve(static_cast<std::size_t>(count-warmup));
  Summary out;
  out.atomics_lock_free=1;
  Clock::time_point start{},finish{};
  Tick tick{};
  for(std::uint64_t expected=0;expected<count;++expected) {
    while(!queue->try_pop(tick)) std::this_thread::yield();
    const auto received_ns=now_ns();
    if(tick.sequence!=expected) ++out.bad_sequences;
    if(tick.sent_ns<=0 || received_ns<tick.sent_ns) ++out.invalid_timestamps;
    if(expected>=warmup) {
      if(samples.empty()) start=Clock::now();
      finish=Clock::now();
      if(tick.sent_ns>0 && received_ns>=tick.sent_ns)
        samples.push_back(static_cast<std::uint64_t>(received_ns-tick.sent_ns));
    }
  }
  out.sample_count=samples.size();
  out.ok=(out.bad_sequences==0 && out.invalid_timestamps==0 &&
          samples.size()==static_cast<std::size_t>(count-warmup))?1:0;
  out.p50_us=percentile(samples,0.50);
  out.p95_us=percentile(samples,0.95);
  out.p99_us=percentile(samples,0.99);
  if(!samples.empty()) {
    out.max_us=static_cast<double>(*std::max_element(samples.begin(),samples.end()))/1000.0;
    std::uint64_t sum=0;
    for(auto v:samples)sum+=v;
    out.mean_us=static_cast<double>(sum)/static_cast<double>(samples.size())/1000.0;
  }
  const double duration=samples.size()>1?std::chrono::duration<double>(finish-start).count():0.0;
  out.duration_ms=duration*1000.0;
  out.throughput_messages_per_second=duration>0?static_cast<double>(samples.size())/duration:0.0;
  const bool wrote=write_all(result_fd,&out,sizeof(out));
  close(result_fd);
  return wrote&&out.ok?0:4;
}
std::string make_report(std::uint64_t messages,std::uint64_t warmup,const Summary& s) {
  std::ostringstream out;
  out<<std::fixed<<std::setprecision(3)
     <<"{\n"
     <<"  \"benchmark\": \"native_cpp_process_shared_spsc_one_way\",\n"
     <<"  \"transport\": \"MAP_SHARED SPSC ring between producer and consumer processes\",\n"
     <<"  \"measurement\": \"Producer monotonic timestamp to consumer pop; same host clock; no sockets\",\n"
     <<"  \"warmup_messages\": "<<warmup<<",\n"
     <<"  \"measured_messages\": "<<messages<<",\n"
     <<"  \"payload_check\": \""<<(s.ok?"passed":"failed")<<"\",\n"
     <<"  \"shared_memory_is_lock_free\": "<<(s.atomics_lock_free?"true":"false")<<",\n"
     <<"  \"sub_10_us_p50\": "<<(s.p50_us<10.0?"true":"false")<<",\n"
     <<"  \"p50_one_way_us\": "<<s.p50_us<<",\n"
     <<"  \"p95_one_way_us\": "<<s.p95_us<<",\n"
     <<"  \"p99_one_way_us\": "<<s.p99_us<<",\n"
     <<"  \"max_one_way_us\": "<<s.max_us<<",\n"
     <<"  \"mean_one_way_us\": "<<s.mean_us<<",\n"
     <<"  \"throughput_messages_per_second\": "<<s.throughput_messages_per_second<<",\n"
     <<"  \"measured_duration_ms\": "<<s.duration_ms<<",\n"
     <<"  \"timed_sample_count\": "<<s.sample_count<<",\n"
     <<"  \"bad_sequences\": "<<s.bad_sequences<<",\n"
     <<"  \"invalid_timestamps\": "<<s.invalid_timestamps<<",\n"
     <<"  \"note\": \"Linux shared-memory handoff benchmark. It measures a different path from ZeroMQ; results depend on the host scheduler and cache behavior.\"\n"
     <<"}\n";
  return out.str();
}
}
int main(int argc,char** argv) {
  try {
    std::uint64_t messages=200000,warmup=20000;
    std::string out_path;
    for(int i=1;i<argc;++i) {
      const std::string arg=argv[i];
      if(arg=="--messages"&&i+1<argc)messages=std::stoull(argv[++i]);
      else if(arg=="--warmup"&&i+1<argc)warmup=std::stoull(argv[++i]);
      else if(arg=="--out"&&i+1<argc)out_path=argv[++i];
      else if(arg=="--help") {
        std::cout<<"Usage: sentinel_shm_spsc_ipc_benchmark [--messages COUNT] [--warmup COUNT] [--out PATH]\n";
        return 0;
      } else throw std::invalid_argument("unknown or incomplete argument: "+arg);
    }
    require(messages>0,"--messages must be positive");
    require(warmup<=std::numeric_limits<std::uint64_t>::max()-messages,"message count overflow");
    const auto total=messages+warmup;
    void* memory=mmap(nullptr,sizeof(SharedSpscQueue),PROT_READ|PROT_WRITE,
                      MAP_SHARED|MAP_ANONYMOUS,-1,0);
    require(memory!=MAP_FAILED,"mmap failed");
    auto* queue=new(memory) SharedSpscQueue();
    require(queue->lock_free(),"this host does not provide lock-free atomics for the shared queue");
    int ready_pipe[2],result_pipe[2];
    if(pipe(ready_pipe)!=0||pipe(result_pipe)!=0) {
      queue->~SharedSpscQueue();munmap(memory,sizeof(SharedSpscQueue));
      throw std::runtime_error("pipe failed");
    }
    const pid_t child=fork();
    if(child<0) {
      close(ready_pipe[0]);close(ready_pipe[1]);close(result_pipe[0]);close(result_pipe[1]);
      queue->~SharedSpscQueue();munmap(memory,sizeof(SharedSpscQueue));
      throw std::runtime_error("fork failed");
    }
    if(child==0) {
      close(ready_pipe[0]);close(result_pipe[0]);
      const int rc=consume(queue,total,warmup,ready_pipe[1],result_pipe[1]);
      _exit(rc);
    }
    close(ready_pipe[1]);close(result_pipe[1]);
    int ready_read=ready_pipe[0],result_read=result_pipe[0];
    bool child_waited=false;
    bool queue_constructed=true;
    bool memory_mapped=true;
    auto cleanup=[&]() {
      if(ready_read>=0){close(ready_read);ready_read=-1;}
      if(result_read>=0){close(result_read);result_read=-1;}
      if(!child_waited){kill(child,SIGTERM);int ignored=0;(void)waitpid(child,&ignored,0);child_waited=true;}
      if(queue_constructed){queue->~SharedSpscQueue();queue_constructed=false;}
      if(memory_mapped){munmap(memory,sizeof(SharedSpscQueue));memory_mapped=false;}
    };
    try {
      char ready=0;
      const ssize_t nr=read(ready_read,&ready,1);
      close(ready_read);ready_read=-1;
      require(nr==1&&ready==1,"shared-memory consumer failed to start");
      for(std::uint64_t i=0;i<total;++i) {
        bool pushed=false;
        while(!pushed) {
          const Tick tick{i,now_ns()};
          pushed=queue->try_push(tick);
          if(!pushed)std::this_thread::yield();
        }
      }
      Summary summary{};
      require(read_all(result_read,&summary,sizeof(summary)),"could not read shared-memory consumer report");
      close(result_read);result_read=-1;
      int status=0;
      const pid_t waited=waitpid(child,&status,0);
      child_waited=true;
      require(waited==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0,
              "shared-memory consumer exited with an error");
      require(summary.ok==1&&summary.sample_count==messages&&summary.bad_sequences==0&&summary.invalid_timestamps==0,
              "shared-memory payload/count validation failed");
      const auto report=make_report(messages,warmup,summary);
      if(out_path.empty())std::cout<<report;
      else {
        std::ofstream file(out_path,std::ios::binary);
        if(!file)throw std::runtime_error("could not open report output: "+out_path);
        file<<report;
        if(!file)throw std::runtime_error("could not write report output: "+out_path);
        std::cout<<report;
      }
      if(queue_constructed){queue->~SharedSpscQueue();queue_constructed=false;}
      if(memory_mapped){munmap(memory,sizeof(SharedSpscQueue));memory_mapped=false;}
      return 0;
    } catch(...) {cleanup();throw;}
  } catch(const std::exception& exc) {
    std::cerr<<"error: "<<exc.what()<<'\n';
    return 2;
  }
}
