# AI Agent Instructions for CashCow Testing

## Quick Start for AI Agents

### Prerequisites Check
```bash
# Verify environment before starting any task
cd  ~/cashcow
poetry --version  # Should show Poetry 1.0+
poetry run python --version  # Should show Python 3.10+
poetry run pytest --version  # Should show pytest 8.0+
```

### Agent Role Assignment
When assigned a task, identify your role:
- **Model Test Specialist** → Execute Task A1
- **Calculator Test Specialist** → Execute Task A2  
- **Storage Test Specialist** → Execute Task A3
- **Integration Test Lead** → Execute Task B1
- **Scenario Test Specialist** → Execute Task B2
- **Report Test Specialist** → Execute Task B3
- **Performance Test Engineer** → Execute Task C1
- **Concurrency Test Engineer** → Execute Task C2
- **Memory Analysis Engineer** → Execute Task C3

---

## EXECUTION TEMPLATES

### Template A: Unit Test Execution
```bash
#!/bin/bash
# Agent Template for Unit Tests (Tasks A1, A2, A3)

TASK_ID="$1"  # A1, A2, or A3
START_TIME=$(date -Iseconds)

echo "Starting Task $TASK_ID at $START_TIME"

# Map task to test file
case $TASK_ID in
    "A1") TEST_FILE="tests/test_models.py" ;;
    "A2") TEST_FILE="tests/test_calculators.py" ;;
    "A3") TEST_FILE="tests/test_storage.py" ;;
    *) echo "Invalid task ID"; exit 1 ;;
esac

# Execute test with detailed output
poetry run pytest $TEST_FILE \
    -v \
    --tb=short \
    --json-report \
    --json-report-file=${TASK_ID}_results.json \
    --cov=cashcow \
    --cov-report=html:${TASK_ID}_coverage \
    --cov-report=json:${TASK_ID}_coverage.json

EXIT_CODE=$?
END_TIME=$(date -Iseconds)

# Generate agent report
cat > ${TASK_ID}_agent_report.json << EOF
{
    "agent_id": "$(hostname)_$$",
    "task_id": "$TASK_ID",
    "status": "$([ $EXIT_CODE -eq 0 ] && echo success || echo failure)",
    "start_time": "$START_TIME",
    "end_time": "$END_TIME",
    "exit_code": $EXIT_CODE,
    "test_file": "$TEST_FILE",
    "artifacts": [
        "${TASK_ID}_results.json",
        "${TASK_ID}_coverage.json",
        "${TASK_ID}_coverage/"
    ]
}
EOF

echo "Task $TASK_ID completed with exit code $EXIT_CODE"
exit $EXIT_CODE
```

### Template B: Integration Test Execution
```bash
#!/bin/bash
# Agent Template for Integration Tests (Tasks B1, B2, B3)

TASK_ID="$1"
SUBTASK="$2"  # Optional subtask identifier
START_TIME=$(date -Iseconds)

echo "Starting Integration Task $TASK_ID${SUBTASK:+:$SUBTASK} at $START_TIME"

# Map task to test class/method
case $TASK_ID in
    "B1") 
        if [ -n "$SUBTASK" ]; then
            case $SUBTASK in
                "a") TEST_TARGET="tests/test_integration.py::TestEndToEndForecast::test_complete_forecast_workflow" ;;
                "b") TEST_TARGET="tests/test_integration.py::TestEndToEndForecast::test_async_forecast_calculation" ;;
                "c") TEST_TARGET="tests/test_integration.py::TestEndToEndForecast::test_parallel_forecast_calculation" ;;
                *) TEST_TARGET="tests/test_integration.py::TestEndToEndForecast" ;;
            esac
        else
            TEST_TARGET="tests/test_integration.py::TestEndToEndForecast"
        fi
        ;;
    "B2") TEST_TARGET="tests/test_scenarios.py" ;;
    "B3") TEST_TARGET="tests/test_reports.py" ;;
    *) echo "Invalid integration task ID"; exit 1 ;;
esac

# Execute integration test with monitoring
poetry run pytest $TEST_TARGET \
    -v \
    -s \
    --tb=long \
    --json-report \
    --json-report-file=${TASK_ID}${SUBTASK:+_$SUBTASK}_results.json \
    --durations=10

EXIT_CODE=$?
END_TIME=$(date -Iseconds)

# Check for common integration issues
if [ $EXIT_CODE -ne 0 ]; then
    echo "Integration test failed. Common troubleshooting:"
    echo "1. Check database connections"
    echo "2. Verify file permissions for temporary directories"
    echo "3. Ensure all dependencies are installed"
    echo "4. Check for port conflicts"
fi

cat > ${TASK_ID}${SUBTASK:+_$SUBTASK}_agent_report.json << EOF
{
    "agent_id": "$(hostname)_$$",
    "task_id": "$TASK_ID",
    "subtask": "${SUBTASK:-null}",
    "status": "$([ $EXIT_CODE -eq 0 ] && echo success || echo failure)",
    "start_time": "$START_TIME", 
    "end_time": "$END_TIME",
    "exit_code": $EXIT_CODE,
    "test_target": "$TEST_TARGET"
}
EOF

exit $EXIT_CODE
```

### Template C: Performance Test Execution
```bash
#!/bin/bash
# Agent Template for Performance Tests (Tasks C1, C2, C3)

TASK_ID="$1"
START_TIME=$(date -Iseconds)

echo "Starting Performance Task $TASK_ID at $START_TIME"

# Setup performance monitoring
MONITOR_PID=""
case $TASK_ID in
    "C1"|"C2")
        # CPU and memory monitoring
        top -b -d 1 -p $$ > ${TASK_ID}_system_monitor.log &
        MONITOR_PID=$!
        ;;
    "C3")
        # Memory profiling specific setup
        export PYTHONPATH=" ~/cashcow/src:$PYTHONPATH"
        ;;
esac

# Map task to performance test
case $TASK_ID in
    "C1") 
        TEST_TARGET="tests/test_performance.py"
        RESOURCE_LIMIT="--maxfail=1 --timeout=1800"  # 30 min timeout
        ;;
    "C2") 
        TEST_TARGET="tests/test_parallel_benchmarks.py"
        RESOURCE_LIMIT="--maxfail=1 --timeout=1800"
        ;;
    "C3") 
        # Memory profiling requires special handling
        echo "Executing memory profiling..."
        poetry run python -m memory_profiler tests/test_memory_profiling.py > ${TASK_ID}_memory_output.log 2>&1
        EXIT_CODE=$?
        
        # Generate memory profile plot if mprof is available
        if command -v mprof >/dev/null 2>&1; then
            mprof run --python poetry run python tests/test_memory_profiling.py
            mprof plot --output ${TASK_ID}_memory_profile.png
        fi
        
        END_TIME=$(date -Iseconds)
        cat > ${TASK_ID}_agent_report.json << EOF
{
    "agent_id": "$(hostname)_$$",
    "task_id": "$TASK_ID",
    "status": "$([ $EXIT_CODE -eq 0 ] && echo success || echo failure)",
    "start_time": "$START_TIME",
    "end_time": "$END_TIME",
    "exit_code": $EXIT_CODE,
    "memory_profile": "${TASK_ID}_memory_profile.png",
    "memory_output": "${TASK_ID}_memory_output.log"
}
EOF
        
        [ -n "$MONITOR_PID" ] && kill $MONITOR_PID 2>/dev/null
        exit $EXIT_CODE
        ;;
    *) echo "Invalid performance task ID"; exit 1 ;;
esac

# Execute performance test
poetry run pytest $TEST_TARGET \
    -v \
    -s \
    --tb=short \
    $RESOURCE_LIMIT \
    --json-report \
    --json-report-file=${TASK_ID}_results.json

EXIT_CODE=$?
END_TIME=$(date -Iseconds)

# Stop monitoring
[ -n "$MONITOR_PID" ] && kill $MONITOR_PID 2>/dev/null

# Analyze performance results
if [ $EXIT_CODE -eq 0 ]; then
    echo "Performance test completed successfully"
    # Extract performance metrics from test output
    if [ -f "${TASK_ID}_results.json" ]; then
        TOTAL_TIME=$(python3 -c "
import json
with open('${TASK_ID}_results.json') as f:
    data = json.load(f)
    print(data.get('summary', {}).get('total', 0))
" 2>/dev/null || echo "unknown")
        echo "Total execution time: $TOTAL_TIME seconds"
    fi
else
    echo "Performance test failed - may indicate performance regression"
fi

cat > ${TASK_ID}_agent_report.json << EOF
{
    "agent_id": "$(hostname)_$$",
    "task_id": "$TASK_ID",
    "status": "$([ $EXIT_CODE -eq 0 ] && echo success || echo failure)",
    "start_time": "$START_TIME",
    "end_time": "$END_TIME", 
    "exit_code": $EXIT_CODE,
    "test_target": "$TEST_TARGET",
    "system_monitor": "${TASK_ID}_system_monitor.log"
}
EOF

exit $EXIT_CODE
```

---

## AGENT DECISION FLOWCHARTS

### Task Assignment Decision Tree
```
Assigned Task ID?
├── A1, A2, A3 → Use Template A (Unit Tests)
├── B1, B2, B3 → Use Template B (Integration Tests)  
├── C1, C2, C3 → Use Template C (Performance Tests)
└── Unknown → Request clarification

Dependencies Met?
├── Category A → No dependencies, proceed
├── Category B → Check if Category A completed
├── Category C → Check if Categories A & B completed
└── Dependencies not met → Wait or request dependency status

Resource Requirements?
├── Unit Tests → 512MB RAM, 1 CPU core
├── Integration Tests → 1GB RAM, 2 CPU cores
├── Performance Tests → 2-4GB RAM, 4 CPU cores
└── Insufficient resources → Request resource allocation
```

### Failure Recovery Decision Tree
```
Test Failed?
├── Unit Test Failure
│   ├── Import Error → Check dependencies: poetry install
│   ├── Calculation Error → Mathematical logic issue, escalate
│   ├── Validation Error → Data model issue, escalate
│   └── Unknown → Retry once, then escalate
├── Integration Test Failure
│   ├── Database Error → Check temp directory permissions
│   ├── Timeout → Increase timeout, retry
│   ├── Memory Error → Request more resources
│   └── Logic Error → Complex issue, escalate
└── Performance Test Failure
    ├── Timeout → Expected for stress tests, analyze partial results
    ├── Memory Exceeded → Reduce dataset size, retry
    ├── Threshold Exceeded → Performance regression, escalate
    └── System Error → Infrastructure issue, escalate
```

---

## ERROR HANDLING PROTOCOLS

### Common Error Scenarios

#### Import Errors
```bash
# If you encounter import errors
poetry install  # Reinstall dependencies
poetry run python -c "import src.cashcow"  # Test import

# If still failing
export PYTHONPATH=" ~/cashcow/src:$PYTHONPATH"
poetry run python -c "import cashcow"
```

#### Database Errors
```bash
# If database connection fails
rm -f /tmp/test_*.db  # Clean up old test databases
mkdir -p /tmp/test_entities  # Ensure temp directories exist
chmod 755 /tmp/test_entities
```

#### Memory Errors
```bash
# If memory tests fail
free -h  # Check available memory
ulimit -v 4194304  # Limit virtual memory to 4GB
# Reduce dataset size in test configuration
```

#### Permission Errors
```bash
# If file permission errors
chmod +w tests/
chmod +w /tmp/
# Ensure agent has write access to working directory
```

### Escalation Triggers

#### Automatic Retry (1 attempt)
- Network timeouts
- Temporary file system errors
- Memory allocation failures (with reduced requirements)

#### Human Escalation Required
- Mathematical calculation errors
- Data corruption detected
- Security violations
- Resource exhaustion after retry
- Multiple test failures (>10% failure rate)

#### Partial Success Handling
- Continue with successful test components
- Document failed components clearly
- Provide recommendations for manual investigation

---

## COMMUNICATION PROTOCOLS

### Progress Reporting (Every 30 seconds)
```json
{
    "agent_id": "agent_001",
    "task_id": "A1", 
    "status": "running",
    "progress": {
        "percentage": 65,
        "current_test": "test_employee_equity_calculation",
        "completed": 29,
        "remaining": 16,
        "estimated_completion": "2025-07-10T10:03:00Z"
    },
    "resources": {
        "memory_mb": 145,
        "cpu_percent": 85
    }
}
```

### Final Report Schema
```json
{
    "agent_id": "agent_001",
    "task_id": "A1",
    "status": "success|failure|partial",
    "execution_summary": {
        "start_time": "2025-07-10T10:00:00Z",
        "end_time": "2025-07-10T10:05:30Z",
        "duration_seconds": 330,
        "exit_code": 0
    },
    "test_results": {
        "total_tests": 45,
        "passed": 43,
        "failed": 2,
        "skipped": 0,
        "failure_details": [
            {
                "test_name": "test_complex_equity_vesting",
                "error_type": "AssertionError",
                "error_message": "Expected 2083.33, got 2083.34"
            }
        ]
    },
    "performance_metrics": {
        "execution_time_seconds": 330,
        "peak_memory_mb": 145,
        "average_cpu_percent": 85,
        "coverage_percentage": 96.2
    },
    "artifacts": [
        "A1_results.json",
        "A1_coverage.json", 
        "A1_agent_report.json"
    ],
    "recommendations": [
        "Review floating-point precision in equity calculations",
        "Consider adding tolerance to financial calculations"
    ],
    "next_steps": [
        "Task A2 can proceed",
        "Address floating-point precision issue before production"
    ]
}
```

### Inter-Agent Coordination
```json
{
    "message_type": "dependency_check",
    "requesting_agent": "agent_002",
    "requested_task": "B1",
    "dependencies": ["A1", "A2", "A3"],
    "dependency_status": {
        "A1": "completed_success",
        "A2": "completed_success", 
        "A3": "running"
    },
    "can_proceed": false,
    "wait_for": ["A3"]
}
```

---

## QUALITY ASSURANCE CHECKLISTS

### Pre-Execution Checklist
- [ ] Working directory: ` ~/cashcow`
- [ ] Poetry environment activated
- [ ] Dependencies installed (`poetry install`)
- [ ] Test files exist and are readable
- [ ] Sufficient system resources available
- [ ] No conflicting processes running
- [ ] Temporary directories writable

### Post-Execution Checklist
- [ ] All test artifacts generated
- [ ] Agent report created
- [ ] Exit code documented
- [ ] Performance metrics captured
- [ ] Cleanup completed (temp files removed)
- [ ] Results uploaded/shared
- [ ] Dependent agents notified

### Quality Gates
- [ ] **Unit Tests**: >95% pass rate required
- [ ] **Integration Tests**: 100% pass rate required
- [ ] **Performance Tests**: Within defined thresholds
- [ ] **Code Coverage**: >90% for modified code
- [ ] **Memory Usage**: Within allocation limits
- [ ] **Execution Time**: Within timeout limits

---

**Agent Instructions Version**: 1.0  
**Compatible Systems**: Bash 4.0+, Python 3.10+, Poetry 1.0+  
**Last Updated**: 2025-07-10  
**Emergency Contact**: Human supervisor for complex failures