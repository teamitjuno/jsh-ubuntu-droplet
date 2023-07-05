from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from authentication.models import User
from django.views.generic import DetailView, ListView
from django.views import View
from django.http import JsonResponse
from django.shortcuts import redirect, render
from elektriker_kalender.forms import PositionForm
from elektriker_kalender.models import ElectricCalendar, Position
from django.shortcuts import get_object_or_404
from authentication.models import User
from authentication.fetch_elektrikers import (
    fetch_all_elektrik_angebots,
    extract_ids,
    fetch_all_detailed_elektrik_records,
)
from dotenv import load_dotenv
from elektriker_kalender.utils import create_instances
from config.settings import ENV_FILE

load_dotenv(ENV_FILE)


def filter_data_by_elektriker_id(json_data, elektriker_id):
    filtered_data = []
    for item in json_data:
        elektriker = item["data"]["Elektriker"]
        if elektriker["ID"] == elektriker_id:
            filtered_data.append(item)
    return filtered_data


class ElektrikerKalenderView(LoginRequiredMixin, View):
    def get_elektriker_kalender(self, request):
        print("Starting elektriker kalender update...")
        elektriker = request.user
        data = fetch_all_elektrik_angebots()
        ids = extract_ids(data)
        fetched_records = fetch_all_detailed_elektrik_records(ids)
        print(fetched_records)
        print(elektriker.zoho_id)
        elektriker_id = str(elektriker.zoho_id)
        filtered_data_by_id = filter_data_by_elektriker_id(
            fetched_records, elektriker_id
        )
        print(filtered_data_by_id)
        print(type(filtered_data_by_id))
        return filtered_data_by_id

    def get(self, request, *args, **kwargs):
        kalender_user_data = self.get_elektriker_kalender(request)
        user = request.user
        kurz = user.kuerzel
        create_instances(kalender_user_data, kurz)
        return render(request, "elektriker_kalender_list.html")
        # return JsonResponse(
        #     {"status": "success", "elektriker_kaleder": kalender_user_data}
        # )


def elektriker_check(user):
    return User.objects.filter(id=user.id, beruf="Elektriker").exists()


def verkaufer_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class ElektrikerCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return elektriker_check(self.request.user)  # type: ignore


class CalendarView(LoginRequiredMixin, DetailView):
    model = ElectricCalendar
    template_name = "elektriker_kalender.html"
    context_object_name = "elektriker_kalender"

    def get_object(self, queryset=None):
        return get_object_or_404(ElectricCalendar, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["elektriker_kalender"] = ElectricCalendar.objects.get(
            user=self.request.user
        )
        # context["kundendata_objects"] = KundenData.objects.filter(calendar=self.object)
        context["position_form"] = PositionForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        kundendata_id = request.POST.get("kundendata")
        # kundendata = get_object_or_404(KundenData, id=kundendata_id)
        position_form = PositionForm(request.POST)

        if position_form.is_valid():
            position = position_form.save(commit=False)
            # position.kunde = kundendata
            position.save()
            return redirect("calendar")

        return self.render_to_response(
            self.get_context_data(
                position_form=position_form,
            )
        )


class ViewCalendarList(ElektrikerCheckMixin, ListView):
    model = ElectricCalendar
    template_name = "elektriker_kalender_list.html"
    context_object_name = "elektriker_kalenders"


class PositionDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        position = get_object_or_404(Position, id=kwargs.get("id"))
        position.delete()
        return redirect("calendar")
