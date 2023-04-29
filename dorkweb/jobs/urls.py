from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'jobs'
urlpatterns = [
    path('', login_required(views.JobListView.as_view()), name='list'),
    path('<int:pk>/', login_required(views.JobDetailView.as_view()), name='detail'),
    path('create/', login_required(views.JobCreateView.as_view()), name='create'),
    path('ajax/load-domains/', login_required(views.load_domains), name='ajax_load_domains'),
]
