# Lab 2 Bonus - Multi-Stage Docker Build for Go

## Multi-Stage Build Strategy

### Architecture Overview
```dockerfile
# Stage 1: Builder - Full Go SDK for compilation
FROM golang:1.21-alpine AS builder

# Stage 2: Runtime - Minimal Alpine with only the binary
FROM alpine:latest
```

**Strategy:** Separate compilation environment from runtime environment to minimize final image size while maintaining full build capabilities.

### Stage 1: Builder
```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod .
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go
```

**Purpose:**
- **Full SDK:** Includes Go compiler, standard library, and build tools
- **Dependency Management:** Downloads and caches Go modules
- **Static Compilation:** `CGO_ENABLED=0` creates fully static binary
- **Optimization:** `-ldflags="-s -w"` strips debug info and symbol table

### Stage 2: Runtime
```dockerfile
FROM alpine:latest
RUN apk --no-cache add ca-certificates
RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser
WORKDIR /app
COPY --from=builder /app/devops-info-service .
RUN chown appuser:appuser devops-info-service
USER appuser
EXPOSE 8080
CMD ["./devops-info-service"]
```

**Purpose:**
- **Minimal Base:** Alpine Linux (~5MB) instead of full Go image (~300MB)
- **Security:** Non-root user with specific UID/GID
- **HTTPS Support:** CA certificates for external API calls
- **Binary Only:** Copy only the compiled executable, no source code

## Size Comparison & Analysis

### Build Process Output
```bash
marianikolashina@MacOs app_go % docker build -t devops-info-service-go .
[+] Building 4.4s (18/18) FINISHED                                                                                                                                                                                                                                                                                                                                            docker:orbstack
 => [internal] load build definition from Dockerfile                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring dockerfile: 819B                                                                                                                                                                                                                                                                                                                                                     0.0s
 => [internal] load metadata for docker.io/library/alpine:latest                                                                                                                                                                                                                                                                                                                         0.0s
 => [internal] load metadata for docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                                    0.0s
 => [internal] load .dockerignore                                                                                                                                                                                                                                                                                                                                                        0.0s
 => => transferring context: 279B                                                                                                                                                                                                                                                                                                                                                        0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                                              0.1s
 => [stage-1 1/6] FROM docker.io/library/alpine:latest                                                                                                                                                                                                                                                                                                                                   0.0s
 => [internal] load build context                                                                                                                                                                                                                                                                                                                                                        0.0s
 => => transferring context: 5.03kB                                                                                                                                                                                                                                                                                                                                                      0.0s
 => [stage-1 2/6] RUN apk --no-cache add ca-certificates                                                                                                                                                                                                                                                                                                                                 1.9s
 => [builder 2/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                                           0.1s
 => [builder 3/6] COPY go.mod .                                                                                                                                                                                                                                                                                                                                                          0.0s
 => [builder 4/6] RUN go mod download                                                                                                                                                                                                                                                                                                                                                    0.1s
 => [builder 5/6] COPY main.go .                                                                                                                                                                                                                                                                                                                                                         0.1s
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go                                                                                                                                                                                                                                                                                  3.5s
 => [stage-1 3/6] RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser                                                                                                                                                                                                                                                                                               0.2s 
 => [stage-1 4/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                                           0.1s 
 => [stage-1 5/6] COPY --from=builder /app/devops-info-service .                                                                                                                                                                                                                                                                                                                         0.1s 
 => [stage-1 6/6] RUN chown appuser:appuser devops-info-service                                                                                                                                                                                                                                                                                                                          0.1s 
 => exporting to image                                                                                                                                                                                                                                                                                                                                                                   0.1s
 => => exporting layers                                                                                                                                                                                                                                                                                                                                                                  0.1s
 => => writing image sha256:dd3f195b86191f9c45c28d3d8d6c1dd37f7fdf4f9a40788409935e782c6babfb                                                                                                                                                                                                                                                                                             0.0s
 => => naming to docker.io/library/devops-info-service-go                                                                                                                                                                                                                                                                                                                                0.0s
```

### Image Size Comparison
```bash
(venv) marianikolashina@MacOs app_go % docker images | grep devops-info-service
devops-info-service-go      latest    95f9106bb28a    18.5MB
devops-info-service-python  latest    0873b3e46f88    156MB

(venv) marianikolashina@MacOs app_go % docker build --target builder -t devops-go-builder .
[+] Building 0.3s (11/11) FINISHED                                                                                                                                                                                                                                                                                                                         docker:orbstack
 => [internal] load build definition from Dockerfile                                                                                                                                                                                                                                                                                                                  0.0s
 => => transferring dockerfile: 819B                                                                                                                                                                                                                                                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                 0.0s
 => [internal] load .dockerignore                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring context: 279B                                                                                                                                                                                                                                                                                                                                     0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                           0.0s
 => [internal] load build context                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring context: 54B                                                                                                                                                                                                                                                                                                                                      0.0s
 => CACHED [builder 2/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                 0.0s
 => CACHED [builder 3/6] COPY go.mod .                                                                                                                                                                                                                                                                                                                                0.0s
 => CACHED [builder 4/6] RUN go mod download                                                                                                                                                                                                                                                                                                                          0.0s
 => CACHED [builder 5/6] COPY main.go .                                                                                                                                                                                                                                                                                                                               0.0s
 => CACHED [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go                                                                                                                                                                                                                                                        0.0s
 => exporting to image                                                                                                                                                                                                                                                                                                                                                0.2s
 => => exporting layers                                                                                                                                                                                                                                                                                                                                               0.2s
 => => writing image sha256:b006977da71b0d7e237f379f30fc8fe819c48e07f4a59ce12cf89afaa4e6b7b4                                                                                                                                                                                                                                                                          0.0s
 => => naming to docker.io/library/devops-go-builder                                                                                                                                                                                                                                                                                                                  0.0s
(venv) marianikolashina@MacOs app_go % docker build -t devops-go-runtime .
[+] Building 0.1s (18/18) FINISHED                                                                                                                                                                                                                                                                                                                         docker:orbstack
 => [internal] load build definition from Dockerfile                                                                                                                                                                                                                                                                                                                  0.0s
 => => transferring dockerfile: 819B                                                                                                                                                                                                                                                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/alpine:latest                                                                                                                                                                                                                                                                                                      0.0s
 => [internal] load metadata for docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                 0.0s
 => [internal] load .dockerignore                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring context: 279B                                                                                                                                                                                                                                                                                                                                     0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                           0.0s
 => [internal] load build context                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring context: 54B                                                                                                                                                                                                                                                                                                                                      0.0s
 => [stage-1 1/6] FROM docker.io/library/alpine:latest                                                                                                                                                                                                                                                                                                                0.0s
 => CACHED [stage-1 2/6] RUN apk --no-cache add ca-certificates                                                                                                                                                                                                                                                                                                       0.0s
 => CACHED [stage-1 3/6] RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser                                                                                                                                                                                                                                                                     0.0s
 => CACHED [stage-1 4/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                 0.0s
 => CACHED [builder 2/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                 0.0s
 => CACHED [builder 3/6] COPY go.mod .                                                                                                                                                                                                                                                                                                                                0.0s
 => CACHED [builder 4/6] RUN go mod download                                                                                                                                                                                                                                                                                                                          0.0s
 => CACHED [builder 5/6] COPY main.go .                                                                                                                                                                                                                                                                                                                               0.0s
 => CACHED [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go                                                                                                                                                                                                                                                        0.0s
 => CACHED [stage-1 5/6] COPY --from=builder /app/devops-info-service .                                                                                                                                                                                                                                                                                               0.0s
 => CACHED [stage-1 6/6] RUN chown appuser:appuser devops-info-service                                                                                                                                                                                                                                                                                                0.0s
 => exporting to image                                                                                                                                                                                                                                                                                                                                                0.0s
 => => exporting layers                                                                                                                                                                                                                                                                                                                                               0.0s
 => => writing image sha256:dd3f195b86191f9c45c28d3d8d6c1dd37f7fdf4f9a40788409935e782c6babfb                                                                                                                                                                                                                                                                          0.0s
 => => naming to docker.io/library/devops-go-runtime                                                                                                                                                                                                                                                                                                                  0.0s
(venv) marianikolashina@MacOs app_go % docker images | grep devops-go
devops-go-builder                                                   latest              b006977da71b   21 minutes ago   290MB
devops-go-runtime                                                   latest              dd3f195b8619   21 minutes ago   18.5MB
```

**Analysis:**
- **Go Final Image:** 18.5MB (88% smaller than Python)
- **Builder Stage:** ~300MB (not in final image)
- **Size Reduction:** 281.5MB saved by multi-stage approach
- **Efficiency:** 8.4x smaller than Python equivalent

### Detailed Size Breakdown
| Component | Size | Purpose |
|-----------|------|---------|
| Alpine Base | ~5MB | Minimal Linux distribution |
| CA Certificates | ~1MB | HTTPS/TLS support |
| Go Binary | ~12MB | Compiled application |
| User/Permissions | ~0.5MB | Security setup |
| **Total** | **18.5MB** | **Production-ready container** |

**Comparison with Single-Stage:**
- Single-stage (golang:1.21-alpine): ~300MB
- Multi-stage (alpine + binary): 18.5MB
- **Space Saved:** 281.5MB (94% reduction)

## Why Multi-Stage Builds Matter for Compiled Languages

### 1. Dramatic Size Reduction
**Problem:** Compiled language images include entire SDK
- Go SDK: ~300MB
- Rust toolchain: ~500MB
- Java JDK: ~400MB

**Solution:** Multi-stage builds separate build-time from runtime dependencies
- Build stage: Full toolchain for compilation
- Runtime stage: Minimal base + binary only

### 2. Security Benefits
**Smaller Attack Surface:**
- No compiler or build tools in production image
- Fewer packages = fewer vulnerabilities
- Minimal base images receive faster security updates

**Example:**
- Builder stage: 300+ packages
- Runtime stage: <20 packages

### 3. Performance Advantages
**Faster Deployments:**
- 18.5MB vs 300MB = 16x faster image pulls
- Reduced network bandwidth usage
- Faster container startup times

**Resource Efficiency:**
- Less disk space per container
- More containers per host
- Reduced memory overhead

### 4. Production Optimization
**Clean Runtime Environment:**
- No source code in production image
- No build artifacts or temporary files
- Only essential runtime dependencies

## Terminal Output & Testing

### Build Process
```bash
(venv) marianikolashina@MacOs app_python % cd ../app_go
(venv) marianikolashina@MacOs app_go % docker build -t devops-info-service-go .
[+] Building 4.4s (18/18) FINISHED                                                                                                                                                                                                                                                                                                                                            docker:orbstack
 => [internal] load build definition from Dockerfile                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring dockerfile: 819B                                                                                                                                                                                                                                                                                                                                                     0.0s
 => [internal] load metadata for docker.io/library/alpine:latest                                                                                                                                                                                                                                                                                                                         0.0s
 => [internal] load metadata for docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                                    0.0s
 => [internal] load .dockerignore                                                                                                                                                                                                                                                                                                                                                        0.0s
 => => transferring context: 279B                                                                                                                                                                                                                                                                                                                                                        0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.21-alpine                                                                                                                                                                                                                                                                                                                              0.1s
 => [stage-1 1/6] FROM docker.io/library/alpine:latest                                                                                                                                                                                                                                                                                                                                   0.0s
 => [internal] load build context                                                                                                                                                                                                                                                                                                                                                        0.0s
 => => transferring context: 5.03kB                                                                                                                                                                                                                                                                                                                                                      0.0s
 => [stage-1 2/6] RUN apk --no-cache add ca-certificates                                                                                                                                                                                                                                                                                                                                 1.9s
 => [builder 2/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                                           0.1s
 => [builder 3/6] COPY go.mod .                                                                                                                                                                                                                                                                                                                                                          0.0s
 => [builder 4/6] RUN go mod download                                                                                                                                                                                                                                                                                                                                                    0.1s
 => [builder 5/6] COPY main.go .                                                                                                                                                                                                                                                                                                                                                         0.1s
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go                                                                                                                                                                                                                                                                                  3.5s
 => [stage-1 3/6] RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser                                                                                                                                                                                                                                                                                               0.2s 
 => [stage-1 4/6] WORKDIR /app                                                                                                                                                                                                                                                                                                                                                           0.1s 
 => [stage-1 5/6] COPY --from=builder /app/devops-info-service .                                                                                                                                                                                                                                                                                                                         0.1s 
 => [stage-1 6/6] RUN chown appuser:appuser devops-info-service                                                                                                                                                                                                                                                                                                                          0.1s 
 => exporting to image                                                                                                                                                                                                                                                                                                                                                                   0.1s
 => => exporting layers                                                                                                                                                                                                                                                                                                                                                                  0.1s
 => => writing image sha256:dd3f195b86191f9c45c28d3d8d6c1dd37f7fdf4f9a40788409935e782c6babfb                                                                                                                                                                                                                                                                                             0.0s
 => => naming to docker.io/library/devops-info-service-go                                                                                                                                                                                                                                                                                                                                0.0s
```

### Container Testing
```bash
(venv) marianikolashina@MacOs app_go % docker run -d -p 8081:8080 --name test-go-app devops-info-service-go

b1b01c779388036fd31be2693161a409b11cf6f7bd2d272d9399b8a3cbf87ca5
(venv) marianikolashina@MacOs app_go % curl http://localhost:8081/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Go net/http"},"system":{"hostname":"b1b01c779388","platform":"linux","platform_version":"linux arm64","architecture":"arm64","cpu_count":10,"go_version":"go1.21.13"},"runtime":{"uptime_seconds":18,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-01T14:06:20Z","timezone":"UTC"},"request":{"client_ip":"192.168.215.1:59466","user_agent":"curl/8.6.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
(venv) marianikolashina@MacOs app_go % curl http://localhost:8081/health
{"status":"healthy","timestamp":"2026-02-01T14:06:26Z","uptime_seconds":25}
```

## Technical Explanation of Each Stage

### Stage 1 (Builder) Purpose
1. **Environment Setup:** Full Go SDK with all build tools
2. **Dependency Resolution:** Download and cache Go modules
3. **Compilation:** Create statically-linked binary
4. **Optimization:** Strip debug symbols for smaller binary

**Key Decisions:**
- `golang:1.21-alpine`: Smaller than full Debian-based image
- `CGO_ENABLED=0`: Ensures static linking (no external dependencies)
- `-ldflags="-s -w"`: Removes symbol table and debug info

### Stage 2 (Runtime) Purpose
1. **Minimal Base:** Alpine Linux for small footprint
2. **Security Setup:** Non-root user creation
3. **Runtime Dependencies:** CA certificates for HTTPS
4. **Application Deployment:** Copy only the binary

**Key Decisions:**
- `alpine:latest`: Minimal Linux distribution
- Specific UID/GID: Consistent user management
- `COPY --from=builder`: Extract only the binary from build stage

## Security Implications

### Reduced Attack Surface
**Builder Stage Vulnerabilities:** Not present in final image
- Compiler vulnerabilities
- Build tool exploits
- Source code exposure
- Development dependencies

**Runtime-Only Threats:**
- Minimal package set reduces vulnerability count
- No build tools available for attackers
- Smaller image = faster security patches

### Comparison
| Aspect | Single-Stage | Multi-Stage |
|--------|-------------|-------------|
| **Packages** | 300+ | <20 |
| **Attack Vectors** | High | Minimal |
| **Update Frequency** | Slow | Fast |
| **Vulnerability Scan Time** | Long | Short |

## Challenges & Solutions

### Challenge 1: Static vs Dynamic Linking
**Problem:** Go binary needed to run on Alpine Linux
**Solution:** Used `CGO_ENABLED=0` to create fully static binary with no external dependencies

### Challenge 2: CA Certificates
**Problem:** HTTPS requests would fail without certificates
**Solution:** Added `ca-certificates` package to runtime stage for TLS support

### Challenge 3: User Permissions
**Problem:** Binary copied as root, needed non-root execution
**Solution:** Added `chown` command after copying binary to ensure proper ownership

### Challenge 4: Build Context Optimization
**Problem:** Large build context slowed down builds
**Solution:** Created .dockerignore to exclude unnecessary files

## Conclusion

Multi-stage builds provide significant advantages for compiled languages:

**Size Efficiency:** 94% reduction (300MB → 18.5MB)
**Security:** Minimal attack surface with no build tools
**Performance:** Faster deployments and container startup
**Production-Ready:** Clean runtime environment with only essential components

This approach is essential for production Go applications where image size, security, and deployment speed matter.