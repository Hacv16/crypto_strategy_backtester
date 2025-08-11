# Position Sizer Documentation

This document provides detailed information about all implemented position sizing algorithms in the Crypto Strategy Backtester.

## Base PositionSizer Class

All position sizers inherit from the abstract `PositionSizer` class:

```python
from abc import ABC, abstractmethod
import pandas as pd

class PositionSizer(ABC):
    @abstractmethod
    def calculate_position_size(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        Calculate position sizes based on signals and market data.
        
        Returns: Series with position sizes as percentage of available capital (0-100%)
        """
        pass
```

## Position Sizing Concepts

Position sizing determines how much capital to allocate to each trade. It's a critical component of risk management that affects both returns and risk exposure.

### Key Principles
- **Risk Management**: Larger positions in lower-risk scenarios, smaller in higher-risk
- **Capital Preservation**: Avoid risking too much capital on any single trade
- **Volatility Adjustment**: Account for market volatility when sizing positions
- **Consistency**: Maintain consistent risk exposure across different market conditions

## Implemented Position Sizers

### 1. FixedPositionSizer

**Description:** The simplest position sizing method that uses a fixed percentage of available capital for every trade. Provides consistent exposure regardless of market conditions.

#### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `fixed_size_pct` | float | 100.0 | 0-100 | Fixed percentage of available capital to use per trade |

#### Algorithm

For every non-zero signal:
```
Position Size = fixed_size_pct (if signal ≠ 0)
Position Size = 0 (if signal = 0)
```

#### Use Cases
- **Conservative Trading**: Use 25-50% for partial position sizing
- **Aggressive Trading**: Use 100% for full capital deployment  
- **Testing**: Consistent sizing for fair strategy comparisons
- **Simple Strategies**: When market volatility isn't a primary concern

#### Configuration Example

```json
{
  "position_sizer": {
    "type": "FixedPositionSizer",
    "params": {
      "fixed_size_pct": 75.0
    }
  }
}
```

#### Validation Rules
- `0 < fixed_size_pct ≤ 100`

---

### 2. ATRPositionSizer

**Description:** Dynamic position sizing based on Average True Range (ATR), which measures market volatility. Automatically reduces position size during high volatility periods and increases it during low volatility, maintaining consistent risk exposure.

#### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `atr_period` | int | 14 | > 0 | Period for ATR calculation |
| `risk_factor` | float | 0.02 | 0-1 | Risk factor controlling overall position sizing |
| `max_position_size` | float | 100.0 | 0-100 | Maximum position size cap (%) |

#### Algorithm

1. **Calculate True Range (TR):**
   ```python
   high_low = High - Low
   high_prev_close = abs(High - Close[t-1])
   low_prev_close = abs(Low - Close[t-1])
   TR = max(high_low, high_prev_close, low_prev_close)
   ```

2. **Calculate ATR using Wilder's Smoothing:**
   ```python
   ATR = EWM(TR, alpha=1/atr_period)
   ```

3. **Calculate Position Size:**
   ```python
   Position Size = (risk_factor × 100) / (ATR / Close)
   Position Size = min(Position Size, max_position_size)
   ```

#### Mathematical Formula

```
Position Size = min(
    (Risk Factor × 100) / (ATR / Current Price),
    Max Position Size
)
```

#### Volatility Relationship
- **High Volatility (High ATR)** → **Smaller Position Size**
- **Low Volatility (Low ATR)** → **Larger Position Size**

This inverse relationship maintains consistent dollar risk across varying market conditions.

#### Use Cases
- **Volatile Markets**: Automatically adjusts for changing volatility
- **Risk Management**: Maintains consistent risk exposure
- **Professional Trading**: Industry-standard volatility-based sizing
- **Multi-Asset**: Works across different assets with varying volatility profiles

#### Configuration Example

```json
{
  "position_sizer": {
    "type": "ATRPositionSizer", 
    "params": {
      "atr_period": 14,
      "risk_factor": 0.02,
      "max_position_size": 100.0
    }
  }
}
```

#### Parameter Guidelines

**ATR Period:**
- **Shorter (7-10)**: More responsive to recent volatility changes
- **Standard (14-21)**: Balanced approach, widely used in industry
- **Longer (30+)**: Smoother, less sensitive to short-term volatility spikes

**Risk Factor:**
- **Conservative (0.01-0.015)**: Lower risk, smaller positions
- **Moderate (0.02-0.03)**: Balanced risk/return profile
- **Aggressive (0.04+)**: Higher risk, larger positions

**Max Position Size:**
- **Conservative (50-75%)**: Limits maximum exposure
- **Standard (100%)**: Allows full capital deployment
- **Custom**: Based on specific risk tolerance

#### Validation Rules
- `atr_period` must be a positive integer
- `0 < risk_factor ≤ 1`
- `0 < max_position_size ≤ 100`

---

## Position Sizing Comparison

### Performance Characteristics

| Aspect | FixedPositionSizer | ATRPositionSizer |
|--------|-------------------|------------------|
| **Complexity** | Simple | Moderate |
| **Volatility Adaptation** | None | Automatic |
| **Risk Management** | Basic | Advanced |
| **Computation Cost** | Minimal | Low |
| **Parameter Tuning** | Single parameter | Multiple parameters |
| **Market Suitability** | All markets | Volatile markets |

### When to Use Each

**FixedPositionSizer:**
- Testing new strategies (eliminates position sizing variables)
- Conservative approaches with manual risk control
- Simple strategies where volatility isn't a major factor
- When you want consistent percentage exposure

**ATRPositionSizer:**
- Professional trading systems
- Volatile cryptocurrency markets
- When risk management is a priority
- Multi-timeframe or multi-asset strategies
- When you want consistent dollar risk exposure

## Creating Custom Position Sizers

To implement a custom position sizer:

1. **Inherit from PositionSizer base class:**
```python
class MyCustomSizer(PositionSizer):
    def __init__(self, custom_param: float = 1.0):
        if custom_param <= 0:
            raise ValueError("Position Sizer Error: custom_param must be positive")
        self.custom_param = custom_param
```

2. **Implement calculate_position_size method:**
```python
def calculate_position_size(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
    # Your position sizing logic here
    position_sizes = pd.Series(0.0, index=signals.index)
    
    # Example: Size based on volume
    for i in range(len(df)):
        if signals.iloc[i] != 0:
            volume_factor = df['Volume'].iloc[i] / df['Volume'].mean()
            position_sizes.iloc[i] = min(self.custom_param * volume_factor, 100.0)
    
    return position_sizes
```

3. **Register in configuration:**
```json
{
  "position_sizer": {
    "type": "MyCustomSizer",
    "params": {"custom_param": 50.0}
  }
}
```

Position sizing significantly affects:
- **Total Returns**: Larger sizes increase both gains and losses
- **Volatility**: Dynamic sizing can reduce portfolio volatility
- **Maximum Drawdown**: Proper sizing limits worst-case losses  
- **Sharpe Ratio**: Risk-adjusted returns often improve with dynamic sizing
- **Consistency**: Reduces performance dependence on market conditions