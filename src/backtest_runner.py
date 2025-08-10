import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskParameters:
    """
    Container for risk management parameters.
    Centralizes all risk-related settings for easy management and validation.
    """
    stop_loss_pct: float = 0.00
    take_profit_pct: float = 0.00
    transaction_fee_pct: float = 0.00

    def __post_init__(self):
        """Validate risk parameters after initialization."""
        if self.stop_loss_pct < 0 or self.stop_loss_pct > 1:
            raise ValueError("Backtest Runner Error: Stop loss must be between 0 and 1")
        if self.take_profit_pct < 0:
            raise ValueError("Backtest Runner Error: Take profit cannot be negative")
        if self.transaction_fee_pct < 0:
            raise ValueError("Backtest Runner Error: Transaction fee cannot be negative")


class BacktestRunner:
    """
    Simulates a trading strategy with realistic execution, including transaction costs,
    stop-loss, and take-profit mechanisms. Supports strategy-level risk parameter overrides.
    """

    def __init__(
            self,
            df: pd.DataFrame,
            initial_capital: float = 10000.0,
            default_risk_params: RiskParameters = None,
            strategy_risk_overrides: Optional[dict] = None
    ):

        if df is None or df.empty:
            raise ValueError("Backtest Runner Error: DataFrame must not be empty.")

        if initial_capital <= 0:
            raise ValueError("Backtest Runner Error: Initial capital must be greater than zero.")

        self.df = df
        self.initial_capital = initial_capital

        # Set up risk parameters with potential strategy overrides
        self.default_risk_params = default_risk_params or RiskParameters()
        self.active_risk_params = self._apply_risk_overrides(strategy_risk_overrides)

        # Initialize backtest state variables
        self._initialize_state()

    def _apply_risk_overrides(self, overrides: Optional[dict]) -> RiskParameters:
        """
        Apply strategy-specific risk parameter overrides to default settings.

        :param overrides: Dictionary containing risk parameter overrides
        :return: RiskParameters object with applied overrides
        """
        if not overrides:
            return self.default_risk_params

        # Start with default parameter values
        params_dict = {
            'stop_loss_pct': self.default_risk_params.stop_loss_pct,
            'take_profit_pct': self.default_risk_params.take_profit_pct,
            'transaction_fee_pct': self.default_risk_params.transaction_fee_pct,
        }

        # Apply overrides
        for key, value in overrides.items():
            if key in params_dict:
                params_dict[key] = value
            else:
                raise ValueError(f"Backtest Runner Error: Unknown risk parameter: '{key}'")

        return RiskParameters(**params_dict)

    def _initialize_state(self) -> None:
        """Initialize all backtest state variables."""
        self.cash = self.initial_capital
        self.crypto_holdings = 0.0
        self.in_position = False
        self.current_date = None
        self.entry_price = 0.0
        self.entry_date = None

        # Data tracking for performance analysis
        self.history = []
        self.trade_logs = []

    def _get_total_capital(self, price: float) -> float:
        """
        Calculate total portfolio value at current prices.

        :param price: Current cryptocurrency price
        :return: Total portfolio value (cash + crypto holdings value)
        """
        return price * self.crypto_holdings + self.cash

    def _update_capital_history(self, price: float) -> None:
        """
        Update the history of portfolio values for the current date.

        :param price: The current price of the cryptocurrency
        """
        total_capital = self._get_total_capital(price)
        self.history.append({
            'date': self.current_date,
            'total_capital': total_capital
        })

    def _sell(self, price: float, reason: str) -> None:
        """
        Execute a sell order, update portfolio state, and log the trade.

        :param price: The price at which the cryptocurrency is sold
        :param reason: The reason for the sell action (e.g., stop-loss, take-profit, signal)
        """
        # Calculate cash return from selling crypto holdings
        cash_return = self.crypto_holdings * price
        fee_amount = cash_return * self.active_risk_params.transaction_fee_pct

        # Log detailed trade information
        current_trade = {
            'entry_date': self.entry_date,
            'exit_date': self.current_date,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.crypto_holdings,
            'cash_profit': cash_return - (self.entry_price * self.crypto_holdings) - fee_amount,
            'exit_reason': reason,
            'stop_loss_used': self.active_risk_params.stop_loss_pct,
            'take_profit_used': self.active_risk_params.take_profit_pct
        }

        # Update portfolio state
        self.cash += cash_return - fee_amount
        self.crypto_holdings = 0
        self.entry_price = 0.0
        self.entry_date = None
        self.in_position = False

        self.trade_logs.append(current_trade)

    def _buy(self, price: float, position_size: float) -> None:
        """
        Execute a buy order and update portfolio state.

        :param price: The price at which the cryptocurrency is bought
        :param position_size: Position size as a percentage of available cash
        """
        # Calculate investment amount and fees
        cash_investment = self.cash * (position_size / 100.0)
        fee_amount = cash_investment * self.active_risk_params.transaction_fee_pct
        amount_after_fee = cash_investment - fee_amount

        # Calculate crypto quantity purchased
        crypto_quantity = amount_after_fee / price

        # Update portfolio state
        self.cash -= cash_investment
        self.crypto_holdings += crypto_quantity
        self.entry_price = price
        self.entry_date = self.current_date
        self.in_position = True

    def _check_risk_exits(self, daily_high: float, daily_low: float) -> tuple[bool, float, str]:
        """
        Check for stop-loss and take-profit exits based on intraday price action.

        :param daily_high: Highest price during the current day
        :param daily_low: Lowest price during the current day
        :return: Tuple of (should_exit, exit_price, exit_reason)
        """
        # Check stop-loss first (risk management priority)
        if self.active_risk_params.stop_loss_pct > 0:
            stop_loss_price = self.entry_price * (1 - self.active_risk_params.stop_loss_pct)
            if daily_low <= stop_loss_price:
                return True, stop_loss_price, "Stop-loss triggered"

        # Check take-profit second
        if self.active_risk_params.take_profit_pct > 0:
            take_profit_price = self.entry_price * (1 + self.active_risk_params.take_profit_pct)
            if daily_high >= take_profit_price:
                return True, take_profit_price, "Take-profit triggered"

        return False, 0.0, ""

    def run(self) -> tuple[pd.DataFrame, list, dict]:
        """
        Execute the backtest over the provided DataFrame and return comprehensive results.

        :return: Tuple containing (equity_curve_df, trade_logs_list, risk_params_used_dict)
        """
        for index, row in self.df.iterrows():
            self.current_date = index

            # Extract price and signal data
            daily_high = row.get('High')
            daily_low = row.get('Low')
            closing_price = row.get('Close')
            current_signal = row.get('Signal')
            current_position_size = row.get('Position_Size')

            # Handle existing position management
            if self.in_position:
                # Check for risk-based exits first (stop-loss, take-profit)
                should_exit, exit_price, exit_reason = self._check_risk_exits(daily_high, daily_low)

                if should_exit:
                    self._sell(exit_price, exit_reason)
                    self._update_capital_history(closing_price)
                    continue

                # Check for signal-based exit if no risk exit occurred
                if current_signal == -1:
                    self._sell(closing_price, "Signal triggered")
                    self._update_capital_history(closing_price)
                    continue

            # Handle new position entry
            elif not self.in_position and current_signal == 1:
                self._buy(closing_price, current_position_size)

            # Update portfolio value history
            self._update_capital_history(closing_price)

        # Finalize the backtest by closing any open positions
        if self.in_position:
            last_price = self.df['Close'].iloc[-1]
            self._sell(last_price, "End of backtest")

            # FIXED: Update the final history entry with correct total capital calculation
            # Remove the last entry and add a corrected one
            if self.history:
                self.history[-1]['total_capital'] = self._get_total_capital(last_price)

        # Prepare results for return
        history_df = pd.DataFrame(self.history)
        history_df.set_index('date', inplace=True)

        # Create summary of risk parameters used
        risk_params_info = {
            'stop_loss_pct': self.active_risk_params.stop_loss_pct,
            'take_profit_pct': self.active_risk_params.take_profit_pct,
            'transaction_fee_pct': self.active_risk_params.transaction_fee_pct,
        }

        return history_df, self.trade_logs, risk_params_info
