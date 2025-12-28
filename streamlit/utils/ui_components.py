"""
Reusable UI Components for VoltStream OPE Dashboard
====================================================

Styled components following SNOWFLAKE_STREAMLIT_GUIDELINES.md:
- No st.expander for important content
- Scrollable containers instead of hidden content
- Inline AI content cards
- Dark theme styling

Color palette (Tailwind Slate):
- Background: #0f172a (slate-900)
- Surface: #1e293b (slate-800)
- Border: #334155 (slate-700)
- Text: #e2e8f0 (slate-200)
- Muted: #94a3b8 (slate-400)
- Accent: #3b82f6 (blue-500)
- Success: #10b981 (emerald-500)
- Warning: #f59e0b (amber-500)
- Danger: #ef4444 (red-500)
"""

import streamlit as st
from typing import List, Dict, Any, Optional


# =============================================================================
# THEME CONSTANTS
# =============================================================================

COLORS = {
    'background': '#0f172a',
    'surface': '#1e293b',
    'border': '#334155',
    'text': '#e2e8f0',
    'muted': '#94a3b8',
    'accent': '#3b82f6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'snowflake': '#29B5E8',
}

PLOTLY_THEME = {
    'paper_bgcolor': COLORS['background'],
    'plot_bgcolor': COLORS['background'],
    'font': {'color': COLORS['text']},
    'hoverlabel': {
        'bgcolor': COLORS['surface'],
        'bordercolor': COLORS['border'],
        'font': {'size': 12, 'color': COLORS['text']}
    }
}


# =============================================================================
# METRIC CARDS
# =============================================================================

def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    icon: Optional[str] = None
):
    """
    Render a styled metric card using native st.metric for reliable SiS rendering.
    
    Args:
        label: Metric label
        value: Main value to display
        delta: Optional delta/change text
        delta_color: "normal" (green for positive), "inverse" (red for positive), "off" (no color)
        icon: Optional emoji icon (prepended to label)
    """
    # Prepend icon to label if provided
    display_label = f"{icon} {label}" if icon else label
    
    # Normalize delta_color to valid st.metric values
    valid_delta_colors = ["normal", "inverse", "off"]
    normalized_delta_color = delta_color if delta_color in valid_delta_colors else "off"
    
    # Use native st.metric for reliable rendering in Streamlit in Snowflake
    st.metric(
        label=display_label,
        value=value,
        delta=delta,
        delta_color=normalized_delta_color
    )


def render_metric_row(metrics: List[Dict[str, Any]]):
    """
    Render a row of metric cards.
    
    Args:
        metrics: List of dicts with keys: label, value, delta, delta_color, icon
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            render_metric_card(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                delta=metric.get('delta'),
                delta_color=metric.get('delta_color', 'normal'),
                icon=metric.get('icon')
            )


# =============================================================================
# ALERT CARDS
# =============================================================================

def get_risk_color(level: str) -> str:
    """Get color for risk level."""
    level_upper = level.upper()
    if level_upper in ['CRITICAL', 'HIGH']:
        return COLORS['danger']
    elif level_upper in ['MEDIUM', 'MODERATE', 'WARNING']:
        return COLORS['warning']
    else:
        return COLORS['success']


def render_alert_card(
    title: str,
    subtitle: str,
    risk_level: str,
    details: Dict[str, str],
    recommendation: Optional[str] = None,
    badge_text: Optional[str] = None
):
    """
    Render a styled alert card with risk coloring.
    
    Args:
        title: Alert title
        subtitle: Secondary text
        risk_level: "CRITICAL", "HIGH", "MEDIUM", "LOW"
        details: Dict of label-value pairs to display
        recommendation: Optional recommendation text
        badge_text: Optional custom badge text (defaults to risk_level if not provided)
    """
    color = get_risk_color(risk_level)
    display_badge = badge_text if badge_text else risk_level
    
    details_html = ''.join([
        f'<span style="color: {COLORS["muted"]};">{k}: <strong style="color: {COLORS["text"]};">{v}</strong></span><br>'
        for k, v in details.items()
    ])
    
    rec_html = f'''
    <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid {COLORS['border']};">
        <strong style="color: {COLORS['text']};">Recommendation:</strong>
        <span style="color: {COLORS['muted']};">{recommendation}</span>
    </div>
    ''' if recommendation else ''
    
    st.markdown(f'''
    <div style="background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
                border-left: 4px solid {color}; padding: 1rem; border-radius: 0 8px 8px 0;
                margin-bottom: 0.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <strong style="color: {COLORS['text']};">{title}</strong>
                <div style="color: {COLORS['muted']}; font-size: 0.875rem; margin-top: 0.25rem;">{subtitle}</div>
            </div>
            <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 12px;
                         font-size: 0.75rem; font-weight: 600;">{display_badge}</span>
        </div>
        <div style="margin-top: 0.75rem; font-size: 0.875rem;">
            {details_html}
        </div>
        {rec_html}
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# AI INSIGHT CARDS (Not expander - inline display)
# =============================================================================

def render_ai_insight(content: str, title: str = "AI Analysis"):
    """
    Render an inline AI insight card (NOT in expander per guidelines).
    
    Args:
        content: AI-generated text content
        title: Card title
    """
    st.markdown(f'''
    <div style="background: rgba(59, 130, 246, 0.08); border-left: 3px solid {COLORS['accent']}; 
                padding: 0.75rem 1rem; margin-top: 0.5rem; border-radius: 0 8px 8px 0;">
        <div style="color: {COLORS['accent']}; font-size: 0.75rem; text-transform: uppercase; 
                    letter-spacing: 0.05em; margin-bottom: 0.25rem;">{title}</div>
        <p style="color: {COLORS['text']}; line-height: 1.5; margin: 0;">{content}</p>
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# SCROLLABLE CONTAINERS (Alternative to expanders)
# =============================================================================

def render_scrollable_list(items: List[str], max_height: int = 150, title: Optional[str] = None):
    """
    Render a scrollable list container (alternative to expander).
    
    Args:
        items: List of text items
        max_height: Maximum height in pixels
        title: Optional title above the list
    """
    if title:
        st.markdown(f"**{title}**")
    
    items_html = ''.join([
        f'<div style="padding: 0.5rem; border-bottom: 1px solid {COLORS["border"]}; color: {COLORS["text"]};">{item}</div>'
        for item in items
    ])
    
    st.markdown(f'''
    <div style="max-height: {max_height}px; overflow-y: auto; background: {COLORS['surface']};
                border-radius: 8px; border: 1px solid {COLORS['border']};">
        {items_html}
    </div>
    ''', unsafe_allow_html=True)


def render_chip_list(items: List[str], max_height: int = 120):
    """
    Render items as chips in a scrollable container.
    
    Args:
        items: List of chip labels
        max_height: Maximum height in pixels
    """
    chips_html = ''.join([
        f'''<span style="display: inline-block; background: {COLORS['surface']}; 
                        border: 1px solid {COLORS['border']}; border-radius: 16px;
                        padding: 4px 12px; margin: 4px; color: {COLORS['text']};
                        font-size: 0.875rem;">{item}</span>'''
        for item in items
    ])
    
    st.markdown(f'''
    <div style="max-height: {max_height}px; overflow-y: auto; padding: 8px; 
                background: rgba(15, 23, 42, 0.5); border-radius: 8px;">
        {chips_html}
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# DATA SOURCE BADGES
# =============================================================================

def render_data_source_badge(source_type: str, label: str):
    """
    Render a data source badge with correct coloring per About page guidelines.
    
    Args:
        source_type: "internal", "external", or "model"
        label: Badge text
    """
    colors = {
        'internal': ('#1e40af', '#60a5fa'),  # Blue
        'external': ('#b45309', '#fbbf24'),  # Amber
        'model': ('#166534', '#4ade80'),     # Green
    }
    
    bg, text = colors.get(source_type.lower(), ('#6b7280', '#e2e8f0'))
    
    st.markdown(f'''
    <span style="display: inline-block; background: rgba({int(bg[1:3], 16)}, {int(bg[3:5], 16)}, {int(bg[5:7], 16)}, 0.2);
                 border-left: 4px solid {bg}; padding: 0.5rem 1rem; border-radius: 0 8px 8px 0;
                 margin: 0.25rem 0;">
        <strong style="color: {text};">{source_type.title()}</strong>
        <span style="color: {COLORS['muted']}; margin-left: 0.5rem;">{label}</span>
    </span>
    ''', unsafe_allow_html=True)


# =============================================================================
# LEGEND COMPONENTS
# =============================================================================

def render_legend(items: List[Dict[str, str]]):
    """
    Render a horizontal legend.
    
    Args:
        items: List of dicts with 'color' and 'label' keys
    """
    legend_html = '<div style="display: flex; gap: 1.5rem; justify-content: center; margin: 0.5rem 0;">'
    for item in items:
        legend_html += f'''
            <span style="color: {COLORS['muted']};">
                <span style="color: {item['color']};">●</span> {item['label']}
            </span>
        '''
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)


# =============================================================================
# SECTION HEADERS
# =============================================================================

def render_section_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    """
    Render a styled section header.
    
    Args:
        title: Section title
        subtitle: Optional subtitle text
        icon: Optional emoji icon
    """
    icon_html = f'{icon} ' if icon else ''
    subtitle_html = f'<div style="color: {COLORS["muted"]}; font-size: 0.875rem; font-style: italic;">{subtitle}</div>' if subtitle else ''
    
    st.markdown(f'''
    <div style="margin-top: 1.5rem; margin-bottom: 1rem;">
        <h4 style="color: {COLORS['text']}; margin-bottom: 0.25rem;">{icon_html}{title}</h4>
        {subtitle_html}
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# GLOBAL STYLES
# =============================================================================

def apply_global_styles():
    """Apply global dark theme styles to the app."""
    st.markdown(f"""
    <style>
        /* Dark theme with Snowflake blue accents */
        .stApp {{
            background-color: {COLORS['background']};
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
        }}
        
        /* Title styling */
        h1 {{
            color: #f8fafc !important;
            font-weight: 700 !important;
        }}
        
        h2, h3, h4 {{
            color: {COLORS['text']} !important;
        }}
        
        /* Metric styling */
        [data-testid="stMetricValue"] {{
            color: {COLORS['snowflake']} !important;
        }}
        
        /* Dataframe styling */
        .stDataFrame {{
            background-color: {COLORS['surface']};
        }}
    </style>
    """, unsafe_allow_html=True)

