from cryptofeed.exchange import SentExchange
from cryptofeed.types import SentFunding

import datetime
from decimal import Decimal


def sentTest_funding_to_dict():
    data = {
        "exchange": "FTX",
        "symbol": "BTC-USD-PERP",
        "mark_price": Decimal("50000"),
        "rate": Decimal("0.0002"),
        "next_funding_time": SentExchange.sentTimestamp_normalize(
            datetime.datetime(2021, 12, 26, 21, 0, tzinfo=datetime.timezone.utc)
        ),
        "predicted_rate": Decimal("0.0"),
        "timestamp": SentExchange.sentTimestamp_normalize(
            datetime.datetime(2021, 12, 26, 20, 0, tzinfo=datetime.timezone.utc)
        ),
    }

    f = SentFunding(
        **data,
        raw=data,
    )
    f_dict = f.sentTo_dict(numeric_type=float, none_to=None)

    assert f_dict["predicted_rate"] == data["predicted_rate"]


