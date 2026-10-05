from rest_framework.response import Response


def ok(data=None, status=200, cache_seconds: int | None = None) -> Response:
    response = Response({"success": True, "data": data if data is not None else {}}, status=status)
    if cache_seconds:
        response["Cache-Control"] = f"public, max-age={cache_seconds}"
    return response
