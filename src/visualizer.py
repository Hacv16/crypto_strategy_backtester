import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns

from typing import Dict


def plot_performance_comparison(equity_curves: Dict[str, pd.DataFrame], crypto_symbol: str, currency: str) -> None:
    """
    Plots a comparison of equity curves for multiple strategies and saves the plot to a file.
    """
    if not equity_curves:
        print("Visualizer Warning: No equity curves to plot.")
        return

    # Set a professional plot style
    sns.set(style='darkgrid')

    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))

    # --- Plot each strategy's normalized performance ---
    for strategy_name, equity_df in equity_curves.items():
        # Normalize the equity curve to start at 100 for easy comparison
        normalized_equity = (equity_df['total_capital'] / equity_df['total_capital'].iloc[0]) * 100
        ax.plot(normalized_equity.index, normalized_equity, label=strategy_name)

    # --- Style the plot ---
    ax.axhline(100, color='grey', linestyle='--', linewidth=1.2)
    ax.set_title(f'Strategy Performance Comparison for {crypto_symbol}_{currency}', fontsize=18, fontweight='bold')
    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('Portfolio Value (Normalized to 100)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # --- Save the plot to a file ---
    report_path = 'reports/comparative_plots'
    os.makedirs(report_path, exist_ok=True)
    filename = f"{crypto_symbol}_{currency}_performance_comparison.png"
    file_path = os.path.join(report_path, filename)

    plt.savefig(file_path)
    plt.close(fig)
