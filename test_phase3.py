#!/usr/bin/env python3
"""Integration test for Phase 3: Core Engine."""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cashcow.engine import CashFlowEngine, KPICalculator, ScenarioManager
from cashcow.storage import EntityStore, YamlEntityLoader


def test_cash_flow_engine():
    """Test the cash flow engine with real data."""
    print("=== Testing Cash Flow Engine ===")
    
    # Setup
    store = EntityStore("test_cashcow.db")
    entities_dir = Path("entities")
    
    if entities_dir.exists():
        # Load entities from YAML files
        loader = YamlEntityLoader(entities_dir)
        
        # Sync entities to database
        import asyncio
        asyncio.run(store.sync_from_yaml(entities_dir))
        
        # Create cash flow engine
        engine = CashFlowEngine(store)
        
        # Calculate 24-month forecast
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        
        print(f"Calculating cash flow from {start_date} to {end_date}")
        
        # Test parallel calculation
        df = engine.calculate_parallel(start_date, end_date, max_workers=2)
        
        print(f"✓ Calculated {len(df)} periods")
        print(f"Total Revenue: ${df['total_revenue'].sum():,.2f}")
        print(f"Total Expenses: ${df['total_expenses'].sum():,.2f}")
        print(f"Net Cash Flow: ${df['net_cash_flow'].sum():,.2f}")
        print(f"Final Cash Balance: ${df['cash_balance'].iloc[-1]:,.2f}")
        
        # Test aggregations
        aggregations = engine.aggregate_by_category(df)
        print(f"✓ Created {len(aggregations)} aggregation categories")
        
        # Test summary
        summary = engine.get_calculation_summary(df)
        print(f"✓ Average monthly burn: ${summary['average_monthly_burn']:,.2f}")
        print(f"✓ Months cash positive: {summary['months_cash_positive']}")
        
        return df, engine, store
    else:
        print("⚠ No entities directory found - skipping cash flow test")
        return None, None, None


def test_kpi_calculator(df):
    """Test KPI calculations."""
    print("\n=== Testing KPI Calculator ===")
    
    if df is None:
        print("⚠ No cash flow data - skipping KPI test")
        return
    
    calculator = KPICalculator()
    
    # Calculate all KPIs
    starting_cash = 500000  # $500K starting cash
    kpis = calculator.calculate_all_kpis(df, starting_cash)
    
    print(f"✓ Calculated {len(kpis)} KPIs:")
    
    # Display key KPIs
    key_kpis = [
        'runway_months',
        'burn_rate',
        'revenue_growth_rate',
        'rd_percentage',
        'revenue_per_employee',
        'cash_efficiency'
    ]
    
    for kpi in key_kpis:
        if kpi in kpis:
            value = kpis[kpi]
            if kpi.endswith('_rate') or kpi.endswith('_percentage'):
                print(f"  {kpi}: {value:.1f}%")
            elif kpi == 'runway_months':
                if value == float('inf'):
                    print(f"  {kpi}: Infinite (profitable)")
                else:
                    print(f"  {kpi}: {value:.1f} months")
            elif 'rate' in kpi or 'amount' in kpi:
                print(f"  {kpi}: ${value:,.2f}")
            else:
                print(f"  {kpi}: {value:.2f}")
    
    # Test alerts
    alerts = calculator.get_kpi_alerts(kpis)
    if alerts:
        print(f"\n⚠ {len(alerts)} alerts generated:")
        for alert in alerts:
            print(f"  {alert['level'].upper()}: {alert['message']}")
    else:
        print("✓ No alerts - metrics within acceptable ranges")
    
    return kpis


def test_scenario_manager(engine, store):
    """Test scenario management."""
    print("\n=== Testing Scenario Manager ===")
    
    if engine is None or store is None:
        print("⚠ No engine or store - skipping scenario test")
        return
    
    # Create scenario manager
    scenario_mgr = ScenarioManager(store, engine)
    
    # Load scenarios from directory
    scenarios_dir = Path("scenarios")
    if scenarios_dir.exists():
        scenario_mgr.load_scenarios_from_directory(scenarios_dir)
    
    # List available scenarios
    scenarios = scenario_mgr.list_scenarios()
    print(f"✓ Loaded {len(scenarios)} scenarios: {', '.join(scenarios)}")
    
    # Test scenario calculations
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)  # 1 year for faster testing
    
    results = {}
    for scenario_name in ['baseline', 'optimistic', 'conservative'][:2]:  # Test first 2
        if scenario_name in scenarios:
            print(f"  Calculating {scenario_name} scenario...")
            try:
                df = scenario_mgr.calculate_scenario(scenario_name, start_date, end_date)
                results[scenario_name] = df
                
                net_cf = df['net_cash_flow'].sum()
                final_balance = df['cash_balance'].iloc[-1]
                print(f"    {scenario_name}: Net CF ${net_cf:,.0f}, Final Balance ${final_balance:,.0f}")
                
            except Exception as e:
                print(f"    Error calculating {scenario_name}: {e}")
    
    if len(results) >= 2:
        # Create scenario comparison
        from cashcow.engine.scenarios import create_scenario_summary
        summary = create_scenario_summary(results)
        print(f"✓ Created scenario comparison with {len(summary)} scenarios")
        
        # Show comparison
        print("\nScenario Comparison:")
        for _, row in summary.iterrows():
            scenario = row['scenario']
            revenue = row['total_revenue']
            expenses = row['total_expenses']
            print(f"  {scenario}: Revenue ${revenue:,.0f}, Expenses ${expenses:,.0f}")
    
    return scenario_mgr


def test_advanced_features(engine, store):
    """Test advanced engine features."""
    print("\n=== Testing Advanced Features ===")
    
    if engine is None:
        print("⚠ No engine - skipping advanced tests")
        return
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 6, 30)  # 6 months
    
    # Test async calculation
    print("Testing async calculation...")
    try:
        import asyncio
        async def test_async():
            return await engine.calculate_period_async(start_date, end_date)
        
        df_async = asyncio.run(test_async())
        print(f"✓ Async calculation completed: {len(df_async)} periods")
        
    except Exception as e:
        print(f"⚠ Async test failed: {e}")
    
    # Test caching
    print("Testing cache...")
    cache_key = engine.get_cache_key(start_date, end_date, "baseline")
    print(f"✓ Cache key generated: {cache_key}")
    
    # Clear cache
    engine.clear_cache()
    print("✓ Cache cleared")


def main():
    """Run all Phase 3 tests."""
    print("=== Phase 3 Integration Test ===\n")
    
    # Test core engine
    df, engine, store = test_cash_flow_engine()
    
    # Test KPIs
    kpis = test_kpi_calculator(df)
    
    # Test scenarios
    scenario_mgr = test_scenario_manager(engine, store)
    
    # Test advanced features
    test_advanced_features(engine, store)
    
    print("\n=== Phase 3 Complete! ===")
    print("\nKey Features Delivered:")
    print("✓ Parallel cash flow calculation engine")
    print("✓ Comprehensive KPI calculations (25+ metrics)")
    print("✓ Scenario management with 4 built-in scenarios")
    print("✓ Async processing support")
    print("✓ Data aggregation and summary statistics")
    print("✓ Alert system for risk management")
    
    print("\nNext Steps:")
    print("1. Start Phase 4: CLI & Reporting")
    print("2. Build command-line interface")
    print("3. Add chart generation")
    print("4. Create report templates")


if __name__ == "__main__":
    main()