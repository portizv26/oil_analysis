"""
S3 sync utilities for uploading eval.db to AWS S3 for daily backup.
Implements the S3 upload functionality as specified in the README.
"""
import os
import boto3
from pathlib import Path
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from datetime import datetime
from typing import Optional


def get_s3_config() -> dict:
    """
    Get S3 configuration from environment variables.
    
    Returns:
        Dictionary with S3 configuration or None if missing
    """
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


if __name__ == "__main__":
    """
    Command line interface for S3 sync operations.
    Usage:
        python s3_sync.py                    # Upload eval.sqlite
        python s3_sync.py test               # Test connection
        python s3_sync.py upload <filepath>  # Upload specific file
    """
    import sys
    
    if len(sys.argv) == 1:
        # Default: upload eval.sqlite
        upload_eval_db()
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        # Test connection
        test_s3_connection()
    elif len(sys.argv) == 3 and sys.argv[1] == "upload":
        # Upload specific file
        file_path = sys.argv[2]
        upload_to_s3(file_path)
    else:
        print("Usage:")
        print("  python s3_sync.py                    # Upload eval.sqlite")
        print("  python s3_sync.py test               # Test S3 connection")
        print("  python s3_sync.py upload <filepath>  # Upload specific file")