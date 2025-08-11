# Crypto Strategy Backtester
An end-to-end Python framework for developing, backtesting, and analyzing quantitative trading strategies with comprehensive risk management, performance analytics, and visualization capabilities.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

## Key Features

### **Advanced Strategy Engine**
- **Modular Architecture**: Clean separation between trading signal generation and position sizing
- **Multiple Strategy Types**: Moving Average crossover (SMA/EMA), RSI mean reversion, Buy & Hold benchmark
- **Flexible Position Sizing**: Fixed percentage and ATR-based volatility sizing algorithms
- **Extensible Framework**: Easy addition of new strategies and position sizers through abstract base classes

### **Comprehensive Risk Management**
- **Configurable Risk Parameters**: Stop-loss, take-profit, and transaction fees through JSON configuration
- **Intraday Risk Execution**: Realistic stop-loss/take-profit using daily High/Low prices
- **Strategy-Level Overrides**: Individual risk parameter customization per strategy
- **Transaction Cost Modeling**: Accurate fee simulation for realistic backtesting

### **Professional Data Infrastructure**
- **Multi-Exchange Support**: Integration with 100+ exchanges via CCXT library
- **Intelligent Caching**: Local CSV storage with automatic data freshness validation
- **Robust Data Pipeline**: Comprehensive error handling and data quality assurance
- **Flexible Timeframes**: Support for multiple timeframes (1d, 4h, 1h, etc.)

### **Advanced Performance Analytics**
- **Comprehensive Metrics**: Total return, CAGR, maximum drawdown, Sharpe ratio, profit factor
- **Trade-Level Analysis**: Detailed entry/exit logging with win rate calculations  
- **Risk-Adjusted Returns**: Volatility-normalized performance measures
- **Comparative Analysis**: Multi-strategy performance benchmarking

### **Rich Visualization & Reporting**
- **Performance Charts**: Normalized equity curve comparisons across strategies
- **Professional Styling**: Publication-ready plots with Seaborn styling
- **Automated Reporting**: Timestamped CSV exports with comprehensive metrics
- **Organized Output**: Structured report directories for easy analysis

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-strategy-backtester.git
cd crypto-strategy-backtester
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run your first backtest:
```bash
python main.py
```

### Dependencies
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations  
- **ccxt**: Cryptocurrency exchange integration
- **matplotlib**: Plotting and visualization
- **seaborn**: Statistical data visualization

## Quick Start Guide

### Basic Usage
The framework is designed to be configuration-driven. Simply modify the JSON files in the `configs/` directory and run:

```bash
python main.py
```

### Configuration Files

**Data Configurations (`configs/data_settings.json`)** - Market data configuration:
- `exchange_name`: CCXT exchange identifier (binance, coinbase, kraken, etc.)
- `crypto_symbol`: Base cryptocurrency (BTC, ETH, XRP, etc.)
- `currency`: Quote currency (USDT, USD, EUR, etc.)
- `timeframe`: Data frequency (1d, 4h, 1h, 15m, etc.)
- `since_days`: Historical data period in days

Example:
```json
{
  "exchange_name": "binance",
  "currency": "USDT", 
  "crypto_symbol": "BTC",
  "timeframe": "1d",
  "since_days": 365
}
```

**Backtest Configurations (`configs/backtest_settings.json`)** - Capital and risk settings:
- `initial_capital`: Starting portfolio value
- `transaction_fee_pct`: Trading fee percentage (0.001 = 0.1%)
- `stop_loss_pct`: Default stop-loss percentage (0.02 = 2%)
- `take_profit_pct`: Default take-profit percentage (0.05 = 5%)

Example:
```json
{
  "initial_capital": 10000.0,
  "transaction_fee_pct": 0.001,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.10
}
```

**Strategy Definitions (`configs/strategies.json`**) - Strategy definitions:
- `name`: Display name for reports
- `type`: Strategy class name (MovingAverageStrategy, RSIStrategy, BuyAndHoldStrategy)
- `params`: Strategy-specific parameters
- `position_sizer`: Position sizing configuration
- `risk_overrides`: Optional risk parameter overrides

Example:
```json
{
  "SMA_Strategy": {
    "name": "SMA 12/26 Crossover",
    "type": "MovingAverageStrategy", 
    "params": {
      "ma_type": "SMA",
      "short_window": 12,
      "long_window": 26
    },
    "position_sizer": {
      "type": "FixedPositionSizer",
      "params": {"fixed_size_pct": 100.0}
    }
  }
}
```

## Project Structure

```
crypto_strategy_backtester/
├── configs/
│   ├── backtest_settings.json  # Risk parameters and capital settings
│   ├── data_settings.json      # Exchange and cryptocurrency selection
│   └── strategies.json         # Strategy definitions and parameters
├── data/                       # Market data storage
│   └── raw/                    # Raw OHLCV data from exchanges
├── reports/
│   ├── comparative_plots/      # Generated performance charts
│   └── comparative_metrics/    # CSV reports with detailed metrics
├── src/
│   ├── __init__.py
│   ├── backtest_runner.py      # Core backtesting engine with risk management
│   ├── data_handler.py         # Exchange integration and data management  
│   ├── performance_analyzer.py # Performance metrics calculation
│   ├── strategy_engine.py      # Strategy framework and implementations
│   ├── strategy_factory.py     # Dynamic strategy creation from configs
│   ├── position_sizer.py       # Position sizing algorithms
│   └── visualizer.py           # Chart generation and styling
├── main.py                     # Main orchestration script
├── README.md
└── requirements.txt            # Python dependencies
```

## Technical Implementation Highlights

### **Object-Oriented Design Patterns**

#### **Strategy Pattern** (Behavioral)
The core architecture uses the Strategy Pattern in two layers:
- **Trading Strategies**: `MovingAverageStrategy`, `RSIStrategy`, `BuyAndHoldStrategy` encapsulate different algorithms
- **Position Sizing**: `FixedPositionSizer`, `ATRPositionSizer` handle different risk management approaches
- Strategies are interchangeable at runtime through JSON configuration

#### **Factory Method Pattern** (Creational)  
- `create_strategy()` and `create_position_sizer()` dynamically instantiate objects from configurations
- Enables configuration-driven strategy selection without code changes

#### **Template Method Pattern** (Behavioral)
- `Strategy.apply_strategy()` defines the algorithm skeleton (generate signals → calculate positions)
- Subclasses implement specific details through `generate_signals()`

#### **Key Benefits**
- **Extensibility**: Add new strategies/position sizers without modifying existing code
- **Separation of Concerns**: Trading logic separated from risk management  
- **Configuration-Driven**: Runtime behavior controlled through JSON files
- **Testability**: Components can be unit tested in isolation

*Note: The Strategy Pattern emerged organically from avoiding conditional complexity - a natural discovery of established design principles.*

### **Intelligent Data Pipeline with Caching**
The data handler implements smart caching and multi-exchange support through CCXT integration:

```python
# Intelligent data freshness checking
if os.path.exists(file_path):
    df = self._load_data_from_csv(file_path)
    required_start_date = pd.to_datetime(dt.datetime.now() - dt.timedelta(days=since_days))
    
    if not df.empty and df.index[0] <= required_start_date:
        return df  # Use cached data if sufficient

# Multi-exchange support with rate limiting
self.exchange = exchange_class({'enableRateLimit': True})
```

**Key Benefits:**
- **Performance**: Avoids redundant API calls through intelligent caching
- **Flexibility**: CCXT integration supports 100+ cryptocurrency exchanges
- **Reliability**: Rate limiting prevents API throttling issues
- **Data Quality**: Automatic validation and preprocessing ensures clean datasets

### **Professional Error Handling System**
The framework implements comprehensive error handling with module-specific prefixes and graceful degradation:

```python
# Module-prefixed error messages for easy debugging
raise ValueError("Strategy Engine Error: Short window must be smaller than long window.")
raise ValueError("Data Handler Error: Exchange not found in ccxt.")

# Graceful strategy failure handling
try:
    strategy = create_strategy(strategy_config)
    # ... run backtest
except Exception as e:
    print(f"  ✗ Failed: {e}")
    continue  # Continue with other strategies
```

**Key Benefits:**
- **Easy Debugging**: Module prefixes instantly identify error sources
- **Robust Execution**: Individual strategy failures don't crash entire backtests  
- **Input Validation**: Comprehensive parameter checking prevents silent failures
- **User-Friendly**: Clear error messages guide users to fix configuration issues

## Available Components

### **Implemented Strategies**

| Strategy | Type | Description |
|----------|------|-------------|
| `MovingAverageStrategy` | Trend Following | Moving average crossover (SMA/EMA) with configurable periods |
| `RSIStrategy` | Mean Reversion | RSI-based overbought/oversold signals with custom thresholds |
| `BuyAndHoldStrategy` | Benchmark | Simple buy-and-hold for performance comparison |

### **Available Position Sizers**

| Position Sizer | Type | Description |
|----------------|------|-------------|
| `FixedPositionSizer` | Static | Fixed percentage of available capital per trade |
| `ATRPositionSizer` | Dynamic | Volatility-based sizing using Average True Range |

📖 **See [Strategy Documentation](docs/strategies.md) and [Position Sizer Documentation](docs/position_sizers.md) for detailed parameters, algorithms, and usage examples.**

## Future Plans

*[This section will be filled with upcoming features and improvements]*

## Performance Metrics

### **Return Metrics**
- **Total Return (%)**: Total percentage gain/loss over backtest period
- **CAGR (%)**: Compound Annual Growth Rate - annualized return
- **Final Capital**: Ending portfolio value

### **Risk Metrics** 
- **Maximum Drawdown (MDD)**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure (return/volatility)

### **Trading Metrics**
- **Total Trades**: Number of completed round-trip trades
- **Win Rate (%)**: Percentage of profitable trades
- **Profit Factor**: Ratio of total profits to total losses

## License

This project is licensed under the MIT License - see the LICENSE file for details.
