"""
Database utilities for SQLite operations in oil analysis evaluator.
Handles database initialization, connection management, and CRUD operations.
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from .schemas import Evaluation, EvaluationCreate, EVALUATIONS_TABLE_SQL, EVALUATIONS_INDICES_SQL


# Database configuration  
DB_PATH = Path(__file__).resolve().parents[2] / "state" / "eval.sqlite"


def get_db_path() -> Path:
    """Get database path and ensure directory exists"""
    DB_PATH.parent.mkdir(exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Get a database connection with proper cleanup"""
    conn = None
    try:
        conn = sqlite3.connect(str(get_db_path()))
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        yield conn
    finally:
        if conn:
            conn.close()


def init_database():
    """
    Initialize database and create tables if they don't exist.
    Also creates recommended indices for performance.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Create evaluations table
            cursor.execute(EVALUATIONS_TABLE_SQL)
            
            # Create indices for performance
            for index_sql in EVALUATIONS_INDICES_SQL:
                cursor.execute(index_sql)
            
            conn.commit()
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
            raise


def create_evaluation(evaluation_data: EvaluationCreate) -> Evaluation:
    """
    Create a new evaluation record.
    
    Args:
        evaluation_data: EvaluationCreate model with evaluation details
        
    Returns:
        Created Evaluation with assigned ID
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Convert to full Evaluation object
        evaluation = evaluation_data.to_evaluation()
        
        # Insert into database
        cursor.execute("""
            INSERT INTO evaluations (AICommentId, AlertId, UserId, Grade, Notes, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            evaluation.AICommentId,
            evaluation.AlertId, 
            evaluation.UserId,
            evaluation.Grade,
            evaluation.Notes,
            evaluation.CreatedAt.isoformat()
        ))
        
        # Get the inserted record
        evaluation_id = cursor.lastrowid
        evaluation.EvaluationId = evaluation_id
        
        conn.commit()
        return evaluation


def get_evaluations_by_alert(alert_id: str) -> List[Evaluation]:
    """
    Get all evaluations for a specific alert.
    
    Args:
        alert_id: The AlertId to filter by
        
    Returns:
        List of evaluations for the alert
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EvaluationId, AICommentId, AlertId, UserId, Grade, Notes, CreatedAt
            FROM evaluations 
            WHERE AlertId = ?
            ORDER BY CreatedAt DESC
        """, (alert_id,))
        
        results = []
        for row in cursor.fetchall():
            evaluation = Evaluation(
                EvaluationId=row['EvaluationId'],
                AICommentId=row['AICommentId'],
                AlertId=row['AlertId'],
                UserId=row['UserId'],
                Grade=row['Grade'],
                Notes=row['Notes'],
                CreatedAt=datetime.fromisoformat(row['CreatedAt'])
            )
            results.append(evaluation)
        
        return results


def get_evaluations_by_comment(comment_id: str) -> List[Evaluation]:
    """
    Get all evaluations for a specific AI comment.
    
    Args:
        comment_id: The AICommentId to filter by
        
    Returns:
        List of evaluations for the comment
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EvaluationId, AICommentId, AlertId, UserId, Grade, Notes, CreatedAt
            FROM evaluations 
            WHERE AICommentId = ?
            ORDER BY CreatedAt DESC
        """, (comment_id,))
        
        results = []
        for row in cursor.fetchall():
            evaluation = Evaluation(
                EvaluationId=row['EvaluationId'],
                AICommentId=row['AICommentId'],
                AlertId=row['AlertId'],
                UserId=row['UserId'],
                Grade=row['Grade'],
                Notes=row['Notes'],
                CreatedAt=datetime.fromisoformat(row['CreatedAt'])
            )
            results.append(evaluation)
        
        return results


def get_evaluation_count() -> int:
    """Get total number of evaluations in database"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evaluations")
        return cursor.fetchone()[0]


def check_comment_evaluated(comment_id: str, user_id: Optional[str] = None) -> bool:
    """
    Check if a comment has already been evaluated (optionally by specific user).  
    
    Args:
        comment_id: The AICommentId to check
        user_id: Optional user filter
        
    Returns:
        True if comment has been evaluated
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if user_id is not None:
            cursor.execute("""
                SELECT COUNT(*) FROM evaluations 
                WHERE AICommentId = ? AND UserId = ?
            """, (comment_id, user_id))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM evaluations 
                WHERE AICommentId = ?
            """, (comment_id,))
        
        count = cursor.fetchone()[0]
        return count > 0


def get_database_stats() -> Dict[str, Any]:
    """
    Get basic database statistics for monitoring.
    
    Returns:
        Dictionary with database stats
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total evaluations
            cursor.execute("SELECT COUNT(*) FROM evaluations")
            total_evaluations = cursor.fetchone()[0]
            
            # Unique alerts evaluated  
            cursor.execute("SELECT COUNT(DISTINCT AlertId) FROM evaluations")
            unique_alerts = cursor.fetchone()[0]
            
            # Unique comments evaluated
            cursor.execute("SELECT COUNT(DISTINCT AICommentId) FROM evaluations")
            unique_comments = cursor.fetchone()[0]
            
            # Unique evaluators (excluding NULL)
            cursor.execute("SELECT COUNT(DISTINCT UserId) FROM evaluations WHERE UserId IS NOT NULL")
            unique_users = cursor.fetchone()[0]
            
            return {
                "total_evaluations": total_evaluations,
                "unique_alerts_evaluated": unique_alerts,
                "unique_comments_evaluated": unique_comments,
                "unique_evaluators": unique_users,
                "database_path": str(get_db_path()),
                "database_exists": get_db_path().exists()
            }
    except Exception as e:
        return {
            "error": str(e),
            "database_path": str(get_db_path()),
            "database_exists": get_db_path().exists()
        }


def get_all_evaluations_with_comment_types() -> List[Dict[str, Any]]:
    """
    Get all evaluations joined with comment types for analytics.
    
    Returns:
        List of dictionaries with evaluation data and comment types
    """
    from .io import load_ai_comments
    
    try:
        # Load AI comments to get CommentType data
        comments_df = load_ai_comments()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EvaluationId, AICommentId, AlertId, UserId, Grade, Notes, CreatedAt
                FROM evaluations 
                ORDER BY CreatedAt DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                # Get comment type from parquet data
                comment_row = comments_df[comments_df['AICommentId'] == row['AICommentId']]
                comment_type = comment_row['CommentType'].iloc[0] if not comment_row.empty else 'Unknown'
                
                result = {
                    'EvaluationId': row['EvaluationId'],
                    'AICommentId': row['AICommentId'],
                    'AlertId': row['AlertId'],
                    'UserId': row['UserId'],
                    'Grade': row['Grade'],
                    'Notes': row['Notes'],
                    'CreatedAt': row['CreatedAt'],
                    'CommentType': comment_type
                }
                results.append(result)
            
            return results
            
    except Exception as e:
        print(f"Error getting evaluations with comment types: {e}")
        return []


def ensure_database():
    """Ensure database is initialized - call this before first use"""
    if not get_db_path().exists():
        print("Database not found, initializing...")
        init_database()
    else:
        print("Database already initialized.")