"""Interface definitions for cap table entities and calculators.

These interfaces define the contracts that all cap table components must follow,
enabling parallel development and ensuring compatibility between agents.
"""

from datetime import date
from typing import Any, Dict, List, Protocol


class IShareholderEntity(Protocol):
    """Interface for shareholder entities."""

    shareholder_type: str
    total_shares: int
    share_class: str

    def calculate_ownership_percentage(self, total_shares: int) -> float:
        """Calculate ownership percentage given total outstanding shares."""
        ...

    def get_voting_power(self, share_classes: Dict[str, Any]) -> float:
        """Calculate voting power based on share class voting rights."""
        ...

    def calculate_vested_shares(self, as_of_date: date) -> int:
        """Calculate number of vested shares as of given date."""
        ...

    def get_liquidation_proceeds(self, exit_value: float, waterfall: Dict[str, Any]) -> float:
        """Calculate liquidation proceeds for this shareholder."""
        ...


class IShareClassEntity(Protocol):
    """Interface for share class entities."""

    class_name: str
    shares_authorized: int
    shares_outstanding: int
    liquidation_preference: float
    participating: bool
    voting_rights_per_share: float

    def calculate_liquidation_proceeds(self, exit_value: float, shares_held: int) -> float:
        """Calculate liquidation proceeds for given number of shares."""
        ...

    def get_preference_coverage(self, company_value: float) -> float:
        """Calculate liquidation preference coverage ratio."""
        ...

    def calculate_conversion_value(self, common_price: float) -> float:
        """Calculate value if converted to common stock."""
        ...

    def get_voting_power_total(self) -> float:
        """Calculate total voting power of this share class."""
        ...


class IFundingRoundEntity(Protocol):
    """Interface for funding round entities."""

    round_type: str
    amount_raised: float
    pre_money_valuation: float
    post_money_valuation: float
    shares_issued: int
    price_per_share: float

    def calculate_dilution_impact(self, existing_cap_table: Dict[str, Any]) -> Dict[str, float]:
        """Calculate dilution impact on existing shareholders."""
        ...

    def get_new_ownership_structure(self, existing_shareholders: List[Any]) -> Dict[str, float]:
        """Calculate new ownership percentages after round."""
        ...

    def calculate_valuation_metrics(self) -> Dict[str, float]:
        """Calculate key valuation metrics for the round."""
        ...

    def validate_round_math(self) -> List[str]:
        """Validate mathematical consistency of round parameters."""
        ...


class ICapTableCalculator(Protocol):
    """Interface for cap table calculation engines."""

    def calculate_ownership_percentages(self, shareholders: List[IShareholderEntity],
                                      share_classes: List[IShareClassEntity]) -> Dict[str, float]:
        """Calculate current ownership percentages for all shareholders."""
        ...

    def calculate_voting_control(self, shareholders: List[IShareholderEntity],
                               share_classes: List[IShareClassEntity]) -> Dict[str, float]:
        """Calculate voting control percentages."""
        ...

    def calculate_dilution_scenario(self, current_cap_table: Dict[str, Any],
                                   new_round: IFundingRoundEntity) -> Dict[str, Any]:
        """Calculate dilution effects of a new funding round."""
        ...

    def calculate_liquidation_waterfall(self, cap_table: Dict[str, Any],
                                      exit_value: float) -> Dict[str, Any]:
        """Calculate liquidation preference waterfall distribution."""
        ...


class ICapTableValidator(Protocol):
    """Interface for cap table validation."""

    def validate_share_math(self, cap_table: Dict[str, Any]) -> List[str]:
        """Validate that share counts and percentages are consistent."""
        ...

    def validate_liquidation_preferences(self, share_classes: List[IShareClassEntity]) -> List[str]:
        """Validate liquidation preference structure."""
        ...

    def validate_voting_rights(self, shareholders: List[IShareholderEntity],
                             share_classes: List[IShareClassEntity]) -> List[str]:
        """Validate voting rights consistency."""
        ...

    def validate_funding_round(self, round_entity: IFundingRoundEntity) -> List[str]:
        """Validate funding round mathematical consistency."""
        ...


# Common data structures used across interfaces
class CapTableSummary:
    """Standard cap table summary structure."""

    def __init__(self):
        self.total_shares_outstanding: int = 0
        self.total_shares_authorized: int = 0
        self.ownership_by_shareholder: Dict[str, float] = {}
        self.ownership_by_class: Dict[str, float] = {}
        self.voting_control: Dict[str, float] = {}
        self.liquidation_preference_overhang: float = 0.0
        self.fully_diluted_shares: int = 0


class DilutionAnalysis:
    """Standard dilution analysis structure."""

    def __init__(self):
        self.pre_round_ownership: Dict[str, float] = {}
        self.post_round_ownership: Dict[str, float] = {}
        self.dilution_by_shareholder: Dict[str, float] = {}
        self.new_shares_issued: int = 0
        self.total_shares_post_round: int = 0


class LiquidationWaterfall:
    """Standard liquidation waterfall structure."""

    def __init__(self):
        self.exit_value: float = 0.0
        self.distributions: List[Dict[str, Any]] = []
        self.total_distributed: float = 0.0
        self.preference_coverage: Dict[str, float] = {}
        self.returns_by_shareholder: Dict[str, float] = {}
