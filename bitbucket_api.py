"""Bitbucket REST API v1.0 client for extracting PR and approval data.

Supports Bitbucket Server/Data Center REST API v1.0.
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional
import time


class BitbucketAPIClient:
    """Client for Bitbucket Server/Data Center REST API v1.0."""

    def __init__(self, base_url: str, username: str, password: str):
        """Initialize Bitbucket API client.

        Args:
            base_url: Bitbucket server URL (e.g., https://bitbucket.sgp.dbs.com:8443)
            username: Bitbucket username
            password: Bitbucket password or app password
        """
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        # Set headers for API v1.0
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, retry_count: int = 3) -> Dict:
        """Make HTTP request to Bitbucket API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            retry_count: Number of retries on failure

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: On API error
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(retry_count):
            try:
                response = self.session.request(method, url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Rate limit
                    wait_time = int(response.headers.get('Retry-After', 60))
                    print(f"  Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 401:
                    raise Exception(f"Authentication failed: {e}")
                elif response.status_code == 404:
                    raise Exception(f"Resource not found: {e}")
                else:
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise
            except requests.exceptions.Timeout:
                if attempt < retry_count - 1:
                    print(f"  Request timeout, retrying ({attempt + 1}/{retry_count})...")
                    time.sleep(2)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
                raise

        raise Exception("Max retries exceeded")

    def _paginate(self, endpoint: str, params: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Paginate through API results.

        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Items per page

        Returns:
            List of all items from all pages
        """
        if params is None:
            params = {}

        params['limit'] = limit
        params['start'] = 0

        all_items = []

        while True:
            response = self._make_request('GET', endpoint, params)

            # API v1.0 uses 'values' for results
            items = response.get('values', [])
            all_items.extend(items)

            # Check if there are more pages
            is_last_page = response.get('isLastPage', True)
            if is_last_page:
                break

            # Get next page start index
            params['start'] = response.get('nextPageStart', 0)
            if params['start'] == 0:
                break  # Safety check

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        return all_items

    def extract_project_and_repo(self, clone_url: str) -> tuple:
        """Extract project key and repository slug from clone URL.

        Args:
            clone_url: Repository clone URL

        Returns:
            Tuple of (project_key, repo_slug)

        Example:
            https://bitbucket.com:8443/dcifgit/scm/clicon-core/user-sync-job.git
            Returns: ('CLICON-CORE', 'user-sync-job')
        """
        # Remove .git suffix
        url = clone_url.replace('.git', '')

        # Extract from /scm/PROJECT/REPO pattern
        if '/scm/' in url:
            parts = url.split('/scm/')[-1].split('/')
            if len(parts) >= 2:
                project_key = parts[0].upper()
                repo_slug = parts[1]
                return project_key, repo_slug

        # Fallback: try to extract from last parts of URL
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            return parts[-2].upper(), parts[-1]

        raise ValueError(f"Could not extract project and repo from URL: {clone_url}")

    def get_pull_requests(self, project_key: str, repo_slug: str, state: str = 'MERGED') -> List[Dict]:
        """Get pull requests for a repository.

        Args:
            project_key: Bitbucket project key
            repo_slug: Repository slug name
            state: PR state (ALL, OPEN, MERGED, DECLINED)

        Returns:
            List of pull request dictionaries

        API Documentation:
            GET /rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests
        """
        endpoint = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests"
        params = {'state': state}

        print(f"  Fetching {state} pull requests from API...")
        prs = self._paginate(endpoint, params)
        print(f"  Found {len(prs)} {state} pull requests")

        return prs

    def get_pr_activities(self, project_key: str, repo_slug: str, pr_id: int) -> List[Dict]:
        """Get activities (including approvals) for a pull request.

        Args:
            project_key: Bitbucket project key
            repo_slug: Repository slug name
            pr_id: Pull request ID

        Returns:
            List of activity dictionaries

        API Documentation:
            GET /rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/activities
        """
        endpoint = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/activities"

        activities = self._paginate(endpoint)
        return activities

    def get_pr_commits(self, project_key: str, repo_slug: str, pr_id: int) -> List[Dict]:
        """Get commits in a pull request.

        Args:
            project_key: Bitbucket project key
            repo_slug: Repository slug name
            pr_id: Pull request ID

        Returns:
            List of commit dictionaries

        API Documentation:
            GET /rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/commits
        """
        endpoint = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/commits"

        commits = self._paginate(endpoint)
        return commits

    def extract_pr_data(self, pr: Dict) -> Dict:
        """Extract and normalize PR data from API response.

        Args:
            pr: Pull request dict from API

        Returns:
            Normalized PR data dict
        """
        return {
            'pr_number': pr.get('id'),
            'title': pr.get('title', ''),
            'description': pr.get('description', ''),
            'author_name': pr.get('author', {}).get('user', {}).get('displayName', ''),
            'author_email': pr.get('author', {}).get('user', {}).get('emailAddress', ''),
            'created_date': self._parse_timestamp(pr.get('createdDate')),
            'updated_date': self._parse_timestamp(pr.get('updatedDate')),
            'merged_date': self._parse_timestamp(pr.get('closedDate')) if pr.get('state') == 'MERGED' else None,
            'state': pr.get('state', '').lower(),
            'source_branch': pr.get('fromRef', {}).get('displayId', ''),
            'target_branch': pr.get('toRef', {}).get('displayId', ''),
            'lines_added': 0,  # Need to calculate from diff
            'lines_deleted': 0,  # Need to calculate from diff
            'commits_count': 0  # Will be updated with actual commit count
        }

    def extract_approvals(self, activities: List[Dict]) -> List[Dict]:
        """Extract approval data from PR activities.

        Args:
            activities: List of activity dicts from API

        Returns:
            List of approval dicts
        """
        approvals = []

        for activity in activities:
            action = activity.get('action', '')

            # API v1.0 uses 'APPROVED' action for approvals
            if action == 'APPROVED':
                user = activity.get('user', {})
                approval_date = self._parse_timestamp(activity.get('createdDate'))

                approvals.append({
                    'approver_name': user.get('displayName', ''),
                    'approver_email': user.get('emailAddress', ''),
                    'approval_date': approval_date,
                    'approval_type': 'approved'
                })

            # Also check for REVIEWED action
            elif action == 'REVIEWED':
                user = activity.get('user', {})
                approval_date = self._parse_timestamp(activity.get('createdDate'))

                approvals.append({
                    'approver_name': user.get('displayName', ''),
                    'approver_email': user.get('emailAddress', ''),
                    'approval_date': approval_date,
                    'approval_type': 'reviewed'
                })

        return approvals

    @staticmethod
    def _parse_timestamp(timestamp_ms: Optional[int]) -> Optional[object]:
        """Parse Bitbucket timestamp (milliseconds) to datetime.

        Args:
            timestamp_ms: Timestamp in milliseconds

        Returns:
            datetime object or None
        """
        if timestamp_ms is None:
            return None

        from datetime import datetime
        return datetime.fromtimestamp(timestamp_ms / 1000.0)

    def get_all_prs_with_approvals(self, project_key: str, repo_slug: str) -> tuple:
        """Get all merged PRs and their approvals.

        Args:
            project_key: Bitbucket project key
            repo_slug: Repository slug name

        Returns:
            Tuple of (pr_list, approvals_dict) where approvals_dict maps PR ID to approval list
        """
        # Get all merged PRs
        prs = self.get_pull_requests(project_key, repo_slug, state='MERGED')

        all_pr_data = []
        all_approvals = {}

        print(f"  Extracting details for {len(prs)} PRs...")
        for i, pr in enumerate(prs, 1):
            if i % 10 == 0:
                print(f"    Processed {i}/{len(prs)} PRs...")

            pr_id = pr.get('id')
            pr_data = self.extract_pr_data(pr)

            # Get activities (including approvals)
            try:
                activities = self.get_pr_activities(project_key, repo_slug, pr_id)
                approvals = self.extract_approvals(activities)
                all_approvals[pr_id] = approvals
            except Exception as e:
                print(f"    Warning: Could not get activities for PR #{pr_id}: {e}")
                all_approvals[pr_id] = []

            # Get commit count
            try:
                commits = self.get_pr_commits(project_key, repo_slug, pr_id)
                pr_data['commits_count'] = len(commits)
            except Exception as e:
                print(f"    Warning: Could not get commits for PR #{pr_id}: {e}")
                pr_data['commits_count'] = 0

            all_pr_data.append(pr_data)

            # Small delay to avoid rate limiting
            time.sleep(0.05)

        print(f"  Extracted {len(all_pr_data)} PRs with approvals")
        return all_pr_data, all_approvals
