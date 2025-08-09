import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class PositionSizer(ABC):
    """
    Abstract base class for position sizing strategies.
    A PositionSizer is responsible for determining how much capital will be used (in percentage) on each trade.
    """

    @abstractmethod
    def calculate_position_size(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        Calculate position sizes based on the given signals and market data.

        :param df: DataFrame containing historical OHLCV data
        :param signals: Series with trading signals (1 for buy, -1 for sell, 0 for hold)
        :return: Series with position sizes as percentage of available capital (0-100%)
        """
        pass


class FixedPositionSizer(PositionSizer):
    """
    Fixed position sizing strategy that uses a fixed percentage of capital for each trade.
    """

    def __init__(self, fixed_size_pct: float = 100.0):
        if not (0 < fixed_size_pct <= 100):
            raise ValueError("Position Sizer Error: Fixed position size percentage must be between 0 and 100.")

        self.fixed_size_pct = fixed_size_pct

    def calculate_position_size(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        Returns fixed position sizes for all non-zero signals.

        :param df: DataFrame containing historical OHLCV data (not used)
        :param signals: Series with trading signals (1 for buy, -1 for sell, 0 for hold)
        :return: Series with fixed position sizes
        """
        return pd.Series(
            np.where(signals != 0, self.fixed_size_pct, 0.0),
            index=signals.index
        )


class ATRPositionSizer(PositionSizer):
    """
    ATR-based volatility position sizing - adjusts position size inversely to market volatility.
    Higher volatility = smaller positions to maintain consistent risk exposure.
    """

    def __init__(self, atr_period: int = 14, risk_factor: float = 0.02, max_position_size: float = 100.0):
        if atr_period <= 0:
            raise ValueError("Position Sizer Error: ATR period must be a positive integer.")
        if not (0 < risk_factor <= 1):
            raise ValueError("Position Sizer Error: Risk factor must be between 0 and 1.")
        if not (0 < max_position_size <= 100):
            raise ValueError("Position Sizer Error: Max position size percentage must be between 0 and 100.")

        self.atr_period = atr_period
        self.risk_factor = risk_factor
        self.max_position_size = max_position_size

    def calculate_position_size(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        Calculate position sizes based on Average True Range (ATR).
        Position size = (risk_factor * 100) / (ATR / Close_Price)

        :param df: DataFrame containing OHLCV data
        :param signals: Trading signals
        :return: Series with volatility-adjusted position sizes
        """
        # Calculate True Range components
        high_low = df['High'] - df['Low']
        high_prev_close = abs(df['High'] - df['Close'].shift(1))
        low_prev_close = abs(df['Low'] - df['Close'].shift(1))

        # True Range is the maximum of the three components
        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)

        # Calculate ATR using exponential moving average (Wilder's smoothing)
        atr = tr.ewm(alpha=1 / self.atr_period, adjust=False).mean()

        # Position size inversely proportional to volatility (higher ATR (more volatile ==> smaller position size)
        position_size = (self.risk_factor * 100) / (atr / df['Close'])
        position_size = position_size.clip(upper=self.max_position_size)

        return pd.Series(
            np.where(signals != 0, position_size, 0.0),
            index=signals.index
        )
