// Native process-to-process ZeroMQ one-way latency benchmark.
// A request/reply acknowledgement paces each message so the send queue cannot build up.
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
struct Message { std::uint64_t sequence; std::int64_t sent_ns; };
struct Ack { std::uint64_t sequence; std::int64_t received_ns; };
void require(bool ok, const std::string& message) {
  if (!ok) throw std::runtime_error(message);
}
std::int64_t now_ns() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
      Clock::now().time_since_epoch()).count();
}
bool set_int(void* socket, int option, int value) {
  return zmq_setsockopt(socket, option, &value, sizeof(value)) == 0;
}
bool configure(void* socket) {
  return set_int(socket, ZMQ_LINGER, 0) &&
         set_int(socket, ZMQ_SNDTIMEO, 5000) &&
         set_int(socket, ZMQ_RCVTIMEO, 5000);
}
bool write_ready(int fd, char value) {
  return write(fd, &value, 1) == 1;
}
double percentile(const std::vector<std::uint64_t>& values, double p) {
  if (values.empty()) return 0.0;
  auto copy = values;
  const auto index = static_cast<std::size_t>(p * static_cast<double>(copy.size() - 1));
  std::nth_element(copy.begin(), copy.begin() + index, copy.end());
  return static_cast<double>(copy[index]) / 1000.0;
}
int receiver(const std::string& endpoint, std::uint64_t total, int ready_fd) {
  void* context = zmq_ctx_new();
  if (!context) {
    (void)write_ready(ready_fd, 0);
    close(ready_fd);
    return 2;
  }
  void* socket = zmq_socket(context, ZMQ_REP);
  if (!socket || !configure(socket) || zmq_bind(socket, endpoint.c_str()) != 0) {
    (void)write_ready(ready_fd, 0);
    close(ready_fd);
    if (socket) zmq_close(socket);
    zmq_ctx_term(context);
    return 3;
  }
  if (!write_ready(ready_fd, 1)) {
    close(ready_fd);
    zmq_close(socket);
    zmq_ctx_term(context);
    return 4;
  }
  close(ready_fd);
  for (std::uint64_t i = 0; i < total; ++i) {
    Message message{};
    const int got = zmq_recv(socket, &message, sizeof(message), 0);
    if (got != static_cast<int>(sizeof(message)) || message.sequence != i ||
        message.sent_ns <= 0) {
      zmq_close(socket);
      zmq_ctx_term(context);
      return 5;
    }
    const Ack ack{message.sequence, now_ns()};
    const int sent = zmq_send(socket, &ack, sizeof(ack), 0);
    if (sent != static_cast<int>(sizeof(ack))) {
      zmq_close(socket);
      zmq_ctx_term(context);
      return 6;
    }
  }
  zmq_close(socket);
  zmq_ctx_term(context);
  return 0;
}
std::string make_report(std::uint64_t messages, std::uint64_t warmup,
                        const std::vector<std::uint64_t>& one_way,
                        const std::vector<std::uint64_t>& round_trip,
                        double total_ms) {
  const auto maximum = one_way.empty() ? 0ULL :
      *std::max_element(one_way.begin(), one_way.end());
  const auto roundtrip_max = round_trip.empty() ? 0ULL :
      *std::max_element(round_trip.begin(), round_trip.end());
  std::uint64_t sum_one_way = 0, sum_round_trip = 0;
  for (auto value : one_way) sum_one_way += value;
  for (auto value : round_trip) sum_round_trip += value;
  const double mean_one_way = one_way.empty() ? 0.0 :
      static_cast<double>(sum_one_way) / static_cast<double>(one_way.size()) / 1000.0;
  const double mean_round_trip = round_trip.empty() ? 0.0 :
      static_cast<double>(sum_round_trip) / static_cast<double>(round_trip.size()) / 1000.0;
  const double throughput = total_ms > 0 ? messages / (total_ms / 1000.0) : 0.0;
  std::ostringstream out;
  out << std::fixed << std::setprecision(3)
      << "{\n"
      << "  \"benchmark\": \"native_cpp_zeromq_ipc_one_way\",\n"
      << "  \"transport\": \"ZeroMQ ipc:// REQ/REP between two C++ processes\",\n"
      << "  \"measurement\": \"Sender timestamp to receiver timestamp; same host monotonic clock; per-message acknowledgement prevents queue buildup\",\n"
      << "  \"warmup_messages\": " << warmup << ",\n"
      << "  \"measured_messages\": " << messages << ",\n"
      << "  \"payload_check\": \"passed\",\n"
      << "  \"transport_is_lock_free\": false,\n"
      << "  \"sub_10_us_p50\": " << (percentile(one_way, 0.50) < 10.0 ? "true" : "false") << ",\n"
      << "  \"p50_one_way_us\": " << percentile(one_way, 0.50) << ",\n"
      << "  \"p95_one_way_us\": " << percentile(one_way, 0.95) << ",\n"
      << "  \"p99_one_way_us\": " << percentile(one_way, 0.99) << ",\n"
      << "  \"max_one_way_us\": " << static_cast<double>(maximum) / 1000.0 << ",\n"
      << "  \"mean_one_way_us\": " << mean_one_way << ",\n"
      << "  \"p50_ack_round_trip_us\": " << percentile(round_trip, 0.50) << ",\n"
      << "  \"p99_ack_round_trip_us\": " << percentile(round_trip, 0.99) << ",\n"
      << "  \"max_ack_round_trip_us\": " << static_cast<double>(roundtrip_max) / 1000.0 << ",\n"
      << "  \"mean_ack_round_trip_us\": " << mean_round_trip << ",\n"
      << "  \"serial_round_trips_per_second\": " << throughput << ",\n"
      << "  \"measured_duration_ms\": " << total_ms << ",\n"
      << "  \"timed_sample_count\": " << one_way.size() << ",\n"
      << "  \"bad_payloads\": 0,\n"
      << "  \"note\": \"This is a paced IPC measurement with one acknowledgement per message. ZeroMQ transport is not lock-free.\"\n"
      << "}\n";
  return out.str();
}
}
int main(int argc, char** argv) {
  try {
    std::uint64_t messages = 20000, warmup = 2000;
    std::string out_path;
    for (int i = 1; i < argc; ++i) {
      const std::string arg = argv[i];
      if (arg == "--messages" && i + 1 < argc) messages = std::stoull(argv[++i]);
      else if (arg == "--warmup" && i + 1 < argc) warmup = std::stoull(argv[++i]);
      else if (arg == "--out" && i + 1 < argc) out_path = argv[++i];
      else if (arg == "--help") {
        std::cout << "Usage: sentinel_zmq_ipc_oneway_benchmark [--messages COUNT] [--warmup COUNT] [--out PATH]\n";
        return 0;
      } else throw std::invalid_argument("unknown or incomplete argument: " + arg);
    }
    require(messages > 0, "--messages must be positive");
    require(warmup <= std::numeric_limits<std::uint64_t>::max() - messages,
            "message count overflow");

    char dir_template[] = "/tmp/sentinel-zmq-oneway-XXXXXX";
    char* dir = mkdtemp(dir_template);
    require(dir != nullptr, "could not create IPC temp directory");
    const std::string directory(dir);
    const std::string endpoint = "ipc://" + directory + "/stream.sock";
    const std::string socket_path = directory + "/stream.sock";
    int ready_pipe[2];
    if (pipe(ready_pipe) != 0) {
      rmdir(directory.c_str());
      throw std::runtime_error("pipe() failed");
    }

    const std::uint64_t total = messages + warmup;
    const pid_t child = fork();
    if (child < 0) {
      close(ready_pipe[0]);
      close(ready_pipe[1]);
      rmdir(directory.c_str());
      throw std::runtime_error("fork() failed");
    }
    if (child == 0) {
      close(ready_pipe[0]);
      _exit(receiver(endpoint, total, ready_pipe[1]));
    }

    close(ready_pipe[1]);
    int ready_read = ready_pipe[0];
    void* context = nullptr;
    void* socket = nullptr;
    bool child_waited = false;
    auto cleanup = [&]() {
      if (socket) { zmq_close(socket); socket = nullptr; }
      if (context) { zmq_ctx_term(context); context = nullptr; }
      if (!child_waited) {
        kill(child, SIGTERM);
        int ignored = 0;
        (void)waitpid(child, &ignored, 0);
        child_waited = true;
      }
      if (ready_read >= 0) { close(ready_read); ready_read = -1; }
      unlink(socket_path.c_str());
      rmdir(directory.c_str());
    };
    try {
      char ready = 0;
      const ssize_t nr = read(ready_read, &ready, 1);
      close(ready_read);
      ready_read = -1;
      require(nr == 1 && ready == 1, "ZeroMQ receiver failed to bind the IPC endpoint");

      context = zmq_ctx_new();
      require(context != nullptr, "zmq_ctx_new failed");
      socket = zmq_socket(context, ZMQ_REQ);
      require(socket != nullptr, "zmq_socket failed");
      require(configure(socket), "ZeroMQ socket options failed");
      require(zmq_connect(socket, endpoint.c_str()) == 0,
              std::string("zmq_connect failed: ") + zmq_strerror(zmq_errno()));

      std::vector<std::uint64_t> one_way, round_trip;
      one_way.reserve(static_cast<std::size_t>(messages));
      round_trip.reserve(static_cast<std::size_t>(messages));
      Clock::time_point measured_start{}, measured_end{};
      for (std::uint64_t i = 0; i < total; ++i) {
        const bool measured = i >= warmup;
        const auto start = Clock::now();
        Message message{i, now_ns()};
        const int sent = zmq_send(socket, &message, sizeof(message), 0);
        require(sent == static_cast<int>(sizeof(message)),
                std::string("ZeroMQ send failed: ") + zmq_strerror(zmq_errno()));
        Ack ack{};
        const int got = zmq_recv(socket, &ack, sizeof(ack), 0);
        const auto finish = Clock::now();
        require(got == static_cast<int>(sizeof(ack)),
                std::string("ZeroMQ acknowledgement receive failed: ") + zmq_strerror(zmq_errno()));
        require(ack.sequence == i && ack.received_ns >= message.sent_ns,
                "ZeroMQ payload or timestamp validation failed");
        if (measured) {
          if (one_way.empty()) measured_start = start;
          measured_end = finish;
          one_way.push_back(static_cast<std::uint64_t>(ack.received_ns - message.sent_ns));
          round_trip.push_back(static_cast<std::uint64_t>(
              std::chrono::duration_cast<std::chrono::nanoseconds>(finish - start).count()));
        }
      }

      const double measured_ms =
          std::chrono::duration<double>(measured_end - measured_start).count() * 1000.0;
      zmq_close(socket);
      socket = nullptr;
      zmq_ctx_term(context);
      context = nullptr;
      int status = 0;
      const pid_t waited = waitpid(child, &status, 0);
      child_waited = true;
      require(waited == child && WIFEXITED(status) && WEXITSTATUS(status) == 0,
              "ZeroMQ receiver exited with an error");
      unlink(socket_path.c_str());
      rmdir(directory.c_str());

      const auto report_text = make_report(messages, warmup, one_way, round_trip, measured_ms);
      if (out_path.empty()) std::cout << report_text;
      else {
        std::ofstream file(out_path, std::ios::binary);
        if (!file) throw std::runtime_error("could not open report output: " + out_path);
        file << report_text;
        if (!file) throw std::runtime_error("could not write report output: " + out_path);
        std::cout << report_text;
      }
      return 0;
    } catch (...) {
      cleanup();
      throw;
    }
  } catch (const std::exception& exc) {
    std::cerr << "error: " << exc.what() << '\n';
    return 2;
  }
}
