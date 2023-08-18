from django.db import models


class VirtualJudge(models.Model):
    url = models.CharField(max_length=64, blank=True, null=True)
