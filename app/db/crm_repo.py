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
        Uses LENIENT matching with synonyms and variations.
        Returns table key or "leads" as default.
        """
        query_lower = query.lower()
        
        # Table detection keywords with comprehensive synonyms (LENIENT matching)
        table_keywords = {
            "campaigns": ["campaign", "campaigns", "marketing campaign", "marketing"],
            "tasks": ["task", "tasks", "todo", "todos", "to-do", "to do"],
            "trainers": ["trainer", "trainers", "instructor", "instructors", "teacher", "teachers"],
            "learners": ["learner", "learners", "student", "students", "trainee", "trainees"],
            "Course": ["course", "courses", "program", "programs", "curriculum", "curricula"],
            "activity": ["activity", "activities", "log", "logs", "event", "events"],
            "notes": ["note", "notes", "comment", "comments", "remark", "remarks"],
            "leads": ["lead", "leads", "prospect", "prospects", "enquiry", "enquiries", 
                     "inquiry", "inquiries", "customer lead", "potential customer"]
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
        
        # STEP 3: Detect if this is a LIST/GET/SHOW query (should return all records)
        # Patterns that indicate "get all" intent (LENIENT matching)
        list_query_patterns = [
            # "all [entity]" patterns
            r'\ball\s+(?:the\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)',
            # "[entity] details/info/data" patterns
            r'(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)\s+(?:details?|information|info|data)',
            # "list [entity]" patterns
            r'list\s+(?:out\s+)?(?:all\s+)?(?:the\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)',
            # "show [entity]" patterns
            r'show\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)',
            # "get [entity]" patterns
            r'get\s+(?:all\s+)?(?:the\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)',
            # "give [entity]" patterns
            r'give\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)',
            # "display [entity]" patterns
            r'display\s+(?:all\s+)?(?:the\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)',
            # Just entity name alone (e.g., "leads", "trainers")
            r'^(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)$',
            # "crm [entity]" or "[entity] in crm"
            r'(?:crm\s+)?(?:trainers?|leads?|campaigns?|tasks?|learners?|courses?|activities?|notes?)(?:\s+in\s+crm)?',
            # "crm data" or "crm information"
            r'crm\s+(?:data|information|info)'
        ]
        
        is_list_query = any(re.search(pattern, query_lower) for pattern in list_query_patterns)
        
        # STEP 4: Extract text query ONLY if this is NOT a list query
        # For list queries, we return all records without text filtering
        if not is_list_query:
            text_query = query
            # Remove common query words that don't represent actual search terms
            # This list is comprehensive to catch all variations
            query_words = [
                # Date keywords
                'today', 'yesterday', 'this week', 'new', 'recent',
                # Action verbs
                'show', 'shows', 'display', 'get', 'give', 'list', 'find', 'fetch', 'search',
                'see', 'view', 'tell', 'provide', 'return', 'bring',
                # Pronouns and filler words
                'me', 'my', 'i', 'want', 'need', 'please', 'can', 'could', 'would',
                # System keywords
                'crm', 'data', 'details', 'information', 'info', 'record', 'records',
                # Articles and determiners
                'all', 'the', 'a', 'an', 'some', 'any', 'every', 'each',
                # Verb forms
                's', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
                # Entity names (will be detected separately)
                'campaign', 'campaigns', 'lead', 'leads', 'task', 'tasks',
                'trainer', 'trainers', 'learner', 'learners', 'course', 'courses',
                'activity', 'activities', 'note', 'notes',
                # Common connectors
                'out', 'of', 'in', 'from', 'with', 'for', 'to'
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
        
        # STEP 5: Apply filters ONLY when clear and specific
        # Default behavior: return all records if no specific filter
        
        # Apply text search ONLY if there's a meaningful text query (not a list query)
        text_query_applied = False
        if filters.get("text_query"):
            # Validate text query is meaningful (not just leftover words)
            text_query = filters["text_query"].strip()
            # Only apply if it's longer than 2 chars and not a common word
            common_words = {'out', 'the', 'all', 'me', 'my', 'i', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'of', 'for', 'to', 'with'}
            if len(text_query) > 2 and text_query.lower() not in common_words:
                # Build OR condition for all search fields
                or_conditions = ",".join([f"{field}.ilike.%{text_query}%" for field in search_fields])
                query_builder = query_builder.or_(or_conditions)
                logger.info(f"Applied text search: {text_query}")
                text_query_applied = True
            else:
                logger.info(f"Ignoring ambiguous text query: '{text_query}' - treating as list query")
                # Clear the text query so we return all records
                filters["text_query"] = None
        
        # If no date filter and no valid text query, return all records (DEFAULT BEHAVIOR)
        if not (filters["start_date"] and filters["end_date"]) and not text_query_applied:
            logger.info("No specific search criteria - returning all records (default behavior)")
        
        # Always order by order_field descending (newest first)
        query_builder = query_builder.order(order_field, desc=True)
        
        # Apply limit
        response = query_builder.limit(limit).execute()
        
        return response.data if response.data else []
    
    def search_crm_paginated(
        self, 
        query: str, 
        page: int = 1, 
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        NEW METHOD: Paginated CRM search (does not change existing search_crm).
        Returns paginated results with metadata.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Number of records per page (defaults to settings.DEFAULT_PAGE_SIZE)
            
        Returns:
            Dict with keys: data, total, page, page_size, has_more
        """
        from app.core.config import settings
        
        if page < 1:
            page = 1
        if page_size is None:
            page_size = settings.DEFAULT_PAGE_SIZE
        if page_size > settings.MAX_PAGE_SIZE:
            page_size = settings.MAX_PAGE_SIZE
        
        offset = (page - 1) * page_size
        
        try:
            # Detect which table to query
            table_key = self._detect_table_intent(query)
            table_config = self.TABLE_CONFIGS[table_key]
            
            logger.info(f"Paginated search - table: {table_key}, page: {page}, page_size: {page_size}")
            
            # Parse filters
            filters = self._parse_date_filters(query)
            
            # Build query with pagination
            table_name = table_config["table"]
            search_fields = table_config["search_fields"]
            date_field = table_config["date_field"]
            order_field = table_config["order_field"]
            
            query_builder = self.supabase.table(table_name).select("*", count="exact")
            
            # Apply filters (same logic as _build_query)
            if filters["start_date"] and filters["end_date"]:
                start_iso = filters["start_date"].isoformat()
                end_iso = filters["end_date"].isoformat()
                query_builder = query_builder.gte(date_field, start_iso)
                query_builder = query_builder.lte(date_field, end_iso)
            
            text_query_applied = False
            if filters.get("text_query"):
                text_query = filters["text_query"].strip()
                common_words = {'out', 'the', 'all', 'me', 'my', 'i', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'of', 'for', 'to', 'with'}
                if len(text_query) > 2 and text_query.lower() not in common_words:
                    or_conditions = ",".join([f"{field}.ilike.%{text_query}%" for field in search_fields])
                    query_builder = query_builder.or_(or_conditions)
                    text_query_applied = True
            
            # Apply pagination
            query_builder = query_builder.order(order_field, desc=True)
            response = query_builder.range(offset, offset + page_size - 1).execute()
            
            data = response.data if response.data else []
            total = response.count if hasattr(response, 'count') and response.count is not None else len(data)
            has_more = (offset + page_size) < total
            
            return {
                "data": data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": has_more
            }
            
        except Exception as e:
            logger.error(f"Error in paginated CRM search: {e}", exc_info=True)
            return {
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_more": False
            }
    
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
