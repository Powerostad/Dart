from enum import Enum, auto
from typing import List, Optional
from django.utils import timezone
from django.db import models

from utils.algorithms.base import SignalType


class SignalStatus(Enum):
    PENDING = auto()
    ACTIVE = auto()
    TRIGGERED = auto()
    EXPIRED = auto()
    INVALIDATED = auto()


class Signal(models.Model):
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10)
    signal_type = models.CharField(max_length=10, choices=[(tag.value, tag.name) for tag in SignalType])
    confidence = models.FloatField()
    algorithms_triggered = models.JSONField(null=True)
    entry_price = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    status = models.CharField(
        max_length=20,
        choices=[(tag.name, tag.name) for tag in SignalStatus],
        default=SignalStatus.PENDING.name
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True)
    risk_reward_ratio = models.FloatField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'status']),
            models.Index(fields=['generated_at', 'valid_until'])
        ]
        ordering = ('-generated_at',)

    @classmethod
    def create_signal(
            cls,
            symbol: str,
            timeframe: str,
            signal_type: SignalType,
            confidence: float,
            algorithms: List[str],
            current_price: float,
            risk_percentage: float = 1.0
    ) -> 'ExtendedSignal':
        """
        Factory method to create a comprehensive trading signal

        :param symbol: Trading symbol
        :param timeframe: Signal timeframe
        :param signal_type: Buy or Sell direction
        :param confidence: Signal confidence level
        :param algorithms: Algorithms that triggered the signal
        :param current_price: Current market price
        :param risk_percentage: Maximum risk percentage of account
        :return: Created signal object
        """
        # Determine entry, take profit, and stop loss
        if signal_type == SignalType.BUY:
            entry_price = current_price
            stop_loss = cls._calculate_stop_loss(
                entry_price,
                signal_type,
                risk_percentage
            )
            take_profit = cls._calculate_take_profit(
                entry_price,
                stop_loss,
                signal_type
            )
        elif signal_type == SignalType.SELL:
            entry_price = current_price
            stop_loss = cls._calculate_stop_loss(
                entry_price,
                signal_type,
                risk_percentage
            )
            take_profit = cls._calculate_take_profit(
                entry_price,
                stop_loss,
                signal_type
            )
        else:
            entry_price, stop_loss, take_profit = None, None, None

        # Determine signal validity based on timeframe
        valid_duration = cls._get_validity_duration(timeframe)

        return cls.objects.create(
            symbol=symbol,
            timeframe=timeframe,
            signal_type=signal_type.value,
            confidence=confidence,
            algorithms_triggered=algorithms,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status=SignalStatus.PENDING.name,
            valid_until=timezone.now() + valid_duration,
            risk_reward_ratio=cls._calculate_risk_reward_ratio(
                entry_price, take_profit, stop_loss
            ) if signal_type != SignalType.NEUTRAL else None,
        )
    @staticmethod
    def _calculate_stop_loss(
            entry_price: float,
            signal_type: SignalType,
            risk_percentage: float,
            base_atr: float = 0.01
    ) -> Optional[float]:
        """
        Calculate stop loss based on signal type and risk percentage

        :param entry_price: Current market price
        :param signal_type: Buy or Sell direction
        :param risk_percentage: Maximum risk percentage
        :param base_atr: Base ATR multiplier for stop loss calculation
        :return: Calculated stop loss price
        """
        atr_adjustment = base_atr * risk_percentage

        if signal_type == SignalType.BUY:
            return entry_price * (1 - atr_adjustment)
        elif signal_type == SignalType.SELL:
            return entry_price * (1 + atr_adjustment)
        else:
            return None

    @staticmethod
    def _calculate_take_profit(
            entry_price: float,
            stop_loss: float,
            signal_type: SignalType,
            risk_reward_ratio: float = 2.0
    ) -> Optional[float]:
        """
        Calculate take profit based on stop loss and risk-reward ratio

        :param entry_price: Current market price
        :param stop_loss: Calculated stop loss
        :param signal_type: Buy or Sell direction
        :param risk_reward_ratio: Desired risk-reward ratio
        :return: Calculated take profit price
        """
        price_difference = abs(entry_price - stop_loss)

        if signal_type == SignalType.BUY:
            return entry_price + (price_difference * risk_reward_ratio)
        elif signal_type == SignalType.SELL:
            return entry_price - (price_difference * risk_reward_ratio)
        return None

    @staticmethod
    def _calculate_risk_reward_ratio(
            entry_price: float,
            take_profit: float,
            stop_loss: float
    ) -> float:
        """
        Calculate risk-reward ratio

        :param entry_price: Signal entry price
        :param take_profit: Take profit price
        :param stop_loss: Stop loss price
        :return: Risk-reward ratio
        """
        potential_profit = abs(take_profit - entry_price)
        potential_loss = abs(stop_loss - entry_price)

        return potential_profit / potential_loss if potential_loss > 0 else 0

    @staticmethod
    def _get_validity_duration(timeframe: str) -> timezone.timedelta:
        """
        Determine signal validity duration based on timeframe

        :param timeframe: Signal timeframe
        :return: Timedelta representing signal validity
        """
        timeframe_mapping = {
            '1m': timezone.timedelta(minutes=5),
            '5m': timezone.timedelta(minutes=15),
            '15m': timezone.timedelta(minutes=30),
            '30m': timezone.timedelta(hours=1),
            '1h': timezone.timedelta(hours=2),
            "4h": timezone.timedelta(hours=8),
            'daily': timezone.timedelta(days=1)
        }

        return timeframe_mapping.get(timeframe, timezone.timedelta(hours=1))

    def update_signal_status(self, current_price: float) -> None:
        """
        Update signal status based on current market conditions

        :param current_price: Current market price
        """
        # Check if signal is expired
        if timezone.now() > self.valid_until:
            self.status = SignalStatus.EXPIRED.name
            self.save()
            return

        # Check if signal has been triggered
        if self.signal_type == SignalType.BUY.value:
            if current_price >= self.take_profit:
                self.status = SignalStatus.TRIGGERED.name
            elif current_price <= self.stop_loss:
                self.status = SignalStatus.INVALIDATED.name
        elif self.signal_type == SignalType.SELL.value:
            if current_price <= self.take_profit:
                self.status = SignalStatus.TRIGGERED.name
            elif current_price >= self.stop_loss:
                self.status = SignalStatus.INVALIDATED.name

        self.save()
    @classmethod
    def cleanup_expired_signals(cls):
        """
        Cleanup method to remove or update expired signals
        """
        expired_signals = cls.objects.filter(
            valid_until__lt=timezone.now(),
            status__in=[
                SignalStatus.PENDING.name,
                SignalStatus.ACTIVE.name
            ]
        )
        expired_signals.update(status=SignalStatus.EXPIRED.name)