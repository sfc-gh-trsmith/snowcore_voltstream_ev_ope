# VoltStream EV Manufacturing - OPE Intelligent Jidoka System

**Snowflake Cortex AI-powered manufacturing intelligence for EV Gigafactory OPE optimization**

## Overview

This project demonstrates an **Intelligent Jidoka System** that bridges the gap between Overall Equipment Effectiveness (OEE) and Overall Process Efficiency (OPE) in high-volume EV battery manufacturing.

### The Problem

In modern Gigafactories, efficiency losses hide in the "white space" between production steps:
- **Ghost Inventory Paradox**: ERP shows inventory as "available" while shop floor sensors report material starvation
- **OEE Blindness**: High equipment uptime (90%+) masks low process efficiency (65%)
- **Reactive Maintenance**: Problems discovered after failures occur, not before

### The Solution

This system implements **Jidoka 2.0** - automation with human intelligence, powered by Snowflake Cortex:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Natural Language Analytics | Cortex Analyst | Query OPE metrics in plain English |
| Knowledge Retrieval | Cortex Search | RAG over maintenance manuals |
| Intelligent Orchestration | Cortex Agent | Automated diagnosis and recommendations |
| Predictive Maintenance | Snowpark ML | Forecast AGV failures before they occur |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOLTSTREAM_EV_OPE Database                    │
├─────────────────────────────────────────────────────────────────┤
│  RAW Schema (Bronze)           │  ATOMIC Schema (Silver)        │
│  ├── MATERIAL_DOCUMENT_CDC     │  ├── ASSET                     │
│  ├── PROD_ORDER_HEADER_CDC     │  ├── PRODUCT                   │
│  ├── EQUIPMENT_STATE_LOG_CDC   │  ├── SHIFT                     │
│  ├── AGV_TELEMATICS_LOG_CDC    │  ├── WORK_ORDER                │
│  └── ENV_SENSOR_STREAM_STAGE   │  ├── EQUIPMENT_DOWNTIME        │
│                                │  ├── EQUIPMENT_FAILURE         │
│                                │  └── ENVIRONMENTAL_READING     │
├─────────────────────────────────────────────────────────────────┤
│  EV_OPE Schema (Gold) - Dimensional Views                       │
│  ├── DIM_ASSET, DIM_PRODUCT, DIM_SHIFT   ← Dimension views      │
│  ├── OPE_DAILY_FACT                      ← OPE/OEE metrics      │
│  ├── AGV_FAILURE_ANALYSIS                ← ML training data     │
│  ├── V_OPE_TRENDS, V_AGV_HEALTH          ← Analytical views     │
│  ├── PREDICTIVE_MAINTENANCE_ALERTS       ← Model predictions    │
│  └── DOCUMENT_CHUNKS                     ← Cortex Search index  │
├─────────────────────────────────────────────────────────────────┤
│  Cortex AI Services                                             │
│  ├── MFG_KNOWLEDGE_BASE_SEARCH   ← Cortex Search service        │
│  ├── ope_semantic_model.yaml     ← Cortex Analyst semantic model│
│  └── VOLTSTREAM_EV_OPE_AGENT     ← Cortex Agent (Jidoka coord.) │
└─────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture

| Layer | Schema | Purpose |
|-------|--------|---------|
| **Bronze** | RAW | Landing zone for CDC data from source systems |
| **Silver** | ATOMIC | Enterprise relational model (normalized, harmonized) |
| **Gold** | EV_OPE | Dimensional views for analytics, ML, and dashboards |

## Demo Scenario

The synthetic data tells a specific causal story:

1. **Baseline (Nov 8 - Dec 8)**: Normal operation, OPE ~85%, OEE ~92%
2. **Crisis (Dec 9-11)**:
   - Humidity drops to 25% (below 35% threshold)
   - Dust spikes to 35 µg/m³ (above 25 µg/m³ threshold)
   - AGV-ERR-99 (optical sensor obscured) errors spike
   - Line 4 experiences material starvation
   - OPE drops to 60%
3. **Resolution**: ML model identifies root cause → Cortex Agent recommends "Dust Mitigation Cycle"

## Quick Start

### Prerequisites

- Snowflake account with Cortex AI features enabled
- Snowflake CLI (`snow`) installed and configured
- Python 3.11+

### Deployment

```bash
# Clone and navigate to project
cd snowcore_voltstream_ev_ope

# Full deployment (includes data generation)
./deploy.sh

# Deploy with custom connection
./deploy.sh -c prod

# Skip data generation if already loaded
./deploy.sh --skip-data

# Deploy only specific components
./deploy.sh --only-streamlit    # Streamlit app only
./deploy.sh --only-notebook     # ML notebook only
./deploy.sh --only-cortex       # Cortex Search only
./deploy.sh --only-agent        # Cortex Agent only
```

### Runtime Operations

```bash
# Check deployment status
./run.sh status

# Get Streamlit dashboard URL
./run.sh streamlit

# Execute ML notebook
./run.sh main

# Run query tests
./run.sh test
```

### Cleanup

```bash
# Remove all Snowflake resources (interactive)
./clean.sh

# Skip confirmation
./clean.sh --force
```

## Project Structure

```
snowcore_voltstream_ev_ope/
├── agents/
│   └── VOLTSTREAM_EV_OPE_AGENT.json    # Cortex Agent configuration
│
├── sql/
│   ├── 01_account_setup.sql            # Database, warehouse, role setup
│   ├── 02_raw_schema.sql               # RAW layer tables (Bronze)
│   ├── 03_atomic_schema.sql            # ATOMIC layer tables (Silver)
│   ├── 03b_raw_to_atomic.sql           # ETL: RAW → ATOMIC transformation
│   ├── 04_ev_ope_schema.sql            # EV_OPE views (Gold)
│   └── 05_cortex_search.sql            # Cortex Search service
│
├── semantic_views/
│   └── ope_semantic_model.yaml         # Cortex Analyst semantic model
│
├── streamlit/
│   ├── streamlit_app.py                # Main app entry point
│   ├── pages/
│   │   ├── 1_Executive_Dashboard.py    # VP Manufacturing view
│   │   ├── 2_Unit_Economics.py         # Cost/efficiency analysis
│   │   ├── 3_Operations_Control.py     # Plant Manager view
│   │   ├── 4_ML_Analysis.py            # Data Scientist view
│   │   └── 5_About.py                  # Documentation
│   ├── utils/
│   │   ├── cortex_helpers.py           # Cortex AI integration
│   │   ├── data_loader.py              # Query execution
│   │   ├── query_registry.py           # SQL query definitions
│   │   └── ui_components.py            # Shared UI components
│   ├── assets/
│   │   └── data_architecture.svg       # Architecture diagram
│   ├── tests/
│   │   └── test_queries.py             # Query validation tests
│   ├── environment.yml
│   └── snowflake.yml
│
├── notebooks/
│   ├── generate_synthetic_data.ipynb   # Data generation (runs in Snowflake)
│   ├── agv_failure_prediction.ipynb    # ML model development
│   ├── environment.yml
│   └── snowflake.yml
│
├── data/
│   ├── synthetic/                      # Generated CSV files (if any)
│   └── unstructured/                   # Maintenance manuals (markdown)
│       ├── agv_maintenance_manual.md
│       ├── dust_mitigation_protocol.md
│       └── shift_report_template.md
│
├── utils/
│   └── sf_cortex_agent_ops.py          # Cortex Agent management utility
│
├── deploy.sh                           # One-click deployment
├── run.sh                              # Runtime operations
├── clean.sh                            # Resource cleanup
├── DRD.md                              # Design Requirements Document
└── README.md
```

## Cortex AI Components

### Cortex Analyst

The semantic model (`ope_semantic_model.yaml`) enables natural language queries:

```
"What was the average OPE for Line 4 last week?"
"Show me the gap between OEE and OPE by line"
"Which lines had the most starvation downtime?"
"What is the relationship between humidity, dust, and AGV failures?"
```

### Cortex Search

The `MFG_KNOWLEDGE_BASE_SEARCH` service indexes:
- AGV Fleet Maintenance Manual (with AGV-ERR-99 procedures)
- Dust Mitigation Protocol (SOP)
- Sample Shift Reports

Sample queries:
```
"What are the troubleshooting steps for AGV-ERR-99?"
"What is the dust mitigation protocol?"
"How do I clean AGV optical sensors?"
```

### Cortex Agent

The `VOLTSTREAM_EV_OPE_AGENT` orchestrates both tools:
- **OPE_ANALYTICS**: Cortex Analyst for numeric/metric queries
- **VOLTSTREAM_EV_OPE_SEARCH**: Cortex Search for procedures and SOPs

Sample orchestrated queries:
```
"Why did OPE drop on Line 4 and what should we do about it?"
"What happened during December 9-11 and how do we prevent it?"
```

### ML Model

XGBoost classifier predicting high-failure periods:
- **Features**: Humidity, dust PM2.5, temperature, hour
- **Target**: IS_HIGH_FAILURE_PERIOD (failure rate > 5%)
- **Performance**: ROC-AUC > 0.90

Key finding: **Environmental factors explain 70%+ of AGV failures**

## User Personas

| Persona | Role | Page | Key Questions |
|---------|------|------|---------------|
| **Strategic** | VP Manufacturing | Executive Dashboard | "Why did OPE drop? What's our efficiency gap?" |
| **Operational** | Plant Manager | Operations Control | "What actions should I take? Approve cleaning cycle?" |
| **Technical** | Data Scientist | ML Analysis | "Verify humidity-dust correlation in the model" |

## Key Metrics

| Metric | Definition |
|--------|------------|
| **OEE** | Overall Equipment Effectiveness (Availability × Performance × Quality) |
| **OPE** | Overall Process Efficiency (includes wait time and material flow) |
| **OEE-OPE Gap** | Hidden inefficiency not captured by traditional metrics |
| **AGV** | Automated Guided Vehicle — self-driving transport robots that move battery cells and materials between production stations using LiDAR navigation |
| **AGV Failures** | When AGVs stop operating due to sensor errors, causing material delivery delays |
| **Starvation** | Downtime due to material delivery delays (often caused by AGV failures) |
| **AGV-ERR-99** | Optical sensor obscured (dust on LiDAR lens) — the primary AGV failure mode in the demo |

## Target Outcomes

- **+15% OPE** by identifying and eliminating hidden inefficiencies
- **-20% starvation** through predictive AGV maintenance
- **4 hours → 5 minutes** time-to-decision with AI-assisted diagnosis

## Technologies

- **Snowflake**: Data Cloud platform
- **Cortex AI**: Analyst, Search, Agent
- **Snowpark ML**: XGBoost model training
- **Streamlit**: Interactive dashboard
- **Python 3.11**: Data generation and ML (Snowflake Notebooks)

## Documentation

- `DRD.md` - Design Requirements Document with detailed specifications
- `cursor_scratch/TEST_PLAN.md` - Test plan and validation procedures
- `cursor_scratch/TEST_LOG.md` - Test execution log

## License

This is a demonstration project for Snowflake capabilities.

---

*Built with Snowflake Cortex AI*
