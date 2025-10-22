"""
S3 sync utilities for uploading eval.db to AWS S3 for daily backup.
Implements the S3 upload functionality as specified in the README.
"""
import os
import boto3
import pandas as pd
import sqlite3
from pathlib import Path
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from datetime import datetime
from typing import Optional, List


def get_s3_config() -> dict:
    """
    Get S3 configuration from environment variables or Streamlit secrets.
    Supports both local .env files and Streamlit Cloud secrets.
    
    Returns:
        Dictionary with S3 configuration
    """
    # Try to get from Streamlit secrets first (for deployed apps)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            config = {
                'access_key': st.secrets.get('ACCESS_KEY'),
                'secret_key': st.secrets.get('SECRET_KEY'), 
                'bucket_name': st.secrets.get('BUCKET_NAME'),
                'region': st.secrets.get('AWS_DEFAULT_REGION', 'us-east-1')
            }
            # If all secrets are available, use them
            if all([config['access_key'], config['secret_key'], config['bucket_name']]):
                return config
    except (ImportError, AttributeError, KeyError):
        # Streamlit not available or secrets not configured
        pass
    
    # Fall back to environment variables (for local development)
    config = {
        'access_key': os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('ACCESS_KEY'),
        'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('SECRET_KEY'),
        'bucket_name': os.getenv('AWS_S3_BUCKET') or os.getenv('BUCKET_NAME'),
        'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    }
    
    return config


def upload_to_s3(
    file_path: str, 
    bucket_name: Optional[str] = None, 
    object_name: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None
) -> bool:
    """
    Upload a file to an S3 bucket.
    
    Args:
        file_path: Path to file to upload
        bucket_name: Bucket to upload to (uses env var if not provided)
        object_name: S3 object name (uses filename if not provided)
        access_key: AWS access key (uses env var if not provided)
        secret_key: AWS secret key (uses env var if not provided)
        
    Returns:
        True if file was uploaded successfully, False otherwise
    """
    # Get configuration
    config = get_s3_config()
    
    # Use provided values or fall back to environment
    bucket_name = bucket_name or config['bucket_name']
    access_key = access_key or config['access_key']
    secret_key = secret_key or config['secret_key']
    
    # Validate required parameters
    if not all([file_path, bucket_name, access_key, secret_key]):
        missing = []
        if not file_path: missing.append("file_path")
        if not bucket_name: missing.append("bucket_name")
        if not access_key: missing.append("access_key")
        if not secret_key: missing.append("secret_key")
        
        print(f"Error: Missing required parameters: {', '.join(missing)}")
        print("Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET")
        return False
    
    # Default object name to filename
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    # Create S3 client
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=config['region']
        )
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        return False
    
    # Upload file
    try:
        # Add timestamp to object name for versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name, ext = os.path.splitext(object_name)
        versioned_object_name = f"{base_name}_{timestamp}{ext}"
        
        # Upload current version
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"✅ Uploaded '{file_path}' → s3://{bucket_name}/{object_name}")
        
        # Upload versioned backup
        s3_client.upload_file(file_path, bucket_name, versioned_object_name)
        print(f"✅ Backup uploaded → s3://{bucket_name}/{versioned_object_name}")
        
        return True
        
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return False
    except NoCredentialsError:
        print("Error: AWS credentials not available.")
        print("Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        return False
    except PartialCredentialsError:
        print("Error: Incomplete AWS credentials provided.")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' does not exist.")
        elif error_code == 'AccessDenied':
            print(f"Error: Access denied to bucket '{bucket_name}'. Check permissions.")
        else:
            print(f"Error uploading to S3: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error uploading to S3: {e}")
        return False


def upload_eval_db(custom_path: Optional[str] = None) -> bool:
    """
    Upload the evaluation database to S3.
    
    Args:
        custom_path: Custom path to eval.sqlite (uses default if not provided)
        
    Returns:
        True if upload successful, False otherwise
    """
    # Determine database path
    if custom_path:
        db_path = Path(custom_path)
    else:
        # Default path relative to this script
        db_path = Path(__file__).resolve().parents[2] / "state" / "eval.sqlite"
    
    if not db_path.exists():
        print(f"Warning: Database file does not exist: {db_path}")
        print("This is normal if no evaluations have been submitted yet.")
        return False
    
    print(f"Uploading evaluation database: {db_path}")
    
    # Upload to S3
    success = upload_to_s3(str(db_path), object_name="eval.sqlite")
    
    if success:
        print(f"✅ Database sync completed at {datetime.now()}")
        return True
    else:
        print(f"❌ Database sync failed at {datetime.now()}")
        return False


def test_s3_connection() -> bool:
    """
    Test S3 connection and permissions.
    
    Returns:
        True if connection successful, False otherwise
    """
    config = get_s3_config()
    
    if not all([config['access_key'], config['secret_key'], config['bucket_name']]):
        print("❌ S3 configuration incomplete")
        return False
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            region_name=config['region']
        )
        
        # Test bucket access
        s3_client.head_bucket(Bucket=config['bucket_name'])
        print(f"✅ S3 connection successful - bucket: {config['bucket_name']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ Bucket '{config['bucket_name']}' not found")
        elif error_code == '403':
            print(f"❌ Access denied to bucket '{config['bucket_name']}'")
        else:
            print(f"❌ S3 connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ S3 connection error: {e}")
        return False


def download_from_s3(
    object_name: str,
    local_path: str,
    bucket_name: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None
) -> bool:
    """
    Download a file from S3 bucket.
    
    Args:
        object_name: S3 object key to download
        local_path: Local path where to save the file
        bucket_name: Bucket name (uses env var if not provided)
        access_key: AWS access key (uses env var if not provided)
        secret_key: AWS secret key (uses env var if not provided)
        
    Returns:
        True if file was downloaded successfully, False otherwise
    """
    # Get configuration
    config = get_s3_config()
    
    # Use provided values or fall back to environment
    bucket_name = bucket_name or config['bucket_name']
    access_key = access_key or config['access_key']
    secret_key = secret_key or config['secret_key']
    
    # Validate required parameters
    if not all([object_name, local_path, bucket_name, access_key, secret_key]):
        missing = []
        if not object_name: missing.append("object_name")
        if not local_path: missing.append("local_path")
        if not bucket_name: missing.append("bucket_name")
        if not access_key: missing.append("access_key")
        if not secret_key: missing.append("secret_key")
        
        print(f"Error: Missing required parameters: {', '.join(missing)}")
        return False
    
    # Create directory if it doesn't exist
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create S3 client
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=config['region']
        )
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        return False
    
    # Download file
    try:
        s3_client.download_file(bucket_name, object_name, local_path)
        print(f"✅ Downloaded s3://{bucket_name}/{object_name} → '{local_path}'")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' does not exist.")
        elif error_code == 'NoSuchKey':
            print(f"Error: Object '{object_name}' not found in bucket '{bucket_name}'.")
        elif error_code == 'AccessDenied':
            print(f"Error: Access denied to s3://{bucket_name}/{object_name}")
        else:
            print(f"Error downloading from S3: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error downloading from S3: {e}")
        return False


def download_data_files() -> bool:
    """
    Download all required data files from S3 on startup.
    
    Returns:
        True if all files downloaded successfully, False otherwise
    """
    data_dir = Path(__file__).resolve().parents[2] / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Required data files
    required_files = [
        "alerts.parquet",
        "oil_measurements.parquet", 
        "telemetry_measurements.parquet",
        "ai_comments.parquet"
    ]
    
    print("📥 Downloading data files from S3...")
    
    success_count = 0
    for file_name in required_files:
        local_path = data_dir / file_name
        
        # Skip if file already exists and is recent (less than 1 day old)
        if local_path.exists():
            file_age = datetime.now().timestamp() - local_path.stat().st_mtime
            if file_age < 86400:  # 24 hours
                print(f"⏩ Skipping {file_name} (already up to date)")
                success_count += 1
                continue
        
        if download_from_s3(file_name, str(local_path)):
            success_count += 1
        else:
            print(f"❌ Failed to download {file_name}")
    
    if success_count == len(required_files):
        print(f"✅ All {len(required_files)} data files downloaded successfully")
        return True
    else:
        print(f"⚠️ Downloaded {success_count}/{len(required_files)} files")
        return success_count > 0


def export_evaluations_to_parquet(custom_db_path: Optional[str] = None) -> Optional[str]:
    """
    Export evaluations from SQLite to Parquet format.
    
    Args:
        custom_db_path: Custom path to eval.sqlite (uses default if not provided)
        
    Returns:
        Path to generated parquet file if successful, None otherwise
    """
    # Determine database path
    if custom_db_path:
        db_path = Path(custom_db_path)
    else:
        db_path = Path(__file__).resolve().parents[2] / "state" / "eval.sqlite"
    
    if not db_path.exists():
        print(f"Warning: Database file does not exist: {db_path}")
        return None
    
    # Output path
    output_path = db_path.parent / f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    
    try:
        # Connect to SQLite and read evaluations
        conn = sqlite3.connect(str(db_path))
        
        # Query evaluations with a join to get more context if needed
        query = """
        SELECT 
            EvaluationId,
            AICommentId,
            AlertId,
            UserId,
            Grade,
            Notes,
            CreatedAt
        FROM evaluations
        ORDER BY CreatedAt DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("No evaluations found in database")
            return None
        
        # Save as Parquet
        df.to_parquet(output_path, index=False)
        print(f"✅ Exported {len(df)} evaluations to {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Error exporting evaluations to parquet: {e}")
        return None


def upload_evaluations_parquet() -> bool:
    """
    Export evaluations to Parquet and upload to S3.
    
    Returns:
        True if successful, False otherwise
    """
    # Export to parquet
    parquet_path = export_evaluations_to_parquet()
    
    if not parquet_path:
        return False
    
    try:
        # Upload to S3
        object_name = f"evaluations/{os.path.basename(parquet_path)}"
        success = upload_to_s3(parquet_path, object_name=object_name)
        
        if success:
            print(f"✅ Evaluations parquet uploaded to S3: {object_name}")
            
            # Clean up local parquet file after upload
            Path(parquet_path).unlink()
            print(f"🗑️ Cleaned up local file: {parquet_path}")
            
        return success
        
    except Exception as e:
        print(f"Error uploading evaluations parquet: {e}")
        return False


if __name__ == "__main__":
    """
    Command line interface for S3 sync operations.
    Usage:
        python s3_sync.py                      # Upload eval.sqlite
        python s3_sync.py test                 # Test connection
        python s3_sync.py download             # Download data files
        python s3_sync.py upload <filepath>    # Upload specific file
        python s3_sync.py export-parquet      # Export evaluations to parquet and upload
    """
    import sys
    
    if len(sys.argv) == 1:
        # Default: upload eval.sqlite
        upload_eval_db()
    elif len(sys.argv) == 2:
        command = sys.argv[1]
        if command == "test":
            # Test connection
            test_s3_connection()
        elif command == "download":
            # Download data files
            download_data_files()
        elif command == "export-parquet":
            # Export evaluations to parquet and upload
            upload_evaluations_parquet()
        else:
            print(f"Unknown command: {command}")
            print("See usage below.")
    elif len(sys.argv) == 3 and sys.argv[1] == "upload":
        # Upload specific file
        file_path = sys.argv[2]
        upload_to_s3(file_path)
    else:
        print("Usage:")
        print("  python s3_sync.py                      # Upload eval.sqlite")
        print("  python s3_sync.py test                 # Test S3 connection")
        print("  python s3_sync.py download             # Download data files")
        print("  python s3_sync.py upload <filepath>    # Upload specific file")
        print("  python s3_sync.py export-parquet      # Export evaluations to parquet and upload")