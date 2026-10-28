from django.urls import path
from . import views

urlpatterns = [
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/<int:pk>/', views.assessment_detail, name='assessment_detail'),
    path('submissions/', views.submission_list, name='submission_list'),
    path('submissions/create/', views.submission_create, name='submission_create'),
]
