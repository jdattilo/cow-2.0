from django.db import models
from simple_history.models import HistoricalRecords
# Create your models here.


class BAMBOOINSTALL(models.Model):
    history = HistoricalRecords()
    jarfile = models.CharField(max_length=128)
    bamboohost = models.CharField(max_length=128)
    crontab = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)
    running = models.BooleanField(default=False)
    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")

    def __str__(self):              # __unicode__ on Python 2
        return str(self.jarfile)
