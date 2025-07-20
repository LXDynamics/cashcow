"""Revenue entity models for CashCow."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import field_validator

from .base import BaseEntity


class Grant(BaseEntity):
    """Grant funding entity with milestone tracking."""

    type: str = "grant"

    # Required fields
    amount: float

    # Grant details
    agency: Optional[str] = None
    program: Optional[str] = None
    grant_number: Optional[str] = None

    # Payment structure
    payment_schedule: Optional[List[Dict[str, Any]]] = None
    indirect_cost_rate: float = 0.0

    # Reporting and compliance
    reporting_requirements: Optional[str] = None
    reporting_frequency: Optional[str] = None

    # Performance metrics
    milestones: Optional[List[Dict[str, Any]]] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError('amount must be positive')
        return v

    @field_validator('indirect_cost_rate')
    @classmethod
    def validate_indirect_rate(cls, v: float) -> float:
        """Ensure indirect cost rate is reasonable."""
        if v < 0 or v > 1.0:
            raise ValueError('indirect_cost_rate must be between 0 and 1.0')
        return v

    def calculate_monthly_disbursement(self, as_of_date: date) -> float:
        """Calculate expected monthly disbursement."""
        if not self.is_active(as_of_date):
            return 0.0

        # If payment schedule exists, use it
        if self.payment_schedule:
            return self._calculate_scheduled_payment(as_of_date)

        # Otherwise, distribute evenly over grant period
        return self._calculate_even_disbursement(as_of_date)

    def _calculate_scheduled_payment(self, as_of_date: date) -> float:
        """Calculate payment based on schedule."""
        current_month = as_of_date.replace(day=1)
        monthly_payment = 0.0

        for payment in self.payment_schedule:
            if 'date' in payment and 'amount' in payment:
                payment_date = date.fromisoformat(payment['date']) if isinstance(payment['date'], str) else payment['date']
                payment_month = payment_date.replace(day=1)

                if payment_month == current_month:
                    monthly_payment += payment['amount']

        return monthly_payment

    def _calculate_even_disbursement(self, as_of_date: date) -> float:
        """Calculate even monthly disbursement."""
        if not self.end_date:
            # If no end date, assume 2-year grant
            grant_months = 24
        else:
            grant_months = (self.end_date.year - self.start_date.year) * 12 + \
                         (self.end_date.month - self.start_date.month)

        return self.amount / max(grant_months, 1)

    def get_milestone_status(self, as_of_date: date) -> Dict[str, Any]:
        """Get current milestone status."""
        if not self.milestones:
            return {}

        current_milestones = []
        upcoming_milestones = []
        completed_milestones = []

        for milestone in self.milestones:
            if 'date' in milestone:
                milestone_date = date.fromisoformat(milestone['date']) if isinstance(milestone['date'], str) else milestone['date']
                status = milestone.get('status', 'planned')

                if status == 'completed':
                    completed_milestones.append(milestone)
                elif milestone_date <= as_of_date:
                    current_milestones.append(milestone)
                else:
                    upcoming_milestones.append(milestone)

        return {
            'current': current_milestones,
            'upcoming': upcoming_milestones,
            'completed': completed_milestones,
        }


class Investment(BaseEntity):
    """Investment funding entity."""

    type: str = "investment"

    # Required fields
    amount: float

    # Investment details
    investor: Optional[str] = None
    round_name: Optional[str] = None
    round_type: Optional[str] = None  # seed, series_a, series_b, etc.

    # Valuation and terms
    pre_money_valuation: Optional[float] = None
    post_money_valuation: Optional[float] = None
    share_price: Optional[float] = None
    shares_issued: Optional[int] = None

    # Terms
    liquidation_preference: Optional[float] = None
    anti_dilution: Optional[str] = None
    board_seats: Optional[int] = None

    # Disbursement
    disbursement_schedule: Optional[List[Dict[str, Any]]] = None

    def calculate_monthly_disbursement(self, as_of_date: date) -> float:
        """Calculate monthly investment disbursement."""
        if not self.is_active(as_of_date):
            return 0.0

        # Use disbursement schedule if available
        if self.disbursement_schedule:
            return self._calculate_scheduled_disbursement(as_of_date)

        # Otherwise assume lump sum in first month
        return self._calculate_lump_sum(as_of_date)

    def _calculate_scheduled_disbursement(self, as_of_date: date) -> float:
        """Calculate scheduled disbursement."""
        current_month = as_of_date.replace(day=1)
        monthly_amount = 0.0

        for disbursement in self.disbursement_schedule:
            if 'date' in disbursement and 'amount' in disbursement:
                disbursement_date = date.fromisoformat(disbursement['date']) if isinstance(disbursement['date'], str) else disbursement['date']
                disbursement_month = disbursement_date.replace(day=1)

                if disbursement_month == current_month:
                    monthly_amount += disbursement['amount']

        return monthly_amount

    def _calculate_lump_sum(self, as_of_date: date) -> float:
        """Calculate lump sum disbursement in first month."""
        start_month = self.start_date.replace(day=1)
        current_month = as_of_date.replace(day=1)

        if start_month == current_month:
            return self.amount

        return 0.0


class Sale(BaseEntity):
    """Product sale entity."""

    type: str = "sale"

    # Required fields
    amount: float

    # Sale details
    customer: Optional[str] = None
    product: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None

    # Delivery and payment
    delivery_date: Optional[date] = None
    payment_terms: Optional[str] = None  # net_30, net_60, etc.

    # Sale structure
    payment_schedule: Optional[List[Dict[str, Any]]] = None

    def calculate_monthly_revenue(self, as_of_date: date) -> float:
        """Calculate monthly revenue from sale."""
        if not self.is_active(as_of_date):
            return 0.0

        # Use payment schedule if available
        if self.payment_schedule:
            return self._calculate_scheduled_revenue(as_of_date)

        # Otherwise use delivery date or start date
        return self._calculate_delivery_revenue(as_of_date)

    def _calculate_scheduled_revenue(self, as_of_date: date) -> float:
        """Calculate revenue based on payment schedule."""
        current_month = as_of_date.replace(day=1)
        monthly_revenue = 0.0

        for payment in self.payment_schedule:
            if 'date' in payment and 'amount' in payment:
                payment_date = date.fromisoformat(payment['date']) if isinstance(payment['date'], str) else payment['date']
                payment_month = payment_date.replace(day=1)

                if payment_month == current_month:
                    monthly_revenue += payment['amount']

        return monthly_revenue

    def _calculate_delivery_revenue(self, as_of_date: date) -> float:
        """Calculate revenue based on delivery date."""
        revenue_date = self.delivery_date or self.start_date
        revenue_month = revenue_date.replace(day=1)
        current_month = as_of_date.replace(day=1)

        if revenue_month == current_month:
            return self.amount

        return 0.0


class Service(BaseEntity):
    """Service contract entity."""

    type: str = "service"

    # Required fields
    monthly_amount: float

    # Service details
    customer: Optional[str] = None
    service_type: Optional[str] = None
    description: Optional[str] = None

    # Service structure
    hourly_rate: Optional[float] = None
    hours_per_month: Optional[float] = None

    # Contract terms
    minimum_commitment_months: Optional[int] = None
    auto_renewal: bool = False

    # Performance metrics
    sla_requirements: Optional[Dict[str, Any]] = None

    @field_validator('monthly_amount')
    @classmethod
    def validate_monthly_amount(cls, v: float) -> float:
        """Ensure monthly amount is positive."""
        if v <= 0:
            raise ValueError('monthly_amount must be positive')
        return v

    def calculate_monthly_revenue(self, as_of_date: date) -> float:
        """Calculate monthly service revenue."""
        if not self.is_active(as_of_date):
            return 0.0

        # Check if we're past minimum commitment
        if self.minimum_commitment_months:
            months_active = (as_of_date.year - self.start_date.year) * 12 + \
                          (as_of_date.month - self.start_date.month)

            if months_active >= self.minimum_commitment_months and self.end_date:
                # Check if contract has ended
                if as_of_date >= self.end_date:
                    return 0.0

        return self.monthly_amount

    def calculate_hourly_revenue(self, as_of_date: date, hours_worked: float) -> float:
        """Calculate revenue based on hours worked."""
        if not self.is_active(as_of_date) or not self.hourly_rate:
            return 0.0

        return self.hourly_rate * hours_worked

    def get_service_metrics(self, as_of_date: date) -> Dict[str, Any]:
        """Get service performance metrics."""
        months_active = (as_of_date.year - self.start_date.year) * 12 + \
                       (as_of_date.month - self.start_date.month) + 1

        total_revenue = self.monthly_amount * months_active

        return {
            'months_active': months_active,
            'total_revenue': total_revenue,
            'monthly_revenue': self.monthly_amount,
            'is_active': self.is_active(as_of_date),
            'customer': self.customer,
            'service_type': self.service_type,
        }
