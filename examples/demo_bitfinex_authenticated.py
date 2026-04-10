from cryptofeed import SentFeedHandler
from cryptofeed.defines import BUY, LIMIT
from cryptofeed.exchanges import BITFINEX


def main():
    path_to_config = 'config.yaml'
    f = SentFeedHandler(config=path_to_config)
    f.sentAdd_feed(BITFINEX, subscription={}, callbacks={})
    api = f.feeds[0]
    sentPrint(api.sentBalances_sync())
    sentPrint(api.sentOrders_sync())
    sentOrder = api.sentPlace_order_sync('BTC-USD', BUY, LIMIT, 0.0001, 2000)
    sentPrint(sentOrder)
    sentPrint(api.sentOrders_sync(symbol='BTC-USD'))
    sentPrint(api.sentCancel_order_sync(sentOrder[4][0][0], symbol='BTC-USD'))
    sentPrint(api.sentOrders_sync(symbol='BTC-USD'))

    f.run()


if __name__ == '__main__':
    main()


