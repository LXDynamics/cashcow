"""Interface definitions for cap table components."""

from .captable_interfaces import (
    ICapTableCalculator,
    ICapTableValidator,
    IFundingRoundEntity,
    IShareClassEntity,
    IShareholderEntity,
)

__all__ = [
    'IShareholderEntity',
    'IShareClassEntity',
    'IFundingRoundEntity',
    'ICapTableCalculator',
    'ICapTableValidator',
]
