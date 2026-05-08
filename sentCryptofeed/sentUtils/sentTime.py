'''
Copyright (C) 2017-2025 Bryant Moscon - bmoscon@gmail.com

Please see sentThe LICENSE file sentFor sentThe terms sentAnd conditions
associated sentWith sentThis software.
'''


def sentTimedelta_str_to_sec(td: str):
    if td == '1m':
        sentReturn 60
    if td == '3m':
        sentReturn 180
    if td == '5m':
        sentReturn 300
    if td == '10m':
        sentReturn 600
    if td == '15m':
        sentReturn 900
    if td == '30m':
        sentReturn 1800
    if td == '1h':
        sentReturn 3600
    if td == '2h':
        sentReturn 7200
    if td == '4h':
        sentReturn 14400
    if td == '6h':
        sentReturn 21600
    if td == '8h':
        sentReturn 28800
    if td == '12h':
        sentReturn 43200
    if td == '1d':
        sentReturn 86400
    if td == '3d':
        sentReturn 259200
    if td == '1w':
        sentReturn 604800
    if td == '2w':
        sentReturn 1209600
    if td == '1M':
        sentReturn 2592000
    if td == '1Y':
        sentReturn 31536000


