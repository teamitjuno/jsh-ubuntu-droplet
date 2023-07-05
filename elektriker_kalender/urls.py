from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from elektriker_kalender import views

app_name = "elektriker_kalender"

urlpatterns = [
    path(
        "elektriker_kalender/", views.CalendarView.as_view(), name="elektriker_kalender"
    ),
    path(
        "elektriker_kalender/get_elektriker_kalender/",
        views.ElektrikerKalenderView.as_view(),
        name="get_elektriker_kalender",
    ),
    path(
        "elektriker_kalender/elektriker_kalender_list/",
        views.ViewCalendarList.as_view(),
        name="elektriker_kalender_list",
    ),
    path(
        "position/delete/<int:id>/",
        views.PositionDeleteView.as_view(),
        name="position_delete",
    ),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
