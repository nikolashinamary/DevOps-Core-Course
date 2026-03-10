"""
DevOps Info Service
Main application module
"""
import json
import os
import socket
import platform
import logging
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, request


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
            'user_agent', 'duration_ms', 'host', 'port', 'debug'
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
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time
START_TIME = datetime.now(timezone.utc)


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


@app.before_request
def log_request_started():
    """Log every incoming HTTP request."""
    request.environ['request_start_ts'] = time.perf_counter()
    logger.info('request_started', extra=request_context())


@app.after_request
def log_request_finished(response):
    """Log response metadata for every completed HTTP request."""
    started = request.environ.get('request_start_ts', time.perf_counter())
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
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


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    system_info = get_system_info()

    response_data = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
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
        'endpoints': [
            {'path': '/', 'method': 'GET',
             'description': 'Service information'},
            {'path': '/health', 'method': 'GET',
             'description': 'Health check'}
        ]
    }

    return jsonify(response_data)


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    uptime = get_uptime()

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })


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
