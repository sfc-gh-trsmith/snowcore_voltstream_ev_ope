-- =============================================================================
-- 03_atomic_schema.sql - ATOMIC Layer Tables (Enterprise Relational Model)
-- =============================================================================
-- Enterprise Relational Model aligned with core.data_dictionary.csv
-- Single source of truth for business entities
-- 
-- Tables from core dictionary:
--   SITE, WORK_CENTER, ASSET, PRODUCT, SHIFT, WORK_ORDER,
--   EQUIPMENT_DOWNTIME, EQUIPMENT_FAILURE, INVENTORY_TRANSACTION
--
-- Project extension (justified: IoT sensor data not in core model):
--   ENVIRONMENTAL_READING
-- =============================================================================

USE SCHEMA ATOMIC;

-- =============================================================================
-- REFERENCE TABLES
-- =============================================================================

-- SITE - Factory/plant reference (from core dictionary)
CREATE OR REPLACE TABLE SITE (
    -- Primary Key
    SITE_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys
    SITE_CODE VARCHAR(50) NOT NULL,
    SITE_NAME VARCHAR(200),
    SITE_TYPE VARCHAR(50),
    
    -- Location
    ADDRESS_LINE_1 VARCHAR(200),
    ADDRESS_LINE_2 VARCHAR(200),
    CITY VARCHAR(100),
    STATE_PROVINCE VARCHAR(100),
    POSTAL_CODE VARCHAR(20),
    COUNTRY VARCHAR(100),
    
    -- Attributes
    OPERATING_STATUS VARCHAR(50),
    CAPACITY_METRIC NUMBER(18,4),
    CAPACITY_UNIT_OF_MEASURE VARCHAR(50),
    
    -- Type 2 SCD columns
    VALID_FROM_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    VALID_TO_TIMESTAMP TIMESTAMP_NTZ,
    IS_CURRENT_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    CREATED_BY_USER VARCHAR(100) DEFAULT CURRENT_USER(),
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY_USER VARCHAR(100),
    UPDATED_TIMESTAMP TIMESTAMP_NTZ,
    
    PRIMARY KEY (SITE_ID)
)
COMMENT = 'Factory/plant sites - from core.data_dictionary.csv SITE';

-- WORK_CENTER - Production work centers (from core dictionary)
CREATE OR REPLACE TABLE WORK_CENTER (
    -- Primary Key
    WORK_CENTER_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys
    WORK_CENTER_CODE VARCHAR(50) NOT NULL,
    WORK_CENTER_NAME VARCHAR(200),
    WORK_CENTER_DESCRIPTION VARCHAR(1000),
    WORK_CENTER_TYPE VARCHAR(50),
    
    -- Relationships
    SITE_ID NUMBER(38,0),
    
    -- Capacity and rates
    CAPACITY_PER_HOUR NUMBER(18,4),
    HOURS_PER_DAY NUMBER(8,2),
    EFFICIENCY_FACTOR NUMBER(5,4),
    LABOR_RATE_PER_HOUR NUMBER(18,4),
    OVERHEAD_RATE_PER_HOUR NUMBER(18,4),
    
    -- Type 2 SCD columns
    VALID_FROM_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    VALID_TO_TIMESTAMP TIMESTAMP_NTZ,
    IS_CURRENT_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    CREATED_BY_USER VARCHAR(100) DEFAULT CURRENT_USER(),
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY_USER VARCHAR(100),
    UPDATED_TIMESTAMP TIMESTAMP_NTZ,
    
    PRIMARY KEY (WORK_CENTER_ID)
)
COMMENT = 'Production work centers - from core.data_dictionary.csv WORK_CENTER';

-- SHIFT - Shift definitions (from core dictionary)
CREATE OR REPLACE TABLE SHIFT (
    -- Primary Key
    SHIFT_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys
    SHIFT_CODE VARCHAR(50) NOT NULL,
    SITE_ID NUMBER(38,0),
    SHIFT_NAME VARCHAR(100),
    
    -- Timing
    START_TIME TIME,
    END_TIME TIME,
    SHIFT_DURATION_HOURS NUMBER(4,2),
    
    -- Type 2 SCD columns
    VALID_FROM_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    VALID_TO_TIMESTAMP TIMESTAMP_NTZ,
    IS_CURRENT_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    CREATED_BY_USER VARCHAR(100) DEFAULT CURRENT_USER(),
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY_USER VARCHAR(100),
    UPDATED_TIMESTAMP TIMESTAMP_NTZ,
    
    PRIMARY KEY (SHIFT_ID)
)
COMMENT = 'Work shift definitions - from core.data_dictionary.csv SHIFT';

-- =============================================================================
-- MASTER DATA TABLES
-- =============================================================================

-- ASSET - Unified asset dimension (from core dictionary + extensions)
CREATE OR REPLACE TABLE ASSET (
    -- Primary Key
    ASSET_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys (from core dictionary)
    ASSET_CODE VARCHAR(100) NOT NULL,
    ASSET_NAME VARCHAR(200),
    ASSET_DESCRIPTION VARCHAR(1000),
    
    -- Classification (from core dictionary)
    ASSET_TYPE VARCHAR(50),                 -- PRODUCTION_LINE, MACHINE, AGV, SENSOR
    ASSET_CLASS VARCHAR(50),                -- ASSEMBLY, WELDING, TRANSPORT, MONITORING
    
    -- Technical attributes (from core dictionary)
    SERIAL_NUMBER VARCHAR(100),
    MODEL_NUMBER VARCHAR(100),
    MANUFACTURER VARCHAR(200),
    ACQUISITION_DATE DATE,
    ACQUISITION_COST NUMBER(18,2),
    ASSET_STATUS VARCHAR(50),               -- ACTIVE, INACTIVE, MAINTENANCE, RETIRED
    
    -- Hierarchy (from core dictionary)
    PARENT_ASSET_ID NUMBER(38,0),
    
    -- PROJECT EXTENSIONS (justified: factory context for OPE analysis)
    SITE_ID NUMBER(38,0),                   -- Link to SITE
    WORK_CENTER_ID NUMBER(38,0),            -- Link to WORK_CENTER
    ZONE_ID VARCHAR(20),                    -- Factory zone (ZONE_A, ZONE_B, etc.)
    PRODUCTION_LINE_ID VARCHAR(20),         -- Production line assignment
    
    -- Type 2 SCD columns
    VALID_FROM_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    VALID_TO_TIMESTAMP TIMESTAMP_NTZ,
    IS_CURRENT_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    CREATED_BY_USER VARCHAR(100) DEFAULT CURRENT_USER(),
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY_USER VARCHAR(100),
    UPDATED_TIMESTAMP TIMESTAMP_NTZ,
    
    PRIMARY KEY (ASSET_ID)
)
COMMENT = 'Unified asset dimension: machines, AGVs, production lines - from core.data_dictionary.csv ASSET + factory extensions';

-- PRODUCT - Product master (from core dictionary + extensions)
CREATE OR REPLACE TABLE PRODUCT (
    -- Primary Key
    PRODUCT_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys (from core dictionary)
    PRODUCT_CODE VARCHAR(100) NOT NULL,     -- SKU
    PRODUCT_NAME VARCHAR(200),
    PRODUCT_DESCRIPTION_SHORT VARCHAR(500),
    PRODUCT_DESCRIPTION_LONG VARCHAR(4000),
    
    -- Classification (from core dictionary)
    PRODUCT_TYPE VARCHAR(50),               -- FINISHED_GOOD, COMPONENT, RAW_MATERIAL
    PRODUCT_STATUS VARCHAR(50),             -- ACTIVE, DISCONTINUED, PENDING
    MAKE_BUY_INDICATOR VARCHAR(20),
    
    -- PROJECT EXTENSIONS (justified: OPE analysis needs cost/cycle time)
    PRODUCT_CATEGORY VARCHAR(50),           -- BATTERY_PACK, MODULE, CELL
    PRODUCT_FAMILY VARCHAR(50),
    PRODUCT_LINE VARCHAR(50),
    PARENT_PRODUCT_ID NUMBER(38,0),         -- BOM hierarchy
    UNIT_OF_MEASURE VARCHAR(10),
    STANDARD_COST NUMBER(18,4),
    STANDARD_CYCLE_TIME_SEC NUMBER(10),
    
    -- Type 2 SCD columns
    VALID_FROM_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    VALID_TO_TIMESTAMP TIMESTAMP_NTZ,
    IS_CURRENT_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    CREATED_BY_USER VARCHAR(100) DEFAULT CURRENT_USER(),
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY_USER VARCHAR(100),
    UPDATED_TIMESTAMP TIMESTAMP_NTZ,
    
    PRIMARY KEY (PRODUCT_ID)
)
COMMENT = 'Product master with BOM hierarchy - from core.data_dictionary.csv PRODUCT + OPE extensions';

-- =============================================================================
-- TRANSACTIONAL TABLES
-- =============================================================================

-- WORK_ORDER - Production orders (from core dictionary + extensions)
CREATE OR REPLACE TABLE WORK_ORDER (
    -- Primary Key
    WORK_ORDER_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys (from core dictionary)
    WORK_ORDER_NUMBER VARCHAR(100) NOT NULL,
    WORK_ORDER_TYPE VARCHAR(50),
    
    -- Relationships (from core dictionary)
    PRODUCT_ID NUMBER(38,0),
    SITE_ID NUMBER(38,0),
    
    -- Quantities (from core dictionary)
    PLANNED_QUANTITY NUMBER(18,4),
    COMPLETED_QUANTITY NUMBER(18,4),
    SCRAPPED_QUANTITY NUMBER(18,4),
    
    -- Status (from core dictionary)
    WORK_ORDER_STATUS VARCHAR(50),          -- CREATED, RELEASED, STARTED, COMPLETED
    PRIORITY VARCHAR(50),
    
    -- Dates (from core dictionary)
    PLANNED_START_DATE DATE,
    PLANNED_COMPLETION_DATE DATE,
    ACTUAL_START_DATE DATE,
    ACTUAL_COMPLETION_DATE DATE,
    
    -- Source reference (from core dictionary)
    SOURCE_DEMAND_TYPE VARCHAR(50),
    SOURCE_DEMAND_REFERENCE VARCHAR(100),
    
    -- PROJECT EXTENSIONS (justified: OPE analysis needs work center/shift/line)
    WORK_CENTER_ID NUMBER(38,0),
    SHIFT_ID NUMBER(38,0),
    PRODUCTION_LINE_ID VARCHAR(20),         -- Denormalized for efficient OPE analytics
    ACTUAL_START_TIMESTAMP TIMESTAMP_NTZ,
    ACTUAL_END_TIMESTAMP TIMESTAMP_NTZ,
    
    -- Type 2 SCD columns
    VALID_FROM_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    VALID_TO_TIMESTAMP TIMESTAMP_NTZ,
    IS_CURRENT_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Audit columns
    CREATED_BY_USER VARCHAR(100) DEFAULT CURRENT_USER(),
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY_USER VARCHAR(100),
    UPDATED_TIMESTAMP TIMESTAMP_NTZ,
    
    PRIMARY KEY (WORK_ORDER_ID)
)
COMMENT = 'Production work orders - from core.data_dictionary.csv WORK_ORDER + OPE extensions';

-- EQUIPMENT_DOWNTIME - Downtime events (from core dictionary + extensions)
CREATE OR REPLACE TABLE EQUIPMENT_DOWNTIME (
    -- Primary Key
    EQUIPMENT_DOWNTIME_ID NUMBER(38,0) NOT NULL,
    
    -- Relationships (from core dictionary)
    ASSET_ID NUMBER(38,0),
    WORK_CENTER_ID NUMBER(38,0),
    
    -- Timing (from core dictionary)
    DOWNTIME_START_TIMESTAMP TIMESTAMP_NTZ,
    DOWNTIME_END_TIMESTAMP TIMESTAMP_NTZ,
    DOWNTIME_DURATION_HOURS NUMBER(8,2),
    
    -- Classification (from core dictionary)
    DOWNTIME_TYPE VARCHAR(50),              -- PLANNED, UNPLANNED
    DOWNTIME_REASON_CODE VARCHAR(50),       -- STARVATION, BLOCKAGE, BREAKDOWN, SETUP
    
    -- Impact (from core dictionary)
    PRODUCTION_LOSS_UNITS NUMBER(18,4),
    PRODUCTION_LOSS_REVENUE NUMBER(18,2),
    
    -- PROJECT EXTENSIONS (justified: OPE analysis needs shift/state details)
    SHIFT_ID NUMBER(38,0),
    STATE_CODE NUMBER(5),                   -- 1=RUN, 2=IDLE, 3=FAULT, 4=SETUP
    STATE_NAME VARCHAR(30),
    REASON_DESCRIPTION VARCHAR(500),
    OPERATOR_ID VARCHAR(30),
    
    -- Audit columns
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    PRIMARY KEY (EQUIPMENT_DOWNTIME_ID)
)
COMMENT = 'Equipment downtime events - from core.data_dictionary.csv EQUIPMENT_DOWNTIME + OPE extensions';

-- EQUIPMENT_FAILURE - Failure events (from core dictionary + extensions)
CREATE OR REPLACE TABLE EQUIPMENT_FAILURE (
    -- Primary Key
    EQUIPMENT_FAILURE_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys (from core dictionary)
    FAILURE_NUMBER VARCHAR(100),
    FAILURE_DATE DATE,
    FAILURE_TIMESTAMP TIMESTAMP_NTZ,
    
    -- Relationships (from core dictionary)
    ASSET_ID NUMBER(38,0),
    WORK_CENTER_ID NUMBER(38,0),
    
    -- Failure details (from core dictionary)
    FAILURE_MODE VARCHAR(50),               -- Error code category
    FAILURE_DESCRIPTION VARCHAR(2000),
    FAILURE_SYMPTOMS VARCHAR(2000),
    FAILURE_CAUSE VARCHAR(2000),
    FAILURE_SEVERITY VARCHAR(50),           -- INFO, WARNING, ERROR, CRITICAL
    
    -- Downtime impact (from core dictionary)
    DOWNTIME_START_TIMESTAMP TIMESTAMP_NTZ,
    DOWNTIME_END_TIMESTAMP TIMESTAMP_NTZ,
    TOTAL_DOWNTIME_HOURS NUMBER(8,2),
    PRODUCTION_IMPACT_DESCRIPTION VARCHAR(1000),
    
    -- PROJECT EXTENSIONS (justified: AGV error code tracking)
    ERROR_CODE VARCHAR(20),                 -- AGV-ERR-99, AGV-ERR-01, etc.
    ERROR_MESSAGE VARCHAR(500),
    ZONE_ID VARCHAR(20),
    ROUTE_SEGMENT VARCHAR(30),
    
    -- Audit columns
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    PRIMARY KEY (EQUIPMENT_FAILURE_ID)
)
COMMENT = 'Equipment failure events with error codes - from core.data_dictionary.csv EQUIPMENT_FAILURE + AGV extensions';

-- INVENTORY_TRANSACTION - Material movements (from core dictionary + extensions)
CREATE OR REPLACE TABLE INVENTORY_TRANSACTION (
    -- Primary Key
    INVENTORY_TRANSACTION_ID NUMBER(38,0) NOT NULL,
    
    -- Business Keys (from core dictionary)
    TRANSACTION_NUMBER VARCHAR(100),
    TRANSACTION_DATE TIMESTAMP_NTZ,
    TRANSACTION_TYPE VARCHAR(50),           -- 101=GR, 321=Transfer, etc.
    
    -- Relationships (from core dictionary)
    PRODUCT_ID NUMBER(38,0),
    SITE_ID NUMBER(38,0),
    
    -- Quantities (from core dictionary)
    TRANSACTION_QUANTITY NUMBER(18,4),
    TRANSACTION_REASON_CODE VARCHAR(50),
    TRANSACTION_COST NUMBER(18,2),
    
    -- Source reference (from core dictionary)
    SOURCE_DOCUMENT_TYPE VARCHAR(50),
    SOURCE_DOCUMENT_REFERENCE VARCHAR(100),
    
    -- PROJECT EXTENSIONS (justified: inventory status tracking for OPE)
    BATCH_ID VARCHAR(30),
    STOCK_TYPE VARCHAR(30),                 -- UNRESTRICTED, QUALITY_INSPECTION
    STORAGE_LOCATION VARCHAR(10),
    MOVEMENT_TYPE VARCHAR(10),              -- SAP movement type
    
    -- Audit columns
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    PRIMARY KEY (INVENTORY_TRANSACTION_ID)
)
COMMENT = 'Inventory transactions/material movements - from core.data_dictionary.csv INVENTORY_TRANSACTION + OPE extensions';

-- =============================================================================
-- PROJECT EXTENSION TABLE
-- =============================================================================

-- ENVIRONMENTAL_READING - IoT sensor data (PROJECT EXTENSION)
-- Justification: Core dictionary has no IoT sensor model; required for OPE analysis
CREATE OR REPLACE TABLE ENVIRONMENTAL_READING (
    -- Primary Key
    READING_ID VARCHAR(36) NOT NULL,
    
    -- Sensor identification
    SENSOR_ID VARCHAR(30),
    SENSOR_TYPE VARCHAR(30),                -- HUMIDITY, PM25, TEMPERATURE, PRESSURE
    
    -- Location context
    SITE_ID NUMBER(38,0),
    ZONE_ID VARCHAR(20),
    PRODUCTION_LINE_ID VARCHAR(20),
    
    -- Reading data
    READING_TIMESTAMP TIMESTAMP_NTZ,
    METRIC_NAME VARCHAR(50),
    METRIC_VALUE NUMBER(18,6),
    UNIT_OF_MEASURE VARCHAR(20),
    QUALITY_FLAG VARCHAR(10),               -- GOOD, SUSPECT, BAD
    
    -- Audit columns
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    PRIMARY KEY (READING_ID)
)
COMMENT = 'Environmental sensor readings (PROJECT EXTENSION - IoT not in core dictionary)';

-- =============================================================================
-- ENABLE CHANGE TRACKING FOR VIEWS
-- =============================================================================
ALTER TABLE SITE SET CHANGE_TRACKING = TRUE;
ALTER TABLE WORK_CENTER SET CHANGE_TRACKING = TRUE;
ALTER TABLE SHIFT SET CHANGE_TRACKING = TRUE;
ALTER TABLE ASSET SET CHANGE_TRACKING = TRUE;
ALTER TABLE PRODUCT SET CHANGE_TRACKING = TRUE;
ALTER TABLE WORK_ORDER SET CHANGE_TRACKING = TRUE;
ALTER TABLE EQUIPMENT_DOWNTIME SET CHANGE_TRACKING = TRUE;
ALTER TABLE EQUIPMENT_FAILURE SET CHANGE_TRACKING = TRUE;
ALTER TABLE INVENTORY_TRANSACTION SET CHANGE_TRACKING = TRUE;
ALTER TABLE ENVIRONMENTAL_READING SET CHANGE_TRACKING = TRUE;

-- =============================================================================
-- SEED DATA FOR REFERENCE TABLES
-- =============================================================================

-- Insert site (VoltStream Gigafactory)
INSERT INTO SITE (SITE_ID, SITE_CODE, SITE_NAME, SITE_TYPE, CITY, STATE_PROVINCE, COUNTRY, OPERATING_STATUS)
VALUES (1, 'P001', 'VoltStream EV Gigafactory', 'MANUFACTURING', 'Austin', 'Texas', 'USA', 'ACTIVE');

-- Insert work centers (production lines)
INSERT INTO WORK_CENTER (WORK_CENTER_ID, WORK_CENTER_CODE, WORK_CENTER_NAME, WORK_CENTER_TYPE, SITE_ID, CAPACITY_PER_HOUR, HOURS_PER_DAY, EFFICIENCY_FACTOR)
VALUES 
    (1, 'WC_LINE_1', 'Production Line 1 Work Center', 'ASSEMBLY', 1, 25, 24, 0.95),
    (2, 'WC_LINE_2', 'Production Line 2 Work Center', 'ASSEMBLY', 1, 25, 24, 0.95),
    (3, 'WC_LINE_3', 'Production Line 3 Work Center', 'ASSEMBLY', 1, 25, 24, 0.95),
    (4, 'WC_LINE_4', 'Production Line 4 Work Center', 'ASSEMBLY', 1, 25, 24, 0.95),
    (5, 'WC_LINE_5', 'Production Line 5 Work Center', 'ASSEMBLY', 1, 25, 24, 0.95);

-- Insert shifts
INSERT INTO SHIFT (SHIFT_ID, SHIFT_CODE, SITE_ID, SHIFT_NAME, START_TIME, END_TIME, SHIFT_DURATION_HOURS)
VALUES 
    (1, 'SHIFT_1', 1, 'Morning Shift', '06:00:00', '14:00:00', 8.0),
    (2, 'SHIFT_2', 1, 'Afternoon Shift', '14:00:00', '22:00:00', 8.0),
    (3, 'SHIFT_3', 1, 'Night Shift', '22:00:00', '06:00:00', 8.0);
