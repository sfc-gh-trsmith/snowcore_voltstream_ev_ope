#!/bin/bash
###############################################################################
# run.sh - Runtime operations for VoltStream OPE
#
# Commands:
#   main       - Execute the AGV failure prediction notebook
#   test       - Run query test suite (validates all Streamlit queries)
#   status     - Check status of deployed resources
#   streamlit  - Get Streamlit app URL
#
# Usage:
#   ./run.sh main                    # Execute notebook
#   ./run.sh test                    # Run query tests
#   ./run.sh status                  # Check resource status
#   ./run.sh streamlit               # Get Streamlit URL
#   ./run.sh -c prod main            # Use 'prod' connection
###############################################################################

set -e
set -o pipefail

# =============================================================================
# Configuration
# =============================================================================

CONNECTION_NAME="demo"           # Default Snowflake CLI connection
ENV_PREFIX=""                    # Optional environment prefix (DEV, PROD)
COMMAND=""                       # Command to execute

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
Usage: $0 [OPTIONS] COMMAND

Runtime operations for VoltStream OPE Intelligent Jidoka System.

Commands:
  main         Execute the AGV failure prediction notebook
  test         Run query test suite (validates all Streamlit queries)
  status       Check status of deployed resources
  streamlit    Get Streamlit app URL

Options:
  -c, --connection NAME    Snowflake CLI connection name (default: demo)
  -p, --prefix PREFIX      Environment prefix for resources (e.g., DEV, PROD)
  -h, --help               Show this help message

Examples:
  $0 main                  # Execute notebook
  $0 test                  # Run query tests
  $0 status                # Check resource status
  $0 streamlit             # Get Streamlit URL
  $0 -c prod main          # Use 'prod' connection
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
        main|test|status|streamlit)
            COMMAND="$1"
            shift
            ;;
        *)
            error_exit "Unknown option: $1\nUse --help for usage information"
            ;;
    esac
done

# Require a command
if [ -z "$COMMAND" ]; then
    usage
fi

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
NOTEBOOK_NAME="${FULL_PREFIX}_AGV_FAILURE_PREDICTION"
STREAMLIT_APP="VOLTSTREAM_OPE_DASHBOARD"

# =============================================================================
# Command: main - Execute notebook
# =============================================================================

cmd_main() {
    echo "=================================================="
    echo "VoltStream OPE - Execute Notebook"
    echo "=================================================="
    echo ""
    echo "Configuration:"
    echo "  Connection: $CONNECTION_NAME"
    echo "  Database: $DB_NAME"
    echo "  Notebook: $NOTEBOOK_NAME"
    echo ""
    
    log_info "Executing AGV failure prediction notebook (synchronous)..."
    log_info "Waiting for notebook to complete..."
    echo ""
    
    # EXECUTE NOTEBOOK with () runs synchronously and waits for completion
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE_NAME};
        USE DATABASE ${DB_NAME};
        USE SCHEMA EV_OPE;
        USE WAREHOUSE ${WH_NAME};
        
        EXECUTE NOTEBOOK ${NOTEBOOK_NAME}();
    " 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "Notebook execution completed successfully"
    else
        error_exit "Notebook execution failed"
    fi
}

# =============================================================================
# Command: test - Run query test suite
# =============================================================================

cmd_test() {
    echo "=================================================="
    echo "VoltStream OPE - Query Test Suite"
    echo "=================================================="
    echo ""
    
    log_info "Running query tests against Snowflake..."
    
    cd streamlit
    
    # Run tests using Python with Snowflake connection
    python3 tests/test_queries.py \
        --connection "$CONNECTION_NAME" \
        --database "$DB_NAME" \
        --schema "EV_OPE" \
        --role "$ROLE_NAME" \
        --warehouse "$WH_NAME"
    
    TEST_EXIT=$?
    cd ..
    
    echo ""
    if [ $TEST_EXIT -eq 0 ]; then
        log_success "All query tests passed"
    else
        echo -e "${RED}[FAIL]${NC} Query tests failed"
        exit 1
    fi
}

# =============================================================================
# Command: status - Check resource status
# =============================================================================

cmd_status() {
    echo "=================================================="
    echo "VoltStream OPE - Status"
    echo "=================================================="
    echo ""
    echo "Configuration:"
    echo "  Connection: $CONNECTION_NAME"
    echo "  Database: $DB_NAME"
    echo "  Role: $ROLE_NAME"
    echo "  Warehouse: $WH_NAME"
    echo ""
    
    # Check warehouse status
    echo "Warehouse Status:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "SHOW WAREHOUSES LIKE '${WH_NAME}';" 2>/dev/null \
        || echo "  Not found or no access"
    echo ""
    
    # Check notebook status
    echo "Notebook Status:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE_NAME};
        USE DATABASE ${DB_NAME};
        USE SCHEMA EV_OPE;
        SHOW NOTEBOOKS LIKE '${NOTEBOOK_NAME}';
    " 2>/dev/null || echo "  Not found or no access"
    echo ""
    
    # Check Streamlit app
    echo "Streamlit App Status:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE_NAME};
        USE DATABASE ${DB_NAME};
        USE SCHEMA EV_OPE;
        SHOW STREAMLITS LIKE '${STREAMLIT_APP}';
    " 2>/dev/null || echo "  Not found or no access"
    echo ""
    
    # Check table row counts
    echo "Table Row Counts:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE_NAME};
        USE DATABASE ${DB_NAME};
        USE SCHEMA EV_OPE;
        USE WAREHOUSE ${WH_NAME};
        
        SELECT 'OPE_DAILY_FACT' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM OPE_DAILY_FACT
        UNION ALL
        SELECT 'AGV_FAILURE_ANALYSIS', COUNT(*) FROM AGV_FAILURE_ANALYSIS
        UNION ALL
        SELECT 'PREDICTIVE_MAINTENANCE_ALERTS', COUNT(*) FROM PREDICTIVE_MAINTENANCE_ALERTS
        ORDER BY TABLE_NAME;
    " 2>/dev/null || echo "  Error querying tables"
    echo ""
    
    # Check Cortex Search service
    echo "Cortex Search Service:"
    echo "------------------------------------------------"
    snow sql $SNOW_CONN -q "
        USE ROLE ${ROLE_NAME};
        USE DATABASE ${DB_NAME};
        USE SCHEMA EV_OPE;
        SHOW CORTEX SEARCH SERVICES;
    " 2>/dev/null || echo "  Not found or no access"
}

# =============================================================================
# Command: streamlit - Get Streamlit URL
# =============================================================================

cmd_streamlit() {
    echo "=================================================="
    echo "VoltStream OPE - Streamlit Dashboard"
    echo "=================================================="
    echo ""
    
    # Try to get URL
    URL=$(snow streamlit get-url $STREAMLIT_APP \
        $SNOW_CONN \
        --database $DB_NAME \
        --schema EV_OPE \
        --role $ROLE_NAME 2>/dev/null) || true
    
    if [ -n "$URL" ]; then
        echo "Streamlit Dashboard URL:"
        echo ""
        echo "  $URL"
        echo ""
        log_success "URL retrieved successfully"
    else
        log_warning "Could not retrieve URL automatically."
        echo ""
        echo "To open the dashboard:"
        echo "  1. Go to Snowsight (https://app.snowflake.com)"
        echo "  2. Navigate to: Projects > Streamlit"
        echo "  3. Open: $STREAMLIT_APP"
        echo ""
        echo "Or try manually:"
        echo "  snow streamlit get-url $STREAMLIT_APP -c $CONNECTION_NAME --database $DB_NAME --schema EV_OPE --role $ROLE_NAME"
    fi
}

# =============================================================================
# Execute Command
# =============================================================================

case $COMMAND in
    main)
        cmd_main
        ;;
    test)
        cmd_test
        ;;
    status)
        cmd_status
        ;;
    streamlit)
        cmd_streamlit
        ;;
    *)
        error_exit "Unknown command: $COMMAND"
        ;;
esac
