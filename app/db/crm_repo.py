from typing import Any, List, Dict, Optional
from app.db.supabase import get_edify_supabase_client
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class CRMRepo:
    """
    Repository for CRM data access.
    Reads from ALL Edify CRM tables using Edify Supabase client (read-only).
    Supports: campaigns, leads, tasks, trainers, learners, Course, activity, notes
    Contains NO business logic - only data retrieval.
    """
    
    # Table configurations with exact field names from Edify Supabase
    TABLE_CONFIGS = {
        "campaigns": {
            "table": "campaigns",
            "search_fields": ["name", "status", "type", "campaign_owner", "phone"],
            "date_field": "created_at",
            "order_field": "created_at"
        },
        "leads": {
            "table": "leads",
            "search_fields": ["name", "email", "phone", "lead_status", "course_list", "lead_source", "lead_owner"],
            "date_field": "created_at",
            "order_field": "created_at"
        },
        "tasks": {
            "table": "tasks",
            "search_fields": ["subject", "priority", "status", "task_type"],
            "date_field": "created_at",
            "order_field": "created_at"
        },
        "trainers": {
            "table": "trainers",
            "search_fields": ["trainer_name", "trainer_status", "tech_stack", "email", "phone", "location"],
            "date_field": "created_at",
            "order_field": "created_at"
        },
        "learners": {
            "table": "learners",
            "search_fields": ["name", "email", "phone", "status", "course", "location"],
            "date_field": "created_at",
            "order_field": "created_at"
        },
        "Course": {
            "table": "Course",  # Note: capital C as per schema
            "search_fields": ["title", "description", "trainer", "duration"],
            "date_field": "createdAt",  # Note: camelCase as per schema
            "order_field": "createdAt"
        },
        "activity": {
            "table": "activity",
            "search_fields": ["activity_name"],
            "date_field": "created_at",
            "order_field": "created_at"
        },
        "notes": {
            "table": "notes",
            "search_fields": ["content"],
            "date_field": "created_at",
            "order_field": "created_at"
        }
    }
    
    def __init__(self):
        self.supabase = get_edify_supabase_client()
    
    def _detect_table_intent(self, query: str) -> Optional[str]:
        """
        Detects which CRM table the user wants to query based on keywords.
        Returns table key or None if ambiguous.
        """
        query_lower = query.lower()
        
        # Table detection keywords (order matters - more specific first)
        table_keywords = {
            "campaigns": ["campaign", "campaigns"],
            "tasks": ["task", "tasks", "todo", "todos"],
            "trainers": ["trainer", "trainers", "instructor", "instructors"],
            "learners": ["learner", "learners", "student", "students"],
            "Course": ["course", "courses", "program", "programs"],
            "activity": ["activity", "activities", "log", "logs"],
            "notes": ["note", "notes", "comment", "comments"],
            "leads": ["lead", "leads", "prospect", "prospects"]
        }
        
        # Count matches for each table
        table_scores = {table: 0 for table in self.TABLE_CONFIGS.keys()}
        
        for table, keywords in table_keywords.items():
            for keyword in keywords:
                if re.search(rf'\b{keyword}\b', query_lower):
                    table_scores[table] += 1
        
        # Find table with highest score
        max_score = max(table_scores.values())
        if max_score == 0:
            # No specific table mentioned, default to leads
            return "leads"
        
        # Return table with highest score
        for table, score in table_scores.items():
            if score == max_score:
                return table
        
        return "leads"  # Default fallback
    
    def _parse_date_filters(self, query: str) -> Dict[str, Any]:
        """
        Parses date-related keywords from the query string.
        Returns a dict with date filter information.
        """
        query_lower = query.lower()
        filters = {
            "start_date": None,
            "end_date": None,
            "is_new": False,
            "text_query": None
        }
        
        # Get today's date range (start and end of day)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Check for "today" keyword
        if re.search(r'\btoday\b', query_lower):
            filters["start_date"] = today_start
            filters["end_date"] = today_end
        
        # Check for "yesterday" keyword
        elif re.search(r'\byesterday\b', query_lower):
            yesterday_start = today_start - timedelta(days=1)
            yesterday_end = today_end - timedelta(days=1)
            filters["start_date"] = yesterday_start
            filters["end_date"] = yesterday_end
        
        # Check for "this week" keyword
        elif re.search(r'\bthis week\b', query_lower):
            days_since_monday = datetime.now().weekday()
            week_start = today_start - timedelta(days=days_since_monday)
            filters["start_date"] = week_start
            filters["end_date"] = today_end
        
        # Check for "new" keyword (typically means recent, e.g., last 7 days)
        if re.search(r'\bnew\b', query_lower):
            filters["is_new"] = True
            # If no other date filter, default "new" to last 7 days
            if filters["start_date"] is None:
                filters["start_date"] = today_start - timedelta(days=7)
                filters["end_date"] = today_end
        
        # Extract text query (remove common query words and date-related keywords)
        text_query = query
        # Remove common query words that don't represent actual search terms
        query_words = [
            'today', 'yesterday', 'this week', 'new', 
            'show', 'shows', 'display', 'get', 'give', 'list', 'find', 'fetch',
            'me', 'my', 'i', 'want', 'need', 'see', 'view',
            'crm', 'data', 'details', 'information', 'info',
            'all', 'the', 'a', 'an', 'some',
            's', 'is', 'are', 'was', 'were',
            'campaign', 'campaigns', 'lead', 'leads', 'task', 'tasks',
            'trainer', 'trainers', 'learner', 'learners', 'course', 'courses',
            'activity', 'activities', 'note', 'notes'
        ]
        for keyword in query_words:
            text_query = re.sub(rf'\b{keyword}\b', '', text_query, flags=re.IGNORECASE)
        text_query = ' '.join(text_query.split())  # Clean up extra spaces
        
        # Only use as text query if there's meaningful content left (more than 2 chars)
        if text_query.strip() and len(text_query.strip()) > 2:
            filters["text_query"] = text_query.strip()
        
        return filters
    
    def _build_query(self, table_config: Dict[str, Any], filters: Dict[str, Any], limit: int = 50):
        """
        Builds and executes Supabase query based on table config and filters.
        """
        table_name = table_config["table"]
        search_fields = table_config["search_fields"]
        date_field = table_config["date_field"]
        order_field = table_config["order_field"]
        
        query_builder = self.supabase.table(table_name).select("*")
        
        # Apply date filters if present
        if filters["start_date"] and filters["end_date"]:
            # Format dates for Supabase (ISO format)
            start_iso = filters["start_date"].isoformat()
            end_iso = filters["end_date"].isoformat()
            
            query_builder = query_builder.gte(date_field, start_iso)
            query_builder = query_builder.lte(date_field, end_iso)
            
            logger.info(f"Applied date filter on {date_field}: {start_iso} to {end_iso}")
        
        # Apply text search if there's a text query
        if filters["text_query"]:
            # Build OR condition for all search fields
            or_conditions = ",".join([f"{field}.ilike.%{filters['text_query']}%" for field in search_fields])
            query_builder = query_builder.or_(or_conditions)
            logger.info(f"Applied text search: {filters['text_query']}")
        elif not (filters["start_date"] and filters["end_date"]):
            # If no date filter and no text query, return all records (no filter)
            logger.info("No specific search criteria - returning all records")
        
        # Always order by order_field descending (newest first)
        query_builder = query_builder.order(order_field, desc=True)
        
        # Apply limit
        response = query_builder.limit(limit).execute()
        
        return response.data if response.data else []
    
    def search_crm(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches CRM data across all supported tables.
        Automatically detects which table to query based on user intent.
        Returns raw verified data from Supabase.
        
        Args:
            query: Search query string (can include table name, date keywords, text search)
            
        Returns:
            List of CRM records (raw data from Supabase)
        """
        try:
            # Detect which table to query
            table_key = self._detect_table_intent(query)
            table_config = self.TABLE_CONFIGS[table_key]
            
            logger.info(f"Detected table: {table_key} (table: {table_config['table']})")
            
            # Parse filters
            filters = self._parse_date_filters(query)
            
            # Build and execute query
            data = self._build_query(table_config, filters, limit=50)
            
            logger.info(f"Retrieved {len(data)} records from {table_config['table']}")
            return data
            
        except Exception as e:
            logger.error(f"Error searching CRM: {e}", exc_info=True)
            # Try fallback: query leads table with simple text search
            try:
                logger.info("Falling back to leads table with simple text search")
                filters = self._parse_date_filters(query)
                table_config = self.TABLE_CONFIGS["leads"]
                data = self._build_query(table_config, filters, limit=50)
                return data
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}", exc_info=True)
                return []
    
    def get_all_campaigns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all campaigns."""
        return self._get_all_from_table("campaigns", limit)
    
    def get_all_leads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all leads."""
        return self._get_all_from_table("leads", limit)
    
    def get_all_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all tasks."""
        return self._get_all_from_table("tasks", limit)
    
    def get_all_trainers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all trainers."""
        return self._get_all_from_table("trainers", limit)
    
    def get_all_learners(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all learners."""
        return self._get_all_from_table("learners", limit)
    
    def get_all_courses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all courses."""
        return self._get_all_from_table("Course", limit)
    
    def get_all_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all activities."""
        return self._get_all_from_table("activity", limit)
    
    def get_all_notes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all notes."""
        return self._get_all_from_table("notes", limit)
    
    def _get_all_from_table(self, table_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Internal method to get all records from a specific table."""
        try:
            table_config = self.TABLE_CONFIGS[table_key]
            filters = {"start_date": None, "end_date": None, "is_new": False, "text_query": None}
            return self._build_query(table_config, filters, limit)
        except Exception as e:
            logger.error(f"Error getting all from {table_key}: {e}", exc_info=True)
            return []
