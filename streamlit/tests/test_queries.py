#!/usr/bin/env python3
"""
Query Test Runner for VoltStream OPE Dashboard
===============================================

Executes all registered queries from the query registry and validates:
1. Queries execute without errors
2. Queries return expected minimum row counts

Usage:
    python tests/test_queries.py --connection demo --database VOLTSTREAM_EV_OPE --schema EV_OPE

Or via run.sh:
    ./run.sh test
"""

import argparse
import sys
from typing import Tuple

# Add parent directory to path for imports
sys.path.insert(0, '.')

from utils.query_registry import get_registered_queries, QueryDefinition


def run_query_tests(
    connection: str,
    database: str,
    schema: str,
    role: str,
    warehouse: str
) -> Tuple[int, int]:
    """
    Run all registered queries and validate results.
    
    Args:
        connection: Snowflake CLI connection name
        database: Database name
        schema: Schema name
        role: Role name
        warehouse: Warehouse name
    
    Returns:
        Tuple of (passed_count, failed_count)
    """
    # Import Snowpark here to handle cases where it's not installed locally
    try:
        from snowflake.snowpark import Session
    except ImportError:
        print("ERROR: snowflake-snowpark-python not installed")
        print("Install with: pip install snowflake-snowpark-python")
        return 0, 1
    
    # Get all registered queries
    queries = get_registered_queries()
    
    if not queries:
        print("WARNING: No queries registered in query_registry.py")
        return 0, 0
    
    print(f"Found {len(queries)} registered queries to test")
    print("=" * 60)
    print()
    
    # Create Snowpark session using CLI connection
    try:
        session = Session.builder.configs({
            "connection_name": connection
        }).create()
        
        # Set context
        session.sql(f"USE ROLE {role}").collect()
        session.sql(f"USE DATABASE {database}").collect()
        session.sql(f"USE SCHEMA {schema}").collect()
        session.sql(f"USE WAREHOUSE {warehouse}").collect()
        
    except Exception as e:
        print(f"ERROR: Failed to create Snowflake session: {e}")
        return 0, 1
    
    passed = 0
    failed = 0
    
    for name, query_def in queries.items():
        print(f"Testing: {name}")
        print(f"  Description: {query_def.description}")
        
        try:
            # Execute query
            result = session.sql(query_def.sql).collect()
            row_count = len(result)
            
            # Check minimum row count
            if row_count >= query_def.min_rows:
                print(f"  Result: PASS ({row_count} rows, min={query_def.min_rows})")
                passed += 1
            else:
                print(f"  Result: FAIL (got {row_count} rows, expected >= {query_def.min_rows})")
                failed += 1
                
        except Exception as e:
            print(f"  Result: FAIL (error: {e})")
            failed += 1
        
        print()
    
    # Close session
    session.close()
    
    return passed, failed


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Run query tests for VoltStream OPE Dashboard"
    )
    parser.add_argument(
        "--connection", "-c",
        default="demo",
        help="Snowflake CLI connection name (default: demo)"
    )
    parser.add_argument(
        "--database", "-d",
        default="VOLTSTREAM_EV_OPE",
        help="Database name (default: VOLTSTREAM_EV_OPE)"
    )
    parser.add_argument(
        "--schema", "-s",
        default="EV_OPE",
        help="Schema name (default: EV_OPE)"
    )
    parser.add_argument(
        "--role", "-r",
        default="VOLTSTREAM_EV_OPE_ROLE",
        help="Role name (default: VOLTSTREAM_EV_OPE_ROLE)"
    )
    parser.add_argument(
        "--warehouse", "-w",
        default="VOLTSTREAM_EV_OPE_WH",
        help="Warehouse name (default: VOLTSTREAM_EV_OPE_WH)"
    )
    
    args = parser.parse_args()
    
    print()
    print("VoltStream OPE - Query Test Suite")
    print("=" * 60)
    print(f"Connection: {args.connection}")
    print(f"Database:   {args.database}")
    print(f"Schema:     {args.schema}")
    print(f"Role:       {args.role}")
    print(f"Warehouse:  {args.warehouse}")
    print("=" * 60)
    print()
    
    passed, failed = run_query_tests(
        connection=args.connection,
        database=args.database,
        schema=args.schema,
        role=args.role,
        warehouse=args.warehouse
    )
    
    # Print summary
    print("=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)
    
    # Exit with error code if any tests failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

