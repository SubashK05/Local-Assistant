from django.db import models


class PendingAction(models.Model):
    tool_name = models.CharField(max_length=100)
    arguments = models.JSONField()
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    executed = models.BooleanField(default=False)
    result = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.tool_name} - {self.id}"
