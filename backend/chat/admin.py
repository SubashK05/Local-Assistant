from django.contrib import admin
from chat.models import Conversation, Message

# Register your models here.
admin.site.register(Conversation)
admin.site.register(Message)