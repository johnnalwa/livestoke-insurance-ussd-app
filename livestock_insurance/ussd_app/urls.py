from django.urls import path

from . import views  # Correct import statement

urlpatterns = [
    
    path('ussd/', views.ussd_handler, name='ussd'),
    path('', views.dashboard, name='dashboard'),

]
