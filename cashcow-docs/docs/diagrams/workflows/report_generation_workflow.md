# Report Generation Workflow

This document contains detailed Mermaid diagrams showing the report generation process and workflows for different types of financial reports and forecasts.

## 1. General Report Generation Workflow

```mermaid
flowchart TD
    START([Report Generation Request]) --> COMMAND_TYPE{Command Type}
    
    COMMAND_TYPE --> FORECAST[forecast]
    COMMAND_TYPE --> KPI[kpi]
    COMMAND_TYPE --> LIST[list]
    
    FORECAST --> FORECAST_OPTS[Parse Forecast Options<br/>--months, --scenario, --format]
    KPI --> KPI_OPTS[Parse KPI Options<br/>--months, --scenario, --alerts]
    LIST --> LIST_OPTS[Parse List Options<br/>--type, --active, --tag]
    
    FORECAST_OPTS --> LOAD_ENTITIES[Load Entity Data]
    KPI_OPTS --> LOAD_ENTITIES
    LIST_OPTS --> LOAD_ENTITIES
    
    LOAD_ENTITIES --> ENTITY_CHECK{Entities Found?}
    ENTITY_CHECK -->|No| NO_ENTITIES[❌ No entities directory found.<br/>Create some entities first.]
    ENTITY_CHECK -->|Yes| VALIDATE_ENTITIES[Validate Loaded Entities]
    
    VALIDATE_ENTITIES --> VALIDATION_OK{All Valid?}
    VALIDATION_OK -->|No| VALIDATION_ERROR[❌ Entity validation errors<br/>Run 'cashcow validate' first]
    VALIDATION_OK -->|Yes| PROCESS_REQUEST[Process Specific Request]
    
    PROCESS_REQUEST --> FORECAST_CALC[Forecast Calculation]
    PROCESS_REQUEST --> KPI_CALC[KPI Calculation]
    PROCESS_REQUEST --> LIST_FILTER[List Filtering]
    
    FORECAST_CALC --> OUTPUT_FORECAST[Output Forecast]
    KPI_CALC --> OUTPUT_KPI[Output KPI Analysis]
    LIST_FILTER --> OUTPUT_LIST[Output Entity List]
    
    OUTPUT_FORECAST --> SUCCESS[✓ Report Generated]
    OUTPUT_KPI --> SUCCESS
    OUTPUT_LIST --> SUCCESS
    
    classDef startEnd fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#000
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    
    class START startEnd
    class FORECAST,KPI,LIST command
    class COMMAND_TYPE,ENTITY_CHECK,VALIDATION_OK decision
    class NO_ENTITIES,VALIDATION_ERROR error
    class FORECAST_OPTS,KPI_OPTS,LIST_OPTS,LOAD_ENTITIES,VALIDATE_ENTITIES,PROCESS_REQUEST,FORECAST_CALC,KPI_CALC,LIST_FILTER,OUTPUT_FORECAST,OUTPUT_KPI,OUTPUT_LIST process
    class SUCCESS success
```

## 2. Forecast Generation Detailed Workflow

```mermaid
flowchart TD
    FORECAST_CMD[cashcow forecast] --> PARSE_OPTIONS[Parse Command Options]
    
    PARSE_OPTIONS --> MONTHS[--months: Default 24]
    PARSE_OPTIONS --> SCENARIO[--scenario: Default baseline]
    PARSE_OPTIONS --> START_DATE[--start-date: Default today]
    PARSE_OPTIONS --> FORMAT[--format: table/csv/json]
    PARSE_OPTIONS --> OUTPUT_FILE[--output: Optional file path]
    PARSE_OPTIONS --> INCLUDE_KPIS[--kpis: Include KPI analysis]
    
    MONTHS --> SETUP_DATES[Setup Date Range]
    SCENARIO --> SETUP_DATES
    START_DATE --> SETUP_DATES
    
    SETUP_DATES --> CALC_END_DATE[Calculate End Date<br/>start + months × 30 days]
    CALC_END_DATE --> LOAD_STORE[Initialize EntityStore]
    
    LOAD_STORE --> SYNC_ENTITIES[Load Entities from YAML<br/>store.sync_from_yamlentities_dir]
    SYNC_ENTITIES --> ENTITY_COUNT{Entities Loaded?}
    
    ENTITY_COUNT -->|0| NO_ENTITIES_ERROR[❌ No entities found<br/>Create entities with 'cashcow add']
    ENTITY_COUNT -->|>0| CREATE_ENGINE[Create CashFlowEngine]

    CREATE_ENGINE --> SCENARIO_CHECK{Scenario = baseline?}
    SCENARIO_CHECK -->|Yes| DIRECT_CALC[Direct Engine Calculation<br/>engine.calculate_parallel]
    SCENARIO_CHECK -->|No| SCENARIO_MANAGER[Create ScenarioManager]
    
    SCENARIO_MANAGER --> LOAD_SCENARIOS[Load Scenario Files<br/>from scenarios/ directory]
    LOAD_SCENARIOS --> SCENARIO_EXISTS{Scenario File Exists?}
    SCENARIO_EXISTS -->|No| SCENARIO_ERROR[❌ Scenario not found<br/>Using baseline instead]
    SCENARIO_EXISTS -->|Yes| SCENARIO_CALC[Scenario Calculation<br/>scenario_mgr.calculate_scenario]
    
    DIRECT_CALC --> DATAFRAME[Forecast DataFrame]
    SCENARIO_CALC --> DATAFRAME
    SCENARIO_ERROR --> DIRECT_CALC
    
    DATAFRAME --> OUTPUT_CHOICE{Output Format}
    OUTPUT_CHOICE --> TABLE_OUTPUT[Table Format]
    OUTPUT_CHOICE --> CSV_OUTPUT[CSV Format]
    OUTPUT_CHOICE --> JSON_OUTPUT[JSON Format]
    
    TABLE_OUTPUT --> DISPLAY_TABLE[Display Forecast Table<br/>Summary + Monthly Breakdown]
    CSV_OUTPUT --> CSV_FILE{Output File Specified?}
    JSON_OUTPUT --> JSON_FILE{Output File Specified?}
    
    CSV_FILE -->|Yes| SAVE_CSV[Save to File<br/>df.to_csvoutput]
    CSV_FILE -->|No| PRINT_CSV[Print CSV to Console]
    JSON_FILE -->|Yes| SAVE_JSON[Save to File<br/>df.to_jsonoutput]
    JSON_FILE -->|No| PRINT_JSON[Print JSON to Console]
    
    DISPLAY_TABLE --> KPI_CHECK{--kpis flag?}
    SAVE_CSV --> KPI_CHECK
    PRINT_CSV --> KPI_CHECK
    SAVE_JSON --> KPI_CHECK
    PRINT_JSON --> KPI_CHECK
    
    KPI_CHECK -->|Yes| CALC_KPIS[Calculate KPIs<br/>KPICalculator.calculate_all_kpis]
    KPI_CHECK -->|No| COMPLETE[✓ Forecast Complete]
    
    CALC_KPIS --> DISPLAY_KPIS[Display KPI Analysis<br/>• Runway<br/>• Burn Rate<br/>• Growth Metrics]
    DISPLAY_KPIS --> CHECK_ALERTS[Check for Alerts<br/>get_kpi_alerts]
    CHECK_ALERTS --> SHOW_ALERTS[Show Alerts if Any]
    SHOW_ALERTS --> COMPLETE
    
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef option fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:#000
    classDef decision fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#000
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef output fill:#e1bee7,stroke:#8e24aa,stroke-width:2px,color:#000
    
    class FORECAST_CMD command
    class MONTHS,SCENARIO,START_DATE,FORMAT,OUTPUT_FILE,INCLUDE_KPIS option
    class ENTITY_COUNT,SCENARIO_CHECK,SCENARIO_EXISTS,OUTPUT_CHOICE,CSV_FILE,JSON_FILE,KPI_CHECK decision
    class PARSE_OPTIONS,SETUP_DATES,CALC_END_DATE,LOAD_STORE,SYNC_ENTITIES,CREATE_ENGINE,SCENARIO_MANAGER,LOAD_SCENARIOS,DIRECT_CALC,SCENARIO_CALC,CALC_KPIS,CHECK_ALERTS process
    class NO_ENTITIES_ERROR,SCENARIO_ERROR error
    class COMPLETE success
    class DISPLAY_TABLE,SAVE_CSV,PRINT_CSV,SAVE_JSON,PRINT_JSON,DISPLAY_KPIS,SHOW_ALERTS output
```

## 3. KPI Analysis Workflow

```mermaid
flowchart TD
    KPI_CMD[cashcow kpi] --> PARSE_KPI_OPTIONS[Parse KPI Options]
    
    PARSE_KPI_OPTIONS --> KPI_MONTHS[--months: Default 12]
    PARSE_KPI_OPTIONS --> KPI_SCENARIO[--scenario: Default baseline]
    PARSE_KPI_OPTIONS --> ALERTS_ONLY[--alerts: Show alerts only]
    
    KPI_MONTHS --> SETUP_KPI_DATES[Setup Analysis Period]
    KPI_SCENARIO --> SETUP_KPI_DATES
    
    SETUP_KPI_DATES --> LOAD_KPI_STORE[Initialize EntityStore]
    LOAD_KPI_STORE --> SYNC_KPI_ENTITIES[Load Entities from YAML]
    SYNC_KPI_ENTITIES --> CREATE_KPI_ENGINE[Create CashFlowEngine]
    
    CREATE_KPI_ENGINE --> GENERATE_FORECAST[Generate Forecast Data<br/>engine.calculate_parallel]
    GENERATE_FORECAST --> KPI_CALCULATOR[Create KPICalculator]
    
    KPI_CALCULATOR --> CALC_ALL_KPIS[Calculate All KPIs<br/>calculate_all_kpisdf]
    CALC_ALL_KPIS --> KPI_RESULTS[KPI Results Dictionary]
    
    KPI_RESULTS --> ALERTS_FLAG{--alerts flag?}
    
    ALERTS_FLAG -->|Yes| GET_ALERTS[Get KPI Alerts<br/>get_kpi_alertskpis]
    GET_ALERTS --> HAS_ALERTS{Alerts Found?}
    HAS_ALERTS -->|Yes| DISPLAY_ALERTS[Display Alert List<br/>Level: Message format]
    HAS_ALERTS -->|No| NO_ALERTS[✓ No alerts - all metrics<br/>within acceptable ranges]
    
    ALERTS_FLAG -->|No| FULL_KPI_DISPLAY[Display Full KPI Analysis]
    
    FULL_KPI_DISPLAY --> KEY_KPIS[Display Key KPIs<br/>• Runway months<br/>• Monthly burn rate<br/>• Revenue growth rate<br/>• R&D percentage<br/>• Revenue per employee<br/>• Cash efficiency]
    
    KEY_KPIS --> FORMAT_KPIS[Format KPI Values<br/>• Percentages: .1f%<br/>• Currency: $,.2f<br/>• Ratios: .2f]
    
    FORMAT_KPIS --> CHECK_KPI_ALERTS[Check for Alerts]
    CHECK_KPI_ALERTS --> SHOW_KPI_ALERTS[Show Alerts Section<br/>if any found]
    
    DISPLAY_ALERTS --> KPI_COMPLETE[✓ KPI Analysis Complete]
    NO_ALERTS --> KPI_COMPLETE
    SHOW_KPI_ALERTS --> KPI_COMPLETE
    
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef option fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:#000
    classDef decision fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#000
    classDef kpi fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef alert fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    
    class KPI_CMD command
    class KPI_MONTHS,KPI_SCENARIO,ALERTS_ONLY option
    class ALERTS_FLAG,HAS_ALERTS decision
    class PARSE_KPI_OPTIONS,SETUP_KPI_DATES,LOAD_KPI_STORE,SYNC_KPI_ENTITIES,CREATE_KPI_ENGINE,GENERATE_FORECAST,KPI_CALCULATOR,CALC_ALL_KPIS,FORMAT_KPIS,CHECK_KPI_ALERTS process
    class KEY_KPIS,FULL_KPI_DISPLAY kpi
    class GET_ALERTS,DISPLAY_ALERTS,SHOW_KPI_ALERTS,NO_ALERTS alert
    class KPI_COMPLETE success
```

## 4. Entity Listing Workflow

```mermaid
flowchart TD
    LIST_CMD[cashcow list] --> PARSE_LIST_OPTIONS[Parse List Options]
    
    PARSE_LIST_OPTIONS --> FILTER_TYPE[--type: Filter by entity type]
    PARSE_LIST_OPTIONS --> FILTER_ACTIVE[--active: Show only active]
    PARSE_LIST_OPTIONS --> FILTER_TAGS[--tag: Filter by tags multiple]
    
    FILTER_TYPE --> LOAD_LIST_STORE[Initialize EntityStore]
    FILTER_ACTIVE --> LOAD_LIST_STORE
    FILTER_TAGS --> LOAD_LIST_STORE
    
    LOAD_LIST_STORE --> CHECK_ENTITIES_DIR[Check entities/ directory]
    CHECK_ENTITIES_DIR --> DIR_EXISTS{Directory Exists?}
    
    DIR_EXISTS -->|No| NO_DIR_ERROR[❌ No entities directory found]
    DIR_EXISTS -->|Yes| SYNC_LIST_ENTITIES[Load Entities from YAML<br/>store.sync_from_yaml]
    
    SYNC_LIST_ENTITIES --> BUILD_FILTERS[Build Query Filters]
    BUILD_FILTERS --> TYPE_FILTER{Type Filter?}
    TYPE_FILTER -->|Yes| ADD_TYPE_FILTER[Add type filter to query]
    TYPE_FILTER -->|No| ACTIVE_FILTER{Active Filter?}
    ADD_TYPE_FILTER --> ACTIVE_FILTER
    
    ACTIVE_FILTER -->|Yes| ADD_ACTIVE_FILTER[Add active filter to query]
    ACTIVE_FILTER -->|No| TAG_FILTER{Tag Filters?}
    ADD_ACTIVE_FILTER --> TAG_FILTER
    
    TAG_FILTER -->|Yes| ADD_TAG_FILTERS[Add tag filters to query]
    TAG_FILTER -->|No| EXECUTE_QUERY[Execute Entity Query<br/>store.queryfilters]
    ADD_TAG_FILTERS --> EXECUTE_QUERY
    
    EXECUTE_QUERY --> QUERY_RESULTS[Query Results]
    QUERY_RESULTS --> HAS_RESULTS{Entities Found?}
    
    HAS_RESULTS -->|No| NO_MATCHES[No entities found<br/>matching filters]
    HAS_RESULTS -->|Yes| COUNT_ENTITIES[Count Results<br/>Found X entities:]
    
    COUNT_ENTITIES --> DISPLAY_HEADER[Display Results Header]
    DISPLAY_HEADER --> ENTITY_LOOP[For Each Entity]
    
    ENTITY_LOOP --> ENTITY_STATUS[Determine Status<br/>Active/Inactive based on dates]
    ENTITY_STATUS --> DISPLAY_ENTITY[Display Entity Info<br/>• Name type - Status<br/>• Start: date<br/>• End: date if exists<br/>• Tags: tag list]
    
    DISPLAY_ENTITY --> MORE_ENTITIES{More Entities?}
    MORE_ENTITIES -->|Yes| ENTITY_LOOP
    MORE_ENTITIES -->|No| LIST_COMPLETE[✓ Entity List Complete]
    
    NO_DIR_ERROR --> LIST_COMPLETE
    NO_MATCHES --> LIST_COMPLETE
    
    classDef command fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef option fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:#000
    classDef decision fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#000
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef display fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,color:#000
    classDef loop fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#000
    
    class LIST_CMD command
    class FILTER_TYPE,FILTER_ACTIVE,FILTER_TAGS option
    class DIR_EXISTS,TYPE_FILTER,ACTIVE_FILTER,TAG_FILTER,HAS_RESULTS,MORE_ENTITIES decision
    class PARSE_LIST_OPTIONS,LOAD_LIST_STORE,CHECK_ENTITIES_DIR,SYNC_LIST_ENTITIES,BUILD_FILTERS,ADD_TYPE_FILTER,ADD_ACTIVE_FILTER,ADD_TAG_FILTERS,EXECUTE_QUERY,COUNT_ENTITIES,ENTITY_STATUS process
    class NO_DIR_ERROR error
    class LIST_COMPLETE success
    class DISPLAY_HEADER,DISPLAY_ENTITY,NO_MATCHES display
    class ENTITY_LOOP loop
```

## 5. Report Output Formats and Examples

```mermaid
flowchart TD
    FORECAST_DATA[Forecast DataFrame] --> OUTPUT_FORMAT{Output Format}
    
    OUTPUT_FORMAT --> TABLE_FORMAT[Table Format<br/>--format table]
    OUTPUT_FORMAT --> CSV_FORMAT[CSV Format<br/>--format csv]
    OUTPUT_FORMAT --> JSON_FORMAT[JSON Format<br/>--format json]
    
    TABLE_FORMAT --> TABLE_SUMMARY[Summary Section<br/>• Period: start to end<br/>• Total Revenue: $X,XXX,XXX<br/>• Total Expenses: $X,XXX,XXX<br/>• Net Cash Flow: $X,XXX,XXX<br/>• Final Cash Balance: $X,XXX,XXX]
    
    TABLE_SUMMARY --> TABLE_BREAKDOWN[Monthly Breakdown<br/>First 6 months shown<br/>YYYY-MM: Revenue $X,XXX, Expenses $X,XXX, Balance $X,XXX]
    
    CSV_FORMAT --> CSV_STRUCTURE[CSV Structure<br/>period,total_revenue,total_expenses,<br/>net_cash_flow,cash_balance<br/>2025-07,85000,95000,490000<br/>2025-08,92000,97000,485000]
    
    JSON_FORMAT --> JSON_STRUCTURE[JSON Structure
    <br/>  'period': '2025-07',<br/>  'total_revenue': 85000,<br/>  'total_expenses': 95000,<br/>  'net_cash_flow': -10000,<br/>  'cash_balance': 490000<br/>]
    
    TABLE_BREAKDOWN --> KPI_OPTION{Include KPIs?}
    CSV_STRUCTURE --> FILE_OUTPUT{Output to File?}
    JSON_STRUCTURE --> FILE_OUTPUT
    
    KPI_OPTION -->|Yes| KPI_SECTION[KPI Analysis Section<br/>• Runway months: X.X months<br/>• Monthly burn rate: $XX,XXX<br/>• Revenue growth rate: X.X%<br/>• R&D percentage: XX.X%<br/>• Revenue per employee: $XXX,XXX<br/>• Cash efficiency: X.XX]
    
    KPI_SECTION --> ALERT_SECTION[Alert Section if any<br/>⚠ X alerts:<br/>  WARNING: Message<br/>  INFO: Message]
    
    FILE_OUTPUT -->|Yes| SAVE_FILE[Save to Specified File<br/>✓ Forecast saved to filename]
    FILE_OUTPUT -->|No| CONSOLE_OUTPUT[Print to Console]
    
    KPI_OPTION -->|No| REPORT_COMPLETE[Report Complete]
    ALERT_SECTION --> REPORT_COMPLETE
    SAVE_FILE --> REPORT_COMPLETE
    CONSOLE_OUTPUT --> REPORT_COMPLETE
    
    classDef data fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000
    classDef format fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef structure fill:#e8f5e8,stroke:#2e7d32,stroke-width:1px,color:#000
    classDef kpi fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#000
    classDef output fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,color:#000
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    
    class FORECAST_DATA data
    class OUTPUT_FORMAT,KPI_OPTION,FILE_OUTPUT decision
    class TABLE_FORMAT,CSV_FORMAT,JSON_FORMAT format
    class TABLE_SUMMARY,TABLE_BREAKDOWN,CSV_STRUCTURE,JSON_STRUCTURE structure
    class KPI_SECTION,ALERT_SECTION kpi
    class SAVE_FILE,CONSOLE_OUTPUT output
    class REPORT_COMPLETE success
```

## 6. Error Handling in Report Generation

```mermaid
flowchart TD
    REPORT_REQUEST[Report Generation Request] --> TRY_EXECUTE[Try Execute Command]
    
    TRY_EXECUTE --> ERROR_TYPE{Error Occurred?}
    
    ERROR_TYPE -->|No Error| SUCCESS_PATH[Normal Execution Path]
    ERROR_TYPE -->|Entity Error| ENTITY_ERRORS[Entity-Related Errors]
    ERROR_TYPE -->|Calculation Error| CALC_ERRORS[Calculation Errors]
    ERROR_TYPE -->|File Error| FILE_ERRORS[File I/O Errors]
    ERROR_TYPE -->|Config Error| CONFIG_ERRORS[Configuration Errors]
    
    ENTITY_ERRORS --> NO_ENTITIES[❌ No entities directory found<br/>Create some entities first with 'cashcow add']
    ENTITY_ERRORS --> INVALID_ENTITIES[❌ Entity validation errors<br/>Run 'cashcow validate' to see details]
    ENTITY_ERRORS --> CORRUPTED_YAML[❌ YAML parsing error<br/>Check file syntax in entities/]
    
    CALC_ERRORS --> ENGINE_ERROR[❌ Calculation engine error<br/>Check entity data consistency]
    CALC_ERRORS --> SCENARIO_ERROR[❌ Scenario not found<br/>Available scenarios: baseline, ...]
    CALC_ERRORS --> DATE_ERROR[❌ Invalid date range<br/>End date must be after start date]
    
    FILE_ERRORS --> PERMISSION_ERROR[❌ Permission denied<br/>Check file write permissions]
    FILE_ERRORS --> DISK_SPACE[❌ Insufficient disk space<br/>Free up space and try again]
    FILE_ERRORS --> INVALID_PATH[❌ Invalid output path<br/>Check directory exists]
    
    CONFIG_ERRORS --> MISSING_CONFIG[❌ Configuration file missing<br/>Create config/settings.yaml]
    CONFIG_ERRORS --> INVALID_CONFIG[❌ Invalid configuration<br/>Check YAML syntax in config/]
    
    NO_ENTITIES --> SHOW_HELP[Show Help Message<br/>• How to create entities<br/>• Directory structure<br/>• Example commands]
    INVALID_ENTITIES --> VALIDATION_PROMPT[Suggest Validation<br/>Run: cashcow validate --fix]
    CORRUPTED_YAML --> YAML_HELP[Show YAML Help<br/>• Common syntax errors<br/>• Validation tools<br/>• Example formats]
    
    ENGINE_ERROR --> DEBUG_PROMPT[Offer Debug Mode<br/>Show detailed error? y/N]
    SCENARIO_ERROR --> LIST_SCENARIOS[List Available Scenarios<br/>From scenarios/ directory]
    DATE_ERROR --> DATE_HELP[Show Date Format Help<br/>Use YYYY-MM-DD format]
    
    PERMISSION_ERROR --> PERMISSION_FIX[Suggest Permission Fix<br/>chmod 755 directory<br/>Check ownership]
    DISK_SPACE --> CLEANUP_SUGGEST[Suggest Cleanup<br/>• Remove old reports<br/>• Clear temp files]
    INVALID_PATH --> PATH_HELP[Show Path Help<br/>Use absolute or relative paths<br/>Ensure parent dir exists]
    
    MISSING_CONFIG --> CONFIG_TEMPLATE[Offer Config Template<br/>Create default settings.yaml?]
    INVALID_CONFIG --> CONFIG_VALIDATION[Validate Config<br/>Show specific errors]
    
    SUCCESS_PATH --> NORMAL_OUTPUT[Generate Normal Report Output]
    SHOW_HELP --> GRACEFUL_EXIT[Graceful Exit with Help]
    VALIDATION_PROMPT --> GRACEFUL_EXIT
    YAML_HELP --> GRACEFUL_EXIT
    DEBUG_PROMPT --> DETAILED_ERROR[Show Stack Trace<br/>if user confirms]
    LIST_SCENARIOS --> GRACEFUL_EXIT
    DATE_HELP --> GRACEFUL_EXIT
    PERMISSION_FIX --> GRACEFUL_EXIT
    CLEANUP_SUGGEST --> GRACEFUL_EXIT
    PATH_HELP --> GRACEFUL_EXIT
    CONFIG_TEMPLATE --> GRACEFUL_EXIT
    CONFIG_VALIDATION --> GRACEFUL_EXIT
    
    NORMAL_OUTPUT --> COMPLETE[✓ Report Complete]
    DETAILED_ERROR --> COMPLETE
    GRACEFUL_EXIT --> COMPLETE
    
    classDef request fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000
    classDef errorType fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef specificError fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef help fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef normal fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#000
    
    class REPORT_REQUEST,TRY_EXECUTE request
    class ERROR_TYPE decision
    class ENTITY_ERRORS,CALC_ERRORS,FILE_ERRORS,CONFIG_ERRORS errorType
    class NO_ENTITIES,INVALID_ENTITIES,CORRUPTED_YAML,ENGINE_ERROR,SCENARIO_ERROR,DATE_ERROR,PERMISSION_ERROR,DISK_SPACE,INVALID_PATH,MISSING_CONFIG,INVALID_CONFIG specificError
    class SHOW_HELP,VALIDATION_PROMPT,YAML_HELP,DEBUG_PROMPT,LIST_SCENARIOS,DATE_HELP,PERMISSION_FIX,CLEANUP_SUGGEST,PATH_HELP,CONFIG_TEMPLATE,CONFIG_VALIDATION,GRACEFUL_EXIT help
    class COMPLETE success
    class SUCCESS_PATH,NORMAL_OUTPUT,DETAILED_ERROR normal
```