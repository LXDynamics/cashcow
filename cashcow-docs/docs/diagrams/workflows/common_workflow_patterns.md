# Common Workflow Patterns

This document contains Mermaid diagrams showing the most common user workflows in CashCow CLI.

## 1. Initial Project Setup Workflow

```mermaid
flowchart TD
    START([Start New Project]) --> MKDIR[Create Directory Structure</br>mkdir -p entities/revenue,expenses,projects]
    MKDIR --> ADD_TEAM[Add Core Team Members]
    ADD_TEAM --> ADD_COSTS[Add Initial Costs]
    ADD_COSTS --> FIX_ENTITIES
    ADD_TEAM --> ADD_CEO[cashcow add --type employee --name 'CEO' --interactive]
    ADD_CEO --> ADD_CTO[cashcow add --type employee --name 'CTO' --interactive]
    ADD_CTO --> ADD_ENG[cashcow add --type employee --name 'Engineer' --interactive]
    
    ADD_COSTS --> ADD_OFFICE[cashcow add --type facility --name 'Office Lease' --interactive]
    ADD_OFFICE --> ADD_SOFTWARE[cashcow add --type software --name 'Development Tools' --interactive]
    
    FIX_ENTITIES --> VALIDATE[cashcow validate]
    VALIDATE --> VALIDATE_OK{All Valid?}
    VALIDATE_OK -->|No| FIX_ENTITIES[Fix Entity Issues]
    VALIDATE_OK -->|Yes| INITIAL_FORECAST[cashcow forecast --months 18 --kpis]
    
    INITIAL_FORECAST --> REVIEW[Review Initial Metrics]
    REVIEW --> ADJUST{Need Adjustments?}
    ADJUST -->|Yes| MODIFY_ENTITIES[Modify Entity Files]
    MODIFY_ENTITIES --> VALIDATE
    ADJUST -->|No| COMPLETE([Setup Complete])
    
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#050505
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#050505
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#050505
    classDef action fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#050505
    
    class START startEnd
    class COMPLETE startEnd
    class ADD_OFFICE command
    class ADD_CEO command
    class INITIAL_FORECAST command
    class ADD_SOFTWARE command
    class ADD_CTO command
    class ADD_ENG command
    class VALIDATE command
    class VALIDATE_OK decision
    class ADJUST decision
    class MKDIR action
    class ADD_TEAM action
    class ADD_COSTS action
    class FIX_ENTITIES action
    class REVIEW action
    class MODIFY_ENTITIES action
```

## 2. Monthly Financial Review Workflow

```mermaid
flowchart TD
    MONTHLY([Monthly Review Day]) --> CHECK_ACTIVE[cashcow list --active]
    CHECK_ACTIVE --> FORECAST_SHORT[cashcow forecast --months 6 --format csv --output monthly.csv]
    FORECAST_SHORT --> FORECAST_LONG[cashcow forecast --months 24 --format csv --output longterm.csv]
    
    FORECAST_LONG --> KPI_CHECK[cashcow kpi --alerts]
    KPI_CHECK --> HAS_ALERTS{Alerts Found?}
    
    HAS_ALERTS -->|Yes| CRITICAL{Critical Alerts?}
    CRITICAL -->|Yes| IMMEDIATE_ACTION[Take Immediate Action • Reduce burn rate • Accelerate revenue]
    CRITICAL -->|No| PLAN_ACTION[Plan Corrective Actions]
    
    HAS_ALERTS -->|No| FULL_KPI[cashcow kpi --months 12]
    PLAN_ACTION --> FULL_KPI
    IMMEDIATE_ACTION --> FULL_KPI
    
    FULL_KPI --> EXPORT_REPORT[Export Full Analysis cashcow forecast --kpis --output full_report.csv]
    EXPORT_REPORT --> DOCUMENT[Document Key Insights]
    DOCUMENT --> SHARE[Share with Stakeholders]
    SHARE --> SCHEDULE_NEXT([Schedule Next Review])
    
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#505050
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#050505
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#050505
    classDef alert fill:#fff8e1,stroke:#d32f2f,stroke-width:2px,color:#050505
    classDef action fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#050505
    
    class MONTHLY,SCHEDULE_NEXT startEnd
    class CHECK_ACTIVE,FORECAST_SHORT,FORECAST_LONG,KPI_CHECK,FULL_KPI,EXPORT_REPORT command
    class HAS_ALERTS,CRITICAL decision
    class IMMEDIATE_ACTION,PLAN_ACTION alert
    class DOCUMENT,SHARE action
```

## 3. Hiring Decision Workflow

```mermaid
flowchart TD
    HIRING_NEED([Need to Hire]) --> CURRENT_STATE[cashcow forecast --months 12 --kpis]
    CURRENT_STATE --> CHECK_RUNWAY[Check Current Runway]
    CHECK_RUNWAY --> RUNWAY_OK{Runway > 18 months?}
    
    RUNWAY_OK -->|No| DELAY_HIRE[Consider Delaying Hire or Reduce Other Costs]
    RUNWAY_OK -->|Yes| ADD_CANDIDATE[cashcow add --type employee --name 'New Hire' --interactive]
    
    ADD_CANDIDATE --> FORECAST_WITH_HIRE[cashcow forecast --months 18 --kpis]
    FORECAST_WITH_HIRE --> NEW_RUNWAY[Check New Runway]
    NEW_RUNWAY --> RUNWAY_STILL_OK{Still > 12 months?}
    
    RUNWAY_STILL_OK -->|No| ADJUST_SALARY[Adjust Salary/Benefits or Reconsider Hire]
    RUNWAY_STILL_OK -->|Yes| REVENUE_IMPACT[Estimate Revenue Impact]
    
    REVENUE_IMPACT --> ROI_CALC[Calculate ROI Revenue Increase vs Cost]
    ROI_CALC --> ROI_POSITIVE{Positive ROI?}
    
    ROI_POSITIVE -->|Yes| APPROVE_HIRE[Approve Hire]
    ROI_POSITIVE -->|No| RECONSIDER[Reconsider or Adjust Expectations]
    
    DELAY_HIRE --> REASSESS[Reassess in 1-3 months]
    ADJUST_SALARY --> FORECAST_WITH_HIRE
    RECONSIDER --> DELAY_HIRE
    APPROVE_HIRE --> MONITOR[Monitor Impact Monthly]
    
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#050505
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#050505
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#050505
    classDef caution fill:#fff8e1,stroke:#d32f2f,stroke-width:2px,color:#050505
    classDef positive fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#050505
    
    class HIRING_NEED startEnd
    class CURRENT_STATE,ADD_CANDIDATE,FORECAST_WITH_HIRE command
    class RUNWAY_OK,RUNWAY_STILL_OK,ROI_POSITIVE decision
    class DELAY_HIRE,ADJUST_SALARY,RECONSIDER caution
    class APPROVE_HIRE,MONITOR positive
```

## 4. Grant Application Workflow

```mermaid
flowchart TD
    GRANT_OPPORTUNITY([Grant Opportunity]) --> RESEARCH[Research Grant Requirements]
    RESEARCH --> ESTIMATE_AMOUNT[Estimate Grant Amount and Timeline]
    
    ESTIMATE_AMOUNT --> ADD_OPTIMISTIC[Create Optimistic Scenario cashcow add --type grant --name 'Potential Grant']
    ADD_OPTIMISTIC --> FORECAST_WITH[cashcow forecast --months 36 --scenario optimistic]
    
    FORECAST_WITH --> IMPACT_ANALYSIS[Analyze Impact on • Runway • Growth Capability • Team Expansion]
    IMPACT_ANALYSIS --> WORTH_EFFORT{Worth the Effort?}
    
    WORTH_EFFORT -->|No| SKIP_GRANT[Skip Grant Application]
    WORTH_EFFORT -->|Yes| APPLY[Submit Grant Application]
    
    APPLY --> WAIT_RESULT[Wait for Results]
    WAIT_RESULT --> GRANT_RESULT{Grant Awarded?}
    
    GRANT_RESULT -->|No| REMOVE_SCENARIO[Remove Optimistic Entity Return to Baseline]
    GRANT_RESULT -->|Yes| UPDATE_ENTITY[Update Grant Entity with Actual Terms]
    
    UPDATE_ENTITY --> NEW_FORECAST[cashcow forecast --months 36 --kpis]
    NEW_FORECAST --> PLAN_USAGE[Plan Grant Fund Usage • Milestones • Reporting • Deliverables]
    
    PLAN_USAGE --> TRACK_PROGRESS[Track Monthly Progress Against Grant Terms]
    REMOVE_SCENARIO --> CONTINUE_BASELINE[Continue with Baseline Planning]
    
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#050505
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#050505
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#050505
    classDef success fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#050505
    classDef neutral fill:#fafafa,stroke:#616161,stroke-width:1px,color:#050505
    
    class GRANT_OPPORTUNITY startEnd
    class ADD_OPTIMISTIC,FORECAST_WITH,NEW_FORECAST command
    class WORTH_EFFORT,GRANT_RESULT decision
    class UPDATE_ENTITY,PLAN_USAGE,TRACK_PROGRESS success
    class SKIP_GRANT,REMOVE_SCENARIO,CONTINUE_BASELINE neutral
```

## 5. Crisis Management Workflow (Low Runway)

```mermaid
flowchart TD
    ALERT([Runway Alert: < 6 months]) --> IMMEDIATE_ASSESS[cashcow kpi --alerts cashcow forecast --months 12]
    
    IMMEDIATE_ASSESS --> EMERGENCY_MEETING[Emergency Team Meeting]
    EMERGENCY_MEETING --> IDENTIFY_OPTIONS[Identify Options: • Cost Reduction • Revenue Acceleration • Emergency Funding]
    
    IDENTIFY_OPTIONS --> COST_REDUCTION[Option 1: Cost Reduction]
    IDENTIFY_OPTIONS --> REVENUE_BOOST[Option 2: Revenue Boost]
    IDENTIFY_OPTIONS --> EMERGENCY_FUNDING[Option 3: Emergency Funding]
    
    COST_REDUCTION --> DEFER_HIRES[Defer New Hires]
    COST_REDUCTION --> REDUCE_SALARIES[Temporary Salary Cuts]
    COST_REDUCTION --> CUT_EXPENSES[Cut Non-Essential Expenses]
    
    REVENUE_BOOST --> ACCELERATE_SALES[Accelerate Sales Pipeline]
    REVENUE_BOOST --> NEW_PRODUCTS[Rush New Product Launch]
    REVENUE_BOOST --> CONSULTING[Emergency Consulting Services]
    
    EMERGENCY_FUNDING --> BRIDGE_LOAN[Bridge Loan]
    EMERGENCY_FUNDING --> EMERGENCY_INVESTOR[Emergency Investor]
    EMERGENCY_FUNDING --> CONVERTIBLE_NOTE[Convertible Note]
    
    DEFER_HIRES --> MODEL_CHANGES[Model All Changes]
    REDUCE_SALARIES --> MODEL_CHANGES
    CUT_EXPENSES --> MODEL_CHANGES
    ACCELERATE_SALES --> MODEL_CHANGES
    NEW_PRODUCTS --> MODEL_CHANGES
    CONSULTING --> MODEL_CHANGES
    BRIDGE_LOAN --> MODEL_CHANGES
    EMERGENCY_INVESTOR --> MODEL_CHANGES
    CONVERTIBLE_NOTE --> MODEL_CHANGES
    
    MODEL_CHANGES --> NEW_FORECAST[cashcow forecast --months 18 --kpis]
    NEW_FORECAST --> RUNWAY_FIXED{Runway > 12 months?}
    
    RUNWAY_FIXED -->|No| MORE_DRASTIC[More Drastic Measures • Layoffs • Office Closure • Pivot Strategy]
    RUNWAY_FIXED -->|Yes| IMPLEMENT[Implement Changes]
    
    MORE_DRASTIC --> MODEL_CHANGES
    IMPLEMENT --> MONITOR_WEEKLY[Weekly Monitoring cashcow kpi --alerts]
    
    classDef emergency fill:#fff8e1,stroke:#d32f2f,stroke-width:3px,color:#050505
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#050505
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#050505
    classDef option fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#050505
    classDef action fill:#e8f5e8,stroke:#2e7d32,stroke-width:1px,color:#050505
    
    class ALERT emergency
    class IMMEDIATE_ASSESS,NEW_FORECAST,MONITOR_WEEKLY command
    class RUNWAY_FIXED decision
    class COST_REDUCTION,REVENUE_BOOST,EMERGENCY_FUNDING option
    class DEFER_HIRES,REDUCE_SALARIES,CUT_EXPENSES,ACCELERATE_SALES,NEW_PRODUCTS,CONSULTING,BRIDGE_LOAN,EMERGENCY_INVESTOR,CONVERTIBLE_NOTE,MORE_DRASTIC action
```

## 6. Scenario Comparison Workflow

```mermaid
flowchart TD
    PLANNING([Strategic Planning]) --> CREATE_SCENARIOS[Create Multiple Scenarios]
    
    CREATE_SCENARIOS --> BASELINE[Baseline: Current Trajectory cashcow forecast --scenario baseline --output baseline.csv]
    CREATE_SCENARIOS --> OPTIMISTIC[Optimistic: 25% Growth cashcow forecast --scenario optimistic --output optimistic.csv]
    CREATE_SCENARIOS --> CONSERVATIVE[Conservative: Slow Growth cashcow forecast --scenario conservative --output conservative.csv]
    
    BASELINE --> COMPARE_KPI[Compare KPIs Across Scenarios]
    OPTIMISTIC --> COMPARE_KPI
    CONSERVATIVE --> COMPARE_KPI
    
    COMPARE_KPI --> BASELINE_KPI[cashcow kpi --scenario baseline]
    COMPARE_KPI --> OPTIMISTIC_KPI[cashcow kpi --scenario optimistic]
    COMPARE_KPI --> CONSERVATIVE_KPI[cashcow kpi --scenario conservative]
    
    BASELINE_KPI --> ANALYZE_DIFFERENCES[Analyze Key Differences: • Runway variations • Break-even points • Resource needs]
    OPTIMISTIC_KPI --> ANALYZE_DIFFERENCES
    CONSERVATIVE_KPI --> ANALYZE_DIFFERENCES
    
    ANALYZE_DIFFERENCES --> IDENTIFY_RISKS[Identify Scenario Risks • Market conditions • Competition • Resource constraints]
    
    IDENTIFY_RISKS --> PROBABILITY[Assign Probabilities • Conservative: 30% • Baseline: 50% • Optimistic: 20%]
    
    PROBABILITY --> WEIGHTED_PLAN[Create Weighted Plan Prepare for Most Likely Plan for Worst Case]
    
    WEIGHTED_PLAN --> MONITOR_INDICATORS[Monitor Leading Indicators • Sales pipeline • Market metrics • Competition]
    
    MONITOR_INDICATORS --> MONTHLY_ADJUST[Monthly Scenario Adjustment Update probabilities Shift strategies]
    
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#050505
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#050505
    classDef scenario fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#050505
    classDef analysis fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#050505
    
    class PLANNING startEnd
    class BASELINE,OPTIMISTIC,CONSERVATIVE,BASELINE_KPI,OPTIMISTIC_KPI,CONSERVATIVE_KPI command
    class COMPARE_KPI scenario
    class CREATE_SCENARIOS,ANALYZE_DIFFERENCES,IDENTIFY_RISKS,PROBABILITY,WEIGHTED_PLAN,MONITOR_INDICATORS,MONTHLY_ADJUST analysis
```