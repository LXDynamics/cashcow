"""KPI (Key Performance Indicator) calculations for CashCow."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from ..config import get_config


class KPICalculator:
    """Calculator for key performance indicators."""
    
    def __init__(self):
        """Initialize KPI calculator."""
        self.config = get_config()
    
    def calculate_all_kpis(self, 
                          df: pd.DataFrame,
                          starting_cash: float = 0.0,
                          current_date: Optional[date] = None) -> Dict[str, Any]:
        """Calculate all available KPIs for a cash flow DataFrame.
        
        Args:
            df: Cash flow DataFrame
            starting_cash: Starting cash balance
            current_date: Current date for calculations
            
        Returns:
            Dictionary of calculated KPIs
        """
        if current_date is None:
            current_date = date.today()
        
        # Adjust cash balance with starting cash
        df_adjusted = df.copy()
        df_adjusted['cash_balance'] = df['cumulative_cash_flow'] + starting_cash
        
        kpis = {}
        
        # Financial KPIs
        kpis.update(self._calculate_financial_kpis(df_adjusted, starting_cash))
        
        # Growth KPIs
        kpis.update(self._calculate_growth_kpis(df_adjusted))
        
        # Operational KPIs
        kpis.update(self._calculate_operational_kpis(df_adjusted))
        
        # Efficiency KPIs
        kpis.update(self._calculate_efficiency_kpis(df_adjusted))
        
        # Risk KPIs
        kpis.update(self._calculate_risk_kpis(df_adjusted))
        
        return kpis
    
    def _calculate_financial_kpis(self, df: pd.DataFrame, starting_cash: float) -> Dict[str, Any]:
        """Calculate financial KPIs."""
        kpis = {}
        
        # Runway (months until cash runs out)
        kpis['runway_months'] = self._calculate_runway(df, starting_cash)
        
        # Burn rate (average monthly cash consumption)
        negative_flows = df[df['net_cash_flow'] < 0]['net_cash_flow']
        if len(negative_flows) > 0:
            kpis['burn_rate'] = abs(negative_flows.mean())
        else:
            kpis['burn_rate'] = 0.0
        
        # Current month burn rate
        if len(df) > 0:
            kpis['current_burn_rate'] = abs(min(0, df['net_cash_flow'].iloc[-1]))
        else:
            kpis['current_burn_rate'] = 0.0
        
        # Cash efficiency (revenue / cash consumed)
        total_cash_consumed = abs(df[df['net_cash_flow'] < 0]['net_cash_flow'].sum())
        total_revenue = df['total_revenue'].sum()
        if total_cash_consumed > 0:
            kpis['cash_efficiency'] = total_revenue / total_cash_consumed
        else:
            kpis['cash_efficiency'] = float('inf')
        
        # Break-even analysis
        kpis['months_to_breakeven'] = self._calculate_breakeven(df)
        
        # Cash flow volatility
        kpis['cash_flow_volatility'] = df['net_cash_flow'].std()
        
        # Working capital needs
        kpis['working_capital'] = df['cash_balance'].iloc[-1] if len(df) > 0 else starting_cash
        
        return kpis
    
    def _calculate_growth_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate growth-related KPIs."""
        kpis = {}
        
        # Revenue growth rate (month-over-month) with null safety
        if len(df) >= 2:
            recent_revenue = df['total_revenue'].iloc[-3:].mean() if len(df) >= 3 else df['total_revenue'].iloc[-1]
            early_revenue = df['total_revenue'].iloc[:3].mean() if len(df) >= 3 else df['total_revenue'].iloc[0]
            
            # Ensure we have valid, non-null, positive values
            if (pd.notna(early_revenue) and pd.notna(recent_revenue) and 
                early_revenue > 0 and recent_revenue >= 0):
                months_span = max(min(len(df), 3), 1)  # Ensure at least 1 month span
                kpis['revenue_growth_rate'] = ((recent_revenue / early_revenue) ** (1/months_span) - 1) * 100
            else:
                kpis['revenue_growth_rate'] = 0.0
        else:
            kpis['revenue_growth_rate'] = 0.0
        
        # Revenue trend (linear regression slope)
        if len(df) >= 3:
            x = np.arange(len(df))
            y = df['total_revenue'].values
            slope, _ = np.polyfit(x, y, 1)
            kpis['revenue_trend'] = slope
        else:
            kpis['revenue_trend'] = 0.0
        
        # Customer acquisition metrics (if sales data available)
        monthly_sales = df['sales_revenue'].sum()
        if monthly_sales > 0 and len(df) > 0:
            kpis['average_deal_size'] = monthly_sales / len(df)
        else:
            kpis['average_deal_size'] = 0.0
        
        # Revenue diversification (Herfindahl index)
        revenue_sources = ['grant_revenue', 'investment_revenue', 'sales_revenue', 'service_revenue']
        total_revenue = df[revenue_sources].sum().sum()
        if total_revenue > 0:
            shares = df[revenue_sources].sum() / total_revenue
            herfindahl = (shares ** 2).sum()
            kpis['revenue_diversification'] = 1 - herfindahl  # Higher = more diversified
        else:
            kpis['revenue_diversification'] = 0.0
        
        return kpis
    
    def _calculate_operational_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate operational KPIs."""
        kpis = {}
        
        # Employee utilization
        if 'active_employees' in df.columns:
            kpis['average_team_size'] = df['active_employees'].mean()
            kpis['peak_team_size'] = df['active_employees'].max()
            kpis['team_growth_rate'] = self._calculate_growth_rate(df['active_employees'])
        
        # Project utilization
        if 'active_projects' in df.columns:
            kpis['average_active_projects'] = df['active_projects'].mean()
            kpis['peak_active_projects'] = df['active_projects'].max()
        
        # R&D intensity
        total_expenses = df['total_expenses'].sum()
        rd_expenses = df['project_costs'].sum()
        if total_expenses > 0:
            kpis['rd_percentage'] = (rd_expenses / total_expenses) * 100
        else:
            kpis['rd_percentage'] = 0.0
        
        # Facility utilization
        facility_costs = df['facility_costs'].sum()
        if total_expenses > 0:
            kpis['facility_cost_percentage'] = (facility_costs / total_expenses) * 100
        else:
            kpis['facility_cost_percentage'] = 0.0
        
        # Technology spending
        software_costs = df['software_costs'].sum()
        equipment_costs = df['equipment_costs'].sum()
        tech_costs = software_costs + equipment_costs
        if total_expenses > 0:
            kpis['technology_cost_percentage'] = (tech_costs / total_expenses) * 100
        else:
            kpis['technology_cost_percentage'] = 0.0
        
        return kpis
    
    def _calculate_efficiency_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate efficiency KPIs."""
        kpis = {}
        
        # Revenue per employee
        if 'revenue_per_employee' in df.columns:
            kpis['revenue_per_employee'] = df['revenue_per_employee'].mean()
        
        # Cost per employee
        if 'cost_per_employee' in df.columns:
            kpis['cost_per_employee'] = df['cost_per_employee'].mean()
        
        # Employee cost efficiency
        total_revenue = df['total_revenue'].sum()
        employee_costs = df['employee_costs'].sum()
        if employee_costs > 0:
            kpis['employee_cost_efficiency'] = total_revenue / employee_costs
        else:
            kpis['employee_cost_efficiency'] = 0.0
        
        # Project ROI
        project_costs = df['project_costs'].sum()
        # Assume projects generate future revenue (simplified)
        if project_costs > 0:
            kpis['project_cost_ratio'] = project_costs / df['total_expenses'].sum()
        else:
            kpis['project_cost_ratio'] = 0.0
        
        # Operating leverage with null safety
        if len(df) >= 2:
            revenue_change = df['total_revenue'].pct_change().fillna(0).mean()
            expense_change = df['total_expenses'].pct_change().fillna(0).mean()
            if (pd.notna(expense_change) and expense_change != 0 and 
                pd.notna(revenue_change)):
                kpis['operating_leverage'] = revenue_change / expense_change
            else:
                kpis['operating_leverage'] = 0.0
        else:
            kpis['operating_leverage'] = 0.0
        
        return kpis
    
    def _calculate_risk_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate risk-related KPIs."""
        kpis = {}
        
        # Cash flow volatility risk
        cf_volatility = df['net_cash_flow'].std()
        cf_mean = abs(df['net_cash_flow'].mean())
        if cf_mean > 0:
            kpis['cash_flow_risk'] = cf_volatility / cf_mean
        else:
            kpis['cash_flow_risk'] = 0.0
        
        # Revenue concentration risk
        revenue_sources = ['grant_revenue', 'investment_revenue', 'sales_revenue', 'service_revenue']
        if len(df) > 0:
            max_source = df[revenue_sources].sum().max()
            total_revenue = df[revenue_sources].sum().sum()
            if total_revenue > 0:
                kpis['revenue_concentration_risk'] = max_source / total_revenue
            else:
                kpis['revenue_concentration_risk'] = 0.0
        
        # Expense flexibility (variable vs fixed costs)
        # Assume employee and facility costs are fixed, others are variable
        fixed_costs = df['employee_costs'].sum() + df['facility_costs'].sum()
        total_costs = df['total_expenses'].sum()
        if total_costs > 0:
            kpis['cost_flexibility'] = 1 - (fixed_costs / total_costs)
        else:
            kpis['cost_flexibility'] = 0.0
        
        # Funding dependency risk
        external_funding = df['grant_revenue'].sum() + df['investment_revenue'].sum()
        total_revenue = df['total_revenue'].sum()
        if total_revenue > 0:
            kpis['funding_dependency'] = external_funding / total_revenue
        else:
            kpis['funding_dependency'] = 0.0
        
        return kpis
    
    def _calculate_runway(self, df: pd.DataFrame, starting_cash: float) -> float:
        """Calculate runway in months."""
        if len(df) == 0:
            return 0.0
        
        # Find when cash balance goes negative
        cash_balance = starting_cash
        for i, row in df.iterrows():
            cash_balance += row['net_cash_flow']
            if cash_balance <= 0:
                # Interpolate to find exact month
                prev_balance = cash_balance - row['net_cash_flow']
                if row['net_cash_flow'] < 0:
                    months_into_period = prev_balance / abs(row['net_cash_flow'])
                    return i + months_into_period
                else:
                    return i
        
        # If we never run out of cash, estimate based on current burn rate
        recent_flows = df['net_cash_flow'].iloc[-3:] if len(df) >= 3 else df['net_cash_flow']
        avg_burn = recent_flows.mean()
        
        if avg_burn >= 0:
            return float('inf')  # Profitable
        
        final_cash = df['cash_balance'].iloc[-1]
        return final_cash / abs(avg_burn)
    
    def _calculate_breakeven(self, df: pd.DataFrame) -> float:
        """Calculate months to break even."""
        # Find when cumulative cash flow turns positive
        for i, row in df.iterrows():
            if row['cumulative_cash_flow'] >= 0:
                return i + 1
        
        # If not achieved in the data, extrapolate
        if len(df) >= 2:
            recent_flows = df['net_cash_flow'].iloc[-3:] if len(df) >= 3 else df['net_cash_flow']
            avg_flow = recent_flows.mean()
            
            if avg_flow <= 0:
                return float('inf')  # Never break even
            
            current_deficit = abs(df['cumulative_cash_flow'].iloc[-1])
            return len(df) + (current_deficit / avg_flow)
        
        return float('inf')
    
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate compound growth rate for a series with null safety."""
        if len(series) < 2:
            return 0.0
        
        start_val = series.iloc[0]
        end_val = series.iloc[-1]
        periods = len(series) - 1
        
        # Comprehensive null and validity checks
        if (pd.isna(start_val) or pd.isna(end_val) or 
            start_val <= 0 or end_val < 0 or periods <= 0):
            return 0.0
        
        try:
            return ((end_val / start_val) ** (1/periods) - 1) * 100
        except (ZeroDivisionError, ValueError, OverflowError):
            return 0.0
    
    def calculate_kpi_trends(self, df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """Calculate rolling trends for key metrics.
        
        Args:
            df: Cash flow DataFrame
            window: Rolling window size in months
            
        Returns:
            DataFrame with trend calculations
        """
        trends = df.copy()
        
        # Rolling averages
        trends['revenue_trend'] = df['total_revenue'].rolling(window).mean()
        trends['expense_trend'] = df['total_expenses'].rolling(window).mean()
        trends['burn_trend'] = (-df['net_cash_flow']).rolling(window).mean()
        
        # Growth rates
        trends['revenue_growth_3m'] = df['total_revenue'].pct_change(periods=window) * 100
        trends['expense_growth_3m'] = df['total_expenses'].pct_change(periods=window) * 100
        
        # Efficiency trends
        if 'active_employees' in df.columns:
            trends['efficiency_trend'] = (df['total_revenue'] / df['active_employees']).rolling(window).mean()
        
        return trends
    
    def get_kpi_alerts(self, kpis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate alerts based on KPI thresholds.
        
        Args:
            kpis: Dictionary of calculated KPIs
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # Runway alerts
        runway = kpis.get('runway_months', 0)
        if runway < 3:
            alerts.append({
                'level': 'critical',
                'metric': 'runway_months',
                'message': f'Critical: Only {runway:.1f} months of runway remaining',
                'recommendation': 'Immediate action required to reduce burn or raise funding'
            })
        elif runway < 6:
            alerts.append({
                'level': 'warning',
                'metric': 'runway_months',
                'message': f'Warning: {runway:.1f} months of runway remaining',
                'recommendation': 'Begin fundraising or cost reduction planning'
            })
        
        # Burn rate alerts
        burn_rate = kpis.get('burn_rate', 0)
        if burn_rate > 100000:  # $100k/month
            alerts.append({
                'level': 'warning',
                'metric': 'burn_rate',
                'message': f'High burn rate: ${burn_rate:,.0f}/month',
                'recommendation': 'Review cost structure and hiring plans'
            })
        
        # Revenue concentration risk
        concentration = kpis.get('revenue_concentration_risk', 0)
        if concentration > 0.8:
            alerts.append({
                'level': 'warning',
                'metric': 'revenue_concentration_risk',
                'message': f'High revenue concentration: {concentration:.1%}',
                'recommendation': 'Diversify revenue sources to reduce risk'
            })
        
        # Cash flow volatility
        volatility = kpis.get('cash_flow_risk', 0)
        if volatility > 2.0:
            alerts.append({
                'level': 'info',
                'metric': 'cash_flow_risk',
                'message': f'High cash flow volatility: {volatility:.1f}',
                'recommendation': 'Consider smoothing revenue or expense timing'
            })
        
        return alerts