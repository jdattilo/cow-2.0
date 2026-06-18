from django.db import models
from picklefield.fields import PickledObjectField
# Create your models here.


class activity(models.Model):
    action = models.CharField(max_length=256)
    # allows any pickle-able input
    arguments = PickledObjectField(null=True, blank=True)
    user = models.CharField(max_length=128, default="unknown")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):              # __unicode__ on Python 2
        return str(str(self.created_at) + ": " +
                   self.user + ", " + self.action)
