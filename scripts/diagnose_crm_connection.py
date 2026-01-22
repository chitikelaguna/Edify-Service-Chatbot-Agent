#!/usr/bin/env python3
"""
Diagnostic script to test Edify Supabase connection and identify CRM data access issues.
This script will:
1. Test connection to Edify Supabase
2. List available tables
3. Check if crm_leads table exists
4. Show table structure and field names
5. Test querying data
6. Identify exact issues
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.supabase import get_edify_supabase_client
from app.core.config import settings
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

# Use ASCII-safe characters for Windows console
CHECK = "[OK]"
CROSS = "[X]"
WARN = "[!]"

def test_connection():
    """Test 1: Check if we can connect to Edify Supabase."""
    print_section("TEST 1: Connection Test")
    
    try:
        print(f"{CHECK} Edify Supabase URL: {settings.EDIFY_SUPABASE_URL[:50]}...")
        print(f"{CHECK} Service Role Key: {'*' * 20}...{settings.EDIFY_SUPABASE_SERVICE_ROLE_KEY[-10:]}")
        
        client = get_edify_supabase_client()
        print(f"{CHECK} Successfully created Supabase client")
        return client
    except Exception as e:
        print(f"{CROSS} FAILED to create client: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def list_tables(client):
    """Test 2: List all available tables in the database."""
    print_section("TEST 2: List Available Tables")
    
    try:
        # Try to query information_schema to get table names
        # Note: This might not work with Supabase Python client directly
        # We'll try alternative methods
        
        print("Attempting to list tables...")
        print("Note: Supabase Python client doesn't directly support listing tables.")
        print("We'll try to query common table names instead...")
        
        common_table_names = [
            "crm_leads", "leads", "crm_lead", "lead",
            "crm_contacts", "contacts", "crm_opportunities",
            "lms_batches", "rms_candidates"
        ]
        
        found_tables = []
        for table_name in common_table_names:
            try:
                result = client.table(table_name).select("count", count="exact").limit(1).execute()
                found_tables.append(table_name)
                print(f"  {CHECK} Table '{table_name}' EXISTS")
            except Exception as e:
                error_msg = str(e).lower()
                if "does not exist" in error_msg or "relation" in error_msg or "not found" in error_msg:
                    print(f"  {CROSS} Table '{table_name}' does NOT exist")
                else:
                    print(f"  {WARN} Table '{table_name}' - Error: {e}")
        
        return found_tables
    except Exception as e:
        print(f"✗ Error listing tables: {e}")
        return []

def check_table_structure(client, table_name):
    """Test 3: Check the structure of a specific table."""
    print_section(f"TEST 3: Table Structure Check - '{table_name}'")
    
    try:
        # Try to get a sample record to see the structure
        print(f"Fetching a sample record from '{table_name}'...")
        result = client.table(table_name).select("*").limit(1).execute()
        
        if result.data and len(result.data) > 0:
            print(f"{CHECK} Table '{table_name}' has data!")
            print(f"{CHECK} Found {len(result.data)} sample record(s)")
            
            # Show the structure
            sample_record = result.data[0]
            print("\n  Table Fields:")
            print("  " + "-"*76)
            for field_name, field_value in sample_record.items():
                field_type = type(field_value).__name__
                value_preview = str(field_value)[:50] if field_value is not None else "NULL"
                print(f"    • {field_name:30} ({field_type:15}) = {value_preview}")
            
            return sample_record
        else:
            print(f"{WARN} Table '{table_name}' exists but has NO data")
            return None
            
    except Exception as e:
        print(f"{CROSS} Error checking table structure: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def test_query_scenarios(client, table_name, sample_record):
    """Test 4: Test different query scenarios."""
    print_section("TEST 4: Query Scenario Tests")
    
    if not sample_record:
        print(f"{WARN} Skipping query tests - no sample data available")
        return
    
    # Get field names from sample record
    field_names = list(sample_record.keys())
    print(f"Available fields: {', '.join(field_names)}")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Get all records (no filter)",
            "query": lambda: client.table(table_name).select("*").limit(10).execute()
        },
        {
            "name": "Count total records",
            "query": lambda: client.table(table_name).select("count", count="exact").execute()
        }
    ]
    
    # Add date field test if we can identify it
    date_fields = [f for f in field_names if 'date' in f.lower() or 'created' in f.lower() or 'time' in f.lower()]
    if date_fields:
        date_field = date_fields[0]
        print(f"\n  Found potential date field: '{date_field}'")
        
        # Test date query
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        scenarios.append({
            "name": f"Filter by date (today) using field '{date_field}'",
            "query": lambda: client.table(table_name).select("*").gte(date_field, today_start.isoformat()).lte(date_field, today_end.isoformat()).limit(10).execute()
        })
    
    # Test text search on common fields
    text_fields = [f for f in field_names if any(x in f.lower() for x in ['name', 'email', 'company', 'status', 'title'])]
    if text_fields:
        test_field = text_fields[0]
        print(f"\n  Found potential text field: '{test_field}'")
        
        # Get a sample value to search for
        sample_value = sample_record.get(test_field)
        if sample_value and isinstance(sample_value, str) and len(sample_value) > 0:
            search_term = sample_value[:5]  # Use first 5 chars
            scenarios.append({
                "name": f"Text search on '{test_field}' field",
                "query": lambda: client.table(table_name).select("*").ilike(test_field, f"%{search_term}%").limit(10).execute()
            })
    
    # Run scenarios
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n  Scenario {i}: {scenario['name']}")
        try:
            result = scenario['query']()
            if hasattr(result, 'data'):
                print(f"    {CHECK} SUCCESS - Retrieved {len(result.data)} records")
                if len(result.data) > 0:
                    print(f"    {CHECK} Sample record keys: {list(result.data[0].keys())[:5]}...")
            elif hasattr(result, 'count'):
                print(f"    {CHECK} SUCCESS - Total count: {result.count}")
            else:
                print(f"    {CHECK} SUCCESS - Result: {result}")
        except Exception as e:
            print(f"    {CROSS} FAILED - Error: {e}")
            error_msg = str(e).lower()
            if "does not exist" in error_msg:
                print(f"      → Field or table does not exist")
            elif "permission" in error_msg or "access" in error_msg:
                print(f"      → Permission denied - check service role key")
            elif "syntax" in error_msg or "invalid" in error_msg:
                print(f"      → Query syntax error")
            else:
                import traceback
                traceback.print_exc()

def test_current_crm_repo_logic():
    """Test 5: Test the current CRMRepo logic with actual query."""
    print_section("TEST 5: Current CRMRepo Logic Test")
    
    try:
        from app.db.crm_repo import CRMRepo
        
        repo = CRMRepo()
        print(f"{CHECK} CRMRepo initialized")
        print(f"  Table name: {repo.table}")
        
        # Test queries
        test_queries = [
            "show me crm leads",
            "show today's new CRM leads",
            "crm leads",
            "leads"
        ]
        
        for query in test_queries:
            print(f"\n  Testing query: '{query}'")
            try:
                result = repo.search_crm(query)
                print(f"    {CHECK} Query executed - Retrieved {len(result)} records")
                if len(result) > 0:
                    print(f"    {CHECK} Sample record: {list(result[0].keys())[:5]}...")
                else:
                    print(f"    {WARN} No records returned")
            except Exception as e:
                print(f"    {CROSS} Query FAILED: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"{CROSS} Error testing CRMRepo: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all diagnostic tests."""
    print("\n" + "="*80)
    print("  EDIFY SUPABASE CRM CONNECTION DIAGNOSTIC TOOL")
    print("="*80)
    
    # Test 1: Connection
    client = test_connection()
    if not client:
        print(f"\n{CROSS} Cannot proceed - connection failed")
        return
    
    # Test 2: List tables
    found_tables = list_tables(client)
    
    # Test 3: Check table structure
    table_name = "crm_leads"  # Default assumption
    if found_tables:
        table_name = found_tables[0]  # Use first found table
        print(f"\n{CHECK} Using table: '{table_name}'")
    else:
        print(f"\n{WARN} No common tables found. Trying '{table_name}' anyway...")
    
    sample_record = check_table_structure(client, table_name)
    
    # Test 4: Query scenarios
    if sample_record:
        test_query_scenarios(client, table_name, sample_record)
    
    # Test 5: Current CRMRepo logic
    test_current_crm_repo_logic()
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    print("Check the results above to identify:")
    print("  1. If connection is working")
    print("  2. If table exists and its actual name")
    print("  3. What fields are available in the table")
    print("  4. If queries are working")
    print("  5. What the current CRMRepo logic is doing")
    print("\nUse this information to fix the table/field names in crm_repo.py")

if __name__ == "__main__":
    main()

