from django.db import models
from picklefield.fields import PickledObjectField
# Create your models here.


class job(models.Model):
    command = models.CharField(max_length=128)
    # allows any pickle-able input
    arguments = PickledObjectField(null=True, blank=True)
    attempted = models.BooleanField(default=False)
    attempt_result = models.IntegerField(
        null=True, blank=True)  # Did the attempt succeed?

    JOB_EXIT_CODES = (
        (0, 'SUCCESS'),
        (1, 'NOMATCH'),
        (2, 'PK NOT FOUND'),
        (3, 'MISSING PK'),
        (4, 'CURL ERROR'),
        (5, 'UNCAUGHT EXCEPTION'),
    )
    command_result = models.IntegerField(
        null=True,
        blank=True,
        choices=JOB_EXIT_CODES)  # Return code from command
    command_message = PickledObjectField(
        null=True, blank=True)  # what did the program return
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.command + " " + str(self.updated_at) +
                   " attempted?:" + str(self.attempted))
