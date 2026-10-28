from django.urls import path
from . import views

urlpatterns = [
    path('', views.evidence_list, name='evidence_list'),
    path('<str:evidence_id>/', views.evidence_detail, name='evidence_detail'),
]
