#!/usr/bin/env python3
"""
Test script to verify all 8 CRM tables are accessible and working correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.crm_repo import CRMRepo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_tables():
    """Test all CRM tables."""
    repo = CRMRepo()
    
    test_queries = [
        ("show me crm leads", "leads"),
        ("show campaigns", "campaigns"),
        ("show trainers", "trainers"),
        ("show learners", "learners"),
        ("show tasks", "tasks"),
        ("show activities", "activity"),
        ("show notes", "notes"),
        ("show courses", "Course"),
    ]
    
    print("\n" + "="*80)
    print("  TESTING ALL CRM TABLES")
    print("="*80 + "\n")
    
    all_passed = True
    
    for query, expected_table in test_queries:
        try:
            result = repo.search_crm(query)
            detected_table = repo._detect_table_intent(query)
            
            status = "[OK]" if detected_table == expected_table and len(result) >= 0 else "[FAIL]"
            print(f"{status} Query: '{query}'")
            print(f"     Detected table: {detected_table} (expected: {expected_table})")
            print(f"     Records retrieved: {len(result)}")
            
            if detected_table != expected_table:
                print(f"     WARNING: Table detection mismatch!")
                all_passed = False
            elif len(result) == 0:
                print(f"     NOTE: Table exists but has no data (this is OK)")
            
            if len(result) > 0:
                sample_keys = list(result[0].keys())[:5]
                print(f"     Sample fields: {sample_keys}...")
            
            print()
            
        except Exception as e:
            print(f"[FAIL] Query: '{query}'")
            print(f"     Error: {e}")
            print()
            all_passed = False
    
    print("="*80)
    if all_passed:
        print("  ALL TESTS PASSED!")
    else:
        print("  SOME TESTS FAILED - CHECK ERRORS ABOVE")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = test_all_tables()
    sys.exit(0 if success else 1)

