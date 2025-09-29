"""
Daily upload script for eval.sqlite to S3.
This script should be run via cron/scheduled task to automatically 
sync the evaluation database to S3 for backup and analytics.

Usage:
    python upload_eval_db.py

Environment Variables Required:
    AWS_ACCESS_KEY_ID or ACCESS_KEY
    AWS_SECRET_ACCESS_KEY or SECRET_KEY  
    AWS_S3_BUCKET or BUCKET_NAME
"""
import sys
from pathlib import Path

# Add the app directory to the path so we can import utils
app_dir = Path(__file__).resolve().parent.parent / "app"
sys.path.append(str(app_dir))

from utils.s3_sync import upload_eval_db


def main():
    """Main function to upload eval.db to S3"""
    print("=" * 50)
    print("AI Comments Evaluator - Daily Database Sync")
    print("=" * 50)
    
    try:
        success = upload_eval_db()
        
        if success:
            print("✅ Database sync completed successfully")
            sys.exit(0)
        else:
            print("❌ Database sync failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error during sync: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()