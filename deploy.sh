#!/bin/bash
###############################################################################
# deploy.sh - Deploy VoltStream EV OPE to Snowflake
#
# Deploys the complete OPE Intelligent Jidoka System:
#   1. Account infrastructure (role, warehouse, database, schemas)
#   2. RAW layer tables (CDC staging)
#   3. ATOMIC layer tables (enterprise relational model)
#   4. EV_OPE data mart views (dimensional model)
#   5. Upload unstructured documents to stages
#   6. Generate synthetic data via Snowpark notebook (direct to RAW/ATOMIC)
#   7. ETL: Transform RAW to ATOMIC
#   8. Deploy ML Snowflake Notebook
#   9. Cortex Search service
#   10. Semantic model upload
#   11. Streamlit application
#
# Medallion Architecture:
#   RAW (Bronze)    <- Notebook generates data directly here
#   ATOMIC (Silver) <- Enterprise relational model (ETL from RAW)
#   EV_OPE (Gold)   <- Dimensional views over ATOMIC
#
# Usage:
#   ./deploy.sh                      # Full deployment with default connection
#   ./deploy.sh -c demo              # Use 'demo' connection
#   ./deploy.sh --prefix DEV         # Deploy with DEV_ prefix
#   ./deploy.sh --only-streamlit     # Deploy only Streamlit app
#   ./deploy.sh --skip-data          # Skip data generation
###############################################################################

set -e
set -o pipefail

# =============================================================================
# Configuration
# =============================================================================

CONNECTION_NAME="demo"           # Default Snowflake CLI connection
ENV_PREFIX=""                    # Optional environment prefix (DEV, PROD)
SKIP_DATA=false                  # Skip data generation flag
ONLY_COMPONENT=""                # Empty means deploy all

# Project settings (base names)
PROJECT_PREFIX="VOLTSTREAM_EV_OPE"

# Get script directory (for relative paths)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# =============================================================================
# Colors
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# =============================================================================
# Helper Functions
# =============================================================================

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy VoltStream EV OPE Intelligent Jidoka System to Snowflake.

Options:
  -c, --connection NAME    Snowflake CLI connection name (default: demo)
  -p, --prefix PREFIX      Environment prefix for resources (e.g., DEV, PROD)
  --skip-data              Skip synthetic data generation and upload
  --only-sql               Deploy only SQL infrastructure
  --only-data              Deploy only data (upload, load, and ETL)
  --only-notebook          Deploy only the Snowflake Notebook
  --only-streamlit         Deploy only the Streamlit app
  --only-cortex            Deploy only Cortex Search service
  --only-agent             Deploy only the Cortex Agent
  -h, --help               Show this help message

Examples:
  $0                       # Full deployment
  $0 -c prod               # Use 'prod' connection
  $0 --prefix DEV          # Deploy with DEV_ prefix
  $0 --only-streamlit      # Redeploy just the Streamlit app
  $0 --only-notebook       # Redeploy just the Notebook
EOF
    exit 0
}

error_exit() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Helper function to check if a step should run
should_run_step() {
    local step_name="$1"
    # If no specific component requested, run all steps
    if [ -z "$ONLY_COMPONENT" ]; then
        return 0
    fi
    # Check if this step matches the requested component
    case "$ONLY_COMPONENT" in
        sql)
            [[ "$step_name" == "account_sql" || "$step_name" == "raw_sql" || "$step_name" == "atomic_sql" || "$step_name" == "ev_ope_sql" ]]
            ;;
        data)
            [[ "$step_name" == "upload_docs" || "$step_name" == "generate_data" || "$step_name" == "etl" ]]
            ;;
        notebook)
            [[ "$step_name" == "ml_notebook" ]]
            ;;
        streamlit)
            [[ "$step_name" == "streamlit" || "$step_name" == "semantic_model" ]]
            ;;
        cortex)
            [[ "$step_name" == "cortex_search" ]]
            ;;
        agent)
            [[ "$step_name" == "cortex_agent" ]]
            ;;
        *)
            return 1
            ;;
    esac
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -c|--connection)
            CONNECTION_NAME="$2"
            shift 2
            ;;
        -p|--prefix)
            ENV_PREFIX="$2"
            shift 2
            ;;
        --skip-data)
            SKIP_DATA=true
            shift
            ;;
        --only-sql)
            ONLY_COMPONENT="sql"
            shift
            ;;
        --only-data)
            ONLY_COMPONENT="data"
            shift
            ;;
        --only-notebook)
            ONLY_COMPONENT="notebook"
            shift
            ;;
        --only-streamlit)
            ONLY_COMPONENT="streamlit"
            shift
            ;;
        --only-cortex)
            ONLY_COMPONENT="cortex"
            shift
            ;;
        --only-agent)
            ONLY_COMPONENT="agent"
            shift
            ;;
        *)
            error_exit "Unknown option: $1\nUse --help for usage information"
            ;;
    esac
done

# =============================================================================
# Compute Resource Names
# =============================================================================

# Build connection string
SNOW_CONN="-c $CONNECTION_NAME"

# Compute full prefix (adds underscore only if prefix provided)
if [ -n "$ENV_PREFIX" ]; then
    FULL_PREFIX="${ENV_PREFIX}_${PROJECT_PREFIX}"
else
    FULL_PREFIX="${PROJECT_PREFIX}"
fi

# Derive all resource names
DB_NAME="${FULL_PREFIX}"
ROLE_NAME="${FULL_PREFIX}_ROLE"
WH_NAME="${FULL_PREFIX}_WH"

# =============================================================================
# Display Configuration
# =============================================================================

echo ""
echo "=================================================="
echo "  VoltStream OPE - Deployment"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  Connection: $CONNECTION_NAME"
if [ -n "$ENV_PREFIX" ]; then
    echo "  Environment Prefix: $ENV_PREFIX"
fi
if [ -n "$ONLY_COMPONENT" ]; then
    echo "  Deploy Only: $ONLY_COMPONENT"
fi
if [ "$SKIP_DATA" = true ]; then
    echo "  Skip Data: Yes"
fi
echo ""
echo "  Database: $DB_NAME"
echo "  Role: $ROLE_NAME"
echo "  Warehouse: $WH_NAME"
echo ""
echo "  Architecture: RAW (Bronze) -> ATOMIC (Silver) -> EV_OPE (Gold)"
echo ""

# =============================================================================
# Step 1: Check Prerequisites
# =============================================================================

echo "Step 1: Checking prerequisites..."
echo "------------------------------------------------"

# Check for snow CLI
if ! command -v snow &> /dev/null; then
    error_exit "Snowflake CLI (snow) not found. Install with: pip install snowflake-cli"
fi
log_success "Snowflake CLI found"

# Test Snowflake connection
echo "Testing Snowflake connection..."
if ! snow sql $SNOW_CONN -q "SELECT 1" &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Failed to connect to Snowflake"
    snow connection test $SNOW_CONN 2>&1 || true
    exit 1
fi
log_success "Connection '$CONNECTION_NAME' verified"

# Check required files
for file in "sql/01_account_setup.sql" "sql/02_raw_schema.sql" "sql/03_atomic_schema.sql" "sql/03b_raw_to_atomic.sql" "sql/04_ev_ope_schema.sql"; do
    if [ ! -f "$file" ]; then
        error_exit "Required file not found: $file"
    fi
done
log_success "Required SQL files present"
echo ""

# =============================================================================
# Step 2: Account-Level SQL Setup
# =============================================================================

if should_run_step "account_sql"; then
    echo "Step 2: Running account-level SQL setup..."
    echo "------------------------------------------------"
    
    {
        echo "-- Set session variables for account-level objects"
        echo "SET PROJECT_DB = '${DB_NAME}';"
        echo "SET PROJECT_WH = '${WH_NAME}';"
        echo "SET PROJECT_ROLE = '${ROLE_NAME}';"
        echo "SET FULL_PREFIX = '${DB_NAME}';"
        echo ""
        cat sql/01_account_setup.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        log_success "Account-level setup completed"
    else
        error_exit "Account-level SQL setup failed"
    fi
    echo ""
else
    echo "Step 2: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 3: RAW Layer Tables
# =============================================================================

if should_run_step "raw_sql"; then
    echo "Step 3: Creating RAW layer tables..."
    echo "------------------------------------------------"
    
    {
        echo "USE ROLE ${ROLE_NAME};"
        echo "USE DATABASE ${DB_NAME};"
        echo "USE WAREHOUSE ${WH_NAME};"
        echo ""
        cat sql/02_raw_schema.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        log_success "RAW layer created (Bronze)"
    else
        error_exit "RAW layer setup failed"
    fi
    echo ""
else
    echo "Step 3: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 4: ATOMIC Layer Tables (Enterprise Relational Model)
# =============================================================================

if should_run_step "atomic_sql"; then
    echo "Step 4: Creating ATOMIC layer tables (Enterprise Relational Model)..."
    echo "------------------------------------------------"
    
    {
        echo "USE ROLE ${ROLE_NAME};"
        echo "USE DATABASE ${DB_NAME};"
        echo "USE WAREHOUSE ${WH_NAME};"
        echo ""
        cat sql/03_atomic_schema.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        log_success "ATOMIC layer created (Silver)"
    else
        error_exit "ATOMIC layer setup failed"
    fi
    echo ""
else
    echo "Step 4: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 5: EV_OPE Data Mart Views (Dimensional Model)
# =============================================================================

if should_run_step "ev_ope_sql"; then
    echo "Step 5: Creating EV_OPE data mart views (Dimensional Model)..."
    echo "------------------------------------------------"
    
    {
        echo "USE ROLE ${ROLE_NAME};"
        echo "USE DATABASE ${DB_NAME};"
        echo "USE WAREHOUSE ${WH_NAME};"
        echo ""
        cat sql/04_ev_ope_schema.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        log_success "EV_OPE data mart created (Gold)"
    else
        error_exit "EV_OPE layer setup failed"
    fi
    echo ""
else
    echo "Step 5: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 6: Upload Unstructured Documents to Stages
# =============================================================================

if should_run_step "upload_docs" && [ "$SKIP_DATA" = false ]; then
    echo "Step 6: Uploading unstructured documents to stages..."
    echo "------------------------------------------------"
    
    # Upload unstructured documents using PUT command
    doc_files=(data/unstructured/*.md)
    doc_count=0
    for f in "${doc_files[@]}"; do
        [ -f "$f" ] && ((doc_count++))
    done
    doc_current=0
    
    echo "Uploading $doc_count unstructured documents..."
    echo ""
    
    for file in "${doc_files[@]}"; do
        if [ -f "$file" ]; then
            ((doc_current++))
            filename=$(basename "$file")
            filesize=$(ls -lh "$file" | awk '{print $5}')
            abs_path="$(cd "$(dirname "$file")" && pwd)/$(basename "$file")"
            
            echo "($doc_current/$doc_count) $filename ($filesize)"
            
            # Use PUT command for documents
            snow sql $SNOW_CONN -q "
                PUT 'file://${abs_path}' '@${DB_NAME}.RAW.DOCS_STAGE/unstructured/'
                AUTO_COMPRESS = TRUE
                OVERWRITE = TRUE;
            "
            if [ $? -eq 0 ]; then
                log_success "Uploaded $filename"
            else
                log_warning "Failed to upload $filename"
            fi
        fi
    done
    
    echo ""
    log_success "Document upload completed"
    echo ""
elif [ "$SKIP_DATA" = true ]; then
    echo "Step 6: Skipped (--skip-data flag)"
    echo ""
else
    echo "Step 6: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 7: Generate Synthetic Data via Snowpark Notebook
# =============================================================================
# The generate_synthetic_data.ipynb notebook runs in Snowflake and inserts
# directly into RAW tables and ATOMIC dimension tables. Much faster than
# CSV upload approach.

if should_run_step "generate_data" && [ "$SKIP_DATA" = false ]; then
    echo "Step 7: Generating synthetic data via Snowpark notebook..."
    echo "------------------------------------------------"
    
    DATA_GEN_NOTEBOOK="notebooks/generate_synthetic_data.ipynb"
    DATA_GEN_NOTEBOOK_NAME="${FULL_PREFIX}_GENERATE_SYNTHETIC_DATA"
    
    if [ -f "$DATA_GEN_NOTEBOOK" ]; then
        # Upload notebook to stage
        snow stage copy \
            "$DATA_GEN_NOTEBOOK" \
            "@${DB_NAME}.EV_OPE.NOTEBOOKS/" \
            $SNOW_CONN \
            --overwrite \
            2>&1 && log_success "Data generation notebook uploaded"
        
        # Create the notebook object
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE_NAME};
            USE DATABASE ${DB_NAME};
            USE SCHEMA EV_OPE;
            USE WAREHOUSE ${WH_NAME};
            
            CREATE OR REPLACE NOTEBOOK ${DATA_GEN_NOTEBOOK_NAME}
            FROM '@${DB_NAME}.EV_OPE.NOTEBOOKS/'
            MAIN_FILE = 'generate_synthetic_data.ipynb'
            QUERY_WAREHOUSE = '${WH_NAME}';
            
            ALTER NOTEBOOK ${DATA_GEN_NOTEBOOK_NAME} ADD LIVE VERSION FROM LAST;
        " 2>&1 && log_success "Data generation notebook created: ${DATA_GEN_NOTEBOOK_NAME}"
        
        # Execute the notebook to generate data
        log_info "Executing notebook to generate synthetic data (this may take several minutes)..."
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE_NAME};
            USE DATABASE ${DB_NAME};
            USE SCHEMA EV_OPE;
            USE WAREHOUSE ${WH_NAME};
            
            EXECUTE NOTEBOOK ${DATA_GEN_NOTEBOOK_NAME}();
        " 2>&1 && log_success "Synthetic data generated successfully" \
               || log_warning "Notebook execution failed - you may need to run it manually in Snowsight"
    else
        error_exit "Data generation notebook not found: $DATA_GEN_NOTEBOOK"
    fi
    echo ""
elif [ "$SKIP_DATA" = true ]; then
    echo "Step 7: Skipped (--skip-data flag)"
    echo ""
else
    echo "Step 7: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 8: ETL - Transform RAW to ATOMIC
# =============================================================================
# Note: ATOMIC.ASSET and ATOMIC.PRODUCT are already populated by the data 
# generation notebook. This ETL transforms RAW transactional tables to ATOMIC.

if should_run_step "etl" && [ "$SKIP_DATA" = false ]; then
    echo "Step 8: Running ETL - RAW to ATOMIC transformation..."
    echo "------------------------------------------------"
    
    {
        echo "USE ROLE ${ROLE_NAME};"
        echo "USE DATABASE ${DB_NAME};"
        echo "USE WAREHOUSE ${WH_NAME};"
        echo ""
        cat sql/03b_raw_to_atomic.sql
    } | snow sql $SNOW_CONN -i
    
    if [ $? -eq 0 ]; then
        log_success "RAW to ATOMIC ETL completed"
    else
        error_exit "RAW to ATOMIC ETL failed"
    fi
    echo ""
elif [ "$SKIP_DATA" = true ]; then
    echo "Step 8: Skipped (--skip-data flag)"
    echo ""
else
    echo "Step 8: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 9: Deploy ML Snowflake Notebook (AGV Failure Prediction)
# =============================================================================

if should_run_step "ml_notebook"; then
    echo "Step 9: Deploying ML Snowflake Notebook..."
    echo "------------------------------------------------"
    
    NOTEBOOK_FILE="notebooks/agv_failure_prediction.ipynb"
    NOTEBOOK_NAME="${FULL_PREFIX}_AGV_FAILURE_PREDICTION"
    
    if [ -f "$NOTEBOOK_FILE" ]; then
        # Upload notebook to stage
        snow stage copy \
            "$NOTEBOOK_FILE" \
            "@${DB_NAME}.EV_OPE.NOTEBOOKS/" \
            $SNOW_CONN \
            --overwrite \
            2>&1 && log_success "ML notebook uploaded to stage"
        
        # Upload environment.yml (CRITICAL for package resolution)
        if [ -f "notebooks/environment.yml" ]; then
            snow stage copy \
                "notebooks/environment.yml" \
                "@${DB_NAME}.EV_OPE.NOTEBOOKS/" \
                $SNOW_CONN \
                --overwrite \
                2>&1 && log_success "Environment config uploaded"
        else
            log_warning "environment.yml not found - notebook may fail to resolve dependencies"
        fi
        
        # Create or replace the notebook
        snow sql $SNOW_CONN -q "
            USE ROLE ${ROLE_NAME};
            USE DATABASE ${DB_NAME};
            USE SCHEMA EV_OPE;
            USE WAREHOUSE ${WH_NAME};
            
            CREATE OR REPLACE NOTEBOOK ${NOTEBOOK_NAME}
            FROM '@${DB_NAME}.EV_OPE.NOTEBOOKS/'
            MAIN_FILE = 'agv_failure_prediction.ipynb'
            QUERY_WAREHOUSE = '${WH_NAME}';
            
            ALTER NOTEBOOK ${NOTEBOOK_NAME} ADD LIVE VERSION FROM LAST;
        " 2>&1 && log_success "ML notebook deployed: ${NOTEBOOK_NAME}" \
               || log_warning "ML notebook deployment failed (may need manual setup)"
    else
        log_warning "ML notebook file not found: $NOTEBOOK_FILE"
    fi
    echo ""
else
    echo "Step 9: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 10: Create Cortex Search Service
# =============================================================================

if should_run_step "cortex_search"; then
    echo "Step 10: Creating Cortex Search service..."
    echo "------------------------------------------------"
    
    {
        echo "USE ROLE ${ROLE_NAME};"
        echo "USE DATABASE ${DB_NAME};"
        echo "USE WAREHOUSE ${WH_NAME};"
        echo "SET PROJECT_WH = '${WH_NAME}';"
        echo ""
        cat sql/05_cortex_search.sql
    } | snow sql $SNOW_CONN -i 2>&1 && log_success "Cortex Search service created" \
                                    || log_warning "Cortex Search setup failed (may require manual setup)"
    echo ""
else
    echo "Step 10: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 11: Upload Semantic Model
# =============================================================================

if should_run_step "semantic_model"; then
    echo "Step 11: Uploading semantic model..."
    echo "------------------------------------------------"
    
    if [ -f "semantic_views/ope_semantic_model.yaml" ]; then
        snow stage copy \
            "semantic_views/ope_semantic_model.yaml" \
            "@${DB_NAME}.EV_OPE.SEMANTIC_MODELS/" \
            $SNOW_CONN \
            --overwrite \
            2>&1 && log_success "Semantic model uploaded" \
                 || log_warning "Semantic model upload failed"
    else
        log_warning "Semantic model file not found"
    fi
    echo ""
else
    echo "Step 11: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 12: Deploy Streamlit App
# =============================================================================

if should_run_step "streamlit"; then
    echo "Step 12: Deploying Streamlit app..."
    echo "------------------------------------------------"
    
    # Complete cleanup - drop EVERYTHING for fresh start
    echo "Performing complete Streamlit cleanup..."
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE_NAME};
        USE DATABASE ${DB_NAME};
        USE SCHEMA EV_OPE;
        DROP STREAMLIT IF EXISTS VOLTSTREAM_OPE_DASHBOARD;
        DROP STAGE IF EXISTS streamlit;
    " 2>/dev/null || true
    
    # Clear ALL local caches (recursive to catch all __pycache__ directories)
    rm -rf streamlit/output 2>/dev/null || true
    find streamlit -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find streamlit -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Deploy from streamlit directory
    cd streamlit
    
    snow streamlit deploy \
        $SNOW_CONN \
        --database $DB_NAME \
        --schema EV_OPE \
        --role $ROLE_NAME \
        --replace \
        2>&1 && log_success "Streamlit app deployed" \
             || log_warning "Streamlit deployment failed. You may need to deploy manually."
    
    cd ..
    echo ""
else
    echo "Step 12: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Step 13: Deploy Cortex Agent
# =============================================================================
# The Cortex Agent combines Cortex Analyst (semantic model) and Cortex Search
# tools into a unified conversational interface.
#
# Requires: SNOWFLAKE_PAT_TOKEN environment variable for REST API authentication

if should_run_step "cortex_agent"; then
    echo "Step 13: Deploying Cortex Agent..."
    echo "------------------------------------------------"
    
    AGENT_FILE="agents/VOLTSTREAM_EV_OPE_AGENT.json"
    
    if [ ! -f "$AGENT_FILE" ]; then
        log_warning "Agent configuration file not found: $AGENT_FILE"
    elif [ -z "$SNOWFLAKE_PAT_TOKEN" ]; then
        log_warning "SNOWFLAKE_PAT_TOKEN not set - skipping agent deployment"
        log_info "To deploy the agent, set: export SNOWFLAKE_PAT_TOKEN='your-pat-token'"
        log_info "Generate a PAT token in Snowsight: User Menu > Security > Programmatic Access Tokens"
    else
        # Extract account from snow CLI connection
        SNOW_ACCOUNT=$(snow connection list --format json 2>/dev/null | python3 -c "
import sys, json
try:
    conns = json.load(sys.stdin)
    for c in conns:
        if c.get('connection_name') == '$CONNECTION_NAME':
            print(c.get('parameters', {}).get('account', ''))
            break
except: pass
" 2>/dev/null)
        
        if [ -z "$SNOW_ACCOUNT" ]; then
            log_warning "Could not extract account from connection '$CONNECTION_NAME'"
            log_info "Set SNOWFLAKE_ACCOUNT environment variable or check your connection"
        else
            log_info "Using account: $SNOW_ACCOUNT"
            
            python3 utils/sf_cortex_agent_ops.py import \
                --input "$AGENT_FILE" \
                --replace \
                --account "$SNOW_ACCOUNT" \
                --pat-token "$SNOWFLAKE_PAT_TOKEN" \
                2>&1 && log_success "Cortex Agent deployed: ${FULL_PREFIX}_AGENT" \
                     || log_warning "Cortex Agent deployment failed. Check PAT token permissions."
        fi
    fi
    echo ""
else
    echo "Step 13: Skipped (--only-$ONLY_COMPONENT)"
    echo ""
fi

# =============================================================================
# Completion Summary
# =============================================================================

echo ""
echo "=================================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=================================================="
echo ""

if [ -n "$ONLY_COMPONENT" ]; then
    echo "Deployed component: $ONLY_COMPONENT"
else
    echo "Resources Created:"
    echo "  - Database: $DB_NAME"
    echo "  - Schemas:"
    echo "      RAW (Bronze)    - Landing zone for CDC data"
    echo "      ATOMIC (Silver) - Enterprise relational model"
    echo "      EV_OPE (Gold)   - Dimensional views for analytics"
    echo "  - Role: $ROLE_NAME"
    echo "  - Warehouse: $WH_NAME"
    echo ""
    echo "Data Flow:"
    echo "  1. Snowpark notebook generates data directly into RAW tables"
    echo "  2. Notebook also populates ATOMIC dimension tables (ASSET, PRODUCT)"
    echo "  3. ETL transforms RAW transactional data to ATOMIC tables"
    echo "  4. EV_OPE views project from ATOMIC (dimensional model)"
    echo ""
    echo "Next Steps:"
    echo "  1. Check deployment status:"
    echo "     ./run.sh status"
    echo ""
    echo "  2. Open the Streamlit dashboard:"
    echo "     ./run.sh streamlit"
    echo ""
    echo "  3. Quick data verification:"
    echo "     snow sql $SNOW_CONN -q \"SELECT * FROM $DB_NAME.EV_OPE.OPE_DAILY_FACT LIMIT 5;\""
fi
echo ""
