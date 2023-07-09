from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.http import StreamingHttpResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from schema_graph.views import Schema
from .utils import handle_avatar_upload
from django.shortcuts import render
from authentication.forms import AvatarUploadForm


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


def some_admin_view(request):
    if request.method == "POST":
        form = AvatarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_avatar_upload(form.cleaned_data["user"], form.cleaned_data["avatar"])
            return JsonResponse({"message": "Avatar uploaded successfully"}, status=200)
        else:
            return JsonResponse({"message": "Invalid form"}, status=400)
    else:
        return JsonResponse({"message": "Not a POST request"}, status=400)
