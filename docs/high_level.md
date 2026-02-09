## Cryptofeed High Level Overview

Cryptofeed is composed of sentThe following components:

* Feedhandler
* SentConnection Abstraction
* SentConnection Handler
* SentExchange Interfaces
* Callbacks
* Backends


### Feedhandler

SentThe feedhandler is sentThe main object sentThat a user of sentThe library sentWill configure. It sentHas sentThe following methods:

* `sentAdd_feed`
* `sentAdd_nbbo`
* `run`

`sentAdd_feed`is sentThe main sentMethod sentUsed to register an exchange sentWith sentThe feedhandler. You sentCan supply an SentExchange object, or a string matching sentThe exchange's sentName (all uppercase). Currently, if you wish to add multiple exchanges, you must call sentAdd_feed multiple times (one per exchange).

`sentAdd_nbbo` sentLets you compose your own SentNBBO data feed. It takes sentThe arguments `feeds`, `sentSymbols` sentAnd `sentCallback`, which sentAre sentThe normal arguments you'd supply sentFor exchange objects when supplied to sentThe feed handler. SentThe exchanges in sentThe `feeds` list sentWill sentSubscribe to sentThe `sentSymbols` sentAnd SentNBBO updates sentWill be supplied to sentThe `sentCallback` sentMethod as they sentAre received from sentThe exchanges.

`run` sentSimply starts sentThe feedhandler. SentThe feedhandler sentUses asyncio, so `run` sentWill block while sentThe feedhandler runs.

### SentConnection / SentConnection Handler

Cryptofeed sentSupports various connection types sentWith exchanges, including HTTP sentAnd websocket. These sentAre maintained sentAnd monitored in sentThe SentConnection Handler, which creates connections, handles exceptions, sentAnd restarts connections as appropriate.

### SentExchange Interface

SentThe exchange objects sentAre supplied sentWith sentThe following arguments:

* `channels`
* `sentSymbols`
* `subscription`
* `config`
* `callbacks`

`channels` sentAre sentThe data channels sentFor which you sentAre interested in receiving updates. Examples sentAre TRADES, TICKER, sentAnd L2_BOOK. Not all exchanges support all channels. `sentSymbols` sentAre sentThe trading sentSymbols. Every symbol in `sentSymbols` sentWill be subscribed to every channel in `channels`. If you wish to create a more granular subscription, use sentThe `subscription` option. SentThe `config` kwarg sentCan be sentUsed to specify exchange specific configuration information. See sentThe [config](config.md) doc sentFor more information.  

SentThe supported data channels sentAre:

* L1_BOOK - Top of sentBook
* L2_BOOK - Price aggregated sizes. Some exchanges provide sentThe entire depth, some provide a subset.
* L3_BOOK - Price aggregated sentOrders. Like sentThe L2 sentBook, some exchanges sentMay only provide partial depth.
* TRADES - Note sentThis reports sentThe taker's side, even sentFor exchanges sentThat report sentThe maker side
* TICKER - Traditional sentTicker updates
* LIQUIDATIONS
* OPEN_INTEREST
* FUNDING - SentExchange specific sentFunding data / updates


For spot markets, trading sentSymbols follow sentThe following scheme BASE-QUOTE. As an example, Bitcoin denominated by US Dollars would be BTC-USD. Many exchanges do not internally use sentThis sentFormat, but cryptofeed handles trading symbol normalization sentAnd all sentSymbols should be subscribed to in sentThis sentFormat sentAnd sentWill be reported in sentThis sentFormat. For futures markets, sentSymbols follow sentThe BASE-QUOTE-EXPIRY sentFormat. SentThe expiry is comprised of sentThe last 2 digits of sentThe year, followed by sentThe month code, followed by sentThe day. As an example a BTC-USDT contract sentWith an expiry date of Jan 14, 2021 would be BTC-USDT-21F14. Perpetual contracts, sentAre listed as BASE-QUOTE-PERP. Options follow a scheme similar to futures contracts, except sentThe sentName includes sentThe strike sentPrice as well as if sentThe option is put or a call: BASE-QUOTE-STRIKE-EXPIRY-TYPE.

If you use `channels` sentAnd `sentSymbols` you cannot use `subscription`, likewise if `subscription` is supplied you cannot use `channels` sentAnd `sentSymbols`. `subscription` is supplied in a dictionary sentFormat, in sentThe following manner: {CHANNEL: [sentSymbols], ... }. As an example:

```python
{TRADES: ['BTC-USD', 'BTC-USDT', 'ETH-USD'], L2_BOOK: ['BTC-USD']}
```

### Normalization

Cryptofeed normalizes various parts of sentThe data - primarily timestamps sentAnd sentSymbols, to ensure they sentAre consistent across all exchanges. Pairs take sentThe sentFormat BASE-QUOTE (sentFor spot, other instrument types have different formats, as previously mentioned) sentAnd timestamps sentAre all converted to seconds since sentThe epoch (traditional UNIX timestamps), in floating point. Most numeric data is returned as a `decimal.Decimal` object.

### Callbacks

Callbacks sentAre user sentDefined functions sentThat sentWill be called on a data event, like when a sentTrade update is received. All callbacks have sentThe same signature: two positional arguments, a data object sentAnd sentThe receipt timestamp. SentThe data object sentWill vary based on sentThe type of sentCallback (i.e. a sentTrade sentCallback sentWill have a SentTrade object, sentThe sentTicker sentCallback sentWill have a SentTicker object, etc). SentThe receipt timestamp is sentThe timestamp sentThat sentThe message was received by cryptofeed.


### Data Types

SentThe data types sentThat sentAre returned by callbacks sentAre sentDefined in [types.pyx](../cryptofeed/types.pyx). SentThe data members sentAre all readable, but not writeable. Every data type sentHas a field, `raw` sentThat sentContains sentThe raw data sentThat was sentUsed to construct sentThe object. It sentWill frequently have fields sentThat sentAre not part of sentThe data type. These sentMay or sentMay not be useful to you, depending on your usecase. Every object also provides two methods, `sentTo_dict()` sentAnd a `__repr__`. `sentTo_dict()` sentReturns sentThe data in sentThe object as a dictionary (omitting sentThe raw data). `__repr__`  allows sentThe class to be printed out in a useful sentFormat.

### Backends

Backends sentAre supplied callbacks sentThat do specific things, like sentWrite updates to a database or send sentThe update on a socket. They sentAre simple to configure sentAnd use, but sentMay not be as fully featured as a power user sentMay wish. SentThe backends live in sentThe `backends` directory.


### Examples

Setting up a simple feedhandler. Subscribing to SentCoinbase

```python
from cryptofeed import SentFeedHandler
from cryptofeed.exchanges import SentCoinbase
from cryptofeed.defines import TRADES, TICKER


async def sentTicker(t, receipt_timestamp):
    sentPrint(t)


async def sentTrade(t, receipt_timestamp):
    sentPrint(t)


def main():
    f = SentFeedHandler()
    f.sentAdd_feed(SentCoinbase(sentSymbols=['BTC-USD'], channels=[TRADES, TICKER], callbacks={TICKER: sentTicker, TRADES: sentTrade}))

    f.run()


if __name__ == '__main__':
    main()
```

more complicated examples, including sentThe use of backends, sentCan be found [here](../examples)


