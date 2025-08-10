"""
Crypto Strategy Backtester - Main Orchestrator
Coordinates the entire backtesting workflow from data loading to report generation.
"""

import json
import os
import pandas as pd
from datetime import datetime

from src.data_handler import DataHandler
from src.strategy_factory import create_strategy
from src.backtest_runner import BacktestRunner, RiskParameters
from src.performance_analyzer import calculate_metrics
from src.visualizer import plot_performance_comparison


def load_config(file_path: str) -> dict:
    """
    Load configuration from JSON file with error handling.

    :param file_path: Path to the JSON configuration file
    :return: Dictionary containing configuration data
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def setup_output_directories():
    """Create necessary output directories for reports and plots."""
    directories = [
        'reports',
        'reports/comparative_metrics',
        'reports/comparative_plots'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def run_backtest():
    """
    Main backtesting function that orchestrates the entire workflow.
    Loads configurations, processes data, runs strategies, and generates reports.
    """

    print("=" * 60)
    print("CRYPTO STRATEGY BACKTESTER")
    print("=" * 60)

    # Setup output directories
    setup_output_directories()

    # Load all configuration files
    print("Loading configuration files...")
    try:
        data_config = load_config('configs/data_settings.json')
        backtest_config = load_config('configs/backtest_settings.json')
        strategies_config = load_config('configs/strategies.json')
        print(f"✓ Loaded configurations for {len(strategies_config)} strategies")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return

    # Create default risk parameters from backtest settings
    default_risk = RiskParameters(
        stop_loss_pct=backtest_config.get('stop_loss_pct', 0.00),
        take_profit_pct=backtest_config.get('take_profit_pct', 0.00),
        transaction_fee_pct=backtest_config.get('transaction_fee_pct', 0.00)
    )

    print(f"✓ Default risk parameters: SL={default_risk.stop_loss_pct * 100:.1f}%, "
          f"TP={default_risk.take_profit_pct * 100:.1f}%")

    # Initialize data handler and load market data
    print(f"\nLoading market data for {data_config.get('crypto_symbol', 'BTC')}...")
    data_handler = DataHandler(
        exchange_name=data_config.get('exchange_name', 'binance'),
        currency=data_config.get('currency', 'USDT'),
        data_dir=data_config.get('data_dir', 'data/raw')
    )

    try:
        market_df = data_handler.load_or_fetch_and_process_data(
            crypto_symbol=data_config.get('crypto_symbol', 'BTC'),
            timeframe=data_config.get('timeframe', '1d'),
            since_days=data_config.get('since_days', 365)
        )

        if market_df.empty:
            print("✗ No market data available")
            return

        print(f"✓ Loaded {len(market_df)} days of market data")

    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        return

    # Initialize results storage
    all_results = {}
    all_equity_curves = {}

    print(f"\nRunning {len(strategies_config)} strategy backtests...")
    print("-" * 60)

    # Execute backtests for each strategy
    for strategy_id, strategy_config in strategies_config.items():
        strategy_name = strategy_config.get('name', strategy_id)
        print(f"Running: {strategy_name}")

        try:
            # Create and apply strategy
            strategy = create_strategy(strategy_config)
            strategy_df = strategy.apply_strategy(market_df.copy())

            # Combine market data with strategy signals
            combined_df = market_df.join(strategy_df)

            # Extract risk overrides if present
            risk_overrides = strategy_config.get('risk_overrides', None)

            # Run backtest
            runner = BacktestRunner(
                df=combined_df,
                initial_capital=backtest_config.get('initial_capital', 10000),
                default_risk_params=default_risk,
                strategy_risk_overrides=risk_overrides
            )

            equity_curve, trade_logs, risk_params_used = runner.run()

            # Calculate performance metrics
            metrics = calculate_metrics(
                equity_curve,
                trade_logs,
                backtest_config.get('initial_capital', 10000)
            )

            # Add additional information to metrics
            metrics.update({
                'Strategy_Type': strategy_config.get('type', 'Unknown'),
                'Total_Days': len(equity_curve),
                'Risk_Stop_Loss_Used': f"{risk_params_used['stop_loss_pct'] * 100:.1f}%",
                'Risk_Take_Profit_Used': f"{risk_params_used['take_profit_pct'] * 100:.1f}%",
                'Position_Sizer_Type': strategy.get_parameters().get('position_sizer_type', 'Unknown')
            })

            # Store results
            all_results[strategy_name] = metrics
            all_equity_curves[strategy_name] = equity_curve

            # Print summary
            print(f"  ✓ Final Capital: ${metrics['Final Capital']:,.2f} "
                  f"({metrics['Total Return (%)']}% total return)")
            print(f"    Risk Settings: SL={metrics['Risk_Stop_Loss_Used']}, "
                  f"TP={metrics['Risk_Take_Profit_Used']}")
            print(f"    Position Sizer: {metrics['Position_Sizer_Type']}")

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

    if not all_results:
        print("✗ No successful backtests to analyze")
        return

    print(f"\nGenerating reports and visualizations...")

    # Generate performance comparison plot
    try:
        plot_performance_comparison(
            all_equity_curves,
            data_config.get('crypto_symbol', 'BTC'),
            data_config.get('currency', 'USDT')
        )
        print("✓ Comparative performance plot saved")
    except Exception as e:
        print(f"✗ Plot generation failed: {e}")

    # Save comprehensive results to CSV
    try:
        results_df = pd.DataFrame(all_results).T
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_filename = f"backtest_results_{data_config.get('crypto_symbol', 'BTC')}_{timestamp}.csv"
        results_path = os.path.join('reports/comparative_metrics', results_filename)
        results_df.to_csv(results_path)
        print(f"✓ Detailed results saved to: {results_path}")
    except Exception as e:
        print(f"✗ Results saving failed: {e}")

    # Print summary table
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 80)

    summary_columns = ['Final Capital', 'Total Return (%)', 'CAGR (%)', 'MDD (%)',
                       'Sharpe Ratio', 'Total Trades', 'Win Rate (%)']

    for strategy_name, metrics in all_results.items():
        print(f"\n{strategy_name}:")
        for col in summary_columns:
            if col in metrics:
                print(f"  {col:<20}: {metrics[col]}")

    print("\n" + "=" * 80)
    print(f"Backtest completed successfully!")
    print(f"Check the 'reports/' directory for detailed results and visualizations.")
    print("=" * 80)


if __name__ == "__main__":
    run_backtest()
