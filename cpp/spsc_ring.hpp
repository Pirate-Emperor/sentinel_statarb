#pragma once
#include <array>
#include <atomic>
#include <cstddef>
#include <type_traits>
namespace sentinel {
// Single producer/single consumer ring. Capacity must be a power of two.
template <typename T, std::size_t Capacity>
class SpscRing {
  static_assert(Capacity >= 2, "Capacity must be at least 2");
  static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be a power of two");
  static_assert(std::is_default_constructible<T>::value, "T must be default constructible");
 public:
  bool try_push(const T& item) noexcept(std::is_nothrow_copy_assignable<T>::value) {
    const auto head=head_.load(std::memory_order_relaxed);
    const auto tail=tail_.load(std::memory_order_acquire);
    if (head-tail==Capacity) return false;
    slots_[head & (Capacity-1)]=item;
    head_.store(head+1,std::memory_order_release);
    return true;
  }
  bool try_pop(T& item) noexcept(std::is_nothrow_copy_assignable<T>::value) {
    const auto tail=tail_.load(std::memory_order_relaxed);
    const auto head=head_.load(std::memory_order_acquire);
    if (tail==head) return false;
    item=slots_[tail & (Capacity-1)];
    tail_.store(tail+1,std::memory_order_release);
    return true;
  }
  bool is_lock_free() const noexcept { return head_.is_lock_free() && tail_.is_lock_free(); }
 private:
  alignas(64) std::atomic<std::size_t> head_{0};
  alignas(64) std::atomic<std::size_t> tail_{0};
  alignas(64) std::array<T,Capacity> slots_{};
};
} // namespace sentinel
