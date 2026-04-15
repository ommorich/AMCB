from django.urls import path
from . import views

app_name = "brake"

urlpatterns = [
    path("", views.brake_view, name="brake_view"),
    path("form2/", views.brake_form2, name="brake_form2"),
    path("form3/", views.brake_form3, name="brake_form3"),

    path("api/calculate/", views.api_calculate_rk4, name="api_calculate_rk4"),
    path("api/upload-csv/", views.api_upload_csv, name="api_upload_csv"),

    path("history/", views.history_page, name="history_page"),
    path("history/<int:pk>/", views.history_detail, name="history_detail"),
]