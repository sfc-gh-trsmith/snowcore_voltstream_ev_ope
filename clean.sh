#!/bin/bash
# =============================================================================
# clean.sh - VoltStream OPE Cleanup Script
# =============================================================================
# Removes all deployed resources from Snowflake.
#
# Usage: ./clean.sh [OPTIONS]
#
# Options:
#   -c, --connection NAME    Snowflake CLI connection name
#   --force, --yes, -y       Skip confirmation prompt
#   -h, --help               Show help message
# =============================================================================

set -e
set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DB_NAME="VOLTSTREAM_EV_OPE"
WH_NAME="VOLTSTREAM_EV_OPE_WH"
ROLE_NAME="VOLTSTREAM_EV_OPE_ROLE"

# Error handler function
error_exit() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Remove all VoltStream OPE resources from Snowflake.

Options:
  -c, --connection NAME    Snowflake CLI connection name (default: uses snow CLI default)
  --force, --yes, -y       Skip confirmation prompt
  -h, --help               Show this help message

Examples:
  $0                       # Interactive cleanup with confirmation
  $0 --force               # Skip confirmation prompt
  $0 -c prod --force       # Use 'prod' connection, skip confirmation
EOF
    exit 0
}

# Parse arguments
FORCE=false
CONNECTION_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -c|--connection)
            CONNECTION_NAME="$2"
            shift 2
            ;;
        --force|--yes|-y)
            FORCE=true
            shift
            ;;
        *)
            error_exit "Unknown option: $1\nUse --help for usage information"
            ;;
    esac
done

# Build connection string
if [ -n "$CONNECTION_NAME" ]; then
    SNOW_CONN="-c $CONNECTION_NAME"
else
    SNOW_CONN=""
fi

echo ""
echo -e "${RED}============================================================${NC}"
echo -e "${RED}  VoltStream OPE - CLEANUP SCRIPT${NC}"
echo -e "${RED}============================================================${NC}"
echo ""
echo -e "${YELLOW}WARNING: This will permanently delete:${NC}"
echo "  - Database: $DB_NAME (all schemas and data)"
echo "  - Warehouse: $WH_NAME"
echo "  - Role: $ROLE_NAME"
echo "  - All Cortex Search services"
echo "  - Streamlit application"
echo ""

if [ "$FORCE" = false ]; then
    read -p "Are you sure you want to delete all resources? (yes/no): " response
    if [ "$response" != "yes" ]; then
        echo -e "${GREEN}[INFO]${NC} Cleanup cancelled."
        exit 0
    fi
fi

echo ""
echo -e "${GREEN}[INFO]${NC} Starting cleanup..."

# Drop Streamlit app
echo -e "${GREEN}[INFO]${NC} Dropping Streamlit application..."
snow sql $SNOW_CONN -q "DROP STREAMLIT IF EXISTS $DB_NAME.EV_OPE.VOLTSTREAM_OPE_DASHBOARD;" 2>/dev/null || true

# Drop Cortex Search service
echo -e "${GREEN}[INFO]${NC} Dropping Cortex Search service..."
snow sql $SNOW_CONN -q "DROP CORTEX SEARCH SERVICE IF EXISTS $DB_NAME.EV_OPE.MFG_KNOWLEDGE_BASE_SEARCH;" 2>/dev/null || true

# Drop database (cascades all schemas and tables)
echo -e "${GREEN}[INFO]${NC} Dropping database..."
snow sql $SNOW_CONN -q "DROP DATABASE IF EXISTS $DB_NAME CASCADE;" 2>/dev/null || true

# Drop warehouse
echo -e "${GREEN}[INFO]${NC} Dropping warehouse..."
snow sql $SNOW_CONN -q "DROP WAREHOUSE IF EXISTS $WH_NAME;" 2>/dev/null || true

# Drop role
echo -e "${GREEN}[INFO]${NC} Dropping role..."
snow sql $SNOW_CONN -q "DROP ROLE IF EXISTS $ROLE_NAME;" 2>/dev/null || true

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Cleanup Complete${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  All VoltStream OPE resources have been removed."
echo ""
echo "  To redeploy: ./deploy.sh"
echo ""
