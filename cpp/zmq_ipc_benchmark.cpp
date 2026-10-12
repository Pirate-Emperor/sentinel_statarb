// Native process-to-process ZeroMQ IPC latency benchmark for Linux/macOS.
#include <zmq.h>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

namespace {
using Clock = std::chrono::steady_clock;
struct Metrics {
  double p50_us=0, p95_us=0, p99_us=0, max_us=0, mean_us=0;
  double round_trips_per_second=0, measured_duration_ms=0;
  std::size_t sample_count=0;
};
void require(bool ok,const std::string& message) {
  if(!ok) throw std::runtime_error(message);
}
bool set_int(void* socket,int option,int value) {
  return zmq_setsockopt(socket,option,&value,sizeof(value))==0;
}
bool configure(void* socket) {
  return set_int(socket,ZMQ_LINGER,0) &&
         set_int(socket,ZMQ_SNDTIMEO,5000) &&
         set_int(socket,ZMQ_RCVTIMEO,5000);
}
int serve(const std::string& endpoint,std::uint64_t count,int ready_fd) {
  void* context=zmq_ctx_new();
  if(!context) { const char v=0; (void)write(ready_fd,&v,1); close(ready_fd); return 2; }
  void* socket=zmq_socket(context,ZMQ_REP);
  if(!socket || !configure(socket) || zmq_bind(socket,endpoint.c_str())!=0) {
    const char v=0; (void)write(ready_fd,&v,1); close(ready_fd);
    if(socket) zmq_close(socket);
    zmq_ctx_term(context);
    return 3;
  }
  const char ready=1;
  if(write(ready_fd,&ready,1)!=1) { close(ready_fd);zmq_close(socket);zmq_ctx_term(context);return 4; }
  close(ready_fd);
  for(std::uint64_t i=0;i<count;++i) {
    std::uint64_t value=0;
    const int received=zmq_recv(socket,&value,sizeof(value),0);
    if(received!=static_cast<int>(sizeof(value))) { zmq_close(socket);zmq_ctx_term(context);return 5; }
    const int sent=zmq_send(socket,&value,sizeof(value),0);
    if(sent!=static_cast<int>(sizeof(value))) { zmq_close(socket);zmq_ctx_term(context);return 6; }
  }
  zmq_close(socket);
  zmq_ctx_term(context);
  return 0;
}
double percentile(const std::vector<std::uint64_t>& values,double fraction) {
  if(values.empty()) return 0.0;
  auto copy=values;
  const auto index=static_cast<std::size_t>(fraction*static_cast<double>(copy.size()-1));
  std::nth_element(copy.begin(),copy.begin()+index,copy.end());
  return static_cast<double>(copy[index])/1000.0;
}
Metrics benchmark(std::uint64_t count,std::uint64_t warmup) {
  require(count>0,"--messages must be positive");
  require(warmup<=std::numeric_limits<std::uint64_t>::max()-count,"message count overflow");
  char dir_template[]="/tmp/sentinel-zmq-cpp-XXXXXX";
  char* dir=mkdtemp(dir_template);
  require(dir!=nullptr,"could not create IPC temp directory");
  const std::string directory(dir);
  const std::string endpoint="ipc://"+directory+"/roundtrip.sock";
  const std::string socket_path=directory+"/roundtrip.sock";
  int ready_pipe[2];
  if(pipe(ready_pipe)!=0) { rmdir(directory.c_str());throw std::runtime_error("pipe() failed"); }
  const std::uint64_t total=count+warmup;
  const pid_t child=fork();
  if(child<0) {
    close(ready_pipe[0]);close(ready_pipe[1]);rmdir(directory.c_str());
    throw std::runtime_error("fork() failed");
  }
  if(child==0) {
    close(ready_pipe[0]);
    const int rc=serve(endpoint,total,ready_pipe[1]);
    _exit(rc);
  }
  close(ready_pipe[1]);
  int ready_read=ready_pipe[0];
  void* context=nullptr;
  void* socket=nullptr;
  bool child_waited=false;
  auto cleanup=[&]() {
    if(socket) { zmq_close(socket);socket=nullptr; }
    if(context) { zmq_ctx_term(context);context=nullptr; }
    if(!child_waited) {
      kill(child,SIGTERM);
      int ignored=0;
      (void)waitpid(child,&ignored,0);
      child_waited=true;
    }
    unlink(socket_path.c_str());
    rmdir(directory.c_str());
    if(ready_read>=0) { close(ready_read);ready_read=-1; }
  };
  try {
    char ready=0;
    const ssize_t nr=read(ready_read,&ready,1);
    close(ready_read);ready_read=-1;
    require(nr==1 && ready==1,"ZeroMQ server failed to bind its IPC endpoint");
    context=zmq_ctx_new();
    require(context!=nullptr,"zmq_ctx_new failed");
    socket=zmq_socket(context,ZMQ_REQ);
    require(socket!=nullptr,"zmq_socket failed");
    require(configure(socket),"ZeroMQ socket options failed");
    require(zmq_connect(socket,endpoint.c_str())==0,std::string("zmq_connect failed: ")+zmq_strerror(zmq_errno()));
    std::vector<std::uint64_t> samples;
    samples.reserve(static_cast<std::size_t>(count));
    Clock::time_point total_start{},total_end{};
    std::uint64_t sum=0;
    for(std::uint64_t i=0;i<total;++i) {
      const bool measured=i>=warmup;
      const auto start=measured?Clock::now():Clock::time_point{};
      const std::uint64_t sent_value=i;
      const int sent=zmq_send(socket,&sent_value,sizeof(sent_value),0);
      require(sent==static_cast<int>(sizeof(sent_value)),std::string("ZeroMQ send failed: ")+zmq_strerror(zmq_errno()));
      std::uint64_t received_value=0;
      const int received=zmq_recv(socket,&received_value,sizeof(received_value),0);
      require(received==static_cast<int>(sizeof(received_value)),std::string("ZeroMQ receive failed: ")+zmq_strerror(zmq_errno()));
      require(received_value==sent_value,"ZeroMQ payload sequence mismatch");
      if(measured) {
        const auto finish=Clock::now();
        if(samples.empty()) total_start=start;
        total_end=finish;
        const auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(finish-start).count();
        samples.push_back(static_cast<std::uint64_t>(ns));
        sum+=static_cast<std::uint64_t>(ns);
      }
    }
    const double duration=std::chrono::duration<double>(total_end-total_start).count();
    Metrics out;
    out.p50_us=percentile(samples,0.50);
    out.p95_us=percentile(samples,0.95);
    out.p99_us=percentile(samples,0.99);
    out.max_us=*std::max_element(samples.begin(),samples.end())/1000.0;
    out.mean_us=static_cast<double>(sum)/static_cast<double>(samples.size())/1000.0;
    out.round_trips_per_second=duration>0?static_cast<double>(count)/duration:0;
    out.measured_duration_ms=duration*1000.0;
    out.sample_count=samples.size();
    if(socket) { zmq_close(socket);socket=nullptr; }
    if(context) { zmq_ctx_term(context);context=nullptr; }
    int status=0;
    const pid_t waited=waitpid(child,&status,0);
    child_waited=true;
    require(waited==child && WIFEXITED(status) && WEXITSTATUS(status)==0,
            "ZeroMQ server process did not exit cleanly");
    unlink(socket_path.c_str());
    rmdir(directory.c_str());
    return out;
  } catch(...) {
    cleanup();
    throw;
  }
}
std::string report(std::uint64_t messages,std::uint64_t warmup,const Metrics& m) {
  std::ostringstream out;
  out<<std::fixed<<std::setprecision(3)
     <<"{\n"
     <<"  \"benchmark\": \"native_cpp_zeromq_ipc_round_trip\",\n"
     <<"  \"transport\": \"ZeroMQ ipc:// REQ/REP between two C++ processes\",\n"
     <<"  \"measurement\": \"Round trip; includes two IPC legs and process scheduling\",\n"
     <<"  \"warmup_messages\": "<<warmup<<",\n"
     <<"  \"measured_messages\": "<<messages<<",\n"
     <<"  \"payload_check\": \"passed\",\n"
     <<"  \"transport_is_lock_free\": false,\n"
     <<"  \"p50_round_trip_us\": "<<m.p50_us<<",\n"
     <<"  \"p95_round_trip_us\": "<<m.p95_us<<",\n"
     <<"  \"p99_round_trip_us\": "<<m.p99_us<<",\n"
     <<"  \"max_round_trip_us\": "<<m.max_us<<",\n"
     <<"  \"mean_round_trip_us\": "<<m.mean_us<<",\n"
     <<"  \"throughput_round_trips_per_second\": "<<m.round_trips_per_second<<",\n"
     <<"  \"timed_sample_count\": "<<m.sample_count<<",\n"
     <<"  \"measured_duration_ms\": "<<m.measured_duration_ms<<",\n"
     <<"  \"note\": \"ZeroMQ transport itself is not lock-free; lock-free status is checked separately for the native SPSC ring.\"\n"
     <<"}\n";
  return out.str();
}
}
int main(int argc,char** argv) {
  try {
    std::uint64_t messages=20000,warmup=2000;
    std::string out_path;
    for(int i=1;i<argc;++i) {
      const std::string arg=argv[i];
      if(arg=="--messages" && i+1<argc) messages=std::stoull(argv[++i]);
      else if(arg=="--warmup" && i+1<argc) warmup=std::stoull(argv[++i]);
      else if(arg=="--out" && i+1<argc) out_path=argv[++i];
      else if(arg=="--help") {
        std::cout<<"Usage: sentinel_zmq_ipc_benchmark [--messages COUNT] [--warmup COUNT] [--out PATH]\n";
        return 0;
      } else throw std::invalid_argument("unknown or incomplete argument: "+arg);
    }
    const auto metrics=benchmark(messages,warmup);
    const auto text=report(messages,warmup,metrics);
    if(out_path.empty()) std::cout<<text;
    else {
      std::ofstream file(out_path,std::ios::binary);
      if(!file) throw std::runtime_error("could not open report output: "+out_path);
      file<<text;
      if(!file) throw std::runtime_error("could not write report output: "+out_path);
      std::cout<<text;
    }
    return 0;
  } catch(const std::exception& exc) {
    std::cerr<<"error: "<<exc.what()<<'\n';
    return 2;
  }
}
