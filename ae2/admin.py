from django.contrib import admin

# Register your models here.
from ae2.models import AE2RUN, AE2INSTALL, suite, env, AEBranch

admin.site.register(AE2RUN)
admin.site.register(AE2INSTALL)
admin.site.register(suite)
admin.site.register(env)
admin.site.register(AEBranch)
