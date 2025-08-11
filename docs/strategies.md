# Strategy Documentation

This document provides detailed information about all implemented trading strategies in the Crypto Strategy Backtester.

## Base Strategy Class

All strategies inherit from the abstract `Strategy` class, which provides the common interface and functionality:

```python
from abc import ABC, abstractmethod
from .position_sizer import PositionSizer

class Strategy(ABC):
    def __init__(self, name: str, description: str, position_sizer: PositionSizer = None)
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on strategy logic"""
        pass
    
    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply complete strategy including signal generation and position sizing"""
        pass
```

## Implemented Strategies

### 1. MovingAverageStrategy

**Description:** Classic trend-following strategy based on moving average crossovers. Generates buy signals when a shorter-period moving average crosses above a longer-period moving average, and sell signals on the reverse crossover.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ma_type` | str | "SMA" | Moving average type: "SMA" (Simple) or "EMA" (Exponential) |
| `short_window` | int | 12 | Period for the fast moving average |
| `long_window` | int | 26 | Period for the slow moving average |

#### Signal Logic

- **Buy Signal (1)**: When short MA crosses above long MA (bullish crossover)
- **Sell Signal (-1)**: When short MA crosses below long MA (bearish crossover)
- **Hold Signal (0)**: No crossover occurred

#### Algorithm Details

1. Calculate short and long moving averages based on `ma_type`
2. Determine trend direction: 1 when short MA > long MA, -1 otherwise
3. Detect trend changes using `diff()` to identify crossovers
4. Convert trend changes to trading signals

#### Configuration Example

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

#### Validation Rules

- `ma_type` must be either "SMA" or "EMA"
- `short_window` must be smaller than `long_window`
- Both window parameters must be positive integers

---

### 2. RSIStrategy

**Description:** Mean reversion strategy using the Relative Strength Index (RSI) to identify overbought and oversold market conditions. Buys when RSI indicates oversold conditions and sells when overbought.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rsi_period` | int | 14 | Period for RSI calculation |
| `oversold_threshold` | float | 30 | RSI level below which to generate buy signals |
| `overbought_threshold` | float | 70 | RSI level above which to generate sell signals |

#### Signal Logic

- **Buy Signal (1)**: When RSI falls below `oversold_threshold`
- **Sell Signal (-1)**: When RSI rises above `overbought_threshold`
- **Hold Signal (0)**: RSI is between thresholds

#### Algorithm Details

1. Calculate price changes using `Close.diff()`
2. Separate gains and losses from price changes
3. Calculate average gains and losses using Wilder's smoothing (EWM)
4. Compute RSI: `100 - (100 / (1 + RS))` where `RS = Average Gain / Average Loss`
5. Generate signals based on RSI thresholds

#### RSI Calculation Formula

```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss
```

Where averages are calculated using Wilder's exponential smoothing method.

#### Configuration Example

```json
{
  "RSI_Strategy": {
    "name": "RSI Mean Reversion",
    "type": "RSIStrategy", 
    "params": {
      "rsi_period": 14,
      "oversold_threshold": 30,
      "overbought_threshold": 70
    },
    "position_sizer": {
      "type": "ATRPositionSizer",
      "params": {
        "atr_period": 14,
        "risk_factor": 0.02,
        "max_position_size": 100.0
      }
    }
  }
}
```

#### Validation Rules

- `rsi_period` must be a positive integer
- `0 < oversold_threshold < overbought_threshold < 100`

---

### 3. BuyAndHoldStrategy

**Description:** Benchmark strategy that simulates buying an asset at the beginning of the backtest period and holding it until the end. Used as a baseline for comparing active trading strategies.

#### Parameters

This strategy takes no configuration parameters.

#### Signal Logic

- **Buy Signal (1)**: First day of the backtest period
- **Sell Signal (-1)**: Last day of the backtest period
- **Hold Signal (0)**: All days in between

#### Algorithm Details

1. Initialize all signals to zero
2. Set buy signal on the first trading day
3. Set sell signal on the last trading day
4. Ensures proper position closing for accurate performance calculation

#### Configuration Example

```json
{
  "Buy_And_Hold": {
    "name": "Buy and Hold Benchmark",
    "type": "BuyAndHoldStrategy",
    "params": {},
    "position_sizer": {
      "type": "FixedPositionSizer", 
      "params": {"fixed_size_pct": 100.0}
    }
  }
}
```

#### Validation Rules

- Requires at least 2 days of data to function properly
- No parameter validation needed (no configurable parameters)

---

## Strategy Performance Characteristics

### MovingAverageStrategy
- **Best Markets**: Trending markets with clear directional moves
- **Strengths**: Simple, robust, captures major trends
- **Weaknesses**: Prone to whipsaws in sideways markets, lagging signals
- **Typical Use**: Trend following, long-term position strategies

### RSIStrategy  
- **Best Markets**: Range-bound, volatile markets
- **Strengths**: Good for capturing reversals, works in consolidating markets
- **Weaknesses**: Can struggle in strong trending markets, multiple false signals
- **Typical Use**: Mean reversion, contrarian strategies

### BuyAndHoldStrategy
- **Best Markets**: Long-term bull markets
- **Strengths**: No transaction costs from frequent trading, captures full market moves
- **Weaknesses**: No downside protection, full exposure to market volatility
- **Typical Use**: Benchmark comparison, passive investment simulation

## Creating Custom Strategies

To implement a custom strategy:

1. **Inherit from Strategy base class:**
```python
class MyCustomStrategy(Strategy):
    def __init__(self, name: str, description: str, custom_param: int = 10, position_sizer: PositionSizer = None):
        super().__init__(name, description, position_sizer)
        self.custom_param = custom_param
        self.parameters = {"custom_param": custom_param}
```

2. **Implement the generate_signals method:**
```python
def generate_signals(self, df: pd.DataFrame) -> pd.Series:
    # Your signal generation logic here
    signals = pd.Series(0, index=df.index)
    
    # Example: Buy when price is above custom threshold
    signals[df['Close'] > df['Close'].rolling(self.custom_param).mean()] = 1
    signals[df['Close'] < df['Close'].rolling(self.custom_param).mean()] = -1
    
    return signals
```

3. **Add validation in __init__ if needed:**
```python
if custom_param <= 0:
    raise ValueError("Strategy Engine Error: custom_param must be positive")
```

4. **Register in configuration:**
```json
{
  "type": "MyCustomStrategy",
  "params": {"custom_param": 15}
}
```

The framework will automatically discover and instantiate your custom strategy through the factory pattern.