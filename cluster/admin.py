from django.contrib import admin

# Register your models here.
from cluster.models import cluster_member

admin.site.register(cluster_member)
