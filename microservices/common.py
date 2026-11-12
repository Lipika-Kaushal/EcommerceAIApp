import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import jsonify


class ServiceError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def database_path(service_name):
    return Path(os.environ.get("DB_PATH", f"/data/{service_name}.db"))


@contextmanager
def open_database(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def configure_api(app):
    @app.get("/health")
    def health():
        return jsonify(status="ok", service=app.name.rsplit(".", 1)[-1])

    @app.errorhandler(ServiceError)
    def service_error(error):
        return jsonify(error=error.message), error.status_code


def api_request(base_url, path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            response_body = response.read()
    except HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(message)
            message = parsed.get("error", message)
        except json.JSONDecodeError:
            pass
        raise ServiceError(message or "Upstream service rejected the request.", error.code) from error
    except URLError as error:
        raise ServiceError(f"Service is unavailable: {error.reason}") from error
    if not response_body:
        return None
    return json.loads(response_body)


def require_json_object():
    from flask import request

    payload = request.get_json(silent=False)
    if not isinstance(payload, dict):
        raise ServiceError("Expected a JSON object.", 400)
    return payload


def rows_as_dicts(rows):
    return [dict(row) for row in rows]
