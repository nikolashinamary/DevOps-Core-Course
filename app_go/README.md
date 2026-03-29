# DevOps Info Service (Go)

A high-performance Go implementation of the DevOps Info Service, providing comprehensive system information and health status monitoring.

## Overview

This is the compiled language implementation of the DevOps Info Service, built with Go's standard `net/http` package. It provides the same functionality as the Python version but with better performance and smaller binary size.

## Prerequisites

- Go 1.21 or higher
- Git (for cloning)

## Installation & Build

1. **Clone and navigate:**
   ```bash
   git clone <repository-url>
   cd app_go
   ```

2. **Build the application:**
   ```bash
   go build -o devops-info-service main.go
   ```

3. **Or build with optimizations:**
   ```bash
   go build -ldflags="-s -w" -o devops-info-service main.go
   ```

## Running the Application

### Using Go run (development)
```bash
go run main.go
```

### Using compiled binary
```bash
./devops-info-service
```

### Custom Configuration
```bash
# Custom port
PORT=3000 ./devops-info-service

# Custom host and port
HOST=127.0.0.1 PORT=8080 ./devops-info-service
```

## API Endpoints

### GET /
Returns comprehensive service and system information (same JSON structure as Python version).

### GET /health
Simple health check endpoint for monitoring.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `8080` | Port number to listen on |

## Performance Comparison

**Binary Size:**
- Go binary: ~6-8 MB (statically linked)
- Python + dependencies: ~50+ MB

**Memory Usage:**
- Go: ~5-10 MB RAM
- Python: ~20-30 MB RAM

**Startup Time:**
- Go: Instant
- Python: ~1-2 seconds

## Testing

```bash
# Test main endpoint
curl http://localhost:8080/

# Test health endpoint
curl http://localhost:8080/health

# Pretty-print JSON
curl http://localhost:8080/ | jq .
```

## Cross-Platform Building

```bash
# Linux
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go

# macOS ARM64
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-darwin-arm64 main.go
```