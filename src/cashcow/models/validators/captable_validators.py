"""Cap table validation engine for data integrity and consistency checks."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..base import BaseEntity
from ..captable import FundingRound, ShareClass, Shareholder
from ..entities import Investment


@dataclass
class ValidationError:
    """Represents a validation error with context."""

    entity_id: Optional[str]
    entity_type: Optional[str]
    field: Optional[str]
    message: str
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """String representation of validation error."""
        prefix = f"[{self.severity.upper()}]"
        if self.entity_type and self.entity_id:
            prefix += f" {self.entity_type}({self.entity_id})"
        if self.field:
            prefix += f".{self.field}"

        result = f"{prefix}: {self.message}"
        if self.suggestion:
            result += f" Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationReport:
    """Comprehensive validation report for cap table analysis."""

    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    info: List[ValidationError]
    summary: Dict[str, Any]

    def __post_init__(self):
        """Post-init processing."""
        if not hasattr(self, 'errors'):
            self.errors = []
        if not hasattr(self, 'warnings'):
            self.warnings = []
        if not hasattr(self, 'info'):
            self.info = []
        if not hasattr(self, 'summary'):
            self.summary = {}

    @property
    def total_issues(self) -> int:
        """Total number of validation issues."""
        return len(self.errors) + len(self.warnings) + len(self.info)

    def add_error(self, error: ValidationError) -> None:
        """Add validation error."""
        if error.severity == "error":
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == "warning":
            self.warnings.append(error)
        else:
            self.info.append(error)

    def __str__(self) -> str:
        """String representation of validation report."""
        lines = []
        lines.append("Cap Table Validation Report")
        lines.append(f"Status: {'✓ VALID' if self.is_valid else '✗ INVALID'}")
        lines.append(f"Issues: {len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.info)} info")
        lines.append("")

        for error in self.errors:
            lines.append(str(error))
        for warning in self.warnings:
            lines.append(str(warning))
        for info in self.info:
            lines.append(str(info))

        if self.summary:
            lines.append("")
            lines.append("Summary:")
            for key, value in self.summary.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)


class CapTableValidator:
    """Main validation coordinator for cap table entities."""

    OWNERSHIP_TOLERANCE = Decimal('0.0001')  # 0.01% tolerance for ownership calculations

    def __init__(self):
        """Initialize cap table validator."""
        self.share_math_validator = ShareMathValidator()
        self.liquidation_validator = LiquidationPreferenceValidator()
        self.voting_validator = VotingRightsValidator()

    def validate_complete_cap_table(self, entities: List[BaseEntity]) -> ValidationReport:
        """Validate complete cap table with all entities.

        Args:
            entities: List of all cap table entities

        Returns:
            Comprehensive validation report
        """
        report = ValidationReport(is_valid=True, errors=[], warnings=[], info=[], summary={})

        # Separate entities by type
        shareholders = [e for e in entities if isinstance(e, Shareholder)]
        share_classes = [e for e in entities if isinstance(e, ShareClass)]
        funding_rounds = [e for e in entities if isinstance(e, FundingRound)]
        investments = [e for e in entities if isinstance(e, Investment)]

        # Generate summary statistics
        report.summary = {
            'total_entities': len(entities),
            'shareholders': len(shareholders),
            'share_classes': len(share_classes),
            'funding_rounds': len(funding_rounds),
            'investments': len(investments),
        }

        # Validate individual entity consistency
        for entity in entities:
            entity_errors = self.validate_entity_consistency(entity)
            for error in entity_errors:
                report.add_error(error)

        # Validate cross-entity consistency
        cross_entity_errors = self._validate_cross_entity_consistency(
            shareholders, share_classes, funding_rounds, investments
        )
        for error in cross_entity_errors:
            report.add_error(error)

        # Run specialized validators
        share_math_errors = self.share_math_validator.validate_ownership_totals(shareholders)
        for error in share_math_errors:
            report.add_error(error)

        liquidation_errors = self.liquidation_validator.validate_preference_stack(share_classes)
        for error in liquidation_errors:
            report.add_error(error)

        voting_errors = self.voting_validator.validate_voting_rights_total(shareholders)
        for error in voting_errors:
            report.add_error(error)

        return report

    def validate_entity_consistency(self, entity: BaseEntity) -> List[ValidationError]:
        """Validate individual entity for internal consistency.

        Args:
            entity: Entity to validate

        Returns:
            List of validation errors
        """
        errors = []

        if isinstance(entity, Shareholder):
            errors.extend(self._validate_shareholder(entity))
        elif isinstance(entity, ShareClass):
            errors.extend(self._validate_share_class(entity))
        elif isinstance(entity, FundingRound):
            errors.extend(self._validate_funding_round(entity))
        elif isinstance(entity, Investment):
            errors.extend(self._validate_investment(entity))

        return errors

    def generate_validation_report(self, entities: List[BaseEntity]) -> ValidationReport:
        """Generate comprehensive validation report.

        Args:
            entities: List of entities to validate

        Returns:
            Detailed validation report
        """
        return self.validate_complete_cap_table(entities)

    def _validate_shareholder(self, shareholder: Shareholder) -> List[ValidationError]:
        """Validate shareholder entity."""
        errors = []

        # Basic field validation
        if shareholder.total_shares <= 0:
            errors.append(ValidationError(
                entity_id=shareholder.name,
                entity_type="shareholder",
                field="total_shares",
                message="Total shares must be positive",
                suggestion="Set total_shares to a positive integer"
            ))

        if shareholder.purchase_price_per_share is not None and shareholder.purchase_price_per_share <= 0:
            errors.append(ValidationError(
                entity_id=shareholder.name,
                entity_type="shareholder",
                field="purchase_price_per_share",
                message="Purchase price per share must be positive",
                suggestion="Set purchase_price_per_share to a positive value or null"
            ))

        # Vesting validation - check if the shareholder has acquisition_date to compare with
        if hasattr(shareholder, 'acquisition_date') and shareholder.acquisition_date and shareholder.acquisition_date < shareholder.start_date:
            errors.append(ValidationError(
                entity_id=shareholder.name,
                entity_type="shareholder",
                field="acquisition_date",
                message="Acquisition date cannot be before shareholder start date",
                suggestion="Align acquisition date with or after shareholder start date"
            ))

        if shareholder.cliff_months and shareholder.cliff_months < 0:
            errors.append(ValidationError(
                entity_id=shareholder.name,
                entity_type="shareholder",
                field="cliff_months",
                message="Vesting cliff months cannot be negative",
                suggestion="Set to 0 for no cliff or positive value for cliff period"
            ))

        # Board seats validation
        if shareholder.board_seats and shareholder.board_seats < 0:
            errors.append(ValidationError(
                entity_id=shareholder.name,
                entity_type="shareholder",
                field="board_seats",
                message="Board seats cannot be negative",
                suggestion="Set to 0 for no board seats or positive value"
            ))

        return errors

    def _validate_share_class(self, share_class: ShareClass) -> List[ValidationError]:
        """Validate share class entity."""
        errors = []

        # Basic field validation
        if share_class.shares_authorized <= 0:
            errors.append(ValidationError(
                entity_id=share_class.name,
                entity_type="share_class",
                field="shares_authorized",
                message="Authorized shares must be positive",
                suggestion="Set shares_authorized to a positive integer"
            ))

        if share_class.liquidation_preference <= 0:
            errors.append(ValidationError(
                entity_id=share_class.name,
                entity_type="share_class",
                field="liquidation_preference",
                message="Liquidation preference must be positive",
                suggestion="Set liquidation_preference to 1.0 for standard preference"
            ))

        # Voting rights validation
        if share_class.voting_rights_per_share < 0:
            errors.append(ValidationError(
                entity_id=share_class.name,
                entity_type="share_class",
                field="voting_rights_per_share",
                message="Voting rights per share cannot be negative",
                suggestion="Set to 0 for non-voting shares or positive value"
            ))

        # Conversion validation
        if share_class.conversion_ratio is not None and share_class.conversion_ratio <= 0:
            errors.append(ValidationError(
                entity_id=share_class.name,
                entity_type="share_class",
                field="conversion_ratio",
                message="Conversion ratio must be positive",
                suggestion="Set conversion_ratio to positive value or null if not convertible"
            ))

        # Anti-dilution validation
        valid_antidilution = {"none", "weighted_average_broad", "weighted_average_narrow", "full_ratchet", None}
        if share_class.anti_dilution_provision not in valid_antidilution:
            errors.append(ValidationError(
                entity_id=share_class.name,
                entity_type="share_class",
                field="anti_dilution_provision",
                message=f"Invalid anti-dilution provision: {share_class.anti_dilution_provision}",
                suggestion=f"Use one of: {', '.join(valid_antidilution)}"
            ))

        return errors

    def _validate_funding_round(self, funding_round: FundingRound) -> List[ValidationError]:
        """Validate funding round entity."""
        errors = []

        # Basic field validation
        if funding_round.amount_raised <= 0:
            errors.append(ValidationError(
                entity_id=funding_round.name,
                entity_type="funding_round",
                field="amount_raised",
                message="Amount raised must be positive",
                suggestion="Set amount_raised to a positive value"
            ))

        if funding_round.shares_issued is not None and funding_round.shares_issued <= 0:
            errors.append(ValidationError(
                entity_id=funding_round.name,
                entity_type="funding_round",
                field="shares_issued",
                message="Shares issued must be positive",
                suggestion="Set shares_issued to a positive integer"
            ))

        if funding_round.price_per_share is not None and funding_round.price_per_share <= 0:
            errors.append(ValidationError(
                entity_id=funding_round.name,
                entity_type="funding_round",
                field="price_per_share",
                message="Price per share must be positive",
                suggestion="Set price_per_share to a positive value"
            ))

        # Valuation validation
        if funding_round.pre_money_valuation is not None and funding_round.pre_money_valuation <= 0:
            errors.append(ValidationError(
                entity_id=funding_round.name,
                entity_type="funding_round",
                field="pre_money_valuation",
                message="Pre-money valuation must be positive",
                suggestion="Set pre_money_valuation to a positive value"
            ))

        if funding_round.post_money_valuation is not None and funding_round.post_money_valuation <= 0:
            errors.append(ValidationError(
                entity_id=funding_round.name,
                entity_type="funding_round",
                field="post_money_valuation",
                message="Post-money valuation must be positive",
                suggestion="Set post_money_valuation to a positive value"
            ))

        # Math consistency validation
        if all([funding_round.pre_money_valuation, funding_round.post_money_valuation]):
            expected_post_money = funding_round.pre_money_valuation + funding_round.amount_raised
            if abs(funding_round.post_money_valuation - expected_post_money) > 1000:
                errors.append(ValidationError(
                    entity_id=funding_round.name,
                    entity_type="funding_round",
                    field="post_money_valuation",
                    message=f"Post-money valuation {funding_round.post_money_valuation:,.2f} doesn't match pre-money + investment ({expected_post_money:,.2f})",
                    suggestion="Ensure post_money_valuation = pre_money_valuation + amount_raised"
                ))

        if all([funding_round.shares_issued, funding_round.price_per_share]):
            expected_shares_value = funding_round.shares_issued * funding_round.price_per_share
            if abs(funding_round.amount_raised - expected_shares_value) > 1000:
                errors.append(ValidationError(
                    entity_id=funding_round.name,
                    entity_type="funding_round",
                    field="amount_raised",
                    message=f"Amount raised {funding_round.amount_raised:,.2f} doesn't match shares × price ({expected_shares_value:,.2f})",
                    suggestion="Ensure amount_raised = shares_issued × price_per_share"
                ))

        return errors

    def _validate_investment(self, investment: Investment) -> List[ValidationError]:
        """Validate investment entity with cap table extensions."""
        errors = []

        # Basic investment validation
        if investment.amount <= 0:
            errors.append(ValidationError(
                entity_id=investment.name,
                entity_type="investment",
                field="amount",
                message="Investment amount must be positive",
                suggestion="Set amount to a positive value"
            ))

        # Cap table field validation
        if investment.shares_issued is not None and investment.shares_issued <= 0:
            errors.append(ValidationError(
                entity_id=investment.name,
                entity_type="investment",
                field="shares_issued",
                message="Shares issued must be positive",
                suggestion="Set shares_issued to a positive integer or null"
            ))

        if investment.price_per_share is not None and investment.price_per_share <= 0:
            errors.append(ValidationError(
                entity_id=investment.name,
                entity_type="investment",
                field="price_per_share",
                message="Price per share must be positive",
                suggestion="Set price_per_share to a positive value or null"
            ))

        if investment.liquidation_preference is not None and investment.liquidation_preference <= 0:
            errors.append(ValidationError(
                entity_id=investment.name,
                entity_type="investment",
                field="liquidation_preference",
                message="Liquidation preference must be positive",
                suggestion="Set liquidation_preference to 1.0 or higher"
            ))

        # Math consistency for cap table fields
        if all([investment.shares_issued, investment.price_per_share]):
            expected_amount = investment.shares_issued * investment.price_per_share
            if abs(investment.amount - expected_amount) > 1000:
                errors.append(ValidationError(
                    entity_id=investment.name,
                    entity_type="investment",
                    field="amount",
                    message=f"Investment amount {investment.amount:,.2f} doesn't match shares × price ({expected_amount:,.2f})",
                    suggestion="Ensure amount = shares_issued × price_per_share"
                ))

        return errors

    def _validate_cross_entity_consistency(
        self,
        shareholders: List[Shareholder],
        share_classes: List[ShareClass],
        funding_rounds: List[FundingRound],
        investments: List[Investment]
    ) -> List[ValidationError]:
        """Validate consistency across different entity types."""
        errors = []

        # Create lookup maps
        share_class_names = {sc.class_name for sc in share_classes}
        shareholder_names = {sh.name for sh in shareholders}

        # Validate shareholder share class references
        for shareholder in shareholders:
            if shareholder.share_class not in share_class_names:
                errors.append(ValidationError(
                    entity_id=shareholder.name,
                    entity_type="shareholder",
                    field="share_class",
                    message=f"Referenced share class '{shareholder.share_class}' not found",
                    suggestion=f"Create share class '{shareholder.share_class}' or update reference"
                ))

        # Validate funding round share class references
        for funding_round in funding_rounds:
            if funding_round.share_class not in share_class_names:
                errors.append(ValidationError(
                    entity_id=funding_round.name,
                    entity_type="funding_round",
                    field="share_class",
                    message=f"Referenced share class '{funding_round.share_class}' not found",
                    suggestion=f"Create share class '{funding_round.share_class}' or update reference"
                ))

        # Validate investment to funding round conversions
        for investment in investments:
            if hasattr(investment, 'share_class') and investment.share_class:
                if investment.share_class not in share_class_names:
                    errors.append(ValidationError(
                        entity_id=investment.name,
                        entity_type="investment",
                        field="share_class",
                        message=f"Referenced share class '{investment.share_class}' not found",
                        suggestion=f"Create share class '{investment.share_class}' or update reference"
                    ))

        return errors


class ShareMathValidator:
    """Mathematical consistency validator for share calculations."""

    def validate_ownership_totals(self, shareholders: List[Shareholder]) -> List[ValidationError]:
        """Validate that ownership percentages sum correctly.

        Args:
            shareholders: List of shareholders to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not shareholders:
            return errors

        # Calculate total shares by class
        shares_by_class = {}
        for shareholder in shareholders:
            class_name = shareholder.share_class
            if class_name not in shares_by_class:
                shares_by_class[class_name] = 0
            shares_by_class[class_name] += shareholder.total_shares

        # Calculate ownership percentages
        total_shares_all_classes = sum(shares_by_class.values())
        if total_shares_all_classes == 0:
            errors.append(ValidationError(
                entity_id=None,
                entity_type="share_math",
                field="total_shares",
                message="No shares found across all shareholders",
                severity="warning",
                suggestion="Add shareholders with positive share counts"
            ))
            return errors

        # Validate that ownership sums to reasonable total (allowing for option pools)
        calculated_ownership = Decimal('0')
        for shareholder in shareholders:
            ownership_pct = Decimal(str(shareholder.total_shares)) / Decimal(str(total_shares_all_classes))
            calculated_ownership += ownership_pct

        # Allow for some deviation due to option pools and rounding
        if calculated_ownership < Decimal('0.8'):
            errors.append(ValidationError(
                entity_id=None,
                entity_type="share_math",
                field="ownership_total",
                message=f"Total ownership {calculated_ownership:.2%} is unusually low - possible missing shareholders",
                severity="warning",
                suggestion="Verify all shareholders are included, including option pools"
            ))
        elif calculated_ownership > Decimal('1.05'):
            errors.append(ValidationError(
                entity_id=None,
                entity_type="share_math",
                field="ownership_total",
                message=f"Total ownership {calculated_ownership:.2%} exceeds 100% - possible double counting",
                severity="error",
                suggestion="Check for duplicate shareholders or incorrect share counts"
            ))

        return errors

    def check_share_authorization_limits(self, share_classes: List[ShareClass]) -> List[ValidationError]:
        """Validate that issued shares don't exceed authorized shares.

        Args:
            share_classes: List of share classes to validate

        Returns:
            List of validation errors
        """
        errors = []

        for share_class in share_classes:
            if share_class.shares_issued > share_class.shares_authorized:
                errors.append(ValidationError(
                    entity_id=share_class.name,
                    entity_type="share_class",
                    field="shares_issued",
                    message=f"Issued shares ({share_class.shares_issued:,}) exceed authorized shares ({share_class.shares_authorized:,})",
                    suggestion="Increase authorized shares or reduce issued shares"
                ))

            utilization = share_class.shares_issued / share_class.shares_authorized
            if utilization > 0.95:
                errors.append(ValidationError(
                    entity_id=share_class.name,
                    entity_type="share_class",
                    field="shares_issued",
                    message=f"Share class utilization {utilization:.1%} is very high",
                    severity="warning",
                    suggestion="Consider increasing authorized shares for future growth"
                ))

        return errors

    def verify_dilution_calculations(self, rounds: List[FundingRound]) -> List[ValidationError]:
        """Verify dilution calculations across funding rounds.

        Args:
            rounds: List of funding rounds to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Sort rounds by date for chronological validation
        sorted_rounds = sorted(rounds, key=lambda r: r.start_date)

        prev_valuation = None
        for i, round_data in enumerate(sorted_rounds):
            # Check for valuation progression (allowing for down rounds)
            if prev_valuation and round_data.pre_money_valuation < prev_valuation * 0.5:
                errors.append(ValidationError(
                    entity_id=round_data.name,
                    entity_type="funding_round",
                    field="pre_money_valuation",
                    message=f"Pre-money valuation {round_data.pre_money_valuation:,.0f} represents significant down round",
                    severity="warning",
                    suggestion="Verify valuation is correct and consider anti-dilution provisions"
                ))

            # Check share price progression
            if i > 0:
                prev_round = sorted_rounds[i-1]
                if round_data.price_per_share < prev_round.price_per_share * 0.8:
                    errors.append(ValidationError(
                        entity_id=round_data.name,
                        entity_type="funding_round",
                        field="price_per_share",
                        message=f"Share price {round_data.price_per_share:.2f} is significantly lower than previous round",
                        severity="warning",
                        suggestion="Verify pricing and consider anti-dilution impact"
                    ))

            prev_valuation = round_data.post_money_valuation

        return errors


class LiquidationPreferenceValidator:
    """Validator for liquidation preference consistency."""

    def validate_preference_stack(self, share_classes: List[ShareClass]) -> List[ValidationError]:
        """Validate liquidation preference stack consistency.

        Args:
            share_classes: List of share classes to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Group by liquidation seniority (use default seniority if not specified)
        preference_groups = {}
        for share_class in share_classes:
            seniority = getattr(share_class, 'liquidation_seniority', 1)  # Default to seniority 1
            if seniority not in preference_groups:
                preference_groups[seniority] = []
            preference_groups[seniority].append(share_class)

        # Validate seniority ordering
        seniorities = sorted(preference_groups.keys())
        for i, seniority in enumerate(seniorities):
            if i > 0 and seniority != seniorities[i-1] + 1:
                errors.append(ValidationError(
                    entity_id=None,
                    entity_type="liquidation_preference",
                    field="liquidation_seniority",
                    message=f"Gap in liquidation seniority between {seniorities[i-1]} and {seniority}",
                    severity="warning",
                    suggestion="Consider consolidating seniority levels"
                ))

        return errors

    def check_participating_rights_consistency(self, preferences: List[ShareClass]) -> List[ValidationError]:
        """Validate participating rights consistency.

        Args:
            preferences: List of share classes with participating rights

        Returns:
            List of validation errors
        """
        errors = []

        for share_class in preferences:
            if share_class.participating and share_class.participation_cap:
                if share_class.participation_cap < share_class.liquidation_preference:
                    errors.append(ValidationError(
                        entity_id=share_class.name,
                        entity_type="share_class",
                        field="participation_cap",
                        message=f"Participation cap {share_class.participation_cap}x is less than liquidation preference {share_class.liquidation_preference}x",
                        suggestion="Set participation cap >= liquidation preference"
                    ))

        return errors

    def verify_conversion_rights(self, share_classes: List[ShareClass]) -> List[ValidationError]:
        """Verify conversion rights consistency.

        Args:
            share_classes: List of share classes to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Find common stock class for conversion validation
        common_classes = [sc for sc in share_classes if 'common' in sc.class_name.lower()]

        for share_class in share_classes:
            if share_class.convertible and share_class.conversion_price:
                # Validate conversion makes economic sense
                if not common_classes:
                    errors.append(ValidationError(
                        entity_id=share_class.name,
                        entity_type="share_class",
                        field="convertible",
                        message="Convertible share class found but no common stock class exists",
                        severity="warning",
                        suggestion="Create common stock class for conversion target"
                    ))

        return errors


class VotingRightsValidator:
    """Validator for voting rights consistency."""

    def validate_voting_rights_total(self, shareholders: List[Shareholder]) -> List[ValidationError]:
        """Validate voting rights distribution.

        Args:
            shareholders: List of shareholders to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not shareholders:
            return errors

        # Calculate total voting power
        total_voting_power = sum(
            shareholder.total_shares * getattr(shareholder, 'voting_rights_per_share', 1.0)
            for shareholder in shareholders
        )

        if total_voting_power == 0:
            errors.append(ValidationError(
                entity_id=None,
                entity_type="voting_rights",
                field="total_voting_power",
                message="No voting power found across all shareholders",
                severity="warning",
                suggestion="Verify shareholders have voting rights"
            ))

        # Check for voting control concentration
        voting_powers = []
        for shareholder in shareholders:
            voting_power = shareholder.total_shares * getattr(shareholder, 'voting_rights_per_share', 1.0)
            voting_percentage = voting_power / total_voting_power if total_voting_power > 0 else 0
            voting_powers.append((shareholder.name, voting_percentage))

        # Sort by voting power
        voting_powers.sort(key=lambda x: x[1], reverse=True)

        # Check for majority control
        if voting_powers and voting_powers[0][1] > 0.5:
            errors.append(ValidationError(
                entity_id=voting_powers[0][0],
                entity_type="voting_rights",
                field="voting_control",
                message=f"Shareholder {voting_powers[0][0]} has majority control ({voting_powers[0][1]:.1%})",
                severity="info",
                suggestion="Consider if majority control is intended"
            ))

        return errors

    def check_board_control_math(self, shareholders: List[Shareholder]) -> List[ValidationError]:
        """Validate board control calculations.

        Args:
            shareholders: List of shareholders to validate

        Returns:
            List of validation errors
        """
        errors = []

        total_board_seats = sum(
            getattr(shareholder, 'board_seats', 0) for shareholder in shareholders
        )

        if total_board_seats == 0:
            errors.append(ValidationError(
                entity_id=None,
                entity_type="board_control",
                field="total_board_seats",
                message="No board seats allocated across shareholders",
                severity="info",
                suggestion="Consider allocating board seats to key shareholders"
            ))

        # Check for board majority
        for shareholder in shareholders:
            board_seats = getattr(shareholder, 'board_seats', 0)
            if total_board_seats > 0 and board_seats / total_board_seats > 0.5:
                errors.append(ValidationError(
                    entity_id=shareholder.name,
                    entity_type="board_control",
                    field="board_seats",
                    message=f"Shareholder has board majority control ({board_seats}/{total_board_seats} seats)",
                    severity="info",
                    suggestion="Consider if board majority control is intended"
                ))

        return errors

    def verify_drag_tag_provisions(self, shareholders: List[Shareholder]) -> List[ValidationError]:
        """Verify drag-along and tag-along provisions.

        Args:
            shareholders: List of shareholders to validate

        Returns:
            List of validation errors
        """
        errors = []

        # This is a placeholder for drag-tag validation
        # Implementation would depend on how these provisions are modeled

        return errors
