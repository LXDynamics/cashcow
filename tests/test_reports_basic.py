import shutil
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.kpis import KPICalculator
from cashcow.reports.generator import ReportGenerator
from cashcow.storage.database import EntityStore


class TestReportGeneratorBasic:
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
        self.report_generator = ReportGenerator(str(self.reports_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        # Close any open matplotlib figures
        plt.close('all')

    def create_test_data(self):
        """Create test data for report generation"""
        # Create mock forecast data directly
        dates = pd.date_range('2024-01-01', '2024-12-31', freq='MS')

        # Create a DataFrame with the expected structure
        forecast_df = pd.DataFrame({
            'period': dates,
            'total_revenue': [50000 + i * 1000 for i in range(len(dates))],
            'total_expenses': [40000 + i * 500 for i in range(len(dates))],
            'net_cash_flow': [10000 + i * 500 for i in range(len(dates))],
            'cash_balance': [100000 + (10000 + i * 500) * (i + 1) for i in range(len(dates))],
            'employee_costs': [25000 + i * 200 for i in range(len(dates))],
            'facility_costs': [8000 for i in range(len(dates))],
            'software_costs': [2000 for i in range(len(dates))],
            'equipment_costs': [3000 + i * 100 for i in range(len(dates))],
            'project_costs': [2000 + i * 200 for i in range(len(dates))],
            'grant_revenue': [20000 if i < 6 else 0 for i in range(len(dates))],
            'investment_revenue': [30000 if i % 3 == 0 else 0 for i in range(len(dates))],
            'sales_revenue': [0 if i < 6 else 10000 + i * 500 for i in range(len(dates))],
            'service_revenue': [0 for i in range(len(dates))],
            'active_employees': [3 + i // 3 for i in range(len(dates))],
            'active_projects': [2 if i < 8 else 3 for i in range(len(dates))],
            'cumulative_cash_flow': [sum([10000 + j * 500 for j in range(i + 1)]) for i in range(len(dates))],
        })

        # Calculate KPIs
        kpis = self.kpi_calculator.calculate_all_kpis(forecast_df)

        return forecast_df, kpis

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
        with open(html_path) as f:
            html_content = f.read()

        assert '<html>' in html_content
        assert 'CashCow Financial Report' in html_content
        assert 'Cash Flow' in html_content
        assert 'KPI' in html_content

        self.tearDown()

    def test_scenario_comparison_chart(self):
        """Test scenario comparison chart generation"""
        self.setUp()

        # Create test data
        forecast_df, kpis = self.create_test_data()

        # Create scenario results dictionary
        scenario_results = {
            'baseline': forecast_df,
            'optimistic': forecast_df.copy()  # Simple copy for test
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
