# Lab 1 Submission - DevOps Info Service

## Framework Selection

### Chosen Framework: Flask

**Justification:**
I chose Flask for this implementation because:

- **Lightweight & Simple**: Flask is minimalistic and perfect for microservices
- **Learning Curve**: Easy to understand and implement quickly
- **Flexibility**: Doesn't impose strict project structure, allowing custom organization
- **Production Ready**: Used by many companies for production applications
- **Extensive Documentation**: Well-documented with large community support

### Framework Comparison

| Framework | Pros | Cons | Best For |
|-----------|------|------|----------|
| **Flask** | Lightweight, flexible, simple | Manual configuration needed | Microservices, APIs |
| **FastAPI** | Modern, async, auto-docs | Newer, smaller community | High-performance APIs |
| **Django** | Full-featured, batteries included | Heavy for simple apps | Full web applications |

## Best Practices Applied

### 1. Clean Code Organization
```python
# Clear function separation
def get_system_info():
    """Collect system information."""
    return {...}

def get_uptime():
    """Calculate application uptime."""
    return {...}
```
**Importance**: Makes code maintainable and testable.

### 2. Environment Configuration
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```
**Importance**: Follows 12-factor app principles for configuration management.

### 3. Structured Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```
**Importance**: Essential for debugging and monitoring in production.

### 4. Error Handling
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404
```
**Importance**: Provides consistent error responses and prevents crashes.

### 5. PEP 8 Compliance
- Proper import organization
- Clear variable names
- Consistent indentation
- Docstrings for functions

**Importance**: Ensures code readability and team collaboration.

## API Documentation

### Main Endpoint: GET /

**Request:**
```bash
curl http://localhost:5001/
```

**Response:**
```json
{
    "endpoints": [
        {
            "description": "Service information",
            "method": "GET",
            "path": "/"
        },
        {
            "description": "Health check",
            "method": "GET",
            "path": "/health"
        }
    ],
    "request": {
        "client_ip": "127.0.0.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.6.0"
    },
    "runtime": {
        "current_time": "2026-01-28T09:19:02.681258+00:00",
        "timezone": "UTC",
        "uptime_human": "0 hours, 1 minutes",
        "uptime_seconds": 62
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "arm64",
        "cpu_count": 10,
        "hostname": "MacOs",
        "platform": "Darwin",
        "platform_version": "macOS-14.5-arm64-arm-64bit",
        "python_version": "3.12.9"
    }
}
```

### Health Endpoint: GET /health

**Request:**
```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T09:18:56.929527+00:00",
  "uptime_seconds": 56
}
```

### Testing Commands

```bash
# Start application
cd app_python
source venv/bin/activate
PORT=5001 python app.py

# Test endpoints
curl http://localhost:5001/
curl http://localhost:5001/health

# Pretty print JSON
curl http://localhost:5001/ | python3 -m json.tool

# Test with custom port
PORT=8080 python app.py
curl http://localhost:8080/
```

## Testing Evidence

**Actual Terminal Output:**

**1. Main Endpoint Test:**
```bash
$ curl http://localhost:5001/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.6.0"},"runtime":{"current_time":"2026-01-28T09:18:08.887802+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":8},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"arm64","cpu_count":10,"hostname":"MacOs","platform":"Darwin","platform_version":"macOS-14.5-arm64-arm-64bit","python_version":"3.12.9"}}
```

**2. Health Check Test:**
```bash
$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"2026-01-28T09:18:56.929527+00:00","uptime_seconds":56}
```

**3. Pretty-Printed JSON Test:**
```bash
$ url http://localhost:5001/ | python3 -m json.tool

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   650  100   650    0     0   315k      0 --:--:-- --:--:-- --:--:--  634k
{
    "endpoints": [
        {
            "description": "Service information",
            "method": "GET",
            "path": "/"
        },
        {
            "description": "Health check",
            "method": "GET",
            "path": "/health"
        }
    ],
    "request": {
        "client_ip": "127.0.0.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.6.0"
    },
    "runtime": {
        "current_time": "2026-01-28T09:19:02.681258+00:00",
        "timezone": "UTC",
        "uptime_human": "0 hours, 1 minutes",
        "uptime_seconds": 62
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "arm64",
        "cpu_count": 10,
        "hostname": "MacOs",
        "platform": "Darwin",
        "platform_version": "macOS-14.5-arm64-arm-64bit",
        "python_version": "3.12.9"
    }
}
```

Screenshots are located in `docs/screenshots/`:
- `01-main-endpoint.png` - Main endpoint JSON response
- `02-health-check.png` - Health check response  
- `03-formatted-output.png` - Pretty-printed JSON output

## Challenges & Solutions

### Challenge 1: Port Conflict
**Problem**: Default port 5000 was already in use by macOS AirPlay Receiver.
**Solution**: Used environment variable `PORT=5001` to run on different port.

### Challenge 2: System Information Collection
**Problem**: Getting comprehensive system information across different platforms.
**Solution**: Used Python's `platform` and `socket` modules for cross-platform compatibility.

### Challenge 3: Uptime Calculation
**Problem**: Calculating human-readable uptime format.
**Solution**: Stored start time globally and calculated delta in seconds, then converted to hours/minutes.

## Conclusion

This lab provided hands-on experience with:
- Web framework selection and implementation
- System introspection and API design
- Python best practices and documentation
- Cross-language implementation comparison

The foundation is now ready for containerization in Lab 2.