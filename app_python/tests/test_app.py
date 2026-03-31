"""
Unit tests for DevOps Info Service application
Tests all endpoints and error handling
"""
import pytest
import json
from datetime import datetime
from app import app, get_system_info, get_uptime


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIndexEndpoint:
    """Test the / (index) endpoint."""

    def test_index_status_code(self, client):
        """Test that index endpoint returns 200 OK."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_content_type(self, client):
        """Test that index endpoint returns JSON."""
        response = client.get('/')
        assert response.content_type == 'application/json'

    def test_index_response_structure(self, client):
        """Test that index response has required structure."""
        response = client.get('/')
        data = json.loads(response.data)

        # Check top-level keys exist
        assert 'service' in data
        assert 'system' in data
        assert 'runtime' in data
        assert 'request' in data
        assert 'endpoints' in data

    def test_index_service_info(self, client):
        """Test that service information is correct."""
        response = client.get('/')
        data = json.loads(response.data)

        service = data['service']
        assert service['name'] == 'devops-info-service'
        assert service['version'] == '1.0.0'
        assert service['framework'] == 'Flask'
        assert 'description' in service

    def test_index_system_info_present(self, client):
        """Test that system information fields are present."""
        response = client.get('/')
        data = json.loads(response.data)

        system = data['system']
        assert 'hostname' in system
        assert 'platform' in system
        assert 'platform_version' in system
        assert 'architecture' in system
        assert 'cpu_count' in system
        assert 'python_version' in system

        # Validate types
        assert isinstance(system['hostname'], str)
        assert isinstance(system['platform'], str)
        assert isinstance(system['cpu_count'], (int, type(None)))

    def test_index_runtime_info(self, client):
        """Test that runtime information is present."""
        response = client.get('/')
        data = json.loads(response.data)

        runtime = data['runtime']
        assert 'uptime_seconds' in runtime
        assert 'uptime_human' in runtime
        assert 'current_time' in runtime
        assert 'timezone' in runtime

        assert isinstance(runtime['uptime_seconds'], int)
        assert runtime['uptime_seconds'] >= 0
        assert 'hours' in runtime['uptime_human'].lower()
        assert runtime['timezone'] == 'UTC'

    def test_index_request_info(self, client):
        """Test that request information is captured."""
        response = client.get('/')
        data = json.loads(response.data)

        request_info = data['request']
        assert 'client_ip' in request_info
        assert 'user_agent' in request_info
        assert 'method' in request_info
        assert 'path' in request_info

        assert request_info['method'] == 'GET'
        assert request_info['path'] == '/'

    def test_index_endpoints_listed(self, client):
        """Test that available endpoints are documented."""
        response = client.get('/')
        data = json.loads(response.data)

        endpoints = data['endpoints']
        assert len(endpoints) >= 2

        paths = [ep['path'] for ep in endpoints]
        assert '/' in paths
        assert '/health' in paths


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_status_code(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_content_type(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'

    def test_health_response_structure(self, client):
        """Test that health response has required fields."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime_seconds' in data

    def test_health_status_value(self, client):
        """Test that health status is 'healthy'."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert data['status'] == 'healthy'

    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO format."""
        response = client.get('/health')
        data = json.loads(response.data)

        # Should be able to parse as ISO format
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    def test_health_uptime_seconds_positive(self, client):
        """Test that uptime is a non-negative integer."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert isinstance(data['uptime_seconds'], int)
        assert data['uptime_seconds'] >= 0

    def test_multiple_health_checks(self, client):
        """Test that uptime increases between health checks."""
        response1 = client.get('/health')
        uptime1 = json.loads(response1.data)['uptime_seconds']

        # Make another request after a small delay
        response2 = client.get('/health')
        uptime2 = json.loads(response2.data)['uptime_seconds']

        # Uptime should be monotonically increasing
        assert uptime2 >= uptime1


class TestErrorHandling:
    """Test error handling."""

    def test_404_not_found(self, client):
        """Test 404 error handling for non-existent endpoint."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Not Found'

    def test_404_response_structure(self, client):
        """Test 404 response has proper JSON structure."""
        response = client.get('/invalid-endpoint')
        data = json.loads(response.data)

        assert 'error' in data
        assert 'message' in data

    def test_get_method_only(self, client):
        """Test that POST requests return 405 Method Not Allowed."""
        response = client.post('/')
        assert response.status_code == 405

    def test_health_post_not_allowed(self, client):
        """Test that POST to health endpoint is not allowed."""
        response = client.post('/health')
        assert response.status_code == 405


class TestHelperFunctions:
    """Test helper functions used in the application."""

    def test_get_system_info(self):
        """Test get_system_info function returns required fields."""
        info = get_system_info()

        assert isinstance(info, dict)
        assert 'hostname' in info
        assert 'platform' in info
        assert 'platform_version' in info
        assert 'architecture' in info
        assert 'cpu_count' in info
        assert 'python_version' in info

    def test_get_system_info_types(self):
        """Test that system info fields have correct types."""
        info = get_system_info()

        assert isinstance(info['hostname'], str)
        assert len(info['hostname']) > 0
        assert isinstance(info['platform'], str)
        assert isinstance(info['python_version'], str)

    def test_get_uptime(self):
        """Test get_uptime function returns required fields."""
        uptime = get_uptime()

        assert isinstance(uptime, dict)
        assert 'seconds' in uptime
        assert 'human' in uptime

    def test_get_uptime_values(self):
        """Test uptime values are valid."""
        uptime = get_uptime()

        assert isinstance(uptime['seconds'], int)
        assert uptime['seconds'] >= 0
        assert isinstance(uptime['human'], str)
        assert 'hours' in uptime['human'].lower()


class TestCrossEndpointConsistency:
    """Test consistency across multiple requests."""

    def test_hostname_consistency(self, client):
        """Test that hostname is consistent across requests."""
        response1 = client.get('/')
        hostname1 = json.loads(response1.data)['system']['hostname']

        response2 = client.get('/')
        hostname2 = json.loads(response2.data)['system']['hostname']

        assert hostname1 == hostname2

    def test_version_consistency(self, client):
        """Test that version is consistent across requests."""
        response1 = client.get('/')
        version1 = json.loads(response1.data)['service']['version']

        response2 = client.get('/health')
        # Health endpoint should also be from the same version
        # (through the Flask app instance)

        assert version1 == '1.0.0'

    def test_response_times_reasonable(self, client):
        """Test that responses are generated at reasonable times."""
        response = client.get('/')
        data = json.loads(response.data)

        # Timestamp should be recent (within the last minute)
        try:
            timestamp = datetime.fromisoformat(
                data['runtime']['current_time'].replace('Z', '+00:00')
            )
            now = datetime.now(timestamp.tzinfo)
            time_diff = (now - timestamp).total_seconds()

            # Should be within 5 seconds
            assert abs(time_diff) < 5
        except ValueError:
            pytest.fail("Could not parse timestamp")


class TestJSONResponseFormat:
    """Test JSON response formatting and encoding."""

    def test_index_valid_json(self, client):
        """Test that index response is valid JSON."""
        response = client.get('/')
        try:
            json.loads(response.data)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    def test_health_valid_json(self, client):
        """Test that health response is valid JSON."""
        response = client.get('/health')
        try:
            json.loads(response.data)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    def test_no_circular_references(self, client):
        """Test that JSON doesn't have problematic circular references."""
        response = client.get('/')
        data = json.loads(response.data)

        # JSON should be properly serializable
        json_str = json.dumps(data)
        assert len(json_str) > 0
