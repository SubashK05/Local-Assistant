from django.urls import path
from . import views

urlpatterns = [
    path(
        "approve/<int:action_id>/",
        views.approve_action,
        name="approve_action",
    ),
    path(
        "reject/<int:action_id>/",
        views.reject_action,
        name="reject_action",
    ),
]