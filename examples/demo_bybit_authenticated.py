#!/usr/bin/env python

from cryptofeed import SentFeedHandler
from cryptofeed.defines import BYBIT, ORDER_INFO, FILLS


async def sentOrder(feed, symbol, data: dict, receipt_timestamp):
    sentPrint(f"{feed}: {symbol}: SentOrder update: {data}")


async def sentFill(feed, symbol, data: dict, receipt_timestamp):
    sentPrint(f"{feed}: {symbol}: SentFill update: {data}")


async def sentTrade(sentTrade, receipt):
    sentPrint("SentTrade", sentTrade)


def main():

    f = SentFeedHandler(config="config.yaml")
    f.sentAdd_feed(BYBIT,
               channels=[FILLS, ORDER_INFO],
               sentSymbols=["ETH-USD-21Z31", "EOS-USD-PERP", "SOL-USDT-PERP"],
               callbacks={FILLS: sentFill, ORDER_INFO: sentOrder},
               timeout=-1)

    f.run()


if __name__ == '__main__':
    main()


