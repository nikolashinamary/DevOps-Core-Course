# DevOps Info Service

[![Python CI/CD](https://github.com/marianikolashina/DevOps-Core-Course/workflows/Python%20CI%2FCD/badge.svg?branch=main)](https://github.com/marianikolashina/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/marianikolashina/DevOps-Core-Course/branch/main/graph/badge.svg)](https://codecov.io/gh/marianikolashina/DevOps-Core-Course)

A production-ready Python web service that provides comprehensive system information and health status monitoring. Built as part of the DevOps Engineering course.

## Overview

The DevOps Info Service is a lightweight web application that reports detailed information about itself and its runtime environment. It serves as a foundation for DevOps monitoring and will evolve throughout the course to include containerization, CI/CD, and advanced monitoring capabilities.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # or if python command not found
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or if pip command not found
   pip3 install -r requirements.txt
   ```

## Running the Application

### Default Configuration
```bash
python app.py
# or if python command not found
python3 app.py
```
The service will start on `http://0.0.0.0:5000`

### Custom Configuration
```bash
# Custom port
PORT=8080 python app.py
# or if python command not found
PORT=8080 python3 app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py
# or if python command not found
HOST=127.0.0.1 PORT=3000 python3 app.py

# Enable debug mode
DEBUG=true python app.py
# or if python command not found
DEBUG=true python3 app.py
```

## API Endpoints

### GET /
Returns comprehensive service and system information.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "platform_version": "macOS-14.0-arm64",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.5"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2024-01-15T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### GET /health
Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

## Configuration

The application supports configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable Flask debug mode |

## Docker

### Building the Image
```bash
docker build -t devops-info-service-python .
```

### Running the Container
```bash
# Run on default port 5000
docker run -p 5000:5000 devops-info-service-python

# Run on custom port
docker run -p 8080:5000 devops-info-service-python

# Run in detached mode
docker run -d -p 5000:5000 --name devops-app devops-info-service-python
```

### Pulling from Docker Hub
```bash
docker pull nikolashinamaria/devops-info-service-python
docker run -p 5000:5000 nikolashinamaria/devops-info-service-python
```

## Testing

### Running Unit Tests Locally

Install testing dependencies:
```bash
pip install -r requirements-dev.txt
```

Run all tests:
```bash
pytest tests/ -v
```

Run tests with coverage report:
```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
```

Run specific test class:
```bash
pytest tests/test_app.py::TestIndexEndpoint -v
```

Run specific test:
```bash
pytest tests/test_app.py::TestIndexEndpoint::test_index_status_code -v
```

### Test Coverage

Current test coverage: **95%**

Coverage report breakdown:
- `app.py`: 91% coverage (43 statements, 4 missed)
- `tests/test_app.py`: 96% coverage (195 statements, 8 missed)

The test suite includes:
- **29 comprehensive unit tests**
- HTTP status code validation
- JSON response structure validation
- System information accuracy tests
- Error handling tests (404, 405, 500)
- Cross-endpoint consistency tests
- Helper function validation

To view detailed coverage report after running tests:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Testing

Test the endpoints using curl:

```bash
# Test main endpoint
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Pretty-print JSON response
curl http://localhost:5000/ | python -m json.tool
```
