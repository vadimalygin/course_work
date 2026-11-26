from . import views
from django.urls import path

app_name = 'homepage'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
]
