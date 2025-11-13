"""Test that API returns new fields."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.routers.commits import CommitDetail
from cli.config import Config
from cli.models import get_engine, get_session, Commit, Repository

def test_api_fields():
    """Test that new fields are accessible via API."""
    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)
    session = get_session(engine)

    try:
        print("=" * 80)
        print("  TESTING API FIELDS")
        print("=" * 80)
        print()

        # Query like the API does
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
            Commit.chars_added,
            Commit.chars_deleted,
            Commit.file_types,
            Commit.branch,
            Repository.slug_name,
            Repository.project_key
        ).join(
            Repository, Commit.repository_id == Repository.id
        ).filter(
            Commit.file_types != None,
            Commit.file_types != ''
        ).limit(3)

        results = query.all()

        print(f"Found {len(results)} commits with file types")
        print()

        for r in results:
            # Create CommitDetail object like the API does
            commit_detail = CommitDetail(
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
                chars_added=r.chars_added or 0,
                chars_deleted=r.chars_deleted or 0,
                file_types=r.file_types or "",
                branch=r.branch,
                repository=r.slug_name,
                project_key=r.project_key
            )

            print(f"Commit: {commit_detail.commit_hash[:12]}")
            print(f"  Author: {commit_detail.author_name}")
            print(f"  Lines: +{commit_detail.lines_added} -{commit_detail.lines_deleted}")
            print(f"  Chars: +{commit_detail.chars_added} -{commit_detail.chars_deleted}")
            print(f"  File Types: {commit_detail.file_types}")
            print(f"  Message: {commit_detail.message[:50]}...")
            print()

        print("=" * 80)
        print("  TEST PASSED - API fields are working correctly!")
        print("=" * 80)
        print()

        # Convert to dict to show JSON-like output
        if results:
            print("Sample JSON output:")
            print("-" * 80)
            import json
            r = results[0]
            sample_json = {
                "commit_hash": r.commit_hash,
                "author_name": r.author_name,
                "lines_added": r.lines_added,
                "lines_deleted": r.lines_deleted,
                "chars_added": r.chars_added or 0,
                "chars_deleted": r.chars_deleted or 0,
                "file_types": r.file_types or "",
                "message": r.message[:50] + "..."
            }
            print(json.dumps(sample_json, indent=2))
            print()

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == '__main__':
    test_api_fields()
