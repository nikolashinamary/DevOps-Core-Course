# Lab 2 Submission - Docker Containerization

## Docker Best Practices Applied

### 1. Non-Root User
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```
**Why it matters:** Running as root inside containers creates security vulnerabilities. If an attacker compromises the container, they have root privileges. Non-root users limit the attack surface and follow the principle of least privilege.

### 2. Layer Caching Optimization
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```
**Why it matters:** Docker caches layers during builds. By copying requirements.txt first and installing dependencies before copying application code, we ensure dependency installation only runs when requirements change, not when code changes. This dramatically speeds up rebuilds.

### 3. Specific Base Image Version
```dockerfile
FROM python:3.13-slim
```
**Why it matters:** Using specific versions ensures reproducible builds. The `slim` variant reduces image size by excluding unnecessary packages while maintaining essential functionality.

### 4. .dockerignore File
```
__pycache__/
*.py[cod]
venv/
.git/
docs/
```
**Why it matters:** Excludes unnecessary files from build context, reducing build time and preventing sensitive files from being copied into the image. Smaller build context means faster uploads to Docker daemon.

### 5. Proper File Ownership
```dockerfile
RUN chown -R appuser:appuser /app
```
**Why it matters:** Ensures the non-root user can access application files. Without proper ownership, the application might fail to read its own files.

## Image Information & Decisions

### Base Image Selection
**Chosen:** `python:3.13-slim`
**Justification:** 
- Latest Python version for security and performance
- `slim` variant balances size (156MB) vs functionality
- Includes essential libraries while excluding development tools
- Official image with regular security updates

### Final Image Size
**Size:** 156MB
**Assessment:** Reasonable for a Python web application. Includes Python runtime, Flask dependencies, and application code. Could be optimized further with Alpine Linux (~50MB reduction) but slim provides better compatibility.

### Layer Structure
1. **Base Layer:** Python 3.13-slim runtime
2. **User Creation:** Non-root user setup
3. **Dependencies:** Flask and related packages
4. **Application:** Source code and configuration
5. **Permissions:** File ownership changes
6. **Runtime:** User switch and startup command

### Optimization Choices
- Used `--no-cache-dir` to avoid storing pip cache
- Copied requirements.txt separately for better caching
- Excluded development files via .dockerignore
- Used system user creation for security

## Build & Run Process

### Build Output
```bash
marianikolashina@MacOs app_python % docker build -t devops-info-service-python .

[+] Building 4.8s (12/12) FINISHED                                                                                                                                                                                                                                                                                                                                            docker:orbstack
 => [internal] load build definition from Dockerfile                                                                                                                                                                                                                                                                                                                                     0.0s
 => => transferring dockerfile: 551B                                                                                                                                                                                                                                                                                                                                                     0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                                                                                                                                                                                                                                                      0.0s
 => [internal] load .dockerignore                                                                                                                                                                                                                                                                                                                                                        0.0s
 => => transferring context: 278B                                                                                                                                                                                                                                                                                                                                                        0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim                                                                                                                                                                                                                                                                                                                                        0.1s
 => [internal] load build context                                                                                                                                                                                                                                                                                                                                                        0.1s
 => => transferring context: 3.48kB                                                                                                                                                                                                                                                                                                                                                      0.0s
 => [2/7] RUN groupadd -r appuser && useradd -r -g appuser appuser                                                                                                                                                                                                                                                                                                                       0.2s
 => [3/7] WORKDIR /app                                                                                                                                                                                                                                                                                                                                                                   0.0s
 => [4/7] COPY requirements.txt .                                                                                                                                                                                                                                                                                                                                                        0.0s
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt                                                                                                                                                                                                                                                                                                                             4.1s
 => [6/7] COPY app.py .                                                                                                                                                                                                                                                                                                                                                                  0.0s 
 => [7/7] RUN chown -R appuser:appuser /app                                                                                                                                                                                                                                                                                                                                              0.1s 
 => exporting to image                                                                                                                                                                                                                                                                                                                                                                   0.1s 
 => => exporting layers                                                                                                                                                                                                                                                                                                                                                                  0.1s 
 => => writing image sha256:a425071dcf5306eb881b236e04c35ee4323a7b35955a7b48222c9232a09b1af5                                                                                                                                                                                                                                                                                             0.0s 
 => => naming to docker.io/library/devops-info-service-python    
```

### Container Running
```bash
marianikolashina@MacOs app_python % docker run -d -p 5001:5000 --name test-python-app devops-info-service-python
06eba029a2c8e4416cd07f5f6000318e005baedb7a19487c64626b145531826e

marianikolashina@MacOs app_python % docker ps

CONTAINER ID   IMAGE                             COMMAND                  CREATED         STATUS                PORTS                                                                                                                                                 NAMES
06eba029a2c8   devops-info-service-python        "python app.py"          6 seconds ago   Up 5 seconds          0.0.0.0:5001->5000/tcp, :::5001->5000/tcp                                                                                                             test-python-app
```

### Endpoint Testing
```bash
marianikolashina@MacOs app_python % curl http://localhost:5001/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"192.168.215.1","method":"GET","path":"/","user_agent":"curl/8.6.0"},"runtime":{"current_time":"2026-02-01T14:03:37.200913+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":14},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":10,"hostname":"06eba029a2c8","platform":"Linux","platform_version":"Linux-6.9.6-orbstack-00147-gb0567c7c0069-aarch64-with-glibc2.41","python_version":"3.13.11"}}

marianikolashina@MacOs app_python % curl http://localhost:5001/health

{"status":"healthy","timestamp":"2026-02-01T14:03:42.733355+00:00","uptime_seconds":19}
```

### Docker Hub Repository
**URL:** `https://hub.docker.com/repository/docker/nikolashinamaria/devops-info-service-python`

## Technical Analysis

### Why This Dockerfile Works
1. **Layer Ordering:** Dependencies installed before code copying enables efficient caching
2. **Security Model:** Non-root user prevents privilege escalation attacks
3. **Build Context:** .dockerignore reduces build time and prevents sensitive file inclusion
4. **Base Image:** Slim variant provides good balance of size and functionality

### Layer Order Impact
If we changed the order to copy all files first:
```dockerfile
COPY . .  # This would invalidate cache on every code change
RUN pip install -r requirements.txt  # This would reinstall deps every time
```
**Result:** Every code change would trigger dependency reinstallation, making builds 10x slower.

### Security Considerations
- **Non-root execution:** Limits container breakout impact
- **Minimal base image:** Reduces attack surface
- **No secrets in layers:** .dockerignore prevents accidental inclusion
- **Specific versions:** Prevents supply chain attacks from version drift

### .dockerignore Benefits
- **Build Speed:** Excludes 50MB+ of unnecessary files (venv/, docs/, .git/)
- **Security:** Prevents sensitive files from entering image
- **Size:** Reduces final image size by excluding development artifacts
- **Consistency:** Ensures only production-relevant files are included

## Challenges & Solutions

### Challenge 1: Layer Caching Understanding
**Problem:** Initial Dockerfile copied all files first, causing slow rebuilds
**Solution:** Researched Docker layer caching and reordered instructions for optimal caching

### Challenge 2: Non-Root User Implementation
**Problem:** Application failed to start due to file permission issues
**Solution:** Added `chown` command to ensure non-root user can access application files

### Challenge 3: Container Networking
**Problem:** Understanding port mapping between container and host
**Solution:** Used `-p 5001:5000` to map host port 5001 to container port 5000, avoiding conflicts
cd m    
## What I Learned

1. **Docker Layer Caching:** Order of instructions dramatically affects build performance
2. **Security Best Practices:** Non-root users are essential for production containers
3. **Image Optimization:** .dockerignore and base image selection significantly impact size
4. **Container Networking:** Port mapping allows multiple containers on same host
5. **Build Context:** Understanding what gets sent to Docker daemon improves build efficiency

The containerized application works identically to the local version while providing better security, portability, and deployment consistency.