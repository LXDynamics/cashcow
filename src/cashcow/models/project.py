"""Project model with comprehensive milestone tracking."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import field_validator

from .base import BaseEntity


class Project(BaseEntity):
    """R&D project entity with advanced milestone and budget tracking."""
    
    type: str = "project"
    
    # Required fields
    total_budget: float
    
    # Project details
    project_manager: Optional[str] = None
    sponsor: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    
    # Budget and financial
    budget_categories: Optional[Dict[str, float]] = None
    budget_spent: float = 0.0
    budget_committed: float = 0.0
    
    # Timeline
    planned_start_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    estimated_completion_date: Optional[date] = None
    
    # Status and progress
    status: str = "planned"  # planned, active, on_hold, completed, cancelled
    completion_percentage: float = 0.0
    
    # Milestones
    milestones: Optional[List[Dict[str, Any]]] = None
    
    # Team and resources
    team_members: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    
    # Risk and dependencies
    risk_level: str = "medium"  # low, medium, high, critical
    dependencies: Optional[List[str]] = None
    
    # Outcomes and deliverables
    deliverables: Optional[List[Dict[str, Any]]] = None
    success_criteria: Optional[List[str]] = None
    
    @field_validator('total_budget')
    @classmethod
    def validate_budget(cls, v: float) -> float:
        """Ensure total budget is positive."""
        if v <= 0:
            raise ValueError('total_budget must be positive')
        return v
    
    @field_validator('completion_percentage')
    @classmethod
    def validate_completion(cls, v: float) -> float:
        """Ensure completion percentage is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError('completion_percentage must be between 0 and 100')
        return v
    
    def calculate_monthly_burn_rate(self, as_of_date: date) -> float:
        """Calculate monthly budget burn rate."""
        if not self.is_active_project(as_of_date):
            return 0.0
        
        # If budget categories are specified, use them
        if self.budget_categories:
            return sum(self.budget_categories.values()) / 12
        
        # Otherwise, distribute total budget over project duration
        project_duration_months = self.get_project_duration_months()
        if project_duration_months > 0:
            return self.total_budget / project_duration_months
        
        return 0.0
    
    def get_project_duration_months(self) -> int:
        """Calculate project duration in months."""
        start_date = self.actual_start_date or self.planned_start_date or self.start_date
        end_date = self.planned_end_date or self.end_date
        
        if not end_date:
            return 12  # Default to 1 year if no end date
        
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    def is_active_project(self, as_of_date: date) -> bool:
        """Check if project is active on given date."""
        if self.status in ['cancelled', 'completed']:
            return False
        
        return self.is_active(as_of_date)
    
    def get_active_milestone(self, as_of_date: date) -> Optional[Dict[str, Any]]:
        """Get the current active milestone."""
        if not self.milestones:
            return None
        
        for milestone in self.milestones:
            if 'planned_date' in milestone:
                milestone_date = milestone['planned_date']
                if isinstance(milestone_date, str):
                    milestone_date = date.fromisoformat(milestone_date)
                
                status = milestone.get('status', 'planned')
                
                # Return milestone if it's current (within 30 days) and not completed
                if (milestone_date >= as_of_date and 
                    (milestone_date - as_of_date).days <= 30 and 
                    status != 'completed'):
                    return milestone
        
        return None
    
    def get_overdue_milestones(self, as_of_date: date) -> List[Dict[str, Any]]:
        """Get list of overdue milestones."""
        if not self.milestones:
            return []
        
        overdue = []
        for milestone in self.milestones:
            if 'planned_date' in milestone:
                milestone_date = milestone['planned_date']
                if isinstance(milestone_date, str):
                    milestone_date = date.fromisoformat(milestone_date)
                
                status = milestone.get('status', 'planned')
                
                if milestone_date < as_of_date and status != 'completed':
                    overdue.append(milestone)
        
        return overdue
    
    def get_milestone_completion_rate(self) -> float:
        """Calculate milestone completion rate."""
        if not self.milestones:
            return 0.0
        
        completed = sum(1 for m in self.milestones if m.get('status') == 'completed')
        return (completed / len(self.milestones)) * 100
    
    def calculate_budget_utilization(self) -> Dict[str, float]:
        """Calculate budget utilization metrics."""
        return {
            'total_budget': self.total_budget,
            'budget_spent': self.budget_spent,
            'budget_committed': self.budget_committed,
            'budget_remaining': self.total_budget - self.budget_spent - self.budget_committed,
            'spend_rate': (self.budget_spent / self.total_budget) * 100,
            'commit_rate': ((self.budget_spent + self.budget_committed) / self.total_budget) * 100,
        }
    
    def get_project_health_score(self, as_of_date: date) -> Dict[str, Any]:
        """Calculate overall project health score."""
        health_factors = {}
        
        # Budget health (30% weight)
        budget_util = self.calculate_budget_utilization()
        if budget_util['commit_rate'] <= 100:
            health_factors['budget'] = 100 - budget_util['commit_rate']
        else:
            health_factors['budget'] = 0
        
        # Schedule health (30% weight)
        overdue_milestones = len(self.get_overdue_milestones(as_of_date))
        total_milestones = len(self.milestones) if self.milestones else 1
        health_factors['schedule'] = max(0, 100 - (overdue_milestones / total_milestones) * 100)
        
        # Progress health (40% weight)
        health_factors['progress'] = self.completion_percentage
        
        # Calculate weighted score
        overall_score = (
            health_factors['budget'] * 0.3 +
            health_factors['schedule'] * 0.3 +
            health_factors['progress'] * 0.4
        )
        
        return {
            'overall_score': round(overall_score, 1),
            'budget_health': round(health_factors['budget'], 1),
            'schedule_health': round(health_factors['schedule'], 1),
            'progress_health': round(health_factors['progress'], 1),
            'status': self.status,
            'risk_level': self.risk_level,
        }
    
    def get_project_summary(self, as_of_date: date) -> Dict[str, Any]:
        """Get comprehensive project summary."""
        health = self.get_project_health_score(as_of_date)
        budget_util = self.calculate_budget_utilization()
        
        return {
            'name': self.name,
            'project_manager': self.project_manager,
            'status': self.status,
            'priority': self.priority,
            'completion_percentage': self.completion_percentage,
            'total_budget': self.total_budget,
            'budget_spent': self.budget_spent,
            'budget_remaining': budget_util['budget_remaining'],
            'monthly_burn_rate': self.calculate_monthly_burn_rate(as_of_date),
            'active_milestone': self.get_active_milestone(as_of_date),
            'overdue_milestones': len(self.get_overdue_milestones(as_of_date)),
            'milestone_completion_rate': self.get_milestone_completion_rate(),
            'health_score': health['overall_score'],
            'risk_level': self.risk_level,
            'team_size': len(self.team_members) if self.team_members else 0,
            'planned_end_date': self.planned_end_date,
            'estimated_completion_date': self.estimated_completion_date,
        }
    
    def update_milestone_status(self, milestone_name: str, status: str, 
                               completion_date: Optional[date] = None) -> bool:
        """Update milestone status."""
        if not self.milestones:
            return False
        
        for milestone in self.milestones:
            if milestone.get('name') == milestone_name:
                milestone['status'] = status
                if completion_date:
                    milestone['actual_completion_date'] = completion_date
                return True
        
        return False
    
    def add_milestone(self, name: str, planned_date: date, 
                     deliverable: str, budget: Optional[float] = None) -> None:
        """Add a new milestone to the project."""
        if not self.milestones:
            self.milestones = []
        
        milestone = {
            'name': name,
            'planned_date': planned_date,
            'deliverable': deliverable,
            'status': 'planned',
        }
        
        if budget:
            milestone['budget'] = budget
        
        self.milestones.append(milestone)