"""
Query Registry for VoltStream OPE Dashboard
============================================

Central registry of all SQL queries used in the Streamlit app.
Each query can be tested independently via ./run.sh test.

Following SNOWFLAKE_STREAMLIT_PARALLEL_QUERIES.md guidelines.
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class QueryDefinition:
    """A testable query definition."""
    name: str
    sql: str
    description: str
    min_rows: int = 0  # Expected minimum rows (0 = just check it runs)


# All queries must be registered here for testability
QUERY_REGISTRY: Dict[str, QueryDefinition] = {}


def register_query(name: str, sql: str, description: str, min_rows: int = 0) -> str:
    """
    Register a query for testing.
    
    Args:
        name: Unique identifier for the query
        sql: The SQL string to execute
        description: Human-readable description of what this query does
        min_rows: Minimum expected rows (0 = just check it runs without error)
    
    Returns:
        The SQL string (for inline use)
    """
    QUERY_REGISTRY[name] = QueryDefinition(name, sql, description, min_rows)
    return sql


def get_registered_queries() -> Dict[str, QueryDefinition]:
    """Get all registered queries for testing."""
    return QUERY_REGISTRY.copy()


# =============================================================================
# REGISTERED QUERIES - OPE Daily Metrics
# =============================================================================

OPE_DAILY_METRICS_SQL = register_query(
    "ope_daily_metrics",
    """
    SELECT 
        METRIC_DATE,
        PRODUCTION_LINE_ID,
        SHIFT_ID,
        OEE_PCT,
        OPE_PCT,
        STARVATION_DOWNTIME_MIN,
        AGV_FAILURE_COUNT,
        AGV_ERR_99_COUNT,
        AVG_HUMIDITY,
        AVG_DUST_PM25,
        ACTUAL_QUANTITY,
        PLANNED_QUANTITY,
        YIELD_PCT
    FROM EV_OPE.OPE_DAILY_FACT
    ORDER BY METRIC_DATE DESC
    """,
    "Daily OPE metrics for all production lines",
    min_rows=1
)

OPE_LATEST_METRICS_SQL = register_query(
    "ope_latest_metrics",
    """
    SELECT 
        METRIC_DATE,
        PRODUCTION_LINE_ID,
        SHIFT_ID,
        OEE_PCT,
        OPE_PCT,
        STARVATION_DOWNTIME_MIN,
        AGV_FAILURE_COUNT,
        AGV_ERR_99_COUNT,
        AVG_HUMIDITY,
        AVG_DUST_PM25,
        ACTUAL_QUANTITY
    FROM EV_OPE.OPE_DAILY_FACT
    WHERE METRIC_DATE = (SELECT MAX(METRIC_DATE) FROM EV_OPE.OPE_DAILY_FACT)
    """,
    "Latest day OPE metrics",
    min_rows=1
)

OPE_BY_LINE_SQL = register_query(
    "ope_by_line",
    """
    SELECT 
        PRODUCTION_LINE_ID,
        ROUND(AVG(OEE_PCT), 2) AS AVG_OEE,
        ROUND(AVG(OPE_PCT), 2) AS AVG_OPE,
        ROUND(AVG(OEE_PCT) - AVG(OPE_PCT), 2) AS EFFICIENCY_GAP,
        SUM(STARVATION_DOWNTIME_MIN) AS TOTAL_STARVATION_MIN,
        SUM(AGV_FAILURE_COUNT) AS TOTAL_AGV_FAILURES
    FROM EV_OPE.OPE_DAILY_FACT
    GROUP BY PRODUCTION_LINE_ID
    ORDER BY PRODUCTION_LINE_ID
    """,
    "OPE metrics aggregated by production line",
    min_rows=1
)

# =============================================================================
# REGISTERED QUERIES - AGV Analysis
# =============================================================================

AGV_ANALYSIS_SQL = register_query(
    "agv_analysis",
    """
    SELECT 
        ANALYSIS_DATE,
        ANALYSIS_HOUR,
        ZONE_ID,
        AVG_HUMIDITY,
        AVG_DUST_PM25,
        HUMIDITY_CATEGORY,
        DUST_CATEGORY,
        TOTAL_AGV_OPERATIONS,
        FAILED_OPERATIONS,
        FAILURE_RATE,
        AGV_ERR_99_COUNT,
        IS_HIGH_FAILURE_PERIOD
    FROM EV_OPE.AGV_FAILURE_ANALYSIS
    ORDER BY ANALYSIS_DATE DESC, ANALYSIS_HOUR DESC
    """,
    "AGV failure analysis with environmental correlation",
    min_rows=1
)

AGV_FAILURE_BY_ENV_SQL = register_query(
    "agv_failure_by_environment",
    """
    SELECT 
        HUMIDITY_CATEGORY,
        DUST_CATEGORY,
        COUNT(*) AS OBSERVATION_COUNT,
        ROUND(AVG(FAILURE_RATE) * 100, 2) AS AVG_FAILURE_RATE_PCT,
        SUM(AGV_ERR_99_COUNT) AS TOTAL_SENSOR_ERRORS
    FROM EV_OPE.AGV_FAILURE_ANALYSIS
    GROUP BY HUMIDITY_CATEGORY, DUST_CATEGORY
    ORDER BY AVG_FAILURE_RATE_PCT DESC
    """,
    "AGV failure rates by environmental conditions",
    min_rows=1
)

# =============================================================================
# REGISTERED QUERIES - Maintenance Alerts
# =============================================================================

PENDING_ALERTS_SQL = register_query(
    "pending_alerts",
    """
    SELECT 
        ALERT_ID,
        TARGET_ZONE_ID,
        TARGET_DATE,
        TARGET_HOUR,
        FAILURE_PROBABILITY,
        FAILURE_PROBABILITY_CATEGORY,
        PRIMARY_RISK_FACTOR,
        FORECAST_HUMIDITY,
        FORECAST_DUST_PM25,
        RECOMMENDED_ACTION,
        ACTION_PRIORITY,
        ACTION_STATUS,
        PREDICTION_TIMESTAMP,
        ESTIMATED_PREVENTION_VALUE
    FROM EV_OPE.PREDICTIVE_MAINTENANCE_ALERTS
    WHERE ACTION_STATUS = 'PENDING'
    ORDER BY FAILURE_PROBABILITY DESC
    LIMIT 20
    """,
    "Pending maintenance alerts sorted by failure probability",
    min_rows=0  # May have no pending alerts
)

ALL_ALERTS_SQL = register_query(
    "all_alerts",
    """
    SELECT 
        ALERT_ID,
        TARGET_ZONE_ID,
        TARGET_DATE,
        TARGET_HOUR,
        FAILURE_PROBABILITY,
        FAILURE_PROBABILITY_CATEGORY,
        PRIMARY_RISK_FACTOR,
        RECOMMENDED_ACTION,
        ACTION_PRIORITY,
        ACTION_STATUS,
        PREDICTION_TIMESTAMP
    FROM EV_OPE.PREDICTIVE_MAINTENANCE_ALERTS
    ORDER BY PREDICTION_TIMESTAMP DESC
    LIMIT 100
    """,
    "All recent maintenance alerts",
    min_rows=0
)

# =============================================================================
# REGISTERED QUERIES - Quick Stats
# =============================================================================

QUICK_STATS_SQL = register_query(
    "quick_stats",
    """
    WITH date_range AS (
        SELECT MAX(METRIC_DATE) AS max_date FROM EV_OPE.OPE_DAILY_FACT
    )
    SELECT 
        COUNT(DISTINCT PRODUCTION_LINE_ID) AS ACTIVE_LINES,
        ROUND(AVG(OPE_PCT), 1) AS AVG_OPE,
        ROUND(AVG(OEE_PCT), 1) AS AVG_OEE,
        SUM(AGV_FAILURE_COUNT) AS TOTAL_AGV_FAILURES
    FROM EV_OPE.OPE_DAILY_FACT, date_range
    WHERE METRIC_DATE >= DATEADD(day, -7, date_range.max_date)
    """,
    "Quick stats for sidebar (last 7 days relative to data)",
    min_rows=1
)

# =============================================================================
# REGISTERED QUERIES - Trend Data
# =============================================================================

DAILY_TREND_SQL = register_query(
    "daily_trend",
    """
    SELECT 
        METRIC_DATE,
        ROUND(AVG(OEE_PCT), 2) AS AVG_OEE,
        ROUND(AVG(OPE_PCT), 2) AS AVG_OPE,
        SUM(STARVATION_DOWNTIME_MIN) AS TOTAL_STARVATION,
        SUM(AGV_FAILURE_COUNT) AS TOTAL_FAILURES
    FROM EV_OPE.OPE_DAILY_FACT
    GROUP BY METRIC_DATE
    ORDER BY METRIC_DATE
    """,
    "Daily trend data for time series charts",
    min_rows=1
)

ENV_TREND_SQL = register_query(
    "env_trend",
    """
    SELECT 
        METRIC_DATE,
        ROUND(AVG(AVG_HUMIDITY), 2) AS AVG_HUMIDITY,
        ROUND(AVG(AVG_DUST_PM25), 2) AS AVG_DUST,
        SUM(AGV_ERR_99_COUNT) AS TOTAL_ERR_99
    FROM EV_OPE.OPE_DAILY_FACT
    GROUP BY METRIC_DATE
    ORDER BY METRIC_DATE
    """,
    "Environmental trend data",
    min_rows=1
)

# =============================================================================
# REGISTERED QUERIES - AGV Fleet Status
# =============================================================================

AGV_FLEET_STATUS_SQL = register_query(
    "agv_fleet_status",
    """
    WITH data_max_date AS (
        -- Get max date from actual data (for demo with historical synthetic data)
        SELECT MAX(EVENT_TIMESTAMP) AS max_ts FROM RAW.AGV_TELEMATICS_LOG_CDC
    ),
    latest_telemetry AS (
        SELECT 
            AGV_ID,
            BATTERY_LEVEL,
            ERROR_CODE,
            ZONE_ID AS TELEMETRY_ZONE,
            ROW_NUMBER() OVER (PARTITION BY AGV_ID ORDER BY EVENT_TIMESTAMP DESC) AS rn
        FROM RAW.AGV_TELEMATICS_LOG_CDC, data_max_date
        WHERE EVENT_TIMESTAMP >= DATEADD(day, -1, data_max_date.max_ts)
    ),
    zone_predictions AS (
        SELECT 
            TARGET_ZONE_ID,
            MAX(FAILURE_PROBABILITY) AS MAX_FAILURE_PROBABILITY
        FROM EV_OPE.PREDICTIVE_MAINTENANCE_ALERTS
        WHERE ACTION_STATUS = 'PENDING'
        GROUP BY TARGET_ZONE_ID
    ),
    recent_errors AS (
        SELECT 
            AGV_ID,
            ERROR_CODE AS LAST_ERROR_CODE,
            ROW_NUMBER() OVER (PARTITION BY AGV_ID ORDER BY EVENT_TIMESTAMP DESC) AS rn
        FROM RAW.AGV_TELEMATICS_LOG_CDC, data_max_date
        WHERE ERROR_CODE IS NOT NULL
          AND EVENT_TIMESTAMP >= DATEADD(day, -7, data_max_date.max_ts)
    )
    SELECT 
        a.ASSET_CODE AS AGV_ID,
        COALESCE(t.TELEMETRY_ZONE, a.ZONE_ID) AS ZONE,
        CASE 
            WHEN e.LAST_ERROR_CODE IS NOT NULL THEN 'AT_RISK'
            WHEN a.ASSET_STATUS = 'MAINTENANCE' THEN 'MAINTENANCE'
            ELSE 'ACTIVE'
        END AS STATUS,
        ROUND(COALESCE(t.BATTERY_LEVEL, 50), 0) AS BATTERY_LEVEL,
        COALESCE(p.MAX_FAILURE_PROBABILITY, 0) AS FAILURE_RISK,
        COALESCE(e.LAST_ERROR_CODE, 'None') AS LAST_ERROR
    FROM ATOMIC.ASSET a
    LEFT JOIN latest_telemetry t ON a.ASSET_CODE = t.AGV_ID AND t.rn = 1
    LEFT JOIN zone_predictions p ON COALESCE(t.TELEMETRY_ZONE, a.ZONE_ID) = p.TARGET_ZONE_ID
    LEFT JOIN recent_errors e ON a.ASSET_CODE = e.AGV_ID AND e.rn = 1
    WHERE a.ASSET_TYPE = 'AGV'
      AND a.IS_CURRENT_FLAG = TRUE
    ORDER BY a.ASSET_CODE
    """,
    "AGV fleet status with latest telemetry and risk levels",
    min_rows=0  # May have no AGVs if data not yet loaded
)

# =============================================================================
# REGISTERED QUERIES - Throughput Economics (Financial Linkage)
# =============================================================================

THROUGHPUT_ECONOMICS_SQL = register_query(
    "throughput_economics",
    """
    WITH product_economics AS (
        -- Get primary product economics (EV battery packs)
        SELECT 
            PRODUCT_CODE AS SKU,
            PRODUCT_NAME,
            COALESCE(STANDARD_COST, 2500) AS STANDARD_COST,
            COALESCE(STANDARD_COST * 1.35, 3375) AS UNIT_PRICE,  -- 35% margin assumption
            COALESCE(STANDARD_COST * 1.35 - STANDARD_COST, 875) AS CONTRIBUTION_MARGIN
        FROM ATOMIC.PRODUCT
        WHERE IS_CURRENT_FLAG = TRUE
        LIMIT 1
    )
    SELECT 
        odf.METRIC_DATE,
        odf.PRODUCTION_LINE_ID,
        odf.SHIFT_ID,
        ROUND(odf.OEE_PCT, 2) AS OEE_PCT,
        ROUND(odf.OPE_PCT, 2) AS OPE_PCT,
        ROUND(odf.OEE_PCT - odf.OPE_PCT, 2) AS EFFICIENCY_GAP_PCT,
        odf.ACTUAL_QUANTITY,
        odf.PLANNED_QUANTITY,
        odf.STARVATION_DOWNTIME_MIN,
        odf.AGV_FAILURE_COUNT,
        pe.SKU,
        pe.CONTRIBUTION_MARGIN,
        -- Throughput loss calculation: Gap% * Planned Units * Margin
        ROUND((odf.OEE_PCT - odf.OPE_PCT) / 100.0 * odf.PLANNED_QUANTITY * pe.CONTRIBUTION_MARGIN, 2) AS THROUGHPUT_LOSS_DOLLARS,
        -- Hourly rate (8 hour shift = 480 min)
        ROUND((odf.OEE_PCT - odf.OPE_PCT) / 100.0 * odf.PLANNED_QUANTITY * pe.CONTRIBUTION_MARGIN / 8, 2) AS THROUGHPUT_LOSS_PER_HOUR,
        -- Contribution margin per minute
        ROUND(odf.ACTUAL_QUANTITY * pe.CONTRIBUTION_MARGIN / 480, 2) AS CONTRIBUTION_MARGIN_PER_MIN
    FROM EV_OPE.OPE_DAILY_FACT odf
    CROSS JOIN product_economics pe
    WHERE odf.PLANNED_QUANTITY > 0
    ORDER BY odf.METRIC_DATE DESC, odf.PRODUCTION_LINE_ID
    """,
    "Throughput economics with financial impact of OPE gap",
    min_rows=1
)

THROUGHPUT_BY_LINE_SQL = register_query(
    "throughput_by_line",
    """
    WITH product_economics AS (
        SELECT 
            COALESCE(STANDARD_COST * 1.35 - STANDARD_COST, 875) AS CONTRIBUTION_MARGIN
        FROM ATOMIC.PRODUCT
        WHERE IS_CURRENT_FLAG = TRUE
        LIMIT 1
    )
    SELECT 
        odf.PRODUCTION_LINE_ID,
        ROUND(AVG(odf.OEE_PCT), 2) AS AVG_OEE,
        ROUND(AVG(odf.OPE_PCT), 2) AS AVG_OPE,
        ROUND(AVG(odf.OEE_PCT) - AVG(odf.OPE_PCT), 2) AS AVG_GAP_PCT,
        SUM(odf.ACTUAL_QUANTITY) AS TOTAL_UNITS,
        SUM(odf.STARVATION_DOWNTIME_MIN) AS TOTAL_STARVATION_MIN,
        -- Total throughput loss by line
        ROUND(SUM((odf.OEE_PCT - odf.OPE_PCT) / 100.0 * odf.PLANNED_QUANTITY * pe.CONTRIBUTION_MARGIN), 2) AS TOTAL_THROUGHPUT_LOSS,
        -- Average hourly loss
        ROUND(AVG((odf.OEE_PCT - odf.OPE_PCT) / 100.0 * odf.PLANNED_QUANTITY * pe.CONTRIBUTION_MARGIN / 8), 2) AS AVG_LOSS_PER_HOUR
    FROM EV_OPE.OPE_DAILY_FACT odf
    CROSS JOIN product_economics pe
    WHERE odf.PLANNED_QUANTITY > 0
    GROUP BY odf.PRODUCTION_LINE_ID
    ORDER BY TOTAL_THROUGHPUT_LOSS DESC
    """,
    "Throughput loss aggregated by production line",
    min_rows=1
)

# =============================================================================
# REGISTERED QUERIES - Little's Law Metrics (WIP vs Throughput)
# =============================================================================

LITTLES_LAW_METRICS_SQL = register_query(
    "littles_law_metrics",
    """
    WITH daily_flow AS (
        SELECT 
            wo.PLANNED_START_DATE AS METRIC_DATE,
            wo.PRODUCTION_LINE_ID,
            -- WIP: Orders started but not completed
            COUNT(CASE WHEN wo.WORK_ORDER_STATUS IN ('RELEASED', 'STARTED', 'IN_PROGRESS') THEN 1 END) AS WIP_COUNT,
            -- Throughput: Completed orders
            SUM(CASE WHEN wo.WORK_ORDER_STATUS = 'COMPLETED' THEN wo.COMPLETED_QUANTITY ELSE 0 END) AS THROUGHPUT_UNITS,
            -- Count of orders
            COUNT(*) AS TOTAL_ORDERS,
            COUNT(CASE WHEN wo.WORK_ORDER_STATUS = 'COMPLETED' THEN 1 END) AS COMPLETED_ORDERS
        FROM ATOMIC.WORK_ORDER wo
        WHERE wo.IS_CURRENT_FLAG = TRUE
          AND wo.PLANNED_START_DATE IS NOT NULL
        GROUP BY 1, 2
    ),
    with_cycle_time AS (
        SELECT 
            df.*,
            -- Little's Law: Cycle Time = WIP / Throughput
            CASE 
                WHEN df.THROUGHPUT_UNITS > 0 THEN ROUND(df.WIP_COUNT * 480.0 / df.THROUGHPUT_UNITS, 2)  -- in minutes
                ELSE 999  -- Infinite cycle time if no throughput
            END AS CALCULATED_CYCLE_TIME_MIN,
            -- Rolling averages for trend detection
            AVG(df.WIP_COUNT) OVER (
                PARTITION BY df.PRODUCTION_LINE_ID 
                ORDER BY df.METRIC_DATE 
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS WIP_3DAY_AVG,
            AVG(df.THROUGHPUT_UNITS) OVER (
                PARTITION BY df.PRODUCTION_LINE_ID 
                ORDER BY df.METRIC_DATE 
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS THROUGHPUT_3DAY_AVG
        FROM daily_flow df
    )
    SELECT 
        ct.*,
        -- Divergence detection: WIP up but Throughput flat/down
        CASE 
            WHEN ct.WIP_COUNT > ct.WIP_3DAY_AVG * 1.2 
             AND ct.THROUGHPUT_UNITS <= ct.THROUGHPUT_3DAY_AVG 
            THEN TRUE
            ELSE FALSE
        END AS LITTLES_LAW_VIOLATION,
        -- Severity of divergence
        CASE 
            WHEN ct.WIP_COUNT > ct.WIP_3DAY_AVG * 1.5 
             AND ct.THROUGHPUT_UNITS < ct.THROUGHPUT_3DAY_AVG * 0.8 
            THEN 'CRITICAL'
            WHEN ct.WIP_COUNT > ct.WIP_3DAY_AVG * 1.2 
             AND ct.THROUGHPUT_UNITS <= ct.THROUGHPUT_3DAY_AVG 
            THEN 'WARNING'
            ELSE 'NORMAL'
        END AS DIVERGENCE_SEVERITY
    FROM with_cycle_time ct
    ORDER BY ct.METRIC_DATE DESC, ct.PRODUCTION_LINE_ID
    """,
    "Little's Law metrics for WIP/Throughput divergence detection",
    min_rows=0
)

# =============================================================================
# REGISTERED QUERIES - Material Flow (for Sankey Diagram)
# =============================================================================

MATERIAL_FLOW_SQL = register_query(
    "material_flow",
    """
    WITH flow_stages AS (
        -- Aggregate material movements by stage
        SELECT 
            mm.MOVEMENT_DATE AS FLOW_DATE,
            mm.FROM_LOCATION AS SOURCE_STAGE,
            mm.TO_LOCATION AS TARGET_STAGE,
            mm.MOVEMENT_TYPE,
            SUM(mm.QUANTITY) AS FLOW_QUANTITY,
            COUNT(*) AS MOVEMENT_COUNT
        FROM ATOMIC.MATERIAL_MOVEMENT mm
        WHERE mm.MOVEMENT_DATE >= DATEADD(day, -7, (SELECT MAX(MOVEMENT_DATE) FROM ATOMIC.MATERIAL_MOVEMENT))
        GROUP BY 1, 2, 3, 4
    ),
    stage_health AS (
        -- Get health status for each production line/stage
        SELECT 
            PRODUCTION_LINE_ID,
            AVG(OPE_PCT) AS AVG_OPE,
            SUM(STARVATION_DOWNTIME_MIN) AS STARVATION_MIN,
            SUM(AGV_FAILURE_COUNT) AS AGV_FAILURES,
            CASE 
                WHEN AVG(OPE_PCT) < 70 OR SUM(AGV_FAILURE_COUNT) > 5 THEN 'BLOCKED'
                WHEN AVG(OPE_PCT) < 80 THEN 'CONSTRAINED'
                ELSE 'HEALTHY'
            END AS STAGE_HEALTH
        FROM EV_OPE.OPE_DAILY_FACT
        WHERE METRIC_DATE >= DATEADD(day, -7, (SELECT MAX(METRIC_DATE) FROM EV_OPE.OPE_DAILY_FACT))
        GROUP BY PRODUCTION_LINE_ID
    )
    SELECT 
        fs.FLOW_DATE,
        fs.SOURCE_STAGE,
        fs.TARGET_STAGE,
        fs.MOVEMENT_TYPE,
        fs.FLOW_QUANTITY,
        fs.MOVEMENT_COUNT,
        COALESCE(sh.STAGE_HEALTH, 'UNKNOWN') AS TARGET_HEALTH,
        COALESCE(sh.STARVATION_MIN, 0) AS TARGET_STARVATION_MIN,
        COALESCE(sh.AGV_FAILURES, 0) AS TARGET_AGV_FAILURES
    FROM flow_stages fs
    LEFT JOIN stage_health sh ON fs.TARGET_STAGE = sh.PRODUCTION_LINE_ID
    ORDER BY fs.FLOW_QUANTITY DESC
    """,
    "Material flow between stages for Sankey diagram",
    min_rows=0
)

# Simplified flow summary for Sankey
SANKEY_FLOW_SUMMARY_SQL = register_query(
    "sankey_flow_summary",
    """
    WITH line_metrics AS (
        SELECT 
            PRODUCTION_LINE_ID,
            SUM(ACTUAL_QUANTITY) AS TOTAL_OUTPUT,
            SUM(PLANNED_QUANTITY) AS TOTAL_PLANNED,
            AVG(OPE_PCT) AS AVG_OPE,
            SUM(STARVATION_DOWNTIME_MIN) AS TOTAL_STARVATION,
            SUM(AGV_FAILURE_COUNT) AS TOTAL_AGV_FAILURES
        FROM EV_OPE.OPE_DAILY_FACT
        WHERE METRIC_DATE >= DATEADD(day, -7, (SELECT MAX(METRIC_DATE) FROM EV_OPE.OPE_DAILY_FACT))
        GROUP BY PRODUCTION_LINE_ID
    )
    SELECT 
        'RAW_MATERIALS' AS SOURCE_NODE,
        PRODUCTION_LINE_ID AS TARGET_NODE,
        TOTAL_PLANNED AS FLOW_VALUE,
        AVG_OPE,
        TOTAL_STARVATION,
        TOTAL_AGV_FAILURES,
        CASE 
            WHEN AVG_OPE < 70 THEN 'CRITICAL'
            WHEN AVG_OPE < 80 THEN 'WARNING'
            ELSE 'HEALTHY'
        END AS FLOW_STATUS,
        1 AS STAGE_ORDER
    FROM line_metrics
    
    UNION ALL
    
    SELECT 
        PRODUCTION_LINE_ID AS SOURCE_NODE,
        'AGV_TRANSFER' AS TARGET_NODE,
        TOTAL_OUTPUT AS FLOW_VALUE,
        AVG_OPE,
        TOTAL_STARVATION,
        TOTAL_AGV_FAILURES,
        CASE 
            WHEN TOTAL_AGV_FAILURES > 5 THEN 'CRITICAL'
            WHEN TOTAL_AGV_FAILURES > 2 THEN 'WARNING'
            ELSE 'HEALTHY'
        END AS FLOW_STATUS,
        2 AS STAGE_ORDER
    FROM line_metrics
    
    UNION ALL
    
    SELECT 
        'AGV_TRANSFER' AS SOURCE_NODE,
        'QC_INSPECTION' AS TARGET_NODE,
        SUM(TOTAL_OUTPUT) * 0.95 AS FLOW_VALUE,  -- 5% held for QC
        AVG(AVG_OPE) AS AVG_OPE,
        SUM(TOTAL_STARVATION) AS TOTAL_STARVATION,
        SUM(TOTAL_AGV_FAILURES) AS TOTAL_AGV_FAILURES,
        'HEALTHY' AS FLOW_STATUS,
        3 AS STAGE_ORDER
    FROM line_metrics
    
    UNION ALL
    
    SELECT 
        'QC_INSPECTION' AS SOURCE_NODE,
        'FINISHED_GOODS' AS TARGET_NODE,
        SUM(TOTAL_OUTPUT) * 0.92 AS FLOW_VALUE,  -- 3% rework
        AVG(AVG_OPE) AS AVG_OPE,
        0 AS TOTAL_STARVATION,
        0 AS TOTAL_AGV_FAILURES,
        'HEALTHY' AS FLOW_STATUS,
        4 AS STAGE_ORDER
    FROM line_metrics
    
    UNION ALL
    
    -- Rework loop (Ghost Inventory)
    SELECT 
        'QC_INSPECTION' AS SOURCE_NODE,
        'REWORK_QUEUE' AS TARGET_NODE,
        SUM(TOTAL_OUTPUT) * 0.03 AS FLOW_VALUE,  -- 3% rework
        AVG(AVG_OPE) AS AVG_OPE,
        0 AS TOTAL_STARVATION,
        0 AS TOTAL_AGV_FAILURES,
        'WARNING' AS FLOW_STATUS,
        5 AS STAGE_ORDER
    FROM line_metrics
    
    ORDER BY STAGE_ORDER, SOURCE_NODE
    """,
    "Simplified flow summary for Sankey diagram visualization",
    min_rows=1
)

