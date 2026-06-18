from django.db import models

# Create your models here.


class cowstatus(models.Model):
    site_root = models.CharField(max_length=256)
    server_type = models.CharField(max_length=256)
    operating_system = models.CharField(max_length=256)
    server_cron = models.BooleanField(default=False)
    queuemaster_cron = models.BooleanField(default=False)
    queuemaster_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.site_root + " " + self.created_at)
