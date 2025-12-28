"""
Unit Economics - MBA Hero Shot View
====================================

The "Hero Shot" dashboard for Stanford MBA-level presentations.
Combines financial linkage, process mining, and AI-powered scenario analysis.

Components:
1. OPE-Adjusted EBITDA ticker (flashing red if below target)
2. Process Mining Sankey diagram with bottleneck visualization
3. Cortex Analyst for financial impact queries

Target Persona: CFO / VP Strategy (Financial)
"""

import sys
from pathlib import Path

# Add parent directory to path for utils imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from snowflake.snowpark.context import get_active_session

# Import utilities
from utils.ui_components import (
    apply_global_styles, COLORS, PLOTLY_THEME,
    render_section_header, render_ai_insight
)
from utils.data_loader import run_queries_parallel, convert_for_plotly
from utils.query_registry import (
    OPE_DAILY_METRICS_SQL, THROUGHPUT_ECONOMICS_SQL, THROUGHPUT_BY_LINE_SQL,
    SANKEY_FLOW_SUMMARY_SQL, LITTLES_LAW_METRICS_SQL, PENDING_ALERTS_SQL
)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Unit Economics | VoltStream OPE",
    page_icon="💰",
    layout="wide"
)

apply_global_styles()

# Custom CSS for financial dashboard aesthetic
st.markdown("""
<style>
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    .pulse-red {
        animation: pulse 1.5s ease-in-out infinite;
    }
    .financial-ticker {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        letter-spacing: -0.5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION AND DATA LOADING
# =============================================================================

@st.cache_resource
def get_session():
    return get_active_session()


@st.cache_data(ttl=300)
def load_unit_economics_data(_session):
    """Load all unit economics data using parallel queries."""
    queries = {
        'daily_metrics': OPE_DAILY_METRICS_SQL,
        'throughput_economics': THROUGHPUT_ECONOMICS_SQL,
        'throughput_by_line': THROUGHPUT_BY_LINE_SQL,
        'sankey_flow': SANKEY_FLOW_SUMMARY_SQL,
        'littles_law': LITTLES_LAW_METRICS_SQL,
        'alerts': PENDING_ALERTS_SQL
    }
    return run_queries_parallel(_session, queries, max_workers=6)


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown(f"""
<h1 style="color: #f8fafc;">Unit Economics Dashboard</h1>
<h4 style="color: {COLORS['muted']};">OPE-Adjusted Financial Performance</h4>
""", unsafe_allow_html=True)

# Load data
try:
    session = get_session()
    data = load_unit_economics_data(session)
    daily_metrics = data['daily_metrics']
    throughput_df = data.get('throughput_economics', pd.DataFrame())
    throughput_by_line = data.get('throughput_by_line', pd.DataFrame())
    sankey_df = data.get('sankey_flow', pd.DataFrame())
    littles_law_df = data.get('littles_law', pd.DataFrame())
    alerts = data.get('alerts', pd.DataFrame())
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please ensure the database is deployed and populated.")
    st.stop()

# Calculate financial metrics
latest_date = daily_metrics['METRIC_DATE'].max()
latest_data = daily_metrics[daily_metrics['METRIC_DATE'] == latest_date]

avg_oee = float(latest_data['OEE_PCT'].mean())
avg_ope = float(latest_data['OPE_PCT'].mean())
oee_ope_gap = avg_oee - avg_ope

# Financial assumptions
contribution_margin = 875  # $ per unit
units_per_hour = 60
hours_per_shift = 8
shifts_per_day = 3
working_days = 250

# Calculate EBITDA impact
hourly_throughput_loss = oee_ope_gap / 100 * units_per_hour * contribution_margin
daily_ebitda_impact = hourly_throughput_loss * hours_per_shift * shifts_per_day
annual_ebitda_impact = daily_ebitda_impact * working_days

# Target EBITDA (assume 15% margin on $500M revenue)
target_annual_ebitda = 75_000_000
current_annual_ebitda = target_annual_ebitda - annual_ebitda_impact
ebitda_variance = (current_annual_ebitda - target_annual_ebitda) / target_annual_ebitda * 100

is_below_target = current_annual_ebitda < target_annual_ebitda

# =============================================================================
# HERO SECTION: OPE-ADJUSTED EBITDA TICKER
# =============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Main EBITDA Ticker - Flashing red if below target
    ticker_class = "pulse-red" if is_below_target else ""
    ticker_color = COLORS['danger'] if is_below_target else COLORS['success']
    
    st.markdown(f"""
    <div class="{ticker_class}" style="background: linear-gradient(135deg, rgba({int(ticker_color[1:3], 16)}, {int(ticker_color[3:5], 16)}, {int(ticker_color[5:7], 16)}, 0.2) 0%, {COLORS['surface']} 100%);
                border: 2px solid {ticker_color}; border-radius: 16px; padding: 1.5rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px;">
            OPE-Adjusted EBITDA
        </div>
        <div class="financial-ticker" style="color: {ticker_color}; font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0;">
            ${current_annual_ebitda/1_000_000:.1f}M
        </div>
        <div style="color: {ticker_color}; font-size: 0.875rem; font-weight: 600;">
            {ebitda_variance:+.1f}% vs Target
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 16px; padding: 1.5rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            Throughput Loss
        </div>
        <div class="financial-ticker" style="color: {COLORS['danger']}; font-size: 2rem; font-weight: 700; margin: 0.5rem 0;">
            ${hourly_throughput_loss:,.0f}/hr
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            ${annual_ebitda_impact/1_000_000:.1f}M annually
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 16px; padding: 1.5rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            OEE → OPE Gap
        </div>
        <div class="financial-ticker" style="color: {COLORS['warning']}; font-size: 2rem; font-weight: 700; margin: 0.5rem 0;">
            {oee_ope_gap:.1f}%
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            Hidden Factory loss
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # Recovery potential
    recovery_rate = 0.7  # 70% recoverable with interventions
    recoverable = annual_ebitda_impact * recovery_rate
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 16px; padding: 1.5rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            Recoverable Value
        </div>
        <div class="financial-ticker" style="color: {COLORS['accent']}; font-size: 2rem; font-weight: 700; margin: 0.5rem 0;">
            ${recoverable/1_000_000:.1f}M
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem;">
            with Jidoka intervention
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# PROCESS MINING SANKEY - With Bottleneck Highlight
# =============================================================================

col1, col2 = st.columns([2, 1])

with col1:
    render_section_header("Process Mining View", "Value stream with bottleneck analysis")
    
    if len(sankey_df) > 0:
        # Build Sankey diagram
        node_labels = ['RAW_MATERIALS', 'LINE_1', 'LINE_2', 'LINE_3', 'LINE_4', 'LINE_5',
                       'AGV_TRANSFER', 'QC_INSPECTION', 'FINISHED_GOODS', 'REWORK_QUEUE']
        node_label_display = ['Raw Materials', 'Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5',
                              'AGV Transfer', 'QC Inspection', 'Finished Goods', 'Rework (Ghost)']
        
        node_map = {label: idx for idx, label in enumerate(node_labels)}
        
        sources = []
        targets = []
        values = []
        link_colors = []
        
        for _, row in sankey_df.iterrows():
            source = str(row['SOURCE_NODE'])
            target = str(row['TARGET_NODE'])
            value = float(row['FLOW_VALUE']) if pd.notna(row['FLOW_VALUE']) else 0
            status = str(row['FLOW_STATUS']) if pd.notna(row['FLOW_STATUS']) else 'HEALTHY'
            
            if source in node_map and target in node_map and value > 0:
                sources.append(node_map[source])
                targets.append(node_map[target])
                values.append(value)
                
                if status == 'CRITICAL':
                    link_colors.append('rgba(239, 68, 68, 0.7)')
                elif status == 'WARNING':
                    link_colors.append('rgba(245, 158, 11, 0.6)')
                else:
                    link_colors.append('rgba(34, 197, 94, 0.4)')
        
        # Node colors - highlight bottleneck
        node_colors = []
        for label in node_labels:
            if label == 'AGV_TRANSFER':
                node_colors.append('#ef4444')  # Red - bottleneck
            elif label == 'REWORK_QUEUE':
                node_colors.append('#f59e0b')  # Orange - ghost inventory
            elif label == 'LINE_4':
                node_colors.append('#f59e0b')  # Orange - crisis line
            else:
                node_colors.append(COLORS['snowflake'])
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(color=COLORS['border'], width=1),
                label=node_label_display,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors
            )
        )])
        
        fig.update_layout(
            **PLOTLY_THEME,
            height=350,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True, key="hero_sankey")
    else:
        st.info("Loading process mining data...")

with col2:
    render_section_header("Bottleneck Analysis", "Top constraints")
    
    # Bottleneck cards
    st.markdown(f"""
    <div style="background: rgba(239, 68, 68, 0.15); border-left: 4px solid {COLORS['danger']}; 
                padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 0.75rem;">
        <div style="color: {COLORS['danger']}; font-weight: 700; font-size: 0.9rem;">
            #1 AGV Transfer Point
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.8rem; margin-top: 0.25rem;">
            Dust-induced sensor errors blocking 15% of flow
        </div>
        <div style="color: {COLORS['text']}; font-size: 1.1rem; font-weight: 600; margin-top: 0.5rem;">
            Impact: ${hourly_throughput_loss * 0.6:,.0f}/hr
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: rgba(245, 158, 11, 0.15); border-left: 4px solid {COLORS['warning']}; 
                padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 0.75rem;">
        <div style="color: {COLORS['warning']}; font-weight: 700; font-size: 0.9rem;">
            #2 Line 4 Starvation
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.8rem; margin-top: 0.25rem;">
            Material wait time causing 25% capacity loss
        </div>
        <div style="color: {COLORS['text']}; font-size: 1.1rem; font-weight: 600; margin-top: 0.5rem;">
            Impact: ${hourly_throughput_loss * 0.3:,.0f}/hr
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid {COLORS['muted']}; 
                padding: 1rem; border-radius: 0 8px 8px 0;">
        <div style="color: {COLORS['muted']}; font-weight: 700; font-size: 0.9rem;">
            #3 QC Rework Loop
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.8rem; margin-top: 0.25rem;">
            3% of units cycling back (Ghost Inventory)
        </div>
        <div style="color: {COLORS['text']}; font-size: 1.1rem; font-weight: 600; margin-top: 0.5rem;">
            Impact: ${hourly_throughput_loss * 0.1:,.0f}/hr
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# FINANCIAL WATERFALL - EBITDA Bridge
# =============================================================================

render_section_header("EBITDA Bridge", "From target to actual performance")

# Create waterfall chart - showing Target, losses breakdown, and final Actual EBITDA
# Note: Plotly waterfall in Snowflake doesn't support marker colors, using shape overlay
waterfall_data = {
    'Category': ['Target EBITDA', 'AGV Failures', 'Starvation', 'Rework/Scrap', 'Other Losses', 'Actual EBITDA'],
    'Value': [target_annual_ebitda/1e6, 
              -annual_ebitda_impact * 0.45 / 1e6,  # 45% from AGV
              -annual_ebitda_impact * 0.35 / 1e6,  # 35% from starvation
              -annual_ebitda_impact * 0.12 / 1e6,  # 12% from rework
              -annual_ebitda_impact * 0.08 / 1e6,  # 8% other
              0],  # Placeholder - 'total' type calculates from running sum
    'Type': ['absolute', 'relative', 'relative', 'relative', 'relative', 'total']
}

# Custom text labels - show actual values
text_labels = [
    f"${target_annual_ebitda/1e6:.1f}M",                    # Target
    f"-${annual_ebitda_impact * 0.45 / 1e6:.1f}M",          # AGV
    f"-${annual_ebitda_impact * 0.35 / 1e6:.1f}M",          # Starvation
    f"-${annual_ebitda_impact * 0.12 / 1e6:.1f}M",          # Rework
    f"-${annual_ebitda_impact * 0.08 / 1e6:.1f}M",          # Other
    f"${current_annual_ebitda/1e6:.1f}M"                    # Actual EBITDA (total)
]

fig = go.Figure(go.Waterfall(
    name="EBITDA",
    orientation="v",
    x=waterfall_data['Category'],
    textposition="outside",
    text=text_labels,
    y=waterfall_data['Value'],
    measure=waterfall_data['Type'],
    connector={"line": {"color": COLORS['border']}},
    # Standard waterfall colors - Actual will be green via totals
    increasing={"marker": {"color": COLORS['success']}},
    decreasing={"marker": {"color": COLORS['danger']}},
    totals={"marker": {"color": COLORS['success']}}
))

# Add rectangle shape to overlay Target EBITDA bar with Snowflake Blue
# This workaround is needed because Plotly waterfall doesn't support per-bar colors
fig.add_shape(
    type="rect",
    x0=-0.4, x1=0.4,  # Position around first category (index 0)
    y0=0, y1=target_annual_ebitda/1e6,
    fillcolor=COLORS['snowflake'],
    line=dict(width=0),
    layer="above"
)

# Calculate Y-axis range with padding for labels
y_max = target_annual_ebitda / 1e6 * 1.15  # 15% padding above target for labels

fig.update_layout(
    **PLOTLY_THEME,
    height=350,
    margin=dict(l=40, r=40, t=50, b=80),
    yaxis_title='EBITDA ($M)',
    yaxis=dict(
        tickformat='$,.0f', 
        color=COLORS['muted'],
        range=[0, y_max]  # Explicit range to prevent label cutoff
    ),
    xaxis=dict(color=COLORS['text']),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True, key="ebitda_waterfall")

# EBITDA summary annotation showing variance from target (colors match chart)
variance_amount = annual_ebitda_impact / 1e6  # Total loss amount
st.markdown(f"""
<div style="display: flex; justify-content: center; gap: 2rem; margin-top: -0.5rem; margin-bottom: 1rem;">
    <div style="text-align: center;">
        <span style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">Target</span>
        <span style="color: {COLORS['snowflake']}; font-size: 1rem; font-weight: 600; margin-left: 0.5rem;">${target_annual_ebitda/1e6:.1f}M</span>
    </div>
    <div style="text-align: center;">
        <span style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">Actual</span>
        <span style="color: {COLORS['success']}; font-size: 1rem; font-weight: 600; margin-left: 0.5rem;">${current_annual_ebitda/1e6:.1f}M</span>
    </div>
    <div style="text-align: center;">
        <span style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">Variance</span>
        <span style="color: {COLORS['danger']}; font-size: 1rem; font-weight: 600; margin-left: 0.5rem;">-${variance_amount:.1f}M ({ebitda_variance:.1f}%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# AI insight for waterfall
render_ai_insight(
    f"AGV failures account for 45% of the EBITDA gap (${annual_ebitda_impact * 0.45 / 1e6:.1f}M annually). "
    f"Resolving the dust-sensor correlation through HVAC optimization would recover approximately "
    f"${recoverable * 0.6 / 1e6:.1f}M in annual EBITDA. Payback period: <30 days.",
    "Financial Root Cause"
)

st.markdown("---")

# =============================================================================
# LITTLE'S LAW INDICATOR
# =============================================================================

if len(littles_law_df) > 0 and 'LITTLES_LAW_VIOLATION' in littles_law_df.columns:
    violations = littles_law_df[littles_law_df['LITTLES_LAW_VIOLATION'] == True]
    
    if len(violations) > 0:
        render_section_header("System Dynamics Alert", "Little's Law divergence detected")
        
        latest = violations.iloc[0]
        wip = int(latest['WIP_COUNT']) if pd.notna(latest.get('WIP_COUNT')) else 0
        throughput = int(latest['THROUGHPUT_UNITS']) if pd.notna(latest.get('THROUGHPUT_UNITS')) else 1
        cycle_time = float(latest['CALCULATED_CYCLE_TIME_MIN']) if pd.notna(latest.get('CALCULATED_CYCLE_TIME_MIN')) else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem; text-align: center;">
                <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">WIP (L)</div>
                <div style="color: {COLORS['warning']}; font-size: 2rem; font-weight: 700;">{wip}</div>
                <div style="color: {COLORS['danger']}; font-size: 0.75rem;">↑ Above normal</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem; text-align: center;">
                <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Throughput (λ)</div>
                <div style="color: {COLORS['muted']}; font-size: 2rem; font-weight: 700;">{throughput}</div>
                <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Stagnant</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem; text-align: center;">
                <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Cycle Time (W)</div>
                <div style="color: {COLORS['danger']}; font-size: 2rem; font-weight: 700;">{cycle_time:.0f}</div>
                <div style="color: {COLORS['danger']}; font-size: 0.75rem;">min (degrading)</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <div style="color: {COLORS['text']}; font-size: 0.875rem;">
                <strong>Little's Law:</strong> L = λ × W → {wip} = {throughput} × {cycle_time/60:.1f}hr
            </div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-top: 0.5rem;">
                WIP is accumulating faster than throughput can process. Classic sign of hidden bottleneck.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")

# =============================================================================
# RECOMMENDED ACTIONS
# =============================================================================

render_section_header("Recommended Actions", "AI-prioritized by financial impact")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, {COLORS['surface']} 100%);
                border: 1px solid {COLORS['success']}; border-radius: 12px; padding: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span style="color: {COLORS['success']}; font-weight: 700;">Priority 1</span>
        </div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin-bottom: 0.5rem;">
            Execute Dust Mitigation Cycle
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem; line-height: 1.5;">
            HVAC humidification + sensor cleaning
        </div>
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid {COLORS['border']};">
            <div style="color: {COLORS['success']}; font-size: 1.25rem; font-weight: 700;">
                +$34K/hr
            </div>
            <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Expected recovery</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 12px; padding: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span style="color: {COLORS['warning']}; font-weight: 700;">Priority 2</span>
        </div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin-bottom: 0.5rem;">
            Reroute Line 4 (Temporary)
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem; line-height: 1.5;">
            Bypass AGV until sensors cleaned
        </div>
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid {COLORS['border']};">
            <div style="color: {COLORS['accent']}; font-size: 1.25rem; font-weight: 700;">
                +$12K/hr
            </div>
            <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Net of labor cost</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 12px; padding: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span style="color: {COLORS['muted']}; font-weight: 700;">Priority 3</span>
        </div>
        <div style="color: {COLORS['text']}; font-weight: 600; margin-bottom: 0.5rem;">
            Increase Buffer Stock 10%
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.875rem; line-height: 1.5;">
            Reduce starvation risk long-term
        </div>
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid {COLORS['border']};">
            <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700;">
                +$5K/hr
            </div>
            <div style="color: {COLORS['muted']}; font-size: 0.75rem;">Requires $500K capital</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {COLORS['muted']}; font-size: 0.875rem;">
    Unit Economics Dashboard | VoltStream Manufacturing Intelligence | Data as of {latest_date}
</div>
""", unsafe_allow_html=True)

