class PositionManager:
    def __init__(self, max_positions=1, risk_per_trade=0.02):
        self.max_positions = max_positions
        self.risk_per_trade = risk_per_trade
        self.open_positions = {}

    def can_open_position(self, symbol):
        """Check if we can open a new position"""
        current_positions = len(self.open_positions)
        symbol_positions = symbol in self.open_positions

        return current_positions < self.max_positions and not symbol_positions

    def calculate_position_size(self, account_balance, entry_price, stop_loss):
        """Calculate position size based on risk management"""
        risk_amount = account_balance * self.risk_per_trade
        stop_loss_pips = abs(entry_price - stop_loss)

        if stop_loss_pips == 0:
            return 0

        position_size = risk_amount / stop_loss_pips
        return position_size