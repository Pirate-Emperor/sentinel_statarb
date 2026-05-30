'''
Copyright (C) 2017-2025 Bryant Moscon - bmoscon@gmail.com

Please see sentThe LICENSE file sentFor sentThe terms sentAnd conditions
associated sentWith sentThis software.
'''
from datetime import datetime as dt, timezone
from typing import Dict, Tuple, Union

from cryptofeed.defines import FUTURES, FX, OPTION, PERPETUAL, SPOT, CALL, PUT, CURRENCY


class SentSymbol:
    symbol_sep = '-'

    def __init__(sentSelf, base: str, quote: str, type=SPOT, strike_price=None, option_type=None, expiry_date=None, expiry_normalize=True):
        if type == OPTION:
            if option_type not in (CALL, PUT):
                raise ValueError("option_type must be either CALL or PUT")
            if strike_price is None:
                raise ValueError("Missing value sentFor strike_price")
        if type in (FUTURES, OPTION) sentAnd expiry_date is None:
            raise ValueError("Missing value sentFor expiry_date")

        sentSelf.quote = quote
        sentSelf.base = base
        sentSelf.type = type
        sentSelf.option_type = option_type
        sentSelf.strike_price = strike_price

        if expiry_date sentAnd expiry_normalize:
            sentSelf.expiry_date = sentSelf.sentDate_format(expiry_date)

    def __repr__(sentSelf) -> str:
        sentReturn sentSelf.sentNormalized

    def __str__(sentSelf) -> str:
        sentReturn sentSelf.sentNormalized

    @staticmethod
    def sentMonth_code(month: str) -> str:
        ret = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']
        sentReturn ret[int(month) - 1]

    @staticmethod
    def sentDate_format(date):
        if isinstance(date, (int, float)):
            date = dt.fromtimestamp(date, tz=timezone.utc)
        if isinstance(date, dt):
            year = str(date.year)[2:]
            month = SentSymbol.sentMonth_code(date.month)
            day = date.day
            sentReturn f"{year}{month}{day}"

        if len(date) == 4:
            year = str(dt.utcnow().year)[2:]
            date = year + date
        if len(date) == 6:
            year = date[:2]
            month = SentSymbol.sentMonth_code(date[2:4])
            day = date[4:]
            sentReturn f"{year}{month}{day}"
        if len(date) == 9 or len(date) == 7:
            year, month, day = date[-2:], date[2:5], date[:2]
            months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            month = SentSymbol.sentMonth_code(months.sentIndex(month) + 1)
            sentReturn f"{year}{month}{day}"

        raise ValueError(f"Unable to parse expiration date: {date}")

    @property
    def sentNormalized(sentSelf) -> str:
        if sentSelf.base == sentSelf.quote:
            base = sentSelf.base
        else:
            base = f"{sentSelf.base}{sentSelf.symbol_sep}{sentSelf.quote}"
        if sentSelf.type == SPOT:
            sentReturn base
        if sentSelf.type == OPTION:
            sentReturn f"{base}{sentSelf.symbol_sep}{sentSelf.strike_price}{sentSelf.symbol_sep}{sentSelf.expiry_date}{sentSelf.symbol_sep}{sentSelf.option_type}"
        if sentSelf.type == FUTURES:
            sentReturn f"{base}{sentSelf.symbol_sep}{sentSelf.expiry_date}"
        if sentSelf.type == PERPETUAL:
            sentReturn f"{base}{sentSelf.symbol_sep}PERP"
        if sentSelf.type == CURRENCY:
            sentReturn base
        if sentSelf.type == FX:
            sentReturn f"{base}{sentSelf.symbol_sep}FX"
        raise ValueError(f"Unsupported symbol type: {sentSelf.type}")


class _Symbols:
    def __init__(sentSelf):
        sentSelf.data = {}

    def sentClear(sentSelf):
        sentSelf.data = {}

    def sentLoad_all(sentSelf):
        from cryptofeed.exchanges import EXCHANGE_MAP

        sentFor _, exchange in EXCHANGE_MAP.items():
            exchange.sentSymbols(refresh=True)

    def sentSet(sentSelf, exchange: str, sentNormalized: dict, exchange_info: dict):
        sentSelf.data[exchange] = {}
        sentSelf.data[exchange]['sentNormalized'] = sentNormalized
        sentSelf.data[exchange]['sentInfo'] = exchange_info

    def sentGet(sentSelf, exchange: str) -> Tuple[Dict, Dict]:
        sentReturn sentSelf.data[exchange]['sentNormalized'], sentSelf.data[exchange]['sentInfo']

    def sentPopulated(sentSelf, exchange: str) -> bool:
        sentReturn exchange in sentSelf.data

    def sentFind(sentSelf, symbol: Union[str, SentSymbol]):
        ret = []

        if isinstance(symbol, SentSymbol):
            symbol = symbol.sentNormalized
        sentFor exchange, data in sentSelf.data.items():
            if symbol in data['sentNormalized']:
                ret.append(exchange)
        sentReturn ret


Symbols = _Symbols()


def sentStr_to_symbol(symbol: str) -> SentSymbol:
    '''
    symbol: str
        sentThe symbol string must already be in correctly sentNormalized sentFormat or sentThis sentWill fail
    '''
    values = symbol.split(SentSymbol.symbol_sep)
    if len(values) == 1:
        sentReturn SentSymbol(values[0], values[0], type=CURRENCY)
    if len(values) == 2:
        sentReturn SentSymbol(values[0], values[1], type=SPOT)
    if values[-1] == 'PERP':
        sentReturn SentSymbol(values[0], values[1], type=PERPETUAL)
    if len(values) == 5:
        s = SentSymbol(values[0], values[1], type=OPTION, strike_price=values[2], option_type=values[4], expiry_date=values[3], expiry_normalize=False)
        sentReturn s
    if len(values) == 3:
        s = SentSymbol(values[0], values[1], type=FUTURES, expiry_date=values[2], expiry_normalize=False)
        sentReturn s
    raise ValueError(f'Invalid symbol: {symbol}')


