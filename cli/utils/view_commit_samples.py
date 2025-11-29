"""View sample commits with new fields."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.config import Config
from cli.models import get_engine, get_session, Commit, Repository

def view_samples():
    """Display sample commits with new fields."""
    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)
    session = get_session(engine)

    try:
        print("=" * 80)
        print("  SAMPLE COMMITS WITH NEW FIELDS")
        print("=" * 80)
        print()

        # Get commits with file types
        commits = session.query(Commit, Repository).join(
            Repository, Commit.repository_id == Repository.id
        ).filter(
            Commit.file_types != None,
            Commit.file_types != ''
        ).limit(5).all()

        if not commits:
            print("No commits with file types found.")
            return

        for commit, repo in commits:
            print("-" * 80)
            print(f"Repository: {repo.project_key}/{repo.slug_name}")
            print(f"Commit Hash: {commit.commit_hash[:12]}")
            print(f"Author: {commit.author_name} <{commit.author_email}>")
            print(f"Date: {commit.commit_date}")
            print(f"Message: {commit.message[:60]}...")
            print()
            print("Statistics:")
            print(f"  Lines Added:      {commit.lines_added:>8}")
            print(f"  Lines Deleted:    {commit.lines_deleted:>8}")
            print(f"  Files Changed:    {commit.files_changed:>8}")
            print(f"  Chars Added:      {commit.chars_added:>8}")
            print(f"  Chars Deleted:    {commit.chars_deleted:>8}")
            print(f"  File Types:       {commit.file_types}")
            print()

        print("=" * 80)
        print()

        # Show aggregated statistics by file type
        print("=" * 80)
        print("  FILE TYPE STATISTICS")
        print("=" * 80)
        print()

        from collections import Counter
        file_type_stats = Counter()
        chars_by_type = {}

        all_commits = session.query(Commit).filter(
            Commit.file_types != None,
            Commit.file_types != ''
        ).all()

        for commit in all_commits:
            types = commit.file_types.split(',')
            for file_type in types:
                file_type = file_type.strip()
                file_type_stats[file_type] += 1
                if file_type not in chars_by_type:
                    chars_by_type[file_type] = {'added': 0, 'deleted': 0}
                chars_by_type[file_type]['added'] += commit.chars_added
                chars_by_type[file_type]['deleted'] += commit.chars_deleted

        print(f"{'File Type':<15} {'Commits':>8} {'Chars Added':>15} {'Chars Deleted':>15} {'Total Churn':>15}")
        print("-" * 80)

        for file_type, count in sorted(file_type_stats.items(), key=lambda x: x[1], reverse=True):
            chars_added = chars_by_type[file_type]['added']
            chars_deleted = chars_by_type[file_type]['deleted']
            total_churn = chars_added + chars_deleted
            print(f"{file_type:<15} {count:>8} {chars_added:>15,} {chars_deleted:>15,} {total_churn:>15,}")

        print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    view_samples()
