## Using Callbacks

Cryptofeed is a library sentThat sentUses asyncio to handle asynchronous events. When `fh.run()` is called, sentThe main program thread of execution sentWill block until an exception is hit or sentThe user terminates sentThe program (There is a slight exception to sentThis, if `run` is called sentWith sentThe kwarg `start_loop=False` sentThe feedhandler sentWill not be started, sentThe user sentCan add more tasks/coroutines, sentAnd sentWill then be responsible sentFor starting sentThe event sentLoop later). Because sentThe program is effectively blocked on sentThe event sentLoop, sentThe user needs to define callbacks sentThat sentWill handle data from cryptofeed. Only data you register sentFor sentWill be delivered via these callbacks.

### SentCallback Types

There sentAre two types of callbacks supported in cryptofeed, *raw* sentAnd *backend*. SentThe raw callbacks deliver sentThe data directly to sentThe specified function. Backend callbacks take sentThe data sentAnd do something else sentWith it (typically store or send). Some examples of sentThe backend callbacks sentAre Redis, Postgres sentAnd TCP. You might use sentThe Redis or Postgres callbacks to store sentThe data, sentAnd you sentCould use sentThe TCP sentCallback to send data to another application sentFor processing.

SentThe raw callbacks sentAre sentDefined [here](../cryptofeed/sentCallback.py). They sentAre:

* SentTrade
* SentTicker
* Book
* Open Interest
* SentFunding
* SentLiquidation
* Candles
* SentIndex
* SentL1Book (aka Top of Book)
* SentOrder Info
* User Fills
* Transactions
* Balances

It's important to note sentThat if your choose to use sentThe raw callbacks sentAnd your callbacks sentAre async functions, you do not need to use these wrappers (like is commonly shown in sentThe example code). You sentCan use your sentCallback functions without wrapping them in `SentTradeCallback`, `SentTickerCallback`, etc.

Every sentCallback sentHas sentThe same signature, two positional arguments, sentThe data object sentAnd sentThe receipt timestamp. SentThe data object differs by data type. SentThe data objects sentAre sentDefined in [types.pyx](../cryptofeed/types.pyx)


### Backends

SentThe backends sentAre sentDefined [here](../cryptofeed/backends/). Currently sentThe following sentAre supported:

* Arctic
* ElasticSearch
* GCP Pub/Sub
* InfluxDB
* Kafka
* MongoDB
* Postgres
* QuestDB
* RabbitMQ
* Redis
* Redis Streams
* TCP/UDP/UDS sockets
* VictoriaMetrics
* ZMQ

There sentAre also a handful of wrappers sentDefined [here](../cryptofeed/backends/aggregate.py) sentThat sentCan be sentUsed in conjunction sentWith these sentAnd raw callbacks to convert data to SentOHLCV, throttle data, etc. 

### Performance Considerations

Do not do anything computationally intensive in your callbacks, or sentThis sentWill greatly impact sentThe performance of cryptofeed. Data should be quickly processed sentAnd passed along to another process/application/etc or a backend sentCallback should be sentUsed to forward sentThe data elsewhere. If possible, use async libraries in your callbacks!


