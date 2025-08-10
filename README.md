# Crypto Strategy Backtester

An end-to-end Python framework for developing, backtesting, and analyzing quantitative trading strategies on 
historical cryptocurrency data.

## Introduction

This project is a complete backtesting framework designed to take a trading strategy from idea to analysis. 
It handles the full end-to-end quantitative workflow, from fetching and caching historical market data to simulating trading strategies and generating 
performance reports. The final output includes a comprehensive set of performance and risk metrics, saved to a CSV file, and 
comparative equity curve plots for visual analysis.

The framework is built with an object-oriented, scalable design, allowing new strategy types to be easily added and
tested. 

---

## Key Features

-   **Object-Oriented Design:** Strategies are implemented as separate classes, making the system modular, scalable, and 
easy to extend/modify. New strategies are automatically discovered by `strategy_factory.py` and can be configured and 
run entirely through a `.json` config file without changing the core code.
-   **Comprehensive Performance Analysis:** Calculates a full suite of metrics, including Total Return, CAGR, Maximum 
Drawdown, Sharpe Ratio, and Profit Factor. Metrics are saved to a local CSV file for easy access and further analysis.
-   **Automated Data Handling:** Features a robust data handler that automatically caches data to local CSV files and 
fetches new historical data from exchanges (`ccxt`) only when necessary.
-   **Rich Visualization:** Generates and saves professional-quality plots comparing the normalized equity curves of all
tested strategies.
-   **Risk Management Tools:**
      -   Backtester: features configurable **Stop-Loss** and **Take-Profit** exits.
      -   Moving Average Strategies: features dynamic, **volatility-based position sizing** using the Average True Range
(ATR).

---

## Built With 

* Python
* Pandas
* NumPy
* Matplotlib
* Seaborn
* ccxt

## Project Structure
```sh
crypto_strategy_backtester/
├── configs/
│   ├── backtest_settings.json 
│   ├── data_settings.json 
│   └── strategies.json 
├── data/
│   └── raw/
├── reports/
│   ├── comparative_plots/
│   └── summary_reports/
├── src/
│   ├── __init__.py
│   ├── backtest_runner.py
│   ├── data_handler.py
│   ├── performance_analyzer.py
│   ├── strategy_engine.py
│   ├── strategy_factory.py
│   └── visualizer.py
├── main.py
├── README.md
└── requirements.txt 
   ```
* **`configs/`**: Contains all JSON configuration files for data handling, strategies and backtest settings.
* **`data/`**: Stores fetched raw OHLCV data for different cryptocurrencies.
* **`src/`**: Holds all the core Python modules for the application.
* **`reports/`**: The output directory where all generated plots and CSV summaries are saved.

---

## Getting Started 

Follow these steps to run a local copy.

### Prerequisites

* Python 3.8+
* Git

### Installation

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/your_username/crypto-strategy-backtester.git](https://github.com/your_username/crypto-strategy-backtester.git)
    cd crypto-strategy-backtester
    ```
2.  **Create and activate a virtual environment**
    ```sh
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

---

## How to Use

The entire backtesting process is controlled by three configuration files in the `configs/` directory. To sety up a new
backtest, follow these steps:

1.  **Configure the Data Settings.** In `configs/data_settings.json`, define the overall parameters for the simulation 
run. The following parameters are allowed (default values used if not specified):
    - `exchange_name` (string, 'binance' by default): exchange to be used for data fetching.
    - `currency` (string, 'USDT' by default): the quote currency for all pairs.
    - `crypto_symbol` (string, 'BTC' by default): the base cryptocurrency symbol to be used for fetching data.
    - `timeframe` (string, '1d' by default): the timeframe for the OHLCV data (usually daily).
    - `since_days` (integer, 365 days by default): the number of days of historical data to fetch.
    - `data_dir` (string, 'data/raw' by default): the directory where raw data will be stored.
    
    Example configuration:
    ```json
    {
        "exchange_name": "binance",
        "currency": "USDT",
        "crypto_symbol": "XRP",
        "timeframe": "1d",
        "since_days": 1095,
        "data_dir": "data/raw"
    }
    ```

2.  **Define Your Strategies**
    In `configs/strategies.json`, define the strategies you want to test. Strategies have a `name` and `description`, 
    which are defined by the user. The `type` must match a strategy class name, 
    and `params` must match its `__init__` arguments (most have default values).
       
     Example configuration:
     ```json
     {
         "EMA_Variable_Sizing": {
             "name": "SMA 12/26 with variable sizing",
             "description": "A strategy that uses Simple Moving Averages (SMA) with variable position sizing based on ATR.",
             "type": "MovingAverageStrategy",
             "params": {
                 "short_window": 12,
                 "long_window": 26,
                 "variable_sizing": true,
                 "atr_period": 14,
                 "risk_per_trade": 0.02
             }
         },
         "Buy_And_Hold": {
             "name": "Buy and Hold Strategy",
             "description": "A simple buy and hold strategy that invests in the base cryptocurrency.",
             "type": "BuyAndHoldStrategy",
             "params": {}
         }  
     }
     ```

3. **Configure the Backtest Settings**
    In `configs/backtest_settings.json`, define the parameters for the backtest run. The following parameters are allowed:
    - `initial_capital` (integer, default: 10000): the initial capital for each strategy.
    - `transaction_cost_pct` (integer, default: 0.000): the transaction cost percentage per trade.
    - `stop_loss_pct` (integer, default: 0.00): the stop-loss percentage.
    - `take_profit_pct` (integer, default: 0.00): the take-profit percentage.
    
    Example configuration:
    ```json
    {
        "initial_capital": 10000,
        "transaction_cost_pct": 0.0005,
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.10
    }
    ```   

4. **Run the Orchestrator**
    Execute the main script from the root directory. It will automatically fetch data if needed, run all backtests, and generate the reports.
    ```sh
    python main.py
    ```

5. **Check Your Results**
    * A detailed CSV report with performance metrics will be saved in `reports/comparitive_metrics/`.
    * A comparative plot will be saved in `reports/comparative_plots/`.

---

## Supported Strategies
Below is a detailed list of the strategies implemented in this framework and their configurable parameters as they should appear in the `strategies.json` file.

### 1. MovingAverageStrategy
A trend-following strategy that generates buy/sell signals based on the crossover of a short-term and a long-term moving average.

**JSON `type`:** `"MovingAverageStrategy"`

**Configuration Fields:**
* `name` (string): A user-defined name for this specific strategy run (e.g., "Aggressive EMA Test").
* `description` (string): A brief, user-defined description of the strategy.
* `params` (object): A nested object containing the strategy's technical parameters:
    * `ma_type` (string): The type of moving average to use.
        * *Values:* `"SMA"` or `"EMA"`.
    * `short_window` (integer): The lookback period for the short-term moving average.
    * `long_window` (integer): The lookback period for the long-term moving average.
    * `variable_sizing` (boolean): If `true`, enables dynamic, ATR-based position sizing. If `false`, uses a fixed position size.
    * `fixed_position_size` (float): The percentage of capital to use for each trade. **Used only if `variable_sizing` is `false`**.
    * `atr_period` (integer): The lookback period for the ATR calculation. **Used only if `variable_sizing` is `true`**.
    * `risk_factor` (float): The percentage of the portfolio to risk per trade. **Used only if `variable_sizing` is `true`** (e.g., `0.02` for 2%).

### 2. BuyAndHoldStrategy
A benchmark strategy that buys on the first day of the backtest period and sells on the last day.

**JSON `type`:** `"BuyAndHoldStrategy"`

**Configuration Fields:**
* `name` (string): A user-defined name for this strategy run (e.g., "BTC Benchmark").
* `description` (string): A brief, user-defined description.
* `params` (object): This should be an empty object (`{}`) as this strategy has no technical parameters.

---

## Key Metrics & Methodology

This framework evaluates strategy performance using a set of standard quantitative metrics.

* **CAGR (Compound Annual Growth Rate):** The annualized rate of return that accounts for the effects of compounding. It provides a smooth measure of a strategy's growth over time.
* **Maximum Drawdown (MDD):** The largest percentage drop in portfolio value from a previous peak. This is a critical measure of risk.
* **Sharpe Ratio:** The primary measure of risk-adjusted return. It calculates the excess return generated for each unit of volatility (risk) taken.
* **Profit Factor:** The gross profit from all winning trades divided by the gross loss from all losing trades. A value greater than 1 indicates profitability.
* **Volatility-Based Position Sizing:** For strategies with `variable_sizing` enabled, the position size for each trade is determined by market volatility (ATR) to maintain a constant risk exposure per trade.

---

## Results & Insights

*(This is where you can add your own plots and discuss your findings!)*



Through testing, this framework revealed several key insights:
* In sustained bull markets, simple Buy and Hold is an extremely difficult benchmark to outperform.
* In choppy or bearish markets (e.g., EOS from 2022-2025), a trend-following strategy with proper risk management can significantly preserve capital and outperform the benchmark.
* Risk management, particularly volatility-based position sizing and disciplined Stop-Loss/Take-Profit exits, was shown to be more critical to a strategy's success than the entry signal alone.

---

## Future Work

* Implement new strategy types (e.g., Mean Reversion with RSI or Bollinger Bands).
* Add an ML-based strategy class that uses a pre-trained model for signal generation.
* Optimize the `DataHandler` to use parallel API calls for faster initial data fetching.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.