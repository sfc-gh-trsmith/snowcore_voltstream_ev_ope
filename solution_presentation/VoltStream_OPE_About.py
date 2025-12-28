"""
About Page - System Documentation
==================================

Dual-audience content for:
- Executives: Business problem, solution, value proposition
- Technical: Architecture, data flow, technology stack

Following SNOWFLAKE_STREAMLIT_ABOUT_SECTION_GUIDE.md guidelines.
"""

import sys
from pathlib import Path

# Add parent directory to path for utils imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# Import utilities
from utils.ui_components import (
    apply_global_styles, COLORS, 
    render_section_header, render_data_source_badge
)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="About | VoltStream OPE",
    page_icon="ℹ️",
    layout="wide"
)

apply_global_styles()

# =============================================================================
# HEADER
# =============================================================================

st.markdown(f"""
<h1 style="color: #f8fafc;">About VoltStream OPE</h1>
<h4 style="color: {COLORS['muted']};">Intelligent Jidoka System for EV Gigafactory Operations</h4>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# OVERVIEW - EXECUTIVE
# =============================================================================

render_section_header("Overview", "Understanding the problem and solution")

st.markdown(f"""
### The Ghost Inventory Paradox

In high-volume EV Gigafactories, efficiency losses hide in the **white space between production steps**. 
Traditional metrics paint a misleading picture:

<div style="display: flex; gap: 2rem; margin: 1.5rem 0;">
    <div style="flex: 1; background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['success']};">
        <div style="color: {COLORS['success']}; font-size: 0.75rem; text-transform: uppercase;">What ERP Shows</div>
        <div style="color: {COLORS['text']}; font-size: 1.5rem; font-weight: 700;">90%+ OEE</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">"Equipment running smoothly"</div>
    </div>
    <div style="flex: 1; background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['danger']};">
        <div style="color: {COLORS['danger']}; font-size: 0.75rem; text-transform: uppercase;">What Shop Floor Sees</div>
        <div style="color: {COLORS['text']}; font-size: 1.5rem; font-weight: 700;">65% OPE</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">"Lines starving for material"</div>
    </div>
</div>

**The Problem:** ERP systems show "available" inventory while shop floor IoT sensors report material starvation. 
This creates a paradox where high machine uptime masks low Overall Process Efficiency.

**The Cost:** Manual root-cause analysis takes **4+ hours**, risking shipment targets and customer commitments.
""", unsafe_allow_html=True)

st.markdown("#### Business Impact")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Time to Decision", "< 5 min", delta="-4 hours", delta_color="normal")
with col2:
    st.metric("OPE Improvement Target", "+15%", delta="vs baseline")
with col3:
    st.metric("Starvation Reduction", "-20%", delta="downtime saved")

st.markdown(f"""
#### The Solution: Intelligent Jidoka

We implement **Jidoka** — automation with human intelligence — using Snowflake Cortex AI:

- **Cortex Analyst** answers "Why did OPE drop on Line 4?" in plain English
- **Cortex Search** retrieves maintenance protocols from unstructured manuals
- **ML Predictions** forecast failures before they cause starvation

The result: A VP of Manufacturing can get instant, data-backed answers without waiting for analyst reports.
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# MANUFACTURING TERMINOLOGY
# =============================================================================

render_section_header("Manufacturing Terminology", "Key terms and concepts")

st.markdown(f"""
<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1rem 0;">
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['snowflake']};">
        <div style="color: {COLORS['snowflake']}; font-weight: 700; margin-bottom: 0.5rem;">AGV (Automated Guided Vehicle)</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            Self-driving transport robots that move battery cells and materials between production stations. 
            AGVs use <strong style="color: {COLORS['text']};">LiDAR sensors</strong> for navigation and obstacle detection.
            In Gigafactories, AGV fleets are critical for maintaining material flow between production lines.
        </div>
    </div>
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['danger']};">
        <div style="color: {COLORS['danger']}; font-weight: 700; margin-bottom: 0.5rem;">AGV-ERR-99</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            Error code indicating <strong style="color: {COLORS['text']};">"optical sensor obscured"</strong> — 
            typically caused by dust accumulation on the AGV's LiDAR lens. This is the primary AGV failure mode
            in the demo scenario, triggered by low humidity and high dust conditions.
        </div>
    </div>
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['success']};">
        <div style="color: {COLORS['success']}; font-weight: 700; margin-bottom: 0.5rem;">OEE (Overall Equipment Effectiveness)</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            Traditional manufacturing KPI measuring <strong style="color: {COLORS['text']};">Availability × Performance × Quality</strong>.
            OEE focuses on individual machine performance but misses losses in material flow between stations.
        </div>
    </div>
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['accent']};">
        <div style="color: {COLORS['accent']}; font-weight: 700; margin-bottom: 0.5rem;">OPE (Overall Process Efficiency)</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            Extended metric that includes <strong style="color: {COLORS['text']};">wait time, queue time, and material flow</strong>.
            OPE captures the "white space" losses that OEE misses — like AGV delays causing line starvation.
        </div>
    </div>
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['warning']};">
        <div style="color: {COLORS['warning']}; font-weight: 700; margin-bottom: 0.5rem;">Jidoka</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            A Toyota Production System principle meaning <strong style="color: {COLORS['text']};">"automation with human intelligence"</strong>.
            Jidoka empowers machines and systems to detect abnormalities and stop automatically, 
            allowing humans to focus on problem-solving rather than monitoring.
        </div>
    </div>
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; border-left: 4px solid {COLORS['muted']};">
        <div style="color: {COLORS['text']}; font-weight: 700; margin-bottom: 0.5rem;">Starvation</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            Production line downtime caused by <strong style="color: {COLORS['text']};">lack of incoming materials</strong>.
            When AGVs fail, they can't deliver materials to production stations, causing lines to "starve" 
            and wait idle despite equipment being operational.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# HOW IT WORKS - EXECUTIVE
# =============================================================================

render_section_header("How It Works", "The causal chain and AI orchestration")

st.markdown(f"""
### The Iceberg Problem

Think of factory efficiency like an iceberg. **OEE (Overall Equipment Effectiveness)** shows you the 10% 
above the waterline — machines running, operators working. But **90% of your losses** lurk below: 
material waiting in queues, AGVs stuck with sensor errors, lines starving for the next batch.

<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
    <div style="color: {COLORS['text']}; font-weight: 600; margin-bottom: 1rem;">The Hidden Causal Chain</div>
    <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
        <div style="background: {COLORS['warning']}20; color: {COLORS['warning']}; padding: 0.5rem 1rem; border-radius: 4px;">
            Low Humidity (25%)
        </div>
        <span style="color: {COLORS['muted']};">→</span>
        <div style="background: {COLORS['danger']}20; color: {COLORS['danger']}; padding: 0.5rem 1rem; border-radius: 4px;">
            High Dust (35 µg/m³)
        </div>
        <span style="color: {COLORS['muted']};">→</span>
        <div style="background: {COLORS['danger']}20; color: {COLORS['danger']}; padding: 0.5rem 1rem; border-radius: 4px;">
            AGV-ERR-99 Errors
        </div>
        <span style="color: {COLORS['muted']};">→</span>
        <div style="background: {COLORS['danger']}20; color: {COLORS['danger']}; padding: 0.5rem 1rem; border-radius: 4px;">
            Material Starvation
        </div>
        <span style="color: {COLORS['muted']};">→</span>
        <div style="background: {COLORS['danger']}20; color: {COLORS['danger']}; padding: 0.5rem 1rem; border-radius: 4px;">
            OPE Drop to 60%
        </div>
    </div>
</div>

### How AI Finds the Root Cause

Traditional analysis: An engineer spends 4 hours pulling reports, cross-referencing error logs, 
checking environmental data, and reading maintenance manuals.

**With Intelligent Jidoka:** The AI automatically:
1. **Queries metrics** to identify OPE anomalies
2. **Correlates** environmental data with failure patterns  
3. **Searches** maintenance manuals for remediation steps
4. **Recommends** a "Dust Mitigation Cycle" — before the line stops
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# DATA ARCHITECTURE
# =============================================================================

render_section_header("Data Architecture", "Medallion architecture data flow")

# Display SVG diagram from deployed assets
st.image("assets/data_architecture.svg", use_container_width=True)

st.markdown("")

# Data sources in three columns
st.markdown("##### Data Sources")
col1, col2, col3 = st.columns(3)

with col1:
    render_data_source_badge("internal", "ERP, MES")
    st.markdown(f"""
<div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-top: 0.5rem;">
    Production orders, inventory movements, equipment states, AGV telemetry
</div>
    """, unsafe_allow_html=True)

with col2:
    render_data_source_badge("external", "IoT Sensors")
    st.markdown(f"""
<div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-top: 0.5rem;">
    Environmental readings: humidity, PM2.5 dust levels, temperature
</div>
    """, unsafe_allow_html=True)

with col3:
    render_data_source_badge("model", "ML & AI Outputs")
    st.markdown(f"""
<div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-top: 0.5rem;">
    Predictive maintenance alerts, document chunks for RAG
</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# CORTEX AI COMPONENTS
# =============================================================================

render_section_header("Cortex AI Components", "AI capabilities and integration")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem;">
    <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem;">Analyst</div>
    <h5 style="color: {COLORS['text']}; margin: 0;">Cortex Analyst</h5>
    <p style="color: {COLORS['muted']}; font-size: 0.875rem; margin: 0.5rem 0;">
        Natural language queries over OPE metrics using semantic model.
    </p>
    <div style="font-size: 0.75rem; color: {COLORS['accent']}; margin-top: 0.5rem;">
        "Show me OPE trend for Line 4"
    </div>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem;">
    <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem;">Search</div>
    <h5 style="color: {COLORS['text']}; margin: 0;">Cortex Search</h5>
    <p style="color: {COLORS['muted']}; font-size: 0.875rem; margin: 0.5rem 0;">
        RAG over maintenance manuals and SOPs for troubleshooting guidance.
    </p>
    <div style="font-size: 0.75rem; color: {COLORS['accent']}; margin-top: 0.5rem;">
        "What does AGV-ERR-99 mean?"
    </div>
</div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem;">
    <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem;">Agent</div>
    <h5 style="color: {COLORS['text']}; margin: 0;">Cortex Agent</h5>
    <p style="color: {COLORS['muted']}; font-size: 0.875rem; margin: 0.5rem 0;">
        Orchestrates multi-tool reasoning for autonomous diagnosis.
    </p>
    <div style="font-size: 0.75rem; color: {COLORS['accent']}; margin-top: 0.5rem;">
        Query → Forecast → Search → Recommend
    </div>
</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# DEMO SCENARIO
# =============================================================================

render_section_header("Demo Scenario", "The December Crisis story")

st.markdown(f"""
<div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid {COLORS['warning']}; 
            padding: 1.25rem; border-radius: 0 8px 8px 0;">
    <h5 style="color: {COLORS['text']}; margin: 0;">The Data Story</h5>
    <div style="display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap;">
        <div>
            <div style="color: {COLORS['success']}; font-weight: 600;">Months 1-2: Baseline</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">Normal operation, OPE ~85%</div>
        </div>
        <div style="color: {COLORS['muted']};">→</div>
        <div>
            <div style="color: {COLORS['danger']}; font-weight: 600;">Dec 9-11: Crisis</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">Humidity 25% → Dust 35µg/m³ → AGV-ERR-99 → OPE 60%</div>
        </div>
        <div style="color: {COLORS['muted']};">→</div>
        <div>
            <div style="color: {COLORS['accent']}; font-weight: 600;">The Insight</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">ML proves environmental causation</div>
        </div>
        <div style="color: {COLORS['muted']};">→</div>
        <div>
            <div style="color: {COLORS['success']}; font-weight: 600;">The Action</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">AI recommends Dust Mitigation Cycle</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# The Wow Moment
st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1.25rem; margin-top: 1rem;">
    <h5 style="color: {COLORS['accent']}; margin: 0 0 0.5rem 0;">New Insight</h5>
    <p style="color: {COLORS['muted']}; margin: 0;">
        A Cortex Agent autonomously correlates a structured forecast (high dust probability) with 
        unstructured maintenance manuals (sensor failure protocols) to proactively recommend a 
        "Dust Mitigation Cycle" <strong style="color: {COLORS['text']};">before</strong> the line stops — 
        demonstrating true <em>Jidoka</em> (automation with human intelligence).
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# APPLICATION PAGES
# =============================================================================

render_section_header("Application Pages", "Navigation guide")

pages_data = [
    {"name": "Home", "target": "All users", 
     "description": "Overview, navigation, and demo scenario introduction"},
    {"name": "Executive Dashboard", "target": "VP Manufacturing",
     "description": "Strategic KPIs, OEE vs OPE gap analysis, AI-powered insights"},
    {"name": "Unit Economics", "target": "Finance/Ops",
     "description": "Cost impact analysis, ROI calculations, efficiency metrics"},
    {"name": "Operations Control", "target": "Plant Manager",
     "description": "Actionable alerts, AGV fleet status, SOP lookups"},
    {"name": "ML Analysis", "target": "Data Scientist",
     "description": "Feature importance, model metrics, raw data explorer"},
    {"name": "About", "target": "All users",
     "description": "This documentation page"},
]

col1, col2 = st.columns(2)

for i, page in enumerate(pages_data):
    with col1 if i % 2 == 0 else col2:
        st.markdown(f"""
<div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem; 
            background: {COLORS['surface']}; border-radius: 8px; margin-bottom: 0.5rem;">
    <div style="flex: 1;">
        <div style="color: {COLORS['text']}; font-weight: 600;">{page['name']}</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">{page['description']}</div>
    </div>
    <div style="background: {COLORS['accent']}20; color: {COLORS['accent']}; padding: 2px 8px; 
            border-radius: 4px; font-size: 0.75rem; white-space: nowrap;">{page['target']}</div>
</div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# TECHNOLOGY STACK
# =============================================================================

render_section_header("Technology Stack", "Platform and tools")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem;">
    <h5 style="color: {COLORS['text']}; margin: 0 0 0.75rem 0;">Data Platform</h5>
    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        <span style="background: {COLORS['snowflake']}30; color: {COLORS['snowflake']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Snowflake</span>
        <span style="background: {COLORS['accent']}30; color: {COLORS['accent']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Snowpark</span>
        <span style="background: {COLORS['success']}30; color: {COLORS['success']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Dynamic Tables</span>
    </div>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem;">
    <h5 style="color: {COLORS['text']}; margin: 0 0 0.75rem 0;">AI / ML</h5>
    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        <span style="background: {COLORS['snowflake']}30; color: {COLORS['snowflake']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Cortex Analyst</span>
        <span style="background: {COLORS['accent']}30; color: {COLORS['accent']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Cortex Search</span>
        <span style="background: {COLORS['warning']}30; color: {COLORS['warning']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">XGBoost</span>
    </div>
</div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem;">
    <h5 style="color: {COLORS['text']}; margin: 0 0 0.75rem 0;">Visualization</h5>
    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        <span style="background: {COLORS['danger']}30; color: {COLORS['danger']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Streamlit</span>
        <span style="background: {COLORS['accent']}30; color: {COLORS['accent']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Plotly</span>
        <span style="background: {COLORS['success']}30; color: {COLORS['success']}; 
                     padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">Altair</span>
    </div>
</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# TECHNICAL DEEP DIVE
# =============================================================================

render_section_header("Technical Deep Dive", "Architecture and implementation details")

st.markdown(f"""
### Architecture Overview

The system implements a **Bronze → Silver → Gold** medallion architecture within Snowflake:

| Layer | Schema | Purpose | Object Types |
|-------|--------|---------|--------------|
| **Bronze** | `RAW` | Source system mirrors, CDC feeds | 5 tables |
| **Silver** | `ATOMIC` | Enterprise data model, Type 2 SCD | 9 tables |
| **Gold** | `EV_OPE` | Analytics data mart, ML outputs | 5 views, 2 tables |

### ML Pipeline
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center;">
    <div style="color: {COLORS['accent']}; font-weight: 600; font-size: 0.75rem;">Algorithm</div>
    <div style="color: {COLORS['text']}; font-weight: 700;">XGBoost</div>
</div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center;">
    <div style="color: {COLORS['accent']}; font-weight: 600; font-size: 0.75rem;">Target</div>
    <div style="color: {COLORS['text']}; font-weight: 700;">IS_HIGH_FAILURE</div>
</div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center;">
    <div style="color: {COLORS['accent']}; font-weight: 600; font-size: 0.75rem;">ROC-AUC</div>
    <div style="color: {COLORS['success']}; font-weight: 700;">> 0.90</div>
</div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center;">
    <div style="color: {COLORS['accent']}; font-weight: 600; font-size: 0.75rem;">Training Data</div>
    <div style="color: {COLORS['text']}; font-weight: 700;">AGV_FAILURE</div>
</div>
    """, unsafe_allow_html=True)

st.markdown(f"""
### Key Technical Components

- **Dynamic Tables**: RAW → ATOMIC transformation with automatic refresh
- **Computed Views**: OPE metrics aggregated from WORK_ORDER, EQUIPMENT_DOWNTIME, EQUIPMENT_FAILURE
- **Cortex Search Service**: `MFG_KNOWLEDGE_BASE_SEARCH` indexing maintenance manuals
- **Semantic Model**: Powers Cortex Analyst for natural language queries

### Data Flow
""", unsafe_allow_html=True)

st.code("""
ERP ─────────┐
             ├──► RAW Schema ──► ATOMIC Schema ──► EV_OPE Schema
MES ─────────┤    (CDC tables)   (9 tables)       (Views + Tables)
             │                        │                  │
IoT Sensors ─┘                        ▼                  ▼
                                 Type 2 SCD        Cortex Analyst
                                 Audit cols        Cortex Search
                                                   Streamlit App
""", language=None)

st.markdown(f"""
### Medallion Architecture Details

**RAW Schema (Bronze)**
- CDC-enabled tables preserving source system formats
- Metadata columns: `_CDC_OPERATION`, `_CDC_TIMESTAMP`, `_LOADED_TIMESTAMP`
- Change tracking enabled for Dynamic Table consumption

**ATOMIC Schema (Silver)**  
- Enterprise relational model aligned with core data dictionary
- Type 2 Slowly Changing Dimensions with `VALID_FROM/TO_TIMESTAMP`, `IS_CURRENT_FLAG`
- Audit columns: `CREATED_BY_USER`, `CREATED_TIMESTAMP`, `UPDATED_BY_USER`, `UPDATED_TIMESTAMP`

**EV_OPE Schema (Gold)**
- **Dimension Views**: Project current records from ATOMIC with `IS_CURRENT_FLAG = TRUE`
- **Fact Views**: Complex aggregations joining WORK_ORDER, EQUIPMENT_DOWNTIME, EQUIPMENT_FAILURE, ENVIRONMENTAL_READING
- **Output Tables**: Write targets for ML predictions and Cortex Search chunks

### OPE Calculation Logic
""", unsafe_allow_html=True)

st.code("""
-- OPE calculation (simplified)
OPE_PCT = OEE_AVAILABILITY × OEE_PERFORMANCE × OEE_QUALITY 
        × (1 - STARVATION_DOWNTIME / PLANNED_TIME)

-- Where:
-- OEE_AVAILABILITY = (PLANNED_TIME - DOWNTIME) / PLANNED_TIME
-- STARVATION_DOWNTIME = downtime where REASON_CODE = 'STARVATION'
""", language="sql")

st.markdown(f"""
### XGBoost Model Training Pipeline

1. **Data Source**: `AGV_FAILURE_ANALYSIS` view (hourly environmental + failure metrics)
2. **Features**: `AVG_HUMIDITY`, `MIN_HUMIDITY`, `AVG_DUST_PM25`, `MAX_DUST_PM25`, `AVG_TEMPERATURE`
3. **Target**: `IS_HIGH_FAILURE_PERIOD` (binary: failure rate > 5%)
4. **Training**: 80/20 split, early stopping, class weight balancing
5. **Output**: Predictions written to `PREDICTIVE_MAINTENANCE_ALERTS`

### Cortex Search Configuration
""", unsafe_allow_html=True)

st.code("""
Service: MFG_KNOWLEDGE_BASE_SEARCH
Indexed Column: CHUNK_TEXT
Attributes: DOCUMENT_NAME, DOCUMENT_TYPE, EQUIPMENT_MODEL, ERROR_CODE_TAG
Chunk Size: ~1500 chars with 200 char overlap
Target Lag: 1 hour
""", language=None)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {COLORS['muted']}; font-size: 0.875rem;">
    <strong style="color: {COLORS['text']};">VoltStream OPE Dashboard</strong> | 
    Built with <span style="color: {COLORS['snowflake']};">Snowflake</span> | 
    Database: VOLTSTREAM_EV_OPE
</div>
""", unsafe_allow_html=True)
