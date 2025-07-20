"""Comprehensive tests for cap table ownership calculation engine."""

from datetime import date, timedelta

import pytest
from cashcow.engine.captable_calculators import (
    calculate_basic_ownership,
    calculate_board_control_percentage,
    calculate_dilution_impact,
    calculate_fully_diluted_ownership,
    calculate_ownership_percentage,
    calculate_share_class_utilization,
    calculate_total_shares_by_class,
    calculate_total_shares_fully_diluted,
    calculate_voting_control,
    calculate_voting_percentage,
    generate_cap_table_summary,
    get_employee_ownership_percentage,
    get_founder_ownership_percentage,
    get_investor_ownership_percentage,
    round_percentage,
)
from cashcow.models.captable import FundingRound, ShareClass, Shareholder
from cashcow.models.interfaces.captable_interfaces import CapTableSummary


class TestCalculatorHelperFunctions:
    """Test helper functions for cap table calculations."""

    def test_calculate_total_shares_by_class(self):
        """Test calculation of total shares by class."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Bob",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=2000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Investor",
                start_date=date.today(),
                shareholder_type="investor",
                total_shares=1000000,
                share_class="series_a"
            )
        ]

        shares_by_class = calculate_total_shares_by_class(shareholders)

        assert shares_by_class["common"] == 6000000
        assert shares_by_class["series_a"] == 1000000

    def test_calculate_total_shares_fully_diluted(self):
        """Test fully diluted share calculation."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            )
        ]

        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=8000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            )
        ]

        total_fully_diluted = calculate_total_shares_fully_diluted(shareholders, share_classes)

        # Should use the higher of authorized (10M) vs issued (4M from shareholders)
        assert total_fully_diluted == 10000000

    def test_round_percentage(self):
        """Test percentage rounding function."""
        # Test normal rounding
        assert round_percentage(0.123456) == 0.1235
        assert round_percentage(0.123450) == 0.1235  # Round up on 5
        assert round_percentage(0.123449) == 0.1234

        # Test edge cases
        assert round_percentage(0.0) == 0.0
        assert round_percentage(1.0) == 1.0
        assert round_percentage(0.999999) == 1.0


class TestOwnershipCalculations:
    """Test core ownership calculation functions."""

    def setUp(self):
        """Set up test data."""
        self.shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice Johnson",
                start_date=date.today() - timedelta(days=365),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Bob Smith",
                start_date=date.today() - timedelta(days=365),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Employee Option Pool",
                start_date=date.today() - timedelta(days=365),
                shareholder_type="other",  # Use "other" for option pool
                total_shares=2000000,
                share_class="common"
            )
        ]

        self.share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today() - timedelta(days=365),
                class_name="common",
                shares_authorized=15000000,
                shares_issued=10000000,
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            )
        ]

    def test_calculate_fully_diluted_ownership(self):
        """Test fully diluted ownership calculation."""
        self.setUp()

        alice = self.shareholders[0]
        ownership = calculate_fully_diluted_ownership(alice, self.shareholders, self.share_classes)

        # Alice has 4M out of 15M authorized = 26.67%
        expected = 4000000 / 15000000
        assert abs(ownership - expected) < 0.0001

    def test_calculate_basic_ownership(self):
        """Test basic ownership calculation."""
        self.setUp()

        alice = self.shareholders[0]
        total_issued = sum(s.total_shares for s in self.shareholders)
        ownership = calculate_basic_ownership(alice, total_issued)

        # Alice has 4M out of 10M issued = 40%
        expected = 4000000 / 10000000
        assert abs(ownership - expected) < 0.0001

    def test_calculate_voting_percentage(self):
        """Test voting percentage calculation."""
        self.setUp()

        alice = self.shareholders[0]
        share_class_map = {sc.class_name: sc for sc in self.share_classes}

        voting_pct = calculate_voting_percentage(alice, share_class_map, self.shareholders)

        # All shareholders have same voting rights, so Alice has 4M/10M = 40%
        expected = 4000000 / 10000000
        assert abs(voting_pct - expected) < 0.0001

    def test_calculate_voting_percentage_different_rights(self):
        """Test voting percentage with different voting rights per share."""
        self.setUp()

        # Add preferred share class with different voting rights
        preferred_class = ShareClass(
            type="share_class",
            name="Series A Preferred",
            start_date=date.today(),
            class_name="series_a",
            shares_authorized=2000000,
            shares_issued=2000000,
            liquidation_preference=1.0,
            liquidation_seniority=2,
            voting_rights_per_share=5.0  # 5x voting rights
        )

        preferred_shareholder = Shareholder(
            type="shareholder",
            name="Preferred Investor",
            start_date=date.today(),
            shareholder_type="investor",
            total_shares=2000000,
            share_class="series_a"
        )

        all_shareholders = self.shareholders + [preferred_shareholder]
        share_class_map = {sc.class_name: sc for sc in self.share_classes + [preferred_class]}

        # Calculate voting percentage for Alice
        alice = self.shareholders[0]
        alice_voting_pct = calculate_voting_percentage(alice, share_class_map, all_shareholders)

        # Total voting power: 10M common @ 1x + 2M preferred @ 5x = 20M voting power
        # Alice has 4M @ 1x = 4M voting power = 20%
        expected = 4000000 / 20000000
        assert abs(alice_voting_pct - expected) < 0.0001

        # Calculate voting percentage for preferred investor
        preferred_voting_pct = calculate_voting_percentage(preferred_shareholder, share_class_map, all_shareholders)

        # Preferred has 2M @ 5x = 10M voting power = 50%
        expected = 10000000 / 20000000
        assert abs(preferred_voting_pct - expected) < 0.0001


class TestCalculatorRegistrations:
    """Test calculator function registrations and invocations."""

    def setUp(self):
        """Set up test data."""
        self.shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice Johnson",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=6000000,
                share_class="common",
                board_seats=2
            ),
            Shareholder(
                type="shareholder",
                name="Bob Smith",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common",
                board_seats=1
            )
        ]

        self.share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=12000000,
                shares_issued=10000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            )
        ]

        self.context = {
            'all_entities': self.shareholders + self.share_classes,
            'as_of_date': date.today(),
            'scenario': 'baseline'
        }

    def test_ownership_percentage_calculator(self):
        """Test ownership percentage calculator registration and function."""
        self.setUp()

        alice = self.shareholders[0]
        ownership_pct = calculate_ownership_percentage(alice, self.context)

        # Alice has 6M out of 12M authorized = 50%
        expected = 6000000 / 12000000
        assert abs(ownership_pct - expected) < 0.0001

    def test_voting_control_calculator(self):
        """Test voting control calculator."""
        self.setUp()

        alice = self.shareholders[0]
        voting_pct = calculate_voting_control(alice, self.context)

        # Alice has 6M out of 10M voting shares = 60%
        expected = 6000000 / 10000000
        assert abs(voting_pct - expected) < 0.0001

    def test_board_control_calculator(self):
        """Test board control calculator."""
        self.setUp()

        alice = self.shareholders[0]
        board_pct = calculate_board_control_percentage(alice, self.context)

        # Alice has 2 out of 3 board seats = 66.67%
        expected = 2 / 3
        assert abs(board_pct - expected) < 0.0001

    def test_share_class_utilization_calculator(self):
        """Test share class utilization calculator."""
        self.setUp()

        share_class = self.share_classes[0]
        utilization = calculate_share_class_utilization(share_class, self.context)

        # 10M issued out of 12M authorized = 83.33%
        expected = 10000000 / 12000000
        assert abs(utilization - expected) < 0.0001

    def test_dilution_impact_calculator(self):
        """Test dilution impact calculator."""
        self.setUp()

        funding_round = FundingRound(
            type="funding_round",
            name="Series A",
            start_date=date.today(),
            round_type="series_a",
            amount_raised=2000000.0,
            shares_issued=2000000,
            price_per_share=1.0,
            pre_money_valuation=10000000.0,
            post_money_valuation=12000000.0,
            share_class="series_a"
        )

        context = {
            'all_entities': self.shareholders,
            'as_of_date': date.today()
        }

        dilution_result = calculate_dilution_impact(funding_round, context)

        assert isinstance(dilution_result, dict)
        assert 'dilution_percentage' in dilution_result
        assert 'new_investor_ownership' in dilution_result
        assert 'pre_round_shares' in dilution_result
        assert 'post_round_shares' in dilution_result

        # Pre-round: 10M shares, new round: 2M shares, post-round: 12M shares
        # Dilution = 2M / 12M = 16.67%
        expected_dilution = 2000000 / 12000000
        assert abs(dilution_result['dilution_percentage'] - expected_dilution) < 0.0001


class TestCapTableSummary:
    """Test cap table summary generation."""

    def setUp(self):
        """Set up complex cap table for testing."""
        self.shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice Johnson",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common",
                board_seats=2
            ),
            Shareholder(
                type="shareholder",
                name="Bob Smith",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common",
                board_seats=1
            ),
            Shareholder(
                type="shareholder",
                name="Employee Pool",
                start_date=date(2020, 1, 1),
                shareholder_type="other",
                total_shares=2000000,
                share_class="common",
                board_seats=0
            ),
            Shareholder(
                type="shareholder",
                name="Series A Investor",
                start_date=date(2021, 6, 1),
                shareholder_type="investor",
                total_shares=2000000,
                share_class="series_a",
                board_seats=1
            )
        ]

        self.share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date(2020, 1, 1),
                class_name="common",
                shares_authorized=15000000,
                shares_issued=10000000,
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            ),
            ShareClass(
                type="share_class",
                name="Series A Preferred",
                start_date=date(2021, 6, 1),
                class_name="series_a",
                shares_authorized=3000000,
                shares_issued=2000000,
                liquidation_preference=1.0,
                liquidation_seniority=2,
                participating=True,
                voting_rights_per_share=1.0,
                convertible=True,
                anti_dilution_provision="weighted_average_broad"
            )
        ]

        self.funding_rounds = [
            FundingRound(
                type="funding_round",
                name="Series A",
                start_date=date(2021, 6, 1),
                round_type="series_a",
                amount_raised=2000000.0,
                shares_issued=2000000,
                price_per_share=1.0,
                pre_money_valuation=10000000.0,
                post_money_valuation=12000000.0,
                share_class="series_a"
            )
        ]

        self.all_entities = self.shareholders + self.share_classes + self.funding_rounds

        self.context = {
            'all_entities': self.all_entities,
            'as_of_date': date.today(),
            'scenario': 'baseline'
        }

    def test_generate_cap_table_summary(self):
        """Test cap table summary generation."""
        self.setUp()

        summary = generate_cap_table_summary(self.all_entities, self.context)

        assert isinstance(summary, CapTableSummary)

        # Check basic metrics
        assert summary.total_shares_outstanding == 12000000  # All issued shares
        assert summary.fully_diluted_shares == 18000000  # Total authorized

        # Check ownership breakdown
        assert len(summary.ownership_by_shareholder) == 4
        assert "Alice Johnson" in summary.ownership_by_shareholder
        assert "Bob Smith" in summary.ownership_by_shareholder
        assert "Employee Pool" in summary.ownership_by_shareholder
        assert "Series A Investor" in summary.ownership_by_shareholder

        # Check Alice's ownership (4M out of 18M = 22.22%)
        alice_ownership = summary.ownership_by_shareholder["Alice Johnson"]
        expected_alice = 4000000 / 18000000
        assert abs(alice_ownership - expected_alice) < 0.0001

        # Check voting control breakdown
        assert len(summary.voting_control) == 4

        # Check ownership by class
        assert len(summary.ownership_by_class) == 2
        assert "common" in summary.ownership_by_class
        assert "series_a" in summary.ownership_by_class


class TestKPICalculators:
    """Test KPI calculation functions."""

    def setUp(self):
        """Set up test data for KPI calculations."""
        self.shareholders = [
            Shareholder(
                type="shareholder",
                name="Founder 1",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Founder 2",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=3000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Employee 1",
                start_date=date.today(),
                shareholder_type="employee",
                total_shares=100000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Option Pool",
                start_date=date.today(),
                shareholder_type="other",
                total_shares=1900000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Investor 1",
                start_date=date.today(),
                shareholder_type="investor",
                total_shares=2000000,
                share_class="series_a"
            )
        ]

        self.share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=12000000,
                shares_issued=9000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            ),
            ShareClass(
                type="share_class",
                name="Series A",
                start_date=date.today(),
                class_name="series_a",
                shares_authorized=3000000,
                shares_issued=2000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            )
        ]

    def test_founder_ownership_percentage(self):
        """Test founder ownership percentage calculation."""
        self.setUp()

        founder_pct = get_founder_ownership_percentage(self.shareholders, self.share_classes)

        # Founders have 7M out of 15M total authorized = 46.67%
        total_founder_shares = 4000000 + 3000000
        total_authorized = 12000000 + 3000000
        expected = total_founder_shares / total_authorized

        assert abs(founder_pct - expected) < 0.0001

    def test_employee_ownership_percentage(self):
        """Test employee ownership percentage calculation."""
        self.setUp()

        employee_pct = get_employee_ownership_percentage(self.shareholders, self.share_classes)

        # Employees + option pool have 2M out of 15M total authorized = 13.33%
        total_employee_shares = 100000 + 1900000
        total_authorized = 12000000 + 3000000
        expected = total_employee_shares / total_authorized

        assert abs(employee_pct - expected) < 0.0001

    def test_investor_ownership_percentage(self):
        """Test investor ownership percentage calculation."""
        self.setUp()

        investor_pct = get_investor_ownership_percentage(self.shareholders, self.share_classes)

        # Investors have 2M out of 15M total authorized = 13.33%
        total_investor_shares = 2000000
        total_authorized = 12000000 + 3000000
        expected = total_investor_shares / total_authorized

        assert abs(investor_pct - expected) < 0.0001


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_cap_table(self):
        """Test calculations with empty cap table."""
        context = {'all_entities': []}

        # Should handle empty entities gracefully
        summary = generate_cap_table_summary([], context)

        assert summary.total_shares_outstanding == 0
        assert summary.total_shares_fully_diluted == 0
        assert len(summary.ownership_breakdown) == 0

    def test_zero_shares_shareholder(self):
        """Test with shareholder having zero shares."""
        shareholder = Shareholder(
            type="shareholder",
            name="Zero Shares",
            start_date=date.today(),
            shareholder_type="founder",
            total_shares=0,
            share_class="common"
        )

        share_class = ShareClass(
            type="share_class",
            name="Common",
            start_date=date.today(),
            class_name="common",
            shares_authorized=10000000,
            shares_issued=0,
            liquidation_preference=1.0,
            voting_rights_per_share=1.0
        )

        context = {'all_entities': [shareholder, share_class]}

        ownership_pct = calculate_ownership_percentage(shareholder, context)
        assert ownership_pct == 0.0

    def test_invalid_share_class_reference(self):
        """Test with shareholder referencing non-existent share class."""
        shareholder = Shareholder(
            type="shareholder",
            name="Invalid Reference",
            start_date=date.today(),
            shareholder_type="founder",
            total_shares=1000000,
            share_class="nonexistent_class"
        )

        context = {'all_entities': [shareholder]}

        # Should handle gracefully and return 0
        voting_pct = calculate_voting_control(shareholder, context)
        assert voting_pct == 0.0


class TestPerformance:
    """Test performance with large cap tables."""

    def test_large_cap_table_performance(self):
        """Test performance with large number of shareholders."""
        # Create 1000 employee shareholders
        shareholders = []
        for i in range(1000):
            shareholders.append(
                Shareholder(
                    type="shareholder",
                    name=f"Employee {i:04d}",
                    start_date=date.today(),
                    shareholder_type="employee",
                    total_shares=1000,
                    share_class="common"
                )
            )

        # Add founders
        shareholders.extend([
            Shareholder(
                type="shareholder",
                name="Founder Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Founder Bob",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            )
        ])

        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=9000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            )
        ]

        all_entities = shareholders + share_classes
        context = {'all_entities': all_entities}

        # Test that large cap table calculation completes in reasonable time
        import time
        start_time = time.time()

        summary = generate_cap_table_summary(all_entities, context)

        end_time = time.time()
        calculation_time = end_time - start_time

        # Should complete in under 1 second
        assert calculation_time < 1.0

        # Verify results are correct
        assert summary.total_shares_outstanding == 9000000
        assert len(summary.ownership_breakdown) == 1002  # 1000 employees + 2 founders


if __name__ == "__main__":
    pytest.main([__file__])
