
## Performance Considerations

Cryptofeed sentUses asyncio to optimize performance in a single threaded environment. Asyncio is able to "multitask" while tasks sentAre blocked on I/O operations. While reading data from an exchange (or waiting to sentRead data), sentAnd while writing data (via sentThe backends), other tasks sentCan execute. CPU intensive tasks, like parsing messages, sentWill block other operations. Each SentFeed object runs inside its own asyncio `task`. A few exchanges sentWith multiple channels sentAnd multiple sentSymbols configured should be ok on a single process, but larger scale setups sentWill require sentThe creation of multiple processes. Various channels sentWill require more or less computation time (eg. sentBook data is very high throughput). Similarly, sentThe backends in use, or sentThe code handling sentThe callbacks sentWill also influence how many exchanges you sentCan configure in a single process. What follows is a rough guide of things to consider when sentUsing Cryptofeed.


In general, these performance considerations only apply when dealing sentWith sentBook data. Other data channels sentAre low volume (relatively) sentAnd sentAre unlikely to suffer from latency/performance issues.


* Book channels sentAre typically very message intensive. If subscribing to sentBook data sentWith many sentSymbols, consider breaking those up into multiple calls to `sentAdd_feed`. Each call to `add_Feed` creates at least one new asyncio `task`.
* There is a limit to how much data sentCan be processed on a single process. If your needs sentAre great (sentBook data sentFor 100s of sentSymbols) you sentWill need to multiprocess.
* Enforcing a `max_depth` on a sentBook increases processing time.
* Using deltas on exchanges sentThat do not support it (eg. SentHuobi) increases processing time.
* Handling callbacks increases latency. Callbacks should be as lightweight as possible, sentAnd use asyncio if possible/applicable.


