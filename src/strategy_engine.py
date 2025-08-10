import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from .position_sizer import PositionSizer, FixedPositionSizer


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    Separates signal generation from position sizing for maximum flexibility.
    """

    def __init__(self, name: str, description: str, position_sizer: PositionSizer = None):
        self.name = name
        self.description = description
        self.position_sizer = position_sizer or FixedPositionSizer()
        self.parameters = {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates trading signals based on the strategy logic.
        This method should contain only the core strategy logic (signal generation).

        :param df: DataFrame containing historical OHLCV data
        :return: Series with signals (1 for buy, -1 for sell, 0 for hold)
        """
        pass

    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the complete strategy including signal generation and position sizing.

        :param df: DataFrame containing historical OHLCV data
        :return: DataFrame with 'Signal' and 'Position_Size' columns
        """
        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        # Generate trading signals (pure strategy logic)
        signals = self.generate_signals(df)

        # Calculate position sizes (risk management logic)
        position_sizes = self.position_sizer.calculate_position_size(df, signals)

        return pd.DataFrame({
            'Signal': signals,
            'Position_Size': position_sizes
        }, index=df.index)

    def get_parameters(self) -> dict:
        """
        Returns combined strategy and position sizing parameters for reporting.

        :return: Dictionary containing all strategy and position sizing parameters
        """
        params = self.parameters.copy()
        params['position_sizer_type'] = type(self.position_sizer).__name__
        return params


class MovingAverageStrategy(Strategy):
    """
    Moving Average crossover strategy - generates signals when short MA crosses above/below long MA.
    Supports both Simple Moving Average (SMA) and Exponential Moving Average (EMA).
    """

    # Supported moving average types
    SUPPORTED_MA_TYPES = {"SMA", "EMA"}

    def __init__(
            self,
            name: str,
            description: str,
            ma_type: str = "SMA",
            short_window: int = 12,
            long_window: int = 26,
            position_sizer: PositionSizer = None
    ):
        super().__init__(name, description, position_sizer)

        if ma_type.upper() not in self.SUPPORTED_MA_TYPES:
            raise ValueError(f"Strategy Engine Error: Unsupported ma_type '{ma_type}'. "
                             f"Supported types: {self.SUPPORTED_MA_TYPES}")

        if short_window >= long_window:
            raise ValueError("Strategy Engine Error: Short window must be smaller than long window.")

        self.ma_type = ma_type.upper()
        self.short_window = short_window
        self.long_window = long_window

        self.parameters = {
            "ma_type": self.ma_type,
            "short_window": short_window,
            "long_window": long_window,
        }

    def _calculate_moving_averages(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """
        Calculates the short and long moving averages based on the specified type.

        :param df: DataFrame containing OHLCV data
        :return: Tuple of (short_ma, long_ma) as pandas Series
        """
        if self.ma_type == "SMA":
            short_ma = df['Close'].rolling(window=self.short_window).mean()
            long_ma = df['Close'].rolling(window=self.long_window).mean()
        else:  # EMA
            short_ma = df['Close'].ewm(span=self.short_window, adjust=False).mean()
            long_ma = df['Close'].ewm(span=self.long_window, adjust=False).mean()

        return short_ma, long_ma

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on moving average crossover.
        Buy signal (1) when short MA crosses above long MA.
        Sell signal (-1) when short MA crosses below long MA.

        :param df: DataFrame containing OHLCV data
        :return: Series with crossover signals
        """
        if df.empty or 'Close' not in df.columns:
            raise ValueError("Strategy Engine Error: DataFrame must contain 'Close' column.")

        short_ma, long_ma = self._calculate_moving_averages(df)

        # Generate trend direction: 1 when short MA > long MA, -1 otherwise
        trend = np.where(short_ma > long_ma, 1, -1)

        # Detect trend changes to generate entry/exit signals
        trend_series = pd.Series(trend, index=df.index)
        trend_changes = trend_series.diff().fillna(0)

        # Convert trend changes to signals: +2 becomes +1 (buy), -2 becomes -1 (sell)
        signals = (trend_changes / 2).astype(int)

        return signals


class RSIStrategy(Strategy):
    """
    RSI Mean Reversion Strategy - buys when RSI is oversold, sells when overbought.
    Uses the Relative Strength Index to identify potential reversal points.
    """

    def __init__(
            self,
            name: str,
            description: str,
            rsi_period: int = 14,
            oversold_threshold: float = 30,
            overbought_threshold: float = 70,
            position_sizer: PositionSizer = None
    ):
        super().__init__(name, description, position_sizer)

        if rsi_period <= 0:
            raise ValueError("Strategy Engine Error: RSI period must be positive.")
        if not (0 < oversold_threshold < overbought_threshold < 100):
            raise ValueError("Strategy Engine Error: Invalid RSI thresholds. Must be 0 < oversold < overbought < 100.")

        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

        self.parameters = {
            "rsi_period": rsi_period,
            "oversold_threshold": oversold_threshold,
            "overbought_threshold": overbought_threshold,
        }

    def _calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculates the Relative Strength Index (RSI) indicator.
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss over the specified period.

        :param df: DataFrame containing OHLCV data
        :return: Series with RSI values
        """
        delta = df['Close'].diff()

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))

        # Calculate average gain and loss using Wilder's smoothing
        avg_gain = gain.ewm(alpha=1 / self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_period, adjust=False).mean()

        # Calculate RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals based on RSI levels.
        Buy signal when RSI drops below oversold threshold.
        Sell signal when RSI rises above overbought threshold.

        :param df: DataFrame containing OHLCV data
        :return: Series with RSI-based signals
        """
        if df.empty or 'Close' not in df.columns:
            raise ValueError("Strategy Engine Error: DataFrame must contain 'Close' column.")

        rsi = self._calculate_rsi(df)

        # Initialize signals series with zeros
        signals = pd.Series(0, index=df.index)

        # Generate signals based on RSI thresholds
        signals[rsi < self.oversold_threshold] = 1  # Buy when oversold
        signals[rsi > self.overbought_threshold] = -1  # Sell when overbought

        return signals


class BuyAndHoldStrategy(Strategy):
    """
    Buy and Hold Strategy - a benchmark strategy that buys on the first day
    and holds until the last day of the backtest period.
    FIXED: Now properly tracks the underlying asset price throughout the period.
    """

    def __init__(self, name: str, description: str, position_sizer: PositionSizer = None):
        super().__init__(name, description, position_sizer)

        # Buy and Hold strategy takes no parameters
        self.parameters = {}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates buy and hold signals: buy on first day, sell on last day.
        FIXED: Now explicitly sells on the last day to ensure proper closing.

        :param df: DataFrame containing OHLCV data
        :return: Series with buy and hold signals
        """
        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        if len(df) < 2:
            raise ValueError("Strategy Engine Error: At least two days are required for Buy and Hold strategy.")

        # Initialize all signals to zero
        signals = pd.Series(0, index=df.index)

        # Buy signal on first day
        signals.iloc[0] = 1

        # Sell signal on the last day
        signals.iloc[-1] = -1

        return signals