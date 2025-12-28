"""
VoltStream OPE Dashboard - Main Entry Point
============================================

Intelligent Jidoka System for EV Gigafactory OPE Analytics.
Powered by Snowflake Cortex AI.

Personas:
- VP Manufacturing (Strategic): Executive Dashboard
- Plant Manager (Operational): Operations Control
- Data Scientist (Technical): ML Analysis
"""

import sys
from pathlib import Path

# Add current directory to path for utils imports (required for Streamlit in Snowflake)
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from snowflake.snowpark.context import get_active_session

# Import utilities
from utils.ui_components import apply_global_styles, COLORS, render_metric_row
from utils.data_loader import run_queries_parallel
from utils.query_registry import QUICK_STATS_SQL

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="VoltStream OPE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global dark theme styles
apply_global_styles()

# =============================================================================
# SESSION
# =============================================================================

@st.cache_resource
def get_session():
    """Get Snowflake session."""
    return get_active_session()


@st.cache_data(ttl=300)
def load_quick_stats(_session):
    """Load quick stats for sidebar using registered query."""
    results = run_queries_parallel(_session, {'stats': QUICK_STATS_SQL}, max_workers=1)
    return results['stats'].iloc[0] if not results['stats'].empty else None


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # Branding
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="color: {COLORS['snowflake']}; font-size: 2rem;">❄️</div>
        <div style="color: {COLORS['text']}; font-weight: 700; margin-top: 0.5rem;">Snowflake</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown(f"""
    <div style="text-align: center;">
        <div style="font-size: 1.5rem;">⚡</div>
        <div style="color: {COLORS['text']}; font-weight: 700;">VoltStream</div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">OPE Intelligent Jidoka</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Stats
    st.markdown(f"### Quick Stats")
    
    try:
        session = get_session()
        stats = load_quick_stats(session)
        
        if stats is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Lines", int(stats['ACTIVE_LINES']))
            with col2:
                avg_ope = float(stats['AVG_OPE'])
                st.metric("OPE", f"{avg_ope:.0f}%")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("OEE", f"{float(stats['AVG_OEE']):.0f}%")
            with col2:
                st.metric("AGV Fails", int(stats['TOTAL_AGV_FAILURES']), help="Automated Guided Vehicle failures")
        
            st.markdown(f"""
            <div style="color: {COLORS['muted']}; font-size: 0.7rem; margin-top: 0.5rem; padding: 0.5rem; background: {COLORS['surface']}; border-radius: 4px;">
                <strong>AGV</strong> = Automated Guided Vehicles (self-driving transport robots)
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.info("Connect to load stats")
    
    st.markdown("---")
    
    # Persona Quick Access
    st.markdown("### Quick Access")
    st.markdown(f"""
    <div style="font-size: 0.875rem; color: {COLORS['muted']};">
        Navigate by role:
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    - **Executive Dashboard** - VP view
    - **Operations Control** - Plant Manager
    - **ML Analysis** - Data Scientist
    - **About** - Documentation
    """)


# =============================================================================
# MAIN CONTENT - HOME PAGE
# =============================================================================

# Title
st.markdown(f"""
<h1 style="color: #f8fafc;">⚡ VoltStream EV Manufacturing</h1>
<h3 style="color: {COLORS['muted']};">OPE Intelligent Jidoka System</h3>
""", unsafe_allow_html=True)

# STAR Narrative: SITUATION (The Problem)
st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
    <h4 style="color: {COLORS['text']}; margin-top: 0;">The Challenge</h4>
    <p style="color: {COLORS['muted']}; line-height: 1.6;">
        In high-volume EV Gigafactories, efficiency losses hide in the <strong style="color: {COLORS['text']};">white space</strong> 
        between production steps. Traditional OEE metrics show 90%+ equipment uptime, yet actual throughput tells a different story.
    </p>
    <div style="display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap;">
        <div>
            <div style="color: {COLORS['danger']}; font-size: 1.5rem; font-weight: 700;">Ghost Inventory</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">ERP shows "available" but shop floor is starved</div>
        </div>
        <div>
            <div style="color: {COLORS['warning']}; font-size: 1.5rem; font-weight: 700;">Hidden Losses</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">High OEE masks low OPE</div>
        </div>
        <div>
            <div style="color: {COLORS['accent']}; font-size: 1.5rem; font-weight: 700;">4+ Hours</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">Current time for root cause analysis</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# STAR Narrative: TASK (The Solution)
st.markdown(f"""
<h4 style="color: {COLORS['text']};">The Solution: Jidoka 2.0</h4>
<p style="color: {COLORS['muted']};">
    <strong style="color: {COLORS['text']};">Intelligent Jidoka</strong> — automation with human intelligence, powered by Snowflake Cortex:
</p>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center; height: 140px;">
        <div style="color: {COLORS['snowflake']}; font-size: 1.5rem; font-weight: 700;">Analyst</div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin: 0.5rem 0;">Cortex Analyst</div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Natural language queries over OPE metrics</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center; height: 140px;">
        <div style="color: {COLORS['snowflake']}; font-size: 1.5rem; font-weight: 700;">Search</div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin: 0.5rem 0;">Cortex Search</div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">RAG over maintenance manuals and SOPs</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center; height: 140px;">
        <div style="color: {COLORS['snowflake']}; font-size: 1.5rem; font-weight: 700;">Agent</div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin: 0.5rem 0;">Cortex Agent</div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Orchestrates analysis and recommendations</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center; height: 140px;">
        <div style="color: {COLORS['snowflake']}; font-size: 1.5rem; font-weight: 700;">ML</div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin: 0.5rem 0;">Snowpark ML</div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Predictive AGV failure forecasting</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# STAR Narrative: ACTION (Navigate by Persona)
st.markdown(f"""
<h4 style="color: {COLORS['text']};">Navigate by Role</h4>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                border: 1px solid {COLORS['border']}; border-radius: 12px; padding: 1.5rem;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">VP Manufacturing</div>
        <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700; margin: 0.5rem 0;">
            Executive Dashboard
        </div>
        <p style="color: {COLORS['muted']}; font-size: 0.875rem; margin: 0.5rem 0;">
            Strategic KPIs, OEE vs OPE gap analysis, AI-powered insights
        </p>
        <div style="color: {COLORS['accent']}; font-size: 0.875rem; margin-top: 0.5rem;">
            "Why did OPE drop on Line 4?"
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                border: 1px solid {COLORS['border']}; border-radius: 12px; padding: 1.5rem;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Plant Manager</div>
        <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700; margin: 0.5rem 0;">
            Operations Control
        </div>
        <p style="color: {COLORS['muted']}; font-size: 0.875rem; margin: 0.5rem 0;">
            Actionable alerts, AGV fleet status, SOP lookups
        </p>
        <div style="color: {COLORS['accent']}; font-size: 0.875rem; margin-top: 0.5rem;">
            "Approve Dust Mitigation Cycle"
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                border: 1px solid {COLORS['border']}; border-radius: 12px; padding: 1.5rem;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Data Scientist</div>
        <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700; margin: 0.5rem 0;">
            ML Analysis
        </div>
        <p style="color: {COLORS['muted']}; font-size: 0.875rem; margin: 0.5rem 0;">
            Model insights, feature importance, environmental correlation
        </p>
        <div style="color: {COLORS['accent']}; font-size: 0.875rem; margin-top: 0.5rem;">
            "Verify humidity-dust-failure correlation"
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Demo Scenario Callout
st.markdown(f"""
<div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid {COLORS['warning']}; 
            padding: 1rem; border-radius: 0 8px 8px 0;">
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <strong style="color: {COLORS['text']};">Demo Scenario: The December Crisis</strong>
    </div>
    <p style="color: {COLORS['muted']}; margin: 0.5rem 0 0 0;">
        December 9-11: Low humidity (25%) → Dust spike (35 µg/m³) → AGV-ERR-99 sensor errors → 
        Material starvation → OPE drops to 60% on Line 4
    </p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {COLORS['muted']}; font-size: 0.875rem;">
    Powered by <span style="color: {COLORS['snowflake']};">Snowflake Cortex</span> | 
    VoltStream EV Manufacturing Demo
</div>
""", unsafe_allow_html=True)
