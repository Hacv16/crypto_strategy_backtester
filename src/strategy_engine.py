import pandas as pd
import numpy as np


MA_TYPES = {"SMA", "EMA"}  # Supported Moving Average types for strategy engine


class StrategyEngine:
    """
    Calculates various technical indicators and, based on the strategy,
    determines trade signals (hold, buy, sell), which are added to the
    dataframe.
    """

    def __init__(self,
                 strategy_type: str,
                 short_window: int = 50,
                 long_window: int = 200) -> None:

        self.strategy_type = strategy_type.upper()
        self.short_window = short_window
        self.long_window = long_window

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates technical indicators needed for signal generation
        based on the strategy type.

        :param df: DataFrame containing OHLCV data.
        :return: DataFrame with calculated indicators.
        """

        if df.empty or 'Close' not in df.columns:
            print("Strategy Engine Error: Missing data.")
            return pd.DataFrame()

        new_df = df.copy()

        try:
            if self.strategy_type == "HODL":
                return new_df  # No needed indicators for HODL strategy
            elif self.strategy_type in MA_TYPES:
                # Informative column names for easier debugging
                if self.strategy_type == "SMA":
                    new_df[f'{self.strategy_type}_{self.short_window}'] = df['Close'].rolling(
                        window=self.short_window).mean()
                    new_df[f'{self.strategy_type}_{self.long_window}'] = df['Close'].rolling(
                        window=self.long_window).mean()
                elif self.strategy_type == "EMA":
                    new_df[f'{self.strategy_type}_{self.short_window}'] = df['Close'].ewm(
                        span=self.short_window, adjust=False).mean()
                    new_df[f'{self.strategy_type}_{self.long_window}'] = df['Close'].ewm(
                        span=self.long_window, adjust=False).mean()
                else:
                    print(f"Strategy Engine Warning: Strategy '{self.strategy_type}' type not recognized.")
                    return new_df

                # Generic column names for easier signal generation
                new_df['Short_MA'] = new_df[f'{self.strategy_type}_{self.short_window}']
                new_df['Long_MA'] = new_df[f'{self.strategy_type}_{self.long_window}']
            else:
                print(f"Strategy Engine Warning: Strategy '{self.strategy_type}' is not recognized.")

        except Exception as e:
            print(f"Strategy Engine Error: Failed to calculate indicators for strategy '{self.strategy_type}': {e}")
            return new_df

        return new_df

    def _generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates trade signals based on the calculated indicators.

        :param df: DataFrame with calculated indicators.
        :return: DataFrame with trade signals.
        """

        if df.empty:
            print("Strategy Engine Error: Can't generate signals because dataframe is empty.")
            return pd.DataFrame()

        new_df = df.copy()

        # Create new columns to store signal type, signal strength and position type
        new_df["Signal"] = 0
        new_df["Signal_Strength"] = 0.0

        try:
            if self.strategy_type == "HODL":  # Ensure there are at least two days of data
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

            elif self.strategy_type in MA_TYPES:
                new_df['Trend'] = np.where(new_df['Short_MA'] > new_df['Long_MA'], 1, -1)
                new_df['Trend_Delta'] = new_df['Trend'].diff().fillna(0).astype(int)
                new_df['Signal'] = (new_df['Trend_Delta'] / 2).fillna(0)
                new_df['Signal_Strength'] = \
                    np.where(new_df['Signal'] != 0,
                             100 * abs((new_df['Short_MA'] - new_df['Long_MA'])/(new_df['Long_MA'])), 0.0)
                new_df.drop(columns=['Trend', 'Trend_Delta'], inplace=True)

            else:
                print(f"Strategy Engine Warning: Strategy '{self.strategy_type}' is not recognized.")

        except Exception as e:
            print(f"Strategy Engine Error: Failed to generate signals for strategy '{self.strategy_type}': {e}")

        return new_df

    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the strategy to the DataFrame.

        :param df: DataFrame containing OHLCV data.
        :return: DataFrame with calculated indicators (SMA/EMA if applicable)
                and trade signals (Signal and Signal_Strength)/positions.
        """

        if df.empty:
            raise ValueError("Strategy Engine Error: DataFrame is empty.")

        df_with_indicators = self._calculate_indicators(df)
        df_with_signals = self._generate_signals(df_with_indicators)

        return df_with_signals
