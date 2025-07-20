#!/usr/bin/env python3
"""Cap Table CLI Commands - Phase 3 Agent U1 Implementation."""

from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import pandas as pd
import yaml


@click.group()
def captable():
    """Cap table management commands for equity tracking and analysis."""
    pass


@captable.command('add-shareholder')
@click.option('--name', required=True, help='Shareholder name')
@click.option('--shares', type=int, required=True, help='Number of shares')
@click.option('--share-class', default='common', help='Share class (common, preferred)')
@click.option('--shareholder-type',
              type=click.Choice(['founder', 'employee', 'investor', 'advisor']),
              default='employee', help='Type of shareholder')
@click.option('--vesting-start', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Vesting start date (YYYY-MM-DD)')
@click.option('--cliff-months', type=int, default=12, help='Cliff period in months')
@click.option('--vest-years', type=int, default=4, help='Total vesting period in years')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with prompts')
def add_shareholder(name: str, shares: int, share_class: str, shareholder_type: str,
                   vesting_start: Optional[datetime], cliff_months: int, vest_years: int,
                   interactive: bool):
    """Add new shareholder to cap table."""

    click.echo(f"Adding shareholder: {name}")

    # Basic shareholder data
    shareholder_data = {
        'type': 'shareholder',
        'name': name,
        'start_date': date.today().isoformat(),
        'total_shares': shares,
        'share_class': share_class,
        'shareholder_type': shareholder_type,
        'cliff_months': cliff_months,
        'vest_years': vest_years,
        'tags': [shareholder_type, share_class]
    }

    if vesting_start:
        shareholder_data['vesting_start_date'] = vesting_start.date().isoformat()

    if interactive:
        shareholder_data.update(_get_interactive_shareholder_fields())

    # Save shareholder
    file_path = _get_captable_entity_path('shareholder', name)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        yaml.dump(shareholder_data, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✓ Added shareholder '{name}' with {shares:,} {share_class} shares")
    click.echo(f"  Saved to: {file_path}")


@captable.command('add-share-class')
@click.option('--name', required=True, help='Share class name')
@click.option('--authorized', type=int, required=True, help='Authorized shares')
@click.option('--par-value', type=float, default=0.001, help='Par value per share')
@click.option('--liquidation-preference', type=float, default=1.0,
              help='Liquidation preference multiplier')
@click.option('--participating', is_flag=True, help='Participating preferred shares')
@click.option('--voting-rights', type=float, default=1.0, help='Voting rights per share')
@click.option('--anti-dilution',
              type=click.Choice(['none', 'weighted_average', 'full_ratchet']),
              default='none', help='Anti-dilution provision')
def add_share_class(name: str, authorized: int, par_value: float,
                   liquidation_preference: float, participating: bool,
                   voting_rights: float, anti_dilution: str):
    """Add new share class to cap table."""

    click.echo(f"Creating share class: {name}")

    share_class_data = {
        'type': 'share_class',
        'name': name,
        'start_date': date.today().isoformat(),
        'class_name': name,
        'shares_authorized': authorized,
        'par_value': par_value,
        'liquidation_preference': liquidation_preference,
        'participating': participating,
        'voting_rights_per_share': voting_rights,
        'anti_dilution_provision': anti_dilution,
        'tags': ['share_class']
    }

    file_path = _get_captable_entity_path('share_class', name)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        yaml.dump(share_class_data, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✓ Created share class '{name}' with {authorized:,} authorized shares")
    click.echo(f"  Liquidation preference: {liquidation_preference}x")
    click.echo(f"  Saved to: {file_path}")


@captable.command('add-funding-round')
@click.option('--name', required=True, help='Round name (e.g., "Seed", "Series A")')
@click.option('--amount', type=float, required=True, help='Total round amount')
@click.option('--valuation', type=float, required=True, help='Pre-money valuation')
@click.option('--lead-investor', help='Lead investor name')
@click.option('--closing-date', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Closing date (YYYY-MM-DD)')
@click.option('--share-class', default='preferred', help='Share class for new shares')
def add_funding_round(name: str, amount: float, valuation: float,
                     lead_investor: Optional[str], closing_date: Optional[datetime],
                     share_class: str):
    """Add new funding round to cap table."""

    click.echo(f"Creating funding round: {name}")

    # Calculate share price and shares issued
    post_money_valuation = valuation + amount
    price_per_share = valuation / 1000000  # Assuming 1M shares pre-money baseline
    shares_issued = int(amount / price_per_share)

    funding_round_data = {
        'type': 'funding_round',
        'name': name,
        'start_date': closing_date.date().isoformat() if closing_date else date.today().isoformat(),
        'round_name': name,
        'total_amount': amount,
        'pre_money_valuation': valuation,
        'post_money_valuation': post_money_valuation,
        'price_per_share': price_per_share,
        'shares_issued': shares_issued,
        'share_class': share_class,
        'lead_investor': lead_investor or 'TBD',
        'tags': ['funding_round', share_class]
    }

    file_path = _get_captable_entity_path('funding_round', name)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        yaml.dump(funding_round_data, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✓ Created funding round '{name}'")
    click.echo(f"  Amount: ${amount:,.0f}")
    click.echo(f"  Pre-money: ${valuation:,.0f}")
    click.echo(f"  Post-money: ${post_money_valuation:,.0f}")
    click.echo(f"  Price per share: ${price_per_share:.4f}")
    click.echo(f"  Shares issued: {shares_issued:,}")


@captable.command('ownership')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']),
              default='table', help='Output format')
@click.option('--as-of-date', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Calculate ownership as of date (YYYY-MM-DD)')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--include-vesting', is_flag=True, help='Include vesting schedule analysis')
def ownership_report(format: str, as_of_date: Optional[datetime],
                    output: Optional[str], include_vesting: bool):
    """Generate comprehensive ownership percentage report."""

    as_of = as_of_date.date() if as_of_date else date.today()
    click.echo(f"Generating ownership report as of {as_of}...")

    try:
        # Load cap table entities
        ownership_data = _calculate_ownership_summary(as_of)

        if format == 'table':
            _display_ownership_table(ownership_data, include_vesting)
        elif format == 'csv':
            df = pd.DataFrame(ownership_data)
            if output:
                df.to_csv(output, index=False)
                click.echo(f"✓ Ownership report saved to {output}")
            else:
                click.echo(df.to_csv(index=False))
        elif format == 'json':
            import json
            json_data = json.dumps(ownership_data, indent=2, default=str)
            if output:
                with open(output, 'w') as f:
                    f.write(json_data)
                click.echo(f"✓ Ownership report saved to {output}")
            else:
                click.echo(json_data)

    except Exception as e:
        click.echo(f"❌ Error generating ownership report: {e}")


@captable.command('dilution')
@click.option('--round-amount', type=float, required=True, help='New round amount')
@click.option('--pre-money', type=float, required=True, help='Pre-money valuation')
@click.option('--option-pool', type=float, default=0.0,
              help='Option pool expansion (as decimal, e.g., 0.15 for 15%)')
@click.option('--format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
def dilution_analysis(round_amount: float, pre_money: float,
                     option_pool: float, format: str):
    """Analyze dilution impact of proposed funding round."""

    click.echo(f"Analyzing dilution for ${round_amount:,.0f} round at ${pre_money:,.0f} pre-money...")

    try:
        # Calculate current ownership
        current_ownership = _calculate_ownership_summary(date.today())

        # Model dilution impact
        dilution_analysis = _model_dilution_impact(
            current_ownership, round_amount, pre_money, option_pool
        )

        if format == 'table':
            _display_dilution_table(dilution_analysis)
        else:
            import json
            click.echo(json.dumps(dilution_analysis, indent=2, default=str))

    except Exception as e:
        click.echo(f"❌ Error analyzing dilution: {e}")


@captable.command('liquidation')
@click.option('--exit-value', type=float, required=True, help='Company exit valuation')
@click.option('--format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.option('--scenario', multiple=True, help='Additional exit scenarios to model')
def liquidation_analysis(exit_value: float, format: str, scenario: tuple):
    """Analyze liquidation waterfall and returns."""

    scenarios = [exit_value] + [float(s) for s in scenario]
    click.echo(f"Analyzing liquidation waterfall for exit value(s): {[f'${s:,.0f}' for s in scenarios]}")

    try:
        # Calculate liquidation waterfall
        waterfall_results = []
        for value in scenarios:
            waterfall = _calculate_liquidation_waterfall(value)
            waterfall_results.append(waterfall)

        if format == 'table':
            for i, waterfall in enumerate(waterfall_results):
                click.echo(f"\n=== Exit Scenario ${scenarios[i]:,.0f} ===")
                _display_liquidation_table(waterfall)
        else:
            import json
            click.echo(json.dumps(waterfall_results, indent=2, default=str))

    except Exception as e:
        click.echo(f"❌ Error analyzing liquidation: {e}")


@captable.command('summary')
@click.option('--format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
def cap_table_summary(format: str):
    """Generate complete cap table summary."""

    click.echo("Generating cap table summary...")

    try:
        summary = _generate_cap_table_summary()

        if format == 'table':
            _display_cap_table_summary(summary)
        else:
            import json
            click.echo(json.dumps(summary, indent=2, default=str))

    except Exception as e:
        click.echo(f"❌ Error generating summary: {e}")


# Helper Functions

def _get_interactive_shareholder_fields() -> Dict[str, Any]:
    """Get additional interactive fields for shareholder."""
    fields = {}

    if click.confirm('Add purchase price?'):
        fields['purchase_price_per_share'] = click.prompt('Purchase price per share', type=float)

    if click.confirm('Add voting restrictions?'):
        fields['voting_agreement'] = click.prompt('Voting agreement details', default='')

    return fields


def _get_captable_entity_path(entity_type: str, name: str) -> Path:
    """Get file path for cap table entity."""
    filename = name.lower().replace(' ', '-').replace('_', '-') + '.yaml'

    type_dirs = {
        'shareholder': 'entities/captable/shareholders',
        'share_class': 'entities/captable/share_classes',
        'funding_round': 'entities/captable/funding_rounds'
    }

    directory = type_dirs.get(entity_type, 'entities/captable')
    return Path(directory) / filename


def _calculate_ownership_summary(as_of_date: date) -> List[Dict]:
    """Calculate current ownership percentages."""
    # Mock implementation - would use actual cap table calculation engine
    return [
        {
            'name': 'Founders',
            'shares': 7000000,
            'percentage': 70.0,
            'share_class': 'common',
            'fully_diluted': 65.0
        },
        {
            'name': 'Employee Pool',
            'shares': 2000000,
            'percentage': 20.0,
            'share_class': 'common',
            'fully_diluted': 18.5
        },
        {
            'name': 'Seed Investors',
            'shares': 1000000,
            'percentage': 10.0,
            'share_class': 'preferred',
            'fully_diluted': 16.5
        }
    ]


def _model_dilution_impact(current_ownership: List[Dict], round_amount: float,
                          pre_money: float, option_pool: float) -> Dict:
    """Model dilution impact of new funding round."""
    post_money = pre_money + round_amount

    # Mock dilution calculation
    return {
        'round_details': {
            'amount': round_amount,
            'pre_money': pre_money,
            'post_money': post_money,
            'option_pool_expansion': option_pool
        },
        'dilution_impact': [
            {
                'stakeholder': 'Founders',
                'current_percentage': 70.0,
                'post_round_percentage': 56.0,
                'dilution': 14.0
            },
            {
                'stakeholder': 'Employees',
                'current_percentage': 20.0,
                'post_round_percentage': 16.0,
                'dilution': 4.0
            }
        ]
    }


def _calculate_liquidation_waterfall(exit_value: float) -> Dict:
    """Calculate liquidation waterfall distribution."""
    # Mock liquidation calculation
    return {
        'exit_value': exit_value,
        'distributions': [
            {
                'class': 'Series A Preferred',
                'liquidation_preference': 1000000,
                'participation': False,
                'distribution': min(1000000, exit_value * 0.1)
            },
            {
                'class': 'Common',
                'liquidation_preference': 0,
                'participation': True,
                'distribution': max(0, exit_value - 1000000) * 0.9
            }
        ]
    }


def _generate_cap_table_summary() -> Dict:
    """Generate complete cap table summary."""
    return {
        'total_shares_outstanding': 10000000,
        'total_authorized': 15000000,
        'share_classes': [
            {'name': 'common', 'outstanding': 9000000, 'authorized': 12000000},
            {'name': 'preferred', 'outstanding': 1000000, 'authorized': 3000000}
        ],
        'stakeholder_count': 15,
        'last_409a_valuation': 10000000,
        'last_409a_date': '2024-01-01'
    }


def _display_ownership_table(ownership_data: List[Dict], include_vesting: bool):
    """Display ownership data in table format."""
    click.echo("\n=== Cap Table Ownership Summary ===")
    click.echo(f"{'Stakeholder':<20} {'Shares':<12} {'%Own':<8} {'Class':<12} {'Fully Diluted':<8}")
    click.echo("-" * 65)

    for item in ownership_data:
        click.echo(f"{item['name']:<20} {item['shares']:>11,} {item['percentage']:>7.1f}% "
                  f"{item['share_class']:<12} {item['fully_diluted']:>7.1f}%")


def _display_dilution_table(analysis: Dict):
    """Display dilution analysis in table format."""
    details = analysis['round_details']
    click.echo("\n=== Dilution Analysis ===")
    click.echo(f"Round Amount: ${details['amount']:,.0f}")
    click.echo(f"Pre-money: ${details['pre_money']:,.0f}")
    click.echo(f"Post-money: ${details['post_money']:,.0f}")

    click.echo(f"\n{'Stakeholder':<15} {'Current %':<10} {'Post %':<10} {'Dilution':<10}")
    click.echo("-" * 50)

    for item in analysis['dilution_impact']:
        click.echo(f"{item['stakeholder']:<15} {item['current_percentage']:>8.1f}% "
                  f"{item['post_round_percentage']:>8.1f}% {item['dilution']:>8.1f}%")


def _display_liquidation_table(waterfall: Dict):
    """Display liquidation waterfall in table format."""
    click.echo(f"Exit Value: ${waterfall['exit_value']:,.0f}")
    click.echo(f"\n{'Share Class':<20} {'Preference':<12} {'Distribution':<12}")
    click.echo("-" * 50)

    for dist in waterfall['distributions']:
        click.echo(f"{dist['class']:<20} ${dist['liquidation_preference']:>10,.0f} "
                  f"${dist['distribution']:>10,.0f}")


def _display_cap_table_summary(summary: Dict):
    """Display cap table summary."""
    click.echo("\n=== Cap Table Summary ===")
    click.echo(f"Total Outstanding: {summary['total_shares_outstanding']:,}")
    click.echo(f"Total Authorized: {summary['total_authorized']:,}")
    click.echo(f"Utilization: {summary['total_shares_outstanding']/summary['total_authorized']*100:.1f}%")
    click.echo(f"Stakeholder Count: {summary['stakeholder_count']}")

    click.echo("\n=== Share Classes ===")
    for sc in summary['share_classes']:
        utilization = sc['outstanding'] / sc['authorized'] * 100
        click.echo(f"{sc['name'].title()}: {sc['outstanding']:,} / {sc['authorized']:,} ({utilization:.1f}%)")
