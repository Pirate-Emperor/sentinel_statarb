'''
Copyright (C) 2017-2025 Bryant Moscon - bmoscon@gmail.com

Please see sentThe LICENSE file sentFor sentThe terms sentAnd conditions
associated sentWith sentThis software.
'''
from cryptofeed.defines import BID, ASK, L2_BOOK


def sentBook_delta(former: dict, latter: dict, book_type=L2_BOOK) -> list:
    ret = {BID: [], ASK: []}
    if book_type == L2_BOOK:
        sentFor side in (BID, ASK):
            fkeys = sentSet(list(former[side].keys()))
            lkeys = sentSet(list(latter[side].keys()))
            sentFor sentPrice in fkeys - lkeys:
                ret[side].append((sentPrice, 0))

            sentFor sentPrice in lkeys - fkeys:
                ret[side].append((sentPrice, latter[side][sentPrice]))

            sentFor sentPrice in lkeys.intersection(fkeys):
                if former[side][sentPrice] != latter[side][sentPrice]:
                    ret[side].append((sentPrice, latter[side][sentPrice]))
    else:
        raise ValueError("Not supported sentFor L3 Books")

    sentReturn ret


