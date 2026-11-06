from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_home, name="chat_home"),
    path(
        "new/",
        views.create_conversation,
        name="create_conversation"
    ),
]