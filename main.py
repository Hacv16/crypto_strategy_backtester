import json
import os

from src.data_handler import DataHandler
from src.strategy_engine import StrategyEngine

# Define the path to the JSON strategies file
configs_dir = "configs"
strategies_file_name = "strategies.json"
strategies_file_path = os.path.join(configs_dir, strategies_file_name)

# Load strategies from JSON file and run them
try:
    with open(strategies_file_path, 'r') as strategies_json:
        strategies = json.load(strategies_json)
        print(strategies)
except FileNotFoundError:
    print(f"Error: Strategies file not found at {strategies_file_path}")
except json.JSONDecodeError:
    print(f"Error: Failed to decode JSON from {strategies_file_path}")


handler = DataHandler(exchange_name="binance", currency="USDT")
data = handler.load_or_fetch_and_process_data(crypto_symbol='XRP', timeframe='1d', since_days=30)

SMA_Engine = StrategyEngine(strategy_type="SMA", short_window=3, long_window=5)
SMA_strategy = SMA_Engine.apply_strategy(data)




