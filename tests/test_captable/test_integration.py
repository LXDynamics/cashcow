"""Integration tests for cap table functionality with existing CashCow system."""

from datetime import date
from pathlib import Path

from cashcow.config import get_config
from cashcow.models import create_entity
from cashcow.models.captable import CAPTABLE_ENTITY_TYPES, create_captable_entity


class TestCapTableIntegration:
    """Test integration of cap table with existing CashCow system."""

    def test_cap_table_entities_in_entity_mapping(self):
        """Test that cap table entities are properly mapped."""
        assert 'shareholder' in CAPTABLE_ENTITY_TYPES
        assert 'share_class' in CAPTABLE_ENTITY_TYPES
        assert 'funding_round' in CAPTABLE_ENTITY_TYPES

    def test_config_loading_with_cap_table_types(self):
        """Test that configuration loads with cap table entity types."""
        config = get_config()

        # Check that raw config contains cap table types
        cashcow_config = config._raw_config.get('cashcow', {})
        entity_types = cashcow_config.get('entity_types', {})

        assert 'shareholder' in entity_types
        assert 'share_class' in entity_types
        assert 'funding_round' in entity_types

        # Check that required fields are configured
        assert 'shareholder_type' in entity_types['shareholder']['required_fields']
        assert 'total_shares' in entity_types['shareholder']['required_fields']
        assert 'class_name' in entity_types['share_class']['required_fields']
        assert 'round_type' in entity_types['funding_round']['required_fields']

    def test_enhanced_investment_backward_compatibility(self):
        """Test that enhanced Investment entity maintains backward compatibility."""
        # Test creating investment the old way
        investment_data = {
            'type': 'investment',
            'name': 'Legacy Investment',
            'amount': 1000000,
            'investor': 'Old School VC',
            'start_date': date.today()
        }

        investment = create_entity(investment_data)
        assert investment.type == 'investment'
        assert investment.amount == 1000000
        assert investment.investor == 'Old School VC'

        # Test that new fields default properly
        assert investment.shares_issued is None
        assert investment.liquidation_preference == 1.0
        assert investment.participating is False

    def test_investment_to_funding_round_conversion(self):
        """Test conversion between Investment and FundingRound entities."""
        # Create investment with cap table data
        investment_data = {
            'type': 'investment',
            'name': 'Convertible Investment',
            'amount': 2000000,
            'investor': 'Convertible VC',
            'round_name': 'Series A',
            'shares_issued': 400000,
            'price_per_share': 5.0,
            'pre_money_valuation': 8000000,
            'start_date': date.today()
        }

        investment = create_entity(investment_data)
        funding_round = investment.to_funding_round()

        assert funding_round is not None
        assert funding_round.round_type == 'series_a'
        assert funding_round.amount_raised == 2000000
        assert funding_round.shares_issued == 400000
        assert funding_round.lead_investor == 'Convertible VC'

    def test_cap_table_entity_creation_workflows(self):
        """Test complete cap table entity creation workflows."""
        # Test shareholder creation
        shareholder_data = {
            'type': 'shareholder',
            'name': 'Test Founder',
            'shareholder_type': 'founder',
            'total_shares': 3000000,
            'share_class': 'common',
            'start_date': date.today()
        }

        shareholder = create_captable_entity(shareholder_data)
        assert shareholder.name == 'Test Founder'
        assert shareholder.is_founder is True

        # Test share class creation
        share_class_data = {
            'type': 'share_class',
            'name': 'Test Common',
            'class_name': 'Common',
            'shares_authorized': 10000000,
            'start_date': date.today()
        }

        share_class = create_captable_entity(share_class_data)
        assert share_class.class_name == 'Common'
        assert share_class.utilization_percentage == 0.0

        # Test funding round creation
        funding_round_data = {
            'type': 'funding_round',
            'name': 'Test Round',
            'round_type': 'seed',
            'amount_raised': 1500000,
            'pre_money_valuation': 6000000,
            'start_date': date.today()
        }

        funding_round = create_captable_entity(funding_round_data)
        assert funding_round.round_type == 'seed'
        assert funding_round.computed_post_money_valuation == 7500000

    def test_cap_table_calculations_integration(self):
        """Test that cap table calculations work with the entity system."""
        # Create a simple cap table scenario
        shareholders = [
            create_captable_entity({
                'type': 'shareholder',
                'name': 'Founder A',
                'shareholder_type': 'founder',
                'total_shares': 4000000,
                'share_class': 'common',
                'start_date': date.today()
            }),
            create_captable_entity({
                'type': 'shareholder',
                'name': 'Founder B',
                'shareholder_type': 'founder',
                'total_shares': 3000000,
                'share_class': 'common',
                'start_date': date.today()
            }),
            create_captable_entity({
                'type': 'shareholder',
                'name': 'Investor',
                'shareholder_type': 'investor',
                'total_shares': 1000000,
                'share_class': 'preferred',
                'start_date': date.today()
            })
        ]

        total_shares = sum(s.total_shares for s in shareholders)

        # Test ownership calculations
        for shareholder in shareholders:
            ownership = shareholder.calculate_ownership_percentage(total_shares)
            assert 0 < ownership <= 100

        # Test voting power calculations
        share_classes = {
            'common': {'voting_rights_per_share': 1.0},
            'preferred': {'voting_rights_per_share': 1.0}
        }

        for shareholder in shareholders:
            voting_power = shareholder.get_voting_power(share_classes)
            assert voting_power > 0

    def test_sample_entity_files_load_correctly(self):
        """Test that sample entity files can be loaded and validated."""
        base_path = Path(__file__).parent.parent.parent / "entities" / "captable"

        # Test that directories exist
        assert (base_path / "shareholders").exists()
        assert (base_path / "share_classes").exists()
        assert (base_path / "funding_rounds").exists()

        # Test that we can load sample files
        sample_files = [
            base_path / "shareholders" / "alice-johnson-founder.yaml",
            base_path / "share_classes" / "common-stock.yaml",
            base_path / "funding_rounds" / "seed-round.yaml"
        ]

        for file_path in sample_files:
            if file_path.exists():
                import yaml
                with open(file_path) as f:
                    data = yaml.safe_load(f)

                entity = create_captable_entity(data)
                assert entity.name is not None
                assert entity.type in ['shareholder', 'share_class', 'funding_round']

    def test_cap_table_kpis_in_config(self):
        """Test that cap table KPIs are properly configured."""
        config = get_config()

        kpis = config._raw_config.get('cashcow', {}).get('kpis', [])

        # Find cap table related KPIs
        ownership_kpis = [kpi for kpi in kpis if kpi.get('category') == 'ownership']
        governance_kpis = [kpi for kpi in kpis if kpi.get('category') == 'governance']

        assert len(ownership_kpis) > 0
        assert len(governance_kpis) > 0

        # Check for specific KPIs
        kpi_names = [kpi['name'] for kpi in kpis]
        assert 'founder_ownership' in kpi_names
        assert 'employee_ownership' in kpi_names
        assert 'liquidation_overhang' in kpi_names
