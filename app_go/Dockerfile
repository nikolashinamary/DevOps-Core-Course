# Stage 1: Builder
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod .

# Download dependencies
RUN go mod download

# Copy source code
COPY main.go .

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go

# Stage 2: Runtime
FROM alpine:latest

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser

WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /app/devops-info-service .

# Change ownership
RUN chown appuser:appuser devops-info-service

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Run application
CMD ["./devops-info-service"]