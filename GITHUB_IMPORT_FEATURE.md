# GitHub Import Feature Documentation

## Overview
The GitHub Import feature allows users to import code from GitHub repositories directly into Mosaic for AI-powered code analysis and Q&A.

## How to Use

### 1. Open the Import Dialog
Click the **🐙 Import from GitHub** button in the sidebar

### 2. Enter Repository Information

**Required:**
- Repository URL (supports multiple formats):
  - `https://github.com/owner/repo`
  - `github.com/owner/repo`
  - `owner/repo`

**Optional:**
- Branch name (defaults to main/master)
- File extensions (e.g., `.py, .js, .ts`)
- Path filter (e.g., `src/` to only import files from src directory)
- GitHub token (for private repos or higher rate limits)

### 3. Import and Analyze
- Click **Import** to fetch the repository
- Wait for the success message
- Start asking questions about the code!

## Examples

### Example 1: Import Flask Source
```
URL: https://github.com/pallets/flask
Extensions: .py
Path: src/

Result: Imports all Python files from the src/ directory
```

### Example 2: Import Full Repository
```
URL: facebook/react

Result: Imports all text files from the React repository
```

### Example 3: Private Repository
```
URL: mycompany/private-repo
Token: ghp_xxxxxxxxxxxxx

Result: Imports files from private repository
```

## Features

- ✅ Multiple URL format support
- ✅ File extension filtering
- ✅ Path-based filtering
- ✅ Size limits (100KB per file, 100 files max)
- ✅ Binary file detection
- ✅ Private repository support
- ✅ Rate limit handling
- ✅ Secure token input

## Error Messages

- **Invalid URL**: Check the URL format
- **Repository not found**: Verify the repository exists
- **Private repo**: Provide a GitHub token
- **Rate limited**: Wait or provide a token
- **No files found**: Adjust your filters

## Technical Details

### File Processing
- Files are formatted with headers: `=== File: path/to/file.py ===`
- Content is chunked (4000 chars, 200 char overlap)
- Chunks are added to the context for AI analysis

### Security
- Tokens are password-masked
- No credentials stored
- Binary files skipped
- Size limits enforced

## Troubleshooting

**Q: Import is slow**
A: Large repositories may take time. Consider using filters to reduce file count.

**Q: Getting rate limited**
A: Provide a GitHub token for higher rate limits.

**Q: Files not appearing**
A: Check your file extension and path filters.

## API Reference

See `rlm/github_loader.py` for the complete API:
- `parse_github_url(url: str) -> Tuple[str, str]`
- `fetch_github_repo(**kwargs) -> List[Dict[str, str]]`
