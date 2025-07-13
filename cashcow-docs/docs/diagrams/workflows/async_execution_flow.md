# Async Execution Flow

```mermaid
flowchart TB
    A[Async Calculate Request] --> B[Validate Input Parameters]
    B --> C{Check Cache}
    C -->|Hit| D[Return Cached Result]
    C -->|Miss| E[Generate Monthly Periods]
    
    E --> F[Load Entities Cached]
    F --> G[Create Async Tasks]
    
    G --> H[For Each Period]
    H --> I[Create Async Task]
    I --> J[Add to Task List]
    
    J --> K{More Periods?}
    K -->|Yes| H
    K -->|No| L[Execute All Tasks]
    
    L --> M[await asyncio.gather *tasks]
    M --> N[Collect Results]
    
    N --> O[Sort by Period Date]
    O --> P[Create DataFrame]
    P --> Q[Add Cumulative Calculations]
    Q --> R[Cache Results]
    R --> S[Return DataFrame]
    
    subgraph "Async Task Creation"
        T1[_calculate_single_period_async]
        T2[loop.run_in_executor]
        T3[Thread Pool Execution]
    end
    
    subgraph "Concurrency Benefits"
        CB1[Parallel Period Processing]
        CB2[Non-blocking I/O]
        CB3[Resource Efficiency]
    end
    
    style A fill:#e1f5fe,color:#000
    style D fill:#e8f5e8,color:#000
    style S fill:#e8f5e8,color:#000
    style M fill:#fff3e0,color:#000
    style L fill:#f3e5f5,color:#000
    
 
```

## Async vs Sync Comparison

```mermaid
graph TB
    subgraph "Synchronous Execution"
        A1[Period 1] --> A2[Period 2]
        A2 --> A3[Period 3]
        A3 --> A4[Period 4]
        A4 --> A5[Complete]
    end
    
    subgraph "Asynchronous Execution"
        B1[Period 1]
        B2[Period 2]
        B3[Period 3]
        B4[Period 4]
        B1 -.-> B5[Complete]
        B2 -.-> B5
        B3 -.-> B5
        B4 -.-> B5
    end
    
    subgraph "Parallel Execution"
        C1[Period 1 - Thread 1]
        C2[Period 2 - Thread 2]
        C3[Period 3 - Thread 3]
        C4[Period 4 - Thread 4]
        C1 -.-> C5[Complete]
        C2 -.-> C5
        C3 -.-> C5
        C4 -.-> C5
    end
    
    style A5 fill:#fce4ec,color:#000
    style B5 fill:#e8f5e8,color:#000
    style C5 fill:#f3e5f5,color:#000
    
 
```

## Async Error Handling

```mermaid
flowchart TD
    A[Async Task Execution] --> B[Try Async Calculation]
    B --> C{Exception Occurred?}
    
    C -->|No| D[Task Successful]
    C -->|Yes| E[Catch Exception]
    
    E --> F[Log Error with Context]
    F --> G[Check Exception Type]
    
    G -->|Timeout| H[Retry with Longer Timeout]
    G -->|Network Error| I[Retry with Backoff]
    G -->|Data Error| J[Use Default Values]
    G -->|Fatal Error| K[Mark Task Failed]
    
    H --> L{Retry Successful?}
    I --> L
    L -->|Yes| D
    L -->|No| K
    
    D --> M[Add to Results]
    J --> M
    K --> N[Log Failure, Continue]
    
    M --> O{All Tasks Complete?}
    N --> O
    
    O -->|No| P[Wait for More Tasks]
    O -->|Yes| Q[Process Results]
    
    P --> O
    Q --> R[Handle Partial Results]
    R --> S[Return Available Data]
    
    subgraph "Error Recovery Strategies"
        ER1[Graceful Degradation]
        ER2[Partial Result Handling]
        ER3[Retry with Backoff]
        ER4[Default Value Substitution]
    end
    
    style A fill:#e1f5fe,color:#000
    style D fill:#e8f5e8,color:#000
    style E fill:#fff8e1,color:#000
    style S fill:#fff3e0,color:#000
    
 
```

## Thread Pool Execution

```mermaid
sequenceDiagram
    participant Main as Main Thread
    participant Pool as Thread Pool
    participant W1 as Worker 1
    participant W2 as Worker 2
    participant W3 as Worker 3
    participant W4 as Worker 4
    
    Main->>Pool: Submit Period 1 Task
    Main->>Pool: Submit Period 2 Task
    Main->>Pool: Submit Period 3 Task
    Main->>Pool: Submit Period 4 Task
    
    Pool->>W1: Assign Period 1
    Pool->>W2: Assign Period 2
    Pool->>W3: Assign Period 3
    Pool->>W4: Assign Period 4
    
    par Parallel Execution
        W1->>W1: Calculate Period 1
        W2->>W2: Calculate Period 2
        W3->>W3: Calculate Period 3
        W4->>W4: Calculate Period 4
    end
    
    W1-->>Pool: Period 1 Complete
    W2-->>Pool: Period 2 Complete
    W3-->>Pool: Period 3 Complete
    W4-->>Pool: Period 4 Complete
    
    Pool-->>Main: All Results Available
    Main->>Main: Sort and Process Results
```

## Async Performance Monitoring

```mermaid
flowchart LR
    A[Start Async Calculation] --> B[Record Start Time]
    B --> C[Create Performance Monitor]
    
    C --> D[Track Task Creation]
    C --> E[Monitor Task Execution]
    C --> F[Track Task Completion]
    
    D --> G[Task Count Metrics]
    E --> H[Execution Time per Task]
    F --> I[Success/Failure Rates]
    
    G --> J[Performance Report]
    H --> J
    I --> J
    
    J --> K[Log Performance Data]
    K --> L[Return Results with Metrics]
    
    subgraph "Metrics Collected"
        M1[Total Execution Time]
        M2[Average Task Duration]
        M3[Concurrency Level]
        M4[Error Rates]
        M5[Memory Usage]
    end
    
    subgraph "Performance Optimization"
        PO1[Adjust Worker Count]
        PO2[Optimize Task Size]
        PO3[Cache Optimization]
        PO4[Resource Management]
    end
    
    style A fill:#e1f5fe,color:#000
    style L fill:#e8f5e8,color:#000
    style C fill:#fff3e0,color:#000
    
 
```

## Async Context Management

```mermaid
flowchart TD
    A[Async Context Creation] --> B[Initialize Event Loop]
    B --> C[Set Context Variables]
    
    C --> D[Database Connection Pool]
    C --> E[Cache Configuration]
    C --> F[Resource Limits]
    
    D --> G[Async Task Execution]
    E --> G
    F --> G
    
    G --> H[Context Propagation]
    H --> I[Task-Local Storage]
    
    I --> J[Cleanup on Completion]
    J --> K[Resource Deallocation]
    K --> L[Context Disposal]
    
    subgraph "Context Variables"
        CV1[Scenario Parameters]
        CV2[Calculation Settings]
        CV3[Error Handling Config]
        CV4[Performance Settings]
    end
    
    subgraph "Resource Management"
        RM1[Connection Pooling]
        RM2[Memory Limits]
        RM3[Timeout Settings]
        RM4[Cleanup Handlers]
    end
    
    style A fill:#e1f5fe,color:#000
    style L fill:#e8f5e8,color:#000
    style G fill:#fff3e0,color:#000
    style J fill:#f3e5f5,color:#000
    
 
```

## Async Best Practices

```mermaid
mindmap
  root((Async Best Practices))
    Task Management
      Create tasks efficiently
      Limit concurrent tasks
      Use task groups
      Handle cancellation
    Error Handling
      Catch specific exceptions
      Implement retry logic
      Graceful degradation
      Log async errors
    Performance
      Monitor task duration
      Optimize task size
      Use connection pooling
      Implement caching
    Resource Management
      Clean up resources
      Use context managers
      Limit memory usage
      Handle timeouts
    Testing
      Mock async dependencies
      Test error conditions
      Verify concurrency
      Performance testing
```

## Async Debugging Flow

```mermaid
flowchart TD
    A[Async Issue Detected] --> B[Enable Debug Logging]
    B --> C[Add Task Tracking]
    
    C --> D[Monitor Task States]
    D --> E[Track Task Duration]
    E --> F[Identify Bottlenecks]
    
    F --> G{Performance Issue?}
    G -->|Yes| H[Profile Task Execution]
    G -->|No| I{Error Issue?}
    
    H --> J[Optimize Task Logic]
    J --> K[Test Performance]
    
    I -->|Yes| L[Add Exception Handling]
    I -->|No| M{Deadlock Issue?}
    
    L --> N[Implement Error Recovery]
    N --> O[Test Error Scenarios]
    
    M -->|Yes| P[Analyze Task Dependencies]
    M -->|No| Q[General Debugging]
    
    P --> R[Resolve Circular Dependencies]
    R --> S[Test Concurrent Execution]
    
    K --> T[Deploy Fix]
    O --> T
    S --> T
    Q --> T
    
    subgraph "Debug Tools"
        DT1[asyncio debug mode]
        DT2[Task monitoring]
        DT3[Performance profiling]
        DT4[Exception tracking]
    end
    
    style A fill:#fff8e1,color:#000
    style T fill:#e8f5e8,color:#000
    style B fill:#fff3e0,color:#000
    style H fill:#f3e5f5,color:#000
    
 
```