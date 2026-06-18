from django.db import models
from simple_history.models import HistoricalRecords
# Create your models here.


class cluster_member(models.Model):
    history = HistoricalRecords()
    hostname = models.CharField(max_length=128)
    ping = models.BooleanField(default=False)
    ssh = models.BooleanField(default=False)
    rpc = models.BooleanField(default=False)
    operating_system = models.CharField(max_length=128, default="NA")
    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.hostname)


class cluster_health(models.Model):
    ping = models.BooleanField(default=False)
    ssh = models.BooleanField(default=False)
    rpc = models.BooleanField(default=False)
    empty = models.BooleanField(default=False)
    operating_system = models.CharField(max_length=128, default="NA")
    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.hostname)
