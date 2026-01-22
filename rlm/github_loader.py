"""
GitHub Repository Loader for Mosaic.

This module provides functionality to fetch code files from GitHub repositories
for use in context-aware code analysis and Q&A.
"""

from typing import List, Dict, Tuple, Optional
import re
from github import Github, GithubException, UnknownObjectException, RateLimitExceededException
import base64


def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Parse a GitHub URL to extract owner and repo name.
    
    Supports multiple URL formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo
    - owner/repo (shorthand)
    
    Args:
        url: GitHub URL in various formats
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        ValueError: If URL format is not recognized
    """
    # Remove whitespace
    url = url.strip()
    
    # Pattern 1: https://github.com/owner/repo or https://github.com/owner/repo.git
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', url)
    if match:
        return match.group(1), match.group(2)
    
    # Pattern 2: github.com/owner/repo
    match = re.match(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', url)
    if match:
        return match.group(1), match.group(2)
    
    # Pattern 3: owner/repo (shorthand)
    match = re.match(r'^([^/]+)/([^/]+?)(?:\.git)?$', url)
    if match:
        return match.group(1), match.group(2)
    
    raise ValueError(
        f"Invalid GitHub URL format: {url}. "
        "Expected formats: 'https://github.com/owner/repo', 'github.com/owner/repo', or 'owner/repo'"
    )


def fetch_github_repo(
    repo_url: str,
    branch: Optional[str] = None,
    file_extensions: Optional[List[str]] = None,
    path_filter: Optional[str] = None,
    github_token: Optional[str] = None,
    max_file_size: int = 100000,  # 100KB default
    max_total_files: int = 100
) -> List[Dict[str, str]]:
    """
    Fetch code files from a GitHub repository.
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
        branch: Specific branch or tag (default: repo's default branch)
        file_extensions: List of extensions to include (e.g., [".py", ".js"])
        path_filter: Only include files under this path (e.g., "src/")
        github_token: Optional GitHub token for private repos or higher rate limits
        max_file_size: Skip files larger than this (in bytes)
        max_total_files: Maximum number of files to fetch
        
    Returns:
        List of dicts with 'path', 'content', and 'size' keys
        
    Raises:
        ValueError: If URL is invalid or repo not found
        PermissionError: If repo is private and no token provided
        RuntimeError: If rate limit exceeded or other API errors occur
    """
    # Parse the GitHub URL
    try:
        owner, repo_name = parse_github_url(repo_url)
    except ValueError as e:
        raise ValueError(str(e))
    
    # Initialize GitHub API client
    try:
        if github_token:
            g = Github(github_token)
        else:
            g = Github()  # Anonymous access (lower rate limits)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize GitHub client: {str(e)}")
    
    # Get the repository
    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
    except UnknownObjectException:
        raise ValueError(f"Repository not found: {owner}/{repo_name}")
    except GithubException as e:
        if e.status == 403:
            raise PermissionError(
                f"Repository is private. Please provide a GitHub token."
            )
        raise RuntimeError(f"Failed to access repository: {str(e)}")
    
    # Determine which branch to use
    try:
        if branch:
            ref = repo.get_branch(branch)
            sha = ref.commit.sha
        else:
            # Use default branch
            sha = repo.default_branch
    except GithubException as e:
        raise ValueError(f"Branch '{branch}' not found in repository")
    
    # Normalize file extensions (ensure they start with '.')
    if file_extensions:
        file_extensions = [
            ext if ext.startswith('.') else f'.{ext}'
            for ext in file_extensions
        ]
    
    # Normalize path filter (remove leading/trailing slashes)
    if path_filter:
        path_filter = path_filter.strip('/')
    
    # Fetch repository contents recursively
    fetched_files = []
    files_processed = 0
    
    try:
        # Get all contents recursively
        contents = repo.get_git_tree(sha, recursive=True)
        
        for item in contents.tree:
            # Check if we've hit the file limit
            if files_processed >= max_total_files:
                break
            
            # Only process files (not directories)
            if item.type != "blob":
                continue
            
            file_path = item.path
            
            # Apply path filter if specified
            if path_filter and not file_path.startswith(path_filter):
                continue
            
            # Apply file extension filter if specified
            if file_extensions:
                if not any(file_path.endswith(ext) for ext in file_extensions):
                    continue
            
            # Check file size
            if item.size > max_file_size:
                continue
            
            # Fetch file content
            try:
                file_content_obj = repo.get_git_blob(item.sha)
                
                # Decode content (handle base64 encoding)
                if file_content_obj.encoding == "base64":
                    try:
                        content = base64.b64decode(file_content_obj.content).decode('utf-8')
                    except UnicodeDecodeError:
                        # Skip binary files that can't be decoded as UTF-8
                        continue
                else:
                    content = file_content_obj.content
                
                # Add to fetched files
                fetched_files.append({
                    'path': file_path,
                    'content': content,
                    'size': item.size
                })
                
                files_processed += 1
                
            except GithubException as e:
                # Skip files that can't be fetched
                continue
            except Exception as e:
                # Skip files with other errors
                continue
        
    except RateLimitExceededException:
        raise RuntimeError(
            "GitHub API rate limit exceeded. Try again later or provide a GitHub token for higher limits."
        )
    except GithubException as e:
        raise RuntimeError(f"Failed to fetch repository contents: {str(e)}")
    
    if not fetched_files:
        raise ValueError("No files found matching your filters")
    
    return fetched_files
