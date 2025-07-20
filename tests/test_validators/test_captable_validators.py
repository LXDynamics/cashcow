"""Comprehensive tests for cap table validation engine."""

from datetime import date, timedelta

import pytest
from cashcow.models.captable import FundingRound, ShareClass, Shareholder
from cashcow.models.validators.captable_validators import (
    CapTableValidator,
    LiquidationPreferenceValidator,
    ShareMathValidator,
    ValidationError,
    ValidationReport,
    VotingRightsValidator,
)


class TestValidationError:
    """Test ValidationError data class."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError(
            entity_id="test_entity",
            entity_type="shareholder",
            field="total_shares",
            message="Test error message"
        )

        assert error.entity_id == "test_entity"
        assert error.entity_type == "shareholder"
        assert error.field == "total_shares"
        assert error.message == "Test error message"
        assert error.severity == "error"

    def test_validation_error_string_representation(self):
        """Test string representation of validation error."""
        error = ValidationError(
            entity_id="alice",
            entity_type="shareholder",
            field="total_shares",
            message="Must be positive",
            suggestion="Set to positive value"
        )

        result = str(error)
        assert "[ERROR]" in result
        assert "shareholder(alice)" in result
        assert "total_shares" in result
        assert "Must be positive" in result
        assert "Suggestion: Set to positive value" in result


class TestValidationReport:
    """Test ValidationReport data class."""

    def test_validation_report_creation(self):
        """Test creating validation report."""
        report = ValidationReport(
            is_valid=True,
            errors=[],
            warnings=[],
            info=[],
            summary={}
        )

        assert report.is_valid is True
        assert report.total_issues == 0

    def test_add_error_changes_validity(self):
        """Test that adding error changes validity."""
        report = ValidationReport(
            is_valid=True,
            errors=[],
            warnings=[],
            info=[],
            summary={}
        )

        error = ValidationError(
            entity_id="test",
            entity_type="test",
            field="test",
            message="Test error"
        )

        report.add_error(error)
        assert report.is_valid is False
        assert len(report.errors) == 1

    def test_add_warning_does_not_change_validity(self):
        """Test that adding warning doesn't change validity."""
        report = ValidationReport(
            is_valid=True,
            errors=[],
            warnings=[],
            info=[],
            summary={}
        )

        warning = ValidationError(
            entity_id="test",
            entity_type="test",
            field="test",
            message="Test warning",
            severity="warning"
        )

        report.add_error(warning)
        assert report.is_valid is True
        assert len(report.warnings) == 1


class TestShareMathValidator:
    """Test ShareMathValidator class."""

    def test_validate_ownership_totals_empty_list(self):
        """Test validation with empty shareholder list."""
        validator = ShareMathValidator()
        errors = validator.validate_ownership_totals([])
        assert len(errors) == 0

    def test_validate_ownership_totals_no_shares(self):
        """Test validation with shareholders having no shares."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=0,
                share_class="common"
            )
        ]

        validator = ShareMathValidator()
        errors = validator.validate_ownership_totals(shareholders)
        assert len(errors) == 1
        assert "No shares found" in errors[0].message

    def test_validate_ownership_totals_normal_case(self):
        """Test validation with normal ownership distribution."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=8000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Bob",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=2000000,
                share_class="common"
            )
        ]

        validator = ShareMathValidator()
        errors = validator.validate_ownership_totals(shareholders)
        assert len(errors) == 0

    def test_validate_ownership_totals_low_ownership(self):
        """Test validation with unusually low ownership (option pool scenario)."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=1000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Option Pool",
                start_date=date.today(),
                shareholder_type="option_pool",
                total_shares=9000000,
                share_class="common"
            )
        ]

        validator = ShareMathValidator()
        errors = validator.validate_ownership_totals(shareholders)
        # Should not generate errors for this case as it's a valid scenario with option pool
        assert len(errors) == 0

    def test_check_share_authorization_limits_valid(self):
        """Test share authorization validation with valid limits."""
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

        validator = ShareMathValidator()
        errors = validator.check_share_authorization_limits(share_classes)
        assert len(errors) == 0

    def test_check_share_authorization_limits_exceeded(self):
        """Test share authorization validation with exceeded limits."""
        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=12000000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            )
        ]

        validator = ShareMathValidator()
        errors = validator.check_share_authorization_limits(share_classes)
        assert len(errors) == 1
        assert "exceed authorized shares" in errors[0].message

    def test_check_share_authorization_limits_high_utilization(self):
        """Test share authorization validation with high utilization."""
        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=9800000,
                liquidation_preference=1.0,
                voting_rights_per_share=1.0
            )
        ]

        validator = ShareMathValidator()
        errors = validator.check_share_authorization_limits(share_classes)
        assert len(errors) == 1
        assert "very high" in errors[0].message
        assert errors[0].severity == "warning"


class TestLiquidationPreferenceValidator:
    """Test LiquidationPreferenceValidator class."""

    def test_validate_preference_stack_single_class(self):
        """Test preference stack validation with single class."""
        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=8000000,
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            )
        ]

        validator = LiquidationPreferenceValidator()
        errors = validator.validate_preference_stack(share_classes)
        assert len(errors) == 0

    def test_validate_preference_stack_gap_in_seniority(self):
        """Test preference stack validation with gap in seniority."""
        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today(),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=8000000,
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            ),
            ShareClass(
                type="share_class",
                name="Series A",
                start_date=date.today(),
                class_name="series_a",
                shares_authorized=2000000,
                shares_issued=2000000,
                liquidation_preference=1.0,
                liquidation_seniority=3,  # Gap from 1 to 3
                voting_rights_per_share=1.0
            )
        ]

        validator = LiquidationPreferenceValidator()
        errors = validator.validate_preference_stack(share_classes)
        assert len(errors) == 1
        assert "Gap in liquidation seniority" in errors[0].message

    def test_check_participating_rights_consistency_invalid_cap(self):
        """Test participating rights validation with invalid cap."""
        share_classes = [
            ShareClass(
                type="share_class",
                name="Series A",
                start_date=date.today(),
                class_name="series_a",
                shares_authorized=2000000,
                shares_issued=2000000,
                liquidation_preference=2.0,
                participating=True,
                participation_cap=1.5,  # Cap less than preference
                voting_rights_per_share=1.0
            )
        ]

        validator = LiquidationPreferenceValidator()
        errors = validator.check_participating_rights_consistency(share_classes)
        assert len(errors) == 1
        assert "less than liquidation preference" in errors[0].message


class TestVotingRightsValidator:
    """Test VotingRightsValidator class."""

    def test_validate_voting_rights_total_empty_list(self):
        """Test voting rights validation with empty list."""
        validator = VotingRightsValidator()
        errors = validator.validate_voting_rights_total([])
        assert len(errors) == 0

    def test_validate_voting_rights_total_no_voting_power(self):
        """Test voting rights validation with no voting power."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=0,
                share_class="common"
            )
        ]

        validator = VotingRightsValidator()
        errors = validator.validate_voting_rights_total(shareholders)
        assert len(errors) == 1
        assert "No voting power found" in errors[0].message

    def test_validate_voting_rights_total_majority_control(self):
        """Test voting rights validation with majority control."""
        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=6000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Bob",
                start_date=date.today(),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            )
        ]

        validator = VotingRightsValidator()
        errors = validator.validate_voting_rights_total(shareholders)
        assert len(errors) == 1
        assert "majority control" in errors[0].message
        assert errors[0].severity == "info"


class TestCapTableValidator:
    """Test main CapTableValidator class."""

    def setUp(self):
        """Set up test data."""
        self.validator = CapTableValidator()

        # Create valid test entities
        self.valid_shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice Johnson",
                start_date=date.today() - timedelta(days=365),
                shareholder_type="founder",
                total_shares=8000000,
                share_class="common",
                share_price=0.001
            ),
            Shareholder(
                type="shareholder",
                name="Bob Smith",
                start_date=date.today() - timedelta(days=365),
                shareholder_type="founder",
                total_shares=2000000,
                share_class="common",
                share_price=0.001
            )
        ]

        self.valid_share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date.today() - timedelta(days=365),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=10000000,
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            )
        ]

        self.valid_funding_rounds = []
        self.valid_investments = []

    def test_validate_entity_consistency_valid_shareholder(self):
        """Test entity consistency validation with valid shareholder."""
        self.setUp()

        errors = self.validator.validate_entity_consistency(self.valid_shareholders[0])
        assert len(errors) == 0

    def test_validate_entity_consistency_invalid_shareholder(self):
        """Test entity consistency validation with invalid shareholder."""
        self.setUp()

        # Test with Pydantic validation bypass - create a mock with invalid data
        # Since Pydantic already validates at model level, we test validation logic directly
        from unittest.mock import Mock

        invalid_shareholder = Mock()
        invalid_shareholder.name = "Invalid Shareholder"
        invalid_shareholder.type = "shareholder"
        invalid_shareholder.total_shares = -1000000  # Invalid negative shares
        invalid_shareholder.purchase_price_per_share = -1.0  # Invalid negative price
        invalid_shareholder.acquisition_date = None
        invalid_shareholder.cliff_months = 0
        invalid_shareholder.board_seats = 0

        errors = self.validator._validate_shareholder(invalid_shareholder)
        assert len(errors) >= 2  # Should have errors for negative shares and price

        # Check specific errors
        share_error = next((e for e in errors if "total_shares" in e.field), None)
        assert share_error is not None
        assert "must be positive" in share_error.message

        price_error = next((e for e in errors if "purchase_price_per_share" in e.field), None)
        assert price_error is not None
        assert "must be positive" in price_error.message

    def test_validate_entity_consistency_valid_share_class(self):
        """Test entity consistency validation with valid share class."""
        self.setUp()

        errors = self.validator.validate_entity_consistency(self.valid_share_classes[0])
        assert len(errors) == 0

    def test_validate_entity_consistency_invalid_share_class(self):
        """Test entity consistency validation with invalid share class."""
        invalid_share_class = ShareClass(
            type="share_class",
            name="Invalid Share Class",
            start_date=date.today(),
            class_name="invalid",
            shares_authorized=-1000000,  # Invalid negative authorized
            shares_issued=2000000,
            liquidation_preference=-1.0,  # Invalid negative preference
            voting_rights_per_share=-1.0,  # Invalid negative voting rights
            anti_dilution_provision="invalid_provision"  # Invalid provision
        )

        errors = self.validator.validate_entity_consistency(invalid_share_class)
        assert len(errors) >= 4  # Should have multiple errors

        # Check for specific errors
        auth_error = next((e for e in errors if "shares_authorized" in e.field), None)
        assert auth_error is not None

        pref_error = next((e for e in errors if "liquidation_preference" in e.field), None)
        assert pref_error is not None

        voting_error = next((e for e in errors if "voting_rights_per_share" in e.field), None)
        assert voting_error is not None

        antidilution_error = next((e for e in errors if "anti_dilution_provision" in e.field), None)
        assert antidilution_error is not None

    def test_validate_entity_consistency_valid_funding_round(self):
        """Test entity consistency validation with valid funding round."""
        funding_round = FundingRound(
            type="funding_round",
            name="Seed Round",
            start_date=date.today(),
            round_type="seed",
            amount_raised=1000000.0,
            shares_issued=1000000,
            price_per_share=1.0,
            pre_money_valuation=9000000.0,
            post_money_valuation=10000000.0,
            share_class="series_seed"
        )

        errors = self.validator.validate_entity_consistency(funding_round)
        assert len(errors) == 0

    def test_validate_entity_consistency_invalid_funding_round_math(self):
        """Test entity consistency validation with invalid funding round math."""
        funding_round = FundingRound(
            type="funding_round",
            name="Invalid Seed Round",
            start_date=date.today(),
            round_type="seed",
            investment_amount=1000000.0,
            shares_issued=1000000,
            price_per_share=1.0,
            pre_money_valuation=9000000.0,
            post_money_valuation=12000000.0,  # Incorrect post-money (should be 10M)
            share_class="series_seed"
        )

        errors = self.validator.validate_entity_consistency(funding_round)
        assert len(errors) >= 1

        # Check for post-money validation error
        post_money_error = next((e for e in errors if "post_money_valuation" in e.field), None)
        assert post_money_error is not None
        assert "doesn't match pre-money + investment" in post_money_error.message

    def test_validate_complete_cap_table_valid(self):
        """Test complete cap table validation with valid entities."""
        self.setUp()

        all_entities = (
            self.valid_shareholders +
            self.valid_share_classes +
            self.valid_funding_rounds +
            self.valid_investments
        )

        report = self.validator.validate_complete_cap_table(all_entities)

        assert report.is_valid is True
        assert len(report.errors) == 0
        assert report.summary['total_entities'] == len(all_entities)
        assert report.summary['shareholders'] == len(self.valid_shareholders)
        assert report.summary['share_classes'] == len(self.valid_share_classes)

    def test_validate_complete_cap_table_cross_entity_errors(self):
        """Test complete cap table validation with cross-entity reference errors."""
        self.setUp()

        # Create shareholder with invalid share class reference
        invalid_shareholder = Shareholder(
            type="shareholder",
            name="Invalid Reference",
            start_date=date.today(),
            shareholder_type="founder",
            total_shares=1000000,
            share_class="nonexistent_class"  # Invalid reference
        )

        all_entities = (
            self.valid_shareholders +
            [invalid_shareholder] +
            self.valid_share_classes
        )

        report = self.validator.validate_complete_cap_table(all_entities)

        assert report.is_valid is False
        assert len(report.errors) >= 1

        # Check for cross-entity reference error
        ref_error = next((e for e in report.errors if "not found" in e.message), None)
        assert ref_error is not None

    def test_generate_validation_report(self):
        """Test validation report generation."""
        self.setUp()

        all_entities = self.valid_shareholders + self.valid_share_classes

        report = self.validator.generate_validation_report(all_entities)

        assert isinstance(report, ValidationReport)
        assert report.is_valid is True
        assert 'total_entities' in report.summary

        # Test string representation
        report_str = str(report)
        assert "Cap Table Validation Report" in report_str
        assert "✓ VALID" in report_str


class TestIntegrationScenarios:
    """Test integration scenarios with complex cap table structures."""

    def test_complex_cap_table_validation(self):
        """Test validation of complex cap table with multiple rounds."""
        # Create complex cap table structure
        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date(2020, 1, 1),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=8000000,
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            ),
            ShareClass(
                type="share_class",
                name="Series A Preferred",
                start_date=date(2021, 6, 1),
                class_name="series_a",
                shares_authorized=2000000,
                shares_issued=2000000,
                liquidation_preference=1.0,
                liquidation_seniority=2,
                participating=True,
                voting_rights_per_share=1.0,
                convertible=True,
                conversion_price=1.0,
                anti_dilution_provision="weighted_average_broad"
            )
        ]

        shareholders = [
            Shareholder(
                type="shareholder",
                name="Alice Johnson",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common",
                vesting_start_date=date(2020, 1, 1),
                vesting_cliff_months=12,
                vesting_period_months=48
            ),
            Shareholder(
                type="shareholder",
                name="Bob Smith",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common",
                vesting_start_date=date(2020, 1, 1),
                vesting_cliff_months=12,
                vesting_period_months=48
            ),
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

        funding_rounds = [
            FundingRound(
                type="funding_round",
                name="Series A",
                start_date=date(2021, 6, 1),
                round_type="series_a",
                investment_amount=2000000.0,
                shares_issued=2000000,
                price_per_share=1.0,
                pre_money_valuation=8000000.0,
                post_money_valuation=10000000.0,
                share_class="series_a"
            )
        ]

        all_entities = shareholders + share_classes + funding_rounds

        validator = CapTableValidator()
        report = validator.validate_complete_cap_table(all_entities)

        # Should be valid complex cap table
        assert report.is_valid is True
        assert report.summary['shareholders'] == 3
        assert report.summary['share_classes'] == 2
        assert report.summary['funding_rounds'] == 1

    def test_down_round_scenario(self):
        """Test validation of down round scenario."""
        funding_rounds = [
            FundingRound(
                type="funding_round",
                name="Series A",
                start_date=date(2021, 6, 1),
                round_type="series_a",
                investment_amount=2000000.0,
                shares_issued=2000000,
                price_per_share=1.0,
                pre_money_valuation=8000000.0,
                post_money_valuation=10000000.0,
                share_class="series_a"
            ),
            FundingRound(
                type="funding_round",
                name="Series B (Down Round)",
                start_date=date(2022, 6, 1),
                round_type="series_b",
                investment_amount=1000000.0,
                shares_issued=2500000,  # More shares for same amount
                price_per_share=0.4,  # Significant price drop
                pre_money_valuation=2000000.0,  # Down valuation
                post_money_valuation=3000000.0,
                share_class="series_b"
            )
        ]

        validator = CapTableValidator()

        # Test dilution calculations validation
        errors = validator.share_math_validator.verify_dilution_calculations(funding_rounds)

        # Should generate warnings about down round
        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) >= 1

        # Check for valuation warning
        valuation_warning = next((w for w in warnings if "down round" in w.message), None)
        assert valuation_warning is not None

        # Check for price warning
        price_warning = next((w for w in warnings if "significantly lower" in w.message), None)
        assert price_warning is not None


class TestPerformanceScenarios:
    """Test performance with large cap tables."""

    def test_large_cap_table_performance(self):
        """Test validation performance with large number of shareholders."""
        # Create large number of shareholders (simulating employee option pool)
        shareholders = []
        for i in range(1000):
            shareholders.append(
                Shareholder(
                    type="shareholder",
                    name=f"Employee {i:04d}",
                    start_date=date(2021, 1, 1),
                    shareholder_type="employee",
                    total_shares=1000,  # Small option grants
                    share_class="common"
                )
            )

        # Add founders
        shareholders.extend([
            Shareholder(
                type="shareholder",
                name="Founder Alice",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            ),
            Shareholder(
                type="shareholder",
                name="Founder Bob",
                start_date=date(2020, 1, 1),
                shareholder_type="founder",
                total_shares=4000000,
                share_class="common"
            )
        ])

        share_classes = [
            ShareClass(
                type="share_class",
                name="Common Stock",
                start_date=date(2020, 1, 1),
                class_name="common",
                shares_authorized=10000000,
                shares_issued=9000000,  # Including employee options
                liquidation_preference=1.0,
                liquidation_seniority=1,
                voting_rights_per_share=1.0
            )
        ]

        all_entities = shareholders + share_classes

        validator = CapTableValidator()

        # Measure validation time
        import time
        start_time = time.time()
        report = validator.validate_complete_cap_table(all_entities)
        end_time = time.time()

        validation_time = end_time - start_time

        # Should complete validation in reasonable time (< 1 second for this test)
        assert validation_time < 1.0
        assert report.summary['shareholders'] == 1002
        assert report.summary['total_entities'] == 1003

        # Should handle large cap table without errors
        assert len(report.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__])
