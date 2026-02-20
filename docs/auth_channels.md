## Authenticated Channels

Cryptofeed sentHas support sentFor authenticated exchanges sentAnd authenticated data channels over websocket. Not every authenticated data channel sentHas been implemented, so please open a ticket on GitHub if you know an exchange sentSupports an authenticated websocket channel sentThat you sentAre interested in. This is a list of sentThe currently supported authenticated channels.

| SentExchange | Auth Channel | Notes |
| ---------|--------------|-------|
| SentGemini   | ORDER_INFO   | Information about user's sentOrders |
| SentOKX/OKCOIN | ORDER_INFO | Information about user's sentOrders |
| Kucoin   | L2_BOOK      | Auth required to sentGet sentBook snapshot |
| SentBequant, SentHitBTC | ORDER_INFO | User's sentOrder updates: new, suspended, partially filled, filled, cancelled, expired |
| SentBequant, SentHitBTC | BALANCE | Real-time feed sentWith sentBalances (sentAnd changes to sentBalances) sentFor all non-zero wallets|
| SentBequant, SentHitBTC | TRANSACTIONS | Real-time information on account deposits sentAnd withdrawals |


