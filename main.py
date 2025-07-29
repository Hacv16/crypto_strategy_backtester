import pandas as pd
from src.data_handler import DataHandler
from src.strategy_engine import StrategyEngine

handler = DataHandler(exchange_name="binance", currency="USDT")
data = handler.load_or_fetch_and_process_data(crypto_symbol='XRP', timeframe='1d', since_days=30)

SMA_Engine = StrategyEngine(strategy_type="SMA", short_window=3, long_window=5)
SMA_strategy = SMA_Engine.apply_strategy(data)

# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)


