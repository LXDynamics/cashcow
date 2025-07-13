# Entity Creation Examples

This document provides practical examples for creating and using each entity type in the CashCow system.

## Employee Examples

### Basic Employee
```python
from datetime import date
from cashcow.models import Employee

# Create a basic employee
employee = Employee(
    type="employee",
    name="John Smith",
    salary=120000,
    position="Senior Engineer",
    department="Propulsion",
    start_date=date(2024, 2, 1)
)

# Calculate monthly cost
monthly_cost = employee.calculate_total_cost(date(2024, 6, 1))
print(f"Monthly cost: ${monthly_cost:,.2f}")
```

### Employee with Equity
```python
# Employee with equity compensation
equity_employee = Employee(
    type="employee",
    name="Jane Doe",
    salary=150000,
    position="Lead Engineer",
    department="Avionics",
    start_date=date(2024, 1, 15),
    overhead_multiplier=1.4,
    equity_eligible=True,
    equity_shares=15000,
    equity_start_date=date(2024, 1, 15),
    equity_cliff_months=12,
    equity_vest_years=4,
    bonus_performance_max=0.15,
    professional_development_annual=5000
)

# Check equity vesting
as_of_date = date(2025, 2, 1)  # 12+ months later
is_vested = equity_employee.is_equity_vested(as_of_date)
vested_shares = equity_employee.calculate_equity_vested_shares(as_of_date)
print(f"Equity vested: {is_vested}, Shares: {vested_shares}")
```

### Employee YAML Example
```yaml
# employees/jane-doe.yaml
type: employee
name: Jane Doe
salary: 150000
position: Lead Engineer
department: Avionics
start_date: 2024-01-15
overhead_multiplier: 1.4
equity_eligible: true
equity_shares: 15000
equity_start_date: 2024-01-15
equity_cliff_months: 12
equity_vest_years: 4
bonus_performance_max: 0.15
professional_development_annual: 5000
benefits_annual: 18000
home_office_stipend: 500
tags:
  - engineering
  - senior-level
  - equity-eligible
notes: "Lead engineer for avionics systems with strong background in embedded systems."
```

## Grant Examples

### NASA SBIR Grant
```python
from cashcow.models import Grant

# Create NASA SBIR Phase II grant
grant = Grant(
    type="grant",
    name="NASA SBIR Phase II - Advanced Propulsion",
    amount=750000,
    agency="NASA",
    program="SBIR",
    start_date=date(2024, 4, 1),
    end_date=date(2025, 9, 30),
    indirect_cost_rate=0.25,
    milestones=[
        {
            "name": "Preliminary Design Review",
            "date": date(2024, 7, 31),
            "amount": 200000,
            "status": "planned",
            "deliverable": "PDR Documentation Package"
        },
        {
            "name": "Critical Design Review", 
            "date": date(2025, 1, 31),
            "amount": 300000,
            "status": "planned",
            "deliverable": "CDR Documentation and Prototype"
        },
        {
            "name": "Final Testing and Report",
            "date": date(2025, 9, 30),
            "amount": 250000,
            "status": "planned",
            "deliverable": "Test Results and Final Report"
        }
    ]
)

# Calculate monthly disbursement
monthly_disbursement = grant.calculate_monthly_disbursement(date(2024, 8, 1))
print(f"Monthly disbursement: ${monthly_disbursement:,.2f}")

# Check milestone status
milestone_status = grant.get_milestone_status(date(2024, 8, 1))
print(f"Current milestones: {len(milestone_status['current'])}")
```

### Grant YAML Example
```yaml
# grants/nasa-sbir-phase2.yaml
type: grant
name: NASA SBIR Phase II - Advanced Propulsion
amount: 750000
agency: NASA
program: SBIR
grant_number: NNX24AA001
start_date: 2024-04-01
end_date: 2025-09-30
indirect_cost_rate: 0.25
reporting_frequency: quarterly
milestones:
  - name: Preliminary Design Review
    date: 2024-07-31
    amount: 200000
    status: planned
    deliverable: PDR Documentation Package
  - name: Critical Design Review
    date: 2025-01-31
    amount: 300000
    status: planned
    deliverable: CDR Documentation and Prototype
  - name: Final Testing and Report
    date: 2025-09-30
    amount: 250000
    status: planned
    deliverable: Test Results and Final Report
payment_schedule:
  - date: 2024-04-15
    amount: 150000
  - date: 2024-08-01
    amount: 200000
  - date: 2025-02-01
    amount: 300000
  - date: 2025-10-01
    amount: 100000
tags:
  - nasa
  - sbir
  - phase-2
  - propulsion
notes: "Phase II SBIR focusing on advanced propulsion technology development for small satellites."
```

## Investment Examples

### Series A Investment
```python
from cashcow.models import Investment

# Create Series A investment round
investment = Investment(
    type="investment",
    name="Series A Round",
    amount=5000000,
    investor="TechVentures Capital",
    round_type="series_a",
    pre_money_valuation=15000000,
    post_money_valuation=20000000,
    start_date=date(2024, 3, 15),
    disbursement_schedule=[
        {
            "date": date(2024, 3, 15),
            "amount": 3000000,
            "milestone": "Closing"
        },
        {
            "date": date(2024, 9, 15),
            "amount": 2000000,
            "milestone": "Product Milestone"
        }
    ]
)

# Calculate monthly disbursement
monthly_disbursement = investment.calculate_monthly_disbursement(date(2024, 3, 15))
print(f"March disbursement: ${monthly_disbursement:,.2f}")
```

### Investment YAML Example
```yaml
# investments/series-a-round.yaml
type: investment
name: Series A Round
amount: 5000000
investor: TechVentures Capital
round_type: series_a
pre_money_valuation: 15000000
post_money_valuation: 20000000
share_price: 5.50
shares_issued: 909091
start_date: 2024-03-15
liquidation_preference: 1.0
anti_dilution: weighted_average
board_seats: 1
disbursement_schedule:
  - date: 2024-03-15
    amount: 3000000
    milestone: Closing
  - date: 2024-09-15
    amount: 2000000
    milestone: Product Milestone Achievement
terms:
  dividend_rate: 0.08
  participating: false
  drag_along: true
  tag_along: true
tags:
  - series-a
  - venture-capital
  - growth-funding
notes: "Series A round led by TechVentures Capital with strategic value-add in aerospace sector."
```

## Sale Examples

### Product Sale
```python
from cashcow.models import Sale

# Create product sale
sale = Sale(
    type="sale",
    name="SpaceX Engine Cluster Order",
    amount=2500000,
    customer="SpaceX",
    product="Raptor-class Engine",
    quantity=5,
    unit_price=500000,
    delivery_date=date(2024, 12, 15),
    start_date=date(2024, 12, 15),
    payment_terms="net_30"
)

# Calculate monthly revenue (occurs on delivery date)
monthly_revenue = sale.calculate_monthly_revenue(date(2024, 12, 15))
print(f"December revenue: ${monthly_revenue:,.2f}")
```

### Sale YAML Example
```yaml
# sales/spacex-engine-cluster.yaml
type: sale
name: SpaceX Engine Cluster Order
amount: 2500000
customer: SpaceX
product: Raptor-class Engine
quantity: 5
unit_price: 500000
delivery_date: 2024-12-15
start_date: 2024-12-15
payment_terms: net_30
payment_schedule:
  - date: 2024-12-15
    amount: 1000000
    description: Initial payment on delivery
  - date: 2025-01-15
    amount: 1500000
    description: Final payment per contract terms
contract_number: SPX-2024-001
specifications:
  thrust: "330,000 lbf"
  fuel: "Methane/LOX"
  chamber_pressure: "300 bar"
tags:
  - spacex
  - raptor-class
  - production
notes: "First production order for Raptor-class engines with potential follow-on orders."
```

## Service Examples

### Consulting Service
```python
from cashcow.models import Service

# Create consulting service contract
service = Service(
    type="service",
    name="NASA Technical Support Contract",
    monthly_amount=45000,
    customer="NASA Goddard",
    service_type="technical_consulting",
    hourly_rate=200,
    hours_per_month=225,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    minimum_commitment_months=12
)

# Calculate monthly revenue
monthly_revenue = service.calculate_monthly_revenue(date(2024, 6, 1))
print(f"Monthly service revenue: ${monthly_revenue:,.2f}")

# Get service metrics
metrics = service.get_service_metrics(date(2024, 6, 1))
print(f"Total revenue to date: ${metrics['total_revenue']:,.2f}")
```

### Service YAML Example
```yaml
# services/nasa-support-contract.yaml
type: service
name: NASA Technical Support Contract
monthly_amount: 45000
customer: NASA Goddard
service_type: technical_consulting
description: "Technical consulting and support for propulsion system development"
hourly_rate: 200
hours_per_month: 225
start_date: 2024-01-01
end_date: 2024-12-31
minimum_commitment_months: 12
auto_renewal: false
sla_requirements:
  response_time: "24 hours"
  availability: "99.5%"
  deliverable_quality: "NASA standards"
contract_number: NASA-GSC-2024-001
billing_frequency: monthly
tags:
  - nasa
  - consulting
  - technical-support
notes: "Ongoing technical support contract with potential for renewal based on performance."
```

## Facility Examples

### Manufacturing Facility
```python
from cashcow.models import Facility

# Create manufacturing facility
facility = Facility(
    type="facility",
    name="Main Manufacturing Facility",
    monthly_cost=28000,
    location="Hawthorne, CA",
    size_sqft=25000,
    facility_type="manufacturing",
    utilities_monthly=4500,
    insurance_annual=36000,
    maintenance_monthly=2000,
    start_date=date(2024, 1, 1)
)

# Calculate total monthly cost
total_cost = facility.calculate_monthly_cost(date(2024, 6, 1))
print(f"Total monthly facility cost: ${total_cost:,.2f}")

# Get facility metrics
metrics = facility.get_facility_metrics(date(2024, 6, 1))
print(f"Cost per sq ft: ${metrics['cost_per_sqft']:.2f}")
```

### Facility YAML Example
```yaml
# facilities/main-manufacturing.yaml
type: facility
name: Main Manufacturing Facility
monthly_cost: 28000
location: Hawthorne, CA
size_sqft: 25000
facility_type: manufacturing
lease_start_date: 2024-01-01
lease_end_date: 2029-12-31
lease_monthly_base: 25000
utilities_monthly: 4500
internet_monthly: 500
security_monthly: 1200
cleaning_monthly: 800
insurance_annual: 36000
property_tax_annual: 24000
maintenance_monthly: 2000
maintenance_quarterly: 15000
start_date: 2024-01-01
certifications:
  - name: ISO 9001
    renewal_date: 2024-12-31
    cost: 15000
  - name: AS9100
    renewal_date: 2025-06-30
    cost: 20000
equipment_capacity: "10 engine assemblies per month"
tags:
  - manufacturing
  - primary-facility
  - iso-certified
notes: "Primary manufacturing facility with capacity for full engine assembly and testing."
```

## Equipment Examples

### CNC Machine
```python
from cashcow.models import Equipment

# Create CNC machine equipment
equipment = Equipment(
    type="equipment",
    name="Haas VF-4 CNC Machine",
    cost=180000,
    purchase_date=date(2024, 2, 15),
    vendor="Haas Automation",
    category="manufacturing",
    depreciation_years=7,
    maintenance_cost_annual=12000,
    start_date=date(2024, 2, 15)
)

# Calculate monthly costs
monthly_depreciation = equipment.calculate_monthly_depreciation(date(2024, 6, 1))
monthly_maintenance = equipment.calculate_monthly_maintenance(date(2024, 6, 1))
total_monthly = equipment.calculate_total_monthly_cost(date(2024, 6, 1))

print(f"Monthly depreciation: ${monthly_depreciation:,.2f}")
print(f"Monthly maintenance: ${monthly_maintenance:,.2f}")
print(f"Total monthly cost: ${total_monthly:,.2f}")

# Get current book value
book_value = equipment.get_current_book_value(date(2024, 6, 1))
print(f"Current book value: ${book_value:,.2f}")
```

### Equipment YAML Example
```yaml
# equipments/haas-cnc-machine.yaml
type: equipment
name: Haas VF-4 CNC Machine
cost: 180000
purchase_date: 2024-02-15
vendor: Haas Automation
model: VF-4
serial_number: 1234567
category: manufacturing
depreciation_years: 7
depreciation_method: straight_line
residual_value: 18000
warranty_years: 2
warranty_end_date: 2026-02-15
support_contract_annual: 8000
maintenance_cost_annual: 12000
maintenance_schedule: monthly
location: Manufacturing Floor A
assigned_to: Machine Operator Team
start_date: 2024-02-15
specifications:
  travel_x: "40 inches"
  travel_y: "20 inches"
  travel_z: "25 inches"
  spindle_speed: "8100 RPM"
  tool_capacity: "20 tools"
tags:
  - cnc
  - manufacturing
  - precision-machining
notes: "Primary CNC machine for precision component manufacturing with automated tool changer."
```

## Project Examples

### R&D Project
```python
from cashcow.models import Project

# Create R&D project
project = Project(
    type="project",
    name="Next-Gen Combustion Chamber",
    total_budget=1500000,
    project_manager="Dr. Sarah Wilson",
    priority="high",
    status="active",
    start_date=date(2024, 1, 1),
    planned_end_date=date(2024, 12, 31),
    budget_categories={
        "personnel": 800000,
        "materials": 400000,
        "equipment": 200000,
        "overhead": 100000
    },
    milestones=[
        {
            "name": "Design Phase Complete",
            "planned_date": date(2024, 4, 30),
            "budget": 300000,
            "status": "completed",
            "deliverable": "Design specifications and CAD models"
        },
        {
            "name": "Prototype Testing",
            "planned_date": date(2024, 8, 31),
            "budget": 600000,
            "status": "active",
            "deliverable": "Test prototype and results"
        }
    ],
    team_members=["Dr. Sarah Wilson", "John Smith", "Jane Doe", "Mike Johnson"]
)

# Calculate project metrics
burn_rate = project.calculate_monthly_burn_rate(date(2024, 6, 1))
health_score = project.get_project_health_score(date(2024, 6, 1))
budget_util = project.calculate_budget_utilization()

print(f"Monthly burn rate: ${burn_rate:,.2f}")
print(f"Health score: {health_score['overall_score']}/100")
print(f"Budget utilization: {budget_util['spend_rate']:.1f}%")
```

### Project YAML Example
```yaml
# projects/next-gen-combustion-chamber.yaml
type: project
name: Next-Gen Combustion Chamber
total_budget: 1500000
project_manager: Dr. Sarah Wilson
sponsor: CTO Office
priority: high
status: active
start_date: 2024-01-01
planned_start_date: 2024-01-01
actual_start_date: 2024-01-05
planned_end_date: 2024-12-31
estimated_completion_date: 2024-12-15
completion_percentage: 35.0
budget_categories:
  personnel: 800000
  materials: 400000
  equipment: 200000
  overhead: 100000
budget_spent: 450000
budget_committed: 200000
milestones:
  - name: Design Phase Complete
    planned_date: 2024-04-30
    actual_completion_date: 2024-05-15
    budget: 300000
    status: completed
    deliverable: Design specifications and CAD models
  - name: Prototype Testing
    planned_date: 2024-08-31
    budget: 600000
    status: active
    deliverable: Test prototype and results
  - name: Final Validation
    planned_date: 2024-12-15
    budget: 600000
    status: planned
    deliverable: Validated design ready for production
team_members:
  - Dr. Sarah Wilson
  - John Smith
  - Jane Doe
  - Mike Johnson
required_skills:
  - combustion_analysis
  - cfd_modeling
  - materials_science
  - test_engineering
risk_level: medium
dependencies:
  - Material procurement approval
  - Test facility availability
deliverables:
  - name: Design Documentation
    due_date: 2024-04-30
    status: completed
  - name: Prototype
    due_date: 2024-08-31
    status: in_progress
success_criteria:
  - "Achieve 15% efficiency improvement"
  - "Pass 100-hour durability test"
  - "Meet weight reduction targets"
tags:
  - rd
  - combustion
  - next-gen
  - high-priority
notes: "Critical project for next-generation engine development with aggressive timeline."
```

## Usage Patterns

### Loading and Validation
```python
from cashcow.storage import YamlEntityLoader
from cashcow.models import create_entity

# Load entities from YAML files
loader = YamlEntityLoader("entities/")
all_entities = loader.load_all()

# Validate specific entity data
entity_data = {
    "type": "employee",
    "name": "Test Employee",
    "salary": 100000,
    "start_date": "2024-01-01"
}

try:
    entity = create_entity(entity_data)
    print(f"Created valid {entity.type}: {entity.name}")
except ValueError as e:
    print(f"Validation error: {e}")
```

### Cost Calculations
```python
from datetime import date

# Calculate costs for all active employees
calculation_date = date(2024, 6, 1)
employees = loader.load_by_type("employee")

total_employee_cost = 0
for employee in employees:
    if employee.is_active(calculation_date):
        cost = employee.calculate_total_cost(calculation_date)
        total_employee_cost += cost
        print(f"{employee.name}: ${cost:,.2f}")

print(f"Total employee cost: ${total_employee_cost:,.2f}")
```

These examples demonstrate the flexibility and power of the CashCow entity system for modeling complex financial scenarios in a rocket engine company.