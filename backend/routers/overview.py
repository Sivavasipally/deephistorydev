"""Overview router for dashboard statistics."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from typing import Dict

from cli.config import Config
from cli.models import get_engine, get_session, Repository, Commit, PullRequest, PRApproval

router = APIRouter()

@router.get("/stats", response_model=Dict)
async def get_overview_stats():
    """
    Get overall statistics for the dashboard.

    Returns:
        Dictionary with total counts for commits, authors, repositories, and lines changed.
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            total_commits = session.query(func.count(Commit.id)).scalar() or 0
            total_authors = session.query(func.count(func.distinct(Commit.author_email))).scalar() or 0
            total_repositories = session.query(func.count(Repository.id)).scalar() or 0
            total_lines = session.query(
                func.sum(Commit.lines_added + Commit.lines_deleted)
            ).scalar() or 0
            total_prs = session.query(func.count(PullRequest.id)).scalar() or 0
            total_approvals = session.query(func.count(PRApproval.id)).scalar() or 0

            return {
                "total_commits": total_commits,
                "total_authors": total_authors,
                "total_repositories": total_repositories,
                "total_lines": int(total_lines),
                "total_prs": total_prs,
                "total_approvals": total_approvals
            }
        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overview stats: {str(e)}")
