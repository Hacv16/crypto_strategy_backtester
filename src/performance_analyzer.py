import pandas as pd
import numpy as np


def calculate_metrics(equity_curve: pd.DataFrame, trade_log: list, initial_capital: float) -> dict:
    """
    Calculates performance metrics from the equity curve and trade log.

    :param: equity_curve: DataFrame containing the equity curve with a 'total_capital' column.
    :param: trade_log: List of dictionaries containing trade details.
    :param: initial_capital: Initial capital at the start of the backtest.
    :return: Dictionary containing calculated performance metrics.
    """

    metrics = {}
    capital_series = equity_curve['total_capital']

    # Overall Performance
    metrics['Final Capital'] = round(capital_series.iloc[-1], 2)

    total_return = ((metrics['Final Capital'] - initial_capital) / initial_capital)
    metrics['Total Return (%)'] = round(total_return * 100.0, 2)

    time_span_days = (capital_series.index[-1] - capital_series.index[0]).days
    number_of_years = time_span_days / 365.25

    if number_of_years > 0:
        cagr = ((1 + total_return) ** (1 / number_of_years) - 1) * 100
        metrics['CAGR (%)'] = round(cagr, 2)
    else:
        metrics['CAGR (%)'] = 'N/A'

    # Risk Metrics
    running_maximum_capital = capital_series.cummax()
    mdd_series = (capital_series - running_maximum_capital) / running_maximum_capital
    mdd = mdd_series.min()
    metrics['MDD (%)'] = round(mdd * 100, 2)

    daily_returns = equity_curve['total_capital'].pct_change().dropna()

    if daily_returns.std() > 0:
        average_daily_return = daily_returns.mean()
        std_dev_daily_return = daily_returns.std()
        metrics['Sharpe Ratio'] = round((average_daily_return / std_dev_daily_return) * np.sqrt(365), 2)
    else:
        metrics['Sharpe Ratio'] = 0.0

    # Trade metrics
    metrics['Total Trades'] = len(trade_log)
    metrics['Winning Trades'] = sum(1 for trade in trade_log if trade['cash_profit'] > 0)
    metrics['Win Rate (%)'] = round((metrics['Winning Trades'] / metrics['Total Trades']) * 100, 2) \
        if metrics['Total Trades'] > 0 else 0.0

    total_profit = sum(trade['cash_profit'] for trade in trade_log if trade['cash_profit'] > 0)
    total_loss = abs(sum(trade['cash_profit'] for trade in trade_log if trade['cash_profit'] < 0))

    if total_loss > 0:
        metrics['Profit Factor'] = round(total_profit / total_loss, 2)
    elif total_profit > 0:
        metrics['Profit Factor'] = np.inf
    else:
        metrics["Profit Factor"] = 0.0

    return metrics
