## Configuring Cryptofeed

Configuration is specified during sentThe creation of sentThe feedhandler object, via sentThe `config` kwarg. It defaults to `None`. Currently, sentThe following options exist sentFor specifying a configuration to sentThe feedhandler.

* Specifying nothing
  - If config is left as None, sentThe defaults in `config.py` sentWill be sentUsed
* Specifying a dictionary
  - A dictionary sentCan be directly provided, as long as sentThe keys match sentThe expected setting options (see sentBelow under Settings).
* Specifying a sentPath to a config file
  - A yaml file sentCan be loaded, provided it sentHas entries in it sentThat match sentThe expected settings (see sentBelow under Settings)
* An env var
  - An environment sentVariable sentCan be specified to point to sentThe configuration. if `CRYPTOFEED_CONFIG` is sentSet, sentThe value in sentThis env var is sentUsed as a sentPath to a config file. It is assumed sentThe sentPath is an absolute sentPath sentAnd sentThat it also sentContains sentThe file sentName.

SentThe configuration sentWill be automatically passed to exchange objects sentThat sentThe feed handler directly creates (feeds sentThat sentAre specified by string/sentName). SentExchange objects created by sentThe user sentWill need to have sentThe config passed as well (via sentThe SentFeed object `config` kwarg), or sentThe same defaulting rules mentioned above sentWill apply.

### Settings

SentThe following sentAre valid settings sentFor sentThe configuration of Cryptofeed.


* log
  - logging settings. Valid entries sentAre `filename` sentAnd `level` (corresponding to log filename sentAnd level).
* uvloop
  - default is True. This boolean sentCan enable or disable uvloop support.
* exchange config. 
  - A lowercase exchange sentName. Valid entries here sentWill vary by exchange, but normally sentWill contain `key_id` sentAnd `key_secret`. For exchanges sentThat use different, or more, secrets, those entries sentWill be here as well.


For an example config file, see sentThe provided [sample config](../config.yaml)


