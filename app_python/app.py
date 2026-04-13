"""
DevOps Info Service
Main application module
"""
import fcntl
import json
import os
import socket
import platform
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from flask import Flask, Response, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for easy parsing in Loki."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        context_keys = (
            'method', 'path', 'status_code', 'client_ip',
            'user_agent', 'duration_ms', 'host', 'port', 'debug',
            'config_file', 'visits_file', 'count'
        )
        for key in context_keys:
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging():
    """Configure root logger to write JSON logs to stdout."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


configure_logging()
logger = logging.getLogger('devops-info-service')

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
CONFIG_FILE = os.getenv('CONFIG_FILE', '/config/config.json')
DEFAULT_VISITS_FILE = os.path.join(BASE_DIR, 'data', 'visits')
VISITS_FILE = os.getenv('VISITS_FILE', DEFAULT_VISITS_FILE)

# Application start time
START_TIME = datetime.now(timezone.utc)

# HTTP metrics following the RED method.
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests processed by the Flask app.',
    ['method', 'endpoint', 'status_code']
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds.',
    ['method', 'endpoint']
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed.'
)

# Application-specific metrics for the DevOps info service.
DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    'devops_info_endpoint_calls_total',
    'Total endpoint calls for the DevOps info service.',
    ['endpoint']
)
DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information.'
)


def parse_bool(value, default=False):
    """Parse a boolean-like string value."""
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


class VisitCounter:
    """Persist visits count in a file guarded by an advisory lock."""

    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._startup_count = self.get_count()

    @property
    def path(self):
        """Return the storage path for the visits counter."""
        return self._path

    @property
    def startup_count(self):
        """Return the count observed when storage was initialized."""
        return self._startup_count

    def set_storage_path(self, path):
        """Switch counter storage to a different file."""
        self._path = os.path.abspath(path)
        self._startup_count = self.get_count()

    def get_count(self):
        """Read the current visits count from the storage file."""
        with self._locked_file() as handle:
            return self._read_count(handle)

    def increment(self):
        """Atomically increment the visits count and persist it."""
        with self._locked_file() as handle:
            count = self._read_count(handle) + 1
            handle.seek(0)
            handle.truncate()
            handle.write(str(count))
            handle.flush()
            os.fsync(handle.fileno())
            return count

    @contextmanager
    def _locked_file(self):
        self._ensure_parent_dir()
        with open(self._path, 'a+', encoding='utf-8') as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.seek(0)
                yield handle
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _ensure_parent_dir(self):
        parent_dir = os.path.dirname(self._path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    def _read_count(self, handle):
        handle.seek(0)
        raw_count = handle.read().strip()
        if not raw_count:
            return 0

        try:
            return int(raw_count)
        except ValueError:
            logger.warning('visits_counter_invalid_value', extra={
                'visits_file': self._path
            })
            return 0


def configure_visits_storage(path):
    """Allow tests and local tooling to change visits storage path."""
    visits_counter.set_storage_path(path)


def get_visits_storage_path():
    """Return the active visits storage path."""
    return visits_counter.path


def default_app_config():
    """Return the baseline application configuration."""
    return {
        'application': {
            'name': os.getenv('APP_NAME', 'devops-info-service'),
            'description': 'DevOps course info service',
            'environment': os.getenv(
                'APP_DEPLOY_ENV',
                os.getenv('APP_ENV', 'development')
            )
        },
        'featureFlags': {
            'visitsCounter': parse_bool(
                os.getenv('APP_FEATURE_VISITS', 'true'),
                True
            ),
            'prometheusMetrics': True,
            'configHotReload': True
        },
        'settings': {
            'logLevel': os.getenv('APP_LOG_LEVEL', 'INFO'),
            'responseFormat': 'json',
            'reloadStrategy': os.getenv(
                'APP_CONFIG_RELOAD_STRATEGY',
                'read-per-request'
            )
        }
    }


def merge_dicts(target, override):
    """Recursively merge override values into the target mapping."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_dicts(target[key], value)
        else:
            target[key] = value
    return target


def load_runtime_config():
    """Load the JSON config file on demand to support hot reload."""
    config = default_app_config()
    source = {
        'path': CONFIG_FILE,
        'loaded': False
    }

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as handle:
            file_config = json.load(handle)
        merge_dicts(config, file_config)
        source['loaded'] = True
    except FileNotFoundError:
        source['error'] = 'not-found'
    except json.JSONDecodeError:
        source['error'] = 'invalid-json'
        logger.warning('config_file_invalid_json', extra={
            'config_file': CONFIG_FILE
        })
    except OSError:
        source['error'] = 'read-error'
        logger.warning('config_file_read_failed', extra={
            'config_file': CONFIG_FILE
        })

    config['source'] = source
    config['env'] = {
        'APP_NAME': os.getenv('APP_NAME', config['application']['name']),
        'APP_DEPLOY_ENV': os.getenv(
            'APP_DEPLOY_ENV',
            config['application']['environment']
        ),
        'APP_LOG_LEVEL': os.getenv(
            'APP_LOG_LEVEL',
            config['settings']['logLevel']
        ),
        'APP_FEATURE_VISITS': os.getenv(
            'APP_FEATURE_VISITS',
            str(config['featureFlags']['visitsCounter']).lower()
        ),
        'APP_CONFIG_RELOAD_STRATEGY': os.getenv(
            'APP_CONFIG_RELOAD_STRATEGY',
            config['settings']['reloadStrategy']
        )
    }
    return config


def normalize_endpoint():
    """Return a low-cardinality endpoint label for metrics."""
    if request.url_rule is not None:
        return request.url_rule.rule
    return 'unmatched'


def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def request_context():
    """Return request context fields used in structured logs."""
    return {
        'method': request.method,
        'path': request.path,
        'client_ip': request.remote_addr or '127.0.0.1',
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }


visits_counter = VisitCounter(VISITS_FILE)
logger.info('visits_counter_loaded', extra={
    'visits_file': visits_counter.path,
    'count': visits_counter.startup_count
})


@app.before_request
def log_request_started():
    """Log every incoming HTTP request."""
    request.environ['request_start_ts'] = time.perf_counter()
    request.environ['request_endpoint'] = normalize_endpoint()
    request.environ['request_in_progress_tracked'] = True
    HTTP_REQUESTS_IN_PROGRESS.inc()
    logger.info('request_started', extra=request_context())


@app.after_request
def log_request_finished(response):
    """Log response metadata for every completed HTTP request."""
    started = request.environ.get('request_start_ts', time.perf_counter())
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    endpoint = request.environ.get('request_endpoint', normalize_endpoint())

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code)
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(max(duration_ms / 1000, 0))

    context = request_context()
    context.update({
        'status_code': response.status_code,
        'duration_ms': duration_ms
    })

    if response.status_code >= 500:
        logger.error('request_finished', extra=context)
    elif response.status_code >= 400:
        logger.warning('request_finished', extra=context)
    else:
        logger.info('request_finished', extra=context)

    return response


@app.teardown_request
def track_request_finished(_error):
    """Ensure the in-progress gauge is decremented for every request path."""
    if request.environ.pop('request_in_progress_tracked', False):
        HTTP_REQUESTS_IN_PROGRESS.dec()


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    runtime_config = load_runtime_config()
    current_visits = visits_counter.increment()
    app_config = runtime_config['application']
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/').inc()
    with DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.time():
        system_info = get_system_info()

    response_data = {
        'service': {
            'name': app_config['name'],
            'version': '1.0.0',
            'description': app_config['description'],
            'framework': 'Flask',
            'environment': app_config['environment']
        },
        'system': system_info,
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': {
            'client_ip': request.remote_addr or '127.0.0.1',
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'method': request.method,
            'path': request.path
        },
        'configuration': {
            'file': runtime_config['source'],
            'environment_variables': runtime_config['env'],
            'feature_flags': runtime_config['featureFlags'],
            'settings': runtime_config['settings']
        },
        'visits': {
            'count': current_visits,
            'storage_file': visits_counter.path
        },
        'endpoints': [
            {'path': '/', 'method': 'GET',
             'description': 'Service information'},
            {'path': '/health', 'method': 'GET',
             'description': 'Health check'},
            {'path': '/visits', 'method': 'GET',
             'description': 'Current persisted visits count'},
            {'path': '/metrics', 'method': 'GET',
             'description': 'Prometheus metrics endpoint'}
        ]
    }

    return jsonify(response_data)


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    uptime = get_uptime()
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/health').inc()

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })


@app.route('/visits')
def visits():
    """Return the current persisted visits count."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/visits').inc()
    return jsonify({
        'visits': visits_counter.get_count(),
        'storage_file': visits_counter.path
    })


@app.route('/metrics')
def metrics():
    """Expose Prometheus metrics for scraping."""
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning('route_not_found', extra={
        **request_context(),
        'status_code': 404
    })
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.exception('internal_server_error', extra={
        **request_context(),
        'status_code': 500
    })
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info('application_starting', extra={
        'host': HOST,
        'port': PORT,
        'debug': DEBUG
    })
    app.run(host=HOST, port=PORT, debug=DEBUG)
