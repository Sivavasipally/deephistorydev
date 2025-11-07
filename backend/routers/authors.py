"""Authors router for author analytics."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, desc
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

from config import Config
from models import get_engine, get_session, Commit, PullRequest, PRApproval, AuthorStaffMapping, StaffDetails

router = APIRouter()

class AuthorStats(BaseModel):
    """Author statistics model."""
    author_name: str
    email: str
    total_commits: int
    lines_added: int
    lines_deleted: int
    total_lines_changed: int
    files_changed: int
    repositories_count: int
    prs_created: int
    prs_approved: int
    # Staff details (when mapped)
    staff_name: Optional[str] = None
    bank_id: Optional[str] = None
    rank: Optional[str] = None
    reporting_manager_name: Optional[str] = None
    work_location: Optional[str] = None
    staff_type: Optional[str] = None
    is_mapped: bool = False

@router.get("/statistics", response_model=List[AuthorStats])
async def get_author_statistics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of authors to return"),
    rank: Optional[str] = Query(None, description="Filter by rank"),
    reporting_manager: Optional[str] = Query(None, description="Filter by reporting manager"),
    work_location: Optional[str] = Query(None, description="Filter by work location"),
    staff_type: Optional[str] = Query(None, description="Filter by staff type")
):
    """
    Get comprehensive statistics for all authors.

    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of authors to return

    Returns:
        List of author statistics
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Parse dates
            start_datetime = datetime.fromisoformat(start_date) if start_date else None
            end_datetime = datetime.fromisoformat(end_date) if end_date else None

            # Get commit statistics per author
            commit_query = session.query(
                Commit.author_name,
                Commit.author_email,
                func.count(Commit.id).label('total_commits'),
                func.sum(Commit.lines_added).label('total_lines_added'),
                func.sum(Commit.lines_deleted).label('total_lines_deleted'),
                func.sum(Commit.files_changed).label('total_files_changed'),
                func.count(func.distinct(Commit.repository_id)).label('repositories_count')
            )

            # Apply date filters
            if start_datetime:
                commit_query = commit_query.filter(Commit.commit_date >= start_datetime)
            if end_datetime:
                commit_query = commit_query.filter(Commit.commit_date <= end_datetime)

            commit_stats = commit_query.group_by(
                Commit.author_name,
                Commit.author_email
            ).subquery()

            # Get PR creation statistics
            pr_created_query = session.query(
                PullRequest.author_email,
                func.count(PullRequest.id).label('total_prs_created')
            )

            if start_datetime:
                pr_created_query = pr_created_query.filter(PullRequest.created_date >= start_datetime)
            if end_datetime:
                pr_created_query = pr_created_query.filter(PullRequest.created_date <= end_datetime)

            pr_created_stats = pr_created_query.group_by(
                PullRequest.author_email
            ).subquery()

            # Get PR approval statistics
            pr_approval_query = session.query(
                PRApproval.approver_email,
                func.count(PRApproval.id).label('total_prs_approved')
            )

            if start_datetime:
                pr_approval_query = pr_approval_query.filter(PRApproval.approval_date >= start_datetime)
            if end_datetime:
                pr_approval_query = pr_approval_query.filter(PRApproval.approval_date <= end_datetime)

            pr_approval_stats = pr_approval_query.group_by(
                PRApproval.approver_email
            ).subquery()

            # Combine all statistics with staff details
            query = session.query(
                commit_stats.c.author_name,
                commit_stats.c.author_email,
                commit_stats.c.total_commits,
                commit_stats.c.total_lines_added,
                commit_stats.c.total_lines_deleted,
                (commit_stats.c.total_lines_added + commit_stats.c.total_lines_deleted).label('total_lines_changed'),
                commit_stats.c.total_files_changed,
                commit_stats.c.repositories_count,
                func.coalesce(pr_created_stats.c.total_prs_created, 0).label('total_prs_created'),
                func.coalesce(pr_approval_stats.c.total_prs_approved, 0).label('total_prs_approved'),
                # Staff details from mapping
                AuthorStaffMapping.staff_name,
                StaffDetails.bank_id_1,
                StaffDetails.rank,
                StaffDetails.reporting_manager_name,
                StaffDetails.work_location,
                StaffDetails.staff_type,
                StaffDetails.email_address
            ).outerjoin(
                pr_created_stats,
                commit_stats.c.author_email == pr_created_stats.c.author_email
            ).outerjoin(
                pr_approval_stats,
                commit_stats.c.author_email == pr_approval_stats.c.approver_email
            ).outerjoin(
                AuthorStaffMapping,
                commit_stats.c.author_name == AuthorStaffMapping.author_name
            ).outerjoin(
                StaffDetails,
                AuthorStaffMapping.bank_id_1 == StaffDetails.bank_id_1
            )

            # Apply staff detail filters
            if rank:
                query = query.filter(StaffDetails.rank == rank)
            if reporting_manager:
                query = query.filter(StaffDetails.reporting_manager_name.ilike(f'%{reporting_manager}%'))
            if work_location:
                query = query.filter(StaffDetails.work_location == work_location)
            if staff_type:
                query = query.filter(StaffDetails.staff_type == staff_type)

            query = query.order_by(desc('total_commits')).limit(limit)

            results = query.all()

            return [
                AuthorStats(
                    author_name=r.staff_name if r.staff_name else r.author_name,  # Use staff name if mapped
                    email=r.email_address if r.email_address else r.author_email,  # Use staff email if available
                    total_commits=r.total_commits,
                    lines_added=r.total_lines_added or 0,
                    lines_deleted=r.total_lines_deleted or 0,
                    total_lines_changed=r.total_lines_changed or 0,
                    files_changed=r.total_files_changed or 0,
                    repositories_count=r.repositories_count,
                    prs_created=r.total_prs_created,
                    prs_approved=r.total_prs_approved,
                    # Staff details
                    staff_name=r.staff_name,
                    bank_id=r.bank_id_1,
                    rank=r.rank,
                    reporting_manager_name=r.reporting_manager_name,
                    work_location=r.work_location,
                    staff_type=r.staff_type,
                    is_mapped=r.staff_name is not None
                )
                for r in results
            ]

        finally:
            session.close()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching author statistics: {str(e)}")

@router.get("/top-contributors")
async def get_top_contributors(
    metric: str = Query("commits", regex="^(commits|lines|prs|approvals)$"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get top contributors by specific metric.

    Args:
        metric: Metric to sort by (commits, lines, prs, approvals)
        limit: Number of top contributors

    Returns:
        List of top contributors
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            if metric == "commits":
                query = session.query(
                    Commit.author_name,
                    Commit.author_email,
                    func.count(Commit.id).label('value')
                ).group_by(
                    Commit.author_name,
                    Commit.author_email
                ).order_by(desc('value')).limit(limit)

            elif metric == "lines":
                query = session.query(
                    Commit.author_name,
                    Commit.author_email,
                    func.sum(Commit.lines_added + Commit.lines_deleted).label('value')
                ).group_by(
                    Commit.author_name,
                    Commit.author_email
                ).order_by(desc('value')).limit(limit)

            elif metric == "prs":
                query = session.query(
                    PullRequest.author_name,
                    PullRequest.author_email,
                    func.count(PullRequest.id).label('value')
                ).group_by(
                    PullRequest.author_name,
                    PullRequest.author_email
                ).order_by(desc('value')).limit(limit)

            elif metric == "approvals":
                query = session.query(
                    PRApproval.approver_name,
                    PRApproval.approver_email,
                    func.count(PRApproval.id).label('value')
                ).group_by(
                    PRApproval.approver_name,
                    PRApproval.approver_email
                ).order_by(desc('value')).limit(limit)

            results = query.all()

            return [
                {
                    "name": r[0],
                    "email": r[1],
                    "value": r[2]
                }
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top contributors: {str(e)}")

@router.get("/filter-options")
async def get_filter_options():
    """
    Get unique values for filter dropdowns.

    Returns:
        Dictionary with unique ranks, managers, locations, and staff types
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Get unique ranks
            ranks = session.query(
                StaffDetails.rank
            ).distinct().filter(
                StaffDetails.rank.isnot(None)
            ).order_by(StaffDetails.rank).all()

            # Get unique reporting managers
            managers = session.query(
                StaffDetails.reporting_manager_name
            ).distinct().filter(
                StaffDetails.reporting_manager_name.isnot(None)
            ).order_by(StaffDetails.reporting_manager_name).all()

            # Get unique work locations
            locations = session.query(
                StaffDetails.work_location
            ).distinct().filter(
                StaffDetails.work_location.isnot(None)
            ).order_by(StaffDetails.work_location).all()

            # Get unique staff types
            staff_types = session.query(
                StaffDetails.staff_type
            ).distinct().filter(
                StaffDetails.staff_type.isnot(None)
            ).order_by(StaffDetails.staff_type).all()

            return {
                "ranks": [r[0] for r in ranks],
                "reporting_managers": [m[0] for m in managers],
                "work_locations": [l[0] for l in locations],
                "staff_types": [t[0] for t in staff_types]
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filter options: {str(e)}")
