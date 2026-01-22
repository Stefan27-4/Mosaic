# Data Donation Feature - Documentation

## Overview

The Data Donation feature allows users to contribute their anonymized training logs to scientific research by uploading them to AWS S3. This feature is designed to be non-intrusive, secure, and easy to use.

## Components

### 1. `mosaic/config/secrets_template.py`

A template file containing placeholder AWS credentials. This file is safe to commit to version control.

**Usage:**
1. Copy `secrets_template.py` to `secrets.py` in the same directory
2. Replace placeholder values with actual AWS credentials
3. `secrets.py` is automatically excluded via `.gitignore`

```python
AWS_PUBLIC_ACCESS_KEY = "your-access-key-here"
AWS_PUBLIC_SECRET_KEY = "your-secret-key-here"
S3_BUCKET_NAME = "mosaic-training-data-donations"
```

### 2. `mosaic/training/uploader.py`

The S3Uploader class handles the upload process with the following features:

**Key Features:**
- Gracefully handles missing dependencies (boto3, secrets module)
- Validates AWS credentials (rejects placeholder values)
- Scans `~/.mosaic/data/trajectories/` for `.jsonl.gz` files
- Creates timestamped zip archives
- Uploads to S3 with proper error handling
- Archives original files on successful upload
- Cross-platform path handling

**API:**
```python
from mosaic.training.uploader import S3Uploader

uploader = S3Uploader()
success, message = uploader.upload_donation_bundle()

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

**Return Values:**
- `(True, "Success message")` - Upload completed successfully
- `(False, "Error message")` - Upload failed with explanation

### 3. `mosaic/gui/settings_tab.py`

A customtkinter-based GUI component for the data donation interface.

**Key Features:**
- Clean, modern UI matching Mosaic's "Lovable Software" theme
- Background thread processing (non-blocking GUI)
- Real-time status feedback with color-coded messages
- "Contribute to Science" section with informative description
- Technical details panel showing file location and format

**Integration:**
```python
from mosaic.gui.settings_tab import SettingsTab

# In your main application window
settings_tab = SettingsTab(parent_widget)
settings_tab.pack(fill="both", expand=True)
```

## Security Considerations

✅ **Safe Practices:**
- `secrets.py` is in `.gitignore` - credentials won't be committed
- Template file uses `PLACEHOLDER` values - safe to commit
- Credentials are validated before use
- All file operations use cross-platform `pathlib.Path`

⚠️ **Important:**
- Never commit real AWS credentials to version control
- Always use `secrets.py` (copy from template) for real credentials
- Ensure S3 bucket has appropriate access controls

## Error Handling

The implementation handles various error scenarios gracefully:

1. **Missing boto3:** Returns error suggesting installation
2. **Missing secrets.py:** Returns error with configuration instructions
3. **Placeholder credentials:** Rejects and asks for real credentials
4. **No files to upload:** Returns informative message
5. **S3 upload failures:** Cleans up temporary files and reports error
6. **Invalid AWS credentials:** Reports authentication failure

## Testing

Run the test suite to verify functionality:

```bash
# From repository root
python /tmp/test_uploader_comprehensive.py
```

**Test Coverage:**
- Missing secrets configuration handling
- File scanning with various file types
- Placeholder credential rejection
- Missing directory handling
- Cross-platform path resolution

## Usage Example

### For Developers

```python
# Setup (one time)
cp mosaic/config/secrets_template.py mosaic/config/secrets.py
# Edit secrets.py with real AWS credentials

# Programmatic usage
from mosaic.training.uploader import S3Uploader

uploader = S3Uploader()
success, message = uploader.upload_donation_bundle()
print(message)
```

### For End Users

1. Click on the "Settings" tab in the Mosaic application
2. Locate the "Contribute to Science" section
3. Read the description and technical details
4. Click the "Donate Data" button
5. Wait for upload to complete (button shows "Uploading...")
6. View success/error message with status indicator

## File Structure

```
mosaic/
├── config/
│   ├── __init__.py
│   ├── secrets_template.py  # Template (committed)
│   └── secrets.py           # Actual credentials (gitignored)
├── training/
│   ├── __init__.py
│   └── uploader.py          # S3Uploader class
└── gui/
    ├── __init__.py
    └── settings_tab.py      # Settings UI component
```

## Dependencies

**Required:**
- Python 3.8+
- pathlib (standard library)
- zipfile (standard library)
- tempfile (standard library)
- datetime (standard library)
- shutil (standard library)

**Optional:**
- boto3 - For AWS S3 uploads (gracefully degrades without it)
- customtkinter - For GUI (only needed for GUI component)

## Future Enhancements

Potential improvements:
- Progress bar for large uploads
- Selective file upload (let users choose which files)
- Encryption before upload
- Upload scheduling (automatic periodic uploads)
- Data anonymization verification tool

## Support

For issues or questions:
1. Check error messages - they provide specific guidance
2. Verify AWS credentials are properly configured
3. Ensure boto3 is installed: `pip install boto3`
4. Check file permissions in `~/.mosaic/data/trajectories/`
