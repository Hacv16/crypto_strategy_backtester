import pandas as pd
import numpy as np

from abc import ABC, abstractmethod


class Strategy(ABC):
    """Abstract base class for all trading strategies"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.parameters = {}

    @abstractmethod
    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the strategy to the DataFrame and returns the DataFrame
        with the Trade signals and their strength.
        """
        pass


class MovingAverageStrategy(Strategy):
    # Stores the possible types of Moving Averages
    SUPPORTED_MA_TYPES = {"SMA", "EMA"}

    def __init__(self, ma_type, short_window, long_window):
        if ma_type.upper() not in self.SUPPORTED_MA_TYPES:
            raise ValueError(
                f"Unsupported ma_type '{ma_type}'. "
            )

        name = f"{ma_type.upper()} Crossover ({short_window}/{long_window})"
        description = f"Generates signals based on crossovers of {short_window}-day and {long_window}-day {ma_type}s."

        super().__init__(name, description)

        self.ma_type = ma_type.upper()
        self.short_window = short_window
        self.long_window = long_window

        self.parameters = {
            "ma_type": ma_type.upper(),
            "short_window": short_window,
            "long_window": long_window,
        }

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or 'Close' not in df.columns:
            print("Strategy Engine Error: Missing data.")
            return df

        new_df = df.copy()

        if self.ma_type == "SMA":
            new_df[f'{self.ma_type}_{self.short_window}'] = df['Close'].rolling(
                window=self.short_window).mean()
            new_df[f'{self.ma_type}_{self.long_window}'] = df['Close'].rolling(
                window=self.long_window).mean()
        elif self.ma_type == "EMA":
            new_df[f'{self.ma_type}_{self.short_window}'] = df['Close'].ewm(
                span=self.short_window, adjust=False).mean()
            new_df[f'{self.ma_type}_{self.long_window}'] = df['Close'].ewm(
                span=self.long_window, adjust=False).mean()
        else:
            print(f"Strategy Engine Warning: Strategy '{self.ma_type}' type not recognized.")
            return new_df

        # Generic column names for easier signal generation
        new_df['Short_MA'] = new_df[f'{self.ma_type}_{self.short_window}']
        new_df['Long_MA'] = new_df[f'{self.ma_type}_{self.long_window}']

        return new_df

    def _generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            print("Strategy Engine Error: Can't generate signals because dataframe is empty.")
            return pd.DataFrame()

        new_df = df.copy()

        # Create new columns to store additional information
        new_df['Trend'] = np.where(new_df['Short_MA'] > new_df['Long_MA'], 1, -1)
        new_df['Trend_Delta'] = new_df['Trend'].diff().fillna(0).astype(int)
        new_df['Signal'] = (new_df['Trend_Delta'] / 2).fillna(0)
        new_df['Signal_Strength'] = \
            np.where(new_df['Signal'] != 0,
                     100 * abs((new_df['Short_MA'] - new_df['Long_MA']) / (new_df['Long_MA'])), 0.0)
        new_df.drop(columns=['Trend', 'Trend_Delta'], inplace=True)

        return new_df

    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        df_with_indicators = self._calculate_indicators(df)
        df_with_signals = self._generate_signals(df_with_indicators)

        return df_with_signals


class BuyAndHoldStrategy(Strategy):
    def __init__(self):
        name = "Buy and Hold (HODL)"
        description = "Buys on the first day and sells on the last"
        super().__init__(name, description)

    def _generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            print("Strategy Engine Error: Can't generate signals because dataframe is empty.")
            return pd.DataFrame()

        new_df = df.copy()
        new_df["Signal"] = 0
        new_df["Signal_Strength"] = 0.0

        if len(new_df) < 2:
            print("Strategy Engine Warning: Not enough data for HODL strategy. At least two days are required.")
            return new_df

        # Buy on the first day
        first_day = new_df.index[0]
        new_df.loc[first_day, 'Signal'] = 1
        new_df.loc[first_day, 'Signal_Strength'] = 100.0

        # Signal to sell on the very last available day
        last_day = new_df.index[-1]
        new_df.loc[last_day, 'Signal'] = -1
        new_df.loc[last_day, 'Signal_Strength'] = 100.0

        return new_df

    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        df_with_signals = self._generate_signals(df)
        return df_with_signals
