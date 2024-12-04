import asyncio
from typing import Dict


class PositionManager:
    def __init__(self, max_positions=1, risk_per_trade=0.02):
        self.max_positions = max_positions
        self.risk_per_trade = risk_per_trade
        self.open_positions: Dict[str, dict] = {}  # Track open positions by symbol

    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position"""
        current_positions = len(self.open_positions)
        symbol_positions = symbol in self.open_positions

        return current_positions < self.max_positions and not symbol_positions

    async def get_account_balance(self) -> float:
        """Fetch account balance asynchronously. In a real-world case, this would interact with an API or DB."""
        # Simulating an async call to an external service (e.g., fetching from an API)
        await asyncio.sleep(1)  # Simulating delay (replace with actual API call)
        account_balance = 10000.0  # Example balance, replace with actual retrieval logic
        return account_balance

    async def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management, using async fetching of balance if needed"""
        account_balance = await self.get_account_balance()  # Fetch account balance asynchronously
        risk_amount = account_balance * self.risk_per_trade
        stop_loss_pips = abs(entry_price - stop_loss)

        if stop_loss_pips == 0:
            return 0

        position_size = risk_amount / stop_loss_pips
        return position_size

    async def open_position(self, symbol: str, entry_price: float, stop_loss: float) -> dict:
        """Open a new position for the given symbol"""
        if not self.can_open_position(symbol):
            raise ValueError(f"Cannot open position for {symbol}, limit reached or already open")

        # Calculate position size asynchronously
        position_size = await self.calculate_position_size(symbol, entry_price, stop_loss)

        # Store the position data
        self.open_positions[symbol] = {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_size': position_size
        }

        return self.open_positions[symbol]

    async def close_position(self, symbol: str) -> dict:
        """Close a position for the given symbol"""
        if symbol not in self.open_positions:
            raise ValueError(f"No open position for {symbol}")

        closed_position = self.open_positions.pop(symbol)

        return closed_position

    def get_open_positions(self):
        """Return a snapshot of open positions"""
        return self.open_positions
