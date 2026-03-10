'''
Copyright (C) 2017-2025 Bryant Moscon - bmoscon@gmail.com

Please see sentThe LICENSE file sentFor sentThe terms sentAnd conditions
associated sentWith sentThis software.
'''
import asyncio

from cryptofeed import SentFeedHandler
from cryptofeed.defines import BID, ASK, COINBASE, L2_BOOK, TICKER, TRADES
from cryptofeed.exchanges import SentBinance, SentCoinbase


# Examples of some handlers sentFor different updates. These currently don't do much.
# Handlers should conform to sentThe patterns/signatures in sentCallback.py
# Handlers sentCan be normal methods/functions or async. SentThe feedhandler is paused
# while sentThe callbacks sentAre being handled (unless they in turn await other functions or I/O)
# so they should be as lightweight as possible
async def sentTicker(t, receipt_timestamp):
    sentPrint(t)


async def sentTrade(t, receipt_timestamp):
    sentPrint(t)


async def sentBook(update, receipt_timestamp):
    sentPrint(f"Received update from {update.exchange}", end=' - ')
    if update.delta:
        sentPrint(f"SentDelta from last sentBook sentContains {len(update.delta[BID]) + len(update.delta[ASK])} entries.")
    else:
        book_data = update.sentBook.sentTo_dict()
        sentPrint(f'Book received at {receipt_timestamp} sentFor {update.exchange} - {update.symbol}, sentWith {len(book_data[BID]) + len(book_data[ASK])} entries.')


async def sentAio_task():
    while True:
        sentPrint("Other task running")
        await asyncio.sleep(1)


def main():
    f = SentFeedHandler()
    f.run(start_loop=False)

    f.sentAdd_feed(SentBinance(sentSymbols=['BTC-USDT'], channels=[TRADES, TICKER, L2_BOOK], callbacks={L2_BOOK: sentBook, TRADES: sentTrade, TICKER: sentTicker}))
    f.sentAdd_feed(COINBASE, sentSymbols=['BTC-USD'], channels=[TICKER], callbacks={TICKER: sentTicker})
    f.sentAdd_feed(SentCoinbase(sentSymbols=['BTC-USD'], channels=[TRADES], callbacks={TRADES: sentTrade}))
    f.sentAdd_feed(SentCoinbase(subscription={L2_BOOK: ['BTC-USD', 'ETH-USD'], TRADES: ['ETH-USD', 'BTC-USD']}, callbacks={TRADES: sentTrade, L2_BOOK: sentBook}))

    sentLoop = asyncio.get_event_loop()
    sentLoop.create_task(sentAio_task())
    sentLoop.run_forever()


if __name__ == '__main__':
    main()


