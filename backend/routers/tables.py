"""Database tables router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any

from config import Config
from models import get_engine, get_session, Repository, Commit, PullRequest, PRApproval, StaffDetails, AuthorStaffMapping

router = APIRouter()

@router.get("/info", response_model=Dict[str, int])
async def get_table_info():
    """Get row counts for all tables."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            return {
                "repositories": session.query(Repository).count(),
                "commits": session.query(Commit).count(),
                "pull_requests": session.query(PullRequest).count(),
                "pr_approvals": session.query(PRApproval).count(),
                "staff_details": session.query(StaffDetails).count(),
                "author_staff_mapping": session.query(AuthorStaffMapping).count()
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching table info: {str(e)}")

@router.get("/{table_name}/data", response_model=List[Dict[str, Any]])
async def get_table_data(
    table_name: str,
    limit: int = Query(1000, ge=1, le=10000)
):
    """Get data from a specific table."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        # Map table names to models
        table_models = {
            "repositories": Repository,
            "commits": Commit,
            "pull_requests": PullRequest,
            "pr_approvals": PRApproval,
            "staff_details": StaffDetails,
            "author_staff_mapping": AuthorStaffMapping
        }

        if table_name not in table_models:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

        try:
            model = table_models[table_name]
            query = session.query(model).limit(limit)

            # Convert to list of dicts
            data = []
            for row in query:
                row_dict = {}
                for column in row.__table__.columns:
                    value = getattr(row, column.name)
                    # Convert datetime to ISO format
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row_dict[column.name] = value
                data.append(row_dict)

            return data

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching table data: {str(e)}")
