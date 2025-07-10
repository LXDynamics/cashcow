"""Expense entity models for CashCow."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import field_validator

from .base import BaseEntity


class Facility(BaseEntity):
    """Facility expense entity with comprehensive cost tracking."""
    
    type: str = "facility"
    
    # Required fields
    monthly_cost: float
    
    # Facility details
    location: Optional[str] = None
    size_sqft: Optional[int] = None
    facility_type: Optional[str] = None  # office, lab, manufacturing, warehouse
    
    # Lease terms
    lease_start_date: Optional[date] = None
    lease_end_date: Optional[date] = None
    lease_monthly_base: Optional[float] = None
    
    # Utilities and services
    utilities_monthly: Optional[float] = None
    internet_monthly: Optional[float] = None
    security_monthly: Optional[float] = None
    cleaning_monthly: Optional[float] = None
    
    # Insurance and taxes
    insurance_annual: Optional[float] = None
    property_tax_annual: Optional[float] = None
    
    # Maintenance and repairs
    maintenance_monthly: Optional[float] = None
    maintenance_quarterly: Optional[float] = None
    maintenance_annual: Optional[float] = None
    
    # Certifications and permits
    certifications: Optional[List[Dict[str, Any]]] = None
    
    @field_validator('monthly_cost')
    @classmethod
    def validate_monthly_cost(cls, v: float) -> float:
        """Ensure monthly cost is positive."""
        if v <= 0:
            raise ValueError('monthly_cost must be positive')
        return v
    
    def calculate_monthly_cost(self, as_of_date: date) -> float:
        """Calculate total monthly facility cost."""
        if not self.is_active(as_of_date):
            return 0.0
        
        total_cost = self.monthly_cost
        
        # Add utilities
        if self.utilities_monthly:
            total_cost += self.utilities_monthly
        
        # Add other monthly costs
        monthly_costs = [
            self.internet_monthly,
            self.security_monthly,
            self.cleaning_monthly,
            self.maintenance_monthly,
        ]
        
        for cost in monthly_costs:
            if cost:
                total_cost += cost
        
        # Add monthly portion of annual costs
        annual_costs = [
            self.insurance_annual,
            self.property_tax_annual,
            self.maintenance_annual,
        ]
        
        for cost in annual_costs:
            if cost:
                total_cost += cost / 12
        
        # Add quarterly maintenance
        if self.maintenance_quarterly:
            total_cost += self.maintenance_quarterly / 3
        
        return total_cost
    
    def get_certification_costs(self, as_of_date: date) -> float:
        """Calculate certification and permit costs for the month."""
        if not self.is_active(as_of_date) or not self.certifications:
            return 0.0
        
        monthly_cert_cost = 0.0
        current_month = as_of_date.replace(day=1)
        
        for cert in self.certifications:
            if 'renewal_date' in cert and 'cost' in cert:
                renewal_date = date.fromisoformat(cert['renewal_date']) if isinstance(cert['renewal_date'], str) else cert['renewal_date']
                renewal_month = renewal_date.replace(day=1)
                
                if renewal_month == current_month:
                    monthly_cert_cost += cert['cost']
        
        return monthly_cert_cost
    
    def get_facility_metrics(self, as_of_date: date) -> Dict[str, Any]:
        """Get facility utilization and cost metrics."""
        return {
            'total_monthly_cost': self.calculate_monthly_cost(as_of_date),
            'cost_per_sqft': self.calculate_monthly_cost(as_of_date) / self.size_sqft if self.size_sqft else None,
            'utilization_status': 'active' if self.is_active(as_of_date) else 'inactive',
            'lease_end_date': self.lease_end_date,
            'location': self.location,
            'facility_type': self.facility_type,
        }


class Software(BaseEntity):
    """Software subscription and license entity."""
    
    type: str = "software"
    
    # Required fields
    monthly_cost: float
    
    # Software details
    vendor: Optional[str] = None
    software_name: Optional[str] = None
    license_type: Optional[str] = None  # subscription, perpetual, usage_based
    
    # Licensing
    license_count: Optional[int] = None
    concurrent_users: Optional[int] = None
    
    # Pricing structure
    annual_cost: Optional[float] = None
    per_user_cost: Optional[float] = None
    usage_based_cost: Optional[float] = None
    
    # Contract terms
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    auto_renewal: bool = True
    
    # Support and maintenance
    support_included: bool = True
    maintenance_percentage: Optional[float] = None
    
    @field_validator('monthly_cost')
    @classmethod
    def validate_monthly_cost(cls, v: float) -> float:
        """Ensure monthly cost is positive."""
        if v <= 0:
            raise ValueError('monthly_cost must be positive')
        return v
    
    def calculate_monthly_cost(self, as_of_date: date) -> float:
        """Calculate monthly software cost."""
        if not self.is_active(as_of_date):
            return 0.0
        
        # If annual cost specified, use that
        if self.annual_cost:
            return self.annual_cost / 12
        
        # If per-user cost specified, calculate based on license count
        if self.per_user_cost and self.license_count:
            return self.per_user_cost * self.license_count
        
        # Otherwise use monthly cost
        return self.monthly_cost
    
    def calculate_annual_cost(self, as_of_date: date) -> float:
        """Calculate annual software cost."""
        return self.calculate_monthly_cost(as_of_date) * 12
    
    def get_renewal_alert(self, as_of_date: date, alert_days: int = 30) -> Optional[Dict[str, Any]]:
        """Check if renewal is approaching."""
        if not self.contract_end_date:
            return None
        
        days_until_renewal = (self.contract_end_date - as_of_date).days
        
        if days_until_renewal <= alert_days:
            return {
                'software_name': self.software_name,
                'vendor': self.vendor,
                'renewal_date': self.contract_end_date,
                'days_until_renewal': days_until_renewal,
                'annual_cost': self.calculate_annual_cost(as_of_date),
                'auto_renewal': self.auto_renewal,
            }
        
        return None


class Equipment(BaseEntity):
    """Equipment purchase and asset entity."""
    
    type: str = "equipment"
    
    # Required fields
    cost: float
    purchase_date: date
    
    # Equipment details
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    category: Optional[str] = None  # computer, lab_equipment, manufacturing, etc.
    
    # Financial
    depreciation_years: Optional[int] = None
    depreciation_method: str = "straight_line"
    residual_value: Optional[float] = None
    
    # Warranty and support
    warranty_years: Optional[int] = None
    warranty_end_date: Optional[date] = None
    support_contract_annual: Optional[float] = None
    
    # Maintenance
    maintenance_schedule: Optional[str] = None
    maintenance_cost_annual: Optional[float] = None
    
    # Location and assignment
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    
    @field_validator('cost')
    @classmethod
    def validate_cost(cls, v: float) -> float:
        """Ensure cost is positive."""
        if v <= 0:
            raise ValueError('cost must be positive')
        return v
    
    def calculate_monthly_depreciation(self, as_of_date: date) -> float:
        """Calculate monthly depreciation expense."""
        if not self.depreciation_years:
            return 0.0
        
        # Check if we're still in depreciation period
        depreciation_end = date(
            self.purchase_date.year + self.depreciation_years,
            self.purchase_date.month,
            self.purchase_date.day
        )
        
        if as_of_date > depreciation_end:
            return 0.0
        
        # Calculate depreciable amount
        depreciable_cost = self.cost - (self.residual_value or 0)
        
        # Monthly depreciation
        return depreciable_cost / (self.depreciation_years * 12)
    
    def calculate_monthly_maintenance(self, as_of_date: date) -> float:
        """Calculate monthly maintenance cost."""
        if not self.maintenance_cost_annual:
            return 0.0
        
        return self.maintenance_cost_annual / 12
    
    def calculate_monthly_support(self, as_of_date: date) -> float:
        """Calculate monthly support contract cost."""
        if not self.support_contract_annual:
            return 0.0
        
        return self.support_contract_annual / 12
    
    def calculate_total_monthly_cost(self, as_of_date: date) -> float:
        """Calculate total monthly cost including depreciation and maintenance."""
        return (
            self.calculate_monthly_depreciation(as_of_date) +
            self.calculate_monthly_maintenance(as_of_date) +
            self.calculate_monthly_support(as_of_date)
        )
    
    def get_current_book_value(self, as_of_date: date) -> float:
        """Calculate current book value of equipment."""
        if not self.depreciation_years:
            return self.cost
        
        months_since_purchase = (as_of_date.year - self.purchase_date.year) * 12 + \
                               (as_of_date.month - self.purchase_date.month)
        
        total_depreciation_months = self.depreciation_years * 12
        
        if months_since_purchase >= total_depreciation_months:
            return self.residual_value or 0
        
        monthly_depreciation = self.calculate_monthly_depreciation(as_of_date)
        total_depreciation = monthly_depreciation * months_since_purchase
        
        return max(self.cost - total_depreciation, self.residual_value or 0)
    
    def get_equipment_summary(self, as_of_date: date) -> Dict[str, Any]:
        """Get comprehensive equipment summary."""
        return {
            'name': self.name,
            'category': self.category,
            'vendor': self.vendor,
            'purchase_date': self.purchase_date,
            'original_cost': self.cost,
            'current_book_value': self.get_current_book_value(as_of_date),
            'monthly_depreciation': self.calculate_monthly_depreciation(as_of_date),
            'monthly_maintenance': self.calculate_monthly_maintenance(as_of_date),
            'total_monthly_cost': self.calculate_total_monthly_cost(as_of_date),
            'location': self.location,
            'assigned_to': self.assigned_to,
            'warranty_end_date': self.warranty_end_date,
        }