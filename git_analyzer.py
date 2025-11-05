"""Git repository analysis and data extraction using GitPython."""

import os
import re
import shutil
import gc
from pathlib import Path
from git import Repo, GitCommandError
from datetime import datetime
from urllib.parse import urlparse, urlunparse, quote
from models import Repository, Commit, PullRequest, PRApproval


class GitAnalyzer:
    """Analyze Git repositories and extract commit and PR data using GitPython."""

    def __init__(self, clone_dir, git_username=None, git_password=None, bitbucket_config=None):
        """Initialize GitAnalyzer.

        Args:
            clone_dir: Directory to clone repositories into
            git_username: Git username for authentication
            git_password: Git password or token for authentication
            bitbucket_config: Not used - kept for backward compatibility
        """
        self.clone_dir = Path(clone_dir)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self.git_username = git_username
        self.git_password = git_password

    def _add_credentials_to_url(self, url):
        """Add credentials to clone URL if provided.

        Properly encodes username and password to handle special characters.

        Args:
            url: Clone URL

        Returns:
            URL with encoded credentials
        """
        if not self.git_username or not self.git_password:
            return url

        parsed = urlparse(url)

        # URL-encode username and password to handle special characters
        # safe='' means encode everything that needs encoding
        encoded_username = quote(self.git_username, safe='')
        encoded_password = quote(self.git_password, safe='')

        # Add encoded credentials to netloc
        netloc_with_auth = f"{encoded_username}:{encoded_password}@{parsed.netloc}"

        # Reconstruct URL with credentials
        authenticated_url = urlunparse((
            parsed.scheme,
            netloc_with_auth,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return authenticated_url

    def clone_repository(self, clone_url, repo_name):
        """Clone a repository.

        Args:
            clone_url: URL to clone from
            repo_name: Name for the local repository directory

        Returns:
            Path to the cloned repository
        """
        repo_path = self.clone_dir / repo_name

        # Remove existing directory if it exists
        if repo_path.exists():
            self.cleanup_repository(repo_path)

        # Add credentials to URL
        auth_url = self._add_credentials_to_url(clone_url)

        # Clone the repository
        try:
            Repo.clone_from(auth_url, repo_path, branch='master')
        except GitCommandError:
            # Try with 'main' branch if 'master' doesn't exist
            try:
                Repo.clone_from(auth_url, repo_path, branch='main')
            except GitCommandError:
                # Clone without specifying branch
                Repo.clone_from(auth_url, repo_path)

        return repo_path

    def get_commit_stats(self, commit, repo):
        """Get statistics for a commit.

        Args:
            commit: Git commit object
            repo: Git repository object

        Returns:
            Dictionary with lines added, deleted, and files changed
        """
        try:
            stats = commit.stats.total
            return {
                'lines_added': stats.get('insertions', 0),
                'lines_deleted': stats.get('deletions', 0),
                'files_changed': stats.get('files', 0)
            }
        except Exception:
            return {
                'lines_added': 0,
                'lines_deleted': 0,
                'files_changed': 0
            }

    def extract_commits(self, repo_path, branch='master'):
        """Extract all commits from a repository branch.

        Args:
            repo_path: Path to the cloned repository
            branch: Branch to extract commits from

        Returns:
            List of commit dictionaries
        """
        repo = Repo(repo_path)
        commits_data = []

        try:
            # Try to get the specified branch, fall back to main or default
            try:
                commits = list(repo.iter_commits(branch))
            except GitCommandError:
                try:
                    commits = list(repo.iter_commits('main'))
                    branch = 'main'
                except GitCommandError:
                    # Use default branch
                    commits = list(repo.iter_commits())
                    branch = repo.active_branch.name

            for commit in commits:
                stats = self.get_commit_stats(commit, repo)

                commit_data = {
                    'commit_hash': commit.hexsha,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'committer_name': commit.committer.name,
                    'committer_email': commit.committer.email,
                    'commit_date': datetime.fromtimestamp(commit.committed_date),
                    'message': commit.message.strip(),
                    'lines_added': stats['lines_added'],
                    'lines_deleted': stats['lines_deleted'],
                    'files_changed': stats['files_changed'],
                    'branch': branch
                }
                commits_data.append(commit_data)
        finally:
            # Close the repo to release file handles
            repo.close()

        return commits_data

    def extract_pull_requests(self, repo_path, clone_url=None):
        """Extract pull request information from Git history using GitPython.

        Supports multiple PR patterns:
        - GitHub: "Merge pull request #123"
        - Bitbucket: "Merged in feature-branch (pull request #123)"
        - GitLab: "Merge branch 'feature' into 'main'"

        Args:
            repo_path: Path to the cloned repository
            clone_url: Original clone URL (for platform detection)

        Returns:
            List of pull request dictionaries
        """
        repo = Repo(repo_path)
        prs_data = []

        # Multiple PR patterns for different platforms
        pr_patterns = [
            # GitHub pattern: Merge pull request #123 from user/branch
            (r'Merge pull request #(\d+)', 'github'),
            # Bitbucket pattern: Merged in feature-branch (pull request #123)
            (r'Merged in .+ \(pull request #(\d+)\)', 'bitbucket'),
            # Bitbucket alternate: Pull request #123: Title
            (r'Pull request #(\d+):', 'bitbucket'),
            # Generic pattern: PR #123 or pr#123 (case insensitive)
            (r'(?:PR|pr|Pr|pR)\s*[:#]?\s*(\d+)', 'generic'),
            # Bitbucket squash-merge pattern: "branch-name: commit message (pull request #123)"
            (r'\(pull request #(\d+)\)', 'bitbucket-squash'),
            # Branch-based patterns (extract ticket/PR number from branch name)
            # Pattern: feature/PROJ-12345 or feature/CG-25002
            (r'into\s+(?:feature|bugfix|hotfix)[/\-]([A-Z]+-\d+)', 'branch-ticket'),
            (r'from\s+(?:feature|bugfix|hotfix)[/\-]([A-Z]+-\d+)', 'branch-ticket'),
            # Pattern: Merge branch 'feature-123' or similar
            (r'Merge branch.*?(?:feature|bugfix|hotfix)[/\-]?(\d{3,})', 'branch-number')
        ]

        try:
            # Try master, then main, then default
            try:
                commits = list(repo.iter_commits('master'))
                default_branch = 'master'
            except GitCommandError:
                try:
                    commits = list(repo.iter_commits('main'))
                    default_branch = 'main'
                except GitCommandError:
                    try:
                        # Try to get any available branch
                        for ref in repo.references:
                            if 'heads' in ref.path:
                                branch_name = ref.name.split('/')[-1]
                                commits = list(repo.iter_commits(branch_name))
                                default_branch = branch_name
                                break
                    except:
                        commits = []
                        default_branch = 'unknown'

            if not commits:
                print(f"Warning: No commits found in repository {repo_path}")
                return []

            processed_prs = set()  # Track processed PR numbers to avoid duplicates
            merge_commit_count = 0
            pr_match_count = 0
            unmatched_merge_commits = []  # Track merge commits that didn't match

            for commit in commits:
                commit_message = commit.message.strip()
                is_merge = len(commit.parents) > 1

                if is_merge:
                    merge_commit_count += 1

                # Check all commits (both merge and non-merge) for PR patterns
                # This handles both traditional merges and squash-merges
                matched = False
                for pattern, platform in pr_patterns:
                    match = re.search(pattern, commit_message, re.IGNORECASE)
                    if match:
                        pr_identifier = match.group(1)

                        # Convert to consistent format
                        # For numeric PRs, convert to int
                        # For alphanumeric (Jira tickets), keep as string
                        if pr_identifier.isdigit():
                            pr_number = int(pr_identifier)
                        else:
                            # For Jira tickets like "CG-25002", use the numeric part as PR number
                            # and store full ticket in title
                            numeric_part = re.search(r'(\d+)$', pr_identifier)
                            if numeric_part:
                                pr_number = int(numeric_part.group(1))
                            else:
                                # Skip if we can't extract a number
                                continue

                        # Skip if already processed
                        if pr_number in processed_prs:
                            continue

                        processed_prs.add(pr_number)
                        pr_match_count += 1
                        matched = True
                        stats = self.get_commit_stats(commit, repo)

                        # Extract PR title
                        title_lines = commit_message.split('\n')
                        title = title_lines[0] if title_lines else 'No title'

                        # If we extracted from a Jira ticket, prepend it to the title
                        if not pr_identifier.isdigit():
                            title = f"[{pr_identifier}] {title}"

                        # Try to extract branch names from commit message
                        source_branch, target_branch = self._extract_branch_names(
                            commit_message, default_branch
                        )

                        # Count commits in PR (only for merge commits)
                        commit_count = self._count_pr_commits(repo, commit) if is_merge else 1

                        pr_data = {
                            'pr_number': pr_number,
                            'title': title,
                            'description': commit_message,
                            'author_name': commit.author.name,
                            'author_email': commit.author.email,
                            'created_date': datetime.fromtimestamp(commit.authored_date),
                            'merged_date': datetime.fromtimestamp(commit.committed_date),
                            'state': 'merged',
                            'source_branch': source_branch,
                            'target_branch': target_branch,
                            'lines_added': stats['lines_added'],
                            'lines_deleted': stats['lines_deleted'],
                            'commits_count': commit_count
                        }
                        prs_data.append(pr_data)
                        break  # Found a match, no need to try other patterns

                # Track unmatched merge commits for debugging
                if is_merge and not matched:
                    # Store first 100 chars of message for debugging
                    unmatched_merge_commits.append(commit_message[:100])

            # Debug information
            print(f"  Total commits: {len(commits)}")
            print(f"  Merge commits: {merge_commit_count}")
            print(f"  PRs detected: {pr_match_count}")

            # If we have merge commits but no PRs detected, show sample messages
            if merge_commit_count > 0 and pr_match_count == 0:
                print("\n  [WARNING] Merge commits found but no PR patterns matched!")
                print("  Sample merge commit messages (first 100 chars):")
                for i, msg in enumerate(unmatched_merge_commits[:3], 1):
                    print(f"    {i}. {msg}")
                print("\n  This may indicate:")
                print("    - PR numbers not included in commit messages")
                print("    - Different commit message format")
                print("    - Manual merges without PR references")
                print("  Run with --no-cleanup and use diagnose_repo.py for details")

        finally:
            # Close the repo to release file handles
            repo.close()

        return prs_data

    def _extract_branch_names(self, commit_message, default_target='master'):
        """Extract source and target branch names from commit message.

        Args:
            commit_message: Full commit message
            default_target: Default target branch name

        Returns:
            Tuple of (source_branch, target_branch)
        """
        # Pattern: "Merged in branch-name (pull request #123)"
        bitbucket_pattern = r'Merged in ([^\s\(]+)'
        match = re.search(bitbucket_pattern, commit_message)
        if match:
            return match.group(1), default_target

        # Pattern: "Merge pull request #123 from user/branch-name"
        github_pattern = r'from [^/]+/([^\s]+)'
        match = re.search(github_pattern, commit_message)
        if match:
            return match.group(1), default_target

        # Pattern: "Merge branch 'source' into 'target'"
        gitlab_pattern = r"Merge branch '([^']+)' into '([^']+)'"
        match = re.search(gitlab_pattern, commit_message)
        if match:
            return match.group(1), match.group(2)

        return 'unknown', default_target

    def _count_pr_commits(self, repo, merge_commit):
        """Count commits in a PR by analyzing the merge commit.

        Args:
            repo: Git repository object
            merge_commit: The merge commit object

        Returns:
            Number of commits in the PR
        """
        try:
            # If it's a merge commit, count commits between first parent and second parent
            if len(merge_commit.parents) >= 2:
                # Get commits between main branch (first parent) and feature branch (second parent)
                first_parent = merge_commit.parents[0]
                second_parent = merge_commit.parents[1]

                # Count commits in second parent that aren't in first parent
                pr_commits = list(repo.iter_commits(f'{first_parent.hexsha}..{second_parent.hexsha}'))
                return len(pr_commits)
        except Exception:
            pass

        return 1  # Default to 1 if we can't determine

    def extract_pr_approvals(self, repo_path, pr_data, clone_url=None):
        """Extract PR approval information from Git commit messages using GitPython.

        Looks for approval patterns in commit messages:
        - "Reviewed-by: Name <email>"
        - "Approved-by: Name <email>"
        - "Acked-by: Name <email>"
        - Bitbucket: "approved by @username"
        - GitHub: "Reviewed by @username"

        Args:
            repo_path: Path to the cloned repository
            pr_data: Pull request data dictionary
            clone_url: Original clone URL (optional)

        Returns:
            List of approval dictionaries
        """
        approvals = []
        pr_description = pr_data.get('description', '')

        # Multiple approval patterns for different platforms
        approval_patterns = [
            # Standard Git trailer format (name and email)
            (r'Reviewed-by:\s*([^<]+?)\s*<([^>]+)>', 'reviewed-by', True),
            (r'Approved-by:\s*([^<]+?)\s*<([^>]+)>', 'approved-by', True),
            (r'Acked-by:\s*([^<]+?)\s*<([^>]+)>', 'acked-by', True),
            (r'Tested-by:\s*([^<]+?)\s*<([^>]+)>', 'tested-by', True),
            (r'Co-authored-by:\s*([^<]+?)\s*<([^>]+)>', 'co-authored', True),
            # Bitbucket style with email
            (r'[Aa]pproved by\s+([^<]+?)\s*<([^>]+)>', 'bitbucket-approval', True),
            # Username-only patterns (name only)
            (r'Reviewed by:\s*@?([^\s,<\n]+)', 'github-review', False),
            (r'[Aa]pproved by:\s*@?([^\s,<\n]+)', 'bitbucket-approval', False),
            (r'Reviewed:\s*@?([^\s,<\n]+)', 'generic-review', False),
            (r'Approved:\s*@?([^\s,<\n]+)', 'generic-approval', False),
        ]

        # Extract approvals from PR description/commit message
        for pattern, approval_type, has_email in approval_patterns:
            matches = re.findall(pattern, pr_description, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                if has_email and isinstance(match, tuple) and len(match) >= 2:
                    # Pattern with name and email
                    approver_name = match[0].strip()
                    approver_email = match[1].strip()
                else:
                    # Single match (username)
                    if isinstance(match, tuple):
                        approver_name = match[0].strip()
                    else:
                        approver_name = match.strip()
                    approver_email = f"{approver_name}@git"

                # Clean up approver name (remove extra whitespace)
                approver_name = ' '.join(approver_name.split())

                # Skip empty names
                if not approver_name:
                    continue

                # Avoid duplicates (check by email)
                if not any(a['approver_email'] == approver_email for a in approvals):
                    approvals.append({
                        'approver_name': approver_name,
                        'approver_email': approver_email,
                        'approval_date': pr_data.get('merged_date'),
                        'approval_type': approval_type
                    })

        # Also check for approvals in PR commits (if we can find them)
        try:
            repo = Repo(repo_path)
            try:
                # Try to find approvals in commit messages of the PR
                # Look for commits near the merge commit time
                merge_date = pr_data.get('merged_date')
                if merge_date:
                    # Get commits around the merge time
                    all_commits = list(repo.iter_commits(max_count=200))
                    for commit in all_commits:
                        commit_date = datetime.fromtimestamp(commit.committed_date)
                        # Look at commits within a week of merge
                        if abs((commit_date - merge_date).days) <= 7:
                            commit_msg = commit.message.strip()
                            # Check for approval patterns in this commit
                            for pattern, approval_type, has_email in approval_patterns:
                                matches = re.findall(pattern, commit_msg, re.MULTILINE | re.IGNORECASE)
                                for match in matches:
                                    if has_email and isinstance(match, tuple) and len(match) >= 2:
                                        approver_name = match[0].strip()
                                        approver_email = match[1].strip()
                                    else:
                                        if isinstance(match, tuple):
                                            approver_name = match[0].strip()
                                        else:
                                            approver_name = match.strip()
                                        approver_email = f"{approver_name}@git"

                                    # Clean up approver name
                                    approver_name = ' '.join(approver_name.split())

                                    # Skip empty names
                                    if not approver_name:
                                        continue

                                    # Avoid duplicates
                                    if not any(a['approver_email'] == approver_email for a in approvals):
                                        approvals.append({
                                            'approver_name': approver_name,
                                            'approver_email': approver_email,
                                            'approval_date': commit_date,
                                            'approval_type': approval_type
                                        })
            finally:
                repo.close()
        except Exception as e:
            pass  # If we can't access repo, just use what we have

        return approvals

    def cleanup_repository(self, repo_path):
        """Remove cloned repository to save space.

        Args:
            repo_path: Path to the repository to remove
        """
        if Path(repo_path).exists():
            # Force garbage collection to release file handles
            gc.collect()

            # Windows-specific: handle permission errors with retry
            def handle_remove_readonly(func, path, exc):
                """Error handler for Windows readonly files."""
                import stat
                import time
                if exc[0] == PermissionError:
                    # Remove readonly attribute and retry
                    os.chmod(path, stat.S_IWRITE)
                    time.sleep(0.1)  # Brief delay
                    try:
                        func(path)
                    except:
                        pass  # If still fails, ignore

            shutil.rmtree(repo_path, onerror=handle_remove_readonly)
