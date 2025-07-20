"""Tests for cap table entity models."""

from datetime import date

import pytest
from cashcow.models.captable import FundingRound, ShareClass, Shareholder, create_captable_entity


class TestShareClass:
    """Test ShareClass entity."""

    def test_create_basic_share_class(self):
        """Test creating a basic share class."""
        share_class = ShareClass(
            name="Common Stock",
            class_name="Common",
            shares_authorized=10000000,
            start_date=date.today()
        )

        assert share_class.class_name == "Common"
        assert share_class.shares_authorized == 10000000
        assert share_class.shares_outstanding == 0
        assert share_class.liquidation_preference == 1.0
        assert share_class.participating is False
        assert share_class.voting_rights_per_share == 1.0

    def test_preferred_share_class(self):
        """Test creating a preferred share class."""
        share_class = ShareClass(
            name="Series A Preferred",
            class_name="Series A Preferred",
            shares_authorized=2000000,
            shares_outstanding=1500000,
            liquidation_preference=1.0,
            participating=False,
            voting_rights_per_share=1.0,
            start_date=date.today()
        )

        assert share_class.liquidation_preference == 1.0
        assert share_class.participating is False
        assert share_class.utilization_percentage == 75.0

    def test_share_class_validation(self):
        """Test share class validation."""
        # Test negative shares authorized
        with pytest.raises(ValueError, match="shares_authorized must be positive"):
            ShareClass(
                name="Invalid",
                class_name="Invalid",
                shares_authorized=-1000,
                start_date=date.today()
            )

        # Test outstanding exceeds authorized
        with pytest.raises(ValueError, match="shares_outstanding cannot exceed shares_authorized"):
            ShareClass(
                name="Invalid",
                class_name="Invalid",
                shares_authorized=1000,
                shares_outstanding=2000,
                start_date=date.today()
            )

        # Test invalid liquidation preference
        with pytest.raises(ValueError, match="liquidation_preference must be between 0 and 10"):
            ShareClass(
                name="Invalid",
                class_name="Invalid",
                shares_authorized=1000,
                liquidation_preference=15.0,
                start_date=date.today()
            )

    def test_liquidation_proceeds_non_participating(self):
        """Test liquidation proceeds calculation for non-participating preferred."""
        share_class = ShareClass(
            name="Series A",
            class_name="Series A",
            shares_authorized=1000000,
            shares_outstanding=1000000,
            liquidation_preference=1.0,
            participating=False,
            par_value=1.0,
            start_date=date.today()
        )

        # Exit value of $5M, holding 100k shares (10%)
        # Preference: 100k * $1 = $100k
        # Pro-rata: 10% * $5M = $500k
        # Should get the higher amount: $500k
        proceeds = share_class.calculate_liquidation_proceeds(5000000, 100000)
        assert proceeds == 500000

        # Exit value of $500k, same holding
        # Preference: $100k, Pro-rata: $50k
        # Should get preference: $100k
        proceeds = share_class.calculate_liquidation_proceeds(500000, 100000)
        assert proceeds == 100000

    def test_liquidation_proceeds_participating(self):
        """Test liquidation proceeds calculation for participating preferred."""
        share_class = ShareClass(
            name="Series A",
            class_name="Series A",
            shares_authorized=1000000,
            shares_outstanding=1000000,
            liquidation_preference=1.0,
            participating=True,
            par_value=1.0,
            start_date=date.today()
        )

        # Exit value of $5M, holding 100k shares (10%)
        # Preference: $100k
        # Remaining: $5M - $1M = $4M
        # Pro-rata of remaining: 10% * $4M = $400k
        # Total: $100k + $400k = $500k
        proceeds = share_class.calculate_liquidation_proceeds(5000000, 100000)
        assert proceeds == 500000


class TestShareholder:
    """Test Shareholder entity."""

    def test_create_founder_shareholder(self):
        """Test creating a founder shareholder."""
        shareholder = Shareholder(
            name="Alice Johnson",
            shareholder_type="founder",
            total_shares=4000000,
            share_class="common",
            start_date=date.today()
        )

        assert shareholder.shareholder_type == "founder"
        assert shareholder.total_shares == 4000000
        assert shareholder.share_class == "common"
        assert shareholder.is_founder is True
        assert shareholder.is_employee is False
        assert shareholder.is_investor is False

    def test_create_employee_shareholder_with_vesting(self):
        """Test creating an employee shareholder with vesting."""
        shareholder = Shareholder(
            name="Bob Smith",
            shareholder_type="employee",
            total_shares=100000,
            share_class="common",
            acquisition_date=date(2024, 1, 1),
            cliff_months=12,
            vesting_months=48,
            start_date=date.today()
        )

        assert shareholder.shareholder_type == "employee"
        assert shareholder.cliff_months == 12
        assert shareholder.vesting_months == 48
        assert shareholder.is_employee is True

    def test_shareholder_validation(self):
        """Test shareholder validation."""
        # Test invalid shareholder type
        with pytest.raises(ValueError, match="shareholder_type must be one of"):
            Shareholder(
                name="Invalid",
                shareholder_type="invalid_type",
                total_shares=1000,
                start_date=date.today()
            )

        # Test negative shares
        with pytest.raises(ValueError, match="total_shares must be positive"):
            Shareholder(
                name="Invalid",
                shareholder_type="founder",
                total_shares=-1000,
                start_date=date.today()
            )

        # Test vested shares exceeding total
        with pytest.raises(ValueError, match="vested_shares cannot exceed total_shares"):
            Shareholder(
                name="Invalid",
                shareholder_type="employee",
                total_shares=1000,
                vested_shares=2000,
                start_date=date.today()
            )

    def test_ownership_percentage_calculation(self):
        """Test ownership percentage calculation."""
        shareholder = Shareholder(
            name="Test",
            shareholder_type="founder",
            total_shares=2000000,
            start_date=date.today()
        )

        # 2M shares out of 10M total = 20%
        ownership = shareholder.calculate_ownership_percentage(10000000)
        assert ownership == 20.0

        # Handle zero total shares
        ownership = shareholder.calculate_ownership_percentage(0)
        assert ownership == 0.0

    def test_vesting_calculation(self):
        """Test vesting calculation."""
        acquisition_date = date(2024, 1, 1)
        shareholder = Shareholder(
            name="Test",
            shareholder_type="employee",
            total_shares=48000,  # 1000 shares per month over 48 months
            acquisition_date=acquisition_date,
            cliff_months=12,
            vesting_months=48,
            start_date=date.today()
        )

        # Before cliff (6 months) - should be 0
        vested = shareholder.calculate_vested_shares(date(2024, 7, 1))
        assert vested == 0

        # At cliff (12 months) - should be 25% = 12000 shares
        vested = shareholder.calculate_vested_shares(date(2025, 1, 1))
        assert vested == 12000

        # At 24 months - should be 50% = 24000 shares
        vested = shareholder.calculate_vested_shares(date(2026, 1, 1))
        assert vested == 24000

        # After full vesting (48+ months) - should be 100%
        vested = shareholder.calculate_vested_shares(date(2028, 1, 1))
        assert vested == 48000

    def test_voting_power_calculation(self):
        """Test voting power calculation."""
        shareholder = Shareholder(
            name="Test",
            shareholder_type="founder",
            total_shares=1000000,
            share_class="common",
            start_date=date.today()
        )

        share_classes = {
            "common": {"voting_rights_per_share": 1.0},
            "preferred": {"voting_rights_per_share": 1.0},
            "super_voting": {"voting_rights_per_share": 10.0}
        }

        # Common shares: 1M shares * 1 vote = 1M votes
        voting_power = shareholder.get_voting_power(share_classes)
        assert voting_power == 1000000

        # Test with super-voting shares
        shareholder.share_class = "super_voting"
        voting_power = shareholder.get_voting_power(share_classes)
        assert voting_power == 10000000


class TestFundingRound:
    """Test FundingRound entity."""

    def test_create_seed_round(self):
        """Test creating a seed round."""
        round_entity = FundingRound(
            name="Seed Round",
            round_type="seed",
            amount_raised=2000000,
            pre_money_valuation=8000000,
            shares_issued=2000000,
            price_per_share=1.0,
            start_date=date.today()
        )

        assert round_entity.round_type == "seed"
        assert round_entity.amount_raised == 2000000
        assert round_entity.computed_pre_money_valuation == 8000000
        assert round_entity.computed_post_money_valuation == 10000000

    def test_funding_round_validation(self):
        """Test funding round validation."""
        # Test invalid round type
        with pytest.raises(ValueError, match="round_type must be one of"):
            FundingRound(
                name="Invalid",
                round_type="invalid_round",
                amount_raised=1000000,
                pre_money_valuation=5000000,
                start_date=date.today()
            )

        # Test negative amount raised
        with pytest.raises(ValueError, match="amount_raised must be positive"):
            FundingRound(
                name="Invalid",
                round_type="seed",
                amount_raised=-1000000,
                pre_money_valuation=5000000,
                start_date=date.today()
            )

        # Test inconsistent valuation
        with pytest.raises(ValueError, match="post_money_valuation must equal"):
            FundingRound(
                name="Invalid",
                round_type="seed",
                amount_raised=2000000,
                pre_money_valuation=8000000,
                post_money_valuation=15000000,  # Should be 10M
                start_date=date.today()
            )

    def test_valuation_calculations(self):
        """Test valuation calculations."""
        # Test with pre-money provided
        round_entity = FundingRound(
            name="Test",
            round_type="seed",
            amount_raised=2000000,
            pre_money_valuation=8000000,
            start_date=date.today()
        )

        assert round_entity.computed_pre_money_valuation == 8000000
        assert round_entity.computed_post_money_valuation == 10000000

        # Test with post-money provided
        round_entity = FundingRound(
            name="Test",
            round_type="seed",
            amount_raised=2000000,
            post_money_valuation=10000000,
            start_date=date.today()
        )

        assert round_entity.computed_pre_money_valuation == 8000000
        assert round_entity.computed_post_money_valuation == 10000000

    def test_dilution_calculation(self):
        """Test dilution calculation."""
        round_entity = FundingRound(
            name="Series A",
            round_type="series_a",
            amount_raised=5000000,
            pre_money_valuation=20000000,
            shares_issued=1000000,
            price_per_share=5.0,
            start_date=date.today()
        )

        existing_cap_table = {
            'total_shares': 4000000,
            'shareholders': {
                'Alice (Founder)': 2000000,
                'Bob (Founder)': 1500000,
                'Employee Pool': 500000
            }
        }

        dilution = round_entity.calculate_dilution_impact(existing_cap_table)

        # Total shares after round: 4M + 1M = 5M
        # Alice: was 50% (2M/4M), now 40% (2M/5M) = 10% dilution
        # Bob: was 37.5% (1.5M/4M), now 30% (1.5M/5M) = 7.5% dilution

        assert abs(dilution['Alice (Founder)'] - 10.0) < 0.01
        assert abs(dilution['Bob (Founder)'] - 7.5) < 0.01
        assert abs(dilution['Employee Pool'] - 2.5) < 0.01

    def test_round_math_validation(self):
        """Test round math validation."""
        round_entity = FundingRound(
            name="Test",
            round_type="seed",
            amount_raised=2000000,
            pre_money_valuation=8000000,
            post_money_valuation=10000000,
            shares_issued=2000000,
            price_per_share=1.0,
            start_date=date.today()
        )

        errors = round_entity.validate_round_math()
        assert len(errors) == 0

        # Test with inconsistent share math
        round_entity.price_per_share = 2.0  # Should cause error
        errors = round_entity.validate_round_math()
        assert len(errors) > 0
        assert "doesn't equal amount raised" in errors[0]


class TestCapTableEntityCreation:
    """Test cap table entity creation functions."""

    def test_create_shareholder_entity(self):
        """Test creating shareholder entity from dict."""
        data = {
            'type': 'shareholder',
            'name': 'Test Shareholder',
            'shareholder_type': 'founder',
            'total_shares': 1000000,
            'share_class': 'common',
            'start_date': date.today()
        }

        entity = create_captable_entity(data)
        assert isinstance(entity, Shareholder)
        assert entity.name == 'Test Shareholder'
        assert entity.shareholder_type == 'founder'

    def test_create_share_class_entity(self):
        """Test creating share class entity from dict."""
        data = {
            'type': 'share_class',
            'name': 'Common Stock',
            'class_name': 'Common',
            'shares_authorized': 10000000,
            'start_date': date.today()
        }

        entity = create_captable_entity(data)
        assert isinstance(entity, ShareClass)
        assert entity.class_name == 'Common'
        assert entity.shares_authorized == 10000000

    def test_create_funding_round_entity(self):
        """Test creating funding round entity from dict."""
        data = {
            'type': 'funding_round',
            'name': 'Seed Round',
            'round_type': 'seed',
            'amount_raised': 2000000,
            'pre_money_valuation': 8000000,
            'start_date': date.today()
        }

        entity = create_captable_entity(data)
        assert isinstance(entity, FundingRound)
        assert entity.round_type == 'seed'
        assert entity.amount_raised == 2000000

    def test_create_invalid_entity_type(self):
        """Test creating invalid entity type."""
        data = {
            'type': 'invalid_type',
            'name': 'Invalid',
            'start_date': date.today()
        }

        with pytest.raises(ValueError, match="Unknown cap table entity type"):
            create_captable_entity(data)
