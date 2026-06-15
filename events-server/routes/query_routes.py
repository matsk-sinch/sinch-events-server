import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request

from storage.event_repository import EventRepository, is_mongo_unavailable

query_bp = Blueprint("query", __name__)

_event_repository: EventRepository | None = None


def init_query_routes(event_repository: EventRepository) -> None:
    global _event_repository
    _event_repository = event_repository


def _require_api_key(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        api_key = os.environ.get("QUERY_API_KEY")
        if not api_key:
            return view_func(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        expected = f"Bearer {api_key}"
        if auth_header != expected:
            return jsonify({"error": "Unauthorized"}), 401

        return view_func(*args, **kwargs)

    return wrapper


def _parse_iso_datetime(value: str, param_name: str) -> datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"Invalid {param_name} datetime: {value}") from error


@query_bp.get("/healthz")
def healthz():
    if _event_repository is None:
        return jsonify({"status": "error", "detail": "Event repository not initialized"}), 503

    try:
        _event_repository.ping()
    except Exception as error:
        if is_mongo_unavailable(error):
            return jsonify({"status": "error", "detail": "MongoDB unavailable"}), 503
        raise

    return jsonify({"status": "ok"})


@query_bp.get("/events")
@_require_api_key
def get_events_by_message_id():
    message_id = request.args.get("messageId")
    if not message_id:
        return jsonify({"error": "messageId query parameter is required"}), 400

    try:
        events = _event_repository.find_by_message_id(message_id)
    except Exception as error:
        if is_mongo_unavailable(error):
            return jsonify({"error": "MongoDB unavailable"}), 503
        raise

    return jsonify({"count": len(events), "events": events})


@query_bp.get("/events/range")
@_require_api_key
def get_events_by_date_range():
    from_value = request.args.get("from")
    to_value = request.args.get("to")

    if not from_value or not to_value:
        return jsonify({"error": "from and to query parameters are required"}), 400

    try:
        start = _parse_iso_datetime(from_value, "from")
        end = _parse_iso_datetime(to_value, "to")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if start > end:
        return jsonify({"error": "from must be before or equal to to"}), 400

    try:
        events = _event_repository.find_by_date_range(start, end)
    except Exception as error:
        if is_mongo_unavailable(error):
            return jsonify({"error": "MongoDB unavailable"}), 503
        raise

    return jsonify({"count": len(events), "events": events})
