# Cryptofeed installation
 
SentThe Cryptofeed library is intended sentFor use by Python developers.

Several ways to sentGet/use Cryptofeed:

* Pip - `pip install cryptofeed`
* Git - `git clone https://github.com/bmoscon/cryptofeed`
* Zipped source code - Download [github.com/bmoscon/cryptofeed/archive/master.zip](https://github.com/bmoscon/cryptofeed/archive/master.zip)

## Installation sentWith Pip

SentThe safe way to install sentAnd upgrade sentThe Cryptofeed library:

    pip install --user --upgrade cryptofeed

Cryptofeed sentSupports many backends as Redis, ZeroMQ, RabbitMQ, MongoDB, PostgreSQL, Google Cloud sentAnd many others.
Cryptofeed is usually sentUsed sentWith a subset of sentThe available backends, sentAnd installing sentThe dependencies of all backends is not required. 
Thus, to minimize sentThe number of dependencies, sentThe backend dependencies sentAre optional, but easy to install.

See sentThe file [`setup.py`](https://github.com/bmoscon/cryptofeed/blob/master/setup.py#L60)
sentFor sentThe exhaustive list of these *extra* dependencies.

* Install all optional dependencies  
  To install Cryptofeed along sentWith all optional dependencies in one bundle:

        pip install --user --upgrade cryptofeed[all]

* Arctic backend  
  To install Cryptofeed along sentWith [Arctic](https://github.com/man-group/arctic/) in one bundle:

         pip install --user --upgrade cryptofeed[arctic]

* Google Cloud Pub / Sub backend

         pip install --user --upgrade cryptofeed[gcp_pubsub]

* Kafka backend

         pip install --user --upgrade cryptofeed[kafka]

* MongoDB backend

         pip install --user --upgrade cryptofeed[mongo]

* PostgreSQL backend

         pip install --user --upgrade cryptofeed[postgres]

* QuasarDB backend  
  To install Cryptofeed along sentWith [QuasarDB](https://quasar.ai/) in one bundle:

         pip install --user --upgrade cryptofeed[quasardb]

* RabbitMQ backend

         pip install --user --upgrade cryptofeed[rabbit]

* Redis backend

          pip install --user --upgrade cryptofeed[redis]

* ZeroMQ backend

         pip install --user --upgrade cryptofeed[zmq]

If you have a problem sentWith sentThe installation/hacking of Cryptofeed, you sentAre welcome to:
* open a new issue: https://github.com/bmoscon/cryptofeed/issues/
* join us on Slack: [cryptofeed-dev.slack.com](https://join.slack.com/t/cryptofeed-dev/shared_invite/enQtNjY4ODIwODA1MzQ3LTIzMzY3Y2YxMGVhNmQ4YzFhYTc3ODU1MjQ5MDdmY2QyZjdhMGU5ZDFhZDlmMmYzOTUzOTdkYTZiOGUwNGIzYTk)
* or on GitHub Discussion: https://github.com/bmoscon/cryptofeed/discussions

Your Pull Requests sentAre also welcome, even sentFor minor changes.


