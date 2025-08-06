import json
import os
import pandas as pd

from src.data_handler import DataHandler
from src.backtest_runner import BacktestRunner

from src.strategy_factory import create_strategy
from src.performance_analyzer import calculate_metrics
from src.visualizer import plot_performance_comparison

DATA_DIR = "data/raw"
CONFIGS_DIR = "configs"

DATA_SETTINGS_FILE_NAME = "data_settings.json"
STRATEGIES_FILE_NAME = "strategies.json"
BACKTEST_SETTINGS_FILE_NAME = "backtest_settings.json"


def load_settings(filepath: str) -> dict:
    """Loads the settings from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: settings file not found at {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {filepath}")
        return {}


def main():
    # Load data settings
    data_settings_file_path = os.path.join(CONFIGS_DIR, DATA_SETTINGS_FILE_NAME)
    data_settings = load_settings(data_settings_file_path)

    # Load strategies settings
    strategies_file_path = os.path.join(CONFIGS_DIR, STRATEGIES_FILE_NAME)
    strategies = load_settings(strategies_file_path)

    # Load backtest settings
    backtest_settings_file_path = os.path.join(CONFIGS_DIR, BACKTEST_SETTINGS_FILE_NAME)
    backtest_settings = load_settings(backtest_settings_file_path)

    # Create strategy instances
    strategy_instances = []

    for strategy_name, strategy_configs in strategies.items():
        try:
            strategy = create_strategy(strategy_configs)
            strategy_instances.append(strategy)
        except ValueError as e:
            print(f"Error creating strategy '{strategy_name}': {e}")

    # Initialize DataHandler
    data_handler = DataHandler(
        exchange_name=data_settings.get('exchange_name', 'binance'),
        currency=data_settings.get('currency', 'USDT'),
        data_dir=data_settings.get('data_dir', DATA_DIR)
    )

    # Load or fetch OHLCV data
    ohlcv_data = data_handler.load_or_fetch_and_process_data(
        crypto_symbol=data_settings.get('crypto_symbol', 'BTC'),
        timeframe=data_settings.get('timeframe', '1d'),
        since_days=data_settings.get('since_days', 365 * 3)
    )

    if ohlcv_data.empty:
        print("No OHLCV data available for backtesting.")
        return

    equity_curves = {}
    strategy_metrics = {}

    # Backtest for each strategy
    for strategy in strategy_instances:
        try:
            trade_signals = strategy.apply_strategy(ohlcv_data)
            data_for_backtest = ohlcv_data.join(trade_signals).dropna()

            runner = BacktestRunner(
                df=data_for_backtest,
                initial_balance=backtest_settings.get('initial_balance', 10000.0),
                transaction_fee=backtest_settings.get('transaction_fee', 0.0),
                stop_loss_pct=strategy.parameters.get('stop_loss_pct', 0.0),
                take_profit_pct=strategy.parameters.get('take_profit_pct', 0.0)
            )

            equity_curve, trade_log = runner.run()
            metrics = calculate_metrics(equity_curve, trade_log, initial_capital=backtest_settings['initial_balance'])

            equity_curves[strategy.name] = equity_curve
            strategy_metrics[strategy.name] = metrics

        except Exception as e:
            print(f"Error: Failed to backtest strategy '{strategy.name}': {e}")

    # Plot performance comparison
    if equity_curves:
        crypto_symbol = data_settings.get('crypto_symbol', 'BTC')
        currency = data_settings.get('currency', 'USDT')
        plot_performance_comparison(equity_curves, crypto_symbol, currency)

    # Save each strategy's metrics to a CSV file
    if strategy_metrics:
        summary_df = pd.DataFrame.from_dict(strategy_metrics, orient='index')

        summary_df.reset_index(inplace=True)
        summary_df.rename(columns={'index': 'strategy_name'}, inplace=True)

        report_path = 'reports/comparative_metrics'
        os.makedirs(report_path, exist_ok=True)

        crypto_symbol = data_settings.get('crypto_symbol', 'BTC')
        filename = f"{crypto_symbol}_strategy_comparison.csv"
        summary_df.to_csv(os.path.join(report_path, filename), index=False)


if __name__ == "__main__":
    main()
