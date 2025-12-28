"""
Operations Control - Plant Manager View
========================================

Actionable operations dashboard for Plant Managers:
- Pending maintenance alerts with approve/dismiss workflow
- AGV fleet status table
- SOP lookup via Cortex Search
- "Top 10 items to review today" pattern

Target Persona: Plant Manager (Operational)
"""

import sys
from pathlib import Path

# Add parent directory to path for utils imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# Import utilities
from utils.ui_components import (
    apply_global_styles, COLORS, PLOTLY_THEME,
    render_alert_card, render_ai_insight, render_section_header,
    render_scrollable_list, get_risk_color
)
from utils.data_loader import run_queries_parallel, run_single_query
from utils.query_registry import (
    PENDING_ALERTS_SQL, ALL_ALERTS_SQL, QUICK_STATS_SQL, AGV_FLEET_STATUS_SQL,
    LITTLES_LAW_METRICS_SQL
)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Operations Control | VoltStream OPE",
    page_icon="🎛️",
    layout="wide"
)

apply_global_styles()

# =============================================================================
# SESSION AND DATA
# =============================================================================

@st.cache_resource
def get_session():
    return get_active_session()


@st.cache_data(ttl=60)  # Shorter TTL for operational data
def load_operations_data(_session):
    """Load operations data using parallel queries."""
    queries = {
        'pending_alerts': PENDING_ALERTS_SQL,
        'all_alerts': ALL_ALERTS_SQL,
        'quick_stats': QUICK_STATS_SQL,
        'agv_fleet': AGV_FLEET_STATUS_SQL,
        'littles_law': LITTLES_LAW_METRICS_SQL
    }
    return run_queries_parallel(_session, queries, max_workers=5)


def update_alert_status(_session, alert_id: str, new_status: str):
    """Update alert status in database."""
    try:
        _session.sql(f"""
            UPDATE EV_OPE.PREDICTIVE_MAINTENANCE_ALERTS
            SET ACTION_STATUS = '{new_status}',
                ACTION_TAKEN_TIMESTAMP = CURRENT_TIMESTAMP()
            WHERE ALERT_ID = '{alert_id}'
        """).collect()
        return True
    except Exception as e:
        st.error(f"Error updating alert: {e}")
        return False


# =============================================================================
# SIDEBAR - QUICK ACTIONS
# =============================================================================

with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 0.5rem;">
        <div style="color: {COLORS['snowflake']}; font-size: 1.25rem; font-weight: 700;">Control Panel</div>
        <div style="color: {COLORS['text']}; font-weight: 700;">Quick Actions</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Current shift indicator
    from datetime import datetime
    current_hour = datetime.now().hour
    if 6 <= current_hour < 14:
        shift = "Day Shift (06:00-14:00)"
    elif 14 <= current_hour < 22:
        shift = "Swing Shift (14:00-22:00)"
    else:
        shift = "Night Shift (22:00-06:00)"
    
    st.markdown(f"""
    <div style="background: {COLORS['surface']}; padding: 0.75rem; border-radius: 8px;">
        <div style="color: {COLORS['muted']}; font-size: 0.75rem; text-transform: uppercase;">Current Shift</div>
        <div style="color: {COLORS['text']}; font-weight: 600;">{shift}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div style='color: {COLORS['muted']}; font-size: 0.75rem; margin-top: 1rem; text-align: center;'>Auto-refresh: 60s</div>", unsafe_allow_html=True)


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown(f"""
<h1 style="color: #f8fafc;">Operations Control</h1>
<h4 style="color: {COLORS['muted']};">Plant Manager Action Center</h4>
""", unsafe_allow_html=True)

# Load data
try:
    session = get_session()
    data = load_operations_data(session)
    pending_alerts = data['pending_alerts']
    all_alerts = data['all_alerts']
    quick_stats = data['quick_stats'].iloc[0] if not data['quick_stats'].empty else None
    agv_fleet_df = data['agv_fleet']
    littles_law_df = data.get('littles_law', pd.DataFrame())
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please ensure the database is deployed and populated.")
    st.stop()

# =============================================================================
# STATUS OVERVIEW
# =============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    pending_count = len(pending_alerts)
    critical_count = len(pending_alerts[pending_alerts['FAILURE_PROBABILITY_CATEGORY'] == 'CRITICAL']) if len(pending_alerts) > 0 else 0
    st.metric("Pending Alerts", pending_count, f"{critical_count} critical" if critical_count > 0 else "None critical")

with col2:
    if quick_stats is not None and pd.notna(quick_stats.get('ACTIVE_LINES')):
        st.metric("Active Lines", int(quick_stats['ACTIVE_LINES']), "All operational")
    else:
        st.metric("Active Lines", 0, "↑ All operational")

with col3:
    if quick_stats is not None and pd.notna(quick_stats.get('TOTAL_AGV_FAILURES')):
        failures = int(quick_stats['TOTAL_AGV_FAILURES'])
        st.metric("AGV Issues (7d)", failures, "Need attention" if failures > 5 else "Normal")
    else:
        st.metric("AGV Issues (7d)", 0, "Normal")

with col4:
    if quick_stats is not None and pd.notna(quick_stats.get('AVG_OPE')):
        ope = float(quick_stats['AVG_OPE'])
        st.metric("Avg OPE (7d)", f"{ope:.1f}%", f"{ope-85:+.1f}% vs target")
    else:
        st.metric("Avg OPE (7d)", "—", "No data")

# =============================================================================
# SHIFT STATUS SUMMARY - STAR "Situation" Context
# =============================================================================

# Calculate summary stats for status message
high_priority_count = len(pending_alerts[pending_alerts['FAILURE_PROBABILITY_CATEGORY'].isin(['CRITICAL', 'HIGH'])]) if len(pending_alerts) > 0 else 0
agv_at_risk = len(agv_fleet_df[agv_fleet_df['STATUS'] == 'AT_RISK']) if len(agv_fleet_df) > 0 else 0
agv_total = len(agv_fleet_df) if len(agv_fleet_df) > 0 else 0
agv_active = len(agv_fleet_df[agv_fleet_df['STATUS'] == 'ACTIVE']) if len(agv_fleet_df) > 0 else 0
agv_capacity_pct = int((agv_active / agv_total * 100)) if agv_total > 0 else 0

# Determine overall status
if high_priority_count > 0 or agv_at_risk > 2:
    status_color = COLORS['danger']
    status_icon = "🔴"
    status_text = "Attention Required"
elif pending_count > 0 or agv_at_risk > 0:
    status_color = COLORS['warning']
    status_icon = "🟡"
    status_text = "Items to Review"
else:
    status_color = COLORS['success']
    status_icon = "🟢"
    status_text = "Operations Normal"

st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.15) 0%, {COLORS['surface']} 100%); 
            border-radius: 12px; padding: 1rem; margin: 1rem 0; border-left: 4px solid {status_color};">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 1.25rem;">{status_icon}</span>
            <strong style="color: {COLORS['text']}; font-size: 1.1rem; margin-left: 0.5rem;">Current Shift Status: {status_text}</strong>
        </div>
    </div>
    <div style="color: {COLORS['muted']}; font-size: 0.9rem; margin-top: 0.5rem;">
        <strong>{high_priority_count}</strong> high-priority items require immediate attention. 
        AGV fleet operating at <strong>{agv_capacity_pct}%</strong> capacity 
        ({agv_active}/{agv_total} active{f", {agv_at_risk} at risk" if agv_at_risk > 0 else ""}).
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# LITTLE'S LAW DIVERGENCE ALERT
# =============================================================================

# Check for Little's Law violations (WIP climbing while throughput stagnates)
if len(littles_law_df) > 0 and 'LITTLES_LAW_VIOLATION' in littles_law_df.columns:
    violations = littles_law_df[littles_law_df['LITTLES_LAW_VIOLATION'] == True]
    
    if len(violations) > 0:
        st.markdown("")
        
        # Get the most severe violation
        critical_violations = violations[violations['DIVERGENCE_SEVERITY'] == 'CRITICAL']
        warning_violations = violations[violations['DIVERGENCE_SEVERITY'] == 'WARNING']
        
        if len(critical_violations) > 0:
            latest_violation = critical_violations.iloc[0]
            severity = 'CRITICAL'
            alert_color = COLORS['danger']
        elif len(warning_violations) > 0:
            latest_violation = warning_violations.iloc[0]
            severity = 'WARNING'
            alert_color = COLORS['warning']
        else:
            latest_violation = violations.iloc[0]
            severity = 'WARNING'
            alert_color = COLORS['warning']
        
        # Extract metrics
        wip_count = int(latest_violation['WIP_COUNT']) if pd.notna(latest_violation.get('WIP_COUNT')) else 0
        throughput = int(latest_violation['THROUGHPUT_UNITS']) if pd.notna(latest_violation.get('THROUGHPUT_UNITS')) else 0
        cycle_time = float(latest_violation['CALCULATED_CYCLE_TIME_MIN']) if pd.notna(latest_violation.get('CALCULATED_CYCLE_TIME_MIN')) else 0
        wip_avg = float(latest_violation['WIP_3DAY_AVG']) if pd.notna(latest_violation.get('WIP_3DAY_AVG')) else 0
        line_id = str(latest_violation['PRODUCTION_LINE_ID']) if pd.notna(latest_violation.get('PRODUCTION_LINE_ID')) else 'Unknown'
        
        # Little's Law Alert Card - Use native Streamlit components for reliability
        wip_pct_above = ((wip_count / wip_avg - 1) * 100) if wip_avg > 0 else 0
        
        st.warning(f"**System Alert: Little's Law Divergence Detected** | {line_id} | Severity: {severity}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("WIP (Current)", wip_count, f"{wip_pct_above:.0f}% above avg")
        with col2:
            st.metric("Throughput", throughput, "units/day")
        with col3:
            st.metric("Cycle Time", f"{cycle_time:.0f}", "min/unit")
        with col4:
            st.metric("Status", "BLOCKED", "flow constrained")
        
        st.markdown(f"""
<div style="background: {COLORS['surface']}; border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
<div style="color: {COLORS['text']}; font-size: 0.875rem;"><strong>Analysis:</strong> WIP is accumulating faster than throughput can process. This is the classic sign of a hidden bottleneck.</div>
<div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-top: 0.5rem;"><strong>Formula:</strong> Cycle Time = WIP / Throughput = {wip_count} / {throughput} = {cycle_time:.1f} min</div>
<div style="color: {COLORS['accent']}; font-size: 0.875rem; margin-top: 0.5rem;"><strong>Recommendation:</strong> Investigate AGV transfer bottleneck. Execute Dust Mitigation Cycle to restore flow.</div>
</div>
""", unsafe_allow_html=True)
        
        # Educational expander for Little's Law
        with st.expander("What is Little's Law and why does this matter?"):
            st.markdown(f"""
**Little's Law** is a fundamental principle from queueing theory that governs how work flows through any system:

**L = λ × W**  (or equivalently: **Cycle Time = WIP / Throughput**)

Where:
- **L (WIP)** = Average number of items in the system (Work In Progress)
- **λ (Throughput)** = Rate at which items complete the system
- **W (Cycle Time)** = Average time an item spends in the system

---

**What is a Divergence?**

A "divergence" occurs when WIP increases but Throughput stays flat or decreases. Per Little's Law, this mathematically forces Cycle Time to increase—meaning work is taking longer to complete.

**Why This Matters for Operations:**

1. **Hidden Bottleneck Signal:** When WIP grows without corresponding throughput gains, something in your process is constraining flow. The bottleneck may not be obvious—it could be AGV transfer delays, quality holds, or material staging issues.

2. **Downstream Starvation Risk:** As WIP accumulates at the constraint, downstream stations will eventually starve, causing cascading delays.

3. **Quality Risk:** Aged WIP can lead to quality issues—batteries waiting too long, environmental exposure, or time-sensitive processes missing windows.

4. **Cost Impact:** Every unit stuck in WIP is tied-up capital that isn't generating revenue.

---

**Recommended Response:**
1. Identify the constraint point (where is WIP accumulating?)
2. Check AGV transfer efficiency and environmental conditions
3. Execute mitigation protocols (e.g., Dust Mitigation Cycle)
4. Monitor until WIP/Throughput ratio normalizes
            """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# PENDING ACTIONS - Top 10 Items to Review
# =============================================================================

render_section_header("Action Required", "Top items requiring your review")

if len(pending_alerts) > 0:
    # Initialize session state for alert actions
    if 'approved_alerts' not in st.session_state:
        st.session_state.approved_alerts = set()
    if 'dismissed_alerts' not in st.session_state:
        st.session_state.dismissed_alerts = set()
    
    for idx, alert in pending_alerts.head(10).iterrows():
        alert_id = str(alert['ALERT_ID'])
        
        # Skip if already actioned
        if alert_id in st.session_state.approved_alerts or alert_id in st.session_state.dismissed_alerts:
            continue
        
        prob = float(alert['FAILURE_PROBABILITY'])
        category = str(alert['FAILURE_PROBABILITY_CATEGORY'])
        zone = str(alert['TARGET_ZONE_ID'])
        risk_factor = str(alert['PRIMARY_RISK_FACTOR'])
        action = str(alert['RECOMMENDED_ACTION'])
        humidity = float(alert['FORECAST_HUMIDITY']) if pd.notna(alert['FORECAST_HUMIDITY']) else 0
        prevention_value = float(alert['ESTIMATED_PREVENTION_VALUE']) if pd.notna(alert.get('ESTIMATED_PREVENTION_VALUE')) else 0
        priority = str(alert['ACTION_PRIORITY']) if pd.notna(alert.get('ACTION_PRIORITY')) else 'MONITOR'
        
        # Determine urgency message based on priority
        urgency_msg = ""
        if priority == 'IMMEDIATE':
            urgency_msg = "Act within 1 hour"
        elif priority == 'SCHEDULED':
            urgency_msg = "Act within 4 hours"
        else:
            urgency_msg = "Monitor closely"
        
        # Alert card with action buttons
        col1, col2 = st.columns([4, 1])
        
        with col1:
            icon = "🔴" if category in ['CRITICAL', 'HIGH'] else "🟡"
            
            # Build details dict including prevention value if applicable
            details = {
                "Risk Factor": risk_factor,
                "Humidity": f"{humidity:.0f}%"
            }
            if prevention_value > 0:
                details["Est. Prevention Value"] = f"${prevention_value:,.0f}"
            
            render_alert_card(
                title=f"{icon} Zone {zone} — {category}",
                subtitle=f"{alert['TARGET_DATE']} Hour {alert['TARGET_HOUR']} | Probability: {prob*100:.0f}%",
                risk_level=category,
                details=details,
                recommendation=action,
                badge_text=urgency_msg
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            
            # Store prevention value in session state for feedback
            if st.button("✅ Approve", key=f"approve_{alert_id}", use_container_width=True):
                if update_alert_status(session, alert_id, 'APPROVED'):
                    st.session_state.approved_alerts.add(alert_id)
                    if prevention_value > 0:
                        st.success(f"Action approved for Zone {zone}. Est. ${prevention_value:,.0f} downtime prevented.")
                    else:
                        st.success(f"Action approved for Zone {zone}. Maintenance scheduled.")
                    st.rerun()
            
            if st.button("❌ Dismiss", key=f"dismiss_{alert_id}", use_container_width=True):
                if update_alert_status(session, alert_id, 'DISMISSED'):
                    st.session_state.dismissed_alerts.add(alert_id)
                    st.info(f"Alert dismissed for Zone {zone}. No action taken.")
                    st.rerun()
        
        st.markdown("")  # Spacing between alerts
else:
    st.success("No pending actions — all alerts have been addressed")

st.markdown("---")

# =============================================================================
# AGV FLEET STATUS
# =============================================================================

render_section_header("AGV Fleet Status", "Current fleet health and status")

# Use AGV fleet data from database query
if len(agv_fleet_df) > 0:
    agv_data = agv_fleet_df.copy()
    
    # Ensure column names are uppercase for consistency
    agv_data.columns = [col.upper() for col in agv_data.columns]
    
    # Add risk level column based on failure risk
    def get_risk_level(risk):
        if risk > 0.5:
            return '🔴 High'
        elif risk > 0.2:
            return '🟡 Medium'
        else:
            return '🟢 Low'
    
    agv_data['RISK_LEVEL'] = agv_data['FAILURE_RISK'].apply(get_risk_level)
    agv_data['BATTERY'] = agv_data['BATTERY_LEVEL'].astype(int).astype(str) + '%'
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_count = len(agv_data[agv_data['STATUS'] == 'ACTIVE'])
        st.metric("Active", active_count, f"/{len(agv_data)} total")
    
    with col2:
        maintenance_count = len(agv_data[agv_data['STATUS'] == 'MAINTENANCE'])
        st.metric("In Maintenance", maintenance_count)
    
    with col3:
        at_risk_count = len(agv_data[agv_data['STATUS'] == 'AT_RISK'])
        st.metric("At Risk", at_risk_count, "Sensor errors" if at_risk_count > 0 else "None")
    
    with col4:
        avg_battery = agv_data['BATTERY_LEVEL'].mean()
        st.metric("Avg Battery", f"{avg_battery:.0f}%")
    
    # AGV table
    st.dataframe(
        agv_data[['AGV_ID', 'ZONE', 'STATUS', 'BATTERY', 'RISK_LEVEL', 'LAST_ERROR']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'AGV_ID': 'AGV',
            'ZONE': 'Zone',
            'STATUS': 'Status',
            'BATTERY': 'Battery',
            'RISK_LEVEL': 'Risk Level',
            'LAST_ERROR': 'Last Error'
        }
    )
    
    # Legend
    st.markdown(f"""
    <div style="display: flex; gap: 2rem; margin-top: 0.5rem; color: {COLORS['muted']}; font-size: 0.875rem;">
        <span>🟢 Low Risk (<20%)</span>
        <span>🟡 Medium Risk (20-50%)</span>
        <span>🔴 High Risk (>50%)</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No AGV fleet data available. Please run the data generation notebook.")

st.markdown("---")

# =============================================================================
# RECENT ACTIVITY LOG
# =============================================================================

render_section_header("Recent Activity", "Alert history and actions taken")

if len(all_alerts) > 0:
    # Display recent alerts as activity log
    activity_df = all_alerts[['PREDICTION_TIMESTAMP', 'TARGET_ZONE_ID', 
                               'FAILURE_PROBABILITY_CATEGORY', 'ACTION_STATUS', 
                               'RECOMMENDED_ACTION']].head(10).copy()
    
    activity_df.columns = ['Timestamp', 'Zone', 'Priority', 'Status', 'Action']
    activity_df['Timestamp'] = pd.to_datetime(activity_df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        activity_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No recent activity to display")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {COLORS['muted']}; font-size: 0.875rem;">
    Operations Control | Auto-refresh: 60 seconds
</div>
""", unsafe_allow_html=True)

