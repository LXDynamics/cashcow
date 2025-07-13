---
title: Complete Entity System Guide
sidebar_label: Entities
sidebar_position: 2
description: Comprehensive guide to every YAML field available in CashCow's entity system
---

# Complete CashCow Entity System Guide

## Overview

The CashCow system uses a flexible entity architecture to model all financial components of a business. Each entity inherits from `BaseEntity` and provides specific validation rules, calculation methods, and financial modeling capabilities with support for any additional custom fields.

## Entity Architecture

### Base Entity (`BaseEntity`)

All entities inherit from `BaseEntity` which provides:

- **Flexible Schema**: Accepts any additional fields via Pydantic's `extra='allow'` configuration
- **Common Fields**: Standard fields shared across all entities  
- **Date Validation**: Automatic parsing and validation of date fields
- **Active Status**: Methods to determine if an entity is active on a given date

#### Common Fields (All Entities)

**Required Fields:**
- `type: str` - Entity type identifier (grant, investment, sale, service, employee, facility, software, equipment, project)
- `name: str` - Human-readable name
- `start_date: date` - When entity becomes active (YYYY-MM-DD format)

**Optional Fields:**
- `end_date: Optional[date] = None` - When entity ends (null = indefinite)
- `tags: List[str] = []` - Classification tags for filtering
- `notes: Optional[str] = None` - Free-form documentation

**Special Features:**
- **Flexible Schema**: Any additional fields beyond those defined are automatically accepted and preserved
- **Date Parsing**: Accepts ISO date strings (YYYY-MM-DD) and converts to Python date objects
- **Validation**: Built-in validation ensures end_date is after start_date when provided

#### Core Methods Available on All Entities

- `is_active(as_of_date)` - Check if entity is active on a specific date
- `get_field(field_name, default)` - Safely access fields with defaults
- `to_dict()` - Convert to dictionary including all extra fields
- `from_yaml_dict(data)` - Create entity from YAML data

---

## Revenue Entities

### 1. Grant Entity (`type: grant`)

Government or institutional funding with milestone and payment tracking.

**File Location:** `src/cashcow/models/revenue.py`

#### Complete Field Reference

**Required Fields:**
- `amount: float` - Total grant amount (must be positive)

**Grant Information:**
- `agency: Optional[str] = None` - Funding agency name
- `program: Optional[str] = None` - Grant program name  
- `grant_number: Optional[str] = None` - Grant identification number

**Payment Structure:**
- `payment_schedule: Optional[List[Dict[str, Any]]] = None` - Scheduled payments with date/amount pairs
- `indirect_cost_rate: float = 0.0` - Indirect cost rate (0.0 to 1.0)

**Reporting and Compliance:**
- `reporting_requirements: Optional[str] = None` - Description of reporting requirements
- `reporting_frequency: Optional[str] = None` - How often reporting is required (monthly, quarterly, annual)

**Performance Tracking:**
- `milestones: Optional[List[Dict[str, Any]]] = None` - List of milestone objects with name/date/amount/status

#### Validation Rules
- `amount` must be positive (> 0)
- `indirect_cost_rate` must be between 0.0 and 1.0

#### Calculation Methods
- `calculate_monthly_disbursement(as_of_date: date) -> float` - Calculate expected monthly funding
- `get_milestone_status(as_of_date: date) -> Dict[str, Any]` - Get current milestone progress

#### Complete YAML Example
```yaml
type: grant
name: "NASA SBIR Phase II"
start_date: "2024-01-01"
end_date: "2025-12-31"
tags: ["SBIR", "NASA", "R&D"]
notes: "Phase II development of rocket engine components"

# Required
amount: 750000.0

# Grant details
agency: "NASA"
program: "Small Business Innovation Research"
grant_number: "80NSSC24C0123"

# Payment structure
indirect_cost_rate: 0.15
payment_schedule:
  - date: "2024-01-01"
    amount: 187500.0
    description: "Q1 payment"
  - date: "2024-04-01"
    amount: 187500.0
    description: "Q2 payment"
  - date: "2024-07-01"
    amount: 187500.0
    description: "Q3 payment"
  - date: "2024-10-01"
    amount: 187500.0
    description: "Q4 payment"

# Milestones
milestones:
  - name: "Phase II Kickoff"
    date: "2024-01-15"
    amount: 0
    status: "completed"
    deliverable: "Project plan and timeline"
  - name: "Prototype Development"
    date: "2024-06-30"
    amount: 375000.0
    status: "in_progress"
    deliverable: "Working prototype"
  - name: "Final Delivery"
    date: "2025-12-31"
    amount: 375000.0
    status: "planned"
    deliverable: "Production-ready design"

# Reporting
reporting_requirements: "Quarterly progress reports, final technical report"
reporting_frequency: "quarterly"

# Custom fields (flexible schema)
technical_monitor: "Dr. Sarah Johnson"
performance_period: "24 months"
cost_sharing_required: false
```

---

### 2. Investment Entity (`type: investment`)

Venture capital or private investment funding with detailed term tracking.

**File Location:** `src/cashcow/models/revenue.py`

#### Complete Field Reference

**Required Fields:**
- `amount: float` - Investment amount (must be positive)

**Investment Details:**
- `investor: Optional[str] = None` - Investor name or firm
- `round_name: Optional[str] = None` - Investment round name
- `round_type: Optional[str] = None` - Type of round (seed, series_a, series_b, bridge, etc.)

**Valuation and Pricing:**
- `pre_money_valuation: Optional[float] = None` - Company valuation before investment
- `post_money_valuation: Optional[float] = None` - Company valuation after investment
- `share_price: Optional[float] = None` - Price per share
- `shares_issued: Optional[int] = None` - Number of shares issued for this investment

**Investment Terms:**
- `liquidation_preference: Optional[float] = None` - Liquidation preference multiplier
- `anti_dilution: Optional[str] = None` - Anti-dilution protection type
- `board_seats: Optional[int] = None` - Number of board seats granted to investor

**Disbursement:**
- `disbursement_schedule: Optional[List[Dict[str, Any]]] = None` - Payment schedule for investment funds

#### Calculation Methods
- `calculate_monthly_disbursement(as_of_date: date) -> float` - Calculate monthly funding received

#### Complete YAML Example
```yaml
type: investment
name: "Series A Round"
start_date: "2024-03-01"
tags: ["Series A", "VC", "Growth"]
notes: "Lead investor with strategic value beyond capital"

# Required
amount: 5000000.0

# Investment details
investor: "Aerospace Ventures"
round_name: "Series A"
round_type: "series_a"

# Valuation and pricing
pre_money_valuation: 15000000.0
post_money_valuation: 20000000.0
share_price: 2.50
shares_issued: 2000000

# Terms
liquidation_preference: 1.0
anti_dilution: "weighted_average_narrow"
board_seats: 1

# Disbursement schedule
disbursement_schedule:
  - date: "2024-03-01"
    amount: 2500000.0
    description: "Initial closing"
    conditions: "Legal completion"
  - date: "2024-06-01"
    amount: 1500000.0
    description: "Milestone tranche"
    conditions: "Prototype completion"
  - date: "2024-09-01"
    amount: 1000000.0
    description: "Final tranche"
    conditions: "Revenue targets"

# Custom fields
lead_investor: true
participating_rights: true
drag_along_rights: true
tag_along_rights: true
information_rights: true
```

---

### 3. Sale Entity (`type: sale`)

Product or service sales with delivery and payment tracking.

**File Location:** `src/cashcow/models/revenue.py`

#### Complete Field Reference

**Required Fields:**
- `amount: float` - Total sale amount (must be positive)

**Sale Details:**
- `customer: Optional[str] = None` - Customer name or company
- `product: Optional[str] = None` - Product or service sold
- `quantity: Optional[int] = None` - Quantity sold
- `unit_price: Optional[float] = None` - Price per unit

**Delivery and Payment:**
- `delivery_date: Optional[date] = None` - When product/service is delivered
- `payment_terms: Optional[str] = None` - Payment terms (net_30, net_60, cash_on_delivery, etc.)

**Payment Structure:**
- `payment_schedule: Optional[List[Dict[str, Any]]] = None` - Custom payment schedule

#### Calculation Methods
- `calculate_monthly_revenue(as_of_date: date) -> float` - Calculate monthly revenue recognition

#### Complete YAML Example
```yaml
type: sale
name: "Rocket Engine Model X Sale"
start_date: "2024-06-01"
tags: ["hardware", "aerospace", "custom"]
notes: "Custom engine design for commercial satellite launch"

# Required
amount: 2500000.0

# Sale details
customer: "Orbital Dynamics Corp"
product: "Rocket Engine Model X"
quantity: 1
unit_price: 2500000.0

# Delivery and payment
delivery_date: "2024-08-15"
payment_terms: "net_30"

# Custom payment schedule
payment_schedule:
  - date: "2024-06-01"
    amount: 750000.0
    description: "Contract signing (30%)"
    milestone: "Contract execution"
  - date: "2024-07-15"
    amount: 750000.0
    description: "Manufacturing milestone (30%)"
    milestone: "Manufacturing start"
  - date: "2024-08-15"
    amount: 1000000.0
    description: "Delivery payment (40%)"
    milestone: "Product delivery"

# Custom fields
contract_number: "OD-2024-001"
warranty_period: "24 months"
maintenance_included: true
training_included: true
certification_required: "FAA Part 25"
```

---

### 4. Service Entity (`type: service`)

Recurring service contracts with flexible billing structures.

**File Location:** `src/cashcow/models/revenue.py`

#### Complete Field Reference

**Required Fields:**
- `monthly_amount: float` - Monthly service revenue (must be positive)

**Service Details:**
- `customer: Optional[str] = None` - Customer name or company
- `service_type: Optional[str] = None` - Type of service provided
- `description: Optional[str] = None` - Detailed service description

**Service Structure:**
- `hourly_rate: Optional[float] = None` - Hourly billing rate for time-based services
- `hours_per_month: Optional[float] = None` - Expected hours per month

**Contract Terms:**
- `minimum_commitment_months: Optional[int] = None` - Minimum contract duration in months
- `auto_renewal: bool = False` - Whether contract automatically renews

**Performance Metrics:**
- `sla_requirements: Optional[Dict[str, Any]] = None` - Service level agreement requirements

#### Validation Rules
- `monthly_amount` must be positive (> 0)

#### Calculation Methods
- `calculate_monthly_revenue(as_of_date: date) -> float` - Calculate monthly service revenue
- `calculate_hourly_revenue(as_of_date: date, hours_worked: float) -> float` - Calculate revenue based on hours worked
- `get_service_metrics(as_of_date: date) -> Dict[str, Any]` - Get service performance metrics

#### Complete YAML Example
```yaml
type: service
name: "Engineering Consulting Services"
start_date: "2024-01-01"
end_date: "2024-12-31"
tags: ["consulting", "engineering", "ongoing"]
notes: "Monthly retainer for rocket engine design consulting"

# Required
monthly_amount: 45000.0

# Service details
customer: "Space Dynamics LLC"
service_type: "engineering_consulting"
description: "Rocket engine design consulting and technical advisory services"

# Service structure
hourly_rate: 300.0
hours_per_month: 150.0

# Contract terms
minimum_commitment_months: 6
auto_renewal: true

# SLA requirements
sla_requirements:
  response_time: "24 hours"
  availability: "99.5%"
  monthly_reports: true
  quarterly_reviews: true

# Custom fields
project_manager: "Dr. Emily Chen"
billing_cycle: "monthly"
invoice_due_days: 30
late_fee_percentage: 1.5
scope_includes:
  - "Design reviews"
  - "Technical documentation"
  - "Performance optimization"
  - "Regulatory compliance"
```

---

## Expense Entities

### 5. Employee Entity (`type: employee`)

Employee compensation with comprehensive benefits and equity tracking.

**File Locations:** 
- Advanced version: `src/cashcow/models/employee.py`
- Simplified version: `src/cashcow/models/entities.py`

#### Complete Field Reference (Advanced Version)

**Required Fields:**
- `salary: float` - Annual salary (must be positive)

**Position and Department:**
- `position: Optional[str] = None` - Job title
- `department: Optional[str] = None` - Department name

**Benefits and Overhead:**
- `overhead_multiplier: float = 1.3` - Cost multiplier for benefits/taxes (1.0 to 3.0)
- `benefits_annual: Optional[float] = None` - Annual benefits cost

**Equity Compensation:**
- `equity_eligible: bool = False` - Whether eligible for equity compensation
- `equity_shares: Optional[int] = None` - Number of equity shares granted
- `equity_start_date: Optional[date] = None` - When equity vesting begins
- `equity_cliff_months: int = 12` - Cliff period before any vesting
- `equity_vest_years: int = 4` - Total vesting period in years

**Bonus Structure:**
- `bonus_performance_max: float = 0.0` - Maximum performance bonus (as percentage of salary)
- `bonus_milestones_max: float = 0.0` - Maximum milestone bonus (as percentage of salary)
- `commission_rate: Optional[float] = None` - Commission rate for sales roles

**Allowances and Stipends (Monthly Amounts):**
- `home_office_stipend: Optional[float] = None` - Monthly home office allowance
- `professional_development_annual: Optional[float] = None` - Annual professional development budget
- `equipment_budget_annual: Optional[float] = None` - Annual equipment budget
- `conference_budget_annual: Optional[float] = None` - Annual conference budget

**One-time Costs:**
- `signing_bonus: Optional[float] = None` - One-time signing bonus
- `relocation_assistance: Optional[float] = None` - One-time relocation assistance

**Special Attributes:**
- `security_clearance: Optional[str] = None` - Security clearance level
- `remote_work_eligible: bool = True` - Whether eligible for remote work

#### Additional Fields (Simplified Version)

**Pay Structure:**
- `pay_frequency: str = 'monthly'` - Payment frequency (monthly, biweekly, weekly, annual)
- `hours_per_week: Optional[float] = None` - Standard hours per week
- `bonus_percentage: Optional[float] = None` - Bonus as percentage of salary (0 to 1.0)

**Benefits and Allowances:**
- `allowances: Optional[Dict[str, float]] = None` - Dictionary of monthly allowances
- `benefits: Optional[Dict[str, float]] = None` - Dictionary of benefit costs

**Additional Equity Fields:**
- `vesting_years: Optional[int] = None` - Alternative vesting period specification
- `cliff_years: Optional[int] = None` - Alternative cliff period specification

#### Validation Rules
- `salary` must be positive (> 0)
- `overhead_multiplier` between 1.0 and 3.0 (advanced) or 1.0 and 5.0 (simplified)
- `bonus_percentage` between 0 and 1.0 (simplified version)
- Valid `pay_frequency` values: monthly, biweekly, weekly, annual

#### Calculation Methods (Advanced Version)
- `calculate_total_cost(as_of_date, include_bonus_potential)` - Total monthly employee cost
- `calculate_base_monthly_cost()` - Base monthly salary cost
- `calculate_overhead_cost(as_of_date)` - Monthly overhead costs
- `calculate_allowances(as_of_date)` - Monthly allowances total
- `calculate_equity_vested_percentage(as_of_date)` - Percentage of equity vested
- `get_cost_breakdown(as_of_date)` - Detailed cost breakdown

#### Complete YAML Example
```yaml
type: employee
name: "Dr. Sarah Rodriguez"
start_date: "2024-01-01"
tags: ["engineering", "senior", "full-time"]
notes: "Lead propulsion engineer with aerospace background"

# Required
salary: 165000.0

# Position and department
position: "Senior Propulsion Engineer"
department: "Engineering"

# Benefits and overhead
overhead_multiplier: 1.4
benefits_annual: 28000.0

# Equity compensation
equity_eligible: true
equity_shares: 2500
equity_start_date: "2024-01-01"
equity_cliff_months: 12
equity_vest_years: 4

# Bonus structure
bonus_performance_max: 0.20
bonus_milestones_max: 0.10
commission_rate: 0.02

# Monthly allowances
home_office_stipend: 200.0
professional_development_annual: 5000.0
equipment_budget_annual: 3000.0
conference_budget_annual: 8000.0

# One-time costs
signing_bonus: 15000.0
relocation_assistance: 10000.0

# Special attributes
security_clearance: "Secret"
remote_work_eligible: true

# Additional fields (simplified version compatibility)
pay_frequency: "monthly"
hours_per_week: 40.0
allowances:
  home_office: 200.0
  phone: 100.0
  internet: 80.0
benefits:
  health_insurance: 800.0
  dental_insurance: 150.0
  vision_insurance: 50.0
  life_insurance: 100.0

# Custom fields
employee_id: "EMP-2024-003"
hire_date: "2024-01-01"
manager: "John Smith"
direct_reports: 2
performance_review_date: "2024-07-01"
```

---

### 6. Facility Entity (`type: facility`)

Physical facility costs with comprehensive expense tracking.

**File Locations:** 
- Comprehensive version: `src/cashcow/models/expense.py`
- Simplified version: `src/cashcow/models/entities.py`

#### Complete Field Reference (Comprehensive Version)

**Required Fields:**
- `monthly_cost: float` - Base monthly facility cost (must be positive)

**Facility Details:**
- `location: Optional[str] = None` - Facility address or location
- `size_sqft: Optional[int] = None` - Size in square feet
- `facility_type: Optional[str] = None` - Type: office, lab, manufacturing, warehouse

**Lease Terms:**
- `lease_start_date: Optional[date] = None` - Lease start date
- `lease_end_date: Optional[date] = None` - Lease end date
- `lease_monthly_base: Optional[float] = None` - Base lease amount

**Monthly Utilities and Services:**
- `utilities_monthly: Optional[float] = None` - Monthly utilities cost
- `internet_monthly: Optional[float] = None` - Monthly internet cost
- `security_monthly: Optional[float] = None` - Monthly security cost
- `cleaning_monthly: Optional[float] = None` - Monthly cleaning cost

**Insurance and Taxes:**
- `insurance_annual: Optional[float] = None` - Annual insurance cost
- `property_tax_annual: Optional[float] = None` - Annual property tax

**Maintenance and Repairs:**
- `maintenance_monthly: Optional[float] = None` - Regular monthly maintenance
- `maintenance_quarterly: Optional[float] = None` - Quarterly maintenance costs
- `maintenance_annual: Optional[float] = None` - Annual maintenance costs

**Certifications:**
- `certifications: Optional[List[Dict[str, Any]]] = None` - Required certifications with renewal tracking

#### Additional Fields (Simplified Version)
- `payment_frequency: str = 'monthly'` - Payment frequency (monthly, quarterly, annual)

#### Validation Rules
- `monthly_cost` must be positive (> 0)
- Valid `payment_frequency` values: monthly, quarterly, annual

#### Calculation Methods (Comprehensive Version)
- `calculate_monthly_cost(as_of_date)` - Total monthly facility cost including all expenses
- `get_certification_costs(as_of_date)` - Certification renewal costs for the month
- `get_facility_metrics(as_of_date)` - Utilization and cost metrics

#### Complete YAML Example
```yaml
type: facility
name: "Main Engineering Facility"
start_date: "2024-01-01"
tags: ["headquarters", "engineering", "lab"]
notes: "Primary facility housing engineering team and test lab"

# Required
monthly_cost: 15000.0

# Facility details
location: "1234 Innovation Drive, Austin, TX 78731"
size_sqft: 8000
facility_type: "office_lab"

# Lease terms
lease_start_date: "2024-01-01"
lease_end_date: "2026-12-31"
lease_monthly_base: 12000.0

# Monthly utilities and services
utilities_monthly: 1200.0
internet_monthly: 500.0
security_monthly: 800.0
cleaning_monthly: 600.0

# Annual costs (converted to monthly in calculations)
insurance_annual: 18000.0
property_tax_annual: 24000.0

# Maintenance costs
maintenance_monthly: 400.0
maintenance_quarterly: 2000.0
maintenance_annual: 5000.0

# Certifications
certifications:
  - name: "Fire Safety Certificate"
    cost: 1500.0
    renewal_date: "2024-06-01"
    authority: "Austin Fire Department"
    required: true
  - name: "Environmental Compliance"
    cost: 3000.0
    renewal_date: "2024-09-01"
    authority: "EPA"
    required: true
  - name: "Building Permit"
    cost: 500.0
    renewal_date: "2025-01-01"
    authority: "City of Austin"
    required: true

# Additional fields
payment_frequency: "monthly"
parking_spaces: 25
conference_rooms: 3
lab_space_sqft: 2000
office_space_sqft: 6000
capacity_employees: 35
```

---

### 7. Software Entity (`type: software`)

Software licensing and subscription costs with contract management.

**File Locations:** 
- Comprehensive version: `src/cashcow/models/expense.py`
- Simplified version: `src/cashcow/models/entities.py`

#### Complete Field Reference (Comprehensive Version)

**Required Fields:**
- `monthly_cost: float` - Monthly software cost (must be positive)

**Software Details:**
- `vendor: Optional[str] = None` - Software vendor or company
- `software_name: Optional[str] = None` - Name of the software
- `license_type: Optional[str] = None` - License type: subscription, perpetual, usage_based

**Licensing:**
- `license_count: Optional[int] = None` - Number of licenses purchased
- `concurrent_users: Optional[int] = None` - Maximum concurrent users allowed

**Pricing Structure:**
- `annual_cost: Optional[float] = None` - Annual cost (takes precedence over monthly_cost)
- `per_user_cost: Optional[float] = None` - Cost per user per month
- `usage_based_cost: Optional[float] = None` - Usage-based pricing rate

**Contract Terms:**
- `contract_start_date: Optional[date] = None` - Contract start date
- `contract_end_date: Optional[date] = None` - Contract end date
- `auto_renewal: bool = True` - Whether contract auto-renews

**Support and Maintenance:**
- `support_included: bool = True` - Whether support is included
- `maintenance_percentage: Optional[float] = None` - Maintenance cost as percentage of license cost

#### Additional Fields (Simplified Version)
- `purchase_price: Optional[float] = None` - One-time purchase price for perpetual licenses
- `useful_life_years: Optional[int] = None` - Useful life for depreciation
- `depreciation_method: str = 'straight-line'` - Depreciation method (straight-line, declining-balance, sum-of-years)

#### Validation Rules
- `monthly_cost` must be positive (> 0) if provided
- Valid `depreciation_method` values: straight-line, declining-balance, sum-of-years
- `maintenance_percentage` between 0 and 1.0

#### Calculation Methods (Comprehensive Version)
- `calculate_monthly_cost(as_of_date)` - Calculate actual monthly cost including usage
- `calculate_annual_cost(as_of_date)` - Calculate total annual cost
- `get_renewal_alert(as_of_date, alert_days)` - Check for upcoming contract renewals

#### Complete YAML Example
```yaml
type: software
name: "CAD Design Suite Enterprise"
start_date: "2024-01-01"
tags: ["design", "engineering", "enterprise"]
notes: "Primary CAD software for rocket engine design"

# Required
monthly_cost: 2400.0

# Software details
vendor: "AutoDesign Corp"
software_name: "CAD Pro Enterprise"
license_type: "subscription"

# Licensing
license_count: 12
concurrent_users: 10

# Pricing structure
annual_cost: 28800.0  # Takes precedence over monthly_cost
per_user_cost: 200.0
usage_based_cost: 0.05  # Per compute hour

# Contract terms
contract_start_date: "2024-01-01"
contract_end_date: "2024-12-31"
auto_renewal: true

# Support and maintenance
support_included: true
maintenance_percentage: 0.18

# Additional fields (simplified version compatibility)
purchase_price: 0.0  # Subscription model
useful_life_years: 3
depreciation_method: "straight-line"

# Custom fields
account_manager: "Jennifer Kim"
billing_cycle: "annual"
payment_method: "invoice"
discount_applied: 0.15
training_included: true
cloud_storage_gb: 1000
api_access: true
mobile_app_included: true
```

---

### 8. Equipment Entity (`type: equipment`)

Physical equipment with depreciation and maintenance tracking.

**File Locations:** 
- Comprehensive version: `src/cashcow/models/expense.py`
- Simplified version: `src/cashcow/models/entities.py`

#### Complete Field Reference (Comprehensive Version)

**Required Fields:**
- `cost: float` - Equipment purchase cost (must be positive)
- `purchase_date: date` - Date equipment was purchased

**Equipment Details:**
- `vendor: Optional[str] = None` - Equipment vendor or manufacturer
- `model: Optional[str] = None` - Equipment model number/name
- `serial_number: Optional[str] = None` - Equipment serial number
- `category: Optional[str] = None` - Equipment category (computer, lab_equipment, manufacturing, etc.)

**Financial Information:**
- `depreciation_years: Optional[int] = None` - Depreciation period in years
- `depreciation_method: str = "straight_line"` - Depreciation method
- `residual_value: Optional[float] = None` - Expected residual/salvage value

**Warranty and Support:**
- `warranty_years: Optional[int] = None` - Warranty period in years
- `warranty_end_date: Optional[date] = None` - Warranty end date
- `support_contract_annual: Optional[float] = None` - Annual support contract cost

**Maintenance:**
- `maintenance_schedule: Optional[str] = None` - Maintenance schedule (monthly, quarterly, annual)
- `maintenance_cost_annual: Optional[float] = None` - Annual maintenance cost

**Location and Assignment:**
- `location: Optional[str] = None` - Where equipment is located
- `assigned_to: Optional[str] = None` - Who equipment is assigned to

#### Additional Fields (Simplified Version)
- `purchase_price: Optional[float] = None` - Alternative to cost field
- `useful_life_years: Optional[int] = None` - Alternative to depreciation_years
- `maintenance_percentage: Optional[float] = None` - Maintenance as percentage of cost (0 to 1.0)
- `maintenance_cost: Optional[float] = None` - Alternative maintenance cost field

#### Validation Rules
- `cost` must be positive (> 0) if provided
- Valid `depreciation_method` values: straight-line, declining-balance, sum-of-years
- `maintenance_percentage` between 0 and 1.0

#### Calculation Methods (Comprehensive Version)
- `calculate_monthly_depreciation(as_of_date)` - Monthly depreciation expense
- `calculate_monthly_maintenance(as_of_date)` - Monthly maintenance cost
- `calculate_total_monthly_cost(as_of_date)` - Total monthly cost including depreciation and maintenance
- `get_current_book_value(as_of_date)` - Current book value after depreciation
- `get_equipment_summary(as_of_date)` - Comprehensive equipment summary

#### Complete YAML Example
```yaml
type: equipment
name: "High-Precision CNC Machine"
start_date: "2024-01-15"  # When it becomes active for cost tracking
tags: ["manufacturing", "cnc", "precision"]
notes: "Primary CNC machine for rocket engine component manufacturing"

# Required
cost: 485000.0
purchase_date: "2024-01-15"

# Equipment details
vendor: "Industrial Machines Inc"
model: "CNC-5000X"
serial_number: "IM2024-CNC-001"
category: "manufacturing"

# Financial information
depreciation_years: 7
depreciation_method: "straight_line"
residual_value: 50000.0

# Warranty and support
warranty_years: 3
warranty_end_date: "2027-01-15"
support_contract_annual: 12000.0

# Maintenance
maintenance_schedule: "quarterly"
maintenance_cost_annual: 8500.0

# Location and assignment
location: "Manufacturing Floor A, Station 3"
assigned_to: "Manufacturing Team Lead"

# Additional fields (simplified version compatibility)
purchase_price: 485000.0
useful_life_years: 7
maintenance_percentage: 0.02
maintenance_cost: 8500.0

# Custom fields
financing_method: "equipment_loan"
loan_term_years: 5
monthly_payment: 9200.0
installation_date: "2024-01-20"
training_required: true
certification_required: "ISO 9001"
operator_training_cost: 3500.0
installation_cost: 15000.0
shipping_cost: 2800.0
```

---

## Project Entity

### 9. Project Entity (`type: project`)

Project management with budget tracking, milestones, and team management.

**File Locations:** 
- `src/cashcow/models/project.py`
- `src/cashcow/models/entities.py`

#### Complete Field Reference

**Required Fields:**
- `total_budget: float` - Total project budget (must be positive)

**Project Management:**
- `project_manager: Optional[str] = None` - Project manager name
- `sponsor: Optional[str] = None` - Project sponsor

**Priority and Status:**
- `priority: str = "medium"` - Project priority (low, medium, high, critical)
- `status: str = "planned"` - Project status (planned, active, on_hold, completed, cancelled)
- `completion_percentage: float = 0.0` - Project completion percentage (0-100)

**Budget Tracking:**
- `budget_categories: Optional[Dict[str, float]] = None` - Budget breakdown by category
- `budget_spent: float = 0.0` - Amount spent to date
- `budget_committed: float = 0.0` - Amount committed but not yet spent

**Schedule Management:**
- `planned_start_date: Optional[date] = None` - Originally planned start date
- `actual_start_date: Optional[date] = None` - Actual start date
- `planned_end_date: Optional[date] = None` - Originally planned end date
- `estimated_completion_date: Optional[date] = None` - Current estimated completion date

**Project Organization:**
- `milestones: Optional[List[Dict[str, Any]]] = None` - Project milestones with dates and deliverables
- `team_members: Optional[List[str]] = None` - List of team member names
- `required_skills: Optional[List[str]] = None` - Skills required for project

**Risk and Dependencies:**
- `risk_level: str = "medium"` - Risk level (low, medium, high, critical)
- `dependencies: Optional[List[str]] = None` - Project dependencies

**Deliverables and Success:**
- `deliverables: Optional[List[Dict[str, Any]]] = None` - Project deliverables
- `success_criteria: Optional[List[str]] = None` - Success criteria for project completion

#### Validation Rules
- `total_budget` must be positive (> 0)
- `completion_percentage` between 0 and 100
- Valid `priority` values: low, medium, high, critical
- Valid `status` values: planned, active, on_hold, completed, cancelled
- Valid `risk_level` values: low, medium, high, critical

#### Calculation Methods
- `calculate_monthly_burn_rate(as_of_date)` - Calculate monthly budget burn rate
- `get_active_milestone(as_of_date)` - Get currently active milestone
- `get_overdue_milestones(as_of_date)` - Get list of overdue milestones
- `get_milestone_completion_rate()` - Calculate milestone completion percentage
- `calculate_budget_utilization()` - Calculate budget utilization metrics
- `get_project_health_score(as_of_date)` - Calculate overall project health score
- `get_project_summary(as_of_date)` - Get comprehensive project summary
- `update_milestone_status(milestone_name, status, completion_date)` - Update milestone status
- `add_milestone(name, planned_date, deliverable, budget)` - Add new milestone

#### Complete YAML Example
```yaml
type: project
name: "Next-Gen Engine Development"
start_date: "2024-01-01"
end_date: "2025-06-30"
tags: ["R&D", "engine", "innovation"]
notes: "Development of next-generation rocket engine with improved efficiency"

# Required
total_budget: 2500000.0

# Project management
project_manager: "Dr. Michael Chen"
sponsor: "VP of Engineering"

# Priority and status
priority: "high"
status: "active"
completion_percentage: 35.0

# Budget tracking
budget_categories:
  personnel: 1200000.0
  materials: 800000.0
  equipment: 300000.0
  testing: 150000.0
  overhead: 50000.0
budget_spent: 875000.0
budget_committed: 300000.0

# Schedule management
planned_start_date: "2024-01-01"
actual_start_date: "2024-01-03"
planned_end_date: "2025-06-30"
estimated_completion_date: "2025-07-15"

# Project organization
milestones:
  - name: "Design Phase Completion"
    planned_date: "2024-03-31"
    actual_date: "2024-04-05"
    status: "completed"
    deliverable: "Complete engine design specifications"
    budget_allocated: 400000.0
    budget_spent: 385000.0
  - name: "Prototype Development"
    planned_date: "2024-08-31"
    actual_date: null
    status: "in_progress"
    deliverable: "Working prototype engine"
    budget_allocated: 800000.0
    budget_spent: 350000.0
  - name: "Performance Testing"
    planned_date: "2024-12-31"
    actual_date: null
    status: "planned"
    deliverable: "Test results and performance data"
    budget_allocated: 600000.0
    budget_spent: 0.0
  - name: "Final Integration"
    planned_date: "2025-06-30"
    actual_date: null
    status: "planned"
    deliverable: "Production-ready engine design"
    budget_allocated: 700000.0
    budget_spent: 0.0

team_members:
  - "Dr. Michael Chen"
  - "Sarah Rodriguez"
  - "John Smith"
  - "Emily Johnson"
  - "David Wilson"

required_skills:
  - "Propulsion Engineering"
  - "CAD Design"
  - "Materials Science"
  - "Test Engineering"
  - "Project Management"

# Risk and dependencies
risk_level: "high"
dependencies:
  - "Completion of materials testing project"
  - "Approval of new test facility"
  - "Hiring of additional test engineer"

# Deliverables and success
deliverables:
  - name: "Engine Design Document"
    type: "documentation"
    due_date: "2024-03-31"
    status: "completed"
  - name: "Prototype Engine"
    type: "hardware"
    due_date: "2024-08-31"
    status: "in_progress"
  - name: "Test Report"
    type: "documentation"
    due_date: "2024-12-31"
    status: "planned"
  - name: "Production Specifications"
    type: "documentation"
    due_date: "2025-06-30"
    status: "planned"

success_criteria:
  - "Engine meets or exceeds performance specifications"
  - "Project completed within 110% of budget"
  - "All safety requirements met"
  - "Design ready for production implementation"

# Custom fields
funding_source: "Internal R&D Budget"
regulatory_approval_required: true
intellectual_property_filing: true
patent_applications: 3
external_consultants: 2
```

---

## Entity Design Patterns

### 1. Flexible Schema Architecture
All entities inherit from `BaseEntity` with Pydantic's `extra='allow'` configuration, which means:

- **Any additional fields** beyond those explicitly defined are automatically accepted
- **Custom fields are preserved** when loading from YAML and saving back
- **No validation errors** for unexpected fields
- **Future-proof design** allows for easy extension without code changes

### 2. Date Field Handling
- **Automatic Parsing**: All date fields accept ISO format strings (YYYY-MM-DD) and convert to Python date objects
- **Validation**: Built-in validation ensures end_date is after start_date when both are provided
- **Flexible Input**: Supports both string and Python date object inputs

### 3. Validation Strategy
- **Field-Level Validation**: Each field has specific validation rules (positive amounts, valid ranges, etc.)
- **Entity-Level Validation**: Cross-field validation for complex business rules
- **Graceful Failure**: Clear error messages with specific field and rule information

### 4. Calculation Methods
Each entity type provides specialized calculation methods for:
- **Monthly Costs/Revenues**: Based on entity-specific business logic
- **Active Status**: Respecting start/end dates and special conditions
- **Payment Schedules**: Supporting complex payment timing
- **Depreciation**: Handling various depreciation methods
- **Vesting**: Equity and benefit vesting calculations

### 5. Entity Type Registry
The system uses a centralized registry pattern:
- **Dynamic Creation**: `create_entity(data)` function automatically creates the correct entity type
- **Type Mapping**: `ENTITY_TYPES` dictionary maps type strings to entity classes
- **Extensible**: New entity types can be added without modifying core code

### 6. YAML Integration
- **Direct Loading**: Entities can be created directly from YAML dictionaries
- **Round-Trip Fidelity**: Data loaded from YAML maintains all original fields when saved back
- **File Integration**: Seamless integration with YAML file storage system

This comprehensive entity system provides a robust foundation for modeling all aspects of a business's financial operations while maintaining flexibility for custom fields and future extensions.