"""Check database contents and create re-extraction CSV."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.config import Config
from cli.models import get_engine, get_session, Repository, Commit

def check_database():
    """Check database and show statistics."""
    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)
    session = get_session(engine)

    try:
        print("=" * 70)
        print("  DATABASE STATUS CHECK")
        print("=" * 70)
        print()

        # Get repositories
        repos = session.query(Repository).all()
        print(f"Total Repositories: {len(repos)}")
        print()

        if repos:
            print("Repositories in database:")
            print("-" * 70)
            for repo in repos:
                print(f"  Project: {repo.project_key}")
                print(f"  Slug: {repo.slug_name}")
                print(f"  URL: {repo.clone_url}")

                # Count commits for this repo
                commit_count = session.query(Commit).filter(
                    Commit.repository_id == repo.id
                ).count()
                print(f"  Commits: {commit_count}")

                # Check if new fields are populated
                populated_count = session.query(Commit).filter(
                    Commit.repository_id == repo.id,
                    Commit.chars_added > 0
                ).count()

                if populated_count > 0:
                    print(f"  New fields populated: {populated_count}/{commit_count} commits")
                else:
                    print(f"  New fields populated: 0/{commit_count} commits (needs re-extraction)")

                print()

        # Get commit statistics
        total_commits = session.query(Commit).count()
        commits_with_chars = session.query(Commit).filter(
            Commit.chars_added > 0
        ).count()
        commits_with_file_types = session.query(Commit).filter(
            Commit.file_types != None,
            Commit.file_types != ''
        ).count()

        print("=" * 70)
        print("  COMMIT STATISTICS")
        print("=" * 70)
        print(f"Total commits: {total_commits}")
        print(f"Commits with character data: {commits_with_chars} ({commits_with_chars/total_commits*100 if total_commits > 0 else 0:.1f}%)")
        print(f"Commits with file types: {commits_with_file_types} ({commits_with_file_types/total_commits*100 if total_commits > 0 else 0:.1f}%)")
        print()

        # Create CSV for re-extraction if needed
        if total_commits > 0 and commits_with_chars == 0:
            print("=" * 70)
            print("  CREATING RE-EXTRACTION CSV")
            print("=" * 70)

            csv_path = Path(__file__).parent.parent / "re_extract_repos.csv"
            with open(csv_path, 'w') as f:
                f.write("project_key,slug_name,clone_url\n")
                for repo in repos:
                    f.write(f"{repo.project_key},{repo.slug_name},{repo.clone_url}\n")

            print(f"Created: {csv_path}")
            print()
            print("To re-extract and populate new fields, run:")
            print(f"  python -m cli extract {csv_path}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    check_database()
