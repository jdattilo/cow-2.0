from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import loader, render
from django.template import RequestContext
from ae2.models import AE2INSTALL, AE2RUN
from bamboo.models import BAMBOOINSTALL
from cluster.models import cluster_member
import socket
import os
from subprocess import check_output
from crontab import CronTab
import os.path
import sys


def systemcheck(request):
    # This should check system crontabs, bamboo status, and ae2 readiness
    RUNNING_DEVSERVER = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')

    SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # check AE2
    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory="/root/ae2",
            branch="https://sqa.yourdomain.com/tools/AwesomeExpress/branches/butterjunk/",
            revision=-1,
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]

    if os.path.exists(AE2Settings.install_directory + "/src/ae2.py"):
        AE2Settings.present = True
        AE2Settings.save()
    else:
        AE2Settings.present = False
        AE2Settings.save()

    # Check for running bamboo instance
    if BAMBOOINSTALL.objects.count() == 0:
        initialBamboo = BAMBOOINSTALL(
            jarfile='/root/atlassian-bamboo-agent-installer-5.8.1.jar',
            bamboohost="http://bamboo.yourdomain.com/agentServer/",
            crontab=False,
            enabled=False,
            running=False)
        initialBamboo.save()

    BambooSettings = BAMBOOINSTALL.objects.all()[0]

    bamboocheck = os.popen(
        "ps aux | grep bamboo-agent.sh | grep -v grep").read()

    if "bamboo" in bamboocheck and "defunct" not in bamboocheck:
        BambooSettings.running = True
    else:
        BambooSettings.running = False

    BambooSettings.save()

    return HttpResponse("--AE2 Install checked. Bamboo install checked. --")
