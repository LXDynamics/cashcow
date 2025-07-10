"""Report generation module for CashCow."""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import json

# Set matplotlib style
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


class ReportGenerator:
    """Generates visual and text reports from cash flow data."""
    
    def __init__(self, output_dir: str = "reports"):
        """Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "charts").mkdir(exist_ok=True)
        (self.output_dir / "html").mkdir(exist_ok=True)
        (self.output_dir / "csv").mkdir(exist_ok=True)
    
    def generate_cash_flow_chart(self, df: pd.DataFrame, title: str = "Cash Flow Forecast") -> str:
        """Generate cash flow chart.
        
        Args:
            df: Cash flow DataFrame
            title: Chart title
            
        Returns:
            Path to saved chart
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Convert period to datetime for plotting
        df['period_date'] = pd.to_datetime(df['period'])
        
        # Chart 1: Cash Flow Components
        ax1.plot(df['period_date'], df['total_revenue'], 
                label='Revenue', linewidth=2, color='green')
        ax1.plot(df['period_date'], df['total_expenses'], 
                label='Expenses', linewidth=2, color='red')
        ax1.plot(df['period_date'], df['net_cash_flow'], 
                label='Net Cash Flow', linewidth=2, color='blue')
        
        ax1.set_title(f'{title} - Cash Flow Components')
        ax1.set_ylabel('Amount ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        
        # Chart 2: Cumulative Cash Balance
        ax2.plot(df['period_date'], df['cash_balance'], 
                linewidth=3, color='purple')
        ax2.fill_between(df['period_date'], df['cash_balance'], 
                        alpha=0.3, color='purple')
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        ax2.set_title('Cumulative Cash Balance')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Cash Balance ($)')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "charts" / f"cash_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def generate_revenue_breakdown_chart(self, df: pd.DataFrame) -> str:
        """Generate revenue breakdown chart.
        
        Args:
            df: Cash flow DataFrame with revenue categories
            
        Returns:
            Path to saved chart
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Chart 1: Revenue by Category (Stacked Area)
        df['period_date'] = pd.to_datetime(df['period'])
        
        revenue_cols = [col for col in df.columns if col.startswith('revenue_') and col != 'revenue_growth_rate']
        
        if revenue_cols:
            ax1.stackplot(df['period_date'], *[df[col] for col in revenue_cols], 
                         labels=[col.replace('revenue_', '').title() for col in revenue_cols],
                         alpha=0.8)
            ax1.set_title('Revenue by Category (Stacked)')
            ax1.set_ylabel('Revenue ($)')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # Chart 2: Total Revenue Pie Chart (Last Month)
        if len(df) > 0:
            last_month_revenues = {}
            for col in revenue_cols:
                total = df[col].sum()
                if total > 0:
                    last_month_revenues[col.replace('revenue_', '').title()] = total
            
            if last_month_revenues:
                ax2.pie(last_month_revenues.values(), labels=last_month_revenues.keys(), 
                       autopct='%1.1f%%', startangle=90)
                ax2.set_title('Total Revenue by Category')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "charts" / f"revenue_breakdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def generate_expense_breakdown_chart(self, df: pd.DataFrame) -> str:
        """Generate expense breakdown chart.
        
        Args:
            df: Cash flow DataFrame with expense categories
            
        Returns:
            Path to saved chart
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Chart 1: Expenses by Category (Stacked Bar)
        df['period_date'] = pd.to_datetime(df['period'])
        
        expense_cols = [col for col in df.columns if col.startswith('expense_')]
        
        if expense_cols:
            # Group by quarter for cleaner visualization
            df['quarter'] = df['period_date'].dt.to_period('Q')
            quarterly_data = df.groupby('quarter')[expense_cols].sum()
            
            quarterly_data.plot(kind='bar', stacked=True, ax=ax1, 
                              figsize=(10, 6), colormap='Reds')
            ax1.set_title('Expenses by Category (Quarterly)')
            ax1.set_ylabel('Expenses ($)')
            ax1.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.set_xlabel('Quarter')
        
        # Chart 2: Expense Trends
        if expense_cols:
            for col in expense_cols[:5]:  # Show top 5 categories
                ax2.plot(df['period_date'], df[col], 
                        label=col.replace('expense_', '').title(), 
                        linewidth=2, marker='o', markersize=4)
            
            ax2.set_title('Expense Trends by Category')
            ax2.set_ylabel('Monthly Expenses ($)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "charts" / f"expense_breakdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def generate_kpi_dashboard(self, kpis: Dict[str, Any]) -> str:
        """Generate KPI dashboard chart.
        
        Args:
            kpis: Dictionary of KPI values
            
        Returns:
            Path to saved chart
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # KPI 1: Runway (Gauge Chart)
        runway = kpis.get('runway_months', 0)
        if runway != float('inf'):
            self._create_gauge_chart(ax1, runway, 'Runway (Months)', 
                                   max_val=36, thresholds=[6, 12, 18])
        else:
            ax1.text(0.5, 0.5, 'Infinite\n(Profitable)', 
                    ha='center', va='center', fontsize=20, 
                    color='green', weight='bold')
            ax1.set_title('Runway (Months)')
        
        # KPI 2: Burn Rate vs Revenue
        burn_rate = abs(kpis.get('burn_rate', 0))
        revenue_rate = kpis.get('monthly_revenue_average', 0)
        
        categories = ['Monthly Burn', 'Monthly Revenue']
        values = [burn_rate, revenue_rate]
        colors = ['red', 'green']
        
        ax2.bar(categories, values, color=colors, alpha=0.7)
        ax2.set_title('Monthly Burn vs Revenue')
        ax2.set_ylabel('Amount ($)')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, v in enumerate(values):
            ax2.text(i, v + max(values) * 0.01, f'${v:,.0f}', 
                    ha='center', va='bottom', fontweight='bold')
        
        # KPI 3: Growth Metrics
        growth_metrics = {
            'Revenue Growth': kpis.get('revenue_growth_rate', 0),
            'Employee Growth': kpis.get('employee_growth_rate', 0),
            'Efficiency Growth': kpis.get('cash_efficiency_trend', 0)
        }
        
        y_pos = np.arange(len(growth_metrics))
        values = list(growth_metrics.values())
        colors = ['green' if v > 0 else 'red' for v in values]
        
        ax3.barh(y_pos, values, color=colors, alpha=0.7)
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(growth_metrics.keys())
        ax3.set_xlabel('Growth Rate (%)')
        ax3.set_title('Growth Metrics')
        ax3.grid(True, alpha=0.3, axis='x')
        
        # KPI 4: Financial Health Score
        health_score = self._calculate_health_score(kpis)
        self._create_gauge_chart(ax4, health_score, 'Financial Health Score', 
                               max_val=100, thresholds=[30, 60, 80])
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "charts" / f"kpi_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def generate_scenario_comparison_chart(self, scenario_results: Dict[str, pd.DataFrame]) -> str:
        """Generate scenario comparison chart.
        
        Args:
            scenario_results: Dictionary of scenario name -> DataFrame
            
        Returns:
            Path to saved chart
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Chart 1: Cash Balance Comparison
        for scenario, df in scenario_results.items():
            df['period_date'] = pd.to_datetime(df['period'])
            ax1.plot(df['period_date'], df['cash_balance'], 
                    label=scenario.title(), linewidth=2, marker='o', markersize=3)
        
        ax1.set_title('Cash Balance by Scenario')
        ax1.set_ylabel('Cash Balance ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # Chart 2: Revenue Comparison
        for scenario, df in scenario_results.items():
            ax2.plot(df['period_date'], df['total_revenue'], 
                    label=scenario.title(), linewidth=2)
        
        ax2.set_title('Revenue by Scenario')
        ax2.set_ylabel('Monthly Revenue ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # Chart 3: Expense Comparison
        for scenario, df in scenario_results.items():
            ax3.plot(df['period_date'], df['total_expenses'], 
                    label=scenario.title(), linewidth=2)
        
        ax3.set_title('Expenses by Scenario')
        ax3.set_ylabel('Monthly Expenses ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # Chart 4: Summary Metrics
        summary_data = []
        for scenario, df in scenario_results.items():
            summary_data.append({
                'Scenario': scenario.title(),
                'Total Revenue': df['total_revenue'].sum(),
                'Total Expenses': df['total_expenses'].sum(),
                'Final Balance': df['cash_balance'].iloc[-1],
                'Net Cash Flow': df['net_cash_flow'].sum()
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        x = np.arange(len(summary_df))
        width = 0.2
        
        ax4.bar(x - width*1.5, summary_df['Total Revenue'], width, 
               label='Total Revenue', color='green', alpha=0.7)
        ax4.bar(x - width*0.5, summary_df['Total Expenses'], width, 
               label='Total Expenses', color='red', alpha=0.7)
        ax4.bar(x + width*0.5, summary_df['Final Balance'], width, 
               label='Final Balance', color='blue', alpha=0.7)
        ax4.bar(x + width*1.5, summary_df['Net Cash Flow'], width, 
               label='Net Cash Flow', color='purple', alpha=0.7)
        
        ax4.set_title('Scenario Summary Comparison')
        ax4.set_ylabel('Amount ($)')
        ax4.set_xticks(x)
        ax4.set_xticklabels(summary_df['Scenario'])
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "charts" / f"scenario_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def export_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """Export DataFrame to CSV.
        
        Args:
            df: DataFrame to export
            filename: Output filename
            
        Returns:
            Path to saved CSV file
        """
        csv_path = self.output_dir / "csv" / f"{filename}.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)
    
    def generate_html_report(self, df: pd.DataFrame, kpis: Dict[str, Any], 
                           scenario: str = "baseline") -> str:
        """Generate comprehensive HTML report.
        
        Args:
            df: Cash flow DataFrame
            kpis: KPI dictionary
            scenario: Scenario name
            
        Returns:
            Path to saved HTML report
        """
        # Generate charts
        cash_flow_chart = self.generate_cash_flow_chart(df, f"Cash Flow Forecast - {scenario.title()}")
        revenue_chart = self.generate_revenue_breakdown_chart(df)
        expense_chart = self.generate_expense_breakdown_chart(df)
        kpi_chart = self.generate_kpi_dashboard(kpis)
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CashCow Financial Report - {scenario.title()}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; color: #333; }}
                .section {{ margin: 30px 0; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                .chart img {{ max-width: 100%; height: auto; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .kpi-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }}
                .kpi-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .kpi-label {{ font-size: 14px; color: #7f8c8d; }}
                .summary-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .summary-table th, .summary-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .summary-table th {{ background-color: #f2f2f2; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CashCow Financial Report</h1>
                <h2>{scenario.title()} Scenario</h2>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">${df['total_revenue'].sum():,.0f}</div>
                        <div class="kpi-label">Total Revenue</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${df['total_expenses'].sum():,.0f}</div>
                        <div class="kpi-label">Total Expenses</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${df['net_cash_flow'].sum():,.0f}</div>
                        <div class="kpi-label">Net Cash Flow</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${df['cash_balance'].iloc[-1]:,.0f}</div>
                        <div class="kpi-label">Final Balance</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Key Performance Indicators</h2>
                <div class="chart">
                    <img src="{Path(kpi_chart).name}" alt="KPI Dashboard">
                </div>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">{kpis.get('runway_months', 0):.1f}</div>
                        <div class="kpi-label">Runway (Months)</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">${kpis.get('burn_rate', 0):,.0f}</div>
                        <div class="kpi-label">Monthly Burn Rate</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{kpis.get('revenue_growth_rate', 0):.1f}%</div>
                        <div class="kpi-label">Revenue Growth</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{kpis.get('rd_percentage', 0):.1f}%</div>
                        <div class="kpi-label">R&D Percentage</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Cash Flow Analysis</h2>
                <div class="chart">
                    <img src="{Path(cash_flow_chart).name}" alt="Cash Flow Forecast">
                </div>
            </div>
            
            <div class="section">
                <h2>Revenue Analysis</h2>
                <div class="chart">
                    <img src="{Path(revenue_chart).name}" alt="Revenue Breakdown">
                </div>
            </div>
            
            <div class="section">
                <h2>Expense Analysis</h2>
                <div class="chart">
                    <img src="{Path(expense_chart).name}" alt="Expense Breakdown">
                </div>
            </div>
            
            <div class="section">
                <h2>Period Details</h2>
                <table class="summary-table">
                    <tr>
                        <th>Period</th>
                        <th>Revenue</th>
                        <th>Expenses</th>
                        <th>Net Cash Flow</th>
                        <th>Cash Balance</th>
                    </tr>
        """
        
        # Add period details
        for _, row in df.iterrows():
            html_content += f"""
                    <tr>
                        <td>{row['period']}</td>
                        <td>${row['total_revenue']:,.0f}</td>
                        <td>${row['total_expenses']:,.0f}</td>
                        <td>${row['net_cash_flow']:,.0f}</td>
                        <td>${row['cash_balance']:,.0f}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Risk Analysis</h2>
                <div class="alert">
                    <strong>Key Risks:</strong>
                    <ul>
                        <li>Cash runway: Monitor closely if below 12 months</li>
                        <li>Revenue growth: Ensure sustainable growth trajectory</li>
                        <li>Expense management: Keep burn rate aligned with revenue</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save HTML report
        html_path = self.output_dir / "html" / f"report_{scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        return str(html_path)
    
    def _create_gauge_chart(self, ax, value: float, title: str, max_val: float = 100, 
                           thresholds: List[float] = None):
        """Create a gauge chart on the given axis."""
        if thresholds is None:
            thresholds = [30, 60, 80]
        
        # Create gauge
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)
        
        # Color zones
        colors = ['red', 'orange', 'yellow', 'green']
        zone_values = [0] + thresholds + [max_val]
        
        for i in range(len(colors)):
            start_angle = np.pi * zone_values[i] / max_val
            end_angle = np.pi * zone_values[i + 1] / max_val
            theta_zone = np.linspace(start_angle, end_angle, 20)
            r_zone = np.ones_like(theta_zone)
            ax.fill_between(theta_zone, 0, r_zone, color=colors[i], alpha=0.3)
        
        # Value needle
        value_angle = np.pi * (1 - value / max_val)
        ax.plot([value_angle, value_angle], [0, 0.8], 'k-', linewidth=3)
        
        # Formatting
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 1)
        ax.set_xlim(0, np.pi)
        ax.set_title(title)
        ax.text(np.pi/2, 0.5, f'{value:.1f}', ha='center', va='center', 
                fontsize=16, fontweight='bold')
        
        # Remove ticks
        ax.set_xticks([])
        ax.set_yticks([])
    
    def _calculate_health_score(self, kpis: Dict[str, Any]) -> float:
        """Calculate overall financial health score."""
        score = 0
        
        # Runway score (0-30 points)
        runway = kpis.get('runway_months', 0)
        if runway == float('inf'):
            score += 30
        elif runway > 18:
            score += 30
        elif runway > 12:
            score += 25
        elif runway > 6:
            score += 15
        elif runway > 3:
            score += 10
        else:
            score += 5
        
        # Revenue growth score (0-25 points)
        growth = kpis.get('revenue_growth_rate', 0)
        if growth > 20:
            score += 25
        elif growth > 10:
            score += 20
        elif growth > 5:
            score += 15
        elif growth > 0:
            score += 10
        else:
            score += 5
        
        # Cash efficiency score (0-25 points)
        efficiency = kpis.get('cash_efficiency', 0)
        if efficiency > 0.8:
            score += 25
        elif efficiency > 0.6:
            score += 20
        elif efficiency > 0.4:
            score += 15
        elif efficiency > 0.2:
            score += 10
        else:
            score += 5
        
        # Burn rate score (0-20 points)
        burn_rate = abs(kpis.get('burn_rate', 0))
        monthly_revenue = kpis.get('monthly_revenue_average', 0)
        
        if monthly_revenue > 0:
            burn_ratio = burn_rate / monthly_revenue
            if burn_ratio < 0.5:
                score += 20
            elif burn_ratio < 0.8:
                score += 15
            elif burn_ratio < 1.2:
                score += 10
            else:
                score += 5
        else:
            score += 5
        
        return min(score, 100)