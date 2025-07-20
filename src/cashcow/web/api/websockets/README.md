# CashCow WebSocket Infrastructure

This directory contains the real-time WebSocket infrastructure for CashCow web GUI, providing live updates for calculations, entity changes, and system status.

## Architecture Overview

### Core Components

1. **Connection Manager** (`manager.py`)
   - Manages WebSocket connections with authentication and heartbeat
   - Handles subscription management for different topics
   - Provides broadcast functionality for real-time updates

2. **WebSocket Handlers** (`handlers.py`)
   - WebSocket endpoints for different update types
   - Broadcast functions for various notification types
   - Real-time progress updates and system alerts

3. **Background Jobs** (`../tasks/`)
   - Job manager for long-running calculations
   - Progress tracking with unique job IDs
   - Queue-based processing with concurrent workers

4. **File Integration** (`file_integration.py`)
   - Integrates existing file watchers with WebSocket notifications
   - Real-time entity file change notifications
   - Validation error broadcasting

5. **Models** (`../models/websockets.py`)
   - Pydantic models for all WebSocket messages
   - Job status and progress tracking models
   - Type-safe message handling

## WebSocket Endpoints

### `/ws/calculations`
Real-time calculation progress updates:
- Monte Carlo simulation progress
- Financial model calculation updates
- KPI recalculation notifications

### `/ws/entities`
Entity file change notifications:
- YAML file creation/modification/deletion
- Entity validation status updates
- Real-time entity list updates

### `/ws/status`
System status and health updates:
- System health status
- Performance metrics
- Error notifications
- Service availability updates

## Message Types

### Connection Management
- `connected` - Welcome message after connection
- `heartbeat` - Keep-alive messages
- `subscribe`/`unsubscribe` - Topic subscription management

### Entity Updates
- `entity_change` - File creation/modification/deletion
- `validation_error` - Entity validation failures
- `entity_list_update` - Bulk entity updates

### Calculation Updates
- `calculation_progress` - Real-time progress updates
- `calculation_complete` - Completion notifications
- `calculation_failed` - Error notifications

### Job Management
- `job_started` - Background job initiation
- `job_progress` - Job progress updates
- `job_completed` - Job completion
- `job_failed` - Job failure notifications

### System Status
- `status_update` - Periodic system health updates
- `system_alert` - Important system notifications

## Usage Examples

### Frontend JavaScript Client

```javascript
// Connect to calculation updates
const calcSocket = new WebSocket('ws://localhost:8000/ws/calculations');

calcSocket.onopen = () => {
    console.log('Connected to calculation updates');
    // Subscribe to specific calculation types
    calcSocket.send(JSON.stringify({
        type: 'subscribe',
        data: { topic: 'calculations' }
    }));
};

calcSocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        case 'calculation_progress':
            updateProgressBar(message.data.progress);
            break;
        case 'calculation_complete':
            showResults(message.data.result_summary);
            break;
        case 'heartbeat':
            // Update last seen timestamp
            break;
    }
};
```

### Backend Job Submission

```python
from cashcow.web.api.tasks import job_manager

# Submit a Monte Carlo simulation job
job_id = await job_manager.submit_job(
    job_func=monte_carlo_simulation_job,
    job_kwargs={
        "iterations": 1000,
        "variables": ["revenue_growth", "expense_inflation"]
    },
    metadata={
        "job_type": "monte_carlo",
        "user_id": "user123"
    }
)

# Job progress will be automatically broadcast to WebSocket clients
```

### Custom Progress Tracking

```python
from cashcow.web.api.tasks.progress_tracker import ProgressTracker

async def custom_calculation(tracker: ProgressTracker):
    await tracker.start()
    
    for i in range(100):
        # Do calculation work
        await asyncio.sleep(0.1)
        
        # Update progress
        progress = (i + 1) / 100
        await tracker.update_progress(
            progress, 
            f"Processing step {i + 1}/100"
        )
    
    await tracker.complete({"result": "success"})
```

## Background Job System

### Job Types

1. **Forecast Calculations** (`calculate_forecast_job`)
   - Financial forecasting for specified months and scenarios
   - KPI calculations and cashflow projections

2. **Monte Carlo Simulations** (`monte_carlo_simulation_job`)
   - Risk analysis with configurable iterations
   - Variable sensitivity analysis

3. **Entity Validation** (`entity_validation_job`)
   - Bulk validation of all entity YAML files
   - Error reporting and fix suggestions

4. **Report Generation** (`report_generation_job`)
   - HTML, CSV, and JSON report generation
   - Scheduled and on-demand reporting

### Job Management API

```bash
# Start a forecast job
POST /api/jobs/forecast
{
    "months": 24,
    "scenario": "optimistic"
}

# Check job status
GET /api/jobs/{job_id}

# Cancel a running job
POST /api/jobs/{job_id}/cancel

# List all jobs
GET /api/jobs
```

## File Watching Integration

The WebSocket system integrates with CashCow's existing file watcher (`cashcow.watchers`) to provide real-time notifications when entity files change:

```python
# File changes are automatically broadcast
# When entities/revenue/grants/nasa_sbir.yaml is modified:
{
    "type": "entity_change",
    "data": {
        "event_type": "modified",
        "file_path": "entities/revenue/grants/nasa_sbir.yaml",
        "entity_type": "grant",
        "entity_id": "nasa_sbir",
        "entity_data": { ... }
    }
}
```

## Configuration

### Connection Settings
- **Heartbeat Interval**: 30 seconds
- **Max Concurrent Jobs**: 5 (configurable)
- **Connection Timeout**: 60 seconds (2x heartbeat)
- **Job History**: 100 completed jobs retained

### Topics
- `calculations` - Calculation progress and results
- `entities` - Entity file changes and validation
- `status` - System health and performance
- `jobs` - Background job updates

## Error Handling

### Connection Errors
- Automatic reconnection on client side recommended
- Heartbeat monitoring for stale connections
- Graceful degradation when WebSocket unavailable

### Job Errors
- Failed jobs remain in history with error details
- Validation errors broadcast to entity subscribers
- System alerts for critical failures

### Memory Management
- Connection cleanup on disconnect
- Job history trimming (configurable limit)
- Periodic cleanup of stale data

## Security Considerations

### Authentication
- Optional user_id tracking for connections
- Client IP logging for audit trails
- Future: JWT token validation

### Rate Limiting
- Heartbeat prevents connection flooding
- Job queue prevents resource exhaustion
- Message size limits (future enhancement)

### Data Privacy
- No sensitive data in WebSocket messages
- Entity data sanitization options
- Audit logging for administrative actions

## Performance

### Scalability
- In-memory job queue (Redis integration planned)
- Concurrent worker processing
- Efficient message broadcasting

### Monitoring
- Connection statistics endpoint
- Job performance metrics
- System resource monitoring

### Optimization
- Message batching for high-frequency updates
- Selective broadcasting by topic
- Lazy loading of entity data

## Development

### Testing WebSocket Connections

```bash
# Test with wscat (install with: npm install -g wscat)
wscat -c ws://localhost:8000/ws/calculations

# Send subscription message
> {"type": "subscribe", "data": {"topic": "calculations"}}

# Start a background job to see progress updates
curl -X POST http://localhost:8000/api/jobs/forecast \
  -H "Content-Type: application/json" \
  -d '{"months": 12, "scenario": "baseline"}'
```

### Adding New Message Types

1. Add message type to `MessageType` enum in `models/websockets.py`
2. Create Pydantic model for the message structure
3. Add handler logic in appropriate WebSocket endpoint
4. Update broadcast functions if needed

### Custom Job Types

1. Create job function in `tasks/background_jobs.py`
2. Accept `tracker: ProgressTracker` parameter
3. Call `await tracker.update_progress()` regularly
4. Add API endpoint in `routers/jobs.py`

## Future Enhancements

### Planned Features
- Redis-based job queue for horizontal scaling
- User authentication and authorization
- Message encryption for sensitive data
- Rate limiting and abuse prevention
- WebSocket connection pooling
- Metrics and analytics dashboard

### Integration Points
- React frontend real-time updates
- Mobile app push notifications
- Email alerts for long-running jobs
- Slack/Teams integration for system alerts
- Export job results to external systems

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure proper Python path
   export PYTHONPATH="/home/alex/cashcow:$PYTHONPATH"
   ```

2. **WebSocket Connection Refused**
   - Check if FastAPI server is running
   - Verify port 8000 is available
   - Check firewall settings

3. **Jobs Not Starting**
   - Verify job manager started during app startup
   - Check worker task status
   - Review job queue for pending items

4. **File Watcher Not Working**
   - Ensure entities directory exists
   - Check file permissions
   - Verify watchdog package installed

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('cashcow.web.api.websockets').setLevel(logging.DEBUG)
logging.getLogger('cashcow.web.api.tasks').setLevel(logging.DEBUG)
```

## API Reference

See the automatically generated OpenAPI documentation at `/docs` when the server is running for complete API reference including all WebSocket message schemas and REST endpoints.