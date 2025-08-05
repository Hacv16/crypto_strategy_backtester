import json
import os

from src.data_handler import DataHandler
from src.backtest_runner import BacktestRunner
from src.strategy_factory import create_strategy


# Define the path to the JSON strategies file
configs_dir = "configs"
strategies_file_name = "strategies.json"
strategies_file_path = os.path.join(configs_dir, strategies_file_name)

# Get data using data handler
handler = DataHandler(exchange_name="binance", currency="USDT")
ohlcv_data = handler.load_or_fetch_and_process_data(crypto_symbol='ETH', timeframe='1d', since_days=200)

# Load strategies from JSON file and run them
try:
    with open(strategies_file_path, 'r') as strategies_json:
        strategies = json.load(strategies_json)

        for strategy_name, config_dict in strategies.items():
            strategy = create_strategy(config_dict)
            signals_df = strategy.apply_strategy(ohlcv_data)
            data_for_backtest = ohlcv_data.join(signals_df)

            backtester = BacktestRunner(data_for_backtest, initial_balance=10000.0, transaction_fee=0.001,
                                        take_profit_pct=0.20, stop_loss_pct=0.10)

            backtest_results, trade_logs = backtester.run()
            final_capital = backtest_results['total_capital'].iloc[-1]
            print(f"{strategy_name}'s return: {final_capital - 10000.0:.2f} USD")


except FileNotFoundError:
    print(f"Error: Strategies file not found at {strategies_file_path}")
except json.JSONDecodeError:
    print(f"Error: Failed to decode JSON from {strategies_file_path}")
