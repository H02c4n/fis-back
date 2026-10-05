"""Consistent JSON error envelope: {"success": false, "error": {"code", "message", "fields"?}}."""
import logging

from rest_framework import exceptions as drf
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, fields: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.status_code, self.fields = code, message, status_code, fields


def _plain(detail):
    if isinstance(detail, dict):
        return {k: _plain(v) for k, v in detail.items()}
    if isinstance(detail, (list, tuple)):
        return [_plain(v) for v in detail]
    return str(detail)


def error_response(code, message, status_code, fields=None):
    error = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return Response({"success": False, "error": error}, status=status_code)


def custom_exception_handler(exc, context):
    if isinstance(exc, ApiError):
        return error_response(exc.code, exc.message, exc.status_code, exc.fields)
    if isinstance(exc, drf.ValidationError):
        return error_response(
            "VALIDATION_ERROR", "Kontrollera de markerade fälten och försök igen.", 400, _plain(exc.detail)
        )
    if isinstance(exc, drf.Throttled):
        return error_response("RATE_LIMITED", "För många förfrågningar. Försök igen om en stund.", 429)
    if isinstance(exc, drf.NotFound):
        return error_response("NOT_FOUND", "Hittades inte.", 404)
    if isinstance(exc, drf.ParseError):
        return error_response("BAD_REQUEST", "Ogiltig förfrågan.", 400)

    response = drf_exception_handler(exc, context)
    if response is not None:
        return error_response(
            getattr(exc, "default_code", "error").upper(), str(getattr(exc, "detail", "Fel.")), response.status_code
        )
    logger.exception("Unhandled API exception", exc_info=exc)
    return error_response("INTERNAL_ERROR", "Något gick fel. Försök igen.", 500)
