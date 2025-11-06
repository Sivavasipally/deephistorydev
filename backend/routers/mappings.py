"""Author-staff mapping router."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Body
from sqlalchemy import func
from typing import List
from datetime import datetime
from pydantic import BaseModel

from config import Config
from models import get_engine, get_session, AuthorStaffMapping, Commit, StaffDetails

router = APIRouter()

class MappingCreate(BaseModel):
    """Mapping creation model."""
    author_name: str
    author_email: str
    bank_id_1: str
    staff_id: str
    staff_name: str
    notes: str = ""

class MappingResponse(BaseModel):
    """Mapping response model."""
    id: int
    author_name: str
    author_email: str
    bank_id_1: str
    staff_id: str
    staff_name: str
    mapped_date: datetime
    notes: str

@router.get("/", response_model=List[MappingResponse])
async def get_mappings():
    """Get all author-staff mappings."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            mappings = session.query(AuthorStaffMapping).order_by(
                AuthorStaffMapping.author_name
            ).all()

            return [
                MappingResponse(
                    id=m.id,
                    author_name=m.author_name,
                    author_email=m.author_email or "",
                    bank_id_1=m.bank_id_1 or "",
                    staff_id=m.staff_id or "",
                    staff_name=m.staff_name or "",
                    mapped_date=m.mapped_date,
                    notes=m.notes or ""
                )
                for m in mappings
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mappings: {str(e)}")

@router.post("/", response_model=MappingResponse)
async def create_mapping(mapping: MappingCreate = Body(...)):
    """Create a new author-staff mapping."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Check if mapping already exists
            existing = session.query(AuthorStaffMapping).filter_by(
                author_name=mapping.author_name
            ).first()

            if existing:
                # Update existing
                existing.author_email = mapping.author_email
                existing.bank_id_1 = mapping.bank_id_1
                existing.staff_id = mapping.staff_id
                existing.staff_name = mapping.staff_name
                existing.mapped_date = datetime.utcnow()
                existing.notes = mapping.notes
                session.commit()
                session.refresh(existing)
                result = existing
            else:
                # Create new
                new_mapping = AuthorStaffMapping(
                    author_name=mapping.author_name,
                    author_email=mapping.author_email,
                    bank_id_1=mapping.bank_id_1,
                    staff_id=mapping.staff_id,
                    staff_name=mapping.staff_name,
                    notes=mapping.notes
                )
                session.add(new_mapping)
                session.commit()
                session.refresh(new_mapping)
                result = new_mapping

            return MappingResponse(
                id=result.id,
                author_name=result.author_name,
                author_email=result.author_email or "",
                bank_id_1=result.bank_id_1 or "",
                staff_id=result.staff_id or "",
                staff_name=result.staff_name or "",
                mapped_date=result.mapped_date,
                notes=result.notes or ""
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating mapping: {str(e)}")

@router.delete("/{author_name}")
async def delete_mapping(author_name: str):
    """Delete an author-staff mapping."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            mapping = session.query(AuthorStaffMapping).filter_by(
                author_name=author_name
            ).first()

            if not mapping:
                raise HTTPException(status_code=404, detail="Mapping not found")

            session.delete(mapping)
            session.commit()

            return {"success": True, "message": f"Deleted mapping for {author_name}"}

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting mapping: {str(e)}")

@router.get("/unmapped-authors")
async def get_unmapped_authors():
    """Get list of authors without mappings."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            # Get all authors with their commit counts
            authors = session.query(
                Commit.author_name,
                Commit.author_email,
                func.count(Commit.id).label('commit_count')
            ).group_by(
                Commit.author_name,
                Commit.author_email
            ).all()

            # Get mapped authors
            mapped_authors = {m.author_name for m in session.query(AuthorStaffMapping).all()}

            # Filter out mapped authors
            unmapped = [
                {
                    "author_name": a.author_name,
                    "author_email": a.author_email,
                    "commit_count": a.commit_count
                }
                for a in authors
                if a.author_name not in mapped_authors
            ]

            return unmapped

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unmapped authors: {str(e)}")
