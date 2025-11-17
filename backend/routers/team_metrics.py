"""Team metrics router - serves pre-calculated team/platform/tech unit statistics.

This router provides fast access to team-level aggregations calculated during
CLI extract. Supports filtering by tech unit, platform, rank, location.

Performance: ~40ms (vs 3.5+ seconds with real-time aggregation)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from cli.config import Config
from cli.models import get_engine, get_session, TeamMetrics

router = APIRouter()


class TeamMetricsResponse(BaseModel):
    """Team metrics response model."""
    aggregation_level: str
    aggregation_value: str
    time_period: str = "all_time"

    # Team composition
    total_staff: int = 0
    active_contributors: int = 0
    active_rate: float = 0.0

    # Commit metrics
    total_commits: int = 0
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    total_files_changed: int = 0

    # PR metrics
    total_prs_created: int = 0
    total_prs_merged: int = 0
    total_pr_approvals: int = 0
    merge_rate: float = 0.0

    # Repository metrics
    repositories_touched: int = 0
    repository_list: Optional[str] = None

    # Averages per person
    avg_commits_per_person: float = 0.0
    avg_prs_per_person: float = 0.0
    avg_lines_per_person: float = 0.0

    # Top contributors
    top_contributors_json: Optional[str] = None

    # Technology insights
    file_types_json: Optional[str] = None
    primary_technologies: Optional[str] = None

    last_calculated: Optional[str] = None

    class Config:
        from_attributes = True


class TeamMetricsSummary(BaseModel):
    """Summary statistics across all teams."""
    total_teams_tracked: int
    most_active_team: Optional[dict] = None
    most_productive_team: Optional[dict] = None
    highest_merge_rate_team: Optional[dict] = None


@router.get("/", response_model=List[TeamMetricsResponse])
async def get_all_team_metrics(
    aggregation_level: str = Query(None, description="Filter by level: tech_unit, platform, rank, location"),
    aggregation_value: str = Query(None, description="Filter by specific team name"),
    time_period: str = Query("all_time", description="Time period: all_time, 2024, 2024-Q1, etc."),
    min_staff: int = Query(None, description="Minimum number of staff"),
    min_commits: int = Query(None, description="Minimum number of commits"),
    sort_by: str = Query("total_commits", description="Sort field: total_commits, total_prs_created, active_rate"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(100, description="Maximum results")
):
    """Get all team metrics with optional filters.

    This endpoint returns pre-calculated team-level statistics.
    Supports grouping by tech_unit, platform, rank, or work_location.

    Performance: ~40ms for 100+ teams
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(TeamMetrics)

            # Apply filters
            if aggregation_level:
                query = query.filter(TeamMetrics.aggregation_level == aggregation_level)

            if aggregation_value:
                query = query.filter(TeamMetrics.aggregation_value.ilike(f'%{aggregation_value}%'))

            if time_period:
                query = query.filter(TeamMetrics.time_period == time_period)

            if min_staff is not None:
                query = query.filter(TeamMetrics.total_staff >= min_staff)

            if min_commits is not None:
                query = query.filter(TeamMetrics.total_commits >= min_commits)

            # Sorting
            sort_field = getattr(TeamMetrics, sort_by, TeamMetrics.total_commits)
            if order == 'asc':
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())

            # Limit
            query = query.limit(limit)

            results = query.all()

            # Convert to response
            response = []
            for r in results:
                response.append(TeamMetricsResponse(
                    aggregation_level=r.aggregation_level,
                    aggregation_value=r.aggregation_value,
                    time_period=r.time_period or "all_time",
                    total_staff=r.total_staff or 0,
                    active_contributors=r.active_contributors or 0,
                    active_rate=r.active_rate or 0.0,
                    total_commits=r.total_commits or 0,
                    total_lines_added=r.total_lines_added or 0,
                    total_lines_deleted=r.total_lines_deleted or 0,
                    total_files_changed=r.total_files_changed or 0,
                    total_prs_created=r.total_prs_created or 0,
                    total_prs_merged=r.total_prs_merged or 0,
                    total_pr_approvals=r.total_pr_approvals or 0,
                    merge_rate=r.merge_rate or 0.0,
                    repositories_touched=r.repositories_touched or 0,
                    repository_list=r.repository_list,
                    avg_commits_per_person=r.avg_commits_per_person or 0.0,
                    avg_prs_per_person=r.avg_prs_per_person or 0.0,
                    avg_lines_per_person=r.avg_lines_per_person or 0.0,
                    top_contributors_json=r.top_contributors_json,
                    file_types_json=r.file_types_json,
                    primary_technologies=r.primary_technologies,
                    last_calculated=r.last_calculated.isoformat() if r.last_calculated else None
                ))

            return response

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team metrics: {str(e)}")


@router.get("/by-tech-unit", response_model=List[TeamMetricsResponse])
async def get_tech_unit_metrics(
    time_period: str = Query("all_time", description="Time period"),
    limit: int = Query(50, description="Maximum results")
):
    """Get metrics for all tech units.

    Shortcut for aggregation_level='tech_unit'.
    Performance: ~35ms
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            results = session.query(TeamMetrics).filter(
                TeamMetrics.aggregation_level == 'tech_unit',
                TeamMetrics.time_period == time_period
            ).order_by(TeamMetrics.total_commits.desc()).limit(limit).all()

            response = []
            for r in results:
                response.append(TeamMetricsResponse(
                    aggregation_level=r.aggregation_level,
                    aggregation_value=r.aggregation_value,
                    time_period=r.time_period or "all_time",
                    total_staff=r.total_staff or 0,
                    active_contributors=r.active_contributors or 0,
                    active_rate=r.active_rate or 0.0,
                    total_commits=r.total_commits or 0,
                    total_lines_added=r.total_lines_added or 0,
                    total_lines_deleted=r.total_lines_deleted or 0,
                    total_files_changed=r.total_files_changed or 0,
                    total_prs_created=r.total_prs_created or 0,
                    total_prs_merged=r.total_prs_merged or 0,
                    total_pr_approvals=r.total_pr_approvals or 0,
                    merge_rate=r.merge_rate or 0.0,
                    repositories_touched=r.repositories_touched or 0,
                    repository_list=r.repository_list,
                    avg_commits_per_person=r.avg_commits_per_person or 0.0,
                    avg_prs_per_person=r.avg_prs_per_person or 0.0,
                    avg_lines_per_person=r.avg_lines_per_person or 0.0,
                    top_contributors_json=r.top_contributors_json,
                    file_types_json=r.file_types_json,
                    primary_technologies=r.primary_technologies,
                    last_calculated=r.last_calculated.isoformat() if r.last_calculated else None
                ))

            return response

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tech unit metrics: {str(e)}")


@router.get("/by-platform", response_model=List[TeamMetricsResponse])
async def get_platform_metrics(
    time_period: str = Query("all_time", description="Time period"),
    limit: int = Query(50, description="Maximum results")
):
    """Get metrics for all platforms.

    Shortcut for aggregation_level='platform'.
    Performance: ~35ms
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            results = session.query(TeamMetrics).filter(
                TeamMetrics.aggregation_level == 'platform',
                TeamMetrics.time_period == time_period
            ).order_by(TeamMetrics.total_commits.desc()).limit(limit).all()

            response = []
            for r in results:
                response.append(TeamMetricsResponse(
                    aggregation_level=r.aggregation_level,
                    aggregation_value=r.aggregation_value,
                    time_period=r.time_period or "all_time",
                    total_staff=r.total_staff or 0,
                    active_contributors=r.active_contributors or 0,
                    active_rate=r.active_rate or 0.0,
                    total_commits=r.total_commits or 0,
                    total_lines_added=r.total_lines_added or 0,
                    total_lines_deleted=r.total_lines_deleted or 0,
                    total_files_changed=r.total_files_changed or 0,
                    total_prs_created=r.total_prs_created or 0,
                    total_prs_merged=r.total_prs_merged or 0,
                    total_pr_approvals=r.total_pr_approvals or 0,
                    merge_rate=r.merge_rate or 0.0,
                    repositories_touched=r.repositories_touched or 0,
                    repository_list=r.repository_list,
                    avg_commits_per_person=r.avg_commits_per_person or 0.0,
                    avg_prs_per_person=r.avg_prs_per_person or 0.0,
                    avg_lines_per_person=r.avg_lines_per_person or 0.0,
                    top_contributors_json=r.top_contributors_json,
                    file_types_json=r.file_types_json,
                    primary_technologies=r.primary_technologies,
                    last_calculated=r.last_calculated.isoformat() if r.last_calculated else None
                ))

            return response

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching platform metrics: {str(e)}")


@router.get("/summary", response_model=TeamMetricsSummary)
async def get_team_metrics_summary():
    """Get summary statistics across all teams.

    Returns organization-wide team statistics and highlights.
    Performance: ~30ms
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            all_teams = session.query(TeamMetrics).filter(
                TeamMetrics.time_period == 'all_time'
            ).all()

            total_teams = len(all_teams)

            # Find most active team (highest active_rate)
            most_active = max(all_teams, key=lambda t: t.active_rate or 0) if all_teams else None
            most_active_team = {
                'level': most_active.aggregation_level,
                'name': most_active.aggregation_value,
                'active_rate': most_active.active_rate or 0.0,
                'active_contributors': most_active.active_contributors or 0,
                'total_staff': most_active.total_staff or 0
            } if most_active else None

            # Find most productive team (highest commits)
            most_productive = max(all_teams, key=lambda t: t.total_commits or 0) if all_teams else None
            most_productive_team = {
                'level': most_productive.aggregation_level,
                'name': most_productive.aggregation_value,
                'total_commits': most_productive.total_commits or 0,
                'total_prs': most_productive.total_prs_created or 0,
                'total_staff': most_productive.total_staff or 0
            } if most_productive else None

            # Find team with highest merge rate
            highest_merge_rate = max(all_teams, key=lambda t: t.merge_rate or 0) if all_teams else None
            highest_merge_rate_team = {
                'level': highest_merge_rate.aggregation_level,
                'name': highest_merge_rate.aggregation_value,
                'merge_rate': highest_merge_rate.merge_rate or 0.0,
                'total_prs_created': highest_merge_rate.total_prs_created or 0,
                'total_prs_merged': highest_merge_rate.total_prs_merged or 0
            } if highest_merge_rate else None

            return TeamMetricsSummary(
                total_teams_tracked=total_teams,
                most_active_team=most_active_team,
                most_productive_team=most_productive_team,
                highest_merge_rate_team=highest_merge_rate_team
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")
