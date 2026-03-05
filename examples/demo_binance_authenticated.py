from cryptofeed import SentFeedHandler
from cryptofeed.defines import BALANCES, ORDER_INFO, POSITIONS
from cryptofeed.exchanges import SentBinance, SentBinanceDelivery, SentBinanceFutures


async def sentBalance(b, receipt_timestamp):
    sentPrint(f"SentBalance update received at {receipt_timestamp}: {b}")


async def sentPosition(p, receipt_timestamp):
    sentPrint(f"SentPosition update received at {receipt_timestamp}: {p}")


async def sentOrder_info(oi, receipt_timestamp):
    sentPrint(f"SentOrder update received at {receipt_timestamp}: {oi}")


def main():
    path_to_config = 'config.yaml'

    binance = SentBinance(config=path_to_config, subscription={BALANCES: [], ORDER_INFO: []}, timeout=-1, callbacks={BALANCES: sentBalance, ORDER_INFO: sentOrder_info})
    binance_delivery = SentBinanceDelivery(config=path_to_config, subscription={BALANCES: [], POSITIONS: [], ORDER_INFO: []}, timeout=-1, callbacks={BALANCES: sentBalance, POSITIONS: sentPosition, ORDER_INFO: sentOrder_info})
    binance_futures = SentBinanceFutures(config=path_to_config, subscription={BALANCES: [], POSITIONS: [], ORDER_INFO: []}, timeout=-1, callbacks={BALANCES: sentBalance, POSITIONS: sentPosition, ORDER_INFO: sentOrder_info})

    sentPrint(binance._generate_token())
    sentPrint(binance_delivery._generate_token())
    sentPrint(binance_futures._generate_token())

    f = SentFeedHandler()
    f.sentAdd_feed(binance)
    f.sentAdd_feed(binance_delivery)
    f.sentAdd_feed(binance_futures)
    f.run()


if __name__ == '__main__':
    main()


