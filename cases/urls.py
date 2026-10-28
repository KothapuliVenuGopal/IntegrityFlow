from django.urls import path
from . import views

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('<str:case_id>/', views.case_detail, name='case_detail'),
    path('<str:case_id>/assign/', views.assign_reviewer, name='assign_reviewer'),
    path('<str:case_id>/decision/', views.record_decision, name='record_decision'),
    path('<str:case_id>/appeal/', views.submit_appeal, name='submit_appeal'),
]
