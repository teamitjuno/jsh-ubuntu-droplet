import json
from prices.models import SolarModulePreise
from functools import wraps
from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth, Coalesce
import calendar
from dotenv import load_dotenv
from django.db.models.functions import Cast
from django import forms
from prices.models import (
    ElektrikPreis,
    ModuleGarantiePreise,
    ModulePreise,
    WallBoxPreise,
    OptionalAccessoriesPreise,
    AndereKonfigurationWerte,
)
from django.contrib.admin.views.decorators import staff_member_required
from authentication.forms import AvatarUploadForm
from prices.forms import (
    SolarModulePreiseForm,
    WallBoxPreiseForm,
    OptionalAccessoriesPreiseForm,
    AndereKonfigurationWerteForm,
)
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
import logging
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test, login_required
from authentication.utils import handle_avatar_upload
from django.db.models import IntegerField, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, UpdateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.forms import RadioSelect
from django.forms.widgets import RadioSelect
from django.core.exceptions import PermissionDenied
from config.settings import ENV_FILE
from authentication.models import User
from vertrieb_interface.models import VertriebAngebot
from vertrieb_interface.permissions import admin_required, AdminRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from adminfeautures.forms import UserForm
from authentication.forms import TopVerkauferContainerViewForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.edit import UpdateView
from adminfeautures.forms import AdminPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.decorators import method_decorator
from functools import wraps
from django.contrib import auth
load_dotenv(ENV_FILE)

def _user_has_perm(user, perm, obj=None):
    """
    A backend can raise `PermissionDenied` to short-circuit permission checking.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, "has_perm"):
            continue
        try:
            if backend.has_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False
    return False
def handler404(request, exception):
    return render(request, "404.html", status=404)


def vertrieb_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class VertriebCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return vertrieb_check(self.request.user)  # type: ignore


class UpdateAdminAngebotForm(forms.ModelForm):
    is_locked = forms.BooleanField(
        widget=RadioSelect(choices=((True, "Locked"), (False, "Unlocked")))
    )

    class Meta:
        model = VertriebAngebot
        fields = ["is_locked"]  # Only include the 'is_locked' field

class UserUpdateSuccessUrlMixin:
    def get_success_url(self):
        return reverse_lazy("adminfeautures:user-edit", kwargs={"pk": self.object.pk})

class TopVerkauferContainerUpdateView(LoginRequiredMixin, UserUpdateSuccessUrlMixin, UpdateView):
    model = User
    form_class = TopVerkauferContainerViewForm
    template_name = "vertrieb/user_update_form.html"

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        form.save()
        return super().form_valid(form)

class UpdateAdminAngebot(AdminRequiredMixin, UpdateView):
    model = VertriebAngebot
    form_class = UpdateAdminAngebotForm
    template_name = "vertrieb/view_orders_admin.html"
    context_object_name = "vertrieb_angebot"

    def get_object(self, queryset=None):
        user_id = self.kwargs.get("user_id")
        angebot_id = self.kwargs.get("angebot_id")
        return get_object_or_404(self.model, user__id=user_id, angebot_id=angebot_id)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            angebot_id = data.get("angebot_id")
            is_locked = data.get("is_locked")
        except (ValueError, KeyError) as e:
            return HttpResponseBadRequest("Invalid request: {}".format(e))

        vertrieb_angebot = self.get_object(angebot_id)
        vertrieb_angebot.is_locked = is_locked  # type: ignore
        vertrieb_angebot.save()

        return JsonResponse({"message": "Data saved successfully!"})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Data saved successfully!")
        return response

@login_required    
def avatar_upload_form(request, user_id):
    # Removed unused user query.
    profile = User.objects.get(id=user_id)
    
    form = AvatarUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        return JsonResponse({"message": "Invalid form"}, status=HttpResponseBadRequest.status_code)
    
    avatar_file = form.cleaned_data.get("avatar")
    
    if not avatar_file:
        return JsonResponse({"message": "No file uploaded"}, status=HttpResponseBadRequest.status_code)
    
    try:
        handle_avatar_upload(profile, avatar_file)
    except Exception as e:
        logging.error(f"Error uploading avatar: {e}")
        return JsonResponse({"message": "Error processing the uploaded file."}, status=HttpResponseServerError.status_code)
    
    return JsonResponse({"message": "Avatar uploaded successfully."})

    
def user_list_view(request):
    users = User.objects.all()
    solar_module_names = [module.name for module in SolarModulePreise.objects.all()]

    monthly_sold_solar_modules = (
        VertriebAngebot.objects.filter(
            status="angenommen", solar_module__in=solar_module_names
        )
        .annotate(month=ExtractMonth("current_date"), year=ExtractYear("current_date"))
        .values("month", "year", "solar_module")
        .annotate(
            total_sold=Coalesce(Sum("modulanzahl") + Sum("modul_anzahl_ticket"), 0)
        )
        .order_by("year", "month", "solar_module")
    )

    # Initialize the dictionaries for each solar_module.
    modules_data = {name: {i: 0 for i in range(1, 13)} for name in solar_module_names}

    # Iterate over the query result to populate the dictionaries.
    for entry in monthly_sold_solar_modules:
        month = entry["month"]
        solar_module = entry["solar_module"]
        total_sold = entry["total_sold"]
        modules_data[solar_module][month] += total_sold

    # Getting all the instances of your models
    elektrik_preis = ElektrikPreis.objects.all()
    module_garantie_preise = ModuleGarantiePreise.objects.all()
    module_preise = ModulePreise.objects.all()
    solar_module_preise = SolarModulePreise.objects.all()
    wall_box_preise = WallBoxPreise.objects.all()
    optional_accessories_preise = OptionalAccessoriesPreise.objects.all()
    andere_konfiguration_werte = AndereKonfigurationWerte.objects.all()

    # Include the dictionaries and models instances in the context.
    context = {
        "users": users,
        "modules_data": modules_data,
        "solar_module_names": solar_module_names,
        "elektrik_preis": elektrik_preis,
        "module_garantie_preise": module_garantie_preise,
        "module_preise": module_preise,
        "solar_module_preise": solar_module_preise,
        "wall_box_preise": wall_box_preise,
        "optional_accessories_preise": optional_accessories_preise,
        "andere_konfiguration_werte": andere_konfiguration_werte,
    }

    return render(request, "vertrieb/user_list.html", context)


def update_solar_module_preise_view(request, module_id):
    module = get_object_or_404(SolarModulePreise, id=module_id)
    if request.method == "POST":
        form = SolarModulePreiseForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            return redirect("adminfeautures:user_list")
    else:
        form = SolarModulePreiseForm(instance=module)
    context = {
        "form": form,
        "module": module,
    }
    return render(request, "vertrieb/update_solar_module_preise.html", context)


def update_wallbox_preise_view(request, wallbox_id):
    wallbox = get_object_or_404(WallBoxPreise, id=wallbox_id)
    if request.method == "POST":
        form = WallBoxPreiseForm(request.POST, instance=wallbox)
        if form.is_valid():
            form.save()
            return redirect("adminfeautures:user_list")
    else:
        form = WallBoxPreiseForm(instance=wallbox)
    context = {
        "form": form,
        "wallbox": wallbox,
    }
    return render(request, "vertrieb/update_wallbox_preise.html", context)


def update_optional_accessories_preise_view(request, accessories_id):
    accessories = get_object_or_404(OptionalAccessoriesPreise, id=accessories_id)
    if request.method == "POST":
        form = OptionalAccessoriesPreiseForm(request.POST, instance=accessories)
        if form.is_valid():
            form.save()
            return redirect("adminfeautures:user_list")
    else:
        form = OptionalAccessoriesPreiseForm(instance=accessories)
    context = {
        "form": form,
        "accessories": accessories,
    }
    return render(request, "vertrieb/update_optional_accessories_preise.html", context)


def update_andere_konfiguration_werte_view(request, andere_konfiguration_id):
    andere_konfiguration = get_object_or_404(
        AndereKonfigurationWerte, id=andere_konfiguration_id
    )
    if request.method == "POST":
        form = AndereKonfigurationWerteForm(request.POST, instance=andere_konfiguration)
        if form.is_valid():
            form.save()
            return redirect("adminfeautures:user_list")
    else:
        form = AndereKonfigurationWerteForm(instance=andere_konfiguration)
    context = {
        "form": form,
        "andere_konfiguration": andere_konfiguration,
    }
    return render(request, "vertrieb/update_andere_konfiguration_werte.html", context)


class ViewAdminOrders(AdminRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/view_orders_admin.html"
    context_object_name = "angebots"


    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied()
        self.user = get_object_or_404(User, pk=kwargs["user_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.model.objects.filter(user=self.user)  # type: ignore
        return queryset

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "vertrieb/user_update_form.html"

    def get_object(self, queryset=None):
        user_id = self.kwargs.get('pk')
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404("User not found")

    def post(self, request, *args, **kwargs):
        # Check if it's a delete request
        if 'delete_user' in request.POST:
            user = self.get_object()
            if user != request.user:
                user.delete()
                return redirect("vertrieb_interface:home")
            else:
                logging.error("You cannot delete your own account!")
                return redirect("adminfeautures:user_list")
        
        # Otherwise, continue as usual
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        form.save()
        print(self.object)
        return super(UserUpdateView, self).form_valid(form)

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.get_object()
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "adminfeautures:user-edit", kwargs={"pk": self.object.pk}
        )

# @method_decorator(csrf_protect, name="dispatch")
# class PasswordUpdateView(LoginRequiredMixin, UserUpdateSuccessUrlMixin, UpdateView):
#     model = User
#     form_class = AdminPasswordChangeForm
#     template_name = "vertrieb/password_change.html"

#     def get_form(self, form_class=None):
#         if form_class is None:
#             form_class = self.get_form_class()
        
#         # Get the default form kwargs
#         kwargs = self.get_form_kwargs()
        
#         # Explicitly set the 'user' key in the kwargs dictionary
#         kwargs["user"] = self.get_object()
        
#         return form_class(**kwargs)

#     def get_form_kwargs(self):
#         """
#         Returns the keyword arguments for instantiating the form.
#         """
#         kwargs = super(PasswordUpdateView, self).get_form_kwargs()
#         # Explicitly set the 'user' key in the kwargs dictionary
#         kwargs["user"] = self.get_object()
#         # Remove the 'instance' key which is not expected by PasswordChangeForm
#         kwargs.pop('instance', None)
#         return kwargs

#     def form_valid(self, form):
#         """
#         If the form is valid, change the user's password.
#         """
#         form.save()  # This calls AdminPasswordChangeForm's save method, which changes the password correctly.
        
#         response = super().form_valid(form)
#         messages.success(self.request, "Data saved successfully!")
#         return response
    
#     def form_invalid(self, form):
        
#         print("Form errors:", form.errors)
#         return super().form_invalid(form)def role_based_permission_required(perm):
def user_has_permission(request, perm_name):
    user = request.user
    if _user_has_perm(request.user, "auth.change_user"):
        logging.error(f"{user.username} has direct permission: {perm_name}")
        return True
    else:
        logging.error(f"{user.username} does not have direct permission: {perm_name}")

    if user.role and user.role.permissions.filter(codename=perm_name).exists():
        logging.error(f"{user.username}'s role ({user.role.name}) has permission: {perm_name}")
        return True
    else:
        if user.role:
            logging.error(f"{user.username}'s role ({user.role.name}) does not have permission: {perm_name}")
        else:
            logging.error(f"{user.username} does not have an associated role.")
    return False

def role_based_permission_required(perm):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if user_has_permission(request, perm):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Permission denied")
        return _wrapped_view
    return decorator

@method_decorator(csrf_protect, name="dispatch")
@method_decorator(login_required, name="dispatch")
@method_decorator(role_based_permission_required('change_user'), name="dispatch")
class PasswordUpdateView(UserUpdateSuccessUrlMixin, UpdateView):
    model = User
    form_class = AdminPasswordChangeForm
    template_name = "vertrieb/password_change.html"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        kwargs = self.get_form_kwargs()
        kwargs["user"] = self.get_object()
        return form_class(**kwargs)

    def get_form_kwargs(self):
        kwargs = super(PasswordUpdateView, self).get_form_kwargs()
        kwargs["user"] = self.get_object()
        kwargs.pop('instance', None)
        return kwargs

    def form_valid(self, form):

        user = self.get_object()
        form.save()
        logging.error(f"User ID: {user.id}, Password: {user.password}")
        new_password = form.cleaned_data.get("password")
        logging.error(f"User ID: {user.id}, Password: {new_password}")

        # Update the session auth hash if the user changes their own password
    
        update_session_auth_hash(self.request, user)

        logging.error("Password changed successfully!")
        logging.error(f"User ID: {user.id}, Password: {user.password}")

        return redirect('authentication:login')

    def form_invalid(self, form):
        logging.error("Form errors:", form.errors)
        return super().form_invalid(form)
# @staff_member_required
# def change_password(request, user_id):
#     target_user = get_object_or_404(User, pk=user_id)

#     if request.method == "POST":
#         form = AdminPasswordChangeForm(target_user, request.POST)
#         if form.is_valid():
#             form.save()
#             update_session_auth_hash(request, form.user)  # Assuming the form has an attribute 'user'
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

@require_POST
def delete_user(request, pk):
    user_id = request.POST.get("user_id")

    try:
        user = User.objects.get(pk=user_id)
        user.delete()
        logging.error("User deleted successfully.")
    except User.DoesNotExist:
        logging.error("User not found.")

    return redirect("adminfeautures:user_list")


class DeleteAngebot(DeleteView):
    model = VertriebAngebot
    template_name = "view_admin_orders.html"

    def get_success_url(self):
        return reverse(
            "adminfeautures:user_list",
        )

    def get_object(self, queryset=None):
        return VertriebAngebot.objects.get(angebot_id=self.kwargs["angebot_id"])

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return response
