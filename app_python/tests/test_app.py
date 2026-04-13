"""
Unit tests for DevOps Info Service application
Tests all endpoints and error handling
"""
import json
from datetime import datetime
import pytest
from app import (
    app,
    configure_visits_storage,
    get_system_info,
    get_uptime,
    get_visits_storage_path,
)


@pytest.fixture(autouse=True)
def isolated_visits_storage(tmp_path):
    """Use a temporary visits file for every test."""
    original_path = get_visits_storage_path()
    test_path = tmp_path / 'visits'
    configure_visits_storage(str(test_path))
    yield test_path
    configure_visits_storage(original_path)


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
        assert 'configuration' in data
        assert 'visits' in data
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
        assert 'environment' in service

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
        assert len(endpoints) >= 3

        paths = [ep['path'] for ep in endpoints]
        assert '/' in paths
        assert '/health' in paths
        assert '/visits' in paths

    def test_index_increments_visits(self, client):
        """Test that the root endpoint increments the visits counter."""
        response1 = client.get('/')
        visits1 = json.loads(response1.data)['visits']['count']

        response2 = client.get('/')
        visits2 = json.loads(response2.data)['visits']['count']

        assert visits1 == 1
        assert visits2 == 2

    def test_index_reports_config_source(self, client):
        """Test that configuration metadata is always present."""
        response = client.get('/')
        data = json.loads(response.data)

        config = data['configuration']
        assert 'file' in config
        assert 'environment_variables' in config
        assert 'feature_flags' in config
        assert 'settings' in config


class TestVisitsEndpoint:
    """Test the /visits endpoint."""

    def test_visits_status_code(self, client):
        """Test that visits endpoint returns 200 OK."""
        response = client.get('/visits')
        assert response.status_code == 200

    def test_visits_returns_zero_before_root_access(self, client):
        """Test the counter defaults to zero when the file is absent."""
        response = client.get('/visits')
        data = json.loads(response.data)

        assert data['visits'] == 0

    def test_visits_reflect_root_requests(self, client):
        """Test the visits endpoint returns the persisted count."""
        client.get('/')
        client.get('/')

        response = client.get('/visits')
        data = json.loads(response.data)

        assert data['visits'] == 2
        assert data['storage_file'].endswith('visits')

    def test_visits_file_is_persisted(self, client, isolated_visits_storage):
        """Test the visits file is written after hitting the root endpoint."""
        client.get('/')

        assert isolated_visits_storage.read_text(encoding='utf-8') == '1'


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


class TestMetricsEndpoint:
    """Test the /metrics endpoint and exported metrics."""

    def test_metrics_status_code(self, client):
        """Test that metrics endpoint returns 200 OK."""
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Test that metrics endpoint uses Prometheus text exposition."""
        response = client.get('/metrics')
        assert response.content_type.startswith('text/plain')

    def test_metrics_include_http_and_business_metrics(self, client):
        """Test that custom metrics are exported with expected labels."""
        client.get('/')
        client.get('/health')
        client.get('/visits')

        metrics_output = client.get('/metrics').get_data(as_text=True)

        assert 'http_requests_total' in metrics_output
        assert 'http_request_duration_seconds_bucket' in metrics_output
        assert 'http_requests_in_progress' in metrics_output
        assert 'devops_info_endpoint_calls_total' in metrics_output
        assert 'devops_info_system_collection_seconds_bucket' in metrics_output
        assert (
            'http_requests_total{endpoint="/",method="GET",status_code="200"}'
            in metrics_output
        )
        assert (
            'http_requests_total{endpoint="/health",method="GET",'
            'status_code="200"}'
            in metrics_output
        )
        assert (
            'http_requests_total{endpoint="/visits",method="GET",'
            'status_code="200"}'
            in metrics_output
        )
        assert (
            'devops_info_endpoint_calls_total{endpoint="/"}'
            in metrics_output
        )
        assert (
            'devops_info_endpoint_calls_total{endpoint="/health"}'
            in metrics_output
        )
        assert (
            'devops_info_endpoint_calls_total{endpoint="/visits"}'
            in metrics_output
        )


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

        client.get('/health')
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
