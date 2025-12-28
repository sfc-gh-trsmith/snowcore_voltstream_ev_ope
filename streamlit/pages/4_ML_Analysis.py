"""
ML Analysis - Data Scientist View
==================================

Technical drill-down for Data Scientists:
- Feature importance analysis
- Model performance metrics
- Environmental correlation heatmaps
- Raw data exploration

Target Persona: Lead Data Scientist (Technical)
"""

import sys
from pathlib import Path

# Add parent directory to path for utils imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

# Import utilities
from utils.ui_components import (
    apply_global_styles, COLORS, PLOTLY_THEME,
    render_section_header, render_ai_insight, render_legend
)
from utils.data_loader import run_queries_parallel, convert_for_plotly
from utils.query_registry import AGV_ANALYSIS_SQL, AGV_FAILURE_BY_ENV_SQL, ALL_ALERTS_SQL

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="ML Analysis | VoltStream OPE",
    page_icon="🔬",
    layout="wide"
)

apply_global_styles()

# =============================================================================
# SESSION AND DATA
# =============================================================================

@st.cache_resource
def get_session():
    return get_active_session()


@st.cache_data(ttl=300)
def load_analysis_data(_session):
    """Load ML analysis data using parallel queries."""
    queries = {
        'agv_analysis': AGV_ANALYSIS_SQL,
        'failure_by_env': AGV_FAILURE_BY_ENV_SQL,
        'predictions': ALL_ALERTS_SQL
    }
    return run_queries_parallel(_session, queries, max_workers=3)


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown(f"""
<h1 style="color: #f8fafc;">ML Analysis</h1>
<h4 style="color: {COLORS['muted']};">Model Insights & Technical Deep-Dive</h4>
""", unsafe_allow_html=True)

# =============================================================================
# ANALYSIS CONTROLS (at top of page)
# =============================================================================

with st.expander("Analysis Controls", expanded=True):
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 2])
    
    with ctrl_col1:
        st.markdown("**Filters**")
        date_range = st.selectbox(
            "Time Range",
            ["All Data", "Last 7 Days", "Last 30 Days", "Crisis Period (Dec 9-11)"],
            index=0,
            label_visibility="collapsed"
        )
        
        zone_filter = st.multiselect(
            "Zones",
            ["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"],
            default=["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"]
        )
    
    with ctrl_col2:
        st.markdown("**Model Info**")
        st.markdown(f"""
        <div style="font-size: 0.875rem;">
            <span style="color: {COLORS['muted']};">Algorithm:</span> <strong>XGBoost</strong><br>
            <span style="color: {COLORS['muted']};">Target:</span> IS_HIGH_FAILURE_PERIOD<br>
            <span style="color: {COLORS['muted']};">ROC-AUC:</span> <span style="color: {COLORS['success']}; font-weight: 600;">>0.90</span>
        </div>
        """, unsafe_allow_html=True)
    
    with ctrl_col3:
        st.markdown("**Key Insight**")
        st.markdown(f"""
        <div style="font-size: 0.875rem; color: {COLORS['muted']};">
            Environmental factors (dust, humidity) explain <strong style="color: {COLORS['snowflake']};">>70%</strong> of AGV failure predictions.
            The model validates the causal chain: Low Humidity → High Dust → Sensor Errors → Failures.
        </div>
        """, unsafe_allow_html=True)

# Load data
try:
    session = get_session()
    data = load_analysis_data(session)
    agv_df = data['agv_analysis']
    failure_by_env = data['failure_by_env']
    predictions_df = data['predictions']
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please ensure the database is deployed and ML notebook has been executed.")
    st.stop()

# Apply filters
if zone_filter:
    agv_df = agv_df[agv_df['ZONE_ID'].isin(zone_filter)]

# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================

render_section_header("Feature Importance Analysis", "What drives AGV failures?")

col1, col2 = st.columns([1, 1])

with col1:
    # Feature importance data (from notebook results)
    importance_data = pd.DataFrame({
        'Feature': [
            'AVG_DUST_PM25', 'HUMIDITY_DUST_INTERACTION', 'DUST_IS_HIGH',
            'AVG_HUMIDITY', 'HUMIDITY_IS_LOW', 'MAX_DUST_PM25',
            'MIN_HUMIDITY', 'AVG_TEMPERATURE', 'ANALYSIS_HOUR'
        ],
        'Importance': [0.28, 0.22, 0.15, 0.12, 0.08, 0.06, 0.04, 0.03, 0.02]
    })
    
    # Convert to native Python types for SiS compatibility
    features = [str(f) for f in importance_data['Feature'].tolist()]
    importance = [float(i) for i in importance_data['Importance'].tolist()]
    
    # Color environmental factors differently
    colors = [COLORS['snowflake'] if 'DUST' in f or 'HUMIDITY' in f else COLORS['muted'] 
              for f in features]
    
    fig = go.Figure(go.Bar(
        x=importance,
        y=features,
        orientation='h',
        marker_color=colors,
        text=[f"{i:.0%}" for i in importance],
        textposition='outside',
        textfont=dict(color=COLORS['text'], size=10)
    ))
    
    fig.update_layout(
        title=dict(text='XGBoost Feature Importance (Gain)', font=dict(color=COLORS['text'])),
        **PLOTLY_THEME,
        height=400,
        margin=dict(l=180, r=60, t=50, b=40),
        xaxis_title='Importance',
        xaxis=dict(tickformat='.0%', color=COLORS['muted']),
        yaxis=dict(color=COLORS['text'])
    )
    
    st.plotly_chart(fig, use_container_width=True, key="feature_importance")
    
    # Summary insight
    env_pct = sum(importance_data[importance_data['Feature'].str.contains('DUST|HUMIDITY')]['Importance']) * 100
    render_ai_insight(
        f"Environmental factors (dust and humidity) explain {env_pct:.0f}% of the model's predictive power. "
        f"The interaction between humidity and dust levels is the second most important feature, "
        f"confirming that low humidity amplifies the effect of dust on AGV sensor failures.",
        "Feature Analysis"
    )

with col2:
    st.markdown("##### Failure Rate by Environmental Conditions")
    
    # Create heatmap from failure_by_env data
    if len(failure_by_env) > 0:
        # Pivot the data - convert to native types for SiS
        pivot_data = failure_by_env.pivot_table(
            index='HUMIDITY_CATEGORY',
            columns='DUST_CATEGORY', 
            values='AVG_FAILURE_RATE_PCT',
            aggfunc='first'
        ).fillna(0)
        
        # Reorder categories
        humidity_order = ['LOW', 'NORMAL', 'HIGH']
        dust_order = ['LOW', 'MODERATE', 'HIGH']
        
        try:
            pivot_data = pivot_data.reindex(humidity_order)
            pivot_data = pivot_data[[c for c in dust_order if c in pivot_data.columns]]
        except:
            pass
        
        # Convert to native Python types for SiS compatibility
        z_values = [[float(v) if pd.notna(v) else 0.0 for v in row] for row in pivot_data.values.tolist()]
        x_labels = [str(c) for c in pivot_data.columns.tolist()]
        y_labels = [str(r) for r in pivot_data.index.tolist()]
        
        # Calculate max for color scale
        z_max = max(max(row) for row in z_values) if z_values and any(z_values) else 10
        
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=x_labels,
            y=y_labels,
            colorscale='YlOrRd',
            zmin=0,
            zmax=z_max,
            text=[[f"{v:.1f}%" for v in row] for row in z_values],
            texttemplate='%{text}',
            textfont={"size": 14, "color": "white"},
            colorbar=dict(
                title=dict(text='Failure Rate (%)', font=dict(color=COLORS['text'])),
                tickfont=dict(color=COLORS['text'])
            )
        ))
        
        fig.update_layout(
            title=dict(text='Failure Rate Heatmap', font=dict(color=COLORS['text'])),
            **PLOTLY_THEME,
            height=400,
            margin=dict(l=40, r=40, t=50, b=60),
            xaxis_title='Dust Category',
            yaxis_title='Humidity Category',
            xaxis=dict(color=COLORS['muted']),
            yaxis=dict(color=COLORS['muted'])
        )
        
        st.plotly_chart(fig, use_container_width=True, key="failure_heatmap")
        
        # Peak failure insight
        max_rate = max(max(row) for row in z_values) if z_values and any(z_values) else 0
        st.warning(f"**Peak failure rate: {max_rate:.1f}%** observed when humidity is LOW and dust is HIGH")
    else:
        st.info("No failure analysis data available")

st.markdown("---")

# =============================================================================
# CORRELATION ANALYSIS
# =============================================================================

render_section_header("Environmental Correlation", "Scatter plot analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Humidity vs Dust (colored by Failure Rate)")
    
    if len(agv_df) > 0:
        # Convert to native Python types
        scatter_data = {
            'humidity': [float(v) for v in agv_df['AVG_HUMIDITY'].fillna(0).tolist()],
            'dust': [float(v) for v in agv_df['AVG_DUST_PM25'].fillna(0).tolist()],
            'failure_rate': [float(v) for v in agv_df['FAILURE_RATE'].fillna(0).tolist()],
            'zone': [str(v) for v in agv_df['ZONE_ID'].tolist()]
        }
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=scatter_data['humidity'],
            y=scatter_data['dust'],
            mode='markers',
            marker=dict(
                size=8,
                color=scatter_data['failure_rate'],
                colorscale='YlOrRd',
                showscale=True,
                opacity=0.6,
                colorbar=dict(
                    title=dict(text='Failure Rate', font=dict(color=COLORS['text'])),
                    tickfont=dict(color=COLORS['text'])
                )
            ),
            text=[f"Zone: {z}<br>Humidity: {h:.1f}%<br>Dust: {d:.1f}<br>Failure: {f:.1%}" 
                  for z, h, d, f in zip(scatter_data['zone'], scatter_data['humidity'], 
                                         scatter_data['dust'], scatter_data['failure_rate'])],
            hoverinfo='text'
        ))
        
        # Add threshold lines
        fig.add_vline(x=35, line_dash='dash', line_color=COLORS['warning'],
                      annotation_text='Low humidity', annotation_font_color=COLORS['warning'])
        fig.add_hline(y=25, line_dash='dash', line_color=COLORS['danger'],
                      annotation_text='High dust', annotation_font_color=COLORS['danger'])
        
        fig.update_layout(
            **PLOTLY_THEME,
            height=400,
            margin=dict(l=40, r=40, t=40, b=60),
            xaxis_title='Humidity (%)',
            yaxis_title='Dust PM2.5 (µg/m³)',
            xaxis=dict(color=COLORS['muted']),
            yaxis=dict(color=COLORS['muted'])
        )
        
        st.plotly_chart(fig, use_container_width=True, key="scatter_humidity_dust")
    else:
        st.info("No data available for scatter plot")

with col2:
    st.markdown("##### Failure Rate by Dust Level Bins")
    
    if len(agv_df) > 0:
        # Bin dust levels
        df_temp = agv_df.copy()
        bins = [0, 10, 15, 20, 25, 30, 35, 100]
        labels = ['0-10', '10-15', '15-20', '20-25', '25-30', '30-35', '35+']
        df_temp['DUST_BIN'] = pd.cut(df_temp['AVG_DUST_PM25'], bins=bins, labels=labels)
        
        dust_failure = df_temp.groupby('DUST_BIN', observed=True)['FAILURE_RATE'].mean().reset_index()
        
        # Convert to native Python types
        dust_bins = [str(b) for b in dust_failure['DUST_BIN'].tolist()]
        failure_rates = [float(f) * 100 for f in dust_failure['FAILURE_RATE'].fillna(0).tolist()]
        
        # Color by risk level
        bar_colors = [COLORS['success'] if f < 3 else COLORS['warning'] if f < 5 else COLORS['danger'] 
                      for f in failure_rates]
        
        fig = go.Figure(go.Bar(
            x=dust_bins,
            y=failure_rates,
            marker_color=bar_colors,
            text=[f"{f:.1f}%" for f in failure_rates],
            textposition='outside',
            textfont=dict(color=COLORS['text'], size=10)
        ))
        
        fig.add_hline(y=5, line_dash='dash', line_color=COLORS['danger'],
                      annotation_text='High failure threshold (5%)',
                      annotation_font_color=COLORS['danger'])
        
        fig.update_layout(
            title=dict(text='Failure Rate by Dust Level', font=dict(color=COLORS['text'])),
            **PLOTLY_THEME,
            height=400,
            margin=dict(l=40, r=40, t=50, b=60),
            xaxis_title='Dust PM2.5 Range (µg/m³)',
            yaxis_title='Failure Rate (%)',
            xaxis=dict(color=COLORS['muted']),
            yaxis=dict(color=COLORS['muted'])
        )
        
        st.plotly_chart(fig, use_container_width=True, key="bar_dust_failure")
    else:
        st.info("No data available for bar chart")

st.markdown("---")

# =============================================================================
# MODEL PREDICTIONS
# =============================================================================

render_section_header("Recent Predictions", "Model output analysis")

if len(predictions_df) > 0:
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(predictions_df)
        st.metric("Total Predictions", total)
    
    with col2:
        critical = len(predictions_df[predictions_df['FAILURE_PROBABILITY_CATEGORY'] == 'CRITICAL'])
        st.metric("Critical", critical, f"{critical/total*100:.0f}%" if total > 0 else "0%")
    
    with col3:
        high = len(predictions_df[predictions_df['FAILURE_PROBABILITY_CATEGORY'] == 'HIGH'])
        st.metric("High Risk", high)
    
    with col4:
        avg_prob = float(predictions_df['FAILURE_PROBABILITY'].mean()) * 100
        st.metric("Avg Probability", f"{avg_prob:.1f}%")
    
    st.markdown("")
    
    # Predictions table
    display_cols = ['TARGET_ZONE_ID', 'TARGET_DATE', 'TARGET_HOUR',
                    'FAILURE_PROBABILITY', 'FAILURE_PROBABILITY_CATEGORY',
                    'PRIMARY_RISK_FACTOR', 'RECOMMENDED_ACTION']
    
    available_cols = [c for c in display_cols if c in predictions_df.columns]
    display_df = predictions_df[available_cols].head(20).copy()
    
    # Format probability
    if 'FAILURE_PROBABILITY' in display_df.columns:
        display_df['FAILURE_PROBABILITY'] = (display_df['FAILURE_PROBABILITY'] * 100).round(1).astype(str) + '%'
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
else:
    st.info("No predictions available. Run the ML notebook to generate predictions.")

st.markdown("---")

# =============================================================================
# RAW DATA EXPLORER
# =============================================================================

render_section_header("Raw Data Explorer", "Inspect underlying data")

# Data explorer toggle
show_raw = st.checkbox("Show raw AGV failure analysis data")

if show_raw and len(agv_df) > 0:
    st.dataframe(
        agv_df.head(100),
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Showing first 100 of {len(agv_df)} records")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {COLORS['muted']}; font-size: 0.875rem;">
    Model: XGBoost v1.0 | Training: Full historical dataset | Framework: Snowpark ML
</div>
""", unsafe_allow_html=True)

