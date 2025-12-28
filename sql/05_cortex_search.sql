-- =============================================================================
-- 05_cortex_search.sql - Cortex Search Service Setup
-- =============================================================================
-- Creates the MFG_KNOWLEDGE_BASE_SEARCH service for RAG over maintenance manuals
-- Indexes: AGV Maintenance Manual, Shift Reports, Dust Mitigation Protocol
-- =============================================================================

USE SCHEMA EV_OPE;

-- =============================================================================
-- DOCUMENT CHUNKING UDF
-- =============================================================================
-- This UDF reads markdown files from stage and splits them into chunks
-- for optimal retrieval. Uses LangChain-style recursive character splitting.

CREATE OR REPLACE FUNCTION CHUNK_MARKDOWN_DOCUMENT(file_url STRING)
RETURNS TABLE (
    chunk_text VARCHAR,
    chunk_index NUMBER,
    total_chunks NUMBER
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'MarkdownChunker'
PACKAGES = ('snowflake-snowpark-python')
AS
$$
from snowflake.snowpark.files import SnowflakeFile
import re

class MarkdownChunker:
    def __init__(self):
        self.chunk_size = 1500  # ~375 tokens
        self.chunk_overlap = 200
    
    def read_file(self, file_url: str) -> str:
        """Read markdown file content from Snowflake stage."""
        with SnowflakeFile.open(file_url, 'rb') as f:
            return f.read().decode('utf-8')
    
    def split_text(self, text: str) -> list:
        """Split text into overlapping chunks."""
        chunks = []
        
        # Split by sections first (## headers)
        sections = re.split(r'\n(?=## )', text)
        
        current_chunk = ""
        for section in sections:
            if len(current_chunk) + len(section) <= self.chunk_size:
                current_chunk += section + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap from end of previous
                if chunks:
                    overlap = chunks[-1][-self.chunk_overlap:] if len(chunks[-1]) > self.chunk_overlap else chunks[-1]
                    current_chunk = overlap + "\n" + section
                else:
                    current_chunk = section
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Further split any chunks that are still too large
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > self.chunk_size * 1.5:
                # Split by paragraphs
                paragraphs = chunk.split('\n\n')
                sub_chunk = ""
                for para in paragraphs:
                    if len(sub_chunk) + len(para) <= self.chunk_size:
                        sub_chunk += para + "\n\n"
                    else:
                        if sub_chunk:
                            final_chunks.append(sub_chunk.strip())
                        sub_chunk = para + "\n\n"
                if sub_chunk:
                    final_chunks.append(sub_chunk.strip())
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def process(self, file_url: str):
        """Process file and yield chunks."""
        try:
            content = self.read_file(file_url)
            chunks = self.split_text(content)
            total = len(chunks)
            
            for idx, chunk in enumerate(chunks):
                yield (chunk, idx + 1, total)
        except Exception as e:
            yield (f"Error processing file: {str(e)}", 0, 0)
$$;

-- =============================================================================
-- LOAD DOCUMENT CHUNKS FROM STAGE
-- =============================================================================
-- This assumes documents have been uploaded to RAW.DOCS_STAGE by deploy.sh

-- Clear existing chunks for idempotent reload
TRUNCATE TABLE DOCUMENT_CHUNKS;

-- Insert chunks from AGV Maintenance Manual
INSERT INTO DOCUMENT_CHUNKS (
    DOCUMENT_NAME, DOCUMENT_TYPE, EQUIPMENT_MODEL, ERROR_CODE_TAG,
    CHUNK_TEXT, CHUNK_INDEX, TOTAL_CHUNKS, FILE_URL
)
SELECT
    'AGV Fleet Maintenance Manual',
    'MAINTENANCE_MANUAL',
    'KUKA KMR-iiwa',
    CASE 
        WHEN func.chunk_text LIKE '%AGV-ERR-99%' THEN 'AGV-ERR-99'
        WHEN func.chunk_text LIKE '%AGV-ERR-01%' THEN 'AGV-ERR-01'
        WHEN func.chunk_text LIKE '%AGV-ERR-42%' THEN 'AGV-ERR-42'
        WHEN func.chunk_text LIKE '%AGV-ERR-55%' THEN 'AGV-ERR-55'
        ELSE NULL
    END AS error_code_tag,
    func.chunk_text,
    func.chunk_index,
    func.total_chunks,
    BUILD_SCOPED_FILE_URL(@RAW.DOCS_STAGE, 'unstructured/agv_maintenance_manual.md')
FROM TABLE(
    CHUNK_MARKDOWN_DOCUMENT(
        BUILD_SCOPED_FILE_URL(@RAW.DOCS_STAGE, 'unstructured/agv_maintenance_manual.md')
    )
) AS func
WHERE func.chunk_index > 0;

-- Insert chunks from Dust Mitigation Protocol
INSERT INTO DOCUMENT_CHUNKS (
    DOCUMENT_NAME, DOCUMENT_TYPE, EQUIPMENT_MODEL, ERROR_CODE_TAG,
    CHUNK_TEXT, CHUNK_INDEX, TOTAL_CHUNKS, FILE_URL
)
SELECT
    'Dust Mitigation Protocol',
    'SOP',
    'KUKA KMR-iiwa',
    CASE 
        WHEN func.chunk_text LIKE '%AGV-ERR-99%' THEN 'AGV-ERR-99'
        ELSE NULL
    END AS error_code_tag,
    func.chunk_text,
    func.chunk_index,
    func.total_chunks,
    BUILD_SCOPED_FILE_URL(@RAW.DOCS_STAGE, 'unstructured/dust_mitigation_protocol.md')
FROM TABLE(
    CHUNK_MARKDOWN_DOCUMENT(
        BUILD_SCOPED_FILE_URL(@RAW.DOCS_STAGE, 'unstructured/dust_mitigation_protocol.md')
    )
) AS func
WHERE func.chunk_index > 0;

-- Insert chunks from Shift Report Template
INSERT INTO DOCUMENT_CHUNKS (
    DOCUMENT_NAME, DOCUMENT_TYPE, EQUIPMENT_MODEL, ERROR_CODE_TAG,
    CHUNK_TEXT, CHUNK_INDEX, TOTAL_CHUNKS, FILE_URL
)
SELECT
    'Production Shift Report - 2024-12-10',
    'SHIFT_REPORT',
    'KUKA KMR-iiwa',
    CASE 
        WHEN func.chunk_text LIKE '%AGV-ERR-99%' THEN 'AGV-ERR-99'
        ELSE NULL
    END AS error_code_tag,
    func.chunk_text,
    func.chunk_index,
    func.total_chunks,
    BUILD_SCOPED_FILE_URL(@RAW.DOCS_STAGE, 'unstructured/shift_report_template.md')
FROM TABLE(
    CHUNK_MARKDOWN_DOCUMENT(
        BUILD_SCOPED_FILE_URL(@RAW.DOCS_STAGE, 'unstructured/shift_report_template.md')
    )
) AS func
WHERE func.chunk_index > 0;

-- Verify chunk loading
SELECT DOCUMENT_NAME, COUNT(*) AS CHUNK_COUNT, MAX(TOTAL_CHUNKS) AS TOTAL
FROM DOCUMENT_CHUNKS
GROUP BY DOCUMENT_NAME;

-- =============================================================================
-- CREATE CORTEX SEARCH SERVICE
-- =============================================================================
-- Service name: MFG_KNOWLEDGE_BASE_SEARCH
-- Indexes document chunks for semantic search

-- Note: IDENTIFIER($PROJECT_WH) causes internal error, use warehouse name directly
-- The warehouse is already set via USE WAREHOUSE in deploy.sh
CREATE OR REPLACE CORTEX SEARCH SERVICE MFG_KNOWLEDGE_BASE_SEARCH
ON CHUNK_TEXT
ATTRIBUTES DOCUMENT_NAME, DOCUMENT_TYPE, EQUIPMENT_MODEL, ERROR_CODE_TAG
WAREHOUSE = VOLTSTREAM_EV_OPE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT
        CHUNK_TEXT,
        DOCUMENT_NAME,
        DOCUMENT_TYPE,
        EQUIPMENT_MODEL,
        ERROR_CODE_TAG,
        FILE_URL,
        CHUNK_INDEX,
        TOTAL_CHUNKS
    FROM DOCUMENT_CHUNKS
);

-- =============================================================================
-- VERIFY SEARCH SERVICE
-- =============================================================================
SHOW CORTEX SEARCH SERVICES IN SCHEMA EV_OPE;

-- Test search query
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'MFG_KNOWLEDGE_BASE_SEARCH',
        '{
            "query": "What should I do when AGV-ERR-99 optical sensor error occurs?",
            "columns": ["CHUNK_TEXT", "DOCUMENT_NAME", "ERROR_CODE_TAG"],
            "limit": 3
        }'
    )
)['results'] AS search_results;

