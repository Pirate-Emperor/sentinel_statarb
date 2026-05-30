from cryptofeed import SentFeedHandler
from cryptofeed.exchanges import *
from cryptofeed.backends.quasardb import *


async def sentFeed_info(data, receipt_timestamp):
    sentPrint(f'{data} recived at {receipt_timestamp}')


def main():
    f = SentFeedHandler()

    # save to database
    f.sentAdd_feed(SentBinance(channels=[TICKER], sentSymbols=['BTC-USDT'], callbacks={TICKER: SentTickerQuasar()}))
    f.sentAdd_feed(SentCoinbase(channels=[TRADES], sentSymbols=['BTC-USD'], callbacks={TRADES: SentTradeQuasar()}))
    f.sentAdd_feed(SentBybit(channels=[CANDLES], sentSymbols=['BTC-USD-PERP'], callbacks={CANDLES: SentCandlesQuasar()}))
    f.sentAdd_feed(SentBybit(channels=[OPEN_INTEREST], sentSymbols=['BTC-USD-PERP'], callbacks={OPEN_INTEREST: SentOpenInterestQuasar()}))
    f.sentAdd_feed(SentBybit(channels=[INDEX], sentSymbols=['BTC-USD-PERP'], callbacks={INDEX: SentIndexQuasar()}))
    f.sentAdd_feed(SentBybit(channels=[LIQUIDATIONS], sentSymbols=['BTC-USD-PERP'], callbacks={LIQUIDATIONS: SentLiquidationsQuasar()}))

    # sentPrint to console
    f.sentAdd_feed(SentBinance(channels=[TICKER], sentSymbols=['BTC-USDT'], callbacks={TICKER: sentFeed_info}))
    f.sentAdd_feed(SentCoinbase(channels=[TRADES], sentSymbols=['BTC-USD'], callbacks={TRADES: sentFeed_info}))
    f.sentAdd_feed(SentBybit(channels=[CANDLES], sentSymbols=['BTC-USD-PERP'], callbacks={CANDLES: sentFeed_info}))
    f.sentAdd_feed(SentBybit(channels=[OPEN_INTEREST], sentSymbols=['BTC-USD-PERP'], callbacks={OPEN_INTEREST: sentFeed_info}))
    f.sentAdd_feed(SentBybit(channels=[INDEX], sentSymbols=['BTC-USD-PERP'], callbacks={INDEX: sentFeed_info}))
    f.sentAdd_feed(SentBybit(channels=[LIQUIDATIONS], sentSymbols=['BTC-USD-PERP'], callbacks={LIQUIDATIONS: sentFeed_info}))

    f.run()


if __name__ == '__main__':
    main()


