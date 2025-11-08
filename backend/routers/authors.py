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

            # Get commit statistics per STAFF (grouped by staff, not author)
            # First join commits with mappings to get staff info
            commit_query = session.query(
                StaffDetails.bank_id_1,
                StaffDetails.staff_name,
                StaffDetails.email_address,
                StaffDetails.rank,
                StaffDetails.reporting_manager_name,
                StaffDetails.work_location,
                StaffDetails.staff_type,
                func.count(Commit.id).label('total_commits'),
                func.sum(Commit.lines_added).label('total_lines_added'),
                func.sum(Commit.lines_deleted).label('total_lines_deleted'),
                func.sum(Commit.files_changed).label('total_files_changed'),
                func.count(func.distinct(Commit.repository_id)).label('repositories_count')
            ).join(
                AuthorStaffMapping,
                Commit.author_name == AuthorStaffMapping.author_name
            ).join(
                StaffDetails,
                AuthorStaffMapping.bank_id_1 == StaffDetails.bank_id_1
            )

            # Apply date filters
            if start_datetime:
                commit_query = commit_query.filter(Commit.commit_date >= start_datetime)
            if end_datetime:
                commit_query = commit_query.filter(Commit.commit_date <= end_datetime)

            # Filter active staff only
            commit_query = commit_query.filter(
                (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
            )

            # Apply staff detail filters
            if rank:
                commit_query = commit_query.filter(StaffDetails.rank == rank)
            if reporting_manager:
                commit_query = commit_query.filter(StaffDetails.reporting_manager_name.ilike(f'%{reporting_manager}%'))
            if work_location:
                commit_query = commit_query.filter(StaffDetails.work_location == work_location)
            if staff_type:
                commit_query = commit_query.filter(StaffDetails.staff_type == staff_type)

            commit_stats = commit_query.group_by(
                StaffDetails.bank_id_1,
                StaffDetails.staff_name,
                StaffDetails.email_address,
                StaffDetails.rank,
                StaffDetails.reporting_manager_name,
                StaffDetails.work_location,
                StaffDetails.staff_type
            ).subquery()

            # Get PR creation statistics per STAFF
            pr_created_query = session.query(
                StaffDetails.bank_id_1,
                func.count(PullRequest.id).label('total_prs_created')
            ).join(
                AuthorStaffMapping,
                PullRequest.author_email == AuthorStaffMapping.author_email
            ).join(
                StaffDetails,
                AuthorStaffMapping.bank_id_1 == StaffDetails.bank_id_1
            )

            if start_datetime:
                pr_created_query = pr_created_query.filter(PullRequest.created_date >= start_datetime)
            if end_datetime:
                pr_created_query = pr_created_query.filter(PullRequest.created_date <= end_datetime)

            pr_created_query = pr_created_query.filter(
                (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
            )

            pr_created_stats = pr_created_query.group_by(
                StaffDetails.bank_id_1
            ).subquery()

            # Get PR approval statistics per STAFF
            pr_approval_query = session.query(
                StaffDetails.bank_id_1,
                func.count(PRApproval.id).label('total_prs_approved')
            ).join(
                AuthorStaffMapping,
                PRApproval.approver_email == AuthorStaffMapping.author_email
            ).join(
                StaffDetails,
                AuthorStaffMapping.bank_id_1 == StaffDetails.bank_id_1
            )

            if start_datetime:
                pr_approval_query = pr_approval_query.filter(PRApproval.approval_date >= start_datetime)
            if end_datetime:
                pr_approval_query = pr_approval_query.filter(PRApproval.approval_date <= end_datetime)

            pr_approval_query = pr_approval_query.filter(
                (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
            )

            pr_approval_stats = pr_approval_query.group_by(
                StaffDetails.bank_id_1
            ).subquery()

            # Combine all statistics - now grouped by staff
            query = session.query(
                commit_stats.c.bank_id_1,
                commit_stats.c.staff_name,
                commit_stats.c.email_address,
                commit_stats.c.rank,
                commit_stats.c.reporting_manager_name,
                commit_stats.c.work_location,
                commit_stats.c.staff_type,
                commit_stats.c.total_commits,
                commit_stats.c.total_lines_added,
                commit_stats.c.total_lines_deleted,
                (commit_stats.c.total_lines_added + commit_stats.c.total_lines_deleted).label('total_lines_changed'),
                commit_stats.c.total_files_changed,
                commit_stats.c.repositories_count,
                func.coalesce(pr_created_stats.c.total_prs_created, 0).label('total_prs_created'),
                func.coalesce(pr_approval_stats.c.total_prs_approved, 0).label('total_prs_approved')
            ).outerjoin(
                pr_created_stats,
                commit_stats.c.bank_id_1 == pr_created_stats.c.bank_id_1
            ).outerjoin(
                pr_approval_stats,
                commit_stats.c.bank_id_1 == pr_approval_stats.c.bank_id_1
            )

            query = query.order_by(desc('total_commits')).limit(limit)

            results = query.all()

            return [
                AuthorStats(
                    author_name=r.staff_name,  # Always staff name (grouped by staff)
                    email=r.email_address,  # Staff email
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
                    is_mapped=True  # All are mapped (query ensures this)
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
            # Base filter to exclude inactive staff and ensure staff has author mapping
            active_filter = (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))

            # Get unique ranks (active staff with mappings only)
            ranks = session.query(
                StaffDetails.rank
            ).join(
                AuthorStaffMapping,
                StaffDetails.bank_id_1 == AuthorStaffMapping.bank_id_1
            ).distinct().filter(
                StaffDetails.rank.isnot(None),
                active_filter
            ).order_by(StaffDetails.rank).all()

            # Get unique reporting managers (active staff with mappings only)
            managers = session.query(
                StaffDetails.reporting_manager_name
            ).join(
                AuthorStaffMapping,
                StaffDetails.bank_id_1 == AuthorStaffMapping.bank_id_1
            ).distinct().filter(
                StaffDetails.reporting_manager_name.isnot(None),
                active_filter
            ).order_by(StaffDetails.reporting_manager_name).all()

            # Get unique work locations (active staff with mappings only)
            locations = session.query(
                StaffDetails.work_location
            ).join(
                AuthorStaffMapping,
                StaffDetails.bank_id_1 == AuthorStaffMapping.bank_id_1
            ).distinct().filter(
                StaffDetails.work_location.isnot(None),
                active_filter
            ).order_by(StaffDetails.work_location).all()

            # Get unique staff types (active staff with mappings only)
            staff_types = session.query(
                StaffDetails.staff_type
            ).join(
                AuthorStaffMapping,
                StaffDetails.bank_id_1 == AuthorStaffMapping.bank_id_1
            ).distinct().filter(
                StaffDetails.staff_type.isnot(None),
                active_filter
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

@router.get("/productivity/{bank_id}")
async def get_staff_productivity(
    bank_id: str,
    granularity: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly|yearly)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    repository_id: Optional[int] = None
):
    """
    Get detailed productivity metrics for a specific staff member.

    Args:
        bank_id: Staff bank ID
        granularity: Time granularity (daily, weekly, monthly, quarterly, yearly)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        repository_id: Optional repository filter

    Returns:
        Comprehensive productivity data including time-series and breakdowns
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

            # Get staff details
            staff = session.query(StaffDetails).filter(
                StaffDetails.bank_id_1 == bank_id
            ).first()

            if not staff:
                raise HTTPException(status_code=404, detail=f"Staff with bank_id {bank_id} not found")

            # Get all author mappings for this staff
            author_mappings = session.query(AuthorStaffMapping).filter(
                AuthorStaffMapping.bank_id_1 == bank_id
            ).all()

            if not author_mappings:
                raise HTTPException(status_code=404, detail=f"No author mappings found for bank_id {bank_id}")

            author_names = [m.author_name for m in author_mappings]
            author_emails = [m.author_email for m in author_mappings if m.author_email]

            # Determine date truncation based on granularity and database type
            db_type = db_config['type'].lower()

            if granularity == "daily":
                if db_type == 'sqlite':
                    date_trunc = func.date(Commit.commit_date)
                else:  # mariadb/mysql
                    date_trunc = func.date(Commit.commit_date)
                date_format = "%Y-%m-%d"
            elif granularity == "weekly":
                if db_type == 'sqlite':
                    date_trunc = func.strftime('%Y-W%W', Commit.commit_date)
                else:  # mariadb/mysql
                    # MySQL: Use DATE_FORMAT to get year-week
                    date_trunc = func.date_format(Commit.commit_date, '%Y-W%u')
                date_format = "%Y-W%W"
            elif granularity == "monthly":
                if db_type == 'sqlite':
                    date_trunc = func.strftime('%Y-%m', Commit.commit_date)
                else:  # mariadb/mysql
                    # MySQL: Use DATE_FORMAT to get year-month
                    date_trunc = func.date_format(Commit.commit_date, '%Y-%m')
                date_format = "%Y-%m"
            elif granularity == "quarterly":
                if db_type == 'sqlite':
                    # SQLite: Format as YYYY-Q# (e.g., 2024-Q1)
                    date_trunc = func.printf('%s-Q%d',
                        func.strftime('%Y', Commit.commit_date),
                        (func.cast(func.strftime('%m', Commit.commit_date), Integer) + 2) / 3
                    )
                else:  # mariadb/mysql
                    # MySQL: Use CONCAT and QUARTER functions (e.g., 2024-Q1)
                    date_trunc = func.concat(
                        func.year(Commit.commit_date),
                        '-Q',
                        func.quarter(Commit.commit_date)
                    )
                date_format = "%Y-Q%q"
            else:  # yearly
                if db_type == 'sqlite':
                    date_trunc = func.strftime('%Y', Commit.commit_date)
                else:  # mariadb/mysql
                    # MySQL: Use DATE_FORMAT or YEAR function
                    date_trunc = func.date_format(Commit.commit_date, '%Y')
                date_format = "%Y"

            # Build base commit query
            commit_query = session.query(
                date_trunc.label('period'),
                func.count(Commit.id).label('commits'),
                func.sum(Commit.lines_added).label('lines_added'),
                func.sum(Commit.lines_deleted).label('lines_deleted'),
                func.sum(Commit.files_changed).label('files_changed'),
                func.count(func.distinct(Commit.repository_id)).label('repos_touched')
            ).filter(
                Commit.author_name.in_(author_names)
            )

            if start_datetime:
                commit_query = commit_query.filter(Commit.commit_date >= start_datetime)
            if end_datetime:
                commit_query = commit_query.filter(Commit.commit_date <= end_datetime)
            if repository_id:
                commit_query = commit_query.filter(Commit.repository_id == repository_id)

            commit_timeseries = commit_query.group_by('period').order_by('period').all()

            # Create date truncation for PR created_date
            if granularity == "daily":
                if db_type == 'sqlite':
                    pr_date_trunc = func.date(PullRequest.created_date)
                else:  # mariadb/mysql
                    pr_date_trunc = func.date(PullRequest.created_date)
            elif granularity == "weekly":
                if db_type == 'sqlite':
                    pr_date_trunc = func.strftime('%Y-W%W', PullRequest.created_date)
                else:  # mariadb/mysql
                    pr_date_trunc = func.date_format(PullRequest.created_date, '%Y-W%u')
            elif granularity == "monthly":
                if db_type == 'sqlite':
                    pr_date_trunc = func.strftime('%Y-%m', PullRequest.created_date)
                else:  # mariadb/mysql
                    pr_date_trunc = func.date_format(PullRequest.created_date, '%Y-%m')
            elif granularity == "quarterly":
                if db_type == 'sqlite':
                    pr_date_trunc = func.printf('%s-Q%d',
                        func.strftime('%Y', PullRequest.created_date),
                        (func.cast(func.strftime('%m', PullRequest.created_date), Integer) + 2) / 3
                    )
                else:  # mariadb/mysql
                    pr_date_trunc = func.concat(
                        func.year(PullRequest.created_date),
                        '-Q',
                        func.quarter(PullRequest.created_date)
                    )
            else:  # yearly
                if db_type == 'sqlite':
                    pr_date_trunc = func.strftime('%Y', PullRequest.created_date)
                else:  # mariadb/mysql
                    pr_date_trunc = func.date_format(PullRequest.created_date, '%Y')

            # PR opened/merged by time period
            pr_query = session.query(
                pr_date_trunc.label('period'),
                func.count(PullRequest.id).label('prs_opened')
            ).filter(
                PullRequest.author_email.in_(author_emails) if author_emails else PullRequest.author_name.in_(author_names)
            )

            if start_datetime:
                pr_query = pr_query.filter(PullRequest.created_date >= start_datetime)
            if end_datetime:
                pr_query = pr_query.filter(PullRequest.created_date <= end_datetime)
            if repository_id:
                pr_query = pr_query.filter(PullRequest.repository_id == repository_id)

            pr_timeseries = pr_query.group_by('period').order_by('period').all()

            # Repository breakdown (monthly/yearly)
            repo_query = session.query(
                Commit.repository_id,
                func.count(Commit.id).label('commits'),
                func.sum(Commit.lines_added).label('lines_added'),
                func.sum(Commit.lines_deleted).label('lines_deleted'),
                func.sum(Commit.files_changed).label('files_changed')
            ).filter(
                Commit.author_name.in_(author_names)
            )

            if start_datetime:
                repo_query = repo_query.filter(Commit.commit_date >= start_datetime)
            if end_datetime:
                repo_query = repo_query.filter(Commit.commit_date <= end_datetime)

            repo_breakdown = repo_query.group_by(Commit.repository_id).all()

            # Calendar heatmap data (commits per day for last 365 days if daily)
            calendar_data = []
            if granularity == "daily":
                calendar_query = session.query(
                    func.date(Commit.commit_date).label('date'),
                    func.count(Commit.id).label('commits')
                ).filter(
                    Commit.author_name.in_(author_names)
                )

                if start_datetime:
                    calendar_query = calendar_query.filter(Commit.commit_date >= start_datetime)
                if end_datetime:
                    calendar_query = calendar_query.filter(Commit.commit_date <= end_datetime)

                calendar_data = calendar_query.group_by('date').order_by('date').all()

            # Total summary
            total_commits = session.query(
                func.count(Commit.id)
            ).filter(
                Commit.author_name.in_(author_names)
            )

            if start_datetime:
                total_commits = total_commits.filter(Commit.commit_date >= start_datetime)
            if end_datetime:
                total_commits = total_commits.filter(Commit.commit_date <= end_datetime)
            if repository_id:
                total_commits = total_commits.filter(Commit.repository_id == repository_id)

            total_commits = total_commits.scalar()

            # Calculate PR merge statistics
            total_prs_query = session.query(
                func.count(PullRequest.id)
            ).filter(
                PullRequest.author_email.in_(author_emails) if author_emails else PullRequest.author_name.in_(author_names)
            )

            if start_datetime:
                total_prs_query = total_prs_query.filter(PullRequest.created_date >= start_datetime)
            if end_datetime:
                total_prs_query = total_prs_query.filter(PullRequest.created_date <= end_datetime)
            if repository_id:
                total_prs_query = total_prs_query.filter(PullRequest.repository_id == repository_id)

            total_prs = total_prs_query.scalar() or 0

            # Count merged PRs
            merged_prs_query = session.query(
                func.count(PullRequest.id)
            ).filter(
                PullRequest.author_email.in_(author_emails) if author_emails else PullRequest.author_name.in_(author_names),
                PullRequest.state == 'MERGED'
            )

            if start_datetime:
                merged_prs_query = merged_prs_query.filter(PullRequest.created_date >= start_datetime)
            if end_datetime:
                merged_prs_query = merged_prs_query.filter(PullRequest.created_date <= end_datetime)
            if repository_id:
                merged_prs_query = merged_prs_query.filter(PullRequest.repository_id == repository_id)

            merged_prs = merged_prs_query.scalar() or 0

            # Calculate merge rate
            merge_rate = (merged_prs / total_prs) if total_prs > 0 else 0

            return {
                "staff": {
                    "bank_id": staff.bank_id_1,
                    "name": staff.staff_name,
                    "email": staff.email_address,
                    "rank": staff.rank,
                    "location": staff.work_location,
                    "tech_unit": staff.tech_unit,
                    "staff_type": staff.staff_type
                },
                "granularity": granularity,
                "timeseries": {
                    "commits": [
                        {
                            "period": str(row.period),
                            "commits": row.commits,
                            "lines_added": row.lines_added or 0,
                            "lines_deleted": row.lines_deleted or 0,
                            "files_changed": row.files_changed or 0,
                            "repos_touched": row.repos_touched
                        }
                        for row in commit_timeseries
                    ],
                    "prs": [
                        {
                            "period": str(row.period),
                            "prs_opened": row.prs_opened
                        }
                        for row in pr_timeseries
                    ]
                },
                "repository_breakdown": [
                    {
                        "repository_id": row.repository_id,
                        "commits": row.commits,
                        "lines_added": row.lines_added or 0,
                        "lines_deleted": row.lines_deleted or 0,
                        "files_changed": row.files_changed or 0
                    }
                    for row in repo_breakdown
                ],
                "calendar_heatmap": [
                    {
                        "date": str(row.date),
                        "commits": row.commits
                    }
                    for row in calendar_data
                ],
                "summary": {
                    "total_commits": total_commits or 0,
                    "total_prs": total_prs,
                    "merged_prs": merged_prs,
                    "merge_rate": round(merge_rate, 3),
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    }
                }
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching productivity data: {str(e)}")
