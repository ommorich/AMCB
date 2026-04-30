from django.urls import path
from . import views

app_name = 'brake'

urlpatterns = [
    # Существующие маршруты
    path('', views.brake_view, name='brake_view'),
    path('form2/', views.brake_form2, name='brake_form2'),
    path('form3/', views.brake_form3, name='brake_form3'),
    path('history/', views.history_page, name='history_page'),
    path('history/<int:pk>/', views.history_detail, name='history_detail'),
    
    # API маршруты
    path('api/calculate/', views.api_calculate_rk4, name='api_calculate_rk4'),
    path('api/upload-csv/', views.api_upload_csv, name='api_upload_csv'),
    

    path(
        'api/history/save-form2/',
        views.save_form2_record,
        name='save_form2_record'
    ),

    # НОВЫЕ API маршруты для удаления
    path('api/history/<int:pk>/delete/', views.api_delete_history, name='api_delete_history'),
    path('api/history/delete-all/', views.api_delete_all_history, name='api_delete_all_history'),
]