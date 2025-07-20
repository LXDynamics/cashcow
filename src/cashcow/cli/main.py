#!/usr/bin/env python3
"""CashCow CLI - Command Line Interface for Cash Flow Modeling."""

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml

from ..engine import CashFlowEngine, KPICalculator, ScenarioManager
from ..storage import EntityStore, YamlEntityLoader
from .captable_commands import captable


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """CashCow - Rocket Engine Company Cash Flow Modeling

    A flexible cash flow modeling system for rocket engine businesses.
    Manage entities, run forecasts, and analyze scenarios.
    """
    pass


@cli.command()
@click.option('--type', 'entity_type',
              type=click.Choice(['employee', 'grant', 'investment', 'sale', 'service', 'facility', 'software', 'equipment', 'project', 'shareholder', 'share_class', 'funding_round']),
              required=True,
              help='Type of entity to create')
@click.option('--name', required=True, help='Entity name')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with prompts')
@click.option('--file', '-f', type=click.Path(), help='Save to specific file path')
def add(entity_type: str, name: str, interactive: bool, file: Optional[str]):
    """Add a new entity interactively."""

    click.echo(f"Creating new {entity_type}: {name}")

    # Basic entity data
    entity_data = {
        'type': entity_type,
        'name': name,
        'start_date': date.today().isoformat(),
        'tags': []
    }

    if interactive:
        # Interactive prompts based on entity type
        entity_data.update(_get_interactive_fields(entity_type))
    else:
        # Add basic required fields
        entity_data.update(_get_basic_fields(entity_type))

    # Determine file path
    if file:
        file_path = Path(file)
    else:
        file_path = _get_default_entity_path(entity_type, name)

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Save entity
    with open(file_path, 'w') as f:
        yaml.dump(entity_data, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✓ Created {entity_type} '{name}' at {file_path}")


@cli.command()
@click.option('--months', default=24, help='Forecast period in months')
@click.option('--scenario', default='baseline', help='Scenario to use')
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date (YYYY-MM-DD)')
@click.option('--format', 'output_format',
              type=click.Choice(['table', 'csv', 'json']),
              default='table', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--kpis', is_flag=True, help='Include KPI analysis')
@click.option('--include-dilution', is_flag=True, help='Include dilution analysis in forecast')
def forecast(months: int, scenario: str, start_date: Optional[datetime],
             output_format: str, output: Optional[str], kpis: bool, include_dilution: bool):
    """Generate cash flow forecast."""

    click.echo(f"Generating {months}-month forecast using '{scenario}' scenario...")

    # Setup dates
    if start_date:
        start = start_date.date()
    else:
        start = date.today()

    end = start + timedelta(days=months * 30)

    try:
        # Initialize components
        store = EntityStore()
        entities_dir = Path("entities")

        if not entities_dir.exists():
            click.echo("❌ No entities directory found. Create some entities first with 'cashcow add'.")
            return

        # Load entities
        asyncio.run(store.sync_from_yaml(entities_dir))

        # Create engine and scenario manager
        engine = CashFlowEngine(store)
        scenario_mgr = ScenarioManager(store, engine)

        # Load scenarios
        scenarios_dir = Path("scenarios")
        if scenarios_dir.exists():
            scenario_mgr.load_scenarios_from_directory(scenarios_dir)

        # Calculate forecast
        if scenario == 'baseline':
            df = engine.calculate_parallel(start, end)
        else:
            df = scenario_mgr.calculate_scenario(scenario, start, end)

        # Output results
        if output_format == 'table':
            _display_forecast_table(df)
        elif output_format == 'csv':
            if output:
                df.to_csv(output, index=False)
                click.echo(f"✓ Forecast saved to {output}")
            else:
                click.echo(df.to_csv(index=False))
        elif output_format == 'json':
            if output:
                df.to_json(output, orient='records', date_format='iso')
                click.echo(f"✓ Forecast saved to {output}")
            else:
                click.echo(df.to_json(orient='records', date_format='iso'))

        # KPI analysis
        if kpis:
            _display_kpi_analysis(df)

        # Dilution analysis
        if include_dilution:
            click.echo("\n=== Dilution Analysis ===")
            click.echo("Checking for cap table entities...")

            # Check for cap table entities in the forecast
            captable_entities = [e for e in store.get_all_entities() if getattr(e, 'type', '') in ['shareholder', 'funding_round']]
            if captable_entities:
                click.echo(f"Found {len(captable_entities)} cap table entities")
                click.echo("Run 'cashcow captable ownership' for detailed cap table analysis")
            else:
                click.echo("No cap table entities found. Add shareholders and funding rounds to enable dilution analysis.")

    except Exception as e:
        click.echo(f"❌ Error generating forecast: {e}")
        if click.confirm("Show detailed error?"):
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--type', 'entity_type', help='Filter by entity type')
@click.option('--active', is_flag=True, help='Show only active entities')
@click.option('--tag', multiple=True, help='Filter by tags')
def list(entity_type: Optional[str], active: bool, tag: tuple):
    """List existing entities."""

    try:
        store = EntityStore()
        entities_dir = Path("entities")

        if not entities_dir.exists():
            click.echo("❌ No entities directory found.")
            return

        # Load entities
        asyncio.run(store.sync_from_yaml(entities_dir))

        # Build filters
        filters = {}
        if entity_type:
            filters['type'] = entity_type
        if active:
            filters['active'] = True
        if tag:
            filters['tags'] = list(tag)

        # Query entities
        entities = store.query(filters)

        if not entities:
            click.echo("No entities found matching filters.")
            return

        # Display results
        click.echo(f"Found {len(entities)} entities:")
        click.echo()

        for entity in entities:
            status = "Active" if entity.is_active() else "Inactive"
            click.echo(f"• {entity.name} ({entity.type}) - {status}")
            click.echo(f"  Start: {entity.start_date}")
            if entity.end_date:
                click.echo(f"  End: {entity.end_date}")
            if entity.tags:
                click.echo(f"  Tags: {', '.join(entity.tags)}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error listing entities: {e}")


@cli.command()
@click.option('--fix', is_flag=True, help='Attempt to fix validation errors')
def validate(fix: bool):
    """Validate all entity files."""

    click.echo("Validating entity files...")

    try:
        entities_dir = Path("entities")

        if not entities_dir.exists():
            click.echo("❌ No entities directory found.")
            return

        # Load and validate entities
        loader = YamlEntityLoader(entities_dir)
        errors = []

        for entity_file in entities_dir.rglob("*.yaml"):
            try:
                entity = loader.load_entity(entity_file)
                # Basic validation passed
                click.echo(f"✓ {entity_file.name}")
            except Exception as e:
                errors.append((entity_file, str(e)))
                click.echo(f"❌ {entity_file.name}: {e}")

        if errors:
            click.echo(f"\nFound {len(errors)} validation errors.")
            if fix:
                click.echo("Auto-fix not yet implemented.")
        else:
            # Count files validated
            file_count = sum(1 for _ in entities_dir.rglob('*.yaml'))
            click.echo(f"\n✓ All {file_count} files validated successfully.")

    except Exception as e:
        import traceback
        click.echo(f"❌ Error during validation: {e}")
        click.echo(f"Traceback: {traceback.format_exc()}")


@cli.command()
@click.option('--months', default=12, help='Analysis period in months')
@click.option('--scenario', default='baseline', help='Scenario to analyze')
@click.option('--alerts', is_flag=True, help='Show alerts only')
@click.option('--include-ownership', is_flag=True, help='Include ownership metrics in KPI analysis')
def kpi(months: int, scenario: str, alerts: bool, include_ownership: bool):
    """Calculate and display KPI metrics."""

    click.echo(f"Calculating KPIs for {months}-month period...")

    try:
        # Setup
        store = EntityStore()
        entities_dir = Path("entities")

        if not entities_dir.exists():
            click.echo("❌ No entities directory found.")
            return

        # Load entities and calculate forecast
        asyncio.run(store.sync_from_yaml(entities_dir))
        engine = CashFlowEngine(store)

        start = date.today()
        end = start + timedelta(days=months * 30)

        df = engine.calculate_parallel(start, end)

        # Calculate KPIs
        kpi_calc = KPICalculator()
        kpis = kpi_calc.calculate_all_kpis(df)

        if alerts:
            # Show alerts only
            alert_list = kpi_calc.get_kpi_alerts(kpis)
            if alert_list:
                click.echo(f"Found {len(alert_list)} alerts:")
                for alert in alert_list:
                    click.echo(f"  {alert['level'].upper()}: {alert['message']}")
            else:
                click.echo("✓ No alerts - all metrics within acceptable ranges.")
        else:
            # Show all KPIs
            _display_kpi_analysis(df)

        # Ownership metrics
        if include_ownership:
            click.echo("\n=== Ownership Metrics ===")

            # Check for cap table entities
            captable_entities = [e for e in store.get_all_entities() if getattr(e, 'type', '') in ['shareholder', 'share_class', 'funding_round']]
            if captable_entities:
                # Calculate basic ownership metrics
                shareholders = [e for e in captable_entities if getattr(e, 'type', '') == 'shareholder']
                funding_rounds = [e for e in captable_entities if getattr(e, 'type', '') == 'funding_round']

                click.echo(f"• Total Shareholders: {len(shareholders)}")
                click.echo(f"• Total Funding Rounds: {len(funding_rounds)}")

                if shareholders:
                    total_shares = sum(getattr(s, 'total_shares', 0) for s in shareholders)
                    click.echo(f"• Total Shares Outstanding: {total_shares:,}")

                click.echo("• Run 'cashcow captable summary' for detailed cap table analysis")
            else:
                click.echo("No cap table entities found. Add cap table entities to see ownership metrics.")

    except Exception as e:
        click.echo(f"❌ Error calculating KPIs: {e}")


def _get_interactive_fields(entity_type: str) -> Dict[str, Any]:
    """Get interactive field inputs for entity type."""

    fields = {}

    if entity_type == 'employee':
        fields['salary'] = click.prompt('Annual salary', type=float)
        fields['position'] = click.prompt('Position', default='')
        fields['department'] = click.prompt('Department', default='Engineering')
        if click.confirm('Add equity?'):
            fields['equity_shares'] = click.prompt('Equity shares', type=int, default=0)

    elif entity_type == 'grant':
        fields['amount'] = click.prompt('Grant amount', type=float)
        fields['funding_agency'] = click.prompt('Funding agency', default='')
        fields['program'] = click.prompt('Program', default='')

    elif entity_type == 'investment':
        fields['amount'] = click.prompt('Investment amount', type=float)
        fields['investor'] = click.prompt('Investor name', default='')
        fields['round_type'] = click.prompt('Round type', default='Seed')

    elif entity_type == 'sale':
        fields['amount'] = click.prompt('Sale amount', type=float)
        fields['customer'] = click.prompt('Customer name', default='')
        fields['product'] = click.prompt('Product/Service', default='')

    elif entity_type == 'facility':
        fields['monthly_cost'] = click.prompt('Monthly cost', type=float)
        fields['location'] = click.prompt('Location', default='')
        fields['lease_type'] = click.prompt('Lease type', default='Monthly')

    # Add end date if desired
    if click.confirm('Add end date?'):
        end_date = click.prompt('End date (YYYY-MM-DD)', default='')
        if end_date:
            fields['end_date'] = end_date

    return fields


def _get_basic_fields(entity_type: str) -> Dict[str, Any]:
    """Get basic required fields for entity type."""

    fields = {}

    if entity_type == 'employee':
        fields['salary'] = 75000
        fields['position'] = 'Engineer'
        fields['department'] = 'Engineering'

    elif entity_type == 'grant':
        fields['amount'] = 100000
        fields['funding_agency'] = 'NASA'

    elif entity_type == 'investment':
        fields['amount'] = 500000
        fields['investor'] = 'VC Fund'

    elif entity_type == 'sale':
        fields['amount'] = 50000
        fields['customer'] = 'Customer'

    elif entity_type == 'facility':
        fields['monthly_cost'] = 10000
        fields['location'] = 'Main Office'

    return fields


def _get_default_entity_path(entity_type: str, name: str) -> Path:
    """Get default file path for entity."""

    # Clean name for filename
    filename = name.lower().replace(' ', '-').replace('_', '-') + '.yaml'

    # Map entity types to directories
    type_dirs = {
        'employee': 'entities/expenses/employees',
        'grant': 'entities/revenue/grants',
        'investment': 'entities/revenue/investments',
        'sale': 'entities/revenue/sales',
        'service': 'entities/revenue/services',
        'facility': 'entities/expenses/facilities',
        'software': 'entities/expenses/operations',
        'equipment': 'entities/expenses/operations',
        'project': 'entities/projects',
        'shareholder': 'entities/captable/shareholders',
        'share_class': 'entities/captable/share_classes',
        'funding_round': 'entities/captable/funding_rounds'
    }

    directory = type_dirs.get(entity_type, 'entities')
    return Path(directory) / filename


def _display_forecast_table(df):
    """Display forecast results in table format."""

    # Show summary
    click.echo("\n=== Cash Flow Forecast Summary ===")
    click.echo(f"Period: {df['period'].iloc[0]} to {df['period'].iloc[-1]}")
    click.echo(f"Total Revenue: ${df['total_revenue'].sum():,.2f}")
    click.echo(f"Total Expenses: ${df['total_expenses'].sum():,.2f}")
    click.echo(f"Net Cash Flow: ${df['net_cash_flow'].sum():,.2f}")
    click.echo(f"Final Cash Balance: ${df['cash_balance'].iloc[-1]:,.2f}")

    # Show monthly breakdown (first 6 months)
    click.echo("\n=== Monthly Breakdown (First 6 Months) ===")
    for i in range(min(6, len(df))):
        row = df.iloc[i]
        click.echo(f"{row['period']}: Revenue ${row['total_revenue']:,.0f}, "
                  f"Expenses ${row['total_expenses']:,.0f}, "
                  f"Balance ${row['cash_balance']:,.0f}")


def _display_kpi_analysis(df):
    """Display KPI analysis."""

    click.echo("\n=== KPI Analysis ===")

    kpi_calc = KPICalculator()
    kpis = kpi_calc.calculate_all_kpis(df)

    # Key KPIs
    key_kpis = [
        ('Runway (months)', 'runway_months'),
        ('Monthly burn rate', 'burn_rate'),
        ('Revenue growth rate', 'revenue_growth_rate'),
        ('R&D percentage', 'rd_percentage'),
        ('Revenue per employee', 'revenue_per_employee'),
        ('Cash efficiency', 'cash_efficiency')
    ]

    for label, kpi in key_kpis:
        if kpi in kpis:
            value = kpis[kpi]
            if kpi == 'runway_months':
                if value == float('inf'):
                    click.echo(f"• {label}: Infinite (profitable)")
                else:
                    click.echo(f"• {label}: {value:.1f} months")
            elif kpi.endswith('_rate') or kpi.endswith('_percentage'):
                click.echo(f"• {label}: {value:.1f}%")
            elif 'rate' in kpi or 'amount' in kpi:
                click.echo(f"• {label}: ${value:,.2f}")
            else:
                click.echo(f"• {label}: {value:.2f}")

    # Show alerts
    alerts = kpi_calc.get_kpi_alerts(kpis)
    if alerts:
        click.echo(f"\n⚠ {len(alerts)} alerts:")
        for alert in alerts:
            click.echo(f"  {alert['level'].upper()}: {alert['message']}")


# Add cap table command group
cli.add_command(captable)

if __name__ == '__main__':
    cli()
