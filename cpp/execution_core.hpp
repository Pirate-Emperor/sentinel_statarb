#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
namespace sentinel {
class DynamicDebouncer {
 public:
  DynamicDebouncer(std::uint64_t base_ns,std::uint64_t max_ns,double stress_bps)
      :base_ns_(base_ns),max_ns_(max_ns),stress_bps_(stress_bps) {
    if(!std::isfinite(stress_bps) || stress_bps<=0.0 || max_ns<base_ns)
      throw std::invalid_argument("invalid debounce settings");
  }
  bool accept(std::uint64_t ts,double mid) {
    if(!std::isfinite(mid)||mid<=0.0) throw std::invalid_argument("mid must be positive and finite");
    if(has_timestamp_ && ts<last_timestamp_ns_)
      throw std::invalid_argument("timestamps must be monotonic");
    last_timestamp_ns_=ts;
    has_timestamp_=true;
    std::uint64_t cooldown=base_ns_;
    if(last_mid_>0.0) {
      const double move=std::abs(mid-last_mid_)/last_mid_*10000.0;
      const long double scaled=static_cast<long double>(base_ns_)*
          (1.0L+static_cast<long double>(move)/static_cast<long double>(stress_bps_));
      cooldown=scaled>=static_cast<long double>(max_ns_)?max_ns_:static_cast<std::uint64_t>(scaled);
      if(move>=stress_bps_) {
        const auto deadline=ts>std::numeric_limits<std::uint64_t>::max()-cooldown
            ?std::numeric_limits<std::uint64_t>::max():ts+cooldown;
        blocked_until_ns_=std::max(blocked_until_ns_,deadline);
      }
    }
    last_mid_=mid;
    if(ts<blocked_until_ns_) return false;
    if(has_signal_ && ts-last_signal_ns_<base_ns_) return false;
    has_signal_=true; last_signal_ns_=ts; return true;
  }
  std::uint64_t blocked_until_ns() const { return blocked_until_ns_; }
 private:
  std::uint64_t base_ns_,max_ns_; double stress_bps_;
  std::uint64_t last_signal_ns_=0,blocked_until_ns_=0,last_timestamp_ns_=0;
  double last_mid_=0.0;
  bool has_signal_=false,has_timestamp_=false;
};
class OcoStopLimit {
 public:
  OcoStopLimit(double entry,double stop_bps,double offset_bps)
    :stop_price_(entry*(1.0-stop_bps/10000.0)),limit_price_(stop_price_*(1.0-offset_bps/10000.0)) {
    if(!std::isfinite(entry)||!std::isfinite(stop_bps)||!std::isfinite(offset_bps)||
       entry<=0||stop_bps<=0||stop_bps>=10000||offset_bps<0||offset_bps>=10000)
      throw std::invalid_argument("invalid stop order");
  }
  bool observe(double mid) {
    if(!std::isfinite(mid)||mid<=0) throw std::invalid_argument("mid must be positive and finite");
    if(triggered_) return false;
    if(mid<=stop_price_) { triggered_=true; marketable_=mid>=limit_price_; return true; }
    return false;
  }
  bool triggered() const { return triggered_; }
  bool marketable() const { return marketable_; }
  double stop_price() const { return stop_price_; }
  double limit_price() const { return limit_price_; }
 private:
  double stop_price_,limit_price_; bool triggered_=false,marketable_=false;
};
} // namespace sentinel
