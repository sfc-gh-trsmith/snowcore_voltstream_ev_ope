-- =============================================================================
-- 01_account_setup.sql - Account-Level Infrastructure Setup
-- =============================================================================
-- Creates role, warehouse, database, and schemas for the OPE Jidoka System
-- This script uses session variables set by deploy.sh
-- =============================================================================

-- Use ACCOUNTADMIN for initial setup
USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- ROLE SETUP
-- =============================================================================
CREATE ROLE IF NOT EXISTS IDENTIFIER($PROJECT_ROLE);

-- Grant Cortex privileges to the role
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE IDENTIFIER($PROJECT_ROLE);

-- Grant role to current user for convenience
GRANT ROLE IDENTIFIER($PROJECT_ROLE) TO ROLE ACCOUNTADMIN;

-- =============================================================================
-- WAREHOUSE SETUP
-- =============================================================================
CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($PROJECT_WH)
    WITH 
        WAREHOUSE_SIZE = 'X-SMALL'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE
        INITIALLY_SUSPENDED = TRUE
        COMMENT = 'Warehouse for VoltStream EV OPE Analytics';

GRANT USAGE ON WAREHOUSE IDENTIFIER($PROJECT_WH) TO ROLE IDENTIFIER($PROJECT_ROLE);
GRANT OPERATE ON WAREHOUSE IDENTIFIER($PROJECT_WH) TO ROLE IDENTIFIER($PROJECT_ROLE);

-- =============================================================================
-- DATABASE SETUP
-- =============================================================================
CREATE DATABASE IF NOT EXISTS IDENTIFIER($FULL_PREFIX)
    COMMENT = 'VoltStream EV Manufacturing - OPE Intelligent Jidoka System';

GRANT OWNERSHIP ON DATABASE IDENTIFIER($FULL_PREFIX) TO ROLE IDENTIFIER($PROJECT_ROLE);

-- =============================================================================
-- SCHEMA SETUP
-- =============================================================================
USE DATABASE IDENTIFIER($FULL_PREFIX);

-- RAW Schema - Landing zone for source system data
CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Landing zone for source system data (SAP ERP, Siemens MES, IoT)';

-- ATOMIC Schema - Normalized enterprise model
CREATE SCHEMA IF NOT EXISTS ATOMIC
    COMMENT = 'Enterprise relational model with normalized entities';

-- EV_OPE Schema - Business data mart for OPE analytics
CREATE SCHEMA IF NOT EXISTS EV_OPE
    COMMENT = 'Business data mart optimized for OPE analytics and Cortex AI';

-- Grant schema ownership to project role
GRANT OWNERSHIP ON SCHEMA RAW TO ROLE IDENTIFIER($PROJECT_ROLE);
GRANT OWNERSHIP ON SCHEMA ATOMIC TO ROLE IDENTIFIER($PROJECT_ROLE);
GRANT OWNERSHIP ON SCHEMA EV_OPE TO ROLE IDENTIFIER($PROJECT_ROLE);

-- =============================================================================
-- STAGE SETUP (for data loading and semantic models)
-- =============================================================================
USE ROLE IDENTIFIER($PROJECT_ROLE);
USE WAREHOUSE IDENTIFIER($PROJECT_WH);
USE DATABASE IDENTIFIER($FULL_PREFIX);

-- Stage for synthetic data files
CREATE STAGE IF NOT EXISTS RAW.DATA_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for loading synthetic demo data';

-- Stage for unstructured documents (maintenance manuals)
CREATE STAGE IF NOT EXISTS RAW.DOCS_STAGE
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for maintenance manuals and shift reports';

-- Stage for semantic models
CREATE STAGE IF NOT EXISTS EV_OPE.SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for Cortex Analyst semantic model YAML files';

-- Stage for notebooks
CREATE STAGE IF NOT EXISTS EV_OPE.NOTEBOOKS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for Snowpark ML notebooks';

-- =============================================================================
-- VERIFICATION
-- =============================================================================
SHOW SCHEMAS IN DATABASE IDENTIFIER($FULL_PREFIX);
SHOW STAGES IN SCHEMA RAW;

