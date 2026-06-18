import datetime
from django.utils import timezone
from django.db import models
from simple_history.models import HistoricalRecords
# Create your models here.


class Test(models.Model):
    # historical records
    history = HistoricalRecords()

    # parent run information
    parentrun = models.ForeignKey('runs.Run')

    # test information
    test_conditions = models.CharField(max_length=256)
    test_args = models.CharField(max_length=512)
    test_sequence_number = models.IntegerField()
    data_file = models.CharField(max_length=512, blank=True)

    TEST_PF_CHOICES = (
        (1, 'PASS'),
        (2, 'PASS OVERRIDE'),
        (0, 'FAIL'),
        (11, 'INTERRUPTED'),
        (12, 'INVALID'),
        (13, 'IN PROGRESS'),
        (60, 'FAIL OVERRIDE'),
        (65, 'UNDER INVESTIGATION')
    )

    test_results = models.IntegerField('Results', choices=TEST_PF_CHOICES)

    caused_bug = models.CharField(max_length=512, blank=True)

    comment = models.CharField(max_length=1024, blank=True)

    start_time = models.DateTimeField('Time started', default=timezone.now)
    end_time = models.DateTimeField(
        'Time ended', default=timezone.now, blank=True)

    test_duration = models.IntegerField('Test duration ()')
    last_update = models.DateTimeField('date updated', default=timezone.now)
    creation_date = models.DateTimeField('date created', default=timezone.now)
    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")

    def __str__(self):              # __unicode__ on Python 2
        return str(self.parentrun.builder) + " build " + \
            str(self.parentrun.build_number) + " step " + str(self.test_sequence_number)
