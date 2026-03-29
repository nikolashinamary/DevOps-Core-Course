package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// TestGetHostname tests the getHostname function
func TestGetHostname(t *testing.T) {
	hostname := getHostname()
	if hostname == "" {
		t.Error("expected non-empty hostname")
	}
}

// TestGetUptime tests the getUptime function
func TestGetUptime(t *testing.T) {
	seconds, human := getUptime()
	if seconds < 0 {
		t.Error("expected non-negative uptime seconds")
	}
	if !strings.Contains(human, "hours") || !strings.Contains(human, "minutes") {
		t.Errorf("expected uptime format with hours and minutes, got: %s", human)
	}
}

// TestGetClientIPFromXForwardedFor tests getClientIP with X-Forwarded-For header
func TestGetClientIPFromXForwardedFor(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("X-Forwarded-For", "192.168.1.1")
	
	ip := getClientIP(req)
	if ip != "192.168.1.1" {
		t.Errorf("expected 192.168.1.1, got: %s", ip)
	}
}

// TestGetClientIPFromXRealIP tests getClientIP with X-Real-IP header
func TestGetClientIPFromXRealIP(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("X-Real-IP", "10.0.0.1")
	
	ip := getClientIP(req)
	if ip != "10.0.0.1" {
		t.Errorf("expected 10.0.0.1, got: %s", ip)
	}
}

// TestGetClientIPFromRemoteAddr tests getClientIP with RemoteAddr
func TestGetClientIPFromRemoteAddr(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.RemoteAddr = "127.0.0.1:12345"
	
	ip := getClientIP(req)
	if ip != "127.0.0.1:12345" {
		t.Errorf("expected 127.0.0.1:12345, got: %s", ip)
	}
}

// TestMainHandler tests the main handler endpoint
func TestMainHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("User-Agent", "test-client/1.0")
	w := httptest.NewRecorder()

	mainHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got: %d", w.Code)
	}

	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got: %s", contentType)
	}

	var info ServiceInfo
	body, _ := io.ReadAll(w.Body)
	if err := json.Unmarshal(body, &info); err != nil {
		t.Errorf("failed to unmarshal response: %v", err)
	}

	if info.Service.Name != "devops-info-service" {
		t.Errorf("expected service name devops-info-service, got: %s", info.Service.Name)
	}

	if info.Service.Version != "1.0.0" {
		t.Errorf("expected version 1.0.0, got: %s", info.Service.Version)
	}

	if len(info.Endpoints) != 2 {
		t.Errorf("expected 2 endpoints, got: %d", len(info.Endpoints))
	}
}

// TestMainHandlerWithoutUserAgent tests main handler without User-Agent
func TestMainHandlerWithoutUserAgent(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got: %d", w.Code)
	}

	var info ServiceInfo
	body, _ := io.ReadAll(w.Body)
	if err := json.Unmarshal(body, &info); err != nil {
		t.Errorf("failed to unmarshal response: %v", err)
	}

	if info.Request.UserAgent != "" {
		t.Errorf("expected empty User-Agent, got: %s", info.Request.UserAgent)
	}
}

// TestHealthHandler tests the health check endpoint
func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got: %d", w.Code)
	}

	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got: %s", contentType)
	}

	var health HealthResponse
	body, _ := io.ReadAll(w.Body)
	if err := json.Unmarshal(body, &health); err != nil {
		t.Errorf("failed to unmarshal response: %v", err)
	}

	if health.Status != "healthy" {
		t.Errorf("expected status healthy, got: %s", health.Status)
	}

	if health.UptimeSeconds < 0 {
		t.Errorf("expected non-negative uptime, got: %d", health.UptimeSeconds)
	}
}

// TestHealthHandlerTimestamp tests that health check returns valid timestamp
func TestHealthHandlerTimestamp(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	var health HealthResponse
	body, _ := io.ReadAll(w.Body)
	json.Unmarshal(body, &health)

	_, err := time.Parse(time.RFC3339, health.Timestamp)
	if err != nil {
		t.Errorf("invalid timestamp format: %v", err)
	}
}

// TestNotFoundHandler tests the 404 handler
func TestNotFoundHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/invalid", nil)
	w := httptest.NewRecorder()

	notFoundHandler(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got: %d", w.Code)
	}

	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got: %s", contentType)
	}

	var response map[string]string
	body, _ := io.ReadAll(w.Body)
	if err := json.Unmarshal(body, &response); err != nil {
		t.Errorf("failed to unmarshal response: %v", err)
	}

	if response["error"] != "Not Found" {
		t.Errorf("expected error Not Found, got: %s", response["error"])
	}

	if response["message"] != "Endpoint does not exist" {
		t.Errorf("expected correct message, got: %s", response["message"])
	}
}

// TestMainHandlerStructure tests the structure of main handler response
func TestMainHandlerStructure(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	var info ServiceInfo
	body, _ := io.ReadAll(w.Body)
	json.Unmarshal(body, &info)

	// Test System info
	if info.System.GoVersion == "" {
		t.Error("expected non-empty Go version")
	}

	if info.System.Platform == "" {
		t.Error("expected non-empty platform")
	}

	if info.System.Architecture == "" {
		t.Error("expected non-empty architecture")
	}

	if info.System.CPUCount <= 0 {
		t.Error("expected positive CPU count")
	}

	// Test Runtime info
	if info.Runtime.Timezone != "UTC" {
		t.Errorf("expected UTC timezone, got: %s", info.Runtime.Timezone)
	}

	// Test Request info
	if info.Request.Method != "GET" {
		t.Errorf("expected GET method, got: %s", info.Request.Method)
	}

	if info.Request.Path != "/" {
		t.Errorf("expected / path, got: %s", info.Request.Path)
	}
}

// TestServiceInfoFieldsNotEmpty tests that critical fields are populated
func TestServiceInfoFieldsNotEmpty(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	var info ServiceInfo
	body, _ := io.ReadAll(w.Body)
	json.Unmarshal(body, &info)

	if info.Service.Name == "" {
		t.Error("service name should not be empty")
	}

	if info.Service.Framework == "" {
		t.Error("service framework should not be empty")
	}

	if info.System.Hostname == "" {
		t.Error("hostname should not be empty")
	}

	if info.Runtime.CurrentTime == "" {
		t.Error("current time should not be empty")
	}
}

// TestHealthHandlerConcurrent tests concurrent calls to health endpoint
func TestHealthHandlerConcurrent(t *testing.T) {
	done := make(chan bool)
	
	for i := 0; i < 10; i++ {
		go func() {
			req := httptest.NewRequest("GET", "/health", nil)
			w := httptest.NewRecorder()
			healthHandler(w, req)
			
			if w.Code != http.StatusOK {
				t.Errorf("expected status 200, got: %d", w.Code)
			}
			done <- true
		}()
	}

	for i := 0; i < 10; i++ {
		<-done
	}
}

// TestMainHandlerDifferentMethods tests main handler with different HTTP methods
func TestMainHandlerDifferentMethods(t *testing.T) {
	methods := []string{"GET", "POST", "PUT", "DELETE", "PATCH"}

	for _, method := range methods {
		req := httptest.NewRequest(method, "/", nil)
		w := httptest.NewRecorder()

		mainHandler(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("expected status 200 for %s, got: %d", method, w.Code)
		}
	}
}

// TestEndpointsListIncludesBothEndpoints tests that both endpoints are listed
func TestEndpointsListIncludesBothEndpoints(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	var info ServiceInfo
	body, _ := io.ReadAll(w.Body)
	json.Unmarshal(body, &info)

	foundRoot := false
	foundHealth := false

	for _, endpoint := range info.Endpoints {
		if endpoint.Path == "/" && endpoint.Method == "GET" {
			foundRoot = true
		}
		if endpoint.Path == "/health" && endpoint.Method == "GET" {
			foundHealth = true
		}
	}

	if !foundRoot {
		t.Error("root endpoint not found in endpoints list")
	}

	if !foundHealth {
		t.Error("health endpoint not found in endpoints list")
	}
}
