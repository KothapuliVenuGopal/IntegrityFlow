from django.urls import path
from . import views

urlpatterns = [
    path('', views.similarity_list, name='similarity_list'),
    path('<str:report_id>/', views.similarity_detail, name='similarity_detail'),
]
