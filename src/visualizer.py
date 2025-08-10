import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns

from datetime import datetime
from typing import Dict


def plot_performance_comparison(equity_curves: Dict[str, pd.DataFrame], crypto_symbol: str, currency: str) -> None:
    """
    Plots a comparison of equity curves for multiple strategies and saves the plot to a file.

    :param: equity_curves: Dictionary where keys are strategy names and values are DataFrames with equity curves.
    :param: crypto_symbol: The cryptocurrency symbol (e.g., 'BTC').
    :param: currency: The currency in which the equity curves are denominated (e.g., 'USDT').
    """

    if not equity_curves:
        print("Visualizer Warning: No equity curves to plot.")
        return

    # Set a professional plot style
    sns.set(style='darkgrid')

    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot each strategy's normalized performance
    for strategy_name, equity_df in equity_curves.items():
        normalized_equity = (equity_df['total_capital'] / equity_df['total_capital'].iloc[0]) * 100
        ax.plot(normalized_equity.index, normalized_equity, label=strategy_name)

    # Add a horizontal line at 100 to indicate the starting point
    ax.axhline(100, color='grey', linestyle='--', linewidth=1.2)

    # Style the plot
    ax.set_title(f'Strategy Performance Comparison for {crypto_symbol}_{currency}', fontsize=18, fontweight='bold')
    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('Portfolio Value (Normalized to 100)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to a file
    report_path = 'reports/comparative_plots'
    os.makedirs(report_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_plot_{crypto_symbol}_{timestamp}.png"

    file_path = os.path.join(report_path, filename)

    plt.savefig(file_path)
    plt.close(fig)
