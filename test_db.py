"""
Test script to verify sqlite3 database operations work correctly.
Run this to test the database functionality after converting from SQLModel.

Usage:
    python test_db.py
"""
import sys
from pathlib import Path

# Add the app directory to the path so we can import utils
app_dir = Path(__file__).parent / "app"
sys.path.append(str(app_dir))

from utils.db import (
    init_database, create_evaluation, get_evaluations_by_alert,
    get_evaluations_by_comment, check_comment_evaluated, 
    get_evaluation_count, get_database_stats, ensure_database
)
from utils.schemas import EvaluationCreate


def test_database_operations():
    """Test all database operations"""
    print("🧪 Testing SQLite3 Database Operations")
    print("=" * 50)
    
    try:
        # Test 1: Initialize database
        print("1. Testing database initialization...")
        ensure_database()
        print("✅ Database initialized successfully")
        
        # Test 2: Get initial stats
        print("\n2. Testing database stats (empty)...")
        stats = get_database_stats()
        print(f"✅ Initial stats: {stats}")
        
        # Test 3: Create evaluation
        print("\n3. Testing evaluation creation...")
        test_eval = EvaluationCreate(
            AICommentId="test_comment_001",
            AlertId="test_alert_001",
            Grade=7,
            UserId="test_user",
            Notes="This is a test evaluation"
        )
        
        created_eval = create_evaluation(test_eval)
        print(f"✅ Created evaluation with ID: {created_eval.EvaluationId}")
        
        # Test 4: Check comment evaluated
        print("\n4. Testing comment evaluation check...")
        is_evaluated = check_comment_evaluated("test_comment_001")
        print(f"✅ Comment evaluated status: {is_evaluated}")
        
        # Test 5: Get evaluations by alert
        print("\n5. Testing get evaluations by alert...")
        alert_evals = get_evaluations_by_alert("test_alert_001")
        print(f"✅ Found {len(alert_evals)} evaluations for alert")
        
        # Test 6: Get evaluations by comment
        print("\n6. Testing get evaluations by comment...")
        comment_evals = get_evaluations_by_comment("test_comment_001")
        print(f"✅ Found {len(comment_evals)} evaluations for comment")
        
        # Test 7: Get evaluation count
        print("\n7. Testing evaluation count...")
        count = get_evaluation_count()
        print(f"✅ Total evaluations: {count}")
        
        # Test 8: Create another evaluation
        print("\n8. Testing second evaluation creation...")
        test_eval2 = EvaluationCreate(
            AICommentId="test_comment_002", 
            AlertId="test_alert_001",
            Grade=5,
            Notes="Another test evaluation"
        )
        
        created_eval2 = create_evaluation(test_eval2)
        print(f"✅ Created second evaluation with ID: {created_eval2.EvaluationId}")
        
        # Test 9: Final stats
        print("\n9. Testing final database stats...")
        final_stats = get_database_stats()
        print(f"✅ Final stats: {final_stats}")
        
        # Test 10: Validate data integrity
        print("\n10. Testing data integrity...")
        all_alert_evals = get_evaluations_by_alert("test_alert_001")
        if len(all_alert_evals) == 2:
            print("✅ Data integrity check passed")
            
            # Show evaluation details
            for eval in all_alert_evals:
                print(f"   - Evaluation {eval.EvaluationId}: Grade {eval.Grade}, User: {eval.UserId}")
        else:
            print(f"❌ Data integrity check failed: expected 2, got {len(all_alert_evals)}")
        
        print("\n" + "=" * 50)
        print("🎉 All database tests completed successfully!")
        print("\nDatabase is ready for use with your Streamlit app.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_operations()
    sys.exit(0 if success else 1)