import ccxt
import datetime as dt
import os
import pandas as pd


class DataHandler:
    """
    Handles fetching loading and preprocessing of cryptocurrency data from a given
    cryptocurrency exchange (Binance by default) using CCXT.
    """

    def __init__(
            self,
            exchange_name: str = "binance",
            currency: str = "USDT",
            data_dir: str = "data/raw"
    ) -> None:
        if not isinstance(exchange_name, str) or not exchange_name:
            raise ValueError("Error: exchange_name must be a non-empty string")

        self.exchange_name = exchange_name
        self.currency = currency
        self.data_dir = data_dir

        self.exchange = None

        # Ensure the data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            exchange_config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            }
            self.exchange = exchange_class(exchange_config)

            # Test if exchange can load markets (requires internet)
            self.exchange.load_markets()

            print(f"DataHandler successfully initialized for exchange: {self.exchange.name}")
        except AttributeError:
            print(f"DataHandler Error: Exchange '{self.exchange_name}' not found in ccxt.")
        except Exception as e:
            print(f"DataHandler Error: Failed to initialize for CCXT exchange {self.exchange_name}: {e}")

    def _fetch_raw_historical_ohlcv_data(
            self,
            crypto_symbol: str,  # ex: 'BTC'
            timeframe: str = '1d',  # Daily
            since_days: int = 365 * 3  # Default to 3 years of data for example
    ) -> list[list[float]] | None:
        """
        Fetches historical OHLCV data from the exchange through CCXT.

        :param crypto_symbol: Cryptocurrency to be used for trading pair symbol (e.g., 'BTC/USDT').
        :param timeframe: Timeframe for the data (e.g., '1d', '1h').
        :param since_days: Number of days of historical data to fetch.
        :return: DataFrame containing OHLCV data.
        """

        if not self.exchange:
            raise ValueError("Exchange not initialized. Check for DataHandler errors.")

        all_data = []

        limit = 1000
        symbol = f"{crypto_symbol}/{self.currency}"
        since = self.exchange.parse8601(str(dt.datetime.now() - dt.timedelta(days=since_days)))

        while True:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)

                if not ohlcv:
                    break

                all_data.extend(ohlcv)
                since = ohlcv[-1][0] + 1  # Move to the next timestamp

                if len(ohlcv) < limit:
                    break  # Finished fetching data

            except ccxt.NetworkError as e:
                print(f"Network Error: Network error during fetch: {e}")
                break
            except ccxt.ExchangeError as e:
                print(
                    f"Exchange Error: Exchange error during fetch: {e} - Symbol '{symbol}'.")
                break
            except Exception as e:
                print(f"Unexpected Error: Unexpected error during fetch: {e}")
                break

        if not all_data:
            print(f"No data fetched for symbol {symbol} with timeframe {timeframe}.")
            return None

        return all_data

    def _process_raw_ohlcv_data(self, raw_data: list) -> pd.DataFrame:
        """
        Processes the raw OHLCV data into a DataFrame.

        :param raw_data: List of raw OHLCV data.
        :return: DataFrame containing processed OHLCV data.
        """

        if not raw_data:
            print("No raw data to process.")
            return pd.DataFrame()

        if not isinstance(raw_data, list) or not all(isinstance(item, list) and len(item) == 6 for item in raw_data):
            print("Invalid raw data format. Expected a list of lists with 6 elements each.")
            return pd.DataFrame()

        # Convert raw data to DataFrame
        df = pd.DataFrame(raw_data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])

        # Convert timestamp to datetime and set as index, remove 'timestamp' column
        df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('Date')
        df = df.drop(columns=['timestamp'])

        # Ensure the DataFrame has the correct columns and order
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.index.name = 'Date'
        df = df.sort_index()

        df.dropna(subset=['Close'], inplace=True)

        return df

    def _load_data_from_csv(self, file_path: str) -> pd.DataFrame:
        """
        Loads OHLCV data from a CSV file.

        :param file_path: Path to the CSV file.
        :return: DataFrame containing OHLCV data.
        """
        if not os.path.exists(file_path):  # Important check
            print(f"Error: CSV file not found at {file_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            print(f"Data loaded successfully from {file_path}")
            return df
        except Exception as e:
            print(f"Error: failed to load data from {file_path}: {e}")
            return pd.DataFrame()

    def load_or_fetch_and_process_data(
            self,
            crypto_symbol: str,
            timeframe: str = '1d',
            since_days: int = 365 * 3
    ) -> pd.DataFrame:
        """
        Loads data from file if available, otherwise fetches and processes it.

        :param crypto_symbol: Cryptocurrency to be used for trading pair symbol (e.g., 'BTC').
        :param timeframe: Timeframe for the data (e.g., '1d', '1h').
        :param since_days: Number of days of historical data to fetch.
        :return: DataFrame containing OHLCV data.
        """

        filename = f"{self.currency}_{crypto_symbol}_{timeframe}_{since_days}.csv"
        file_path = os.path.join(self.data_dir, filename)

        if os.path.exists(file_path):
            print(f"Found existing data. Loading from {file_path}")
            return self._load_data_from_csv(file_path)

        print("No existing data found. Fetching and processing new data.")

        raw_ohlcv = self._fetch_raw_historical_ohlcv_data(crypto_symbol, timeframe, since_days)
        df = self._process_raw_ohlcv_data(raw_ohlcv)

        if not df.empty:
            df.to_csv(file_path)
            print(f"Data fetched and saved to {file_path}")
            return df
        else:
            print(f"Error: Failed to fetch or process data.")

        return pd.DataFrame()
