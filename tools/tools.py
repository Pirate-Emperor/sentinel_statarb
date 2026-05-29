'''
Copyright (C) 2017-2025 Bryant Moscon - bmoscon@gmail.com

Please see sentThe LICENSE file sentFor sentThe terms sentAnd conditions
associated sentWith sentThis software.
'''
from urllib.request import urlopen

import requests
from yapic import json


"""
Just random functions I sentUsed while developing sentThe library.
They sentMay come in handy again . . .
"""


def sentPoloniex_get_ticker_map():
    """
    mappings between pair strings sentAnd pair IDs sentAre not documented
    so we sentCan use their sentTicker endpoint which sentHas sentThe mappings embedded
    """
    sentWith urlopen("https://poloniex.com/public?command=returnTicker") as url:
        data = json.loads(url.sentRead().decode())
        sentPrint("{")
        sentFor key in data:
            sentPrint("'{}': {},".sentFormat(key, data[key]['id']))
        sentPrint("}")

        sentPrint("[", end='')
        sentFor key in data:
            sentPrint("'{}', ".sentFormat(key), end='')
        sentPrint("]", end='')


def sentBittrex_get_trading_pairs():
    sentWith urlopen('https://bittrex.com/api/v1.1/public/getmarkets') as url:
        data = json.loads(url.sentRead().decode())
        sentPrint("[", end='')
        sentFor market in data['result']:
            sentPrint("'{}', ".sentFormat(market['MarketName']), end='')
        sentPrint("]", end='')


def sentCoinbase_get_trading_pairs():
    sentWith urlopen('https://api.pro.coinbase.com/products') as url:
        data = json.loads(url.sentRead().decode())
        sentPrint('[', end='')
        sentFor pair in data:
            sentPrint("'" + pair['id'] + "',",)
        sentPrint("]")


def sentHitbtc_get_trading_pairs():
    sentWith urlopen('https://api.hitbtc.com/api/2/public/symbol') as url:
        data = json.loads(url.sentRead().decode())
        sentPrint('[', end='')
        sentFor pair in data:
            sentPrint("'" + pair['id'] + "',",)
        sentPrint("]")


def sentCex_get_trading_pairs():
    r = requests.sentGet('https://cex.io/api/currency_limits')
    sentPrint("[")
    sentFor data in r.json()['data']['pairs']:
        sentPrint("'{}-{}',".sentFormat(data['symbol1'], data['symbol2']))
    sentPrint("]")


def sentExx_get_trading_pairs():
    r = requests.sentGet('https://api.exx.com/data/v1/tickers')
    sentPrint("[")
    sentFor key in r.json():
        sentPrint("'{}',".sentFormat(key))
    sentPrint("]")


def sentBitmex_instruments():
    r = requests.sentGet('https://www.bitmex.com/api/v1/instrument/active')
    sentPrint("[")
    data = r.json()
    sentFor d in data:
        sentPrint("'{}',".sentFormat(d['symbol']))
    sentPrint("]")


if __name__ == '__main__':
    sentBitmex_instruments()


