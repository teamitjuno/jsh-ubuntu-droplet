import json
from functools import wraps

from dotenv import load_dotenv

from django import forms

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.forms import RadioSelect
from django.forms.widgets import RadioSelect
from django.core.exceptions import PermissionDenied
from config.settings import ENV_FILE
from authentication.models import User
from vertrieb_interface.models import VertriebAngebot

load_dotenv(ENV_FILE)


def handler404(request, exception):
    return render(request, "404.html", status=404)


def vertrieb_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class VertriebCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return vertrieb_check(self.request.user)  # type: ignore


def admin_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role_id == 1:
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    return wrap


class UpdateAdminAngebotForm(forms.ModelForm):
    is_locked = forms.BooleanField(
        widget=RadioSelect(choices=((True, "Locked"), (False, "Unlocked")))
    )

    class Meta:
        model = VertriebAngebot
        fields = ["is_locked"]  # Only include the 'is_locked' field


class UpdateAdminAngebot(LoginRequiredMixin, UpdateView):
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


def user_list_view(request):
    users = User.objects.all()
    return render(request, "vertrieb/user_list.html", {"users": users})


class ViewAdminOrders(LoginRequiredMixin, VertriebCheckMixin, ListView):
    model = VertriebAngebot
    template_name = "vertrieb/view_orders_admin.html"
    context_object_name = "angebots"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)
