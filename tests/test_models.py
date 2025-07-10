import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any

from src.cashcow.models.base import BaseEntity
from src.cashcow.models.entities import (
    Employee, Grant, Investment, Sale, Service,
    Facility, Software, Equipment, Project, create_entity
)


class TestBaseEntity:
    def test_basic_entity_creation(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1)
        )
        
        assert entity.type == 'test'
        assert entity.name == 'Test Entity'
        assert entity.start_date == date(2024, 1, 1)
        assert entity.end_date is None
        assert entity.tags == []
    
    def test_entity_with_end_date(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        assert entity.end_date == date(2024, 12, 31)
    
    def test_entity_with_tags(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1),
            tags=['important', 'revenue']
        )
        
        assert entity.tags == ['important', 'revenue']
    
    def test_date_parsing_from_string(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        assert entity.start_date == date(2024, 1, 1)
        assert entity.end_date == date(2024, 12, 31)
    
    def test_extra_fields_allowed(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1),
            custom_field='custom_value',
            another_field=123
        )
        
        assert entity.custom_field == 'custom_value'
        assert entity.another_field == 123
    
    def test_is_active_no_end_date(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1)
        )
        
        assert entity.is_active(date(2024, 6, 1)) is True
        assert entity.is_active(date(2023, 6, 1)) is False
    
    def test_is_active_with_end_date(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        assert entity.is_active(date(2024, 6, 1)) is True
        assert entity.is_active(date(2023, 6, 1)) is False
        assert entity.is_active(date(2025, 6, 1)) is False
    
    def test_get_field_access(self):
        entity = BaseEntity(
            type='test',
            name='Test Entity',
            start_date=date(2024, 1, 1),
            custom_field='value'
        )
        
        assert entity.get_field('custom_field') == 'value'
        assert entity.get_field('nonexistent') is None
        assert entity.get_field('nonexistent', 'default') == 'default'


class TestEmployee:
    def test_employee_creation(self):
        employee = Employee(
            type='employee',
            name='John Doe',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly'
        )
        
        assert employee.type == 'employee'
        assert employee.name == 'John Doe'
        assert employee.salary == 60000
        assert employee.pay_frequency == 'monthly'
    
    def test_employee_with_equity(self):
        employee = Employee(
            type='employee',
            name='Jane Smith',
            start_date=date(2024, 1, 1),
            salary=80000,
            pay_frequency='monthly',
            equity_shares=5000,
            vesting_years=4,
            cliff_years=1
        )
        
        assert employee.equity_shares == 5000
        assert employee.vesting_years == 4
        assert employee.cliff_years == 1
    
    def test_employee_with_benefits(self):
        employee = Employee(
            type='employee',
            name='Bob Johnson',
            start_date=date(2024, 1, 1),
            salary=70000,
            pay_frequency='monthly',
            benefits={'health': 400, 'dental': 100, 'retirement': 200},
            allowances={'transport': 300, 'food': 200}
        )
        
        assert employee.benefits == {'health': 400, 'dental': 100, 'retirement': 200}
        assert employee.allowances == {'transport': 300, 'food': 200}
    
    def test_employee_total_cost_calculation(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly',
            overhead_multiplier=1.3,
            benefits={'health': 400, 'retirement': 200},
            allowances={'transport': 300}
        )
        
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        total_cost = employee.calculate_total_cost(context)
        
        # Base: 5000, Benefits: 600, Allowances: 300, Overhead: 1500
        expected = 5000 + 600 + 300 + 1500
        assert total_cost == expected
    
    def test_employee_invalid_pay_frequency(self):
        with pytest.raises(ValueError):
            Employee(
                type='employee',
                name='Test Employee',
                start_date=date(2024, 1, 1),
                salary=60000,
                pay_frequency='invalid'
            )
    
    def test_employee_negative_salary(self):
        with pytest.raises(ValueError):
            Employee(
                type='employee',
                name='Test Employee',
                start_date=date(2024, 1, 1),
                salary=-1000,
                pay_frequency='monthly'
            )


class TestGrant:
    def test_grant_creation(self):
        grant = Grant(
            type='grant',
            name='SBIR Phase I',
            start_date=date(2024, 1, 1),
            amount=100000,
            grantor='NASA'
        )
        
        assert grant.type == 'grant'
        assert grant.name == 'SBIR Phase I'
        assert grant.amount == 100000
        assert grant.grantor == 'NASA'
    
    def test_grant_with_milestones(self):
        grant = Grant(
            type='grant',
            name='SBIR Phase II',
            start_date=date(2024, 1, 1),
            amount=500000,
            grantor='NASA',
            milestones=[
                {'name': 'Phase 1', 'amount': 200000, 'due_date': '2024-06-01'},
                {'name': 'Phase 2', 'amount': 300000, 'due_date': '2024-12-01'}
            ]
        )
        
        assert len(grant.milestones) == 2
        assert grant.milestones[0]['name'] == 'Phase 1'
        assert grant.milestones[0]['amount'] == 200000
    
    def test_grant_milestone_validation(self):
        grant = Grant(
            type='grant',
            name='Test Grant',
            start_date=date(2024, 1, 1),
            amount=100000,
            grantor='Test',
            milestones=[
                {'name': 'Phase 1', 'amount': 60000, 'due_date': '2024-06-01'},
                {'name': 'Phase 2', 'amount': 50000, 'due_date': '2024-12-01'}
            ]
        )
        
        # Should raise validation error as milestone amounts exceed total
        with pytest.raises(ValueError):
            grant.validate_milestones()
    
    def test_grant_negative_amount(self):
        with pytest.raises(ValueError):
            Grant(
                type='grant',
                name='Test Grant',
                start_date=date(2024, 1, 1),
                amount=-10000,
                grantor='Test'
            )


class TestInvestment:
    def test_investment_creation(self):
        investment = Investment(
            type='investment',
            name='Series A',
            start_date=date(2024, 1, 1),
            amount=2000000,
            investor='VC Fund'
        )
        
        assert investment.type == 'investment'
        assert investment.name == 'Series A'
        assert investment.amount == 2000000
        assert investment.investor == 'VC Fund'
    
    def test_investment_with_disbursement_schedule(self):
        investment = Investment(
            type='investment',
            name='Series A',
            start_date=date(2024, 1, 1),
            amount=2000000,
            investor='VC Fund',
            disbursement_schedule=[
                {'date': '2024-01-15', 'amount': 800000},
                {'date': '2024-06-15', 'amount': 1200000}
            ]
        )
        
        assert len(investment.disbursement_schedule) == 2
        assert investment.disbursement_schedule[0]['amount'] == 800000
    
    def test_investment_equity_details(self):
        investment = Investment(
            type='investment',
            name='Series A',
            start_date=date(2024, 1, 1),
            amount=2000000,
            investor='VC Fund',
            equity_percentage=0.20,
            valuation=10000000,
            board_seats=1
        )
        
        assert investment.equity_percentage == 0.20
        assert investment.valuation == 10000000
        assert investment.board_seats == 1


class TestSale:
    def test_sale_creation(self):
        sale = Sale(
            type='sale',
            name='Q1 Sales',
            start_date=date(2024, 1, 1),
            amount=50000,
            customer='Customer A'
        )
        
        assert sale.type == 'sale'
        assert sale.name == 'Q1 Sales'
        assert sale.amount == 50000
        assert sale.customer == 'Customer A'
    
    def test_sale_with_payment_schedule(self):
        sale = Sale(
            type='sale',
            name='Enterprise Deal',
            start_date=date(2024, 1, 1),
            amount=100000,
            customer='Enterprise Corp',
            payment_schedule=[
                {'date': '2024-01-15', 'amount': 30000},
                {'date': '2024-02-15', 'amount': 30000},
                {'date': '2024-03-15', 'amount': 40000}
            ]
        )
        
        assert len(sale.payment_schedule) == 3
        assert sum(p['amount'] for p in sale.payment_schedule) == 100000
    
    def test_sale_with_products(self):
        sale = Sale(
            type='sale',
            name='Product Sales',
            start_date=date(2024, 1, 1),
            amount=75000,
            customer='Customer B',
            products=['Product A', 'Product B'],
            quantities=[10, 5]
        )
        
        assert sale.products == ['Product A', 'Product B']
        assert sale.quantities == [10, 5]


class TestService:
    def test_service_creation(self):
        service = Service(
            type='service',
            name='Consulting Services',
            start_date=date(2024, 1, 1),
            hourly_rate=150,
            hours_per_month=40
        )
        
        assert service.type == 'service'
        assert service.name == 'Consulting Services'
        assert service.hourly_rate == 150
        assert service.hours_per_month == 40
    
    def test_service_monthly_revenue(self):
        service = Service(
            type='service',
            name='Consulting Services',
            start_date=date(2024, 1, 1),
            hourly_rate=150,
            hours_per_month=40
        )
        
        monthly_revenue = service.calculate_monthly_revenue()
        assert monthly_revenue == 6000  # 150 * 40
    
    def test_service_with_contract_value(self):
        service = Service(
            type='service',
            name='Fixed Contract',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            contract_value=120000
        )
        
        assert service.contract_value == 120000
        monthly_revenue = service.calculate_monthly_revenue()
        assert monthly_revenue == 10000  # 120000 / 12


class TestFacility:
    def test_facility_creation(self):
        facility = Facility(
            type='facility',
            name='Main Office',
            start_date=date(2024, 1, 1),
            monthly_cost=8000,
            address='123 Main St'
        )
        
        assert facility.type == 'facility'
        assert facility.name == 'Main Office'
        assert facility.monthly_cost == 8000
        assert facility.address == '123 Main St'
    
    def test_facility_with_utilities(self):
        facility = Facility(
            type='facility',
            name='Manufacturing Plant',
            start_date=date(2024, 1, 1),
            monthly_cost=15000,
            utilities={'electricity': 2000, 'water': 500, 'gas': 300}
        )
        
        assert facility.utilities == {'electricity': 2000, 'water': 500, 'gas': 300}
        total_cost = facility.calculate_total_monthly_cost()
        assert total_cost == 17800  # 15000 + 2800
    
    def test_facility_square_footage(self):
        facility = Facility(
            type='facility',
            name='Office Space',
            start_date=date(2024, 1, 1),
            monthly_cost=6000,
            square_footage=3000
        )
        
        assert facility.square_footage == 3000
        cost_per_sqft = facility.calculate_cost_per_sqft()
        assert cost_per_sqft == 2.0  # 6000 / 3000


class TestSoftware:
    def test_software_creation(self):
        software = Software(
            type='software',
            name='CAD Software',
            start_date=date(2024, 1, 1),
            purchase_price=5000,
            vendor='CAD Corp'
        )
        
        assert software.type == 'software'
        assert software.name == 'CAD Software'
        assert software.purchase_price == 5000
        assert software.vendor == 'CAD Corp'
    
    def test_software_subscription(self):
        software = Software(
            type='software',
            name='Cloud Service',
            start_date=date(2024, 1, 1),
            monthly_cost=299,
            subscription_type='monthly',
            users=10
        )
        
        assert software.monthly_cost == 299
        assert software.subscription_type == 'monthly'
        assert software.users == 10
    
    def test_software_with_maintenance(self):
        software = Software(
            type='software',
            name='Enterprise Software',
            start_date=date(2024, 1, 1),
            purchase_price=50000,
            maintenance_percentage=0.18,
            support_level='premium'
        )
        
        assert software.maintenance_percentage == 0.18
        assert software.support_level == 'premium'
        monthly_maintenance = software.calculate_monthly_maintenance()
        assert monthly_maintenance == 750  # 50000 * 0.18 / 12


class TestEquipment:
    def test_equipment_creation(self):
        equipment = Equipment(
            type='equipment',
            name='CNC Machine',
            start_date=date(2024, 1, 1),
            purchase_price=150000,
            vendor='Machine Corp'
        )
        
        assert equipment.type == 'equipment'
        assert equipment.name == 'CNC Machine'
        assert equipment.purchase_price == 150000
        assert equipment.vendor == 'Machine Corp'
    
    def test_equipment_with_depreciation(self):
        equipment = Equipment(
            type='equipment',
            name='Manufacturing Equipment',
            start_date=date(2024, 1, 1),
            purchase_price=200000,
            useful_life_years=10,
            depreciation_method='straight-line',
            salvage_value=20000
        )
        
        assert equipment.useful_life_years == 10
        assert equipment.depreciation_method == 'straight-line'
        assert equipment.salvage_value == 20000
        
        monthly_depreciation = equipment.calculate_monthly_depreciation()
        assert monthly_depreciation == 1500  # (200000 - 20000) / 10 / 12
    
    def test_equipment_with_maintenance(self):
        equipment = Equipment(
            type='equipment',
            name='Test Equipment',
            start_date=date(2024, 1, 1),
            purchase_price=100000,
            maintenance_percentage=0.08,
            maintenance_schedule='quarterly'
        )
        
        assert equipment.maintenance_percentage == 0.08
        assert equipment.maintenance_schedule == 'quarterly'
        monthly_maintenance = equipment.calculate_monthly_maintenance()
        assert monthly_maintenance == 666.67  # 100000 * 0.08 / 12


class TestProject:
    def test_project_creation(self):
        project = Project(
            type='project',
            name='Engine Development',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=1000000
        )
        
        assert project.type == 'project'
        assert project.name == 'Engine Development'
        assert project.budget == 1000000
    
    def test_project_with_milestones(self):
        project = Project(
            type='project',
            name='Research Project',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=500000,
            milestones=[
                {'name': 'Design Phase', 'budget': 150000, 'due_date': '2024-04-01'},
                {'name': 'Prototype', 'budget': 200000, 'due_date': '2024-08-01'},
                {'name': 'Testing', 'budget': 150000, 'due_date': '2024-12-01'}
            ]
        )
        
        assert len(project.milestones) == 3
        assert project.milestones[0]['name'] == 'Design Phase'
        assert project.milestones[0]['budget'] == 150000
    
    def test_project_budget_utilization(self):
        project = Project(
            type='project',
            name='Test Project',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=100000,
            spent_to_date=35000
        )
        
        utilization = project.calculate_budget_utilization()
        assert utilization == 0.35  # 35000 / 100000
    
    def test_project_health_score(self):
        project = Project(
            type='project',
            name='Test Project',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=100000,
            spent_to_date=30000,
            milestones=[
                {'name': 'Phase 1', 'budget': 50000, 'due_date': '2024-06-01', 'completed': True},
                {'name': 'Phase 2', 'budget': 50000, 'due_date': '2024-12-01', 'completed': False}
            ]
        )
        
        health_score = project.calculate_health_score()
        assert 0.0 <= health_score <= 1.0


class TestEntityFactory:
    def test_create_employee(self):
        data = {
            'type': 'employee',
            'name': 'Test Employee',
            'start_date': '2024-01-01',
            'salary': 60000,
            'pay_frequency': 'monthly'
        }
        
        entity = create_entity(data)
        assert isinstance(entity, Employee)
        assert entity.name == 'Test Employee'
        assert entity.salary == 60000
    
    def test_create_grant(self):
        data = {
            'type': 'grant',
            'name': 'Test Grant',
            'start_date': '2024-01-01',
            'amount': 100000,
            'grantor': 'NASA'
        }
        
        entity = create_entity(data)
        assert isinstance(entity, Grant)
        assert entity.name == 'Test Grant'
        assert entity.amount == 100000
    
    def test_create_investment(self):
        data = {
            'type': 'investment',
            'name': 'Series A',
            'start_date': '2024-01-01',
            'amount': 2000000,
            'investor': 'VC Fund'
        }
        
        entity = create_entity(data)
        assert isinstance(entity, Investment)
        assert entity.name == 'Series A'
        assert entity.amount == 2000000
    
    def test_create_unknown_type(self):
        data = {
            'type': 'unknown',
            'name': 'Test Entity',
            'start_date': '2024-01-01'
        }
        
        entity = create_entity(data)
        assert isinstance(entity, BaseEntity)
        assert entity.type == 'unknown'
    
    def test_create_with_invalid_data(self):
        data = {
            'type': 'employee',
            'name': 'Test Employee',
            'start_date': '2024-01-01',
            'salary': -1000,  # Invalid negative salary
            'pay_frequency': 'monthly'
        }
        
        with pytest.raises(ValueError):
            create_entity(data)


class TestEntityValidation:
    def test_start_date_before_end_date(self):
        with pytest.raises(ValueError):
            BaseEntity(
                type='test',
                name='Test Entity',
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1)
            )
    
    def test_required_fields_validation(self):
        with pytest.raises(ValueError):
            Employee(
                type='employee',
                name='Test Employee',
                start_date=date(2024, 1, 1)
                # Missing required salary field
            )
    
    def test_field_type_validation(self):
        with pytest.raises(ValueError):
            Employee(
                type='employee',
                name='Test Employee',
                start_date=date(2024, 1, 1),
                salary='not_a_number',  # Should be numeric
                pay_frequency='monthly'
            )
    
    def test_enum_validation(self):
        with pytest.raises(ValueError):
            Equipment(
                type='equipment',
                name='Test Equipment',
                start_date=date(2024, 1, 1),
                purchase_price=100000,
                depreciation_method='invalid_method'  # Should be valid method
            )