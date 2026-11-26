from django.urls import path

from . import views


app_name = "course_management"

urlpatterns = [
    path("", views.course_index, name="course_index"),
    path("lesson/<int:lesson_number>/", views.lesson_detail_view, name="lesson_detail"),
    path(
        "lesson/<int:lesson_number>/step/<int:step_number>/",
        views.step_detail_view,
        name="step_detail",
    ),
]
