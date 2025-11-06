"""SQL executor router with AI query generation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any
import requests
import pandas as pd

from config import Config
from models import get_engine

router = APIRouter()

class SQLQuery(BaseModel):
    """SQL query model."""
    query: str

class AIQueryRequest(BaseModel):
    """AI query generation request."""
    prompt: str

class AIQueryResponse(BaseModel):
    """AI query generation response."""
    generated_sql: str

@router.post("/execute", response_model=Dict[str, Any])
async def execute_sql(sql_query: SQLQuery = Body(...)):
    """Execute a SQL query and return results."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)

        # Execute query
        df = pd.read_sql_query(sql_query.query, engine)

        # Convert to JSON-serializable format
        result = df.to_dict(orient='records')

        # Convert datetime objects to ISO format
        for row in result:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):
                    row[key] = value.isoformat()
                elif pd.isna(value):
                    row[key] = None

        return {
            "success": True,
            "rows": len(result),
            "columns": list(df.columns),
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "rows": 0,
            "columns": [],
            "data": []
        }

@router.post("/generate-query", response_model=AIQueryResponse)
async def generate_sql_query(request: AIQueryRequest = Body(...)):
    """Generate SQL query from natural language using AI."""
    try:
        # Schema string for AI context
        schema_string = """Table Schemas
repositories

id INTEGER PRIMARY KEY
project_key VARCHAR(255)
slug_name VARCHAR(255)
clone_url VARCHAR(500)
created_at DATETIME

commits

id INTEGER PRIMARY KEY
repository_id INTEGER (FK -> repositories.id)
commit_hash VARCHAR(40) UNIQUE
author_name VARCHAR(255)
author_email VARCHAR(255)
committer_name VARCHAR(255)
committer_email VARCHAR(255)
commit_date DATETIME
message TEXT
lines_added INTEGER
lines_deleted INTEGER
files_changed INTEGER
branch VARCHAR(255)

pull_requests

id INTEGER PRIMARY KEY
repository_id INTEGER (FK -> pull_requests.id)
pr_number INTEGER
title VARCHAR(500)
description TEXT
author_name VARCHAR(255)
author_email VARCHAR(255)
created_date DATETIME
merged_date DATETIME
state VARCHAR(50)
source_branch VARCHAR(255)
target_branch VARCHAR(255)
lines_added INTEGER
lines_deleted INTEGER
commits_count INTEGER

pr_approvals

id INTEGER PRIMARY KEY
pull_request_id INTEGER (FK -> pull_requests.id)
approver_name VARCHAR(255)
approver_email VARCHAR(255)
approval_date DATETIME

staff_details

id INTEGER PRIMARY KEY
bank_id_1 VARCHAR(50)
staff_id VARCHAR(50)
staff_name VARCHAR(255)
email_address VARCHAR(255)
staff_start_date DATE
staff_end_date DATE
tech_unit VARCHAR(255)
platform_name VARCHAR(255)
staff_type VARCHAR(100)
staff_status VARCHAR(100)
rank VARCHAR(100)
department_id VARCHAR(50)

author_staff_mapping

id INTEGER PRIMARY KEY
author_name VARCHAR(255) UNIQUE
author_email VARCHAR(255)
bank_id_1 VARCHAR(50)
staff_id VARCHAR(50)
staff_name VARCHAR(255)
mapped_date DATETIME
notes TEXT
"""

        # API call to Dify
        url = "https://dify.api.apps.k8s.sp.ut.dbs.corp/v1/completion-messages"
        headers = {
            "Authorization": "Bearer app-4int1WqBf4BB4s7k84YUpJd",
            "Content-Type": "application/json"
        }

        payload = {
            "sqlschema": schema_string,
            "promptforData": request.prompt,
            "response_mode": "blocking",
            "user": "api_user"
        }

        # Disable SSL verification and suppress warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)

        if response.status_code == 200:
            result = response.json()
            generated_sql = result.get('answer', '').strip()

            # Clean up SQL (remove markdown code blocks)
            if generated_sql.startswith('```sql'):
                generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
            elif generated_sql.startswith('```'):
                generated_sql = generated_sql.replace('```', '').strip()

            return AIQueryResponse(generated_sql=generated_sql)
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"AI API Error: {response.text}"
            )

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating query: {str(e)}")
