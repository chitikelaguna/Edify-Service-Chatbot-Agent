# Optimization Features Guide

This document describes the optional optimization features that have been added to improve scalability and performance. **All features are disabled by default** and must be explicitly enabled via environment variables.

## Safety Guarantees

✅ **Non-Breaking**: All optimizations are optional and disabled by default  
✅ **Backward Compatible**: Existing code continues to work without changes  
✅ **Graceful Degradation**: Features fail gracefully if dependencies are missing  
✅ **No Function Signature Changes**: All existing methods remain unchanged  

## Available Optimizations

### 1. Rate Limiting

**Purpose**: Prevent API abuse and control costs

**Enable**: Set `ENABLE_RATE_LIMITING=true` in `.env`

**Configuration**:
```env
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

**Installation**:
```bash
pip install slowapi
```

**Behavior**: Limits requests per IP address. Returns 429 (Too Many Requests) when exceeded.

---

### 2. Redis Caching

**Purpose**: Reduce database load and improve response times

**Enable**: Set `ENABLE_CACHING=true` in `.env`

**Configuration**:
```env
ENABLE_CACHING=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional
CACHE_TTL_SECONDS=300  # 5 minutes default
```

**Installation**:
```bash
pip install redis
```

**What's Cached**:
- Chat history (session-based, 5 min TTL)
- CRM query results (query-based, 5 min TTL)

**Behavior**: Falls back to database if Redis unavailable (non-breaking).

---

### 3. Request Timeouts

**Purpose**: Prevent long-running requests from blocking

**Enable**: Set `ENABLE_REQUEST_TIMEOUT=true` in `.env`

**Configuration**:
```env
ENABLE_REQUEST_TIMEOUT=true
REQUEST_TIMEOUT_SECONDS=30
```

**Behavior**: Returns timeout error if request exceeds configured seconds.

---

### 4. Response Compression

**Purpose**: Reduce bandwidth usage

**Enable**: Set `ENABLE_COMPRESSION=true` in `.env`

**Behavior**: Automatically compresses responses > 1KB using gzip.

---

### 5. CORS Configuration

**Purpose**: Security - restrict allowed origins

**Configuration**:
```env
# Allow all (default, not recommended for production)
CORS_ALLOW_ORIGINS=*

# Restrict to specific domains
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

### 6. Pagination Support

**Purpose**: Handle large datasets efficiently

**New Method**: `CRMRepo.search_crm_paginated()`

**Usage**:
```python
repo = CRMRepo()
result = repo.search_crm_paginated("leads", page=1, page_size=50)
# Returns: {"data": [...], "total": 100, "page": 1, "page_size": 50, "has_more": True}
```

**Configuration**:
```env
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=200
```

**Note**: Existing `search_crm()` method unchanged - pagination is a new method.

---

### 7. Connection Pooling

**Purpose**: Optimize database connections

**Enable**: Set `ENABLE_CONNECTION_POOLING=true` in `.env`

**Configuration**:
```env
ENABLE_CONNECTION_POOLING=true
MAX_CONNECTIONS=100
```

**Note**: Supabase client handles pooling internally. This is for future advanced configuration.

---

## Example .env Configuration

```env
# Core settings (required)
OPENAI_API_KEY=your_key
EDIFY_SUPABASE_URL=your_url
EDIFY_SUPABASE_SERVICE_ROLE_KEY=your_key
CHATBOT_SUPABASE_URL=your_url
CHATBOT_SUPABASE_SERVICE_ROLE_KEY=your_key

# Optional optimizations (all disabled by default)
ENABLE_RATE_LIMITING=false
ENABLE_CACHING=false
ENABLE_REQUEST_TIMEOUT=false
ENABLE_COMPRESSION=false
ENABLE_CONNECTION_POOLING=false

# CORS (default allows all)
CORS_ALLOW_ORIGINS=*

# Pagination defaults
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=200
```

## Production Recommendations

For production, enable:

1. **Rate Limiting**: `ENABLE_RATE_LIMITING=true`
2. **Caching**: `ENABLE_CACHING=true` (if Redis available)
3. **CORS**: Set specific origins, not `*`
4. **Compression**: `ENABLE_COMPRESSION=true`
5. **Timeouts**: `ENABLE_REQUEST_TIMEOUT=true`

## Testing

All features can be tested individually:

```bash
# Test with rate limiting
ENABLE_RATE_LIMITING=true RATE_LIMIT_PER_MINUTE=5 python -m uvicorn app.main:app

# Test with caching
ENABLE_CACHING=true REDIS_HOST=localhost python -m uvicorn app.main:app

# Test with all optimizations
ENABLE_RATE_LIMITING=true ENABLE_CACHING=true ENABLE_COMPRESSION=true python -m uvicorn app.main:app
```

## Monitoring

Check logs for optimization status:
- Rate limiting: "Rate limiting enabled: X/min, Y/hour"
- Caching: "Redis caching enabled and connected"
- Compression: "Response compression enabled"
- CORS: "CORS configured for origins: [...]"

## Troubleshooting

**Rate limiting not working?**
- Check if `slowapi` is installed: `pip install slowapi`
- Verify `ENABLE_RATE_LIMITING=true` in `.env`

**Caching not working?**
- Check if `redis` is installed: `pip install redis`
- Verify Redis is running: `redis-cli ping`
- Check connection settings in `.env`

**Features disabled even when enabled?**
- Check logs for import errors
- Verify environment variables are loaded
- Ensure dependencies are installed

