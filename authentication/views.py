# Django Core and Component Imports:
from django.core.management import call_command
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import (
    HttpResponseNotAllowed,
    JsonResponse,
    StreamingHttpResponse,
    HttpResponse,
)
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

# App-specific Imports:
from schema_graph.views import Schema
from .utils import handle_avatar_upload
from authentication.forms import AvatarUploadForm
from authentication.models import User


@staff_member_required
def update_vertrieblers(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    def stream_response():
        yield "Starting user update\n"
        call_command("update_vertrieblers")
        yield "User update completed\n"

    response = StreamingHttpResponse(stream_response())
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

        call_command("update_elektrikers")

        yield "User update completed\n"

    response = StreamingHttpResponse(stream_response())
    response["X-Accel-Buffering"] = "no"
    response["Cache-Control"] = "no-cache"

    return response


@staff_member_required
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


@require_POST
def delete_user_view(request):
    user_id = request.POST.get("user_id")

    try:
        user = User.objects.get(pk=user_id)
        user.delete()
        messages.success(request, "User deleted successfully.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")

    return redirect("adminfeautures:user_list")


@login_required
@permission_required("delete_user", raise_exception=True)
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if user != request.user:
            user.delete()
            messages.success(request, "User deleted successfully.")
            return redirect("adminfeautures:user_list")
        else:
            messages.error(request, "You cannot delete your own account!")

    return redirect("adminfeautures:user_list")


def zoho_callback(request):
    auth_code = request.GET.get("code", None)

    if not auth_code:
        return HttpResponse("Authorization code not found.", status=400)

    return HttpResponse(f"Received authorization code: {auth_code}")
