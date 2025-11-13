"""Analytics router for file type and character-level metrics."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from collections import Counter
from sqlalchemy import func

from cli.config import Config
from cli.models import get_engine, get_session, Commit, Repository, StaffDetails, AuthorStaffMapping

router = APIRouter()

class FileTypeStats(BaseModel):
    """File type statistics model."""
    file_type: str
    commits: int
    chars_added: int
    chars_deleted: int
    lines_added: int
    lines_deleted: int
    total_churn: int

class CategoryStats(BaseModel):
    """Category statistics model."""
    category: str
    commits: int
    percentage: float
    chars_added: int
    chars_deleted: int

class CharacterMetrics(BaseModel):
    """Character-level metrics model."""
    total_chars_added: int
    total_chars_deleted: int
    total_churn: int
    avg_chars_per_commit: float
    commits_with_data: int
    total_commits: int

@router.get("/file-types/top", response_model=List[FileTypeStats])
async def get_top_file_types(
    limit: int = Query(10, ge=1, le=50),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    repository: Optional[str] = Query(None),
    staff_id: Optional[str] = Query(None)
):
    """
    Get top file types by commit count.

    Args:
        limit: Number of top file types to return
        start_date: Filter by start date (YYYY-MM-DD)
        end_date: Filter by end date (YYYY-MM-DD)
        repository: Filter by repository slug
        staff_id: Filter by staff bank_id

    Returns:
        List of file type statistics
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(Commit).filter(
                Commit.file_types != None,
                Commit.file_types != ''
            )

            # Apply filters
            if start_date:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Commit.commit_date >= start_datetime)

            if end_date:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Commit.commit_date <= end_datetime)

            if repository:
                query = query.join(Repository).filter(Repository.slug_name.ilike(f"%{repository}%"))

            if staff_id:
                # Get all author names for this staff member
                mappings = session.query(AuthorStaffMapping).filter(
                    AuthorStaffMapping.bank_id_1 == staff_id
                ).all()
                author_names = [m.author_name for m in mappings]
                if author_names:
                    query = query.filter(Commit.author_name.in_(author_names))
                else:
                    return []

            commits = query.all()

            # Aggregate file type stats
            file_type_stats = {}
            for commit in commits:
                types = commit.file_types.split(',')
                for file_type in types:
                    file_type = file_type.strip()
                    if not file_type:
                        continue

                    if file_type not in file_type_stats:
                        file_type_stats[file_type] = {
                            'commits': 0,
                            'chars_added': 0,
                            'chars_deleted': 0,
                            'lines_added': 0,
                            'lines_deleted': 0
                        }

                    file_type_stats[file_type]['commits'] += 1
                    file_type_stats[file_type]['chars_added'] += commit.chars_added or 0
                    file_type_stats[file_type]['chars_deleted'] += commit.chars_deleted or 0
                    file_type_stats[file_type]['lines_added'] += commit.lines_added or 0
                    file_type_stats[file_type]['lines_deleted'] += commit.lines_deleted or 0

            # Convert to response format and sort
            results = []
            for file_type, stats in file_type_stats.items():
                results.append(FileTypeStats(
                    file_type=file_type,
                    commits=stats['commits'],
                    chars_added=stats['chars_added'],
                    chars_deleted=stats['chars_deleted'],
                    lines_added=stats['lines_added'],
                    lines_deleted=stats['lines_deleted'],
                    total_churn=stats['chars_added'] + stats['chars_deleted']
                ))

            results.sort(key=lambda x: x.commits, reverse=True)
            return results[:limit]

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file-types/distribution", response_model=List[CategoryStats])
async def get_file_type_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    repository: Optional[str] = Query(None),
    staff_id: Optional[str] = Query(None)
):
    """
    Get file type distribution by category (code, config, docs).

    Args:
        start_date: Filter by start date (YYYY-MM-DD)
        end_date: Filter by end date (YYYY-MM-DD)
        repository: Filter by repository slug
        staff_id: Filter by staff bank_id

    Returns:
        List of category statistics
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(Commit).filter(
                Commit.file_types != None,
                Commit.file_types != ''
            )

            # Apply filters (same as above)
            if start_date:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Commit.commit_date >= start_datetime)

            if end_date:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Commit.commit_date <= end_datetime)

            if repository:
                query = query.join(Repository).filter(Repository.slug_name.ilike(f"%{repository}%"))

            if staff_id:
                mappings = session.query(AuthorStaffMapping).filter(
                    AuthorStaffMapping.bank_id_1 == staff_id
                ).all()
                author_names = [m.author_name for m in mappings]
                if author_names:
                    query = query.filter(Commit.author_name.in_(author_names))
                else:
                    return []

            commits = query.all()
            total_commits = len(commits)

            # Categorize file types
            # Simple categorization - can be enhanced
            code_extensions = ['java', 'js', 'jsx', 'ts', 'tsx', 'py', 'go', 'rb', 'php', 'cs', 'cpp', 'c', 'h']
            config_extensions = ['yml', 'yaml', 'xml', 'json', 'properties', 'ini', 'toml', 'env', 'conf']
            doc_extensions = ['md', 'txt', 'rst', 'adoc']

            categories = {
                'code': {'commits': 0, 'chars_added': 0, 'chars_deleted': 0},
                'config': {'commits': 0, 'chars_added': 0, 'chars_deleted': 0},
                'documentation': {'commits': 0, 'chars_added': 0, 'chars_deleted': 0},
                'other': {'commits': 0, 'chars_added': 0, 'chars_deleted': 0}
            }

            for commit in commits:
                types = set(commit.file_types.split(','))
                types = {t.strip().lower() for t in types if t.strip()}

                categorized = False
                if any(t in code_extensions for t in types):
                    categories['code']['commits'] += 1
                    categories['code']['chars_added'] += commit.chars_added or 0
                    categories['code']['chars_deleted'] += commit.chars_deleted or 0
                    categorized = True

                if any(t in config_extensions for t in types):
                    categories['config']['commits'] += 1
                    categories['config']['chars_added'] += commit.chars_added or 0
                    categories['config']['chars_deleted'] += commit.chars_deleted or 0
                    categorized = True

                if any(t in doc_extensions for t in types):
                    categories['documentation']['commits'] += 1
                    categories['documentation']['chars_added'] += commit.chars_added or 0
                    categories['documentation']['chars_deleted'] += commit.chars_deleted or 0
                    categorized = True

                if not categorized:
                    categories['other']['commits'] += 1
                    categories['other']['chars_added'] += commit.chars_added or 0
                    categories['other']['chars_deleted'] += commit.chars_deleted or 0

            # Convert to response format
            results = []
            for category, stats in categories.items():
                if stats['commits'] > 0:
                    results.append(CategoryStats(
                        category=category,
                        commits=stats['commits'],
                        percentage=round((stats['commits'] / total_commits * 100) if total_commits > 0 else 0, 1),
                        chars_added=stats['chars_added'],
                        chars_deleted=stats['chars_deleted']
                    ))

            return results

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/characters/metrics", response_model=CharacterMetrics)
async def get_character_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    repository: Optional[str] = Query(None),
    staff_id: Optional[str] = Query(None)
):
    """
    Get character-level metrics.

    Args:
        start_date: Filter by start date (YYYY-MM-DD)
        end_date: Filter by end date (YYYY-MM-DD)
        repository: Filter by repository slug
        staff_id: Filter by staff bank_id

    Returns:
        Character-level metrics
    """
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        try:
            query = session.query(Commit)

            # Apply filters
            if start_date:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Commit.commit_date >= start_datetime)

            if end_date:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Commit.commit_date <= end_datetime)

            if repository:
                query = query.join(Repository).filter(Repository.slug_name.ilike(f"%{repository}%"))

            if staff_id:
                mappings = session.query(AuthorStaffMapping).filter(
                    AuthorStaffMapping.bank_id_1 == staff_id
                ).all()
                author_names = [m.author_name for m in mappings]
                if author_names:
                    query = query.filter(Commit.author_name.in_(author_names))
                else:
                    return CharacterMetrics(
                        total_chars_added=0,
                        total_chars_deleted=0,
                        total_churn=0,
                        avg_chars_per_commit=0,
                        commits_with_data=0,
                        total_commits=0
                    )

            commits = query.all()
            total_commits = len(commits)

            total_chars_added = sum(c.chars_added or 0 for c in commits)
            total_chars_deleted = sum(c.chars_deleted or 0 for c in commits)
            commits_with_data = sum(1 for c in commits if (c.chars_added or 0) > 0)

            return CharacterMetrics(
                total_chars_added=total_chars_added,
                total_chars_deleted=total_chars_deleted,
                total_churn=total_chars_added + total_chars_deleted,
                avg_chars_per_commit=round(total_chars_added / total_commits if total_commits > 0 else 0, 2),
                commits_with_data=commits_with_data,
                total_commits=total_commits
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
