"""360 Dashboard metrics router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import func, and_, or_, case, extract
from sqlalchemy.orm import Session

from config import Config
from models import (
    get_engine, get_session,
    Repository, Commit, PullRequest, PRApproval, StaffDetails, AuthorStaffMapping
)

router = APIRouter()

class TeamMetrics(BaseModel):
    """Team-level metrics for Repo/Team 360."""
    total_commits: int
    total_prs: int
    open_prs: int
    merged_prs: int
    declined_prs: int
    merge_rate: float
    decline_rate: float
    avg_review_time_hours: float
    unique_contributors: int
    repositories_count: int

class TimeSeriesPoint(BaseModel):
    """Time series data point."""
    period: str
    commits: int
    prs_opened: int
    prs_merged: int
    prs_declined: int

class PRAgeBucket(BaseModel):
    """PR age bucket for risk analysis."""
    bucket: str
    count: int
    pr_ids: List[int]

class ContributorStats(BaseModel):
    """Contributor statistics."""
    author_name: str
    staff_name: Optional[str]
    commits: int
    prs: int
    lines_added: int
    lines_deleted: int
    repos_count: int

class OrgMetrics(BaseModel):
    """Organization-level metrics."""
    total_commits: int
    total_prs: int
    total_contributors: int
    total_repositories: int
    median_cycle_time_hours: float
    p90_cycle_time_hours: float
    overall_merge_rate: float

@router.get("/team/summary", response_model=TeamMetrics)
async def get_team_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    rank: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    staff_type: Optional[str] = Query(None),
    manager: Optional[str] = Query(None),
    sub_platform: Optional[str] = Query(None)
):
    """Get team-level summary metrics."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Build filters for staff
            staff_filters = [StaffDetails.bank_id_1.isnot(None)]
            if rank:
                staff_filters.append(StaffDetails.rank == rank)
            if location:
                staff_filters.append(StaffDetails.work_location == location)
            if staff_type:
                staff_filters.append(StaffDetails.staff_type == staff_type)
            if manager:
                staff_filters.append(StaffDetails.reporting_manager_name == manager)
            if sub_platform:
                staff_filters.append(StaffDetails.sub_platform == sub_platform)

            # Get filtered staff bank_ids
            staff_bank_ids = session.query(StaffDetails.bank_id_1).filter(
                and_(*staff_filters)
            ).distinct().all()
            bank_ids = [bid[0] for bid in staff_bank_ids]

            if not bank_ids:
                return TeamMetrics(
                    total_commits=0, total_prs=0, open_prs=0, merged_prs=0,
                    declined_prs=0, merge_rate=0, decline_rate=0,
                    avg_review_time_hours=0, unique_contributors=0, repositories_count=0
                )

            # Get author emails mapped to these staff
            author_emails = session.query(AuthorStaffMapping.author_email).filter(
                AuthorStaffMapping.bank_id_1.in_(bank_ids)
            ).distinct().all()
            emails = [email[0] for email in author_emails if email[0]]

            # Date filters
            date_filters = []
            if start_date:
                date_filters.append(Commit.commit_date >= datetime.fromisoformat(start_date))
            if end_date:
                date_filters.append(Commit.commit_date <= datetime.fromisoformat(end_date))

            # Get commit metrics
            commit_query = session.query(
                func.count(Commit.id).label('total_commits'),
                func.count(func.distinct(Commit.author_email)).label('unique_contributors'),
                func.count(func.distinct(Commit.repository_id)).label('repositories_count')
            ).filter(Commit.author_email.in_(emails))

            if date_filters:
                commit_query = commit_query.filter(and_(*date_filters))

            commit_stats = commit_query.first()

            # Get PR metrics
            pr_date_filters = []
            if start_date:
                pr_date_filters.append(PullRequest.created_date >= datetime.fromisoformat(start_date))
            if end_date:
                pr_date_filters.append(PullRequest.created_date <= datetime.fromisoformat(end_date))

            pr_query = session.query(
                func.count(PullRequest.id).label('total_prs'),
                func.sum(case((PullRequest.state == 'OPEN', 1), else_=0)).label('open_prs'),
                func.sum(case((PullRequest.state == 'MERGED', 1), else_=0)).label('merged_prs'),
                func.sum(case((PullRequest.state == 'DECLINED', 1), else_=0)).label('declined_prs')
            ).filter(PullRequest.author_email.in_(emails))

            if pr_date_filters:
                pr_query = pr_query.filter(and_(*pr_date_filters))

            pr_stats = pr_query.first()

            # Calculate merge rate and decline rate
            total_prs = pr_stats.total_prs or 0
            merged_prs = pr_stats.merged_prs or 0
            declined_prs = pr_stats.declined_prs or 0
            merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0
            decline_rate = (declined_prs / total_prs * 100) if total_prs > 0 else 0

            # Calculate average review time (created to merged)
            avg_review_time = session.query(
                func.avg(
                    func.timestampdiff(
                        'SECOND',
                        PullRequest.created_date,
                        PullRequest.merged_date
                    )
                )
            ).filter(
                PullRequest.author_email.in_(emails),
                PullRequest.merged_date.isnot(None)
            )
            if pr_date_filters:
                avg_review_time = avg_review_time.filter(and_(*pr_date_filters))

            avg_seconds = avg_review_time.scalar() or 0
            avg_review_time_hours = avg_seconds / 3600 if avg_seconds else 0

            return TeamMetrics(
                total_commits=commit_stats.total_commits or 0,
                total_prs=total_prs,
                open_prs=pr_stats.open_prs or 0,
                merged_prs=merged_prs,
                declined_prs=declined_prs,
                merge_rate=round(merge_rate, 2),
                decline_rate=round(decline_rate, 2),
                avg_review_time_hours=round(avg_review_time_hours, 2),
                unique_contributors=commit_stats.unique_contributors or 0,
                repositories_count=commit_stats.repositories_count or 0
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team summary: {str(e)}")

@router.get("/team/timeseries", response_model=List[TimeSeriesPoint])
async def get_team_timeseries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    granularity: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$"),
    rank: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    staff_type: Optional[str] = Query(None),
    manager: Optional[str] = Query(None),
    sub_platform: Optional[str] = Query(None)
):
    """Get team-level time series data."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Build filters for staff
            staff_filters = [StaffDetails.bank_id_1.isnot(None)]
            if rank:
                staff_filters.append(StaffDetails.rank == rank)
            if location:
                staff_filters.append(StaffDetails.work_location == location)
            if staff_type:
                staff_filters.append(StaffDetails.staff_type == staff_type)
            if manager:
                staff_filters.append(StaffDetails.reporting_manager_name == manager)
            if sub_platform:
                staff_filters.append(StaffDetails.sub_platform == sub_platform)

            # Get filtered staff bank_ids
            staff_bank_ids = session.query(StaffDetails.bank_id_1).filter(
                and_(*staff_filters)
            ).distinct().all()
            bank_ids = [bid[0] for bid in staff_bank_ids]

            if not bank_ids:
                return []

            # Get author emails
            author_emails = session.query(AuthorStaffMapping.author_email).filter(
                AuthorStaffMapping.bank_id_1.in_(bank_ids)
            ).distinct().all()
            emails = [email[0] for email in author_emails if email[0]]

            # Determine date format based on granularity
            date_format_map = {
                'daily': '%Y-%m-%d',
                'weekly': '%Y-W%u',
                'monthly': '%Y-%m',
                'quarterly': '%Y-Q'
            }
            date_format = date_format_map[granularity]

            # Build date filters
            date_filters = []
            if start_date:
                date_filters.append(Commit.commit_date >= datetime.fromisoformat(start_date))
            if end_date:
                date_filters.append(Commit.commit_date <= datetime.fromisoformat(end_date))

            # Get commits grouped by period
            if granularity == 'quarterly':
                period_expr = func.concat(
                    func.year(Commit.commit_date),
                    '-Q',
                    func.quarter(Commit.commit_date)
                )
            else:
                period_expr = func.date_format(Commit.commit_date, date_format)

            commit_data = session.query(
                period_expr.label('period'),
                func.count(Commit.id).label('commits')
            ).filter(
                Commit.author_email.in_(emails),
                *date_filters
            ).group_by('period').order_by('period').all()

            # Get PRs grouped by period
            pr_date_filters = []
            if start_date:
                pr_date_filters.append(PullRequest.created_date >= datetime.fromisoformat(start_date))
            if end_date:
                pr_date_filters.append(PullRequest.created_date <= datetime.fromisoformat(end_date))

            if granularity == 'quarterly':
                pr_period_expr = func.concat(
                    func.year(PullRequest.created_date),
                    '-Q',
                    func.quarter(PullRequest.created_date)
                )
            else:
                pr_period_expr = func.date_format(PullRequest.created_date, date_format)

            pr_data = session.query(
                pr_period_expr.label('period'),
                func.count(PullRequest.id).label('prs_opened'),
                func.sum(case((PullRequest.state == 'MERGED', 1), else_=0)).label('prs_merged'),
                func.sum(case((PullRequest.state == 'DECLINED', 1), else_=0)).label('prs_declined')
            ).filter(
                PullRequest.author_email.in_(emails),
                *pr_date_filters
            ).group_by('period').order_by('period').all()

            # Combine data
            pr_dict = {row.period: row for row in pr_data}

            result = []
            for commit_row in commit_data:
                pr_row = pr_dict.get(commit_row.period)
                result.append(TimeSeriesPoint(
                    period=commit_row.period,
                    commits=commit_row.commits,
                    prs_opened=pr_row.prs_opened if pr_row else 0,
                    prs_merged=pr_row.prs_merged if pr_row else 0,
                    prs_declined=pr_row.prs_declined if pr_row else 0
                ))

            # Add periods that only have PRs
            for period, pr_row in pr_dict.items():
                if period not in [r.period for r in result]:
                    result.append(TimeSeriesPoint(
                        period=period,
                        commits=0,
                        prs_opened=pr_row.prs_opened,
                        prs_merged=pr_row.prs_merged,
                        prs_declined=pr_row.prs_declined
                    ))

            return sorted(result, key=lambda x: x.period)

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team timeseries: {str(e)}")

@router.get("/team/pr-aging", response_model=List[PRAgeBucket])
async def get_pr_aging(
    rank: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    staff_type: Optional[str] = Query(None),
    manager: Optional[str] = Query(None),
    sub_platform: Optional[str] = Query(None)
):
    """Get open PRs grouped by age buckets for risk analysis."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Build filters for staff
            staff_filters = [StaffDetails.bank_id_1.isnot(None)]
            if rank:
                staff_filters.append(StaffDetails.rank == rank)
            if location:
                staff_filters.append(StaffDetails.work_location == location)
            if staff_type:
                staff_filters.append(StaffDetails.staff_type == staff_type)
            if manager:
                staff_filters.append(StaffDetails.reporting_manager_name == manager)
            if sub_platform:
                staff_filters.append(StaffDetails.sub_platform == sub_platform)

            # Get filtered staff bank_ids
            staff_bank_ids = session.query(StaffDetails.bank_id_1).filter(
                and_(*staff_filters)
            ).distinct().all()
            bank_ids = [bid[0] for bid in staff_bank_ids]

            if not bank_ids:
                return []

            # Get author emails
            author_emails = session.query(AuthorStaffMapping.author_email).filter(
                AuthorStaffMapping.bank_id_1.in_(bank_ids)
            ).distinct().all()
            emails = [email[0] for email in author_emails if email[0]]

            # Get open PRs with age in days
            open_prs = session.query(
                PullRequest.id,
                PullRequest.pr_number,
                PullRequest.title,
                PullRequest.created_date,
                func.datediff(func.now(), PullRequest.created_date).label('age_days')
            ).filter(
                PullRequest.author_email.in_(emails),
                PullRequest.state == 'OPEN'
            ).all()

            # Group into buckets
            buckets = {
                '0-7 days': [],
                '8-14 days': [],
                '15-30 days': [],
                '31-60 days': [],
                '60+ days': []
            }

            for pr in open_prs:
                age = pr.age_days
                if age <= 7:
                    buckets['0-7 days'].append(pr.id)
                elif age <= 14:
                    buckets['8-14 days'].append(pr.id)
                elif age <= 30:
                    buckets['15-30 days'].append(pr.id)
                elif age <= 60:
                    buckets['31-60 days'].append(pr.id)
                else:
                    buckets['60+ days'].append(pr.id)

            return [
                PRAgeBucket(bucket=bucket, count=len(pr_ids), pr_ids=pr_ids)
                for bucket, pr_ids in buckets.items()
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PR aging: {str(e)}")

@router.get("/team/contributors", response_model=List[ContributorStats])
async def get_team_contributors(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    rank: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    staff_type: Optional[str] = Query(None),
    manager: Optional[str] = Query(None),
    sub_platform: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Get top contributors with their statistics."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Build filters for staff
            staff_filters = [StaffDetails.bank_id_1.isnot(None)]
            if rank:
                staff_filters.append(StaffDetails.rank == rank)
            if location:
                staff_filters.append(StaffDetails.work_location == location)
            if staff_type:
                staff_filters.append(StaffDetails.staff_type == staff_type)
            if manager:
                staff_filters.append(StaffDetails.reporting_manager_name == manager)
            if sub_platform:
                staff_filters.append(StaffDetails.sub_platform == sub_platform)

            # Get filtered staff bank_ids
            staff_bank_ids = session.query(StaffDetails.bank_id_1).filter(
                and_(*staff_filters)
            ).distinct().all()
            bank_ids = [bid[0] for bid in staff_bank_ids]

            if not bank_ids:
                return []

            # Get author emails
            author_emails = session.query(AuthorStaffMapping.author_email).filter(
                AuthorStaffMapping.bank_id_1.in_(bank_ids)
            ).distinct().all()
            emails = [email[0] for email in author_emails if email[0]]

            # Build date filters
            date_filters = []
            if start_date:
                date_filters.append(Commit.commit_date >= datetime.fromisoformat(start_date))
            if end_date:
                date_filters.append(Commit.commit_date <= datetime.fromisoformat(end_date))

            # Get commit stats by author
            commit_stats = session.query(
                Commit.author_name,
                Commit.author_email,
                func.count(Commit.id).label('commits'),
                func.sum(Commit.lines_added).label('lines_added'),
                func.sum(Commit.lines_deleted).label('lines_deleted'),
                func.count(func.distinct(Commit.repository_id)).label('repos_count')
            ).filter(
                Commit.author_email.in_(emails),
                *date_filters
            ).group_by(Commit.author_email, Commit.author_name).all()

            # Get PR counts
            pr_date_filters = []
            if start_date:
                pr_date_filters.append(PullRequest.created_date >= datetime.fromisoformat(start_date))
            if end_date:
                pr_date_filters.append(PullRequest.created_date <= datetime.fromisoformat(end_date))

            pr_stats = session.query(
                PullRequest.author_email,
                func.count(PullRequest.id).label('prs')
            ).filter(
                PullRequest.author_email.in_(emails),
                *pr_date_filters
            ).group_by(PullRequest.author_email).all()

            pr_dict = {row.author_email: row.prs for row in pr_stats}

            # Get staff names
            mappings = session.query(
                AuthorStaffMapping.author_email,
                StaffDetails.staff_name
            ).join(
                StaffDetails,
                AuthorStaffMapping.bank_id_1 == StaffDetails.bank_id_1
            ).filter(AuthorStaffMapping.author_email.in_(emails)).all()

            staff_name_dict = {row.author_email: row.staff_name for row in mappings}

            # Combine stats
            result = []
            for stat in commit_stats:
                result.append(ContributorStats(
                    author_name=stat.author_name,
                    staff_name=staff_name_dict.get(stat.author_email),
                    commits=stat.commits,
                    prs=pr_dict.get(stat.author_email, 0),
                    lines_added=stat.lines_added or 0,
                    lines_deleted=stat.lines_deleted or 0,
                    repos_count=stat.repos_count
                ))

            # Sort by commits and limit
            result.sort(key=lambda x: x.commits, reverse=True)
            return result[:limit]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contributors: {str(e)}")

@router.get("/org/summary", response_model=OrgMetrics)
async def get_org_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get organization-level summary metrics."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Build date filters
            date_filters = []
            if start_date:
                date_filters.append(Commit.commit_date >= datetime.fromisoformat(start_date))
            if end_date:
                date_filters.append(Commit.commit_date <= datetime.fromisoformat(end_date))

            # Get commit metrics
            commit_query = session.query(
                func.count(Commit.id).label('total_commits'),
                func.count(func.distinct(Commit.author_email)).label('total_contributors'),
                func.count(func.distinct(Commit.repository_id)).label('total_repositories')
            )

            if date_filters:
                commit_query = commit_query.filter(and_(*date_filters))

            commit_stats = commit_query.first()

            # Get PR metrics
            pr_date_filters = []
            if start_date:
                pr_date_filters.append(PullRequest.created_date >= datetime.fromisoformat(start_date))
            if end_date:
                pr_date_filters.append(PullRequest.created_date <= datetime.fromisoformat(end_date))

            pr_query = session.query(
                func.count(PullRequest.id).label('total_prs'),
                func.sum(case((PullRequest.state == 'MERGED', 1), else_=0)).label('merged_prs')
            )

            if pr_date_filters:
                pr_query = pr_query.filter(and_(*pr_date_filters))

            pr_stats = pr_query.first()

            # Calculate merge rate
            total_prs = pr_stats.total_prs or 0
            merged_prs = pr_stats.merged_prs or 0
            merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0

            # Calculate cycle time percentiles
            cycle_times_query = session.query(
                func.timestampdiff(
                    'SECOND',
                    PullRequest.created_date,
                    PullRequest.merged_date
                ).label('cycle_time_seconds')
            ).filter(
                PullRequest.merged_date.isnot(None)
            )

            if pr_date_filters:
                cycle_times_query = cycle_times_query.filter(and_(*pr_date_filters))

            cycle_times = [row.cycle_time_seconds / 3600 for row in cycle_times_query.all() if row.cycle_time_seconds]

            median_cycle_time = 0
            p90_cycle_time = 0
            if cycle_times:
                cycle_times.sort()
                n = len(cycle_times)
                median_cycle_time = cycle_times[n // 2]
                p90_cycle_time = cycle_times[int(n * 0.9)]

            return OrgMetrics(
                total_commits=commit_stats.total_commits or 0,
                total_prs=total_prs,
                total_contributors=commit_stats.total_contributors or 0,
                total_repositories=commit_stats.total_repositories or 0,
                median_cycle_time_hours=round(median_cycle_time, 2),
                p90_cycle_time_hours=round(p90_cycle_time, 2),
                overall_merge_rate=round(merge_rate, 2)
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching org summary: {str(e)}")
