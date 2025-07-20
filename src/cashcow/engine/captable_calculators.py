"""Cap table ownership calculation engine."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List

from ..models.base import BaseEntity
from ..models.captable import FundingRound, ShareClass, Shareholder
from ..models.interfaces.captable_interfaces import CapTableSummary
from ..models.validators.captable_validators import CapTableValidator
from .calculators import register_calculator

# Helper functions for ownership calculations

def get_entities_by_type(context: Dict[str, Any], entity_type: str) -> List[BaseEntity]:
    """Get all entities of a specific type from calculation context."""
    all_entities = context.get('all_entities', [])
    return [e for e in all_entities if e.type == entity_type]


def calculate_total_shares_by_class(shareholders: List[Shareholder]) -> Dict[str, int]:
    """Calculate total shares by share class."""
    shares_by_class = {}
    for shareholder in shareholders:
        class_name = shareholder.share_class
        if class_name not in shares_by_class:
            shares_by_class[class_name] = 0
        shares_by_class[class_name] += shareholder.total_shares
    return shares_by_class


def calculate_total_shares_fully_diluted(shareholders: List[Shareholder], share_classes: List[ShareClass]) -> int:
    """Calculate fully diluted share count including authorized but unissued shares."""
    # Get issued shares
    issued_shares = sum(s.total_shares for s in shareholders)

    # Add authorized but unissued shares (option pools, etc.)
    total_authorized = sum(sc.shares_authorized for sc in share_classes)

    # Use the higher of issued or authorized to account for option pools
    return max(issued_shares, total_authorized)


def validate_cap_table_data(shareholders: List[Shareholder], share_classes: List[ShareClass]) -> bool:
    """Validate cap table data before calculations."""
    validator = CapTableValidator()

    # Quick validation - just check for critical errors
    for shareholder in shareholders:
        errors = validator.validate_entity_consistency(shareholder)
        critical_errors = [e for e in errors if e.severity == "error"]
        if critical_errors:
            return False

    for share_class in share_classes:
        errors = validator.validate_entity_consistency(share_class)
        critical_errors = [e for e in errors if e.severity == "error"]
        if critical_errors:
            return False

    return True


def round_percentage(value: float, decimal_places: int = 4) -> float:
    """Round percentage to specified decimal places."""
    decimal_value = Decimal(str(value))
    rounded = decimal_value.quantize(
        Decimal('0.' + '0' * decimal_places),
        rounding=ROUND_HALF_UP
    )
    return float(rounded)


# Core calculator functions

@register_calculator("shareholder", "ownership_percentage",
                    description="Calculate shareholder ownership percentage on fully diluted basis")
def calculate_ownership_percentage(entity: Shareholder, context: Dict[str, Any]) -> float:
    """Calculate shareholder ownership percentage.

    Args:
        entity: Shareholder entity to calculate for
        context: Calculation context with all entities

    Returns:
        Ownership percentage as decimal (0.0 to 1.0)
    """
    shareholders = get_entities_by_type(context, "shareholder")
    share_classes = get_entities_by_type(context, "share_class")

    if not validate_cap_table_data(shareholders, share_classes):
        return 0.0

    # Calculate fully diluted ownership
    return calculate_fully_diluted_ownership(entity, shareholders, share_classes)


@register_calculator("shareholder", "voting_control",
                    description="Calculate shareholder voting control percentage")
def calculate_voting_control(entity: Shareholder, context: Dict[str, Any]) -> float:
    """Calculate voting control percentage.

    Args:
        entity: Shareholder entity to calculate for
        context: Calculation context with all entities

    Returns:
        Voting control percentage as decimal (0.0 to 1.0)
    """
    shareholders = get_entities_by_type(context, "shareholder")
    share_classes = get_entities_by_type(context, "share_class")

    if not validate_cap_table_data(shareholders, share_classes):
        return 0.0

    # Create share class lookup
    share_class_map = {sc.class_name: sc for sc in share_classes}

    return calculate_voting_percentage(entity, share_class_map, shareholders)


@register_calculator("shareholder", "board_control",
                    description="Calculate shareholder board control percentage")
def calculate_board_control_percentage(entity: Shareholder, context: Dict[str, Any]) -> float:
    """Calculate board control percentage.

    Args:
        entity: Shareholder entity to calculate for
        context: Calculation context with all entities

    Returns:
        Board control percentage as decimal (0.0 to 1.0)
    """
    shareholders = get_entities_by_type(context, "shareholder")

    total_board_seats = sum(getattr(s, 'board_seats', 0) for s in shareholders)
    entity_board_seats = getattr(entity, 'board_seats', 0)

    if total_board_seats == 0:
        return 0.0

    return round_percentage(entity_board_seats / total_board_seats)


@register_calculator("share_class", "utilization_rate",
                    description="Calculate share class utilization percentage")
def calculate_share_class_utilization(entity: ShareClass, context: Dict[str, Any]) -> float:
    """Calculate share class utilization percentage.

    Args:
        entity: ShareClass entity to calculate for
        context: Calculation context

    Returns:
        Utilization percentage as decimal (0.0 to 1.0)
    """
    if entity.shares_authorized == 0:
        return 0.0

    utilization = entity.shares_issued / entity.shares_authorized
    return round_percentage(utilization)


@register_calculator("funding_round", "dilution_impact",
                    description="Calculate dilution impact of funding round")
def calculate_dilution_impact(entity: FundingRound, context: Dict[str, Any]) -> Dict[str, float]:
    """Calculate dilution impact of funding round.

    Args:
        entity: FundingRound entity to calculate for
        context: Calculation context with all entities

    Returns:
        Dictionary with dilution analysis
    """
    shareholders = get_entities_by_type(context, "shareholder")

    # Calculate pre-round total shares
    pre_round_shares = sum(s.total_shares for s in shareholders)

    # Calculate post-round total shares
    post_round_shares = pre_round_shares + entity.shares_issued

    # Calculate dilution percentage
    dilution_percentage = entity.shares_issued / post_round_shares if post_round_shares > 0 and entity.shares_issued else 0.0

    # Calculate new investor ownership
    new_investor_ownership = dilution_percentage

    return {
        'dilution_percentage': round_percentage(dilution_percentage),
        'new_investor_ownership': round_percentage(new_investor_ownership),
        'pre_round_shares': pre_round_shares,
        'post_round_shares': post_round_shares,
        'shares_issued': entity.shares_issued
    }


@register_calculator("all", "cap_table_summary",
                    description="Generate comprehensive cap table summary")
def generate_cap_table_summary(entities: List[BaseEntity], context: Dict[str, Any]) -> CapTableSummary:
    """Generate comprehensive cap table summary.

    Args:
        entities: List of all entities
        context: Calculation context

    Returns:
        CapTableSummary object with all metrics
    """
    # Separate entities by type
    shareholders = [e for e in entities if isinstance(e, Shareholder)]
    share_classes = [e for e in entities if isinstance(e, ShareClass)]
    funding_rounds = [e for e in entities if isinstance(e, FundingRound)]

    if not validate_cap_table_data(shareholders, share_classes):
        return CapTableSummary()

    # Calculate ownership breakdown
    ownership_breakdown = {}
    voting_control_breakdown = {}
    board_control_breakdown = {}

    total_shares_outstanding = sum(s.total_shares for s in shareholders)
    total_shares_fully_diluted = calculate_total_shares_fully_diluted(shareholders, share_classes)

    share_class_map = {sc.class_name: sc for sc in share_classes}

    for shareholder in shareholders:
        # Ownership percentage
        ownership_pct = calculate_fully_diluted_ownership(shareholder, shareholders, share_classes)
        ownership_breakdown[shareholder.name] = ownership_pct

        # Voting control
        voting_pct = calculate_voting_percentage(shareholder, share_class_map, shareholders)
        voting_control_breakdown[shareholder.name] = voting_pct

        # Board control
        board_seats = getattr(shareholder, 'board_seats', 0)
        total_board_seats = sum(getattr(s, 'board_seats', 0) for s in shareholders)
        board_pct = board_seats / total_board_seats if total_board_seats > 0 else 0.0
        board_control_breakdown[shareholder.name] = round_percentage(board_pct)

    # Calculate share class breakdown
    share_class_breakdown = {}
    for share_class in share_classes:
        class_shareholders = [s for s in shareholders if s.share_class == share_class.class_name]
        class_shares = sum(s.total_shares for s in class_shareholders)

        share_class_breakdown[share_class.class_name] = {
            'shares_authorized': share_class.shares_authorized,
            'shares_issued': share_class.shares_issued,
            'shares_outstanding': class_shares,
            'utilization_rate': round_percentage(class_shares / share_class.shares_authorized) if share_class.shares_authorized > 0 else 0.0,
            'liquidation_preference': share_class.liquidation_preference,
            'voting_rights_per_share': share_class.voting_rights_per_share
        }

    # Calculate valuation metrics if funding rounds exist
    valuation_metrics = {}
    if funding_rounds:
        latest_round = max(funding_rounds, key=lambda r: r.start_date)
        valuation_metrics = {
            'latest_pre_money_valuation': latest_round.pre_money_valuation,
            'latest_post_money_valuation': latest_round.post_money_valuation,
            'latest_share_price': latest_round.price_per_share,
            'latest_round_date': latest_round.start_date.isoformat(),
            'latest_round_type': latest_round.round_type
        }

    # Create and populate CapTableSummary
    summary = CapTableSummary()
    summary.total_shares_outstanding = total_shares_outstanding
    summary.total_shares_authorized = sum(sc.shares_authorized for sc in share_classes)
    summary.ownership_by_shareholder = ownership_breakdown
    summary.ownership_by_class = {
        class_name: sum(ownership_breakdown.get(s.name, 0) for s in shareholders if s.share_class == class_name)
        for class_name in share_class_map.keys()
    }
    summary.voting_control = voting_control_breakdown
    summary.fully_diluted_shares = total_shares_fully_diluted

    # Calculate liquidation preference overhang
    total_liquidation_preference = 0
    for share_class in share_classes:
        class_shareholders = [s for s in shareholders if s.share_class == share_class.class_name]
        class_shares = sum(s.total_shares for s in class_shareholders)
        total_liquidation_preference += class_shares * share_class.liquidation_preference * share_class.par_value

    summary.liquidation_preference_overhang = total_liquidation_preference

    return summary


# Core calculation helper functions

def calculate_fully_diluted_ownership(
    shareholder: Shareholder,
    all_shareholders: List[Shareholder],
    share_classes: List[ShareClass]
) -> float:
    """Calculate fully-diluted ownership percentage.

    Args:
        shareholder: Shareholder to calculate for
        all_shareholders: All shareholders in cap table
        share_classes: All share classes

    Returns:
        Ownership percentage as decimal (0.0 to 1.0)
    """
    total_shares_fully_diluted = calculate_total_shares_fully_diluted(all_shareholders, share_classes)

    if total_shares_fully_diluted == 0:
        return 0.0

    ownership_percentage = shareholder.total_shares / total_shares_fully_diluted
    return round_percentage(ownership_percentage)


def calculate_basic_ownership(
    shareholder: Shareholder,
    total_issued_shares: int
) -> float:
    """Calculate basic ownership percentage (issued shares only).

    Args:
        shareholder: Shareholder to calculate for
        total_issued_shares: Total issued shares

    Returns:
        Ownership percentage as decimal (0.0 to 1.0)
    """
    if total_issued_shares == 0:
        return 0.0

    ownership_percentage = shareholder.total_shares / total_issued_shares
    return round_percentage(ownership_percentage)


def calculate_voting_percentage(
    shareholder: Shareholder,
    share_classes: Dict[str, ShareClass],
    all_shareholders: List[Shareholder]
) -> float:
    """Calculate voting control percentage by share class.

    Args:
        shareholder: Shareholder to calculate for
        share_classes: Share class lookup map
        all_shareholders: All shareholders for total calculation

    Returns:
        Voting percentage as decimal (0.0 to 1.0)
    """
    # Get voting rights per share for this shareholder's class
    share_class = share_classes.get(shareholder.share_class)
    if not share_class:
        return 0.0

    voting_rights_per_share = share_class.voting_rights_per_share
    shareholder_voting_power = shareholder.total_shares * voting_rights_per_share

    # Calculate total voting power
    total_voting_power = 0
    for sh in all_shareholders:
        sh_class = share_classes.get(sh.share_class)
        if sh_class:
            total_voting_power += sh.total_shares * sh_class.voting_rights_per_share

    if total_voting_power == 0:
        return 0.0

    voting_percentage = shareholder_voting_power / total_voting_power
    return round_percentage(voting_percentage)


def calculate_board_control(
    shareholders: List[Shareholder]
) -> Dict[str, float]:
    """Calculate board control distribution.

    Args:
        shareholders: List of shareholders

    Returns:
        Dictionary mapping shareholder names to board control percentages
    """
    total_board_seats = sum(getattr(s, 'board_seats', 0) for s in shareholders)

    board_control = {}
    for shareholder in shareholders:
        board_seats = getattr(shareholder, 'board_seats', 0)
        control_percentage = board_seats / total_board_seats if total_board_seats > 0 else 0.0
        board_control[shareholder.name] = round_percentage(control_percentage)

    return board_control


def generate_ownership_breakdown(
    entities: List[BaseEntity]
) -> CapTableSummary:
    """Generate complete ownership breakdown with all metrics.

    Args:
        entities: List of all entities

    Returns:
        CapTableSummary with comprehensive ownership data
    """
    # This is a simplified version of the full cap table summary
    # The main implementation is in generate_cap_table_summary
    context = {'all_entities': entities}
    return generate_cap_table_summary(entities, context)


# Convenience functions for common calculations

def get_founder_ownership_percentage(shareholders: List[Shareholder], share_classes: List[ShareClass]) -> float:
    """Get total founder ownership percentage.

    Args:
        shareholders: All shareholders
        share_classes: All share classes

    Returns:
        Combined founder ownership percentage
    """
    founder_shareholders = [s for s in shareholders if s.shareholder_type == "founder"]
    total_founder_shares = sum(s.total_shares for s in founder_shareholders)
    total_shares_fully_diluted = calculate_total_shares_fully_diluted(shareholders, share_classes)

    if total_shares_fully_diluted == 0:
        return 0.0

    return round_percentage(total_founder_shares / total_shares_fully_diluted)


def get_employee_ownership_percentage(shareholders: List[Shareholder], share_classes: List[ShareClass]) -> float:
    """Get total employee ownership percentage (including option pool).

    Args:
        shareholders: All shareholders
        share_classes: All share classes

    Returns:
        Combined employee ownership percentage
    """
    employee_shareholders = [s for s in shareholders if s.shareholder_type in ["employee", "other"]]  # "other" includes option pools
    total_employee_shares = sum(s.total_shares for s in employee_shareholders)
    total_shares_fully_diluted = calculate_total_shares_fully_diluted(shareholders, share_classes)

    if total_shares_fully_diluted == 0:
        return 0.0

    return round_percentage(total_employee_shares / total_shares_fully_diluted)


def get_investor_ownership_percentage(shareholders: List[Shareholder], share_classes: List[ShareClass]) -> float:
    """Get total investor ownership percentage.

    Args:
        shareholders: All shareholders
        share_classes: All share classes

    Returns:
        Combined investor ownership percentage
    """
    investor_shareholders = [s for s in shareholders if s.shareholder_type == "investor"]
    total_investor_shares = sum(s.total_shares for s in investor_shareholders)
    total_shares_fully_diluted = calculate_total_shares_fully_diluted(shareholders, share_classes)

    if total_shares_fully_diluted == 0:
        return 0.0

    return round_percentage(total_investor_shares / total_shares_fully_diluted)


# KPI calculators for cap table metrics

@register_calculator("all", "founder_ownership",
                    description="Calculate total founder ownership percentage")
def calculate_founder_ownership_kpi(entities: List[BaseEntity], context: Dict[str, Any]) -> float:
    """Calculate founder ownership KPI.

    Args:
        entities: List of all entities
        context: Calculation context

    Returns:
        Founder ownership percentage
    """
    shareholders = [e for e in entities if isinstance(e, Shareholder)]
    share_classes = [e for e in entities if isinstance(e, ShareClass)]

    return get_founder_ownership_percentage(shareholders, share_classes)


@register_calculator("all", "employee_ownership",
                    description="Calculate total employee ownership percentage")
def calculate_employee_ownership_kpi(entities: List[BaseEntity], context: Dict[str, Any]) -> float:
    """Calculate employee ownership KPI.

    Args:
        entities: List of all entities
        context: Calculation context

    Returns:
        Employee ownership percentage
    """
    shareholders = [e for e in entities if isinstance(e, Shareholder)]
    share_classes = [e for e in entities if isinstance(e, ShareClass)]

    return get_employee_ownership_percentage(shareholders, share_classes)


@register_calculator("all", "investor_ownership",
                    description="Calculate total investor ownership percentage")
def calculate_investor_ownership_kpi(entities: List[BaseEntity], context: Dict[str, Any]) -> float:
    """Calculate investor ownership KPI.

    Args:
        entities: List of all entities
        context: Calculation context

    Returns:
        Investor ownership percentage
    """
    shareholders = [e for e in entities if isinstance(e, Shareholder)]
    share_classes = [e for e in entities if isinstance(e, ShareClass)]

    return get_investor_ownership_percentage(shareholders, share_classes)
