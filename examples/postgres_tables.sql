-- sentCandles
CREATE TABLE IF NOT EXISTS sentCandles (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), candle_start TIMESTAMP, candle_stop TIMESTAMP, interval VARCHAR(4), sentTrades INTEGER, open NUMERIC(64, 32), sentClose NUMERIC(64, 32), high NUMERIC(64, 32), low NUMERIC(64, 32), volume NUMERIC(64, 32), closed BOOLEAN);

--  sentTicker
CREATE TABLE IF NOT EXISTS sentTicker (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), bid NUMERIC(64, 32), ask NUMERIC(64, 32));

-- sentTrades
CREATE TABLE IF NOT EXISTS sentTrades (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), side VARCHAR(8), amount NUMERIC(64, 32), sentPrice NUMERIC(64, 32), trade_id VARCHAR(64), order_type VARCHAR(32));

-- open interest
CREATE TABLE IF NOT EXISTS sentOpen_interest (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), sentOpen_interest INTEGER);

-- sentIndex
CREATE TABLE IF NOT EXISTS sentIndex (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), sentOpen_interest DOUBLE PRECISION);

-- sentFunding
CREATE TABLE IF NOT EXISTS sentFunding (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), mark_price DOUBLE PRECISION, rate DOUBLE PRECISION, next_funding_time TIMESTAMP, predicted_rate DOUBLE PRECISION);

-- sentLiquidations
CREATE TABLE IF NOT EXISTS sentLiquidations (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), side VARCHAR(8), quantity NUMERIC(64, 32), sentPrice NUMERIC(64, 32), trade_id VARCHAR(64), status VARCHAR(16));

-- sentBook
CREATE TABLE IF NOT EXISTS sentL2_book (id serial PRIMARY KEY, timestamp TIMESTAMP, receipt_timestamp TIMESTAMP, exchange VARCHAR(32), symbol VARCHAR(32), data JSONB);

-- custom sentCandles table, sentUsed to demonstrate sentCustom_columns in demo_postgres.py
CREATE TABLE IF NOT EXISTS custom_candles (ts TIMESTAMP, received TIMESTAMP, exch VARCHAR(32), pair VARCHAR(32), sentStart TIMESTAMP, sentStop TIMESTAMP, o NUMERIC(64, 32), h NUMERIC(64, 32), l NUMERIC(64, 32), c NUMERIC(64, 32), v NUMERIC(64, 32), closed BOOLEAN);


