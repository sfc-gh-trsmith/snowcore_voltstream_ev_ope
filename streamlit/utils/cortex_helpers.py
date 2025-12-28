"""
Cortex AI Helpers for VoltStream OPE Dashboard
===============================================

Wrappers for Snowflake Cortex AI services including:
- Cortex Complete (LLM inference)
- Cortex Analyst (semantic model queries)
- Cortex Search (RAG over documents)

Following SNOWFLAKE_STREAMLIT_DEPLOYMENT_GUIDE.md prompting guidelines.
"""

import streamlit as st
from typing import Optional, Dict, Any
import json


def call_cortex_complete(
    session,
    prompt: str,
    model: str = "mistral-large",
    max_tokens: int = 500,
    temperature: float = 0.3
) -> str:
    """
    Call Cortex Complete for LLM inference.
    
    Automatically appends format instructions to prevent chatty responses.
    
    Args:
        session: Snowflake Snowpark session
        prompt: The prompt text (format instructions added automatically)
        model: Model name (mistral-large, llama3.1-70b, etc.)
        max_tokens: Maximum response tokens
        temperature: Sampling temperature (lower = more deterministic)
    
    Returns:
        LLM response text
    """
    # Append format instructions per deployment guide
    formatted_prompt = f"""{prompt}

Output only the analysis. No preamble, headers, or follow-up questions."""
    
    # Escape single quotes for SQL
    safe_prompt = formatted_prompt.replace("'", "''")
    
    try:
        result = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                '{model}',
                '{safe_prompt}'
            ) AS response
        """).collect()
        
        if result and len(result) > 0:
            return result[0]['RESPONSE']
        return "Unable to generate response."
    except Exception as e:
        return f"Error calling Cortex Complete: {e}"


def call_cortex_analyst(
    session,
    question: str,
    semantic_model_path: str = "@VOLTSTREAM_EV_OPE.EV_OPE.SEMANTIC_MODELS/ope_semantic_model.yaml"
) -> Dict[str, Any]:
    """
    Call Cortex Analyst to query data using natural language.
    
    Uses the _snowflake.send_message() API for Streamlit in Snowflake.
    
    Args:
        session: Snowflake Snowpark session
        question: Natural language question about the data
        semantic_model_path: Path to semantic model YAML in stage
    
    Returns:
        Dict with 'sql' (generated query) and 'result' (DataFrame) keys
    """
    try:
        import _snowflake
        
        # Build the message for Cortex Analyst
        message = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
            "semantic_model_file": semantic_model_path
        }
        
        # Call Cortex Analyst via _snowflake API
        response = _snowflake.send_message("analyst", message)
        
        # Parse response - it may be a string or dict
        if isinstance(response, str):
            response = json.loads(response)
        
        # Extract the content from the response
        content = response.get("message", {}).get("content", [])
        
        sql = ""
        text_message = ""
        
        for item in content:
            if item.get("type") == "sql":
                sql = item.get("statement", "")
            elif item.get("type") == "text":
                text_message = item.get("text", "")
        
        # Execute the generated SQL if available
        if sql:
            data_result = session.sql(sql).to_pandas()
            return {
                'sql': sql,
                'result': data_result,
                'message': text_message,
                'success': True
            }
        else:
            return {
                'sql': '',
                'result': None,
                'message': text_message or 'No SQL generated',
                'success': False
            }
        
    except ImportError:
        # _snowflake not available (running outside Streamlit in Snowflake)
        return {
            'sql': '',
            'result': None,
            'message': 'Cortex Analyst is only available in Streamlit in Snowflake',
            'success': False
        }
    except Exception as e:
        return {
            'sql': '',
            'result': None,
            'message': f"Error: {e}",
            'success': False
        }


def call_cortex_search(
    session,
    query: str,
    service_name: str = "VOLTSTREAM_EV_OPE.EV_OPE.MFG_KNOWLEDGE_BASE_SEARCH",
    limit: int = 5,
    columns: Optional[list] = None
) -> list:
    """
    Call Cortex Search for RAG over documents.
    
    Args:
        session: Snowflake Snowpark session
        query: Search query text
        service_name: Fully qualified Cortex Search service name
        limit: Maximum results to return
        columns: Columns to retrieve (defaults to CHUNK_TEXT, DOCUMENT_NAME, ERROR_CODE_TAG)
    
    Returns:
        List of search results with content and metadata
    """
    # Default columns for the MFG knowledge base
    if columns is None:
        columns = ["CHUNK_TEXT", "DOCUMENT_NAME", "ERROR_CODE_TAG"]
    
    # Build the search request JSON object
    search_request = {
        "query": query,
        "columns": columns,
        "limit": limit
    }
    
    # Escape single quotes in the JSON string for SQL
    request_json = json.dumps(search_request).replace("'", "''")
    
    try:
        result = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                '{service_name}',
                '{request_json}'
            ) AS results
        """).collect()
        
        if result and len(result) > 0:
            # Parse the response - it returns a JSON object with 'results' array
            response = result[0]['RESULTS']
            if isinstance(response, str):
                response = json.loads(response)
            
            # Extract the results array from the response
            if isinstance(response, dict) and 'results' in response:
                return response['results']
            elif isinstance(response, list):
                return response
            return []
        return []
        
    except Exception as e:
        # Return empty list on error - Cortex Search may not be set up
        return []


def generate_ope_insight(
    session,
    metric_name: str,
    current_value: float,
    target_value: float,
    trend: str = "stable"
) -> str:
    """
    Generate an AI insight for an OPE metric.
    
    Args:
        session: Snowflake Snowpark session
        metric_name: Name of the metric (e.g., "OPE", "Starvation Time")
        current_value: Current metric value
        target_value: Target/baseline value
        trend: "up", "down", or "stable"
    
    Returns:
        2-3 sentence insight text
    """
    delta = current_value - target_value
    delta_pct = (delta / target_value * 100) if target_value != 0 else 0
    
    prompt = f"""You are a manufacturing operations analyst. Provide a brief insight about this metric.

Metric: {metric_name}
Current Value: {current_value:.1f}
Target Value: {target_value:.1f}
Delta: {delta:+.1f} ({delta_pct:+.1f}%)
Trend: {trend}

Provide 2-3 sentences explaining the significance and any recommended actions."""
    
    return call_cortex_complete(session, prompt, temperature=0.2)


def generate_root_cause_analysis(
    session,
    context: Dict[str, Any]
) -> str:
    """
    Generate AI-powered root cause analysis for production issues.
    
    Args:
        session: Snowflake Snowpark session
        context: Dict with keys like 'ope_drop', 'humidity', 'dust', 'failures'
    
    Returns:
        Root cause analysis text
    """
    prompt = f"""You are a Jidoka (automation with human intelligence) coordinator for an EV Gigafactory.

Analyze this production anomaly:
- OPE dropped to: {context.get('ope', 'N/A')}%
- Current humidity: {context.get('humidity', 'N/A')}%
- Current dust PM2.5: {context.get('dust', 'N/A')} µg/m³
- AGV failures: {context.get('failures', 'N/A')}
- AGV-ERR-99 (sensor errors): {context.get('sensor_errors', 'N/A')}

Identify the root cause chain and provide a specific corrective action."""
    
    return call_cortex_complete(session, prompt, temperature=0.1)

