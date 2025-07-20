"""Tests for enhanced Investment entity with cap table integration."""

from datetime import date

import pytest
from cashcow.models.captable import FundingRound
from cashcow.models.entities import Investment


class TestEnhancedInvestment:
    """Test enhanced Investment entity with cap table features."""

    def test_create_basic_investment_backward_compatibility(self):
        """Test that basic investment creation still works (backward compatibility)."""
        investment = Investment(
            name="Basic Investment",
            amount=1000000,
            investor="VC Fund",
            start_date=date.today()
        )

        assert investment.amount == 1000000
        assert investment.investor == "VC Fund"
        assert investment.shares_issued is None
        assert investment.liquidation_preference == 1.0
        assert investment.participating is False

    def test_create_investment_with_cap_table_fields(self):
        """Test creating investment with cap table fields."""
        investment = Investment(
            name="Series A",
            amount=5000000,
            investor="Top Tier VC",
            shares_issued=1000000,
            price_per_share=5.0,
            pre_money_valuation=20000000,
            liquidation_preference=1.0,
            participating=False,
            anti_dilution_provision="weighted_average",
            board_seats=2,
            voting_rights_per_share=1.0,
            start_date=date.today()
        )

        assert investment.shares_issued == 1000000
        assert investment.price_per_share == 5.0
        assert investment.pre_money_valuation == 20000000
        assert investment.liquidation_preference == 1.0
        assert investment.anti_dilution_provision == "weighted_average"
        assert investment.board_seats == 2

    def test_investment_validation(self):
        """Test validation of cap table fields."""
        # Test invalid liquidation preference
        with pytest.raises(ValueError, match="liquidation_preference must be between 0 and 10"):
            Investment(
                name="Invalid",
                amount=1000000,
                liquidation_preference=15.0,
                start_date=date.today()
            )

        # Test invalid anti-dilution provision
        with pytest.raises(ValueError, match="anti_dilution_provision must be one of"):
            Investment(
                name="Invalid",
                amount=1000000,
                anti_dilution_provision="invalid_provision",
                start_date=date.today()
            )

        # Test negative board seats
        with pytest.raises(ValueError, match="board_seats cannot be negative"):
            Investment(
                name="Invalid",
                amount=1000000,
                board_seats=-1,
                start_date=date.today()
            )

        # Test invalid voting rights
        with pytest.raises(ValueError, match="voting_rights_per_share must be between 0 and 100"):
            Investment(
                name="Invalid",
                amount=1000000,
                voting_rights_per_share=150.0,
                start_date=date.today()
            )

    def test_to_funding_round_conversion(self):
        """Test conversion of Investment to FundingRound."""
        investment = Investment(
            name="Series A Investment",
            amount=5000000,
            investor="Acme Ventures",
            round_name="Series A",
            shares_issued=1000000,
            price_per_share=5.0,
            pre_money_valuation=20000000,
            liquidation_preference=1.0,
            participating=False,
            board_seats=2,
            start_date=date(2024, 1, 15)
        )

        funding_round = investment.to_funding_round()

        assert funding_round is not None
        assert isinstance(funding_round, FundingRound)
        assert funding_round.round_type == "series_a"
        assert funding_round.amount_raised == 5000000
        assert funding_round.shares_issued == 1000000
        assert funding_round.price_per_share == 5.0
        assert funding_round.pre_money_valuation == 20000000
        assert funding_round.lead_investor == "Acme Ventures"
        assert funding_round.board_seats_granted == 2

    def test_to_funding_round_without_cap_table_data(self):
        """Test that Investment without cap table data doesn't convert."""
        investment = Investment(
            name="Basic Investment",
            amount=1000000,
            investor="Basic Investor",
            start_date=date.today()
        )

        funding_round = investment.to_funding_round()
        assert funding_round is None

    def test_round_type_inference(self):
        """Test round type inference from various inputs."""
        # Test inference from round name
        test_cases = [
            ("Pre-Seed Round", "pre_seed"),
            ("Seed Investment", "seed"),
            ("Series A Funding", "series_a"),
            ("Series B Round", "series_b"),
            ("Bridge Financing", "bridge"),
        ]

        for round_name, expected_type in test_cases:
            investment = Investment(
                name=f"Test {round_name}",
                amount=2000000,
                round_name=round_name,
                shares_issued=100000,
                start_date=date.today()
            )

            assert investment._infer_round_type() == expected_type

        # Test inference from amount (when no round name)
        amount_test_cases = [
            (300000, "pre_seed"),
            (1500000, "seed"),
            (8000000, "series_a"),
            (25000000, "series_b"),
            (75000000, "series_c"),
        ]

        for amount, expected_type in amount_test_cases:
            investment = Investment(
                name="Amount Based",
                amount=amount,
                shares_issued=100000,
                start_date=date.today()
            )

            assert investment._infer_round_type() == expected_type

    def test_ownership_percentage_calculation(self):
        """Test ownership percentage calculation."""
        investment = Investment(
            name="Test Investment",
            amount=2000000,
            shares_issued=1000000,
            start_date=date.today()
        )

        # 1M new shares, 4M existing = 20% ownership
        ownership = investment.calculate_ownership_percentage(4000000)
        assert ownership == 20.0

        # No shares issued - should return None
        investment.shares_issued = None
        ownership = investment.calculate_ownership_percentage(4000000)
        assert ownership is None

        # Zero existing shares - should return None
        investment.shares_issued = 1000000
        ownership = investment.calculate_ownership_percentage(0)
        assert ownership is None

    def test_dilution_impact_calculation(self):
        """Test dilution impact calculation."""
        investment = Investment(
            name="Series A",
            amount=5000000,
            shares_issued=1000000,
            start_date=date.today()
        )

        existing_shareholders = {
            "Alice (Founder)": 2000000,
            "Bob (Founder)": 1500000,
            "Employee Pool": 500000
        }

        dilution = investment.calculate_dilution_impact(existing_shareholders)

        # Total shares before: 4M, after: 5M
        # Alice: 50% -> 40% = 10% dilution
        # Bob: 37.5% -> 30% = 7.5% dilution
        # Employee Pool: 12.5% -> 10% = 2.5% dilution

        assert abs(dilution["Alice (Founder)"] - 10.0) < 0.01
        assert abs(dilution["Bob (Founder)"] - 7.5) < 0.01
        assert abs(dilution["Employee Pool"] - 2.5) < 0.01

    def test_cap_table_summary(self):
        """Test cap table summary generation."""
        investment = Investment(
            name="Test Investment",
            amount=3000000,
            investor="Test VC",
            shares_issued=600000,
            price_per_share=5.0,
            pre_money_valuation=12000000,
            liquidation_preference=1.0,
            participating=False,
            board_seats=1,
            voting_rights_per_share=1.0,
            start_date=date.today()
        )

        summary = investment.get_cap_table_summary()

        assert summary['investor'] == "Test VC"
        assert summary['amount'] == 3000000
        assert summary['shares_issued'] == 600000
        assert summary['price_per_share'] == 5.0
        assert summary['pre_money_valuation'] == 12000000
        assert summary['liquidation_preference'] == 1.0
        assert summary['participating'] is False
        assert summary['board_seats'] == 1
        assert summary['voting_rights_per_share'] == 1.0
        assert summary['has_cap_table_data'] is True

        # Test investment without cap table data
        basic_investment = Investment(
            name="Basic",
            amount=1000000,
            start_date=date.today()
        )

        basic_summary = basic_investment.get_cap_table_summary()
        assert basic_summary['has_cap_table_data'] is False

    def test_legacy_methods_still_work(self):
        """Test that legacy Investment methods still work with new fields."""
        investment = Investment(
            name="Test Investment",
            amount=2000000,
            investor="Test Investor",
            shares_issued=400000,  # New cap table field
            price_per_share=5.0,   # New cap table field
            start_date=date(2024, 1, 1)
        )

        # Test existing method still works
        disbursement = investment.calculate_monthly_disbursement(date(2024, 1, 15))
        assert disbursement == 2000000  # Lump sum in first month

        # Test with disbursement schedule
        investment.disbursement_schedule = [
            {"date": "2024-01-01", "amount": 1000000},
            {"date": "2024-07-01", "amount": 1000000}
        ]

        disbursement_jan = investment.calculate_monthly_disbursement(date(2024, 1, 15))
        assert disbursement_jan == 1000000

        disbursement_july = investment.calculate_monthly_disbursement(date(2024, 7, 15))
        assert disbursement_july == 1000000

        disbursement_other = investment.calculate_monthly_disbursement(date(2024, 3, 15))
        assert disbursement_other == 0
