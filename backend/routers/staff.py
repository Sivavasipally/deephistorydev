"""Staff details router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel

from cli.config import Config
from cli.models import get_engine, get_session, StaffDetails, AuthorStaffMapping

router = APIRouter()

class StaffInfo(BaseModel):
    """Staff information model."""
    bank_id_1: str
    staff_id: str
    staff_name: str
    email_address: str
    tech_unit: str
    platform_name: str
    staff_type: str
    staff_status: str
    work_location: str
    rank: str
    sub_platform: str
    staff_grouping: str
    reporting_manager_name: str
    staff_start_date: str
    staff_end_date: str

@router.get("/", response_model=List[StaffInfo])
async def get_staff_list(
    search: str = Query(None, description="Search by name or email"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get staff list with optional search."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Exclude inactive staff members
            query = session.query(StaffDetails).filter(
                StaffDetails.bank_id_1.isnot(None),
                (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
            )

            if search:
                query = query.filter(
                    (StaffDetails.staff_name.ilike(f"%{search}%")) |
                    (StaffDetails.email_address.ilike(f"%{search}%"))
                )

            query = query.order_by(StaffDetails.staff_name).limit(limit)
            results = query.all()

            return [
                StaffInfo(
                    bank_id_1=r.bank_id_1,
                    staff_id=r.staff_id or "",
                    staff_name=r.staff_name or "",
                    email_address=r.email_address or "",
                    tech_unit=r.tech_unit or "",
                    platform_name=r.platform_name or "",
                    staff_type=r.staff_type or "",
                    staff_status=r.staff_status or "",
                    work_location=r.work_location or "",
                    rank=r.rank or "",
                    sub_platform=r.sub_platform or "",
                    staff_grouping=r.staff_grouping or "",
                    reporting_manager_name=r.reporting_manager_name or "",
                    staff_start_date=str(r.staff_start_date) if r.staff_start_date else "",
                    staff_end_date=str(r.staff_end_date) if r.staff_end_date else ""
                )
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching staff: {str(e)}")

@router.get("/unmapped", response_model=List[StaffInfo])
async def get_unmapped_staff(
    search: str = Query(None, description="Search by name or email"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get staff members who are NOT mapped to any author."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Get staff members who do NOT have a mapping
            # Subquery to get all bank_id_1 values that have mappings
            mapped_bank_ids = session.query(AuthorStaffMapping.bank_id_1).distinct().subquery()

            # Main query: active staff NOT in the mapped list
            query = session.query(StaffDetails).filter(
                StaffDetails.bank_id_1.isnot(None),
                (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None)),
                ~StaffDetails.bank_id_1.in_(mapped_bank_ids)  # NOT in mapped list
            )

            if search:
                query = query.filter(
                    (StaffDetails.staff_name.ilike(f"%{search}%")) |
                    (StaffDetails.email_address.ilike(f"%{search}%"))
                )

            query = query.order_by(StaffDetails.staff_name).limit(limit)
            results = query.all()

            return [
                StaffInfo(
                    bank_id_1=r.bank_id_1,
                    staff_id=r.staff_id or "",
                    staff_name=r.staff_name or "",
                    email_address=r.email_address or "",
                    tech_unit=r.tech_unit or "",
                    platform_name=r.platform_name or "",
                    staff_type=r.staff_type or "",
                    staff_status=r.staff_status or "",
                    work_location=r.work_location or "",
                    rank=r.rank or "",
                    sub_platform=r.sub_platform or "",
                    staff_grouping=r.staff_grouping or "",
                    reporting_manager_name=r.reporting_manager_name or "",
                    staff_start_date=str(r.staff_start_date) if r.staff_start_date else "",
                    staff_end_date=str(r.staff_end_date) if r.staff_end_date else ""
                )
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unmapped staff: {str(e)}")
