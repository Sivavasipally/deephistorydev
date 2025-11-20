"""Staff metrics router - serves pre-calculated staff productivity metrics."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from cli.config import Config
from cli.models import get_engine, get_session, StaffMetrics, CurrentYearStaffMetrics
from cli.staff_metrics_calculator import StaffMetricsCalculator

router = APIRouter()


class StaffMetricsResponse(BaseModel):
    """Staff metrics response model."""
    # Identification
    bank_id_1: str
    staff_id: Optional[str] = ""
    staff_name: Optional[str] = ""
    email_address: Optional[str] = ""

    # Organizational
    tech_unit: Optional[str] = ""
    platform_name: Optional[str] = ""
    staff_type: Optional[str] = ""
    original_staff_type: Optional[str] = ""
    staff_status: Optional[str] = ""
    work_location: Optional[str] = ""
    rank: Optional[str] = ""
    staff_level: Optional[str] = ""
    hr_role: Optional[str] = ""
    job_function: Optional[str] = ""
    department_id: Optional[str] = ""
    company_name: Optional[str] = ""
    sub_platform: Optional[str] = ""
    staff_grouping: Optional[str] = ""
    reporting_manager_name: Optional[str] = ""

    # Commit Metrics
    total_commits: int = 0
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    total_files_changed: int = 0
    total_chars_added: int = 0
    total_chars_deleted: int = 0

    # PR Metrics
    total_prs_created: int = 0
    total_prs_merged: int = 0
    total_pr_approvals_given: int = 0

    # Repository Metrics
    repositories_touched: int = 0
    repository_list: Optional[str] = ""

    # Activity Timeline
    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None
    first_pr_date: Optional[str] = None
    last_pr_date: Optional[str] = None

    # Technology Insights
    file_types_worked: Optional[str] = ""
    primary_file_type: Optional[str] = ""

    # Metadata
    last_calculated: Optional[str] = None
    calculation_version: Optional[str] = ""

    # Derived Metrics
    avg_lines_per_commit: float = 0.0
    avg_files_per_commit: float = 0.0
    code_churn_ratio: float = 0.0


class CurrentYearStaffMetricsResponse(BaseModel):
    """Current year staff metrics response model."""
    # Staff Identification
    bank_id_1: str
    staff_name: Optional[str] = ""
    staff_email: Optional[str] = ""
    staff_status: Optional[str] = ""
    staff_pc_code: Optional[str] = ""
    default_role: Optional[str] = ""

    # Organizational Fields
    work_location: Optional[str] = ""
    staff_type: Optional[str] = ""
    rank: Optional[str] = ""
    job_function: Optional[str] = ""
    sub_platform: Optional[str] = ""
    reporting_manager_name: Optional[str] = ""

    # Current Year Context
    current_year: Optional[int] = None
    cy_start_date: Optional[str] = None
    cy_end_date: Optional[str] = None

    # Activity Totals
    cy_total_commits: int = 0
    cy_total_prs: int = 0
    cy_total_approvals_given: int = 0
    cy_total_code_reviews_given: int = 0
    cy_total_code_reviews_received: int = 0
    cy_total_repositories: int = 0
    cy_total_files_changed: int = 0
    cy_total_lines_changed: int = 0
    cy_total_chars: int = 0
    cy_total_code_churn: int = 0

    # Diversity Metrics
    cy_different_file_types: int = 0
    cy_different_repositories: int = 0
    cy_different_project_keys: int = 0

    # File Type Distribution Percentages
    cy_pct_code: float = 0.0
    cy_pct_config: float = 0.0
    cy_pct_documentation: float = 0.0
    cy_pct_others: float = 0.0

    # Monthly Averages
    cy_avg_commits_monthly: float = 0.0
    cy_avg_prs_monthly: float = 0.0
    cy_avg_approvals_monthly: float = 0.0

    # Details Lists
    cy_file_types_list: Optional[str] = ""
    cy_repositories_list: Optional[str] = ""
    cy_project_keys_list: Optional[str] = ""

    # Monthly Breakdown
    cy_monthly_commits: Optional[str] = ""
    cy_monthly_prs: Optional[str] = ""
    cy_monthly_approvals: Optional[str] = ""

    # Metadata
    last_calculated: Optional[str] = None
    calculation_version: Optional[str] = ""


class StaffMetricsSummary(BaseModel):
    """Summary statistics for staff metrics."""
    total_staff: int
    active_staff: int
    inactive_staff: int
    staff_with_commits: int
    staff_with_prs: int
    total_commits_all: int
    total_prs_all: int


@router.get("/", response_model=List[StaffMetricsResponse])
async def get_all_staff_metrics(
    search: str = Query(None, description="Search by name or email"),
    tech_unit: str = Query(None, description="Filter by tech unit"),
    platform_name: str = Query(None, description="Filter by platform"),
    staff_status: str = Query(None, description="Filter by status"),
    work_location: str = Query(None, description="Filter by location"),
    rank: str = Query(None, description="Filter by rank"),
    limit: int = Query(10000, ge=1, le=10000),
    exclude_zero_activity: bool = Query(False, description="Exclude staff with no commits/PRs")
):
    """Get all staff metrics with optional filters.

    This endpoint returns pre-calculated metrics for fast dashboard loading.
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Build query
            query = session.query(StaffMetrics)

            # Apply filters
            if search:
                query = query.filter(
                    (StaffMetrics.staff_name.ilike(f"%{search}%")) |
                    (StaffMetrics.email_address.ilike(f"%{search}%"))
                )

            if tech_unit:
                query = query.filter(StaffMetrics.tech_unit == tech_unit)

            if platform_name:
                query = query.filter(StaffMetrics.platform_name == platform_name)

            if staff_status:
                query = query.filter(StaffMetrics.staff_status == staff_status)
            else:
                # Exclude inactive staff by default
                query = query.filter(
                    (StaffMetrics.staff_status != 'Inactive') |
                    (StaffMetrics.staff_status.is_(None))
                )

            if work_location:
                query = query.filter(StaffMetrics.work_location == work_location)

            if rank:
                query = query.filter(StaffMetrics.rank == rank)

            if exclude_zero_activity:
                query = query.filter(
                    (StaffMetrics.total_commits > 0) |
                    (StaffMetrics.total_prs_created > 0)
                )

            # Order by activity (most active first)
            query = query.order_by(StaffMetrics.total_commits.desc()).limit(limit)

            results = query.all()

            return [
                StaffMetricsResponse(
                    bank_id_1=r.bank_id_1,
                    staff_id=r.staff_id or "",
                    staff_name=r.staff_name or "",
                    email_address=r.email_address or "",
                    tech_unit=r.tech_unit or "",
                    platform_name=r.platform_name or "",
                    staff_type=r.staff_type or "",
                    original_staff_type=r.original_staff_type or "",
                    staff_status=r.staff_status or "",
                    work_location=r.work_location or "",
                    rank=r.rank or "",
                    staff_level=r.staff_level or "",
                    hr_role=r.hr_role or "",
                    job_function=r.job_function or "",
                    department_id=r.department_id or "",
                    company_name=r.company_name or "",
                    sub_platform=r.sub_platform or "",
                    staff_grouping=r.staff_grouping or "",
                    reporting_manager_name=r.reporting_manager_name or "",
                    total_commits=r.total_commits,
                    total_lines_added=r.total_lines_added,
                    total_lines_deleted=r.total_lines_deleted,
                    total_files_changed=r.total_files_changed,
                    total_chars_added=r.total_chars_added,
                    total_chars_deleted=r.total_chars_deleted,
                    total_prs_created=r.total_prs_created,
                    total_prs_merged=r.total_prs_merged,
                    total_pr_approvals_given=r.total_pr_approvals_given,
                    repositories_touched=r.repositories_touched,
                    repository_list=r.repository_list or "",
                    first_commit_date=str(r.first_commit_date) if r.first_commit_date else None,
                    last_commit_date=str(r.last_commit_date) if r.last_commit_date else None,
                    first_pr_date=str(r.first_pr_date) if r.first_pr_date else None,
                    last_pr_date=str(r.last_pr_date) if r.last_pr_date else None,
                    file_types_worked=r.file_types_worked or "",
                    primary_file_type=r.primary_file_type or "",
                    last_calculated=str(r.last_calculated) if r.last_calculated else None,
                    calculation_version=r.calculation_version or "",
                    avg_lines_per_commit=r.avg_lines_per_commit,
                    avg_files_per_commit=r.avg_files_per_commit,
                    code_churn_ratio=r.code_churn_ratio
                )
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching staff metrics: {str(e)}")


@router.get("/summary", response_model=StaffMetricsSummary)
async def get_staff_metrics_summary():
    """Get summary statistics for all staff metrics."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Total staff
            total_staff = session.query(StaffMetrics).count()

            # Active staff
            active_staff = session.query(StaffMetrics).filter(
                (StaffMetrics.staff_status != 'Inactive') |
                (StaffMetrics.staff_status.is_(None))
            ).count()

            # Staff with activity
            staff_with_commits = session.query(StaffMetrics).filter(
                StaffMetrics.total_commits > 0
            ).count()

            staff_with_prs = session.query(StaffMetrics).filter(
                StaffMetrics.total_prs_created > 0
            ).count()

            # Total metrics
            from sqlalchemy import func
            totals = session.query(
                func.sum(StaffMetrics.total_commits),
                func.sum(StaffMetrics.total_prs_created)
            ).first()

            return StaffMetricsSummary(
                total_staff=total_staff,
                active_staff=active_staff,
                inactive_staff=total_staff - active_staff,
                staff_with_commits=staff_with_commits,
                staff_with_prs=staff_with_prs,
                total_commits_all=totals[0] or 0,
                total_prs_all=totals[1] or 0
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")


# ========================================
# Current Year Staff Metrics Endpoints
# ========================================

@router.get("/current-year", response_model=List[CurrentYearStaffMetricsResponse])
async def get_all_current_year_staff_metrics(
    search: str = Query(None, description="Search by name or email"),
    staff_status: str = Query(None, description="Filter by status"),
    work_location: str = Query(None, description="Filter by work location"),
    staff_type: str = Query(None, description="Filter by staff type"),
    rank: str = Query(None, description="Filter by rank"),
    job_function: str = Query(None, description="Filter by job function"),
    sub_platform: str = Query(None, description="Filter by sub platform"),
    reporting_manager_name: str = Query(None, description="Filter by reporting manager"),
    limit: int = Query(10000, ge=1, le=10000),
):
    """Get current year metrics for all staff members with multiple filter options."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Base query
            query = session.query(CurrentYearStaffMetrics)

            # Apply filters
            if search:
                query = query.filter(
                    (CurrentYearStaffMetrics.staff_name.ilike(f'%{search}%')) |
                    (CurrentYearStaffMetrics.staff_email.ilike(f'%{search}%'))
                )

            if staff_status:
                query = query.filter(CurrentYearStaffMetrics.staff_status == staff_status)
            else:
                # Exclude inactive staff by default
                query = query.filter(
                    (CurrentYearStaffMetrics.staff_status != 'Inactive') |
                    (CurrentYearStaffMetrics.staff_status.is_(None))
                )

            # Apply organizational filters
            if work_location:
                query = query.filter(CurrentYearStaffMetrics.work_location == work_location)

            if staff_type:
                query = query.filter(CurrentYearStaffMetrics.staff_type == staff_type)

            if rank:
                query = query.filter(CurrentYearStaffMetrics.rank == rank)

            if job_function:
                query = query.filter(CurrentYearStaffMetrics.job_function == job_function)

            if sub_platform:
                query = query.filter(CurrentYearStaffMetrics.sub_platform == sub_platform)

            if reporting_manager_name:
                query = query.filter(CurrentYearStaffMetrics.reporting_manager_name.ilike(f'%{reporting_manager_name}%'))

            # Order by activity (most active first)
            query = query.order_by(CurrentYearStaffMetrics.cy_total_commits.desc()).limit(limit)

            results = query.all()

            return [
                CurrentYearStaffMetricsResponse(
                    bank_id_1=r.bank_id_1,
                    staff_name=r.staff_name or "",
                    staff_email=r.staff_email or "",
                    staff_status=r.staff_status or "",
                    staff_pc_code=r.staff_pc_code or "",
                    default_role=r.default_role or "",
                    work_location=r.work_location or "",
                    staff_type=r.staff_type or "",
                    rank=r.rank or "",
                    job_function=r.job_function or "",
                    sub_platform=r.sub_platform or "",
                    reporting_manager_name=r.reporting_manager_name or "",
                    current_year=r.current_year,
                    cy_start_date=str(r.cy_start_date) if r.cy_start_date else None,
                    cy_end_date=str(r.cy_end_date) if r.cy_end_date else None,
                    cy_total_commits=r.cy_total_commits or 0,
                    cy_total_prs=r.cy_total_prs or 0,
                    cy_total_approvals_given=r.cy_total_approvals_given or 0,
                    cy_total_code_reviews_given=r.cy_total_code_reviews_given or 0,
                    cy_total_code_reviews_received=r.cy_total_code_reviews_received or 0,
                    cy_total_repositories=r.cy_total_repositories or 0,
                    cy_total_files_changed=r.cy_total_files_changed or 0,
                    cy_total_lines_changed=r.cy_total_lines_changed or 0,
                    cy_total_chars=r.cy_total_chars or 0,
                    cy_total_code_churn=r.cy_total_code_churn or 0,
                    cy_different_file_types=r.cy_different_file_types or 0,
                    cy_different_repositories=r.cy_different_repositories or 0,
                    cy_different_project_keys=r.cy_different_project_keys or 0,
                    cy_pct_code=r.cy_pct_code or 0.0,
                    cy_pct_config=r.cy_pct_config or 0.0,
                    cy_pct_documentation=r.cy_pct_documentation or 0.0,
                    cy_pct_others=r.cy_pct_others or 0.0,
                    cy_avg_commits_monthly=r.cy_avg_commits_monthly or 0.0,
                    cy_avg_prs_monthly=r.cy_avg_prs_monthly or 0.0,
                    cy_avg_approvals_monthly=r.cy_avg_approvals_monthly or 0.0,
                    cy_file_types_list=r.cy_file_types_list or "",
                    cy_repositories_list=r.cy_repositories_list or "",
                    cy_project_keys_list=r.cy_project_keys_list or "",
                    cy_monthly_commits=r.cy_monthly_commits or "",
                    cy_monthly_prs=r.cy_monthly_prs or "",
                    cy_monthly_approvals=r.cy_monthly_approvals or "",
                    last_calculated=str(r.last_calculated) if r.last_calculated else None,
                    calculation_version=r.calculation_version or ""
                )
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching current year staff metrics: {str(e)}")


@router.get("/current-year/{bank_id}", response_model=CurrentYearStaffMetricsResponse)
async def get_current_year_staff_metrics_by_id(bank_id: str):
    """Get current year metrics for a specific staff member by bank ID."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            metric = session.query(CurrentYearStaffMetrics).filter(
                CurrentYearStaffMetrics.bank_id_1 == bank_id
            ).first()

            if not metric:
                raise HTTPException(status_code=404, detail=f"Current year staff metrics not found for {bank_id}")

            return CurrentYearStaffMetricsResponse(
                bank_id_1=metric.bank_id_1,
                staff_name=metric.staff_name or "",
                staff_email=metric.staff_email or "",
                staff_status=metric.staff_status or "",
                staff_pc_code=metric.staff_pc_code or "",
                default_role=metric.default_role or "",
                work_location=metric.work_location or "",
                staff_type=metric.staff_type or "",
                rank=metric.rank or "",
                job_function=metric.job_function or "",
                sub_platform=metric.sub_platform or "",
                reporting_manager_name=metric.reporting_manager_name or "",
                current_year=metric.current_year,
                cy_start_date=str(metric.cy_start_date) if metric.cy_start_date else None,
                cy_end_date=str(metric.cy_end_date) if metric.cy_end_date else None,
                cy_total_commits=metric.cy_total_commits or 0,
                cy_total_prs=metric.cy_total_prs or 0,
                cy_total_approvals_given=metric.cy_total_approvals_given or 0,
                cy_total_code_reviews_given=metric.cy_total_code_reviews_given or 0,
                cy_total_code_reviews_received=metric.cy_total_code_reviews_received or 0,
                cy_total_repositories=metric.cy_total_repositories or 0,
                cy_total_files_changed=metric.cy_total_files_changed or 0,
                cy_total_lines_changed=metric.cy_total_lines_changed or 0,
                cy_total_chars=metric.cy_total_chars or 0,
                cy_total_code_churn=metric.cy_total_code_churn or 0,
                cy_different_file_types=metric.cy_different_file_types or 0,
                cy_different_repositories=metric.cy_different_repositories or 0,
                cy_different_project_keys=metric.cy_different_project_keys or 0,
                cy_pct_code=metric.cy_pct_code or 0.0,
                cy_pct_config=metric.cy_pct_config or 0.0,
                cy_pct_documentation=metric.cy_pct_documentation or 0.0,
                cy_pct_others=metric.cy_pct_others or 0.0,
                cy_avg_commits_monthly=metric.cy_avg_commits_monthly or 0.0,
                cy_avg_prs_monthly=metric.cy_avg_prs_monthly or 0.0,
                cy_avg_approvals_monthly=metric.cy_avg_approvals_monthly or 0.0,
                cy_file_types_list=metric.cy_file_types_list or "",
                cy_repositories_list=metric.cy_repositories_list or "",
                cy_project_keys_list=metric.cy_project_keys_list or "",
                cy_monthly_commits=metric.cy_monthly_commits or "",
                cy_monthly_prs=metric.cy_monthly_prs or "",
                cy_monthly_approvals=metric.cy_monthly_approvals or "",
                last_calculated=str(metric.last_calculated) if metric.last_calculated else None,
                calculation_version=metric.calculation_version or ""
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching current year staff metrics: {str(e)}")


@router.get("/current-year/filter-options/unique-values")
async def get_current_year_filter_options():
    """Get unique values for all filter fields."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Get unique values for each filter field
            from sqlalchemy import distinct

            locations = [row[0] for row in session.query(distinct(CurrentYearStaffMetrics.work_location)).filter(
                CurrentYearStaffMetrics.work_location.isnot(None),
                CurrentYearStaffMetrics.work_location != ""
            ).all()]

            staff_types = [row[0] for row in session.query(distinct(CurrentYearStaffMetrics.staff_type)).filter(
                CurrentYearStaffMetrics.staff_type.isnot(None),
                CurrentYearStaffMetrics.staff_type != ""
            ).all()]

            ranks = [row[0] for row in session.query(distinct(CurrentYearStaffMetrics.rank)).filter(
                CurrentYearStaffMetrics.rank.isnot(None),
                CurrentYearStaffMetrics.rank != ""
            ).all()]

            job_functions = [row[0] for row in session.query(distinct(CurrentYearStaffMetrics.job_function)).filter(
                CurrentYearStaffMetrics.job_function.isnot(None),
                CurrentYearStaffMetrics.job_function != ""
            ).all()]

            sub_platforms = [row[0] for row in session.query(distinct(CurrentYearStaffMetrics.sub_platform)).filter(
                CurrentYearStaffMetrics.sub_platform.isnot(None),
                CurrentYearStaffMetrics.sub_platform != ""
            ).all()]

            managers = [row[0] for row in session.query(distinct(CurrentYearStaffMetrics.reporting_manager_name)).filter(
                CurrentYearStaffMetrics.reporting_manager_name.isnot(None),
                CurrentYearStaffMetrics.reporting_manager_name != ""
            ).all()]

            return {
                "locations": sorted(locations),
                "staff_types": sorted(staff_types),
                "ranks": sorted(ranks),
                "job_functions": sorted(job_functions),
                "sub_platforms": sorted(sub_platforms),
                "reporting_managers": sorted(managers)
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filter options: {str(e)}")


@router.get("/{bank_id}", response_model=StaffMetricsResponse)
async def get_staff_metrics_by_id(bank_id: str):
    """Get metrics for a specific staff member by bank ID."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            metric = session.query(StaffMetrics).filter(
                StaffMetrics.bank_id_1 == bank_id
            ).first()

            if not metric:
                raise HTTPException(status_code=404, detail=f"Staff metrics not found for {bank_id}")

            return StaffMetricsResponse(
                bank_id_1=metric.bank_id_1,
                staff_id=metric.staff_id or "",
                staff_name=metric.staff_name or "",
                email_address=metric.email_address or "",
                tech_unit=metric.tech_unit or "",
                platform_name=metric.platform_name or "",
                staff_type=metric.staff_type or "",
                original_staff_type=metric.original_staff_type or "",
                staff_status=metric.staff_status or "",
                work_location=metric.work_location or "",
                rank=metric.rank or "",
                staff_level=metric.staff_level or "",
                hr_role=metric.hr_role or "",
                job_function=metric.job_function or "",
                department_id=metric.department_id or "",
                company_name=metric.company_name or "",
                sub_platform=metric.sub_platform or "",
                staff_grouping=metric.staff_grouping or "",
                reporting_manager_name=metric.reporting_manager_name or "",
                total_commits=metric.total_commits,
                total_lines_added=metric.total_lines_added,
                total_lines_deleted=metric.total_lines_deleted,
                total_files_changed=metric.total_files_changed,
                total_chars_added=metric.total_chars_added,
                total_chars_deleted=metric.total_chars_deleted,
                total_prs_created=metric.total_prs_created,
                total_prs_merged=metric.total_prs_merged,
                total_pr_approvals_given=metric.total_pr_approvals_given,
                repositories_touched=metric.repositories_touched,
                repository_list=metric.repository_list or "",
                first_commit_date=str(metric.first_commit_date) if metric.first_commit_date else None,
                last_commit_date=str(metric.last_commit_date) if metric.last_commit_date else None,
                first_pr_date=str(metric.first_pr_date) if metric.first_pr_date else None,
                last_pr_date=str(metric.last_pr_date) if metric.last_pr_date else None,
                file_types_worked=metric.file_types_worked or "",
                primary_file_type=metric.primary_file_type or "",
                last_calculated=str(metric.last_calculated) if metric.last_calculated else None,
                calculation_version=metric.calculation_version or "",
                avg_lines_per_commit=metric.avg_lines_per_commit,
                avg_files_per_commit=metric.avg_files_per_commit,
                code_churn_ratio=metric.code_churn_ratio
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching staff metrics: {str(e)}")


@router.post("/recalculate/{bank_id}")
async def recalculate_staff_metrics(bank_id: str):
    """Recalculate metrics for a specific staff member.

    Useful after mapping changes or data updates.
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            calculator = StaffMetricsCalculator(session)
            result = calculator.recalculate_after_mapping_change(bank_id)

            if result:
                return {"message": f"Metrics recalculated successfully for {bank_id}"}
            else:
                raise HTTPException(status_code=500, detail="Failed to recalculate metrics")

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalculating metrics: {str(e)}")


@router.post("/recalculate-all")
async def recalculate_all_staff_metrics():
    """Recalculate metrics for all staff members.

    This is a potentially long-running operation.
    Use after bulk mapping changes or major data updates.
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            calculator = StaffMetricsCalculator(session)
            summary = calculator.calculate_all_staff_metrics()

            return {
                "message": "Metrics recalculated successfully for all staff",
                "summary": summary
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalculating all metrics: {str(e)}")
