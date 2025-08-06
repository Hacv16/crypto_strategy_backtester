import pandas as pd


class BacktestRunner:
    """
    Simulates a trading strategy, including transaction costs, stop-loss,
    and take-profit mechanisms.
    """

    def __init__(
            self,
            df: pd.DataFrame,
            initial_balance: float = 10000.0,
            transaction_fee: float = 0.00,
            stop_loss_pct: float = 0.00,
            take_profit_pct: float = 0.00
    ) -> None:

        if df is None or df.empty:
            raise ValueError("Backtest Runner Error: DataFrame must not be empty.")

        if initial_balance <= 0:
            raise ValueError("Backtest Runner Error: Initial balance must be greater than zero.")

        self.df = df
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

        # Initialize backtest state variables
        self.cash = initial_balance
        self.crypto_holdings = 0.0
        self.in_position = False
        self.current_date = None

        self.entry_price = 0.0
        self.entry_date = None

        # Data to track performance
        self.history = []
        self.trade_logs = []

    def _get_total_capital(self, price) -> float:
        return price * self.crypto_holdings + self.cash

    def _update_capital_history(self, price: float) -> None:
        """ Updates the history of capital for the current date. """
        total_capital = self._get_total_capital(price)
        self.history.append({
            'date': self.current_date,
            'total_capital': total_capital
        })

    def _sell(self, price: float, reason: str) -> None:
        """ Executes a sell order and updates the state. """
        cash_return = self.crypto_holdings * price
        fee_amount = cash_return * self.transaction_fee

        current_trade = {
            'entry_date': self.entry_date,
            'exit_date': self.current_date,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.crypto_holdings,
            'cash_profit': cash_return - (self.entry_price * self.crypto_holdings) - fee_amount,
            'exit_reason': reason
        }

        self.cash += cash_return - fee_amount
        self.crypto_holdings = 0
        self.entry_price = 0.0
        self.entry_date = None
        self.in_position = False

        self.trade_logs.append(current_trade)

    def _buy(self, price: float, position_size: float) -> None:
        cash_investment = self.cash * (position_size / 100.0)
        fee_amount = cash_investment * self.transaction_fee
        amount_after_fee = cash_investment - fee_amount

        crypto_quantity = amount_after_fee / price

        self.cash -= cash_investment
        self.crypto_holdings += crypto_quantity
        self.entry_price = price
        self.entry_date = self.current_date
        self.in_position = True

    def run(self) -> tuple[pd.DataFrame, list]:
        """ Executes the backtest over the provided DataFrame. """

        for index, row in self.df.iterrows():
            self.current_date = index

            daily_high = row.get('High')
            daily_low = row.get('Low')

            closing_price = row.get('Close')

            current_signal = row.get('Signal')
            current_position_size = row.get('Position_Size')

            if self.in_position:
                if self.stop_loss_pct > 0:
                    stop_loss_price = self.entry_price * (1 - self.stop_loss_pct)
                    if daily_low <= stop_loss_price:
                        self._sell(stop_loss_price, reason="Stop-loss triggered")
                        self._update_capital_history(closing_price)
                        continue

                elif self.take_profit_pct > 0:
                    take_profit_price = self.entry_price * (1 + self.take_profit_pct)
                    if daily_high >= take_profit_price:
                        self._sell(take_profit_price, reason="Take-profit triggered")
                        self._update_capital_history(closing_price)
                        continue

                elif current_signal == -1:
                    self._sell(closing_price, reason="Signal trigger")

            elif not self.in_position and current_signal == 1:
                self._buy(closing_price, current_position_size)

            self._update_capital_history(closing_price)

        # Close any open position at the end of the backtest
        if self.in_position:
            last_price = self.df['Close'].iloc[-1]
            self._sell(last_price, reason="End of backtest")
            self.history[-1]['total_capital'] = self.cash

        history_df = pd.DataFrame(self.history)
        history_df.set_index('date', inplace=True)

        return history_df, self.trade_logs
