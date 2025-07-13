#!/usr/bin/env python3
"""
Custom Calculator Examples for CashCow

This file demonstrates how to create custom calculators for specialized
business logic specific to rocket engine companies.

To use these calculators:
1. Copy this file to your project
2. Import and register them in your main application
3. Reference them in your config/settings.yaml file
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
import math
from decimal import Decimal

from cashcow.engine.calculators import Calculator, CalculatorRegistry
from cashcow.models.base import BaseEntity


class RocketEngineTestCalculator(Calculator):
    """
    Custom calculator for rocket engine testing costs.
    
    Calculates the cost of engine testing based on:
    - Test duration
    - Facility requirements  
    - Fuel consumption
    - Equipment wear and tear
    """
    
    name = "rocket_engine_test_calc"
    description = "Calculates rocket engine testing costs"
    
    def calculate(self, entity: BaseEntity, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate testing costs over the period."""
        if entity.type != "engine_test":
            return []
        
        results = []
        current_date = start_date
        
        # Extract test parameters
        test_duration_hours = entity.data.get("test_duration_hours", 4)
        thrust_level = entity.data.get("thrust_level_lbf", 100000)  # pounds force
        tests_per_month = entity.data.get("tests_per_month", 2)
        
        # Cost factors
        facility_cost_per_hour = 5000  # $5K/hour for test facility
        fuel_cost_per_pound = 2.50     # $2.50 per pound of propellant
        
        # Fuel consumption based on thrust and duration (simplified model)
        fuel_consumption_rate = thrust_level * 0.8  # lbs/hour (simplified)
        
        while current_date < end_date:
            # Calculate monthly testing costs
            month_end = self._get_month_end(current_date)
            
            # Facility costs
            facility_cost = facility_cost_per_hour * test_duration_hours * tests_per_month
            
            # Fuel costs  
            fuel_consumption = fuel_consumption_rate * test_duration_hours * tests_per_month
            fuel_cost = fuel_consumption * fuel_cost_per_pound
            
            # Equipment wear and maintenance (10% of test cost)
            maintenance_cost = (facility_cost + fuel_cost) * 0.1
            
            # Safety and compliance costs (fixed per test)
            safety_cost = 2000 * tests_per_month
            
            total_cost = facility_cost + fuel_cost + maintenance_cost + safety_cost
            
            results.append({
                "date": current_date,
                "amount": -total_cost,  # Negative for expense
                "category": "testing",
                "description": f"{tests_per_month} engine tests ({test_duration_hours}h each)",
                "details": {
                    "facility_cost": facility_cost,
                    "fuel_cost": fuel_cost,
                    "maintenance_cost": maintenance_cost,
                    "safety_cost": safety_cost,
                    "fuel_consumed_lbs": fuel_consumption
                }
            })
            
            current_date = month_end + timedelta(days=1)
        
        return results


class SpaceXContractCalculator(Calculator):
    """
    Custom calculator for SpaceX-style milestone-based contracts.
    
    Models revenue from contracts with:
    - Milestone-based payments
    - Performance bonuses
    - Penalty clauses for delays
    """
    
    name = "spacex_contract_calc"
    description = "SpaceX milestone-based contract revenue"
    
    def calculate(self, entity: BaseEntity, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate milestone-based contract revenue."""
        if entity.type != "spacex_contract":
            return []
        
        results = []
        
        # Contract parameters
        total_value = entity.data.get("total_value", 10000000)
        milestones = entity.data.get("milestones", [])
        performance_bonus_rate = entity.data.get("performance_bonus_rate", 0.05)  # 5%
        delay_penalty_rate = entity.data.get("delay_penalty_rate", 0.02)  # 2% per month
        
        # Default milestones if none specified
        if not milestones:
            milestones = [
                {"name": "Design Review", "percentage": 0.20, "target_date": "2024-03-01"},
                {"name": "Critical Design Review", "percentage": 0.25, "target_date": "2024-06-01"},
                {"name": "First Article Test", "percentage": 0.30, "target_date": "2024-09-01"},
                {"name": "Qualification Testing", "percentage": 0.15, "target_date": "2024-11-01"},
                {"name": "Delivery", "percentage": 0.10, "target_date": "2024-12-15"}
            ]
        
        for milestone in milestones:
            milestone_date = datetime.strptime(milestone["target_date"], "%Y-%m-%d").date()
            
            if start_date <= milestone_date <= end_date:
                base_payment = total_value * milestone["percentage"]
                
                # Calculate performance bonus/penalty based on schedule
                actual_completion = milestone_date  # Assuming on-time for this example
                target_date = milestone_date
                delay_months = max(0, (actual_completion - target_date).days / 30)
                
                # Performance adjustment
                if delay_months == 0:
                    # On time - get performance bonus
                    performance_adjustment = base_payment * performance_bonus_rate
                else:
                    # Delayed - pay penalty
                    performance_adjustment = -base_payment * delay_penalty_rate * delay_months
                
                final_payment = base_payment + performance_adjustment
                
                results.append({
                    "date": milestone_date,
                    "amount": final_payment,
                    "category": "contract_revenue",
                    "description": f"SpaceX {milestone['name']} milestone",
                    "details": {
                        "base_payment": base_payment,
                        "performance_adjustment": performance_adjustment,
                        "delay_months": delay_months,
                        "milestone_percentage": milestone["percentage"]
                    }
                })
        
        return results


class EquityVestingCalculator(Calculator):
    """
    Custom calculator for employee equity vesting schedules.
    
    Handles:
    - Cliff periods
    - Monthly vesting
    - Acceleration on acquisition
    - 409A valuations
    """
    
    name = "equity_vesting_calc"
    description = "Employee equity vesting calculations"
    
    def calculate(self, entity: BaseEntity, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate equity vesting schedule."""
        if entity.type != "employee" or not entity.data.get("equity_eligible", False):
            return []
        
        results = []
        
        # Equity parameters
        total_shares = entity.data.get("equity_shares", 0)
        cliff_months = entity.data.get("equity_cliff_months", 12)
        vest_years = entity.data.get("equity_vest_years", 4)
        equity_start_date = entity.data.get("equity_start_date", entity.data.get("start_date"))
        
        if isinstance(equity_start_date, str):
            equity_start_date = datetime.strptime(equity_start_date, "%Y-%m-%d").date()
        
        # Calculate vesting schedule
        cliff_date = equity_start_date + timedelta(days=cliff_months * 30)
        vest_end_date = equity_start_date + timedelta(days=vest_years * 365)
        
        # Monthly shares after cliff
        monthly_shares = total_shares / (vest_years * 12)
        
        current_date = max(start_date, equity_start_date)
        
        while current_date < end_date and current_date < vest_end_date:
            if current_date >= cliff_date:
                # Calculate 409A valuation (simplified model)
                days_since_start = (current_date - equity_start_date).days
                base_409a = 10.0  # Base $10 per share
                growth_rate = 0.02  # 2% monthly growth
                current_409a = base_409a * (1 + growth_rate) ** (days_since_start / 30)
                
                # Vested shares this month
                if current_date == cliff_date:
                    # Cliff vesting - vest all shares up to cliff
                    vested_shares = monthly_shares * cliff_months
                else:
                    # Regular monthly vesting
                    vested_shares = monthly_shares
                
                # Calculate expense (for company) and value (for employee)
                share_value = vested_shares * current_409a
                
                results.append({
                    "date": current_date,
                    "amount": -share_value,  # Expense for company
                    "category": "equity_expense",
                    "description": f"Equity vesting for {entity.data.get('name', 'Employee')}",
                    "details": {
                        "vested_shares": vested_shares,
                        "share_price_409a": current_409a,
                        "total_value": share_value,
                        "cumulative_vested": self._calculate_cumulative_vested(
                            current_date, equity_start_date, monthly_shares, cliff_months
                        )
                    }
                })
            
            current_date = self._get_month_end(current_date) + timedelta(days=1)
        
        return results
    
    def _calculate_cumulative_vested(self, current_date: date, start_date: date, 
                                   monthly_shares: float, cliff_months: int) -> float:
        """Calculate total shares vested to date."""
        months_elapsed = (current_date - start_date).days / 30
        if months_elapsed < cliff_months:
            return 0
        return monthly_shares * months_elapsed


class RegulatoryCostCalculator(Calculator):
    """
    Custom calculator for regulatory compliance costs in aerospace.
    
    Accounts for:
    - FAA licensing fees
    - ITAR compliance
    - Export control
    - Safety certifications
    """
    
    name = "regulatory_cost_calc"
    description = "Aerospace regulatory compliance costs"
    
    def calculate(self, entity: BaseEntity, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate regulatory compliance costs."""
        if entity.type != "regulatory_compliance":
            return []
        
        results = []
        
        # Regulatory cost components
        faa_annual_fee = entity.data.get("faa_annual_fee", 50000)
        itar_compliance_monthly = entity.data.get("itar_compliance_monthly", 15000)
        export_control_quarterly = entity.data.get("export_control_quarterly", 25000)
        
        # ITAR and export control staffing
        compliance_staff_count = entity.data.get("compliance_staff_count", 2)
        compliance_staff_salary = entity.data.get("compliance_staff_salary", 120000)
        
        current_date = start_date
        
        while current_date < end_date:
            month_costs = []
            
            # Monthly ITAR compliance
            month_costs.append({
                "type": "itar_compliance",
                "amount": itar_compliance_monthly,
                "description": "ITAR compliance consulting and documentation"
            })
            
            # Quarterly export control review
            if current_date.month % 3 == 1:  # January, April, July, October
                month_costs.append({
                    "type": "export_control",
                    "amount": export_control_quarterly,
                    "description": "Export control review and documentation"
                })
            
            # Annual FAA fees
            if current_date.month == 1:  # January
                month_costs.append({
                    "type": "faa_licensing",
                    "amount": faa_annual_fee,
                    "description": "FAA licensing and certification fees"
                })
            
            # Compliance staff costs
            monthly_staff_cost = (compliance_staff_salary / 12) * compliance_staff_count * 1.3  # With overhead
            month_costs.append({
                "type": "compliance_staff",
                "amount": monthly_staff_cost,
                "description": f"Regulatory compliance staff ({compliance_staff_count} FTE)"
            })
            
            # Sum all costs for the month
            total_monthly_cost = sum(cost["amount"] for cost in month_costs)
            
            results.append({
                "date": current_date,
                "amount": -total_monthly_cost,  # Negative for expense
                "category": "regulatory",
                "description": "Regulatory compliance costs",
                "details": {
                    "cost_breakdown": month_costs,
                    "staff_count": compliance_staff_count
                }
            })
            
            current_date = self._get_month_end(current_date) + timedelta(days=1)
        
        return results


# Register all custom calculators
def register_custom_calculators():
    """Register all custom calculators with the CashCow system."""
    
    # Register each calculator
    CalculatorRegistry.register(RocketEngineTestCalculator())
    CalculatorRegistry.register(SpaceXContractCalculator()) 
    CalculatorRegistry.register(EquityVestingCalculator())
    CalculatorRegistry.register(RegulatoryCostCalculator())
    
    print("Registered custom calculators:")
    for calc_name in ["rocket_engine_test_calc", "spacex_contract_calc", 
                      "equity_vesting_calc", "regulatory_cost_calc"]:
        print(f"  - {calc_name}")


# Usage example
if __name__ == "__main__":
    # Register calculators
    register_custom_calculators()
    
    # Example entity configurations for testing
    example_entities = {
        "engine_test": {
            "type": "engine_test",
            "name": "Raptor V2 Testing Campaign",
            "test_duration_hours": 6,
            "thrust_level_lbf": 230000,
            "tests_per_month": 4,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        
        "spacex_contract": {
            "type": "spacex_contract", 
            "name": "Dragon Engine Supply Contract",
            "total_value": 50000000,
            "performance_bonus_rate": 0.08,
            "delay_penalty_rate": 0.03
        },
        
        "employee_with_equity": {
            "type": "employee",
            "name": "Senior Propulsion Engineer",
            "salary": 160000,
            "equity_eligible": True,
            "equity_shares": 25000,
            "equity_cliff_months": 12,
            "equity_vest_years": 4,
            "start_date": "2024-01-01"
        },
        
        "regulatory_compliance": {
            "type": "regulatory_compliance",
            "name": "Aerospace Compliance Program",
            "faa_annual_fee": 75000,
            "itar_compliance_monthly": 20000,
            "export_control_quarterly": 35000,
            "compliance_staff_count": 3,
            "compliance_staff_salary": 130000
        }
    }
    
    print("\nExample entity configurations created.")
    print("To use these in CashCow:")
    print("1. Copy this file to your project directory")
    print("2. Import and call register_custom_calculators() in your main app")
    print("3. Add the calculator names to your config/settings.yaml entity types")
    print("4. Create entities using the example configurations above")