from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'organizations'
urlpatterns = [
    path('', login_required(views.OrganizationListView.as_view()), name='list'),
    path('<int:pk>/', login_required(views.OrganizationDetailView.as_view()), name='detail'),
    path('create/', login_required(views.OrganizationCreateView.as_view()), name='create'),
]
