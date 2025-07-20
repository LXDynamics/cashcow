"""Integration tests for Phase 2 cap table functionality."""

from datetime import date

import pytest
from cashcow.engine.captable_calculators import (
    calculate_ownership_percentage,
    calculate_voting_control,
    generate_cap_table_summary,
    get_employee_ownership_percentage,
    get_founder_ownership_percentage,
    get_investor_ownership_percentage,
)
from cashcow.models.captable import FundingRound, ShareClass, Shareholder
from cashcow.models.validators.captable_validators import CapTableValidator


class TestPhase2Integration:
    """Test integration between validation and calculation engines."""

    def setUp(self):
        """Set up realistic cap table for integration testing."""
        # Create a realistic Series A cap table
        self.shareholders = [
            # Founders
            Shareholder(
                type="shareholder",
                name="Alice Johnson (Founder)",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=3500000,
                share_class="common",
                board_seats=2
            ),
            Shareholder(
                type="shareholder",
                name="Bob Smith (Founder)",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=3500000,
                share_class="common",
                board_seats=1
            ),
            # Employees
            Shareholder(
                type="shareholder",
                name="Employee Option Pool",
                start_date=date(2020, 1, 1),
                shareholder_type="other",
                total_shares=2000000,
                share_class="common",
                board_seats=0
            ),
            # Investor
            Shareholder(
                type="shareholder",
                name="Venture Capital Fund",
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
                shares_authorized=12000000,
                shares_issued=9000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0,
                par_value=0.001
            ),
            ShareClass(
                type="share_class",
                name="Series A Preferred",
                start_date=date(2021, 6, 1),
                class_name="series_a",
                shares_authorized=3000000,
                shares_issued=2000000,
                liquidation_preference=1.0,
                participating=True,
                voting_rights_per_share=1.0,
                convertible_to="common",
                conversion_ratio=1.0,
                anti_dilution_provision="weighted_average_broad",
                par_value=1.0
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
                pre_money_valuation=9000000.0,
                post_money_valuation=11000000.0,
                share_class="series_a"
            )
        ]

        self.all_entities = self.shareholders + self.share_classes + self.funding_rounds

        self.context = {
            'all_entities': self.all_entities,
            'as_of_date': date.today(),
            'scenario': 'baseline'
        }

    def test_phase2_complete_workflow(self):
        """Test complete Phase 2 workflow: validation -> calculation -> summary."""
        self.setUp()

        # Step 1: Validate cap table data
        validator = CapTableValidator()

        # Validate individual entities
        for entity in self.all_entities:
            errors = validator.validate_entity_consistency(entity)
            # Should have no critical errors
            critical_errors = [e for e in errors if e.severity == "error"]
            assert len(critical_errors) == 0, f"Critical validation errors in {entity.name}: {critical_errors}"

        # Validate complete cap table
        report = validator.validate_complete_cap_table(self.all_entities)

        # Should be valid overall
        assert report.is_valid, f"Cap table validation failed: {report}"

        # Should have correct entity counts
        assert report.summary['shareholders'] == 4
        assert report.summary['share_classes'] == 2
        assert report.summary['funding_rounds'] == 1

        # Step 2: Calculate individual ownership percentages
        alice = self.shareholders[0]
        alice_ownership = calculate_ownership_percentage(alice, self.context)

        # Alice should own 3.5M out of 15M total authorized = 23.33%
        expected_alice = 3500000 / 15000000
        assert abs(alice_ownership - expected_alice) < 0.001

        # Step 3: Calculate voting control
        alice_voting = calculate_voting_control(alice, self.context)

        # Alice should have 3.5M out of 11M voting shares = 31.82%
        total_voting_shares = 9000000 + 2000000  # Common + Series A
        expected_alice_voting = 3500000 / total_voting_shares
        assert abs(alice_voting - expected_alice_voting) < 0.001

        # Step 4: Generate comprehensive cap table summary
        summary = generate_cap_table_summary(self.all_entities, self.context)

        # Verify summary structure
        assert summary.total_shares_outstanding == 11000000  # Issued shares
        assert summary.fully_diluted_shares == 15000000  # Total authorized

        # Verify ownership breakdown
        assert len(summary.ownership_by_shareholder) == 4
        assert "Alice Johnson (Founder)" in summary.ownership_by_shareholder
        assert "Venture Capital Fund" in summary.ownership_by_shareholder

        # Verify ownership by class
        assert len(summary.ownership_by_class) == 2
        assert "common" in summary.ownership_by_class
        assert "series_a" in summary.ownership_by_class

        # Common should be ~60% (9M out of 15M)
        common_ownership = summary.ownership_by_class["common"]
        expected_common = 9000000 / 15000000
        assert abs(common_ownership - expected_common) < 0.001

        # Step 5: Test KPI calculations
        founder_ownership = get_founder_ownership_percentage(self.shareholders, self.share_classes)
        employee_ownership = get_employee_ownership_percentage(self.shareholders, self.share_classes)
        investor_ownership = get_investor_ownership_percentage(self.shareholders, self.share_classes)

        # Verify KPI totals add up to allocated shares (not 100% since there are unallocated authorized shares)
        total_ownership = founder_ownership + employee_ownership + investor_ownership
        # Total should be 11M out of 15M = 73.33%
        expected_total = 11000000 / 15000000
        assert abs(total_ownership - expected_total) < 0.01

        # Founders should own 46.67% (7M out of 15M)
        expected_founder = 7000000 / 15000000
        assert abs(founder_ownership - expected_founder) < 0.001

        # Employees should own 13.33% (2M out of 15M)
        expected_employee = 2000000 / 15000000
        assert abs(employee_ownership - expected_employee) < 0.001

        # Investors should own 13.33% (2M out of 15M)
        expected_investor = 2000000 / 15000000
        assert abs(investor_ownership - expected_investor) < 0.001

    def test_phase2_performance(self):
        """Test Phase 2 performance with larger cap table."""
        # Create larger cap table with 100 employees
        shareholders = []

        # Add founders
        shareholders.extend([
            Shareholder(
                type="shareholder",
                name="Founder 1",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Founder 2",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=3000000,
                share_class="common"
            )
        ])

        # Add 100 employees
        for i in range(100):
            shareholders.append(
                Shareholder(
                    type="shareholder",
                    name=f"Employee {i:03d}",
                    start_date=date(2021, 1, 1),
                    shareholder_type="employee",
                    total_shares=10000,
                    share_class="common"
                )
            )

        # Add investors
        shareholders.append(
            Shareholder(
                type="shareholder",
                name="Series A Investor",
                start_date=date(2021, 6, 1),
                shareholder_type="investor",
                total_shares=2000000,
                share_class="series_a"
            )
        )

        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date(2020, 1, 1),
                class_name="common",
                shares_authorized=12000000,
                shares_issued=8000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0,
                par_value=0.001
            ),
            ShareClass(
                type="share_class",
                name="Series A",
                start_date=date(2021, 6, 1),
                class_name="series_a",
                shares_authorized=3000000,
                shares_issued=2000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0,
                par_value=1.0
            )
        ]

        all_entities = shareholders + share_classes
        context = {'all_entities': all_entities}

        # Test performance
        import time

        start_time = time.time()

        # Validate
        validator = CapTableValidator()
        report = validator.validate_complete_cap_table(all_entities)

        # Calculate summary
        summary = generate_cap_table_summary(all_entities, context)

        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete in under 1 second for 103 shareholders
        assert execution_time < 1.0

        # Verify correct results
        assert report.is_valid
        assert len(summary.ownership_by_shareholder) == 103
        assert summary.total_shares_outstanding == 10000000  # 7M founders + 1M employees + 2M investor

    def test_phase2_error_handling(self):
        """Test Phase 2 error handling with invalid data."""
        # Test with empty entities
        empty_context = {'all_entities': []}

        summary = generate_cap_table_summary([], empty_context)
        assert summary.total_shares_outstanding == 0
        assert len(summary.ownership_by_shareholder) == 0

        # Test validation with problematic data
        validator = CapTableValidator()

        # Test with mismatched share class references
        invalid_shareholder = Shareholder(
            type="shareholder",
            name="Invalid Reference",
            start_date=date.today(),
            shareholder_type="founder",
            total_shares=1000000,
            share_class="nonexistent_class"
        )

        share_class = ShareClass(
            type="share_class",
            name="Common",
            start_date=date.today(),
            class_name="common",
            shares_authorized=10000000,
            shares_issued=5000000,
            liquidation_preference=1.0,
            voting_rights_per_share=1.0
        )

        entities = [invalid_shareholder, share_class]
        report = validator.validate_complete_cap_table(entities)

        # Should detect cross-entity reference error
        assert not report.is_valid
        assert len(report.errors) > 0

        # Should contain reference error
        ref_errors = [e for e in report.errors if "not found" in e.message]
        assert len(ref_errors) > 0


if __name__ == "__main__":
    pytest.main([__file__])
