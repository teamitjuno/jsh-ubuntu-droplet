from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.http import (
    HttpResponseNotAllowed,
    JsonResponse,
    StreamingHttpResponse,
    HttpResponse,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from schema_graph.views import Schema
from .utils import handle_avatar_upload
from authentication.forms import AvatarUploadForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.edit import UpdateView
from authentication.models import User
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)



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


# class UserUpdateView(LoginRequiredMixin, UpdateView):
#     model = User
#     form_class = UserForm
#     template_name = "vertrieb/user_update_form.html"

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["user"] = self.request.user
#         return kwargs

#     def get_success_url(self):
#         return reverse_lazy(
#             "user-detail", kwargs={"pk": self.object.pk}
#         )  # Assuming you have a user detail view named 'user-detail'

#     def form_valid(self, form):
#         form.save()
#         return super(UserUpdateView, self).form_valid(form)


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
@permission_required("authentication.delete_user", raise_exception=True)
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


# @staff_member_required
# def change_password(request, user_id):
#     target_user = get_object_or_404(User, pk=user_id)

#     if not request.user.role.name == "admin":
#         messages.error(request, "Only superusers can change other users' passwords.")
#         return redirect("vertrieb_interface:home")

#     if request.method == "POST":
#         form = AdminPasswordChangeForm(target_user, request.POST)
#         if form.is_valid():
#             form.save()
#             update_session_auth_hash(request, form.user)
#             messages.success(
#                 request,
#                 f"Password for user {target_user.username} changed successfully.",
#             )
#             return redirect("adminfeautures:user_list")
#     else:
#         form = AdminPasswordChangeForm(target_user)

#     return render(
#         request,
#         "vertrieb/password_change.html",
#         {"form": form, "target_user": target_user},
#     )
