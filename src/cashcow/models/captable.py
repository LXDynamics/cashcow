"""Cap table entity models for CashCow.

This module defines the core cap table entities: Shareholder, ShareClass, and FundingRound.
These entities implement the interfaces defined in captable_interfaces.py and provide
comprehensive cap table modeling capabilities.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import computed_field, field_validator, model_validator

from .base import BaseEntity


class ShareClass(BaseEntity):
    """Share class entity representing different types of equity."""

    type: str = "share_class"

    # Required fields
    class_name: str  # "Common", "Series A Preferred", etc.
    shares_authorized: int

    # Optional fields with defaults
    shares_outstanding: int = 0
    par_value: float = 0.001
    liquidation_preference: float = 1.0
    participating: bool = False
    voting_rights_per_share: float = 1.0
    dividend_rate: Optional[float] = None

    # Conversion and anti-dilution
    convertible_to: Optional[str] = None
    conversion_ratio: Optional[float] = None
    anti_dilution_provision: Optional[str] = None  # "weighted_average", "ratchet", "none"

    # Rights and restrictions
    redemption_rights: bool = False
    tag_along_rights: bool = False
    drag_along_rights: bool = False

    @field_validator('shares_authorized')
    @classmethod
    def validate_shares_authorized(cls, v: int) -> int:
        """Ensure shares authorized is positive."""
        if v <= 0:
            raise ValueError('shares_authorized must be positive')
        return v

    @field_validator('shares_outstanding')
    @classmethod
    def validate_shares_outstanding(cls, v: int) -> int:
        """Ensure shares outstanding is non-negative."""
        if v < 0:
            raise ValueError('shares_outstanding cannot be negative')
        return v

    @field_validator('liquidation_preference')
    @classmethod
    def validate_liquidation_preference(cls, v: float) -> float:
        """Ensure liquidation preference is reasonable."""
        if v < 0 or v > 10:
            raise ValueError('liquidation_preference must be between 0 and 10')
        return v

    @field_validator('voting_rights_per_share')
    @classmethod
    def validate_voting_rights(cls, v: float) -> float:
        """Ensure voting rights is reasonable."""
        if v < 0 or v > 100:
            raise ValueError('voting_rights_per_share must be between 0 and 100')
        return v

    @model_validator(mode='after')
    def validate_outstanding_vs_authorized(self):
        """Ensure outstanding shares don't exceed authorized."""
        if self.shares_outstanding > self.shares_authorized:
            raise ValueError('shares_outstanding cannot exceed shares_authorized')
        return self

    @computed_field
    @property
    def utilization_percentage(self) -> float:
        """Calculate percentage of authorized shares that are outstanding."""
        if self.shares_authorized == 0:
            return 0.0
        return (self.shares_outstanding / self.shares_authorized) * 100

    def calculate_liquidation_proceeds(self, exit_value: float, shares_held: int) -> float:
        """Calculate liquidation proceeds for given number of shares."""
        if shares_held <= 0 or self.shares_outstanding <= 0:
            return 0.0

        # Calculate share of liquidation preference
        preference_per_share = self.liquidation_preference * self.par_value
        total_preference = preference_per_share * shares_held

        if not self.participating:
            # Non-participating: get preference OR pro-rata share, whichever is higher
            pro_rata_share = (shares_held / self.shares_outstanding) * exit_value
            return max(total_preference, pro_rata_share)
        else:
            # Participating: get preference AND pro-rata share of remaining
            remaining_value = max(0, exit_value - (self.shares_outstanding * preference_per_share))
            pro_rata_remainder = (shares_held / self.shares_outstanding) * remaining_value
            return total_preference + pro_rata_remainder

    def get_preference_coverage(self, company_value: float) -> float:
        """Calculate liquidation preference coverage ratio."""
        if self.shares_outstanding == 0:
            return float('inf')

        total_preference = self.liquidation_preference * self.par_value * self.shares_outstanding
        if total_preference == 0:
            return float('inf')

        return company_value / total_preference

    def calculate_conversion_value(self, common_price: float) -> float:
        """Calculate value if converted to common stock."""
        if not self.convertible_to or not self.conversion_ratio:
            return 0.0

        return common_price * self.conversion_ratio

    def get_voting_power_total(self) -> float:
        """Calculate total voting power of this share class."""
        return self.shares_outstanding * self.voting_rights_per_share


class Shareholder(BaseEntity):
    """Individual shareholder entity with equity holdings."""

    type: str = "shareholder"

    # Required fields
    shareholder_type: str  # "founder", "employee", "investor", "advisor", "consultant"
    total_shares: int
    share_class: str = "common"

    # Optional shareholder details
    email: Optional[str] = None
    title: Optional[str] = None
    is_board_member: bool = False
    board_seats: int = 0

    # Acquisition details
    acquisition_date: Optional[date] = None
    acquisition_method: str = "grant"  # "grant", "purchase", "exercise", "conversion"
    purchase_price_per_share: Optional[float] = None

    # Vesting details
    vesting_schedule: Optional[Dict[str, Any]] = None
    cliff_months: int = 0
    vesting_months: int = 0
    vested_shares: Optional[int] = None

    # Rights and restrictions
    transfer_restrictions: bool = True
    tag_along_rights: bool = False
    drag_along_rights: bool = False
    anti_dilution_rights: bool = False

    @field_validator('shareholder_type')
    @classmethod
    def validate_shareholder_type(cls, v: str) -> str:
        """Ensure shareholder type is valid."""
        valid_types = ['founder', 'employee', 'investor', 'advisor', 'consultant', 'other']
        if v.lower() not in valid_types:
            raise ValueError(f'shareholder_type must be one of: {valid_types}')
        return v.lower()

    @field_validator('total_shares')
    @classmethod
    def validate_total_shares(cls, v: int) -> int:
        """Ensure total shares is positive."""
        if v <= 0:
            raise ValueError('total_shares must be positive')
        return v

    @field_validator('board_seats')
    @classmethod
    def validate_board_seats(cls, v: int) -> int:
        """Ensure board seats is non-negative."""
        if v < 0:
            raise ValueError('board_seats cannot be negative')
        return v

    @model_validator(mode='after')
    def validate_vesting_consistency(self):
        """Ensure vesting parameters are consistent."""
        if self.vested_shares is not None:
            if self.vested_shares > self.total_shares:
                raise ValueError('vested_shares cannot exceed total_shares')
            if self.vested_shares < 0:
                raise ValueError('vested_shares cannot be negative')
        return self

    def calculate_ownership_percentage(self, total_shares: int) -> float:
        """Calculate ownership percentage given total outstanding shares."""
        if total_shares <= 0:
            return 0.0
        return (self.total_shares / total_shares) * 100

    def get_voting_power(self, share_classes: Dict[str, Any]) -> float:
        """Calculate voting power based on share class voting rights."""
        share_class_data = share_classes.get(self.share_class, {})
        voting_rights_per_share = share_class_data.get('voting_rights_per_share', 1.0)
        return self.total_shares * voting_rights_per_share

    def calculate_vested_shares(self, as_of_date: date) -> int:
        """Calculate number of vested shares as of given date."""
        if self.vested_shares is not None:
            return self.vested_shares

        if not self.acquisition_date or not self.vesting_months:
            return self.total_shares

        # Calculate months since acquisition
        months_elapsed = (as_of_date.year - self.acquisition_date.year) * 12 + \
                        (as_of_date.month - self.acquisition_date.month)

        # Apply cliff
        if months_elapsed < self.cliff_months:
            return 0

        # Calculate vested percentage
        if months_elapsed >= self.vesting_months:
            return self.total_shares

        vested_percentage = months_elapsed / self.vesting_months
        return int(self.total_shares * vested_percentage)

    def get_liquidation_proceeds(self, exit_value: float, waterfall: Dict[str, Any]) -> float:
        """Calculate liquidation proceeds for this shareholder."""
        # This is a simplified calculation - full implementation would be in liquidation calculator
        share_class_data = waterfall.get('share_classes', {}).get(self.share_class, {})
        total_class_shares = share_class_data.get('total_shares', 1)
        class_proceeds = waterfall.get('proceeds_by_class', {}).get(self.share_class, 0.0)

        if total_class_shares == 0:
            return 0.0

        return (self.total_shares / total_class_shares) * class_proceeds

    @computed_field
    @property
    def is_founder(self) -> bool:
        """Check if this shareholder is a founder."""
        return self.shareholder_type == "founder"

    @computed_field
    @property
    def is_employee(self) -> bool:
        """Check if this shareholder is an employee."""
        return self.shareholder_type == "employee"

    @computed_field
    @property
    def is_investor(self) -> bool:
        """Check if this shareholder is an investor."""
        return self.shareholder_type == "investor"


class FundingRound(BaseEntity):
    """Funding round entity representing investment transactions."""

    type: str = "funding_round"

    # Required fields
    round_type: str  # "pre_seed", "seed", "series_a", "series_b", etc.
    amount_raised: float

    # Valuation fields (at least one required)
    pre_money_valuation: Optional[float] = None
    post_money_valuation: Optional[float] = None

    # Share details
    shares_issued: Optional[int] = None
    price_per_share: Optional[float] = None
    share_class: str = "preferred"

    # Round details
    lead_investor: Optional[str] = None
    investors: List[Dict[str, Any]] = []
    closing_date: Optional[date] = None

    # Terms
    liquidation_preference: float = 1.0
    participating: bool = False
    anti_dilution_provision: str = "weighted_average"
    board_seats_granted: int = 0

    # Option pool
    option_pool_increase: Optional[float] = None  # Percentage increase
    option_pool_pre_money: bool = True  # Whether option pool comes from pre-money

    @field_validator('round_type')
    @classmethod
    def validate_round_type(cls, v: str) -> str:
        """Ensure round type is valid."""
        valid_types = ['pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'series_d',
                      'bridge', 'convertible', 'other']
        if v.lower() not in valid_types:
            raise ValueError(f'round_type must be one of: {valid_types}')
        return v.lower()

    @field_validator('amount_raised')
    @classmethod
    def validate_amount_raised(cls, v: float) -> float:
        """Ensure amount raised is positive."""
        if v <= 0:
            raise ValueError('amount_raised must be positive')
        return v

    @field_validator('anti_dilution_provision')
    @classmethod
    def validate_anti_dilution(cls, v: str) -> str:
        """Ensure anti-dilution provision is valid."""
        valid_provisions = ['none', 'weighted_average', 'ratchet']
        if v.lower() not in valid_provisions:
            raise ValueError(f'anti_dilution_provision must be one of: {valid_provisions}')
        return v.lower()

    @model_validator(mode='after')
    def validate_valuation_consistency(self):
        """Ensure valuation fields are consistent."""
        if self.pre_money_valuation is None and self.post_money_valuation is None:
            raise ValueError('Either pre_money_valuation or post_money_valuation must be provided')

        if self.pre_money_valuation is not None and self.post_money_valuation is not None:
            expected_post_money = self.pre_money_valuation + self.amount_raised
            if abs(self.post_money_valuation - expected_post_money) > 0.01:
                raise ValueError('post_money_valuation must equal pre_money_valuation + amount_raised')

        if self.shares_issued is not None and self.price_per_share is not None:
            expected_amount = self.shares_issued * self.price_per_share
            if abs(expected_amount - self.amount_raised) > 0.01:
                raise ValueError('shares_issued * price_per_share must equal amount_raised')

        return self

    @computed_field
    @property
    def computed_pre_money_valuation(self) -> float:
        """Calculate pre-money valuation if not provided."""
        if self.pre_money_valuation is not None:
            return self.pre_money_valuation
        if self.post_money_valuation is not None:
            return self.post_money_valuation - self.amount_raised
        return 0.0

    @computed_field
    @property
    def computed_post_money_valuation(self) -> float:
        """Calculate post-money valuation if not provided."""
        if self.post_money_valuation is not None:
            return self.post_money_valuation
        if self.pre_money_valuation is not None:
            return self.pre_money_valuation + self.amount_raised
        return 0.0

    def calculate_dilution_impact(self, existing_cap_table: Dict[str, Any]) -> Dict[str, float]:
        """Calculate dilution impact on existing shareholders."""
        total_existing_shares = existing_cap_table.get('total_shares', 0)

        if total_existing_shares == 0:
            return {}

        # Calculate new shares issued
        if self.shares_issued:
            new_shares = self.shares_issued
        elif self.price_per_share and total_existing_shares > 0:
            # Calculate price per share based on pre-money valuation
            pre_money = self.computed_pre_money_valuation
            current_price_per_share = pre_money / total_existing_shares
            new_shares = int(self.amount_raised / current_price_per_share)
        else:
            return {}

        total_post_round_shares = total_existing_shares + new_shares

        # Calculate dilution for each shareholder
        dilution_impact = {}
        for shareholder_name, shares in existing_cap_table.get('shareholders', {}).items():
            pre_ownership = (shares / total_existing_shares) * 100
            post_ownership = (shares / total_post_round_shares) * 100
            dilution = pre_ownership - post_ownership
            dilution_impact[shareholder_name] = dilution

        return dilution_impact

    def get_new_ownership_structure(self, existing_shareholders: List[Any]) -> Dict[str, float]:
        """Calculate new ownership percentages after round."""
        # This would be implemented with full cap table context
        # For now, return placeholder
        return {}

    def calculate_valuation_metrics(self) -> Dict[str, float]:
        """Calculate key valuation metrics for the round."""
        return {
            'pre_money_valuation': self.computed_pre_money_valuation,
            'post_money_valuation': self.computed_post_money_valuation,
            'amount_raised': self.amount_raised,
            'price_per_share': self.price_per_share or 0.0,
            'shares_issued': self.shares_issued or 0,
            'liquidation_preference': self.liquidation_preference,
        }

    def validate_round_math(self) -> List[str]:
        """Validate mathematical consistency of round parameters."""
        errors = []

        # Check valuation consistency
        if self.pre_money_valuation and self.post_money_valuation:
            expected = self.pre_money_valuation + self.amount_raised
            if abs(self.post_money_valuation - expected) > 0.01:
                errors.append("Post-money valuation inconsistent with pre-money + amount raised")

        # Check share math
        if self.shares_issued and self.price_per_share:
            expected_amount = self.shares_issued * self.price_per_share
            if abs(expected_amount - self.amount_raised) > 0.01:
                errors.append("Shares issued * price per share doesn't equal amount raised")

        return errors


# Entity type mapping for cap table entities
CAPTABLE_ENTITY_TYPES = {
    'shareholder': Shareholder,
    'share_class': ShareClass,
    'funding_round': FundingRound,
}


def create_captable_entity(data: Dict[str, Any]) -> BaseEntity:
    """Create the appropriate cap table entity type from a dictionary."""
    entity_type = data.get('type', '').lower()

    if entity_type in CAPTABLE_ENTITY_TYPES:
        entity_class = CAPTABLE_ENTITY_TYPES[entity_type]
        return entity_class(**data)
    else:
        raise ValueError(f"Unknown cap table entity type: {entity_type}")
