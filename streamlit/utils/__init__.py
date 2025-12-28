"""
VoltStream OPE Dashboard Utilities
===================================

Provides:
- Query registry for testable SQL queries
- Parallel query executor for fast page loads
- Cortex AI helpers for LLM/RAG integration
- Reusable UI components with dark theme styling
"""

from utils.query_registry import (
    register_query,
    get_registered_queries,
    QUERY_REGISTRY,
    # Pre-registered queries
    OPE_DAILY_METRICS_SQL,
    OPE_LATEST_METRICS_SQL,
    OPE_BY_LINE_SQL,
    AGV_ANALYSIS_SQL,
    AGV_FAILURE_BY_ENV_SQL,
    PENDING_ALERTS_SQL,
    ALL_ALERTS_SQL,
    QUICK_STATS_SQL,
    DAILY_TREND_SQL,
    ENV_TREND_SQL,
)

from utils.data_loader import (
    run_queries_parallel,
    run_single_query,
    convert_for_plotly,
)

from utils.cortex_helpers import (
    call_cortex_complete,
    call_cortex_analyst,
    call_cortex_search,
    generate_ope_insight,
    generate_root_cause_analysis,
)

from utils.ui_components import (
    COLORS,
    PLOTLY_THEME,
    render_metric_card,
    render_metric_row,
    render_alert_card,
    get_risk_color,
    render_ai_insight,
    render_scrollable_list,
    render_chip_list,
    render_data_source_badge,
    render_legend,
    render_section_header,
    apply_global_styles,
)

__all__ = [
    # Query registry
    'register_query',
    'get_registered_queries',
    'QUERY_REGISTRY',
    'OPE_DAILY_METRICS_SQL',
    'OPE_LATEST_METRICS_SQL',
    'OPE_BY_LINE_SQL',
    'AGV_ANALYSIS_SQL',
    'AGV_FAILURE_BY_ENV_SQL',
    'PENDING_ALERTS_SQL',
    'ALL_ALERTS_SQL',
    'QUICK_STATS_SQL',
    'DAILY_TREND_SQL',
    'ENV_TREND_SQL',
    # Data loader
    'run_queries_parallel',
    'run_single_query',
    'convert_for_plotly',
    # Cortex helpers
    'call_cortex_complete',
    'call_cortex_analyst',
    'call_cortex_search',
    'generate_ope_insight',
    'generate_root_cause_analysis',
    # UI components
    'COLORS',
    'PLOTLY_THEME',
    'render_metric_card',
    'render_metric_row',
    'render_alert_card',
    'get_risk_color',
    'render_ai_insight',
    'render_scrollable_list',
    'render_chip_list',
    'render_data_source_badge',
    'render_legend',
    'render_section_header',
    'apply_global_styles',
]

