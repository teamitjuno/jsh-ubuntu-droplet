import json
from functools import wraps

from dotenv import load_dotenv
from django.db.models.functions import Cast
from django import forms
from django.db.models import IntegerField, Q
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
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
from vertrieb_interface.permissions import admin_required, AdminRequiredMixin

load_dotenv(ENV_FILE)


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


@admin_required
def user_list_view(request):
    users = User.objects.all()
    return render(request, "vertrieb/user_list.html", {"users": users})


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
        queryset = self.model.objects.filter( #type: ignore
            user=self.user, zoho_kundennumer__regex=r"^\d+$"
        )

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(zoho_kundennumer__icontains=query)
                | Q(angebot_id__icontains=query)
                | Q(status__icontains=query)
                | Q(name__icontains=query)
                | Q(anfrage_vom__icontains=query)
            )

        queryset = queryset.annotate(
            zoho_kundennumer_int=Cast("zoho_kundennumer", IntegerField())
        )
        queryset = queryset.order_by("-zoho_kundennumer_int")

        return queryset
