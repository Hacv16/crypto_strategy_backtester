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
            raise ValueError("Data Handler Error: exchange_name must be a non-empty string")

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
            self.exchange.load_markets()

        except AttributeError:
            raise ValueError(f"Data Handler Error: Exchange '{self.exchange_name}' not found in ccxt.")
        except Exception as e:
            raise RuntimeError(f"Data Handler Error: Unexpected error occurred during DataHandler initialization: {e}")

    def _fetch_raw_historical_ohlcv_data(
            self,
            crypto_symbol: str,
            timeframe: str,
            since_days: int
    ) -> list[list[float]]:
        """
        Fetches historical OHLCV data from the exchange through CCXT.

        :param crypto_symbol: Cryptocurrency to be used for trading pair symbol (e.g., 'BTC').
        :param timeframe: Timeframe for the data (e.g., '1d' for daily data).
        :param since_days: Number of days of historical data to fetch.
        :return: A list of lists containing raw OHLCV data, or raises an error.
        """

        if not self.exchange:
            raise ValueError("Data Handler Error: Exchange not initialized.")

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
                since = ohlcv[-1][0] + 1

                # Finished fetching data
                if len(ohlcv) < limit:
                    break

            except ccxt.NetworkError as e:
                print(f"Data Handler Error: Network error during fetch: {e}")
                break
            except ccxt.ExchangeError as e:
                print(
                    f"Data Handler Error: Exchange error during fetch: {e} - Symbol '{symbol}'.")
                break
            except Exception as e:
                print(f"Data Handler Error: Unexpected error during fetch: {e}")
                break

        if not all_data:
            raise IOError(f"Data Handler Error Failed to fetch any data for symbol {symbol}.")

        return all_data

    def _process_raw_ohlcv_data(self, raw_data: list) -> pd.DataFrame:
        """
        Processes the raw OHLCV data into a DataFrame.

        :param raw_data: List of raw OHLCV data.
        :return: DataFrame containing processed OHLCV data, or raises an error.
        """

        if not raw_data:
            raise ValueError("Data Handler Error: No raw data was provided to process.")

        if not isinstance(raw_data, list) or not all(isinstance(item, list) and len(item) == 6 for item in raw_data):
            raise ValueError("Data Handler Error: Invalid raw data format.")

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
        :return: DataFrame containing OHLCV data or raises an error.
        """
        try:
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            return df
        except FileNotFoundError:
            raise IOError(f"Data Handler Error: CSV file not found at {file_path}")
        except Exception as e:
            raise IOError(f"Data Handler Error: Failed to parse data from {file_path}: {e}")

    def load_or_fetch_and_process_data(
            self,
            crypto_symbol: str,
            timeframe: str = '1d',
            since_days: int = 365 * 3
    ) -> pd.DataFrame:
        """
        Loads data from a local file if available and sufficient. Otherwise,
        fetches new data from the exchange, saves it, and returns it.

        :param crypto_symbol: Cryptocurrency to be used for trading pair symbol (e.g., 'BTC').
        :param timeframe: Timeframe for the data (e.g., '1d' for daily data).
        :param since_days: Number of days of historical data to fetch.
        :return: A DataFrame containing the OHLCV data
        """

        # Use a canonical filename independent of the date range
        symbol_pair = f"{crypto_symbol}-{self.currency}"
        filename = f"{symbol_pair.replace('/', '')}_{timeframe}.csv"
        file_path = os.path.join(self.data_dir, filename)

        try:
            # Check if a local file already exists
            if os.path.exists(file_path):
                df = self._load_data_from_csv(file_path)

                # Check if the existing data is sufficient for the request
                required_start_date = pd.to_datetime(dt.datetime.now() - dt.timedelta(days=since_days))

                if not df.empty and df.index[0] <= required_start_date:
                    return df

            raw_data = self._fetch_raw_historical_ohlcv_data(crypto_symbol, timeframe, since_days)
            df = self._process_raw_ohlcv_data(raw_data)

            # Save the new, complete data, overwriting the old file if it existed
            if not df.empty:
                df.to_csv(file_path)

            return df

        except (ValueError, IOError, ConnectionError) as e:
            print(f"DataHandler Error for {crypto_symbol}: {e}")
            return pd.DataFrame()
