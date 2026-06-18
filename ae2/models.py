from django.db import models
from simple_history.models import HistoricalRecords
# Create your models here.


class AE2INSTALL(models.Model):
    history = HistoricalRecords()
    install_directory = models.CharField(max_length=128)
    branch = models.CharField(max_length=128)
    revision = models.IntegerField()
    autopull = models.BooleanField(default=False)
    present = models.BooleanField(default=False)
    RUN_PF_CHOICES = (
        (0, 'In Stall (Automation Ready)'),
        (1, 'Hand Milked (Manual Testing)'),
        (2, 'Grazing (Disabled)'),
    )
    cow_mode = models.IntegerField(
        'Cow Mode', choices=RUN_PF_CHOICES, default=0)
    mode_dtg = models.DateTimeField(null=True, blank=True)
    mode_username = models.CharField(max_length=128, default="None")
    automated_suite = models.CharField(
        max_length=256, default="", null=True, blank=True)
    automated_env = models.CharField(
        max_length=256, default="", null=True, blank=True)
    automated_name = models.CharField(max_length=128, default="Unset")
    automated_description = models.CharField(max_length=512, default="Unset")
    AUTO_OS_CHOICES = (
        ('Unset', 'Unset'),
        ('sles11sp3', 'sles11sp3'),
        ('rhel67', 'rhel67'),
        ('rhel65', 'rhel65'),
        ('rhel64', 'rhel64'),
        ('win2k12', 'win2k12'),
    )
    automated_os = models.CharField(
        max_length=64,
        choices=AUTO_OS_CHOICES,
        default="Unset")
    automated_compiler = models.CharField(max_length=128, default="Unset")
    automated_scheduler = models.CharField(max_length=128, default="Unset")

    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")
    lastqueuecheck = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):              # __unicode__ on Python 2
        return self.install_directory + " " + \
            self.branch + " " + str(self.revision)


class AE2RUN(models.Model):
    suite = models.CharField(max_length=256)
    env = models.CharField(max_length=256)
    rpm = models.CharField(max_length=512, blank=True)
    tools = models.CharField(max_length=512, blank=True)
    branch = models.CharField(max_length=512)
    commit = models.IntegerField()
    buildnumber = models.IntegerField(default=0)
    pid = models.IntegerField(default=0)
    running = models.BooleanField(default=False)
    paused = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)
    cleanup = models.IntegerField('Clean flag', blank=True, default=0)
    needs_triage = models.BooleanField(default=False)
    username = models.CharField(max_length=128, default="Automatic")
    entrytype = models.CharField(max_length=128, default="Automatic")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):              # __unicode__ on Python 2
        return unicode(str(self.suite) + " " + str(self.env))


class suite(models.Model):
    location = models.CharField(max_length=512)
    name = models.CharField(max_length=128)

    def __str__(self):              # __unicode__ on Python 2
        return unicode(str(self.name) + " at " + str(self.location))


class env(models.Model):
    location = models.CharField(max_length=512)
    name = models.CharField(max_length=128)

    def __str__(self):              # __unicode__ on Python 2
        return unicode(str(self.name) + " at " + str(self.location))


class AEBranch(models.Model):
    location = models.CharField(max_length=512)
    name = models.CharField(max_length=128)

    def __str__(self):              # __unicode__ on Python 2
        return unicode(str(self.name) + " at " + str(self.location))
