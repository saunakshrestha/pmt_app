from ninja.responses import Response
from starlette.status import HTTP_200_OK

def api_response(
    data=None,
    message=None,
    success=True,
    status_code=HTTP_200_OK,
    error=None,
    meta=None
):
    response_data = {}
    if data is not None:
        response_data["data"] = data
    if message is not None:
        response_data["message"] = message
    if error is not None:
        response_data["error"] = error
    if meta is not None:
        response_data["meta"] = meta

    return Response(
        {
            "success": success,
            **response_data
        },
        status=status_code
    )
