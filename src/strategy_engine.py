import pandas as pd
import numpy as np

from abc import ABC, abstractmethod


class Strategy(ABC):
    """Abstract base class for all trading strategies"""

    def __init__(
            self,
            name: str,
            description: str
    ) -> None:

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

    def __init__(
            self,
            ma_type: str,
            short_window: int,
            long_window: int,
            variable_sizing: bool = False,
            fixed_position_size: float = 100.0,
            atr_period: int = 14,
            risk_factor: float = 0.02
    ) -> None:

        if ma_type.upper() not in self.SUPPORTED_MA_TYPES:
            raise ValueError(
                f"Strategy Engine Error: Unsupported ma_type '{ma_type}'. "
            )

        name = f"{ma_type.upper()} Crossover ({short_window}/{long_window})"
        description = f"Generates signals based on crossovers of {short_window}-day and {long_window}-day {ma_type}s."

        super().__init__(name, description)

        self.ma_type = ma_type.upper()
        self.short_window = short_window
        self.long_window = long_window
        self.variable_sizing = variable_sizing

        self.parameters = {
            "ma_type": ma_type.upper(),
            "short_window": short_window,
            "long_window": long_window,
            "variable_sizing": variable_sizing
        }

        if self.variable_sizing:
            self.parameters['atr_period'] = atr_period
            self.parameters['risk_factor'] = risk_factor
        else:
            self.parameters["fixed_position_size"] = fixed_position_size

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates the moving averages and adds them to the DataFrame."""

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
            print(f"Strategy Engine Error: Strategy '{self.ma_type}' type not recognized.")
            return new_df

        # Generic column names for easier signal generation
        new_df['Short_MA'] = new_df[f'{self.ma_type}_{self.short_window}']
        new_df['Long_MA'] = new_df[f'{self.ma_type}_{self.long_window}']

        return new_df

    def _generate_position_sizes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generates position sizes based on the strategy's variable sizing."""
        if df.empty or 'Signal' not in df.columns or 'Short_MA' not in df.columns or 'Long_MA' not in df.columns:
            print("Strategy Engine Error: Missing data.")
            return pd.DataFrame()

        new_df = df.copy()

        if self.variable_sizing:
            high_low = new_df['High'] - new_df['Low']
            high_prev_close = abs(new_df['High'] - new_df['Close'].shift(1))
            low_prev_close = abs(new_df['Low'] - new_df['Close'].shift(1))
            tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
            atr = tr.ewm(span=self.parameters['atr_period'], adjust=False).mean()

            # Calculate position size inversely to volatility
            position_size = (self.parameters['risk_factor'] * 100) / (atr / new_df['Close'])
            position_size.clip(upper=100.0, inplace=True)  # Cap at 100%

            new_df['Position_Size'] = np.where(new_df['Signal'] != 0, position_size, 0.0)
        else:
            new_df['Position_Size'] = np.where(
                new_df['Signal'] != 0, self.parameters['fixed_position_size'], 0.0
            )

        return new_df

    def _generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Generates trading signals based on the moving averages."""
        if df.empty or 'Short_MA' not in df.columns or 'Long_MA' not in df.columns:
            print("Strategy Engine Error: Missing data.")
            return pd.DataFrame()

        new_df = df.copy()

        # Create new columns to store additional information
        new_df['Trend'] = np.where(new_df['Short_MA'] > new_df['Long_MA'], 1, -1)
        new_df['Trend_Delta'] = new_df['Trend'].diff().fillna(0).astype(int)
        new_df['Signal'] = (new_df['Trend_Delta'] / 2).fillna(0)
        new_df.drop(columns=['Trend', 'Trend_Delta'], inplace=True)

        return new_df

    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        df_with_indicators = self._calculate_indicators(df)
        df_with_signals = self._generate_signals(df_with_indicators)
        final_df = self._generate_position_sizes(df_with_signals)

        return final_df[['Signal', 'Position_Size']]


class BuyAndHoldStrategy(Strategy):
    def __init__(self):
        name = "Buy and Hold (HODL)"
        description = "Buys on the first day and sells on the last"
        super().__init__(name, description)

    def _generate_signals_and_position_sizes(self, df: pd.DataFrame) -> pd.DataFrame:
        """        Generates buy and sell signals for a Buy and Hold strategy."""
        if df.empty:
            print("Strategy Engine Error: Missing data.")
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
        new_df.loc[first_day, 'Position_Size'] = 100.0

        # Signal to sell on the very last available day
        last_day = new_df.index[-1]
        new_df.loc[last_day, 'Signal'] = -1
        new_df.loc[last_day, 'Position_Size'] = 100.0

        return new_df

    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        final_df = self._generate_signals_and_position_sizes(df)
        return final_df[['Signal', 'Position_Size']]
