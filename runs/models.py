import datetime
from django.utils import timezone
from django.db import models
from simple_history.models import HistoricalRecords
import socket
# Create your models here.


class Run(models.Model):
    history = HistoricalRecords()
    builder = models.CharField(
        max_length=512,
        blank=True,
        default=socket.gethostname())
    # run information
    build_number = models.IntegerField()
    commit = models.IntegerField()
    suite_file = models.CharField(max_length=512)
    env_file = models.CharField(max_length=512)

    parent_branch = models.CharField(max_length=512)

    operating_system = models.CharField(max_length=128)
    log_file = models.URLField(blank=True)

    RUN_PF_CHOICES = (
        (1, 'PASS'),
        (2, 'PASS OVERRIDE'),
        (0, 'FAIL'),
        (11, 'INTERRUPTED'),
        (12, 'INVALID'),
        (13, 'IN PROGRESS'),
        (60, 'FAIL OVERRIDE'),
        (65, 'UNDER INVESTIGATION')
    )

    run_results = models.IntegerField('Results', choices=RUN_PF_CHOICES)
    cleanup = models.IntegerField('Clean flag', blank=True, default=0)
    for_bug = models.CharField(max_length=512, blank=True)
    caused_bug = models.CharField(max_length=512, blank=True)

    comment = models.CharField(max_length=1024, blank=True)

    start_time = models.DateTimeField('Time started', default=timezone.now)
    end_time = models.DateTimeField('Time ended', default=timezone.now)
    last_update = models.DateTimeField(
        'Entry updated at', default=timezone.now)
    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")

    def __str__(self):              # __unicode__ on Python 2
        return str(self.builder + " build " + str(self.build_number))
