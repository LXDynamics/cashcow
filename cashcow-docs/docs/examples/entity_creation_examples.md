# Complete Entity Creation Examples

This document provides comprehensive YAML examples for creating every type of entity in the CashCow system, including all available fields discovered through model analysis.

## Revenue Entities

### Grant Entity - Complete Example

```yaml
# Complete Grant Entity with all possible fields
type: grant
name: "NASA SBIR Phase II - Advanced Propulsion Research"
start_date: "2024-01-01"
end_date: "2025-12-31"
tags: ["SBIR", "NASA", "R&D", "Phase II"]
notes: "Phase II SBIR for advanced rocket propulsion system development"

# Required field
amount: 750000.0

# Grant information
agency: "NASA"
program: "Small Business Innovation Research (SBIR)"
grant_number: "80NSSC24C0123"

# Payment structure
indirect_cost_rate: 0.15
payment_schedule:
  - date: "2024-01-01"
    amount: 187500.0
    description: "Q1 2024 payment"
    milestone: "Project initiation"
  - date: "2024-04-01"
    amount: 187500.0
    description: "Q2 2024 payment"
    milestone: "Design completion"
  - date: "2024-07-01"
    amount: 187500.0
    description: "Q3 2024 payment"
    milestone: "Prototype development"
  - date: "2024-10-01"
    amount: 187500.0
    description: "Q4 2024 payment"
    milestone: "Testing phase"

# Reporting and compliance
reporting_requirements: "Quarterly technical progress reports, annual financial reports, final technical report"
reporting_frequency: "quarterly"

# Performance tracking
milestones:
  - name: "Phase II Kickoff Meeting"
    date: "2024-01-15"
    amount: 0
    status: "completed"
    deliverable: "Project management plan and timeline"
    description: "Initial project setup and team alignment"
  - name: "Preliminary Design Review"
    date: "2024-03-31"
    amount: 187500.0
    status: "completed"
    deliverable: "Preliminary design documents"
    description: "First major technical milestone"
  - name: "Critical Design Review"
    date: "2024-06-30"
    amount: 187500.0
    status: "in_progress"
    deliverable: "Final design specifications"
    description: "Detailed design completion"
  - name: "Prototype Completion"
    date: "2024-09-30"
    amount: 187500.0
    status: "planned"
    deliverable: "Working prototype"
    description: "First functional prototype"
  - name: "Final Demonstration"
    date: "2025-12-31"
    amount: 187500.0
    status: "planned"
    deliverable: "Technology demonstration and final report"
    description: "Project completion and technology transfer"

# Custom fields (flexible schema allows any additional fields)
technical_monitor: "Dr. Sarah Johnson"
contracting_officer: "Michael Brown"
performance_period: "24 months"
cost_sharing_required: false
intellectual_property_rights: "Government retains unlimited rights"
security_classification: "Unclassified"
principal_investigator: "Dr. Emily Chen"
co_investigators: ["Dr. John Smith", "Dr. Maria Rodriguez"]
```

### Investment Entity - Complete Example

```yaml
# Complete Investment Entity with all possible fields
type: investment
name: "Series A Funding Round"
start_date: "2024-03-01"
tags: ["Series A", "VC", "Growth Capital", "Strategic"]
notes: "Strategic Series A investment from aerospace-focused VC firm"

# Required field
amount: 5000000.0

# Investment details
investor: "Aerospace Ventures LP"
round_name: "Series A"
round_type: "series_a"

# Valuation and pricing
pre_money_valuation: 15000000.0
post_money_valuation: 20000000.0
share_price: 2.50
shares_issued: 2000000

# Investment terms
liquidation_preference: 1.0
anti_dilution: "weighted_average_narrow"
board_seats: 1

# Disbursement schedule
disbursement_schedule:
  - date: "2024-03-01"
    amount: 2500000.0
    description: "Initial closing"
    conditions: "Legal documentation completion"
    tranche: "first"
  - date: "2024-06-01"
    amount: 1500000.0
    description: "Performance milestone tranche"
    conditions: "Prototype completion and customer validation"
    tranche: "second"
  - date: "2024-09-01"
    amount: 1000000.0
    description: "Revenue milestone tranche"
    conditions: "First commercial contract signed"
    tranche: "third"

# Custom fields
lead_investor: true
strategic_investor: true
participating_rights: true
drag_along_rights: true
tag_along_rights: true
information_rights: true
pro_rata_rights: true
board_observer_rights: false
investor_contact: "Jennifer Kim"
fund_name: "Aerospace Ventures Fund III"
vintage_year: 2023
fund_size: 250000000.0
investment_committee_approval: "2024-02-15"
due_diligence_completion: "2024-02-28"
```

### Sale Entity - Complete Example

```yaml
# Complete Sale Entity with all possible fields
type: sale
name: "Rocket Engine Model X-200 Sale to Orbital Dynamics"
start_date: "2024-06-01"
tags: ["hardware", "aerospace", "custom", "high-value"]
notes: "Custom rocket engine design and manufacturing for commercial satellite launch vehicle"

# Required field
amount: 2500000.0

# Sale details
customer: "Orbital Dynamics Corporation"
product: "Rocket Engine Model X-200"
quantity: 1
unit_price: 2500000.0

# Delivery and payment
delivery_date: "2024-08-15"
payment_terms: "custom_schedule"

# Payment structure
payment_schedule:
  - date: "2024-06-01"
    amount: 750000.0
    description: "Contract signing payment (30%)"
    milestone: "Contract execution and down payment"
    invoice_number: "INV-2024-001"
  - date: "2024-07-15"
    amount: 750000.0
    description: "Manufacturing milestone payment (30%)"
    milestone: "Manufacturing initiation and materials procurement"
    invoice_number: "INV-2024-002"
  - date: "2024-08-15"
    amount: 1000000.0
    description: "Delivery and acceptance payment (40%)"
    milestone: "Product delivery and customer acceptance"
    invoice_number: "INV-2024-003"

# Custom fields
contract_number: "OD-2024-001"
purchase_order: "PO-OD-2024-X200"
warranty_period: "24 months"
warranty_terms: "Full replacement for manufacturing defects"
maintenance_included: true
maintenance_period: "12 months"
training_included: true
training_hours: 40
certification_required: "FAA Part 25"
export_license_required: false
delivery_location: "Orbital Dynamics Facility, Hawthorne, CA"
shipping_method: "specialized_freight"
insurance_coverage: 3000000.0
performance_guarantees: ["thrust_specification", "efficiency_rating", "reliability_metrics"]
technical_support_included: true
spare_parts_included: true
documentation_package: "complete"
```

### Service Entity - Complete Example

```yaml
# Complete Service Entity with all possible fields
type: service
name: "Engineering Consulting Services for Space Dynamics"
start_date: "2024-01-01"
end_date: "2024-12-31"
tags: ["consulting", "engineering", "recurring", "technical"]
notes: "Comprehensive rocket engine design consulting and technical advisory services"

# Required field
monthly_amount: 45000.0

# Service details
customer: "Space Dynamics LLC"
service_type: "engineering_consulting"
description: "Rocket engine design consulting, performance optimization, and technical advisory services"

# Service structure
hourly_rate: 300.0
hours_per_month: 150.0

# Contract terms
minimum_commitment_months: 6
auto_renewal: true

# Performance metrics
sla_requirements:
  response_time: "24 hours for urgent issues"
  availability: "99.5% during business hours"
  monthly_reports: true
  quarterly_reviews: true
  escalation_procedure: "defined"
  performance_metrics: ["response_time", "deliverable_quality", "customer_satisfaction"]

# Custom fields
project_manager: "Dr. Emily Chen"
technical_lead: "Dr. John Smith"
billing_cycle: "monthly"
invoice_terms: "net_30"
invoice_due_days: 30
late_fee_percentage: 1.5
discount_for_annual_payment: 0.05
contract_value_annual: 540000.0
renewal_notice_days: 60
termination_notice_days: 30

# Scope of work
scope_includes:
  - "Rocket engine design reviews"
  - "Performance analysis and optimization"
  - "Technical documentation preparation"
  - "Regulatory compliance consulting"
  - "Test planning and analysis"
  - "Manufacturing process consultation"
  - "Quality assurance guidance"
  - "Risk assessment and mitigation"

# Deliverables
monthly_deliverables:
  - "Technical progress report"
  - "Time and expense summary"
  - "Recommendations document"
  - "Meeting minutes and action items"

# Exclusions
scope_excludes:
  - "Physical testing services"
  - "Manufacturing services"
  - "Travel expenses (billed separately)"
  - "Third-party software licenses"
```

---

## Expense Entities

### Employee Entity - Complete Example

```yaml
# Complete Employee Entity with all possible fields
type: employee
name: "Dr. Sarah Rodriguez"
start_date: "2024-01-01"
end_date: null  # Indefinite employment
tags: ["engineering", "senior", "full-time", "key-personnel"]
notes: "Lead propulsion engineer with 15 years aerospace industry experience"

# Required field
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

# Allowances and stipends (annual amounts converted to monthly)
home_office_stipend: 200.0  # Monthly
professional_development_annual: 5000.0
equipment_budget_annual: 3000.0
conference_budget_annual: 8000.0

# One-time costs
signing_bonus: 15000.0
relocation_assistance: 10000.0

# Special attributes
security_clearance: "Secret"
remote_work_eligible: true

# Additional fields from simplified version
pay_frequency: "monthly"
hours_per_week: 40.0
allowances:
  home_office: 200.0
  phone: 100.0
  internet: 80.0
  parking: 150.0
  gym_membership: 75.0

benefits:
  health_insurance: 800.0
  dental_insurance: 150.0
  vision_insurance: 50.0
  life_insurance: 100.0
  disability_insurance: 200.0
  retirement_match: 500.0

# Custom fields
employee_id: "EMP-2024-003"
hire_date: "2024-01-01"
manager: "John Smith"
direct_reports: 2
performance_review_date: "2024-07-01"
emergency_contact: "Maria Rodriguez (spouse)"
citizenship_status: "US Citizen"
education: "PhD Aerospace Engineering, MIT"
certifications: ["Professional Engineer", "Project Management Professional"]
languages: ["English", "Spanish"]
previous_employers: ["NASA", "SpaceX", "Blue Origin"]
```

### Facility Entity - Complete Example

```yaml
# Complete Facility Entity with all possible fields
type: facility
name: "Main Engineering and Manufacturing Facility"
start_date: "2024-01-01"
tags: ["headquarters", "engineering", "manufacturing", "testing"]
notes: "Primary facility housing engineering team, manufacturing floor, and test laboratory"

# Required field
monthly_cost: 25000.0

# Facility details
location: "1234 Innovation Drive, Austin, TX 78731"
size_sqft: 15000
facility_type: "mixed_use"

# Lease terms
lease_start_date: "2024-01-01"
lease_end_date: "2026-12-31"
lease_monthly_base: 18000.0

# Monthly utilities and services
utilities_monthly: 2200.0
internet_monthly: 800.0
security_monthly: 1200.0
cleaning_monthly: 900.0

# Annual costs (converted to monthly in calculations)
insurance_annual: 36000.0
property_tax_annual: 48000.0

# Maintenance and repairs
maintenance_monthly: 800.0
maintenance_quarterly: 3000.0
maintenance_annual: 10000.0

# Certifications and permits
certifications:
  - name: "Fire Safety Certificate"
    cost: 2500.0
    renewal_date: "2024-06-01"
    authority: "Austin Fire Department"
    required: true
    valid_until: "2025-06-01"
  - name: "Environmental Compliance Certificate"
    cost: 5000.0
    renewal_date: "2024-09-01"
    authority: "Texas Environmental Protection Agency"
    required: true
    valid_until: "2025-09-01"
  - name: "Manufacturing License"
    cost: 3000.0
    renewal_date: "2024-12-01"
    authority: "Texas Manufacturing Board"
    required: true
    valid_until: "2025-12-01"
  - name: "Building Permit"
    cost: 1000.0
    renewal_date: "2025-01-01"
    authority: "City of Austin"
    required: true
    valid_until: "2026-01-01"

# Additional fields
payment_frequency: "monthly"
parking_spaces: 50
conference_rooms: 5
lab_space_sqft: 3000
office_space_sqft: 8000
manufacturing_space_sqft: 4000
capacity_employees: 60
hvac_zones: 4
electrical_capacity_kw: 500
loading_docks: 2
crane_capacity_tons: 5
compressed_air_available: true
emergency_systems: ["fire_suppression", "emergency_lighting", "backup_generator"]

# Custom fields
property_manager: "Austin Commercial Properties"
landlord_contact: "Jennifer Wilson"
lease_type: "triple_net"
escalation_clause: "3% annual"
renewal_options: 2
renewal_terms: "5 years each"
tenant_improvements: 75000.0
co_tenants: ["Tech Startup A", "Manufacturing Company B"]
```

### Software Entity - Complete Example

```yaml
# Complete Software Entity with all possible fields
type: software
name: "CAD Design Suite Enterprise"
start_date: "2024-01-01"
tags: ["design", "engineering", "CAD", "enterprise", "critical"]
notes: "Primary CAD software suite for rocket engine design and analysis"

# Required field
monthly_cost: 3200.0

# Software details
vendor: "AutoDesign Corporation"
software_name: "CAD Pro Enterprise Suite"
license_type: "subscription"

# Licensing
license_count: 15
concurrent_users: 12

# Pricing structure
annual_cost: 38400.0  # Takes precedence over monthly_cost
per_user_cost: 213.33
usage_based_cost: 0.08  # Per compute hour for cloud rendering

# Contract terms
contract_start_date: "2024-01-01"
contract_end_date: "2024-12-31"
auto_renewal: true

# Support and maintenance
support_included: true
maintenance_percentage: 0.18

# Additional fields from simplified version
purchase_price: 0.0  # Subscription model, no upfront cost
useful_life_years: 3
depreciation_method: "straight-line"

# Custom fields
account_manager: "Jennifer Kim"
technical_support_contact: "support@autodesign.com"
billing_cycle: "annual"
payment_method: "corporate_credit_card"
discount_applied: 0.15
volume_discount_tier: "enterprise"
training_included: true
training_hours_annual: 40
certification_program_included: true
cloud_storage_gb: 2000
api_access: true
mobile_app_included: true
offline_capability: true
collaboration_features: true
version_control_included: true
backup_service_included: true
sso_integration: "active_directory"

# Feature modules included
modules_included:
  - "3D Modeling"
  - "Simulation and Analysis"
  - "Rendering Engine"
  - "Technical Drawings"
  - "Assembly Management"
  - "Materials Database"
  - "Collaboration Tools"
  - "Project Management"

# Usage metrics tracking
usage_metrics:
  track_user_hours: true
  track_feature_usage: true
  generate_monthly_reports: true
  license_optimization_alerts: true
```

### Equipment Entity - Complete Example

```yaml
# Complete Equipment Entity with all possible fields
type: equipment
name: "High-Precision 5-Axis CNC Machining Center"
start_date: "2024-02-01"  # When active for cost tracking
tags: ["manufacturing", "cnc", "precision", "critical", "production"]
notes: "Primary CNC machine for precision rocket engine component manufacturing"

# Required fields
cost: 485000.0
purchase_date: "2024-01-15"

# Equipment details
vendor: "Advanced Manufacturing Solutions Inc"
model: "CNC-5000X-5AXIS"
serial_number: "AMS2024-CNC-001"
category: "manufacturing"

# Financial information
depreciation_years: 7
depreciation_method: "straight_line"
residual_value: 50000.0

# Warranty and support
warranty_years: 3
warranty_end_date: "2027-01-15"
support_contract_annual: 15000.0

# Maintenance
maintenance_schedule: "quarterly"
maintenance_cost_annual: 12000.0

# Location and assignment
location: "Manufacturing Floor A, Station 3"
assigned_to: "Manufacturing Team Lead"

# Additional fields from simplified version
purchase_price: 485000.0
useful_life_years: 7
maintenance_percentage: 0.025
maintenance_cost: 12000.0

# Custom fields
financing_method: "equipment_loan"
loan_provider: "Industrial Equipment Finance Corp"
loan_term_years: 5
monthly_payment: 9800.0
loan_rate: 0.055
down_payment: 50000.0
installation_date: "2024-01-20"
commissioning_date: "2024-01-25"
first_production_date: "2024-02-01"
training_required: true
training_cost: 8500.0
trainer: "Advanced Manufacturing Solutions"
certification_required: "ISO 9001"
certification_cost: 2500.0
operator_training_hours: 80
maintenance_training_hours: 40
safety_training_hours: 16

# Installation and setup costs
installation_cost: 18000.0
electrical_work_cost: 8000.0
foundation_work_cost: 12000.0
hvac_modifications_cost: 5000.0
shipping_cost: 3500.0
crane_rental_cost: 2000.0
initial_tooling_cost: 25000.0

# Technical specifications
specifications:
  max_workpiece_weight: "2000 kg"
  spindle_speed_max: "12000 RPM"
  axis_travel_x: "1600 mm"
  axis_travel_y: "800 mm"
  axis_travel_z: "600 mm"
  positioning_accuracy: "±0.005 mm"
  repeatability: "±0.003 mm"
  power_requirement: "50 kW"
  coolant_capacity: "300 liters"
  tool_changer_capacity: 40

# Performance metrics
performance_metrics:
  target_utilization: 0.85
  target_oee: 0.80
  planned_maintenance_hours_monthly: 16
  expected_production_hours_monthly: 600
```

---

## Project Entity

### Project Entity - Complete Example

```yaml
# Complete Project Entity with all possible fields
type: project
name: "Next-Generation Rocket Engine Development"
start_date: "2024-01-01"
end_date: "2025-06-30"
tags: ["R&D", "engine", "innovation", "high-priority", "strategic"]
notes: "Development of next-generation rocket engine with 25% improved efficiency and reduced manufacturing cost"

# Required field
total_budget: 3500000.0

# Project management
project_manager: "Dr. Michael Chen"
sponsor: "VP of Engineering"

# Priority and status
priority: "high"
status: "active"
completion_percentage: 42.0

# Budget tracking
budget_categories:
  personnel: 1800000.0
  materials: 900000.0
  equipment: 400000.0
  testing: 250000.0
  overhead: 100000.0
  contingency: 50000.0
budget_spent: 1470000.0
budget_committed: 450000.0

# Schedule management
planned_start_date: "2024-01-01"
actual_start_date: "2024-01-03"
planned_end_date: "2025-06-30"
estimated_completion_date: "2025-07-15"

# Project organization
milestones:
  - name: "Project Initiation and Planning"
    planned_date: "2024-01-31"
    actual_date: "2024-02-02"
    status: "completed"
    deliverable: "Project charter, work breakdown structure, and resource plan"
    budget_allocated: 150000.0
    budget_spent: 148000.0
    completion_percentage: 100.0
    critical_path: false
  - name: "Conceptual Design Phase"
    planned_date: "2024-03-31"
    actual_date: "2024-04-05"
    status: "completed"
    deliverable: "Conceptual design specifications and performance requirements"
    budget_allocated: 500000.0
    budget_spent: 485000.0
    completion_percentage: 100.0
    critical_path: true
  - name: "Detailed Design and Analysis"
    planned_date: "2024-06-30"
    actual_date: null
    status: "completed"
    deliverable: "Complete engineering drawings and analysis reports"
    budget_allocated: 700000.0
    budget_spent: 680000.0
    completion_percentage: 100.0
    critical_path: true
  - name: "Prototype Manufacturing"
    planned_date: "2024-10-31"
    actual_date: null
    status: "in_progress"
    deliverable: "Functional prototype engine"
    budget_allocated: 900000.0
    budget_spent: 350000.0
    completion_percentage: 65.0
    critical_path: true
  - name: "Performance Testing Phase"
    planned_date: "2025-02-28"
    actual_date: null
    status: "planned"
    deliverable: "Test results and performance validation"
    budget_allocated: 600000.0
    budget_spent: 0.0
    completion_percentage: 0.0
    critical_path: true
  - name: "Design Optimization"
    planned_date: "2025-04-30"
    actual_date: null
    status: "planned"
    deliverable: "Optimized design for production readiness"
    budget_allocated: 400000.0
    budget_spent: 0.0
    completion_percentage: 0.0
    critical_path: false
  - name: "Final Documentation and Handoff"
    planned_date: "2025-06-30"
    actual_date: null
    status: "planned"
    deliverable: "Production-ready design package and documentation"
    budget_allocated: 250000.0
    budget_spent: 0.0
    completion_percentage: 0.0
    critical_path: false

# Team organization
team_members:
  - "Dr. Michael Chen (Project Manager)"
  - "Dr. Sarah Rodriguez (Lead Engineer)"
  - "John Smith (Mechanical Engineer)"
  - "Emily Johnson (Systems Engineer)"
  - "David Wilson (Test Engineer)"
  - "Lisa Brown (Manufacturing Engineer)"
  - "Mark Davis (Quality Engineer)"
  - "Jennifer Lee (Design Engineer)"

required_skills:
  - "Rocket Propulsion Engineering"
  - "Computational Fluid Dynamics"
  - "Materials Science and Engineering"
  - "Mechanical Design"
  - "Systems Engineering"
  - "Test Engineering"
  - "Manufacturing Engineering"
  - "Project Management"
  - "Quality Assurance"

# Risk and dependencies
risk_level: "high"
dependencies:
  - "Completion of materials characterization project (MAT-2024-001)"
  - "Approval of new test facility modifications"
  - "Hiring of additional test technician"
  - "Procurement of specialized testing equipment"
  - "Environmental impact assessment approval"
  - "Customer requirements finalization"

# Risk register
risks:
  - name: "Technical Performance Risk"
    probability: "medium"
    impact: "high"
    mitigation: "Extensive modeling and early prototype testing"
    owner: "Dr. Sarah Rodriguez"
  - name: "Schedule Delay Risk"
    probability: "medium"
    impact: "medium"
    mitigation: "Buffer time in critical path, parallel work streams"
    owner: "Dr. Michael Chen"
  - name: "Budget Overrun Risk"
    probability: "low"
    impact: "high"
    mitigation: "Strict change control process, regular budget reviews"
    owner: "Dr. Michael Chen"
  - name: "Key Personnel Risk"
    probability: "low"
    impact: "high"
    mitigation: "Cross-training, knowledge documentation"
    owner: "VP of Engineering"

# Deliverables and success criteria
deliverables:
  - name: "Project Charter"
    type: "documentation"
    due_date: "2024-01-31"
    status: "completed"
    owner: "Dr. Michael Chen"
    description: "Formal project authorization and scope definition"
  - name: "Conceptual Design Package"
    type: "design"
    due_date: "2024-03-31"
    status: "completed"
    owner: "Dr. Sarah Rodriguez"
    description: "High-level design concepts and trade studies"
  - name: "Detailed Engineering Drawings"
    type: "design"
    due_date: "2024-06-30"
    status: "completed"
    owner: "John Smith"
    description: "Manufacturing-ready engineering drawings"
  - name: "Prototype Engine"
    type: "hardware"
    due_date: "2024-10-31"
    status: "in_progress"
    owner: "Lisa Brown"
    description: "Functional prototype for testing"
  - name: "Test Report"
    type: "documentation"
    due_date: "2025-02-28"
    status: "planned"
    owner: "David Wilson"
    description: "Comprehensive performance test results"
  - name: "Production Design Package"
    type: "design"
    due_date: "2025-06-30"
    status: "planned"
    owner: "Dr. Sarah Rodriguez"
    description: "Production-ready design and manufacturing specifications"

success_criteria:
  - "Engine meets or exceeds 25% efficiency improvement target"
  - "Manufacturing cost reduced by minimum 15% compared to current design"
  - "Project completed within 110% of approved budget"
  - "All safety and regulatory requirements met"
  - "Design ready for production implementation"
  - "Technology transfer to manufacturing team completed"
  - "Customer acceptance achieved"

# Stakeholder information
stakeholders:
  - name: "VP of Engineering"
    role: "Executive Sponsor"
    involvement: "High"
    communication_frequency: "Weekly"
  - name: "Manufacturing Director"
    role: "End User"
    involvement: "Medium"
    communication_frequency: "Bi-weekly"
  - name: "Quality Director"
    role: "Approver"
    involvement: "Medium"
    communication_frequency: "Monthly"
  - name: "Customer Representative"
    role: "Requirements Owner"
    involvement: "High"
    communication_frequency: "Weekly"

# Custom fields
funding_source: "Internal R&D Budget"
contract_number: "INT-R&D-2024-001"
customer_project_number: "CUST-ENG-2024-005"
regulatory_approval_required: true
environmental_impact_assessment: "completed"
intellectual_property_filing: true
patent_applications: 3
trade_secret_classification: "high"
export_control_classification: "EAR99"
security_classification: "Proprietary"
external_consultants: 2
university_partnerships: 1
supplier_partnerships: 4
technology_readiness_level_start: 3
technology_readiness_level_target: 7
```

---

## Entity Design Patterns and Best Practices

### 1. Flexible Schema Usage

All entities support additional custom fields beyond those explicitly defined:

```yaml
# Any entity can include custom fields
type: employee
name: "John Smith"
salary: 120000.0
start_date: "2024-01-01"

# Custom fields automatically preserved
employee_id: "EMP-001"
badge_number: "B12345"
parking_space: "A-15"
emergency_contact: "Jane Smith"
dietary_restrictions: "vegetarian"
t_shirt_size: "Large"
```

### 2. Date Field Handling

All date fields accept ISO format strings and convert automatically:

```yaml
# All these date formats work
start_date: "2024-01-01"        # ISO string
end_date: 2024-12-31            # Date object (in YAML)
hire_date: "2024-01-15"         # Custom field with date
```

### 3. Complex Data Structures

Use dictionaries and lists for complex data:

```yaml
# Dictionary structures
budget_categories:
  personnel: 1000000.0
  materials: 500000.0
  overhead: 200000.0

# List of dictionaries
payment_schedule:
  - date: "2024-01-01"
    amount: 25000.0
    description: "Q1 payment"
  - date: "2024-04-01"
    amount: 25000.0
    description: "Q2 payment"

# Nested structures
milestones:
  - name: "Phase 1"
    deliverables:
      - "Design Document"
      - "Test Plan"
    budget:
      allocated: 100000.0
      spent: 75000.0
```

### 4. Validation Best Practices

Follow validation rules for each entity type:

```yaml
# Positive amounts required
amount: 100000.0        # ✓ Valid
amount: -5000.0         # ✗ Invalid

# Percentage fields (0.0 to 1.0)
indirect_cost_rate: 0.15   # ✓ Valid (15%)
indirect_cost_rate: 15     # ✗ Invalid (should be 0.15)

# Date ordering
start_date: "2024-01-01"   # ✓ Valid
end_date: "2024-12-31"     # ✓ Valid (after start)
end_date: "2023-12-31"     # ✗ Invalid (before start)
```

### 5. Performance Optimization

Structure data for efficient calculations:

```yaml
# Pre-calculate monthly amounts where possible
monthly_cost: 5000.0      # Direct monthly cost
annual_cost: 60000.0      # System converts to monthly

# Use payment schedules for complex timing
payment_schedule:
  - date: "2024-01-01"
    amount: 30000.0
  - date: "2024-07-01"
    amount: 30000.0
# System handles monthly distribution automatically
```

These comprehensive examples demonstrate every available field for each entity type, showing how to leverage the flexible schema design while following validation rules and best practices for optimal system performance.