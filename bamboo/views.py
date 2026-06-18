from django.shortcuts import render
from django.shortcuts import loader, render
# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from models import BAMBOOINSTALL
# Create your views here.


def changesettings(request):
    jarfile = '/root/atlassian-bamboo-agent-installer-5.8.1.jar'
    bamboohost = 'http://bamboo.yourdomain.com/agentServer/'
    crontab = False
    enabled = False

    if BAMBOOINSTALL.objects.count() == 0:
        initialBamboo = BAMBOOINSTALL(
            jarfile=jarfile,
            bamboohost=bamboohost,
            crontab=crontab,
            enabled=enabled,
            running=False)
        initialBamboo.save()
    else:
        BambooSettings = BAMBOOINSTALL.objects.all()[0]
        if jarfile != '':
            BambooSettings.jarfile = jarfile
        if bamboohost != '':
            BambooSettings.bamboohost = bamboohost
        if crontab != '':
            BambooSettings.crontab = crontab
        if enabled != '':
            BambooSettings.enabled = enabled
        BambooSettings.save()

    return HttpResponse(
        "<html><head><script>parent.location.reload();</script></head></html>")
