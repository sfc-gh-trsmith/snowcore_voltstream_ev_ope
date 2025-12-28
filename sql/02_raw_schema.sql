-- =============================================================================
-- 02_raw_schema.sql - RAW Layer Tables
-- =============================================================================
-- Landing zone tables preserving source system formats
-- Sources: SAP ERP, Siemens MES, IoT Historian
-- =============================================================================

USE SCHEMA RAW;

-- =============================================================================
-- SAP ERP TABLES
-- =============================================================================

-- Material Document CDC - Inventory movements from SAP
-- Represents the "financial" view of inventory
CREATE OR REPLACE TABLE MATERIAL_DOCUMENT_CDC (
    -- Source columns
    MAT_DOC_ID VARCHAR(20) NOT NULL,
    POSTING_DATE DATE,
    SKU VARCHAR(50),
    MVMT_TYPE VARCHAR(10),                  -- 101=GR, 321=Transfer, etc.
    STOCK_TYPE VARCHAR(30),                 -- UNRESTRICTED, QUALITY_INSPECTION
    BATCH_ID VARCHAR(30),
    PLANT_ID VARCHAR(10),
    STORAGE_LOCATION VARCHAR(10),
    QUANTITY NUMBER(18,3),
    UNIT_OF_MEASURE VARCHAR(5),
    
    -- CDC metadata columns
    _CDC_OPERATION VARCHAR(10),             -- INSERT, UPDATE, DELETE
    _CDC_TIMESTAMP TIMESTAMP_NTZ,
    _CDC_SEQUENCE NUMBER,
    _CDC_SOURCE_SYSTEM VARCHAR(50) DEFAULT 'SAP_ERP',
    _LOADED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'CDC feed from SAP Material Documents - inventory movements and status';

-- Production Order Header - Production plans from SAP
CREATE OR REPLACE TABLE PROD_ORDER_HEADER_CDC (
    -- Source columns
    ORDER_ID VARCHAR(20) NOT NULL,
    ORDER_TYPE VARCHAR(10),
    SKU VARCHAR(50),
    TARGET_QTY NUMBER(18,3),
    ACTUAL_QTY NUMBER(18,3),                 -- Actual quantity produced (may differ from target)
    UNIT_OF_MEASURE VARCHAR(5),
    SCHED_START TIMESTAMP_NTZ,
    SCHED_END TIMESTAMP_NTZ,
    ACTUAL_START TIMESTAMP_NTZ,
    ACTUAL_END TIMESTAMP_NTZ,
    PRODUCTION_LINE_ID VARCHAR(20),
    WORK_CENTER_ID VARCHAR(20),
    ORDER_STATUS VARCHAR(20),               -- CREATED, RELEASED, STARTED, COMPLETED
    PRIORITY NUMBER(5),
    
    -- CDC metadata columns
    _CDC_OPERATION VARCHAR(10),
    _CDC_TIMESTAMP TIMESTAMP_NTZ,
    _CDC_SEQUENCE NUMBER,
    _CDC_SOURCE_SYSTEM VARCHAR(50) DEFAULT 'SAP_ERP',
    _LOADED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'CDC feed from SAP Production Orders - manufacturing plans';

-- =============================================================================
-- SIEMENS MES TABLES
-- =============================================================================

-- Equipment State Log - Machine states from MES
CREATE OR REPLACE TABLE EQUIPMENT_STATE_LOG_CDC (
    -- Source columns
    EVENT_ID VARCHAR(36) NOT NULL,
    ASSET_ID VARCHAR(30),
    PRODUCTION_LINE_ID VARCHAR(20),
    EVENT_TIMESTAMP TIMESTAMP_NTZ,
    STATE_CODE NUMBER(5),                   -- 1=RUN, 2=IDLE, 3=FAULT, 4=SETUP
    STATE_NAME VARCHAR(30),
    REASON_CODE VARCHAR(30),                -- STARVATION, BLOCKAGE, BREAKDOWN, etc.
    REASON_DESCRIPTION VARCHAR(200),
    DURATION_SECONDS NUMBER(10),
    SHIFT_ID VARCHAR(20),
    OPERATOR_ID VARCHAR(30),
    
    -- CDC metadata columns
    _CDC_OPERATION VARCHAR(10),
    _CDC_TIMESTAMP TIMESTAMP_NTZ,
    _CDC_SEQUENCE NUMBER,
    _CDC_SOURCE_SYSTEM VARCHAR(50) DEFAULT 'SIEMENS_MES',
    _LOADED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'CDC feed from Siemens MES - equipment state transitions and downtime reasons';

-- AGV Telematics Log - AGV telemetry from MES
CREATE OR REPLACE TABLE AGV_TELEMATICS_LOG_CDC (
    -- Source columns
    MSG_ID VARCHAR(36) NOT NULL,
    AGV_ID VARCHAR(20),
    EVENT_TIMESTAMP TIMESTAMP_NTZ,
    X_COORD NUMBER(10,3),
    Y_COORD NUMBER(10,3),
    Z_COORD NUMBER(10,3),
    ZONE_ID VARCHAR(20),
    ROUTE_SEGMENT VARCHAR(30),
    VELOCITY NUMBER(8,3),
    BATTERY_LEVEL NUMBER(5,2),
    PAYLOAD_ID VARCHAR(30),
    ERROR_CODE VARCHAR(20),                 -- AGV-ERR-99 = Optical Sensor Obscured
    ERROR_SEVERITY VARCHAR(10),             -- INFO, WARNING, ERROR, CRITICAL
    ERROR_MESSAGE VARCHAR(500),
    
    -- CDC metadata columns
    _CDC_OPERATION VARCHAR(10),
    _CDC_TIMESTAMP TIMESTAMP_NTZ,
    _CDC_SEQUENCE NUMBER,
    _CDC_SOURCE_SYSTEM VARCHAR(50) DEFAULT 'SIEMENS_MES',
    _LOADED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'CDC feed from Siemens MES - AGV telemetry, position, and error codes';

-- =============================================================================
-- IOT HISTORIAN TABLES
-- =============================================================================

-- Environmental Sensor Stream - High-frequency IoT data
CREATE OR REPLACE TABLE ENV_SENSOR_STREAM_STAGE (
    -- Source columns
    READING_ID VARCHAR(36) NOT NULL,
    SENSOR_ID VARCHAR(30),
    SENSOR_TYPE VARCHAR(30),                -- HUMIDITY, PM25, TEMPERATURE, PRESSURE
    ZONE_ID VARCHAR(20),
    PRODUCTION_LINE_ID VARCHAR(20),
    READING_TIMESTAMP TIMESTAMP_NTZ,
    METRIC_NAME VARCHAR(50),
    METRIC_VALUE NUMBER(18,6),
    UNIT_OF_MEASURE VARCHAR(20),
    QUALITY_FLAG VARCHAR(10),               -- GOOD, SUSPECT, BAD
    
    -- Stage metadata columns
    _SOURCE_FILE_NAME VARCHAR(500),
    _SOURCE_FILE_ROW_NUMBER NUMBER,
    _LOADED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Staged IoT sensor readings - environmental conditions (humidity, dust, temp)';

-- =============================================================================
-- ENABLE CHANGE TRACKING FOR DYNAMIC TABLES
-- =============================================================================
ALTER TABLE MATERIAL_DOCUMENT_CDC SET CHANGE_TRACKING = TRUE;
ALTER TABLE PROD_ORDER_HEADER_CDC SET CHANGE_TRACKING = TRUE;
ALTER TABLE EQUIPMENT_STATE_LOG_CDC SET CHANGE_TRACKING = TRUE;
ALTER TABLE AGV_TELEMATICS_LOG_CDC SET CHANGE_TRACKING = TRUE;
ALTER TABLE ENV_SENSOR_STREAM_STAGE SET CHANGE_TRACKING = TRUE;

-- =============================================================================
-- TABLE COMMENTS FOR DOCUMENTATION
-- =============================================================================
COMMENT ON COLUMN MATERIAL_DOCUMENT_CDC.STOCK_TYPE IS 
    'Inventory status: UNRESTRICTED (available), QUALITY_INSPECTION (blocked for QA)';

COMMENT ON COLUMN EQUIPMENT_STATE_LOG_CDC.STATE_CODE IS 
    'Machine state: 1=Running, 2=Idle, 3=Fault, 4=Setup/Changeover';

COMMENT ON COLUMN EQUIPMENT_STATE_LOG_CDC.REASON_CODE IS 
    'Downtime reason: STARVATION (no material), BLOCKAGE (output blocked), BREAKDOWN (equipment failure)';

COMMENT ON COLUMN AGV_TELEMATICS_LOG_CDC.ERROR_CODE IS 
    'AGV error codes: AGV-ERR-99 = Optical Sensor Obscured (dust on LiDAR lens)';

COMMENT ON COLUMN ENV_SENSOR_STREAM_STAGE.METRIC_NAME IS 
    'Environmental metrics: HUMIDITY (%), PM25 (µg/m³), TEMPERATURE (°C), PRESSURE (hPa)';

COMMENT ON COLUMN PROD_ORDER_HEADER_CDC.ACTUAL_QTY IS 
    'Actual quantity produced - may be less than TARGET_QTY due to quality issues, starvation, or other losses';

