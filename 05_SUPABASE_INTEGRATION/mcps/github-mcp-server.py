"""
GitHub MCP Server
GitHub API integration for version control and code management
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from mcp_auth_handler import get_auth_handler
from mcp_cache import get_cache, cached_mcp_call
from mcp_logging import get_mcp_logger

class GitHubMCPServer:
    """MCP Server for GitHub operations"""

    def __init__(self):
        self.auth_handler = get_auth_handler()
        self.cache = get_cache()
        self.logger = get_mcp_logger()
        self.credentials = None
        self._initialize()

    def _initialize(self):
        """Initialize GitHub connection"""
        try:
            self.credentials = self.auth_handler.get_github_credentials()
            self.base_url = self.credentials['base_url']
            self.token = self.credentials['token']
            self.logger.log_auth_event('github', 'initialization', True)
        except Exception as e:
            self.logger.log_auth_event('github', 'initialization', False, str(e))
            raise

    def _make_request(self,
                      endpoint: str,
                      method: str = 'GET',
                      params: Dict = None,
                      data: Dict = None,
                      max_retries: int = 3) -> Dict[str, Any]:
        """Make GitHub API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=30)
                elif method == 'PATCH':
                    response = requests.patch(url, headers=headers, json=data, timeout=30)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, timeout=30)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response_time = (time.time() - start_time) * 1000

                self.logger.log_api_call(
                    service='github',
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    response_status=response.status_code,
                    response_time_ms=response_time
                )

                # Handle rate limiting
                if response.status_code == 403:
                    if 'X-RateLimit-Remaining' in response.headers:
                        if int(response.headers['X-RateLimit-Remaining']) == 0:
                            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                            wait_time = max(reset_time - time.time(), 0)
                            self.logger.log_error('github', 'rate_limit', f'Rate limited, retry after {wait_time}s')
                            time.sleep(min(wait_time, 300))  # Max 5 min wait
                            continue

                response.raise_for_status()

                # Some endpoints return 204 No Content
                if response.status_code == 204:
                    return {'success': True}

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5
                    self.logger.log_error('github', 'request_error', str(e), query=endpoint)
                    time.sleep(wait_time)
                else:
                    self.logger.log_error('github', 'request_failed', str(e), query=endpoint)
                    raise

        return {'error': 'Max retries exceeded'}

    @cached_mcp_call('github', ttl=600)
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository details
        """
        try:
            result = self._make_request(f'repos/{owner}/{repo}')

            return {
                'owner': owner,
                'name': repo,
                'full_name': result.get('full_name'),
                'description': result.get('description'),
                'url': result.get('html_url'),
                'created_at': result.get('created_at'),
                'updated_at': result.get('updated_at'),
                'language': result.get('language'),
                'stars': result.get('stargazers_count'),
                'forks': result.get('forks_count'),
                'open_issues': result.get('open_issues_count'),
                'default_branch': result.get('default_branch'),
                'private': result.get('private')
            }

        except Exception as e:
            self.logger.log_error('github', 'repo_error', str(e), query=f'{owner}/{repo}')
            return {'error': str(e), 'owner': owner, 'repo': repo}

    @cached_mcp_call('github', ttl=300)
    def list_repositories(self, user: str = None, org: str = None, limit: int = 30) -> Dict[str, Any]:
        """
        List repositories for user or organization

        Args:
            user: GitHub username
            org: Organization name
            limit: Maximum repositories to return

        Returns:
            Repository list
        """
        try:
            if org:
                endpoint = f'orgs/{org}/repos'
            elif user:
                endpoint = f'users/{user}/repos'
            else:
                endpoint = 'user/repos'  # Authenticated user

            params = {
                'per_page': min(limit, 100),
                'sort': 'updated',
                'direction': 'desc'
            }

            result = self._make_request(endpoint, params=params)

            return {
                'user': user,
                'org': org,
                'count': len(result),
                'repositories': [{
                    'name': r.get('name'),
                    'full_name': r.get('full_name'),
                    'description': r.get('description'),
                    'url': r.get('html_url'),
                    'language': r.get('language'),
                    'stars': r.get('stargazers_count'),
                    'updated_at': r.get('updated_at')
                } for r in result]
            }

        except Exception as e:
            self.logger.log_error('github', 'list_repos_error', str(e))
            return {'error': str(e)}

    @cached_mcp_call('github', ttl=600)
    def get_commits(self,
                   owner: str,
                   repo: str,
                   branch: str = None,
                   since: str = None,
                   until: str = None,
                   limit: int = 30) -> Dict[str, Any]:
        """
        Get commit history

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            since: Start date (ISO 8601)
            until: End date (ISO 8601)
            limit: Maximum commits to return

        Returns:
            Commit list
        """
        try:
            params = {
                'per_page': min(limit, 100)
            }

            if branch:
                params['sha'] = branch
            if since:
                params['since'] = since
            if until:
                params['until'] = until

            result = self._make_request(f'repos/{owner}/{repo}/commits', params=params)

            return {
                'owner': owner,
                'repo': repo,
                'branch': branch,
                'count': len(result),
                'commits': [{
                    'sha': c.get('sha'),
                    'message': c.get('commit', {}).get('message'),
                    'author': c.get('commit', {}).get('author', {}).get('name'),
                    'author_email': c.get('commit', {}).get('author', {}).get('email'),
                    'date': c.get('commit', {}).get('author', {}).get('date'),
                    'url': c.get('html_url')
                } for c in result]
            }

        except Exception as e:
            self.logger.log_error('github', 'commits_error', str(e), query=f'{owner}/{repo}')
            return {'error': str(e), 'owner': owner, 'repo': repo}

    @cached_mcp_call('github', ttl=600)
    def get_pull_requests(self,
                         owner: str,
                         repo: str,
                         state: str = 'open',
                         limit: int = 30) -> Dict[str, Any]:
        """
        Get pull requests

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            limit: Maximum PRs to return

        Returns:
            Pull request list
        """
        try:
            params = {
                'state': state,
                'per_page': min(limit, 100),
                'sort': 'updated',
                'direction': 'desc'
            }

            result = self._make_request(f'repos/{owner}/{repo}/pulls', params=params)

            return {
                'owner': owner,
                'repo': repo,
                'state': state,
                'count': len(result),
                'pull_requests': [{
                    'number': pr.get('number'),
                    'title': pr.get('title'),
                    'state': pr.get('state'),
                    'author': pr.get('user', {}).get('login'),
                    'created_at': pr.get('created_at'),
                    'updated_at': pr.get('updated_at'),
                    'merged': pr.get('merged'),
                    'url': pr.get('html_url')
                } for pr in result]
            }

        except Exception as e:
            self.logger.log_error('github', 'prs_error', str(e), query=f'{owner}/{repo}')
            return {'error': str(e), 'owner': owner, 'repo': repo}

    @cached_mcp_call('github', ttl=300)
    def get_issues(self,
                  owner: str,
                  repo: str,
                  state: str = 'open',
                  labels: List[str] = None,
                  limit: int = 30) -> Dict[str, Any]:
        """
        Get repository issues

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state ('open', 'closed', 'all')
            labels: Filter by labels
            limit: Maximum issues to return

        Returns:
            Issue list
        """
        try:
            params = {
                'state': state,
                'per_page': min(limit, 100),
                'sort': 'updated',
                'direction': 'desc'
            }

            if labels:
                params['labels'] = ','.join(labels)

            result = self._make_request(f'repos/{owner}/{repo}/issues', params=params)

            # Filter out pull requests (GitHub API returns both)
            issues = [i for i in result if 'pull_request' not in i]

            return {
                'owner': owner,
                'repo': repo,
                'state': state,
                'count': len(issues),
                'issues': [{
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'state': issue.get('state'),
                    'author': issue.get('user', {}).get('login'),
                    'labels': [l.get('name') for l in issue.get('labels', [])],
                    'created_at': issue.get('created_at'),
                    'updated_at': issue.get('updated_at'),
                    'comments': issue.get('comments'),
                    'url': issue.get('html_url')
                } for issue in issues]
            }

        except Exception as e:
            self.logger.log_error('github', 'issues_error', str(e), query=f'{owner}/{repo}')
            return {'error': str(e), 'owner': owner, 'repo': repo}

    def create_issue(self,
                    owner: str,
                    repo: str,
                    title: str,
                    body: str = None,
                    labels: List[str] = None,
                    assignees: List[str] = None) -> Dict[str, Any]:
        """
        Create a new issue

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Issue labels
            assignees: Issue assignees

        Returns:
            Created issue
        """
        try:
            data = {
                'title': title,
                'body': body or '',
                'labels': labels or [],
                'assignees': assignees or []
            }

            result = self._make_request(f'repos/{owner}/{repo}/issues', method='POST', data=data)

            return {
                'success': True,
                'number': result.get('number'),
                'url': result.get('html_url'),
                'created_at': result.get('created_at')
            }

        except Exception as e:
            self.logger.log_error('github', 'create_issue_error', str(e), query=f'{owner}/{repo}')
            return {'error': str(e), 'success': False}

    @cached_mcp_call('github', ttl=600)
    def search_code(self,
                   query: str,
                   repo: str = None,
                   language: str = None,
                   limit: int = 30) -> Dict[str, Any]:
        """
        Search code across GitHub

        Args:
            query: Search query
            repo: Limit to specific repository (owner/repo)
            language: Filter by language
            limit: Maximum results

        Returns:
            Code search results
        """
        try:
            search_query = query

            if repo:
                search_query += f' repo:{repo}'
            if language:
                search_query += f' language:{language}'

            params = {
                'q': search_query,
                'per_page': min(limit, 100)
            }

            result = self._make_request('search/code', params=params)

            return {
                'query': query,
                'total_count': result.get('total_count', 0),
                'count': len(result.get('items', [])),
                'results': [{
                    'name': item.get('name'),
                    'path': item.get('path'),
                    'repository': item.get('repository', {}).get('full_name'),
                    'url': item.get('html_url'),
                    'score': item.get('score')
                } for item in result.get('items', [])]
            }

        except Exception as e:
            self.logger.log_error('github', 'search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def get_api_status(self) -> Dict[str, Any]:
        """Check GitHub API status and rate limits"""
        try:
            result = self._make_request('rate_limit')

            return {
                'status': 'operational',
                'service': 'github',
                'rate_limit': {
                    'limit': result.get('rate', {}).get('limit'),
                    'remaining': result.get('rate', {}).get('remaining'),
                    'reset': datetime.fromtimestamp(result.get('rate', {}).get('reset', 0)).isoformat()
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'github',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def create_github_mcp():
    """Factory function to create GitHub MCP server"""
    return GitHubMCPServer()


if __name__ == '__main__':
    # Test the MCP server
    mcp = create_github_mcp()
    print("GitHub MCP Server initialized")
    print("\nChecking API status:")
    status = mcp.get_api_status()
    print(json.dumps(status, indent=2))
