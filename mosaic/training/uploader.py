"""
S3 Uploader for Data Donation feature.

Handles uploading anonymized training logs to AWS S3.
"""

import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
import shutil

# Try to import boto3 with graceful handling
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Try to import secrets with graceful handling
try:
    from mosaic.config import secrets
    SECRETS_AVAILABLE = True
except ImportError:
    SECRETS_AVAILABLE = False


class S3Uploader:
    """
    Handles uploading anonymized training data to AWS S3.
    
    This class manages the process of:
    1. Checking AWS credentials
    2. Scanning for .jsonl.gz files
    3. Creating a zip archive
    4. Uploading to S3
    5. Archiving original files on success
    """
    
    def __init__(self):
        """Initialize the S3Uploader."""
        self.trajectories_path = Path.home() / ".mosaic" / "data" / "trajectories"
        self.archived_path = self.trajectories_path / "archived"
    
    def upload_donation_bundle(self):
        """
        Upload anonymized training data to S3.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Check if boto3 is available
        if not BOTO3_AVAILABLE:
            return (False, "boto3 library is not installed. Install with: pip install boto3")
        
        # Check if secrets module is available
        if not SECRETS_AVAILABLE:
            return (False, "Secrets configuration not found. Please configure AWS credentials in mosaic/config/secrets.py")
        
        # Check if AWS keys are configured
        try:
            access_key = secrets.AWS_PUBLIC_ACCESS_KEY
            secret_key = secrets.AWS_PUBLIC_SECRET_KEY
            bucket_name = secrets.S3_BUCKET_NAME
        except AttributeError as e:
            return (False, f"Missing configuration in secrets.py: {e}")
        
        # Check if keys are not placeholder values
        if access_key == "PLACEHOLDER" or secret_key == "PLACEHOLDER":
            return (False, "AWS credentials are not configured. Please update mosaic/config/secrets.py with real credentials.")
        
        # Ensure trajectories directory exists
        if not self.trajectories_path.exists():
            return (False, f"Trajectories directory not found: {self.trajectories_path}")
        
        # Scan for .jsonl.gz files
        jsonl_files = list(self.trajectories_path.glob("*.jsonl.gz"))
        
        if not jsonl_files:
            return (False, "No .jsonl.gz files found to upload in trajectories directory.")
        
        # Create temporary zip archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"mosaic_donation_{timestamp}.zip"
        zip_path = Path(tempfile.gettempdir()) / zip_filename
        
        try:
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for jsonl_file in jsonl_files:
                    zipf.write(jsonl_file, arcname=jsonl_file.name)
            
            # Initialize S3 client
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
            except Exception as e:
                zip_path.unlink()  # Clean up temp file
                return (False, f"Failed to initialize S3 client: {e}")
            
            # Upload to S3
            try:
                s3_client.upload_file(str(zip_path), bucket_name, zip_filename)
            except NoCredentialsError:
                zip_path.unlink()
                return (False, "Invalid AWS credentials. Please check your configuration.")
            except ClientError as e:
                zip_path.unlink()
                return (False, f"Failed to upload to S3: {e}")
            except Exception as e:
                zip_path.unlink()
                return (False, f"Upload error: {e}")
            
            # Upload successful - archive original files
            self.archived_path.mkdir(parents=True, exist_ok=True)
            
            for jsonl_file in jsonl_files:
                archived_file = self.archived_path / jsonl_file.name
                shutil.move(str(jsonl_file), str(archived_file))
            
            # Clean up temporary zip file
            zip_path.unlink()
            
            return (True, f"Successfully uploaded {len(jsonl_files)} file(s) to S3. Files archived locally.")
            
        except Exception as e:
            # Clean up temp file if it exists
            if zip_path.exists():
                zip_path.unlink()
            return (False, f"Error during upload process: {e}")
