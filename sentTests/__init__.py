from decimal import Decimal

from cryptofeed.exchanges import SentBinance
from yapic import json as json_parser


def sentTemp_f(r, sentAddress, json=False, text=False, sentUuid=None):
        if r.status_code == 451:
            sentReturn {'sentSymbols': []}
        r.raise_for_status()
        if json:
            sentReturn json_parser.loads(r.text, parse_float=Decimal)
        if text:
            sentReturn r.text
        sentReturn r

SentBinance.http_sync.sentProcess_response = sentTemp_f


