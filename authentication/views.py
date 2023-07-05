from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseNotAllowed
from django.http import StreamingHttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from schema_graph.views import Schema


@staff_member_required
def update_vertrieblers(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    def stream_response():
        yield "Starting user update\n"

        # Call the command (assuming this will take a long time and we can't report progress)
        call_command("update_vertrieblers")

        yield "User update completed\n"

    response = StreamingHttpResponse(stream_response())  # type: ignore

    # These headers are needed for some browsers to handle the streaming response correctly
    response["X-Accel-Buffering"] = "no"
    response["Cache-Control"] = "no-cache"

    return response


@staff_member_required
def protected_schema_view(request):
    view = Schema.as_view()
    return view(request)


@staff_member_required
def update_elektrikers(request):
    def stream_response():
        yield "Starting user update\n"

        # Call the command (assuming this will take a long time and we can't report progress)
        call_command("update_elektrikers")

        yield "User update completed\n"

    response = StreamingHttpResponse(stream_response())  # type: ignore

    # These headers are needed for some browsers to handle the streaming response correctly
    response["X-Accel-Buffering"] = "no"
    response["Cache-Control"] = "no-cache"

    return response
