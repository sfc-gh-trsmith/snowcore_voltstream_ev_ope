#!/usr/bin/env python3
"""
Synthetic Data Generator for VoltStream EV OPE Demo
=====================================================

Generates causally-linked synthetic data following the DRD specification:
- Months 1-2 (Baseline): Steady production, normal humidity (45%), low dust, 99.9% AGV reliability
- Month 3 Week 2 (Crisis): Humidity drops → Dust spikes → AGV-ERR-99 → Line starvation → OPE drops

Usage:
    # List available datasets
    python3 utils/generate_synthetic_data.py --list
    
    # Generate a specific dataset
    python3 utils/generate_synthetic_data.py env_sensors
    python3 utils/generate_synthetic_data.py agv_telemetry
    
    # Force overwrite existing file
    python3 utils/generate_synthetic_data.py env_sensors --force
    
    # Generate all datasets (run once per dataset)
    for ds in env_sensors agv_telemetry equipment_states prod_orders \\
              material_documents ope_daily_fact agv_failure_analysis \\
              dim_asset dim_product; do
        python3 utils/generate_synthetic_data.py $ds
    done
    
    # Validate all joins after generation
    python3 utils/generate_synthetic_data.py --validate

The generated data tells this story:
1. OPE drops from 85% to 60% on "Demo Day"
2. ML model finds perfect correlation: Humidity ↓ → Dust ↑ → Failures ↑
3. Search finds AGV-ERR-99 manual explaining "Dust on LiDAR lens"
"""

import argparse
import os
import random
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable, Tuple
import uuid
import math

import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Date range: 3 months of data
START_DATE = datetime(2024, 10, 1)
END_DATE = datetime(2024, 12, 31)

# Crisis period: Month 3, Week 2 (Dec 9-11, 2024)
CRISIS_START = datetime(2024, 12, 9)
CRISIS_END = datetime(2024, 12, 11, 23, 59, 59)

# Production lines
PRODUCTION_LINES = ['LINE_1', 'LINE_2', 'LINE_3', 'LINE_4', 'LINE_5']

# AGVs per zone
AGVS = [f'AGV_{i:03d}' for i in range(1, 21)]  # 20 AGVs

# Zones
ZONES = ['ZONE_A', 'ZONE_B', 'ZONE_C', 'ZONE_D']

# Shifts
SHIFTS = ['SHIFT_1', 'SHIFT_2', 'SHIFT_3']

# Products (Battery hierarchy)
PRODUCTS = [
    {'sku': 'BP-100', 'name': 'Battery Pack 100kWh', 'category': 'BATTERY_PACK'},
    {'sku': 'BP-150', 'name': 'Battery Pack 150kWh', 'category': 'BATTERY_PACK'},
    {'sku': 'MOD-20', 'name': 'Battery Module 20kWh', 'category': 'MODULE'},
    {'sku': 'MOD-25', 'name': 'Battery Module 25kWh', 'category': 'MODULE'},
    {'sku': 'CELL-2170', 'name': '2170 Cell', 'category': 'CELL'},
    {'sku': 'CELL-4680', 'name': '4680 Cell', 'category': 'CELL'},
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_crisis_period(timestamp: datetime) -> bool:
    """Check if timestamp falls within the crisis period."""
    return CRISIS_START <= timestamp <= CRISIS_END


def get_shift_for_hour(hour: int) -> str:
    """Get shift ID based on hour of day."""
    if 6 <= hour < 14:
        return 'SHIFT_1'
    elif 14 <= hour < 22:
        return 'SHIFT_2'
    else:
        return 'SHIFT_3'


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def log_progress(count: int, interval: int = 10000) -> None:
    """Log progress every `interval` rows."""
    if count > 0 and count % interval == 0:
        print(f"    ... {count:,} rows generated", flush=True)


# =============================================================================
# ENVIRONMENTAL DATA GENERATION
# =============================================================================

def generate_env_sensor_data() -> pd.DataFrame:
    """
    Generate environmental sensor readings at 5-minute intervals.
    
    Baseline: Humidity ~45%, Dust ~10 µg/m³
    Crisis: Humidity drops to 25%, Dust spikes to 35 µg/m³
    """
    records = []
    row_count = 0
    
    current_time = START_DATE
    reading_interval = timedelta(minutes=5)
    
    sensor_types = ['HUMIDITY', 'PM25', 'TEMPERATURE']
    
    while current_time <= END_DATE:
        is_crisis = is_crisis_period(current_time)
        
        for zone in ZONES:
            for line in PRODUCTION_LINES:
                for sensor_type in sensor_types:
                    sensor_id = f"{zone}_{line}_{sensor_type}_01"
                    
                    if sensor_type == 'HUMIDITY':
                        if is_crisis:
                            # Crisis: Low humidity (25% mean)
                            value = max(15, min(40, np.random.normal(25, 3)))
                        else:
                            # Normal: ~45% humidity
                            value = max(30, min(60, np.random.normal(45, 5)))
                        unit = '%'
                        
                    elif sensor_type == 'PM25':
                        if is_crisis:
                            # Crisis: High dust, inversely correlated with humidity
                            # Dust = (50 - Humidity) + noise
                            base_dust = 50 - 25 + np.random.normal(10, 5)
                            value = max(5, min(50, base_dust))
                        else:
                            # Normal: Low dust (~10 µg/m³)
                            value = max(2, min(20, np.random.normal(10, 2)))
                        unit = 'µg/m³'
                        
                    else:  # TEMPERATURE
                        # Slight variation, not crisis-linked
                        value = np.random.normal(22, 1.5)
                        unit = '°C'
                    
                    records.append({
                        'READING_ID': generate_uuid(),
                        'SENSOR_ID': sensor_id,
                        'SENSOR_TYPE': sensor_type,
                        'ZONE_ID': zone,
                        'PRODUCTION_LINE_ID': line,
                        'READING_TIMESTAMP': current_time.isoformat(),
                        'METRIC_NAME': sensor_type,
                        'METRIC_VALUE': round(value, 3),
                        'UNIT_OF_MEASURE': unit,
                        'QUALITY_FLAG': 'GOOD'
                    })
                    row_count += 1
                    log_progress(row_count)
        
        current_time += reading_interval
    
    return pd.DataFrame(records)


# =============================================================================
# AGV TELEMETRY GENERATION
# =============================================================================

def generate_agv_telemetry() -> pd.DataFrame:
    """
    Generate AGV telemetry data with error codes.
    
    Baseline: 99.9% reliability, rare AGV-ERR-99
    Crisis: 15% error probability when dust > 30
    """
    records = []
    row_count = 0
    
    current_time = START_DATE
    reading_interval = timedelta(minutes=1)  # 1-minute readings per AGV
    
    while current_time <= END_DATE:
        is_crisis = is_crisis_period(current_time)
        
        for agv_id in AGVS:
            # Simulate AGV position (grid-based factory floor)
            x = random.uniform(0, 500)
            y = random.uniform(0, 300)
            zone = random.choice(ZONES)
            route = f"ROUTE_{random.randint(1, 10):02d}"
            velocity = random.uniform(0.5, 2.0) if random.random() > 0.1 else 0  # 90% moving
            battery = random.uniform(20, 100)
            
            # Error logic
            error_code = None
            error_severity = None
            error_message = None
            
            if is_crisis:
                # During crisis: 15% chance of AGV-ERR-99 (dust on sensor)
                if random.random() < 0.15:
                    error_code = 'AGV-ERR-99'
                    error_severity = 'ERROR'
                    error_message = 'Optical sensor obscured - reduced visibility detected'
            else:
                # Normal operation: 0.1% chance of random error
                if random.random() < 0.001:
                    error_code = random.choice(['AGV-ERR-01', 'AGV-ERR-42', 'AGV-ERR-55'])
                    error_severity = 'WARNING'
                    error_message = 'Minor operational issue detected'
            
            records.append({
                'MSG_ID': generate_uuid(),
                'AGV_ID': agv_id,
                'EVENT_TIMESTAMP': current_time.isoformat(),
                'X_COORD': round(x, 3),
                'Y_COORD': round(y, 3),
                'Z_COORD': 0,
                'ZONE_ID': zone,
                'ROUTE_SEGMENT': route,
                'VELOCITY': round(velocity, 3),
                'BATTERY_LEVEL': round(battery, 2),
                'PAYLOAD_ID': f'BATCH_{random.randint(1000, 9999)}' if random.random() > 0.3 else None,
                'ERROR_CODE': error_code,
                'ERROR_SEVERITY': error_severity,
                'ERROR_MESSAGE': error_message,
                '_CDC_OPERATION': 'INSERT',
                '_CDC_TIMESTAMP': current_time.isoformat(),
                '_CDC_SEQUENCE': int(current_time.timestamp() * 1000),
                '_CDC_SOURCE_SYSTEM': 'SIEMENS_MES'
            })
            row_count += 1
            log_progress(row_count)
        
        current_time += reading_interval
    
    return pd.DataFrame(records)


# =============================================================================
# EQUIPMENT STATE LOG GENERATION
# =============================================================================

def generate_equipment_states() -> pd.DataFrame:
    """
    Generate equipment state transitions.
    
    Crisis causes STARVATION events due to AGV failures.
    """
    records = []
    
    current_date = START_DATE.date()
    
    while current_date <= END_DATE.date():
        current_datetime = datetime.combine(current_date, datetime.min.time())
        is_crisis = is_crisis_period(current_datetime)
        
        for line in PRODUCTION_LINES:
            for hour in range(24):
                event_time = current_datetime + timedelta(hours=hour)
                shift_id = get_shift_for_hour(hour)
                
                # Determine state based on crisis
                if is_crisis and line == 'LINE_4':  # LINE_4 is most affected
                    # 40% chance of starvation during crisis
                    if random.random() < 0.4:
                        state_code = 2  # IDLE
                        state_name = 'IDLE'
                        reason_code = 'STARVATION'
                        reason_desc = 'Waiting for material - AGV delivery delayed'
                        duration = random.randint(600, 1800)  # 10-30 min
                    else:
                        state_code = 1
                        state_name = 'RUNNING'
                        reason_code = None
                        reason_desc = None
                        duration = 3600
                elif is_crisis:
                    # Other lines: 20% starvation chance during crisis
                    if random.random() < 0.2:
                        state_code = 2
                        state_name = 'IDLE'
                        reason_code = 'STARVATION'
                        reason_desc = 'Waiting for material'
                        duration = random.randint(300, 900)  # 5-15 min
                    else:
                        state_code = 1
                        state_name = 'RUNNING'
                        reason_code = None
                        reason_desc = None
                        duration = 3600
                else:
                    # Normal operation: 95% running, 5% minor issues
                    if random.random() < 0.95:
                        state_code = 1
                        state_name = 'RUNNING'
                        reason_code = None
                        reason_desc = None
                        duration = 3600
                    else:
                        state_code = random.choice([2, 3, 4])
                        state_name = ['IDLE', 'FAULT', 'SETUP'][state_code - 2]
                        reason_code = random.choice(['CHANGEOVER', 'MINOR_STOP', 'ADJUSTMENT'])
                        reason_desc = 'Planned minor stop'
                        duration = random.randint(60, 300)
                
                records.append({
                    'EVENT_ID': generate_uuid(),
                    'ASSET_ID': f'{line}_MAIN',
                    'PRODUCTION_LINE_ID': line,
                    'EVENT_TIMESTAMP': event_time.isoformat(),
                    'STATE_CODE': state_code,
                    'STATE_NAME': state_name,
                    'REASON_CODE': reason_code,
                    'REASON_DESCRIPTION': reason_desc,
                    'DURATION_SECONDS': duration,
                    'SHIFT_ID': shift_id,
                    'OPERATOR_ID': f'OP_{random.randint(100, 999)}',
                    '_CDC_OPERATION': 'INSERT',
                    '_CDC_TIMESTAMP': event_time.isoformat(),
                    '_CDC_SEQUENCE': int(event_time.timestamp() * 1000),
                    '_CDC_SOURCE_SYSTEM': 'SIEMENS_MES'
                })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(records)


# =============================================================================
# PRODUCTION ORDERS
# =============================================================================

def generate_prod_orders() -> pd.DataFrame:
    """Generate production order headers from SAP."""
    records = []
    
    order_id = 1000000
    current_date = START_DATE.date()
    
    while current_date <= END_DATE.date():
        for line in PRODUCTION_LINES:
            for shift in SHIFTS:
                product = random.choice(PRODUCTS)
                target_qty = random.randint(50, 200)
                
                # Determine actual completion based on crisis
                current_datetime = datetime.combine(current_date, datetime.min.time())
                is_crisis = is_crisis_period(current_datetime)
                
                if is_crisis and line == 'LINE_4':
                    # Crisis: LINE_4 only achieves 60-70% of target
                    completion_rate = random.uniform(0.6, 0.7)
                elif is_crisis:
                    # Crisis: other lines 80-90%
                    completion_rate = random.uniform(0.8, 0.9)
                else:
                    # Normal: 95-100% completion
                    completion_rate = random.uniform(0.95, 1.0)
                
                actual_qty = int(target_qty * completion_rate)
                
                shift_start_hour = {'SHIFT_1': 6, 'SHIFT_2': 14, 'SHIFT_3': 22}[shift]
                sched_start = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=shift_start_hour)
                sched_end = sched_start + timedelta(hours=8)
                
                records.append({
                    'ORDER_ID': f'PO{order_id}',
                    'ORDER_TYPE': 'PP01',
                    'SKU': product['sku'],
                    'TARGET_QTY': target_qty,
                    'UNIT_OF_MEASURE': 'EA',
                    'SCHED_START': sched_start.isoformat(),
                    'SCHED_END': sched_end.isoformat(),
                    'ACTUAL_START': sched_start.isoformat(),
                    'ACTUAL_END': sched_end.isoformat() if completion_rate > 0.9 else None,
                    'PRODUCTION_LINE_ID': line,
                    'WORK_CENTER_ID': f'WC_{line}',
                    'ORDER_STATUS': 'COMPLETED' if completion_rate > 0.9 else 'STARTED',
                    'PRIORITY': random.randint(1, 5),
                    '_CDC_OPERATION': 'INSERT',
                    '_CDC_TIMESTAMP': sched_start.isoformat(),
                    '_CDC_SEQUENCE': order_id,
                    '_CDC_SOURCE_SYSTEM': 'SAP_ERP'
                })
                
                order_id += 1
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(records)


# =============================================================================
# MATERIAL DOCUMENTS
# =============================================================================

def generate_material_documents() -> pd.DataFrame:
    """Generate inventory movements from SAP."""
    records = []
    
    doc_id = 5000000
    current_date = START_DATE.date()
    
    while current_date <= END_DATE.date():
        current_datetime = datetime.combine(current_date, datetime.min.time())
        is_crisis = is_crisis_period(current_datetime)
        
        # Generate multiple material movements per day
        for _ in range(random.randint(50, 100)):
            product = random.choice(PRODUCTS)
            batch_id = f'BATCH_{random.randint(10000, 99999)}'
            
            # During crisis, more material goes to QUALITY_INSPECTION
            if is_crisis and random.random() < 0.3:
                stock_type = 'QUALITY_INSPECTION'
                mvmt_type = '321'  # Transfer to QI
            else:
                stock_type = 'UNRESTRICTED'
                mvmt_type = random.choice(['101', '261', '601'])
            
            posting_time = current_datetime + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            records.append({
                'MAT_DOC_ID': str(doc_id),
                'POSTING_DATE': current_date.isoformat(),
                'SKU': product['sku'],
                'MVMT_TYPE': mvmt_type,
                'STOCK_TYPE': stock_type,
                'BATCH_ID': batch_id,
                'PLANT_ID': 'P001',
                'STORAGE_LOCATION': random.choice(['SL01', 'SL02', 'SL03']),
                'QUANTITY': random.randint(10, 500),
                'UNIT_OF_MEASURE': 'EA',
                '_CDC_OPERATION': 'INSERT',
                '_CDC_TIMESTAMP': posting_time.isoformat(),
                '_CDC_SEQUENCE': doc_id,
                '_CDC_SOURCE_SYSTEM': 'SAP_ERP'
            })
            
            doc_id += 1
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(records)


# =============================================================================
# OPE DAILY FACT (Pre-aggregated)
# =============================================================================

def generate_ope_daily_fact() -> pd.DataFrame:
    """
    Generate pre-aggregated OPE metrics.
    
    Key story: OEE stays high (>90%) but OPE drops to 60% during crisis.
    """
    records = []
    
    current_date = START_DATE.date()
    
    while current_date <= END_DATE.date():
        current_datetime = datetime.combine(current_date, datetime.min.time())
        is_crisis = is_crisis_period(current_datetime)
        
        for line in PRODUCTION_LINES:
            for shift in SHIFTS:
                # Equipment metrics (OEE components)
                availability = random.uniform(92, 98)
                performance = random.uniform(90, 98)
                quality = random.uniform(97, 99.5)
                oee = (availability * performance * quality) / 10000
                
                # Process metrics (OPE components)
                if is_crisis and line == 'LINE_4':
                    # Crisis on LINE_4: OPE drops significantly
                    value_added_pct = random.uniform(55, 65)
                    material_efficiency = random.uniform(60, 70)
                    flow_efficiency = random.uniform(55, 65)
                    starvation_min = random.randint(60, 120)
                    agv_failures = random.randint(15, 30)
                    agv_err_99 = random.randint(10, 25)
                    humidity = random.uniform(22, 28)
                    dust = random.uniform(30, 40)
                elif is_crisis:
                    # Crisis on other lines: moderate impact
                    value_added_pct = random.uniform(70, 80)
                    material_efficiency = random.uniform(75, 85)
                    flow_efficiency = random.uniform(70, 80)
                    starvation_min = random.randint(20, 45)
                    agv_failures = random.randint(5, 15)
                    agv_err_99 = random.randint(3, 10)
                    humidity = random.uniform(24, 30)
                    dust = random.uniform(25, 35)
                else:
                    # Normal operation
                    value_added_pct = random.uniform(82, 90)
                    material_efficiency = random.uniform(88, 95)
                    flow_efficiency = random.uniform(85, 92)
                    starvation_min = random.randint(0, 15)
                    agv_failures = random.randint(0, 2)
                    agv_err_99 = 0 if random.random() > 0.05 else 1
                    humidity = random.uniform(42, 48)
                    dust = random.uniform(8, 14)
                
                ope = (value_added_pct * material_efficiency * flow_efficiency) / 10000
                
                planned_qty = random.randint(100, 200)
                actual_qty = int(planned_qty * ope / 100 * random.uniform(0.95, 1.05))
                scrap_qty = max(0, int(actual_qty * (100 - quality) / 100))
                
                records.append({
                    'METRIC_DATE': current_date.isoformat(),
                    'PRODUCTION_LINE_ID': line,
                    'SHIFT_ID': shift,
                    'OEE_AVAILABILITY_PCT': round(availability, 2),
                    'OEE_PERFORMANCE_PCT': round(performance, 2),
                    'OEE_QUALITY_PCT': round(quality, 2),
                    'OEE_PCT': round(oee * 100, 2),
                    'OPE_VALUE_ADDED_TIME_PCT': round(value_added_pct, 2),
                    'OPE_MATERIAL_EFFICIENCY_PCT': round(material_efficiency, 2),
                    'OPE_FLOW_EFFICIENCY_PCT': round(flow_efficiency, 2),
                    'OPE_PCT': round(ope * 100, 2),
                    'PLANNED_QUANTITY': planned_qty,
                    'ACTUAL_QUANTITY': actual_qty,
                    'SCRAP_QUANTITY': scrap_qty,
                    'YIELD_PCT': round(quality, 2),
                    'PLANNED_PRODUCTION_TIME_MIN': 480,
                    'ACTUAL_PRODUCTION_TIME_MIN': int(480 * availability / 100),
                    'DOWNTIME_MIN': int(480 * (100 - availability) / 100),
                    'STARVATION_DOWNTIME_MIN': starvation_min,
                    'BLOCKAGE_DOWNTIME_MIN': random.randint(0, 10),
                    'BREAKDOWN_DOWNTIME_MIN': random.randint(0, 20),
                    'CHANGEOVER_MIN': random.randint(15, 30),
                    'AVG_CYCLE_TIME_SEC': random.uniform(45, 60),
                    'THEORETICAL_CYCLE_TIME_SEC': 45,
                    'AVG_HUMIDITY': round(humidity, 2),
                    'AVG_DUST_PM25': round(dust, 3),
                    'AVG_TEMPERATURE': round(random.uniform(21, 23), 2),
                    'AGV_FAILURE_COUNT': agv_failures,
                    'AGV_ERR_99_COUNT': agv_err_99
                })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(records)


# =============================================================================
# AGV FAILURE ANALYSIS (ML Training Data)
# =============================================================================

def generate_agv_failure_analysis() -> pd.DataFrame:
    """
    Generate hourly AGV failure analysis data for ML.
    
    This table shows the correlation: Low Humidity → High Dust → AGV Failures
    """
    records = []
    
    current_date = START_DATE.date()
    
    while current_date <= END_DATE.date():
        current_datetime = datetime.combine(current_date, datetime.min.time())
        
        for hour in range(24):
            event_time = current_datetime + timedelta(hours=hour)
            is_crisis = is_crisis_period(event_time)
            shift = get_shift_for_hour(hour)
            
            for zone in ZONES:
                # Environmental conditions
                if is_crisis:
                    humidity = np.random.normal(25, 3)
                    humidity = max(15, min(40, humidity))
                    # Dust inversely correlated with humidity
                    dust = (50 - humidity) + np.random.normal(5, 3)
                    dust = max(5, min(50, dust))
                else:
                    humidity = np.random.normal(45, 5)
                    humidity = max(30, min(60, humidity))
                    dust = np.random.normal(10, 2)
                    dust = max(2, min(20, dust))
                
                # Categorize
                if humidity < 35:
                    humidity_cat = 'LOW'
                elif humidity > 55:
                    humidity_cat = 'HIGH'
                else:
                    humidity_cat = 'NORMAL'
                
                if dust > 25:
                    dust_cat = 'HIGH'
                elif dust > 15:
                    dust_cat = 'MODERATE'
                else:
                    dust_cat = 'LOW'
                
                # AGV operations and failures
                total_ops = random.randint(80, 150)
                
                # Failure rate depends on dust level
                if dust > 30:
                    failure_rate = random.uniform(0.10, 0.20)
                elif dust > 25:
                    failure_rate = random.uniform(0.05, 0.10)
                elif dust > 20:
                    failure_rate = random.uniform(0.02, 0.05)
                else:
                    failure_rate = random.uniform(0.001, 0.01)
                
                failed_ops = int(total_ops * failure_rate)
                successful_ops = total_ops - failed_ops
                
                # Error breakdown
                total_errors = failed_ops
                if is_crisis:
                    # Most errors are AGV-ERR-99 during crisis
                    err_99 = int(total_errors * 0.7)
                    err_01 = int(total_errors * 0.1)
                    err_42 = int(total_errors * 0.1)
                    err_55 = int(total_errors * 0.05)
                else:
                    # Random distribution during normal ops
                    err_99 = int(total_errors * 0.2)
                    err_01 = int(total_errors * 0.3)
                    err_42 = int(total_errors * 0.3)
                    err_55 = int(total_errors * 0.1)
                
                other_errors = total_errors - err_99 - err_01 - err_42 - err_55
                
                # Impact on production
                starvation_events = err_99  # Each ERR-99 causes a starvation event
                starvation_duration = starvation_events * random.randint(10, 20)
                
                records.append({
                    'ANALYSIS_DATE': current_date.isoformat(),
                    'ANALYSIS_HOUR': hour,
                    'SHIFT_ID': shift,
                    'ZONE_ID': zone,
                    'AVG_HUMIDITY': round(humidity, 3),
                    'MIN_HUMIDITY': round(humidity - random.uniform(2, 5), 3),
                    'MAX_HUMIDITY': round(humidity + random.uniform(2, 5), 3),
                    'AVG_DUST_PM25': round(dust, 3),
                    'MAX_DUST_PM25': round(dust + random.uniform(3, 8), 3),
                    'AVG_TEMPERATURE': round(np.random.normal(22, 1), 3),
                    'HUMIDITY_CATEGORY': humidity_cat,
                    'DUST_CATEGORY': dust_cat,
                    'TOTAL_AGV_OPERATIONS': total_ops,
                    'SUCCESSFUL_OPERATIONS': successful_ops,
                    'FAILED_OPERATIONS': failed_ops,
                    'FAILURE_RATE': round(failure_rate, 6),
                    'TOTAL_ERRORS': total_errors,
                    'AGV_ERR_99_COUNT': err_99,
                    'AGV_ERR_01_COUNT': err_01,
                    'AGV_ERR_42_COUNT': err_42,
                    'AGV_ERR_55_COUNT': err_55,
                    'OTHER_ERROR_COUNT': max(0, other_errors),
                    'IS_HIGH_FAILURE_PERIOD': failure_rate > 0.05,
                    'FAILURE_PROBABILITY': round(failure_rate, 6),
                    'STARVATION_EVENTS_CAUSED': starvation_events,
                    'STARVATION_DURATION_MIN': starvation_duration
                })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(records)


# =============================================================================
# DIMENSION DATA
# =============================================================================

def generate_dim_asset() -> pd.DataFrame:
    """Generate asset dimension data."""
    records = []
    asset_id = 1
    
    # Production lines
    for line in PRODUCTION_LINES:
        records.append({
            'ASSET_ID': asset_id,
            'ASSET_CODE': line,
            'ASSET_NAME': f'Production Line {line[-1]}',
            'ASSET_DESCRIPTION': f'Battery pack assembly line {line[-1]}',
            'ASSET_TYPE': 'PRODUCTION_LINE',
            'ASSET_CLASS': 'ASSEMBLY',
            'ASSET_STATUS': 'ACTIVE',
            'PRODUCTION_LINE_ID': line,
            'ZONE_ID': f'ZONE_{chr(64 + int(line[-1]))}',
            'MANUFACTURER': 'Siemens',
            'MODEL_NUMBER': 'SIMATIC-5000',
            'MES_ASSET_ID': f'{line}_MAIN',
            'ERP_WORK_CENTER': f'WC_{line}'
        })
        asset_id += 1
    
    # AGVs
    for agv in AGVS:
        records.append({
            'ASSET_ID': asset_id,
            'ASSET_CODE': agv,
            'ASSET_NAME': f'Automated Guided Vehicle {agv[-3:]}',
            'ASSET_DESCRIPTION': 'Material transport AGV with LiDAR navigation',
            'ASSET_TYPE': 'AGV',
            'ASSET_CLASS': 'TRANSPORT',
            'ASSET_STATUS': 'ACTIVE',
            'ZONE_ID': random.choice(ZONES),
            'MANUFACTURER': 'KUKA',
            'MODEL_NUMBER': 'KMR-iiwa',
            'MES_ASSET_ID': agv,
            'IOT_DEVICE_ID': f'IOT_{agv}'
        })
        asset_id += 1
    
    return pd.DataFrame(records)


def generate_dim_product() -> pd.DataFrame:
    """Generate product dimension data."""
    records = []
    
    for i, product in enumerate(PRODUCTS, 1):
        records.append({
            'PRODUCT_ID': i,
            'SKU': product['sku'],
            'PRODUCT_NAME': product['name'],
            'PRODUCT_DESCRIPTION': f"High-performance {product['name'].lower()} for electric vehicles",
            'PRODUCT_CATEGORY': product['category'],
            'PRODUCT_FAMILY': 'EV_BATTERY',
            'PRODUCT_LINE': 'VOLTSTREAM',
            'UNIT_OF_MEASURE': 'EA',
            'STANDARD_COST': random.uniform(100, 5000),
            'STANDARD_CYCLE_TIME_SEC': random.randint(30, 120)
        })
    
    return pd.DataFrame(records)


# =============================================================================
# DATASET REGISTRY
# =============================================================================

# Registry of all datasets with their generators and expected row counts
# Row count estimates based on: 92 days (Oct 1 - Dec 31, 2024)
DATASETS: Dict[str, Dict[str, Any]] = {
    'env_sensors': {
        'filename': 'env_sensors.csv',
        'generator': generate_env_sensor_data,
        'description': 'Environmental sensor readings (humidity, dust, temperature)',
        'expected_min_rows': 1_500_000,  # ~1.57M rows (5min intervals, 4 zones, 5 lines, 3 sensors)
    },
    'agv_telemetry': {
        'filename': 'agv_telemetry.csv',
        'generator': generate_agv_telemetry,
        'description': 'AGV telemetry with error codes',
        'expected_min_rows': 2_600_000,  # ~2.65M rows (1min intervals, 20 AGVs)
    },
    'equipment_states': {
        'filename': 'equipment_states.csv',
        'generator': generate_equipment_states,
        'description': 'Equipment state transitions',
        'expected_min_rows': 10_000,  # ~11K rows (hourly, 5 lines)
    },
    'prod_orders': {
        'filename': 'prod_orders.csv',
        'generator': generate_prod_orders,
        'description': 'Production orders from SAP',
        'expected_min_rows': 1_000,  # ~1.4K rows (daily, 5 lines, 3 shifts)
    },
    'material_documents': {
        'filename': 'material_documents.csv',
        'generator': generate_material_documents,
        'description': 'Material movements from SAP',
        'expected_min_rows': 5_000,  # ~7K rows (50-100 per day)
    },
    'ope_daily_fact': {
        'filename': 'ope_daily_fact.csv',
        'generator': generate_ope_daily_fact,
        'description': 'Pre-aggregated OPE daily metrics',
        'expected_min_rows': 1_000,  # ~1.4K rows (daily, 5 lines, 3 shifts)
    },
    'agv_failure_analysis': {
        'filename': 'agv_failure_analysis.csv',
        'generator': generate_agv_failure_analysis,
        'description': 'Hourly AGV failure analysis for ML',
        'expected_min_rows': 8_000,  # ~8.8K rows (hourly, 4 zones)
    },
    'dim_asset': {
        'filename': 'dim_asset.csv',
        'generator': generate_dim_asset,
        'description': 'Asset dimension table',
        'expected_min_rows': 20,  # 25 rows (5 lines + 20 AGVs)
    },
    'dim_product': {
        'filename': 'dim_product.csv',
        'generator': generate_dim_product,
        'description': 'Product dimension table',
        'expected_min_rows': 5,  # 6 rows (6 products)
    },
}


# =============================================================================
# HELPER FUNCTIONS FOR GENERATION
# =============================================================================

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def validate_dataframe(df: pd.DataFrame, dataset_name: str, expected_min_rows: int) -> Tuple[bool, List[str]]:
    """Validate generated DataFrame and return (is_valid, errors)."""
    errors = []
    
    # Check row count
    if len(df) < expected_min_rows:
        errors.append(f"Row count {len(df):,} below minimum {expected_min_rows:,}")
    
    # Check for empty DataFrame
    if len(df) == 0:
        errors.append("DataFrame is empty")
        return False, errors
    
    # Check for null columns (all values null)
    null_cols = [col for col in df.columns if df[col].isna().all()]
    if null_cols:
        errors.append(f"Columns with all null values: {null_cols}")
    
    # Check for duplicate columns
    if len(df.columns) != len(set(df.columns)):
        errors.append("Duplicate column names detected")
    
    return len(errors) == 0, errors


def validate_joins(output_dir: str) -> bool:
    """
    Validate that all expected joins between datasets work correctly.
    
    Checks referential integrity between:
    - Fact tables and dimension tables
    - Foreign key columns and reference lists
    
    Returns True if all validations pass, False otherwise.
    """
    print("\n" + "=" * 60)
    print("Validating Dataset Joins")
    print("=" * 60)
    
    errors = []
    warnings = []
    checks_passed = 0
    
    # Load all datasets
    datasets = {}
    missing_files = []
    
    for name, config in DATASETS.items():
        filepath = os.path.join(output_dir, config['filename'])
        if os.path.exists(filepath):
            try:
                datasets[name] = pd.read_csv(filepath)
                print(f"  Loaded {name}: {len(datasets[name]):,} rows")
            except Exception as e:
                errors.append(f"Failed to load {name}: {e}")
        else:
            missing_files.append(name)
    
    if missing_files:
        print(f"\n  ⚠ Missing files: {', '.join(missing_files)}")
        print("    Run generation for missing datasets before validation.")
    
    if not datasets:
        print("\n  ERROR: No datasets loaded. Cannot validate.")
        return False
    
    print()
    
    # Define validation checks
    # Format: (source_dataset, source_column, target_dataset_or_list, target_column_or_None, description)
    join_checks = [
        # SKU joins to dim_product
        ('prod_orders', 'SKU', 'dim_product', 'SKU', 'Production orders → Products'),
        ('material_documents', 'SKU', 'dim_product', 'SKU', 'Material documents → Products'),
        
        # PRODUCTION_LINE_ID validation against constant
        ('prod_orders', 'PRODUCTION_LINE_ID', PRODUCTION_LINES, None, 'Production orders → Production lines'),
        ('equipment_states', 'PRODUCTION_LINE_ID', PRODUCTION_LINES, None, 'Equipment states → Production lines'),
        ('ope_daily_fact', 'PRODUCTION_LINE_ID', PRODUCTION_LINES, None, 'OPE daily fact → Production lines'),
        ('env_sensors', 'PRODUCTION_LINE_ID', PRODUCTION_LINES, None, 'Env sensors → Production lines'),
        
        # ZONE_ID validation against constant
        ('env_sensors', 'ZONE_ID', ZONES, None, 'Env sensors → Zones'),
        ('agv_telemetry', 'ZONE_ID', ZONES, None, 'AGV telemetry → Zones'),
        ('agv_failure_analysis', 'ZONE_ID', ZONES, None, 'AGV failure analysis → Zones'),
        
        # SHIFT_ID validation against constant
        ('ope_daily_fact', 'SHIFT_ID', SHIFTS, None, 'OPE daily fact → Shifts'),
        ('equipment_states', 'SHIFT_ID', SHIFTS, None, 'Equipment states → Shifts'),
        ('agv_failure_analysis', 'SHIFT_ID', SHIFTS, None, 'AGV failure analysis → Shifts'),
        
        # AGV_ID validation against dim_asset
        ('agv_telemetry', 'AGV_ID', 'dim_asset', 'ASSET_CODE', 'AGV telemetry → Assets'),
    ]
    
    for source_ds, source_col, target, target_col, description in join_checks:
        # Skip if source dataset not loaded
        if source_ds not in datasets:
            warnings.append(f"Skipped: {description} (source not loaded)")
            continue
        
        source_df = datasets[source_ds]
        
        # Check if source column exists
        if source_col not in source_df.columns:
            errors.append(f"{description}: Source column '{source_col}' not found in {source_ds}")
            continue
        
        # Get unique values from source (excluding nulls)
        source_values = set(source_df[source_col].dropna().unique())
        
        # Determine target values
        if isinstance(target, list):
            # Target is a constant list
            target_values = set(target)
            target_name = f"[{', '.join(target[:3])}...]"
        elif isinstance(target, str) and target in datasets:
            # Target is another dataset
            target_df = datasets[target]
            if target_col not in target_df.columns:
                errors.append(f"{description}: Target column '{target_col}' not found in {target}")
                continue
            target_values = set(target_df[target_col].dropna().unique())
            target_name = f"{target}.{target_col}"
        else:
            warnings.append(f"Skipped: {description} (target not loaded)")
            continue
        
        # Check for orphaned values
        orphaned = source_values - target_values
        
        if orphaned:
            orphan_sample = list(orphaned)[:5]
            errors.append(
                f"{description}: {len(orphaned):,} orphaned values in {source_ds}.{source_col} "
                f"(e.g., {orphan_sample})"
            )
        else:
            checks_passed += 1
            print(f"  ✓ {description}")
    
    # Additional data quality checks
    print("\n  Additional Quality Checks:")
    
    # Check crisis period has elevated failures
    if 'ope_daily_fact' in datasets:
        df = datasets['ope_daily_fact']
        crisis_mask = df['METRIC_DATE'].between('2024-12-09', '2024-12-11')
        if crisis_mask.any():
            crisis_avg_failures = df.loc[crisis_mask, 'AGV_ERR_99_COUNT'].mean()
            normal_avg_failures = df.loc[~crisis_mask, 'AGV_ERR_99_COUNT'].mean()
            if crisis_avg_failures > normal_avg_failures * 2:
                checks_passed += 1
                print(f"  ✓ Crisis period shows elevated AGV-ERR-99 (crisis: {crisis_avg_failures:.1f}, normal: {normal_avg_failures:.1f})")
            else:
                warnings.append(f"Crisis period AGV-ERR-99 not significantly elevated")
    
    # Check OPE drops during crisis
    if 'ope_daily_fact' in datasets:
        df = datasets['ope_daily_fact']
        crisis_mask = df['METRIC_DATE'].between('2024-12-09', '2024-12-11')
        if crisis_mask.any():
            crisis_avg_ope = df.loc[crisis_mask, 'OPE_PCT'].mean()
            normal_avg_ope = df.loc[~crisis_mask, 'OPE_PCT'].mean()
            if crisis_avg_ope < normal_avg_ope * 0.9:
                checks_passed += 1
                print(f"  ✓ OPE drops during crisis (crisis: {crisis_avg_ope:.1f}%, normal: {normal_avg_ope:.1f}%)")
            else:
                warnings.append(f"OPE not significantly lower during crisis")
    
    # Check dim tables have expected counts
    if 'dim_asset' in datasets:
        asset_count = len(datasets['dim_asset'])
        expected_assets = len(PRODUCTION_LINES) + len(AGVS)
        if asset_count == expected_assets:
            checks_passed += 1
            print(f"  ✓ dim_asset has expected count ({asset_count} = {len(PRODUCTION_LINES)} lines + {len(AGVS)} AGVs)")
        else:
            warnings.append(f"dim_asset count {asset_count} != expected {expected_assets}")
    
    if 'dim_product' in datasets:
        product_count = len(datasets['dim_product'])
        expected_products = len(PRODUCTS)
        if product_count == expected_products:
            checks_passed += 1
            print(f"  ✓ dim_product has expected count ({product_count} products)")
        else:
            warnings.append(f"dim_product count {product_count} != expected {expected_products}")
    
    # Summary
    print()
    print("=" * 60)
    
    if errors:
        print(f"❌ VALIDATION FAILED: {len(errors)} error(s)")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print(f"⚠  WARNINGS: {len(warnings)}")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors:
        print(f"✓ VALIDATION PASSED: {checks_passed} check(s) passed")
    
    print("=" * 60)
    print()
    
    return len(errors) == 0


def generate_single_dataset(dataset_name: str, output_dir: str, verbose: bool = True) -> bool:
    """
    Generate a single dataset with monitoring and validation.
    
    Returns True if successful, False otherwise.
    """
    if dataset_name not in DATASETS:
        print(f"ERROR: Unknown dataset '{dataset_name}'")
        print(f"Available datasets: {', '.join(DATASETS.keys())}")
        return False
    
    config = DATASETS[dataset_name]
    filename = config['filename']
    generator = config['generator']
    description = config['description']
    expected_min_rows = config['expected_min_rows']
    filepath = os.path.join(output_dir, filename)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Generating: {dataset_name}")
        print(f"{'='*60}")
        print(f"  Description: {description}")
        print(f"  Output: {filepath}")
        print(f"  Expected rows: >= {expected_min_rows:,}")
        print()
    
    # Reset random seeds for reproducibility
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    # Generate data with timing
    start_time = time.time()
    if verbose:
        print("  Generating data...", flush=True)
    
    try:
        df = generator()
    except Exception as e:
        print(f"  FAILED")
        print(f"  ERROR: {e}")
        return False
    
    gen_time = time.time() - start_time
    if verbose:
        print(f"  Generation complete ({format_duration(gen_time)}, {len(df):,} rows)")
    
    # Validate
    if verbose:
        print("  Validating...", end=' ', flush=True)
    
    is_valid, errors = validate_dataframe(df, dataset_name, expected_min_rows)
    
    if not is_valid:
        print("FAILED")
        for error in errors:
            print(f"    - {error}")
        return False
    
    if verbose:
        print("passed")
    
    # Write to CSV with timing
    if verbose:
        print("  Writing CSV...", end=' ', flush=True)
    
    write_start = time.time()
    try:
        df.to_csv(filepath, index=False)
    except Exception as e:
        print(f"FAILED")
        print(f"  ERROR: {e}")
        return False
    
    write_time = time.time() - write_start
    file_size = os.path.getsize(filepath)
    
    if verbose:
        print(f"done ({format_duration(write_time)})")
    
    # Summary
    total_time = time.time() - start_time
    if verbose:
        print()
        print(f"  ✓ SUCCESS: {len(df):,} rows, {format_size(file_size)}, {format_duration(total_time)} total")
    else:
        print(f"  ✓ {dataset_name}: {len(df):,} rows, {format_size(file_size)}")
    
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Generate a single synthetic dataset for VoltStream EV OPE demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s env_sensors              # Generate env_sensors.csv
  %(prog)s agv_telemetry --force    # Regenerate agv_telemetry.csv (overwrites existing)
  %(prog)s --list                   # List available datasets
  %(prog)s --validate               # Validate joins between all datasets
  
To generate all datasets, run this script once for each dataset name.
        """
    )
    parser.add_argument('dataset', nargs='?', type=str, default=None,
                        help='Name of the dataset to generate (required unless --list or --validate)')
    parser.add_argument('--output-dir', type=str, default='data/synthetic',
                        help='Output directory for CSV files (default: data/synthetic)')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing file if it exists')
    parser.add_argument('--list', action='store_true', dest='list_datasets',
                        help='List available datasets and exit')
    parser.add_argument('--validate', action='store_true',
                        help='Validate joins between all generated datasets')
    parser.add_argument('--quiet', action='store_true',
                        help='Reduce output verbosity')
    args = parser.parse_args()
    
    # List datasets and exit
    if args.list_datasets:
        print("\nAvailable datasets:")
        print("-" * 70)
        for name, config in DATASETS.items():
            print(f"  {name:<20} {config['description']}")
        print()
        print("Generate all with:")
        print("  for ds in " + " ".join(DATASETS.keys()) + "; do")
        print("    python3 utils/generate_synthetic_data.py $ds")
        print("  done")
        print()
        print("Validate all joins:")
        print("  python3 utils/generate_synthetic_data.py --validate")
        print()
        return 0
    
    # Validate joins and exit
    if args.validate:
        success = validate_joins(args.output_dir)
        return 0 if success else 1
    
    # Require dataset name
    if not args.dataset:
        parser.error("dataset name is required (use --list to see available datasets)")
    
    # Validate dataset name
    if args.dataset not in DATASETS:
        print(f"ERROR: Unknown dataset '{args.dataset}'")
        print(f"Use --list to see available datasets")
        return 1
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Check if file already exists
    config = DATASETS[args.dataset]
    filepath = os.path.join(args.output_dir, config['filename'])
    
    if os.path.exists(filepath) and not args.force:
        file_size = os.path.getsize(filepath)
        print(f"\nFile already exists: {filepath} ({format_size(file_size)})")
        print("Use --force to overwrite")
        return 1
    
    # Header
    if not args.quiet:
        print()
        print("=" * 60)
        print("VoltStream EV OPE - Synthetic Data Generator")
        print("=" * 60)
        print(f"  Random seed: {RANDOM_SEED}")
        print(f"  Date range: {START_DATE.date()} to {END_DATE.date()}")
        print(f"  Crisis period: {CRISIS_START.date()} to {CRISIS_END.date()}")
        print(f"  Output directory: {args.output_dir}")
    
    # Generate the dataset
    success = generate_single_dataset(args.dataset, args.output_dir, verbose=not args.quiet)
    
    if success and not args.quiet:
        print()
        print("Data story embedded:")
        print("  • Months 1-2: Normal operation, OPE ~85%")
        print("  • Dec 9-11 (Crisis): Humidity↓ → Dust↑ → AGV-ERR-99 → OPE drops to 60%")
        print("  • LINE_4 most affected by starvation events")
        print()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

