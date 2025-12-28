"""
Executive Dashboard - VP Manufacturing View
============================================

STAR Flow:
- Situation: OEE-OPE gap reveals hidden inefficiency
- Task: Investigate root cause
- Action: Drill down with AI assistance
- Result: Data-backed insights and recommendations

Target Persona: VP of Manufacturing (Strategic)
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
    render_metric_row, render_alert_card, render_ai_insight,
    render_section_header, render_legend
)
from utils.data_loader import run_queries_parallel, convert_for_plotly
from utils.query_registry import (
    OPE_DAILY_METRICS_SQL, OPE_BY_LINE_SQL,
    DAILY_TREND_SQL, ENV_TREND_SQL, PENDING_ALERTS_SQL,
    THROUGHPUT_ECONOMICS_SQL, THROUGHPUT_BY_LINE_SQL,
    SANKEY_FLOW_SUMMARY_SQL
)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Executive Dashboard | VoltStream OPE",
    page_icon="📊",
    layout="wide"
)

apply_global_styles()

# =============================================================================
# SESSION AND DATA LOADING
# =============================================================================

@st.cache_resource
def get_session():
    return get_active_session()


@st.cache_data(ttl=300)
def load_dashboard_data(_session):
    """Load all dashboard data using parallel queries."""
    queries = {
        'daily_metrics': OPE_DAILY_METRICS_SQL,
        'by_line': OPE_BY_LINE_SQL,
        'daily_trend': DAILY_TREND_SQL,
        'env_trend': ENV_TREND_SQL,
        'alerts': PENDING_ALERTS_SQL,
        'throughput_economics': THROUGHPUT_ECONOMICS_SQL,
        'throughput_by_line': THROUGHPUT_BY_LINE_SQL,
        'sankey_flow': SANKEY_FLOW_SUMMARY_SQL
    }
    return run_queries_parallel(_session, queries, max_workers=6)


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown(f"""
<h1 style="color: #f8fafc;">Executive Dashboard</h1>
<h4 style="color: {COLORS['muted']};">OEE vs OPE Gap Analysis — Strategic View</h4>
""", unsafe_allow_html=True)

# Load data
try:
    session = get_session()
    data = load_dashboard_data(session)
    df = data['daily_metrics']
    by_line = data['by_line']
    daily_trend = data['daily_trend']
    env_trend = data['env_trend']
    alerts = data['alerts']
    throughput_df = data.get('throughput_economics', pd.DataFrame())
    throughput_by_line_df = data.get('throughput_by_line', pd.DataFrame())
    sankey_df = data.get('sankey_flow', pd.DataFrame())
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please ensure the database is deployed and populated.")
    st.stop()

# =============================================================================
# SITUATION: KPI ROW - The Gap
# =============================================================================

render_section_header("Current Status", "Real-time efficiency metrics")

# Calculate current metrics from latest data
latest_date = df['METRIC_DATE'].max()
latest_data = df[df['METRIC_DATE'] == latest_date]

avg_oee = float(latest_data['OEE_PCT'].mean())
avg_ope = float(latest_data['OPE_PCT'].mean())
oee_ope_gap = avg_oee - avg_ope
total_starvation = float(latest_data['STARVATION_DOWNTIME_MIN'].sum())
total_agv_failures = int(latest_data['AGV_FAILURE_COUNT'].sum())
total_err_99 = int(latest_data['AGV_ERR_99_COUNT'].sum())

# KPI metrics row
metrics = [
    {"label": "Average OEE", "value": f"{avg_oee:.1f}%", "delta": "Equipment Efficiency"},
    {"label": "Average OPE", "value": f"{avg_ope:.1f}%", "delta": f"{avg_ope - 85:+.1f}% vs target", "delta_color": "inverse" if avg_ope < 80 else "normal"},
    {"label": "OEE-OPE Gap", "value": f"{oee_ope_gap:.1f}%", "delta": "Hidden inefficiency", "delta_color": "inverse"},
    {"label": "Starvation", "value": f"{total_starvation:.0f} min", "delta": "Material wait time", "delta_color": "inverse"},
    {"label": "AGV Failures", "value": f"{total_agv_failures}", "delta": f"{total_err_99} sensor errors", "delta_color": "inverse"},
]

render_metric_row(metrics)

# AI Insight for current state
if oee_ope_gap > 15:
    insight = f"The {oee_ope_gap:.1f}% gap between OEE and OPE indicates significant hidden inefficiencies. Material starvation accounts for {total_starvation:.0f} minutes of downtime. AGV sensor errors (ERR-99) are the primary driver—typically caused by dust accumulation on optical sensors when humidity drops below 35%."
    render_ai_insight(insight, "Gap Analysis")

st.markdown("---")

# =============================================================================
# THROUGHPUT DOLLAR DASHBOARD - Financial Linkage
# =============================================================================

render_section_header("Throughput Economics", "Financial impact of efficiency gaps")

# Calculate financial metrics from throughput data
if len(throughput_df) > 0:
    latest_throughput = throughput_df[throughput_df['METRIC_DATE'] == throughput_df['METRIC_DATE'].max()]
    total_loss_hourly = float(latest_throughput['THROUGHPUT_LOSS_PER_HOUR'].sum()) if 'THROUGHPUT_LOSS_PER_HOUR' in latest_throughput.columns else 0
    total_loss_daily = float(latest_throughput['THROUGHPUT_LOSS_DOLLARS'].sum()) if 'THROUGHPUT_LOSS_DOLLARS' in latest_throughput.columns else 0
    avg_margin_per_min = float(latest_throughput['CONTRIBUTION_MARGIN_PER_MIN'].mean()) if 'CONTRIBUTION_MARGIN_PER_MIN' in latest_throughput.columns else 0
    contribution_margin = float(latest_throughput['CONTRIBUTION_MARGIN'].iloc[0]) if 'CONTRIBUTION_MARGIN' in latest_throughput.columns else 875
else:
    # Fallback calculations based on OPE gap
    contribution_margin = 875  # $875 per unit margin
    units_per_hour = 60  # Estimated throughput
    total_loss_hourly = oee_ope_gap / 100 * units_per_hour * contribution_margin
    total_loss_daily = total_loss_hourly * 8  # 8 hour shift
    avg_margin_per_min = units_per_hour * contribution_margin / 60

# Financial metrics ticker row
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Throughput Loss Ticker - Flashing style for high values
    loss_color = COLORS['danger'] if total_loss_hourly > 20000 else COLORS['warning'] if total_loss_hourly > 10000 else COLORS['success']
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(239,68,68,0.15) 0%, {COLORS['surface']} 100%);
                border: 2px solid {loss_color}; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            Throughput Loss
        </div>
        <div style="color: {loss_color}; font-size: 2rem; font-weight: 800; font-family: 'SF Mono', monospace;">
            ${total_loss_hourly:,.0f}<span style="font-size: 1rem; font-weight: 400;">/hr</span>
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">
            ${total_loss_daily:,.0f} daily impact
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            Contribution Margin
        </div>
        <div style="color: {COLORS['snowflake']}; font-size: 1.75rem; font-weight: 700;">
            ${contribution_margin:,.0f}
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">
            per unit produced
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            Margin per Minute
        </div>
        <div style="color: {COLORS['success']}; font-size: 1.75rem; font-weight: 700;">
            ${avg_margin_per_min:,.0f}
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">
            real-time value flow
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # Calculate recovery potential
    recovery_potential = total_loss_hourly * 0.7  # 70% recoverable
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
            Recovery Potential
        </div>
        <div style="color: {COLORS['accent']}; font-size: 1.75rem; font-weight: 700;">
            ${recovery_potential:,.0f}/hr
        </div>
        <div style="color: {COLORS['muted']}; font-size: 0.75rem;">
            with dust mitigation
        </div>
    </div>
    """, unsafe_allow_html=True)

# Throughput loss by production line
if len(throughput_by_line_df) > 0:
    st.markdown("")
    st.markdown("##### Throughput Loss by Production Line")
    
    line_loss_data = convert_for_plotly(throughput_by_line_df, {
        'PRODUCTION_LINE_ID': 'str',
        'AVG_GAP_PCT': 'float',
        'TOTAL_THROUGHPUT_LOSS': 'float',
        'AVG_LOSS_PER_HOUR': 'float'
    })
    
    # Create horizontal bar chart showing loss by line
    fig = go.Figure()
    
    # Color bars by severity
    bar_colors = [COLORS['danger'] if v > 50000 else COLORS['warning'] if v > 20000 else COLORS['success'] 
                  for v in line_loss_data['TOTAL_THROUGHPUT_LOSS']]
    
    fig.add_trace(go.Bar(
        x=line_loss_data['TOTAL_THROUGHPUT_LOSS'],
        y=line_loss_data['PRODUCTION_LINE_ID'],
        orientation='h',
        marker_color=bar_colors,
        text=[f"${v:,.0f}" for v in line_loss_data['TOTAL_THROUGHPUT_LOSS']],
        textposition='outside',
        textfont=dict(color=COLORS['text'], size=11)
    ))
    
    fig.update_layout(
        **PLOTLY_THEME,
        height=200,
        margin=dict(l=80, r=80, t=20, b=40),
        xaxis_title='Total Throughput Loss ($)',
        xaxis=dict(tickformat='$,.0f', color=COLORS['muted']),
        yaxis=dict(color=COLORS['text'])
    )
    
    st.plotly_chart(fig, use_container_width=True, key="throughput_by_line")
    
    # Find highest-loss line for insight (from dictionary format)
    max_idx = line_loss_data['TOTAL_THROUGHPUT_LOSS'].index(max(line_loss_data['TOTAL_THROUGHPUT_LOSS']))
    max_line_id = line_loss_data['PRODUCTION_LINE_ID'][max_idx]
    max_line_loss = line_loss_data['TOTAL_THROUGHPUT_LOSS'][max_idx]
    max_line_gap = line_loss_data['AVG_GAP_PCT'][max_idx]
    
    render_ai_insight(
        f"Line {max_line_id} accounts for ${max_line_loss:,.0f} in throughput losses "
        f"({max_line_gap:.1f}% efficiency gap). This line should be prioritized for the Dust Mitigation Cycle "
        f"as it handles the highest-margin SKU.",
        "Financial Impact Analysis"
    )

st.markdown("---")

# =============================================================================
# TASK: OEE vs OPE Comparison Charts
# =============================================================================

render_section_header("Efficiency Comparison", "OEE vs OPE by production line")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"##### By Production Line")
    
    # Convert to native Python types for SiS compatibility
    line_data = convert_for_plotly(by_line, {
        'PRODUCTION_LINE_ID': 'str',
        'AVG_OEE': 'float',
        'AVG_OPE': 'float',
        'EFFICIENCY_GAP': 'float'
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='OEE',
        x=line_data['PRODUCTION_LINE_ID'],
        y=line_data['AVG_OEE'],
        marker_color=COLORS['snowflake'],
        text=[f"{v:.1f}%" for v in line_data['AVG_OEE']],
        textposition='outside',
        textfont=dict(color=COLORS['text'], size=10)
    ))
    fig.add_trace(go.Bar(
        name='OPE',
        x=line_data['PRODUCTION_LINE_ID'],
        y=line_data['AVG_OPE'],
        marker_color=COLORS['success'],
        text=[f"{v:.1f}%" for v in line_data['AVG_OPE']],
        textposition='outside',
        textfont=dict(color=COLORS['text'], size=10)
    ))
    
    fig.update_layout(
        barmode='group',
        **PLOTLY_THEME,
        height=350,
        margin=dict(l=40, r=40, t=40, b=60),
        legend=dict(orientation='h', y=1.12, x=0.5, xanchor='center'),
        xaxis_title='Production Line',
        yaxis_title='Efficiency (%)',
        yaxis=dict(range=[0, 110])
    )
    
    st.plotly_chart(fig, use_container_width=True, key="bar_by_line")

with col2:
    st.markdown(f"##### Trend Over Time")
    
    # Convert and sort trend data
    trend_data = convert_for_plotly(daily_trend.sort_values('METRIC_DATE'), {
        'METRIC_DATE': 'str',
        'AVG_OEE': 'float',
        'AVG_OPE': 'float'
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_data['METRIC_DATE'],
        y=trend_data['AVG_OEE'],
        name='OEE',
        line=dict(color=COLORS['snowflake'], width=2),
        mode='lines+markers'
    ))
    fig.add_trace(go.Scatter(
        x=trend_data['METRIC_DATE'],
        y=trend_data['AVG_OPE'],
        name='OPE',
        line=dict(color=COLORS['success'], width=2),
        mode='lines+markers'
    ))
    
    # Add crisis period shading if applicable
    fig.add_vrect(
        x0='2024-12-09', x1='2024-12-11',
        fillcolor='rgba(239, 68, 68, 0.2)',
        layer='below',
        line_width=0,
        annotation_text='Crisis',
        annotation_position='top left',
        annotation_font_color=COLORS['danger']
    )
    
    fig.update_layout(
        **PLOTLY_THEME,
        height=350,
        margin=dict(l=40, r=40, t=40, b=60),
        legend=dict(orientation='h', y=1.12, x=0.5, xanchor='center'),
        xaxis_title='Date',
        yaxis_title='Efficiency (%)'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="trend_over_time")

st.markdown("---")

# =============================================================================
# VALUE STREAM SANKEY - Process Mining Visualization
# =============================================================================

render_section_header("Value Stream Flow", "Real-time material flow analysis")

if len(sankey_df) > 0:
    # Build Sankey diagram from flow data
    
    # Define node labels and their display order
    node_labels = ['RAW_MATERIALS', 'LINE_1', 'LINE_2', 'LINE_3', 'LINE_4', 'LINE_5',
                   'AGV_TRANSFER', 'QC_INSPECTION', 'FINISHED_GOODS', 'REWORK_QUEUE']
    node_label_display = ['Raw Materials', 'Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5',
                          'AGV Transfer', 'QC Inspection', 'Finished Goods', 'Rework Queue']
    
    # Create node index mapping
    node_map = {label: idx for idx, label in enumerate(node_labels)}
    
    # Prepare link data
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
            
            # Color by flow status
            if status == 'CRITICAL':
                link_colors.append('rgba(239, 68, 68, 0.6)')  # Red
            elif status == 'WARNING':
                link_colors.append('rgba(245, 158, 11, 0.6)')  # Orange
            else:
                link_colors.append('rgba(34, 197, 94, 0.4)')  # Green
    
    # Node colors based on health
    node_colors = []
    for label in node_labels:
        if label == 'AGV_TRANSFER':
            # AGV transfer is bottleneck
            node_colors.append(COLORS['danger'])
        elif label == 'REWORK_QUEUE':
            node_colors.append(COLORS['warning'])
        elif label in ['LINE_4']:  # Crisis line
            node_colors.append(COLORS['warning'])
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
        title=dict(
            text='Material Flow: Raw → Production → QC → Finished Goods',
            font=dict(color=COLORS['text'], size=14)
        ),
        **PLOTLY_THEME,
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="sankey_flow")
    
    # Flow analysis insight
    agv_blocked = any(sankey_df['FLOW_STATUS'] == 'CRITICAL')
    rework_volume = sankey_df[sankey_df['TARGET_NODE'] == 'REWORK_QUEUE']['FLOW_VALUE'].sum() if len(sankey_df[sankey_df['TARGET_NODE'] == 'REWORK_QUEUE']) > 0 else 0
    
    if agv_blocked:
        render_ai_insight(
            f"The Sankey diagram reveals a bottleneck at the AGV Transfer point (red flow). "
            f"Material is backing up due to sensor errors caused by dust accumulation. "
            f"Additionally, {rework_volume:.0f} units are in the Rework Queue (Ghost Inventory). "
            f"Recommended: Execute Dust Mitigation Cycle to restore flow.",
            "Process Mining Analysis"
        )
else:
    # Fallback static Sankey when data not available
    st.info("Value Stream data loading... The Sankey diagram visualizes material flow through production stages.")

st.markdown("---")

# =============================================================================
# ACTION: Environmental Correlation
# =============================================================================

render_section_header("Root Cause Analysis", "Environmental correlation with failures")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Humidity → AGV Sensor Errors")
    
    env_data = convert_for_plotly(env_trend.sort_values('METRIC_DATE'), {
        'METRIC_DATE': 'str',
        'AVG_HUMIDITY': 'float',
        'TOTAL_ERR_99': 'int'
    })
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=env_data['METRIC_DATE'],
            y=env_data['AVG_HUMIDITY'],
            name='Humidity (%)',
            line=dict(color='#64D2FF', width=2)
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(
            x=env_data['METRIC_DATE'],
            y=env_data['TOTAL_ERR_99'],
            name='AGV-ERR-99 Count',
            marker_color='rgba(239, 68, 68, 0.7)'
        ),
        secondary_y=True
    )
    
    # Add threshold line
    fig.add_hline(y=35, line_dash='dash', line_color=COLORS['warning'],
                  annotation_text='Low humidity threshold (35%)',
                  annotation_font_color=COLORS['warning'])
    
    fig.update_layout(
        **PLOTLY_THEME,
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center')
    )
    fig.update_yaxes(title_text='Humidity (%)', secondary_y=False, color=COLORS['muted'])
    fig.update_yaxes(title_text='Error Count', secondary_y=True, color=COLORS['muted'])
    
    st.plotly_chart(fig, use_container_width=True, key="humidity_correlation")

with col2:
    st.markdown("##### Dust Levels → Production Starvation")
    
    starvation_data = convert_for_plotly(env_trend.sort_values('METRIC_DATE'), {
        'METRIC_DATE': 'str',
        'AVG_DUST': 'float'
    })
    
    # Get starvation from daily trend
    starvation_trend = convert_for_plotly(daily_trend.sort_values('METRIC_DATE'), {
        'METRIC_DATE': 'str',
        'TOTAL_STARVATION': 'float'
    })
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=starvation_data['METRIC_DATE'],
            y=starvation_data['AVG_DUST'],
            name='Dust PM2.5 (µg/m³)',
            line=dict(color='#FF9F0A', width=2)
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(
            x=starvation_trend['METRIC_DATE'],
            y=starvation_trend['TOTAL_STARVATION'],
            name='Starvation (min)',
            marker_color='rgba(245, 158, 11, 0.7)'
        ),
        secondary_y=True
    )
    
    # Add threshold line
    fig.add_hline(y=25, line_dash='dash', line_color=COLORS['danger'],
                  annotation_text='High dust threshold (25 µg/m³)',
                  annotation_font_color=COLORS['danger'])
    
    fig.update_layout(
        **PLOTLY_THEME,
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center')
    )
    fig.update_yaxes(title_text='Dust (µg/m³)', secondary_y=False, color=COLORS['muted'])
    fig.update_yaxes(title_text='Starvation (min)', secondary_y=True, color=COLORS['muted'])
    
    st.plotly_chart(fig, use_container_width=True, key="dust_starvation")

st.markdown("---")

# =============================================================================
# SENSITIVITY ANALYSIS SIMULATOR - What-If Scenarios
# =============================================================================

render_section_header("Scenario Planner", "What-if analysis for operational decisions")

st.markdown(f"""
<div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-bottom: 1rem;">
    Adjust the sliders to simulate different operational strategies and see their impact on OPE and Working Capital.
</div>
""", unsafe_allow_html=True)

# Current baseline values (from data)
baseline_ope = avg_ope if 'avg_ope' in dir() else 75
baseline_starvation = total_starvation if 'total_starvation' in dir() else 120
contribution_margin_baseline = 875  # $ per unit

# Scenario inputs with sliders
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Operational Levers")
    
    # Slider 1: Buffer Stock Increase
    buffer_increase = st.slider(
        "Increase Buffer Stock (%)",
        min_value=0,
        max_value=50,
        value=0,
        step=5,
        help="Increasing buffer stock reduces starvation risk but ties up working capital",
        key="buffer_slider"
    )
    
    # Slider 2: Maintenance Frequency
    maintenance_increase = st.slider(
        "Increase Preventive Maintenance (%)",
        min_value=0,
        max_value=100,
        value=0,
        step=10,
        help="More frequent maintenance reduces failures but costs OPE during maintenance windows",
        key="maintenance_slider"
    )
    
    # Slider 3: HVAC Humidity Target
    humidity_target = st.slider(
        "HVAC Humidity Target (%)",
        min_value=30,
        max_value=60,
        value=40,
        step=5,
        help="Higher humidity reduces dust-related sensor errors but increases energy costs",
        key="humidity_slider"
    )

with col2:
    st.markdown("##### Projected Impact")
    
    # Calculate scenario outcomes
    # Buffer impact: Each 10% buffer increase reduces starvation by 15% but costs $500K in working capital
    starvation_reduction = min(0.9, buffer_increase * 0.015)  # Max 90% reduction
    working_capital_impact = buffer_increase * 50000  # $50K per 1% buffer
    
    # Maintenance impact: Each 10% maintenance increase reduces failures by 8% but costs 2% OPE
    failure_reduction = min(0.8, maintenance_increase * 0.008)  # Max 80% reduction
    maintenance_ope_cost = maintenance_increase * 0.02  # 0.02% OPE per 1% maintenance
    
    # Humidity impact: Optimal at 45%, reduces errors significantly
    if humidity_target >= 40:
        humidity_benefit = min(0.7, (humidity_target - 35) * 0.07)  # Error reduction
    else:
        humidity_benefit = 0
    energy_cost_increase = max(0, (humidity_target - 40) * 1000)  # $1K per % above 40
    
    # Combined OPE projection
    base_ope_gain = (starvation_reduction * 8) + (failure_reduction * 5) + (humidity_benefit * 4)  # Points of OPE
    ope_cost = maintenance_ope_cost * 100  # Convert to points
    projected_ope = min(95, baseline_ope + base_ope_gain - ope_cost)
    ope_delta = projected_ope - baseline_ope
    
    # Financial projections
    throughput_gain_hourly = ope_delta / 100 * 60 * contribution_margin_baseline  # Hourly gain
    net_benefit_daily = (throughput_gain_hourly * 8) - (energy_cost_increase / 30)  # Daily after energy costs
    
    # Display projected metrics
    col2a, col2b = st.columns(2)
    
    with col2a:
        ope_color = COLORS['success'] if ope_delta > 0 else COLORS['danger'] if ope_delta < 0 else COLORS['muted']
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center; margin-bottom: 0.5rem;">
            <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Projected OPE</div>
            <div style="color: {COLORS['text']}; font-size: 1.75rem; font-weight: 700;">{projected_ope:.1f}%</div>
            <div style="color: {ope_color}; font-size: 0.875rem;">{ope_delta:+.1f}% vs current</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2b:
        benefit_color = COLORS['success'] if net_benefit_daily > 0 else COLORS['danger']
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; text-align: center; margin-bottom: 0.5rem;">
            <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Net Benefit</div>
            <div style="color: {benefit_color}; font-size: 1.75rem; font-weight: 700;">${net_benefit_daily:,.0f}</div>
            <div style="color: {COLORS['muted']}; font-size: 0.875rem;">per day</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Working capital impact
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: {COLORS['muted']};">Working Capital Required:</span>
            <span style="color: {COLORS['warning']}; font-weight: 600;">${working_capital_impact:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: {COLORS['muted']};">Energy Cost Increase:</span>
            <span style="color: {COLORS['warning']}; font-weight: 600;">${energy_cost_increase:,.0f}/mo</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: {COLORS['muted']};">Starvation Reduction:</span>
            <span style="color: {COLORS['success']}; font-weight: 600;">{starvation_reduction*100:.0f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Efficient Frontier Chart
st.markdown("")
st.markdown("##### Efficient Frontier: OPE Gain vs. Capital Cost")

# Generate frontier data points
frontier_data = []
for buffer in range(0, 55, 5):
    for maint in range(0, 110, 10):
        starv_red = min(0.9, buffer * 0.015)
        fail_red = min(0.8, maint * 0.008)
        maint_cost = maint * 0.02
        ope_gain = (starv_red * 8) + (fail_red * 5) - (maint_cost * 100)
        capital = buffer * 50000 + maint * 2000  # Maintenance also has capital cost
        frontier_data.append({
            'ope_gain': ope_gain,
            'capital': capital,
            'buffer': buffer,
            'maintenance': maint
        })

frontier_df = pd.DataFrame(frontier_data)

# Find Pareto frontier points
pareto_points = []
for _, row in frontier_df.iterrows():
    is_dominated = False
    for _, other in frontier_df.iterrows():
        if other['ope_gain'] > row['ope_gain'] and other['capital'] <= row['capital']:
            is_dominated = True
            break
        if other['ope_gain'] >= row['ope_gain'] and other['capital'] < row['capital']:
            is_dominated = True
            break
    if not is_dominated:
        pareto_points.append(row)

pareto_df = pd.DataFrame(pareto_points).sort_values('capital')

fig = go.Figure()

# All scenarios as scatter
fig.add_trace(go.Scatter(
    x=[float(x) for x in frontier_df['capital'].tolist()],
    y=[float(y) for y in frontier_df['ope_gain'].tolist()],
    mode='markers',
    marker=dict(size=6, color=COLORS['muted'], opacity=0.3),
    name='All Scenarios',
    hovertemplate='Capital: $%{x:,.0f}<br>OPE Gain: %{y:.1f}%<extra></extra>'
))

# Efficient frontier line
if len(pareto_df) > 0:
    fig.add_trace(go.Scatter(
        x=[float(x) for x in pareto_df['capital'].tolist()],
        y=[float(y) for y in pareto_df['ope_gain'].tolist()],
        mode='lines+markers',
        line=dict(color=COLORS['accent'], width=3),
        marker=dict(size=10, color=COLORS['accent']),
        name='Efficient Frontier',
        hovertemplate='Capital: $%{x:,.0f}<br>OPE Gain: %{y:.1f}%<extra></extra>'
    ))

# Current scenario point
current_capital = working_capital_impact + maintenance_increase * 2000
fig.add_trace(go.Scatter(
    x=[float(current_capital)],
    y=[float(ope_delta)],
    mode='markers',
    marker=dict(size=15, color=COLORS['snowflake'], symbol='star'),
    name='Current Selection',
    hovertemplate='Your Selection<br>Capital: $%{x:,.0f}<br>OPE Gain: %{y:.1f}%<extra></extra>'
))

fig.update_layout(
    **PLOTLY_THEME,
    height=300,
    margin=dict(l=40, r=40, t=20, b=60),
    xaxis_title='Working Capital Investment ($)',
    yaxis_title='OPE Gain (%)',
    xaxis=dict(tickformat='$,.0f', color=COLORS['muted']),
    yaxis=dict(color=COLORS['muted']),
    legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center')
)

st.plotly_chart(fig, use_container_width=True, key="efficient_frontier")

# Decision insight
if ope_delta > 0 and net_benefit_daily > 0:
    render_ai_insight(
        f"Your selected scenario projects a {ope_delta:.1f}% OPE improvement with ${net_benefit_daily:,.0f}/day net benefit. "
        f"This requires ${working_capital_impact:,.0f} in buffer stock investment. "
        f"The scenario is {'on' if current_capital <= pareto_df['capital'].max() else 'near'} the efficient frontier, "
        f"representing an optimal trade-off between investment and return.",
        "Scenario Analysis"
    )
elif ope_delta > 0:
    render_ai_insight(
        f"The scenario improves OPE by {ope_delta:.1f}% but energy costs offset the throughput gains. "
        f"Consider reducing the humidity target to optimize net benefit.",
        "Scenario Analysis"
    )

st.markdown("---")

# =============================================================================
# RESULT: Active Alerts
# =============================================================================

render_section_header("Actionable Alerts", "Predictive maintenance recommendations")

if len(alerts) > 0:
    for _, alert in alerts.head(3).iterrows():
        prob = float(alert['FAILURE_PROBABILITY'])
        category = str(alert['FAILURE_PROBABILITY_CATEGORY'])
        
        render_alert_card(
            title=f"Zone {alert['TARGET_ZONE_ID']}",
            subtitle=f"Target: {alert['TARGET_DATE']} Hour {alert['TARGET_HOUR']}",
            risk_level=category,
            details={
                "Failure Probability": f"{prob*100:.1f}%",
                "Risk Factor": str(alert['PRIMARY_RISK_FACTOR']),
                "Forecast Humidity": f"{float(alert['FORECAST_HUMIDITY']):.1f}%"
            },
            recommendation=str(alert['RECOMMENDED_ACTION'])
        )
else:
    st.success("No critical alerts at this time")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {COLORS['muted']}; font-size: 0.875rem;">
    Last updated: {latest_date}
</div>
""", unsafe_allow_html=True)

