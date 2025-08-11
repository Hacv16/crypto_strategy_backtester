# Data Handler Documentation

The `DataHandler` class manages cryptocurrency data acquisition, caching, and preprocessing. It provides intelligent data management with automatic caching and multi-exchange support through the CCXT library.

## Core Functionality

### **Multi-Exchange Support**
- Supports 100+ cryptocurrency exchanges via CCXT integration
- Configurable exchange selection (Binance by default)
- Automatic market loading and rate limiting

### **Intelligent Data Caching**
- Local CSV storage for improved performance
- Automatic data freshness validation
- Smart cache management prevents redundant API calls

### **Robust Data Pipeline**
- Comprehensive error handling with graceful degradation
- Data quality validation and preprocessing
- Automatic retry logic for network issues

## Configuration Parameters

### data_settings.json

The data handler is configured through the `data_settings.json` file:

```json
{
  "exchange_name": "binance",
  "currency": "USDT", 
  "crypto_symbol": "BTC",
  "timeframe": "1d",
  "since_days": 365,
  "data_dir": "data/raw"
}
```

#### Parameter Details

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange_name` | string | "binance" | CCXT exchange identifier (binance, coinbase, kraken, etc.) |
| `currency` | string | "USDT" | Quote currency for trading pairs |
| `crypto_symbol` | string | "BTC" | Base cryptocurrency symbol |
| `timeframe` | string | "1d" | Data timeframe (1d, 4h, 1h, etc.) |
| `since_days` | integer | 365 | Number of historical days to fetch |
| `data_dir` | string | "data/raw" | Directory for local data storage |


#### Popular Exchanges
- `binance` - Binance (default)
- `coinbase` - Coinbase Pro
- `kraken` - Kraken
- `bitfinex` - Bitfinex
- `huobi` - Huobi Global

## Data Pipeline Process

### 1. Cache Check
```python
# Check if local data exists and is sufficient
if os.path.exists(file_path):
    df = self._load_data_from_csv(file_path)
    if data_is_sufficient:
        return df  # Use cached data
```

### 2. Data Fetching
```python
# Fetch from exchange with rate limiting
while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
    # Handle pagination and rate limits
```

### 3. Data Processing
```python
# Convert to DataFrame with proper indexing
df = pd.DataFrame(data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('Date', inplace=True)
```

## Output Format

The DataHandler returns a standardized pandas DataFrame with:

| Column | Type | Description |
|--------|------|-------------|
| `Date` | DatetimeIndex | Trading date (index) |
| `Open` | float | Opening price |
| `High` | float | Highest price |
| `Low` | float | Lowest price |
| `Close` | float | Closing price |
| `Volume` | float | Trading volume |

## Error Handling

### Network Errors
- Automatic retry logic for temporary network issues
- Graceful degradation on persistent connection problems
- Rate limiting compliance to prevent API throttling

### Data Validation
- Empty dataset detection and error reporting
- Invalid data format validation

### Exchange Errors
- Invalid exchange name detection
- Market loading error handling
- Symbol availability validation

## Usage Examples

### Basic Usage
```python
from src.data_handler import DataHandler

# Initialize with default settings
data_handler = DataHandler()

# Load BTC/USDT daily data
df = data_handler.load_or_fetch_and_process_data(
    crypto_symbol="BTC",
    timeframe="1d", 
    since_days=365
)
```

### Custom Exchange
```python
# Use Coinbase instead of Binance
data_handler = DataHandler(
    exchange_name="coinbase",
    currency="USD"
)

# Fetch ETH data
df = data_handler.load_or_fetch_and_process_data("ETH")
```

### High-Frequency Data
```python
# Fetch hourly data for short-term strategies
df = data_handler.load_or_fetch_and_process_data(
    crypto_symbol="BTC",
    timeframe="1h",
    since_days=30
)
```
