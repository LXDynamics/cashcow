import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import matplotlib.pyplot as plt
import json
from unittest.mock import Mock, patch, MagicMock

from cashcow.storage.database import EntityStore
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.kpis import KPICalculator
from cashcow.reports.generator import ReportGenerator
from cashcow.models.entities import Employee, Grant, Investment, Facility


class TestReportGenerator:
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.reports_dir = Path(self.temp_dir) / 'reports'
        self.reports_dir.mkdir(parents=True)
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
        self.kpi_calculator = KPICalculator()
        self.report_generator = ReportGenerator(str(self.reports_dir), self.store, self.engine, self.kpi_calculator)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        # Close any open matplotlib figures
        plt.close('all')
    
    def create_test_data(self):
        """Create test data for report generation"""
        entities = [
            Employee(
                type='employee',
                name='CEO',
                start_date=date(2024, 1, 1),
                salary=180000,
                pay_frequency='monthly',
                overhead_multiplier=1.4,
                tags=['executive', 'core']
            ),
            Employee(
                type='employee',
                name='Engineer',
                start_date=date(2024, 1, 1),
                salary=120000,
                pay_frequency='monthly',
                overhead_multiplier=1.3,
                tags=['engineering', 'core']
            ),
            Employee(
                type='employee',
                name='Marketing Manager',
                start_date=date(2024, 6, 1),
                salary=95000,
                pay_frequency='monthly',
                overhead_multiplier=1.25,
                tags=['marketing', 'growth']
            ),
            Grant(
                type='grant',
                name='SBIR Phase I',
                start_date=date(2024, 1, 1),
                amount=275000,
                grantor='NASA',
                milestones=[
                    {'name': 'Phase 1', 'amount': 137500, 'due_date': '2024-06-01'},
                    {'name': 'Phase 2', 'amount': 137500, 'due_date': '2024-12-01'}
                ],
                tags=['government', 'research']
            ),
            Investment(
                type='investment',
                name='Seed Round',
                start_date=date(2024, 3, 1),
                amount=1500000,
                investor='Space Ventures',
                disbursement_schedule=[
                    {'date': '2024-03-15', 'amount': 750000},
                    {'date': '2024-09-15', 'amount': 750000}
                ],
                tags=['private', 'equity']
            ),
            Facility(
                type='facility',
                name='Main Office',
                start_date=date(2024, 1, 1),
                monthly_cost=12000,
                tags=['office', 'overhead']
            )
        ]
        
        for entity in entities:
            self.store.add_entity(entity)
        
        # Generate forecast data
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        forecast_df = self.engine.calculate_period(start_date, end_date)
        
        # Calculate KPIs
        kpis = self.kpi_calculator.calculate_all_kpis(forecast_df)
        
        return forecast_df, kpis
    
    def _scale_numeric_columns(self, df, scale_factor):
        """Scale only numeric columns in a DataFrame."""
        df_copy = df.copy()
        numeric_cols = df_copy.select_dtypes(include=['number']).columns
        df_copy[numeric_cols] = df_copy[numeric_cols] * scale_factor
        return df_copy
    
    def test_report_generator_initialization(self):
        """Test ReportGenerator initialization"""
        self.setUp()
        
        assert self.report_generator.output_dir == self.reports_dir
        
        # Check that output directory exists
        assert self.reports_dir.exists()
        assert self.reports_dir.is_dir()
        
        # Check that subdirectories are created
        assert (self.reports_dir / "charts").exists()
        assert (self.reports_dir / "html").exists()
        assert (self.reports_dir / "csv").exists()
        
        self.tearDown()
    
    def test_generate_cash_flow_chart(self):
        """Test cash flow chart generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate chart
        chart_path = self.report_generator.generate_cash_flow_chart(
            forecast_df, 
            title='Test Cash Flow Chart'
        )
        
        # Verify chart was created
        chart_path_obj = Path(chart_path)
        assert chart_path_obj.exists()
        assert chart_path_obj.suffix == '.png'
        
        # Verify file is not empty
        assert chart_path_obj.stat().st_size > 0
        
        self.tearDown()
    
    def test_generate_revenue_breakdown_chart(self):
        """Test revenue breakdown chart generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate chart
        chart_path = self.report_generator.generate_revenue_breakdown_chart(
            forecast_df
        )
        
        # Verify chart was created
        chart_path_obj = Path(chart_path)
        assert chart_path_obj.exists()
        assert chart_path_obj.suffix == '.png'
        
        # Verify file is not empty
        assert chart_path_obj.stat().st_size > 0
        
        self.tearDown()
    
    def test_generate_expense_breakdown_chart(self):
        """Test expense breakdown chart generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate chart
        chart_path = self.report_generator.generate_expense_breakdown_chart(
            forecast_df
        )
        
        # Verify chart was created
        chart_path_obj = Path(chart_path)
        assert chart_path_obj.exists()
        assert chart_path_obj.suffix == '.png'
        
        # Verify file is not empty
        assert chart_path_obj.stat().st_size > 0
        
        self.tearDown()
    
    def test_generate_kpi_dashboard(self):
        """Test KPI dashboard generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate dashboard
        dashboard_path = self.report_generator.generate_kpi_dashboard(
            kpis
        )
        
        # Verify dashboard was created
        dashboard_path_obj = Path(dashboard_path)
        assert dashboard_path_obj.exists()
        assert dashboard_path_obj.suffix == '.png'
        
        # Verify file is not empty
        assert dashboard_path_obj.stat().st_size > 0
        
        self.tearDown()
    
    def test_scenario_comparison_chart(self):
        """Test scenario comparison chart generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Create scenario results dictionary
        optimistic_df = forecast_df.copy()
        numeric_cols = forecast_df.select_dtypes(include=['number']).columns
        optimistic_df[numeric_cols] = optimistic_df[numeric_cols] * 1.1
        
        scenario_results = {
            'baseline': forecast_df,
            'optimistic': optimistic_df,
        }
        
        # Generate chart
        chart_path = self.report_generator.generate_scenario_comparison_chart(
            scenario_results
        )
        
        # Verify chart was created
        chart_path_obj = Path(chart_path)
        assert chart_path_obj.exists()
        assert chart_path_obj.suffix == '.png'
        
        # Verify file is not empty
        assert chart_path_obj.stat().st_size > 0
        
        self.tearDown()
    
    def test_export_to_csv(self):
        """Test CSV export functionality"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Export to CSV
        csv_path = self.report_generator.export_to_csv(
            forecast_df,
            filename='test_forecast'
        )
        
        # Verify CSV was created
        csv_path_obj = Path(csv_path)
        assert csv_path_obj.exists()
        assert csv_path_obj.suffix == '.csv'
        
        # Verify CSV content
        loaded_df = pd.read_csv(csv_path)
        assert len(loaded_df) == len(forecast_df)
        assert list(loaded_df.columns) == list(forecast_df.columns)
        
        self.tearDown()
    
    def test_export_functionality_basic(self):
        """Test basic export functionality for CSV"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Test CSV export
        csv_path = self.report_generator.export_to_csv(
            forecast_df,
            filename='test_export'
        )
        
        # Verify CSV was created
        csv_path_obj = Path(csv_path)
        assert csv_path_obj.exists()
        assert csv_path_obj.suffix == '.csv'
        
        # Verify CSV content can be loaded
        loaded_df = pd.read_csv(csv_path)
        assert len(loaded_df) > 0
        
        self.tearDown()
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate HTML report
        html_path = self.report_generator.generate_html_report(
            forecast_df,
            kpis,
            scenario='test'
        )
        
        # Verify HTML was created
        html_path_obj = Path(html_path)
        assert html_path_obj.exists()
        assert html_path_obj.suffix == '.html'
        
        # Verify HTML content
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        assert '<html>' in html_content
        assert 'CashCow Financial Report' in html_content
        assert 'Cash Flow' in html_content
        assert 'KPI' in html_content
        
        self.tearDown()
    
    def test_generate_pdf_report(self):
        """Test PDF report generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Mock PDF generation (requires additional dependencies)
        with patch('cashcow.reports.generator.ReportGenerator._generate_pdf') as mock_pdf:
            mock_pdf.return_value = self.reports_dir / 'test_report.pdf'
            
            # Generate PDF report
            pdf_path = self.report_generator.generate_pdf_report(
                forecast_df,
                kpis,
                title='Test PDF Report',
                filename='test_report.pdf'
            )
            
            # Verify PDF generation was called
            mock_pdf.assert_called_once()
            assert pdf_path.suffix == '.pdf'
        
        self.tearDown()
    
    def test_generate_complete_report_package(self):
        """Test complete report package generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate complete report package
        package_path = self.report_generator.generate_complete_report_package(
            forecast_df,
            kpis,
            title='Test Complete Report',
            package_name='test_package'
        )
        
        # Verify package directory was created
        assert package_path.exists()
        assert package_path.is_dir()
        
        # Verify package contains expected files
        expected_files = [
            'cash_flow_chart.png',
            'revenue_breakdown.png',
            'expense_breakdown.png',
            'kpi_dashboard.png',
            'runway_analysis.png',
            'burn_rate_chart.png',
            'forecast_data.csv',
            'forecast_data.xlsx',
            'kpis.json',
            'report.html'
        ]
        
        for filename in expected_files:
            file_path = package_path / filename
            assert file_path.exists(), f"Missing file: {filename}"
        
        self.tearDown()
    
    def test_generate_executive_summary(self):
        """Test executive summary generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate executive summary
        summary = self.report_generator.generate_executive_summary(forecast_df, kpis)
        
        # Verify summary structure
        assert isinstance(summary, dict)
        assert 'title' in summary
        assert 'period' in summary
        assert 'key_metrics' in summary
        assert 'highlights' in summary
        assert 'concerns' in summary
        assert 'recommendations' in summary
        
        # Verify key metrics
        key_metrics = summary['key_metrics']
        assert 'total_revenue' in key_metrics
        assert 'total_expenses' in key_metrics
        assert 'net_cash_flow' in key_metrics
        assert 'runway_months' in key_metrics
        assert 'burn_rate' in key_metrics
        
        # Verify highlights and concerns are lists
        assert isinstance(summary['highlights'], list)
        assert isinstance(summary['concerns'], list)
        assert isinstance(summary['recommendations'], list)
        
        self.tearDown()
    
    def test_generate_entity_breakdown_report(self):
        """Test entity breakdown report generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate entity breakdown report
        breakdown = self.report_generator.generate_entity_breakdown_report()
        
        # Verify breakdown structure
        assert isinstance(breakdown, dict)
        assert 'entities_by_type' in breakdown
        assert 'entities_by_tag' in breakdown
        assert 'cost_breakdown' in breakdown
        assert 'revenue_breakdown' in breakdown
        
        # Verify entities by type
        entities_by_type = breakdown['entities_by_type']
        assert 'employee' in entities_by_type
        assert 'grant' in entities_by_type
        assert 'investment' in entities_by_type
        assert 'facility' in entities_by_type
        
        # Verify each type has count and details
        for entity_type, details in entities_by_type.items():
            assert 'count' in details
            assert 'entities' in details
            assert isinstance(details['count'], int)
            assert isinstance(details['entities'], list)
        
        self.tearDown()
    
    def test_generate_trend_analysis_report(self):
        """Test trend analysis report generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate trend analysis
        trends = self.report_generator.generate_trend_analysis_report(forecast_df)
        
        # Verify trends structure
        assert isinstance(trends, dict)
        assert 'revenue_trend' in trends
        assert 'expense_trend' in trends
        assert 'cash_flow_trend' in trends
        assert 'growth_rates' in trends
        
        # Verify each trend has analysis
        for trend_name, trend_data in trends.items():
            if trend_name != 'growth_rates':
                assert 'trend_direction' in trend_data
                assert 'trend_strength' in trend_data
                assert 'monthly_change' in trend_data
        
        # Verify growth rates
        growth_rates = trends['growth_rates']
        assert 'revenue_growth' in growth_rates
        assert 'expense_growth' in growth_rates
        
        self.tearDown()
    
    def test_generate_risk_assessment_report(self):
        """Test risk assessment report generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Generate risk assessment
        risks = self.report_generator.generate_risk_assessment_report(forecast_df, kpis)
        
        # Verify risk assessment structure
        assert isinstance(risks, dict)
        assert 'cash_flow_risks' in risks
        assert 'revenue_risks' in risks
        assert 'expense_risks' in risks
        assert 'operational_risks' in risks
        assert 'risk_score' in risks
        
        # Verify risk score is numeric
        assert isinstance(risks['risk_score'], (int, float))
        assert 0 <= risks['risk_score'] <= 100
        
        # Verify each risk category has assessment
        for risk_category in ['cash_flow_risks', 'revenue_risks', 'expense_risks', 'operational_risks']:
            risk_data = risks[risk_category]
            assert 'level' in risk_data
            assert 'factors' in risk_data
            assert 'mitigation' in risk_data
            assert isinstance(risk_data['factors'], list)
            assert isinstance(risk_data['mitigation'], list)
        
        self.tearDown()
    
    def test_generate_scenario_comparison_report(self):
        """Test scenario comparison report generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Create multiple scenarios (mock data)
        scenarios = {
            'baseline': {
                'forecast': forecast_df,
                'kpis': kpis,
                'description': 'Baseline scenario'
            },
            'optimistic': {
                'forecast': self._scale_numeric_columns(forecast_df, 1.2),  # 20% increase
                'kpis': {k: v * 1.1 for k, v in kpis.items() if isinstance(v, (int, float))},
                'description': 'Optimistic scenario'
            },
            'conservative': {
                'forecast': self._scale_numeric_columns(forecast_df, 0.8),  # 20% decrease
                'kpis': {k: v * 0.9 for k, v in kpis.items() if isinstance(v, (int, float))},
                'description': 'Conservative scenario'
            }
        }
        
        # Generate scenario comparison report
        comparison = self.report_generator.generate_scenario_comparison_report(scenarios)
        
        # Verify comparison structure
        assert isinstance(comparison, dict)
        assert 'scenarios' in comparison
        assert 'comparison_metrics' in comparison
        assert 'best_case' in comparison
        assert 'worst_case' in comparison
        assert 'recommendations' in comparison
        
        # Verify all scenarios are included
        for scenario_name in scenarios.keys():
            assert scenario_name in comparison['scenarios']
        
        # Verify comparison metrics
        comparison_metrics = comparison['comparison_metrics']
        assert 'total_revenue' in comparison_metrics
        assert 'total_expenses' in comparison_metrics
        assert 'final_cash_position' in comparison_metrics
        
        self.tearDown()
    
    def test_generate_custom_report_template(self):
        """Test custom report template generation"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Define custom template
        template_config = {
            'title': 'Custom Report Template',
            'sections': [
                {
                    'type': 'summary',
                    'title': 'Executive Summary',
                    'include_kpis': True
                },
                {
                    'type': 'chart',
                    'title': 'Cash Flow Analysis',
                    'chart_type': 'line',
                    'data_source': 'forecast'
                },
                {
                    'type': 'table',
                    'title': 'Monthly Breakdown',
                    'data_source': 'forecast',
                    'columns': ['period', 'revenue', 'expenses', 'net_cashflow']
                },
                {
                    'type': 'text',
                    'title': 'Analysis Notes',
                    'content': 'This is a custom analysis section.'
                }
            ]
        }
        
        # Generate custom report
        report_path = self.report_generator.generate_custom_report(
            forecast_df,
            kpis,
            template_config,
            filename='custom_report.html'
        )
        
        # Verify custom report was created
        assert report_path.exists()
        assert report_path.suffix == '.html'
        
        # Verify custom content
        with open(report_path, 'r') as f:
            html_content = f.read()
        
        assert 'Custom Report Template' in html_content
        assert 'Executive Summary' in html_content
        assert 'Cash Flow Analysis' in html_content
        assert 'Monthly Breakdown' in html_content
        assert 'Analysis Notes' in html_content
        
        self.tearDown()
    
    def test_report_error_handling(self):
        """Test error handling in report generation"""
        self.setUp()
        
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        
        # Should handle empty data gracefully
        chart_path = self.report_generator.generate_cash_flow_chart(
            empty_df,
            title='Empty Data Test',
            filename='empty_test.png'
        )
        
        # Should either create a placeholder chart or raise informative error
        assert chart_path is not None
        
        # Test with invalid KPI data
        invalid_kpis = {'invalid_kpi': 'not_a_number'}
        
        # Should handle invalid KPIs gracefully
        try:
            dashboard_path = self.report_generator.generate_kpi_dashboard(
                invalid_kpis,
                title='Invalid KPI Test',
                filename='invalid_kpi_test.png'
            )
            assert dashboard_path is not None
        except Exception as e:
            # Should raise informative error
            assert 'invalid' in str(e).lower() or 'error' in str(e).lower()
        
        # Test with non-existent output directory
        invalid_generator = ReportGenerator(
            str(Path('/non/existent/directory')),
            self.store, self.engine, self.kpi_calculator
        )
        
        # Should handle invalid output directory
        try:
            invalid_generator.generate_cash_flow_chart(
                pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]}),
                title='Invalid Directory Test',
                filename='test.png'
            )
        except Exception as e:
            assert 'directory' in str(e).lower() or 'path' in str(e).lower()
        
        self.tearDown()
    
    def test_report_customization_options(self):
        """Test report customization options"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Test chart customization
        chart_path = self.report_generator.generate_cash_flow_chart(
            forecast_df,
            title='Custom Chart',
            filename='custom_chart.png',
            style='dark_background',
            color_scheme='plasma',
            figure_size=(12, 8),
            dpi=300
        )
        
        # Verify chart was created with custom settings
        chart_path_obj = Path(chart_path)
        assert chart_path_obj.exists()
        assert chart_path_obj.stat().st_size > 0
        
        # Test HTML report customization
        html_path = self.report_generator.generate_html_report(
            forecast_df,
            kpis,
            title='Custom HTML Report',
            filename='custom_report.html',
            theme='dark',
            include_charts=True,
            include_data_table=True,
            custom_css='body { background-color: #f0f0f0; }'
        )
        
        # Verify HTML was created with custom settings
        html_path_obj = Path(html_path)
        assert html_path_obj.exists()
        
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        assert 'Custom HTML Report' in html_content
        assert 'background-color: #f0f0f0' in html_content
        
        self.tearDown()
    
    def test_report_automation_and_scheduling(self):
        """Test report automation and scheduling capabilities"""
        self.setUp()
        
        # Create test data
        forecast_df, kpis = self.create_test_data()
        
        # Test automated report generation
        automation_config = {
            'frequency': 'monthly',
            'reports': ['cash_flow_chart', 'kpi_dashboard', 'html_report'],
            'output_format': 'timestamped',
            'archive_old_reports': True
        }
        
        # Generate automated report
        report_info = self.report_generator.generate_automated_report(
            forecast_df,
            kpis,
            automation_config,
            run_timestamp=datetime.now()
        )
        
        # Verify automation results
        assert isinstance(report_info, dict)
        assert 'timestamp' in report_info
        assert 'generated_reports' in report_info
        assert 'output_directory' in report_info
        
        # Verify reports were generated
        generated_reports = report_info['generated_reports']
        assert len(generated_reports) > 0
        
        for report_path in generated_reports:
            assert Path(report_path).exists()
        
        self.tearDown()
    
    def test_report_performance_optimization(self):
        """Test report generation performance optimization"""
        self.setUp()
        
        # Create larger test dataset
        large_entities = []
        for i in range(50):
            employee = Employee(
                type='employee',
                name=f'Employee {i}',
                start_date=date(2024, 1, 1),
                salary=60000 + i * 1000,
                pay_frequency='monthly',
                overhead_multiplier=1.2 + i * 0.01,
                tags=['test', f'batch_{i // 10}']
            )
            large_entities.append(employee)
        
        for entity in large_entities:
            self.store.add_entity(entity)
        
        # Generate forecast for larger dataset
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        large_forecast_df = self.engine.calculate_period(start_date, end_date)
        large_kpis = self.kpi_calculator.calculate_all_kpis(large_forecast_df, start_date, end_date)
        
        # Test performance of report generation
        import time
        
        start_time = time.time()
        
        # Generate multiple reports
        chart_path = self.report_generator.generate_cash_flow_chart(
            large_forecast_df,
            title='Performance Test Chart',
            filename='performance_chart.png'
        )
        
        html_path = self.report_generator.generate_html_report(
            large_forecast_df,
            large_kpis,
            title='Performance Test Report',
            filename='performance_report.html'
        )
        
        csv_path = self.report_generator.export_to_csv(
            large_forecast_df,
            filename='performance_data.csv'
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Verify reports were generated
        assert chart_path.exists()
        assert html_path.exists()
        assert csv_path.exists()
        
        # Should complete in reasonable time (< 30 seconds for 50 entities)
        assert generation_time < 30
        
        self.tearDown()
    
    def test_report_data_validation(self):
        """Test report data validation"""
        self.setUp()
        
        # Create test data with potential issues
        forecast_df, kpis = self.create_test_data()
        
        # Add some problematic data
        problematic_df = forecast_df.copy()
        problematic_df.loc[5, 'revenue'] = -1000  # Negative revenue
        problematic_df.loc[8, 'expenses'] = float('inf')  # Infinite expense
        
        # Test validation
        validation_results = self.report_generator.validate_report_data(
            problematic_df, kpis
        )
        
        # Verify validation results
        assert isinstance(validation_results, dict)
        assert 'is_valid' in validation_results
        assert 'warnings' in validation_results
        assert 'errors' in validation_results
        
        # Should detect problems
        assert validation_results['is_valid'] is False
        assert len(validation_results['warnings']) > 0 or len(validation_results['errors']) > 0
        
        # Test with clean data
        clean_validation = self.report_generator.validate_report_data(
            forecast_df, kpis
        )
        
        assert clean_validation['is_valid'] is True
        
        self.tearDown()