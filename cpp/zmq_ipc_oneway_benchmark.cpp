// Measure one-way native ZeroMQ IPC latency using timestamps from the same host clock.
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
using Clock=std::chrono::steady_clock;
struct Message { std::uint64_t sequence; std::int64_t sent_ns; };
struct Summary {
  int ok;
  std::uint64_t sample_count;
  std::uint64_t bad_payloads;
  double p50_us,p95_us,p99_us,max_us,mean_us;
  double receiver_throughput_per_second,receiver_duration_ms;
};
void require(bool ok,const std::string& message) {
  if(!ok) throw std::runtime_error(message);
}
std::int64_t now_ns() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();
}
bool set_int(void* socket,int option,int value) {
  return zmq_setsockopt(socket,option,&value,sizeof(value))==0;
}
bool configure(void* socket) {
  return set_int(socket,ZMQ_LINGER,0) &&
         set_int(socket,ZMQ_SNDTIMEO,5000) &&
         set_int(socket,ZMQ_RCVTIMEO,5000) &&
         set_int(socket,ZMQ_SNDHWM,1) &&
         set_int(socket,ZMQ_RCVHWM,1);
}
double percentile(const std::vector<std::uint64_t>& values,double p) {
  if(values.empty()) return 0.0;
  auto copy=values;
  auto index=static_cast<std::size_t>(p*static_cast<double>(copy.size()-1));
  std::nth_element(copy.begin(),copy.begin()+index,copy.end());
  return static_cast<double>(copy[index])/1000.0;
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
int receiver(const std::string& endpoint,std::uint64_t total,std::uint64_t warmup,int ready_fd,int result_fd) {
  void* context=zmq_ctx_new();
  if(!context) { const char v=0;(void)write_all(ready_fd,&v,1);close(ready_fd);close(result_fd);return 2; }
  void* socket=zmq_socket(context,ZMQ_PULL);
  if(!socket || !configure(socket) || zmq_bind(socket,endpoint.c_str())!=0) {
    const char v=0;(void)write_all(ready_fd,&v,1);close(ready_fd);
    if(socket)zmq_close(socket);zmq_ctx_term(context);close(result_fd);return 3;
  }
  const char ready=1;
  if(!write_all(ready_fd,&ready,1)) {close(ready_fd);zmq_close(socket);zmq_ctx_term(context);close(result_fd);return 4;}
  close(ready_fd);
  std::vector<std::uint64_t> samples;
  samples.reserve(static_cast<std::size_t>(total-warmup));
  std::uint64_t bad=0;
  std::int64_t first=0,last=0;
  for(std::uint64_t i=0;i<total;++i) {
    Message msg{};
    const int n=zmq_recv(socket,&msg,sizeof(msg),0);
    if(n!=static_cast<int>(sizeof(msg))) { ++bad;break; }
    const auto received=now_ns();
    if(msg.sequence!=i || msg.sent_ns<=0 || received<msg.sent_ns) { ++bad;continue; }
    if(i>=warmup) {
      if(samples.empty())first=received;
      last=received;
      samples.push_back(static_cast<std::uint64_t>(received-msg.sent_ns));
    }
  }
  Summary out{};
  out.ok=(bad==0 && samples.size()==static_cast<std::size_t>(total-warmup))?1:0;
  out.sample_count=samples.size();
  out.bad_payloads=bad;
  out.p50_us=percentile(samples,0.50);
  out.p95_us=percentile(samples,0.95);
  out.p99_us=percentile(samples,0.99);
  out.max_us=samples.empty()?0.0:static_cast<double>(*std::max_element(samples.begin(),samples.end()))/1000.0;
  std::uint64_t sum=0;
  for(auto v:samples)sum+=v;
  out.mean_us=samples.empty()?0.0:static_cast<double>(sum)/static_cast<double>(samples.size())/1000.0;
  const double duration=samples.size()>1?static_cast<double>(last-first)/1e9:0.0;
  out.receiver_duration_ms=duration*1000.0;
  out.receiver_throughput_per_second=duration>0?static_cast<double>(samples.size())/duration:0.0;
  zmq_close(socket);zmq_ctx_term(context);
  const bool sent=write_all(result_fd,&out,sizeof(out));
  close(result_fd);
  if (!sent) return 7;
  if (!out.ok) {
    std::cerr << "receiver validation failed: samples=" << out.sample_count
              << ", expected=" << (total-warmup)
              << ", bad_payloads=" << out.bad_payloads << '\\n';
    return 5;
  }
  return 0;
}
std::string make_report(std::uint64_t messages,std::uint64_t warmup,const Summary& s,double sender_rate,double sender_duration_ms) {
  std::ostringstream out;
  out<<std::fixed<<std::setprecision(3)
     <<"{\n"
     <<"  \"benchmark\": \"native_cpp_zeromq_ipc_one_way\",\n"
     <<"  \"transport\": \"ZeroMQ ipc:// PUSH to PULL between two C++ processes\",\n"
     <<"  \"measurement\": \"One way from sender steady-clock timestamp to receiver after recv; same host clock\",\n"
     <<"  \"warmup_messages\": "<<warmup<<",\n"
     <<"  \"measured_messages\": "<<messages<<",\n"
     <<"  \"payload_check\": \""<<(s.ok?"passed":"failed")<<"\",\n"
     <<"  \"transport_is_lock_free\": false,\n"
     <<"  \"sub_10_us_p50\": "<<(s.p50_us<10.0?"true":"false")<<",\n"
     <<"  \"p50_one_way_us\": "<<s.p50_us<<",\n"
     <<"  \"p95_one_way_us\": "<<s.p95_us<<",\n"
     <<"  \"p99_one_way_us\": "<<s.p99_us<<",\n"
     <<"  \"max_one_way_us\": "<<s.max_us<<",\n"
     <<"  \"mean_one_way_us\": "<<s.mean_us<<",\n"
     <<"  \"receiver_throughput_messages_per_second\": "<<s.receiver_throughput_per_second<<",\n"
     <<"  \"sender_throughput_messages_per_second\": "<<sender_rate<<",\n"
     <<"  \"sender_measured_duration_ms\": "<<sender_duration_ms<<",\n"
     <<"  \"timed_sample_count\": "<<s.sample_count<<",\n"
     <<"  \"bad_payloads\": "<<s.bad_payloads<<",\n"
     <<"  \"note\": \"ZeroMQ transport itself is not lock-free; lock-free status is measured separately for the native SPSC ring.\"\n"
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
      if(arg=="--messages"&&i+1<argc)messages=std::stoull(argv[++i]);
      else if(arg=="--warmup"&&i+1<argc)warmup=std::stoull(argv[++i]);
      else if(arg=="--out"&&i+1<argc)out_path=argv[++i];
      else if(arg=="--help") {
        std::cout<<"Usage: sentinel_zmq_ipc_oneway_benchmark [--messages COUNT] [--warmup COUNT] [--out PATH]\n";
        return 0;
      } else throw std::invalid_argument("unknown or incomplete argument: "+arg);
    }
    require(messages>0,"--messages must be positive");
    require(warmup<=std::numeric_limits<std::uint64_t>::max()-messages,"message count overflow");
    char dir_template[]="/tmp/sentinel-zmq-oneway-XXXXXX";
    char* dir=mkdtemp(dir_template);
    require(dir!=nullptr,"could not create IPC temp directory");
    const std::string directory(dir),endpoint="ipc://"+directory+"/stream.sock",socket_path=directory+"/stream.sock";
    int ready_pipe[2],result_pipe[2];
    if(pipe(ready_pipe)!=0||pipe(result_pipe)!=0) {rmdir(directory.c_str());throw std::runtime_error("pipe() failed");}
    const auto total=messages+warmup;
    const pid_t child=fork();
    if(child<0) {
      close(ready_pipe[0]);close(ready_pipe[1]);close(result_pipe[0]);close(result_pipe[1]);rmdir(directory.c_str());
      throw std::runtime_error("fork() failed");
    }
    if(child==0) {
      close(ready_pipe[0]);close(result_pipe[0]);
      const int rc=receiver(endpoint,total,warmup,ready_pipe[1],result_pipe[1]);
      _exit(rc);
    }
    close(ready_pipe[1]);close(result_pipe[1]);
    int ready_read=ready_pipe[0];
    int result_read=result_pipe[0];
    void* context=nullptr;void* socket=nullptr;bool child_waited=false;
    auto cleanup=[&]() {
      if(socket){zmq_close(socket);socket=nullptr;}
      if(context){zmq_ctx_term(context);context=nullptr;}
      if(!child_waited){kill(child,SIGTERM);int ignored=0;(void)waitpid(child,&ignored,0);child_waited=true;}
      if(ready_read>=0){close(ready_read);ready_read=-1;}
      if(result_read>=0){close(result_read);result_read=-1;}
      unlink(socket_path.c_str());rmdir(directory.c_str());
    };
    try {
      char ready=0;const auto nr=read(ready_read,&ready,1);
      close(ready_read);ready_read=-1;
      require(nr==1&&ready==1,"ZeroMQ receiver failed to bind the IPC endpoint");
      context=zmq_ctx_new();require(context!=nullptr,"zmq_ctx_new failed");
      socket=zmq_socket(context,ZMQ_PUSH);require(socket!=nullptr,"zmq_socket failed");
      require(configure(socket),"ZeroMQ socket options failed");
      require(zmq_connect(socket,endpoint.c_str())==0,std::string("zmq_connect failed: ")+zmq_strerror(zmq_errno()));
      Clock::time_point first_send{},last_send{};
      for(std::uint64_t i=0;i<total;++i) {
        const bool measured=i>=warmup;
        if(measured&&i==warmup)first_send=Clock::now();
        Message msg{i,now_ns()};
        const int sent=zmq_send(socket,&msg,sizeof(msg),0);
        require(sent==static_cast<int>(sizeof(msg)),std::string("ZeroMQ send failed: ")+zmq_strerror(zmq_errno()));
        if(measured)last_send=Clock::now();
      }
      const double send_duration=std::chrono::duration<double>(last_send-first_send).count();
      const double sender_rate=send_duration>0?static_cast<double>(messages)/send_duration:0.0;
      const double sender_ms=send_duration*1000.0;
      // Keep the PUSH socket open until the receiver confirms that every queued
      // message was consumed. LINGER=0 would otherwise drop buffered messages.
      Summary summary{};
      require(read_all(result_read,&summary,sizeof(summary)),"could not read ZeroMQ receiver report");
      close(result_read);result_read=-1;
      zmq_close(socket);socket=nullptr;
      zmq_ctx_term(context);context=nullptr;
      int status=0;const auto waited=waitpid(child,&status,0);child_waited=true;
      require(waited==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"ZeroMQ receiver exited with an error");
      require(summary.ok==1&&summary.sample_count==messages&&summary.bad_payloads==0,"ZeroMQ payload or sample count check failed");
      unlink(socket_path.c_str());rmdir(directory.c_str());
      const auto report=make_report(messages,warmup,summary,sender_rate,sender_ms);
      if(out_path.empty())std::cout<<report;
      else {
        std::ofstream file(out_path,std::ios::binary);
        if(!file)throw std::runtime_error("could not open report output: "+out_path);
        file<<report;
        if(!file)throw std::runtime_error("could not write report output: "+out_path);
        std::cout<<report;
      }
      return 0;
    } catch(...) {cleanup();throw;}
  } catch(const std::exception& exc) {
    std::cerr<<"error: "<<exc.what()<<'\n';
    return 2;
  }
}
