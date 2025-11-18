"""Database tables router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any

from cli.config import Config
from cli.models import (
    get_engine, get_session,
    Repository, Commit, PullRequest, PRApproval,
    StaffDetails, AuthorStaffMapping,
    StaffMetrics, CommitMetrics, PRMetrics,
    RepositoryMetrics, AuthorMetrics, TeamMetrics, DailyMetrics
)

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
                # Core tables
                "repositories": session.query(Repository).count(),
                "commits": session.query(Commit).count(),
                "pull_requests": session.query(PullRequest).count(),
                "pr_approvals": session.query(PRApproval).count(),

                # Staff tables
                "staff_details": session.query(StaffDetails).count(),
                "author_staff_mapping": session.query(AuthorStaffMapping).count(),

                # Metric tables (pre-calculated)
                "staff_metrics": session.query(StaffMetrics).count(),
                "commit_metrics": session.query(CommitMetrics).count(),
                "pr_metrics": session.query(PRMetrics).count(),
                "repository_metrics": session.query(RepositoryMetrics).count(),
                "author_metrics": session.query(AuthorMetrics).count(),
                "team_metrics": session.query(TeamMetrics).count(),
                "daily_metrics": session.query(DailyMetrics).count()
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
            # Core tables
            "repositories": Repository,
            "commits": Commit,
            "pull_requests": PullRequest,
            "pr_approvals": PRApproval,

            # Staff tables
            "staff_details": StaffDetails,
            "author_staff_mapping": AuthorStaffMapping,

            # Metric tables (pre-calculated)
            "staff_metrics": StaffMetrics,
            "commit_metrics": CommitMetrics,
            "pr_metrics": PRMetrics,
            "repository_metrics": RepositoryMetrics,
            "author_metrics": AuthorMetrics,
            "team_metrics": TeamMetrics,
            "daily_metrics": DailyMetrics
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
