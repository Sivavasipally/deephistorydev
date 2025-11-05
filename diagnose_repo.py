"""Diagnostic script to analyze repository commit patterns."""

import sys
import re
from git import Repo
from pathlib import Path

def analyze_repository(repo_path):
    """Analyze repository to find merge commits and PR patterns."""
    print("=" * 80)
    print(f"Analyzing Repository: {repo_path}")
    print("=" * 80)
    print()

    repo = Repo(repo_path)

    # Try to find the default branch
    commits = []
    branch = 'unknown'

    try:
        # Get all branches
        branches = [ref.name for ref in repo.references if 'heads' in ref.path]
        print(f"Available branches: {branches}")
        print()

        if not branches:
            print("ERROR: No branches found in repository")
            repo.close()
            return

        # Try common branch names
        for branch_name in ['master', 'main', 'develop']:
            try:
                commits = list(repo.iter_commits(branch_name, max_count=100))
                branch = branch_name
                break
            except:
                continue

        # If still no commits, try the first available branch
        if not commits:
            for ref in repo.references:
                if 'heads' in ref.path:
                    branch = ref.name.split('/')[-1]
                    try:
                        commits = list(repo.iter_commits(branch, max_count=100))
                        break
                    except:
                        continue
    except Exception as e:
        print(f"ERROR: Could not access repository: {e}")
        repo.close()
        return

    print(f"Branch analyzed: {branch}")
    print(f"Total commits analyzed: {len(commits)}")
    print()

    # Find merge commits
    merge_commits = [c for c in commits if len(c.parents) > 1]
    print(f"Merge commits found: {len(merge_commits)}")
    print()

    if merge_commits:
        print("=" * 80)
        print("MERGE COMMIT ANALYSIS")
        print("=" * 80)
        print()

        # PR patterns to test
        pr_patterns = [
            (r'Merge pull request #(\d+)', 'GitHub'),
            (r'Merged in .+ \(pull request #(\d+)\)', 'Bitbucket standard'),
            (r'Pull request #(\d+):', 'Bitbucket alternate'),
            (r'(?:PR|pr)\s*#(\d+)', 'Generic PR'),
            (r'Merge branch .+ into', 'GitLab style'),
        ]

        for i, commit in enumerate(merge_commits[:10], 1):  # First 10 merge commits
            print(f"\n--- Merge Commit #{i} ---")
            print(f"Hash: {commit.hexsha[:8]}")
            print(f"Author: {commit.author.name} <{commit.author.email}>")
            print(f"Date: {commit.committed_datetime}")
            print(f"Parents: {len(commit.parents)}")
            print(f"\nCommit Message:")
            print("-" * 40)
            print(commit.message)
            print("-" * 40)

            # Test all patterns
            print("\nPattern Matching:")
            matched = False
            for pattern, name in pr_patterns:
                match = re.search(pattern, commit.message, re.IGNORECASE)
                if match:
                    print(f"  [MATCH] {name}: {match.group()}")
                    matched = True

            if not matched:
                print("  [NO MATCH] No PR pattern detected")

            print()

    # Check for approval patterns in all commits
    print("=" * 80)
    print("APPROVAL PATTERN ANALYSIS")
    print("=" * 80)
    print()

    approval_patterns = [
        (r'Reviewed-by:\s*([^<]+?)\s*<([^>]+)>', 'Standard Reviewed-by'),
        (r'Approved-by:\s*([^<]+?)\s*<([^>]+)>', 'Standard Approved-by'),
        (r'Acked-by:\s*([^<]+?)\s*<([^>]+)>', 'Standard Acked-by'),
        (r'Tested-by:\s*([^<]+?)\s*<([^>]+)>', 'Standard Tested-by'),
        (r'[Rr]eviewed by:\s*@?([^\s<]+)', 'Platform reviewed by'),
        (r'[Aa]pproved by:\s*@?([^\s<]+)', 'Platform approved by'),
    ]

    commits_with_approvals = []
    for commit in commits:
        for pattern, name in approval_patterns:
            if re.search(pattern, commit.message, re.IGNORECASE):
                commits_with_approvals.append((commit, name))
                break

    print(f"Commits with approval patterns: {len(commits_with_approvals)}")

    if commits_with_approvals:
        print("\nFirst 5 commits with approvals:")
        for i, (commit, pattern_name) in enumerate(commits_with_approvals[:5], 1):
            print(f"\n--- Approval Commit #{i} ---")
            print(f"Hash: {commit.hexsha[:8]}")
            print(f"Pattern: {pattern_name}")
            print(f"Message preview:")
            print(commit.message[:200])
            print()

    repo.close()
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_repo.py <repo_path>")
        print("\nExample:")
        print("  python diagnose_repo.py ./repositories/PROJ_my-repo")
        sys.exit(1)

    repo_path = sys.argv[1]

    if not Path(repo_path).exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)

    analyze_repository(repo_path)
