"""Quick script to show merge commit messages from a repository."""

import sys
from git import Repo
from pathlib import Path

def show_merge_commits(repo_path, count=10):
    """Show merge commit messages from repository."""
    print("=" * 80)
    print(f"Merge Commits in: {repo_path}")
    print("=" * 80)
    print()

    if not Path(repo_path).exists():
        print(f"ERROR: Repository path does not exist: {repo_path}")
        return

    try:
        repo = Repo(repo_path)

        # Try to get commits from master or main
        try:
            commits = list(repo.iter_commits('master', max_count=500))
        except:
            try:
                commits = list(repo.iter_commits('main', max_count=500))
            except:
                # Get from any branch
                for ref in repo.references:
                    if 'heads' in ref.path:
                        branch_name = ref.name.split('/')[-1]
                        commits = list(repo.iter_commits(branch_name, max_count=500))
                        break

        # Find merge commits
        merge_commits = [c for c in commits if len(c.parents) > 1]

        print(f"Total commits: {len(commits)}")
        print(f"Merge commits: {len(merge_commits)}")
        print()

        if not merge_commits:
            print("No merge commits found!")
            print("\nPossible reasons:")
            print("  - Repository uses squash-merge (no merge commits)")
            print("  - Repository uses rebase workflow")
            print("  - Very few commits in repository")
            repo.close()
            return

        print(f"Showing first {min(count, len(merge_commits))} merge commits:")
        print("=" * 80)

        for i, commit in enumerate(merge_commits[:count], 1):
            print(f"\n--- Merge Commit #{i} ---")
            print(f"Hash: {commit.hexsha[:8]}")
            print(f"Author: {commit.author.name} <{commit.author.email}>")
            print(f"Date: {commit.committed_datetime}")
            print(f"Parents: {len(commit.parents)}")
            print(f"\nFull Commit Message:")
            print("-" * 40)
            print(commit.message)
            print("-" * 40)

        repo.close()

        print("\n" + "=" * 80)
        print("Done!")
        print("\nPlease share these commit messages to get the right pattern.")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_merge_commits.py <repo_path> [count]")
        print("\nExample:")
        print("  python show_merge_commits.py ./repositories/PROJ_my-repo")
        print("  python show_merge_commits.py ./repositories/PROJ_my-repo 20")
        sys.exit(1)

    repo_path = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    show_merge_commits(repo_path, count)
