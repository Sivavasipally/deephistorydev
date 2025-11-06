"""Staff details router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel

from config import Config
from models import get_engine, get_session, StaffDetails

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
            query = session.query(StaffDetails).filter(
                StaffDetails.bank_id_1.isnot(None)
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
                    staff_status=r.staff_status or ""
                )
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching staff: {str(e)}")
