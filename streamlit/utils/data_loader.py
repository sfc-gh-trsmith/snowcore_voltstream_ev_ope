"""
Parallel Query Executor for VoltStream OPE Dashboard
=====================================================

Implements ThreadPoolExecutor pattern for parallel Snowflake queries.
Reduces page load time from sum of all query times to time of slowest query.

Following SNOWFLAKE_STREAMLIT_PARALLEL_QUERIES.md guidelines.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def run_queries_parallel(
    session,
    queries: Dict[str, str],
    max_workers: int = 4
) -> Dict[str, pd.DataFrame]:
    """
    Execute multiple independent SQL queries in parallel.
    
    FAIL-FAST: Any query failure raises an exception immediately.
    
    Args:
        session: Snowflake Snowpark session
        queries: Dict mapping names to SQL strings
        max_workers: Max concurrent queries (4 recommended for Snowflake)
    
    Returns:
        Dict mapping query names to result DataFrames
    
    Raises:
        RuntimeError: If any query fails
    """
    if not queries:
        return {}
    
    start_time = time.time()
    results: Dict[str, pd.DataFrame] = {}
    errors: list = []
    
    def execute_query(name: str, query: str) -> tuple:
        try:
            df = session.sql(query).to_pandas()
            if df is None:
                raise RuntimeError(f"Query '{name}' returned None")
            return name, df, None
        except Exception as e:
            logger.error(f"Query '{name}' failed: {e}")
            return name, None, str(e)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(execute_query, name, query): name
            for name, query in queries.items()
        }
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                query_name, result_df, error = future.result()
                if error:
                    errors.append(f"{query_name}: {error}")
                else:
                    results[query_name] = result_df
            except Exception as e:
                errors.append(f"{name}: {e}")
    
    # FAIL-FAST: Raise if any queries failed
    if errors:
        error_msg = f"Query execution failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)
    
    elapsed = time.time() - start_time
    logger.info(f"Parallel execution: {len(queries)} queries in {elapsed:.2f}s")
    return results


def run_single_query(session, sql: str, name: str = "query") -> pd.DataFrame:
    """
    Execute a single query with fail-fast error handling.
    
    Args:
        session: Snowflake Snowpark session
        sql: SQL query string
        name: Query name for error messages
    
    Returns:
        DataFrame with query results
    
    Raises:
        RuntimeError: If query fails
    """
    try:
        df = session.sql(sql).to_pandas()
        if df is None:
            raise RuntimeError(f"Query '{name}' returned None")
        return df
    except Exception as e:
        raise RuntimeError(f"Query '{name}' failed: {e}")


def convert_for_plotly(df: pd.DataFrame, columns: Optional[Dict[str, str]] = None) -> Dict:
    """
    Convert DataFrame columns to native Python types for Plotly SiS compatibility.
    
    Snowpark returns numpy types that may not serialize properly to Plotly JSON
    in Streamlit-in-Snowflake. This function converts to native Python types.
    
    Args:
        df: DataFrame with query results
        columns: Optional dict mapping column names to types ('float', 'int', 'str')
                 If not provided, converts all numeric to float and object to str
    
    Returns:
        Dict with column names as keys and native Python lists as values
    """
    result = {}
    
    if columns:
        for col, dtype in columns.items():
            if col in df.columns:
                if dtype == 'float':
                    result[col] = [float(v) if pd.notna(v) else 0.0 for v in df[col].tolist()]
                elif dtype == 'int':
                    result[col] = [int(v) if pd.notna(v) else 0 for v in df[col].tolist()]
                else:  # str
                    result[col] = [str(v) if pd.notna(v) else '' for v in df[col].tolist()]
    else:
        for col in df.columns:
            if df[col].dtype in ['int64', 'int32', 'int16', 'int8']:
                result[col] = [int(v) if pd.notna(v) else 0 for v in df[col].tolist()]
            elif df[col].dtype in ['float64', 'float32']:
                result[col] = [float(v) if pd.notna(v) else 0.0 for v in df[col].tolist()]
            else:
                result[col] = [str(v) if pd.notna(v) else '' for v in df[col].tolist()]
    
    return result

