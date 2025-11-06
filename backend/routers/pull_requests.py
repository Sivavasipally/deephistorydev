"""Pull requests router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config import Config
from models import get_engine, get_session, PullRequest, PRApproval, Repository

router = APIRouter()

class PullRequestDetail(BaseModel):
    """Pull request detail model."""
    pr_number: int
    title: str
    description: str
    author_name: str
    author_email: str
    created_date: datetime
    merged_date: Optional[datetime]
    state: str
    source_branch: str
    target_branch: str
    lines_added: int
    lines_deleted: int
    total_lines: int
    commits_count: int
    approvals_count: int
    repository: str
    project_key: str

@router.get("/", response_model=List[PullRequestDetail])
async def get_pull_requests(
    author: Optional[str] = Query(None),
    repository: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get pull requests with optional filters."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(
                PullRequest.pr_number,
                PullRequest.title,
                PullRequest.description,
                PullRequest.author_name,
                PullRequest.author_email,
                PullRequest.created_date,
                PullRequest.merged_date,
                PullRequest.state,
                PullRequest.source_branch,
                PullRequest.target_branch,
                PullRequest.lines_added,
                PullRequest.lines_deleted,
                (PullRequest.lines_added + PullRequest.lines_deleted).label('total_lines'),
                PullRequest.commits_count,
                func.count(PRApproval.id).label('approvals_count'),
                Repository.slug_name,
                Repository.project_key
            ).join(
                Repository, PullRequest.repository_id == Repository.id
            ).outerjoin(
                PRApproval, PullRequest.id == PRApproval.pull_request_id
            ).group_by(PullRequest.id)

            # Apply filters
            if author:
                query = query.filter(PullRequest.author_name.ilike(f"%{author}%"))
            if repository:
                query = query.filter(Repository.slug_name.ilike(f"%{repository}%"))
            if state:
                query = query.filter(PullRequest.state.ilike(f"%{state}%"))
            if start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(PullRequest.created_date >= start_datetime)
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(PullRequest.created_date <= end_datetime)

            # Order and paginate
            query = query.order_by(desc(PullRequest.created_date)).limit(limit).offset(offset)

            results = query.all()

            return [
                PullRequestDetail(
                    pr_number=r.pr_number,
                    title=r.title,
                    description=r.description[:200] + "..." if len(r.description) > 200 else r.description,
                    author_name=r.author_name,
                    author_email=r.author_email,
                    created_date=r.created_date,
                    merged_date=r.merged_date,
                    state=r.state,
                    source_branch=r.source_branch,
                    target_branch=r.target_branch,
                    lines_added=r.lines_added,
                    lines_deleted=r.lines_deleted,
                    total_lines=r.total_lines,
                    commits_count=r.commits_count,
                    approvals_count=r.approvals_count,
                    repository=r.slug_name,
                    project_key=r.project_key
                )
                for r in results
            ]

        finally:
            session.close()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pull requests: {str(e)}")

@router.get("/top-approvers")
async def get_top_pr_approvers(limit: int = Query(10, ge=1, le=100)):
    """Get top PR approvers."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(
                PRApproval.approver_name,
                PRApproval.approver_email,
                func.count(PRApproval.id).label('approvals_count'),
                func.count(func.distinct(PullRequest.repository_id)).label('repositories_count')
            ).join(
                PullRequest, PRApproval.pull_request_id == PullRequest.id
            ).group_by(
                PRApproval.approver_name,
                PRApproval.approver_email
            ).order_by(
                desc('approvals_count')
            ).limit(limit)

            results = query.all()

            return [
                {
                    "approver_name": r.approver_name,
                    "email": r.approver_email,
                    "total_approvals": r.approvals_count,
                    "repositories": r.repositories_count
                }
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top approvers: {str(e)}")
