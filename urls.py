from django.urls import path
from . import views_simple

app_name = 'licenses'

urlpatterns = [
    path('config/', views_simple.license_form_config, name='license-config'),
    path('generate/', views_simple.LicenseGenerateView.as_view(), name='license-generate'),
    path('records/', views_simple.license_records, name='license-records'),
    path('files/<path:relative_path>/', views_simple.license_file, name='license-file'),
    path('delete/<path:relative_path>/', views_simple.delete_license_file, name='license-delete'),
]
