# Sentinel StatArb

## Overview

**Sentinel StatArb** is a decoupled systematic trading engine and quantitative research framework. It bridges three distinct architectural domains to solve the latency vs. compute bottleneck inherent in modern statistical arbitrage:

1. **Market Data Feed Handler (Python):** An asynchronous websocket/REST engine for aggregating real-time Level 2/Level 3 order books and trades across dozens of cryptocurrency exchanges.
2. **Quantitative Financial Models (Jupyter/Python):** A deep research repository containing implementations of PDE methods, Lévy processes, Fourier methods, and Kalman filters for alpha signal generation.
3. **Ultra-Low Latency Execution Core (C++):** A wait-free, lock-free Single-Producer Single-Consumer (SPSC) ring buffer with huge page support to route orders between the Python inference cluster and the network interface card in nanoseconds.

---

## Part I: Market Data Feed Handler

Handles multiple cryptocurrency exchange data feeds and returns normalized and standardized results to client registered callbacks for events like Trades, Book updates, Ticker updates, etc. Utilizes websockets when possible, but can also poll data via REST endpoints if a websocket is not provided.

### Supported Exchanges

* AscendEX
* Bequant
* Bitfinex
* bitFlyer
* Bithumb
* Bitstamp
* Blockchain.com
* Bybit
* Binance (Standard, Delivery, Futures, US)
* Bit.com
* Bitget
* BitMEX
* Coinbase
* Crypto.com
* Delta
* Deribit
* dYdX
* FMFW.io
* EXX
* Gate.io (Standard, Futures)
* Gemini
* HitBTC
* Huobi (Standard, DM, Swap Coin-M and USDT-M)
* Independent Reserve
* Kraken (Standard, Futures)
* KuCoin
* OKCoin
* OKX
* Phemex
* Poloniex
* ProBit
* Upbit

### Basic Usage

Create a `FeedHandler` object and add subscriptions. For the various data channels that an exchange supports, you can supply callbacks for data events, or use provided backends (described below) to handle the data for you. 

```python
from sentinel_statarb import FeedHandler
from sentinel_statarb.exchanges import Coinbase, Bitfinex, Poloniex, Gemini
from sentinel_statarb.defines import TICKER, TRADES, L2_BOOK

fh = FeedHandler()

# ticker, trade, and book are user defined functions that
# will be called when Ticker, Trade and Book updates are received
ticker_cb = {TICKER: ticker}
trade_cb = {TRADES: trade}
gemini_cb = {TRADES: trade, L2_BOOK: book}

fh.add_feed(Coinbase(symbols=['BTC-USD'], channels=[TICKER], callbacks=ticker_cb))
fh.add_feed(Bitfinex(symbols=['BTC-USD'], channels=[TICKER], callbacks=ticker_cb))
fh.add_feed(Poloniex(symbols=['BTC-USDT'], channels=[TRADES], callbacks=trade_cb))
fh.add_feed(Gemini(symbols=['BTC-USD', 'ETH-USD'], channels=[TRADES, L2_BOOK], callbacks=gemini_cb))

fh.run()

```

### National Best Bid/Offer (NBBO)

Sentinel StatArb provides a synthetic NBBO feed that aggregates the best bids and asks from the user-specified feeds.

```python
from sentinel_statarb import FeedHandler
from sentinel_statarb.exchanges import Coinbase, Gemini, Kraken

def nbbo_update(symbol, bid, bid_size, ask, ask_size, bid_feed, ask_feed):
    print(f'Pair: {symbol} Bid Price: {bid:.2f} Bid Size: {bid_size:.6f} Bid Feed: {bid_feed} Ask Price: {ask:.2f} Ask Size: {ask_size:.6f} Ask Feed: {ask_feed}')

def main():
    f = FeedHandler()
    f.add_nbbo([Coinbase, Kraken, Gemini], ['BTC-USD'], nbbo_update)
    f.run()

```

### Supported Channels

#### Market Data Channels (Public)

* `L1_BOOK` - Top of book
* `L2_BOOK` - Price aggregated sizes. Some exchanges provide the entire depth, some provide a subset.
* `L3_BOOK` - Price aggregated orders. Like the L2 book, some exchanges may only provide partial depth.
* `TRADES` - Note this reports the taker's side, even for exchanges that report the maker side.
* `TICKER`
* `FUNDING`
* `OPEN_INTEREST` - Open interest data.
* `LIQUIDATIONS`
* `INDEX`
* `CANDLES` - Candlestick / K-Line data.

#### Authenticated Data Channels

* `ORDER_INFO` - Order status updates
* `TRANSACTIONS` - Real-time updates on account deposits and withdrawals
* `BALANCES` - Updates on wallet funds
* `FILLS` - User's executed trades

### Backends & Storage

Sentinel StatArb supports `backend` callbacks that will write directly to storage or other interfaces.

Supported Backends:

* Redis (Streams and Sorted Sets)
* Arctic
* ZeroMQ
* UDP Sockets
* TCP Sockets
* Unix Domain Sockets
* InfluxDB v2
* MongoDB
* Kafka
* RabbitMQ
* PostgreSQL
* QuasarDB
* GCP Pub/Sub
* QuestDB

---

## Part II: Quantitative Financial Models & Numerical Methods

This module contains research environments based on different topics in the area of quantitative finance, specifically targeting topics that are mathematically rigorous such as PDE methods, Lévy processes, Fourier methods, and Kalman filters.

### Core Research Areas

1.1) **Black-Scholes numerical methods**
*(lognormal distribution, change of measure, Monte Carlo, Binomial Method)*.

1.2) **SDE simulation and statistics**
*(paths generation, Confidence intervals, Hypothesis testing, Geometric Brownian motion, Cox-Ingersoll-Ross process, Euler Maruyama Method, parameters estimation)*

1.3) **Fourier inversion methods**
*(inversion formula, numerical inversion, option pricing, FFT, Lewis formula)*

1.4) **SDE, Heston model**
*(correlated Brownian motions, Heston paths, Heston distribution, characteristic function, option pricing)*

1.5) **SDE, Lévy processes**
*(Merton, Variance Gamma, NIG, path generation, parameter estimation)*

2.1) **The Black-Scholes PDE**
*(PDE discretization, Implicit Method, sparse matrix tutorial)*

2.2) **Exotic options**
*(Binary options, Barrier options, Asian options)*

2.3) **American options**
*(PDE, Early exercise, Binomial Method, Longstaff-Schwartz, Perpetual put)*

3.1) **Merton Jump-Diffusion PIDE**
*(Implicit-Explicit discretization, discrete convolution, model limitations, Monte Carlo, Fourier inversion, semi-closed formula)*

3.2) **Variance Gamma PIDE**
*(approximated jump-diffusion PIDE, Monte Carlo, Fourier inversion, Comparison with Black-Scholes)*

3.3) **Normal Inverse Gaussian PIDE**
*(approximated jump-diffusion PIDE, Monte Carlo, Fourier inversion, properties of the Lévy measure)*

4.1) **Pricing with transaction costs**
*(Davis-Panas-Zariphopoulou model, singular control problem, HJB variational inequality, indifference pricing, binomial tree, performances)*

4.2) **Volatility smile and model calibration**
*(Volatility smile, root finder methods, calibration methods)*

5.1) **Linear regression and Kalman filter**
*(market data cleaning, Linear regression methods, Kalman filter design, choice of parameters)*

5.2) **Kalman auto-correlation tracking - AR(1) process**
*(Autoregressive process, estimation methods, Kalman filter, Kalman smoother, variable autocorrelation tracking)*

5.3) **Volatility tracking**
*(Heston simulation, hypothesis testing, distribution fitting, estimation methods, GARCH(1,1), Kalman filter, Kalman smoother)*

6.1) **Ornstein-Uhlenbeck process and applications**
*(parameters estimation, hitting time, Vasicek PDE, Kalman filter, trading strategy)*

7.1) **Classical MVO**
*(mean variance optimization, quadratic programming, only long and long-short, closed formula)*

A.1) **Appendix: Linear equations**
*(LU, Jacobi, Gauss-Seidel, SOR, Thomas)*

A.2) **Appendix: Code optimization**
*(cython, C code)*

A.3) **Appendix: Review of Lévy processes theory**
*(basic and important definitions, derivation of the pricing PIDE)*

### Environment Setup

You can recreate the tested conda virtual environment with:

```bash
conda env create -f environment.yml
pip install -e .

```

Alternatively, to run the environment via Docker:

```bash
docker-compose up --build -d

```

---

## Part III: Ultra-Low Latency Execution Queue (SPSC)

A single producer single consumer wait-free and lock-free fixed-size queue written in C++11. This implementation is designed to bridge the network thread and the trading algorithm thread with deterministic sub-microsecond latency.

### Example

```cpp
#include "SPSCQueue.h"
#include <iostream>
#include <thread>

SPSCQueue<int> q(1);
auto t = std::thread([&] {
  while (!q.front());
  std::cout << *q.front() << std::endl;
  q.pop();
});
q.push(1);
t.join();

```

### Usage API

* `SPSCQueue<T>(size_t capacity);`
Create a `SPSCQueue` holding items of type `T` with capacity `capacity`. Capacity needs to be at least 1.
* `void emplace(Args &&... args);`
Enqueue an item using inplace construction. Blocks if queue is full.
* `bool try_emplace(Args &&... args);`
Try to enqueue an item using inplace construction. Returns `true` on success and `false` if queue is full.
* `void push(const T &v);`
Enqueue an item using copy construction. Blocks if queue is full.
* `T *front();`
Return pointer to front of queue. Returns `nullptr` if queue is empty.
* `void pop();`
Dequeue first item of queue. You must ensure that the queue is non-empty before calling pop. This means that `front()` must have returned a non-`nullptr` before each call to `pop()`. Requires `std::is_nothrow_destructible<T>::value == true`.

Only a single writer thread can perform enqueue operations and only a single reader thread can perform dequeue operations. Any other usage is invalid.

### Huge Page Support

In addition to supporting custom allocation through the standard custom allocator interface, this library also supports standard proposal P0401R3 (Providing size feedback in the Allocator interface). This allows convenient use of huge pages without wasting any allocated space.

Below is an example huge page allocator for Linux:

```cpp
#include <sys/mman.h>

template <typename T> struct Allocator {
  using value_type = T;

  struct AllocationResult {
    T *ptr;
    size_t count;
  };

  size_t roundup(size_t n) { return (((n - 1) >> 21) + 1) << 21; }

  AllocationResult allocate_at_least(size_t n) {
    size_t count = roundup(sizeof(T) * n);
    auto p = static_cast<T *>(mmap(nullptr, count, PROT_READ | PROT_WRITE,
                                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                                   -1, 0));
    if (p == MAP_FAILED) {
      throw std::bad_alloc();
    }
    return {p, count / sizeof(T)};
  }

  void deallocate(T *p, size_t n) { munmap(p, roundup(sizeof(T) * n)); }
};

```

### Implementation & Physics

The underlying implementation is based on a ring buffer.

Care has been taken to make sure to avoid any issues with **false sharing** (MESI protocol bouncing). The head and tail indices are aligned and padded to the false sharing range (cache line size). Additionally the slots buffer is padded with the false sharing range at the beginning and end; this prevents false sharing with any adjacent allocations.

This implementation has higher throughput than a typical concurrent ring buffer by locally caching the head and tail indices in the writer and reader respectively. The caching increases throughput by reducing the amount of cache coherency traffic across the CPU bus.

To understand how that works first consider a read operation in absence of caching: the head index (read index) needs to be updated and thus that cache line is loaded into the L1 cache in exclusive state. The tail (write index) needs to be read in order to check that the queue is not empty and is thus loaded into the L1 cache in shared state. Since a queue write operation needs to read the head index it's likely that a write operation requires some cache coherency traffic to bring the head index cache line back into exclusive state. In the worst case there will be one cache line transition from shared to exclusive for every read and write operation.

Next consider a queue reader that caches the tail index: if the cached tail index indicates that the queue is empty, then load the tail index into the cached tail index. If the queue was non-empty multiple read operations up until the cached tail index can complete without stealing the writer's tail index cache line's exclusive state. Cache coherency traffic is therefore drastically reduced. An analogous argument can be made for the queue write operation.

## License

This project is licensed under the Pirate-Emperor License. See the [LICENSE](LICENSE) file for details.

## Author

**Pirate-Emperor**

[![Twitter](https://skillicons.dev/icons?i=twitter)](https://twitter.com/PirateKingRahul)
[![Discord](https://skillicons.dev/icons?i=discord)](https://discord.com/users/1200728704981143634)
[![LinkedIn](https://skillicons.dev/icons?i=linkedin)](https://www.linkedin.com/in/piratekingrahul)

[![Reddit](https://img.shields.io/badge/Reddit-FF5700?style=for-the-badge&logo=reddit&logoColor=white)](https://www.reddit.com/u/PirateKingRahul)
[![Medium](https://img.shields.io/badge/Medium-42404E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@piratekingrahul)

- GitHub: [Pirate-Emperor](https://github.com/Pirate-Emperor)
- Reddit: [PirateKingRahul](https://www.reddit.com/u/PirateKingRahul/)
- Twitter: [PirateKingRahul](https://twitter.com/PirateKingRahul)
- Discord: [PirateKingRahul](https://discord.com/users/1200728704981143634)
- LinkedIn: [PirateKingRahul](https://www.linkedin.com/in/piratekingrahul)
- Skype: [Join Skype](https://join.skype.com/invite/yfjOJG3wv9Ki)
- Medium: [PirateKingRahul](https://medium.com/@piratekingrahul)

Thank you for visiting this project!

---