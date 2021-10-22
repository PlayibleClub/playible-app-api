from django.db import models


class BaseInfo(models.Model):
  created_at = models.DateTimeField(auto_now=False, auto_now_add=True, blank=True, null=True)
  updated_at = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)

  class Meta:
      ordering = ['-updated_at', '-created_at']
      abstract = True
