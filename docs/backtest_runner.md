# Backtest Runner Documentation

This document provides detailed information about this project's `BacktestRunner` class, which provides professional-grade backtesting with intraday risk management and comprehensive trade logging.

## Core Functionality

### **Realistic Trading Simulation**
- Order execution with transaction costs and slippage modeling
- Intraday stop-loss and take-profit using High/Low prices
- Proper position sizing and capital management
- Accurate profit/loss calculations with fee deduction

### **Advanced Risk Management**
- Strategy-level risk parameter overrides
- Stop-loss and take-profit execution priority
- Transaction fee modeling for realistic returns
- Comprehensive trade logging and audit trail

### **Professional Execution Engine**
- Event-driven backtesting architecture
- Proper handling of signals, entries, and exits
- Portfolio state management and validation
- Performance tracking throughout backtest period

## Configuration Parameters

### backtest_settings.json

The backtest runner is configured through the `backtest_settings.json` file:

```json
{
  "initial_capital": 10000.0,
  "transaction_fee_pct": 0.001,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.10
}
```

#### Parameter Details

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial_capital` | float | 10000.0 | Starting portfolio value in quote currency |
| `transaction_fee_pct` | float | 0.001 | Fee percentage per trade (0.1% = 0.001) |
| `stop_loss_pct` | float | 0.05 | Default stop-loss percentage (5% = 0.05) |
| `take_profit_pct` | float | 0.10 | Default take-profit percentage (10% = 0.10) |


### Strategy-Level Risk Overrides

Individual strategies can override default risk parameters in `strategies.json`:

```json
{
  "My_Strategy": {
    "name": "Custom Strategy",
    "type": "MovingAverageStrategy",
    "params": { "short_window": 12, "long_window": 26 },
    "position_sizer": {
      "type": "FixedPositionSizer",
      "params": { "fixed_size_pct": 100.0 }
    },
    "risk_overrides": {
      "stop_loss_pct": 0.03,
      "take_profit_pct": 0.15,
      "transaction_fee_pct": 0.002
    }
  }
}
```

#### Override Benefits
- **Strategy-Specific Risk**: Different strategies may require different risk levels
- **Custom Fee Structures**: Account for different exchange fees or VIP rates
- **A/B Testing**: Compare same strategy with different risk parameters
- **Optimization**: Fine-tune risk parameters per strategy type

## Risk Management System

### **RiskParameters Class**
```python
@dataclass
class RiskParameters:
    stop_loss_pct: float = 0.00      # Stop-loss percentage
    take_profit_pct: float = 0.00    # Take-profit percentage  
    transaction_fee_pct: float = 0.00 # Transaction fee percentage
```

### **Intraday Risk Execution**
The backtester uses daily High/Low prices for realistic risk management:

```python
def _check_risk_exits(self, daily_high: float, daily_low: float):
    # Check stop-loss first (risk priority)
    if daily_low <= stop_loss_price:
        return True, stop_loss_price, "Stop-loss triggered"
    
    # Check take-profit second  
    if daily_high >= take_profit_price:
        return True, take_profit_price, "Take-profit triggered"
```

This approach provides more realistic exit modeling than using only closing prices.

## Execution Flow

### 1. **Signal Processing**
- Read trading signals from strategy output
- Validate signal format and position sizes
- Handle signal conflicts and edge cases

### 2. **Risk Management**
- Check existing positions for stop-loss/take-profit triggers
- Execute risk-based exits before signal-based actions
- Apply transaction fees to all trades

### 3. **Position Management**
- Execute buy/sell orders based on signals
- Update portfolio state (cash, holdings, positions)
- Log detailed trade information for analysis

### 4. **Performance Tracking**
- Record daily portfolio values
- Track trade-level profits and losses
- Maintain audit trail of all transactions

## Trade Logging

Each completed trade generates a comprehensive log entry:

```python
{
    'entry_date': '2023-01-15',
    'exit_date': '2023-01-20', 
    'entry_price': 42000.0,
    'exit_price': 45000.0,
    'quantity': 0.238095,
    'cash_profit': 714.29,
    'exit_reason': 'Take-profit triggered',
    'stop_loss_used': 0.05,
    'take_profit_used': 0.10
}
```

### Trade Log Fields

| Field | Description |
|-------|-------------|
| `entry_date` | Position opening date |
| `exit_date` | Position closing date |
| `entry_price` | Entry price per unit |
| `exit_price` | Exit price per unit |
| `quantity` | Number of units traded |
| `cash_profit` | Net profit/loss after fees |
| `exit_reason` | Reason for position closure |
| `stop_loss_used` | Stop-loss percentage applied |
| `take_profit_used` | Take-profit percentage applied |

## Output Data

The `run()` method returns three components:

### 1. Equity Curve DataFrame
```python
equity_curve = pd.DataFrame({
    'date': timestamps,
    'total_capital': portfolio_values
}).set_index('date')
```

### 2. Trade Logs List
```python
trade_logs = [
    {'entry_date': ..., 'exit_price': ..., 'cash_profit': ...},
    # ... all completed trades
]
```

### 3. Risk Parameters Summary
```python
risk_params_info = {
    'stop_loss_pct': 0.05,
    'take_profit_pct': 0.10, 
    'transaction_fee_pct': 0.001
}
```

## Advanced Features

### **Portfolio State Management**
- Accurate tracking of cash and cryptocurrency holdings
- Proper handling of partial fills and position sizing
- Real-time portfolio value calculations

### **Transaction Cost Modeling**
- Realistic fee deduction on both entry and exit
- Support for maker/taker fee structures
- Custom fee schedules per strategy

### **Risk Priority System**
1. **Stop-Loss** (highest priority - risk management)
2. **Take-Profit** (secondary priority - profit taking)  
3. **Signal-Based Exits** (lowest priority - strategy logic)

### **Error Handling**
- Input validation for all parameters
- Portfolio state consistency checks
- Comprehensive error messages with module prefixes

