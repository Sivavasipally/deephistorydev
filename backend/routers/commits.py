"""Commits router for commit data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config import Config
from models import get_engine, get_session, Commit, Repository

router = APIRouter()

class CommitDetail(BaseModel):
    """Commit detail model."""
    commit_hash: str
    author_name: str
    author_email: str
    committer_name: str
    commit_date: datetime
    message: str
    lines_added: int
    lines_deleted: int
    total_lines: int
    files_changed: int
    branch: str
    repository: str
    project_key: str

@router.get("/", response_model=List[CommitDetail])
async def get_commits(
    author: Optional[str] = Query(None, description="Filter by author name"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get commits with optional filters.

    Args:
        author: Filter by author name
        repository: Filter by repository slug
        branch: Filter by branch name
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of commits
        offset: Number of commits to skip

    Returns:
        List of commits
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(
                Commit.commit_hash,
                Commit.author_name,
                Commit.author_email,
                Commit.committer_name,
                Commit.commit_date,
                Commit.message,
                Commit.lines_added,
                Commit.lines_deleted,
                (Commit.lines_added + Commit.lines_deleted).label('total_lines'),
                Commit.files_changed,
                Commit.branch,
                Repository.slug_name,
                Repository.project_key
            ).join(
                Repository, Commit.repository_id == Repository.id
            )

            # Apply filters
            if author:
                query = query.filter(Commit.author_name.ilike(f"%{author}%"))
            if repository:
                query = query.filter(Repository.slug_name.ilike(f"%{repository}%"))
            if branch:
                query = query.filter(Commit.branch.ilike(f"%{branch}%"))
            if start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Commit.commit_date >= start_datetime)
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Commit.commit_date <= end_datetime)

            # Order and paginate
            query = query.order_by(desc(Commit.commit_date)).limit(limit).offset(offset)

            results = query.all()

            return [
                CommitDetail(
                    commit_hash=r.commit_hash,
                    author_name=r.author_name,
                    author_email=r.author_email,
                    committer_name=r.committer_name,
                    commit_date=r.commit_date,
                    message=r.message,
                    lines_added=r.lines_added,
                    lines_deleted=r.lines_deleted,
                    total_lines=r.total_lines,
                    files_changed=r.files_changed,
                    branch=r.branch,
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
        raise HTTPException(status_code=500, detail=f"Error fetching commits: {str(e)}")

@router.get("/top-by-lines")
async def get_top_commits_by_lines(limit: int = Query(10, ge=1, le=100)):
    """Get top commits by lines changed."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(
                Commit.commit_hash,
                Commit.author_name,
                Commit.commit_date,
                Commit.message,
                Commit.lines_added,
                Commit.lines_deleted,
                (Commit.lines_added + Commit.lines_deleted).label('total_lines'),
                Commit.files_changed,
                Repository.project_key,
                Repository.slug_name
            ).join(
                Repository, Commit.repository_id == Repository.id
            ).order_by(
                desc('total_lines')
            ).limit(limit)

            results = query.all()

            return [
                {
                    "commit_hash": r.commit_hash[:8],
                    "full_hash": r.commit_hash,
                    "author": r.author_name,
                    "date": r.commit_date.isoformat(),
                    "message": r.message[:100] + "..." if len(r.message) > 100 else r.message,
                    "lines_added": r.lines_added,
                    "lines_deleted": r.lines_deleted,
                    "total_lines": r.total_lines,
                    "files_changed": r.files_changed,
                    "repository": f"{r.project_key}/{r.slug_name}"
                }
                for r in results
            ]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top commits: {str(e)}")
