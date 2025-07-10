# Agentic AI Testing Task Orchestration

## Overview

This document provides a structured breakdown of testing tasks optimized for parallel execution by agentic AI systems. Each task is independent, well-defined, and includes specific instructions for AI agents.

## Task Categories

### Category A: Unit Test Validation (Parallel Execution)
**Execution Mode**: Independent parallel tasks  
**Dependencies**: None  
**Estimated Time**: 5-10 minutes per task  

### Category B: Integration Test Execution (Sequential with Parallel Subtasks)
**Execution Mode**: Sequential main tasks, parallel subtasks  
**Dependencies**: Category A completion recommended  
**Estimated Time**: 15-30 minutes per task  

### Category C: Performance Analysis (Resource-Intensive)
**Execution Mode**: Sequential execution (resource constraints)  
**Dependencies**: Categories A & B completion  
**Estimated Time**: 30-60 minutes per task  

---

## CATEGORY A: UNIT TEST VALIDATION TASKS

### Task A1: Model Validation Testing
**Agent Role**: Model Test Specialist  
**Objective**: Validate all entity models and business logic  

#### Instructions for AI Agent:
1. **Execute Command**: `poetry run pytest tests/test_models.py -v --tb=short`
2. **Analyze Results**: Check for failures in entity creation, validation, calculations
3. **Validate Coverage**: Ensure >95% code coverage for models package
4. **Report Format**: JSON output with test results, coverage metrics, failure analysis

#### Success Criteria:
- [ ] All model tests pass (100% success rate)
- [ ] Code coverage >95% for `src/cashcow/models/`
- [ ] No validation logic errors
- [ ] All entity types properly tested

#### Failure Handling:
```bash
# If failures occur, run individual test classes
poetry run pytest tests/test_models.py::TestEmployee -v
poetry run pytest tests/test_models.py::TestGrant -v
# Continue for each entity type
```

#### Expected Output Schema:
```json
{
  "task_id": "A1",
  "status": "success|failure",
  "test_results": {
    "total_tests": 45,
    "passed": 45,
    "failed": 0,
    "coverage_percentage": 96.2
  },
  "failures": [],
  "recommendations": []
}
```

---

### Task A2: Calculator Function Testing
**Agent Role**: Calculator Test Specialist  
**Objective**: Validate all financial calculation functions  

#### Instructions for AI Agent:
1. **Execute Command**: `poetry run pytest tests/test_calculators.py -v --tb=short`
2. **Verify Functions**: Test all calculator functions for accuracy
3. **Check Registry**: Validate calculator registration and lookup
4. **Edge Cases**: Confirm handling of zero values, future dates, invalid entities

#### Success Criteria:
- [ ] All calculator tests pass (100% success rate)
- [ ] Financial calculations mathematically correct
- [ ] Registry functions properly
- [ ] Edge cases handled gracefully

#### Specific Validations:
```python
# Example validation checks for AI agent
assert salary_calculator(employee, context) == expected_monthly_salary
assert equity_calculator(employee, context) == expected_monthly_vesting
assert depreciation_calculator(equipment, context) == expected_depreciation
```

---

### Task A3: Storage Layer Testing
**Agent Role**: Storage Test Specialist  
**Objective**: Validate data persistence and retrieval operations  

#### Instructions for AI Agent:
1. **Execute Command**: `poetry run pytest tests/test_storage.py -v --tb=short`
2. **Database Operations**: Test CRUD operations for all entity types
3. **YAML Loading**: Validate file parsing and entity creation
4. **Concurrency**: Check thread-safe operations

#### Success Criteria:
- [ ] All storage tests pass (100% success rate)
- [ ] Database integrity maintained
- [ ] YAML parsing robust
- [ ] Concurrent access safe

---

## CATEGORY B: INTEGRATION TEST EXECUTION

### Task B1: End-to-End Workflow Testing
**Agent Role**: Integration Test Lead  
**Objective**: Validate complete forecast generation pipeline  

#### Instructions for AI Agent:
1. **Setup Environment**: Create temporary test environment
2. **Execute Command**: `poetry run pytest tests/test_integration.py::TestEndToEndForecast -v`
3. **Validate Pipeline**: Ensure complete workflow from entity loading to forecast output
4. **Check Data Integrity**: Verify mathematical consistency across all calculations

#### Pre-execution Checklist:
```bash
# Agent should verify these conditions before starting
poetry run python -c "import src.cashcow; print('Import successful')"
ls tests/test_integration.py  # Verify test file exists
poetry run pytest --collect-only tests/test_integration.py  # Verify test discovery
```

#### Success Criteria:
- [ ] Complete 24-month forecast generated successfully
- [ ] All entity types contribute to calculations
- [ ] Mathematical consistency verified (revenue - expenses = net_cashflow)
- [ ] Cumulative calculations accurate

---

### Task B2: Scenario Management Testing
**Agent Role**: Scenario Test Specialist  
**Objective**: Validate scenario creation, comparison, and Monte Carlo simulations  

#### Instructions for AI Agent:
1. **Execute Command**: `poetry run pytest tests/test_scenarios.py -v`
2. **Scenario Creation**: Test best/worst/realistic scenario generation
3. **Parameter Overrides**: Validate entity parameter modifications
4. **Monte Carlo**: Check simulation convergence and statistical validity

#### Parallel Subtasks:
- **B2a**: Basic scenario creation and management
- **B2b**: Parameter override functionality  
- **B2c**: Monte Carlo simulation validation
- **B2d**: Risk analysis calculations

---

### Task B3: Report Generation Testing
**Agent Role**: Report Test Specialist  
**Objective**: Validate all report generation capabilities  

#### Instructions for AI Agent:
1. **Execute Command**: `poetry run pytest tests/test_reports.py -v`
2. **Chart Generation**: Verify matplotlib chart creation and accuracy
3. **Export Functions**: Test CSV/Excel export integrity
4. **Template Rendering**: Check HTML report generation

#### Output Validation:
```python
# Agent should verify these outputs exist and are valid
assert os.path.exists("test_report.html")
assert os.path.exists("test_forecast.csv")
assert plt.gcf().get_axes()  # Chart was created
```

---

## CATEGORY C: PERFORMANCE ANALYSIS TASKS

### Task C1: Scale Performance Testing
**Agent Role**: Performance Test Engineer  
**Objective**: Validate system performance with large datasets  

#### Instructions for AI Agent:
1. **Resource Monitoring**: Start memory and CPU monitoring
2. **Execute Command**: `poetry run pytest tests/test_performance.py -v -s`
3. **Benchmark Collection**: Record execution times and memory usage
4. **Threshold Validation**: Ensure performance meets defined limits

#### Performance Thresholds:
```yaml
max_memory_usage: 100MB  # For 100 entities
max_execution_time: 30s  # For 24-month forecast
min_entities_supported: 1000
max_forecast_months: 60
```

#### Monitoring Commands:
```bash
# Agent should run these in parallel with tests
top -p $PYTEST_PID -n 1 > memory_usage.log &
time poetry run pytest tests/test_performance.py > performance.log
```

---

### Task C2: Parallel Execution Benchmarking
**Agent Role**: Concurrency Test Engineer  
**Objective**: Validate and benchmark parallel processing capabilities  

#### Instructions for AI Agent:
1. **Baseline Measurement**: Record single-threaded performance
2. **Execute Command**: `poetry run pytest tests/test_parallel_benchmarks.py -v`
3. **Speedup Analysis**: Calculate parallel execution speedup ratios
4. **Resource Utilization**: Monitor CPU core utilization

#### Expected Metrics:
- Thread pool speedup: 2-4x on 4-core system
- Process pool speedup: 3-6x on 4-core system  
- Async concurrency: 5-10x for I/O-bound operations
- Memory overhead: <20% increase for parallel execution

---

### Task C3: Memory Profiling Analysis
**Agent Role**: Memory Analysis Engineer  
**Objective**: Analyze memory usage patterns and detect leaks  

#### Instructions for AI Agent:
1. **Profile Execution**: `poetry run python -m memory_profiler tests/test_memory_profiling.py`
2. **Leak Detection**: Monitor memory growth patterns
3. **Scaling Analysis**: Verify linear memory scaling with entity count
4. **Optimization Recommendations**: Identify memory optimization opportunities

#### Analysis Commands:
```bash
# Agent should execute these profiling commands
mprof run --python python -m pytest tests/test_memory_profiling.py
mprof plot --output memory_profile.png
poetry run python -c "import gc; gc.collect(); print(f'Objects: {len(gc.get_objects())}')"
```

---

## TASK ORCHESTRATION GUIDELINES

### Parallel Execution Strategy

#### Phase 1: Unit Test Validation (Parallel)
```yaml
parallel_tasks:
  - task_id: A1
    command: "poetry run pytest tests/test_models.py -v --json-report --json-report-file=A1_results.json"
    timeout: 600
    
  - task_id: A2  
    command: "poetry run pytest tests/test_calculators.py -v --json-report --json-report-file=A2_results.json"
    timeout: 600
    
  - task_id: A3
    command: "poetry run pytest tests/test_storage.py -v --json-report --json-report-file=A3_results.json"
    timeout: 600
```

#### Phase 2: Integration Testing (Sequential with Parallel Subtasks)
```yaml
sequential_tasks:
  - task_id: B1
    depends_on: [A1, A2, A3]
    subtasks:
      - B1a: "pytest tests/test_integration.py::TestEndToEndForecast::test_complete_forecast_workflow"
      - B1b: "pytest tests/test_integration.py::TestEndToEndForecast::test_async_forecast_calculation"
      - B1c: "pytest tests/test_integration.py::TestEndToEndForecast::test_parallel_forecast_calculation"
    parallel_subtasks: true
    
  - task_id: B2
    depends_on: [B1]
    parallel_subtasks: true
    
  - task_id: B3  
    depends_on: [B1]
    parallel_subtasks: true
```

#### Phase 3: Performance Analysis (Sequential)
```yaml
sequential_tasks:
  - task_id: C1
    depends_on: [B1, B2, B3]
    resource_requirements:
      memory: "2GB"
      cpu_cores: 4
      
  - task_id: C2
    depends_on: [C1]
    resource_requirements:
      memory: "2GB" 
      cpu_cores: 4
      
  - task_id: C3
    depends_on: [C1]
    resource_requirements:
      memory: "4GB"
      cpu_cores: 2
```

### Agent Communication Protocol

#### Task Result Schema
```json
{
  "agent_id": "agent_001",
  "task_id": "A1",
  "status": "success|failure|timeout",
  "start_time": "2025-07-10T10:00:00Z",
  "end_time": "2025-07-10T10:05:00Z",
  "execution_log": "...",
  "test_results": {
    "total": 45,
    "passed": 43,
    "failed": 2,
    "errors": []
  },
  "performance_metrics": {
    "execution_time": 300,
    "memory_peak": "150MB",
    "cpu_utilization": 85
  },
  "artifacts": [
    "test_results.json",
    "coverage_report.html",
    "performance_log.txt"
  ]
}
```

#### Failure Escalation
1. **Automatic Retry**: Failed tasks retry once automatically
2. **Dependency Halt**: Dependent tasks wait for failure resolution
3. **Human Intervention**: Complex failures escalate to human review
4. **Partial Success**: Continue with successful components

### Resource Management

#### Memory Allocation
- **Unit Tests**: 512MB per agent
- **Integration Tests**: 1GB per agent  
- **Performance Tests**: 2-4GB per agent
- **Memory Profiling**: 4GB+ per agent

#### CPU Allocation  
- **Unit Tests**: 1 core per agent
- **Integration Tests**: 2 cores per agent
- **Performance Tests**: 4 cores per agent
- **Parallel Benchmarks**: All available cores

#### Disk Space
- **Temporary Files**: 1GB per agent
- **Test Artifacts**: 500MB per agent
- **Log Files**: 100MB per agent

### Quality Gates

#### Phase 1 Success Criteria
- All unit tests pass (100% success rate)
- Code coverage >95% for core modules
- No critical validation failures

#### Phase 2 Success Criteria  
- End-to-end workflow completes successfully
- Integration scenarios pass
- Report generation functional

#### Phase 3 Success Criteria
- Performance within defined thresholds
- No memory leaks detected
- Parallel execution demonstrates expected speedup

### Monitoring and Alerting

#### Real-time Monitoring
```yaml
metrics:
  - test_execution_time
  - memory_usage_peak
  - cpu_utilization
  - test_failure_rate
  - coverage_percentage

alerts:
  - condition: "test_failure_rate > 5%"
    action: "pause_dependent_tasks"
  - condition: "memory_usage > 8GB"
    action: "terminate_task"
  - condition: "execution_time > 30min"
    action: "escalate_to_human"
```

#### Progress Reporting
```python
# Agent should report progress every 30 seconds
progress_report = {
    "task_id": "A1",
    "progress_percentage": 65,
    "current_test": "test_employee_equity_calculation",
    "tests_completed": 29,
    "tests_remaining": 16,
    "estimated_completion": "2025-07-10T10:03:00Z"
}
```

---

**Orchestration Version**: 1.0  
**Compatible AI Systems**: Claude, GPT-4, Local LLMs with function calling  
**Last Updated**: 2025-07-10  
**Review Cycle**: After each major test suite update