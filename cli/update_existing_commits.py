"""Update existing commits with new fields (file types and character counts)."""

import sys
from pathlib import Path
import click
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.config import Config
from cli.models import get_engine, get_session, Repository, Commit
from cli.git_analyzer import GitAnalyzer

def update_commits():
    """Update existing commits with character counts and file types."""
    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)
    session = get_session(engine)

    credentials = config.get_git_credentials()
    bitbucket_config = config.get_bitbucket_config()
    clone_dir = config.get_clone_dir()

    analyzer = GitAnalyzer(
        clone_dir,
        credentials['username'],
        credentials['password'],
        bitbucket_config
    )

    print("=" * 70)
    print("  UPDATE EXISTING COMMITS WITH NEW FIELDS")
    print("=" * 70)
    print()

    try:
        # Get all repositories
        repos = session.query(Repository).all()

        if not repos:
            print("No repositories found in database.")
            return

        print(f"Found {len(repos)} repositories to process")
        print()

        total_updated = 0
        total_commits = 0

        for repo in repos:
            print("=" * 70)
            print(f"Processing: {repo.project_key}/{repo.slug_name}")
            print("=" * 70)

            # Clone repository
            try:
                print("Cloning repository...")
                repo_name = f"{repo.project_key}_{repo.slug_name}"
                repo_path = analyzer.clone_repository(
                    repo.clone_url,
                    repo_name
                )
                print(f"  Cloned to: {repo_path}")
            except Exception as e:
                print(f"  [ERROR] Failed to clone: {e}")
                continue

            # Get commits from database for this repo
            db_commits = session.query(Commit).filter(
                Commit.repository_id == repo.id
            ).all()

            total_commits += len(db_commits)
            print(f"Found {len(db_commits)} commits in database")

            # Extract fresh commit data with new fields
            try:
                print("Extracting commit details...")
                fresh_commits_data = analyzer.extract_commits(repo_path)

                # Create a mapping of commit_hash -> commit_data
                fresh_commits_map = {
                    c['commit_hash']: c for c in fresh_commits_data
                }

                # Update database commits with new fields
                updated_count = 0
                print("Updating commits with new fields...")

                for db_commit in tqdm(db_commits, desc="Updating", unit="commit"):
                    fresh_data = fresh_commits_map.get(db_commit.commit_hash)

                    if fresh_data:
                        # Update new fields
                        db_commit.chars_added = fresh_data.get('chars_added', 0)
                        db_commit.chars_deleted = fresh_data.get('chars_deleted', 0)
                        db_commit.file_types = fresh_data.get('file_types', '')
                        updated_count += 1

                session.commit()
                total_updated += updated_count
                print(f"  [OK] Updated {updated_count} commits")

            except Exception as e:
                print(f"  [ERROR] Failed to extract commits: {e}")
                session.rollback()
                import traceback
                traceback.print_exc()

            # Cleanup cloned repo
            try:
                import shutil
                shutil.rmtree(repo_path)
                print("  Cleaned up cloned repository")
            except Exception as e:
                print(f"  [WARNING] Failed to cleanup: {e}")

            print()

        print("=" * 70)
        print("  UPDATE COMPLETE")
        print("=" * 70)
        print(f"Total commits processed: {total_commits}")
        print(f"Total commits updated: {total_updated}")
        print()

        # Show updated statistics
        commits_with_chars = session.query(Commit).filter(
            Commit.chars_added > 0
        ).count()
        commits_with_file_types = session.query(Commit).filter(
            Commit.file_types != None,
            Commit.file_types != ''
        ).count()

        print("New statistics:")
        print(f"  Commits with character data: {commits_with_chars}/{total_commits} ({commits_with_chars/total_commits*100 if total_commits > 0 else 0:.1f}%)")
        print(f"  Commits with file types: {commits_with_file_types}/{total_commits} ({commits_with_file_types/total_commits*100 if total_commits > 0 else 0:.1f}%)")
        print()

    except KeyboardInterrupt:
        print("\n[CANCELLED] Update cancelled by user")
        session.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Update failed: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == '__main__':
    update_commits()
